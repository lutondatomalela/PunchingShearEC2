"""Consolidated reports: current combination results, grouped by floor and support."""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

from .collection_workflow import cached_calculation, summaries, PENDING_LABELS
from .connections import describe_case
from .reports import sections, drawing, _pdf_fonts, INPUT_LABELS, fmt
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
    chosen.update(e['combination'] for e in items if e['status'].startswith('FAIL'))
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, CondPageBreak
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    font,bold=_pdf_fonts();width=A4[0]-104
    body=ParagraphStyle('body',fontName=font,fontSize=10,leading=15,spaceAfter=6)
    heading=ParagraphStyle('heading',fontName=bold,fontSize=12,leading=18,spaceBefore=14,spaceAfter=10,keepWithNext=True)
    small=ParagraphStyle('small',fontName=font,fontSize=8,leading=12,spaceAfter=0)
    title=ParagraphStyle('title',parent=heading,fontSize=15,leading=21,spaceAfter=16)
    table_heading=ParagraphStyle('table_heading',parent=heading,keepWithNext=False)
    def par(value,style=body):return Paragraph(escape(str(value)),style)
    def table(headers,values,widths):
        rows=[[par(v,small) for v in headers]]+[[par(v,small) for v in row] for row in values]
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfe9f0')),
            ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#7b8a96')),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7fa')])]))
        return t
    story=[par('Verificação de punçoamento',title),par('Conjunto de ligações por piso',heading),
        par('Projeto: '+(' / '.join(report['projects']) or 'Por identificar')),par(f"Versão {report['version']} | Emissão {report['emitted_at']}"),par(report['standard']),
        par(f"{len(report['floor_order'])} pisos; {len(report['groups'])} ligações; {len(report['entries'])} combinações verificadas ou com pendências registadas."),par(report['scope'])]
    if report['model_reference']:story.append(par('Referência do modelo: '+report['model_reference']))
    story.append(par('VEd e MEd são concomitantes por combinação. A combinação condicionante é indicada por verificação, sem construir uma combinação artificial de máximos.'))
    story.append(par('Detalhe: '+('todas as combinações.' if report['full'] else 'combinações condicionantes; os quadros apresentam as combinações abrangidas pela seleção.')))
    for floor in report['floor_order']:
        story.append(par('Piso: '+floor,heading))
        groups=[g for g in report['groups'] if g['floor']==floor]
        story.append(table(['Pilar','Calculadas / total','Falhas','Omitidas','Conclusão'],[[g['support'],f"{g['calculated_count']}/{g['total_count']}",g['failed'],g['omitted_count'],g['status']] for g in groups],[70,83,40,52,width-245]))
    for floor in report['floor_order']:
        for group in [g for g in report['groups'] if g['floor']==floor]:
            items=[e for e in report['entries'] if (e['floor'],e['support'])==(floor,group['support'])]
            story.extend([PageBreak(),par(f"Piso: {floor} - Pilar {group['support']}",heading),par('Conclusão da ligação: '+group['status']),par(group['coverage']+'; '+str(group['omitted_count'])+' omitidas.'),par('Grupo: '+(group['group'] or group['classification']))])
            if group['different_reinforcement_proposals']:
                story.append(par('Existem propostas de armadura distintas entre combinações. A adoção de um pormenor comum requer a sua conferência em todas as combinações; não basta escolher a maior área de aço.'))
            rows=[]
            for e in items:
                r=e['snapshot'];v=r['load_trace']['adopted'] if r else e.get('actions')
                rows.append([e['combination'],*(f'{v[f]:.3f}' if v else '-' for f in ('V_Ed','M_Edx','M_Edy')),r['badge'] if r else PENDING_LABELS[e['status']]])
            story.append(table(['Combinação','VEd (kN)','MEdx (kN.m)','MEdy (kN.m)','Situação'],rows,[88,66,75,75,width-304]))
            story.append(par('Combinações condicionantes',heading))
            if group['governing']:
                for g in group['governing'].values():story.append(par(f"{g['name']}: {g['combination']}; utilização {g['utilization']:.3f}."))
            else:story.append(par('Não existem verificações resistentes concluídas.'))
            for e in items:
                if e['error']:story.append(par(e['combination']+': '+e['error']))
            chosen=detail_combinations(items,group,report['full'])
            for e in items:
                if e['combination'] not in chosen:continue
                story.extend([PageBreak(),par(f"{floor} / {group['support']} / {e['combination']}",heading)])
                r=e['snapshot']
                if r:
                    for i,sec in enumerate(sections(r)):
                        story.append(par(sec['title'],heading))
                        for line in sec['lines']:story.append(par(line))
                        if i==2 and r['geometry']:story.append(drawing(r,width=width))
                    story.extend([CondPageBreak(110),par('Registo das entradas do caso',table_heading)])
                    entries=[[INPUT_LABELS.get(k,k),fmt(v)] for k,v in r['inputs'].items() if v is not None and k not in ('openings','u1_ineffective')]
                    story.append(table(['Entrada','Valor'],entries,[260,width-260]))
                else:
                    story.append(par('Verificação pendente: '+e['error']))
                    for line in e['origin'].splitlines():
                        if line:story.append(par(line))
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=52,rightMargin=52,topMargin=42,bottomMargin=60,
                         title='PunchingShearEC2 - Memória do conjunto de ligações',author='PunchingShearEC2',
                         creator='PunchingShearEC2 '+report['version'],subject=report['scope'],
                         keywords='punçoamento; ligações; grupos; '+report['version'])
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont(font,8);canvas.setStrokeColor(colors.lightgrey);canvas.line(52,46,A4[0]-52,46)
        canvas.drawCentredString(A4[0]/2,34,f"PunchingShearEC2 {report['version']} | {report['emitted_at']} | {doc.page}")
        canvas.drawCentredString(A4[0]/2,22,REPOSITORY);canvas.linkURL(REPOSITORY,(52,18,A4[0]-52,29),relative=0);canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
