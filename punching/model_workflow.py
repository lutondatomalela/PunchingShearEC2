"""Model-wide topology, joint preparation and cardinal changes of reference frame.

The existing Modelo adapter owns sectional-force conventions. This module never
infers a local-axis direction from row order or a missing column from its name.
"""
from collections import defaultdict
from copy import copy, deepcopy
import json
import math
import re

from .table_import import key, identity, numeric
from .analysis_import import (all_records, members, parse_nodes, restore, archive,
    column_map, split_key, member_role, build_joint, geometry_for, validate_candidate,
    analysis_source_lines)

FRAME_ADAPTER = 'Modelo.joint-frame/1'
FRAME_LABELS = {
    0: 'X = +X modelo; Y = +Y modelo | bordo -Y',
    1: 'X = +Y modelo; Y = -X modelo | bordo +X',
    2: 'X = -X modelo; Y = -Y modelo | bordo +Y',
    3: 'X = -Y modelo; Y = +X modelo | bordo -X',
}
PAIRS = ((1,0),(0,1),(-1,0),(0,-1))
CONFIRMATIONS = ('analysis_3d','same_combination','isolated_joint','at_joint','axes_confirmed')


def quarter(value):
    if type(value) is not int or value not in FRAME_LABELS: raise ValueError('Orientação: selecione 0, 90, 180 ou 270 graus.')
    return value


def rotate_forces(values, turn):
    c,s = PAIRS[quarter(turn)]
    # Stored convention: MEdx = physical Mx, MEdy = -physical My.
    a,b=values['M_Edx'],values['M_Edy']
    return {'V_Ed':values['V_Ed'], 'M_Edx':c*a-s*b, 'M_Edy':s*a+c*b}


def frame_candidate(base, turn):
    quarter(turn)
    if base.get('adapter')==FRAME_ADAPTER: base=base['frame']['base']
    result={k:deepcopy(base[k]) for k in ('floor','support','combination','kind','issues','reference','records')}
    result.update(adapter=FRAME_ADAPTER, frame={'turn':turn,'base':deepcopy(base)},
                  adopted=rotate_forces(base['adopted'],turn) if base['adopted'] is not None else None,
                  method=f"Ligação Modelo; referencial do caso: {FRAME_LABELS[turn]}. Esforços convertidos conjuntamente por rotação de {turn*90} graus.")
    return result


def validate_frame(candidate):
    base=candidate['frame']['base']; validate_candidate(base)
    if candidate!=frame_candidate(base,candidate['frame']['turn']):
        raise ValueError('A transformação dos esforços não corresponde ao referencial guardado.')


def frame_source_lines(candidate):
    result=['Origem no referencial do modelo (antes da rotação):', *analysis_source_lines(candidate['frame']['base']),
            'Referencial da verificação: '+FRAME_LABELS[candidate['frame']['turn']]+'.',
            'Transformação: MEdx\' = cos(t)*MEdx - sin(t)*MEdy; MEdy\' = sin(t)*MEdx + cos(t)*MEdy; VEd inalterado.']
    if candidate['adopted']:
        result.append('Esforços no referencial do caso: '+ '; '.join(f'{k}={v:.6g}' for k,v in candidate['adopted'].items())+' (kN; kN.m).')
    else: result.append('Resultante da ligação pendente; a rotação não resolve a origem dos esforços.')
    return result


def frame_geometry(geometry, turn):
    g=deepcopy(geometry)
    if g and quarter(turn)%2 and g['inputs']['pilar_forma']=='retangular':
        p=g['inputs'];p['pilar_c1'],p['pilar_c2']=p['pilar_c2'],p['pilar_c1']
    return g


def combo_filter(text, available):
    text=text.strip()
    if not text or text.casefold()=='todas': return set(available)
    wanted=set()
    for part in re.split(r'[;,\s]+',text.replace('–','-').replace('−','-')):
        m=re.fullmatch(r'(\d+)(?:-(\d+))?',part)
        if not m: raise ValueError('Combinações: use números ou intervalos, por exemplo 101-117 201; vazio inclui todas.')
        lo=int(m[1]);hi=int(m[2] or m[1])
        if lo>hi or hi-lo>10000: raise ValueError('Intervalo de combinações inválido.')
        wanted.update(range(lo,hi+1))
    found={c for c in available if (m:=re.match(r'^\s*(\d+)(?:\s|$|\()',c)) and int(m[1]) in wanted}
    represented={int(re.match(r'^\s*(\d+)',c)[1]) for c in found}
    if wanted-represented: raise ValueError('Combinações não encontradas: '+', '.join(map(str,sorted(wanted-represented))))
    return found


def topology(tables, node_table=None):
    records=all_records(tables);index=members(records)
    nodes=parse_nodes(restore(node_table)) if node_table else {}
    connected=defaultdict(list)
    for m,data in index.items():
        for n in data['nodes']:connected[n].append(m)
    result=[]
    for node,links in connected.items():
        below=[m for m in links if member_role(m,node,index,nodes)[0]=='below']
        above=[m for m in links if member_role(m,node,index,nodes)[0]=='above']
        b=below[0] if len(below)==1 else '';a=above[0] if len(above)==1 else ''
        if len(links)>2:issue='Mais de duas barras: conferir todas as transferências no nó.'
        elif any(member_role(m,node,index,nodes)[0]=='unsupported' for m in links):issue='Barra inclinada; fora do âmbito deste equilíbrio.'
        elif b and a and len(links)==2:issue=''
        elif b and len(links)==1:issue='Confirmar se o tramo superior está fisicamente ausente.'
        elif a and len(links)==1:issue='Sem tramo inferior na tabela; ligação por resolver.'
        else:issue='Cotas em falta ou associação ambígua; definir inferior/superior.'
        label=index[b or links[0]]
        result.append({'node':node,'floor':label['story'],'support':label['support'],
            'below':b,'above':a,'upper_absent':False,'enabled':not bool(issue),
            'z':nodes.get(node,{}).get('z'),'members':links,'issue':issue})
    return sorted(result,key=lambda j:(j['z'] is None,j['z'] or 0,j['floor'],j['support'],int(j['node'])))


