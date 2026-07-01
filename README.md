# PunchingShearEC2

**PunchingShearEC2** é uma ferramenta em Python para verificação do punçoamento em lajes maciças de betão armado, de acordo com o **Eurocódigo 2 — NP EN 1992-1-1:2010 + A1:2019**, com interface gráfica, exportação de relatórios e apoio ao dimensionamento preliminar de armaduras de punçoamento.

O programa permite verificar casos correntes de pilares interiores, pilares de bordo, pilares de canto e pilares circulares, com cálculo dos principais parâmetros resistentes e atuantes.

---

## Funcionalidades principais

- Verificação ao punçoamento segundo o EC2;
- Interface gráfica em `tkinter`;
- Entrada organizada de dados geométricos, materiais e esforços;
- Representação gráfica simplificada dos perímetros `u0`, `u1` e `u1*`;
- Cálculo do coeficiente `β`;
- Verificação de:
  - tensão de cálculo no perímetro crítico;
  - resistência do betão sem armadura de punçoamento;
  - resistência máxima junto ao pilar;
  - necessidade de armadura de punçoamento;
- Recomendação preliminar de pormenorização;
- Exportação de relatório técnico em PDF;
- Exportação de resultados para Excel;
- Exportação simples em TXT.

---

## Estrutura do projeto

```text
PunchingShearEC2/
│
├── Punching_EC2.py        # Motor de cálculo
├── Punching_EC2_GUI.py    # Interface gráfica
├── TestePuncoamentoEC2.py # Ficheiro de testes/exemplos
├── _utils.py              # Funções auxiliares
├── __init__.py
├── README.md
└── requirements.txt
```

---

## Instalação

Clone o repositório:

```bash
git clone https://github.com/lutondatomalela/PunchingShearEC2.git
cd PunchingShearEC2
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Ou, em alternativa:

```bash
python -m pip install -r requirements.txt
```

---

## Dependências

O programa usa principalmente bibliotecas padrão do Python.

Para exportação de relatórios em PDF e Excel, são usadas:

```text
reportlab
openpyxl
```

Instalação manual:

```bash
pip install reportlab openpyxl
```

---

## Como executar

Para abrir a interface gráfica:

```bash
python Punching_EC2_GUI.py
```

O motor de cálculo encontra-se em:

```text
Punching_EC2.py
```

Este ficheiro contém a classe principal de cálculo e pode ser usado diretamente em scripts próprios.

---

## Casos disponíveis na interface

A interface inclui exemplos e modos de cálculo para:

- Pilar interior retangular;
- Pilar de bordo;
- Pilar de canto;
- Pilar circular.

A designação interior, bordo ou canto refere-se à **posição do pilar na laje**, e não ao tipo de laje.

---

## Enquadramento normativo

A verificação segue a lógica da **NP EN 1992-1-1:2010 + A1:2019**, em particular as disposições relativas ao punçoamento em lajes.

O programa considera, entre outros aspetos:

- perímetro junto ao pilar `u0`;
- perímetro crítico `u1`;
- perímetro reduzido `u1*`, quando aplicável;
- tensão de cálculo `v_Ed`;
- resistência ao punçoamento sem armadura `v_Rd,c`;
- resistência máxima `v_Rd,max`;
- coeficiente de majoração `β`;
- recomendações preliminares para armadura de punçoamento.

Para pilares de bordo e de canto, foram consideradas as formulações específicas do EC2, incluindo a distinção entre excentricidades dirigidas para o interior ou para o exterior da laje.

---

## Exportação de relatórios

A interface permite exportar:

### Relatório PDF

Relatório técnico formatado com:
- dados de entrada;
- parâmetros de cálculo;
- resultados principais;
- referências normativas;
- conclusão;
- recomendação de pormenorização;
- nota técnica final.

### Excel

Ficheiro `.xlsx` com:
- resumo;
- dados de entrada;
- resultados detalhados;
- memória simplificada.

### TXT

Relatório simples em texto, equivalente ao resumo apresentado na interface.

---

## Utilização típica

1. Abrir a interface gráfica;
2. Selecionar o tipo de pilar;
3. Introduzir geometria, materiais e esforços;
4. Escolher o modo de cálculo de `β`;
5. Executar a verificação;
6. Rever os resultados na interface;
7. Exportar PDF ou Excel, se necessário.

---

## Notas importantes

- A ferramenta destina-se a apoio ao cálculo e à verificação técnica.
- A interpretação final das disposições do Eurocódigo 2 cabe ao projetista.
- Em casos fora do domínio corrente, recomenda-se validação independente ou modelo complementar.

---

## Desenvolvimento futuro

Melhorias previstas:

- módulo para lajes apoiadas em paredes;
- verificação de apoios lineares por esforço transverso unidirecional;
- tratamento de paredes curtas como áreas carregadas alongadas;
- exportação PDF com desenhos técnicos mais detalhados;
- organização modular do projeto;
- criação de executável para Windows.

---

## Autor

Desenvolvido por **Lutonda Tomalela, Engº**.

Repositório:

```text
https://github.com/lutondatomalela/PunchingShearEC2
```

---

## Licença

Este projeto é distribuído sob a licença MIT.
