# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 01:56:35 2025

@author: Engº Lutonda Tomalela
"""

import math
import re
import pytest

from Punching_EC2 import PuncoamentoEC2


# ----------------------------
# helpers
# ----------------------------
def base_kwargs(**over):
    """Argumentos base para criar cenários rapidamente."""
    kw = dict(
        laje_d=0.220,
        betão_fck=30, aço_fyk=500, aço_fywk=500,
        pilar_tipo='interior', pilar_forma='retangular',
        V_Ed=600_000,                  # em [N] 
        pilar_c1=0.40, pilar_c2=0.40,
        M_Edx=0.0, M_Edy=0.0, # em [Nm] 
        sigma_cp=0.0,
        is_sapata=False, sigma_gd_kpa=0.0,
        u1_ineffective=0.0,
        beta_mode='simplificado',
        laje_As_lx_cm2pm=8.80, laje_As_ly_cm2pm=8.80  # ~0.40% para d=0.22
    )
    kw.update(over)
    return kw


def run_and_get(obj: PuncoamentoEC2):
    """Executa e devolve também o texto do relatório."""
    rep = obj.verificar_puncoamento()
    return obj, rep


# ---------     -------------------
# testes
# --------------------------   --

def test_rho_from_As_is_computed():
    # para d=0.20 e As=8 cm²/m -> ρ = 8/10000 / (1*0.20) = 0.004 (0.400%)
    v = PuncoamentoEC2(**base_kwargs(laje_d=0.200, laje_As_lx_cm2pm=8.0, laje_As_ly_cm2pm=8.0))
    assert pytest.approx(v.rho_l, rel=0, abs=1e-9) == 0.004


@pytest.mark.parametrize("tipo,expected", [
    ("interior", 1.15),
    ("bordo",    1.40),
    ("canto",    1.50),
])
def test_beta_simplificado_valores(tipo, expected):
    # forçar caminho "com momentos" (senão β=1.0)
    v = PuncoamentoEC2(**base_kwargs(pilar_tipo=tipo, M_Edx=10.0, M_Edy=0.0, beta_mode='simplificado'))
    _, rep = run_and_get(v)
    assert math.isclose(v.beta, expected, rel_tol=0, abs_tol=1e-12)
    assert ("simplificado" in rep.lower())  # relatório identifica o modo


def test_beta_calculado_interp_k_por_ratio():
    # retangular bordo com c1/c2 = 1.5 -> k ~ 0.65 (interp. linear do Quadro 6.1 (EC2))
    v = PuncoamentoEC2(**base_kwargs(
        pilar_tipo='bordo', pilar_forma='retangular',
        pilar_c1=0.45, pilar_c2=0.30,    # ratio = 1.5
        M_Edx=0.0, M_Edy=30_000.0,       # forçar excentricidade paralela ao bordo; momentos fletores em [Nm]
        beta_mode='calculado'
    ))
    _, rep = run_and_get(v)
    # k calculado deve aparecer no relatório
    assert v.k_beta is not None
    assert pytest.approx(v.k_beta, rel=0, abs=1e-3) == 0.65
    assert "calculado" in rep.lower()


def test_abertura_reduz_u1_efetivo():
    # interior retangular; u1_ineffective reduz u1,ef
    v = PuncoamentoEC2(**base_kwargs(u1_ineffective=0.30))
    v._get_perimetros_criticos()
    v._get_V_Ed_red_e_u1_efetivo()
    assert v.u1_eff == pytest.approx(v.u1 - 0.30, rel=0, abs=1e-12)


def test_sapata_reduz_VEd():
    # circular interior, com pressão no solo -> VEd_red < VEd
    v = PuncoamentoEC2(**base_kwargs(
        pilar_forma='circular', pilar_c1=0.50, pilar_c2=None,
        is_sapata=True, sigma_gd_kpa=150.0
    ))
    v._get_perimetros_criticos()
    v._get_V_Ed_red_e_u1_efetivo()
    assert v.V_Ed_red < v.V_Ed


def test_esmagamento_na_face_detecta_falha_e_apos_ajuste_passa():
    # esmagamento com d muito pequeno
    v_fail = PuncoamentoEC2(**base_kwargs(laje_d=0.10, pilar_tipo='interior'))
    _, rep_fail = run_and_get(v_fail)
    assert "esmagamento" in rep_fail.lower()
    assert "falha" in rep_fail.lower()

    # aumenta o d 
    v_ok = PuncoamentoEC2(**base_kwargs(laje_d=0.30, pilar_tipo='interior'))
    _, rep_ok = run_and_get(v_ok)
    assert "ok" in rep_ok.lower()
    assert "esmagamento" in rep_ok.lower()


def test_armadura_necessaria_vs_nao_necessaria():
    # caso com baixos esforços: não necessita armadura
    v1 = PuncoamentoEC2(**base_kwargs(V_Ed=300_000))  # em kN
    _, rep1 = run_and_get(v1)
    assert "não é necessária armadura" in rep1.lower()

    # caso com esforços mais altos: deverá necessitar armadura
    v2 = PuncoamentoEC2(**base_kwargs(V_Ed=1_000_000))  # em kN
    _, rep2 = run_and_get(v2)
    assert "é necessária armadura" in rep2.lower()


def test_circular_beta_calculado_existe():
    # pilar circular de canto, β calculado via equivalência retangular
    v = PuncoamentoEC2(**base_kwargs(
        pilar_tipo='canto', pilar_forma='circular',
        pilar_c1=0.40, pilar_c2=None,
        M_Edx=20_000.0, M_Edy=15_000.0,
        beta_mode='calculado'
    ))
    _, rep = run_and_get(v)
    assert "calculado – canto circ" in rep.lower() or "calculado – canto" in rep.lower()
    assert v.beta >= 1.0  # regra geral com excentricidades, β >= 1


def test_relatorio_tem_tres_casas_decimais_em_valores_chave():
    # verifica formatação de 3 casas em linhas típicas
    v = PuncoamentoEC2(**base_kwargs(beta_mode='calculado', M_Edx=10_000, M_Edy=5_000))
    _, rep = run_and_get(v)
    # procura um padrão comum " 0.123 MPa" e " m)" com 3 casas
    assert re.search(r"\b\d+\.\d{3}\s*MPa\b", rep) is not None
    assert re.search(r"u1,?ef=\d+\.\d{3}\s*m", rep.replace(" ", "")) or re.search(r"u1=\d+\.\d{3}\s*m", rep) is not None

