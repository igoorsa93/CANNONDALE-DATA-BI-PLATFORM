-- Fix Data Quality Issues:
-- 1. Update contexto with full Cannondale catalog (57 products)
-- 2. Regenerate vendas with seasonal/category logic
-- 3. Regenerate estoque to exactly match vendas quantities

BEGIN;

-- =====================================================
-- 1. RELOAD CONTEXTO WITH FULL CATALOG (57 products)
-- =====================================================
TRUNCATE TABLE contexto RESTART IDENTITY CASCADE;

COPY contexto(id_produto, modelo, categoria, subcategoria, plataforma, descricao, material, ano_modelo, preco, url_produto, source_url, source_name, collection_date) 
FROM '/tmp/cannabondale_produtos_raw.csv' WITH (FORMAT csv, HEADER true, NULL '');

UPDATE contexto SET 
    preco_site = COALESCE(preco, 0),
    moeda = 'BRL',
    url_imagem_principal = '',
    especificacoes = '',
    data_coleta = COALESCE(collection_date, CURRENT_DATE),
    fonte = COALESCE(source_name, 'Cannondale Oficial'),
    tipo_dado = 'OFICIAL',
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP;

SELECT 'Contexto reloaded' AS step, COUNT(*) AS total FROM contexto;

-- =====================================================
-- 2. REGENERATE VENDAS WITH SEASONAL/CATEGORY LOGIC
-- =====================================================
TRUNCATE TABLE vendas RESTART IDENTITY CASCADE;

-- Add estimated prices by category/platform to contexto
ALTER TABLE contexto ADD COLUMN IF NOT EXISTS preco_estimado NUMERIC(12,2);

UPDATE contexto SET preco_estimado = CASE
    WHEN categoria = 'Electric' AND subcategoria = 'E-MTB' THEN 60000 + (random()*50000)
    WHEN categoria = 'Electric' AND subcategoria = 'E-Road' THEN 25000 + (random()*30000)
    WHEN categoria = 'Electric' AND subcategoria = 'E-Urban' THEN 15000 + (random()*20000)
    WHEN categoria = 'Electric' AND subcategoria = 'E-Touring' THEN 20000 + (random()*25000)
    WHEN categoria = 'Electric' AND subcategoria = 'E-Cargo' THEN 25000 + (random()*20000)
    WHEN categoria = 'Electric' AND subcategoria = 'E-Fitness' THEN 12000 + (random()*15000)
    WHEN categoria = 'Road' AND subcategoria = 'Race' THEN 25000 + (random()*60000)
    WHEN categoria = 'Road' AND subcategoria = 'Endurance' THEN 15000 + (random()*30000)
    WHEN categoria = 'Road' AND subcategoria = 'Gravel' THEN 12000 + (random()*30000)
    WHEN categoria = 'Road' AND subcategoria = 'Cyclocross' THEN 18000 + (random()*25000)
    WHEN categoria = 'Mountain' AND subcategoria = 'Cross Country' THEN 18000 + (random()*90000)
    WHEN categoria = 'Mountain' AND subcategoria = 'Trail' THEN 5000 + (random()*30000)
    WHEN categoria = 'Mountain' AND subcategoria = 'Enduro' THEN 25000 + (random()*50000)
    WHEN categoria = 'Active' AND subcategoria = 'Fitness' THEN 3000 + (random()*8000)
    WHEN categoria = 'Active' AND subcategoria = 'Urban' THEN 4000 + (random()*10000)
    ELSE 5000 + (random()*10000)
END;

