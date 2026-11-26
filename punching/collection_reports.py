"""Consolidated reports: current combination results, grouped by floor and support."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

from .collection_workflow import cached_calculation, summaries, PENDING_LABELS
from .connections import describe_case
from .reports import sections
from .version import VERSION, STANDARD, REPOSITORY


CALCULATED_STATUSES = {'PASS_WITH','PASS_WITHOUT','FAIL_U0','FAIL_MAX','FAIL_DETAIL',
                       'REQUIRES_REINFORCEMENT','DETAIL_PENDING','EDGE_DETAIL_PENDING'}


def is_calculated(entry):
    return bool(entry and entry.get('snapshot') and entry['status'] in CALCULATED_STATUSES)


def build_report(book, keys=None, full=False, only_calculated=True):
    from .batch_workflow import named_group, classification
    keys=list(book.cases) if keys is None else list(keys)
    if not keys:raise ValueError('Não existem ligações para exportar.')
    if len(keys)!=len(set(keys)):raise ValueError('A seleção contém casos repetidos.')
    entries=[]
    for k in keys:
        case=book.cases[k];entry=cached_calculation(case)
        if only_calculated and not is_calculated(entry):continue
        if entry is None:
            entry=dict(floor=case['floor'],support=case['support'],combination=case['combination'],
                       status='NOT_EVALUATED',error='Por calcular com os dados atuais.',snapshot=None,actions=None)
        entry=deepcopy(entry);entry['inputs_gui']=deepcopy(case['draft']);entry['origin']=describe_case(case)
        entry['group']=named_group(book,case);entry['classification']=classification(case)
        entries.append(entry)
    if not entries:raise ValueError('Não existem resultados calculados e atualizados na seleção. Calcule os pilares pretendidos antes de exportar.')
    groups=summaries(entries);floor_order=[]
    for group in groups:
        items=[e for e in entries if (e['floor'],e['support'])==(group['floor'],group['support'])]
        total=sum((c['floor'],c['support'])==(group['floor'],group['support']) for c in book.cases.values())
        calculated=sum(is_calculated(e) for e in items)
        group.update(total_count=total,exported_count=len(items),calculated_count=calculated,
                     omitted_count=total-len(items),group=items[0]['group'],classification=items[0]['classification'])
        if calculated<total:
            group['status']='PARCIAL — NÃO VERIFICA' if group['failed'] else 'PARCIAL — PENDENTE'
        group['coverage']=f"{calculated}/{total} combinações calculadas"
    elevations={}
    for j in (book.model_setup or {}).get('joints',[]):
        if j.get('z') is not None:elevations.setdefault(j['floor'],[]).append(j['z'])
    for e in entries:
        if e['floor'] not in floor_order:floor_order.append(e['floor'])
    if elevations:floor_order.sort(key=lambda f:min(elevations.get(f,[float('inf')])))
    floor_rank={f:i for i,f in enumerate(floor_order)}
    entries.sort(key=lambda e:(floor_rank[e['floor']],e['group'],e['support'],e['combination']))
    groups.sort(key=lambda e:(floor_rank[e['floor']],e['group'],e['support']))
    projects=sorted({e['inputs_gui'].get('project','').strip() for e in entries if e['inputs_gui'] and e['inputs_gui'].get('project','').strip()})
    scope=('Apenas resultados calculados e atualizados, incluindo verificações favoráveis e desfavoráveis. '
           'As combinações omitidas são contabilizadas na cobertura de cada ligação.' if only_calculated else
           'Mapa de acompanhamento: inclui resultados atualizados e casos pendentes ou por calcular.')
    scope+=' Não abrange nós excluídos ou ainda não preparados.'
    return {'schema':'PunchingShearEC2.collection-report/2','version':VERSION,'standard':STANDARD,
            'emitted_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'projects':projects,'full':bool(full),
            'only_calculated':bool(only_calculated),'excluded_cases':len(keys)-len(entries),
            'floor_order':floor_order,'groups':groups,'entries':entries,'scope':scope,
            'model_reference':(book.model_setup or {}).get('config',{}).get('reference','')}


def detail_combinations(items, group, full):
    if full:return {e['combination'] for e in items}
    chosen={g['combination'] for g in group['governing'].values()}
    for field in ('Asw_sr_req','r_out_face'):
        available=[e for e in items if e['snapshot'] and e['snapshot']['values'].get(field) is not None]
        if available:chosen.add(max(available,key=lambda e:e['snapshot']['values'][field])['combination'])
    chosen.update(e['combination'] for e in items if e['status'] not in ('PASS_WITH','PASS_WITHOUT'))
    # Also represent each distinct physical input configuration, even if it does not govern.
    configurations={}
    for e in items:
        if not e.get('snapshot'):continue
        physical={k:v for k,v in e['snapshot']['inputs'].items()
                  if k not in ('V_Ed','M_Edx','M_Edy','combination','edge_perp_interior','corner_interior')}
        signature=json.dumps(physical,sort_keys=True,ensure_ascii=False)
        configurations.setdefault(signature,[]).append(e['combination'])
    for combinations in configurations.values():
        if not chosen.intersection(combinations):
            chosen.add(combinations[0])
    # Failed input/scope cases are individually listed in the result table.
    if not chosen and items:chosen.add(items[0]['combination'])
    return chosen


def export_collection_json(report,path):
    Path(path).write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def export_collection_txt(report,path):
    lines=['VERIFICAÇÃO DE PUNÇOAMENTO - CONJUNTO DE LIGAÇÕES',f"PunchingShearEC2 {report['version']} | {report['emitted_at']}",report['standard'],report['scope']]
    for floor in report['floor_order']:
        lines.extend(['',f'PISO: {floor}'])
        for group in [g for g in report['groups'] if g['floor']==floor]:
            lines.extend(['',f"PILAR: {group['support']} - {group['status']}",group['coverage'],'Grupo: '+(group['group'] or group['classification'])])
            items=[e for e in report['entries'] if (e['floor'],e['support'])==(floor,group['support'])]
            for e in items:
                lines.append(f"{e['combination']}: {e['status']}"+((' - '+e['error']) if e['error'] else ''))
                if e['snapshot']:
                    for sec in sections(e['snapshot']):lines.extend(['',sec['title'],*sec['lines']])
                    lines.extend(['Entradas (unidades da API)',json.dumps(e['snapshot']['inputs'],ensure_ascii=False,indent=2)])
                else:lines.extend([e['origin'],'Dados guardados (unidades da interface)',json.dumps(e['inputs_gui'],ensure_ascii=False,indent=2)])
    lines.extend(['',REPOSITORY]);Path(path).write_text('\n'.join(lines)+'\n',encoding='utf-8')


def export_collection_pdf(report,path):
    from .memory_pdf import export_collection
    export_collection(report,path)
