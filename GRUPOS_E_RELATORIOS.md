# Grupos e relatórios — PunchingShearEC2 1.13.0

Esta versão permite preparar e calcular vários pilares na mesma sessão. Cada ligação conserva os seus esforços por combinação, a secção, as aberturas, o afastamento aos bordos e os dados que já foram definidos individualmente.

## 1. Abrir o trabalho existente

Extraia a nova distribuição para uma pasta própria. Inicie `main.py` ou `iniciar.bat` e use **Pilares… → Abrir conjunto…** para abrir o JSON anteriormente guardado. A leitura aceita os esquemas de conjunto 1 e 2 e converte-os para o esquema 3 ao guardar. Os dados existentes são preservados como exceções individuais. O ficheiro anterior só é substituído se escolher esse destino ao guardar.

Os conjuntos antigos exigem novo cálculo na versão 1.13.0. Nos conjuntos guardados nesta versão, os casos previamente executados e sem alterações são reconstruídos a partir dos dados e fontes conservados. Os restantes pilares continuam por calcular. O programa não utiliza números de resultados arquivados como prova de uma verificação.

## 2. Filtrar e selecionar pilares

Abra **Pilares…**. Use os filtros **Piso**, **Posição / bordo** e **Grupo**, ou escreva o nome do pilar na pesquisa. A coluna final apresenta o número de combinações calculadas e o total da ligação.

Selecione uma linha, alargue a seleção com **Ctrl** ou **Shift**, ou prima **Selecionar visíveis**. **Limpar seleção** retira a seleção atual. Os filtros limitam as linhas visíveis; as operações em lote abrangem apenas as linhas selecionadas, incluindo as combinações de cada ligação.

Os pilares de bordo são distinguidos pela direção do bordo livre no modelo: +X, −X, +Y ou −Y. Nos cantos, a classificação mostra o par de bordos. Estes dados resultam da posição e da orientação declaradas no caso; não são inferidos automaticamente da forma da malha da laje.

## 3. Criar um grupo

Selecione os pilares e prima **Agrupar…**. Escreva um nome, por exemplo **COBERTURA · Bordo −X**, ou escolha um grupo existente. A atribuição organiza a seleção; a alteração dos parâmetros faz-se em **Editar seleção…**.

Uma ligação pertence a um grupo personalizado. A atribuição a outro grupo transfere essa ligação. **Dissolver grupo** remove a organização do grupo filtrado, conservando os pilares, os dados e os resultados atuais.

## 4. Aplicar dados comuns

Prima **Editar seleção…** e assinale exclusivamente os campos que pretende aplicar. Os separadores organizam projeto e materiais, laje, armadura de punçoamento e posição do pilar.

| Operação | Resultado |
|---|---|
| Preencher apenas campos vazios | Completa os campos assinalados que ainda não têm valor. Conserva valores existentes. |
| Atualizar os campos assinalados | Aplica esses campos a todos os pilares selecionados. Os outros dados são conservados. |
| Orientação: Manter em cada pilar | Conserva o referencial individual. |
| Escolher uma orientação | Roda as ligações selecionadas para esse referencial, incluindo esforços, geometria e aberturas. |

Para voltar a **s0** ou **sr automático**, assinale o campo, deixe-o vazio e escolha **Atualizar os campos assinalados**. No modo de preenchimento de vazios, um valor já definido continua inalterado. Os campos dx e dy vazios utilizam a altura útil média d; quando ambos estão preenchidos, d é obtido pela sua média.

As,x, As,y, dx e dy referem-se aos eixos do caso após a orientação escolhida. Os valores comuns não devem ser aplicados a direções fisicamente diferentes sem essa conferência.

Os esforços, dimensões da secção, aberturas e declarações técnicas não são copiados entre pilares pelo editor em lote. A confirmação de amarração e a fundamentação de métodos de β pertencem a cada ligação. O motor continua a verificar os valores e o âmbito de cada caso durante o cálculo.

## 5. Reutilizar os parâmetros

O nome do projeto, materiais, coeficientes parciais, diâmetro dos ramos, s0, sr, recobrimento e agregado editados numa ligação são recordados para inicializar pilares ainda não editados do mesmo conjunto. As exceções já definidas são conservadas.

