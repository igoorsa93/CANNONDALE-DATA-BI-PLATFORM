#!/usr/bin/env python3
"""
Generate simulated sales with realistic patterns
- Uses real product prices from official data
- Seasonal patterns
- Store performance profiles
- 12-24 months of history
"""
import os
import sys
import pg8000
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

# Sales channels and weights
CANAIS = [
    ("Loja Física", 0.60),
    ("E-commerce Próprio", 0.25),
    ("Marketplace", 0.10),
    ("B2B/Corporativo", 0.05),
]

# Payment methods and weights
FORMAS_PAGAMENTO = [
    ("PIX", 0.35),
    ("Cartão de Crédito", 0.30),
    ("Cartão de Débito", 0.15),
    ("Boleto", 0.10),
    ("Financiamento", 0.05),
]

# Seasonal multipliers by month (1=Jan, 12=Dec)
SEASONALITY = {
    1: 0.9,   # Jan - summer in Brazil, lower
    2: 0.85,  # Feb - carnival period
    3: 0.95,  # Mar - back to normal
    4: 1.0,   # Apr
    5: 1.1,   # May - Mother's Day
    6: 1.15,  # Jun - winter, bike season
    7: 1.2,   # Jul - winter peak
    8: 1.15,  # Aug - Father's Day
    9: 1.05,  # Sep - spring
    10: 1.1,  # Oct - Children's Day
    11: 1.25, # Nov - Black Friday
    12: 1.3,  # Dec - Christmas
}

# Store performance multipliers
PERFIL_MULTIPLIERS = {
    "Alto Desempenho": 1.5,
    "Desempenho Médio": 1.0,
    "Baixo Desempenho": 0.4,
    "Excesso de Estoque": 0.3,
    "Estoque Crítico": 1.2,
}

# Category multipliers (premium bikes sell less units)
CATEGORY_MULTIPLIERS = {
    "Road": 0.8,
    "Gravel": 0.9,
    "Mountain": 1.0,
    "Trail": 1.1,
    "Cross Country": 0.7,
    "Enduro": 0.6,
    "Electric": 0.5,
    "E-MTB": 0.5,
    "E-Road": 0.4,
    "E-Urban": 0.7,
    "E-Touring": 0.4,
    "E-Cargo": 0.3,
    "E-Fitness": 0.6,
    "Active": 1.2,
    "Fitness": 1.3,
    "Urban": 1.1,
    "Kids": 1.5,
    "Cyclocross": 0.4,
}

def get_dim_data_id(conn, target_date):
    """Get or create dim_data entry"""
    cur = conn.cursor()
    cur.execute("SELECT id_data FROM dim.dim_data WHERE data = %s", (target_date,))
    result = cur.fetchone()
    if result:
        return result[0]
    
    # Create new entry
    id_data = target_date.year * 10000 + target_date.month * 100 + target_date.day
    dia_semana = target_date.weekday() + 1  # 1=Mon, 7=Sun
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

def load_canais_formas(conn):
    """Load dimension tables for channels and payment methods"""
    cur = conn.cursor()
    
    for canal, _ in CANAIS:
        cur.execute("""
            INSERT INTO dim.dim_canais_venda (canal, descricao, tipo_dado)
            VALUES (%s, %s, 'SIMULADO')
            ON CONFLICT (canal) DO NOTHING
        """, (canal, f"Canal de vendas: {canal}"))
    
    for forma, _ in FORMAS_PAGAMENTO:
        cur.execute("""
            INSERT INTO dim.dim_formas_pagamento (forma_pagamento, descricao, tipo_dado)
            VALUES (%s, %s, 'SIMULADO')
            ON CONFLICT (forma_pagamento) DO NOTHING
        """, (forma, f"Forma de pagamento: {forma}"))
    
    conn.commit()

