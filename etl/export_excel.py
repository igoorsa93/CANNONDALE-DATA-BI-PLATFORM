#!/usr/bin/env python3
"""
Export data to Excel files for Power BI
"""
import os
import sys
import pg8000
import pandas as pd
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCEL_DIR = ROOT / "excel"
EXCEL_DIR.mkdir(parents=True, exist_ok=True)

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def export_excel():
    conn = get_db_connection()
    
    try:
        print("=== EXPORTING TO EXCEL ===")
        
        # CANNONDALE_DATA.xlsx
        data_file = EXCEL_DIR / "CANNONDALE_DATA.xlsx"
        print(f"Creating {data_file}...")
        
        with pd.ExcelWriter(data_file, engine='openpyxl') as writer:
            # 1. Produtos
            df_produtos = pd.read_sql("""
                SELECT 
                    id_produto, salsify_id, sku, modelo, categoria, subcategoria, plataforma,
                    codigo_modelo, ano_modelo, cor, tamanho, material_quadro, peso,
                    suspensao, freios, rodas, preco_site, moeda, url_produto,
                    descricao, badges, tags, is_electric, tipo_dado, url_imagem_principal,
                    collection_date
                FROM dim.dim_produtos 
                WHERE is_active = TRUE
                ORDER BY categoria, subcategoria, plataforma, modelo
            """, conn)
            df_produtos.to_excel(writer, sheet_name='Produtos', index=False)
            print(f"  Produtos: {len(df_produtos)} rows")
            
            # 2. Vendas
            df_vendas = pd.read_sql("""
                SELECT 
                    v.id_venda, d.data, d.ano, d.mes, d.mes_ano, d.trimestre,
                    l.id_loja, l.nome_loja, l.cidade, l.estado, l.pais, l.regiao, l.tipo_loja, l.perfil_desempenho,
                    p.id_produto, p.modelo, p.categoria, p.subcategoria, p.plataforma,
                    v.quantidade, v.preco_unitario, v.desconto, v.valor_bruto, v.valor_liquido,
                    v.custo_produto, v.margem, v.margem_pct,
                    c.canal, fp.forma_pagamento, v.status
                FROM fact.fato_vendas v
                JOIN dim.dim_data d ON d.id_data = v.id_data
                JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
                JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
                LEFT JOIN dim.dim_canais_venda c ON c.id_canal = v.id_canal
                LEFT JOIN dim.dim_formas_pagamento fp ON fp.id_forma_pagamento = v.id_forma_pagamento
                WHERE v.tipo_dado = 'SIMULADO'
                ORDER BY d.data DESC
            """, conn)
            df_vendas.to_excel(writer, sheet_name='Vendas', index=False)
            print(f"  Vendas: {len(df_vendas)} rows")
            
            # 3. Estoque
            df_estoque = pd.read_sql("""
                SELECT 
                    e.id_estoque, d.data, d.ano, d.mes, d.mes_ano,
                    l.id_loja, l.nome_loja, l.cidade, l.estado, l.pais, l.regiao, l.tipo_loja, l.perfil_desempenho,
                    p.id_produto, p.modelo, p.categoria, p.subcategoria, p.plataforma, p.preco_site,
                    e.estoque_inicial, e.entradas, e.saidas, e.transferencias, e.vendas, e.estoque_final,
                    e.estoque_minimo, e.estoque_maximo, e.ponto_reposicao,
                    e.classificacao_estoque, e.giro_estoque, e.cobertura_dias
                FROM fact.fato_estoque e
                JOIN dim.dim_data d ON d.id_data = e.id_data
                JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
                JOIN dim.dim_produtos p ON p.id_produto = e.id_produto
                WHERE e.tipo_dado = 'SIMULADO'
                ORDER BY d.data DESC, l.nome_loja, p.modelo
            """, conn)
            df_estoque.to_excel(writer, sheet_name='Estoque', index=False)
            print(f"  Estoque: {len(df_estoque)} rows")
            
            # 4. Lojas
            df_lojas = pd.read_sql("""
                SELECT 
                    id_loja, nome_loja, tipo_loja, endereco, cidade, estado, pais,
                    regiao, continente, cep, latitude, longitude, telefone, site,
                    perfil_desempenho, is_simulated, tipo_dado
                FROM dim.dim_lojas
                ORDER BY pais, regiao, cidade, nome_loja
            """, conn)
            df_lojas.to_excel(writer, sheet_name='Lojas', index=False)
            print(f"  Lojas: {len(df_lojas)} rows")
            
            # 5. Dicionário de Dados
            dict_data = []
            
            # Produtos columns
            for col in df_produtos.columns:
                dict_data.append({
                    'Tabela': 'Produtos',
                    'Coluna': col,
                    'Tipo': str(df_produtos[col].dtype),
                    'Origem': 'OFICIAL' if col in ['modelo', 'categoria', 'preco_site', 'url_produto'] else 'CALCULADO',
                    'Obrigatorio': 'SIM' if df_produtos[col].notna().all() else 'NÃO',
                    'Descricao': ''
                })
            
            # Vendas columns
            for col in df_vendas.columns:
                dict_data.append({
                    'Tabela': 'Vendas',
                    'Coluna': col,
                    'Tipo': str(df_vendas[col].dtype),
                    'Origem': 'SIMULADO' if col in ['quantidade', 'preco_unitario', 'desconto', 'valor_bruto', 'valor_liquido'] else 'DIMENSÃO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            # Estoque columns
            for col in df_estoque.columns:
                dict_data.append({
                    'Tabela': 'Estoque',
                    'Coluna': col,
                    'Tipo': str(df_estoque[col].dtype),
                    'Origem': 'SIMULADO' if col in ['estoque_inicial', 'entradas', 'saidas', 'estoque_final'] else 'DIMENSÃO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            # Lojas columns
            for col in df_lojas.columns:
                dict_data.append({
                    'Tabela': 'Lojas',
                    'Coluna': col,
                    'Tipo': str(df_lojas[col].dtype),
                    'Origem': 'SIMULADO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            df_dict = pd.DataFrame(dict_data)
            df_dict.to_excel(writer, sheet_name='Dicionario_Dados', index=False)
            print(f"  Dicionario_Dados: {len(df_dict)} rows")
        
        # CANNONDALE_IMAGENS.xlsx
        images_file = EXCEL_DIR / "CANNONDALE_IMAGENS.xlsx"
        print(f"\nCreating {images_file}...")
        
        # Get images from images database
        img_conn = pg8000.connect(
            host=os.getenv("PGIMAGES_HOST", "localhost"),
            port=int(os.getenv("PGIMAGES_PORT", "5434")),
            database=os.getenv("PGIMAGES_DATABASE", "cannondale_images"),
            user=os.getenv("PGIMAGES_USER", "postgres"),
            password=os.getenv("PGIMAGES_PASSWORD", "postgres")
        )
        
        df_imagens = pd.read_sql("""
            SELECT 
                id_imagem, id_produto, modelo, categoria, url_produto,
                url_imagem_original, url_imagem_widen, tipo_imagem, imagem_principal,
                nome_arquivo, caminho_local, minio_object_name, minio_bucket,
                hash_md5, tamanho_bytes, largura, altura, formato,
                data_coleta, data_download, status
            FROM images.imagens
            ORDER BY categoria, modelo, imagem_principal DESC, tipo_imagem
        """, img_conn)
        
        with pd.ExcelWriter(images_file, engine='openpyxl') as writer:
            df_imagens.to_excel(writer, sheet_name='Imagens', index=False)
            print(f"  Imagens: {len(df_imagens)} rows")
            
            # Summary sheet
            summary = df_imagens.groupby(['categoria', 'tipo_imagem', 'status']).agg(
                count=('id_imagem', 'count'),
                total_size_mb=('tamanho_bytes', lambda x: round(x.sum() / (1024*1024), 2))
            ).reset_index()
            summary.to_excel(writer, sheet_name='Resumo_Imagens', index=False)
            print(f"  Resumo_Imagens: {len(summary)} rows")
        
        img_conn.close()
        
        print(f"\n[OK] Excel files created:")
        print(f"  {data_file}")
        print(f"  {images_file}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = export_excel()
    sys.exit(0 if success else 1)