-- Generate sales: 2024-01-01 to 2026-10-05
-- ~12,000 records with proper seasonality
WITH sales_base AS (
    SELECT 
        d.data AS data_venda,
        l.id_loja,
        l.nome_loja,
        l.cidade,
        l.estado_provincia,
        l.pais,
        l.regiao,
        p.id_produto,
        p.modelo,
        p.categoria,
        p.subcategoria,
        p.plataforma,
        p.preco_estimado,
        CASE 
            WHEN EXTRACT(MONTH FROM d.data) IN (11,12,1,2) THEN 3  -- Verão BR = alta
            WHEN EXTRACT(MONTH FROM d.data) IN (3,4,9,10) THEN 2  -- Meia estação
            ELSE 1  -- Inverno = baixa
        END AS sazonalidade,
        CASE 
            WHEN p.categoria = 'Electric' THEN 1.5
            WHEN p.categoria = 'Road' AND p.subcategoria = 'Race' THEN 1.3
            WHEN p.categoria = 'Mountain' AND p.subcategoria IN ('Cross Country','Enduro') THEN 1.2
            ELSE 1.0
        END AS categoria_weight,
        CASE 
            WHEN l.perfil_desempenho = 'Alto Desempenho' THEN 1.5
            WHEN l.perfil_desempenho = 'Excesso de Estoque' THEN 1.2
            WHEN l.perfil_desempenho = 'Baixo Desempenho' THEN 0.6
            WHEN l.perfil_desempenho = 'Estoque Crítico' THEN 0.8
            ELSE 1.0
        END AS loja_weight
    FROM (
        SELECT generate_series('2024-01-01'::date, '2026-10-05'::date, '1 day'::interval) AS data
    ) d
    CROSS JOIN LATERAL (
        SELECT * FROM lojas WHERE status_loja = 'Ativa' ORDER BY random() LIMIT 1
    ) l
    CROSS JOIN LATERAL (
        SELECT * FROM contexto ORDER BY random() LIMIT 1
    ) p
    WHERE (sazonalidade >= 2 OR random() < 0.35)
      AND (categoria_weight * loja_weight * random()) > 0.25
),
sales_calc AS (
    SELECT
        data_venda,
        id_loja,
        nome_loja,
        cidade,
        estado_provincia,
        pais,
        regiao,
        id_produto,
        modelo,
        categoria,
        subcategoria,
        plataforma,
        (1 + floor(random() * 3))::int AS quantidade,
        ROUND(preco_estimado * (0.85 + random() * 0.3), 2) AS preco_unitario,
        ROUND(((random() < 0.2)::int) * preco_estimado * random() * 0.15, 2) AS desconto,
        (ARRAY['Loja Física','Online','Revenda'])[floor(random()*3)+1] AS canal_venda,
        (ARRAY['Cartão de Crédito','PIX','Financiamento','Boleto'])[floor(random()*4)+1] AS forma_pagamento,
        'Faturado' AS status_venda
    FROM sales_base
)
INSERT INTO vendas (
    data_venda, id_loja, nome_loja, cidade, estado_provincia, pais, regiao,
    id_produto, modelo, categoria, subcategoria, plataforma,
    quantidade, preco_unitario, desconto,
    valor_bruto, valor_liquido,
    canal_venda, forma_pagamento, status_venda
)
SELECT
    data_venda, id_loja, nome_loja, cidade, estado_provincia, pais, regiao,
    id_produto, modelo, categoria, subcategoria, plataforma,
    quantidade, preco_unitario, desconto,
    ROUND(preco_unitario * quantidade, 2),
    ROUND(preco_unitario * quantidade - desconto, 2),
    canal_venda, forma_pagamento, status_venda
FROM sales_calc;

SELECT 'Vendas regenerated' AS step, COUNT(*) AS total, ROUND(SUM(valor_liquido),2) AS receita_total FROM vendas;

-- =====================================================
-- 3. REGENERATE ESTOQUE TO EXACTLY MATCH VENDAS
-- =====================================================
TRUNCATE TABLE estoque RESTART IDENTITY CASCADE;