def generate_sales():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Load dimension tables
        load_canais_formas(conn)
        
        # Get all stores
        cur.execute("SELECT id_loja, perfil_desempenho, pais FROM dim.dim_lojas WHERE is_simulated = TRUE")
        stores = cur.fetchall()
        print(f"Found {len(stores)} stores")
        
        # Get all products
        cur.execute("""
            SELECT id_produto, preco_site, categoria, subcategoria, modelo
            FROM dim.dim_produtos 
            WHERE is_active = TRUE AND preco_site > 0
        """)
        products = cur.fetchall()
        print(f"Found {len(products)} products with prices")
        
        # Get canal IDs
        cur.execute("SELECT id_canal, canal FROM dim.dim_canais_venda")
        canais_dict = {row[1]: row[0] for row in cur.fetchall()}
        
        # Get forma_pagamento IDs
        cur.execute("SELECT id_forma_pagamento, forma_pagamento FROM dim.dim_formas_pagamento")
        formas_dict = {row[1]: row[0] for row in cur.fetchall()}
        
        # Generate sales for last 24 months
        end_date = date.today().replace(day=1) - timedelta(days=1)  # Last day of previous month
        start_date = end_date - timedelta(days=730)  # ~24 months
        
        # Clear existing simulated sales
        cur.execute("DELETE FROM fact.fato_vendas WHERE tipo_dado = 'SIMULADO'")
        conn.commit()
        
        total_sales = 0
        batch_size = 1000
        batch = []
        
        current_date = start_date
        while current_date <= end_date:
            id_data = get_dim_data_id(conn, current_date)
            seasonal_mult = SEASONALITY.get(current_date.month, 1.0)
            
            # Number of sales per day varies
            base_daily_sales = random.randint(5, 25)
            daily_sales = int(base_daily_sales * seasonal_mult)
            
            for _ in range(daily_sales):
                # Select store weighted by performance
                store = random.choices(
                    stores, 
                    weights=[PERFIL_MULTIPLIERS.get(s[1], 1.0) for s in stores]
                )[0]
                id_loja, perfil, pais = store
                perfil_mult = PERFIL_MULTIPLIERS.get(perfil, 1.0)
                
                # Select product weighted by category and price
                product = random.choices(
                    products,
                    weights=[
                        CATEGORY_MULTIPLIERS.get(p[2], 1.0) * (1.0 / max(1, float(p[1]) / 10000))
                        for p in products
                    ]
                )[0]
                id_produto, preco_oficial, categoria, subcategoria, modelo = product
                
                # Quantity (mostly 1, sometimes 2-3)
                quantidade = random.choices([1, 2, 3], weights=[0.85, 0.12, 0.03])[0]
                
                # Price = official price (with small variation ±2%)
                preco_unitario = round(float(preco_oficial) * random.uniform(0.98, 1.02), 2)
                
                # Discount (0-15%)
                desconto_pct = random.choices([0, 0.02, 0.05, 0.08, 0.1, 0.12, 0.15], weights=[0.4, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])[0]
                desconto = round(preco_unitario * quantidade * desconto_pct, 2)
                
                valor_bruto = round(preco_unitario * quantidade, 2)
                valor_liquido = round(valor_bruto - desconto, 2)
                
                # Cost (assume 60% of price)
                custo_produto = round(preco_unitario * 0.6 * quantidade, 2)
                margem = round(valor_liquido - custo_produto, 2)
                margem_pct = round(margem / valor_liquido * 100, 2) if valor_liquido > 0 else 0
                
                # Channel and payment
                canal = random.choices(CANAIS, weights=[w for _, w in CANAIS])[0][0]
                forma_pag = random.choices(FORMAS_PAGAMENTO, weights=[w for _, w in FORMAS_PAGAMENTO])[0][0]
                
                batch.append((
                    id_data, store[0], id_produto,
                    canais_dict[canal], formas_dict[forma_pag],
                    quantidade, preco_unitario, desconto, valor_bruto, valor_liquido,
                    custo_produto, margem, margem_pct,
                    'Faturado', 'SIMULADO'
                ))
                
                total_sales += 1
                
                if len(batch) >= batch_size:
                    cur.executemany("""
                        INSERT INTO fact.fato_vendas (
                            id_data, id_loja, id_produto, id_canal, id_forma_pagamento,
                            quantidade, preco_unitario, desconto, valor_bruto, valor_liquido,
                            custo_produto, margem, margem_pct,
                            status, tipo_dado
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch)
                    conn.commit()
                    batch = []
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Progress
            if current_date.day == 1:
                print(f"  Processed up to {current_date.strftime('%Y-%m')}: {total_sales} sales so far")
        
        # Insert remaining
        if batch:
            cur.executemany("""
                INSERT INTO fact.fato_vendas (
                    id_data, id_loja, id_produto, id_canal, id_forma_pagamento,
                    quantidade, preco_unitario, desconto, valor_bruto, valor_liquido,
                    custo_produto, margem, margem_pct,
                    status, tipo_dado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
        
        print(f"[OK] Sales generated: {total_sales} total")
        
        # Summary
        cur.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                SUM(quantidade) as unidades,
                SUM(valor_bruto) as faturamento_bruto,
                SUM(desconto) as descontos,
                SUM(valor_liquido) as faturamento_liquido,
                AVG(valor_liquido/NULLIF(quantidade,0)) as ticket_medio
            FROM fact.fato_vendas WHERE tipo_dado = 'SIMULADO'
        """)
        row = cur.fetchone()
        print(f"  Unidades: {row[1]}")
        print(f"  Faturamento Bruto: R$ {row[2]:,.2f}")
        print(f"  Descontos: R$ {row[3]:,.2f}")
        print(f"  Faturamento Líquido: R$ {row[4]:,.2f}")
        print(f"  Ticket Médio: R$ {row[5]:,.2f}")
        
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
    success = generate_sales()
    sys.exit(0 if success else 1)