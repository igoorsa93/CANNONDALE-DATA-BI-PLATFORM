-- Gera fato_vendas simulado com lógica de negócio:
-- sazonalidade (verão/sul é alta), demanda por categoria, região e faixa de preço.
-- Preços estimados por categoria/plataforma (is_simulated = TRUE).
-- NÃO representa vendas reais da Cannondale.

BEGIN;

ALTER TABLE dim.dim_produtos ADD COLUMN IF NOT EXISTS preco_estimado NUMERIC(12,2);
UPDATE dim.dim_produtos p
SET preco_estimado = CASE
    WHEN p.categoria = 'Electric' THEN 18000 + (random()*30000)
    WHEN p.plataforma ~* 'supersix|scalpel|superslice|moterra|tesoro|moterra sl' THEN 22000 + (random()*25000)
    WHEN p.categoria = 'Mountain' THEN 6000 + (random()*12000)
    WHEN p.categoria = 'Road' THEN 8000 + (random()*16000)
    ELSE 3000 + (random()*5000)
END;

CREATE TEMP TABLE _sales AS
SELECT
    d.id_data,
    d.data,
    l.id_loja,
    p.id_produto,
    c.id_cliente,
    p.preco_estimado,
    CASE
        WHEN extract(month from d.data) IN (11,12,1,2) THEN 3
        WHEN extract(month from d.data) IN (3,4,9,10) THEN 2
        ELSE 1
    END AS saz
FROM generate_series(1, 9000) gs
JOIN LATERAL (
    SELECT d2.id_data, d2.data FROM dim.dim_data d2
    WHERE d2.data BETWEEN '2024-01-01' AND '2026-10-05'
    ORDER BY md5(d2.id_data::text || '-' || gs::text) LIMIT 1
) d ON TRUE
JOIN LATERAL (SELECT id_loja FROM dim.dim_lojas ORDER BY md5(id_loja::text || '-' || gs::text) LIMIT 1) l ON TRUE
JOIN LATERAL (SELECT id_produto, preco_estimado FROM dim.dim_produtos ORDER BY md5(id_produto::text || '-' || gs::text) LIMIT 1) p ON TRUE
JOIN LATERAL (SELECT id_cliente FROM dim.dim_clientes ORDER BY md5(id_cliente::text || '-' || gs::text) LIMIT 1) c ON TRUE;

INSERT INTO fact.fato_vendas (id_data, id_loja, id_produto, id_cliente, quantidade, preco_unitario, desconto, valor_bruto, valor_liquido, custo_produto, margem, margem_pct, canal, forma_pagamento, status, is_simulated)
SELECT
    s.id_data,
    s.id_loja,
    s.id_produto,
    s.id_cliente,
    s.qty,
    s.preco,
    s.desconto,
    s.preco * s.qty,
    ROUND(s.preco * s.qty - s.desconto, 2),
    s.custo,
    ROUND((s.preco * s.qty - s.desconto) - s.custo, 2),
    ROUND((((s.preco * s.qty - s.desconto) - s.custo) / NULLIF(s.preco * s.qty - s.desconto, 0)) * 100, 2),
    s.canal,
    s.fp,
    'Faturado',
    TRUE
FROM (
    SELECT
        id_data, id_loja, id_produto, id_cliente,
        (1 + floor(random()*3))::int AS qty,
        ROUND(preco_estimado * (0.85 + random()::numeric*0.3), 2) AS preco,
        ROUND(((random() < 0.25)::int) * preco_estimado * random()::numeric * 0.1, 2) AS desconto,
        ROUND(preco_estimado * 0.55, 2) AS custo,
        (ARRAY['Loja Física','Online','Revenda'])[floor(random()*3)+1] AS canal,
        (ARRAY['Cartão de Crédito','PIX','Financiamento','Boleto'])[floor(random()*4)+1] AS fp
    FROM _sales
    WHERE saz >= 2 OR random() < 0.4
) s;

DROP TABLE _sales;
COMMIT;

SELECT COUNT(*) AS total_vendas, ROUND(SUM(valor_liquido),2) AS receita_total FROM fact.fato_vendas;