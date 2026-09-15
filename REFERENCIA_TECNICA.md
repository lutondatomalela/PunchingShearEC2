# Referência técnica — PunchingShearEC2 1.15.0

Verificação de punçoamento de lajes de betão armado segundo a **NP EN 1992-1-1:2010 + AC:2012 + A1:2019**, com o Anexo Nacional português. Os relatórios identificam este referencial; não é implementada a segunda geração do EC2.

[Repositório do projeto](https://github.com/lutondatomalela/PunchingShearEC2)

A versão 1.15.0 acrescenta **seleção de barras por listas e intervalos, extensão à prumada e gravação da configuração do modelo sem selecionar novas ligações**. A revisão dos eixos atualiza os esforços das ligações existentes, conserva os seus dados individuais e exige novo cálculo dos casos afetados. Consulte [MODELO_POR_PISO.md](MODELO_POR_PISO.md).

Mantém-se a **armadura longitudinal por combinação de base e reforço, com cálculo automático de As,x, As,y, dx, dy e d**. A opção manual é conservada. O novo modo está disponível por ligação e na edição em lote, conserva a disposição das camadas ao rodar o caso e documenta as entradas e a derivação nos relatórios. Consulte [ARMADURA_LONGITUDINAL.md](ARMADURA_LONGITUDINAL.md).

Mantêm-se os grupos, predefinições e relatórios apenas com resultados calculados e atualizados. As designações próprias da aplicação continuam a usar terminologia neutra.

Consulte [GRUPOS_E_RELATORIOS.md](GRUPOS_E_RELATORIOS.md) para o procedimento da versão 1.13.0. A preparação das ligações a partir de tabelas continua documentada em [MODELO_POR_PISO.md](MODELO_POR_PISO.md). As expressões de resistência existentes são conservadas; o modo automático transforma a disposição das armaduras nas entradas d e As utilizadas nessas verificações. Casos CQC/SRSS permanecem pendentes de resultantes fundamentadas com tratamento modal adequado.

O tema utiliza Tkinter/ttk, sem novas dependências. Os casos JSON existentes conservam as chaves e unidades. [VALIDACAO.md](VALIDACAO.md), [CHANGELOG.md](CHANGELOG.md) e o [catálogo de exemplos](examples/README.md) documentam o âmbito.

## Interface

Os separadores **Dados**, **Método β** e **Armadura** organizam as entradas. À direita, **Planta**, **Verificações**, **Fiadas** e **Memória** partilham a conclusão global e os indicadores da execução. A planta acompanha as entradas; para alterar dimensões com o rato, ative **Editar pilar**.

Use **Exemplos…** para pesquisar os 30 casos. **F5** calcula; **Ctrl+O** abre; **Ctrl+S** guarda; **Ctrl+N** inicia um caso; **F1** abre a ajuda. Os botões de exportação ficam desativados enquanto não existir um resultado atualizado.

Use **Pilares…** para importar XLSX/CSV/TSV, escolher uma ligação e guardar/abrir o conjunto. Em **Dados → Origem dos esforços…**, escolha entre equilíbrio dos tramos, resultante integral da ligação ou esforços manuais fundamentados. N acumulado não é adotado como carga da laje. O programa exige a compatibilidade de eixos, sinais, extremos e combinações; não integra resultados locais de elementos finitos. Inclui um [XLSX de exemplo](examples/importacao/Exemplo_importacao.xlsx) e um [conjunto preparado](examples/importacao/Ligacoes_exemplo.json).

Para a tabela de barras com `Member/Node/Case`, `FX`, `MY`, `MZ`, `Name` e `Story`, a associação de colunas é automática; `Name` é opcional. Use **Preparar modelo…** e, opcionalmente, importe `Node/X/Y/Z`. Configure os eixos e confira as ligações; depois escolha o piso/pilar, complete a laje e prima **F5** para calcular as suas combinações. **Orientar ligação…** roda esforços e geometria em conjunto. **Relatório do conjunto…** exporta PDF/TXT/JSON por piso, grupo ou seleção, com filtro de resultados atualizados ativo por predefinição. Inclui um [conjunto fictício preparado](examples/importacao/Modelo_Ligacoes.json), [pilares](examples/importacao/Modelo_Pilares.csv) e [nós](examples/importacao/Modelo_Nos.csv). A consulta e preparação de uma ligação individual continuam em **Barras e nós…**; ver [MODELO_IMPORTACAO.md](MODELO_IMPORTACAO.md).

## Editor gráfico de aberturas

Em **Método β**, use **Definir aberturas na planta…**, ou prima **Aberturas…** no separador **Planta**. Adicione retângulos ou círculos, desenhe um retângulo com o rato, arraste para mover e use o quadrado azul para redimensionar. Pode introduzir coordenadas/dimensões exatas ou uma distância livre à face escolhida do pilar. **Aplicar ao caso** guarda as alterações e exige novo cálculo; **Cancelar** conserva o caso anterior.

O motor recalcula a distância mínima, o limite 6d e os setores a partir das aberturas físicas. Os setores manuais anteriores são adicionais. O ajuste de aberturas alongadas e a envolvente radial conservadora para posições oblíquas são identificados na memória. Aberturas além de 6d ficam registadas sem dedução por 6.4.2(3). Interseções, sobreposições, aberturas que toquem o bordo e geometrias fora do âmbito são rejeitadas.

A folha **Aberturas** do XLSX e os esquemas da GUI/PDF conservam a definição geométrica. O recobrimento dos ramos às aberturas é verificado por coordenadas. Com setores ativos, mantém-se a fundamentação específica de beta. Consulte [ABERTURAS_GUI.md](ABERTURAS_GUI.md) para instruções e limites.

## Instalação

A distribuição contém código Python, não um executável autónomo. Requer **Python 3.10 ou superior**, Tkinter e as dependências indicadas em `requirements.txt`. Extraia todo o ZIP, incluindo a pasta `examples`, antes de iniciar.

Instalação com o lançador `py`, num terminal da pasta extraída:

```bat
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

Nas utilizações seguintes pode abrir `iniciar.bat`. Tkinter deve estar incluído na instalação de Python utilizada.

Instalação com `python3`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Em Linux pode ser necessário instalar o pacote Tkinter correspondente ao Python utilizado.

## Dados e convenções

1. Identifique projeto, apoio e combinação ELU. O campo Combinação é texto: não seleciona intervalos nem calcula envolventes. Introduza VEd, MEdx e MEdy concomitantes.
2. Introduza d médio. Com dx e dy preenchidos, a interface calcula d = (dx + dy)/2. Na API, esses valores têm de ser coerentes.
3. As,x e As,y são áreas de armadura aderente de tração, médias nas faixas de 6.4.4(1), com largura do apoio acrescida de 3d para cada lado e limitadas pelos bordos livres. Confirmar a extensão e amarração dessas áreas no projeto.
4. Escolha a posição, forma e dimensões do pilar. Para um bordo livre, g é a distância da face do pilar ao bordo da laje: g = 0 significa encostado.
5. Escolha um método de beta aplicável, calcule e confira as verificações. A alteração de entradas invalida o resultado anterior para exportação.
6. Quando existir proposta de armadura, consulte Fiadas, Planta e Memória. Confirme a amarração apenas após conferir o pormenor construtivo correspondente.

| Grandeza | Interface | API / JSON |
|---|---|---|
| VEd | kN | N |
| MEdx, MEdy | kN.m | N.m |
| Dimensões, alturas úteis, g e espaçamentos | m | m |
| Resistências e compressão no plano | MPa | MPa |
| Armaduras longitudinais | cm²/m | cm²/m |
| Diâmetros, recobrimento e agregado | mm | mm |
| Pressão líquida da sapata | kPa | kPa |
| Setores ineficazes | graus | graus |

A interface aceita ponto ou vírgula decimal, sem separadores de milhares. O JSON usa ponto decimal. Um momento nulo deve ser introduzido como zero; um campo vazio não equivale a zero. Por compatibilidade, a API mantém momentos omitidos iguais a zero.

X é paralelo a c1 e Y a c2. As excentricidades referidas ao centro do pilar são ex = MEdy/VEd e ey = MEdx/VEd. No bordo, c1 é paralelo e c2 perpendicular ao bordo livre, localizado em Y = -c2/2 - g. O lado interior da laje é +Y; o seletor de excentricidade normal define o seu sentido. No canto encostado, os bordos são X = -c1/2 e Y = -c2/2. As convenções devem ser conciliadas com os eixos e sinais do modelo estrutural.

## Escolha do coeficiente beta

| Modo | Tratamento |
|---|---|
| `ec2`, pilar interior sem aberturas | Circular: (6.42). Retangular: (6.43) por predefinição, incluindo os limites uniaxiais e concêntrico; pode selecionar (6.39) para cálculo uniaxial. |
| `ec2`, bordo encostado, sem aberturas e excentricidade normal interior | (6.44), incluindo o limite de momento perpendicular nulo. |
| `ec2`, canto encostado, sem aberturas e excentricidades interiores | (6.46), incluindo os limites de momentos nulos. |
| `ec2`, bordo exterior encostado e sem aberturas | (6.39) com os esforços referidos ao centro do perímetro e W integrado segundo (6.40). Se a resultante for biaxial, exige selecionar a combinação conservadora. |
| `ec2`, canto exterior encostado e sem aberturas | Cálculo por direção de (6.39), mediante seleção da combinação biaxial conservadora. Sem essa seleção, BETA_PENDING. |
| `ec2`, g > 0 ou setores de aberturas ativos | BETA_PENDING: geometria disponível, mas beta exige fundamentação específica. |
| `simplificado` | Valores 1,15 / 1,40 / 1,50 para interior / bordo / canto, segundo 6.4.3(6), mediante declaração das condições de aplicabilidade. Não disponível com setores ineficazes. |
| `manual` | Fator finito beta ≥ 1 e referência obrigatória da análise que o fundamenta. O valor é aplicado na face, nos contornos de controlo e nos contornos exteriores. |
| Sapata concêntrica | Apenas modo `ec2`, beta = 1. |

Em **Método β**, o método simplificado exige confirmar que a estabilidade lateral é independente dos pórticos laje-pilar e que a diferença entre vãos adjacentes não excede 25%. O programa não verifica estas condições a partir dos dados locais da ligação. Este método substitui o cálculo explícito da transferência de momentos; os momentos ficam registados, sem serem novamente adicionados ao fator simplificado.

Selecione **Manual · valor e referência**. Preencha **Coeficiente β ≥ 1** e **Referência da análise de β**. Estes campos só ficam ativos nesse método. A análise deve abranger geometria, esforços concomitantes, aberturas e aplicação do fator aos contornos relevantes. O programa verifica o valor numérico e a existência da referência, não o conteúdo técnico dessa análise. Rever a fundamentação sempre que as entradas mudarem.

Nos casos exteriores de bordo/canto sem afastamento ou aberturas, os momentos introduzidos no centro do pilar são transportados uma única vez para o centro do perímetro de controlo. As majorações de (6.39) utilizam k do Quadro 6.1, não k = 1. A memória mostra os momentos de entrada, os sentidos declarados, os momentos transportados, W e k. Não introduza momentos já transportados para o centro do perímetro.

Com duas componentes, a opção **Combinação biaxial conservadora de (6.39)** soma os módulos das majorações calculadas por direção. Esta combinação é uma hipótese adicional do programa, não uma equação biaxial literal do EC2 para bordo/canto. Está desativada por predefinição; o canto exterior exige essa seleção também para evitar mudanças de âmbito durante a pesquisa do contorno exterior. Para o interior retangular, (6.43) está disponível diretamente.

O seletor `interior_beta_method` admite `ec2_643` (predefinido) ou `ec2_639`. (6.43) mantém-se nos limites de momentos nulos; não existe mudança automática de expressão por um momento passar de zero a um valor pequeno. Se selecionar (6.39) e a resultante for biaxial, escolha a combinação conservadora ou mude para (6.43).

A expressão (6.43) segue a correspondência literal de eixos da NP: y,z da norma correspondem a X,Y da interface. Assim, beta = 1 + 1,8 sqrt[(ex/by)^2 + (ey/bx)^2], com ex = MEdy/VEd, ey = MEdx/VEd, bx = c1 + 4d e by = c2 + 4d. A correspondência está registada em cada memória; não se trocam denominadores silenciosamente.

Para g > 0 e para aberturas mantém-se a exigência de fundamentação específica. Selecionar a combinação biaxial não elimina esse limite. Consulte [METODOS_BETA.md](METODOS_BETA.md) para as expressões e o âmbito.

## Geometria junto a um bordo livre

Com g > 0, o motor compara o contorno fechado e o contorno aberto que termina no bordo, sem contar o bordo livre no comprimento resistente. Um contorno fechado que toca ou ultrapassa o bordo não é admissível. O menor comprimento efetivo é adotado como referência. A classificação não resulta apenas da comparação entre g e 2d: mesmo cabendo na laje, o contorno fechado pode ser mais longo do que o aberto.

Com beta manual ou simplificado, aplica-se o mesmo fator às alternativas admissíveis; o contorno mínimo condiciona a tensão. O centro geométrico e W são registados apenas como características geométricas. A comparação repete-se para os contornos exteriores.

**u0 com afastamento:** conserva-se a capacidade de referência do bordo encostado, usando c1 + 2 min(c2; 1,5d), antes de aplicar setores ineficazes. A quarta face do pilar não recebe crédito automático apenas porque g é positivo. Trata-se de uma hipótese conservadora do programa, não de uma interpolação normativa para o afastamento. Pode ser restritiva mesmo quando u1 é fechado; a hipótese consta do relatório e do JSON `u0_terms`. Não se calcula u1* para g > 0.

Para 0 < g < d, a armadura especial de bordo de 6.4.2(5)/9.3.1.4 continua a exigir dimensionamento separado.

## Armadura de punçoamento

A proposta usa ramos verticais de estribos Ø10, Ø12 ou Ø16. s0 automático = 0,5d; sr automático ≤ 0,75d, arredondado por defeito a 5 mm. São verificadas pelo menos duas fiadas, extensão até 1,5d do contorno exterior, st ≤ 1,5d até 2d e st ≤ 2d mais além. A distância livre mínima segue max(phi; 20 mm; dg + 5 mm).

**A armadura de resistência e o mínimo local são grandezas distintas.** (6.52) fornece Asw/sr necessário por resistência. O mínimo de (9.11) é verificado com sr e st efetivos de cada fiada, por ramo. O valor calculado com u1 é apresentado como referência, não como mínimo universal a impor a todas as fiadas. Uma fiada mais curta pode cumprir (9.11) com Asw/sr inferior à referência calculada em u1.

Em ligações afastadas do bordo com beta definido, a proposta pode incluir fiadas abertas em U e fechos adicionais. Os ramos comuns contam uma vez no inventário físico e na verificação de cada contorno alternativo que atravessam. A conferência parte das coordenadas XY e verifica pertença aos contornos, áreas, mínimo local, espaçamentos, recobrimento, distâncias livres e extensão. O cálculo procura uma distribuição admissível; não garante o número mínimo de ramos.

Os pontos do desenho representam ramos verticais. Dobras, ganchos, forma completa dos estribos, amarração e compatibilidade em altura são definidos no pormenor construtivo. A confirmação de amarração não altera verificações resistentes nem elimina uma pendência de beta.

## Aberturas e sapatas

Os setores ineficazes das aberturas são definidos pelo projetista a partir das tangentes da Figura 6.14. Exemplo de entrada: `-20;20 | 100;125`; JSON: `"opening_sectors": [[-20, 20], [100, 125]]`. São unidos e aplicados a u0, u1, contornos exteriores e distribuição de ramos. A versão 1.8.0 acrescenta o editor de posição e dimensões descrito abaixo. A dedução isolada antiga `u1_ineffective > 0` é rejeitada. Com setores, beta necessita de fundamentação específica.

As sapatas admitidas são retangulares ou circulares, de altura útil constante, apoio interior centrado e carga concêntrica. A pressão líquida uniforme deve equilibrar VEd; zero determina-a por VEd/área. Um valor indicado tem de concordar dentro de 1%, sendo adotado o valor exato de equilíbrio. São pesquisados perímetros entre a face e 2d, com reação integrada na área real e contornos recortados pela sapata. Não são calculadas a capacidade geotécnica nem a armadura de punçoamento de sapatas.

## Âmbito

Não são modelados capitéis, espessura variável, apoios de parede, pilares afastados de dois bordos, pilares circulares de bordo/canto, sistemas comerciais de punçoamento, sapatas excêntricas ou com pressão não uniforme. Apoios retangulares com razão entre dimensões ≥ 4 estão fora do âmbito validado. O método fib anterior mantém-se desativado. Flexão, esforço transverso unidirecional, ELS e integridade global exigem verificações próprias.

## Estados e exportações

| Estado | Significado |
|---|---|
| `BETA_PENDING` | Geometria disponível; beta por fundamentar; sem conclusão resistente. |
| `PASS_WITHOUT` | Verifica sem armadura específica nos mecanismos avaliados. |
| `DETAIL_PENDING` | Proposta cumpre as verificações implementadas; falta declarar a amarração. |
| `PASS_WITH` | Proposta cumpre as verificações implementadas, com amarração declarada. |
| `FAIL_U0` | Não verifica na face; cálculos posteriores indisponíveis. |
| `FAIL_MAX` | Ultrapassa o limite resistente com armadura. |
| `FAIL_DETAIL` | Distribuição incompleta ou não conforme. |
| `REQUIRES_REINFORCEMENT` | Sapata requer intervenção ou dimensionamento específico. |
| `INVALID` / `ERROR` | Cálculo interrompido; sem conclusão favorável. |

Guardar caso grava as entradas JSON. Abrir caso aceita esse JSON ou o resultado de uma execução anterior, recalculando as entradas. Os ficheiros anteriores continuam a abrir, mas são recalculados segundo os métodos atuais. Em interiores retangulares, casos sem indicação de método passam a usar (6.43), o que pode alterar beta em relação à soma de majorações usada até 1.6.0. A revisão não convalida resultados antigos.

PDF, TXT, XLSX e JSON são gerados a partir do mesmo resultado. Incluem norma, versão, identificação, data UTC e identificador SHA-256 das entradas e versão. Este identificador distingue execuções; não certifica o cálculo. Valores indisponíveis são `None`/`null`, células vazias ou «Não calculado», nunca armadura nula por omissão.

O PDF usa Courier New, com alternativa monoespaçada incorporada; o XLSX usa Courier New. A folha Beta contém a expressão, substituição numérica, valor, unidade e referência de cada etapa. As folhas Fiadas, FiadasContornos e Ramos registam quantidades e pertença aos contornos. Fiadas inclui a área de um ramo, mínimo local, utilização de (9.11) e armadura requerida por resistência. Editar as entradas no XLSX não recalcula o motor; as fórmulas de utilização servem apenas para conferência.

## Linha de comandos e testes

```sh
python -m punching.cli examples/14_bordo_000mm_594kN.json --out resultados/caso14 --pdf --xlsx
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Códigos de saída: 0 = verifica; 1 = falha ou pendência, incluindo `BETA_PENDING`; 2 = dados inválidos; 3 = erro de cálculo ou ficheiro. Os relatórios registam também as pendências.

Mantém-se `from Punching_EC2 import PuncoamentoEC2`. Os argumentos `interior_beta_method` e `allow_biaxial_envelope` controlam os métodos acima. No modo manual, os argumentos são `beta_mode='manual'`, `beta_manual=<valor fundamentado>` e `beta_reference=<referência da análise>`.

Nos resultados JSON, `Asw_sr_req` passa a representar a necessidade por resistência; o mínimo local consta de cada fiada. `Asw_sr_min_u1_reference` é a referência mínima em u1. O campo antigo `Asw_sr_min` é mantido para leitura por integrações anteriores, como máximo dos mínimos de referência dos contornos avaliados; não deve ser interpretado como mínimo universal. As unidades desses campos são m²/m.

O catálogo contém 29 exemplos com descrições técnicas, incluindo a ligação de 594 kN com g = 0, 1 e 343 mm e dois exemplos condicionais do método simplificado. Os ensaios e respetivos limites estão descritos em VALIDACAO.md. A distribuição não equivale a uma certificação geral para todos os casos aceites na interface.
