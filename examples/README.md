# Exemplos de cálculo - PunchingShearEC2 1.9.0

Os exemplos usam N, N.m e m. Todas as amarrações abrem por confirmar. Hipóteses de beta manual, simplificado ou combinações conservadoras necessitam de confirmação no projeto. Os exemplos 25 a 29 ilustram o editor de aberturas.

| Exemplo | Ficheiro | Estado esperado |
|---|---|---|
| Pilar interior - carga concêntrica, 300 kN | [01_interior_carga_concentrica.json](01_interior_carga_concentrica.json) | PASS_WITHOUT |
| Pilar de bordo - excentricidade perpendicular interior | [02_bordo_excentricidade_interior.json](02_bordo_excentricidade_interior.json) | DETAIL_PENDING |
| Pilar interior - armadura de punçoamento, 600 kN | [03_interior_armadura_puncoamento.json](03_interior_armadura_puncoamento.json) | DETAIL_PENDING |
| Pilar interior - limite resistente com armadura | [04_interior_limite_resistente.json](04_interior_limite_resistente.json) | FAIL_MAX |
| Pilar circular interior - esforço transverso, 450 kN | [05_circular_interior.json](05_circular_interior.json) | DETAIL_PENDING |
| Pilar de canto - excentricidades interiores | [06_canto_excentricidades_interiores.json](06_canto_excentricidades_interiores.json) | DETAIL_PENDING |
| Sapata circular - carga concêntrica e pressão uniforme | [07_sapata_carga_concentrica.json](07_sapata_carga_concentrica.json) | REQUIRES_REINFORCEMENT |
| Pilar interior - setor ineficaz de 40 graus | [08_interior_setor_ineficaz_40graus.json](08_interior_setor_ineficaz_40graus.json) | BETA_PENDING |
| Pilar interior - resistência máxima na face | [09_interior_resistencia_face.json](09_interior_resistencia_face.json) | FAIL_U0 |
| Pilar de bordo - g = 400 mm, VEd = 300 kN | [10_bordo_400mm_300kN.json](10_bordo_400mm_300kN.json) | BETA_PENDING |
| Pilar de bordo - g = 400 mm, VEd = 400 kN | [11_bordo_400mm_400kN.json](11_bordo_400mm_400kN.json) | BETA_PENDING |
| Pilar de bordo - g = 800 mm, VEd = 550 kN | [12_bordo_800mm_550kN.json](12_bordo_800mm_550kN.json) | BETA_PENDING |
| Pilar de bordo - g = 400 mm, flexão biaxial | [13_bordo_400mm_flexao_biaxial.json](13_bordo_400mm_flexao_biaxial.json) | BETA_PENDING |
| Pilar de bordo - g = 0 mm, VEd = 594 kN | [14_bordo_000mm_594kN.json](14_bordo_000mm_594kN.json) | DETAIL_PENDING |
| Pilar de bordo - g = 343 mm, VEd = 594 kN | [15_bordo_343mm_594kN.json](15_bordo_343mm_594kN.json) | BETA_PENDING |
| Pilar de bordo - g = 1 mm, VEd = 594 kN | [16_bordo_001mm_594kN.json](16_bordo_001mm_594kN.json) | BETA_PENDING |
| Pilar de bordo - g = 0 mm, beta simplificado | [17_bordo_000mm_metodo_simplificado.json](17_bordo_000mm_metodo_simplificado.json) | DETAIL_PENDING |
| Pilar de bordo - g = 343 mm, beta simplificado | [18_bordo_343mm_metodo_simplificado.json](18_bordo_343mm_metodo_simplificado.json) | DETAIL_PENDING |
| Pilar interior - flexão biaxial, expressão (6.43) | [19_interior_flexao_biaxial_643.json](19_interior_flexao_biaxial_643.json) | PASS_WITHOUT |
| Pilar interior - flexão uniaxial, expressão (6.39) | [20_interior_flexao_uniaxial_639.json](20_interior_flexao_uniaxial_639.json) | PASS_WITHOUT |
| Pilar de bordo - excentricidade exterior uniaxial | [21_bordo_excentricidade_exterior_uniaxial.json](21_bordo_excentricidade_exterior_uniaxial.json) | DETAIL_PENDING |
| Pilar de bordo - excentricidade exterior biaxial | [22_bordo_exterior_combinacao_biaxial.json](22_bordo_exterior_combinacao_biaxial.json) | DETAIL_PENDING |
| Pilar de canto - excentricidade exterior biaxial | [23_canto_exterior_combinacao_biaxial.json](23_canto_exterior_combinacao_biaxial.json) | DETAIL_PENDING |
| Pilar de canto - definição do modelo biaxial | [24_canto_exterior_modelo_por_definir.json](24_canto_exterior_modelo_por_definir.json) | BETA_PENDING |
| Pilar interior - abertura quadrada a 600 mm | [25_abertura_quadrada_600mm.json](25_abertura_quadrada_600mm.json) | BETA_PENDING |
| Pilar interior - abertura circular descentrada | [26_abertura_circular_descentrada.json](26_abertura_circular_descentrada.json) | BETA_PENDING |
| Pilar interior - abertura retangular alongada | [27_abertura_retangular_alongada.json](27_abertura_retangular_alongada.json) | BETA_PENDING |
| Pilar interior - abertura além de 6d | [28_abertura_distancia_superior_6d.json](28_abertura_distancia_superior_6d.json) | PASS_WITHOUT |
| Pilar interior - duas aberturas ortogonais | [29_duas_aberturas_ortogonais.json](29_duas_aberturas_ortogonais.json) | BETA_PENDING |

