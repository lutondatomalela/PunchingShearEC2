# -*- coding: utf-8 -*-
"""
Created on Sun May 4 00:04:57 2025

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
    print(header("Ex.1 – Pilar INTERIOR retangular | β simplificado"))

    # ------------------------------------------------------------
    # DADOS PARA INPUT
    # ------------------------------------------------------------
    # laje_d ............. altura útil da laje (m)
    # betão_fck .......... resistência característica à compressão do betão (MPa)
    # aço_fyk, aço_fywk .. resistência característica à tração do aço (MPa)
    # pilar_tipo ......... "interior", "bordo" ou "canto"
    # pilar_forma ........ "retangular" ou "circular"
    # V_Ed ............... esforço transverso de cálculo (N)
    # pilar_c1, c2 ....... dimensões do pilar (m)
    # M_Edx, M_Edy ....... momentos atuantes de cálculo (N·m)
    # sigma_cp ........... tensão média de compressão (MPa)
    # laje_As_lx_cm2pm ... armadura de flexão na direção x (cm²/m)
    # laje_As_ly_cm2pm ... armadura de flexão na direção y (cm²/m)
    # beta_mode .......... "simplificado" ou "calculado"
    # ------------------------------------------------------------

    v = PuncoamentoEC2(
        laje_d=0.220,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='interior', pilar_forma='retangular',
        V_Ed=600_000,              # 600 kN
        pilar_c1=0.40, pilar_c2=0.40,
        M_Edx=0.0, M_Edy=0.0,
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.0,
        beta_mode='simplificado',
        laje_As_lx_cm2pm=8.80,
        laje_As_ly_cm2pm=8.80
    )

    print(v.verificar_puncoamento())


