"""
Mostra as "gavetas" (camadas) do banco e quantas linhas cada tabela tem.
Ótimo para a demo: rode antes (vazio) e depois (cheio) do pipeline e do dbt build.

Uso:  python -m src.ver_camadas
"""
from pathlib import Path

import duckdb

BANCO = Path("warehouse/projeto.duckdb")

if not BANCO.exists():
    print("O banco ainda não existe: todas as camadas estão VAZIAS.")
    print("Rode:  python -m src.pipeline")
    raise SystemExit

con = duckdb.connect(str(BANCO), read_only=True)
tabelas = con.execute("""
    select table_schema, table_name
    from information_schema.tables
    where table_schema in ('raw', 'bronze', 'silver', 'gold')
""").fetchall()

for camada in ["raw", "bronze", "silver", "gold"]:
    print(f"\n[{camada.upper()}]")
    nomes = sorted(t for s, t in tabelas if s == camada)
    if not nomes:
        print("   (vazia)")
    for t in nomes:
        n = con.execute(f'select count(*) from {camada}."{t}"').fetchone()[0]
        print(f"   {t:<28} {n:>6} linhas")
con.close()
