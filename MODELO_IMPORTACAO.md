# Importação Modelo — barras e ligações laje–pilar

A importação reconhece a tabela com `Member/Node/Case`, `FX`, `MY`, `MZ` e `Story`; a coluna `Name` é opcional. Não é necessário associar a mesma coluna separadamente à barra, ao nó e à combinação. O programa conserva os esforços originais e prepara a ligação apenas depois de o nó e os tramos serem conferidos.

## Preparação por piso e pilar

Após importar a tabela, use **Preparar modelo…**: perfil comum de eixos, exceções por barra e conferência das ligações. Os esforços disponíveis são adotados por combinação; a laje é preenchida uma vez por ligação. F5 calcula as combinações e **Relatório do conjunto…** organiza os resultados por piso. O procedimento completo e o exemplo incluído estão em [MODELO_POR_PISO.md](MODELO_POR_PISO.md).

## Preparação individual de uma ligação

A consulta detalhada continua disponível em **Pilares… → Barras e nós…**. Pode fechar a janela de preparação do modelo para seguir o procedimento individual:


1. Abra **Pilares… → Importar tabela… → Escolher…** e selecione o CSV, TSV ou XLSX. No XLSX, confirme a folha. O cabeçalho Modelo é procurado nas primeiras 50 linhas. Use **Ler tabela** após mudar de folha.
2. Confira a interpretação apresentada em **Associar colunas** e prima **Conferir → Importar**. As unidades vêm dos cabeçalhos de cada coluna. Os controlos de unidades do importador genérico não são aplicados a este perfil.
3. Na janela **Barras e nós…**, consulte os resultados e filtre por piso da barra, pilar, barra, nó ou combinação. A consulta apresenta até 250 linhas por página e conserva a origem de cada registo.
4. Opcionalmente, use **Adicionar tabela…** para importar as coordenadas `Node`, `X`, `Y` e `Z`. As unidades devem constar dos cabeçalhos das coordenadas. O programa passa a identificar topo/base pela cota dos dois nós da barra.
5. Selecione uma linha correspondente ao **nó da ligação** e prima **Preparar ligação neste nó…**. Confira o piso da ligação e a sua identificação. Associe o tramo inferior, com o nó no topo, e o superior, com o nó na base. Havendo coordenadas completas e associação inequívoca, estes campos são sugeridos automaticamente.
6. Indique a orientação observada no modelo para **x local** e **y local** de cada barra, relativamente aos eixos da planta do caso. Selecione a combinação ou todas as combinações do par. Confira as condições apresentadas e registe a referência do modelo/conferência.
7. Prima **Conferir equilíbrio**. A memória apresenta as linhas usadas, a transformação dos momentos e os esforços obtidos. **Adicionar ligação** cria os casos; resultados incompletos permanecem identificados como pendentes.
8. Regresse a **Pilares…**, selecione a ligação e use **Analisar ligação**. Em **Origem dos esforços…**, adote a fonte. Complete a laje, armaduras, materiais, bordos, aberturas e método β antes de calcular.

**Guardar conjunto…** conserva tabelas, coordenadas, associações e dados dos casos, mesmo que ainda não tenha sido preparada uma ligação. O caso individual e os restantes perfis de importação continuam disponíveis. Uma nova revisão dos ficheiros deve entrar num novo conjunto; fontes repetidas não substituem silenciosamente os dados existentes.

## Interpretação das colunas

