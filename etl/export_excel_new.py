#!/usr/bin/env python3
"""
Export data to Excel files for Power BI - New 5-table structure
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
            # 1. Contexto (Products)
            df_contexto = pd.read_sql("""
                SELECT 
                    id_produto, nome_produto, modelo, plataforma, categoria, subcategoria,
                    model_code, sku, ano_modelo, cor, tamanho, material_quadro, peso,
                    suspensao, freios, rodas, preco_site, moeda, url_produto,
                    descricao, url_imagem_principal, data_coleta, fonte, status_produto,
                    created_at, updated_at
                FROM contexto
                ORDER BY categoria, subcategoria, plataforma, modelo
            """, conn)
            df_contexto.to_excel(writer, sheet_name='Contexto', index=False)
            print(f"  Contexto: {len(df_contexto)} rows")
            
            # 2. Vendas
            df_vendas = pd.read_sql("""
                SELECT 
                    id_venda, data_venda, id_loja, id_produto, quantidade, preco_unitario,
                    desconto, valor_bruto, valor_liquido, canal_venda, forma_pagamento,
                    status_venda, pais_venda, regiao_venda, created_at
                FROM vendas
                ORDER BY data_venda DESC
            """, conn)
            df_vendas.to_excel(writer, sheet_name='Vendas', index=False)
            print(f"  Vendas: {len(df_vendas)} rows")
            
            # 3. Estoque
            df_estoque = pd.read_sql("""
                SELECT 
                    id_estoque, id_produto, id_loja, data_atualizacao,
                    estoque_inicial, entradas, saidas, estoque_atual,
                    estoque_minimo, estoque_maximo, status_estoque,
                    dias_cobertura, giro_estimado, created_at, updated_at
                FROM estoque
                ORDER BY data_atualizacao DESC, id_loja, id_produto
            """, conn)
            df_estoque.to_excel(writer, sheet_name='Estoque', index=False)
            print(f"  Estoque: {len(df_estoque)} rows")
            
            # 4. Lojas
            df_lojas = pd.read_sql("""
                SELECT 
                    id_loja, nome_loja, tipo_loja, endereco, cidade, estado_provincia, pais,
                    regiao, continente, cep, latitude, longitude, telefone, site,
                    perfil_desempenho, status_loja, fonte, created_at, updated_at
                FROM lojas
                ORDER BY pais, regiao, cidade, nome_loja
            """, conn)
            df_lojas.to_excel(writer, sheet_name='Lojas', index=False)
            print(f"  Lojas: {len(df_lojas)} rows")
            
            # 5. Logistica
            df_logistica = pd.read_sql("""
                SELECT 
                    id_logistica, data_envio, data_prevista, data_entrega,
                    id_produto, quantidade,
                    origem, cidade_origem, pais_origem,
                    destino, cidade_destino, pais_destino,
                    modal, transportadora, status_logistica,
                    distancia_km, tempo_transito_dias, custo_frete,
                    prioridade, observacao, created_at
                FROM logistica
                ORDER BY data_envio DESC
            """, conn)
            df_logistica.to_excel(writer, sheet_name='Logistica', index=False)
            print(f"  Logistica: {len(df_logistica)} rows")
            
            # 6. Dicionário de Dados
            dict_data = []
            
            for col in df_contexto.columns:
                dict_data.append({
                    'Tabela': 'Contexto',
                    'Coluna': col,
                    'Tipo': str(df_contexto[col].dtype),
                    'Origem': 'OFICIAL' if col in ['nome_produto', 'categoria', 'preco_site', 'url_produto', 'modelo'] else 'CALCULADO',
                    'Obrigatorio': 'SIM' if df_contexto[col].notna().all() else 'NÃO',
                    'Descricao': ''
                })
            
            for col in df_vendas.columns:
                dict_data.append({
                    'Tabela': 'Vendas',
                    'Coluna': col,
                    'Tipo': str(df_vendas[col].dtype),
                    'Origem': 'SIMULADO' if col in ['quantidade', 'preco_unitario', 'desconto', 'valor_bruto', 'valor_liquido'] else 'DIMENSÃO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            for col in df_estoque.columns:
                dict_data.append({
                    'Tabela': 'Estoque',
                    'Coluna': col,
                    'Tipo': str(df_estoque[col].dtype),
                    'Origem': 'SIMULADO' if col in ['estoque_inicial', 'entradas', 'saidas', 'estoque_atual'] else 'DIMENSÃO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            for col in df_lojas.columns:
                dict_data.append({
                    'Tabela': 'Lojas',
                    'Coluna': col,
                    'Tipo': str(df_lojas[col].dtype),
                    'Origem': 'SIMULADO',
                    'Obrigatorio': 'SIM',
                    'Descricao': ''
                })
            
            for col in df_logistica.columns:
                dict_data.append({
                    'Tabela': 'Logistica',
                    'Coluna': col,
                    'Tipo': str(df_logistica[col].dtype),
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