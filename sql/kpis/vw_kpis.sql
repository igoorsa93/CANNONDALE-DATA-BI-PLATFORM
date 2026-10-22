CREATE SCHEMA IF NOT EXISTS sql;

-- KPI / metric views
-- Establish reusable SQL measures aligned with the BI layer.

-- Receita mensal
CREATE OR REPLACE VIEW sql.vw_kpi_receita_mensal AS
SELECT d.ano, d.mes, d.mes_ano,
       SUM(v.valor_liquido) AS receita,
       SUM(v.quantidade) AS unidades,
       COUNT(DISTINCT v.id_venda) AS pedidos,
       ROUND(SUM(v.valor_liquido) / NULLIF(SUM(v.quantidade),0), 2) AS ticket_medio
FROM fact.fato_vendas v
JOIN dim.dim_data d ON d.id_data = v.id_data
GROUP BY d.ano, d.mes, d.mes_ano;

-- Receita e margem por categoria
CREATE OR REPLACE VIEW sql.vw_kpi_categoria AS
SELECT p.categoria,
       SUM(v.valor_liquido) AS receita,
       SUM(v.margem) AS margem,
       ROUND(SUM(v.margem)/NULLIF(SUM(v.valor_liquido),0)*100,2) AS margem_pct,
       SUM(v.quantidade) AS unidades
FROM fact.fato_vendas v
JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
GROUP BY p.categoria;

-- Performance regional
CREATE OR REPLACE VIEW sql.vw_kpi_regional AS
SELECT l.estado, l.cidade,
       SUM(v.valor_liquido) AS receita,
       SUM(v.quantidade) AS unidades
FROM fact.fato_vendas v
JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
GROUP BY l.estado, l.cidade;

-- Estoque atual por loja/produto
CREATE OR REPLACE VIEW sql.vw_kpi_estoque AS
SELECT d.data, l.nome_loja, p.modelo, p.categoria,
       e.estoque_final, e.classificacao_estoque, e.giro_estoque, e.cobertura_dias
FROM fact.fato_estoque e
JOIN dim.dim_data d ON d.id_data = e.id_data
JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
JOIN dim.dim_produtos p ON p.id_produto = e.id_produto;

-- % SKU por classificação de estoque
CREATE OR REPLACE VIEW sql.vw_kpi_estoque_classificacao AS
SELECT classificacao_estoque,
       COUNT(*) AS skus,
       ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) AS pct
FROM fact.fato_estoque
GROUP BY classificacao_estoque;

-- Logística: lead time, OTIF, custo
CREATE OR REPLACE VIEW sql.vw_kpi_logistica AS
SELECT t.nome AS transportadora,
       COUNT(*) AS movimentos,
       ROUND(AVG(lg.prazo_real),1) AS lead_time_medio,
       ROUND(COUNT(*) FILTER (WHERE lg.atraso_dias = 0 AND lg.status='Entregue')*100.0/COUNT(*),2) AS pct_entrega_prazo,
       SUM(lg.custo_frete) AS custo_logistico
FROM fact.fato_logistica lg
JOIN dim.dim_transportadoras t ON t.id_transportadora = lg.id_transportadora
GROUP BY t.nome;