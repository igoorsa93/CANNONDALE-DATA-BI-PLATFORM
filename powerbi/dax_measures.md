# Medidas DAX — Cannondale Data Platform

Organizadas por tabela/tema. Todas criadas no modelo *(separar em grupos de medidas)*.

## Vendas
```dax
Receita = SUM ( fato_vendas[valor_liquido] )

Unidades Vendidas = SUM ( fato_vendas[quantidade] )

Pedidos = DISTINCTCOUNT ( fato_vendas[id_venda] )

Ticket Médio = DIVIDE ( [Receita], [Unidades Vendidas] )

Margem = SUM ( fato_vendas[margem] )

Margem % = DIVIDE ( [Margem], [Receita] )

Receita LY = CALCULATE ( [Receita], SAMEPERIODLASTYEAR ( dim_data[data] ) )

Crescimento % = DIVIDE ( [Receita] - [Receita LY], [Receita LY] )
```

## Estoque
```dax
Estoque Atual = CALCULATE ( SUM ( fato_estoque[estoque_final] ), LASTDATE ( dim_data[data] ) )

% SKU em Excesso = DIVIDE ( COUNTROWS ( FILTER ( fato_estoque, fato_estoque[classificacao_estoque] = "Excesso" ) ), COUNTROWS ( fato_estoque ) )

% SKU em Atenção = DIVIDE ( COUNTROWS ( FILTER ( fato_estoque, fato_estoque[classificacao_estoque] = "Atenção" ) ), COUNTROWS ( fato_estoque ) )

% SKU Crítico = DIVIDE ( COUNTROWS ( FILTER ( fato_estoque, fato_estoque[classificacao_estoque] = "Crítico" ) ), COUNTROWS ( fato_estoque ) )

Giro de Estoque = DIVIDE ( [Unidades Vendidas], AVERAGE ( fato_estoque[estoque_final] ) )

Cobertura (dias) = AVERAGE ( fato_estoque[cobertura_dias] )

Ruptura = COUNTROWS ( FILTER ( fato_estoque, fato_estoque[classificacao_estoque] = "Ruptura" ) )
```

## Logística
```dax
Pedidos em Trânsito = COUNTROWS ( FILTER ( fato_logistica, fato_logistica[status] = "Em trânsito" ) )

Lead Time Médio = AVERAGE ( fato_logistica[prazo_real] )

% Entrega no Prazo = DIVIDE ( COUNTROWS ( FILTER ( fato_logistica, fato_logistica[atraso_dias] = 0 && fato_logistica[status] = "Entregue" ) ), COUNTROWS ( fato_logistica ) )

OTIF = DIVIDE ( COUNTROWS ( FILTER ( fato_logistica, fato_logistica[atraso_dias] = 0 && fato_logistica[status] = "Entregue" ) ), COUNTROWS ( fato_logistica ) )

Custo Logístico = SUM ( fato_logistica[custo_frete] )
```

## Regras de modelagem
- Medidas na tabela `_medidas` dedicada ou na primeira tabela fato.
- Usar `DIVIDE` em vez de `/` para evitar divisão por zero.
- Medidas de estoque usam `LASTDATE`/`CALCULATE` para "estoque atual".
- `Receita LY` usa `SAMEPERIODLASTYEAR`; exige tabela `dim_data` marcada como tabela de data.
