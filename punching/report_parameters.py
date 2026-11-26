"""Human-readable report vocabulary. No calculations or changes to results."""
import math
from datetime import datetime


def number(value, decimals=3, factor=1):
    if value is None:
        return 'Não calculado'
    if isinstance(value, bool):
        return 'Sim' if value else 'Não'
    if isinstance(value, (int, float)):
        value *= factor
        return f'{value:.{decimals}f}'.replace('.', ',') if math.isfinite(value) else 'Inválido'
    return str(value) or '-'


def date_label(value):
    try:
        date = datetime.fromisoformat(value)
        # Preserve the recorded timezone; never silently relabel UTC as local time.
        zone = ' UTC' if date.utcoffset() is not None and date.utcoffset().total_seconds() == 0 else date.strftime(' %z')
        return date.strftime('%d/%m/%Y %H:%M') + zone
    except (TypeError, ValueError):
        return str(value or '-')


INPUT_NAMES = {
    'laje_d': 'Altura útil média da laje - d (m)',
    'laje_dx': 'Altura útil na direção X - dx (m)',
    'laje_dy': 'Altura útil na direção Y - dy (m)',
    'betão_fck': 'Resistência característica à compressão do betão - fck (MPa)',
    'aço_fyk': 'Tensão característica de cedência do aço longitudinal - fyk (MPa)',
    'aço_fywk': 'Tensão característica de cedência do aço de punçoamento - fywk (MPa)',
    'gamma_C': 'Coeficiente parcial de segurança do betão - γC',
    'gamma_S': 'Coeficiente parcial de segurança do aço - γS',
    'V_Ed': 'Esforço transverso de cálculo - VEd (N)',
    'M_Edx': 'Momento de cálculo segundo X - MEdx (N.m)',
    'M_Edy': 'Momento de cálculo segundo Y - MEdy (N.m)',
    'pilar_c1': 'Dimensão do apoio em X / diâmetro - c1 / D (m)',
    'pilar_c2': 'Dimensão do apoio em Y - c2 (m)',
    'edge_distance_m': 'Distância livre da face do pilar ao bordo - g (m)',
    'laje_As_lx_cm2pm': 'Armadura longitudinal média em X - As,x (cm²/m)',
    'laje_As_ly_cm2pm': 'Armadura longitudinal média em Y - As,y (cm²/m)',
    'laje_rho_l': 'Taxa média de armadura longitudinal - ρl',
    'sigma_cp': 'Tensão média de compressão no plano - σcp (MPa)',
    'beta_mode': 'Método do coeficiente de majoração por excentricidade - β',
    'reinforcement_sr_m': 'Espaçamento radial indicado entre fiadas - sr (m)',
    'reinforcement_s0_m': 'Distância indicada da primeira fiada à face - s0 (m)',
    'reinforcement_diameter_mm': 'Diâmetro dos ramos de punçoamento - Ø (mm)',
    'cover_mm': 'Recobrimento nominal - cnom (mm)',
    'aggregate_mm': 'Dimensão máxima do agregado - dg (mm)',
}

