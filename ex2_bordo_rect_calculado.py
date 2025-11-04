# -*- coding: utf-8 -*-
"""
Created Sun May  4 00:54:30 2025

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
    print(header("Ex.2 – Pilar de BORDO retangular | β calculado (Eq. 6.44)"))


    # β É calculado conforme Eq. (6.44) e (6.45) do EC2
    # k é interpolado do Quadro 6.1 em função de c1/c2
    # os momentos aplicados M_Edx / M_Edy criam excentricidades (excentricidade dupla)

    v = PuncoamentoEC2(
        laje_d=0.220,
        betão_fck=35, aço_fyk=500, aço_fywk=500,
        pilar_tipo='bordo', pilar_forma='retangular',
        V_Ed=650_000,                   # em N
        pilar_c1=0.40, pilar_c2=0.30,   # c1/c2 = 1.33 → k ≈ 0.633
        M_Edx=30_000, M_Edy=60_000,     # em Nm 
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.0,
        beta_mode='calculado',
        laje_As_lx_cm2pm=9.50, # em cm2/m
        laje_As_ly_cm2pm=9.50 # em c2/m
    )

    print(v.verificar_puncoamento())

