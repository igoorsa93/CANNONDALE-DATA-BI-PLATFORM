#!/usr/bin/env python3
"""
Generate logistics data for the new estrutura
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

MODAIS = ["MARITIMA", "AEREA", "RODOVIARIA"]
STATUS_LOGISTICA = ["Em Processamento", "Em Trânsito", "Entregue", "Atrasado", "Cancelado"]

# Ports and airports for international
PORTS_ORIGIN = [
    ("Porto de Santos", "Santos", "Brasil"),
    ("Porto de Itajaí", "Itajaí", "Brasil"),
    ("Porto de Paranaguá", "Paranaguá", "Brasil"),
    ("Porto de Rotterdam", "Rotterdam", "Holanda"),
    ("Porto de Xangai", "Xangai", "China"),
    ("Porto de Los Angeles", "Los Angeles", "EUA"),
    ("Porto de Hamburgo", "Hamburgo", "Alemanha"),
]

PORTS_DEST = [
    ("Porto de Santos", "Santos", "Brasil"),
    ("Porto de Itajaí", "Itajaí", "Brasil"),
    ("Porto de Salvador", "Salvador", "Brasil"),
    ("Porto de Fortaleza", "Fortaleza", "Brasil"),
    ("Porto de Manaus", "Manaus", "Brasil"),
    ("Porto de Belém", "Belém", "Brasil"),
    ("Porto de Rio Grande", "Rio Grande", "Brasil"),
]

AIRPORTS_ORIGIN = [
    ("GRU - Guarulhos", "São Paulo", "Brasil"),
    ("VCP - Viracopos", "Campinas", "Brasil"),
    ("GIG - Galeão", "Rio de Janeiro", "Brasil"),
    ("BSB - Brasília", "Brasília", "Brasil"),
    ("Schiphol", "Amsterdã", "Holanda"),
    ("Frankfurt", "Frankfurt", "Alemanha"),
    ("Charles de Gaulle", "Paris", "França"),
    ("Heathrow", "Londres", "Reino Unido"),
    ("Narita", "Tóquio", "Japão"),
    ("LAX - Los Angeles", "Los Angeles", "EUA"),
    ("JFK - Nova York", "Nova York", "EUA"),
]

AIRPORTS_DEST = AIRPORTS_ORIGIN  # Same airports

TRANSPORTADORAS = [
    "Maersk", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO",  # Marítimas
    "LATAM Cargo", "GOLLOG", "Azul Cargo", "FedEx", "UPS", "DHL",  # Aéreas
    "Jamef", "Rodonaves", "Translovato", "Sider", "Gontijo",  # Rodoviárias
]

def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5433,
        database="cannondale",
        user="postgres",
        password="postgres"
    )

def main():
    conn = pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )
    cur = conn.cursor()
    
    try:
        # Clear existing logistics
        cur.execute("DELETE FROM logistica")
        conn.commit()
        
        # Get all stores
        cur.execute("SELECT id_loja, nome_loja, cidade, estado_provincia, pais FROM lojas")
        stores = cur.fetchall()
        print(f"Found {len(stores)} stores")
        
# Get all products
        cur.execute("SELECT id_produto, preco_site, categoria, modelo FROM contexto WHERE preco_site > 0")
        products = cur.fetchall()
        print(f"Found {len(products)} products")
        
        # Get date range from sales
        cur.execute("SELECT MIN(data_venda), MAX(data_venda) FROM vendas")
        date_range = cur.fetchone()
        if not date_range or not date_range[0]:
            print("No sales data found")
            return
        
        start_date, end_date = date_range
        print(f"Date range: {start_date} to {end_date}")
        
        # Clear existing logistics
        cur.execute("DELETE FROM logistica")
        conn.commit()
        
        # Generate logistics records
        # We'll create logistics for restocking based on inventory entradas
        # and some international shipments
        
        batch_size = 1000
        batch = []
        total_records = 0
        
        # Generate international shipments (maritime)
        print("Generating maritime shipments...")
        for _ in range(200):  # 200 maritime shipments over the period
            modal = "MARITIMA"
            port_orig = random.choice(PORTS_ORIGIN)
            port_dest = random.choice(PORTS_DEST)
            transportadora = random.choice([t for t in TRANSPORTADORAS if t in ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO"]])
            
            id_produto = random.choice(products)[0]
            id_loja_dest = random.choice(stores)[0]
            loja_dest = next(s for s in stores if s[0] == id_loja_dest)
            
            quantidade = random.randint(10, 100)
            data_envio = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            tempo_transito = random.randint(20, 45)
            data_prevista = data_envio + timedelta(days=tempo_transito)
            data_entrega = data_prevista + timedelta(days=random.randint(-5, 10))
            
            atrasado = data_entrega > data_prevista
            status = "Atrasado" if atrasado else random.choice(["Entregue", "Em Trânsito"])
            if data_entrega > end_date:
                status = "Em Trânsito"
            
            distancia = random.randint(5000, 20000)
            custo_frete = round(quantidade * random.uniform(50, 200), 2)
            prioridade = random.choice(["Normal", "Baixa"])
            
            # Get product details
            prod_info = next(p for p in products if p[0] == id_produto)
            modelo = prod_info[3]
            categoria = prod_info[2]
            
            batch.append((
                data_envio, data_prevista, data_entrega,
                id_produto, quantidade,
                loja_dest[0], loja_dest[1],
                port_orig[0], port_orig[1], port_orig[2],
                loja_dest[4] if loja_dest[4] != 'Brasil' else port_dest[0],
                loja_dest[2], loja_dest[3],
                modal, transportadora, status,
                distancia, tempo_transito, custo_frete,
                prioridade, f"Shipment {port_orig[1]} -> {port_dest[1]}",
                modelo, categoria
            ))
            # DEBUG
            if len(batch[-1]) != 20:
                print(f"DEBUG maritime tuple length: {len(batch[-1])}")
            total_records += 1
        
        # Generate air shipments
        print("Generating air shipments...")
        for _ in range(150):
            modal = "AEREA"
            air_orig = random.choice(AIRPORTS_ORIGIN)
            air_dest = random.choice(AIRPORTS_DEST)
            transportadora = random.choice([t for t in TRANSPORTADORAS if t in ["LATAM Cargo", "GOLLOG", "Azul Cargo", "FedEx", "UPS", "DHL"]])
            
            id_produto = random.choice(products)[0]
            id_loja_dest = random.choice(stores)[0]
            loja_dest = next(s for s in stores if s[0] == id_loja_dest)
            
            quantidade = random.randint(1, 20)
            data_envio = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            tempo_transito = random.randint(1, 5)
            data_prevista = data_envio + timedelta(days=tempo_transito)
            data_entrega = data_prevista + timedelta(days=random.randint(-1, 2))
            
            atrasado = data_entrega > data_prevista
            status = "Atrasado" if atrasado else random.choice(["Entregue", "Em Trânsito"])
            if data_entrega > end_date:
                status = "Em Trânsito"
            
            # Get product details
            prod_info = next(p for p in products if p[0] == id_produto)
            modelo = prod_info[3]
            categoria = prod_info[2]
            
            distancia = random.randint(2000, 15000)
            custo_frete = round(quantidade * random.uniform(200, 800), 2)
            prioridade = random.choice(["Alta", "Normal", "Normal", "Normal"])
            
            batch.append((
                data_envio, data_prevista, data_entrega,
                id_produto, quantidade,
                loja_dest[0], loja_dest[1],
                air_orig[0], air_orig[1], air_orig[2],
                air_dest[0], air_dest[1], air_dest[2],
                modal, transportadora, status,
                distancia, tempo_transito, custo_frete,
                prioridade, f"Air {air_orig[1]} -> {air_dest[1]}",
                modelo, categoria
            ))
            # DEBUG
            if len(batch[-1]) != 20:
                print(f"DEBUG air tuple length: {len(batch[-1])}")
            total_records += 1
        
        # Generate road shipments (domestic distribution)
        print("Generating road shipments...")
        for _ in range(500):
            modal = "RODOVIARIA"
            # Origin: major distribution centers or ports
            orig_cities = ["São Paulo", "Curitiba", "Porto Alegre", "Belo Horizonte", "Recife", "Salvador", "Fortaleza", "Manaus"]
            dest_cities = [s[1] for s in stores]
            
            transportadora = random.choice([t for t in TRANSPORTADORAS if t in ["Jamef", "Rodonaves", "Translovato", "Sider", "Gontijo"]])
            
            id_produto = random.choice(products)[0]
            id_loja_dest = random.choice(stores)[0]
            loja_dest = next(s for s in stores if s[0] == id_loja_dest)
            
            cidade_origem = random.choice(orig_cities)
            estado_origem = "SP" if cidade_origem == "São Paulo" else "PR" if cidade_origem == "Curitiba" else "RS" if cidade_origem == "Porto Alegre" else "MG" if cidade_origem == "Belo Horizonte" else "PE" if cidade_origem == "Recife" else "BA" if cidade_origem == "Salvador" else "CE" if cidade_origem == "Fortaleza" else "AM"
            pais_origem = "Brasil"
            
            quantidade = random.randint(5, 50)
            data_envio = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
            tempo_transito = random.randint(1, 10)
            data_prevista = data_envio + timedelta(days=tempo_transito)
            data_entrega = data_prevista + timedelta(days=random.randint(-2, 3))
            
            atrasado = data_entrega > data_prevista
            status = "Atrasado" if atrasado else random.choice(["Entregue", "Em Trânsito"])
            if data_entrega > end_date:
                status = "Em Trânsito"
            
            distancia = random.randint(100, 3000)
            custo_frete = round(quantidade * random.uniform(10, 80), 2)
            prioridade = random.choice(["Normal", "Normal", "Alta"])
            
# Get product details
            prod_info = next(p for p in products if p[0] == id_produto)
            modelo = prod_info[3]
            categoria = prod_info[2]
            
            batch.append((
                data_envio, data_prevista, data_entrega,
                id_produto, quantidade,
                loja_dest[0], loja_dest[1],
                f"CD {cidade_origem}", cidade_origem, pais_origem,
                loja_dest[4] if loja_dest[4] != 'Brasil' else cidade_origem,
                loja_dest[2], loja_dest[3],
                modal, transportadora, status,
                distancia, tempo_transito, custo_frete,
                prioridade, f"Road {cidade_origem} -> {loja_dest[2]}",
                modelo, categoria
            ))
            # DEBUG
            if len(batch[-1]) != 20:
                print(f"DEBUG road tuple length: {len(batch[-1])}")
            total_records += 1
         
        # Insert all batches
        print(f"Inserting {total_records} logistics records...")
        cur.executemany("""
            INSERT INTO logistica (
                data_envio, data_prevista, data_entrega,
                id_produto, quantidade,
                id_loja, nome_loja,
                origem, cidade_origem, pais_origem,
                destino, cidade_destino, pais_destino,
                modal, transportadora, status_logistica,
                distancia_km, tempo_transito_dias, custo_frete,
                prioridade, observacao, modelo, categoria
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()
        
        print(f"✅ Logistics generated: {total_records} records")
        
        # Summary
        cur.execute("""
            SELECT modal, COUNT(*) as count, AVG(custo_frete) as custo_medio
            FROM logistica
            GROUP BY modal
        """)
        print("\nLogística por Modal:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} registros, Custo médio: R$ {row[2]:,.2f}")
        
        cur.execute("""
            SELECT status_logistica, COUNT(*) FROM logistica GROUP BY status_logistica
        """)
        print("\nStatus Logística:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
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