#!/usr/bin/env python3
"""
Generate simulated inventory - OPTIMIZED VERSION
Generates monthly snapshots instead of daily records for better performance
"""
import os
import sys
import pg8000
import random
from datetime import date, timedelta
from decimal import Decimal

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

# Store profile parameters
PERFIL_PARAMS = {
    "Alto Desempenho": {
        "estoque_base_multiplier": 1.2,
        "estoque_minimo_pct": 0.15,
        "estoque_maximo_pct": 0.40,
        "reposicao_freq": 7,
    },
    "Desempenho Médio": {
        "estoque_base_multiplier": 1.0,
        "estoque_minimo_pct": 0.20,
        "estoque_maximo_pct": 0.50,
        "reposicao_freq": 14,
    },
    "Baixo Desempenho": {
        "estoque_base_multiplier": 0.6,
        "estoque_minimo_pct": 0.10,
        "estoque_maximo_pct": 0.30,
        "reposicao_freq": 30,
    },
    "Excesso de Estoque": {
        "estoque_base_multiplier": 2.5,
        "estoque_minimo_pct": 0.10,
        "estoque_maximo_pct": 0.60,
        "reposicao_freq": 60,
    },
    "Estoque Crítico": {
        "estoque_base_multiplier": 0.4,
        "estoque_minimo_pct": 0.25,
        "estoque_maximo_pct": 0.35,
        "reposicao_freq": 5,
    },
}

def get_dim_data_id(conn, target_date):
    """Get dim_data id for date"""
    cur = conn.cursor()
    cur.execute("SELECT id_data FROM dim.dim_data WHERE data = %s", (target_date,))
    result = cur.fetchone()
    if result:
        return result[0]
    
    # Create new entry
    id_data = target_date.year * 10000 + target_date.month * 100 + target_date.day
    dia_semana = target_date.weekday() + 1
    nomes_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    nomes_meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    cur.execute("""
        INSERT INTO dim.dim_data (id_data, data, ano, mes, dia, trimestre, semestre,
                                  semana_ano, dia_semana, nome_dia_semana, nome_mes,
                                  mes_ano, trimestre_ano, eh_fim_semana)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id_data) DO NOTHING
    """, (
        id_data, target_date, target_date.year, target_date.month, target_date.day,
        (target_date.month - 1) // 3 + 1,
        1 if target_date.month <= 6 else 2,
        target_date.isocalendar()[1],
        dia_semana, nomes_dias[dia_semana - 1], nomes_meses[target_date.month],
        f"{target_date.year}-{target_date.month:02d}",
        f"{target_date.year}-T{(target_date.month - 1) // 3 + 1}",
        dia_semana >= 6
    ))
    conn.commit()
    return id_data

