# -*- coding: utf-8 -*-
"""
Created on Sun May  4 00:56:53 2025

@author: Engº Lutonda Tomalela
"""

import sys, os
EX_DIR = os.path.dirname(__file__)
ROOT = os.path.dirname(EX_DIR)
sys.path.append(EX_DIR)
sys.path.append(ROOT)

from Punching_EC2 import PuncoamentoEC2
from _utils import header

if __name__ == "__main__":
    print(header("Ex.3 – Pilar de CANTO retangular | β calculado (aprox.)"))

    # Este exemplo ilustra o cálculo de β com excentricidades nos dois eixos.
    # O programa aplica a aproximação equivalente da Eq. (6.44) + (6.45).

    v = PuncoamentoEC2(
        laje_d=0.230,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='canto', pilar_forma='retangular',
        V_Ed=520_000,                 # 520 kN
        pilar_c1=0.35, pilar_c2=0.45,
        M_Edx=25_000, M_Edy=25_000,   # Nm (25 kN·m)
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.0,
        beta_mode='calculado',
        laje_As_lx_cm2pm=8.50,
        laje_As_ly_cm2pm=8.50
    )

    print(v.verificar_puncoamento())
