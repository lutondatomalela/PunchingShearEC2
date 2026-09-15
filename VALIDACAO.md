# Validação — PunchingShearEC2

## Release candidate 1.15.1-rc.1

A RC usa leituras UTF-8 explícitas nos testes e acrescenta um teste de regressão da linha de comandos com saída CP1252 estrita: os resultados JSON/TXT mantêm UTF-8 e um símbolo não representável no terminal não interrompe o cálculo.

A publicação exige aprovação de 534 testes em Linux/Python 3.10 e 3.12 e Windows/Python 3.12. Depois, o executável é compilado e ensaiado em Windows: catálogo incluído, arranque real de Tk, cálculo pela interface, gravação/reabertura de caso e conjunto, importação XLSX/CSV UTF-16 e exportação PDF/XLSX/TXT/JSON. O ensaio corre fora da pasta do código, num caminho com acentos.

A evidência efetiva de cada compilação está em Actions e no BUILD-INFO.json anexado à release. A configuração destes requisitos não equivale, por si só, à sua aprovação. Não foi realizada uma campanha visual completa em diferentes postos ou escalas de ecrã.

## Evidência histórica da base 1.15.0

A distribuição 1.15.0 reúne **533 testes automatizados**, incluindo 37 testes acrescentados para seleção de barras, extensão à prumada e revisão do modelo. A suite foi novamente executada na preparação deste repositório. O resultado da execução está em [validation/pytest_result.txt](validation/pytest_result.txt).

O commit da base 1.15.0 preserva todos os ficheiros Python da distribuição original, incluindo os testes. A conferência SHA-256 está descrita em [BASELINE.md](BASELINE.md). A organização da documentação e os ficheiros de integração contínua não alteram o motor de cálculo.

## Cobertura

- Referências numéricas independentes para geometrias, métodos de β e verificações resistentes implementadas.
- Aberturas, contornos e distribuição das armaduras.
- Armadura longitudinal por base e reforço e cálculo das alturas úteis.
- Leitura de tabelas, unidades, sinais, origem e conservação dos dados.
- Seleção por listas e intervalos; rejeição de identificadores ausentes.
- Extensão a barras conectadas e alinhadas, com deteção de situações não admissíveis.
- Gravação e reabertura, conservação de dados individuais e invalidação de cálculos afetados.
- Revisão simultânea de eixos e combinações; cancelamento e falha de escrita.
- Controladores da interface com variáveis Tcl e widgets substituídos.
- Exportações, âmbito dos resultados e estados de pendência.

O registo de âmbito original encontra-se em [validation/release_1_15_0.json](validation/release_1_15_0.json). Os testes não demonstram, por si só, a correção de entradas de projeto nem a aplicabilidade de todas as hipóteses a uma obra.

## Ambiente e reprodução

A campanha local usa Python 3.12.14, pytest 9.1.1, reportlab 4.4.9 e openpyxl 3.1.5. As dependências ensaiadas estão fixadas em `requirements.txt` e `requirements-dev.txt`.

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tools/verify_baseline.py
```

A integração contínua acrescenta execuções em Linux/Python 3.10 e 3.12 e Windows/Python 3.12. A existência da configuração não equivale à aprovação dessas execuções; consulte os resultados de cada commit em [Actions](https://github.com/lutondatomalela/PunchingShearEC2/actions).

## Limites

A revisão visual nativa das janelas, diferentes escalas de ecrã e utilização em cada plataforma continua a exigir a campanha de [GUI_TESTES.md](GUI_TESTES.md). Os testes de controladores não substituem essa revisão.

A tabela de nós já importada não pode ser substituída no mesmo conjunto nesta versão. A proposta de um pormenor comum a todas as combinações não é gerada e verificada automaticamente. Estas limitações são conservadas na base congelada.

Os exemplos públicos são didáticos. Ficheiros de projetos, coordenadas reais, resultados de obras e registos de validação associados a fontes privadas não integram esta publicação.
