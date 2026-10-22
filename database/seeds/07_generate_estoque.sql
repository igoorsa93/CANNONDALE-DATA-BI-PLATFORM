-- Gera fato_estoque simulado (snapshot semanal por produto x loja)

BEGIN;

CREATE TEMP TABLE _est AS
SELECT
    d.id_data,
    l.id_loja,
    p.id_produto
FROM dim.dim_data d
CROSS JOIN dim.dim_lojas l
CROSS JOIN dim.dim_produtos p
WHERE d.data BETWEEN '2024-01-01' AND '2026-10-05'
  AND extract(dow from d.data) = 1
  AND l.tipo_loja IN ('Loja Própria','Revendedor Autorizado');

CREATE TEMP TABLE _estcalc AS
SELECT
    id_data, id_loja, id_produto,
    (5 + floor(random()*20))::int AS ini,
    (floor(random()*8))::int AS entradas,
    (floor(random()*4))::int AS saidas,
    (floor(random()*3))::int AS transf,
    (floor(random()*3))::int AS vendas,
    5 AS min_est,
    40 AS max_est
FROM _est;

INSERT INTO fact.fato_estoque (id_data, id_loja, id_produto, estoque_inicial, entradas, saidas, transferencias, vendas, estoque_final, estoque_minimo, estoque_maximo, classificacao_estoque, giro_estoque, cobertura_dias)
SELECT
    id_data,
    id_loja,
    id_produto,
    ini,
    entradas,
    saidas,
    transf,
    vendas,
    ROUND(ini + entradas - saidas - transf - vendas, 0),
    min_est,
    max_est,
    CASE
        WHEN ROUND(ini + entradas - saidas - transf - vendas, 0) <= 0 THEN 'Ruptura'
        WHEN ROUND(ini + entradas - saidas - transf - vendas, 0) <= min_est * 1.5 THEN 'Crítico'
        WHEN ROUND(ini + entradas - saidas - transf - vendas, 0) >= max_est THEN 'Excesso'
        WHEN ROUND(ini + entradas - saidas - transf - vendas, 0) <= min_est * 2 THEN 'Atenção'
        ELSE 'Normal'
    END,
    ROUND((vendas + 1) / NULLIF(ini + entradas, 0), 2),
    CASE WHEN vendas > 0 THEN ROUND((ini + entradas) / NULLIF(vendas, 0) * 7, 0) ELSE 999 END
FROM _estcalc;

DROP TABLE _est;
DROP TABLE _estcalc;
COMMIT;

SELECT classificacao_estoque, COUNT(*) FROM fact.fato_estoque GROUP BY classificacao_estoque;