#!/usr/bin/env python3
"""
Generate simulated stores for Brazil and International
"""
import os
import sys
import pg8000
import random
from faker import Faker
from datetime import datetime

# Initialize Faker for Brazil and other locales
fake_br = Faker('pt_BR')
fake_us = Faker('en_US')
fake_uk = Faker('en_GB')
fake_de = Faker('de_DE')
fake_fr = Faker('fr_FR')
fake_es = Faker('es_ES')
fake_pt = Faker('pt_PT')
fake_jp = Faker('ja_JP')
fake_au = Faker('en_AU')
fake_mx = Faker('es_MX')
fake_ca = Faker('en_CA')
fake_it = Faker('it_IT')
fake_nl = Faker('nl_NL')

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

# Brazilian cities by region
BR_CITIES = {
    "Norte": [
        ("Belém", "PA", -1.4558, -48.5044),
        ("Manaus", "AM", -3.1190, -60.0217),
        ("Porto Velho", "RO", -8.7612, -63.9036),
        ("Rio Branco", "AC", -9.9748, -67.8243),
        ("Boa Vista", "RR", 2.8198, -60.6733),
        ("Macapá", "AP", 0.0350, -51.0705),
        ("Palmas", "TO", -10.1843, -48.3337),
    ],
    "Nordeste": [
        ("Salvador", "BA", -12.9714, -38.5014),
        ("Fortaleza", "CE", -3.7319, -38.5267),
        ("Recife", "PE", -8.0476, -34.8770),
        ("São Luís", "MA", -2.5307, -44.3068),
        ("Maceió", "AL", -9.6658, -35.7353),
        ("Aracaju", "SE", -10.9472, -37.0731),
        ("João Pessoa", "PB", -7.1195, -34.8450),
        ("Natal", "RN", -5.7945, -35.2110),
        ("Teresina", "PI", -5.0892, -42.8016),
    ],
    "Centro-Oeste": [
        ("Brasília", "DF", -15.7942, -47.8825),
        ("Goiânia", "GO", -16.6869, -49.2648),
        ("Cuiabá", "MT", -15.6014, -56.0979),
        ("Campo Grande", "MS", -20.4697, -54.6201),
    ],
    "Sudeste": [
        ("São Paulo", "SP", -23.5505, -46.6333),
        ("Rio de Janeiro", "RJ", -22.9068, -43.1729),
        ("Belo Horizonte", "MG", -19.9167, -43.9345),
        ("Campinas", "SP", -22.9056, -47.0608),
        ("Santos", "SP", -23.9618, -46.3322),
        ("Vitória", "ES", -20.3155, -40.3128),
        ("Uberlândia", "MG", -18.9186, -48.2772),
        ("Ribeirão Preto", "SP", -21.1775, -47.8103),
        ("Juiz de Fora", "MG", -21.7642, -43.3503),
        ("Sorocaba", "SP", -23.5015, -47.4526),
    ],
    "Sul": [
        ("Curitiba", "PR", -25.4284, -49.2733),
        ("Porto Alegre", "RS", -30.0346, -51.2177),
        ("Florianópolis", "SC", -27.5954, -48.5480),
        ("Joinville", "SC", -26.3044, -48.8456),
        ("Londrina", "PR", -23.3045, -51.1696),
        ("Caxias do Sul", "RS", -29.1682, -51.1794),
        ("Blumenau", "SC", -26.9194, -49.0661),
        ("Ponta Grossa", "PR", -25.0949, -50.1618),
    ],
}

