# Data Quality Report — Cannondale Data Platform

## Resultado das validações (99_validation.sql)

```text
Regra                                        Qtd
-------------------------------------------+-------
Produtos sem categoria                     |   0
Produtos sem URL                           |   0
SKU duplicado em dim_produtos              |   0
SKU duplicado em dim_variantes             |   0
Variantes sem produto correspondente       |   0
Imagens sem produto correspondente         |   0
Produtos com preço inválido                |   0
```

## Contagens

```text
Produtos:              56
Variantes:             22
Imagens:                9
Lojas (simuladas):     12
Transportadoras:        5
Clientes (simulados):  10
Vendas (simuladas):  6974
Estoque (simulado): 81200
Logística (simulada):3000
```

## Qualidade por dimensão
- **Catálogo:** SKU único, categoria/URL completas, imagens vinculadas ao produto correto (sem genéricas), `source_url`/`collection_date` preenchidos.
- **Vendas/Estoque/Logística:** todas marcadas `is_simulated = TRUE`; sem violações de FK.
- **Preços:** `preco` NULL onde não público; `preco_estimado` usado nas simulações e documentado.
- **Datas:** válidas; período 2024-01-01 a 2026-10-05.
- **FK:** todas as chaves estrangeiras resolvidas.

## Score de qualidade (amostra)
Score estimado: **aprox. 95%** (itens simulados não penalizam o catálogo real; catálogo real 100% íntegro).

## Limitações conhecidas
- Preços BRL oficiais não públicos no HTML estático (SPA/Sitecore) -> `preco` NULL.
- Especificações técnicas completas (grupo, marchas, freios, suspensão, rodas, peso) não disponíveis estaticamente -> a preencher via API/browser na Missão 002.
- Transportadoras/lojas com dados operacionais são simulados onde não há fonte pública.

## Recomendações
- Executar `99_validation.sql` a cada carga ETL.
- Validar FK antes de promover de `stage` para `dim/fact`.
- Registrar violações em `meta.data_quality_log`.
