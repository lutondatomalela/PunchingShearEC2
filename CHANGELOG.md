# Histórico de alterações

## 1.15.1-rc.1 — 2026-09-15

- Primeira candidata com executável Windows x64 autónomo, ícone e metadados.
- Testes com leitura UTF-8 explícita; regressão da consola CP1252.
- A linha de comandos representa símbolos não disponíveis por escapes, conservando os relatórios UTF-8.
- Compilação e ensaio do executável condicionados à aprovação da suite em Linux e Windows.
- Publicação em Releases com código-fonte, ZIP, executável, metadados e hashes SHA-256.
- Fórmulas e formato de projetos preservados; revisão visual completa pendente.


## Publicação da base 1.15.0 — 2026-09-15

- Código da aplicação e testes conservados integralmente da distribuição 1.15.0.
- Documentação de apresentação reorganizada, inventário SHA-256 e política de evolução da base.
- Integração contínua e publicação inicial condicionada à aprovação dos testes.
- Registos associados a fontes privadas excluídos da publicação pública.

## 1.15.0 — 2026-09-13

- Barras por listas e intervalos: `110para113 115 118para123`, `110-113 115 118-123` ou números separados por espaços. A aplicação e remoção de exceções é atómica; identificadores ausentes e intervalos inválidos são apresentados antes de qualquer alteração.
- **Estender à prumada** identifica barras verticais conectadas pelos mesmos nós e alinhadas em planta, com coordenadas importadas. A lista é apresentada antes da aplicação dos eixos; nomes, números, lacunas e barras inclinadas não estabelecem continuidade.
- **Guardar configuração e fechar** grava o conjunto e regressa à lista de pilares mesmo sem novas ligações selecionadas. A primeira gravação pede o ficheiro; as seguintes usam o caminho do conjunto aberto/guardado. Cancelamento e erro de escrita conservam a configuração anterior.
- Revisão dos eixos nas ligações existentes, com regeneração da proveniência e conservação da orientação do caso, dados da laje, armaduras, aberturas, grupos e fontes manuais. Cálculos afetados são invalidados; os restantes são conservados.
- Geometria proveniente da importação acompanha a revisão dos eixos. Dimensões alteradas pelo utilizador são conservadas e identificadas na conferência.
- As ligações existentes aparecem como **Preparada**, com a associação dos tramos protegida. Deixam de apresentar uma caixa de inclusão aparentemente editável que não tinha efeito.
- Configuração sem ligações pode ser guardada e reaberta. O filtro pode acrescentar combinações; retirar combinações já preparadas continua bloqueado para não apagar trabalho existente.
- Resumo das exceções agrupado por perfil, intervalos compactos e lista completa acessível em **Ver exceções…**. Comandos de rodapé repartidos por duas linhas.
- Expressões de resistência, geometria de punçoamento, armaduras e relatórios numéricos conservados da versão 1.14.0.

## 1.14.0 — 2026-09-12

- Modo automático de armadura longitudinal, com base e reforço intercalados por direção X/Y, espaçamento comum e série prática.
- Cálculo de As,x e As,y a partir dos diâmetros e espaçamento; cálculo de dx, dy e d a partir de h, recobrimento longitudinal e ordem das camadas.
- Disposição explícita com eixos coplanares por direção e duas camadas ortogonais. O maior diâmetro define a envolvente de cada camada. Afastamento X/Y configurável.
- Equivalência de duas malhas iguais intercaladas: por exemplo, Ø10 // 200 + Ø10 // 200 = Ø10 // 100. Combinações mistas conservam os dois diâmetros.
- Integração com a edição por grupos, predefinições de piso/grupo, gravação de casos e conjuntos, rotação e relatórios PDF/TXT/JSON/XLSX.
- Modo manual preservado; migração dos conjuntos antigos sem alterar as áreas e alturas úteis introduzidas. Valores automáticos derivados são recalculados a partir da definição guardada.
- Novo exemplo fictício e guia ARMADURA_LONGITUDINAL.md. Cálculos resistentes existentes mantidos.

## 1.13.0 — 2026-09-12

