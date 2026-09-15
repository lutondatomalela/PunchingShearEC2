# Ligações por piso e pilar — versão 1.15.0

Este procedimento parte de esforços de barras de um modelo de análise. Prepara as resultantes de cada ligação laje–pilar, conserva as combinações e permite definir a laje uma vez por pilar/piso. A consulta e a introdução de casos individuais continuam disponíveis.

## 1. Importar e configurar o modelo

Em **Pilares… → Importar tabela…**, carregue a tabela de pilares. O assistente reconhece `Member/Node/Case`, esforços, unidades, nomes, pisos e propriedades da secção. Após a importação abre **Modelo — preparar ligações por piso**. Pode voltar a esta janela através de **Preparar modelo…**.

Use **Importar nós…** para acrescentar a tabela `Node/X/Y/Z`. É opcional: com coordenadas completas, o programa reconhece os tramos imediatamente acima e abaixo de cada nó; sem coordenadas, identifica os nós comuns e pede a associação dos tramos no separador **Ligações por piso**. Os números dos nós, a ordem das linhas e os nomes dos pisos não substituem as coordenadas.

Em **Modelo e eixos**, indique:

- **x local axial**: +Z ou −Z do modelo, segundo o sentido observado na barra.
- **y local transversal**: +X, −X, +Y ou −Y do modelo. z local resulta de x × y. As cores identificam os eixos locais, mas não determinam a sua orientação global.
- **Barras / intervalos**: introduza os números das barras com orientação diferente, selecione x/y e prima **Aplicar eixos às barras**; as restantes usam o perfil comum.
- **Combinações**: números ou intervalos, por exemplo `101-117 201`. Vazio inclui todas as combinações presentes; o rótulo completo é conservado.
- **Referência do modelo e dos eixos**: identifique a revisão do modelo e a conferência efetuada.

As declarações apresentadas aplicam-se às ligações selecionadas: modelo 3D com pilares verticais alinhados, esforços ELU concomitantes, extremos à cota da laje sem offsets, eixos conferidos e laje como única transferência entre os tramos. Se estas condições não se verificarem, use uma resultante integral da ligação obtida numa análise adequada. Uma viga, carga nodal ou outro elemento que participe no equilíbrio exige tratamento próprio.

### Selecionar várias barras

As três entradas seguintes selecionam as mesmas barras:

- `110para113 115 118para123`
- `110-113 115 118-123`
- `110 111 112 113 115 118 119 120 121 122 123`

Pode combinar números e intervalos. Aceitam-se espaços, vírgulas e ponto e vírgula entre grupos. Os extremos são incluídos e as repetições são eliminadas. Um número ausente ou intervalo inválido impede a operação completa; não são aplicadas exceções parcialmente. **Usar perfil comum** remove as exceções de todas as barras indicadas.

**Estender à prumada** substitui a seleção pela lista de barras verticais conectadas. Exige os dois extremos de cada barra e as coordenadas dos nós; usa os mesmos nós de ligação e uma tolerância de alinhamento X/Y de 0,01 mm. A expansão para em lacunas e desvios; ligações verticais sobrepostas ou ramificadas são consideradas ambíguas. Um nome de pilar repetido não estabelece continuidade. Confira a lista expandida e os eixos de todas as barras e prima **Aplicar eixos às barras**. A direção dos eixos locais continua a ser indicada pelo utilizador.

O resumo agrupa as exceções por perfil x/y. **Ver exceções…** apresenta a lista completa por número de barra.

### Guardar a configuração e continuar

**Guardar configuração e fechar** funciona mesmo sem novas ligações selecionadas. Confere a configuração, atualiza a origem dos esforços das ligações já preparadas, grava o conjunto e regressa à lista de pilares. Na primeira gravação escolha o ficheiro JSON; depois é usado o caminho do conjunto aberto ou guardado. Se cancelar a escolha do ficheiro ou a escrita falhar, os novos eixos não são aplicados ao conjunto.

Este comando não cria as novas ligações selecionadas no separador 2. Para as criar, use **Conferir ligações → Aplicar ligações conferidas** e depois **Guardar conjunto…**. Também pode guardar apenas a configuração dos eixos antes de preparar a primeira ligação; as declarações de âmbito e a referência devem estar completas.

Numa revisão dos eixos, os esforços de origem são novamente transformados para o referencial que cada ligação já utiliza. O programa conserva projeto, laje, materiais, armaduras, aberturas, grupos e orientação do caso. As dimensões que continuam a coincidir com a geometria importada acompanham a revisão; dimensões definidas pelo utilizador são conservadas e identificadas na conferência. Fontes manuais fundamentadas conservam a sua adoção. Esforços alterados sem fundamentação têm de ser resolvidos em **Origem dos esforços…** antes da revisão.

