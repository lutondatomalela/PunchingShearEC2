# -*- coding: utf-8 -*-
"""
Created on Sun May  11 00:59:26 2025

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
    print(header("Ex.4 – Pilar INTERIOR circular | β calculado (equiv. retangular)"))

    # Circular tratado como equivalente retangular (c1=c2=D)
    # Permite cálculo de β com as mesmas equações do pilar retangular.

    v = PuncoamentoEC2(
        laje_d=0.220,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='interior', pilar_forma='circular',
        V_Ed=600_000,
        pilar_c1=0.35,               # D (diâmetro em metros)
        M_Edx=40_000, M_Edy=20_000,  # Nm
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.0,
        beta_mode='calculado',
        laje_As_lx_cm2pm=9.00,
        laje_As_ly_cm2pm=9.00
    )

    print(v.verificar_puncoamento())
