# MISSÃO 001 — CANNONDALE CATALOG DISCOVERY

## Metodologia

Site oficial Cannondale Brasil (`https://www.cannondale.com/pt-br`) foi explorado via fetch e sitemap oficial (`robots.txt` -> `a304077.sitemaphosting6.com/4356448/sitemap.xml`).

Foram mapeadas:
- Categorias de bikes (Road, Mountain, Active, Electric, Kids).
- Subcategorias (Race, Endurance, Gravel, Cyclocross, Cross Country, Enduro, Trail, E-MTB, E-Road, E-Urban, E-Touring, E-Cargo, E-Fitness).
- Plataformas e modelos (SuperSix EVO, SuperSlice, CAAD13/CAAD14, Synapse, SuperX, Topstone Alloy/Carbon, CAADX, Scalpel, Scalpel HT, F-Si, Trail, Habit, Habit HT, Dave, Jekyll, Bad Habit, Moterra Neo/LT/SL, Trail Neo, Habit Neo, Topstone Neo, Synapse Neo, SuperSix EVO Neo, Compact Neo, Flying V, Adventure Neo, Mavaro, Canvas Neo, Tesoro, Tesoro Neo, Tesoro Neo X, Cargowagen Neo, Wonderwagen Neo, Quick, Treadwell, Bad Boy, Adventure, Quick Neo, Treadwell Neo, Quick Neo SL).
- URLs oficiais de cada plataforma e imagens via CDN (Cloudfront).

## Campos disponíveis coletados
- SKU (modelo-ano), modelo, categoria, subcategoria, plataforma, descrição, material, ano_modelo, URL do produto, source_url, source_name, collection_date, imagens.

## Campos ausentes (não públicos / não disponíveis inicialmente)
- Preço oficial (BRL) -> registrado como NULL até confirmação pública.
- Especificações técnicas completas por SKU (grupo, marchas, freios, suspensão, rodas, peso) -> parcialmente capturadas (ex.: Trail 6), preenchimento na Missão 002.
- Variantes com preço e disponibilidade em todos os SKUs.

## Estruturas criadas
- `dim.dim_produtos` (PKs, SKU único, índices)
- `dim.dim_variantes` (FK para produtos, SKU único, índices)
- `dim.dim_imagens` (FK para produtos, tipos de imagem, índices)
- `dim.dim_data`, `dim.dim_lojas`, `dim.dim_transportadoras`, `dim.dim_clientes`
- `fact.fato_vendas`, `fact.fato_estoque`, `fact.fato_logistica`
- Views: `dim.vw_produtos_completo`, `fact.vw_vendas_completo`, `fact.vw_estoque_completo`, `fact.vw_logistica_completo`

## Validações
Script `database/seeds/99_validation.sql` cobre:
- Duplicidade de SKU em produtos e variantes.
- Produtos sem categoria / sem URL / preço inválido.
- Variantes e imagens sem produto correspondente (FK).
- Resumo de contagens.

Validação manual resultante: nenhuma inconsistência de FK detectada nos seeds; preços mantidos como NULL onde não públicos; sem imagens genéricas atribuídas a modelos específicos.

## Observações
- O site oficial é SPA (Sitecore) e o catálogo detalhado (variações por SKU, preços, disponibilidade) é carregado via JavaScript/API; os dados crus usados foram derivados da navegação pública, sitemap e páginas de plataforma.
- Empresas/transportadoras/lojas fictícias ainda não foram criadas (Missão 002/003).

## Próximos passos
MISSÃO 002 — PRODUCT DATABASE (preencher preços oficiais, especificações técnicas completas e enriquecer variantes por SKU).