Os resultados cujas entradas ou proveniência mudaram ficam por calcular. Os restantes mantêm os seus registos de cálculo. A revisão dos eixos não muda o referencial da laje: **Orientar ligação…** continua a ser a operação própria para rodar conjuntamente o caso.

## 2. Conferir as ligações

O programa apresenta os nós, as cotas disponíveis e os tramos. Ligações inequívocas entre dois tramos verticais são incluídas inicialmente. Filtre por piso, pilar ou nó; inclua apenas as ligações pretendidas.

O **piso da ligação** é sugerido a partir de `Story` do tramo inferior. Confira-o com a cota da laje e edite a designação, se necessário. Um ficheiro com «PISO 02» no nome pode conter vários pisos: o nome do ficheiro não define o âmbito.

Para completar uma associação, selecione a linha e indique piso, pilar, tramo inferior e tramo superior. As alterações são conservadas ao mudar de linha, filtrar ou conferir. O botão **Aplicar à ligação selecionada** atualiza imediatamente a lista.

Um nó com um único tramo não é considerado cobertura automaticamente. A opção **Tramo superior fisicamente ausente** requer essa condição real no modelo; ausência de resultados no ficheiro não basta.

Prima **Conferir ligações**. Confira as resultantes e pendências por combinação e use **Aplicar ligações conferidas**. São criados casos com os esforços disponíveis já adotados. Tipo de apoio, altura útil, materiais e armaduras da laje ficam por definir.

## 3. Esforços da ligação

A carga vertical transmitida pela laje é obtida no mesmo nó e na mesma combinação, com compressão positiva:

`VEd = FX do topo do tramo inferior − FX da base do tramo superior`

Não é a diferença entre os dois extremos da mesma barra. Não é o esforço axial acumulado. Neste passo, VEd ainda não inclui beta nem a dedução de cargas interiores ao perímetro.

Os momentos locais MY/MZ são transformados para ações das barras sobre o nó usando os eixos e o extremo de cada barra. Depois são somados e convertidos para a convenção do programa: `MEdx = ΣMx,nó`, `MEdy = −ΣMy,nó`, com `ex = MEdy/VEd` e `ey = MEdx/VEd`. A memória conserva os valores originais, linhas, transformações e valores adotados. Ver [MODELO_IMPORTACAO.md](MODELO_IMPORTACAO.md) para a convenção Modelo e o seu âmbito.

Se uma combinação selecionada faltar por inteiro nos dois tramos de uma ligação, a preparação pede para completar a exportação ou rever expressamente o filtro. Essa combinação não pode desaparecer silenciosamente do âmbito.

**CQC/SRSS e envolventes não produzem uma resultante pela subtração direta dos valores tabelados.** Permanecem visíveis, com esforços pendentes. Uma combinação selecionada com pendências impede que a ligação seja apresentada globalmente como verificada. Para a resolver, associe uma resultante fundamentada e compatível com o referencial do caso.

## 4. Analisar um pilar num piso

Em **Pilares…**, as ligações preparadas pelo modelo aparecem numa linha por piso/pilar, com o número de combinações. Selecione a ligação e prima **Analisar ligação**.

Preencha posição do pilar, afastamento ao bordo, altura útil, materiais, armaduras da laje, aberturas e método de beta. Estes dados são comuns às combinações da ligação. Ao mudar de combinação/pilar, calcular ou guardar, o programa conserva e sincroniza essas entradas. Cada combinação mantém os seus esforços, origem e sentidos de excentricidade. Alterações aos dados comuns invalidam os resultados anteriores afetados.

### Orientação relativamente ao bordo

Use **Dados → Orientar ligação…**. X e Y do caso são os eixos da planta apresentada. Num bordo, Y aponta para o interior da laje e X é paralelo ao bordo; o bordo fica em −Y do caso.

| Bordo no modelo | X do caso | Y do caso |
|---|---|---|
| −Y | +X do modelo | +Y do modelo |
| +X | +Y do modelo | −X do modelo |
| +Y | −X do modelo | −Y do modelo |
| −X | −Y do modelo | +X do modelo |

A mudança de referencial roda conjuntamente esforços, dimensões do pilar, dx/dy, direções das armaduras, aberturas e setores de todas as combinações dessa ligação. Confira a localização física do bordo depois da operação. No canto, os bordos ficam em −X e −Y do caso. Pilares/contornos oblíquos não estão incluídos nesta automatização.