# Description, symbol, displayed unit, conversion from the snapshot unit.
VALUE_NAMES = {
    'd': ('Altura útil média', 'd', 'm', 1),
    'dx': ('Altura útil em X', 'dx', 'm', 1),
    'dy': ('Altura útil em Y', 'dy', 'm', 1),
    'rho_lx': ('Taxa de armadura longitudinal em X', 'ρl,x', '%', 100),
    'rho_ly': ('Taxa de armadura longitudinal em Y', 'ρl,y', '%', 100),
    'rho_raw': ('Taxa média de armadura antes da limitação', 'ρl', '%', 100),
    'rho_l': ('Taxa média de armadura adotada', 'ρl', '%', 100),
    'fcd': ('Resistência de cálculo à compressão do betão', 'fcd', 'MPa', 1),
    'fyd': ('Tensão de cedência de cálculo do aço longitudinal', 'fyd', 'MPa', 1),
    'fywd': ('Tensão de cedência de cálculo do aço de punçoamento', 'fywd', 'MPa', 1),
    'k_val': ('Coeficiente de efeito de escala', 'k', '-', 1),
    'C_Rd_c': ('Coeficiente da resistência do betão ao punçoamento', 'CRd,c', '-', 1),
    'k1': ('Coeficiente da contribuição da compressão no plano', 'k1', '-', 1),
    'kmax': ('Fator do limite resistente com armadura', 'kmax', '-', 1),
    'v_min': ('Tensão resistente mínima sem armadura de punçoamento', 'vmin', 'MPa', 1),
    'nu': ('Fator de redução da resistência do betão fendilhado', 'ν', '-', 1),
    'u0': ('Perímetro de controlo na face do pilar', 'u0', 'm', 1),
    'u1': ('Perímetro de controlo de referência, geométrico', 'u1', 'm', 1),
    'u1_eff': ('Perímetro de controlo de referência, efetivo', 'u1,ef', 'm', 1),
    'u1_star': ('Perímetro de controlo reduzido', 'u1*', 'm', 1),
    'V_Ed_red': ('Esforço transverso reduzido pela reação do terreno', 'VEd,red', 'kN', .001),
    'beta': ('Coeficiente de majoração por excentricidade', 'β', '-', 1),
    'v_Ed_u0': ('Tensão de punçoamento atuante na face', 'vEd,0', 'MPa', 1),
    'v_Ed_u1': ('Tensão de punçoamento atuante no perímetro de referência', 'vEd,1', 'MPa', 1),
    'v_Rd_max': ('Resistência máxima ao punçoamento na face', 'vRd,max', 'MPa', 1),
    'v_Rd_c': ('Resistência ao punçoamento sem armadura específica', 'vRd,c', 'MPa', 1),
    'v_Rd_cs_max': ('Limite da resistência com armadura de punçoamento', 'vRd,cs,max', 'MPa', 1),
    'f_ywd_ef': ('Tensão efetiva de cálculo do aço de punçoamento', 'fywd,ef', 'MPa', 1),
    'Asw_sr_calc': ('Armadura por unidade radial calculada', 'Asw/sr', 'cm²/m', 1e4),
    'Asw_sr_min': ('Armadura mínima de referência por unidade radial', 'Asw/sr,min', 'cm²/m', 1e4),
    'Asw_sr_req': ('Armadura requerida por resistência por unidade radial', 'Asw/sr,req', 'cm²/m', 1e4),
    'Asw_sr_min_u1_reference': ('Armadura mínima de referência no perímetro u1', 'Asw/sr,min,u1', 'cm²/m', 1e4),
    'Asw_por_perimetro': ('Área de armadura por perímetro', 'Asw', 'cm²', 1e4),
    'u_out_ef': ('Perímetro exterior efetivo', 'uout,ef', 'm', 1),
    'u_out_required': ('Comprimento requerido do perímetro exterior', 'uout,req', 'm', 1),
    'r_out_face': ('Distância do perímetro exterior à face do pilar', 'rout', 'm', 1),
    'dist_zona_armar': ('Distância mínima da última fiada à face', 'rúlt', 'm', 1),
    'n_perimetros': ('Número de fiadas de armadura', 'n', '-', 1),
    's0_max': ('Distância máxima da primeira fiada à face', 's0,max', 'm', 1),
    'sr_max': ('Espaçamento radial máximo entre fiadas', 'sr,max', 'm', 1),
    'v_Rd_cs_provided': ('Resistência com a armadura proposta', 'vRd,cs', 'MPa', 1),
    'a_governing': ('Distância da secção condicionante à face', 'a', 'm', 1),
    'soil_pressure_used_kpa': ('Pressão líquida do terreno considerada', 'σgd', 'kPa', 1),
}


def value_rows(result, names):
    rows = []
    for key in names:
        name, symbol, unit, factor = VALUE_NAMES[key]
        rows.append((name, symbol, number(result['values'].get(key), factor=factor), unit))
    return rows


