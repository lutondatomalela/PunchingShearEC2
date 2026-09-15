# Conferência da interface — versão 1.15.0

Este guião documenta a revisão visual a realizar no ambiente de utilização. Os testes automatizados exercitam controladores com Tcl e widgets substituídos; não constituem uma conferência visual nativa.

Registe sistema operativo, versão de Python, resolução, escala, versão do programa e resultado de cada ensaio. Utilize cópias dos conjuntos e exemplos incluídos.

| Ensaio | Procedimento | Resultado esperado |
|---|---|---|
| Arranque | Abrir `main.py`, maximizar e reduzir a janela; testar as escalas de ecrã usadas no trabalho. | Entradas, botões e resultados acessíveis; texto legível e barras de deslocamento funcionais. |
| Caso didático | Abrir um exemplo e calcular com F5. | Resultados coerentes com a documentação do exemplo. |
| Dados alterados | Alterar uma entrada após calcular. | Estado de dados alterados e exportações desativadas até novo cálculo. |
| Gravação | Guardar um caso e um conjunto; fechar e reabrir. | Identificação, entradas, fontes e dados individuais conservados. |
| Importação | Utilizar as tabelas de `examples/importacao/`; conferir campos, unidades e origem. | Identificadores e valores conservados; pendências apresentadas sem adoção silenciosa de esforços. |
| Intervalos | Selecionar `110para113 115`, `110-113 115` ou números individuais, num modelo que contenha essas barras. | Seleção equivalente; identificadores ausentes recusados antes da alteração. |
| Prumada | Expandir uma seleção com coordenadas e nós comuns conhecidos. | Apenas a cadeia vertical admissível é selecionada; ambiguidades são comunicadas. |
| Eixos | Rever eixos e exceções numa ligação já preparada. | Esforços e origem atualizados; dados da laje, materiais e armaduras conservados. |
| Guardar configuração | Alterar eixos sem incluir novas ligações; guardar e fechar. | Conjunto gravado e regresso à lista; novo cálculo exigido onde aplicável. |
| Cancelamento | Cancelar os diálogos de gravação e alteração. | Dados anteriores conservados, sem aplicação parcial. |
| Grupos | Criar grupo e alterar apenas campos assinalados. | Restantes parâmetros e exceções individuais conservados. |
| Armadura automática | Definir base, reforço, espaçamento, espessura, recobrimento e camadas. | As, dx, dy e d coerentes; modo manual permanece disponível. |
| Orientação | Rodar uma ligação com armaduras diferentes em X/Y. | Geometria, esforços, armaduras e disposição das camadas rodados em conjunto. |
| Aberturas | Criar, mover e redimensionar uma abertura; testar Aplicar e Cancelar. | Aplicar exige novo cálculo; Cancelar conserva a geometria anterior. |
| Combinações | Consultar combinações e propostas diferentes de armadura. | Estado de pormenor comum por conferir mantido quando aplicável. |
| Relatórios | Exportar caso e conjunto com o filtro de calculados. | Âmbito, versão, entradas e estados coerentes; nenhum cálculo pendente apresentado como concluído. |

Não tente contornar uma mensagem de incompatibilidade geométrica alterando indiscriminadamente coordenadas ou tolerâncias. A correção deve ser fundamentada no modelo de origem e manter a rastreabilidade.

A campanha deve ser repetida após alterações de interface e nas plataformas que se pretendam suportar.