| Coluna de origem | Interpretação |
|---|---|
| `Member/Node/Case`, por exemplo `2/7460/101 (C)` | Barra `2`, nó `7460`, caso `101 (C)`. O sufixo do caso é conservado. |
| `Name` (opcional) | Nome de consulta. Se faltar, usa o nome preenchido noutra linha da mesma barra, com referência à origem; na ausência deste, usa «Barra N». |
| `Story` | Piso associado à barra no modelo. Deve ser distinguido da cota do nó da ligação. |
| `FX (kN)` | Axial local da barra, positivo em compressão. Não é adotado diretamente como carga da laje. |
| `MY (kNm)` / `MZ (kNm)` | Momentos locais de análise da barra, antes de serem convertidos em ações sobre o nó. |
| `HY`, `HZ` | Dimensões segundo y/z locais. Requerem unidades nos cabeçalhos. |
| `AX`, `IY`, `IZ` | Área e inércias usadas para conferir a compatibilidade da secção. |
| `Node`, `X`, `Y`, `Z`, numa tabela de nós | Identificação e coordenadas globais; associação pelo número exato do nó. |

São reconhecidos cabeçalhos em inglês e os equivalentes implementados `Barra/Nó/Caso`, `Nome`, `Piso` e `Nó`. Os identificadores não são associados por semelhança. Resultados no mesmo nó mas em combinações diferentes permanecem separados.

As forças aceitam N/kN; os momentos N.m, N.mm, kN.m e kN.cm; dimensões m/cm/mm; áreas m²/cm²/mm² e inércias m⁴/cm⁴/mm⁴. A apresentação normalizada usa m, kN e kN.m. O adaptador reconhece ponto ou vírgula decimal e aceita milhares agrupados por espaços de três algarismos. Não aceita misturas de ponto/vírgula nem inventa unidades ausentes. Fórmulas/erros XLSX, esforços em falta, duplicados e identificações estruturais inconsistentes impedem a importação do ficheiro. Um Name vazio não equivale a um número de barra em falta. Os nomes originais ficam preservados; não há preenchimento com o nome da linha anterior de outra barra. Pode atribuir uma designação profissional ao campo «Identificação do pilar / ligação» ao preparar o nó.

O resumo indica todos os pisos presentes em `Story`. O nome do ficheiro não limita a importação a um piso: escolha o piso no filtro de consulta e confirme a cota da ligação.

## Secção e eixos

O programa compara AX e IY/IZ com as propriedades de um retângulo maciço HY × HZ ou de um círculo maciço. A tolerância relativa de 0,5% admite o arredondamento da exportação; a forma deve ser conferida no modelo. A falta ou incompatibilidade das propriedades não impede consultar os esforços, mas deixa a geometria do cálculo por definir.

Por exemplo, HY = 25 cm, HZ = 70 cm, AX = 1750 cm², IY ≈ 714583,33 cm⁴ e IZ ≈ 91145,83 cm⁴ são compatíveis com um retângulo de 25 × 70 cm. Se y local for paralelo a X do caso, c1 = 0,25 m e c2 = 0,70 m; se for paralelo a Y, as dimensões trocam de direção. A secção de contacto adotada corresponde ao tramo inferior e deve ser conferida quando existem alterações de secção, capitéis ou outros pormenores.

O adaptador admite x local = +Z ou −Z e y local = +X, −X, +Y ou −Y. z local resulta de x × y. Na preparação individual, os eixos X/Y são os da planta do **caso de cálculo**, não necessariamente os eixos globais do modelo. No assistente por piso, o perfil comum refere-se ao modelo e a operação «Orientar ligação…» define depois o referencial de cada caso. No bordo, Y aponta para o interior e c1 é paralelo ao bordo; no canto, X/Y apontam para o interior. Para orientações oblíquas, utilize esforços já convertidos no perfil genérico ou resultantes integrais da ligação.

## Equilíbrio e âmbito

A carga transferida é obtida no **mesmo nó**, com o topo do tramo inferior e a base do superior, para a **mesma combinação**:

```text
VEd = FXinf − FXsup
```

O resultado de uma barra no seu outro extremo não representa o pilar acima da laje. Por exemplo, duas linhas `2/7460/...` e `2/51520/...` pertencem à mesma barra 2; a sua diferença não é a transferência da laje.


