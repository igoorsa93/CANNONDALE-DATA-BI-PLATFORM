# Cannondale Data & BI Platform

Projeto de portfólio profissional de **Dados, Banco de Dados, ETL, Logística, Vendas, Estoque, Lojas e Business Intelligence** baseado na Cannondale.

> **Aviso importante (obrigatório):** Os dados de catálogo e informações públicas foram obtidos de fontes públicas (www.cannondale.com/pt-br). Dados de vendas, estoque e operações internas são **simulados** para fins educacionais e de portfólio. Este projeto **não é afiliado, endossado ou patrocinado pela Cannondale / Cycling Sports Group**.

## 📊 Visão Geral

Plataforma completa de dados com:
- **Catálogo real** extraído do site oficial Cannondale Brasil (56 produtos, 22 variantes, 105 imagens do CDN oficial).
- **Dados simulados de negócio** (vendas, estoque, logística, lojas, clientes, transportadoras) marcados com `is_simulated = TRUE`.
- **Banco PostgreSQL** com modelo dimensional (`dim_*`, `fact_*`) e views de KPI.
- **ETL modular em Python** com orquestração, validação de qualidade e exportação.
- **Power BI** com 18 medidas DAX e tema identidade visual Cannondale.
- **Dashboard executivo** no Lovable (frontend) pronto para conexão com API/banco.

## 🏗️ Arquitetura

```
FONTE (cannondale.com/pt-br)
  -> EXTRAÇÃO (Requests/BeautifulSoup — etl/scraper)
  -> RAW (data/raw)
  -> TRATAMENTO (etl/products, etl/images, etl/stores, etl/sales, etl/logistics)
  -> VALIDAÇÃO (99_validation.sql + etl/validate_data.py)
  -> PostgreSQL (database/schema + database/seeds)
  -> KPI/DAX (sql/kpis + powerbi/dax_measures.md)
  -> Power BI / Lovable Dashboard
```

### Modelo Dimensional

```text
                      dim_data
                         |
      +------------------+------------------+
      |                  |                  |
   fato_vendas      fato_estoque     fato_logistica
      |                  |                  |
      +------+-----------+-----------+-------+
             |                   |
       dim_produtos          dim_lojas
             |                   |
       dim_imagens       dim_transportadoras
                                 dim_clientes
```

### Camadas
| Camada | Conteúdo |
|--------|----------|
| `stage / meta` | Controle de execuções ETL e log de qualidade |
| `dim / fact` | Modelo dimensional para consumo analítico |
| `sql (views)` | Views de KPI reutilizáveis |
| `powerbi/` | Tema, medidas DAX, guia de conexão |

## 📁 Estrutura do Repositório

```
cannondale-data-platform/
├── .github/workflows/ci.yml          # CI com validação de qualidade de dados
├── .gitignore
├── CHANGELOG.md
├── docker-compose.yml                # PostgreSQL 16 (porta 5433) + imagens (5434)
├── Dockerfile.etl                    # Imagem Docker do pipeline Python
├── README.md                         # Este arquivo
├── requirements.txt                  # Dependências Python
├── run_analise.bat                   # Análise terminal no Windows
├── backups/                          # Backups CSV (produtos, vendas, estoque, etc.)
├── data/                             # Dados crus, processados, imagens e backup SQL
│   ├── raw/                          # CSVs e JSONs extraídos do site
│   ├── processed/                    # CSVs validados
│   └── cannondale_backup.sql         # Dump do banco (~16 MB)
├── database/                         # Schema, seeds e views SQL
│   ├── schema/                       # 01_create_schema.sql, 01_complete_schema.sql
│   ├── seeds/                        # 00..09 seeds + 10_fix + 99_validation
│   ├── tables/                       # Definições de tabelas
│   ├── views/                        # Views do banco
│   └── medidas_dax_corrigido.txt
├── dashboard/                        # App Flask + análise terminal
│   ├── app.py
│   ├── analise_terminal.py
│   ├── static/ (css, js)
│   └── templates/ (index.html)
├── docs/                             # Documentação completa
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── data_quality.md
│   ├── EXECUTIVE_SUMMARY.md
│   ├── MISSION_001_CATALOG_DISCOVERY.md
│   ├── powerbi_guide.md
│   └── PUBLISHING.md
├── etl/                              # Pipeline Python (scraper, produtos, imagens, vendas, estoque, logística)
│   ├── run_pipeline.py
│   ├── run_full_pipeline.py
│   ├── validate_data.py
│   ├── validate_final.py
│   ├── products/, images/, stores/, sales/, logistics/, scraper/
│   └── generate_*.py, load_*.py, export_excel*.py
├── excel/                            # Exportações Excel
├── Imagens/                          # Imagens do projeto
├── powerbi/                          # Tema Cannondale + medidas DAX
│   ├── cannondale_theme.json
│   └── dax_measures.md
├── reports/                          # Relatórios gerados
├── sql/
│   └── kpis/
│       └── vw_kpis.sql               # 6 views de KPI
└── product_links.txt
```

