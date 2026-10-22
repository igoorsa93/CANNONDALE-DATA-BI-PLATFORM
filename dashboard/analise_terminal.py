#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Análise de dados Cannondale no terminal - Faturamento, Lojas, Estoque, Transporte."""
import psycopg2
import psycopg2.extras
from decimal import Decimal
from datetime import date

DB = {
    "host": "localhost",
    "port": 5433,
    "dbname": "cannondale",
    "user": "postgres",
    "password": "postgres",
}

LARGURA = 130


def linha(car="="):
    print(car * LARGURA)


def cabecalho(titulo):
    linha()
    print(f"  {titulo}")
    linha()


def fmt_real(v):
    if v is None:
        return "–"
    try:
        d = Decimal(str(v))
        return f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


def fmt_int(v):
    if v is None:
        return "–"
    try:
        return f"{int(v):,}".replace(",", ".")
    except Exception:
        return str(v)


def conectar():
    return psycopg2.connect(**DB)


def q(sql, params=None):
    conn = conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def tabela(titulo, colunas, linhas, total_linha=None, formatadores=None):
    """
    colunas: lista de tuplas (rotulo_exibicao, chave_banco, alinhamento, formato)
      formato: "real", "int" ou None
    """
    if not linhas:
        print(f"\n{titulo}: nenhum dado encontrado.\n")
        return
    print(f"\n{titulo}")
    rotulos = [c[0] for c in colunas]
    chaves = [c[1] for c in colunas]
    alinhs = [c[2] if len(c) > 2 else "<" for c in colunas]
    frmts = [c[3] if len(c) > 3 else None for c in colunas]
    if formatadores:
        frmts = formatadores

    largs = [len(r) for r in rotulos]
    for r in linhas:
        for i, chave in enumerate(chaves):
            v = r.get(chave, "")
            s = fmt_real(v) if frmts[i] == "real" else (fmt_int(v) if frmts[i] == "int" else str(v))
            if len(s) > largs[i]:
                largs[i] = len(s)

    def monta(valores, sep=" | "):
        partes = []
        for i, v in enumerate(valores):
            al = alinhs[i]
            s = fmt_real(v) if frmts[i] == "real" else (fmt_int(v) if frmts[i] == "int" else str(v))
            if al == ">":
                partes.append(s.rjust(largs[i]))
            elif al == "^":
                partes.append(s.center(largs[i]))
            else:
                partes.append(s.ljust(largs[i]))
        return sep.join(partes)

    print("  " + monta(rotulos))
    print("  " + "-" * (sum(largs) + (len(colunas) - 1) * 3))
    for r in linhas:
        print("  " + monta([r.get(chave, "") for chave in chaves]))
    if total_linha:
        print("  " + "-" * (sum(largs) + (len(colunas) - 1) * 3))
        print("  " + monta(total_linha))
    print()


