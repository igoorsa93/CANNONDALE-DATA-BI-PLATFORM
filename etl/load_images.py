#!/usr/bin/env python3
"""
Load images into both main database and images database using pg8000
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
IMAGES_DIR = ROOT / "Imagens"

def get_main_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def get_images_db_connection():
    return pg8000.connect(
        host=os.getenv("PGIMAGES_HOST", "localhost"),
        port=int(os.getenv("PGIMAGES_PORT", "5434")),
        database=os.getenv("PGIMAGES_DATABASE", "cannondale_images"),
        user=os.getenv("PGIMAGES_USER", "postgres"),
        password=os.getenv("PGIMAGES_PASSWORD", "postgres")
    )

def load_images():
    csv_file = RAW_DIR / "catalogo_imagens.csv"
    json_file = RAW_DIR / "catalogo_imagens.json"
    
    if not json_file.exists():
        print(f"[ERROR] JSON file not found: {json_file}")
        return False
    
    with open(json_file, 'r', encoding='utf-8') as f:
        images = json.load(f)
    
    print(f"Loading {len(images)} images...")
    
    main_conn = get_main_db_connection()
    main_cur = main_conn.cursor()
    
    img_conn = get_images_db_connection()
    img_cur = img_conn.cursor()
    
    try:
        inserted_main = 0
        inserted_img = 0
        errors = 0
        
        for img in images:
            if img["status"] != "OK" or not img["caminho_local"]:
                continue
            
            try:
                local_path = Path(img["caminho_local"])
                if not local_path.exists():
                    print(f"  File not found: {local_path}")
                    errors += 1
                    continue
                
                # Get product ID from main DB
                main_cur.execute(
                    "SELECT id_produto FROM dim.dim_produtos WHERE salsify_id = %s",
                    (img["id_produto"],)
                )
                prod_result = main_cur.fetchone()
                
                if not prod_result:
                    print(f"  Product not found in DB: {img['id_produto']}")
                    errors += 1
                    continue
                
                db_produto_id = prod_result[0]
                
                # Insert into main DB
                main_cur.execute("""
                    INSERT INTO dim.dim_produto_imagens (
                        id_produto, modelo, categoria, url_produto, url_imagem,
                        tipo_imagem, imagem_principal, nome_arquivo, caminho_local,
                        hash_md5, tamanho_bytes, data_download, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    db_produto_id, img["modelo"], img["categoria"], img["url_produto"],
                    img["url_imagem"], img["tipo_imagem"], img["imagem_principal"],
                    img["nome_arquivo"], img["caminho_local"], img["hash_md5"],
                    img["tamanho_bytes"], datetime.now().date(), img["status"]
                ))
                inserted_main += 1
                
                # Insert into images DB
                img_cur.execute("""
                    INSERT INTO images.imagens (
                        id_produto, modelo, categoria, url_produto, url_imagem_original,
                        url_imagem_widen, tipo_imagem, imagem_principal, ordem,
                        nome_arquivo, caminho_local, minio_object_name, minio_bucket,
                        hash_md5, tamanho_bytes, data_coleta, data_download, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    img["id_produto"], img["modelo"], img["categoria"], img["url_produto"],
                    img["url_imagem"], img["url_imagem"], img["tipo_imagem"],
                    img["imagem_principal"], 0, img["nome_arquivo"], img["caminho_local"],
                    "", "", img["hash_md5"], img["tamanho_bytes"],
                    datetime.now().date(), datetime.now(), img["status"]
                ))
                inserted_img += 1
                
            except Exception as e:
                print(f"  Error loading image for {img.get('modelo', 'unknown')}: {e}")
                errors += 1
        
        main_conn.commit()
        img_conn.commit()
        
        print(f"[OK] Images loaded: {inserted_main} main DB, {inserted_img} images DB, {errors} errors")
        return True
        
    except Exception as e:
        main_conn.rollback()
        img_conn.rollback()
        print(f"[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        main_cur.close()
        main_conn.close()
        img_cur.close()
        img_conn.close()

if __name__ == "__main__":
    success = load_images()
    sys.exit(0 if success else 1)