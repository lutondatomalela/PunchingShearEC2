"""Groups, common input templates and transactional edits across physical joints."""
from copy import deepcopy
import math
from .table_import import key
from .connections import initial_draft
from .longitudinal import DEFAULTS as LONG_DEFAULTS, CHOICES as LONG_CHOICES, DERIVED_KEYS, refresh_draft
from .collection_workflow import invalidate, rotate_joint, turn_of

PROJECT_KEYS = {'project','betão_fck','aço_fyk','aço_fywk','gamma_C','gamma_S',
                'reinforcement_diameter_mm','reinforcement_s0_m','reinforcement_sr_m','cover_mm','aggregate_mm'}
FLOOR_KEYS = {'laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm','sigma_cp'}
FLOOR_KEYS |= set(LONG_DEFAULTS)
GROUP_KEYS = {'pilar_tipo','edge_distance_m'}
SHARED_KEYS = PROJECT_KEYS | FLOOR_KEYS | GROUP_KEYS
TYPES = {'interior':'Interiores','bordo':'Bordo','canto':'Canto','':'Por classificar'}
EDGES = {0:'−Y',1:'+X',2:'+Y',3:'−X'}
CORNERS = {0:'−X / −Y',1:'+X / −Y',2:'+X / +Y',3:'−X / +Y'}
OPTIONAL = {'laje_dx','laje_dy','reinforcement_sr_m','reinforcement_s0_m'}


def empty_settings():
    return {'project':{},'floors':{},'groups':{}}


def validate_fields(fields, allowed=SHARED_KEYS):
    if not isinstance(fields,dict) or set(fields)-allowed:
        raise ValueError('A seleção contém campos que exigem definição individual.')
    for name,value in fields.items():
        if not isinstance(value,str):raise ValueError('Os parâmetros comuns devem ser texto ou números.')
        if name=='project':continue
        if name in LONG_CHOICES:
            if value not in LONG_CHOICES[name]:raise ValueError(f'{name}: escolha uma opção da lista.')
            continue
        if name=='pilar_tipo':
            if value not in {'interior','bordo','canto'}:raise ValueError('Escolha interior, bordo ou canto.')
            continue
        if not value.strip() and name in OPTIONAL:continue
        try:n=float(value.replace(',','.'))
        except ValueError:raise ValueError(f'{name}: indique um valor numérico.') from None
        if not math.isfinite(n) or n<0 or (n==0 and name not in {'edge_distance_m','sigma_cp','cover_mm','long_cover_mm','long_layer_gap_mm'}):
            raise ValueError(f'{name}: valor fora do domínio.')
        if name=='reinforcement_diameter_mm' and n not in {10,12,16}:
            raise ValueError('Diâmetro: selecione 10, 12 ou 16 mm.')


def validate_settings(settings, book):
    if not isinstance(settings,dict) or set(settings)!={'project','floors','groups'}:
        raise ValueError('Parâmetros comuns do conjunto inválidos.')
    validate_fields(settings['project'],PROJECT_KEYS)
    if not isinstance(settings['floors'],dict) or not isinstance(settings['groups'],dict):raise ValueError('Grupos ou pisos inválidos.')
    joints={key(c['floor'],c['support']) for c in book.cases.values()}
    for floor,fields in settings['floors'].items():
        if not isinstance(floor,str) or not floor.strip():raise ValueError('Piso inválido.')
        validate_fields(fields,PROJECT_KEYS|FLOOR_KEYS)
    for name,group in settings['groups'].items():
        if not isinstance(name,str) or not name.strip() or set(group)!={'fields','members'}:raise ValueError('Grupo inválido.')
        validate_fields(group['fields'])
        if not isinstance(group['members'],list) or len(set(group['members']))!=len(group['members']) or set(group['members'])-joints:
            raise ValueError('O grupo refere ligações inexistentes ou repetidas.')
    members=[m for g in settings['groups'].values() for m in g['members']]
    if len(members)!=len(set(members)):raise ValueError('Uma ligação não pode pertencer a dois grupos personalizados.')


def named_group(book, case):
    joint=key(case['floor'],case['support'])
    return next((name for name,g in book.batch_settings['groups'].items() if joint in g['members']),'')


def classification(case):
    kind=(case.get('draft') or {}).get('pilar_tipo','')
    result=TYPES.get(kind,'Por classificar')
    if kind=='bordo':result+=' '+(EDGES[turn_of(case)] if case.get('automated') else '(referencial do caso)')
    if kind=='canto':result+=' '+(CORNERS[turn_of(case)] if case.get('automated') else '(referencial do caso)')
    return result