# International cities
INT_CITIES = {
    "América do Norte": [
        ("New York", "NY", "EUA", "América do Norte", 40.7128, -74.0060, fake_us),
        ("Los Angeles", "CA", "EUA", "América do Norte", 34.0522, -118.2437, fake_us),
        ("Chicago", "IL", "EUA", "América do Norte", 41.8781, -87.6298, fake_us),
        ("Houston", "TX", "EUA", "América do Norte", 29.7604, -95.3698, fake_us),
        ("Toronto", "ON", "Canadá", "América do Norte", 43.6532, -79.3832, fake_ca),
        ("Vancouver", "BC", "Canadá", "América do Norte", 49.2827, -123.1207, fake_ca),
        ("Montreal", "QC", "Canadá", "América do Norte", 45.5017, -73.5673, fake_ca),
        ("Cidade do México", "CDMX", "México", "América do Norte", 19.4326, -99.1332, fake_mx),
        ("Guadalajara", "JAL", "México", "América do Norte", 20.6597, -103.3496, fake_mx),
    ],
    "Europa": [
        ("Londres", "", "Reino Unido", "Europa", 51.5074, -0.1278, fake_uk),
        ("Manchester", "", "Reino Unido", "Europa", 53.4808, -2.2426, fake_uk),
        ("Paris", "", "França", "Europa", 48.8566, 2.3522, fake_fr),
        ("Lyon", "", "França", "Europa", 45.7640, 4.8357, fake_fr),
        ("Berlim", "", "Alemanha", "Europa", 52.5200, 13.4050, fake_de),
        ("Munique", "", "Alemanha", "Europa", 48.1374, 11.5761, fake_de),
        ("Hamburgo", "", "Alemanha", "Europa", 53.5511, 9.9937, fake_de),
        ("Madrid", "", "Espanha", "Europa", 40.4168, -3.7038, fake_es),
        ("Barcelona", "", "Espanha", "Europa", 41.3851, 2.1734, fake_es),
        ("Roma", "", "Itália", "Europa", 41.9028, 12.4964, fake_it),
        ("Milão", "", "Itália", "Europa", 45.4642, 9.1900, fake_it),
        ("Lisboa", "", "Portugal", "Europa", 38.7223, -9.1393, fake_pt),
        ("Porto", "", "Portugal", "Europa", 41.1579, -8.6291, fake_pt),
        ("Amsterdã", "", "Holanda", "Europa", 52.3676, 4.9041, fake_nl),
    ],
    "Ásia": [
        ("Tóquio", "", "Japão", "Ásia", 35.6762, 139.6503, fake_jp),
        ("Osaka", "", "Japão", "Ásia", 34.6937, 135.5023, fake_jp),
    ],
    "Oceania": [
        ("Sydney", "NSW", "Austrália", "Oceania", -33.8688, 151.2093, fake_au),
        ("Melbourne", "VIC", "Austrália", "Oceania", -37.8136, 144.9631, fake_au),
    ],
}

STORE_TYPES = ["Flagship", "Concept Store", "Dealer Premium", "Dealer Standard", "Outlet"]
PERFIS = ["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"]
PERFIL_WEIGHTS = [0.15, 0.35, 0.25, 0.15, 0.10]

def generate_br_stores(num_stores=30):
    """Generate Brazilian stores"""
    stores = []
    store_id = 1
    
    for regiao, cities in BR_CITIES.items():
        # Distribute stores across regions (more in Sudeste/Sul)
        region_weights = {
            "Norte": 0.08, "Nordeste": 0.12, "Centro-Oeste": 0.08,
            "Sudeste": 0.45, "Sul": 0.27
        }
        n = max(1, int(num_stores * region_weights.get(regiao, 0.1)))
        
        for _ in range(n):
            city, estado, lat, lon = random.choice(cities)
            perfil = random.choices(PERFIS, weights=PERFIL_WEIGHTS)[0]
            tipo_loja = random.choice(STORE_TYPES)
            
            # Generate store name
            if tipo_loja == "Flagship":
                nome = f"Cannondale Flagship {city}"
            elif tipo_loja == "Concept Store":
                nome = f"Cannondale Concept {city}"
            else:
                nome = f"Cannondale {city} {fake_br.company_suffix()}"
            
            stores.append({
                "id_loja": store_id,
                "nome_loja": nome,
                "tipo_loja": tipo_loja,
                "endereco": fake_br.street_address(),
                "cidade": city,
                "estado": estado,
                "pais": "Brasil",
                "regiao": regiao,
                "continente": "América do Sul",
                "cep": fake_br.postcode(),
                "latitude": round(lat + random.uniform(-0.05, 0.05), 6),
                "longitude": round(lon + random.uniform(-0.05, 0.05), 6),
                "telefone": fake_br.phone_number(),
                "site": f"https://cannondale{city.lower().replace(' ', '')}.com.br",
                "perfil_desempenho": perfil,
                "is_simulated": True,
                "tipo_dado": "SIMULADO"
            })
            store_id += 1
    
    return stores

