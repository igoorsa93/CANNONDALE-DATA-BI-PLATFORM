-- Seed data: dim_imagens
-- Official image URLs discovered on Cannondale BR website (Cloudfront CDN)

BEGIN;

DROP TABLE IF EXISTS _sku_map;
CREATE TEMP TABLE _sku_map AS
SELECT id_produto, sku FROM dim.dim_produtos;

INSERT INTO dim.dim_imagens (id_produto, modelo, tipo_imagem, url_imagem, url_produto, nome_arquivo, imagem_principal, ordem, source_url, collection_date)
SELECT
    m.id_produto,
    i.modelo,
    i.tipo_imagem,
    i.url_imagem,
    i.url_produto,
    i.nome_arquivo,
    i.imagem_principal::boolean,
    i.ordem::int,
    i.source_url,
    i.collection_date::date
FROM (VALUES
    ('CAD014-2026-001','SuperSix EVO 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my26/bikes/road/race/s6-evo/collection/c26_s6evo_collection_d_2.ashx?mh=2560&mw=1920&hash=4BBDBF186B1FF6976056BA7D48D5DC7E','https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','c26_s6evo_collection_d_2.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','2026-10-05'),
    ('CAD014-2026-001','SuperSix EVO 1','lateral','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my26/bikes/road/race/s6-evo/collection/c26_s6evo_collection_d_3.ashx?mh=2560&mw=1920&hash=E33DBCD3C06C21584B9B1038B3DCEFBC','https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','c26_s6evo_collection_d_3.ashx','false',2,'https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','2026-10-05'),
    ('CAD014-2026-001','SuperSix EVO 1','detalhe','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my26/bikes/road/race/s6-evo/collection/c26_s6evo_collection_d_8.ashx?mh=2560&mw=1920&hash=26B83C7AE294DBD06B2C44761B0D45AE','https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','c26_s6evo_collection_d_8.ashx','false',3,'https://www.cannondale.com/pt-br/bikes/road/race/supersix-evo','2026-10-05'),
    ('SUPX-2026-001','SuperX 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/categorycarousels/model_superx_c25.ashx?mh=1920&mw=2560&hash=B4801514973EAA15C68A3E3075717B7C','https://www.cannondale.com/pt-br/bikes/road/gravel/superx','model_superx_c25.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/road/gravel','2026-10-05'),
    ('TOPSTONE-ALLOY-2026-001','Topstone Alloy 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/categorycarousels/model_topstonealloy_c23.ashx?mh=1920&mw=2560&hash=6ABE6976BCAF0B1CBE67D1291A0ADD53','https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-alloy','model_topstonealloy_c23.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/road/gravel','2026-10-05'),
    ('TOPSTONE-CARBON-2026-001','Topstone Carbon 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/categorycarousels/model_topstonecarbon_cy25.ashx?mh=1920&mw=2560&hash=B58B965AC4204DC5CC76A886DAF4F60D','https://www.cannondale.com/pt-br/bikes/road/gravel/topstone-carbon','model_topstonecarbon_cy25.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/road/gravel','2026-10-05'),
    ('MOTERRA-2026-001','Moterra Neo 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my24/bikes/electric/e-mountain/moterra-sl/homepage/c24_moterrasl_navigationdriver_desktop.ashx?mh=1440&mw=1440&hash=B72FCC8915001DB543900AEB397B6C75','https://www.cannondale.com/pt-br/bikes/electric/e-mountain/moterra-neo','c24_moterrasl_navigationdriver_desktop.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/electric','2026-10-05'),
    ('SCALPEL-2026-001','Scalpel 1','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my25/bikes/mountain/cross-country/scalpel-updates/collection/cy25_scalpel_d3_2.ashx?mh=427&mw=320&hash=C505378DB0EF7FAF29980C8FB4F28954','https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel','cy25_scalpel_d3_2.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/mountain/cross-country/scalpel','2026-10-05'),
    ('TRAIL-2026-001','Trail 6','principal','https://d1mo5ln9tjltxq.cloudfront.net/-/media/images/my25/bikes/mountain/trail-bikes/trail/collection-page/c25_trail_collection_desktop_02.ashx?mh=320&mw=427&hash=A7BF6D29F019EA4034F03F9034BF862E','https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/trail','c25_trail_collection_desktop_02.ashx','true',1,'https://www.cannondale.com/pt-br/bikes/mountain/trail-bikes/trail','2026-10-05')
) AS i(id_produto_sku, modelo, tipo_imagem, url_imagem, url_produto, nome_arquivo, imagem_principal, ordem, source_url, collection_date)
JOIN _sku_map m ON m.sku = i.id_produto_sku;

DROP TABLE _sku_map;
COMMIT;

SELECT COUNT(*) AS total_imagens FROM dim.dim_imagens;