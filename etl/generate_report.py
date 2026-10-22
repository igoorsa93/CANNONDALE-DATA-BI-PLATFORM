#!/usr/bin/env python3
"""
Generate final execution report
"""
import os
import sys
import pg8000
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def get_db_connection():
    return pg8000.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5433")),
        database=os.getenv("PGDATABASE", "cannondale"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )

def generate_report():
    conn = get_db_connection()
    cur = conn.cursor()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    print("=== GENERATING FINAL REPORT ===\n")
    
    # CATÁLOGO
    print("[CATALOGO]")
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN tipo_dado = 'OFICIAL' THEN 1 END) as oficial
        FROM dim.dim_produtos WHERE is_active = TRUE
    """)
    row = cur.fetchone()
    report["catalogo"] = {
        "total_produtos": row[0],
        "produtos_oficiais": row[1],
        "por_categoria": {},
        "por_subcategoria": {},
        "por_plataforma": {},
        "novos": 0,  # Would need comparison with previous run
        "atualizados": 0,
        "removidos": 0
    }
    print(f"  Total produtos: {row[0]}")
    print(f"  Oficiais: {row[1]}")
    
    cur.execute("""
        SELECT categoria, COUNT(*) FROM dim.dim_produtos 
        WHERE is_active = TRUE GROUP BY categoria ORDER BY COUNT(*) DESC
    """)
    for cat, cnt in cur.fetchall():
        report["catalogo"]["por_categoria"][cat] = cnt
        print(f"    {cat}: {cnt}")
    
    cur.execute("""
        SELECT subcategoria, COUNT(*) FROM dim.dim_produtos 
        WHERE is_active = TRUE GROUP BY subcategoria ORDER BY COUNT(*) DESC
    """)
    for sub, cnt in cur.fetchall():
        report["catalogo"]["por_subcategoria"][sub] = cnt
    
    cur.execute("""
        SELECT plataforma, COUNT(*) FROM dim.dim_produtos 
        WHERE is_active = TRUE GROUP BY plataforma ORDER BY COUNT(*) DESC
    """)
    for plat, cnt in cur.fetchall():
        report["catalogo"]["por_plataforma"][plat] = cnt
    
    # PREÇOS
    print("\n[PRECOS]")
    cur.execute("""
        SELECT 
            COUNT(*) as com_preco,
            MIN(preco_site) as menor,
            MAX(preco_site) as maior,
            AVG(preco_site) as medio
        FROM dim.dim_produtos WHERE is_active = TRUE AND preco_site > 0
    """)
    row = cur.fetchone()
    report["precos"] = {
        "produtos_com_preco": row[0],
        "menor_preco": float(row[1]) if row[1] else 0,
        "maior_preco": float(row[2]) if row[2] else 0,
        "preco_medio": float(row[3]) if row[3] else 0
    }
    print(f"  Com preço: {row[0]}")
    print(f"  Menor: R$ {row[1]:,.2f}")
    print(f"  Maior: R$ {row[2]:,.2f}")
    print(f"  Médio: R$ {row[3]:,.2f}")
    
    # IMAGENS
    print("\n[IMAGENS]")
    img_conn = pg8000.connect(
        host=os.getenv("PGIMAGES_HOST", "localhost"),
        port=int(os.getenv("PGIMAGES_PORT", "5434")),
        database=os.getenv("PGIMAGES_DATABASE", "cannondale_images"),
        user=os.getenv("PGIMAGES_USER", "postgres"),
        password=os.getenv("PGIMAGES_PASSWORD", "postgres")
    )
    img_cur = img_conn.cursor()
    
    img_cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'OK' THEN 1 END) as ok,
            COUNT(DISTINCT id_produto) as produtos_com_imagem
        FROM images.imagens
    """)
    row = img_cur.fetchone()
    report["imagens"] = {
        "total_imagens": row[0],
        "imagens_ok": row[1],
        "produtos_com_imagem": row[2]
    }
    print(f"  Total: {row[0]}")
    print(f"  OK: {row[1]}")
    print(f"  Produtos com imagem: {row[2]}")
    
    img_cur.execute("""
        SELECT COUNT(*) FROM images.imagens WHERE imagem_principal = TRUE
    """)
    principais = img_cur.fetchone()[0]
    report["imagens"]["imagens_principais"] = principais
    print(f"  Principais: {principais}")
    
    img_cur.execute("""
        SELECT hash_md5, COUNT(*) FROM images.imagens 
        WHERE status = 'OK' GROUP BY hash_md5 HAVING COUNT(*) > 1
    """)
    duplicadas = img_cur.fetchall()
    report["imagens"]["imagens_duplicadas"] = len(duplicadas)
    print(f"  Duplicadas: {len(duplicadas)}")
    
    img_conn.close()
    
    # LOJAS
    print("\n[LOJAS]")
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN pais = 'Brasil' THEN 1 END) as brasil,
            COUNT(CASE WHEN pais != 'Brasil' THEN 1 END) as exterior
        FROM dim.dim_lojas WHERE is_simulated = TRUE
    """)
    row = cur.fetchone()
    report["lojas"] = {
        "total_lojas": row[0],
        "brasil": row[1],
        "exterior": row[2],
        "paises": {},
        "regioes": {}
    }
    print(f"  Total: {row[0]}")
    print(f"  Brasil: {row[1]}")
    print(f"  Exterior: {row[2]}")
    
    cur.execute("""
        SELECT pais, COUNT(*) FROM dim.dim_lojas 
        WHERE is_simulated = TRUE GROUP BY pais ORDER BY COUNT(*) DESC
    """)
    for pais, cnt in cur.fetchall():
        report["lojas"]["paises"][pais] = cnt
    
    cur.execute("""
        SELECT regiao, COUNT(*) FROM dim.dim_lojas 
        WHERE is_simulated = TRUE GROUP BY regiao ORDER BY COUNT(*) DESC
    """)
    for regiao, cnt in cur.fetchall():
        report["lojas"]["regioes"][regiao] = cnt
    
    # VENDAS
    print("\n[VENDAS]")
    cur.execute("""
        SELECT 
            COUNT(*) as total_vendas,
            SUM(quantidade) as unidades,
            SUM(valor_bruto) as bruto,
            SUM(desconto) as descontos,
            SUM(valor_liquido) as liquido,
            AVG(valor_liquido/NULLIF(quantidade,0)) as ticket_medio
        FROM fact.fato_vendas WHERE tipo_dado = 'SIMULADO'
    """)
    row = cur.fetchone()
    report["vendas"] = {
        "total_vendas": row[0],
        "unidades_vendidas": row[1],
        "faturamento_bruto": float(row[2]) if row[2] else 0,
        "descontos": float(row[3]) if row[3] else 0,
        "faturamento_liquido": float(row[4]) if row[4] else 0,
        "ticket_medio": float(row[5]) if row[5] else 0
    }
    print(f"  Total vendas: {row[0]}")
    print(f"  Unidades: {row[1]}")
    print(f"  Bruto: R$ {row[2]:,.2f}")
    print(f"  Descontos: R$ {row[3]:,.2f}")
    print(f"  Líquido: R$ {row[4]:,.2f}")
    print(f"  Ticket médio: R$ {row[5]:,.2f}")
    
    # ESTOQUE
    print("\n[ESTOQUE]")
    cur.execute("""
        SELECT 
            SUM(estoque_final) as total_estoque,
            COUNT(CASE WHEN classificacao_estoque = 'Critico' THEN 1 END) as critico,
            COUNT(CASE WHEN classificacao_estoque = 'Normal' THEN 1 END) as normal,
            COUNT(CASE WHEN classificacao_estoque = 'Excesso' THEN 1 END) as excesso,
            COUNT(CASE WHEN classificacao_estoque = 'Atencao' THEN 1 END) as atencao
        FROM fact.fato_estoque WHERE tipo_dado = 'SIMULADO'
    """)
    row = cur.fetchone()
    report["estoque"] = {
        "estoque_total": row[0],
        "lojas_critico": row[1],
        "lojas_normal": row[2],
        "lojas_excesso": row[3],
        "lojas_atencao": row[4]
    }
    print(f"  Estoque total: {row[0]}")
    print(f"  Crítico: {row[1]}")
    print(f"  Normal: {row[2]}")
    print(f"  Excesso: {row[3]}")
    print(f"  Atenção: {row[4]}")
    
    # Products without movement
    cur.execute("""
        SELECT COUNT(DISTINCT e.id_produto) 
        FROM fact.fato_estoque e
        LEFT JOIN fact.fato_vendas v ON v.id_produto = e.id_produto AND v.id_loja = e.id_loja
        WHERE e.tipo_dado = 'SIMULADO' AND v.id_venda IS NULL
    """)
    sem_giro = cur.fetchone()[0]
    report["estoque"]["produtos_sem_giro"] = sem_giro
    print(f"  Produtos sem giro: {sem_giro}")
    
    # Alta demanda (top 10 by sales)
    cur.execute("""
        SELECT p.modelo, SUM(v.quantidade) as qtd
        FROM fact.fato_vendas v
        JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
        WHERE v.tipo_dado = 'SIMULADO'
        GROUP BY p.modelo ORDER BY qtd DESC LIMIT 10
    """)
    alta_demanda = [{"modelo": r[0], "quantidade": r[1]} for r in cur.fetchall()]
    report["estoque"]["produtos_alta_demanda"] = alta_demanda
    
    # QUALIDADE
    print("\n[QUALIDADE]")
    quality_file = ROOT / "quality_report.json"
    if quality_file.exists():
        with open(quality_file, 'r') as f:
            quality = json.load(f)
        report["qualidade"] = {
            "testes_executados": quality["summary"]["total"],
            "testes_pass": quality["summary"]["pass"],
            "testes_fail": quality["summary"]["fail"],
            "detalhes": quality["tests"]
        }
        print(f"  Testes: {quality['summary']['pass']}/{quality['summary']['total']} PASS")
    else:
        report["qualidade"] = {"testes_executados": 0, "testes_pass": 0, "testes_fail": 0}
        print("  Quality report not found")
    
    # Save report
    report_file = REPORTS_DIR / f"execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Report saved to {report_file}")
    
    conn.close()
    return True

if __name__ == "__main__":
    success = generate_report()
    sys.exit(0 if success else 1)