# Publicação — Cannondale Data & BI Platform

## Aviso legal (obrigatório no repositório)
> Os dados de catálogo e informações públicas foram obtidos de fontes públicas (www.cannondale.com/pt-br). Dados de vendas, estoque e operações internas são **simulados** para fins educacionais e de portfólio. Este projeto **não é afiliado, endossado ou patrocinado pela Cannondale / Cycling Sports Group**.

## Direitos e uso das imagens
- Apenas a **URL oficial** das imagens da Cannondale é referenciada (`dim_imagens.url_imagem`), hospedada no CDN oficial (Cloudfront).
- **Não** republicar, copiar ou redistribuir as imagens sem verificar as condições de uso da marca.
- Para uso em portfólio/apresentação, prefira referenciar a URL oficial em vez de baixar e redistribuir os arquivos.

## Dados simulados
- Todas as tabelas de vendas, estoque, logística, clientes e transportadoras operacionais têm `is_simulated = TRUE`.
- Lojas com `is_simulated = TRUE` não correspondem necessariamente a lojas reais da Cannondale; foram geradas com base em cidades brasileiras de grande porte.

## Publicação recomendada (portfólio)
1. Subir o repositório no GitHub (público ou privado) com este README.
2. Exportar o banco para um dump SQL (opcional): `pg_dump -U postgres -d cannondale > backup.sql`.
3. Publicar o relatório Power BI (Power BI Service) ou capturas de tela em `docs/`.
4. Incluir link para o repositório no seu portfólio/LinkedIn.

## Estrutura de publicação
```text
- README.md (visão geral + aviso)
- docs/ (arquitetura, dicionário, data_quality, powerbi_guide, mission_001)
- database/ (schema + seeds reproduzíveis)
- etl/ (código Python modular)
- sql/kpis/ (views)
- powerbi/ (DAX + tema)
```

## Próximos passos (opcionais)
- Automatizar scraping (API/browser) para preços e specs por SKU.
- Agendar ETL (Airflow/cron).
- Publicar Power BI Service com refresh agendado.
- Adicionar testes de dados (Great Expectations / dbt tests).