O equilíbrio está limitado a barras 3D verticais e alinhadas, esforços nos extremos reais no centro do pilar à cota da laje, sem outras transferências nodais. Coordenadas que mostrem uma barra inclinada ou uma posição incompatível bloqueiam a associação. Outras barras conhecidas no mesmo nó também impedem omitir essas contribuições. O utilizador deve conferir no modelo os elementos/cargas que não constam da tabela exportada.

Não são calculados o transporte de esforços por offsets ou braços rígidos, a integração de esforços de cascas por metro, nem a composição de envolventes. Um superior sem resultados não é considerado fisicamente ausente; na cobertura, a inexistência deve ser declarada. Uma combinação sem par fica pendente. VEd não positivo não é substituído pelo valor absoluto. O âmbito normativo de β e das resistências EC2 permanece o documentado nas versões anteriores.

## Combinações modais CQC/SRSS

Os sufixos CQC/SRSS são conservados na identificação do caso. As respostas modais já combinadas não estabelecem esforços concomitantes nos dois tramos. Como a combinação quadrática é uma operação não linear, subtrair resultados combinados não equivale, em geral, a combinar a diferença dos resultados de cada modo. Um sinal atribuído à resposta combinada não resolve essa distinção.

Por esse motivo, **este adaptador deixa CQC/SRSS pendentes**: conserva FX/MY/MZ e a geometria, mas não apresenta VEd/MEd obtidos por subtração/soma direta. Deve obter no modelo de análise a resultante da ligação com tratamento modal e combinação de ações adequados; depois pode importá-la no perfil de resultantes integrais com referência à metodologia. Trata-se de um limite explícito do adaptador, não de uma nova regra de resistência do EC2. A ausência de um sufixo CQC/SRSS não dispensa conferir a natureza e a concomitância dos esforços.


Um conjunto antigo que contenha resultantes Modelo CQC/SRSS adotadas por equilíbrio direto é rejeitado. Reimporte as tabelas para conservar os dados de origem como pendentes e substitua a fonte por resultantes fundamentadas.

## Exemplo fornecido

Os ficheiros `examples/importacao/Modelo_Pilares_Exemplo.csv` e `Modelo_Nos_Exemplo.csv` contêm **dados fictícios de demonstração**, com cabeçalhos do formato reconhecido. O conjunto `Modelo_Ligacoes_Exemplo.json` já contém as duas tabelas e as duas combinações preparadas, com a origem por adotar e os dados da laje por preencher.

Para preparar a ligação a partir dos CSV:

- Selecione o nó **7460**, com cota Z = 3,00 m; inferior **barra 2**, superior **barra 3**.
- Piso da ligação **PISO 2**, pilar **P103**. Em ambas as barras, x local = **+Z** e y local = **+X**.
- Escolha todas as combinações do par. As condições e a referência são confirmadas apenas para este exemplo fictício.
- Caso **101 (C)**: VEd = **450 kN**, MEdx = **12 kN.m**, MEdy = **16 kN.m**.
- Caso **102 (C)**: VEd = **400 kN**, MEdx = **18 kN.m**, MEdy = **26 kN.m**.

Os testes reproduzem o esquema das imagens fornecidas e referências sintéticas de equilíbrio. A exportação CSV/XLSX integral do projeto e a utilização da interface nativa Ambiente de trabalho devem ser conferidas antes da atualização do repositório. A proveniência identifica os dados e as decisões de importação; não certifica o modelo estrutural.

## Exemplo com nomes em falta

`examples/importacao/Modelo_Pilares_SemNome.csv` contém dados fictícios de uma ligação entre duas barras verticais, com Name vazio. A consulta deve mostrar «Barra 2» e «Barra 3». A tabela de nós é a mesma do exemplo anterior. Pode definir «Pilar P02» como identificação da ligação, sem mudar os números de barra.

A combinação estática 101 (C), com as orientações do exemplo, resulta em 450/12/16 kN/kN.m. A combinação 118 (C) (CQC) serve para demonstrar a pendência: os valores são fictícios e não representam um resultado de análise modal para dimensionamento. Todos os oito registos devem ficar disponíveis.
