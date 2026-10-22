-- Data quality validation for Mission 001
-- Run after seeds are applied

-- 1. Products without category
SELECT 'Produtos sem categoria' AS regra, COUNT(*) AS qtd
FROM dim.dim_produtos
WHERE categoria IS NULL OR TRIM(categoria) = '';

-- 2. Products without URL
SELECT 'Produtos sem URL' AS regra, COUNT(*) AS qtd
FROM dim.dim_produtos
WHERE url_produto IS NULL OR TRIM(url_produto) = '';

-- 3. Duplicate SKU in dim_produtos
SELECT 'SKU duplicado em dim_produtos' AS regra, COUNT(*) - COUNT(DISTINCT sku) AS qtd
FROM dim.dim_produtos;

-- 4. Duplicate product models (potential duplicates)
SELECT modelo, COUNT(*) AS qtd
FROM dim.dim_produtos
GROUP BY modelo
HAVING COUNT(*) > 1;

-- 5. Variants whose id_produto has no matching product (FK violations)
SELECT 'Variantes sem produto correspondente' AS regra, COUNT(*) AS qtd
FROM dim.dim_variantes v
LEFT JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
WHERE p.id_produto IS NULL;

-- 6. Images whose id_produto foreign key is missing
SELECT 'Imagens sem produto correspondente' AS regra, COUNT(*) AS qtd
FROM dim.dim_imagens i
LEFT JOIN dim.dim_produtos p ON p.id_produto = i.id_produto
WHERE p.id_produto IS NULL;

-- 7. Duplicate variant SKUs
SELECT 'SKU duplicado em variantes' AS regra, COUNT(*) - COUNT(DISTINCT sku) AS qtd
FROM dim.dim_variantes;

-- 8. Negative / null prices
SELECT 'Produtos com preço inválido' AS regra, COUNT(*) AS qtd
FROM dim.dim_produtos
WHERE preco IS NOT NULL AND preco < 0;

-- 9. Summary counts
SELECT 'Produtos' AS tabela, COUNT(*) AS total FROM dim.dim_produtos
UNION ALL
SELECT 'Variantes', COUNT(*) FROM dim.dim_variantes
UNION ALL
SELECT 'Imagens', COUNT(*) FROM dim.dim_imagens
UNION ALL
SELECT 'Categorias distintas', COUNT(DISTINCT categoria) FROM dim.dim_produtos
UNION ALL
SELECT 'Plataformas distintas', COUNT(DISTINCT plataforma) FROM dim.dim_produtos;