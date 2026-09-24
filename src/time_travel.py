"""
TIME TRAVEL no Delta Lake: a MESMA consulta na versão atual e na anterior.

Uso:  python -m src.time_travel
"""
import re
from datetime import datetime, timezone

from deltalake import DeltaTable

CAMINHO = "data/delta/decisoes"


def para_data(valor):
    m = re.search(r"-?\d+", str(valor))
    if not m or int(m.group()) <= 0:
        return None
    return datetime.fromtimestamp(int(m.group()) / 1000, tz=timezone.utc).date()


def consulta(df):
    """A mesma pergunta feita às duas versões: quantas decisões e até que data?"""
    datas = df["DtHrMov"].map(para_data).dropna()
    mono = (df["DescrTipDoc"] == "Decisão monocrática").sum()
    return (f"{len(df):>6} linhas | {mono:>5} monocráticas | "
            f"decisão mais recente: {max(datas).strftime('%d/%m/%Y')}")


dt = DeltaTable(CAMINHO)
print("HISTÓRICO (cada gravação = 1 versão):")
for h in sorted(dt.history(), key=lambda h: h["version"]):
    quando = datetime.fromtimestamp(h["timestamp"] / 1000).strftime("%d/%m/%Y %H:%M:%S")
    print(f"  versão {h['version']}  |  {h.get('operation')}  |  {quando}")

atual = dt.version()
if atual < 1:
    print("\nSó existe 1 versão. Rode 'python -m src.baixar_fontes --lote 2' e depois o pipeline.")
    raise SystemExit

print("\nMESMA CONSULTA, DUAS VERSÕES:")
for v in [atual - 1, atual]:
    df = DeltaTable(CAMINHO, version=v).to_pandas(columns=["DtHrMov", "DescrTipDoc"])
    print(f"  versão {v}: {consulta(df)}")
