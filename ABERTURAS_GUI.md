# Definição gráfica de aberturas - versão 1.9.0

Abra **Método β → Aberturas e setores ineficazes → Definir aberturas na planta…**, ou use **Aberturas…** no separador **Planta**.

1. Adicione um **Retângulo** ou um **Círculo**. Em alternativa, escolha **Desenhar retângulo**, clique num canto e arraste até ao canto oposto.
2. Selecione a abertura na lista ou na planta. Introduza a identificação, as coordenadas do centro e as dimensões, em metros, e clique em **Aplicar medidas**.
3. Para definir a abertura pela distância livre, escolha uma face **+X, -X, +Y ou -Y**, indique a distância e clique em **Posicionar na face escolhida**. A abertura fica centrada relativamente a essa face. Pode depois ajustar X e Y.
4. Arraste o interior da abertura para a mover. Arraste o quadrado azul para redimensionar em torno do centro. O arrastamento ajusta as medidas a 1 cm; as entradas numéricas permitem maior precisão.
5. Consulte a distância mínima à face, o limite **6d**, a construção geométrica e os setores automáticos. Clique em **Aplicar ao caso** e volte a calcular. **Cancelar** conserva o caso anterior. Escape cancela um desenho em curso ou fecha o editor.

Os valores de X e Y referem-se ao **centro do pilar**: X paralelo a c1; Y paralelo a c2. Em pilares de bordo, c1 é paralelo ao bordo e o interior da laje é +Y. Rodar a planta de origem exige transformar também as coordenadas. As aberturas retangulares desta versão são alinhadas com X/Y; não existe rotação individual nem editor de polígonos.

## Exemplo de abertura quadrada

Pilar 0,40 × 0,40 m; d = 0,20 m. Adicione um retângulo de 0,40 × 0,40 m, escolha a face +X e introduza 0,60 m de distância livre. O centro fica em X = 1,00 m e Y = 0. A distância mínima é 0,60 m e os ângulos são aproximadamente -14,036243° e +14,036243°. O motor conserva os valores sem arredondamento de apresentação. O exemplo 25 já contém estes dados.

## Construção dos setores

- A distância é medida entre as fronteiras físicas do pilar e da abertura, incluindo a distância diagonal quando aplicável. Não é a distância entre centros.
- Para distância ≤ 6d, os setores são calculados e unidos aos setores manuais adicionais. Uma abertura exatamente a 6d é considerada. Sobreposições angulares contam uma vez.
- Para círculos, as tangentes são analíticas. Para retângulos, os ângulos extremos dos vértices definem as tangentes antes do ajuste de alongamento.
- No caso radial alongado l1 > l2, usa-se a largura equivalente sqrt(l1·l2) da Figura 6.14. Para retângulos cuja posição seja oblíqua à direção radial, calcula-se primeiro uma envolvente retangular radial. Essa envolvente é uma hipótese geométrica conservadora adicional, identificada na GUI e na memória; não é apresentada como uma construção oblíqua literal publicada na norma.
- Se essa envolvente alcançar o centro do pilar, a conversão automática é rejeitada. Utilize uma definição por setores fundamentada para essa geometria.
- Aberturas a mais de 6d ficam desenhadas e registadas, sem dedução do perímetro por 6.4.2(3). A regra não dispensa as restantes verificações da laje. Se existirem ramos propostos junto da abertura, o seu recobrimento é verificado independentemente do limite 6d.

O tracejado junto de uma abertura alongada mostra a envolvente utilizada. O contorno vermelho corresponde ao perímetro efetivo; o contorno de referência sem aberturas é mostrado a tracejado no editor.

## Compatibilidade e limites

O campo **Setores manuais adicionais** mantém a sintaxe `início;fim | início;fim`. Não copie para esse campo os ângulos que o editor calculou. Os casos antigos que só contêm setores continuam a funcionar; não é possível recuperar uma forma, tamanho e distância únicos apenas a partir desses ângulos.

As posições e dimensões são guardadas em `openings`. Os ângulos automáticos são recalculados ao alterar d, o pilar ou as aberturas. Os setores manuais permanecem em `opening_sectors`. JSON de resultados, memória e XLSX identificam as entradas e o resultado dessa conversão. A folha **Aberturas** contém distância, limite 6d, ângulos, largura equivalente e método.

Uma abertura não pode tocar ou intersectar o pilar, tocar ou ultrapassar um bordo livre, nem sobrepor-se ou ser contígua a outra abertura. Reentrâncias, aberturas compostas, polígonos ou retângulos rodados requerem definição específica. O módulo de sapatas mantém o âmbito sem aberturas.

**O editor define a geometria; não fundamenta beta.** Com setores ineficazes ativos, o modo EC2 mantém BETA_PENDING; o método simplificado continua indisponível. Uma verificação resistente exige beta manual fundamentado para a geometria e os contornos relevantes. A existência de uma referência escrita não valida o conteúdo dessa análise.

O recobrimento dos ramos às aberturas é conferido com as coordenadas propostas. Uma falha impede a conclusão PASS_WITH, mesmo quando a amarração foi confirmada. O editor não dimensiona os reforços de flexão à volta das aberturas nem os respetivos remates.
