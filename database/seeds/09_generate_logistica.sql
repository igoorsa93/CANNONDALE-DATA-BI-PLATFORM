-- Gera fato_logistica simulada entre centros de distribuicao e lojas.

BEGIN;

CREATE TEMP TABLE _src AS
SELECT
    d.id_data,
    d.data AS dt,
    p.id_produto,
    origem.id_loja AS id_loja_origem,
    dest.id_loja AS id_loja_destino,
    t.id_transportadora,
    t.prazo_medio_dias AS prazo_previsto
FROM generate_series(1, 3000) gs
JOIN LATERAL (
    SELECT d2.id_data, d2.data FROM dim.dim_data d2
    WHERE d2.data BETWEEN '2024-01-01' AND '2026-10-05' ORDER BY md5(d2.id_data::text || '-' || gs::text) LIMIT 1
) d ON TRUE
JOIN LATERAL (SELECT id_produto FROM dim.dim_produtos ORDER BY md5(id_produto::text || '-' || gs::text) LIMIT 1) p ON TRUE
JOIN LATERAL (SELECT id_loja FROM dim.dim_lojas WHERE tipo_loja = 'Centro de Distribuicao' ORDER BY md5(id_loja::text || '-' || gs::text) LIMIT 1) origem ON TRUE
JOIN LATERAL (SELECT id_loja FROM dim.dim_lojas WHERE tipo_loja <> 'Centro de Distribuicao' ORDER BY md5(id_loja::text || '-' || gs::text) LIMIT 1) dest ON TRUE
JOIN LATERAL (SELECT id_transportadora, prazo_medio_dias FROM dim.dim_transportadoras ORDER BY md5(id_transportadora::text || '-' || gs::text) LIMIT 1) t ON TRUE;

CREATE TEMP TABLE _logc AS
SELECT
    id_data,
    id_produto,
    id_loja_origem,
    id_loja_destino,
    id_transportadora,
    dt,
    prazo_previsto,
    (1 + floor(random()*10))::int AS qty,
    CASE WHEN random() < 0.85 THEN 0 ELSE 1 + floor(random()*5)::int END AS atraso,
    CASE
        WHEN random() < 0.80 THEN 'Entregue'
        WHEN random() < 0.90 THEN 'Em transito'
        WHEN random() < 0.95 THEN 'Aguardando coleta'
        WHEN random() < 0.98 THEN 'Atrasado'
        ELSE 'Cancelado'
    END AS status
FROM _src;

INSERT INTO fact.fato_logistica (id_data, id_produto, id_loja_origem, id_loja_destino, id_transportadora, quantidade, data_pedido, data_envio, data_entrega, prazo_previsto, prazo_real, custo_frete, status, atraso_dias, is_simulated)
SELECT
    id_data,
    id_produto,
    id_loja_origem,
    id_loja_destino,
    id_transportadora,
    qty,
    dt,
    dt + (1 + floor(random()*2))::int,
    dt + prazo_previsto + atraso,
    prazo_previsto,
    prazo_previsto + atraso,
    ROUND((80 + random()::numeric*500) * qty, 2),
    status,
    atraso,
    TRUE
FROM _logc;

DROP TABLE _src;
DROP TABLE _logc;
COMMIT;

SELECT status, COUNT(*) FROM fact.fato_logistica GROUP BY status;
