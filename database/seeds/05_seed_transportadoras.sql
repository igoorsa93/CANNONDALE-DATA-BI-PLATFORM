-- Seed: dim_transportadoras (SIMULATED where operational data not public)
BEGIN;
INSERT INTO dim.dim_transportadoras (nome, tipo, regiao_atendida, prazo_medio_dias, custo_medio, status, is_simulated) VALUES
('JSL Engenharia e Logística','Rodoviária','Nacional',4,350.00,'Ativa',TRUE),
('Total Express','Rodoviária Expressa','Nacional',3,180.00,'Ativa',TRUE),
('Loggi','Última Milha','Nacional (Capitais)',2,120.00,'Ativa',TRUE),
('Correios — SEDEX','Rodoviária Nacional','Nacional',5,95.00,'Ativa',FALSE),
('Patrus Transportes','Rodoviária','Sudeste/Sul',4,200.00,'Ativa',TRUE);
COMMIT;
SELECT COUNT(*) AS total_transportadoras FROM dim.dim_transportadoras;