# 🧱 PunchingShearEC2

Verificação do **punçoamento em lajes maciças de betão armado** segundo a **NP EN 1992-1-1:2010 (+A1:2019)**.  
Desenvolvido por **Eng.º Lutonda Tomalela** 🇵🇹 | 🇦🇴

---

## ⚙️ Descrição

**PunchingShearEC2** é um programa interativo e um módulo Python para  
verificação do **punçoamento** em lajes maciças apoiadas em pilares (interiores, de bordo e de canto).  

O programa segue o **Eurocódigo 2** e integra as principais verificações da secção 6.4, incluindo:
- cálculo automático dos perímetros críticos `u₀` e `u₁`;
- verificação ao **esmagamento da escora** (`v_Ed(u₀) ≤ v_Rd,max`);
- determinação da **resistência sem armadura** (`v_Rd,c`);
- **dimensionamento da armadura de punçoamento** (`Asw/sr`);
- consideração de **sapatas**, **aberturas**, **tensões de compressão**, e **modos de β**:
  - **β simplificado** (valores recomendados 1.15 / 1.40 / 1.50)
  - **β calculado** (Eqs. 6.44 e 6.45, com interpolação de _k_ do Quadro 6.1)

---

## 🧩 Funcionalidades principais

| Tema | Implementado | Detalhes |
|------|---------------|-----------|
| Pilares | ✅ | Interior, Bordo e Canto (retangulares e circulares) |
| β calculado | ✅ | Eqs. (6.44) e (6.45) com `k(c₁/c₂)` interpolado |
| Sapatas | ✅ | Redução automática de `V_Ed` pela pressão do solo |
| Aberturas | ✅ | Redução de `u₁` (u₁,ef) por perímetro ineficaz |
| Armadura | ✅ | Cálculo de `Asw/sr` e verificação de mínimos |
| Entrada intuitiva | ✅ | Dados em unidades práticas (kN, cm²/m, m, MPa) |
| Saída | ✅ | Relatório técnico formatado em texto e PDF (opcional) |

---

## 📦 Estrutura do Repositório
PunshingShearEC2/      
│
├── README.md
├── LICENSE
├── .gitignore
│
├── PunchingShear/
│ ├── __init__.py
│ ├── Punchsing_EC2.py
│ └── _utils.py
│
├── examples/
│ ├── _utils.py
│ ├── ex1_interior_rect_simplificado.py
│ ├── ex2_bordo_rect_calculado.py
│ ├── ex3_canto_rect_calculado.py
│ ├── ex4_interior_circular_calculado.py
│ ├── ex5_sapata_circular.py
│ ├── ex6_bordo_rect_abertura.py
│
└── Testes/
└── TestePuncoamentoEC2.py


---

## 🚀 Utilização

### 1️⃣ Executar como programa interativo
```bash
python PunshingShear/PunchingEC2.py
```

## 🪪 Licença

Este projeto é distribuído sob a Licença MIT.
Consulta o ficheiro LICENSE para mais detalhes.

## 🧠 Créditos

Desenvolvido no contexto de estudos e prática profissional em Engenharia Estrutural.
Ferramenta de apoio ao dimensionamento conforme o Eurocódigo 2, para utilização técnica, educativa e académica.