- Grupos personalizados de ligações, filtros por piso/posição/direção do bordo/grupo, seleção múltipla e cálculo da seleção.
- Editor em lote com campos assinalados: preencher vazios ou atualizar a seleção. Preservação dos esforços, dimensões e aberturas individuais.
- Predefinições de projeto, piso e grupo; conservação do nome do projeto, materiais, coeficientes e parâmetros de armadura, incluindo s0/sr automáticos.
- Relatório por piso, grupo ou seleção: apenas calculados e atualizados por predefinição, incluindo falhas. Cobertura das combinações e indicação explícita de resultados parciais. Mapa geral de acompanhamento opcional.
- A exportação deixa de executar novos cálculos. O esquema de conjunto 3 conserva as combinações já executadas e reconstrói os casos compatíveis ao reabrir; leitura dos esquemas 1 e 2 mantida.
- Correção transacional da orientação: os sentidos de excentricidade são reconciliados com a fonte validada, conservando a rejeição de esforços alterados manualmente.
- Terminologia neutra na aplicação, documentação, perfis e formatos gerados. Leitura dos identificadores de adaptador das versões anteriores.
- Motor resistente, geometria, pormenorização, aberturas e determinação de β sem alterações face à versão 1.12.0.


## 1.12.0 — 2026-09-12

- Preparação de várias ligações Modelo com perfil comum de eixos, exceções por barra, filtro de combinações e conferência de nós/pisos.
- Reconhecimento dos tramos por coordenadas; associação explícita sem coordenadas. Extremos isolados continuam sem identificação automática como cobertura.
- Esforços concomitantes adotados por combinação; CQC/SRSS e restantes pendências permanecem visíveis.
- Dados comuns da laje por piso/pilar, cálculo por F5, seleção de combinações e condicionantes por verificação.
- Mudança de referencial com rotação conjunta de esforços, secção, armaduras e aberturas; alterações de fonte não são ocultadas.
- Relatório do conjunto em PDF/TXT/JSON, recalculado antes de exportar, com âmbito e pendências explícitos. Propostas de armadura distintas exigem conferência de um pormenor comum.
- Conjuntos automáticos compactos `connections/2`; reconstrução a partir das tabelas ao reabrir, deteção de casos em falta e compatibilidade com `connections/1`.
- Exemplo fictício de dois pisos, quatro ligações e doze combinações, com guia de utilização.
- 426 testes; 29 referências iguais à versão 1.11.1, excluindo metadados da execução; cinco módulos resistentes sem alterações.
- Conferência de leitura e persistência em amostras de utilização; ensaio de 100 ligações/3 300 combinações num modelo sintético. O ensaio visual nativo no Ambiente de trabalho continua por realizar.


## 1.11.1 — 2026-09-11

- Corrigida a rejeição de barras sem Name: a chave barra/nó/caso permite conservar os registos. A identificação de consulta passa a «Barra N», sem alterar o campo original. A ausência de toda a coluna Name também é admitida.
- Um nome preenchido noutra linha da mesma barra pode ser recuperado, incluindo entre tabelas, com referência à linha usada. Não se copia o nome de barras vizinhas. Nomes explicitamente incompatíveis continuam a impedir a importação.
- Resumo da importação com pisos presentes, registos sem nome e combinações CQC/SRSS. O consultor e a memória identificam a origem do nome. O nome da ligação pode ser definido ao prepará-la.
- CQC/SRSS ficam disponíveis para consulta, mas o adaptador não subtrai/soma diretamente respostas modais já combinadas para obter VEd/MEd. Estes casos ficam pendentes de resultantes fundamentadas. Um resultado antigo que tenha adotado esse equilíbrio é rejeitado com indicação de reimportação.
- Ensaiadas importações UTF-16 com nomes em falta, comparação de valores e gravação/reabertura. Os ficheiros de projeto e os registos associados a fontes privadas não integram a publicação.
- 392 testes aprovados; 29 casos de referência e cinco módulos de cálculo sem alterações face à versão 1.11.0. Incluídos exemplo fictício com nomes em falta e guia atualizado. Ensaio visual nativo no Ambiente de trabalho pendente.

# Alterações — 1.11.0 — 11-09-2026

