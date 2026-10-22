# Changelog

## [1.0.0] — 2026-10-05
### Adicionado
- Catálogo real da Cannondale BR (56 produtos, 22 variantes, 9 imagens) em `dim_produtos`, `dim_variantes`, `dim_imagens`.
- Dados simulados marcados `is_simulated=TRUE`: 12 lojas, 5 transportadoras, 10 clientes, 6974 vendas, 81200 estoques, 3000 logísticas.
- Schema PostgreSQL dimensional (`dim_*`, `fact.*`, views de KPI).
- ETL modular em Python (`etl/`) com `run_pipeline.py` e `validate_data.py` (12/12 PASS).
- 6 views de KPI em `sql/kpis/vw_kpis.sql`.
- 18 medidas DAX documentadas + tema Cannondale em `powerbi/`.
- Documentação: arquitetura, dicionário, data_quality, powerbi_guide, PUBLISHING, MISSION_001, EXECUTIVE_SUMMARY.
- Backup SQL `data/cannondale_backup.sql`.
- `.gitignore`.

### Corrigido
- Distribuição de vendas/logística (laterais não-correlacionados faziam `random()` rodar 1x → agora `md5(gs||id)`).
- Tipos numéricos em ROUND (cast `::numeric`).
- FK lojas/transportadoras alinhadas (`Centro de Distribuicao` ASCII).

### Observações
- Preços BRL oficiais e specs técnicas por SKU não disponíveis no HTML estático → `preco` NULL, `preco_estimado` simulado.
