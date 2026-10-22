-- Seed data: dim_produtos
-- Based on Cannondale Brasil official website catalog mapping (2026-10-05)

\copy dim.dim_produtos(sku, modelo, categoria, subcategoria, plataforma, descricao, material, ano_modelo, preco, url_produto, source_url, source_name, collection_date) FROM '/data/raw/cannabondale_produtos_raw.csv' WITH (FORMAT csv, HEADER true, NULL '');

SELECT categoria, COUNT(*) as total_modelos
FROM dim.dim_produtos
GROUP BY categoria
ORDER BY categoria;