## Descrição técnica

**Pilar interior - carga concêntrica, 300 kN**

Ligação laje-pilar interior de secção quadrada, sujeita a esforço transverso sem transferência de momentos.

**Pilar de bordo - excentricidade perpendicular interior**

Pilar encostado ao bordo livre, com momento de transferência perpendicular dirigido para o interior da laje. Aplicação de (6.44).

**Pilar interior - armadura de punçoamento, 600 kN**

Ligação interior com solicitação superior à resistência sem armadura específica; dimensionamento e distribuição de estribos verticais.

**Pilar interior - limite resistente com armadura**

Verificação do limite kmax vRd,c para uma ligação interior sujeita a 1000 kN.

**Pilar circular interior - esforço transverso, 450 kN**

Ligação interior com secção circular e perímetros concêntricos.

**Pilar de canto - excentricidades interiores**

Pilar encostado a dois bordos livres, com ambas as excentricidades dirigidas para o interior. Aplicação de (6.46).

**Sapata circular - carga concêntrica e pressão uniforme**

Sapata com apoio centrado e pressão líquida de equilíbrio uniforme; pesquisa do perímetro condicionante entre a face e 2d.

**Pilar interior - setor ineficaz de 40 graus**

Abertura representada por um setor de tangentes entre -20 e +20 graus. Geometria reduzida; o coeficiente beta requer fundamentação específica.

**Pilar interior - resistência máxima na face**

Verificação de u0 sob esforço transverso de 2000 kN, com aplicação da resistência máxima de AC:2012.

**Pilar de bordo - g = 400 mm, VEd = 300 kN**

Pilar de secção 0,25 x 0,70 m afastado 400 mm do bordo; comparação geométrica entre contorno aberto e fechado. Beta por fundamentar.

**Pilar de bordo - g = 400 mm, VEd = 400 kN**

Ligação com afastamento de 400 mm e esforço transverso de 400 kN. A verificação resistente depende da fundamentação de beta.

**Pilar de bordo - g = 800 mm, VEd = 550 kN**

Pilar com afastamento de 800 mm; avaliação dos comprimentos dos contornos de controlo. Beta por fundamentar.

**Pilar de bordo - g = 400 mm, flexão biaxial**

Pilar de secção 0,25 x 0,70 m; d = 202 mm; VEd = 371 kN, MEdx = -10 kN.m e MEdy = -65 kN.m. Beta por fundamentar.

**Pilar de bordo - g = 0 mm, VEd = 594 kN**

Pilar de secção 0,70 x 0,25 m; d = 352 mm; MEdx = -23 kN.m e MEdy = -64 kN.m. Afastamento livre de 0 mm. Aplicação de (6.44) com excentricidade normal interior.

**Pilar de bordo - g = 343 mm, VEd = 594 kN**

Pilar de secção 0,70 x 0,25 m; d = 352 mm; MEdx = -23 kN.m e MEdy = -64 kN.m. Afastamento livre de 343 mm. Beta requer fundamentação para a geometria afastada.

**Pilar de bordo - g = 1 mm, VEd = 594 kN**

Pilar de secção 0,70 x 0,25 m; d = 352 mm; MEdx = -23 kN.m e MEdy = -64 kN.m. Afastamento livre de 1 mm. Beta requer fundamentação para a geometria afastada.

**Pilar de bordo - g = 0 mm, beta simplificado**