def main():
    print("\n" + "=" * LARGURA)
    print("  CANNONDALE BIKE INTELLIGENCE — ANÁLISE DE DADOS (TERMINAL)")
    print("=" * LARGURA)
    print(f"  Fonte: PostgreSQL Docker (localhost:5433) | banco: cannondale")
    print(f"  Data da consulta: {date.today().strftime('%d/%m/%Y')}\n")

    # ============ 1. FATURAMENTO ============
    cabecalho("1. FATURAMENTO")
    vendas = q("""
        SELECT 
            to_char(data_venda, 'YYYY-MM') AS mes,
            count(*) AS pedidos,
            sum(quantidade) AS unidades,
            sum(valor_bruto) AS bruto,
            sum(desconto) AS descontos,
            sum(valor_liquido) AS liquido
        FROM public.vendas
        GROUP BY to_char(data_venda, 'YYYY-MM')
        ORDER BY mes
    """)
    if vendas:
        total_geral = q("""
            SELECT count(*) AS pedidos, sum(quantidade) AS unidades,
                   sum(valor_bruto) AS bruto, sum(desconto) AS descontos,
                   sum(valor_liquido) AS liquido
            FROM public.vendas
        """)[0]
        tabela("Faturamento por mês",
               [("Mês", "mes", "<", None),
                ("Pedidos", "pedidos", ">", "int"),
                ("Unidades", "unidades", ">", "int"),
                ("Bruto (R$)", "bruto", ">", "real"),
                ("Descontos (R$)", "descontos", ">", "real"),
                ("Líquido (R$)", "liquido", ">", "real")],
               vendas,
               total_linha=["TOTAL", total_geral["pedidos"], total_geral["unidades"],
                            total_geral["bruto"], total_geral["descontos"], total_geral["liquido"]])

        print(f"  Resumo: {len(vendas)} mês(es) | {fmt_int(total_geral['pedidos'])} pedidos | "
              f"{fmt_int(total_geral['unidades'])} unidades | Faturamento líquido: {fmt_real(total_geral['liquido'])}")

    top_prod = q("""
        SELECT modelo, categoria, sum(quantidade) AS unidades, sum(valor_liquido) AS faturamento
        FROM public.vendas
        GROUP BY modelo, categoria
        ORDER BY faturamento DESC
        LIMIT 10
    """)
    tabela("Top 10 produtos por faturamento",
           [("Produto", "modelo", "<", None),
            ("Categoria", "categoria", "<", None),
            ("Unidades", "unidades", ">", "int"),
            ("Faturamento (R$)", "faturamento", ">", "real")],
           top_prod)

    # ============ 2. LOJAS ============
    cabecalho("2. LOJAS")
    lojas = q("""
        SELECT nome_loja, tipo_loja, cidade, estado_provincia, pais, regiao, perfil_desempenho, status_loja, fonte
        FROM public.lojas
        ORDER BY nome_loja
    """)
    tabela("Rede de lojas",
           [("Loja", "nome_loja", "<", None),
            ("Tipo", "tipo_loja", "<", None),
            ("Cidade / Estado", "cidade", "<", None),
            ("País", "pais", "<", None),
            ("Região", "regiao", "<", None),
            ("Perfil", "perfil_desempenho", "<", None),
            ("Status", "status_loja", "<", None),
            ("Fonte", "fonte", "<", None)],
           lojas)
    print(f"  Total de lojas: {len(lojas)}")

    vendas_loja = q("""
        SELECT nome_loja, cidade, regiao, pais,
               count(*) AS pedidos,
               sum(quantidade) AS unidades,
               sum(valor_liquido) AS faturamento
        FROM public.vendas
        GROUP BY nome_loja, cidade, regiao, pais
        ORDER BY faturamento DESC
        LIMIT 15
    """)
    tabela("Top 15 lojas por faturamento",
           [("Loja", "nome_loja", "<", None),
            ("Cidade / Região", "cidade", "<", None),
            ("País", "pais", "<", None),
            ("Pedidos", "pedidos", ">", "int"),
            ("Unidades", "unidades", ">", "int"),
            ("Faturamento (R$)", "faturamento", ">", "real")],
           vendas_loja)

    # ============ 3. ESTOQUE ============
    cabecalho("3. ESTOQUE")
    ultimo = q("SELECT max(data_atualizacao) AS d FROM public.estoque")[0]["d"]
    print(f"  Referência do estoque: {ultimo.strftime('%d/%m/%Y')}\n")

    resumo = q("""
        SELECT sum(estoque_atual) AS total_unidades,
               count(*) AS skus,
               count(*) FILTER (WHERE estoque_atual <= estoque_minimo) AS criticos
        FROM public.estoque
        WHERE data_atualizacao = %s
    """, (ultimo,))[0]
    print(f"  Estoque total: {fmt_int(resumo['total_unidades'])} unidades | SKUs: {fmt_int(resumo['skus'])} | "
          f"Críticos (abaixo do mínimo): {fmt_int(resumo['criticos'])}")

    estoque_cat = q("""
        SELECT categoria,
               count(*) AS skus,
               sum(estoque_atual) AS unidades
        FROM public.estoque
        WHERE data_atualizacao = %s
        GROUP BY categoria
        ORDER BY unidades DESC
    """, (ultimo,))
    tabela("Estoque por categoria",
           [("Categoria", "categoria", "<", None),
            ("SKUs", "skus", ">", "int"),
            ("Unidades", "unidades", ">", "int")],
           estoque_cat)

    estoque_status = q("""
        SELECT status_estoque AS status,
               count(*) AS skus,
               sum(estoque_atual) AS unidades
        FROM public.estoque
        WHERE data_atualizacao = %s
        GROUP BY status_estoque
    """, (ultimo,))
    tabela("Classificação de estoque",
           [("Status", "status", "<", None),
            ("SKUs", "skus", ">", "int"),
            ("Unidades", "unidades", ">", "int")],
           estoque_status)

    baixo = q("""
        SELECT e.modelo, e.categoria, l.nome_loja, e.estoque_atual, e.estoque_minimo
        FROM public.estoque e
        JOIN public.lojas l ON l.id_loja = e.id_loja
        WHERE e.data_atualizacao = %s
          AND e.estoque_atual <= COALESCE(e.estoque_minimo, 0)
        ORDER BY e.estoque_atual ASC
        LIMIT 15
    """, (ultimo,))
    tabela("Produtos com baixo estoque (críticos)",
           [("Produto", "modelo", "<", None),
            ("Categoria", "categoria", "<", None),
            ("Loja", "nome_loja", "<", None),
            ("Atual", "estoque_atual", ">", "int"),
            ("Mínimo", "estoque_minimo", ">", "int")],
           baixo)

    # ============ 4. TRANSPORTE ============
    cabecalho("4. TRANSPORTE E LOGÍSTICA")
    log_resumo = q("""
        SELECT count(*) AS movimentos,
               sum(quantidade) AS unidades,
               sum(custo_frete) AS custo_total,
               avg(tempo_transito_dias) AS tempo_medio,
               count(*) FILTER (WHERE data_entrega IS NOT NULL AND data_prevista IS NOT NULL AND data_entrega > data_prevista) AS atrasados
        FROM public.logistica
    """)[0]
    print(f"  Movimentos: {fmt_int(log_resumo['movimentos'])} | Unidades: {fmt_int(log_resumo['unidades'])} | "
          f"Custo total frete: {fmt_real(log_resumo['custo_total'])} | Atrasados: {fmt_int(log_resumo['atrasados'])}")

    por_modal = q("""
        SELECT modal,
               count(*) AS movimentos,
               sum(quantidade) AS unidades,
               sum(custo_frete) AS custo_total,
               round(avg(tempo_transito_dias),1) AS tempo_medio_dias
        FROM public.logistica
        GROUP BY modal
        ORDER BY movimentos DESC
    """)
    tabela("Logística por modal",
           [("Modal", "modal", "<", None),
            ("Movimentos", "movimentos", ">", "int"),
            ("Unidades", "unidades", ">", "int"),
            ("Custo frete (R$)", "custo_total", ">", "real"),
            ("Tempo médio (dias)", "tempo_medio_dias", ">", "real")],
           por_modal)

    por_status = q("""
        SELECT status_logistica AS status,
               count(*) AS movimentos,
               sum(quantidade) AS unidades
        FROM public.logistica
        GROUP BY status_logistica
        ORDER BY movimentos DESC
    """)
    tabela("Status das cargas",
           [("Status", "status", "<", None),
            ("Movimentos", "movimentos", ">", "int"),
            ("Unidades", "unidades", ">", "int")],
           por_status)

    por_transp = q("""
        SELECT transportadora,
               count(*) AS movimentos,
               sum(custo_frete) AS custo_total,
               round(avg(tempo_transito_dias),1) AS tempo_medio_dias
        FROM public.logistica
        GROUP BY transportadora
        ORDER BY movimentos DESC
        LIMIT 10
    """)
    tabela("Top 10 transportadoras",
           [("Transportadora", "transportadora", "<", None),
            ("Movimentos", "movimentos", ">", "int"),
            ("Custo frete (R$)", "custo_total", ">", "real"),
            ("Tempo médio (dias)", "tempo_medio_dias", ">", "real")],
           por_transp)

    ultimos = q("""
        SELECT data_envio, modelo, categoria, quantidade, nome_loja, cidade_origem, cidade_destino,
               modal, transportadora, status_logistica, custo_frete
        FROM public.logistica
        ORDER BY data_envio DESC NULLS LAST, id_logistica DESC
        LIMIT 10
    """)
    tabela("Últimos movimentos de transporte",
           [("Envio", "data_envio", "<", None),
            ("Produto", "modelo", "<", None),
            ("Categoria", "categoria", "<", None),
            ("Qtd.", "quantidade", ">", "int"),
            ("Loja", "nome_loja", "<", None),
            ("Origem", "cidade_origem", "<", None),
            ("Destino", "cidade_destino", "<", None),
            ("Modal", "modal", "<", None),
            ("Transportadora", "transportadora", "<", None),
            ("Status", "status_logistica", "<", None),
            ("Custo (R$)", "custo_frete", ">", "real")],
           ultimos)

    linha()
    print("  Fim da análise. Dados extraídos do banco Cannondale (Docker PostgreSQL).")
    linha()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERRO: não foi possível conectar/consultar o banco de dados.")
        print(f"Detalhe: {e}")
        print("\nCertifique-se de que o container 'cannondale-pg' está rodando:")
        print("  docker start cannondale-pg")
