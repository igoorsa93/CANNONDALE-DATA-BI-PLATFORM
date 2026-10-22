#!/usr/bin/env python3
"""
Generate inventory data - OPTIMIZED VERSION using in-memory processing
"""
import pg8000
import random
from datetime import date, timedelta

def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5433,
        database="cannondale",
        user="postgres",
        password="postgres"
    )

# Store profile parameters
PERFIL_PARAMS = {
    "Alto Desempenho": {"estoque_base_multiplier": 1.2, "estoque_minimo_pct": 0.15, "estoque_maximo_pct": 0.40, "reposicao_freq": 7},
    "Desempenho Médio": {"estoque_base_multiplier": 1.0, "estoque_minimo_pct": 0.20, "estoque_maximo_pct": 0.50, "reposicao_freq": 14},
    "Baixo Desempenho": {"estoque_base_multiplier": 0.6, "estoque_minimo_pct": 0.10, "estoque_maximo_pct": 0.30, "reposicao_freq": 30},
    "Excesso de Estoque": {"estoque_base_multiplier": 2.5, "estoque_minimo_pct": 0.10, "estoque_maximo_pct": 0.60, "reposicao_freq": 60},
    "Estoque Crítico": {"estoque_base_multiplier": 0.4, "estoque_minimo_pct": 0.25, "estoque_maximo_pct": 0.35, "reposicao_freq": 5},
}