O editor em lote permite guardar os campos assinalados como predefinição:

| Nível | Parâmetros admitidos |
|---|---|
| Projeto | Identificação, materiais, coeficientes e parâmetros de armadura de punçoamento. |
| Piso | Parâmetros de projeto, alturas úteis, armaduras longitudinais e compressão no plano. |
| Grupo | Os parâmetros anteriores, posição do pilar e afastamento ao bordo. |

A prioridade de inicialização é **projeto → piso → grupo**. Um pilar já editado conserva os seus valores. Para rever pilares existentes, selecione-os e aplique explicitamente os campos pretendidos. As predefinições de piso ou grupo são apresentadas quando a seleção pertence a um único piso ou grupo, respetivamente.

## 6. Calcular a seleção

Prima **Calcular seleção**. O programa executa as combinações dos pilares selecionados, mantendo cada conjunto de esforços concomitantes. A janela apresenta o avanço e permite interromper após a combinação em execução. Os resultados já obtidos são conservados.

Para uma ligação preparada a partir do modelo, **Analisar ligação → F5** continua a calcular as suas combinações. **Combinações…** permite consultar o estado e apresentar uma combinação específica. Nos casos importados individualmente, o cálculo pela seleção também abrange as combinações da ligação.

Alterar dados de uma ligação invalida os seus resultados anteriores. Uma alteração em lote invalida os resultados dos pilares efetivamente alterados. Alterar a organização dos grupos ou da seleção não altera a verificação física.

## 7. Corrigir a orientação

Use **Orientar ligação…** ou a opção de orientação do editor em lote. A rotação reconcilia os sentidos das excentricidades com os esforços transformados. Deixa de ser necessário voltar a adotar a fonte apenas porque o seletor de excentricidade ficou incoerente.

A operação continua a recusar esforços alterados manualmente, fontes incompatíveis ou registos que não correspondam aos dados de origem. Se um dos pilares da seleção impedir a rotação, a operação é cancelada sem aplicar alterações parciais aos outros pilares.

## 8. Exportar os resultados calculados

Use **Pilares… → Relatório do conjunto…**. Se existirem pilares selecionados, a opção **Apenas os pilares selecionados na lista** começa ativa. Pode também filtrar por piso e grupo.

A opção **Apenas resultados calculados e atualizados** começa ativa. Inclui verificações favoráveis e desfavoráveis e resultados resistentes com pormenorização ainda pendente. Exclui casos por calcular, dados inválidos, esforços pendentes e β por fundamentar. Um relatório parcial identifica, por ligação, quantas combinações foram calculadas e quantas foram omitidas.

Exemplo: uma ligação com 17 combinações calculadas e 16 pendentes apresenta **17/33 combinações calculadas** e conclusão **PARCIAL — PENDENTE**, mesmo que as 17 combinações calculadas verifiquem. Uma falha calculada é incluída e identificada.

A exportação utiliza os resultados atuais e não inicia o cálculo de novos pilares. Desative o filtro de calculados para obter um **mapa de acompanhamento**, incluindo casos pendentes e por calcular. PDF, TXT e JSON conservam o âmbito escolhido. O PDF pode detalhar apenas as combinações condicionantes ou todas as combinações exportadas.

O relatório identifica projeto, versão, referencial normativo, data de emissão, origem dos esforços e repositório. Conserva a tipografia e os espaçamentos dos relatórios anteriores.

## 9. Guardar

Use **Guardar conjunto…** para conservar ligações, fontes, grupos, predefinições, dados individuais e o registo das combinações executadas. O botão **Guardar** do ecrã principal mantém a função de guardar o caso individual.

As designações da interface, dos perfis de importação, dos relatórios e da documentação são neutras. O reconhecimento automático identifica a estrutura e as unidades da tabela; a convenção de sinais tem de corresponder ao perfil documentado, independentemente da aplicação que gerou os dados. Os nomes dos ficheiros e observações fornecidos pelo utilizador conservam-se para rastreabilidade.

Repositório: https://github.com/lutondatomalela/PunchingShearEC2
