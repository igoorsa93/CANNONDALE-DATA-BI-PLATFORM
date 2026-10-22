-- Seed: dim_lojas (SIMULATED - marked is_simulated = TRUE)
-- Lojas simuladas baseadas em cidades brasileiras reais de grande porte.

BEGIN;
INSERT INTO dim.dim_lojas (nome_loja, tipo_loja, endereco, cidade, estado, pais, cep, latitude, longitude, telefone, site, source_url, collection_date, is_simulated) VALUES
('Cannondale São Paulo — Vila Madalena','Loja Própria','Rua Harmonia, 1000','São Paulo','SP','Brasil','05438000',-23.5480,-46.6900,'(11) 3000-0001','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale São Paulo — Jardins','Loja Própria','Alameda Santos, 1500','São Paulo','SP','Brasil','01419000',-23.5630,-46.6680,'(11) 3000-0002','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Rio de Janeiro — Ipanema','Revendedor Autorizado','Rua Visconde de Pirajá, 500','Rio de Janeiro','RJ','Brasil','22410010',-22.9830,-43.2000,'(21) 3000-0003','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Belo Horizonte — Savassi','Revendedor Autorizado','Rua Pernambuco, 300','Belo Horizonte','MG','Brasil','30130010',-19.9160,-43.9380,'(31) 3000-0004','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Curitiba — Batel','Revendedor Autorizado','Av. Batel, 1600','Curitiba','PR','Brasil','80420090',-25.4330,-49.2790,'(41) 3000-0005','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Porto Alegre — Moinhos','Revendedor Autorizado','Rua Padre Chagas, 180','Porto Alegre','RS','Brasil','90570080',-30.0350,-51.1740,'(51) 3000-0006','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Florianópolis — Agronômica','Revendedor Autorizado','Av. Beira Mar, 2000','Florianópolis','SC','Brasil','88025001',-27.5830,-48.5520,'(48) 3000-0007','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Salvador — Barra','Revendedor Autorizado','Av. Oceânica, 1000','Salvador','BA','Brasil','40130150',-13.0000,-38.5200,'(71) 3000-0008','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Recife — Boa Viagem','Revendedor Autorizado','Av. Boa Viagem, 3000','Recife','PE','Brasil','51021200',-8.1180,-34.9060,'(81) 3000-0009','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Fortaleza — Aldeota','Revendedor Autorizado','Av. Dom Luís, 1100','Fortaleza','CE','Brasil','60160000',-3.7310,-38.5240,'(85) 3000-0010','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Centro de Distribuicao — Guarulhos','Centro de Distribuicao','Rod. Presidente Dutra, km 220','Guarulhos','SP','Brasil','07100000',-23.4660,-46.5330,'(11) 3000-0100','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE),
('Cannondale Centro de Distribuicao — Contagem','Centro de Distribuicao','BR-381, km 410','Contagem','MG','Brasil','32100000',-19.9400,-44.0500,'(31) 3000-0101','https://www.cannondale.com/pt-br','https://www.cannondale.com/pt-br/find-a-dealer','2026-10-05',TRUE);
COMMIT;

SELECT COUNT(*) AS total_lojas FROM dim.dim_lojas;