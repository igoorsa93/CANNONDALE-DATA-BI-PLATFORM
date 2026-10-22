import os
from datetime import date, timedelta
from flask import Flask, jsonify, request, send_from_directory, render_template
import psycopg2
import psycopg2.extras

app = Flask(__name__, template_folder="templates", static_folder="static")

DB = {
    "host": os.environ.get("CANNONDALE_DB_HOST", "localhost"),
    "port": int(os.environ.get("CANNONDALE_DB_PORT", "5433")),
    "dbname": os.environ.get("CANNONDALE_DB_NAME", "cannondale"),
    "user": os.environ.get("CANNONDALE_DB_USER", "postgres"),
    "password": os.environ.get("CANNONDALE_DB_PASSWORD", "postgres"),
}

IMAGES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Imagens")


def get_conn():
    return psycopg2.connect(**DB)


def q(sql, params=None, one=False):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/imagens/<path:filename>")
def imagens(filename):
    return send_from_directory(IMAGES_ROOT, filename)


@app.route("/api/health")
def health():
    try:
        q("SELECT 1")
        return jsonify({"status": "ok", "db": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500


@app.route("/api/kpis/overview")
def kpis_overview():
    ultimo_estoque = q(
        "SELECT max(data_atualizacao) AS d FROM public.estoque"
    )[0]["d"]
    ultimo_venda = q(
        "SELECT max(data_venda) AS d FROM public.vendas"
    )[0]["d"]
    ultima = max(ultimo_estoque, ultimo_venda)

    total_produtos = q(
        "SELECT count(*) AS c FROM public.contexto"
    )[0]["c"]

    estoque_total = q(
        "SELECT sum(estoque_atual) AS s FROM public.estoque "
        "WHERE data_atualizacao = %s",
        (ultimo_estoque,),
    )[0]["s"] or 0

    valor_estoque = q(
        "SELECT sum(e.estoque_atual * c.preco_site) AS s "
        "FROM public.estoque e "
        "JOIN public.contexto c ON c.id_produto = e.id_produto "
        "WHERE e.data_atualizacao = %s AND c.preco_site IS NOT NULL",
        (ultimo_estoque,),
    )[0]["s"]

    periodo_ini = (ultima - timedelta(days=90)).isoformat()
    faturamento = q(
        "SELECT sum(valor_liquido) AS s, sum(quantidade) AS u, count(*) AS n "
        "FROM public.vendas WHERE data_venda >= %s",
        (periodo_ini,),
    )[0]

    total_lojas = q("SELECT count(*) AS c FROM public.lojas")[0]["c"]
    movimentos = q("SELECT count(*) AS c FROM public.logistica")[0]["c"]

    entregue = q(
        "SELECT count(*) AS c FROM public.logistica WHERE status_logistica = 'Entregue'"
    )[0]["c"]
    otif = round((entregue / movimentos) * 100, 1) if movimentos else 0

    return jsonify({
        "ultima_atualizacao": ultima.isoformat(),
        "estoque_data": ultimo_estoque.isoformat(),
        "total_produtos": total_produtos,
        "estoque_total_unidades": int(estoque_total),
        "valor_estoque": float(valor_estoque or 0),
        "faturamento_90d": float(faturamento["s"] or 0),
        "unidades_vendidas_90d": int(faturamento["u"] or 0),
        "pedidos_90d": int(faturamento["n"] or 0),
        "total_lojas": total_lojas,
        "movimentos_logistica": movimentos,
        "otif_pct": otif,
    })


@app.route("/api/vendas/mensal")
def vendas_mensal():
    meses = int(request.args.get("meses", "12"))
    ini = (date.today() - timedelta(days=30 * meses)).isoformat()
    rows = q(
        "SELECT to_char(data_venda, 'YYYY-MM') AS mes, "
        "sum(valor_liquido) AS receita, sum(quantidade) AS unidades, count(*) AS pedidos "
        "FROM public.vendas WHERE data_venda >= %s "
        "GROUP BY to_char(data_venda, 'YYYY-MM') ORDER BY mes",
        (ini,),
    )
    return jsonify(rows)


@app.route("/api/vendas/loja")
def vendas_loja():
    rows = q(
        "SELECT nome_loja, cidade, estado_provincia, regiao, pais, "
        "sum(valor_liquido) AS faturamento, sum(quantidade) AS unidades, count(*) AS pedidos "
        "FROM public.vendas GROUP BY nome_loja, cidade, estado_provincia, regiao, pais "
        "ORDER BY faturamento DESC LIMIT 20"
    )
    return jsonify(rows)


@app.route("/api/vendas/categoria")
def vendas_categoria():
    rows = q(
        "SELECT categoria, sum(valor_liquido) AS faturamento, sum(quantidade) AS unidades "
        "FROM public.vendas GROUP BY categoria ORDER BY faturamento DESC"
    )
    return jsonify(rows)


@app.route("/api/produtos")
def produtos():
    busca = request.args.get("busca", "")
    categoria = request.args.get("categoria", "")
    params = []
    conditions = []
    if busca:
        conditions.append("(c.modelo ILIKE %s OR c.id_produto ILIKE %s)")
        params += [f"%{busca}%", f"%{busca}%"]
    if categoria:
        conditions.append("c.categoria = %s")
        params.append(categoria)

    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT c.id_produto, c.modelo, c.categoria, c.subcategoria, c.plataforma,
               c.preco_site, c.moeda, c.url_produto, c.especificacoes, c.tipo_dado,
               i.url_imagem, i.arquivo_local, i.nome_arquivo
        FROM public.contexto c
        LEFT JOIN LATERAL (
            SELECT url_imagem, arquivo_local, nome_arquivo
            FROM public.imagens
            WHERE modelo = c.modelo AND imagem_principal = TRUE
            ORDER BY id_imagem DESC LIMIT 1
        ) i ON TRUE
        {where_sql}
        ORDER BY c.categoria, c.modelo
    """
    rows = q(sql, tuple(params))
    out = []
    for r in rows:
        out.append({
            "id_produto": r["id_produto"],
            "modelo": r["modelo"],
            "categoria": r["categoria"],
            "subcategoria": r["subcategoria"],
            "plataforma": r["plataforma"],
            "preco": float(r["preco_site"]) if r["preco_site"] is not None else None,
            "moeda": r["moeda"],
            "url_produto": r["url_produto"],
            "especificacoes": r["especificacoes"],
            "tipo_dado": r["tipo_dado"],
            "imagem": r["url_imagem"],
            "arquivo_local": r["arquivo_local"],
            "nome_arquivo": r["nome_arquivo"],
        })
    return jsonify(out)


@app.route("/api/produto/<id_produto>")
def produto_detalhe(id_produto):
    p = q(
        "SELECT * FROM public.contexto WHERE id_produto = %s",
        (id_produto,), one=True
    )
    if not p:
        return jsonify({"error": "produto nao encontrado"}), 404
    imgs = q(
        "SELECT tipo_imagem, imagem_principal, url_imagem, arquivo_local, nome_arquivo "
        "FROM public.imagens WHERE modelo = %s ORDER BY imagem_principal DESC, id_imagem",
        (p["modelo"],)
    )
    estoque = q(
        "SELECT sum(estoque_atual) AS total, sum(estoque_minimo) AS minimo "
        "FROM public.estoque WHERE id_produto = %s AND data_atualizacao = "
        "(SELECT max(data_atualizacao) FROM public.estoque)",
        (id_produto,), one=True
    )
    vendas = q(
        "SELECT sum(quantidade) AS unidades, sum(valor_liquido) AS faturamento "
        "FROM public.vendas WHERE id_produto = %s",
        (id_produto,), one=True
    )
    return jsonify({
        "produto": dict(p),
        "imagens": [dict(i) for i in imgs],
        "estoque": dict(estoque) if estoque else None,
        "vendas": dict(vendas) if vendas else None,
    })


@app.route("/api/categorias")
def categorias():
    rows = q("SELECT categoria, count(*) AS total FROM public.contexto GROUP BY categoria ORDER BY categoria")
    return jsonify(rows)


@app.route("/api/estoque/resumo")
def estoque_resumo():
    ultimo = q("SELECT max(data_atualizacao) AS d FROM public.estoque")[0]["d"]
    por_loja = q(
        "SELECT l.nome_loja, l.cidade, l.estado_provincia, l.regiao, "
        "sum(e.estoque_atual) AS unidades, count(*) AS skus "
        "FROM public.estoque e JOIN public.lojas l ON l.id_loja = e.id_loja "
        "WHERE e.data_atualizacao = %s GROUP BY l.nome_loja, l.cidade, l.estado_provincia, l.regiao "
        "ORDER BY unidades DESC",
        (ultimo,),
    )
    por_categoria = q(
        "SELECT e.categoria, sum(e.estoque_atual) AS unidades, count(*) AS skus "
        "FROM public.estoque e WHERE e.data_atualizacao = %s "
        "GROUP BY e.categoria ORDER BY unidades DESC",
        (ultimo,),
    )
    por_status = q(
        "SELECT e.status_estoque AS status, count(*) AS skus, sum(e.estoque_atual) AS unidades "
        "FROM public.estoque e WHERE e.data_atualizacao = %s "
        "GROUP BY e.status_estoque",
        (ultimo,),
    )
    baixo = q(
        "SELECT e.modelo, e.categoria, l.nome_loja, e.estoque_atual, e.estoque_minimo "
        "FROM public.estoque e JOIN public.lojas l ON l.id_loja = e.id_loja "
        "WHERE e.data_atualizacao = %s AND e.estoque_atual <= COALESCE(e.estoque_minimo, 0) "
        "ORDER BY e.estoque_atual ASC LIMIT 30",
        (ultimo,),
    )
    return jsonify({
        "data": ultimo.isoformat(),
        "por_loja": [dict(r) for r in por_loja],
        "por_categoria": [dict(r) for r in por_categoria],
        "por_status": [dict(r) for r in por_status],
        "baixo_estoque": [dict(r) for r in baixo],
    })


@app.route("/api/estoque/serie")
def estoque_serie():
    rows = q(
        "SELECT data_atualizacao AS data, sum(estoque_atual) AS unidades "
        "FROM public.estoque GROUP BY data_atualizacao ORDER BY data_atualizacao"
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/lojas")
def lojas():
    rows = q(
        "SELECT id_loja, nome_loja, tipo_loja, endereco, cidade, estado_provincia, "
        "pais, regiao, continente, cep, latitude, longitude, perfil_desempenho, status_loja, fonte "
        "FROM public.lojas ORDER BY nome_loja"
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/logistica/resumo")
def logistica_resumo():
    por_modal = q(
        "SELECT modal, count(*) AS movimentos, sum(quantidade) AS unidades, "
        "sum(custo_frete) AS custo_total, avg(tempo_transito_dias) AS tempo_medio "
        "FROM public.logistica GROUP BY modal ORDER BY movimentos DESC"
    )
    por_status = q(
        "SELECT status_logistica AS status, count(*) AS movimentos "
        "FROM public.logistica GROUP BY status_logistica ORDER BY movimentos DESC"
    )
    por_transportadora = q(
        "SELECT transportadora, count(*) AS movimentos, sum(custo_frete) AS custo_total, "
        "avg(tempo_transito_dias) AS tempo_medio "
        "FROM public.logistica GROUP BY transportadora ORDER BY movimentos DESC LIMIT 10"
    )
    atraso = q(
        "SELECT avg(CASE WHEN data_entrega IS NOT NULL AND data_prevista IS NOT NULL THEN (data_entrega - data_prevista)::numeric END) AS atraso_medio, "
        "count(*) FILTER (WHERE data_entrega IS NOT NULL AND data_prevista IS NOT NULL AND data_entrega > data_prevista) AS atrasados, "
        "count(*) AS total "
        "FROM public.logistica"
    )[0]
    return jsonify({
        "por_modal": [dict(r) for r in por_modal],
        "por_status": [dict(r) for r in por_status],
        "por_transportadora": [dict(r) for r in por_transportadora],
        "atraso_medio": float(atraso["atraso_medio"] or 0),
        "atrasados": int(atraso["atrasados"] or 0),
        "total": int(atraso["total"] or 0),
    })


@app.route("/api/logistica/movimentos")
def logistica_movimentos():
    rows = q(
        "SELECT data_envio, data_prevista, data_entrega, id_produto, modelo, categoria, "
        "quantidade, nome_loja, origem, cidade_origem, destino, cidade_destino, "
        "modal, transportadora, status_logistica, distancia_km, tempo_transito_dias, "
        "custo_frete, prioridade "
        "FROM public.logistica ORDER BY data_envio DESC NULLS LAST, id_logistica DESC LIMIT 100"
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/vendas/detalhe")
def vendas_detalhe():
    limit = int(request.args.get("limit", "100"))
    rows = q(
        "SELECT data_venda, id_produto, modelo, categoria, quantidade, preco_unitario, "
        "desconto, valor_bruto, valor_liquido, nome_loja, cidade, estado_provincia, "
        "canal_venda, forma_pagamento, status_venda "
        "FROM public.vendas ORDER BY data_venda DESC, id_venda DESC LIMIT %s",
        (limit,),
    )
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