def material_rows(result):
    p = result['inputs']
    return [
        ('Resistência característica à compressão do betão', 'fck', number(p['betão_fck'], 1), 'MPa'),
        ('Tensão característica de cedência do aço longitudinal', 'fyk', number(p['aço_fyk'], 0), 'MPa'),
        ('Tensão característica de cedência do aço de punçoamento', 'fywk', number(p['aço_fywk'], 0), 'MPa'),
        ('Coeficiente parcial de segurança do betão', 'γC', number(p['gamma_C'], 2), '-'),
        ('Coeficiente parcial de segurança do aço', 'γS', number(p['gamma_S'], 2), '-'),
    ]


def geometry_rows(result):
    p = result['inputs']
    rows = [('Posição / forma do apoio', '-', p['pilar_tipo'].capitalize() + ' / ' + p['pilar_forma'], '-')]
    if p['pilar_forma'] == 'circular':
        rows.append(('Diâmetro do pilar', 'D', number(p['pilar_c1']), 'm'))
    else:
        rows.append(('Dimensões do pilar em X / Y', 'c1 / c2',
                     number(p['pilar_c1'])+' / '+number(p['pilar_c2']), 'm'))
    if p['pilar_tipo'] == 'bordo':
        rows.append(('Distância livre da face ao bordo', 'g', number(p.get('edge_distance_m', 0)), 'm'))
    trace = result.get('longitudinal_trace')
    if trace:
        layout = trace['layout']
        rows.extend([('Espessura da laje', 'h', number(layout['h_mm'], 0), 'mm'),
                     ('Recobrimento à superfície da armadura longitudinal', 'c', number(layout['cover_mm'], 0), 'mm')])
    rows += value_rows(result, ['d'])
    rows.append(('Alturas úteis em X / Y', 'dx / dy',
                 number(result['values']['dx'])+' / '+number(result['values']['dy']), 'm'))
    rows.append(('Armaduras longitudinais médias em X / Y', 'As,x / As,y',
                 number(p['laje_As_lx_cm2pm'], 2)+' / '+number(p['laje_As_ly_cm2pm'], 2), 'cm²/m'))
    rows += value_rows(result, ['rho_l'])
    rows.append(('Tensão média de compressão no plano', 'σcp', number(p['sigma_cp']), 'MPa'))
    return rows


def readable_input(key, value):
    """Text values for spreadsheet cells; structured data stays in JSON exports."""
    if key == 'beta_mode':
        return {'ec2':'Eurocódigo 2', 'manual':'Valor fundamentado pelo projetista', 'simplificado':'Coeficiente simplificado'}.get(value, str(value))
    if key == 'interior_beta_method':
        return {'ec2_643':'Flexão biaxial - expressão (6.43)', 'ec2_639':'Expressão (6.39)',
                'biaxial_envelope':'Combinação conservadora da expressão (6.39)'}.get(value, str(value))
    if key == 'longitudinal_layout' and isinstance(value, dict):
        lines = [f"Espessura: {number(value['h_mm'],0)} mm; recobrimento longitudinal: {number(value['cover_mm'],0)} mm",
                 f"Camada exterior: {value['outer_axis'].upper()}; afastamento entre camadas: {number(value['layer_gap_mm'],0)} mm"]
        for axis in ('x','y'):
            a = value[axis]
            lines.append(f"{axis.upper()}: Ø{number(a['base_mm'],0)} // {number(a['spacing_mm'],0)} mm" +
                         (f" + Ø{number(a['extra_mm'],0)} // {number(a['spacing_mm'],0)} mm" if a['extra_mm'] else ''))
        return '\n'.join(lines)
    if key == 'opening_sectors' and isinstance(value, (list,tuple)):
        return '; '.join(f'{number(a,1)}° a {number(b,1)}°' for a,b in value) or 'Sem setores manuais'
    if isinstance(value, bool):
        return 'Sim' if value else 'Não'
    if isinstance(value, (list,dict,tuple)):
        return 'Consultar a folha específica e o registo JSON' if value else 'Sem elementos'
    return value
