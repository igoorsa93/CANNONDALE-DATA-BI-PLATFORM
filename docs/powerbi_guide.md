# Guia Power BI — Cannondale Data Platform

## Conexão
1. Power BI Desktop -> Obter dados -> PostgreSQL.
2. Servidor: `localhost:5433`, Banco: `cannondale`, usuário `postgres`, senha `postgres`.
3. Importar as tabelas dims e facts + views de `sql`.
4. Marcar `dim_data` como tabela de data.
5. Importar tema `powerbi/cannondale_theme.json`.

## Páginas
### 01 — Executive
Cards: Receita, Unidades, Ticket Médio, Margem, Margem %, Estoque, Pedidos em Trânsito, Entregas no Prazo.
Visuais: tendência de vendas (linha), performance por categoria (colunas), performance regional (mapa/colunas).

### 02 — Vendas
Receita mensal, unidades, ticket médio, ranking de produtos/lojas, categoria, região, margem, evolução temporal.

### 03 — Logística
Pedidos, entregas, atrasos, prazo médio, OTIF, custo logístico, transportadoras, origem/destino. Mapa quando coordenadas válidas.

### 04 — Estoque
Estoque atual, crítico, atenção, excesso, ruptura, giro, cobertura, estoque por loja/produto.
Indicadores: % SKU Excesso, % SKU Atenção, % SKU Crítico.

### 05 — Catálogo
Experiência de catálogo: foto (url_imagem), modelo, categoria, preço, especificações, vendas, estoque, margem. Selecionar modelo via slicer.

## Regras visuais (identidade Cannondale)
- Paleta: verde (#00693C), preto (#111111), branco, cinza.
- Fundo claro, tipografia moderna, espaço negativo, hierarquia clara, contraste alto.
- Evitar 3D, excesso de pizza, gradientes fortes, sombras pesadas, poluição visual.
- Fotografia de produto como elemento de destaque no catálogo.