def validate_config(config, index):
    if any(config.get(k) is not True for k in CONFIRMATIONS):
        raise ValueError('Confira o âmbito do modelo, a natureza das combinações e os eixos uma vez antes de preparar as ligações.')
    if not str(config.get('reference','')).strip():raise ValueError('Indique a referência do modelo e da convenção de eixos.')
    allowed_x={'+Z','-Z'};allowed_y={'+X','-X','+Y','-Y'}
    profiles=[config.get('axes',{})]
    for m,axes in config.get('member_axes',{}).items():
        if m not in index:raise ValueError(f'Exceção de eixos: barra {m} não encontrada.')
        profiles.append(axes)
    for axes in profiles:
        if set(axes)!= {'x','y'} or axes['x'] not in allowed_x or axes['y'] not in allowed_y:
            raise ValueError('Defina x local (+Z/-Z) e y local (+X/-X/+Y/-Y), com exceções por barra quando necessário.')


def prepare_model(tables, node_table, config, joints, *, allow_empty=False):
    records=all_records(tables);index=members(records);validate_config(config,index)
    wanted=combo_filter(config.get('combinations',''),{r['combination'] for r in records})
    # Index source rows once. Avoid rereading a complete project for each joint.
    grouped=[]
    for data in tables:
        t=restore(data);col=column_map(t)['compound'][0];rows=defaultdict(list)
        for i,raw in t.rows:rows[split_key(raw[col])[0]].append((i,raw))
        grouped.append((t,rows))
    bynode=defaultdict(set)
    for m,info in index.items():
        for node in info['nodes']:bynode[node].add(m)
    nt = restore(node_table) if node_table else None
    node_rows = {}
    if nt:
        parse_nodes(nt)
        col = column_map(nt)['node'][0]
        node_rows = {identity(raw[col],'Nó'):(i,raw) for i,raw in nt.rows}
    batch={'mode':'columns','file':'Modelo - ligações por piso','sha256':'','row_count':0,'loads':{},'geometries':{}}
    seen=set();seen_names=set();review=[];selected=[]
    for j in joints:
        if not j.get('enabled'):continue
        node=identity(j.get('node'),'Nó');floor=identity(j.get('floor'),'Piso');support=identity(j.get('support'),'Pilar')
        if node in seen:raise ValueError(f'Nó {node} selecionado mais de uma vez.')
        gkey=key(floor,support)
        if gkey in seen_names:raise ValueError(f'{floor} / {support}: dois nós com a mesma identificação de ligação. Distinga os apoios.')
        seen_names.add(gkey)
        seen.add(node);b=j.get('below','');a=j.get('above','')
        if b not in index or (a and a not in index):raise ValueError(f'Nó {node}: associe o tramo inferior e o superior.')
        if bynode[node]-{b,a}:raise ValueError(f'Nó {node}: existem outras barras que não podem ser omitidas.')
        subtables=[]
        for t,rows in grouped:
            subset=copy(t);subset.rows=sorted(rows.get(b,[])+rows.get(a,[]),key=lambda x:x[0])
            if subset.rows:subtables.append(archive(subset))
        setup={k:config[k] for k in CONFIRMATIONS}
        setup.update(floor=floor,support=support,node=node,below=b,above=a,upper_absent=j.get('upper_absent',False),
            below_axes=deepcopy(config.get('member_axes',{}).get(b,config['axes'])),
            above_axes=deepcopy(config.get('member_axes',{}).get(a,config['axes'])),
            reference=config['reference'],combination='')
        subnodes=None
        if nt:
            ends=index[b]['nodes'] | (index[a]['nodes'] if a else set())
            subset=copy(nt);subset.rows=sorted((node_rows[n] for n in ends if n in node_rows),key=lambda pair:pair[0]);subnodes=archive(subset)
        prepared=build_joint(subtables,setup,subnodes)
        kept={ckey:load for ckey,load in prepared['loads'].items() if load['combination'] in wanted}
        if not kept:raise ValueError(f'Nó {node}: sem resultados nas combinações selecionadas.')
        missing=wanted-{load['combination'] for load in kept.values()}
        if missing:
            raise ValueError(f'Nó {node}: faltam inteiramente as combinações '+', '.join(sorted(missing))+'. Complete a exportação ou reveja explicitamente o filtro do modelo.')
        for ckey,load in kept.items():
            if ckey in batch['loads']:raise ValueError('Ligações com identificadores repetidos.')
            batch['loads'][ckey]=frame_candidate(load,0)
        batch['geometries'].update(prepared['geometries']);batch['row_count']+=prepared['row_count']
        selected.append(deepcopy(j))
        review.append({'node':node,'floor':floor,'support':support,'ready':sum(v['adopted'] is not None for v in kept.values()),
                       'pending':sum(v['adopted'] is None for v in kept.values())})
    if not selected and not allow_empty:raise ValueError('Selecione pelo menos uma ligação com os tramos definidos.')
    batch['model_setup']={'config':deepcopy(config),'joints':selected}
    batch['model_review']=review
    return batch
