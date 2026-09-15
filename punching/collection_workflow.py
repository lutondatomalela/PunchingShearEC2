"""Shared joint data, calculation records and group summaries (no force envelope)."""
from copy import deepcopy
import hashlib
import json
import math

from .connections import FORCE_KEYS, initial_draft, provenance, adopt, validate_case
from .core import PuncoamentoEC2
from .input_data import collect_inputs, parse_sectors
from .model_workflow import (FRAME_ADAPTER, PAIRS, quarter, frame_candidate,
                             frame_geometry, rotate_forces)
from .table_import import key, numeric
from .openings import normalize_openings
from .version import VERSION

SEPARATE_KEYS = {*FORCE_KEYS,'support','combination','edge_perp_interior','corner_interior'}
SUCCESS={'PASS_WITH','PASS_WITHOUT'}
PENDING_LABELS={'INPUT_PENDING':'DADOS POR COMPLETAR','FORCES_PENDING':'ESFORÇOS PENDENTES',
                'NOT_EVALUATED':'POR CALCULAR','ERROR':'ERRO DE CÁLCULO'}


def group_keys(book, case):
    return [k for k,c in book.cases.items() if (c['floor'],c['support'])==(case['floor'],case['support'])]


def invalidate(case):
    case['last_status']=None;case.pop('_calculation',None);case.pop('_calculation_hash',None)


def sync_joint(book, active_key, draft, defaults):
    current=book.cases[active_key]
    if current['draft']!=draft:
        from .batch_workflow import remember_project
        remember_project(book,draft,current['draft'])
        current['user_edited']=True
        invalidate(current)
    current['draft']=deepcopy(draft)
    if not current.get('automated'):return
    for k in group_keys(book,current):
        if k==active_key:continue
        case=book.cases[k]
        if not case.get('automated'):continue
        other=deepcopy(case['draft'] or initial_draft(defaults,case))
        for name,value in draft.items():
            if name not in SEPARATE_KEYS:other[name]=deepcopy(value)
        if case['draft']!=other:invalidate(case);case['draft']=other;case['user_edited']=True


def turn_of(case):
    candidate=case['candidates'].get('columns',{})
    return candidate.get('frame',{}).get('turn',0)


def rotate_joint(book, ckey, turn, defaults):
    """Transactional rotation of complete physical definitions and source actions."""
    turn=quarter(turn);current=book.cases[ckey]
    if not current.get('automated'):raise ValueError('A orientação do modelo está disponível nas ligações preparadas automaticamente.')
    keys=group_keys(book,current);updated={}
    for k in keys:
        case=deepcopy(book.cases[k]);old=turn_of(case);delta=(turn-old)%4
        if not case.get('automated') or case['candidates'].get('columns',{}).get('adapter')!=FRAME_ADAPTER:
            raise ValueError('A ligação contém fontes sem o referencial do modelo.')
        if set(case['candidates']) != {'columns'} or case['choice']=='manual':
            raise ValueError('A ligação tem esforços manuais ou outra fonte. Converta e confira essa fonte no novo referencial antes de a rodar.')
        # Refuse to mask edited forces by overwriting them during a rotation.
        validate_case(case,defaults)
        if case['choice']:provenance(case,case['draft'],check_sense=False)
        draft=deepcopy(case['draft'] or initial_draft(defaults,case));c,s=PAIRS[delta]
        if delta%2:
            for name in ('base_mm','extra_mm','spacing_mm'):
                a,b='long_x_'+name,'long_y_'+name
                draft[a],draft[b]=draft[b],draft[a]
            draft['long_outer_axis']='y' if draft['long_outer_axis']=='x' else 'x'
            for a,b in [('pilar_c1','pilar_c2'),('laje_dx','laje_dy'),('laje_As_lx_cm2pm','laje_As_ly_cm2pm'),('footing_bx','footing_by')]:
                if a=='pilar_c1' and draft['pilar_forma']=='circular':continue
                draft[a],draft[b]=draft[b],draft[a]
        items=normalize_openings(json.loads(draft['openings'] or '[]'))
        for o in items:
            x,y=o['x'],o['y'];o['x'],o['y']=c*x+s*y,-s*x+c*y
            if delta%2 and o['shape']=='rectangular':o['width'],o['height']=o['height'],o['width']
        draft['openings']=json.dumps(items,ensure_ascii=False)
        sectors=parse_sectors(draft['opening_sectors'])
        draft['opening_sectors']=' | '.join(f'{a-delta*90:g};{b-delta*90:g}' for a,b in sectors)
        candidate=frame_candidate(case['candidates']['columns'],turn);case['candidates']['columns']=candidate
        case['geometry']=frame_geometry(case['geometry'],delta)
        if candidate['adopted'] is not None:adopt(case,'columns',draft,case['reference'])
        else:
            for name in FORCE_KEYS:draft[name]=''
            case['draft']=draft
        if case['draft']!=book.cases[k]['draft'] or delta:
            invalidate(case);case['user_edited']=True;updated[k]=case
    for k,case in updated.items():book.cases[k]=case
    if updated:
        sample=next(iter(updated.values()))
        if sample['geometry']:book.geometries[key(sample['floor'],sample['support'])]=deepcopy(sample['geometry'])


