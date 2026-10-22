#!/usr/bin/env python3
"""
Generate simulated inventory mathematically consistent with sales
- Estoque_Atual = Estoque_Inicial + Entradas - Saídas
- Saídas = Vendas correspondentes
- Status: Crítico, Atenção, Normal, Excesso
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
        "estoque_base_multiplier": 1.2,  # More stock for high demand
        "estoque_minimo_pct": 0.15,
        "estoque_maximo_pct": 0.40,
        "reposicao_freq": 7,  # days
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
    return result[0] if result else None

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
        
        # Get date range from sales
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
        
        # For each store-product combination, calculate initial stock and track over time
        batch_size = 5000
        batch = []
        total_records = 0
        
        # Pre-calculate daily sales per store-product
        print("Calculating daily sales per store-product...")
        cur.execute("""
            SELECT v.id_loja, v.id_produto, d.data, SUM(v.quantidade) as vendas_dia
            FROM fact.fato_vendas v
            JOIN dim.dim_data d ON d.id_data = v.id_data
            WHERE v.tipo_dado = 'SIMULADO'
            GROUP BY v.id_loja, v.id_produto, d.data
        """)
        daily_sales = {}
        for row in cur.fetchall():
            key = (row[0], row[1], row[2])
            daily_sales[key] = row[3]
        
        print(f"  {len(daily_sales)} store-product-day combinations with sales")
        
        # Process each store-product combination
        for id_loja, perfil in stores:
            params = PERFIL_PARAMS.get(perfil, PERFIL_PARAMS["Desempenho Médio"])
            
            for id_produto, preco in products:
                # Calculate base stock level based on average daily sales
                # Get average daily sales for this store-product
                sales_for_combo = [
                    v for k, v in daily_sales.items() 
                    if k[0] == id_loja and k[1] == id_produto
                ]
                avg_daily_sales = sum(sales_for_combo) / max(1, len(sales_for_combo)) if sales_for_combo else 0
                
                # Base stock = avg daily sales * coverage days * multiplier
                coverage_days = params["reposicao_freq"]
                estoque_base = max(1, int(avg_daily_sales * coverage_days * params["estoque_base_multiplier"]))
                
                # Min/Max levels
                estoque_minimo = max(1, int(estoque_base * params["estoque_minimo_pct"]))
                estoque_maximo = max(estoque_minimo + 1, int(estoque_base * params["estoque_maximo_pct"]))
                ponto_reposicao = estoque_minimo + max(1, int(avg_daily_sales * 3))
                
                # Initial stock (random around base)
                estoque_atual = max(estoque_minimo, int(estoque_base * random.uniform(0.8, 1.3)))
                
                # Track inventory day by day
                current_date = start_date
                while current_date <= end_date:
                    id_data = get_dim_data_id(conn, current_date)
                    if not id_data:
                        current_date += timedelta(days=1)
                        continue
                    
                    # Get sales for this day
                    vendas_dia = daily_sales.get((id_loja, id_produto, current_date), 0)
                    
                    # Calculate replenishment
                    entradas = 0
                    if current_date.weekday() == 0:  # Monday replenishment check
                        if estoque_atual <= ponto_reposicao:
                            # Order up to max
                            entradas = random.randint(estoque_maximo - estoque_atual, estoque_maximo - estoque_atual + 5)
                    
                    # Saidas = sales
                    saidas = vendas_dia
                    
                    # Update stock
                    estoque_inicial = estoque_atual
                    estoque_atual = estoque_inicial + entradas - saidas
                    estoque_atual = max(0, estoque_atual)  # No negative stock
                    
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
                    giro = (saidas / max(1, (estoque_inicial + estoque_atual) / 2)) * 30 if (estoque_inicial + estoque_atual) > 0 else 0
                    cobertura = int(estoque_atual / max(0.1, avg_daily_sales)) if avg_daily_sales > 0 else 999
                    
                    batch.append((
                        id_data, id_loja, id_produto,
                        estoque_inicial, entradas, saidas, 0,  # transferencias = 0
                        vendas_dia, estoque_atual,
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
                    
                    current_date += timedelta(days=1)
                
                # Progress
                if id_loja % 10 == 1 and id_produto == products[0][0]:
                    print(f"  Processed store {id_loja} ({perfil})")
        
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
        print("\nClassificação de Estoque:")
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
        print(f"\nConsistência Vendas: Estoque={row[0]}, Sales={row[1]}, Match={row[0]==row[1]}")
        
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