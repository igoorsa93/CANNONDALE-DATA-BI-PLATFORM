#!/usr/bin/env python3
"""
Load images into the new imagens table (PostgreSQL main DB + images DB)
"""
import json
import pg8000
from pathlib import Path

ROOT = Path(r"C:\Users\igoor\OneDrive\Desktop\CANNONDALE DATA & BI PLATFORM")
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

def get_main_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

def get_images_db_connection():
    return pg8000.connect(
        host="localhost", port=5434, database="cannondale_images", user="postgres", password="postgres"
    )

def main():
    main_conn = get_main_db_connection()
    main_cur = main_conn.cursor()
    
    img_conn = get_images_db_connection()
    img_cur = img_conn.cursor()
    
    try:
        # Load all products with images
        json_file = Path(r"C:\Users\igoor\OneDrive\Desktop\data\raw\gravel_products.json")
        with open(json_file, 'r', encoding='utf-8') as f:
            gravel_products = json.load(f)
        
        # Also load existing products with images
        json_file2 = ROOT / "data" / "raw" / "produtos_reais_api.json"
        with open(json_file2, 'r', encoding='utf-8') as f:
            existing_products = json.load(f)
        
        all_products = existing_products
        
        print(f"Loading images for {len(all_products)} products...")
        
        inserted_main = 0
        inserted_img = 0
        
        for p in all_products:
            try:
                # Parse all images
                imagens = json.loads(p.get("todas_imagens", "[]"))
                url_principal = p.get("url_imagem_principal", "")
                
                for idx, img in enumerate(imagens):
                    img_id = img.get("image_id", "")
                    url = img.get("url", "")
                    color = img.get("color", "")
                    size = img.get("size", "")
                    
                    # Determine image type
                    tipo = "Principal" if idx == 0 else "Detalhe"
                    principal = (idx == 0)
                    
                    # Generate filename
                    modelo_safe = p["modelo"].replace("/", "-").replace(" ", "_")
                    nome_arquivo = f"{modelo_safe}_{img_id}.jpg"
                    
                    # Insert into main DB (imagens table)
                    main_cur.execute("""
                        INSERT INTO imagens (
                            id_produto, modelo, categoria, tipo_imagem, imagem_principal,
                            url_produto, url_imagem, arquivo_local, nome_arquivo,
                            data_coleta, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p["id_produto"],
                        p["modelo"],
                        p["categoria"],
                        tipo,
                        principal,
                        p.get("url_produto", ""),
                        url,
                        f"Imagens/{p['categoria']}/{nome_arquivo}",
                        nome_arquivo,
                        p.get("data_coleta", ""),
                        "OK"
                    ))
                    inserted_main += 1
                    
                    # Insert into images DB (images.imagens table)
                    img_cur.execute("""
                        INSERT INTO images.imagens (
                            id_produto, modelo, categoria, url_produto,
                            url_imagem_original, url_imagem_widen, tipo_imagem, imagem_principal,
                            nome_arquivo, caminho_local, hash_md5, tamanho_bytes,
                            data_coleta, data_download, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p["id_produto"],
                        p["modelo"],
                        p["categoria"],
                        p.get("url_produto", ""),
                        url,
                        url,
                        "Principal" if idx == 0 else "Detalhe",
                        idx == 0,
                        nome_arquivo,
                        f"Imagens/{p['categoria']}/{nome_arquivo}",
                        "",  # hash_md5
                        0,   # tamanho_bytes
                        p.get("data_coleta", ""),
                        "2026-10-07",
                        "OK"
                    ))
                    inserted_img += 1
                    
            except Exception as e:
                print(f"Erro ao processar imagens de {p.get('modelo', 'unknown')}: {e}")
        
        main_conn.commit()
        img_conn.commit()
        
        print(f"\n[OK] Imagens inseridas: {inserted_main} (main DB), {inserted_img} (images DB)")
        
        # Verify
        main_cur.execute("SELECT categoria, COUNT(*) FROM imagens GROUP BY categoria ORDER BY COUNT(*) DESC")
        print("\nImagens por categoria (main DB):")
        for row in main_cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        img_cur.execute("SELECT categoria, COUNT(*) FROM images.imagens GROUP BY categoria ORDER BY COUNT(*) DESC")
        print("\nImagens por categoria (images DB):")
        for row in img_cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
    finally:
        main_cur.close()
        main_conn.close()
        img_cur.close()
        img_conn.close()

if __name__ == "__main__":
    main()