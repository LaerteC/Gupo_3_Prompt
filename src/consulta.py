"""
Roda a consulta final (a RESPOSTA) sobre a camada gold e mostra o resultado.

Uso:
  python -m src.consulta                                  -> consultas/resposta.sql
  python -m src.consulta consultas/resposta_por_camara.sql -> ângulo por câmara
  python -m src.consulta consultas/resposta_por_classe.sql -> ângulo por tipo de recurso
  python -m src.consulta consultas/resposta_por_mes.sql    -> ângulo por mês
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 100)

arquivo = Path(sys.argv[1] if len(sys.argv) > 1 else "consultas/resposta.sql")
sql = arquivo.read_text(encoding="utf-8")

con = duckdb.connect("warehouse/projeto.duckdb", read_only=True)
print(f"--- {arquivo} ---")
print(con.execute(sql).df().to_string(index=False))
con.close()