- Perfil Modelo para tabelas de barras: separação automática de Member/Node/Case; identificação por Name/Story; leitura de FX, MY e MZ com as respetivas unidades. Reconhecimento do cabeçalho nas primeiras 50 linhas, do separador e da convenção decimal.
- Conferência da secção maciça retangular ou circular por HY/HZ, AX e IY/IZ. Dimensões incompatíveis ficam por definir; c1/c2 dependem da orientação adotada no caso.
- Consulta dos resultados por piso da barra, pilar, barra, nó e combinação, com filtros, paginação e acesso à linha original. Tabela opcional de coordenadas dos nós para identificar topo/base, sem recorrer à ordem das linhas ou aos números dos nós.
- Preparação de uma ligação no nó comum, por combinação ou conjunto de combinações. Conversão dos momentos locais de barras 3D verticais para ações sobre o nó, com orientação dos eixos e âmbito conferidos. Bloqueio de barras adicionais conhecidas, posições incompatíveis e eixos não suportados; ausência de dados do superior mantém a pendência.
- Gravação das tabelas e associações no conjunto, incluindo conjuntos ainda sem ligações. Proveniência Modelo nas exportações e reconstrução dos esforços guardados na reabertura.
- Exemplos profissionais com dados fictícios, guia MODELO_IMPORTACAO.md e ensaios de leitura, equilíbrio, interface e persistência. O motor resistente conserva os mesmos bytes da versão 1.10.0. Validação com exportação real e interface nativa Ambiente de trabalho ainda pendente.

# Alterações — 1.10.0 — 11-09-2026

- Importação opcional de XLSX, CSV e TSV, com folha/cabeçalho, associação de colunas, unidades, separador decimal e codificação explícitos.
- Geometria por piso/pilar e esforços por piso/pilar/combinação. Equilíbrio dos extremos com N normalizado e momentos de ações sobre o nó. Ausência do superior explicitamente declarada; sem mistura de combinações nem valor absoluto de VEd.
- Resultantes integrais da ligação como fonte alternativa, com comparação de fontes e adoção explícita. Resultados locais de lajes por metro não são convertidos automaticamente.
- Gestor de ligações, conservação de rascunhos por caso, gravação/reabertura do conjunto e identificação de dados por resolver. A laje, armaduras e posição do pilar começam por definir.
- Proveniência e equilíbrio nas quatro exportações e na memória. Alterações manuais mantêm os valores originais e a fundamentação. Reabertura de casos/resultados individuais com origem preservada.
- Conjunto, XLSX e CSV de exemplo; documentação em IMPORTACAO.md. Leitura de folhas sem dimensões declaradas e conferência dos valores guardados contra os registos de origem.
- Módulos core, geometry, detailing, openings e beta_trace sem alterações face à versão 1.9.0. A CLI conserva e confere a proveniência dos novos casos. A interface nativa em Ambiente de trabalho e uma exportação real do software utilizado devem ainda ser ensaiadas antes de atualizar o GitHub.

# Alterações — 1.9.0 — 11-09-2026

- Renovação visual da aplicação: tema azul e branco, tipografia uniforme, unidades junto das entradas, formulários à esquerda e área de planta/resultados à direita.
- Separação da apresentação em módulos próprios, sem alterações ao motor de cálculo, geometria, armadura ou formatos de exportação.
- Nomes legíveis para os métodos de β; os campos de cada método acompanham a seleção. As chaves EC2/JSON existentes mantêm-se. A orientação dos esforços passa para Dados, com controlos apenas para bordo/canto.
- Ajuda contextual expansível, janela de ajuda e atalhos Ctrl+N/O/S, F5 e F1. Catálogo de 29 exemplos pesquisável, com descrições técnicas.
- Indicadores de β, perímetro efetivo e utilização resistente. Resultados anteriores retirados após alterações, com exportações desativadas até recalcular.
- Edição do pilar ativada explicitamente; arrastamento limitado às pegas, escala estável durante o movimento e reenquadramento ao terminar. A planta utiliza as dimensões reais do painel.
- Editor de aberturas com o mesmo tema e mensagem neutra sobre o método de β, sem declarar uma pendência que não avaliou.
- Valores válidos dos métodos inativos conservados. Rascunhos numéricos inválidos em campos ocultos não utilizados não bloqueiam outro método; são guardados como vazios opcionais ou pressão inativa 0.
- Guião de ensaio da interface no Ambiente de trabalho em GUI_TESTES.md. Os ensaios automatizados não substituem a revisão visual nativa e de escalas de ecrã. Esta entrega antecede a atualização do repositório.

# Versão 1.8.0 - 11 de setembro de 2026

- Editor de aberturas retangulares e circulares na GUI: desenho, seleção, movimento, redimensionamento, medidas exatas e posicionamento por distância à face.
- Distância mínima face a face, limite 6d, tangentes analíticas e ajuste de largura da Figura 6.14. Envolvente conservadora explicitada para o ajuste de retângulos em posição oblíqua.
- Gravação das geometrias e recálculo dos setores; preservação dos setores manuais e dos casos anteriores. Cancelamento transacional e invalidação de resultados após alterações.
- Aberturas e construção equivalente nos esquemas e na memória; nova folha Aberturas no XLSX.
- Rejeição de contactos/sobreposições e conferência do recobrimento dos ramos junto às aberturas. A fundamentação específica de beta mantém-se.
- Cinco novos exemplos com descrição técnica; catálogo com 29 exemplos. Instruções em ABERTURAS_GUI.md.

