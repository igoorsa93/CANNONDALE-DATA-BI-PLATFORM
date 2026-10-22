#!/usr/bin/env python3
"""Consultas rápidas no schema simplificado (core)."""
import psycopg2
import sys

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="cannondale",
    user="postgres", password="postgres"
)

queries = {
    "vendas_por_mes": """
        SELECT d.mes_ano, SUM(v.valor_liquido) AS receita, SUM(v.quantidade) AS unids
        FROM core.fato_vendas v
        JOIN core.dim_data d ON d.id_data = v.id_data
        GROUP BY d.mes_ano ORDER BY d.mes_ano;
    """,
    "top_produtos": """
        SELECT p.modelo, SUM(v.valor_liquido) AS receita, SUM(v.quantidade) AS qtd
        FROM core.fato_vendas v
        JOIN core.dim_produto p ON p.id_produto = v.id_produto
        GROUP BY p.modelo ORDER BY receita DESC LIMIT 10;
    """,
    "estoque_por_loja": """
        SELECT l.nome_loja, e.classificacao, COUNT(*) AS skus, SUM(e.estoque_final) AS total
        FROM core.fato_estoque e
        JOIN core.dim_loja l ON l.id_loja = e.id_loja
        GROUP BY l.nome_loja, e.classificacao ORDER BY l.nome_loja, e.classificacao;
    """,
    "loja_resumo": """
        SELECT nome_loja, total_vendas, total_estoque, ultima_atualizacao
        FROM core.dim_loja_resumo r
        JOIN core.dim_loja l ON l.id_loja = r.id_loja
        ORDER BY total_vendas DESC;
    """,
}

if __name__ == "__main__":
    with conn.cursor() as cur:
        for name, sql in queries.items():
            print(f"\n=== {name} ===")
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            for row in cur.fetchall():
                print(dict(zip(cols, row)))
    conn.close()