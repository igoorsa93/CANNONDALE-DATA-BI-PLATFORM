#!/usr/bin/env python3
"""
Generate inventory data with HIGH VARIABILITY - realistic min/max/current/outflow
"""
import pg8000
import random
from datetime import date, timedelta

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

# Store profile parameters - MORE VARIABILITY
PERFIL_PARAMS = {
    "Alto Desempenho": {
        "base_multiplier": (1.0, 1.8),      # range instead of fixed
        "min_pct": (0.08, 0.25),            # 8-25% of base
        "max_pct": (0.35, 0.60),            # 35-60% of base
        "reposicao_freq": (5, 10),          # days
        "variabilidade_diaria": 0.35,       # 35% daily variation
    },
    "Desempenho Médio": {
        "base_multiplier": (0.8, 1.4),
        "min_pct": (0.12, 0.30),
        "max_pct": (0.40, 0.70),
        "reposicao_freq": (10, 21),
        "variabilidade_diaria": 0.25,
    },
    "Baixo Desempenho": {
        "base_multiplier": (0.4, 1.0),
        "min_pct": (0.05, 0.18),
        "max_pct": (0.25, 0.50),
        "reposicao_freq": (20, 45),
        "variabilidade_diaria": 0.20,
    },
    "Excesso de Estoque": {
        "base_multiplier": (1.8, 3.5),
        "min_pct": (0.03, 0.15),
        "max_pct": (0.50, 1.00),
        "reposicao_freq": (45, 90),
        "variabilidade_diaria": 0.15,
    },
    "Estoque Crítico": {
        "base_multiplier": (0.2, 0.6),
        "min_pct": (0.15, 0.35),
        "max_pct": (0.25, 0.50),
        "reposicao_freq": (3, 7),
        "variabilidade_diaria": 0.40,
    },
}

# Product velocity categories (affects stock turnover)
VELOCIDADE_PRODUTO = {
    # High velocity - fast movers
    "Trail": 1.5, "Fitness": 1.4, "Urban": 1.3, "Kids": 1.5,
    "Cross Country": 1.2, "Gravel": 1.1, "Endurance": 1.0,
    # Medium velocity
    "Road": 0.9, "Mountain": 1.0, "Trail": 1.1,
    # Low velocity - premium/specialty
    "Electric": 0.5, "E-MTB": 0.5, "E-Road": 0.4,
    "E-Urban": 0.7, "E-Touring": 0.4, "E-Cargo": 0.3,
    "E-Fitness": 0.6, "Cyclocross": 0.5, "Enduro": 0.6,
}

def get_velocidade(categoria, subcategoria, plataforma):
    # Check specific categories first
    for key in VELOCIDADE_PRODUTO:
        if key in str(plataforma) or key in str(categoria) or key in str(subcategoria):
            return VELOCIDADE_PRODUTO[key]
    return 1.0

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