# Alterações - 1.7.0 - 11-09-2026

- Introduzida (6.43) como método predefinido do pilar interior retangular, incluindo os limites uniaxiais e concêntrico. O utilizador pode selecionar (6.39); não há mudança automática de fórmula junto de momento nulo.
- Implementada a expressão geral (6.39) para bordo exterior encostado, com W referido ao centro do perímetro e k do Quadro 6.1. Os momentos de entrada no centro do pilar são transportados uma única vez para o centro do perímetro.
- Acrescentada uma opção explícita de soma conservadora das majorações de (6.39) por direção para os casos gerais biaxiais e canto exterior. A memória distingue esta hipótese de combinação de uma equação biaxial literal do EC2. A opção abre desativada.
- Mantidas as pendências para g > 0 e aberturas; a opção biaxial não as elimina.
- Nova secção de determinação de beta na memória, com expressões, substituições, valores intermédios, unidades, referências e condições de aplicação. Nova folha Beta no XLSX.
- Separado o rótulo de k do efeito de escala dos coeficientes de transferência de momentos.
- Acrescentados seis exemplos com descrições técnicas, totalizando 24. Incluídos interior biaxial, interior uniaxial, bordo exterior uniaxial/biaxial e canto exterior com e sem seleção do modelo.
- Novos ensaios de eixos em secção não quadrada, integração independente de W e do centro dos contornos, transporte dos momentos, k por direção, condições dos métodos e coerência das exportações.

**Compatibilidade:** os casos antigos são recalculados. Para interiores retangulares sem indicação de método passa a aplicar-se (6.43), em vez da soma de majorações anterior; os valores podem mudar. O modo manual e as condições do simplificado mantêm-se. Os novos campos são interior_beta_method e allow_biaxial_envelope. A revisão não certifica todos os casos estruturais nem valida genericamente os fatores introduzidos manualmente.

# Alterações - 1.6.0 - 10-09-2026

- Retirado o cálculo automático geral de beta com k = 1 e translação MEd-VEd*CG, que produzia uma alteração abrupta quando g passava de zero a um valor positivo.
- Novo estado BETA_PENDING para g > 0, setores ineficazes ou excentricidade exterior de bordo/canto no modo EC2 automático. Mantém a geometria disponível, sem emitir conclusão resistente ou dimensionar armadura com beta por fundamentar.
- Acrescentado modo manual, com valor beta e referência obrigatória da análise. O fator é aplicado em u0, nos contornos de controlo e exteriores.
- Corrigido o modo simplificado: aplica diretamente os valores de 6.4.3(6), mediante declaração das condições, sem acumular o modelo geral retirado.
- Retido u0 do bordo encostado como limite conservador de capacidade para g > 0. A quarta face não recebe crédito automático; a hipótese e a sua possível restrição constam da memória e do JSON.
- O momento normal nulo passa a ser o limite do ramo interior de (6.44); também se consideram os limites de momentos nulos no canto interior de (6.46).
- Separados Asw/sr por resistência, referência mínima em u1 e verificação local de (9.11) por ramo. Os relatórios e o XLSX mostram áreas, mínimos e utilização local por fiada.
- Uniformizada a necessidade por resistência usada pelo gerador de fiadas afastadas; a armadura mínima é verificada na geometria real de cada fiada.
- Reorganizados 18 exemplos com nomes, descrições e metadados técnicos. O catálogo único alimenta a interface e os ficheiros JSON.
- Adicionados os casos com VEd = 594 kN e g = 0, 1 e 343 mm, e dois estudos condicionais com beta simplificado.
- Novos testes de transição, âmbito, mínimos locais, catálogo e exportação de pendências. Mantidos os ensaios de corrupção de coordenadas e de estados de cálculo.

**Alteração de âmbito:** esta versão não valida uma fórmula automática de beta para pilares afastados do bordo. A correção impede conclusões baseadas no modelo retirado e permite prosseguir com uma fundamentação explícita. Os casos antigos abrem, mas podem devolver BETA_PENDING. As verificações da versão 1.5.0 afetadas pelo modelo anterior não são convalidadas.

