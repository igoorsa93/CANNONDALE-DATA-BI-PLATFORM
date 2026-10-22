#!/usr/bin/env python3
"""
Load products into main PostgreSQL database using pg8000
"""
import os
import sys
import json
import pg8000
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def load_products():
    csv_file = RAW_DIR / "produtos_reais_api.csv"
    json_file = RAW_DIR / "produtos_reais_api.json"
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"Loading {len(products)} products...")
        
        inserted = 0
        updated = 0
        errors = 0
        
        for p in products:
            try:
                # Check if product exists
                cur.execute(
                    "SELECT id_produto FROM dim.dim_produtos WHERE salsify_id = %s",
                    (p["id_produto"],)
                )
                existing = cur.fetchone()
                
                if existing:
                    # Update
                    cur.execute("""
                        UPDATE dim.dim_produtos SET
                            sku = %s, modelo = %s, categoria = %s, subcategoria = %s,
                            plataforma = %s, codigo_modelo = %s, ano_modelo = %s,
                            cor = %s, tamanho = %s, material_quadro = %s, peso = %s,
                            suspensao = %s, freios = %s, rodas = %s, preco_site = %s,
                            moeda = %s, url_produto = %s, descricao = %s, badges = %s,
                            tags = %s, is_electric = %s, source_category_slug = %s,
                            tipo_dado = %s, url_imagem_principal = %s, updated_at = %s
                        WHERE salsify_id = %s
                    """, (
                        p["sku"], p["modelo"], p["categoria"], p["subcategoria"],
                        p["plataforma"], p["codigo_modelo"], p["ano_modelo"],
                        p["cor"], p["tamanho"], p["material_quadro"], p["peso"],
                        p["suspensao"], p["freios"], p["rodas"], p["preco_site"],
                        p["moeda"], p["url_produto"], p["descricao"], p["badges"],
                        p["tags"], p["is_electric"], p["source_category_slug"],
                        p["tipo_dado"], p["url_imagem_principal"], datetime.now(),
                        p["id_produto"]
                    ))
                    updated += 1
                else:
                    # Insert
                    cur.execute("""
                        INSERT INTO dim.dim_produtos (
                            salsify_id, sku, modelo, categoria, subcategoria, plataforma,
                            codigo_modelo, ano_modelo, cor, tamanho, material_quadro, peso,
                            suspensao, freios, rodas, preco_site, moeda, url_produto,
                            descricao, badges, tags, is_electric, source_category_slug,
                            tipo_dado, url_imagem_principal, collection_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p["id_produto"], p["sku"], p["modelo"], p["categoria"], p["subcategoria"],
                        p["plataforma"], p["codigo_modelo"], p["ano_modelo"], p["cor"],
                        p["tamanho"], p["material_quadro"], p["peso"], p["suspensao"],
                        p["freios"], p["rodas"], p["preco_site"], p["moeda"], p["url_produto"],
                        p["descricao"], p["badges"], p["tags"], p["is_electric"],
                        p["source_category_slug"], p["tipo_dado"], p["url_imagem_principal"],
                        datetime.now().date()
                    ))
                    inserted += 1
                    
            except Exception as e:
                print(f"  Error loading {p.get('modelo', 'unknown')}: {e}")
                errors += 1
        
        conn.commit()
        print(f"[OK] Products loaded: {inserted} inserted, {updated} updated, {errors} errors")
        
        # Log to ETL log
        cur.execute("""
            INSERT INTO meta.etl_log (processo, tabela_destino, status, registros_processados, 
                                     registros_inseridos, registros_atualizados, registros_erro, 
                                     inicio_execucao, fim_execucao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ("load_products", "dim.dim_produtos", "SUCCESS" if errors == 0 else "PARTIAL",
              len(products), inserted, updated, errors, datetime.now(), datetime.now()))
        conn.commit()
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    success = load_products()
    sys.exit(0 if success else 1)