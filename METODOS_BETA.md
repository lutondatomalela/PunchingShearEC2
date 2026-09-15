# Métodos de beta - PunchingShearEC2 1.9.0

Referencial: NP EN 1992-1-1:2010, 6.4.3, páginas 114-118; AC:2012 e A1:2019 fornecidos. As opções e o método realmente utilizado são guardados no JSON e nos relatórios.

## Convenção de entrada

As coordenadas são centradas no pilar: X paralelo a c1 e Y a c2. ex = MEdy/VEd e ey = MEdx/VEd. No bordo, X é paralelo ao bordo livre, o interior da laje é +Y e o seletor normal determina o sentido de ey. No canto interior, usam-se os módulos; no canto exterior usam-se os sinais dos momentos.

MEdx e MEdy são os momentos concomitantes no centro do pilar. Não introduzir momentos já transportados para o centro do perímetro de controlo. As linhas de excentricidade da memória mostram os valores depois de aplicar os sentidos declarados.

## (6.39)-(6.41): expressão geral por direção

Para uma componente: beta = 1 + k |MG|/VEd * u1/W.

W = integral |distância ao eixo do momento| dl, sobre o contorno efetivo. O motor integra retas e arcos analiticamente. No pilar interior retangular, o valor coincide com a expressão fechada (6.41).

No tratamento exterior de bordo/canto, calcula-se G do perímetro por integral(x dl)/u1 e integral(y dl)/u1. Os momentos são transportados uma única vez para G, na convenção de eixos da interface:

- Mx,G = Mx,orientado - VEd*yG;
- My,G = My,orientado - VEd*xG.

A razão para k é a dimensão do pilar paralela à excentricidade dividida pela perpendicular. Para ex, usa-se c1/c2; para ey, c2/c1. O Quadro 6.1 fornece k = 0,45; 0,60; 0,70; 0,80 para razões 0,5; 1; 2; 3, com interpolação linear e valores extremos constantes.

O bordo exterior uniaxial pode ser calculado diretamente. Com duas componentes, a opção adicional selecionada pelo projetista calcula beta = 1 + delta_beta_x + delta_beta_y. As parcelas são os módulos das majorações de (6.39), com os k próprios. É uma combinação conservadora por direção adotada pelo programa, não uma expressão biaxial literal do EC2. O canto exterior exige selecionar esta combinação. Esta opção não se estende a afastamentos positivos ou aberturas.

## (6.43): interior retangular

A expressão aproximada é aplicada com a correspondência y,z da NP -> X,Y da interface:

beta = 1 + 1,8 sqrt[(ex/by)^2 + (ey/bx)^2]

bx = c1 + 4d; by = c2 + 4d.

Os denominadores seguem a expressão e a nota de eixos da página 116 da NP. A memória mostra a correspondência e os dois termos. Incluem-se os limites uniaxiais e concêntrico; não há mudança de fórmula por arredondamento de uma componente para zero. Para utilizar a expressão geral uniaxial (6.39), selecione ec2_639.

## (6.42): interior circular

beta = 1 + 0,6 pi e/(D + 4d), com e = sqrt(ex² + ey²). Sem aberturas.

## (6.44)-(6.45): bordo com excentricidade normal interior

Pilar encostado e sem aberturas. Na interface, c1 é paralelo e c2 perpendicular ao bordo, pelo que os símbolos c1 e c2 da Figura 6.20(a) ficam trocados relativamente à interface.

- u1* = c1 + 2 min(c2/2; 1,5d) + 2 pi d;
- Wy = c1²/4 + c2*c1 + 4*c2*d + 8*d² + pi*d*c1;
- razão de k = c2/(2*c1);
- beta = u1/u1* + k |ex| u1/Wy.

Sem excentricidade paralela, o segundo termo é nulo. O limite de momento normal nulo é tratado no mesmo ramo quando a opção interior está selecionada. O modelo não é transposto automaticamente para g > 0.

## (6.46): canto com excentricidades interiores

Pilar encostado aos dois bordos, sem aberturas:

u1* = min(c1/2; 1,5d) + min(c2/2; 1,5d) + pi d;
beta = u1/u1*.

## Valores simplificados, fator manual e contornos exteriores

O método simplificado de 6.4.3(6) usa 1,15 / 1,40 / 1,50 para interior / bordo / canto, exclusivamente com as condições de estabilidade e vãos declaradas. Os momentos não são novamente acrescentados a esses fatores.

O modo manual requer beta finito ≥ 1 e referência da análise que o fundamenta. O programa não valida o conteúdo técnico dessa referência. Mantém-se para geometrias não abrangidas pelos procedimentos automáticos e outras avaliações específicas.

Na face é usado o beta de u1. No contorno exterior, conserva-se pelo menos o beta de u1, e o motor pode aumentar o fator se a avaliação desse contorno o exigir. Essa majoração adicional é uma opção conservadora do programa. Não significa que (6.43), (6.44) ou outra expressão tenham sido publicadas como fórmulas novas para um contorno arbitrário.

## Limites da automatização

Afastamentos positivos, aberturas, dois bordos com afastamento, capitéis, apoios de parede e secções fora do âmbito definido não são automaticamente resolvidos por esta revisão. A integração geométrica de um perímetro não estabelece, por si só, o modelo adequado de transferência de momentos. A pendência identifica essa limitação, sem concluir aprovação nem insuficiência resistente.

A versão 1.8.0 acrescenta a definição física de aberturas. Apenas as que geram setores ativos por 6.4.2(3), juntamente com setores manuais, desencadeiam a pendência de beta. A conversão geométrica não altera os métodos resistentes. Consulte ABERTURAS_GUI.md.
