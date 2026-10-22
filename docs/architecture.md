# Arquitetura — Cannondale Data & BI Platform

## Visão geral
Plataforma de dados de portfólio com catálogo real (site Cannondale BR) + dados simulados de negócio (vendas, estoque, logística), PostgreSQL como base, ETL em Python (planejado), e Power BI como camada de visualização.

```text
FONTE (site cannondale.com/pt-br)
  -> EXTRAÇÃO (Requests/BeautifulSoup — etl/scraper)
  -> RAW (data/raw)
  -> TRATAMENTO/PADRONIZAÇÃO (etl/products, etl/images, etl/stores, etl/sales, etl/logistics)
  -> VALIDAÇÃO (99_validation.sql + meta.data_quality_log)
  -> PostgreSQL (database/schema, database/seeds)
  -> KPI/DAX (sql/kpis, powerbi/dax_measures.md)
  -> Power BI (powerbi/)
```

## Modelo dimensional
```text
                  dim_data
                     |
        +------------+------------+
        |            |            |
   fato_vendas  fato_estoque  fato_logistica
        |            |            |
        +-----+------+------+-----+
              |             |
        dim_produtos    dim_lojas
              |             |
        dim_imagens    dim_transportadoras
                      dim_clientes
```

## Camadas
- **stage / meta**: controle de ETL e qualidade.
- **dim / fact**: modelo dimensional para consumo.
- **sql (views)**: KPIs reutilizáveis.

## Fontes de dados
| Dado | Fonte | Status |
|---|---|---|
| Catálogo, categorias, plataformas, URLs, imagens | www.cannondale.com/pt-br | Real (público) |
| Preços BRL | não público (SPA) | Nulo / estimado |
| Lojas, clientes, transportadoras operacionais | simulado | `is_simulated = TRUE` |
| Vendas, estoque, logística | simulado | `is_simulated = TRUE` |

## Componentes
- ETL: `etl/` (módulos por domínio).
- Banco: `database/` (schema, seeds, validation).
- KPI: `sql/kpis/`, `powerbi/dax_measures.md`.
- BI: `powerbi/` (tema, guia).
