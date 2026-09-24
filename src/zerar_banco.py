"""
Apaga SÓ o banco (pasta warehouse). As fontes (data/raw) e o histórico Delta
(data/delta) ficam intactos. Serve para a demo: "começando com as camadas vazias".

Uso:  python -m src.zerar_banco
"""
import shutil
from pathlib import Path

shutil.rmtree(Path("warehouse"), ignore_errors=True)
shutil.rmtree(Path("target"), ignore_errors=True)
print("Banco apagado. Todas as camadas estão vazias. (data/raw e data/delta intactos)")
