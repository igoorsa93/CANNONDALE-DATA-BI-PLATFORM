#!/usr/bin/env python3
"""
Data Quality Validation Agent
Runs comprehensive tests on all data
"""
import os
import sys
import pg8000
import json
from datetime import datetime
from decimal import Decimal

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def run_tests():
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    
    # ========== PRODUCT TESTS ==========
    print("[PRODUCT TESTS]")
    
    # Test 1: No duplicate salsify_id
    cur.execute("""
        SELECT salsify_id, COUNT(*) as cnt 
        FROM dim.dim_produtos 
        GROUP BY salsify_id HAVING COUNT(*) > 1
    """)
    dupes = cur.fetchall()
    add_test(
        "produtos_sem_duplicatas_salsify",
        len(dupes) == 0,
        f"Found {len(dupes)} duplicate salsify_ids" if dupes else "No duplicate salsify_ids",
        {"duplicates": dupes}
    )
    
    # Test 2: No empty model names
    cur.execute("SELECT COUNT(*) FROM dim.dim_produtos WHERE modelo IS NULL OR modelo = ''")
    empty_names = cur.fetchone()[0]
    add_test(
        "produtos_nome_nao_vazio",
        empty_names == 0,
        f"{empty_names} products with empty names" if empty_names else "All products have names"
    )
    
    # Test 3: Prices valid (> 0)
    cur.execute("SELECT COUNT(*) FROM dim.dim_produtos WHERE preco_site IS NULL OR preco_site <= 0")
    invalid_prices = cur.fetchone()[0]
    add_test(
        "produtos_preco_valido",
        invalid_prices == 0,
        f"{invalid_prices} products with invalid prices" if invalid_prices else "All products have valid prices"
    )
    
    # Test 4: Categories valid
    valid_cats = ['Road', 'Mountain', 'Electric', 'Active', 'Gravel', 'Kids', 'Cyclocross', 'Endurance', 'Trail', 'Cross Country', 'Enduro', 'E-MTB', 'E-Road', 'E-Urban', 'E-Touring', 'E-Cargo', 'E-Fitness', 'Fitness', 'Urban']
    cur.execute("SELECT DISTINCT categoria FROM dim.dim_produtos")
    cats = [row[0] for row in cur.fetchall()]
    invalid_cats = [c for c in cats if c not in valid_cats]
    add_test(
        "produtos_categoria_valida",
        len(invalid_cats) == 0,
        f"Invalid categories: {invalid_cats}" if invalid_cats else "All categories valid",
        {"categories": cats}
    )
    
    # Test 5: URLs valid format
    cur.execute("""
        SELECT COUNT(*) FROM dim.dim_produtos 
        WHERE url_produto IS NULL OR url_produto NOT LIKE 'https://www.cannondale.com%'
    """)
    invalid_urls = cur.fetchone()[0]
    add_test(
        "produtos_url_valida",
        invalid_urls == 0,
        f"{invalid_urls} products with invalid URLs" if invalid_urls else "All URLs valid"
    )
    
    # Test 6: Model code not empty
    cur.execute("SELECT COUNT(*) FROM dim.dim_produtos WHERE codigo_modelo IS NULL OR codigo_modelo = ''")
    empty_codes = cur.fetchone()[0]
    add_test(
        "produtos_codigo_modelo_presente",
        empty_codes == 0,
        f"{empty_codes} products missing model code" if empty_codes else "All have model codes"
    )
    
    # ========== IMAGE TESTS ==========
    print("\n[IMAGE TESTS]")
    
    # Test 7: Images linked to existing products
    cur.execute("""
        SELECT COUNT(*) FROM dim.dim_produto_imagens i
        LEFT JOIN dim.dim_produtos p ON p.id_produto = i.id_produto
        WHERE p.id_produto IS NULL
    """)
    orphan_images = cur.fetchone()[0]
    add_test(
        "imagens_vinculadas_produto",
        orphan_images == 0,
        f"{orphan_images} orphan images" if orphan_images else "All images linked to products"
    )
    
    # Test 8: Products have at least one image
    cur.execute("""
        SELECT COUNT(*) FROM dim.dim_produtos p
        LEFT JOIN dim.dim_produto_imagens i ON i.id_produto = p.id_produto
        WHERE p.is_active = TRUE AND i.id_imagem IS NULL
    """)
    products_no_images = cur.fetchone()[0]
    add_test(
        "produtos_com_imagem",
        products_no_images == 0,
        f"{products_no_images} products without images" if products_no_images else "All products have images"
    )
    
    # Test 9: Each product has exactly one principal image
    cur.execute("""
        SELECT p.modelo, COUNT(*) as cnt FROM dim.dim_produtos p
        JOIN dim.dim_produto_imagens i ON i.id_produto = p.id_produto
        WHERE i.imagem_principal = TRUE
        GROUP BY p.modelo HAVING COUNT(*) != 1
    """)
    principal_issues = cur.fetchall()
    add_test(
        "imagem_principal_unica",
        len(principal_issues) == 0,
        f"{len(principal_issues)} products with 0 or >1 principal images" if principal_issues else "Each product has exactly 1 principal image",
        {"issues": principal_issues}
    )
    
    # Test 10: Image files exist locally
    cur.execute("SELECT caminho_local FROM dim.dim_produto_imagens WHERE status = 'OK'")
    paths = [row[0] for row in cur.fetchall()]
    missing_files = [p for p in paths if p and not os.path.exists(p)]
    add_test(
        "arquivos_imagem_existem",
        len(missing_files) == 0,
        f"{len(missing_files)} image files missing" if missing_files else "All image files exist locally"
    )
    
    # ========== SALES TESTS ==========
    print("\n[SALES TESTS]")
    
    # Test 11: All sales reference valid products
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_vendas v
        LEFT JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
        WHERE v.tipo_dado = 'SIMULADO' AND p.id_produto IS NULL
    """)
    invalid_sales_prod = cur.fetchone()[0]
    add_test(
        "vendas_produto_existente",
        invalid_sales_prod == 0,
        f"{invalid_sales_prod} sales with invalid product" if invalid_sales_prod else "All sales reference valid products"
    )
    
    # Test 12: All sales reference valid stores
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_vendas v
        LEFT JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
        WHERE v.tipo_dado = 'SIMULADO' AND l.id_loja IS NULL
    """)
    invalid_sales_store = cur.fetchone()[0]
    add_test(
        "vendas_loja_existente",
        invalid_sales_store == 0,
        f"{invalid_sales_store} sales with invalid store" if invalid_sales_store else "All sales reference valid stores"
    )
    
    # Test 13: Sales calculations correct
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_vendas
        WHERE tipo_dado = 'SIMULADO' 
        AND ABS(valor_bruto - (preco_unitario * quantidade)) > 0.01
    """)
    calc_errors = cur.fetchone()[0]
    add_test(
        "vendas_calculo_bruto_correto",
        calc_errors == 0,
        f"{calc_errors} sales with incorrect valor_bruto calculation" if calc_errors else "All valor_bruto calculations correct"
    )
    
    # Test 14: Valor liquido = bruto - desconto
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_vendas
        WHERE tipo_dado = 'SIMULADO' 
        AND ABS(valor_liquido - (valor_bruto - desconto)) > 0.01
    """)
    liq_errors = cur.fetchone()[0]
    add_test(
        "vendas_calculo_liquido_correto",
        liq_errors == 0,
        f"{liq_errors} sales with incorrect valor_liquido calculation" if liq_errors else "All valor_liquido calculations correct"
    )
    
    # Test 15: No negative quantities
    cur.execute("SELECT COUNT(*) FROM fact.fato_vendas WHERE tipo_dado = 'SIMULADO' AND quantidade <= 0")
    neg_qty = cur.fetchone()[0]
    add_test(
        "vendas_quantidade_positiva",
        neg_qty == 0,
        f"{neg_qty} sales with non-positive quantity" if neg_qty else "All quantities positive"
    )
    
    # ========== INVENTORY TESTS ==========
    print("\n[INVENTORY TESTS]")
    
    # Test 16: Inventory references valid products/stores
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_estoque e
        LEFT JOIN dim.dim_produtos p ON p.id_produto = e.id_produto
        LEFT JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
        WHERE e.tipo_dado = 'SIMULADO' AND (p.id_produto IS NULL OR l.id_loja IS NULL)
    """)
    invalid_inv = cur.fetchone()[0]
    add_test(
        "estoque_referencias_validas",
        invalid_inv == 0,
        f"{invalid_inv} inventory records with invalid references" if invalid_inv else "All inventory references valid"
    )
    
    # Test 17: Estoque_final = inicial + entradas - saidas
    cur.execute("""
        SELECT COUNT(*) FROM fact.fato_estoque
        WHERE tipo_dado = 'SIMULADO' 
        AND estoque_final != (estoque_inicial + entradas - saidas - transferencias)
    """)
    inv_calc_errors = cur.fetchone()[0]
    add_test(
        "estoque_calculo_correto",
        inv_calc_errors == 0,
        f"{inv_calc_errors} inventory records with incorrect calculation" if inv_calc_errors else "All inventory calculations correct"
    )
    
    # Test 18: No negative final stock
    cur.execute("SELECT COUNT(*) FROM fact.fato_estoque WHERE tipo_dado = 'SIMULADO' AND estoque_final < 0")
    neg_stock = cur.fetchone()[0]
    add_test(
        "estoque_nao_negativo",
        neg_stock == 0,
        f"{neg_stock} records with negative final stock" if neg_stock else "No negative stock"
    )
    
    # Test 19: Saidas = Vendas (consistency)
    cur.execute("""
        SELECT 
            SUM(e.vendas) as total_vendas_estoque,
            SUM(v.quantidade) as total_vendas_sales
        FROM fact.fato_estoque e
        JOIN fact.fato_vendas v ON v.id_data = e.id_data AND v.id_loja = e.id_loja AND v.id_produto = e.id_produto
        WHERE e.tipo_dado = 'SIMULADO' AND v.tipo_dado = 'SIMULADO'
    """)
    row = cur.fetchone()
    vendas_match = row[0] == row[1] if row[0] is not None else True
    add_test(
        "estoque_vendas_consistentes",
        vendas_match,
        f"Saidas in inventory ({row[0]}) != Sales quantity ({row[1]})" if not vendas_match else "Inventory sales match sales table",
        {"estoque_vendas": row[0], "sales_quantidade": row[1]}
    )
    
    # Test 20: Classification valid
    valid_class = ['Critico', 'Atencao', 'Normal', 'Excesso']
    cur.execute("SELECT DISTINCT classificacao_estoque FROM fact.fato_estoque WHERE tipo_dado = 'SIMULADO'")
    classes = [row[0] for row in cur.fetchall()]
    invalid_classes = [c for c in classes if c not in valid_class]
    add_test(
        "estoque_classificacao_valida",
        len(invalid_classes) == 0,
        f"Invalid classifications: {invalid_classes}" if invalid_classes else "All classifications valid"
    )
    
    # ========== STORE TESTS ==========
    print("\n[STORE TESTS]")
    
    # Test 21: All stores have coordinates
    cur.execute("SELECT COUNT(*) FROM dim.dim_lojas WHERE is_simulated = TRUE AND (latitude IS NULL OR longitude IS NULL)")
    no_coords = cur.fetchone()[0]
    add_test(
        "lojas_com_coordenadas",
        no_coords == 0,
        f"{no_coords} stores missing coordinates" if no_coords else "All stores have coordinates"
    )
    
    # Test 22: Brazilian stores have valid states
    br_states = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
    cur.execute("SELECT DISTINCT estado FROM dim.dim_lojas WHERE pais = 'Brasil' AND is_simulated = TRUE")
    states = [row[0] for row in cur.fetchall()]
    invalid_states = [s for s in states if s not in br_states]
    add_test(
        "lojas_brasil_estados_validos",
        len(invalid_states) == 0,
        f"Invalid BR states: {invalid_states}" if invalid_states else "All BR states valid"
    )
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print(f"SUMMARY: {results['summary']['pass']}/{results['summary']['total']} tests passed")
    print(f"FAILED: {results['summary']['fail']}")
    
    # Save results
    output_file = os.getenv("DATA_DIR", ".") + "/quality_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved to {output_file}")
    
    cur.close()
    conn.close()
    
    return results['summary']['fail'] == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)