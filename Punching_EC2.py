# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 22:06:40 2025

@author: Engº Lutonda Tomalela
"""

"""
Programa Interativo para Verificação de Punçoamento em Lajes Maciças (Versão Avançada)
Baseado na NP EN 1992-1-1:2010 (+A1:2019)

melhorias:
- β pode ser "simplificado" ou "calculado".
- Para β "calculado":
  * Retangulares (bordo/canto): usa u1*, W1 e k(c1/c2) (Quadro 6.1, com interpolação).
  * Circulares (interior/bordo/canto): usa equivalência retangular (c1=c2=D) para W1 e u1*.
"""

"""
Projeto:    PunçoamentoEC2
Versão:     v1.0.0
Autor:      Eng.º Lutonda Tomalela
LikedIn:    
GitHub:     https://github.com/lutondatomalela/PuncoamentoEC2
Direitos:   © 2025 Eng.º Lutonda Tomalela. Todos os direitos reservados.
Norma:      NP EN 1992-1-1:2010 (+A1:2019)
Local/Data: Porto, 2025-10-31
"""

import math
import sys

FMT = ".3f"  # formato global de 3 casas

class PuncoamentoEC2:
    """
    Verificação ao punçoamento em lajes maciças (NP EN 1992-1-1:2010 + A1:2019).
    Unidades internas: N, m, MPa.
    """

    def __init__(self,
                 laje_d: float,
                 betão_fck: float,
                 aço_fyk: float,
                 aço_fywk: float,
                 pilar_tipo: str,
                 pilar_forma: str,
                 V_Ed: float,
                 pilar_c1: float,
                 pilar_c2: float = None,
                 M_Edx: float = 0.0,
                 M_Edy: float = 0.0,
                 sigma_cp: float = 0.0,
                 is_sapata: bool = False,
                 sigma_gd_kpa: float = 0.0,
                 u1_ineffective: float = 0.0,
                 gamma_C: float = 1.5,
                 gamma_S: float = 1.15,
                 beta_mode: str = "simplificado",
                 # NOVOS parâmetros de entrada
                 laje_As_lx_cm2pm: float | None = None,
                 laje_As_ly_cm2pm: float | None = None,
                 laje_rho_l: float | None = None):
        """
        Aceita Asx/Asy [cm²/m] ou ρl diretamente (retrocompatível).
        """

        # -------- entradas base --------
        self.d = laje_d
        self.fck = betão_fck
        self.fyk = aço_fyk
        self.fywk = aço_fywk
        self.tipo_pilar = pilar_tipo.lower()
        self.forma_pilar = pilar_forma.lower()
        self.V_Ed = V_Ed
        self.c1 = pilar_c1
        self.c2 = pilar_c2 if self.forma_pilar == 'retangular' else pilar_c1
        self.D = pilar_c1 if self.forma_pilar == 'circular' else None
        self.M_Edx = M_Edx
        self.M_Edy = M_Edy
        self.sigma_cp = sigma_cp
        self.is_sapata = is_sapata
        self.sigma_gd = sigma_gd_kpa * 1000
        self.u1_ineffective = u1_ineffective
        self.gamma_C = gamma_C
        self.gamma_S = gamma_S
        self.beta_mode = beta_mode.lower()

        # -------- cálculo automático de ρl --------
        def _calc_rho_l_from_As(As_lx_cm2pm, As_ly_cm2pm, d):
            rho_lx = (As_lx_cm2pm or 0.0) / 10000.0 / d
            rho_ly = (As_ly_cm2pm or 0.0) / 10000.0 / d
            if rho_lx <= 0 or rho_ly <= 0:
                return None
            return min((rho_lx * rho_ly) ** 0.5, 0.02)

        rho_from_As = _calc_rho_l_from_As(laje_As_lx_cm2pm, laje_As_ly_cm2pm, self.d)

        if rho_from_As is not None:
            self.rho_l = rho_from_As  # prioridade: Asx/Asy
            self.Asx_cm2pm = laje_As_lx_cm2pm
            self.Asy_cm2pm = laje_As_ly_cm2pm
        elif laje_rho_l is not None:
            self.rho_l = min(float(laje_rho_l), 0.02)
            self.Asx_cm2pm = None
            self.Asy_cm2pm = None
        else:
            raise ValueError("Forneça As_lx/As_ly (cm²/m) ou laje_rho_l.")

        # -------- parâmetros de cálculo --------
        self.fcd = 1.0 * self.fck / self.gamma_C
        self.fctm = 0.30 * self.fck ** (2 / 3) if self.fck <= 50 else (2.12 * math.log(1 + (self.fck + 8) / 10))
        self.fctk_0_05 = 0.7 * self.fctm
        self.fctd = (1.0 * self.fctk_0_05 / self.gamma_C)
        self.fyd = self.fyk / self.gamma_S
        self.fywd = self.fywk / self.gamma_S
        self.k_val = min(1 + math.sqrt(200 / (self.d * 1000)), 2.0)
        self.C_Rd_c = 0.18 / self.gamma_C
        self.k1 = 0.1
        self.v_min = 0.035 * (self.k_val ** 1.5) * (self.fck ** 0.5)
        self.nu = 0.6 * (1 - self.fck / 250)
        self.kmax = 1.5

        # -------- resultados --------
        self.u0 = 0.0
        self.u1 = 0.0
        self.u1_eff = 0.0
        self.V_Ed_red = self.V_Ed
        self.beta = 1.0
        self.k_beta = None
        self.v_Ed_u0 = 0.0
        self.v_Ed_u1 = 0.0
        self.v_Rd_max = 0.0
        self.v_Rd_c = 0.0
        self.armadura_necessaria = False
        self.relatorio = []

    # --------------------------
    # Perímetros críticos u0 / u1
    # --------------------------
    def _get_perimetros_criticos(self):
        """Calcula u0 (face) e u1 (a 2d)."""

        if self.forma_pilar == 'retangular':
            if self.tipo_pilar == 'interior':
                self.u0 = 2 * (self.c1 + self.c2)
                self.u1 = 2 * (self.c1 + self.c2) + 4 * math.pi * self.d
            elif self.tipo_pilar == 'bordo':
                self.u0 = min(self.c2 + 3 * self.d, self.c2 + 2 * self.c1)
                self.u1 = (self.c1 + 2 * self.c2) + 3 * math.pi * self.d
            elif self.tipo_pilar == 'canto':
                self.u0 = min(3 * self.d, self.c1 + self.c2)
                self.u1 = (self.c1 + self.c2) + 2 * math.pi * self.d

        elif self.forma_pilar == 'circular':
            if self.tipo_pilar == 'interior':
                self.u0 = math.pi * self.D
                self.u1 = math.pi * (self.D + 4 * self.d)
            elif self.tipo_pilar == 'bordo':
                self.u0 = min(self.D + 3 * self.d, 3 * self.D)
                self.u1 = 0.5 * math.pi * self.D + 3 * math.pi * self.d
            elif self.tipo_pilar == 'canto':
                self.u0 = min(3 * self.d, 2 * self.D)
                self.u1 = 0.25 * math.pi * self.D + 2 * math.pi * self.d
    # ---------------------------------
    # Auxiliares para β calculado
    # ---------------------------------
    @staticmethod
    def _interp_k_por_ratio(r: float) -> float:
        """
        Quadro 6.1 – k em função de c1/c2, com interpolação linear.
        Pontos: (0.5,0.45), (1.0,0.60), (2.0,0.70), (3.0,0.80). Extrapola por patamar.
        """
        if r <= 0.5:
            return 0.45
        if r >= 3.0:
            return 0.80
        # Entre 0.5–1.0
        if r < 1.0:
            # de 0.45 a 0.60
            t = (r - 0.5) / (1.0 - 0.5)
            return 0.45 + t * (0.60 - 0.45)
        # Entre 1.0–2.0
        if r < 2.0:
            t = (r - 1.0) / (2.0 - 1.0)
            return 0.60 + t * (0.70 - 0.60)
        # Entre 2.0–3.0
        t = (r - 2.0) / (3.0 - 2.0)
        return 0.70 + t * (0.80 - 0.70)

    def _u1_estrela_bordo_ret(self):
        """u1* (Fig. 6.20a) – retangular bordo."""
        red = 2.0 * min(0.5*self.c1, 1.5*self.d)
        return max(self.u1 - red, 0.0)

    def _u1_estrela_canto_ret(self):
        """u1* (Fig. 6.20b) – retangular canto."""
        red = min(0.5*self.c1, 1.5*self.d) + min(0.5*self.c2, 1.5*self.d)
        return max(self.u1 - red, 0.0)

    def _W1_retangular(self, c1=None, c2=None):
        """Momento estático W1 do perímetro u1 (forma rearranjada da Eq. 6.45)."""
        if c1 is None: c1 = self.c1
        if c2 is None: c2 = self.c2
        d = self.d
        return (c1*c1 + c2*c2)/4.0 + 8.0*d*c1 + 4.0*d*d + 2.0*math.pi*d*c2 + 2.0*math.pi*d*d

    # Equivalências para circulares (c1=c2=D)
    def _u1_estrela_bordo_circ(self):
        c_eq = self.D
        red = 2.0 * min(0.5*c_eq, 1.5*self.d)
        return max(self.u1 - red, 0.0)

    def _u1_estrela_canto_circ(self):
        c_eq = self.D
        red = min(0.5*c_eq, 1.5*self.d) + min(0.5*c_eq, 1.5*self.d)
        return max(self.u1 - red, 0.0)

    def _W1_circular_equiv(self):
        c_eq = self.D
        return self._W1_retangular(c1=c_eq, c2=c_eq)

    # --------------------------
    # Beta (simplificado/calculado)
    # --------------------------
    def _get_beta(self):
        """Calcula o fator β (simplificado ou calculado)."""
        # Sem momentos → β=1.0
        if abs(self.M_Edx) < 1e-12 and abs(self.M_Edy) < 1e-12:
            self.beta = 1.0
            self.k_beta = None
            self.relatorio.append(f"\nFator β: {self.beta:{FMT}} (sem momentos)")
            return

        if self.beta_mode == "simplificado":
            if self.tipo_pilar == 'interior':
                self.beta = 1.15
            elif self.tipo_pilar == 'bordo':
                self.beta = 1.4
            elif self.tipo_pilar == 'canto':
                self.beta = 1.5
            self.k_beta = None
            self.relatorio.append(f"\nFator β (simplificado): {self.beta:{FMT}} (valores recomendados).")
            return

        # ---- β calculado ----
        V = max(self.V_Ed, 1e-9)
        ex = abs(self.M_Edx)/V  # m
        ey = abs(self.M_Edy)/V  # m

        # k automático por Quadro 6.1
        if self.forma_pilar == 'retangular':
            ratio = self.c1 / self.c2 if self.c2 != 0 else 1.0
        else:  # circular → c1=c2=D ⇒ ratio=1.0
            ratio = 1.0
        self.k_beta = self._interp_k_por_ratio(ratio)

        if self.forma_pilar == 'retangular' and self.tipo_pilar == 'bordo':
            u1_star = self._u1_estrela_bordo_ret()
            W1 = self._W1_retangular()
            e_par = ey  # bordo paralelo a c1
            if u1_star <= 0 or W1 <= 0:
                self.beta = 1.0
                self.relatorio.append("\nAviso: u1* ou W1 inválido; assumido β=1.000.")
                return
            self.beta = 1.0 + (self.u1/u1_star) * (e_par / W1) * self.k_beta
            self.relatorio.append(
                f"\nFator β (calculado – bordo ret.): {self.beta:{FMT}} "
                f"(u1/u1*={(self.u1/u1_star):{FMT}}, e∥={e_par:{FMT}} m, W1={W1:{FMT}} m², k={self.k_beta:{FMT}}, c1/c2={ratio:{FMT}})."
            )
            return

        if self.forma_pilar == 'retangular' and self.tipo_pilar == 'canto':
            u1_star = self._u1_estrela_canto_ret()
            W1 = self._W1_retangular()
            if u1_star <= 0 or W1 <= 0:
                self.beta = 1.0
                self.relatorio.append("\nAviso: u1* ou W1 inválido (canto); assumido β=1.000.")
                return
            self.beta = 1.0 + (self.u1/u1_star) * ((ex + ey) / W1) * self.k_beta
            self.relatorio.append(
                f"\nFator β (calculado – canto ret.): {self.beta:{FMT}} "
                f"(u1/u1*={(self.u1/u1_star):{FMT}}, ex+ey={(ex+ey):{FMT}} m, W1={W1:{FMT}} m², k={self.k_beta:{FMT}}, c1/c2={ratio:{FMT}})."
            )
            return

        if self.forma_pilar == 'circular':
            W1_eq = self._W1_circular_equiv()
            if self.tipo_pilar == 'interior':
                if W1_eq <= 0:
                    self.beta = 1.0
                else:
                    self.beta = 1.0 + ((ex + ey) / W1_eq) * self.k_beta
                self.relatorio.append(
                    f"\nFator β (calculado – interior circ., equiv. ret.): {self.beta:{FMT}} "
                    f"(ex+ey={(ex+ey):{FMT}} m, W1_eq={W1_eq:{FMT}} m², k={self.k_beta:{FMT}}, c1/c2={ratio:{FMT}})."
                )
                return
            if self.tipo_pilar == 'bordo':
                u1_star = self._u1_estrela_bordo_circ()
                e_par = ey
                if u1_star <= 0 or W1_eq <= 0:
                    self.beta = 1.0
                    self.relatorio.append("\nAviso: u1* ou W1_eq inválido (bordo circ.); assumido β=1.000.")
                    return
                self.beta = 1.0 + (self.u1/u1_star) * (e_par / W1_eq) * self.k_beta
                self.relatorio.append(
                    f"\nFator β (calculado – bordo circ., equiv. ret.): {self.beta:{FMT}} "
                    f"(u1/u1*={(self.u1/u1_star):{FMT}}, e∥={e_par:{FMT}} m, W1_eq={W1_eq:{FMT}} m², k={self.k_beta:{FMT}}, c1/c2={ratio:{FMT}})."
                )
                return
            if self.tipo_pilar == 'canto':
                u1_star = self._u1_estrela_canto_circ()
                if u1_star <= 0 or W1_eq <= 0:
                    self.beta = 1.0
                    self.relatorio.append("\nAviso: u1* ou W1_eq inválido (canto circ.); assumido β=1.000.")
                    return
                self.beta = 1.0 + (self.u1/u1_star) * ((ex + ey) / W1_eq) * self.k_beta
                self.relatorio.append(
                    f"\nFator β (calculado – canto circ., equiv. ret.): {self.beta:{FMT}} "
                    f"(u1/u1*={(self.u1/u1_star):{FMT}}, ex+ey={(ex+ey):{FMT}} m, W1_eq={W1_eq:{FMT}} m², k={self.k_beta:{FMT}}, c1/c2={ratio:{FMT}})."
                )
                return

        # fallback (não previsto)
        if self.tipo_pilar == 'interior':
            self.beta = 1.15
            origem = "aprox. interior (com momentos)"
        elif self.tipo_pilar == 'canto':
            self.beta = 1.5
            origem = "aprox. canto (com momentos)"
        else:
            self.beta = 1.4
            origem = "aprox. bordo (com momentos)"
        self.k_beta = None
        self.relatorio.append(f"\nFator β (provisório): {self.beta:{FMT}} [{origem}].")

    # --------------------------
    # Resistências e esforços
    # --------------------------
    def _get_v_Rd_c(self):
        """v_Rd,c (MPa) – Eq. 6.47."""
        v_Rd_c_calc = self.C_Rd_c * self.k_val * (100 * self.rho_l * self.fck)**(1/3) + self.k1 * self.sigma_cp
        v_min_calc = self.v_min + self.k1 * self.sigma_cp
        self.v_Rd_c = max(v_Rd_c_calc, v_min_calc)
        self.relatorio.append(f"\nResistência s/ armadura (v_Rd,c): {self.v_Rd_c:{FMT}} MPa (ρl={(self.rho_l*100):{FMT}} %, σ_cp={self.sigma_cp:{FMT}} MPa)")

    def _get_V_Ed_red_e_u1_efetivo(self):
        """V_Ed_red (sapatas) e u1_eff (aberturas)."""
        self.V_Ed_red = self.V_Ed
        
        # Sapatas
        if self.is_sapata and self.sigma_gd > 0:
            if self.forma_pilar == 'retangular':
                A_control_1 = (self.c1 * self.c2) + (self.c1 * 2 * self.d) + (self.c2 * 2 * self.d) + (math.pi * (2 * self.d)**2 / 4)
            else: # circular
                A_control_1 = math.pi * (self.D/2 + 2*self.d)**2
            Delta_V_Ed = self.sigma_gd * A_control_1
            self.V_Ed_red = self.V_Ed - Delta_V_Ed
            self.relatorio.append(
                f"\nSapata detetada. V_Ed reduzido de {(self.V_Ed/1000):{FMT}} kN para {(self.V_Ed_red/1000):{FMT}} kN "
                f"(ΔV_Ed={(Delta_V_Ed/1000):{FMT}} kN)."
            )
        
        # Aberturas
        self.u1_eff = self.u1 - self.u1_ineffective
        if self.u1_ineffective > 0:
            self.relatorio.append(f"\nAbertura detetada. u1: {self.u1:{FMT}} m → u1,ef: {self.u1_eff:{FMT}} m.")
        else:
            self.u1_eff = self.u1

    def _verificar_esmagamento(self):
        """v_Ed(u0) vs v_Rd,max na face do pilar."""
        if self.u0 == 0:
            self.relatorio.append("\nERRO: Perímetro u0 é zero. Verifique dimensões do pilar.")
            return False
        
        self.v_Rd_max = 0.4 * self.nu * self.fcd
        #self.v_Rd_max = 0.5 * self.nu * self.fcd """alteração de 0.5 para 0.4"""
        self.v_Ed_u0 = (self.beta * self.V_Ed) / (self.u0 * self.d) / 1e6 # MPa
        
        self.relatorio.append(f"\n--- Verificação da Escora (u0={self.u0:{FMT}} m) ---")
        self.relatorio.append(f"Tensão de cálculo v_Ed(u0): {self.v_Ed_u0:{FMT}} MPa")
        self.relatorio.append(f"Tensão resistente v_Rd,max: {self.v_Rd_max:{FMT}} MPa")
        
        if self.v_Ed_u0 > self.v_Rd_max:
            self.relatorio.append("\nFALHA: Esmagamento da escora (v_Ed > v_Rd,max).")
            self.relatorio.append("       Aumentar d, fck ou dimensão do pilar.")
            return False
        self.relatorio.append("OK: Resistência ao esmagamento da escora verificada.")
        return True

    def _dimensionar_armadura(self):
        """Dimensiona a armadura de punçoamento Asw/sr."""
        self.armadura_necessaria = True
        self.relatorio.append(f"\n\n--- Dimensionamento de Armadura (u1,ef={self.u1_eff:{FMT}} m) ---")

        # Limite superior
        v_Rd_cs_max = self.kmax * self.v_Rd_c
        self.relatorio.append(f"Resistência máxima c/ armadura (v_Rd,cs,max = {self.kmax:{FMT}} * v_Rd,c): {v_Rd_cs_max:{FMT}} MPa")
        if self.v_Ed_u1 > v_Rd_cs_max:
            self.relatorio.append(f"FALHA: v_Ed(u1) ({self.v_Ed_u1:{FMT}} MPa) > v_Rd,cs,max ({v_Rd_cs_max:{FMT}} MPa). Aumentar d, fck ou pilar.")
            return

        # Asw/sr (Eq. 6.52)
        f_ywd_ef_d_mm = self.d * 1000
        f_ywd_ef = min(250 + 0.25 * f_ywd_ef_d_mm, self.fywd) # MPa
        
        Asw_sr_calc = (self.v_Ed_u1 - 0.75 * self.v_Rd_c) * self.u1_eff / (1.5 * f_ywd_ef)
        Asw_sr_min = (0.08 * math.sqrt(self.fck) / self.fywk) * (self.u1_eff / 1.5)
        Asw_sr_req = max(Asw_sr_calc, Asw_sr_min)
        
        self.relatorio.append(f"Tensão f_ywd,ef: {f_ywd_ef:{FMT}} MPa")
        self.relatorio.append(f"Armadura necessária (Asw/sr) (cálculo): {(Asw_sr_calc * 1e4):{FMT}} cm²/m")
        self.relatorio.append(f"Armadura mínima (Asw/sr): {(Asw_sr_min * 1e4):{FMT}} cm²/m")
        self.relatorio.append(f"**Armadura adotada (Asw/sr): {(Asw_sr_req * 1e4):{FMT}} cm²/m**")
        
        # perímetro exterior u_out,ef
        self.u_out_ef = (self.beta * self.V_Ed_red) / (self.v_Rd_c * self.d) / 1e6 # m
        self.relatorio.append(f"\nPerímetro exterior (u_out,ef): {self.u_out_ef:{FMT}} m")

        # zona a armar e nº de perímetros
        if self.forma_pilar == 'retangular':
            if self.tipo_pilar == 'interior':
                r_out = (self.u_out_ef - 2*(self.c1 + self.c2)) / (2*math.pi)
            elif self.tipo_pilar == 'bordo':
                r_out = (self.u_out_ef - (self.c1 + 2*self.c2)) / (3*math.pi/2)
            else: # canto
                r_out = (self.u_out_ef - (self.c1 + self.c2)) / (math.pi)
        else: # circular
            r_out = (self.u_out_ef / math.pi - self.D) / 2
        
        dist_zona_armar = r_out - 1.5 * self.d  # até 1.5d antes de u_out,ef
        
        s0_max = 0.5 * self.d
        sr_max = 0.75 * self.d
        
        self.relatorio.append("\n--- Pormenorização recomendada ---")
        self.relatorio.append(f"Distância radial a armar (da face): {dist_zona_armar:{FMT}} m (até {(1.5*self.d):{FMT}} m dentro de u_out,ef)")
        self.relatorio.append(f"Espaçamento radial máx. (sr): {sr_max:{FMT}} m")
        self.relatorio.append(f"Posição do 1º perímetro (s0): ≤ {s0_max:{FMT}} m")
        
        if dist_zona_armar < s0_max:
            n_perimetros = 2  # mínimo
            self.relatorio.append(f"Zona a armar é pequena. Adotar {n_perimetros} perímetros (mínimo).")
        else:
            n_perimetros = math.ceil((dist_zona_armar - s0_max) / sr_max) + 1
            if n_perimetros < 2:
                n_perimetros = 2
            self.relatorio.append(f"Número de perímetros estimado (com sr={sr_max:{FMT}} m): {n_perimetros}")

        Asw_por_perimetro = Asw_sr_req * sr_max
        self.relatorio.append(f"Área por perímetro (Asw) (para sr={sr_max:{FMT}} m): {(Asw_por_perimetro * 1e4):{FMT}} cm²")

    # --------------------------
    # Pipeline principal
    # --------------------------
    def verificar_puncoamento(self):
        """Executa a verificação completa ao punçoamento."""
        
        self.relatorio = ["\n--- Relatório de Verificação de Punçoamento (NP EN 1992-1-1) ---\n"]
        
        self.relatorio.append(f"Taxa média de armadura ρl = {(self.rho_l*100):.3f} %")        
        try:
            self._get_perimetros_criticos()
            self._get_beta()
            self._get_V_Ed_red_e_u1_efetivo()
            
            self.relatorio.append(
                f"Parâmetros: d={self.d:{FMT}} m, fck={self.fck:{FMT}} MPa, VEd_total={(self.V_Ed/1000):{FMT}} kN"
            )
            if self.is_sapata:
                self.relatorio.append(f"V_Ed_red (sapata): {(self.V_Ed_red/1000):{FMT}} kN")

            if not self._verificar_esmagamento():
                return "\n".join(self.relatorio)

            self._get_v_Rd_c()
            
            if self.u1_eff == 0:
                self.relatorio.append("\nERRO: Perímetro u1,ef é zero. Verifique dimensões/aberturas.")
                return "\n".join(self.relatorio)
            
            self.v_Ed_u1 = (self.beta * self.V_Ed_red) / (self.u1_eff * self.d) / 1e6 # MPa
            
            self.relatorio.append(f"\n--- Verificação da Necessidade de Armadura (u1,ef={self.u1_eff:{FMT}} m) ---")
            self.relatorio.append(f"Tensão de cálculo v_Ed(u1): {self.v_Ed_u1:{FMT}} MPa")
            
            if self.v_Ed_u1 <= self.v_Rd_c:
                self.relatorio.append(f"OK: v_Ed(u1) ({self.v_Ed_u1:{FMT}} MPa) ≤ v_Rd,c ({self.v_Rd_c:{FMT}} MPa).")
                self.relatorio.append("Não é necessária armadura de punçoamento.")
                self.armadura_necessaria = False
            else:
                self.relatorio.append(f"FALHA: v_Ed(u1) ({self.v_Ed_u1:{FMT}} MPa) > v_Rd,c ({self.v_Rd_c:{FMT}} MPa).")
                self.relatorio.append("É necessária armadura de punçoamento.")
                self._dimensionar_armadura()
        
        except Exception as e:
            self.relatorio.append(f"\nERRO INESPERADO: {e}")
            import traceback
            self.relatorio.append(traceback.format_exc())

        return "\n".join(self.relatorio)

# ---------------------------------------------------------------------
# --- FUNÇÕES INTERATIVAS PARA OBTER DADOS ---
# ---------------------------------------------------------------------

def obter_float(mensagem: str, min_val: float = -math.inf, max_val: float = math.inf, default_zero: bool = False) -> float:
    """Pede ao utilizador um valor float e valida-o."""
    while True:
        try:
            valor_str = input(mensagem)
            if valor_str.strip() == "" and default_zero:
                return 0.0
            valor = float(valor_str)
            if valor < min_val:
                print(f"Valor inválido. Deve ser >= {min_val:{FMT}}. Tente novamente.")
                continue
            if max_val is not None and valor > max_val:
                print(f"Valor inválido. Deve ser <= {max_val:{FMT}}. Tente novamente.")
                continue
            return valor
        except ValueError:
            print("Entrada inválida. Por favor, insira um número.")
        except Exception as e:
            print(f"Erro: {e}")

def obter_string(mensagem: str, opcoes_validas: list) -> str:
    """Pede ao utilizador uma string e valida-a contra uma lista de opções."""
    opcoes_lower = [opt.lower() for opt in opcoes_validas]
    while True:
        try:
            valor = input(mensagem).lower()
            if valor in opcoes_lower:
                return valor
            else:
                print(f"Opção inválida. Escolha entre: {', '.join(opcoes_validas)}")
        except Exception as e:
            print(f"Erro: {e}")

def obter_sim_nao(mensagem: str) -> bool:
    """Pede ao utilizador uma resposta 's' ou 'n'."""
    return obter_string(mensagem + " (s/n): ", ['s', 'n']) == 's'

# ---------------------------------------------------------------------
# --- EXECUÇÃO PRINCIPAL ---
# ---------------------------------------------------------------------
if __name__ == "__main__":

    print("==============================================================")
    print(" Verificação de Punçoamento (Avançado) - NP EN 1992-1-1")
    print("==============================================================")
    print("Por favor, insira os dados do projeto.")
    
    # 1. Materiais
    print("\n--- 1. Materiais ---")
    fck = obter_float(f"Classe do Betão, fck (MPa) [ex: 30]: ", min_val=12, max_val=90)
    fyk = obter_float(f"Classe do Aço (fyk) (MPa) [ex: 500]: ", min_val=400, max_val=600)
    fywk = fyk

    # 2. Laje
    print("\n--- 2. Laje ---")
    d = obter_float(f"Altura útil da laje, d (m) [ex: 0.22]: ", min_val=0.01)
    
    As_lx_cm2 = obter_float("Armadura As,lx (cm²/m): ", min_val=0.0)
    As_ly_cm2 = obter_float("Armadura As,ly (cm²/m): ", min_val=0.0)
    
    rho_lx = (As_lx_cm2 / 10000) / (1.0 * d)
    rho_ly = (As_ly_cm2 / 10000) / (1.0 * d)
    rho_l = min(math.sqrt(rho_lx * rho_ly), 0.02)
    
    print(f" (Taxa de armadura ρl: {(rho_l*100):{FMT}} %)")

    sigma_cp = obter_float(f"\nTensão de compressão média, σ_cp (MPa) [Default=0]: ", min_val=0.0, default_zero=True)

    # 3. Pilar
    print("\n--- 3. Pilar ---")
    tipo_pilar = obter_string("Tipo de Pilar (interior, bordo, canto): ", ['interior', 'bordo', 'canto'])
    forma_pilar = obter_string("Forma do Pilar (retangular, circular): ", ['retangular', 'circular'])

    c1 = 0.0
    c2 = None
    if forma_pilar == 'retangular':
        if tipo_pilar == 'interior':
            c1 = obter_float("Dimensão pilar c1 (m) [ex: 0.400]: ", min_val=0.01)
            c2 = obter_float("Dimensão pilar c2 (m) [ex: 0.400]: ", min_val=0.01)
        elif tipo_pilar == 'bordo':
            c1 = obter_float("Dimensão pilar c1 (m) [paralela ao bordo]: ", min_val=0.01)
            c2 = obter_float("Dimensão pilar c2 (m) [perpendicular ao bordo]: ", min_val=0.01)
        else: # canto
            c1 = obter_float("Dimensão pilar c1 (m) [paralela eixo x]: ", min_val=0.01)
            c2 = obter_float("Dimensão pilar c2 (m) [paralela eixo y]: ", min_val=0.01)
    else: # circular
        c1 = obter_float("Diâmetro do pilar (m) [ex: 0.350]: ", min_val=0.01)

    # 4. Esforços (ELU)
    print("\n--- 4. Esforços (ELU) ---")
    V_Ed_kN = obter_float("Esforço Transverso de Cálculo, V_Ed (kN) [ex: 600]: ", min_val=0.0)
    V_Ed_N = V_Ed_kN * 1000
    
    M_Edx_kNm = obter_float("Momento fletor M_Edx (kN.m) [em torno do eixo x, default=0]: ", default_zero=True)
    M_Edx_Nm = M_Edx_kNm * 1000
    M_Edy_kNm = obter_float("Momento fletor M_Edy (kN.m) [em torno do eixo y, default=0]: ", default_zero=True)
    M_Edy_Nm = M_Edy_kNm * 1000
    
    # 5. Parâmetros adicionais
    print("\n--- 5. Parâmetros adicionais ---")
    is_sapata = obter_sim_nao("O elemento é uma sapata (laje de fundação)?")
    sigma_gd_kpa = 0.0
    if is_sapata:
        sigma_gd_kpa = obter_float("\nTensão de cálculo no solo, σ_gd (kPa) [ex: 150]: ", min_val=0.0)

    u1_ineffective = 0.0
    if obter_sim_nao(f"\nExistem aberturas a menos de 6*d ({(6*d):{FMT}} m) da face do pilar?"):
        u1_ineffective = obter_float("Comprimento ineficaz a subtrair a u1 (m) [Fig. 6.14]: ", min_val=0.0)

    # 6. Modo de β
    print("\n--- 6. Opções de β ---")
    beta_mode = obter_string("Modo de β (simplificado, calculado): ", ['simplificado', 'calculado'])

    # Instância
    verificacao = PuncoamentoEC2(
        laje_d=d,
        laje_rho_l=rho_l,
        betão_fck=fck,
        aço_fyk=fyk,
        aço_fywk=fywk,
        pilar_tipo=tipo_pilar,
        pilar_forma=forma_pilar,
        V_Ed=V_Ed_N,
        pilar_c1=c1,
        pilar_c2=c2,
        M_Edx=M_Edx_Nm,
        M_Edy=M_Edy_Nm,
        sigma_cp=sigma_cp,
        is_sapata=is_sapata,
        sigma_gd_kpa=sigma_gd_kpa,
        u1_ineffective=u1_ineffective,
        beta_mode=beta_mode
    )

    # Executar
    print("\n" + "="*62)
    print(" INICIALIZAÇÃO...")
    print("="*62)
    print(verificacao.verificar_puncoamento())
    print("="*62 + "\n")
