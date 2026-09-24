# Projeto de Dados — Decisões monocráticas no TJRJ

**Pergunta de negócio:** *Quais áreas e câmaras do Tribunal de Justiça do Rio de Janeiro mais decidem
de forma monocrática (um desembargador sozinho, sem o colegiado), por tipo de recurso e ao longo dos meses?*

Por que isso importa para um gestor: decisão monocrática é mais rápida, mas o colegiado dá mais segurança.
Saber onde cada modo predomina ajuda a distribuir trabalho e acompanhar a produtividade das câmaras.

Jornada: **FONTES → INGESTÃO → PRESERVAÇÃO DO BRUTO (Delta Lake) → TRANSFORMAÇÃO (dbt) → CONSUMO (gold) → RESPOSTA (SQL)**

```
Hugging Face ──> data/raw/decisoes.csv ───────┐                         ┌─ bronze ─ silver ─ gold ─┐
equipe ────────> data/raw/camaras_depara.json ┴─> data/delta (versões) ─> raw ────────(dbt)────────┴─> consultas/resposta.sql
                          (fontes)                 (bruto preservado)    (DuckDB: warehouse/projeto.duckdb)
```

## Fontes

| Fonte | Formato | Origem |
|---|---|---|
| `data/raw/decisoes.csv` | CSV | Hugging Face [`celsowm/jurisprudencias_tjrj`](https://huggingface.co/datasets/celsowm/jurisprudencias_tjrj) — ~61 mil decisões públicas do TJRJ |
| `data/raw/camaras_depara.json` | JSON | de-para da reestruturação das câmaras, montado pela equipe |

## Como rodar (Windows, PowerShell)

Pré-requisito: **Python 3.12** (marcar "Add python.exe to PATH" na instalação).

```powershell
cd projeto-dados
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python -m src.pipeline      # ingestão + preservação do bruto (Delta) + carga do banco
dbt build                   # bronze, silver, gold + 18 testes
python -m src.consulta      # a resposta
```

> Os dados já estão em `data/raw` e o histórico em `data/delta`. Para baixar de novo da Hugging Face:
> `python -m src.baixar_fontes` (lote 1) e `python -m src.baixar_fontes --lote 2` (lote 2).
>
> Se o PowerShell bloquear o `activate`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Outros comandos

| Comando | Para quê |
|---|---|
| `python -m src.ver_camadas` | mostra quantas linhas tem cada camada |
| `python -m src.zerar_banco` | apaga só o banco (camadas vazias), para a demo |
| `python -m src.time_travel` | mesma consulta na versão atual e na anterior do Delta |
| `python -m src.pipeline --versao 0` | reprocessa o banco a partir da versão 0 do Delta |
| `python -m src.consulta consultas/resposta_por_camara.sql` | ângulo 1: por câmara |
| `python -m src.consulta consultas/resposta_por_classe.sql` | ângulo 2: por tipo de recurso |
| `python -m src.consulta consultas/resposta_por_mes.sql` | ângulo 3: por mês |
| `dbt docs generate` e `dbt docs serve` | linhagem (DAG) em http://localhost:8080 |

## Estrutura

```
data/raw/        fontes como chegaram (CSV + JSON)
data/delta/      bruto preservado em Delta Lake (2+ versões)
src/             scripts Python (download, pipeline, consultas)
models/bronze    cópia fiel do bruto
models/silver    limpeza, tipagem, de-para das câmaras, deduplicação, quarentena
models/gold      camada de consumo (gold_decisoes)
tests/           teste singular do dbt
consultas/       as consultas que respondem a pergunta
DECISOES.md      as decisões documentadas
```

Dados pessoais: ficaram de fora os textos das decisões (podem citar partes) e o nome do relator
(só o código `CodMagRel` foi mantido). São decisões públicas do tribunal.
