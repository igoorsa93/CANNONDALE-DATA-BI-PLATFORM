-- Seeds simplificados: core (3 fatos + dims mínimas)

-- dim_data
INSERT INTO core.dim_data (id_data, data, ano, mes, dia, mes_ano)
SELECT to_char(d,'YYYYMMDD')::int, d, EXTRACT(year FROM d)::int, EXTRACT(month FROM d)::int, EXTRACT(day FROM d)::int, to_char(d,'YYYY-MM')
FROM generate_series('2024-01-01'::date, '2026-12-31'::date, '1 day') d;

-- dim_produto (12)
INSERT INTO core.dim_produto (sku, modelo, categoria) VALUES
('CAD014-2026-001','SuperSix EVO 1','Road'),
('CAD014-2026-002','SuperSix EVO 2','Road'),
('CAAD14-2026-001','CAAD14 1','Road'),
('SUPX-2026-001','SuperX 1','Road'),
('TOPSTONE-CARBON-2026-001','Topstone Carbon 1','Road'),
('SCALPEL-2026-001','Scalpel 1','Mountain'),
('SCALPEL-HT-2026-001','Scalpel HT 1','Mountain'),
('TRAIL-2026-001','Trail 6','Mountain'),
('MOTERRA-2026-001','Moterra Neo 1','Electric'),
('QUICK-2026-001','Quick 1','Active'),
('TREADWELL-2026-001','Treadwell 1','Active'),
('BADBOY-2026-001','Bad Boy 1','Active');

-- dim_loja (12)
INSERT INTO core.dim_loja (nome_loja, cidade, estado) VALUES
('Cannondale SP Vila Madalena','São Paulo','SP'),
('Cannondale SP Jardins','São Paulo','SP'),
('Cannondale RJ Ipanema','Rio de Janeiro','RJ'),
('Cannondale BH Savassi','Belo Horizonte','MG'),
('Cannondale Curitiba Batel','Curitiba','PR'),
('Cannondale POA Moinhos','Porto Alegre','RS'),
('Cannondale Floripa Agronômica','Florianópolis','SC'),
('Cannondale Salvador Barra','Salvador','BA'),
('Cannondale Recife Boa Viagem','Recife','PE'),
('Cannondale Fortaleza Aldeota','Fortaleza','CE'),
('CD Guarulhos','Guarulhos','SP'),
('CD Contagem','Contagem','MG');

-- fato_vendas (6974)
INSERT INTO core.fato_vendas (id_data, id_loja, id_produto, quantidade, valor_liquido, data_venda)
SELECT d.id_data, l.id_loja, p.id_produto,
       (1 + floor(random()*3))::int,
       round(
           (CASE p.categoria
             WHEN 'Electric' THEN 18000.0 + random()*30000.0
             WHEN 'Road' THEN 8000.0 + random()*16000.0
             WHEN 'Mountain' THEN 6000.0 + random()*12000.0
             ELSE 3000.0 + random()*5000.0
           END)::numeric * (0.85 + random()*0.3)::numeric, 2),
       d.data
FROM generate_series(1, 6974) gs
JOIN LATERAL (SELECT id_data, data FROM core.dim_data WHERE data BETWEEN '2024-01-01' AND '2026-10-05' ORDER BY md5(id_data::text || '-' || gs::text) LIMIT 1) d ON TRUE
JOIN LATERAL (SELECT id_loja FROM core.dim_loja ORDER BY md5(id_loja::text || '-' || gs::text) LIMIT 1) l ON TRUE
JOIN LATERAL (SELECT id_produto, categoria FROM core.dim_produto ORDER BY md5(id_produto::text || '-' || gs::text) LIMIT 1) p ON TRUE;

-- fato_estoque (81200)
INSERT INTO core.fato_estoque (id_data, id_loja, id_produto, estoque_final, classificacao)
SELECT d.id_data, l.id_loja, p.id_produto,
       (5 + floor(random()*40))::int,
       CASE
         WHEN r < 0.01 THEN 'Ruptura'
         WHEN r < 0.15 THEN 'Crítico'
         WHEN r < 0.30 THEN 'Atenção'
         WHEN r < 0.05 THEN 'Excesso'
         ELSE 'Normal'
       END
FROM generate_series(1, 81200) gs
JOIN LATERAL (SELECT id_data FROM core.dim_data WHERE EXTRACT(dow FROM data)=1 ORDER BY md5(id_data::text || '-' || gs::text) LIMIT 1) d ON TRUE
JOIN LATERAL (SELECT id_loja FROM core.dim_loja ORDER BY md5(id_loja::text || '-' || gs::text) LIMIT 1) l ON TRUE
JOIN LATERAL (SELECT id_produto FROM core.dim_produto ORDER BY md5(id_produto::text || '-' || gs::text) LIMIT 1) p ON TRUE
CROSS JOIN LATERAL (SELECT random() AS r) rnd;

-- dim_loja_resumo
INSERT INTO core.dim_loja_resumo (id_loja, total_vendas, total_estoque, ultima_atualizacao)
SELECT l.id_loja,
       COALESCE(SUM(v.valor_liquido),0),
       COALESCE(SUM(e.estoque_final),0),
       GREATEST(COALESCE(MAX(v.data_venda),'1900-01-01'), COALESCE(MAX(d.data),'1900-01-01'))
FROM core.dim_loja l
LEFT JOIN core.fato_vendas v ON v.id_loja = l.id_loja
LEFT JOIN core.fato_estoque e ON e.id_loja = l.id_loja
LEFT JOIN core.dim_data d ON d.id_data = e.id_data
GROUP BY l.id_loja;