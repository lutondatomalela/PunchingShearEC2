# PunchingShearEC2

Verificação do punçoamento em lajes de betão armado segundo a **NP EN 1992-1-1:2010, AC:2012 e A1:2019**, com o Anexo Nacional português.

Aplicação em Python com interface gráfica, preparação de ligações laje–pilar, gestão de conjuntos e relatórios de cálculo rastreáveis. O referencial implementado é o da primeira geração do Eurocódigo 2.

## Versão de referência

A **1.15.0** é a base congelada para o desenvolvimento seguinte. Esta publicação mantém, byte a byte, o código da distribuição 1.15.0. As alterações de publicação abrangem documentação, organização dos registos públicos e integração contínua.

Consulte [BASELINE.md](BASELINE.md) para a identificação da distribuição original e as regras de evolução. O congelamento não constitui certificação nem elimina as limitações documentadas.

## Funcionalidades

- Pilares interiores, de bordo e de canto, dentro do âmbito geométrico implementado.
- Verificações junto ao pilar, no perímetro de controlo e nos contornos exteriores.
- Métodos de cálculo de β com condições de aplicabilidade explícitas.
- Proposta e conferência de armadura de punçoamento por fiadas e coordenadas dos ramos.
- Armadura longitudinal manual ou por base e reforço, com cálculo automático de As,x, As,y, dx, dy e d.
- Importação de tabelas XLSX, CSV e TSV, com conservação da origem dos dados.
- Preparação das ligações por piso; revisão dos eixos e orientação conjunta de geometria e esforços.
- Seleção de barras por listas e intervalos, com extensão à prumada quando a conectividade e as coordenadas o permitem.
- Grupos de ligações, parâmetros comuns, exceções individuais e cálculo em lote.
- Gravação de casos e conjuntos em JSON.
- Relatórios individuais PDF, XLSX, TXT e JSON; relatórios de conjunto PDF, TXT e JSON, filtrados por resultados calculados e atualizados.
- Editor gráfico de aberturas e exemplos didáticos incluídos.

## Instalação

Requer **Python 3.10 ou superior**, Tkinter e as bibliotecas de `requirements.txt`. A distribuição contém código-fonte; não é um executável autónomo.

Obtenha o código:

```sh
git clone https://github.com/lutondatomalela/PunchingShearEC2.git
cd PunchingShearEC2
```

### Windows

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

### Linux e macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

A instalação de Python deve incluir Tkinter; em Linux pode ser necessário instalar o pacote correspondente. A verificação visual nativa em cada plataforma e escala de ecrã deve seguir [GUI_TESTES.md](GUI_TESTES.md).

Também pode descarregar o código na secção [Releases](https://github.com/lutondatomalela/PunchingShearEC2/releases). Extraia a pasta completa, incluindo `punching/` e `examples/`.

## Utilização

1. Abra um exemplo ou crie um caso. Para vários apoios, use **Pilares…** e importe as tabelas.
2. Confira unidades, eixos, sinais, extremos e combinações; prepare as ligações por piso.
3. Defina a geometria da laje, materiais, bordos, aberturas e armaduras de cada ligação.
4. Escolha um método de β aplicável e execute **Calcular / F5**.
5. Consulte **Verificações**, **Fiadas**, **Memória** e as combinações condicionantes.
6. Guarde o conjunto e exporte os resultados. Alterações de dados exigem novo cálculo.

O esforço axial acumulado num pilar não é, por si só, a carga transmitida pela laje. A preparação a partir dos tramos exige esforços ELU originais concomitantes e as condições de equilíbrio documentadas. CQC/SRSS e envolventes não são tratados como esforços concomitantes por simples soma ou diferença.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Referência técnica](REFERENCIA_TECNICA.md) | Formulações, unidades, hipóteses, estados e exportações |
| [Métodos de β](METODOS_BETA.md) | Expressões e domínio de aplicação |
| [Importação](IMPORTACAO.md) | Tabelas genéricas, campos e unidades |
| [Modelo e ligações](MODELO_IMPORTACAO.md) | Origem dos esforços e conferência da ligação |
| [Preparação por piso](MODELO_POR_PISO.md) | Eixos, intervalos, prumadas e gravação |
| [Armadura longitudinal](ARMADURA_LONGITUDINAL.md) | Base, reforço, camadas e alturas úteis |
| [Grupos e relatórios](GRUPOS_E_RELATORIOS.md) | Predefinições, edição em lote e âmbito exportado |
| [Aberturas](ABERTURAS_GUI.md) | Definição gráfica e limites geométricos |
| [Exemplos](examples/README.md) | Casos didáticos e resultados esperados |
| [Validação](VALIDACAO.md) | Ensaios automatizados e limites da evidência |
| [Histórico](CHANGELOG.md) | Evolução das versões |

## Âmbito e limitações

O programa é uma ferramenta de apoio ao projeto. A interpretação normativa, a conferência dos dados e a validação do pormenor construtivo permanecem da responsabilidade do projetista.

Entre os casos fora do âmbito estão apoios de parede, capitéis, espessura variável, pilares circulares de bordo/canto e apoios retangulares com razão entre dimensões ≥ 4. Flexão, esforço transverso unidirecional, ELS e integridade global exigem verificações próprias.

Limitações operacionais mantidas na 1.15.0:

- A substituição de uma tabela de nós já importada exige um novo conjunto.
- Propostas de armadura diferentes entre combinações exigem conferência de um pormenor comum; não são automaticamente uma única solução executável.
- A extensão à prumada exige barras verticais, coordenadas compatíveis e nós de extremidade comuns.
- As combinações já preparadas não são removidas silenciosamente.
- Os testes automatizados não substituem a inspeção visual da interface nem a verificação independente de um projeto.

## Testes

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tools/verify_baseline.py
```

A campanha local da publicação reúne **533 testes aprovados** em Python 3.12.14. A integração contínua executa a suite e a conferência da base; os resultados efetivos estão disponíveis em [Actions](https://github.com/lutondatomalela/PunchingShearEC2/actions).

## Estrutura

- `main.py` — arranque da aplicação.
- `punching/` — cálculo, geometria, importação, interface e relatórios.
- `examples/` — casos didáticos e tabelas de demonstração.
- `tests/` — testes automatizados.
- `validation/` — identificação da base e registos públicos de validação.
- `tools/` — conferência de integridade da versão.
- `docs/releases/` — notas de publicação.

Os antigos pontos de entrada `Punching_EC2.py` e `Punching_EC2_GUI.py` são conservados para compatibilidade.

## Contribuições e licença

As próximas alterações devem partir desta base, usar uma nova versão e incluir testes e registo no histórico. Ver [CONTRIBUTING.md](CONTRIBUTING.md).

Distribuído sob a [licença MIT](LICENSE). Repositório: [lutondatomalela/PunchingShearEC2](https://github.com/lutondatomalela/PunchingShearEC2).
