"""Images ETL: valida imagens -> dim_imagens."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "cannabondale_imagens_raw.csv"
OUT = ROOT / "data" / "processed" / "dim_imagens_validated.csv"


def build_imagens(raw_path: Path = RAW, out_path: Path = OUT) -> pd.DataFrame:
    df = pd.read_csv(raw_path)
    df = df.dropna(subset=["id_produto_sku", "url_imagem", "tipo_imagem"])
    df = df.drop_duplicates(subset=["id_produto_sku", "tipo_imagem", "url_imagem"])
    # normaliza tipo_imagem
    df["tipo_imagem"] = df["tipo_imagem"].str.strip().str.lower()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"dim_imagens validado: {len(df)} linhas -> {out_path}")
    return df


if __name__ == "__main__":
    print(build_imagens().groupby("tipo_imagem").size())