Se existirem esforços alterados manualmente ou fontes adicionais, a rotação fica bloqueada até essas fontes serem convertidas e conferidas. A mudança de referencial não pode apagar uma alteração manual nem justificar beta.

### Cálculo e combinações condicionantes

**F5** calcula todas as combinações selecionadas desta ligação. A janela **Combinações…** apresenta os esforços, beta, estados e combinações condicionantes. Pode escolher a combinação que pretende observar nas verificações, fiadas e planta.

Cada combinação é calculada com VEd/MEd concomitantes. A combinação condicionante é apurada por verificação; os maiores VEd, MEdx e MEdy de casos diferentes não são reunidos num esforço artificial.

Quando forem propostas armaduras de punçoamento diferentes entre combinações, aparece **PORMENOR COMUM POR CONFERIR**. Deve conferir a mesma disposição física de armadura em todas as combinações relevantes; a maior área de aço, isoladamente, não resolve diferenças de extensão e distribuição.

## 5. Guardar e exportar

Use **Pilares… → Guardar conjunto…** para conservar tabelas, configuração do modelo, ligações e dados preenchidos. **Abrir conjunto…** recupera o trabalho e os cálculos guardados que correspondem às mesmas entradas e versão. Alterações ou resultados de outra versão exigem novo cálculo. O botão Guardar da janela principal destina-se ao caso individual.


O relatório organiza as ligações por piso e pilar. Por predefinição inclui apenas resultados calculados e atualizados, identificando a cobertura parcial e as pendências excluídas. O PDF apresenta a memória das combinações condicionantes; pode pedir o detalhe de todas as combinações abrangidas. TXT e JSON respeitam o âmbito escolhido. A exportação XLSX individual continua disponível na janela principal.

O âmbito do relatório é o das ligações preparadas e selecionadas. Não inclui automaticamente nós excluídos, pisos ausentes da exportação ou ligações ainda não preparadas.

Os conjuntos são guardados no formato `connections/3`, com tabelas partilhadas, referências compactas por ligação, parâmetros de grupo e registos dos cálculos executados. Ao abrir, as resultantes são reconstruídas e conferidas. Os formatos anteriores continuam legíveis; calcule novamente ao mudar de versão do programa.

Pode rever os eixos e acrescentar ligações ou combinações no mesmo conjunto. O filtro não pode retirar combinações já preparadas: use os filtros do relatório para restringir a exportação. Uma nova revisão dos ficheiros de origem ou da associação dos tramos continua a exigir um conjunto próprio, preservando o anterior.

## Exemplo incluído: edifício de escritórios

Todos os dados seguintes são fictícios e destinam-se a aprender a utilização:

- `examples/importacao/Modelo_Pilares.csv`: P01 e P02, com três tramos verticais por pilar e três combinações.
- `examples/importacao/Modelo_Nos.csv`: oito nós, pisos às cotas 3 e 6 m.
- `examples/importacao/Modelo_Ligacoes.json`: quatro ligações preparadas e doze combinações, com a laje por preencher.

Abra **Pilares… → Abrir conjunto… → Modelo_Ligacoes.json**. Para experimentar a verificação, escolha Piso 1/P01, pilar interior, d = 0,22 m, C30/37, As,x = 10 cm²/m e As,y = 12 cm²/m; mantenha as restantes opções iniciais e calcule.

| Piso / pilar | Combinação | VEd | MEdx | MEdy |
|---|---|---|---|---|
| Piso 1 / P01 | 201 (C) | 300 kN | 12 kN.m | 11 kN.m |
| Piso 1 / P01 | 202 (C) | 340 kN | 12 kN.m | 11 kN.m |
| Piso 2 / P01 | 201 (C) | 280 kN | 8 kN.m | 6 kN.m |

P01 tem x local = +Z e y local = +X; P02 tem y local = +Y, declarado nas exceções das barras 201/202/203. A configuração refere-se apenas a este exemplo. A combinação 203 (CQC) mantém-se pendente e a conclusão global é PENDENTE, mesmo quando as duas combinações estáticas verificam.


## Gestão em lote e relatórios

Na versão 1.13.0, a lista de pilares permite grupos, seleção múltipla e parâmetros comuns. A exportação usa os resultados atuais e filtra por predefinição os casos calculados; as ligações incompletas são identificadas como parciais. Consulte [GRUPOS_E_RELATORIOS.md](GRUPOS_E_RELATORIOS.md) para o procedimento e as regras de conservação dos dados.