def main():
    conn = pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    
    try:
        # Clear existing inventory
        print("Limpando estoque anterior...")
        cur.execute("DELETE FROM estoque")
        conn.commit()
        
        # Get all stores with profiles
        cur.execute("SELECT id_loja, perfil_desempenho, nome_loja FROM lojas")
        stores = cur.fetchall()
        print(f"Lojas: {len(stores)}")
        
        # Create a dict mapping id_loja to nome_loja
        loja_nomes = {s[0]: s[2] for s in stores}
        
        # Get all products with details
        cur.execute("""
            SELECT id_produto, preco_site, categoria, subcategoria, plataforma, modelo
            FROM contexto WHERE preco_site > 0
        """)
        products = cur.fetchall()
        print(f"Produtos: {len(products)}")
        
        # Get date range from sales
        cur.execute("SELECT MIN(data_venda), MAX(data_venda) FROM vendas")
        date_range = cur.fetchone()
        start_date, end_date = date_range
        start_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        print(f"Período: {start_month} a {end_month}")
        
        # Get MONTHLY sales per store-product
        print("Calculando vendas mensais por loja-produto...")
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
        print(f"  {len(monthly_sales)} combinações com vendas")
        
        # Build ALL store-product combos
        all_combos = [(s[0], p[0]) for s in stores for p in products]
        print(f"Total combos loja-produto: {len(all_combos)}")
        
        # Clear existing inventory
        cur.execute("DELETE FROM estoque")
        conn.commit()
        
        # ============================================================
        # PRE-COMPUTE PARAMETERS FOR EACH COMBO (with high variability)
        # ============================================================
        combo_params = {}
        stock_levels = {}
        
        print("Inicializando parâmetros com variabilidade...")
        
        for id_loja, perfil, nome_loja in stores:
            perfil_config = PERFIL_PARAMS.get(perfil, PERFIL_PARAMS["Desempenho Médio"])
            
            for id_produto, preco, cat, subcat, plat, modelo in products:
                combo = (id_loja, id_produto)
                
                # Base velocity for this product
                velocidade = get_velocidade(cat, subcat, plat)
                
                # Calculate average monthly sales across all months
                total_months = (end_month.year - start_month.year) * 12 + end_month.month - start_month.month + 1
                total_sales = sum(
                    monthly_sales.get((id_loja, id_produto, a, m), 0)
                    for a in range(start_month.year, end_month.year + 1)
                    for m in range(1, 13)
                )
                avg_monthly_sales = total_sales / max(1, total_months)
                avg_daily_sales = (avg_monthly_sales / 30.0) * velocidade
                
                # RANDOMIZE base parameters within ranges
                base_mult = random.uniform(*perfil_config["base_multiplier"])
                min_pct = random.uniform(*perfil_config["min_pct"])
                max_pct = random.uniform(*perfil_config["max_pct"])
                reposicao_freq = random.randint(*perfil_config["reposicao_freq"])
                variabilidade = perfil_config["variabilidade_diaria"]
                
                coverage_days = reposicao_freq
                estoque_base = max(1, int(avg_daily_sales * coverage_days * base_mult))
                
                estoque_minimo = max(1, int(estoque_base * min_pct))
                estoque_maximo = max(estoque_minimo + random.randint(1, 5), int(estoque_base * max_pct))
                ponto_reposicao = estoque_minimo + max(1, int(avg_daily_sales * random.uniform(2, 5)))
                
                combo_params[combo] = {
                    "perfil": perfil,
                    "velocidade": velocidade,
                    "modelo": modelo,
                    "categoria": cat,
                    "nome_loja": nome_loja,
                    "estoque_base": estoque_base,
                    "estoque_minimo": estoque_minimo,
                    "estoque_maximo": estoque_maximo,
                    "ponto_reposicao": ponto_reposicao,
                    "avg_daily_sales": avg_daily_sales,
                    "avg_monthly_sales": avg_monthly_sales,
                    "reposicao_freq": reposicao_freq,
                    "variabilidade": variabilidade,
                    "preco": preco,
                }
                
                # Initial stock with high variability
                stock_levels[combo] = random.randint(
                    max(0, estoque_minimo - 2),
                    estoque_maximo + random.randint(0, 3)
                )
        
        print(f"Parâmetros inicializados para {len(combo_params)} combos")
        
        # ============================================================
        # PROCESS EACH MONTH WITH HIGH VARIABILITY
        # ============================================================
        batch_size = 5000
        batch = []
        total_records = 0
        
        current_date = start_month
        while current_date <= end_month:
            ano = current_date.year
            mes = current_date.month
            
            print(f"Processando {ano}-{mes:02d}...")
            
            for combo in all_combos:
                id_loja, id_produto = combo
                cp = combo_params[combo]
                
                estoque_minimo = cp["estoque_minimo"]
                estoque_maximo = cp["estoque_maximo"]
                ponto_reposicao = cp["ponto_reposicao"]
                avg_daily_sales = cp["avg_daily_sales"]
                variabilidade = cp["variabilidade"]
                
                # Get current stock
                estoque_atual = stock_levels.get(combo, cp["estoque_minimo"])
                
                # Get monthly sales
                vendas_mes = monthly_sales.get((id_loja, id_produto, ano, mes), 0)
                
                # VARIABLE REPLENISHMENT LOGIC
                entradas = 0
                if estoque_atual <= ponto_reposicao:
                    # Variable replenishment quantity
                    necessidade = estoque_maximo - estoque_atual
                    if necessidade > 0:
                        # Random factor 0.8 to 1.5 of need
                        fator = random.uniform(0.8, 1.5)
                        entradas = max(1, int(necessidade * fator))
                        
                        # Sometimes over-order (specially for high performers)
                        if random.random() < 0.15:
                            entradas += random.randint(1, 5)
                
                # VARIABLE SALES/SAIDAS
                # Apply daily variability to monthly sales
                variacao_diaria = random.uniform(1 - variabilidade, 1 + variabilidade)
                saidas_base = vendas_mes
                saidas = max(0, int(saidas_base * variacao_diaria))
                
                # Cap at available stock
                max_saidas = estoque_atual + entradas
                if saidas > max_saidas:
                    saidas = max_saidas
                
                # Update stock
                estoque_inicial = estoque_atual
                estoque_atual = estoque_inicial + entradas - saidas
                estoque_atual = max(0, estoque_atual)
                
                # Classify stock status with some randomness near boundaries
                if estoque_atual <= estoque_minimo:
                    classificacao = "Critico"
                elif estoque_atual <= estoque_minimo * 1.2 and random.random() < 0.3:
                    classificacao = "Atencao"  # Sometimes upgrade near min
                elif estoque_atual <= ponto_reposicao:
                    classificacao = "Atencao"
                elif estoque_atual >= estoque_maximo:
                    classificacao = "Excesso"
                elif estoque_atual >= estoque_maximo * 0.9 and random.random() < 0.2:
                    classificacao = "Excesso"  # Sometimes classify as excess near max
                else:
                    classificacao = "Normal"
                
                # Calculate metrics
                giro = (saidas / max(1, (estoque_inicial + estoque_atual) / 2)) * 12 if (estoque_inicial + estoque_atual) > 0 else 0
                cobertura = int(estoque_atual / max(0.1, avg_daily_sales)) if avg_daily_sales > 0 else 999
                
                # Update stock for next month
                stock_levels[combo] = estoque_atual
                
                data_atualizacao = current_date
                batch.append((
                    id_produto, id_loja, data_atualizacao,
                    estoque_inicial, entradas, saidas, estoque_atual,
                    estoque_minimo, estoque_maximo,
                    classificacao, cobertura, round(giro, 2), cp["modelo"], cp["categoria"], cp["nome_loja"]
                ))
                
                total_records += 1
                
                if len(batch) >= 5000:
                    cur.executemany("""
                        INSERT INTO estoque (
                            id_produto, id_loja, data_atualizacao,
                            estoque_inicial, entradas, saidas, estoque_atual,
                            estoque_minimo, estoque_maximo,
                            status_estoque, dias_cobertura, giro_estimado, modelo, categoria, nome_loja
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    status_estoque, dias_cobertura, giro_estimado, modelo, categoria, nome_loja
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
        
        print(f"\n[OK] Estoque gerado: {total_records} registros")
        
        # Summary with detailed stats
        cur.execute("""
            SELECT 
                status_estoque,
                COUNT(*) as count,
                SUM(estoque_atual) as total_estoque,
                AVG(estoque_atual) as media_estoque,
                MIN(estoque_atual) as min_estoque,
                MAX(estoque_atual) as max_estoque,
                AVG(giro_estimado) as giro_medio,
                AVG(dias_cobertura) as cobertura_media
            FROM estoque
            GROUP BY status_estoque
            ORDER BY total_estoque DESC
        """)
        print("\nClassificação de Estoque:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} regs | Total: {row[2]} | Média: {row[3]:.1f} | Min: {row[4]} | Max: {row[5]} | Giro: {row[6]:.2f} | Cobertura: {row[7]:.0f}d")
        
        # Additional stats: saidas stats
        cur.execute("""
            SELECT 
                AVG(saidas) as media_saidas,
                MIN(saidas) as min_saidas,
                MAX(saidas) as max_saidas,
                AVG(entradas) as media_entradas,
                MIN(entradas) as min_entradas,
                MAX(entradas) as max_entradas
            FROM estoque
        """)
        row = cur.fetchone()
        print(f"\nSaídas: Média={row[0]:.1f} Min={row[1]} Max={row[2]}")
        print(f"Entradas: Média={row[3]:.1f} Min={row[4]} Max={row[5]}")
        
        # Min/Max stats
        cur.execute("""
            SELECT 
                AVG(estoque_minimo) as avg_min,
                MIN(estoque_minimo) as min_min,
                MAX(estoque_minimo) as max_min,
                AVG(estoque_maximo) as avg_max,
                MIN(estoque_maximo) as min_max,
                MAX(estoque_maximo) as max_max
            FROM estoque
        """)
        row = cur.fetchone()
        print(f"\nMínimos: Média={row[0]:.1f} Min={row[1]} Max={row[2]}")
        print(f"Máximos: Média={row[3]:.1f} Min={row[4]} Max={row[5]}")
        
        # Consistency check
        cur.execute("""
            SELECT 
                SUM(e.saidas) as total_saidas_estoque,
                SUM(v.quantidade) as total_vendas_sales
            FROM estoque e
            JOIN vendas v ON v.id_loja = e.id_loja AND v.id_produto = e.id_produto
                AND EXTRACT(YEAR FROM v.data_venda) = EXTRACT(YEAR FROM e.data_atualizacao)
                AND EXTRACT(MONTH FROM v.data_venda) = EXTRACT(MONTH FROM e.data_atualizacao)
        """)
        row = cur.fetchone()
        print(f"\nConsistência Vendas: Estoque={row[0]}, Sales={row[1]}, Match={row[0]==row[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()