def case_signature(case):
    p={k:case.get(k) for k in ('floor','support','combination','draft','choice','reference','candidates','geometry')}
    return hashlib.sha256((VERSION+json.dumps(p,ensure_ascii=False,sort_keys=True,allow_nan=False)).encode()).hexdigest()


def cached_calculation(case):
    if '_calculation' not in case:return None
    return case.get('_calculation') if case.get('_calculation_hash')==case_signature(case) else None


def calculate_case(case, defaults):
    """Rebuild a result from current inputs; pending cases are explicit records."""
    entry={'floor':case['floor'],'support':case['support'],'combination':case['combination'],
           'status':'INPUT_PENDING','error':'','snapshot':None,'actions':None}
    try:
        validate_case(case,defaults)
        draft=case['draft'] or initial_draft(defaults,case)
        from .longitudinal import refresh_draft
        try:draft,_=refresh_draft(draft);case['draft']=draft
        except ValueError:pass  # The selected source status takes precedence below.
        if not case['choice']:
            issues=[issue for c in case['candidates'].values() for issue in c['issues']]
            entry['status']='FORCES_PENDING';entry['error']=' '.join(issues) or 'Origem dos esforços por selecionar.'
        else:
            trace=provenance(case,draft)
            entry['actions']=deepcopy(trace['adopted'])
            draft,_=refresh_draft(draft)
            case['draft']=draft
            inputs=collect_inputs(draft,defaults)
            if case.get('automated'):
                # The imported signs define the eccentricity direction in this frame.
                correct=(inputs['M_Edx']>=0, inputs['M_Edx']>=0 and inputs['M_Edy']>=0)
                if (inputs['pilar_tipo']=='bordo' and inputs['edge_perp_interior']!=correct[0]) or (inputs['pilar_tipo']=='canto' and inputs['corner_interior']!=correct[1]):
                    raise ValueError('O sentido da excentricidade difere dos esforços importados. Reponha a fonte ou corrija o referencial da ligação.')
            engine=PuncoamentoEC2(**inputs);engine.verificar_puncoamento();snapshot=engine.snapshot();snapshot['load_trace']=trace
            entry.update(status=snapshot['status'],snapshot=snapshot)
    except (ValueError,TypeError,KeyError) as exc:entry['error']=str(exc)
    except Exception as exc:entry['status']='ERROR';entry['error']=f'{type(exc).__name__}: {exc}'
    case['user_edited']=True
    case['_calculation']=deepcopy(entry);case['_calculation_hash']=case_signature(case)
    case['last_status']=entry['snapshot']['badge'] if entry['snapshot'] else PENDING_LABELS[entry['status']]
    return entry


def calculate_group(book, keys, defaults):
    for k in keys:yield k,calculate_case(book.cases[k],defaults)


def summaries(entries):
    groups={}
    for entry in entries:groups.setdefault(key(entry['floor'],entry['support']),[]).append(entry)
    result=[]
    for items in groups.values():
        first=items[0];governing={};fail=sum(i['status'].startswith('FAIL') or i['status']=='REQUIRES_REINFORCEMENT' for i in items)
        pending=sum(i['status'] not in SUCCESS and not i['status'].startswith('FAIL') and i['status']!='REQUIRES_REINFORCEMENT' for i in items)
        signatures=set();reinforced=False
        for item in items:
            snap=item['snapshot']
            if not snap:continue
            for check in snap['checks']:
                value=check.get('utilization')
                if value is not None and math.isfinite(value) and (check['id'] not in governing or value>governing[check['id']]['utilization']):
                    governing[check['id']]={'name':check['name'],'combination':item['combination'],'utilization':value}
            if snap['reinforcement_rows']:
                reinforced=True
                physical=[{k:row[k] for k in ('r','sr','phi_mm','n_legs','coordinates') if k in row} for row in snap['reinforcement_rows']]
                signatures.add(json.dumps(physical,sort_keys=True,allow_nan=False))
        distinct=reinforced and len(signatures)>1
        if fail:status='NÃO VERIFICA'
        elif pending:status='PENDENTE'
        elif distinct:status='PORMENOR COMUM POR CONFERIR'
        else:status='VERIFICA'
        result.append({'floor':first['floor'],'support':first['support'],'count':len(items),'failed':fail,'pending':pending,
                       'status':status,'governing':governing,'different_reinforcement_proposals':distinct})
    return result
