# Importação de pilares e ligações laje–pilar

A versão 1.11.0 permite importar tabelas opcionais e analisar uma ligação/combinação de cada vez. A utilização individual continua disponível. O motor EC2 recebe os mesmos dados e utiliza os mesmos métodos da versão 1.10.0.

**Tabelas Modelo com `Member/Node/Case`:** utilize o reconhecimento automático descrito em [MODELO_IMPORTACAO.md](MODELO_IMPORTACAO.md). Esse perfil separa barra, nó e caso, lê as unidades dos cabeçalhos e mantém os esforços locais para a preparação da ligação. As instruções seguintes referem-se aos três perfis de tabelas genéricas.

## Começar

1. Abra **Pilares… → Importar tabela…**. Escolha XLSX, CSV ou TSV.
2. Selecione o conteúdo: **Geometria dos pilares**, **Esforços nos extremos dos pilares** ou **Resultantes integrais da ligação**. No XLSX, escolha a folha. Confirme linha dos cabeçalhos, unidades e convenções.
3. Prima **Ler tabela**, associe os cabeçalhos aos campos do programa e use **Conferir**. As associações sugeridas têm de ser revistas. **Importar** acrescenta os registos ao conjunto.
4. Pode importar as outras tabelas para o mesmo conjunto. A associação usa exatamente **piso + pilar + combinação**; a geometria usa **piso + pilar**. Os identificadores devem coincidir, incluindo zeros iniciais. Não se aproxima por coordenadas nem pelo nome mais semelhante.
5. Selecione uma linha e prima **Analisar ligação**. Em **Dados → Esforços ELU → Origem dos esforços…**, escolha a fonte a adotar. As fontes e diferenças ficam visíveis. Não existe adoção automática da fonte de maior ou menor valor.
6. Complete a posição do pilar, altura útil, armadura longitudinal, betão, bordos e aberturas. Estes dados não são deduzidos da tabela de pilares. Execute o cálculo e confira o método β e os sentidos das excentricidades.
7. Regresse a **Pilares…** para analisar outra ligação. Os dados de cada caso permanecem na sessão, incluindo campos ainda incompletos. Use **Guardar conjunto…** para os conservar num ficheiro JSON. Ao reabrir ou voltar a ativar uma ligação, recalcule para obter relatórios atuais.

**Guardar**, na janela principal, guarda apenas o caso ativo. **Guardar conjunto…**, no gestor de pilares, guarda todas as ligações, fontes e dados introduzidos. **Novo**, nesse gestor, inicia um conjunto vazio. O programa propõe guardar alterações ao conjunto antes de fechar a aplicação ou substituir o conjunto. **Caso individual** permite regressar ao caso que estava aberto antes de entrar nas ligações importadas.

## Formatos e campos

| Tabela | Campos obrigatórios | Campos adicionais |
|---|---|---|
| Geometria | Piso, pilar, forma, c1/D; c2 para retângulos | Nenhum esforço é necessário. |
| Extremos dos pilares | Piso, pilar, combinação, barra, tramo, extremo, N, Mx nó, My nó | Declaração de superior ausente; forma/c1/c2. |
| Resultante da ligação | Piso, pilar, combinação, V, Mx, My | Forma/c1/c2. |

Formas: `retangular` ou `circular`. Tramos: `inferior` / `superior`. Extremos: `topo` / `base`. Ausência de superior: `sim` / `nao`; vazio significa ausência **não confirmada**. Na tabela de extremos, a geometria importada corresponde à secção do tramo inferior. A superfície efetiva de contacto deve ser conferida no caso, sobretudo se as secções diferirem ou existir capitel.

As dimensões aceitam m, cm ou mm; as forças N ou kN; os momentos N.m, N.mm, kN.m ou kN.cm. A interface e a proveniência normalizada usam m, kN e kN.m; as entradas do motor e `inputs` no JSON continuam em N e N.m. As unidades são escolhidas por tabela, sem mistura de unidades na mesma grandeza.

O CSV aceita ponto e vírgula, vírgula ou tabulação. A deteção de codificação cobre UTF-8 e UTF-16 com BOM; também pode escolher a codificação explicitamente, incluindo Ambiente de trabalho-1252. Escolha o separador decimal e **não use separadores de milhares**. Guarde identificadores como texto no XLSX. Formatos numéricos simples como `0000` preservam os zeros iniciais.

