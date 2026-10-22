# Sumário Executivo — Cannondale Data & BI Platform

## Visão
Plataforma de dados de portfólio com catálogo real (Cannondale BR) + dados simulados de negócio, PostgreSQL, ETL Python e base Power BI.

## Números
| Indicador | Valor |
|---|---|
| Produtos (catálogo real) | 56 |
| Variantes | 22 |
| Imagens (CDN oficial) | 9 |
| Categorias | 4 (Road, Mountain, Electric, Active) |
| Plataformas | 45 |
| Lojas (simuladas) | 12 |
| Transportadoras | 5 |
| Clientes (simulados) | 10 |
| Vendas (simuladas) | 6.974 pedidos · R$ 356,9M |
| Estoque (simulado) | 81.200 registros · Normal 70,2% / Crítico 15,4% / Atenção 14,0% / Ruptura 0,3% |
| Logística (simulada) | 3.000 movimentos · OTIF ~66% |
| Validação | 12/12 testes PASS · 0 duplicidades · 0 FK quebradas |

## Receita por ano
| Ano | Pedidos | Receita |
|---|---|---|
| 2024 | 2.553 | R$ 131,7M |
| 2025 | 2.603 | R$ 133,0M |
| 2026 (até 05/10) | 1.818 | R$ 92,2M |

## Artefatos
- `README.md` — visão geral + como reproduzir
- `docs/` — arquitetura, dicionário, data_quality, powerbi_guide, PUBLISHING, MISSION_001
- `database/` — schema + seeds (executados)
- `etl/` — módulos Python + `validate_data.py` (12/12 PASS)
- `sql/kpis/` — 6 views de KPIs
- `powerbi/` — 18 medidas DAX + tema Cannondale
- `data/cannondale_backup.sql` — dump (~16 MB)

## Limitações
- Preços BRL oficiais e specs técnicas por SKU não disponíveis no HTML estático (SPA/Sitecore) → `preco` NULL, `preco_estimado` simulado.
- Vendas/estoque/logística/lojas/clientes/transportadoras são simulados e marcados `is_simulated = TRUE`.
- Imagens apenas referenciadas por URL oficial (não redistribuídas).

## Próximos passos opcionais
- Scraping automatizado de preços/specs via API/browser.
- Agendamento de ETL (Airflow/cron).
- Testes de dados com dbt/Great Expectations.
- Publicação no Power BI Service.