## 📈 Indicadores (versão final)

| Indicador | Valor |
|-----------|-------|
| Produtos (catálogo real) | 56 |
| Variantes | 22 |
| Imagens (CDN oficial) | 105 |
| Categorias | Road, Mountain, Electric, Active, Gravel, Kids |
| Lojas (simuladas) | 173 |
| Transportadoras | 5 |
| Clientes (simulados) | 10 |
| Vendas (simuladas) | 16.743 pedidos · R$ 356,9 M |
| Estoque (simulado) | 329.392 registros |
| Logística (simulada) | 2.008 movimentos |
| Validação | 27/27 testes PASS · 0 duplicidades · 0 FK quebradas |

### Receita por Ano
| Ano | Pedidos | Receita |
|-----|---------|---------|
| 2024 | 2.553 | R$ 131,7 M |
| 2025 | 2.603 | R$ 133,0 M |
| 2026 (até 05/10) | 1.818 | R$ 92,2 M |

## 🧪 Data Quality

Relatório final (`quality_report_final.json`): **27/27 testes aprovados, 0 falhas**.

### Testes cobertos
- **Produtos:** sem duplicatas, nomes não vazios, preços válidos, categorias válidas, URLs válidas, códigos de modelo presentes.
- **Imagens:** vinculadas a produtos existentes, todos produtos com imagem, 1 imagem principal por produto, arquivos locais existem, sem duplicatas por hash.
- **Vendas:** referências válidas (produto/loja), cálculos de valor bruto e líquido corretos, quantidades positivas.
- **Estoque:** referências válidas, cálculo `estoque_final = inicial + entradas - saídas - transferências`, sem estoque negativo, classificação válida, consistência entre saídas de estoque e vendas.
- **Lojas:** coordenadas preenchidas, estados brasileiros válidos.

Execução local:
```bash
python etl/validate_data.py
```

CI (GitHub Actions): roda PostgreSQL 16, aplica schema + seeds e executa `validate_data.py` em cada push/PR na `main`.

## 🔌 ETL Pipeline

Orquestrador principal: `etl/run_full_pipeline.py`

Passos:
1. **Load Products** — carrega produtos no banco
2. **Load Images** — carrega imagens vinculadas
3. **Generate Stores** — gera lojas simuladas
4. **Generate Sales** — gera vendas simuladas
5. **Generate Inventory** — gera estoque simulado
6. **Run Validation** — executa testes de qualidade
7. **Export Excel** — exporta para Excel
8. **Generate Report** — gera relatório final

Execução rápida:
```bash
python etl/run_pipeline.py
```

## ⚡ Como Reproduzir

### Pré-requisitos
- Docker e Docker Compose
- Python 3.11+ (para ETL local)
- `psql` (cliente PostgreSQL)

### 1. Subir banco de dados
```bash
docker compose up -d
```
Isso sobe `cannondale-pg` na porta **5433** (banco `cannondale`, usuário `postgres`, senha `postgres`).

### 2. Aplicar schema e seeds
```bash
psql -h localhost -p 5433 -U postgres -d cannondale -f database/schema/01_create_schema.sql
for f in database/seeds/00_seed_dim_data.sql \
         database/seeds/01_seed_produtos.sql \
         database/seeds/02_seed_variantes.sql \
         database/seeds/03_seed_imagens.sql \
         database/seeds/04_seed_lojas.sql \
         database/seeds/05_seed_transportadoras.sql \
         database/seeds/06_seed_clientes.sql \
         database/seeds/07_generate_estoque.sql \
         database/seeds/08_generate_vendas.sql \
         database/seeds/09_generate_logistica.sql; do
  psql -h localhost -p 5433 -U postgres -d cannondale -f "$f"
done
```

