# -*- coding: utf-8 -*-
"""
Created on Sun May  4 01:00:55 2025

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
    print(header("Ex.5 – Sapata com pilar circular | alívio por σ_gd no solo"))

    # σ_gd_kpa ........ tensão de cálculo no solo (kPa)
    # o programa reduz automaticamente V_Ed com base na área sob o perímetro u1

    v = PuncoamentoEC2(
        laje_d=0.300,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='interior', pilar_forma='circular',
        V_Ed=900_000,               # em N
        pilar_c1=0.50,               # D em metros
        M_Edx=0.0, M_Edy=0.0,
        sigma_cp=0.0,
        is_sapata=True, sigma_gd_kpa=150.0,  # kPa
        u1_ineffective=0.0,
        beta_mode='simplificado',
        laje_As_lx_cm2pm=10.50, # cm2/m
        laje_As_ly_cm2pm=10.50 # cm2/m
    )

    print(v.verificar_puncoamento())

