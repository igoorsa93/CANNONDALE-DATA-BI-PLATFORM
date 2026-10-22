#!/usr/bin/env python3
"""
Generate lojas data
"""
import pg8000
import random
from datetime import datetime

def get_db_connection():
    return pg8000.connect(
        host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
    )

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Clear existing lojas
        cur.execute("DELETE FROM lojas")
        conn.commit()
        
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
                ("New York", "NY", "EUA", "América do Norte", 40.7128, -74.0060),
                ("Los Angeles", "CA", "EUA", "América do Norte", 34.0522, -118.2437),
                ("Chicago", "IL", "EUA", "América do Norte", 41.8781, -87.6298),
                ("Houston", "TX", "EUA", "América do Norte", 29.7604, -95.3698),
                ("Toronto", "ON", "Canadá", "América do Norte", 43.6532, -79.3832),
                ("Vancouver", "BC", "Canadá", "América do Norte", 49.2827, -123.1207),
                ("Montreal", "QC", "Canadá", "América do Norte", 45.5017, -73.5673),
                ("Cidade do México", "CDMX", "México", "América do Norte", 19.4326, -99.1332),
                ("Guadalajara", "JAL", "México", "América do Norte", 20.6597, -103.3496),
            ],
            "Europa": [
                ("Londres", "", "Reino Unido", "Europa", 51.5074, -0.1278),
                ("Manchester", "", "Reino Unido", "Europa", 53.4808, -2.2426),
                ("Paris", "", "França", "Europa", 48.8566, 2.3522),
                ("Lyon", "", "França", "Europa", 45.7640, 4.8357),
                ("Berlim", "", "Alemanha", "Europa", 52.5200, 13.4050),
                ("Munique", "", "Alemanha", "Europa", 48.1374, 11.5761),
                ("Hamburgo", "", "Alemanha", "Europa", 53.5511, 9.9937),
                ("Madrid", "", "Espanha", "Europa", 40.4168, -3.7038),
                ("Barcelona", "", "Espanha", "Europa", 41.3851, 2.1734),
                ("Roma", "", "Itália", "Europa", 41.9028, 12.4964),
                ("Milão", "", "Itália", "Europa", 45.4642, 9.1900),
                ("Lisboa", "", "Portugal", "Europa", 38.7223, -9.1393),
                ("Porto", "", "Portugal", "Europa", 41.1579, -8.6291),
                ("Amsterdã", "", "Holanda", "Europa", 52.3676, 4.9041),
            ],
            "Ásia": [
                ("Tóquio", "", "Japão", "Ásia", 35.6762, 139.6503),
                ("Osaka", "", "Japão", "Ásia", 34.6937, 135.5023),
            ],
            "Oceania": [
                ("Sydney", "NSW", "Austrália", "Oceania", -33.8688, 151.2093),
                ("Melbourne", "VIC", "Austrália", "Oceania", -37.8136, 144.9631),
            ],
        }
        
        PERFIS = ["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"]
        PERFIL_WEIGHTS = [0.15, 0.35, 0.25, 0.15, 0.10]
        
        conn = pg8000.connect(
            host="localhost", port=5433, database="cannondale", user="postgres", password="postgres"
        )
        cur = conn.cursor()
        
        # Clear existing lojas
        cur.execute("DELETE FROM lojas")
        conn.commit()
        
        store_id = 1
        
        # Brazil stores
        for regiao, cities in BR_CITIES.items():
            for city, estado, lat, lon in cities:
                    perfil = random.choices(["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"], weights=[0.15, 0.35, 0.25, 0.15, 0.10])[0]
                    tipo_loja = random.choice(["Flagship", "Concept Store", "Dealer Premium", "Dealer Standard", "Outlet"])
                    
                    if tipo_loja == "Flagship":
                        nome = f"Cannondale Flagship {city}"
                    elif tipo_loja == "Concept Store":
                        nome = f"Cannondale Concept {city}"
                    else:
                        nome = f"Cannondale {city}"
                    
                    cur.execute("""
                        INSERT INTO lojas (nome_loja, tipo_loja, cidade, estado_provincia, pais, regiao, continente, latitude, longitude, perfil_desempenho, status_loja, fonte)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        nome, random.choice(["Flagship", "Concept Store", "Dealer Premium", "Dealer Standard", "Outlet"]), city, estado, "Brasil", regiao, "América do Sul",
                        lat, lon, random.choice(["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"]), "Ativa", "SIMULADO"
                    ))
            
            # International stores
            INT_CITIES = {
                "América do Norte": [
                    ("New York", "NY", "EUA", "América do Norte", 40.7128, -74.0060),
                    ("Los Angeles", "CA", "EUA", "América do Norte", 34.0522, -118.2437),
                    ("Chicago", "IL", "EUA", "América do Norte", 41.8781, -87.6298),
                    ("Houston", "TX", "EUA", "América do Norte", 29.7604, -95.3698),
                    ("Toronto", "ON", "Canadá", "América do Norte", 43.6532, -79.3832),
                    ("Vancouver", "BC", "Canadá", "América do Norte", 49.2827, -123.1207),
                    ("Montreal", "QC", "Canadá", "América do Norte", 45.5017, -73.5673),
                    ("Cidade do México", "CDMX", "México", "América do Norte", 19.4326, -99.1332),
                    ("Guadalajara", "JAL", "México", "América do Norte", 20.6597, -103.3496),
                ],
                "Europa": [
                    ("Londres", "", "Reino Unido", "Europa", 51.5074, -0.1278),
                    ("Manchester", "", "Reino Unido", "Europa", 53.4808, -2.2426),
                    ("Paris", "", "França", "Europa", 48.8566, 2.3522),
                    ("Lyon", "", "França", "Europa", 45.7640, 4.8357),
                    ("Berlim", "", "Alemanha", "Europa", 52.5200, 13.4050),
                    ("Munique", "", "Alemanha", "Europa", 48.1374, 11.5761),
                    ("Hamburgo", "", "Alemanha", "Europa", 53.5511, 9.9937),
                    ("Madrid", "", "Espanha", "Europa", 40.4168, -3.7038),
                    ("Barcelona", "", "Espanha", "Europa", 41.3851, 2.1734),
                    ("Roma", "", "Itália", "Europa", 41.9028, 12.4964),
                    ("Milão", "", "Itália", "Europa", 45.4642, 9.1900),
                    ("Lisboa", "", "Portugal", "Europa", 38.7223, -9.1393),
                    ("Porto", "", "Portugal", "Europa", 41.1579, -8.6291),
                    ("Amsterdã", "", "Holanda", "Europa", 52.3676, 4.9041),
                ],
                "Ásia": [
                    ("Tóquio", "", "Japão", "Ásia", 35.6762, 139.6503),
                    ("Osaka", "", "Japão", "Ásia", 34.6937, 135.5023),
                ],
                "Oceania": [
                    ("Sydney", "NSW", "Austrália", "Oceania", -33.8688, 151.2093),
                    ("Melbourne", "VIC", "Austrália", "Oceania", -37.8136, 144.9631),
                ],
            }
            
            for continente, cities in INT_CITIES.items():
                for city_data in cities:
                    city, estado, pais, cont, lat, lon = city_data
                    perfil = random.choices(["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"], weights=[0.15, 0.35, 0.25, 0.15, 0.10])[0]
                    tipo_loja = random.choice(["Flagship", "Concept Store", "Dealer Premium", "Dealer Standard", "Outlet"])
                    
                    if tipo_loja == "Flagship":
                        nome = f"Cannondale Flagship {city}"
                    elif tipo_loja == "Concept Store":
                        nome = f"Cannondale Concept {city}"
                    else:
                        nome = f"Cannondale {city}"
                    
                    cur.execute("""
                        INSERT INTO lojas (nome_loja, tipo_loja, cidade, estado_provincia, pais, regiao, continente, latitude, longitude, perfil_desempenho, status_loja, fonte)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        nome, random.choice(["Flagship", "Concept Store", "Dealer Premium", "Dealer Standard", "Outlet"]), city, estado, pais, continente, continente,
                        lat, lon, random.choice(["Alto Desempenho", "Desempenho Médio", "Baixo Desempenho", "Excesso de Estoque", "Estoque Crítico"]), "Ativa", "SIMULADO"
                    ))
            
            conn.commit()
            print(f"[OK] Lojas geradas")
            
            # Summary
            cur.execute("SELECT pais, COUNT(*) FROM lojas GROUP BY pais ORDER BY COUNT(*) DESC")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")
            
            cur.execute("SELECT perfil_desempenho, COUNT(*) FROM lojas GROUP BY perfil_desempenho")
            print("\nPerfis de desempenho:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")
            
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