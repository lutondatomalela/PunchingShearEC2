# -*- coding: utf-8 -*-
"""
Created on Sun May  11 01:03:15 2025

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
    print(header("Ex.6 – Pilar de BORDO retangular | abertura próxima (u1_ineffective)"))

    # u1_ineffective .... comprimento (m) do perímetro ineficaz devido a aberturas
    # O valor pode ser obtido pela Fig. 6.14 da NP EN 1992-1-1.

    v = PuncoamentoEC2(
        laje_d=0.220,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='bordo', pilar_forma='retangular',
        V_Ed=600_000,
        pilar_c1=0.40, pilar_c2=0.35,
        M_Edx=15_000, M_Edy=45_000,   # Nm
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.40,          # m
        beta_mode='calculado',
        laje_As_lx_cm2pm=8.80,
        laje_As_ly_cm2pm=8.80
    )

    print(v.verificar_puncoamento())
