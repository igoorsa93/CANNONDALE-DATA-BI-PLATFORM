-- Schema simplificado: apenas 3 tabelas fato + dimensões mínimas
CREATE SCHEMA IF NOT EXISTS core;

-- Dimensões mínimas
CREATE TABLE core.dim_data (
    id_data INTEGER PRIMARY KEY,
    data DATE NOT NULL UNIQUE,
    ano INTEGER, mes INTEGER, dia INTEGER,
    mes_ano VARCHAR(7)
);

CREATE TABLE core.dim_produto (
    id_produto BIGSERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE,
    modelo VARCHAR(100),
    categoria VARCHAR(50)
);

CREATE TABLE core.dim_loja (
    id_loja BIGSERIAL PRIMARY KEY,
    nome_loja VARCHAR(150),
    cidade VARCHAR(100),
    estado VARCHAR(50)
);

-- 3 Tabelas principais
CREATE TABLE core.fato_vendas (
    id_venda BIGSERIAL PRIMARY KEY,
    id_data INTEGER REFERENCES core.dim_data(id_data),
    id_loja INTEGER REFERENCES core.dim_loja(id_loja),
    id_produto INTEGER REFERENCES core.dim_produto(id_produto),
    quantidade INTEGER,
    valor_liquido NUMERIC(12,2),
    data_venda DATE
);

CREATE TABLE core.fato_estoque (
    id_estoque BIGSERIAL PRIMARY KEY,
    id_data INTEGER REFERENCES core.dim_data(id_data),
    id_loja INTEGER REFERENCES core.dim_loja(id_loja),
    id_produto INTEGER REFERENCES core.dim_produto(id_produto),
    estoque_final INTEGER,
    classificacao VARCHAR(30)
);

CREATE TABLE core.dim_loja_resumo (
    id_loja INTEGER PRIMARY KEY REFERENCES core.dim_loja(id_loja),
    total_vendas NUMERIC(14,2),
    total_estoque INTEGER,
    ultima_atualizacao DATE
);