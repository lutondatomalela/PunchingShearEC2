"""Canonical GUI-unit parsing shared by individual and collection calculations."""
import json
from .core import number
from . import geometry as geo
from .openings import normalize_openings

def parse_sectors(text):
    if not text.strip():return []
    pairs=[]
    for part in text.replace('\n','|').split('|'):
        bits=part.strip().split(';')
        if len(bits)!=2:raise ValueError('Setores: use início;fim, separados por |. Exemplo: -20;20 | 100;125.')
        pairs.append([number(x.replace(',','.'),'Ângulo') for x in bits])
    geo.sectors_normalized(pairs);return pairs


def collect_inputs(draft, defaults):
    from .longitudinal import DEFAULTS as LONG_DEFAULTS, refresh_draft
    draft, longitudinal = refresh_draft(draft)
    p={}
    strings={'project','support','combination','pilar_tipo','pilar_forma','beta_mode','footing_shape','beta_reference','interior_beta_method'}
    optional={'laje_dx','laje_dy','reinforcement_sr_m','reinforcement_s0_m','footing_bx','footing_by','footing_diameter','beta_manual'}
    # Keep valid values for round trips, but an unfinished number in a
    # hidden, unused control must not block the selected calculation mode.
    inactive=set()
    if draft['beta_mode']!='manual':inactive.add('beta_manual')
    if not draft['is_sapata']:inactive.update(('footing_bx','footing_by','footing_diameter','sigma_gd_kpa'))
    elif draft['footing_shape']=='circular':inactive.update(('footing_bx','footing_by'))
    else:inactive.add('footing_diameter')
    for k,var in draft.items():
        if k in LONG_DEFAULTS: continue
        value=var
        if k=='pilar_c2' and draft['pilar_forma']=='circular':p[k]=None
        elif k in inactive:
            try:p[k]=number(value.replace(',','.'),k) if value.strip() else None
            except ValueError:p[k]=None
            if k=='sigma_gd_kpa' and (p[k] is None or not 0<=p[k]<=1e6):p[k]=0.
        elif k=='opening_sectors':p[k]=parse_sectors(value)
        elif k=='openings':p[k]=normalize_openings(json.loads(value or '[]'))
        elif isinstance(defaults[k],bool):p[k]=bool(value)
        elif k in strings:p[k]=value.strip()
        elif k in optional and not value.strip():p[k]=None
        else:p[k]=number(value.replace(',','.'),k)
    if p['pilar_forma']=='circular':p['pilar_c2']=None
    for k in ('V_Ed','M_Edx','M_Edy'):p[k]*=1000
    if p['laje_dx'] is not None and p['laje_dy'] is not None:p['laje_d']=(p['laje_dx']+p['laje_dy'])/2
    if longitudinal is not None:p['longitudinal_layout']=longitudinal['layout']
    return p