def generate_inventory():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get all stores with profiles
        cur.execute("""
            SELECT id_loja, perfil_desempenho FROM dim.dim_lojas WHERE is_simulated = TRUE
        """)
        stores = cur.fetchall()
        print(f"Found {len(stores)} stores")
        
        # Get all products
        cur.execute("SELECT id_produto, preco_site FROM dim.dim_produtos WHERE is_active = TRUE")
        products = cur.fetchall()
        print(f"Found {len(products)} products")
        
        # Get date range from sales (monthly granularity)
        cur.execute("""
            SELECT MIN(d.data), MAX(d.data) 
            FROM fact.fato_vendas v
            JOIN dim.dim_data d ON d.id_data = v.id_data
            WHERE v.tipo_dado = 'SIMULADO'
        """)
        date_range = cur.fetchone()
        if not date_range or not date_range[0]:
            print("No sales data found")
            return False
        
        start_date, end_date = date_range
        print(f"Date range: {start_date} to {end_date}")
        
        # Clear existing simulated inventory
        cur.execute("DELETE FROM fact.fato_estoque WHERE tipo_dado = 'SIMULADO'")
        conn.commit()
        
        # Pre-calculate MONTHLY sales per store-product
        print("Calculating monthly sales per store-product...")
        cur.execute("""
            SELECT v.id_loja, v.id_produto, d.ano, d.mes, SUM(v.quantidade) as vendas_mes
            FROM fact.fato_vendas v
            JOIN dim.dim_data d ON d.id_data = v.id_data
            WHERE v.tipo_dado = 'SIMULADO'
            GROUP BY v.id_loja, v.id_produto, d.ano, d.mes
        """)
        monthly_sales = {}
        for row in cur.fetchall():
            key = (row[0], row[1], row[2], row[3])
            monthly_sales[key] = row[4]
        
        print(f"  {len(monthly_sales)} store-product-month combinations with sales")
        
        # Process each store-product combination - MONTHLY SNAPSHOTS
        batch_size = 5000
        batch = []
        total_records = 0
        
        current_date = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current_date <= end_month:
            id_data = get_dim_data_id(conn, current_date)
            ano = current_date.year
            mes = current_date.month
            
            print(f"Processing {ano}-{mes:02d}...")
            
            for id_loja, perfil in stores:
                params = PERFIL_PARAMS.get(perfil, PERFIL_PARAMS["Desempenho Médio"])
                
                for id_produto, preco in products:
                    # Get monthly sales
                    vendas_mes = monthly_sales.get((id_loja, id_produto, ano, mes), 0)
                    avg_daily_sales = vendas_mes / 30.0
                    
                    # Base stock level
                    coverage_days = params["reposicao_freq"]
                    estoque_base = max(1, int(avg_daily_sales * coverage_days * params["estoque_base_multiplier"]))
                    
                    # Min/Max levels
                    estoque_minimo = max(1, int(estoque_base * params["estoque_minimo_pct"]))
                    estoque_maximo = max(estoque_minimo + 1, int(estoque_base * params["estoque_maximo_pct"]))
                    ponto_reposicao = estoque_minimo + max(1, int(avg_daily_sales * 3))
                    
                    # Stock varies monthly
                    if current_date == start_date.replace(day=1):
                        # First month - initial stock
                        estoque_atual = max(estoque_minimo, int(estoque_base * random.uniform(0.8, 1.3)))
                    else:
                        # Subsequent months - evolve from previous
                        # Get previous month's final stock
                        prev_date = (current_date - timedelta(days=1)).replace(day=1)
                        cur.execute("""
                            SELECT estoque_final FROM fact.fato_estoque
                            WHERE id_loja = %s AND id_produto = %s AND id_data = (
                                SELECT id_data FROM dim.dim_data WHERE data = %s
                            ) AND tipo_dado = 'SIMULADO'
                        """, (id_loja, id_produto, prev_date))
                        prev_result = cur.fetchone()
                        if prev_result:
                            estoque_atual = prev_result[0]
                        else:
                            estoque_atual = max(estoque_minimo, int(estoque_base * random.uniform(0.8, 1.3)))
                    
                    # Replenishment logic
                    entradas = 0
                    if estoque_atual <= ponto_reposicao:
                        entradas = random.randint(
                            max(1, estoque_maximo - estoque_atual),
                            max(2, estoque_maximo - estoque_atual + 5)
                        )
                    
                    # Saidas = monthly sales
                    saidas = vendas_mes
                    
                    # Update stock
                    estoque_inicial = estoque_atual
                    estoque_atual = estoque_inicial + entradas - saidas
                    estoque_atual = max(0, estoque_atual)
                    
                    # Classify stock status
                    if estoque_atual <= estoque_minimo:
                        classificacao = "Critico"
                    elif estoque_atual <= ponto_reposicao:
                        classificacao = "Atencao"
                    elif estoque_atual >= estoque_maximo:
                        classificacao = "Excesso"
                    else:
                        classificacao = "Normal"
                    
                    # Calculate turnover and coverage
                    giro = (saidas / max(1, (estoque_inicial + estoque_atual) / 2)) * 12 if (estoque_inicial + estoque_atual) > 0 else 0
                    cobertura = int(estoque_atual / max(0.1, avg_daily_sales)) if avg_daily_sales > 0 else 999
                    
                    batch.append((
                        id_data, id_loja, id_produto,
                        estoque_inicial, entradas, saidas, 0,
                        vendas_mes, estoque_atual,
                        estoque_minimo, estoque_maximo, ponto_reposicao,
                        classificacao, round(giro, 2), cobertura, 'SIMULADO'
                    ))
                    
                    total_records += 1
                    
                    if len(batch) >= batch_size:
                        cur.executemany("""
                            INSERT INTO fact.fato_estoque (
                                id_data, id_loja, id_produto,
                                estoque_inicial, entradas, saidas, transferencias,
                                vendas, estoque_final,
                                estoque_minimo, estoque_maximo, ponto_reposicao,
                                classificacao_estoque, giro_estoque, cobertura_dias, tipo_dado
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, batch)
                        conn.commit()
                        batch = []
            
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
        
        # Insert remaining
        if batch:
            cur.executemany("""
                INSERT INTO fact.fato_estoque (
                    id_data, id_loja, id_produto,
                    estoque_inicial, entradas, saidas, transferencias,
                    vendas, estoque_final,
                    estoque_minimo, estoque_maximo, ponto_reposicao,
                    classificacao_estoque, giro_estoque, cobertura_dias, tipo_dado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
        
        print(f"[OK] Inventory generated: {total_records} records")
        
        # Summary
        cur.execute("""
            SELECT 
                classificacao_estoque,
                COUNT(*) as count,
                SUM(estoque_final) as total_estoque,
                AVG(giro_estoque) as giro_medio,
                AVG(cobertura_dias) as cobertura_media
            FROM fact.fato_estoque WHERE tipo_dado = 'SIMULADO'
            GROUP BY classificacao_estoque
        """)
        print("\nClassificacao de Estoque:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} registros, Estoque: {row[2]}, Giro: {row[3]:.2f}, Cobertura: {row[4]:.0f} dias")
        
        # Verify consistency with sales
        cur.execute("""
            SELECT 
                SUM(e.vendas) as total_vendas_estoque,
                SUM(v.quantidade) as total_vendas_sales
            FROM fact.fato_estoque e
            JOIN fact.fato_vendas v ON v.id_data = e.id_data AND v.id_loja = e.id_loja AND v.id_produto = e.id_produto
            WHERE e.tipo_dado = 'SIMULADO' AND v.tipo_dado = 'SIMULADO'
        """)
        row = cur.fetchone()
        print(f"\nConsistencia Vendas: Estoque={row[0]}, Sales={row[1]}, Match={row[0]==row[1]}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    success = generate_inventory()
    sys.exit(0 if success else 1)