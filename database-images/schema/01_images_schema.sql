-- Cannondale Images Database Schema
-- Created: 2026-10-07

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS images;

-- Tabela principal de imagens
CREATE TABLE images.imagens (
    id_imagem BIGSERIAL PRIMARY KEY,
    id_produto VARCHAR(50) NOT NULL,
    modelo VARCHAR(150) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    url_produto VARCHAR(500),
    url_imagem_original VARCHAR(500) NOT NULL,
    url_imagem_widen VARCHAR(500),
    tipo_imagem VARCHAR(30) NOT NULL,
    imagem_principal BOOLEAN DEFAULT FALSE,
    ordem INTEGER DEFAULT 0,
    nome_arquivo VARCHAR(200),
    caminho_local VARCHAR(500),
    minio_object_name VARCHAR(500),
    minio_bucket VARCHAR(100) DEFAULT 'cannondale-images',
    hash_md5 VARCHAR(32),
    tamanho_bytes BIGINT,
    largura INTEGER,
    altura INTEGER,
    formato VARCHAR(10),
    data_coleta DATE DEFAULT CURRENT_DATE,
    data_download TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING',
    erro TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_imagens_id_produto ON images.imagens(id_produto);
CREATE INDEX idx_imagens_categoria ON images.imagens(categoria);
CREATE INDEX idx_imagens_tipo ON images.imagens(tipo_imagem);
CREATE INDEX idx_imagens_principal ON images.imagens(imagem_principal) WHERE imagem_principal = TRUE;
CREATE INDEX idx_imagens_status ON images.imagens(status);
CREATE INDEX idx_imagens_hash ON images.imagens(hash_md5);

-- Tabela de metadados de download
CREATE TABLE images.download_log (
    id_log BIGSERIAL PRIMARY KEY,
    id_imagem BIGINT REFERENCES images.imagens(id_imagem),
    url_tentada VARCHAR(500),
    status VARCHAR(20),
    codigo_http INTEGER,
    tamanho_bytes BIGINT,
    duracao_ms INTEGER,
    erro TEXT,
    tentativas INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_download_log_id_imagem ON images.download_log(id_imagem);
CREATE INDEX idx_download_log_status ON images.download_log(status);

-- View: Imagens por produto
CREATE OR REPLACE VIEW images.vw_imagens_por_produto AS
SELECT 
    i.id_produto,
    i.modelo,
    i.categoria,
    COUNT(*) as total_imagens,
    COUNT(CASE WHEN i.imagem_principal THEN 1 END) as tem_imagem_principal,
    STRING_AGG(i.url_imagem_widen, '; ') as urls_widen,
    STRING_AGG(i.caminho_local, '; ') as caminhos_locais
FROM images.imagens i
WHERE i.status = 'OK'
GROUP BY i.id_produto, i.modelo, i.categoria;

-- View: Resumo de imagens por categoria
CREATE OR REPLACE VIEW images.vw_resumo_imagens_categoria AS
SELECT 
    categoria,
    COUNT(DISTINCT id_produto) as produtos_com_imagem,
    COUNT(*) as total_imagens,
    SUM(tamanho_bytes) as tamanho_total_bytes,
    AVG(tamanho_bytes) as tamanho_medio_bytes,
    COUNT(CASE WHEN status = 'OK' THEN 1 END) as imagens_ok,
    COUNT(CASE WHEN status != 'OK' THEN 1 END) as imagens_falha
FROM images.imagens
GROUP BY categoria
ORDER BY categoria;