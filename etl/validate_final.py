#!/usr/bin/env python3
"""
Run comprehensive validation tests on the new 5-table structure
"""
import os
import sys
import pg8000
import json
from datetime import datetime
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def get_images_db_connection():
    return pg8000.connect(
        host=os.getenv("PGIMAGES_HOST", "localhost"),
        port=int(os.getenv("PGIMAGES_PORT", "5434")),
        database=os.getenv("PGIMAGES_DATABASE", "cannondale_images"),
        user=os.getenv("PGIMAGES_USER", "postgres"),
        password=os.getenv("PGIMAGES_PASSWORD", "postgres")
    )

def run_tests():
    conn = get_db_connection()
    img_conn = get_images_db_connection()
    cur = conn.cursor()
    img_cur = img_conn.cursor()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"pass": 0, "fail": 0, "total": 0}
    }
    
    def add_test(name, passed, message, details=None):
        results["tests"].append({
            "name": name,
            "passed": passed,
            "message": message,
            "details": details
        })
        results["summary"]["total"] += 1
        if passed:
            results["summary"]["pass"] += 1
            print(f"  [OK] {name}: {message}")
        else:
            results["summary"]["fail"] += 1
            print(f"  [FAIL] {name}: {message}")
    
    print("=== RUNNING DATA QUALITY TESTS ===\n")
    
    # ========== CONTEXTO TESTS ==========
    print("[CONTEXTO TESTS]")
    
    cur.execute("SELECT COUNT(*) FROM contexto")
    total_produtos = cur.fetchone()[0]
    add_test(
        "contexto_total_produtos",
        total_produtos == 56,
        f"Total produtos: {total_produtos}"
    )
    
    cur.execute("SELECT COUNT(*) FROM contexto WHERE preco_site IS NULL OR preco_site <= 0")
    invalid_prices = cur.fetchone()[0]
    add_test(
        "contexto_precos_validos",
        invalid_prices == 0,
        f"{invalid_prices} produtos com preços inválidos" if invalid_prices else "Todos os preços válidos"
    )
    
    cur.execute("SELECT COUNT(*) FROM contexto WHERE modelo IS NULL OR modelo = ''")
    empty_names = cur.fetchone()[0]
    add_test(
        "contexto_nomes_nao_vazios",
        empty_names == 0,
        f"{empty_names} produtos sem nome" if empty_names else "Todos têm nomes"
    )
    
    cur.execute("SELECT COUNT(*) FROM contexto WHERE url_produto IS NULL OR url_produto NOT LIKE 'https://www.cannondale.com%'")
    invalid_urls = cur.fetchone()[0]
    add_test(
        "contexto_urls_validas",
        invalid_urls == 0,
        f"{invalid_urls} URLs inválidas" if invalid_urls else "Todas as URLs válidas"
    )
    
    cur.execute("""
        SELECT id_produto, COUNT(*) as cnt 
        FROM contexto 
        GROUP BY id_produto HAVING COUNT(*) > 1
    """)
    dupes = cur.fetchall()
    add_test(
        "contexto_sem_duplicatas",
        len(dupes) == 0,
        f"{len(dupes)} produtos duplicados" if dupes else "Sem duplicatas"
    )
    
    # ========== VENDAS TESTS ==========
    print("\n[VENDAS TESTS]")
    
    cur.execute("SELECT COUNT(*) FROM vendas")
    total_vendas = cur.fetchone()[0]
    add_test(
        "vendas_total_registros",
        total_vendas > 0,
        f"Total vendas: {total_vendas}"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM vendas v
        LEFT JOIN contexto c ON c.id_produto = v.id_produto
        WHERE c.id_produto IS NULL
    """)
    invalid_prod = cur.fetchone()[0]
    add_test(
        "vendas_produtos_existem",
        invalid_prod == 0,
        f"{invalid_prod} vendas com produto inexistente" if invalid_prod else "Todas referenciam produtos válidos"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM vendas v
        LEFT JOIN lojas l ON l.id_loja = v.id_loja
        WHERE l.id_loja IS NULL
    """)
    invalid_loja = cur.fetchone()[0]
    add_test(
        "vendas_lojas_existem",
        invalid_loja == 0,
        f"{invalid_loja} vendas com loja inexistente" if invalid_loja else "Todas referenciam lojas válidas"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM vendas
        WHERE ABS(valor_bruto - (preco_unitario * quantidade)) > 0.01
    """)
    calc_errors = cur.fetchone()[0]
    add_test(
        "vendas_calculo_bruto",
        calc_errors == 0,
        f"{calc_errors} erros de cálculo valor_bruto" if calc_errors else "Cálculos corretos"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM vendas
        WHERE ABS(valor_liquido - (valor_bruto - desconto)) > 0.01
    """)
    liq_errors = cur.fetchone()[0]
    add_test(
        "vendas_calculo_liquido",
        liq_errors == 0,
        f"{liq_errors} erros de cálculo valor_liquido" if liq_errors else "Cálculos corretos"
    )
    
    # ========== ESTOQUE TESTS ==========
    print("\n[ESTOQUE TESTS]")
    
    cur.execute("SELECT COUNT(*) FROM estoque")
    total_estoque = cur.fetchone()[0]
    add_test(
        "estoque_total_registros",
        total_estoque > 0,
        f"Total registros: {total_estoque}"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM estoque e
        LEFT JOIN contexto c ON c.id_produto = e.id_produto
        LEFT JOIN lojas l ON l.id_loja = e.id_loja
        WHERE c.id_produto IS NULL OR l.id_loja IS NULL
    """)
    invalid_refs = cur.fetchone()[0]
    add_test(
        "estoque_referencias_validas",
        invalid_refs == 0,
        f"{invalid_refs} registros com referências inválidas" if invalid_refs else "Todas as referências válidas"
    )
    
    cur.execute("""
        SELECT COUNT(*) FROM estoque
        WHERE estoque_atual != (estoque_inicial + entradas - saidas)
    """)
    calc_errors = cur.fetchone()[0]
    add_test(
        "estoque_calculo_correto",
        calc_errors == 0,
        f"{calc_errors} registros com cálculo incorreto" if calc_errors else "Cálculos corretos (estoque_atual = inicial + entradas - saidas)"
    )
    
    cur.execute("SELECT COUNT(*) FROM estoque WHERE estoque_atual < 0")
    neg_stock = cur.fetchone()[0]
    add_test(
        "estoque_sem_negativos",
        neg_stock == 0,
        f"{neg_stock} registros com estoque negativo" if neg_stock else "Sem estoque negativo"
    )
    
    valid_status = ['Critico', 'Atencao', 'Normal', 'Excesso']
    cur.execute("SELECT DISTINCT status_estoque FROM estoque")
    statuses = [row[0] for row in cur.fetchall()]
    invalid_statuses = [s for s in statuses if s not in valid_status]
    add_test(
        "estoque_status_validos",
        len(invalid_statuses) == 0,
        f"Status inválidos: {invalid_statuses}" if invalid_statuses else "Todos os status válidos"
    )
    
    # Consistency vendas vs estoque (aggregate vendas by month first)
    cur.execute("""
        SELECT 
            SUM(e.saidas) as total_saidas_estoque,
            SUM(v.quantidade_mes) as total_vendas
        FROM estoque e
        JOIN (
            SELECT id_loja, id_produto, DATE_TRUNC('month', data_venda)::date AS mes, SUM(quantidade) as quantidade_mes
            FROM vendas
            GROUP BY id_loja, id_produto, DATE_TRUNC('month', data_venda)
        ) v ON v.id_loja = e.id_loja AND v.id_produto = e.id_produto AND v.mes = e.data_atualizacao
    """)
    row = cur.fetchone()
    vendas_match = row[0] == row[1] if row[0] is not None else True
    add_test(
        "estoque_vendas_consistentes",
        vendas_match,
        f"Saidas estoque ({row[0]}) != Vendas ({row[1]})" if not vendas_match else "Saidas no estoque = Quantidade vendida",
        {"estoque_saidas": row[0], "vendas_quantidade": row[1]}
    )
    
    # ========== LOJAS TESTS ==========
    print("\n[LOJAS TESTS]")
    
    cur.execute("SELECT COUNT(*) FROM lojas")
    total_lojas = cur.fetchone()[0]
    add_test(
        "lojas_total",
        total_lojas > 0,
        f"Total lojas: {total_lojas}"
    )
    
    cur.execute("SELECT COUNT(*) FROM lojas WHERE latitude IS NULL OR longitude IS NULL")
    no_coords = cur.fetchone()[0]
    add_test(
        "lojas_com_coordenadas",
        no_coords == 0,
        f"{no_coords} lojas sem coordenadas" if no_coords else "Todas têm coordenadas"
    )
    
    br_states = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    cur.execute("SELECT DISTINCT estado_provincia FROM lojas WHERE pais = 'Brasil'")
    states = [row[0] for row in cur.fetchall()]
    invalid_states = [s for s in states if s not in br_states]
    add_test(
        "lojas_estados_brasil_validos",
        len(invalid_states) == 0,
        f"Estados inválidos: {invalid_states}" if invalid_states else "Todos estados brasileiros válidos"
    )
    
    # ========== LOGISTICA TESTS ==========
    print("\n[LOGISTICA TESTS]")
    
    cur.execute("SELECT COUNT(*) FROM logistica")
    total_log = cur.fetchone()[0]
    add_test(
        "logistica_total",
        total_log > 0,
        f"Total registros: {total_log}"
    )
    
    cur.execute("SELECT DISTINCT modal FROM logistica")
    modais = [row[0] for row in cur.fetchall()]
    valid_modais = ['MARITIMA', 'AEREA', 'RODOVIARIA', 'FLUVIAL']
    invalid_modais = [m for m in modais if m not in valid_modais]
    add_test(
        "logistica_modais_validos",
        len(invalid_modais) == 0,
        f"Modais inválidos: {invalid_modais}" if invalid_modais else "Todos os modais válidos"
    )
    
    cur.execute("SELECT COUNT(*) FROM logistica WHERE id_produto NOT IN (SELECT id_produto FROM contexto)")
    invalid_prod = cur.fetchone()[0]
    add_test(
        "logistica_produtos_existem",
        invalid_prod == 0,
        f"{invalid_prod} registros com produto inexistente" if invalid_prod else "Todos referenciam produtos válidos"
    )
    
    cur.execute("SELECT COUNT(*) FROM logistica WHERE quantidade <= 0")
    neg_qty = cur.fetchone()[0]
    add_test(
        "logistica_quantidade_positiva",
        neg_qty == 0,
        f"{neg_qty} registros com quantidade <= 0" if neg_qty else "Todas quantidades positivas"
    )
    
    # ========== IMAGENS TESTS ==========
    print("\n[IMAGENS TESTS]")
    
    img_cur = img_conn.cursor()
    img_cur.execute("SELECT COUNT(*) FROM images.imagens")
    total_img = img_cur.fetchone()[0]
    add_test(
        "imagens_total",
        total_img == 105,
        f"Total imagens: {total_img} (esperado: 105)"
    )
    
    img_cur.execute("SELECT COUNT(*) FROM images.imagens WHERE status = 'OK'")
    ok_img = img_cur.fetchone()[0]
    add_test(
        "imagens_status_ok",
        ok_img == 105,
        f"Imagens OK: {ok_img} (esperado: 105)"
    )
    
    img_cur.execute("SELECT COUNT(DISTINCT id_produto) FROM images.imagens WHERE status = 'OK'")
    produtos_com_img = img_cur.fetchone()[0]
    add_test(
        "imagens_produtos_cobertos",
        produtos_com_img == 32,
        f"Produtos com imagem: {produtos_com_img} (esperado: 32)"
    )
    
    img_cur.execute("SELECT hash_md5, COUNT(*) FROM images.imagens WHERE status = 'OK' GROUP BY hash_md5 HAVING COUNT(*) > 1")
    duplicadas = img_cur.fetchall()
    add_test(
        "imagens_sem_duplicatas_hash",
        len(duplicadas) == 0,
        f"{len(duplicadas)} hashes duplicados" if duplicadas else "Sem duplicatas por hash"
    )
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print(f"SUMMARY: {results['summary']['pass']}/{results['summary']['total']} tests passed")
    print(f"FAILED: {results['summary']['fail']}")
    
    # Save results
    output_file = os.getenv("DATA_DIR", ".") + "/quality_report_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
    print(f"\nReport saved to {output_file}")
    
    cur.close()
    conn.close()
    img_cur.close()
    img_conn.close()
    
    return results['summary']['fail'] == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)