**Compatibilidade de resultados:** Asw_sr_req passa a significar requisito por resistência, em m²/m. O mínimo local fica em cada fiada; Asw_sr_min_u1_reference identifica o valor de referência em u1. O campo antigo Asw_sr_min mantém-se como referência histórica dos contornos, sem constituir um mínimo universal.

O histórico abaixo descreve o comportamento de cada versão na data respetiva. Os métodos retirados e os resultados antigos não devem ser lidos como comportamento da versão atual.

# Alterações — 1.5.0 — 10-09-2026

## Distribuição da armadura com afastamento ao bordo

- Completada a geração de fiadas abertas em U e de fechos adicionais necessários para a verificação do contorno fechado.
- Cada contorno recebe apenas a área dos ramos que o atravessam. Ramos comuns não são duplicados no inventário físico. O XLSX e o JSON identificam a correspondência por fiada e ramo.
- Conferência das posições XY: área, mínimo por ramo, st, sr, recobrimento, distâncias livres entre todos os ramos, número de fiadas e extensão da última fiada.
- O estado `EDGE_DETAIL_PENDING` da versão 1.4.0 deixa de bloquear os novos cálculos: a proposta válida passa a `DETAIL_PENDING` ou `PASS_WITH`, conforme a declaração de amarração. Distribuições incompletas ou não conformes ficam em `FAIL_DETAIL` e não são aprovadas por essa declaração.
- Novo separador **Fiadas**, com quantidade de ramos, áreas e espaçamentos. Mensagens do separador Pormenor atualizadas.
- Acrescentadas as folhas XLSX `FiadasContornos` e `Pormenorizacao`, as verificações por contorno e a respetiva informação no PDF/TXT/JSON.
- Incluído o ligação de bordo com flexão biaxial: VEd = 371 kN, MEdx = -10 kN.m, MEdy = -65 kN.m, d = 0,202 m e As,x = As,y = 13,98 cm²/m. Mantêm-se beta = 1,656147034 e vEd,u1 = 0,817845931 MPa; passa a existir uma proposta de seis fiadas Ø10.
- Ensaios independentes das posições sobre o U e dos ramos pertencentes a contornos alternativos. Ensaios de corrupção de posições confirmam que dados de área ou declarações de amarração não permitem uma falsa aprovação.

A amarração, as dobras e a compatibilidade em altura continuam a exigir o pormenor construtivo do projetista. O novo algoritmo calcula ramos verticais; não fornece a forma completa ou a lista de corte de estribos. O âmbito continua limitado a um bordo livre e a lajes de altura útil constante.

## Histórico — 1.4.0 — 10-09-2026

## Afastamento a um bordo livre

- Novo argumento `edge_distance_m` (m), predefinido como zero. Aplica-se a pilares retangulares do tipo `bordo`; mede a distância livre entre a face do pilar e um bordo livre da laje.
- Introdução na interface, gravação e reabertura de casos JSON, memória, XLSX, PDF e desenho com o bordo à distância real e indicação de g.
- Comparação entre contorno fechado e contorno aberto que termina no bordo. O bordo livre não contribui para o comprimento resistente; um contorno fechado que toca ou ultrapassa o bordo é identificado como não admissível.
- Consideração do centro de gravidade e dos momentos estáticos do contorno efetivo. O cálculo envolve a tensão dos contornos admissíveis, mantendo o menor comprimento como referência de u1.
- A comparação é repetida no contorno exterior, incluindo as transições entre contorno fechado e aberto. Setores ineficazes são aplicados às duas alternativas.
- Armadura requerida registada por contorno. Quando um contorno aberto é relevante, o estado `EDGE_DETAIL_PENDING` mantém a distribuição dos ramos e a amarração pendentes de avaliação específica. A confirmação de amarração não aprova automaticamente este pormenor.
- Exemplo P157: c1 = 0,25 m, c2 = 0,70 m, d = 0,20 m e g = 0,40 m. Contorno fechado geométrico = 4,413 m; aberto = 3,707 m. As ações do exemplo são ilustrativas.
- Os casos com afastamento zero preservam o cálculo da versão 1.3.0. Afastamentos positivos em casos de canto, interiores, circulares de bordo ou sapatas são rejeitados.
- Casos antigos continuam a abrir: na ausência do novo argumento adota-se g = 0. A versão e o identificador das novas execuções mudam para 1.4.0.

