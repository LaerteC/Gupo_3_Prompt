"""
BAIXA A FONTE 1 da Hugging Face: celsowm/jurisprudencias_tjrj
(decisões do Tribunal de Justiça do Rio de Janeiro, ~61 mil linhas).

Salva em data/raw/decisoes.csv, SEM limpar nada.
A fonte 2 (data/raw/camaras_depara.json) já vem pronta no repositório.

Uso:
  python -m src.baixar_fontes            -> lote 1: as 80% decisões mais antigas
  python -m src.baixar_fontes --lote 2   -> lote 2: todas as decisões (chegaram as mais novas)

Na primeira vez, baixa uns 200 MB (fica guardado no cache, as próximas são rápidas).
Não precisa de login: o dataset é público.
"""
import argparse
import random
import re
from pathlib import Path

import pandas as pd

DATASET = "celsowm/jurisprudencias_tjrj"
SAIDA = Path("data/raw/decisoes.csv")

# Só as colunas que a pergunta usa. Ficam de FORA de propósito:
#  - Texto, TextoSemFormat, tese: textos longos (deixariam o arquivo com ~400 MB)
#    e podem citar nomes de partes (dado pessoal).
#  - NomeMagRel: nome do relator. Guardamos só o código (CodMagRel).
COLUNAS = [
    "_id", "CodDoc", "NumProcCnj", "NumAntigo", "Classe", "DescrTipDoc",
    "CodOrgJulg", "NomeOrgJulg", "CodMagRel", "DtHrMov", "DtHrPubl",
]


def baixar(arquivo_local=None):
    from datasets import load_dataset
    if arquivo_local:  # só para testes, com um parquet de amostra
        ds = load_dataset("parquet", data_files=arquivo_local, split="train")
    else:
        print(f"Baixando {DATASET} da Hugging Face (pode demorar na 1ª vez)...")
        ds = load_dataset(DATASET, split="train")
    faltando = [c for c in COLUNAS if c not in ds.column_names]
    if faltando:
        raise SystemExit(f"O dataset não tem as colunas {faltando}. Colunas: {ds.column_names}")
    return ds.select_columns(COLUNAS).to_pandas()


def milissegundos(valor):
    """'/Date(1737428400000)/' -> 1737428400000 (só para decidir o lote)."""
    m = re.search(r"-?\d+", str(valor))
    return int(m.group()) if m else 0


def injetar_defeitos(df):
    """
    Os dados reais JÁ têm defeitos (ver DECISOES.md). Colocamos mais 3,
    com semente fixa, para exercitar testes que os dados reais não exercitariam.
    """
    rng = random.Random(42)
    n = len(df)
    amostra = lambda pct: rng.sample(range(n), max(1, int(n * pct)))
    df = df.copy()
    col = df.columns.get_loc
    for i in amostra(0.01):     # I1: Classe digitada em minúsculo e com espaços
        df.iat[i, col("Classe")] = f"  {str(df.iat[i, col('Classe')]).lower()} "
    for i in amostra(0.005):    # I2: data do movimento em branco
        df.iat[i, col("DtHrMov")] = ""
    dup = df.iloc[amostra(0.005)]  # I3: mesma decisão exportada 2 vezes
    return pd.concat([df, dup], ignore_index=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lote", type=int, default=1, choices=[1, 2])
    p.add_argument("--arquivo-local", default=None, help=argparse.SUPPRESS)
    args = p.parse_args()

    df = baixar(args.arquivo_local)
    df = injetar_defeitos(df)

    if args.lote == 1:
        # simula a "primeira carga": só as decisões mais antigas (80%)
        ms = df["DtHrMov"].map(milissegundos)
        corte = ms.quantile(0.80)
        df = df[ms <= corte]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"Lote {args.lote}: {len(df)} decisões salvas em {SAIDA}")


if __name__ == "__main__":
    main()