def generate_int_stores(num_stores=20):
    """Generate international stores"""
    stores = []
    store_id = 1000  # Start from 1000 for international
    
    total_cities = sum(len(cities) for cities in INT_CITIES.values())
    
    for continente, cities in INT_CITIES.items():
        n = max(1, int(num_stores * len(cities) / total_cities))
        
        for _ in range(n):
            city_data = random.choice(cities)
            city, estado, pais, cont, lat, lon, faker = city_data
            perfil = random.choices(PERFIS, weights=PERFIL_WEIGHTS)[0]
            tipo_loja = random.choice(STORE_TYPES)
            
            if tipo_loja == "Flagship":
                nome = f"Cannondale Flagship {city}"
            elif tipo_loja == "Concept Store":
                nome = f"Cannondale Concept {city}"
            else:
                nome = f"Cannondale {city} {faker.company_suffix()}"
            
            stores.append({
                "id_loja": store_id,
                "nome_loja": nome,
                "tipo_loja": tipo_loja,
                "endereco": faker.street_address(),
                "cidade": city,
                "estado": estado,
                "pais": pais,
                "regiao": continente,
                "continente": continente,
                "cep": faker.postcode() if hasattr(faker, 'postcode') else "",
                "latitude": round(lat + random.uniform(-0.05, 0.05), 6),
                "longitude": round(lon + random.uniform(-0.05, 0.05), 6),
                "telefone": faker.phone_number(),
                "site": f"https://cannondale{city.lower().replace(' ', '')}.com",
                "perfil_desempenho": perfil,
                "is_simulated": True,
                "tipo_dado": "SIMULADO"
            })
            store_id += 1
    
    return stores

def load_stores():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Clear existing simulated stores
        cur.execute("DELETE FROM dim.dim_lojas WHERE is_simulated = TRUE")
        
        # Generate stores
        br_stores = generate_br_stores(35)
        int_stores = generate_int_stores(25)
        all_stores = br_stores + int_stores
        
        print(f"Generating {len(all_stores)} stores ({len(br_stores)} Brazil, {len(int_stores)} International)...")
        
        inserted = 0
        for store in all_stores:
            try:
                cur.execute("""
                    INSERT INTO dim.dim_lojas (
                        nome_loja, tipo_loja, endereco, cidade, estado, pais,
                        regiao, continente, cep, latitude, longitude, telefone,
                        site, perfil_desempenho, is_simulated, tipo_dado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    store["nome_loja"], store["tipo_loja"], store["endereco"],
                    store["cidade"], store["estado"], store["pais"],
                    store["regiao"], store["continente"], store["cep"],
                    store["latitude"], store["longitude"], store["telefone"],
                    store["site"], store["perfil_desempenho"],
                    store["is_simulated"], store["tipo_dado"]
                ))
                inserted += 1
            except Exception as e:
                print(f"  Error inserting {store['nome_loja']}: {e}")
        
        conn.commit()
        print(f"[OK] Stores generated: {inserted} inserted")
        
        # Summary
        cur.execute("SELECT pais, COUNT(*) FROM dim.dim_lojas WHERE is_simulated = TRUE GROUP BY pais ORDER BY COUNT(*) DESC")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} stores")
        
        cur.execute("SELECT perfil_desempenho, COUNT(*) FROM dim.dim_lojas WHERE is_simulated = TRUE GROUP BY perfil_desempenho")
        print("\nPerfis de desempenho:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error: {e}")
        return False
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    success = load_stores()
    sys.exit(0 if success else 1)