def main():
    conn = pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    
    try:
        # Clear existing inventory
        cur.execute("DELETE FROM estoque")
        conn.commit()
        
        # Get all stores with profiles
        cur.execute("SELECT id_loja, perfil_desempenho FROM lojas")
        stores = cur.fetchall()
        print(f"Found {len(stores)} stores")
        
        # Get all products
        cur.execute("SELECT id_produto, preco_site FROM contexto WHERE preco_site > 0")
        products = cur.fetchall()
        print(f"Found {len(products)} products")
        
        # Get date range from sales
        cur.execute("SELECT MIN(data_venda), MAX(data_venda) FROM vendas")
        date_range = cur.fetchone()
        if not date_range or not date_range[0]:
            print("No sales data found")
            return
        
        start_date, end_date = date_range
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        print(f"Date range: {start_month} to {end_month}")
        
        # Get MONTHLY sales per store-product
        print("Calculating monthly sales per store-product...")
        cur.execute("""
            SELECT id_loja, id_produto, 
                   EXTRACT(YEAR FROM data_venda)::int as ano,
                   EXTRACT(MONTH FROM data_venda)::int as mes,
                   SUM(quantidade) as vendas_mes
            FROM vendas
            GROUP BY id_loja, id_produto, ano, mes
        """)
        monthly_sales = {}
        for row in cur.fetchall():
            key = (row[0], row[1], row[2], row[3])
            monthly_sales[key] = row[4]
        print(f"  {len(monthly_sales)} store-product-month combinations with sales")
        
        # Build set of store-product combos that have sales at any point
        combos_with_sales = set()
        for (loja, prod, ano, mes) in monthly_sales.keys():
            combos_with_sales.add((loja, prod))
        
        # Also include combos that might need stock (all store-product pairs)
        all_combos = [(s[0], p[0]) for s in stores for p in products]
        print(f"Total store-product combos: {len(all_combos)}")
        
        # Clear existing inventory
        cur.execute("DELETE FROM estoque")
        conn.commit()
        
        # Initialize stock for all combos at start_month
        # Use a dictionary for O(1) lookups
        stock_levels = {}
        combo_params = {}
        
        for id_loja, perfil in stores:
            params = PERFIL_PARAMS.get(perfil, PERFIL_PARAMS["Desempenho Médio"])
            for id_produto, preco in products:
                combo = (id_loja, id_produto)
                
                # Calculate base stock for this combo
                avg_monthly_sales = sum(
                    monthly_sales.get((id_loja, id_produto, a, m), 0)
                    for a in range(start_month.year, end_month.year + 1)
                    for m in range(1, 13)
                ) / max(1, (end_month.year - start_month.year) * 12 + end_month.month - start_month.month + 1)
                
                avg_daily_sales = avg_monthly_sales / 30.0
                
                params_combo = PERFIL_PARAMS.get(perfil, PERFIL_PARAMS["Desempenho Médio"])
                coverage_days = params_combo["reposicao_freq"]
                estoque_base = max(1, int(avg_daily_sales * coverage_days * params_combo["estoque_base_multiplier"]))
                
                estoque_minimo = max(1, int(estoque_base * params_combo["estoque_minimo_pct"]))
                estoque_maximo = max(estoque_minimo + 1, int(estoque_base * params_combo["estoque_maximo_pct"]))
                ponto_reposicao = estoque_minimo + max(1, int(avg_daily_sales * 3))
                
                combo_params[combo] = {
                    "params": params_combo,
                    "estoque_base": estoque_base,
                    "estoque_minimo": estoque_minimo,
                    "estoque_maximo": estoque_maximo,
                    "ponto_reposicao": ponto_reposicao,
                    "avg_daily_sales": avg_monthly_sales / 30.0,
                    "avg_monthly_sales": avg_monthly_sales
                }
                
                # Initial stock
                stock_levels[combo] = max(estoque_minimo, int(estoque_base * random.uniform(0.8, 1.3)))
        
        print(f"Initialized stock for {len(stock_levels)} combos")
        
        # Process each month
        batch_size = 5000
        batch = []
        total_records = 0
        
        current_date = start_month
        while current_date <= end_month:
            ano = current_date.year
            mes = current_date.month
            
            print(f"Processing {ano}-{mes:02d}...")
            
            for combo in all_combos:
                id_loja, id_produto = combo
                cp = combo_params[combo]
                
                estoque_minimo = cp["estoque_minimo"]
                estoque_maximo = cp["estoque_maximo"]
                ponto_reposicao = cp["ponto_reposicao"]
                avg_daily_sales = cp["avg_daily_sales"]
                params_combo = cp["params"]
                
                # Get current stock
                estoque_atual = stock_levels.get(combo, cp["estoque_minimo"])
                
                # Get monthly sales
                vendas_mes = monthly_sales.get((id_loja, id_produto, ano, mes), 0)
                
                # Replenishment logic
                entradas = 0
                if estoque_atual <= ponto_reposicao:
                    entradas = random.randint(
                        max(1, cp["estoque_maximo"] - estoque_atual),
                        max(2, cp["estoque_maximo"] - estoque_atual + 5)
                    )
                
                # Saidas = monthly sales (capped at available stock)
                estoque_inicial = estoque_atual
                max_saidas = estoque_inicial + entradas
                saidas = monthly_sales.get((id_loja, id_produto, ano, mes), 0)
                if saidas > max_saidas:
                    saidas = max_saidas
                
                # Update stock
                estoque_atual = estoque_inicial + entradas - saidas
                
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
                cobertura = int(estoque_atual / max(0.1, cp["avg_daily_sales"])) if cp["avg_daily_sales"] > 0 else 999
                
                # Update stock for next month
                stock_levels[combo] = estoque_atual
                
                data_atualizacao = current_date
                batch.append((
                    id_produto, id_loja, data_atualizacao,
                    estoque_inicial, entradas, saidas, estoque_atual,
                    estoque_minimo, estoque_maximo,
                    classificacao, cobertura, round(giro, 2)
                ))
                
                total_records += 1
                
                if len(batch) >= 5000:
                    cur.executemany("""
                        INSERT INTO estoque (
                            id_produto, id_loja, data_atualizacao,
                            estoque_inicial, entradas, saidas, estoque_atual,
                            estoque_minimo, estoque_maximo,
                            status_estoque, dias_cobertura, giro_estimado
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch)
                    conn.commit()
                    batch = []
                
                total_records += 1
            
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
        
        if batch:
            cur.executemany("""
                INSERT INTO estoque (
                    id_produto, id_loja, data_atualizacao,
                    estoque_inicial, entradas, saidas, estoque_atual,
                    estoque_minimo, estoque_maximo,
                    status_estoque, dias_cobertura, giro_estimado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
        
        print(f"✅ Inventory generated: {total_records} records")
        
        # Summary
        cur.execute("""
            SELECT 
                status_estoque,
                COUNT(*) as count,
                SUM(estoque_atual) as total_estoque,
                AVG(giro_estimado) as giro_medio,
                AVG(dias_cobertura) as cobertura_media
            FROM estoque
            GROUP BY status_estoque
        """)
        print("\nClassificacao de Estoque:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} registros, Estoque: {row[2]}, Giro: {row[3]:.2f}, Cobertura: {row[4]:.0f} dias")
        
        # Verify consistency
        cur.execute("""
            SELECT 
                SUM(e.saidas) as total_vendas_estoque,
                SUM(v.quantidade) as total_vendas_sales
            FROM estoque e
            JOIN vendas v ON v.id_loja = e.id_loja AND v.id_produto = e.id_produto
                AND EXTRACT(YEAR FROM v.data_venda) = EXTRACT(YEAR FROM e.data_atualizacao)
                AND EXTRACT(MONTH FROM v.data_venda) = EXTRACT(MONTH FROM e.data_atualizacao)
        """)
        row = cur.fetchone()
        print(f"\nConsistencia Vendas: Estoque={row[0]}, Sales={row[1]}, Match={row[0]==row[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()