#!/usr/bin/env python3
"""
Load all products (existing + gravel) into the new contexto table
"""
import json
import pg8000
from pathlib import Path

ROOT = Path(r"C:\Users\igoor\OneDrive\Desktop\CANNONDALE DATA & BI PLATFORM")
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

def load_existing_products():
    """Load existing products from backup"""
    json_file = RAW_DIR / "produtos_reais_api.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_gravel_products():
    """Load gravel products from new scrape"""
    json_file = RAW_DIR / "gravel_products.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    conn = pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    
    try:
        # Load existing products
        existing = load_existing_products()
        print(f"Existing products: {len(existing)}")
        
        # Load gravel products
        gravel = load_gravel_products()
        print(f"Gravel products: {len(gravel)}")
        
        # Combine all products
        all_products = existing + gravel
        print(f"Total products: {len(all_products)}")
        
        # Insert into contexto table
        inserted = 0
        for p in all_products:
            try:
                cur.execute("""
                    INSERT INTO contexto (
                        id_produto, modelo, categoria, subcategoria, plataforma,
                        preco_site, moeda, url_produto, url_imagem_principal,
                        especificacoes, data_coleta, fonte, tipo_dado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id_produto) DO UPDATE SET
                        modelo = EXCLUDED.modelo,
                        categoria = EXCLUDED.categoria,
                        subcategoria = EXCLUDED.subcategoria,
                        plataforma = EXCLUDED.plataforma,
                        preco_site = EXCLUDED.preco_site,
                        moeda = EXCLUDED.moeda,
                        url_produto = EXCLUDED.url_produto,
                        url_imagem_principal = EXCLUDED.url_imagem_principal,
                        especificacoes = EXCLUDED.especificacoes,
                        data_coleta = EXCLUDED.data_coleta,
                        fonte = EXCLUDED.fonte,
                        tipo_dado = EXCLUDED.tipo_dado
                """, (
                    p["id_produto"],
                    p["modelo"],
                    p["categoria"],
                    p.get("subcategoria", ""),
                    p.get("plataforma", ""),
                    p.get("preco_site", 0),
                    p.get("moeda", "BRL"),
                    p.get("url_produto", ""),
                    p.get("url_imagem_principal", ""),
                    p.get("especificacoes", ""),
                    p.get("data_coleta", ""),
                    p.get("fonte", "Cannondale Oficial"),
                    p.get("tipo_dado", "OFICIAL")
                ))
                inserted += 1
            except Exception as e:
                print(f"Erro ao inserir {p.get('modelo', 'unknown')}: {e}")
        
        conn.commit()
        print(f"\n[OK] Total produtos inseridos/atualizados: {inserted}")
        
        # Verify
        cur.execute("SELECT categoria, COUNT(*) FROM contexto GROUP BY categoria ORDER BY COUNT(*) DESC")
        print("\nProdutos por categoria:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        cur.execute("SELECT subcategoria, COUNT(*) FROM contexto WHERE subcategoria IS NOT NULL AND subcategoria != '' GROUP BY subcategoria ORDER BY COUNT(*) DESC")
        print("\nProdutos por subcategoria:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()