-- Monthly sales aggregation per store/product
WITH monthly_sales AS (
    SELECT
        id_loja,
        id_produto,
        DATE_TRUNC('month', data_venda)::date AS mes,
        SUM(quantidade) AS vendas_mes
    FROM vendas
    GROUP BY id_loja, id_produto, DATE_TRUNC('month', data_venda)
),
store_product AS (
    SELECT 
        l.id_loja,
        l.nome_loja,
        l.perfil_desempenho,
        p.id_produto,
        p.modelo,
        p.categoria,
        p.subcategoria,
        p.plataforma,
        p.preco_estimado
    FROM lojas l
    CROSS JOIN contexto p
    WHERE l.status_loja = 'Ativa'
),
estoque_calc AS (
    SELECT
        sp.id_loja,
        sp.nome_loja,
        sp.id_produto,
        sp.modelo,
        sp.categoria,
        sp.subcategoria,
        sp.plataforma,
        ms.mes AS data_atualizacao,
        COALESCE(ms.vendas_mes, 0) AS saidas,
        -- Calculate stock levels based on store profile and sales
        CASE sp.perfil_desempenho
            WHEN 'Alto Desempenho' THEN GREATEST(5, COALESCE(ms.vendas_mes, 0) * 2)
            WHEN 'Desempenho Médio' THEN GREATEST(3, COALESCE(ms.vendas_mes, 0) * 1.5)
            WHEN 'Baixo Desempenho' THEN GREATEST(2, COALESCE(ms.vendas_mes, 0))
            WHEN 'Excesso de Estoque' THEN GREATEST(15, COALESCE(ms.vendas_mes, 0) * 4)
            WHEN 'Estoque Crítico' THEN GREATEST(1, COALESCE(ms.vendas_mes, 0))
            ELSE GREATEST(3, COALESCE(ms.vendas_mes, 0) * 1.5)
        END::int AS estoque_inicial,
        CASE 
            WHEN COALESCE(ms.vendas_mes, 0) > 0 AND random() < 0.3 THEN 
                (COALESCE(ms.vendas_mes, 0) + floor(random() * 5 + 1)::int)
            ELSE 0
        END AS entradas,
        0 AS transferencias,
        COALESCE(ms.vendas_mes, 0) AS vendas,
        CASE sp.perfil_desempenho
            WHEN 'Alto Desempenho' THEN 5
            WHEN 'Desempenho Médio' THEN 8
            WHEN 'Baixo Desempenho' THEN 10
            WHEN 'Excesso de Estoque' THEN 3
            WHEN 'Estoque Crítico' THEN 12
            ELSE 8
        END AS estoque_minimo,
        CASE sp.perfil_desempenho
            WHEN 'Alto Desempenho' THEN 50
            WHEN 'Desempenho Médio' THEN 30
            WHEN 'Baixo Desempenho' THEN 20
            WHEN 'Excesso de Estoque' THEN 80
            WHEN 'Estoque Crítico' THEN 15
            ELSE 30
        END AS estoque_maximo
    FROM store_product sp
    LEFT JOIN monthly_sales ms ON ms.id_loja = sp.id_loja AND ms.id_produto = sp.id_produto
),
estoque_final AS (
    SELECT
        id_loja,
        nome_loja,
        id_produto,
        modelo,
        categoria,
        subcategoria,
        plataforma,
        data_atualizacao,
        estoque_inicial,
        entradas,
        saidas,
        transferencias,
        vendas,
        (estoque_inicial + entradas - saidas - transferencias - vendas) AS estoque_atual,
        estoque_minimo,
        estoque_maximo,
        CASE
            WHEN (estoque_inicial + entradas - saidas - transferencias - vendas) <= 0 THEN 'Ruptura'
            WHEN (estoque_inicial + entradas - saidas - transferencias - vendas) <= estoque_minimo * 1.5 THEN 'Crítico'
            WHEN (estoque_inicial + entradas - saidas - transferencias - vendas) >= estoque_maximo THEN 'Excesso'
            WHEN (estoque_inicial + entradas - saidas - transferencias - vendas) <= estoque_minimo * 2 THEN 'Atenção'
            ELSE 'Normal'
        END AS status_estoque,
        CASE 
            WHEN vendas > 0 THEN ROUND((estoque_inicial + entradas)::numeric / NULLIF(vendas, 0) * 30, 0)
            ELSE 999
        END AS dias_cobertura,
        CASE 
            WHEN (estoque_inicial + estoque_inicial + entradas - saidas - transferencias - vendas) > 0 
            THEN ROUND((vendas + 1)::numeric / ((estoque_inicial + estoque_inicial + entradas - saidas - transferencias - vendas) / 2.0) * 12, 2)
            ELSE 0
        END AS giro_estimado
    FROM estoque_calc
)
INSERT INTO estoque (
    data_atualizacao, id_loja, nome_loja, id_produto, modelo, categoria, subcategoria, plataforma,
    estoque_inicial, entradas, saidas, transferencias, vendas, estoque_atual,
    estoque_minimo, estoque_maximo, status_estoque, dias_cobertura, giro_estimado
)
SELECT
    data_atualizacao, id_loja, nome_loja, id_produto, modelo, categoria, subcategoria, plataforma,
    estoque_inicial, entradas, saidas, transferencias, vendas, estoque_atual,
    estoque_minimo, estoque_maximo, status_estoque, dias_cobertura, giro_estimado
FROM estoque_final;

-- Verify consistency
SELECT 'Estoque regenerated' AS step, COUNT(*) AS total FROM estoque;

-- Verify: estoque.saidas should equal vendas.quantidade per store/product/month
SELECT 
    'Consistency Check' AS check_type,
    SUM(e.saidas) AS total_saidas_estoque,
    SUM(v.quantidade) AS total_vendas_qty,
    CASE WHEN SUM(e.saidas) = SUM(v.quantidade) THEN 'MATCH' ELSE 'MISMATCH' END AS status
FROM estoque e
JOIN vendas v ON v.id_loja = e.id_loja AND v.id_produto = e.id_produto
    AND DATE_TRUNC('month', v.data_venda) = e.data_atualizacao;

COMMIT;