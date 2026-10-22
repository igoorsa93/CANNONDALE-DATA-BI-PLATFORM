-- Cannondale Data Platform - Complete Database Schema
-- Created: 2026-10-07
-- Description: Dimensional model for Cannondale catalog, inventory, sales, and logistics

-- =====================================================
-- EXTENSIONS
-- =====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- SCHEMAS
-- =====================================================
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS dim;
CREATE SCHEMA IF NOT EXISTS fact;
CREATE SCHEMA IF NOT EXISTS stage;
CREATE SCHEMA IF NOT EXISTS meta;

-- =====================================================
-- DIMENSION: dim.dim_data
-- =====================================================
CREATE TABLE dim.dim_data (
    id_data INTEGER PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    semestre INTEGER NOT NULL,
    semana_ano INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    nome_dia_semana VARCHAR(20) NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    mes_ano VARCHAR(7) NOT NULL,
    trimestre_ano VARCHAR(7) NOT NULL,
    eh_fim_semana BOOLEAN NOT NULL,
    eh_feriado_br BOOLEAN DEFAULT FALSE,
    nome_feriado VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_data_data ON dim.dim_data(data);
CREATE INDEX idx_dim_data_ano_mes ON dim.dim_data(ano, mes);

-- =====================================================
-- DIMENSION: dim.dim_produtos
-- =====================================================
CREATE TABLE dim.dim_produtos (
    id_produto BIGSERIAL PRIMARY KEY,
    salsify_id VARCHAR(50) NOT NULL UNIQUE,
    sku VARCHAR(50),
    modelo VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    subcategoria VARCHAR(50),
    plataforma VARCHAR(100) NOT NULL,
    codigo_modelo VARCHAR(50),
    ano_modelo INTEGER,
    cor VARCHAR(100),
    tamanho VARCHAR(100),
    material_quadro VARCHAR(50),
    peso VARCHAR(50),
    suspensao VARCHAR(100),
    freios VARCHAR(100),
    rodas VARCHAR(100),
    preco_site NUMERIC(12,2),
    moeda VARCHAR(3) DEFAULT 'BRL',
    url_produto VARCHAR(500),
    descricao TEXT,
    badges VARCHAR(200),
    tags VARCHAR(200),
    is_electric BOOLEAN DEFAULT FALSE,
    source_category_slug VARCHAR(100),
    tipo_dado VARCHAR(20) DEFAULT 'OFICIAL',
    url_imagem_principal VARCHAR(500),
    collection_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_produtos_salsify_id ON dim.dim_produtos(salsify_id);
CREATE INDEX idx_dim_produtos_sku ON dim.dim_produtos(sku);
CREATE INDEX idx_dim_produtos_categoria ON dim.dim_produtos(categoria);
CREATE INDEX idx_dim_produtos_subcategoria ON dim.dim_produtos(subcategoria);
CREATE INDEX idx_dim_produtos_plataforma ON dim.dim_produtos(plataforma);
CREATE INDEX idx_dim_produtos_ano_modelo ON dim.dim_produtos(ano_modelo);
CREATE INDEX idx_dim_produtos_is_electric ON dim.dim_produtos(is_electric);
CREATE INDEX idx_dim_produtos_tipo_dado ON dim.dim_produtos(tipo_dado);

-- =====================================================
-- DIMENSION: dim.dim_produto_imagens
-- =====================================================
CREATE TABLE dim.dim_produto_imagens (
    id_imagem BIGSERIAL PRIMARY KEY,
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    modelo VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    url_produto VARCHAR(500),
    url_imagem VARCHAR(500) NOT NULL,
    tipo_imagem VARCHAR(30) NOT NULL,
    imagem_principal BOOLEAN DEFAULT FALSE,
    nome_arquivo VARCHAR(200),
    caminho_local VARCHAR(500),
    hash_md5 VARCHAR(32),
    tamanho_bytes BIGINT,
    data_download DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'OK',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_produto_imagens_id_produto ON dim.dim_produto_imagens(id_produto);
CREATE INDEX idx_dim_produto_imagens_tipo ON dim.dim_produto_imagens(tipo_imagem);
CREATE INDEX idx_dim_produto_imagens_principal ON dim.dim_produto_imagens(imagem_principal) WHERE imagem_principal = TRUE;

-- =====================================================
-- DIMENSION: dim.dim_lojas
-- =====================================================
CREATE TABLE dim.dim_lojas (
    id_loja BIGSERIAL PRIMARY KEY,
    nome_loja VARCHAR(150) NOT NULL,
    tipo_loja VARCHAR(50),
    endereco VARCHAR(200),
    cidade VARCHAR(100),
    estado VARCHAR(50),
    pais VARCHAR(50) DEFAULT 'Brasil',
    regiao VARCHAR(50),
    continente VARCHAR(50),
    cep VARCHAR(20),
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    telefone VARCHAR(30),
    site VARCHAR(200),
    perfil_desempenho VARCHAR(30),
    is_simulated BOOLEAN DEFAULT TRUE,
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_lojas_cidade_estado ON dim.dim_lojas(cidade, estado);
CREATE INDEX idx_dim_lojas_pais ON dim.dim_lojas(pais);
CREATE INDEX idx_dim_lojas_tipo ON dim.dim_lojas(tipo_loja);
CREATE INDEX idx_dim_lojas_perfil ON dim.dim_lojas(perfil_desempenho);
CREATE INDEX idx_dim_lojas_simulated ON dim.dim_lojas(is_simulated);

-- =====================================================
-- DIMENSION: dim.dim_canais_venda
-- =====================================================
CREATE TABLE dim.dim_canais_venda (
    id_canal BIGSERIAL PRIMARY KEY,
    canal VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(200),
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DIMENSION: dim.dim_formas_pagamento
-- =====================================================
CREATE TABLE dim.dim_formas_pagamento (
    id_forma_pagamento BIGSERIAL PRIMARY KEY,
    forma_pagamento VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(200),
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- FACT TABLE: fact.fato_vendas
-- =====================================================
CREATE TABLE fact.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim.dim_data(id_data),
    id_loja BIGINT NOT NULL REFERENCES dim.dim_lojas(id_loja),
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    id_canal BIGINT REFERENCES dim.dim_canais_venda(id_canal),
    id_forma_pagamento BIGINT REFERENCES dim.dim_formas_pagamento(id_forma_pagamento),
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_unitario NUMERIC(12,2) NOT NULL,
    desconto NUMERIC(12,2) DEFAULT 0,
    valor_bruto NUMERIC(12,2) NOT NULL,
    valor_liquido NUMERIC(12,2) NOT NULL,
    custo_produto NUMERIC(12,2),
    margem NUMERIC(12,2),
    margem_pct NUMERIC(5,2),
    status VARCHAR(30) DEFAULT 'Faturado',
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_vendas_data ON fact.fato_vendas(id_data);
CREATE INDEX idx_fato_vendas_loja ON fact.fato_vendas(id_loja);
CREATE INDEX idx_fato_vendas_produto ON fact.fato_vendas(id_produto);
CREATE INDEX idx_fato_vendas_canal ON fact.fato_vendas(id_canal);
CREATE INDEX idx_fato_vendas_tipo_dado ON fact.fato_vendas(tipo_dado);

-- =====================================================
-- FACT TABLE: fact.fato_estoque
-- =====================================================
CREATE TABLE fact.fato_estoque (
    id_estoque BIGSERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim.dim_data(id_data),
    id_loja BIGINT NOT NULL REFERENCES dim.dim_lojas(id_loja),
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    estoque_inicial INTEGER DEFAULT 0,
    entradas INTEGER DEFAULT 0,
    saidas INTEGER DEFAULT 0,
    transferencias INTEGER DEFAULT 0,
    vendas INTEGER DEFAULT 0,
    estoque_final INTEGER NOT NULL,
    estoque_minimo INTEGER,
    estoque_maximo INTEGER,
    ponto_reposicao INTEGER,
    classificacao_estoque VARCHAR(30),
    giro_estoque NUMERIC(8,2),
    cobertura_dias INTEGER,
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_estoque_data ON fact.fato_estoque(id_data);
CREATE INDEX idx_fato_estoque_loja ON fact.fato_estoque(id_loja);
CREATE INDEX idx_fato_estoque_produto ON fact.fato_estoque(id_produto);
CREATE INDEX idx_fato_estoque_classificacao ON fact.fato_estoque(classificacao_estoque);
CREATE INDEX idx_fato_estoque_tipo_dado ON fact.fato_estoque(tipo_dado);

-- =====================================================
-- FACT TABLE: fact.fato_logistica
-- =====================================================
CREATE TABLE fact.fato_logistica (
    id_movimento BIGSERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim.dim_data(id_data),
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    id_loja_origem BIGINT REFERENCES dim.dim_lojas(id_loja),
    id_loja_destino BIGINT REFERENCES dim.dim_lojas(id_loja),
    quantidade INTEGER NOT NULL,
    data_pedido DATE,
    data_envio DATE,
    data_entrega DATE,
    prazo_previsto INTEGER,
    prazo_real INTEGER,
    custo_frete NUMERIC(12,2),
    status VARCHAR(30),
    atraso_dias INTEGER DEFAULT 0,
    tipo_dado VARCHAR(20) DEFAULT 'SIMULADO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_logistica_data ON fact.fato_logistica(id_data);
CREATE INDEX idx_fato_logistica_produto ON fact.fato_logistica(id_produto);
CREATE INDEX idx_fato_logistica_origem ON fact.fato_logistica(id_loja_origem);
CREATE INDEX idx_fato_logistica_destino ON fact.fato_logistica(id_loja_destino);
CREATE INDEX idx_fato_logistica_status ON fact.fato_logistica(status);
CREATE INDEX idx_fato_logistica_tipo_dado ON fact.fato_logistica(tipo_dado);

-- =====================================================
-- METADATA TABLES
-- =====================================================
CREATE TABLE meta.etl_log (
    id_log BIGSERIAL PRIMARY KEY,
    processo VARCHAR(100) NOT NULL,
    tabela_destino VARCHAR(100),
    status VARCHAR(30) NOT NULL,
    registros_processados INTEGER DEFAULT 0,
    registros_inseridos INTEGER DEFAULT 0,
    registros_atualizados INTEGER DEFAULT 0,
    registros_erro INTEGER DEFAULT 0,
    mensagem_erro TEXT,
    inicio_execucao TIMESTAMP NOT NULL,
    fim_execucao TIMESTAMP,
    duracao_segundos INTERVAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meta.data_quality_log (
    id_quality BIGSERIAL PRIMARY KEY,
    tabela VARCHAR(100) NOT NULL,
    regra VARCHAR(100) NOT NULL,
    descricao TEXT,
    severidade VARCHAR(20) NOT NULL,
    registros_afetados INTEGER DEFAULT 0,
    detalhes JSONB,
    status VARCHAR(20) DEFAULT 'Pendente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- VIEWS
-- =====================================================

-- View: Produtos com imagens
CREATE OR REPLACE VIEW dim.vw_produtos_com_imagens AS
SELECT 
    p.id_produto,
    p.salsify_id,
    p.sku,
    p.modelo,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.codigo_modelo,
    p.ano_modelo,
    p.cor,
    p.tamanho,
    p.material_quadro,
    p.peso,
    p.suspensao,
    p.freios,
    p.rodas,
    p.preco_site,
    p.moeda,
    p.url_produto,
    p.descricao,
    p.badges,
    p.tags,
    p.is_electric,
    p.tipo_dado,
    i.id_imagem,
    i.url_imagem,
    i.tipo_imagem,
    i.imagem_principal,
    i.nome_arquivo,
    i.caminho_local,
    i.hash_md5
FROM dim.dim_produtos p
LEFT JOIN dim.dim_produto_imagens i ON i.id_produto = p.id_produto
WHERE p.is_active = TRUE;

-- View: Vendas com dimensões
CREATE OR REPLACE VIEW fact.vw_vendas_completo AS
SELECT 
    v.*,
    d.data,
    d.ano,
    d.mes,
    d.trimestre,
    d.mes_ano,
    d.nome_mes,
    l.nome_loja,
    l.cidade,
    l.estado,
    l.pais,
    l.regiao,
    l.tipo_loja,
    l.perfil_desempenho,
    p.modelo,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.preco_site as preco_oficial,
    c.canal,
    fp.forma_pagamento
FROM fact.fato_vendas v
JOIN dim.dim_data d ON d.id_data = v.id_data
JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
LEFT JOIN dim.dim_canais_venda c ON c.id_canal = v.id_canal
LEFT JOIN dim.dim_formas_pagamento fp ON fp.id_forma_pagamento = v.id_forma_pagamento;

-- View: Estoque com dimensões
CREATE OR REPLACE VIEW fact.vw_estoque_completo AS
SELECT 
    e.*,
    d.data,
    d.ano,
    d.mes,
    d.trimestre,
    d.mes_ano,
    l.nome_loja,
    l.cidade,
    l.estado,
    l.pais,
    l.regiao,
    l.tipo_loja,
    l.perfil_desempenho,
    p.modelo,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.preco_site
FROM fact.fato_estoque e
JOIN dim.dim_data d ON d.id_data = e.id_data
JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
JOIN dim.dim_produtos p ON p.id_produto = e.id_produto;

-- View: KPIs de Vendas
CREATE OR REPLACE VIEW fact.vw_kpis_vendas AS
SELECT 
    d.ano,
    d.mes,
    d.mes_ano,
    l.pais,
    l.regiao,
    l.nome_loja,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.modelo,
    COUNT(*) as num_vendas,
    SUM(v.quantidade) as unidades_vendidas,
    SUM(v.valor_bruto) as faturamento_bruto,
    SUM(v.desconto) as total_descontos,
    SUM(v.valor_liquido) as faturamento_liquido,
    AVG(v.valor_liquido / NULLIF(v.quantidade, 0)) as ticket_medio,
    SUM(v.margem) as margem_total,
    CASE WHEN SUM(v.valor_bruto) > 0 THEN SUM(v.margem) / SUM(v.valor_bruto) * 100 ELSE 0 END as margem_pct_media
FROM fact.fato_vendas v
JOIN dim.dim_data d ON d.id_data = v.id_data
JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
GROUP BY d.ano, d.mes, d.mes_ano, l.pais, l.regiao, l.nome_loja, p.categoria, p.subcategoria, p.plataforma, p.modelo;

-- View: KPIs de Estoque
CREATE OR REPLACE VIEW fact.vw_kpis_estoque AS
SELECT 
    d.ano,
    d.mes,
    d.mes_ano,
    l.pais,
    l.regiao,
    l.nome_loja,
    l.perfil_desempenho,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.modelo,
    SUM(e.estoque_final) as estoque_total,
    SUM(e.estoque_minimo) as estoque_minimo_total,
    SUM(e.estoque_maximo) as estoque_maximo_total,
    COUNT(CASE WHEN e.classificacao_estoque = 'Critico' THEN 1 END) as produtos_criticos,
    COUNT(CASE WHEN e.classificacao_estoque = 'Excesso' THEN 1 END) as produtos_excesso,
    COUNT(CASE WHEN e.classificacao_estoque = 'Normal' THEN 1 END) as produtos_normal,
    COUNT(CASE WHEN e.classificacao_estoque = 'Atencao' THEN 1 END) as produtos_atencao,
    AVG(e.giro_estoque) as giro_medio,
    AVG(e.cobertura_dias) as cobertura_media_dias
FROM fact.fato_estoque e
JOIN dim.dim_data d ON d.id_data = e.id_data
JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
JOIN dim.dim_produtos p ON p.id_produto = e.id_produto
GROUP BY d.ano, d.mes, d.mes_ano, l.pais, l.regiao, l.nome_loja, l.perfil_desempenho, p.categoria, p.subcategoria, p.plataforma, p.modelo;

-- View: Produtos por categoria/plataforma
CREATE OR REPLACE VIEW dim.vw_catalogo_resumo AS
SELECT 
    categoria,
    subcategoria,
    plataforma,
    COUNT(*) as total_produtos,
    MIN(preco_site) as preco_minimo,
    MAX(preco_site) as preco_maximo,
    AVG(preco_site) as preco_medio,
    SUM(CASE WHEN is_electric THEN 1 ELSE 0 END) as qtd_electric,
    SUM(CASE WHEN tipo_dado = 'OFICIAL' THEN 1 ELSE 0 END) as qtd_oficial
FROM dim.dim_produtos
WHERE is_active = TRUE
GROUP BY categoria, subcategoria, plataforma
ORDER BY categoria, subcategoria, plataforma;