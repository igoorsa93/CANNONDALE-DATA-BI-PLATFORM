-- Seed dim.dim_data: full calendar 2024-01-01 to 2027-12-31
-- Simple date dimension used by all fact tables.

BEGIN;
INSERT INTO dim.dim_data (id_data, data, ano, mes, dia, trimestre, semestre, semana_ano, dia_semana, nome_dia_semana, nome_mes, mes_ano, trimestre_ano, eh_fim_semana)
SELECT
    to_char(d, 'YYYYMMDD')::int AS id_data,
    d::date AS data,
    extract(year from d)::int AS ano,
    extract(month from d)::int AS mes,
    extract(day from d)::int AS dia,
    extract(quarter from d)::int AS trimestre,
    CASE WHEN extract(month from d) <= 6 THEN 1 ELSE 2 END AS semestre,
    extract(week from d)::int AS semana_ano,
    extract(dow from d)::int AS dia_semana,
    to_char(d, 'TMDay') AS nome_dia_semana,
    to_char(d, 'TMMonth') AS nome_mes,
    to_char(d, 'YYYY-MM') AS mes_ano,
    extract(year from d)::text || '-T' || extract(quarter from d)::text AS trimestre_ano,
    CASE WHEN extract(dow from d) IN (0, 6) THEN TRUE ELSE FALSE END AS eh_fim_semana
FROM generate_series('2024-01-01'::date, '2027-12-31'::date, '1 day'::interval) d;
COMMIT;

SELECT COUNT(*) AS total_dias FROM dim.dim_data;