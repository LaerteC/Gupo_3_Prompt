"""
Abre o Dashboard Executivo da camada Gold no navegador padro.

Uso:  python -m src.dashboard
"""
import webbrowser
from pathlib import Path

arquivo = Path("dashboard.html").resolve()
if not arquivo.exists():
    print(f"Erro: Arquivo {arquivo} no encontrado.")
    raise SystemExit(1)

print(f"Abrindo Dashboard Executivo da camada Gold: {arquivo}")
webbrowser.open(arquivo.as_uri())
