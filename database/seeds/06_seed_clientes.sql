-- Seed: dim_clientes (SIMULATED)
BEGIN;
INSERT INTO dim.dim_clientes (nome, tipo_cliente, cidade, estado, pais, canal_origem, is_simulated) VALUES
('Atelier Bike SP','B2B Revenda','São Paulo','SP','Brasil','Revenda',TRUE),
('Ciclismo Elite RJ','B2B Revenda','Rio de Janeiro','RJ','Brasil','Revenda',TRUE),
('MTB Hub BH','B2B Revenda','Belo Horizonte','MG','Brasil','Revenda',TRUE),
('Velo Store Curitiba','B2B Revenda','Curitiba','PR','Brasil','Revenda',TRUE),
('Ride Sul POA','B2B Revenda','Porto Alegre','RS','Brasil','Revenda',TRUE),
('João Pessoa Souza','B2C Pessoa Física','São Paulo','SP','Brasil','Loja Física',TRUE),
('Maria Fernanda Lima','B2C Pessoa Física','Rio de Janeiro','RJ','Brasil','Online',TRUE),
('Carlos Eduardo Santos','B2C Pessoa Física','Belo Horizonte','MG','Brasil','Loja Física',TRUE),
('Ana Beatriz Rocha','B2C Pessoa Física','Florianópolis','SC','Brasil','Online',TRUE),
('Pedro Henrique Alves','B2C Pessoa Física','Curitiba','PR','Brasil','Loja Física',TRUE);
COMMIT;
SELECT COUNT(*) AS total_clientes FROM dim.dim_clientes;