VEd = 594 kN; d = 352 mm; secção 0,70 x 0,25 m. Exemplo didático com beta = 1,40: pressupõe estabilidade independente dos pórticos laje-pilar e diferença entre vãos adjacentes até 25%. Estas condições têm de ser confirmadas em cada projeto.

**Pilar de bordo - g = 343 mm, beta simplificado**

VEd = 594 kN; d = 352 mm; secção 0,70 x 0,25 m. Exemplo didático com beta = 1,40: pressupõe estabilidade independente dos pórticos laje-pilar e diferença entre vãos adjacentes até 25%. Estas condições têm de ser confirmadas em cada projeto.

**Pilar interior - flexão biaxial, expressão (6.43)**

Pilar de secção 0,30 x 0,80 m; d = 200 mm; VEd = 300 kN, MEdx = 15 kN.m e MEdy = 40 kN.m. Aplicação da aproximação (6.43), com correspondência explícita entre os eixos da norma e da interface.

**Pilar interior - flexão uniaxial, expressão (6.39)**

Pilar quadrado de 0,40 m; VEd = 300 kN e MEdy = 90 kN.m. Aplicação uniaxial de (6.39), com W de (6.40)-(6.41) e k do Quadro 6.1.

**Pilar de bordo - excentricidade exterior uniaxial**

Pilar quadrado encostado ao bordo; VEd = 200 kN e MEdx = -20 kN.m, dirigido para o exterior. Os momentos são introduzidos no centro do pilar e transportados uma única vez para o centro do perímetro; aplicação de (6.39).

**Pilar de bordo - excentricidade exterior biaxial**

Pilar quadrado encostado ao bordo; VEd = 180 kN, MEdx = -15 kN.m e MEdy = 10 kN.m. Exemplo com a opção de soma conservadora das majorações de (6.39) selecionada; esta combinação é uma hipótese adicional do programa.

**Pilar de canto - excentricidade exterior biaxial**

Pilar quadrado encostado a dois bordos; VEd = 60 kN, MEdx = -5 kN.m e MEdy = -7 kN.m. Exemplo com a opção de soma conservadora das majorações de (6.39) selecionada e k do Quadro 6.1 por direção.

**Pilar de canto - definição do modelo biaxial**

Mesma geometria e ações do exemplo 23, sem seleção da combinação conservadora. A determinação de beta fica pendente até definir o modelo de transferência biaxial.

**Pilar interior - abertura quadrada a 600 mm**

Abertura quadrada de 0,40 m, centrada à direita de um pilar de 0,40 m, com 0,60 m livres entre faces. Tangentes calculadas a partir da geometria; beta por fundamentar.

**Pilar interior - abertura circular descentrada**

Abertura circular de 0,30 m, com centro em X = 0,80 m e Y = 0,60 m. Distância mínima e tangentes exatas ao círculo; beta por fundamentar.

**Pilar interior - abertura retangular alongada**

Abertura de 1,20 x 0,20 m, centrada no eixo +X. Largura equivalente da Figura 6.14 e respetivo setor calculados automaticamente; beta por fundamentar.

**Pilar interior - abertura além de 6d**

Abertura quadrada com distância livre de 1,60 m para d = 0,20 m. Mantida na planta e no registo, sem dedução do perímetro por 6.4.2(3).

**Pilar interior - duas aberturas ortogonais**

Abertura quadrada no lado +X e circular no lado +Y, ambas com distância livre de 0,60 m. União dos setores de influência sem duplicar sobreposições; beta por fundamentar.


## Modelo de vários pisos

A pasta `importacao` inclui `Modelo_Pilares.csv`, `Modelo_Nos.csv` e `Modelo_Ligacoes.json`: exemplo fictício de edifício de escritórios, com dois pisos, dois pilares e combinações estáticas e CQC. O conjunto abre em **Pilares → Abrir conjunto** e deixa a laje por preencher. A configuração dos eixos, valores de referência e sequência de utilização constam de [MODELO_POR_PISO.md](../MODELO_POR_PISO.md).


## Grupos e exportação parcial — 1.13.0

Abra `importacao/Grupos_Ligacoes.json` em **Pilares → Abrir conjunto**. O exemplo fictício contém quatro ligações em dois pisos, dois grupos e duas combinações calculadas. O relatório predefinido exporta apenas essas duas combinações e identifica a ligação como parcial (2/3).


O exemplo `30_armadura_longitudinal_automatica.json` define duas malhas Ø10 // 200 + Ø12 // 200 por direção, h = 250 mm, recobrimento longitudinal = 30 mm e X exterior. Produz As = 9,582 cm²/m e d = 0,208 m. É um exemplo fictício do novo modo automático.