def joint_selection(book, keys):
    selected=set(keys)
    if selected-set(book.cases):raise ValueError('Seleção de pilares inválida.')
    joints={(book.cases[k]['floor'],book.cases[k]['support']) for k in selected}
    return [k for k,c in book.cases.items() if (c['floor'],c['support']) in joints]


def representatives(book, keys):
    seen=set();result=[]
    for k in joint_selection(book,keys):
        c=book.cases[k];j=(c['floor'],c['support'])
        if j not in seen:seen.add(j);result.append(k)
    return result


def inherited_fields(book,case):
    fields=deepcopy(book.batch_settings['project'])
    fields.update(book.batch_settings['floors'].get(case['floor'],{}))
    group=named_group(book,case)
    if group:fields.update(book.batch_settings['groups'][group]['fields'])
    return fields


def seed_case(book,case,defaults):
    """Defaults only initialize untouched cases; an edited pillar is an exception."""
    draft=deepcopy(case.get('draft') or initial_draft(defaults,case))
    if not case.get('user_edited'):draft.update(inherited_fields(book,case))
    return draft


def remember_project(book,draft,previous=None):
    # Viewing a pillar must not replace project defaults with its exceptions.
    for name in PROJECT_KEYS:
        value=draft.get(name,'')
        if previous is not None and value==previous.get(name):continue
        if not value.strip() and name not in OPTIONAL and name!='project':continue
        try:validate_fields({name:value},PROJECT_KEYS)
        except ValueError:continue
        book.batch_settings['project'][name]=value


def save_template(book,scope,name,fields):
    allowed={'project':PROJECT_KEYS,'floor':PROJECT_KEYS|FLOOR_KEYS,'group':SHARED_KEYS}.get(scope)
    if allowed is None:raise ValueError('Âmbito de parâmetros desconhecido.')
    validate_fields(fields,allowed)
    if scope=='project':target=book.batch_settings['project']
    elif scope=='floor':
        if not name.strip():raise ValueError('Selecione o piso.')
        target=book.batch_settings['floors'].setdefault(name,{})
    else:
        if name not in book.batch_settings['groups']:raise ValueError('Selecione um grupo existente.')
        target=book.batch_settings['groups'][name]['fields']
    target.update(deepcopy(fields))


def assign_group(book,keys,name):
    name=name.strip()
    if not name:raise ValueError('Indique o nome do grupo.')
    joints={key(book.cases[k]['floor'],book.cases[k]['support']) for k in joint_selection(book,keys)}
    if not joints:raise ValueError('Selecione os pilares do grupo.')
    for g in book.batch_settings['groups'].values():g['members']=[j for j in g['members'] if j not in joints]
    g=book.batch_settings['groups'].setdefault(name,{'fields':{},'members':[]})
    g['members']=sorted(set(g['members'])|joints)


def remove_group(book,name):
    if name not in book.batch_settings['groups']:raise ValueError('Grupo inexistente.')
    del book.batch_settings['groups'][name]


def bulk_edit(book,keys,fields,defaults,only_empty=True,turn=None,template=None):
    """Validate the complete edit before committing; preserve each joint's loads."""
    validate_fields(fields)
    keys=joint_selection(book,keys)
    if not keys:raise ValueError('Selecione pelo menos um pilar.')
    proposed=deepcopy(book)
    if template:save_template(proposed,*template,fields)
    if turn is not None:
        for k in representatives(proposed,keys):rotate_joint(proposed,k,turn,defaults)
    changed=set()
    for k in keys:
        case=proposed.cases[k];draft=deepcopy(case['draft'] or initial_draft(defaults,case))
        for name,value in fields.items():
            if not only_empty or not str(draft.get(name,'')).strip():draft[name]=value
        if case.get('automated') and case.get('choice'):
            values=case['candidates'][case['choice']].get('adopted')
            if values:
                draft['edge_perp_interior']=values['M_Edx']>=0
                draft['corner_interior']=values['M_Edx']>=0 and values['M_Edy']>=0
        if draft.get('long_mode')=='automatic':
            if set(fields)&set(DERIVED_KEYS):
                raise ValueError('No modo automático, altere os varões, h e o recobrimento. Para editar d ou As diretamente, escolha o modo manual.')
            draft,_=refresh_draft(draft)
        elif draft['laje_dx'].strip() and draft['laje_dy'].strip():
            draft['laje_d']=f"{(float(draft['laje_dx'].replace(',','.'))+float(draft['laje_dy'].replace(',','.')))/2:.6g}"
        if draft!=case['draft']:invalidate(case);case['draft']=draft
        case['user_edited']=True
        if draft!=book.cases[k]['draft'] or turn_of(case)!=turn_of(book.cases[k]):changed.add(key(case['floor'],case['support']))
    book.cases=proposed.cases;book.geometries=proposed.geometries;book.batch_settings=proposed.batch_settings
    return len(changed)