Os cabeçalhos têm de estar preenchidos e ser distintos. Uma coluna não pode ser usada para duas grandezas. Fórmulas ou erros XLSX nas células associadas são rejeitados: exporte os **valores calculados**. Não há substituição de células vazias por zero. São admitidas até 50 000 linhas, 256 colunas e 32 MB por tabela. A primeira versão não importa XLS binário.

Nos perfis genéricos, a tabela deve disponibilizar as grandezas e os identificadores acima. Os esforços já devem estar nos eixos e na convenção indicada. O adaptador Modelo é descrito em MODELO_IMPORTACAO.md e MODELO_POR_PISO.md. As tabelas de demonstração usam dados didáticos; cada exportação de projeto deve ser conferida quanto a unidades, eixos, sinais e conservação dos valores.

## Equilíbrio dos tramos

O programa utiliza o **topo do tramo inferior** e a **base do tramo superior**, junto à mesma laje e na **mesma combinação ELU**. Só é admitido automaticamente o modelo declarado de tramos verticais alinhados, no qual a laje é a única origem da transferência no nó. Vigas, pilares adicionais, cargas nodais, eixos descentrados ou pilares inclinados exigem outro tratamento dos esforços.

Após normalizar N para positivo em compressão:

```text
VEd = Ninf - Nsup
```

Para os momentos da tabela de tramos, Mx e My têm de ser **ações vetoriais dos pilares sobre o nó**, já reduzidas ao centro do pilar, na cota da laje. O referencial é dextrógiro, com Z para cima; X paralelo a c1 e Y paralelo a c2 da planta. No bordo, +Y aponta para o interior da laje. No canto, +X e +Y apontam para o interior.

Como o programa adota `ex = MEdy/VEd` e `ey = MEdx/VEd`:

```text
MEdx = Mx,nó,inf + Mx,nó,sup
MEdy = -(My,nó,inf + My,nó,sup)
```

O sinal de menos em MEdy converte a convenção vetorial para a convenção de excentricidade do programa. Não corresponde a inverter indiscriminadamente um momento local do software de origem. Por exemplo, uma reação vertical ascendente V aplicada em (x,y) tem momento vetorial `(V*y, -V*x, 0)`.

**Não associe diretamente My/Mz locais dos pilares aos campos Mx/My do perfil genérico sem a transformação necessária.** As ações do nó sobre a barra têm sinais opostos às ações da barra sobre o nó. Os sentidos dos eixos locais e o extremo de leitura importam. O adaptador Modelo tem uma transformação própria, limitada a barras 3D verticais e eixos transversais paralelos aos eixos X/Y do caso, com orientação conferida. Se o ponto de referência não coincidir com o centro do pilar, o transporte vetorial `r × F` deve ser feito previamente; não está incluído neste importador.

Exemplo fictício, Piso 1 / P01 / ELU 01:

| Origem | N (kN, compressão +) | Mx no nó (kN.m) | My no nó (kN.m) |
|---|---:|---:|---:|
| Topo do inferior | 1800 | 18 | -24 |
| Base do superior | 1350 | -6 | 8 |
| Grandezas adotadas pelo programa | **VEd = 450** | **MEdx = 12** | **MEdy = 16** |

Um registo superior em falta não equivale a um pilar inexistente. Na cobertura, a ausência deve ser indicada na linha do inferior. Duplicados, ausência contraditória, tramos com a mesma identificação, combinações sem par e VEd não positivo ficam pendentes. Não se aplica valor absoluto a VEd, não se somam linhas duplicadas e não se combinam máximos independentes. A transferência com sentido inverso requer revisão da face tracionada e do caso estrutural.

## Tabela da laje

O perfil **Resultantes integrais da ligação** recebe esforços reduzidos da ligação completa em kN/kN.m. Pode usar a convenção do programa ou a convenção vetorial da reação do apoio sobre a laje, com +Z para cima. No segundo caso, o programa converte `MEdx=Mx` e `MEdy=-My`.

