"""
PIPELINE: data/raw (arquivos) -> Delta Lake (bruto preservado, com versões) -> DuckDB (schema raw)

Regras deste script:
  * NENHUMA regra de negócio: tudo é guardado como TEXTO, exatamente como chegou
    (inclusive os defeitos). Limpar e tipar é trabalho do dbt.
  * O banco é SEMPRE carregado a partir do Delta, nunca direto do arquivo.
    Assim, dá para reconstruir tudo do zero a partir do bruto preservado.

Uso:
  python -m src.pipeline                 -> preserva o bruto (nova versão se mudou) e carrega o banco
  python -m src.pipeline --versao 0      -> reprocessa o banco a partir da versão 0 do Delta (time travel)
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

RAW = Path("data/raw")
DELTA = Path("data/delta")
BANCO = Path("warehouse/projeto.duckdb")


# ---------- 1) LER as fontes, sem mudar nada ----------
def ler_decisoes_csv(caminho):
    # dtype=str + keep_default_na=False: nada é "adivinhado", vazio continua vazio
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def ler_camaras_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        conteudo = json.load(f)

    def texto(v):
        if v is None:
            return None                       # null do JSON continua nulo
        if isinstance(v, (list, dict)):
            return json.dumps(v, ensure_ascii=False)  # lista vira texto JSON
        return str(v)

    linhas = [{k: texto(v) for k, v in item.items()} for item in conteudo["camaras"]]
    return pd.DataFrame(linhas, dtype=object)


FONTES = {
    "decisoes": ("decisoes.csv", ler_decisoes_csv),
    "camaras": ("camaras_depara.json", ler_camaras_json),
}


def hash_arquivo(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()[:16]


def como_texto(df, arquivo, hash_):
    df = df.copy()
    df["_arquivo_origem"] = arquivo
    df["_hash_arquivo"] = hash_
    df["_ingerido_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    esquema = pa.schema([(c, pa.string()) for c in df.columns])
    return pa.Table.from_pandas(df, schema=esquema, preserve_index=False)


# ---------- 2) PRESERVAR no Delta (cada mudança = nova versão) ----------
def preservar(nome, arquivo, ler):
    caminho_arquivo = RAW / arquivo
    caminho_delta = DELTA / nome
    h = hash_arquivo(caminho_arquivo)

    if (caminho_delta / "_delta_log").exists():
        dt = DeltaTable(str(caminho_delta))
        hash_atual = dt.to_pandas(columns=["_hash_arquivo"]).iloc[0, 0]
        if hash_atual == h:
            print(f"  [{nome}] arquivo não mudou -> mantém versão {dt.version()}")
            return

    tabela = como_texto(ler(caminho_arquivo), arquivo, h)
    write_deltalake(str(caminho_delta), tabela, mode="overwrite", schema_mode="overwrite")
    print(f"  [{nome}] nova versão gravada: {DeltaTable(str(caminho_delta)).version()} "
          f"({tabela.num_rows} linhas)")


# ---------- 3) CARREGAR o banco a partir do Delta ----------
def carregar(con, nome, versao=None):
    dt = DeltaTable(str(DELTA / nome))
    if versao is not None:
        # se essa fonte não tem a versão pedida, usa a mais recente que ela tiver
        dt = DeltaTable(str(DELTA / nome), version=min(versao, dt.version()))
    df = dt.to_pandas()
    con.register("tmp", df)
    con.execute(f"CREATE OR REPLACE TABLE raw.{nome} AS SELECT * FROM tmp")
    con.unregister("tmp")
    print(f"  [{nome}] raw.{nome} <- Delta versão {dt.version()} ({len(df)} linhas)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--versao", type=int, default=None,
                        help="reprocessa o banco a partir de uma versão antiga do Delta")
    args = parser.parse_args()

    faltando = [a for a, _ in FONTES.values() if not (RAW / a).exists()]
    if faltando:
        print(f"Faltam as fontes em data/raw: {faltando}")
        print("Rode primeiro:  python -m src.baixar_fontes")
        raise SystemExit(1)

    DELTA.mkdir(parents=True, exist_ok=True)
    BANCO.parent.mkdir(parents=True, exist_ok=True)

    if args.versao is None:
        print("1) Preservando o bruto no Delta Lake...")
        for nome, (arquivo, ler) in FONTES.items():
            preservar(nome, arquivo, ler)

    print("2) Carregando o banco (schema raw) a partir do Delta...")
    con = duckdb.connect(str(BANCO))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for nome in FONTES:
        carregar(con, nome, args.versao)
    con.close()
    print("Pronto! Agora rode:  dbt build")


if __name__ == "__main__":
    main()
