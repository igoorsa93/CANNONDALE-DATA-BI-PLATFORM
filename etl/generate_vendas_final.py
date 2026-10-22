#!/usr/bin/env python3
"""
Generate vendas data with new denormalized structure
"""
import pg8000
import random
from datetime import date, timedelta

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
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

# Seasonal multipliers by month
SEASONALITY = {
    1: 0.9, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.1, 6: 1.15,
    7: 1.2, 8: 1.15, 9: 1.05, 10: 1.1, 11: 1.25, 12: 1.3
}

# Store performance multipliers
PERFIL_MULTIPLIERS = {
    "Alto Desempenho": 1.5,
    "Desempenho Médio": 1.0,
    "Baixo Desempenho": 0.4,
    "Excesso de Estoque": 0.3,
    "Estoque Crítico": 1.2,
}

# Category multipliers (affects sales velocity)
CATEGORY_MULTIPLIERS = {
    "Road": 0.8, "Mountain": 1.0, "Electric": 0.5,
    "Gravel": 0.9, "Trail": 1.1, "Cross Country": 0.7,
    "Enduro": 0.6, "E-MTB": 0.5, "E-Road": 0.4,
    "E-Urban": 0.7, "E-Touring": 0.4, "E-Cargo": 0.3,
    "E-Fitness": 0.6, "Fitness": 1.3, "Urban": 1.1,
    "Kids": 1.5, "Cyclocross": 0.4, "Endurance": 0.9,
}

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Clear existing vendas
        cur.execute("DELETE FROM vendas")
        conn.commit()
        
        # Get all stores
        cur.execute("SELECT id_loja, perfil_desempenho, pais, regiao, nome_loja FROM lojas")
        stores = cur.fetchall()
        print(f"Lojas: {len(stores)}")
        
        # Get all products with prices
        cur.execute("SELECT id_produto, preco_site, categoria, modelo FROM contexto WHERE preco_site > 0")
        products = cur.fetchall()
        print(f"Produtos com preço: {len(products)}")
        
        # Generate sales for last 24 months
        end_date = date.today().replace(day=1) - timedelta(days=1)
        start_date = end_date - timedelta(days=730)
        
        total_sales = 0
        batch_size = 1000
        batch = []
        
        current_date = start_date
        while current_date <= end_date:
            seasonal_mult = SEASONALITY.get(current_date.month, 1.0)
            base_daily_sales = random.randint(5, 25)
            daily_sales = int(base_daily_sales * seasonal_mult)
            
            for _ in range(daily_sales):
                # Select store weighted by performance
                store = random.choices(
                    stores,
                    weights=[PERFIL_MULTIPLIERS.get(s[1], 1.0) for s in stores]
                )[0]
                id_loja, perfil, pais, regiao, nome_loja = store
                perfil_mult = PERFIL_MULTIPLIERS.get(perfil, 1.0)
                
                # Select product weighted by category and price
                product = random.choices(
                    products,
                    weights=[
                        CATEGORY_MULTIPLIERS.get(p[2], 1.0) * (1.0 / max(1, float(p[1]) / 10000))
                        for p in products
                    ]
                )[0]
                id_produto, preco_oficial, categoria, modelo = product
                
                quantidade = random.choices([1, 2, 3], weights=[0.85, 0.12, 0.03])[0]
                
                # Price = official price (with small variation ±2%)
                preco_unitario = round(float(preco_oficial) * random.uniform(0.98, 1.02), 2)
                
                # Discount (0-15%)
                desconto_pct = random.choices([0, 0.02, 0.05, 0.08, 0.1, 0.12, 0.15], 
                                             weights=[0.4, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])[0]
                desconto = round(preco_unitario * quantidade * desconto_pct, 2)
                
                valor_bruto = round(preco_unitario * quantidade, 2)
                valor_liquido = round(valor_bruto - desconto, 2)
                
                canal = random.choices(CANAIS, weights=[w for _, w in CANAIS])[0][0]
                forma_pag = random.choices(FORMAS_PAGAMENTO, weights=[w for _, w in FORMAS_PAGAMENTO])[0][0]
                
                batch.append((
                    current_date, id_loja, nome_loja, id_produto, modelo, categoria,
                    '', '', quantidade, preco_unitario, desconto, valor_bruto, valor_liquido,
                    pais, regiao, canal, forma_pag, 'Faturado'
                ))
                
                total_sales += 1
                
                if len(batch) >= 1000:
                    cur.executemany("""
                        INSERT INTO vendas (
                            data_venda, id_loja, nome_loja, id_produto, modelo, categoria,
                            subcategoria, plataforma, quantidade, preco_unitario, desconto,
                            valor_bruto, valor_liquido, pais, regiao, canal_venda, forma_pagamento, status_venda
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch)
                    conn.commit()
                    batch = []
            
            current_date += timedelta(days=1)
            
            if current_date.day == 1:
                print(f"  Processado até {current_date.strftime('%Y-%m')}: {total_sales} vendas")
        
        if batch:
            cur.executemany("""
                INSERT INTO vendas (
                    data_venda, id_loja, nome_loja, id_produto, modelo, categoria,
                    subcategoria, plataforma, quantidade, preco_unitario, desconto,
                    valor_bruto, valor_liquido, pais, regiao, canal_venda, forma_pagamento, status_venda
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
        
        print(f"\n[OK] Vendas geradas: {total_sales} registros")
        
        # Summary
        cur.execute("""
            SELECT 
                COUNT(*) as total_vendas,
                SUM(quantidade) as unidades,
                SUM(valor_bruto) as faturamento_bruto,
                SUM(desconto) as descontos,
                SUM(valor_liquido) as faturamento_liquido,
                AVG(valor_liquido/NULLIF(quantidade,0)) as ticket_medio
            FROM vendas
        """)
        row = cur.fetchone()
        print(f"  Unidades: {row[1]}")
        print(f"  Faturamento Bruto: R$ {row[2]:,.2f}")
        print(f"  Descontos: R$ {row[3]:,.2f}")
        print(f"  Faturamento Líquido: R$ {row[4]:,.2f}")
        print(f"  Ticket Médio: R$ {row[5]:,.2f}")
        
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