O ponto de redução tem de ser o centro do pilar. O esforço não pode estar previamente majorado por β, nem reduzido por dedução de cargas interiores a um contorno afastado. Uma resultante num corte arbitrário não equivale necessariamente à transferência completa. Usar diretamente uma força reduzida de u1 também na face u0 pode ser incorreto.

Valores locais `Mxx`, `Myy`, `Mxy` em kN.m/m e `Qx`, `Qy` em kN/m não são as resultantes pedidas. Exigem integração e informação da malha, dos contornos e dos eixos. Esse processamento não está incluído. Exporte resultantes adequadas do software de análise ou obtenha e fundamente os esforços fora deste importador.

Se existirem ambas as fontes, a GUI e os relatórios apresentam as diferenças com sinal, em unidades físicas. Essas diferenças **não são um critério automático de aceitação**. O utilizador escolhe a fonte que corresponde ao modelo da ligação e pode registar a referência da decisão.

## Alterações, registos e relatórios

- A origem conserva nome e SHA-256 do ficheiro, folha, linha, valores originais, mapeamento, unidades, declarações e método. O hash identifica o ficheiro; não certifica a sua origem nem o cálculo.
- A escolha de uma fonte importada atualiza os três esforços em conjunto e os sentidos das excentricidades. Os restantes dados do caso são conservados. Os sentidos continuam sujeitos à conferência do projetista; no modo manual mantêm-se os sentidos definidos no caso.
- Se editar diretamente um esforço importado, o cálculo pede que reponha a fonte ou escolha **Introdução manual** com uma referência. Os valores originais são conservados para comparação.
- Não é permitida a mudança silenciosa do nome da combinação com esforços importados. Uma combinação diferente exige a seleção do respetivo registo ou esforços manuais fundamentados.
- A memória, TXT, PDF, XLSX (folha **OrigemEsforcos**) e JSON usam uma cópia da proveniência da execução. Alterar dados desativa as exportações até ao novo cálculo.
- Uma nova fonte pode ser acrescentada ao conjunto. Uma fonte repetida ou uma geometria incompatível não substitui os dados existentes; use um novo conjunto para uma revisão das exportações. A importação é atómica: erros de leitura/mapeamento não descartam apenas as linhas problemáticas.
- Os conjuntos JSON conservam os dados de origem. As resultantes dos tramos são reconstruídas a partir desses registos na reabertura para conferir a consistência dos valores guardados. Os resultados resistentes devem ser recalculados.

## Ficheiros de exemplo

Na pasta `examples/importacao`, `Exemplo_importacao.xlsx` contém as folhas **Geometria**, **Tramos** e **Resultantes**. Os três CSV apresentam os mesmos dados. Cabeçalhos na linha 1; dimensões em m, forças em kN, momentos em kN.m; decimal ponto; N positivo em compressão. As resultantes usam a convenção do programa. São dados fictícios destinados a testar a importação.

Importe cada folha no perfil correspondente. P01 / Piso 1 / ELU 01 fornece VEd = 450 kN, MEdx = 12 kN.m e MEdy = 16 kN.m nas duas fontes. Em ELU 02 há uma diferença deliberada de 5 kN entre fontes. P02 tem o tramo superior em falta: o equilíbrio fica pendente, mas a tabela de resultantes oferece uma fonte alternativa. Na cobertura, a ausência de superior está declarada e VEd = 280 kN.

O ficheiro `Ligacoes_exemplo.json` já reúne as três fontes; abra-o em **Pilares… → Abrir conjunto…**. Os dados da laje ficam por preencher, para não confundir os valores de demonstração com dados de projeto.

## Fundamentação e âmbito

A obtenção dos esforços resulta do equilíbrio estático do modelo declarado. As verificações de punçoamento e de β continuam a seguir o referencial e o âmbito documentados em [METODOS_BETA.md](METODOS_BETA.md) e [VALIDACAO.md](VALIDACAO.md).

A documentação oficial da [SCIA sobre extração de esforços para punçoamento](https://help.scia.net/19.1/en/dlo/steelfibreconcrete/06b_punching/06b_punching_theory.htm) descreve a utilização dos esforços originais por combinação e a distinção entre tramos superiores/inferiores. A consulta é usada apenas para o princípio de extração; não são adotadas as regras resistentes desse módulo de betão com fibras.
