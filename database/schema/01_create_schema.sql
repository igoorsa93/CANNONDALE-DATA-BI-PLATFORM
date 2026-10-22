-- Cannondale Data Platform - Database Schema
-- Created: 2026-10-05
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
    sku VARCHAR(50) NOT NULL UNIQUE,
    modelo VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    subcategoria VARCHAR(50),
    plataforma VARCHAR(100) NOT NULL,
    descricao TEXT,
    material VARCHAR(50),
    ano_modelo INTEGER,
    preco NUMERIC(12,2),
    moeda VARCHAR(3) DEFAULT 'BRL',
    url_produto VARCHAR(500),
    source_url VARCHAR(500),
    source_name VARCHAR(100),
    collection_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_produtos_sku ON dim.dim_produtos(sku);
CREATE INDEX idx_dim_produtos_categoria ON dim.dim_produtos(categoria);
CREATE INDEX idx_dim_produtos_plataforma ON dim.dim_produtos(plataforma);
CREATE INDEX idx_dim_produtos_ano_modelo ON dim.dim_produtos(ano_modelo);

-- =====================================================
-- DIMENSION: dim.dim_variantes
-- =====================================================
CREATE TABLE dim.dim_variantes (
    id_variante BIGSERIAL PRIMARY KEY,
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    sku VARCHAR(50) NOT NULL UNIQUE,
    tamanho VARCHAR(20),
    cor VARCHAR(50),
    preco NUMERIC(12,2),
    disponibilidade VARCHAR(30),
    source_url VARCHAR(500),
    collection_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_variantes_id_produto ON dim.dim_variantes(id_produto);
CREATE INDEX idx_dim_variantes_sku ON dim.dim_variantes(sku);

-- =====================================================
-- DIMENSION: dim.dim_imagens
-- =====================================================
CREATE TABLE dim.dim_imagens (
    id_imagem BIGSERIAL PRIMARY KEY,
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    modelo VARCHAR(100) NOT NULL,
    tipo_imagem VARCHAR(30) NOT NULL,
    url_imagem VARCHAR(500) NOT NULL,
    url_produto VARCHAR(500),
    nome_arquivo VARCHAR(200),
    imagem_principal BOOLEAN DEFAULT FALSE,
    ordem INTEGER DEFAULT 0,
    source_url VARCHAR(500),
    collection_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_imagens_id_produto ON dim.dim_imagens(id_produto);
CREATE INDEX idx_dim_imagens_tipo ON dim.dim_imagens(tipo_imagem);
CREATE INDEX idx_dim_imagens_principal ON dim.dim_imagens(imagem_principal) WHERE imagem_principal = TRUE;

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
    cep VARCHAR(20),
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    telefone VARCHAR(30),
    site VARCHAR(200),
    source_url VARCHAR(500),
    collection_date DATE DEFAULT CURRENT_DATE,
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_lojas_cidade_estado ON dim.dim_lojas(cidade, estado);
CREATE INDEX idx_dim_lojas_tipo ON dim.dim_lojas(tipo_loja);
CREATE INDEX idx_dim_lojas_simulated ON dim.dim_lojas(is_simulated);

-- =====================================================
-- DIMENSION: dim.dim_transportadoras
-- =====================================================
CREATE TABLE dim.dim_transportadoras (
    id_transportadora BIGSERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    tipo VARCHAR(50),
    regiao_atendida VARCHAR(100),
    prazo_medio_dias INTEGER,
    custo_medio NUMERIC(10,2),
    status VARCHAR(30) DEFAULT 'Ativa',
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_transportadoras_nome ON dim.dim_transportadoras(nome);

-- =====================================================
-- DIMENSION: dim.dim_clientes
-- =====================================================
CREATE TABLE dim.dim_clientes (
    id_cliente BIGSERIAL PRIMARY KEY,
    nome VARCHAR(150),
    tipo_cliente VARCHAR(30),
    cidade VARCHAR(100),
    estado VARCHAR(50),
    pais VARCHAR(50) DEFAULT 'Brasil',
    canal_origem VARCHAR(50),
    is_simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_clientes_cidade_estado ON dim.dim_clientes(cidade, estado);

-- =====================================================
-- FACT TABLE: fact.fato_vendas
-- =====================================================
CREATE TABLE fact.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim.dim_data(id_data),
    id_loja BIGINT NOT NULL REFERENCES dim.dim_lojas(id_loja),
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    id_cliente BIGINT REFERENCES dim.dim_clientes(id_cliente),
    quantidade INTEGER NOT NULL DEFAULT 1,
    preco_unitario NUMERIC(12,2) NOT NULL,
    desconto NUMERIC(12,2) DEFAULT 0,
    valor_bruto NUMERIC(12,2) NOT NULL,
    valor_liquido NUMERIC(12,2) NOT NULL,
    custo_produto NUMERIC(12,2),
    margem NUMERIC(12,2),
    margem_pct NUMERIC(5,2),
    canal VARCHAR(50),
    forma_pagamento VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Faturado',
    is_simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_vendas_data ON fact.fato_vendas(id_data);
CREATE INDEX idx_fato_vendas_loja ON fact.fato_vendas(id_loja);
CREATE INDEX idx_fato_vendas_produto ON fact.fato_vendas(id_produto);
CREATE INDEX idx_fato_vendas_cliente ON fact.fato_vendas(id_cliente);
CREATE INDEX idx_fato_vendas_simulated ON fact.fato_vendas(is_simulated);

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
    classificacao_estoque VARCHAR(30),
    giro_estoque NUMERIC(8,2),
    cobertura_dias INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_estoque_data ON fact.fato_estoque(id_data);
CREATE INDEX idx_fato_estoque_loja ON fact.fato_estoque(id_loja);
CREATE INDEX idx_fato_estoque_produto ON fact.fato_estoque(id_produto);
CREATE INDEX idx_fato_estoque_classificacao ON fact.fato_estoque(classificacao_estoque);

-- =====================================================
-- FACT TABLE: fact.fato_logistica
-- =====================================================
CREATE TABLE fact.fato_logistica (
    id_movimento BIGSERIAL PRIMARY KEY,
    id_data INTEGER NOT NULL REFERENCES dim.dim_data(id_data),
    id_produto BIGINT NOT NULL REFERENCES dim.dim_produtos(id_produto),
    id_loja_origem BIGINT REFERENCES dim.dim_lojas(id_loja),
    id_loja_destino BIGINT REFERENCES dim.dim_lojas(id_loja),
    id_transportadora BIGINT REFERENCES dim.dim_transportadoras(id_transportadora),
    quantidade INTEGER NOT NULL,
    data_pedido DATE,
    data_envio DATE,
    data_entrega DATE,
    prazo_previsto INTEGER,
    prazo_real INTEGER,
    custo_frete NUMERIC(12,2),
    status VARCHAR(30),
    atraso_dias INTEGER DEFAULT 0,
    is_simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fato_logistica_data ON fact.fato_logistica(id_data);
CREATE INDEX idx_fato_logistica_produto ON fact.fato_logistica(id_produto);
CREATE INDEX idx_fato_logistica_origem ON fact.fato_logistica(id_loja_origem);
CREATE INDEX idx_fato_logistica_destino ON fact.fato_logistica(id_loja_destino);
CREATE INDEX idx_fato_logistica_transportadora ON fact.fato_logistica(id_transportadora);
CREATE INDEX idx_fato_logistica_status ON fact.fato_logistica(status);
CREATE INDEX idx_fato_logistica_simulated ON fact.fato_logistica(is_simulated);

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

-- View: Produtos com variantes e imagens
CREATE OR REPLACE VIEW dim.vw_produtos_completo AS
SELECT 
    p.id_produto,
    p.sku,
    p.modelo,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    p.descricao,
    p.material,
    p.ano_modelo,
    p.preco,
    p.url_produto,
    v.id_variante,
    v.sku as sku_variante,
    v.tamanho,
    v.cor,
    v.preco as preco_variante,
    v.disponibilidade,
    i.id_imagem,
    i.tipo_imagem,
    i.url_imagem,
    i.imagem_principal
FROM dim.dim_produtos p
LEFT JOIN dim.dim_variantes v ON v.id_produto = p.id_produto
LEFT JOIN dim.dim_imagens i ON i.id_produto = p.id_produto
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
    l.nome_loja,
    l.cidade,
    l.estado,
    l.tipo_loja,
    p.modelo,
    p.categoria,
    p.subcategoria,
    p.plataforma,
    c.nome as cliente_nome,
    c.tipo_cliente
FROM fact.fato_vendas v
JOIN dim.dim_data d ON d.id_data = v.id_data
JOIN dim.dim_lojas l ON l.id_loja = v.id_loja
JOIN dim.dim_produtos p ON p.id_produto = v.id_produto
LEFT JOIN dim.dim_clientes c ON c.id_cliente = v.id_cliente;

-- View: Estoque com dimensões
CREATE OR REPLACE VIEW fact.vw_estoque_completo AS
SELECT 
    e.*,
    d.data,
    d.ano,
    d.mes,
    l.nome_loja,
    l.cidade,
    l.estado,
    p.modelo,
    p.categoria,
    p.plataforma,
    p.preco
FROM fact.fato_estoque e
JOIN dim.dim_data d ON d.id_data = e.id_data
JOIN dim.dim_lojas l ON l.id_loja = e.id_loja
JOIN dim.dim_produtos p ON p.id_produto = e.id_produto;

-- View: Logística com dimensões
CREATE OR REPLACE VIEW fact.vw_logistica_completo AS
SELECT 
    lg.*,
    d.data,
    d.ano,
    d.mes,
    p.modelo,
    p.categoria,
    lo.nome_loja as loja_origem,
    lo.cidade as cidade_origem,
    lo.estado as estado_origem,
    ld.nome_loja as loja_destino,
    ld.cidade as cidade_destino,
    ld.estado as estado_destino,
    t.nome as transportadora_nome
FROM fact.fato_logistica lg
JOIN dim.dim_data d ON d.id_data = lg.id_data
JOIN dim.dim_produtos p ON p.id_produto = lg.id_produto
LEFT JOIN dim.dim_lojas lo ON lo.id_loja = lg.id_loja_origem
LEFT JOIN dim.dim_lojas ld ON ld.id_loja = lg.id_loja_destino
LEFT JOIN dim.dim_transportadoras t ON t.id_transportadora = lg.id_transportadora;