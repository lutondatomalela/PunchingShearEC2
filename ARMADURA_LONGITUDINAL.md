# Armadura longitudinal e altura útil automática

PunchingShearEC2 1.14.0 · 12 de setembro de 2026  
[Repositório](https://github.com/lutondatomalela/PunchingShearEC2)

## 1. Escolher o modo de introdução

Em **Dados → Laje e armadura longitudinal → Introdução da armadura**, escolha:

- **Automático · base e reforço**: introduza a espessura, o recobrimento, a disposição das camadas e as malhas. O programa calcula As,x, As,y, dx, dy e d.
- **Manual · d e áreas de armadura**: conserva a introdução existente de áreas médias e alturas úteis. Com dx e dy preenchidos, d continua a ser a média das duas alturas.

Os conjuntos anteriores abrem em modo manual e conservam os valores introduzidos. A mudança de versão exige novo cálculo para obter resultados atualizados. Ao passar de automático para manual, os valores calculados visíveis ficam disponíveis como ponto de partida; para introduzir apenas d, deixe dx e dy vazios.

## 2. Definir a geometria das camadas

Preencha os seguintes dados em milímetros:

| Campo | Significado |
|---|---|
| Espessura h | Espessura total da laje na ligação. |
| Recobrimento longitudinal | Distância da face tracionada à superfície exterior dos varões longitudinais mais próximos dessa face. |
| Camada exterior | Direção X ou Y mais próxima da face tracionada. |
| Afastamento X/Y | Distância livre entre as envolventes das duas camadas ortogonais; zero quando estão em contacto. |

O recobrimento longitudinal é independente do recobrimento dos estribos introduzido no separador **Armadura**. Se existirem estribos ou outros varões exteriores às armaduras longitudinais, a sua espessura deve estar incluída na distância indicada para o cálculo de d.

O modo automático representa **uma camada de eixos coplanares por direção**, com base e reforço intercalados. O maior diâmetro de cada direção define a envolvente da respetiva camada. Não representa reforço colocado sobre a malha base, agrupamentos de varões ou várias camadas paralelas. Para esses pormenores, use a introdução manual das áreas e alturas úteis equivalentes.

## 3. Introduzir a base e o reforço

Defina separadamente em X e Y:

1. O diâmetro da armadura base.
2. O diâmetro do reforço, ou **Sem reforço**.
3. O espaçamento comum às duas malhas.

Os diâmetros disponíveis são 6, 8, 10, 12, 16, 20, 25, 32 e 40 mm. A base pode ter qualquer diâmetro desta série.

A série de espaçamentos é **100, 125, 150, 175, 200, 250 e 300 mm**. Quando há reforço, os seus varões são colocados a meio do intervalo entre os varões da base. Para que também esse passo final pertença à série prática, o modo automático admite malhas com reforço a 200, 250 ou 300 mm, resultando em intercalação a 100, 125 ou 150 mm. Outros pormenores podem ser definidos pelo modo manual; não são arredondados silenciosamente.

**Ø10 // 200 + Ø10 // 200 = Ø10 // 100**, quando os varões são intercalados a meio e pertencem à mesma camada. Com diâmetros diferentes, o relatório conserva ambas as parcelas; não as substitui por um diâmetro fictício.

O programa verifica também a distância livre entre varões adjacentes, em função dos diâmetros e da dimensão máxima do agregado. A seleção de um espaçamento prático não dispensa os requisitos de pormenorização aplicáveis ao projeto.

## 4. Áreas e alturas úteis calculadas

Para cada direção, com diâmetros e espaçamento em milímetros:

`As [cm²/m] = (π / 4) × (φbase² + φreforço²) × 10 / s`

Sem reforço, a segunda parcela é nula. Não é necessário introduzir um espaçamento adicional: base e reforço partilham o passo s.

Sendo X a camada exterior, φX e φY os maiores diâmetros de cada direção, c o recobrimento longitudinal e aXY o afastamento entre camadas:

`aX = c + φX / 2`

`aY = c + φX + aXY + φY / 2`

`dx = (h - aX) / 1000 ; dy = (h - aY) / 1000`

`d = (dx + dy) / 2`

As distâncias aX e aY são medidas desde a face tracionada até aos eixos das armaduras. dx e dy são medidos desde a face comprimida e expressos em metros. Se Y for a camada exterior, a ordem é invertida. A média das alturas úteis segue a expressão (6.32) da NP EN 1992-1-1:2010; a disposição geométrica das camadas é a hipótese explícita deste modo de entrada.

Exemplo com **h = 250 mm**, **c = 30 mm**, camadas X/Y em contacto e a mesma combinação nas duas direções:

| Combinação em cada direção | As em cada direção (cm²/m) | d médio (mm) |
|---|---:|---:|
| Ø10 // 200 + Ø10 // 200 | 7,854 | 210 |
| Ø10 // 200 + Ø12 // 200 | 9,582 | 208 |
| Ø10 // 200 + Ø16 // 200 | 13,980 | 204 |
| Ø10 // 200 + Ø20 // 200 | 19,635 | 200 |
| Ø10 // 200 + Ø25 // 200 | 28,471 | 195 |
| Ø10 // 200 + Ø32 // 200 | 44,139 | 188 |

Estes valores de d dependem de h, c e da disposição indicada; não são valores gerais associados a cada diâmetro.

## 5. Armadura a considerar na faixa de cálculo

As,x e As,y devem representar as armaduras de tração aderentes médias na faixa do apoio acrescida de 3d para cada lado, limitada pelos bordos livres, conforme 6.4.4(1).

Utilize uma combinação automática quando a base e o reforço definidos representarem essa faixa de cálculo. Se o reforço ocupar apenas uma parte da faixa, não adote a soma integral como área média: determine a área média e a altura útil equivalente pelo modo manual. A extensão e a amarração dos reforços continuam a fazer parte do pormenor do projeto.

## 6. Aplicar a vários pilares

1. Abra **Pilares…** e filtre o piso ou grupo pretendido.
2. Selecione as ligações e abra **Editar seleção…**.
3. Escolha **Atualizar os campos assinalados** para substituir os parâmetros existentes. **Preencher apenas campos vazios** conserva os valores já preenchidos, incluindo o modo manual.
4. No separador **Laje**, assinale **Modo de armadura longitudinal** e escolha **Automático**.
5. Em **Armadura longitudinal automática**, assinale e preencha h, recobrimento, ordem das camadas, afastamento e malhas X/Y que pretende aplicar.
6. Se necessário, guarde a predefinição do piso ou grupo e aplique à seleção.
7. Execute **Calcular seleção** e guarde o conjunto.

d e As são derivados no modo automático. Para os alterar diretamente em lote, escolha primeiro o modo manual. O programa valida a alteração antes de a aplicar ao conjunto.

Os parâmetros X/Y referem-se aos eixos do caso. Ao rodar a ligação 90° ou 270°, o programa troca os dados das malhas e a identificação da camada exterior, juntamente com as grandezas direcionais existentes. Uma rotação de 180° conserva a ordem das duas direções.

## 7. Consultar e exportar

A alteração de diâmetros, espaçamentos, espessura, recobrimento ou disposição invalida os resultados anteriores. Prima **F5** ou calcule a seleção para atualizar as verificações.

A memória PDF/TXT e o resultado JSON registam a definição das malhas, a hipótese de disposição, as áreas e o cálculo de dx, dy e d. A exportação XLSX individual inclui a folha **ArmaduraLongitudinal**. O relatório do conjunto conserva o filtro de resultados calculados e atualizados e identifica a cobertura parcial de combinações.

Em **Exemplos…**, abra **Armadura longitudinal - base e reforço, altura útil automática** para experimentar um caso fictício com Ø10 // 200 + Ø12 // 200 nas duas direções.