Na versão 1.4.0, o novo campo representava **um bordo livre**, mantendo a convenção c1 paralelo/c2 perpendicular ao bordo. Distâncias a dois bordos próximos e pormenorização automática para os contornos abertos com afastamento ainda não estavam implementadas; esta última foi acrescentada em 1.5.0.

## Histórico — 1.3.0 — 09-09-2026

Base: ZIP `PunchingShearEC2-main.zip` fornecido pelo utilizador, motor identificado como 1.2.0. SHA-256 da base:

`9f62c81caa7b25dcd71523b499081ac59b73ad90a3694f6c43eecc4e9c6b331d`

## Correções que podem alterar a decisão

- Corrigidos u1 e u1* de pilares retangulares de bordo e canto. Corrigida a correspondência entre c1/c2 da interface e da Figura 6.20 na determinação de u0 e k.
- Contornos, comprimentos, centros geométricos e momentos estáticos partilham a mesma representação de retas e arcos. Os desenhos usam esses contornos.
- A componente paralela do momento no bordo exterior deixa de ser ignorada. O caso geral considera os dois momentos em relação ao centro do perímetro efetivo, com a opção conservadora documentada no README.
- Retirado o modo fib que saturava artificialmente beta e misturava o perímetro do EC2 com parâmetros fib.
- Validação de finitude, sinais, materiais, coeficientes, armaduras e geometrias no motor; entradas fora do âmbito definido são rejeitadas.
- Sapatas: integração da reação útil na área real, pesquisa da secção condicionante entre a face e 2d, fator resistente 2d/a e exclusão dos bordos livres no perímetro resistente.
- Aberturas: setores aplicados aos contornos relevantes e unidos sem duplicação; rejeitada a antiga dedução isolada em u1. A extensão da armadura é calculada no contorno exterior efetivo.
- Mantidos e documentados os coeficientes 0,4 da resistência na face (AC:2012) e kmax = 1,5 (A1:2019/Anexo Nacional português).

## Armadura e apresentação

- A proposta de estribos define diâmetro, número de ramos, área e coordenadas de cada fiada. Verifica resistência instalada, armadura mínima por ramo, sr, st, posição da primeira fiada, extensão da última e distância livre mínima entre ramos.
- A amarração depende de confirmação do projetista. Sem confirmação, a proposta tem estado pendente. O módulo não dimensiona amarrações nem sistemas comerciais.
- Estados únicos e explícitos para falha em u0, ultrapassagem de kmax, pormenor pendente e outras situações. Uma falha resistente não é apresentada como mera necessidade de acrescentar armadura.
- Valores não calculados ficam indisponíveis; deixaram de ser apresentados como armadura zero ou dispensa de armadura.
- GUI e exportações partilham o resultado da execução. Alterar entradas bloqueia exportações até novo cálculo; um cálculo inválido elimina o resultado anterior da interface.
- JSON de casos e de resultados, identificação da execução e relatórios PDF/XLSX/TXT coerentes. O XLSX regista também ramos, fiadas e secções de sapatas.
- Introduzidas dx/dy opcionais, combinação e identificação do apoio. As áreas longitudinais continuam a ser fornecidas pelo projetista.
- Versão centralizada, importação do pacote corrigida e interface de linha de comandos com códigos de saída distintos.

## Compatibilidade e âmbito

Mantém-se `from Punching_EC2 import PuncoamentoEC2`. Métodos internos antigos e a disposição visual da GUI não constituem uma API estável. As entradas de cálculo são preservadas por execução: crie outro objeto para outro caso.

Casos anteriores com fib, dedução isolada de u1, pilares circulares de bordo/canto, apoios com razão entre dimensões ≥ 4 ou sapatas fora do âmbito atual devem ser reformulados ou tratados por avaliação específica. O bloqueio destes casos é intencional e consta das mensagens do programa.

Na versão 1.3.0 ainda não estavam implementados: pilares afastados de bordos próximos; editor de aberturas por posição/dimensões; capitéis/espessura variável; cálculo completo fib; cálculo de alturas úteis e médias de As a partir das camadas de armadura; importação em lote e envolvente de combinações; armadura automática de sapatas. O primeiro destes pontos foi tratado na versão 1.4.0 para um único bordo livre, com o âmbito descrito acima.

Os testes e exemplos verificam as regressões identificadas e as regras descritas em `VALIDACAO.md`. Foi recalculado o caso fornecido na imagem; não foi feita uma validação de todos os intervalos de entrada nem uma revisão dos restantes projetos do utilizador.
