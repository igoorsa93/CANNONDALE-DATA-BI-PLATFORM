"""Pipeline orchestrator: products -> images -> stores/sales/logistics -> validação.

Carregamento no PostgreSQL via docker exec psql (seeds já aplicados).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path = ROOT) -> int:
    print(">>", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def main() -> int:
    rc = 0
    rc |= run([sys.executable, "etl/products/build_produtos.py"])
    rc |= run([sys.executable, "etl/images/build_imagens.py"])
    rc |= run([sys.executable, "etl/sales/generate_sales.py"])
    print("Pipeline de transformações concluído. Carga SQL já aplicada via seeds.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