### 3. Rodar ETL
```bash
pip install -r requirements.txt
python etl/run_full_pipeline.py
```

### 4. Validar dados
```bash
python etl/validate_data.py
```

### 5. Conectar Power BI
1. Power BI Desktop → Obter dados → PostgreSQL
2. Servidor: `localhost:5433`, Banco: `cannondale`, usuário `postgres`, senha `postgres`
3. Importar tabelas `dim.*`, `fact.*` e views de `sql/kpis/`
4. Marcar `dim_data` como tabela de data
5. Aplicar tema: `powerbi/cannondale_theme.json`

Guia completo: `docs/powerbi_guide.md`

## 🌐 Conectar com o Dashboard (Lovable)

O dashboard frontend está hospedado em:
`https://cannondalebikeintelligence.lovable.app/`

**Status:** interface pronta, dados atualmente são exemplos. Para conectar aos dados reais:

### Opção recomendada: Supabase (nativo Lovable)
1. Exporte o banco local:
   ```bash
   pg_dump -h localhost -p 5433 -U postgres -d cannondale > cannondale_export.sql
   ```
2. Importe no Supabase do projeto Lovable (connection string nas configurações do projeto).
3. Vincule o Supabase ao app no Lovable.
4. O dashboard consome as tabelas `dim.*` e `fact.*` diretamente.

### Opção alternativa: API intermediária
1. Crie uma API (Node/Express ou Python) que leia o PostgreSQL local (porta 5433).
2. Exponha via túnel (ngrok/Cloudflare) — **não exponha a porta 5433 diretamente na internet**.
3. No Lovable, substitua os dados fixos por `fetch` para os endpoints da API (`/api/produtos`, `/api/vendas`, `/api/estoque`, etc.).

## 📊 Power BI — Medidas DAX (resumo)

| Tema | Medidas |
|------|---------|
| Vendas | Receita, Unidades Vendidas, Pedidos, Ticket Médio, Margem, Margem %, Receita LY, Crescimento % |
| Estoque | Estoque Atual, % SKU Excesso, % SKU Atenção, % SKU Crítico, Giro de Estoque, Cobertura (dias), Ruptura |
| Logística | Pedidos em Trânsito, Lead Time Médio, % Entrega no Prazo, OTIF, Custo Logístico |

Arquivo completo: `powerbi/dax_measures.md`

## 🗺️ Roadmap / Próximos Passos

- [x] Missão 001 — Catalog Discovery (catálogo real validado)
- [x] Missão 002–009 — Banco, Lojas, Estoque, Vendas, Logística, ETL, Data Quality, Power BI
- [ ] Missão 010 — Publicação final (Power BI Service)
- [ ] Scraping automatizado de preços/specs via API/browser
- [ ] Agendamento de ETL (Airflow/cron)
- [ ] Testes de dados com dbt / Great Expectations
- [ ] Publicar no Power BI Service com refresh agendado

## 📄 Documentação

| Documento | Conteúdo |
|-----------|----------|
| `docs/architecture.md` | Arquitetura, modelo dimensional, camadas, fontes |
| `docs/data_dictionary.md` | Dicionário completo de todas as tabelas e colunas |
| `docs/data_quality.md` | Regras de validação, contagens, score de qualidade |
| `docs/EXECUTIVE_SUMMARY.md` | Sumário executivo com números e artefatos |
| `docs/MISSION_001_CATALOG_DISCOVERY.md` | Metodologia de extração do catálogo real |
| `docs/powerbi_guide.md` | Guia de conexão e páginas do Power BI |
| `docs/PUBLISHING.md` | Direitos de uso, dados simulados, publicação em portfólio |

## ⚠️ Aviso Legal

- **Não afiliado** à Cannondale / Cycling Sports Group.
- Dados de catálogo (modelos, URLs, imagens) são públicos e referenciados via CDN oficial — **não redistribuir imagens** sem verificar condições de uso.
- Vendas, estoque, logística, lojas, clientes e transportadoras são **simulados** (`is_simulated = TRUE`) e não refletem operações reais.
- Destinado a fins educacionais e de portfólio profissional.

---

Mantido por **igoor** — Portfólio de Dados & BI. Atualizado em 05/10/2026.