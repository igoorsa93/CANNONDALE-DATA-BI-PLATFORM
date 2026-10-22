"""Products ETL: valida e deduplica o catálogo bruto -> dim_produtos."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "cannabondale_produtos_raw.csv"
OUT = ROOT / "data" / "processed" / "dim_produtos_validated.csv"


def build_produtos(raw_path: Path = RAW, out_path: Path = OUT) -> pd.DataFrame:
    df = pd.read_csv(raw_path)
    # regras de qualidade
    df = df.dropna(subset=["sku", "modelo", "categoria"])
    df = df.drop_duplicates(subset=["sku"])
    df = df[df["categoria"].str.strip() != ""]
    df = df[df["url_produto"].notna()]
    # padroniza case
    df["categoria"] = df["categoria"].str.strip().str.title()
    df["plataforma"] = df["plataforma"].str.strip()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"dim_produtos validado: {len(df)} linhas -> {out_path}")
    return df


if __name__ == "__main__":
    df = build_produtos()
    print(df.groupby("categoria").size())
