# Dicionário de Dados — Cannondale Data Platform

## dim.dim_data
| Coluna | Tipo | Descrição |
|---|---|---|
| id_data | INTEGER PK | YYYYMMDD |
| data | DATE | Data |
| ano, mes, dia, trimestre, semestre | INT | Componentes calendário |
| semana_ano, dia_semana | INT | Semana do ano / dia da semana (0=dom) |
| nome_dia_semana, nome_mes | VARCHAR | Nomes em PT |
| mes_ano, trimestre_ano | VARCHAR | Agregação |
| eh_fim_semana | BOOLEAN | Sá/do |
| eh_feriado_br, nome_feriado | BOOLEAN/VARCHAR | Feriados BR |

## dim.dim_produtos
| Coluna | Tipo | Descrição |
|---|---|---|
| id_produto | BIGSERIAL PK | Identificador interno |
| sku | VARCHAR UNIQUE | Código do produto |
| modelo | VARCHAR | Nome comercial oficial |
| categoria | VARCHAR | Road, Mountain, Electric, Active, Kids |
| subcategoria | VARCHAR | Race, Endurance, Gravel, Cross Country, Trail, E-MTB, E-Road, E-Urban, E-Touring, E-Cargo, E-Fitness, Urban, Fitness |
| plataforma | VARCHAR | Ex.: SuperSix EVO, Scalpel, Trail, Moterra Neo |
| descricao | TEXT | Descrição pública |
| material | VARCHAR | Carbono / Alumínio |
| ano_modelo | INT | Ano/modelo |
| preco | NUMERIC | NULL quando não público |
| preco_estimado | NUMERIC | Estimado (simulado) |
| moeda | VARCHAR(3) | BRL |
| url_produto, source_url | VARCHAR | Link oficial / fonte |
| source_name, collection_date | VARCHAR/DATE | Fonte e data da coleta |
| is_active | BOOLEAN | Ativo no catálogo |

## dim.dim_variantes
| Coluna | Tipo | Descrição |
|---|---|---|
| id_variante | BIGSERIAL PK | |
| id_produto | FK | Produto pai |
| sku | VARCHAR UNIQUE | SKU da variante |
| tamanho, cor | VARCHAR | |
| preco | NUMERIC | |
| disponibilidade | VARCHAR | |

## dim.dim_imagens
| Coluna | Tipo | Descrição |
|---|---|---|
| id_imagem | BIGSERIAL PK | |
| id_produto | FK | |
| modelo | VARCHAR | |
| tipo_imagem | VARCHAR | principal, lateral, traseira, detalhe, componente, ambiente |
| url_imagem | VARCHAR | URL oficial (Cloudfront) |
| imagem_principal, ordem | BOOLEAN/INT | |
| source_url, collection_date | | |

## dim.dim_lojas
| Coluna | Tipo | Descrição |
|---|---|---|
| id_loja | BIGSERIAL PK | |
| nome_loja, tipo_loja | VARCHAR | Loja Própria / Revendedor Autorizado / Centro de Distribuicao |
| endereco, cidade, estado, pais, cep | | |
| latitude, longitude | NUMERIC | |
| telefone, site, source_url | | |
| is_simulated | BOOLEAN | TRUE para dados simulados |

## dim.dim_transportadoras / dim.dim_clientes
Transportadoras: nome, tipo, regiao_atendida, prazo_medio_dias, custo_medio, status, is_simulated.
Clientes: nome, tipo_cliente (B2B/B2C), cidade, estado, canal_origem, is_simulated.

## fact.fato_vendas
id_venda PK, id_data FK, id_loja FK, id_produto FK, id_cliente FK, quantidade, preco_unitario, desconto, valor_bruto, valor_liquido, custo_produto, margem, margem_pct, canal, forma_pagamento, status, is_simulated.

## fact.fato_estoque
id_estoque PK, id_data/id_loja/id_produto FKs, estoque_inicial, entradas, saidas, transferencias, vendas, estoque_final, estoque_minimo, estoque_maximo, classificacao_estoque, giro_estoque, cobertura_dias.

## fact.fato_logistica
id_movimento PK, id_data/id_produto FKs, id_loja_origem/id_loja_destino FKs, id_transportadora FK, quantidade, data_pedido/data_envio/data_entrega, prazo_previsto/prazo_real, custo_frete, status, atraso_dias, is_simulated.

## meta.etl_log / meta.data_quality_log
Controle de execuções do ETL e registro de regras de qualidade.
