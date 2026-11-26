"""PDF annexes for design statements, rendered from frozen calculation results.

The JSON/TXT audit exports retain the complete machine/provenance record.
This module never changes inputs, checks, conclusions or combination coverage.
"""
from datetime import datetime, timezone
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                               TableStyle, PageBreak, CondPageBreak, KeepTogether)

from .report_parameters import number, date_label, value_rows, material_rows, geometry_rows
from .version import REPOSITORY, VERSION


class MemoryPDF:
    def __init__(self, path, title, version, emitted):
        from .reports import _pdf_fonts
        self.font, self.bold = _pdf_fonts()
        self.width = A4[0] - 100
        self.version, self.emitted = version, emitted
        self.styles = {
            'body': ParagraphStyle('body', fontName=self.font, fontSize=10, leading=15, spaceAfter=7),
            'heading': ParagraphStyle('heading', fontName=self.bold, fontSize=12, leading=18,
                                      spaceBefore=12, spaceAfter=8, keepWithNext=True),
            'title': ParagraphStyle('title', fontName=self.bold, fontSize=16, leading=22,
                                    spaceAfter=14, keepWithNext=True),
            'cell': ParagraphStyle('cell', fontName=self.font, fontSize=9, leading=13.5),
            'headcell': ParagraphStyle('headcell', fontName=self.bold, fontSize=9, leading=13.5),
            'caption': ParagraphStyle('caption', fontName=self.font, fontSize=8, leading=12, spaceAfter=7),
        }
        # Account for the frame's 6 pt padding: tables and paragraphs share one width.
        self.doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=44, rightMargin=44,
            topMargin=34, bottomMargin=54, title=title, author=REPOSITORY,
            creator='PunchingShearEC2 '+VERSION, subject='Verificação de punçoamento - anexo à memória descritiva e justificativa',
            keywords='punçoamento; memória de cálculo; '+version)
        self.story = []

    def par(self, value, style='body'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), self.styles[style])

    def add(self, value, style='body'):
        self.story.append(self.par(value, style))

    def table(self, headers, rows, widths, width=None, append=True):
        rows = list(rows)
        if not rows:
            return
        cells = [[self.par(v, 'headcell') for v in headers]]
        cells += [[self.par(v, 'cell') for v in row] for row in rows]
        table = Table(cells, colWidths=[(width or self.width)*w for w in widths], repeatRows=1,
                      hAlign='LEFT', spaceAfter=9)
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8ebee')),
            ('TEXTCOLOR',(0,0),(-1,-1),colors.HexColor('#18232c')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f7f8')]),
            ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#8c959e')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        if append:
            self.story.append(table)
        return table

    def parameters(self, rows):
        self.table(['Parâmetro', 'Símbolo', 'Valor', 'Unidade'], rows, [.53,.14,.20,.13])

    def state(self, label, explanation=''):
        p = self.par(label, 'heading')
        t = Table([[p]], colWidths=[self.width], spaceAfter=9)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e8ebee')),
            ('BOX',(0,0),(-1,-1),.5,colors.HexColor('#8c959e')),
            ('LEFTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        self.story.append(KeepTogether([t]+([self.par(explanation)] if explanation else [])))

    def build(self):
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor('#aeb5bb'))
            canvas.line(50,46,A4[0]-50,46)
            canvas.setFont(self.font,8)
            canvas.drawString(50,34,f'PunchingShearEC2 {self.version} | {date_label(self.emitted)}')
            canvas.drawRightString(A4[0]-50,34,f'Página {doc.page}')
            canvas.drawCentredString(A4[0]/2,22,REPOSITORY)
            canvas.linkURL(REPOSITORY,(50,18,A4[0]-50,29),relative=0)
            canvas.restoreState()
        self.doc.build(self.story,onFirstPage=footer,onLaterPages=footer)


def actions(result):
    # Inputs are authoritative and in N/N.m; provenance is optional in saved cases.
    p = result['inputs']
    return [number(p[k],2,.001) for k in ('V_Ed','M_Edx','M_Edy')]


def _count(value, singular, plural):
    return f'{value} {singular if value == 1 else plural}'


def _longitudinal(pdf, r):
    trace = r.get('longitudinal_trace')
    if not trace:
        pdf.add('As alturas úteis e as áreas médias de armadura foram definidas manualmente.', 'caption')
        return
    layout = trace['layout']
    pdf.add('Disposição da armadura longitudinal', 'heading')
    pdf.table(['Direção','Armadura base e reforço','Disposição equivalente'],
        [[axis.upper(), trace['axes'][axis]['label']+' mm',
          (trace['axes'][axis].get('equivalent')+' mm') if trace['axes'][axis].get('equivalent') else 'Base e reforço intercalados']
         for axis in ('x','y')], [.12,.48,.40])
    pdf.add(f"Camada exterior: {layout['outer_axis'].upper()}; afastamento livre entre camadas: {number(layout['layer_gap_mm'],0)} mm. "
            'Alturas úteis calculadas a partir da espessura, do recobrimento e dos diâmetros.', 'caption')
    pdf.add(trace['scope'], 'caption')


def _source(pdf, r):
    trace = r.get('load_trace') or {}
    if trace:
        # Deliberately use only the adopted source description and reference.
        # Hashes, original CSV rows and serialised dictionaries belong to the audit record.
        from .connections import MODES
        label = 'Introdução manual' if trace.get('choice')=='manual' else MODES.get(trace.get('choice'), 'Resultantes da ligação')
        pdf.add('Origem dos esforços: '+label+'.', 'caption')
        if trace.get('reference'):
            pdf.add('Referência da análise: '+str(trace['reference']), 'caption')


def _checks(pdf, r):
    pdf.add('Esforços ELU concomitantes', 'caption')
    pdf.table(['Combinação','Esforço transverso\nVEd (kN)', 'Momento em X\nMEdx (kN.m)', 'Momento em Y\nMEdy (kN.m)'],
              [[r['inputs'].get('combination') or '-', *actions(r)]], [.22,.26,.26,.26])
    _source(pdf, r)
    pdf.add('Verificações resistentes', 'heading')
    pdf.table(['Verificação','Atuante\n(MPa)','Resistente\n(MPa)','Utilização\n(%)','Resultado'],
        [[c['name'],number(c['demand']),number(c['resistance']),number(c['utilization'],1,100),
          'Verifica' if c['passed'] else 'Não verifica'] for c in r['checks']], [.35,.15,.18,.14,.18])
    if not r['checks']:
        pdf.add('Não existem verificações resistentes concluídas para este caso.')
    else:
        pdf.add('Utilização = valor atuante / valor resistente. O resultado global considera também as pendências de pormenorização.', 'caption')
        references = list(dict.fromkeys(c['reference'] for c in r['checks']))
        pdf.add('Referências das verificações: '+'; '.join(references)+'.', 'caption')
    if any(not c['passed'] for c in r['checks']) and r.get('reinforcement_rows'):
        pdf.add('A verificação sem armadura específica e a verificação com armadura são apresentadas separadamente. A conclusão global corresponde à solução indicada acima.', 'caption')


def _geometry(pdf, r):
    pdf.add('Perímetros e distribuição de esforços', 'heading')
    names = ['u0','u1_eff']
    if r['values'].get('u1') != r['values'].get('u1_eff'):
        names.insert(1,'u1')
    if r['values'].get('u1_star') is not None:
        names.append('u1_star')
    names.append('beta')
    parameters = value_rows(r,names)
    if r.get('geometry'):
        from .reports import drawing
        # A plan beside the perimeter values keeps the evidence together and avoids
        # spending an entire continuation page on a small schematic.
        left = pdf.width*.59
        table = pdf.table(['Parâmetro','Valor'],
                          [[f'{name} ({symbol})', value+' '+unit] for name,symbol,value,unit in parameters],
                          [.71,.29],width=left,append=False)
        plan = drawing(r,width=pdf.width-left-8,height=175,legend=False)
        pair = Table([[table,plan]],colWidths=[left,pdf.width-left],hAlign='LEFT')
        pair.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                 ('LEFTPADDING',(0,0),(-1,-1),0),
                                 ('RIGHTPADDING',(0,0),(-1,-1),0),
                                 ('TOPPADDING',(0,0),(-1,-1),0)]))
        pdf.story.append(pair)
        pdf.add('Planta esquemática, sem escala. X/Y: direções da verificação. Roxo: face do pilar (u0); vermelho: referência (u1); ocre: reduzido (u1*); verde: exterior (uout); azul: secção crítica.', 'caption')
    else:
        pdf.parameters(parameters)
    terms = r.get('beta_terms') or {}
    pdf.add(terms.get('method') or 'Coeficiente de majoração ainda não determinado.', 'caption')
    if terms.get('reference'):
        pdf.add('Referência do método: '+terms['reference']+'.', 'caption')
    if r['inputs'].get('beta_mode') == 'manual':
        pdf.add('Fundamentação do coeficiente: '+str(r['inputs'].get('beta_reference') or 'Por indicar'), 'caption')
    if r.get('opening_records'):
        pdf.add('Aberturas consideradas', 'heading')
        pdf.table(['Abertura','Centro X / Y\n(m)','Distância livre\n(m)','Influência'],
            [[o['id'],number(o['x'])+' / '+number(o['y']),number(o['distance_m']),
              'Deduzida do perímetro' if o['active'] else 'Fora da zona de influência'] for o in r['opening_records']], [.19,.30,.21,.30])
    sectors = r['inputs'].get('opening_sectors') or []
    if sectors:
        pdf.add('Setores ineficazes adicionais definidos manualmente: '+
                '; '.join(f'{number(a,1)}° a {number(b,1)}°' for a,b in sectors)+'.', 'caption')


def _reinforcement(pdf, r):
    rows = r.get('reinforcement_rows') or []
    if not rows:
        if r['status'] == 'PASS_WITHOUT':
            pdf.add('Dispensa-se armadura específica de punçoamento nos mecanismos avaliados. Mantêm-se as armaduras longitudinais e de integridade previstas no projeto.', 'caption')
        elif r['status'] == 'EDGE_DETAIL_PENDING':
            pdf.add('Armadura necessária - pormenor por definir', 'heading')
            pdf.parameters(value_rows(r,['Asw_sr_req','u_out_ef','r_out_face','dist_zona_armar']))
            pdf.add('Não foi aprovada uma distribuição de ramos. É necessária a verificação de cada contorno, dos espaçamentos e da amarração.')
        else:
            pdf.add('Não foi obtida uma solução de armadura aprovada. Os valores não calculados não representam armadura nula.')
        return
    pdf.story.append(CondPageBreak(180))
    pdf.add('Armadura de punçoamento proposta', 'heading')
    pdf.add('As fiadas são medidas a partir da face do pilar. A proposta só pode ser adotada quando as verificações e a pormenorização estiverem concluídas.')
    pdf.table(['Fiada','Distância à face\n(m)','Ramos × Ø\n(mm)','Área total\n(cm²)','Passo radial\n(m)','Passo tangencial máx.\n(m)'],
        [[x['row'],number(x['r']),f"{x['n_legs']} × {number(x['phi_mm'],0)}",number(x['Asw_m2'],2,1e4),
          number(x['sr']),number(x['st'])] for x in rows], [.09,.19,.17,.17,.17,.21])
    pdf.parameters(value_rows(r,['f_ywd_ef','Asw_sr_req','u_out_ef','r_out_face']))
    pdf.add('O mínimo de armadura é verificado por ramo, com os espaçamentos efetivos de cada fiada (9.11). A área total de uma fiada não substitui a área que atravessa cada contorno.', 'caption')
    pdf.table(['Fiada','Área por ramo\n(cm²)','Mínimo por ramo\n(cm²)','Resultado local'],
        [[x['row'],number(x['Asw_branch_provided_m2'],3,1e4),number(x['Asw_min_branch_m2'],3,1e4),
          'Verifica' if x['passed'] else 'Não verifica'] for x in rows], [.12,.25,.28,.35])
    families = [[x['row'], 'Aberto ao bordo' if f['kind']=='aberto_bordo' else 'Fechado',
                 number(f['Asw_m2'],2,1e4),number(f['Asw_required_m2'],2,1e4), 'Verifica' if f['passed'] else 'Não verifica']
                for x in rows for f in x.get('families',[])]
    if families:
        pdf.table(['Fiada','Contorno','Área eficaz\n(cm²)','Área requerida\n(cm²)','Resultado'],families,[.1,.23,.22,.23,.22])
    pdf.add('Amarração confirmada pelo projetista: '+number(r['inputs']['anchorage_confirmed'])+'.')
    if r.get('detail_checks'):
        pdf.table(['Condição de pormenorização','Verificação','Resultado'],
            [[c['name'], f"{number(c['value'])} {c['rule']} {number(c['limit'])} {c['unit']}"
              if c['id'] not in ('paths','families','radii') else 'Conferência da disposição dos ramos',
              'Verifica' if c['passed'] else 'Não verifica'] for c in r['detail_checks']], [.49,.31,.20])


def _footing(pdf, r):
    p=r['inputs']
    if not p['is_sapata']:
        return
    pdf.add('Geometria e reação da sapata', 'heading')
    if p['footing_shape']=='circular':
        pdf.parameters([('Diâmetro da sapata','D',number(p['footing_diameter']),'m')])
    else:
        pdf.parameters([('Dimensão da sapata em X','Bx',number(p['footing_bx']),'m'),
                        ('Dimensão da sapata em Y','By',number(p['footing_by']),'m')])
    pdf.parameters(value_rows(r,['soil_pressure_used_kpa','a_governing']))
    points=r.get('footing_scan') or []
    if points:
        peak=max(points,key=lambda p:p['ratio'])
        pdf.add(f"Foram avaliadas {len(points)} secções. Na secção condicionante, o perímetro é {number(peak['u'])} m, "
                f"a área de reação é {number(peak['area'])} m² e o esforço transverso reduzido é {number(peak['V_red'],2,.001)} kN.")


def case_pages(pdf, r, show_materials=True, shared_notes=()):
    pdf.state(r['badge'], r['conclusion'])
    if show_materials:
        pdf.add('Materiais e coeficientes de segurança','heading')
        pdf.parameters(material_rows(r))
    pdf.add('Geometria e armadura longitudinal','heading')
    pdf.parameters(geometry_rows(r))
    _longitudinal(pdf,r)
    _footing(pdf,r)
    # Avoid creating an almost empty page when a long name or extra inputs wrap.
    pdf.story.append(CondPageBreak(520))
    identity=' / '.join(str(r['inputs'].get(k) or '-') for k in ('support','combination'))
    pdf.add('Verificações - '+identity,'heading')
    _checks(pdf,r)
    _geometry(pdf,r)
    _reinforcement(pdf,r)
    notes=list(dict.fromkeys(n for n in r.get('notes',[]) if n and n not in shared_notes))
    if notes:
        pdf.add('Condições e observações','heading')
        for n in notes:
            pdf.add(n,'caption')


def export_case(r, path):
    emitted=datetime.now(timezone.utc).isoformat(timespec='seconds')
    pdf=MemoryPDF(path,'Verificação de punçoamento - memória de cálculo',r['version'],emitted)
    pdf.add('Verificação de punçoamento','title')
    pdf.add('Projeto: '+str(r['inputs'].get('project') or 'Por identificar'))
    pdf.add('Apoio: '+str(r['inputs'].get('support') or '-')+' | Combinação: '+str(r['inputs'].get('combination') or '-'))
    pdf.add(r['standard'],'caption')
    case_pages(pdf,r)
    pdf.build()


def export_collection(report,path):
    from .collection_reports import detail_combinations
    from .collection_workflow import PENDING_LABELS
    pdf=MemoryPDF(path,'Verificação de punçoamento - conjunto de ligações',report['version'],report['emitted_at'])
    snapshots=[e['snapshot'] for e in report['entries'] if e.get('snapshot')]
    common_materials=bool(snapshots) and all(material_rows(r)==material_rows(snapshots[0]) for r in snapshots)
    common_notes=[n for n in snapshots[0].get('notes',[]) if all(n in r.get('notes',[]) for r in snapshots)] if snapshots else []
    pdf.add('Verificação de punçoamento','title')
    pdf.add('Anexo à memória descritiva e justificativa','heading')
    pdf.add('Projeto: '+(' / '.join(report['projects']) or 'Por identificar'))
    pdf.add(report['standard'],'caption')
    pdf.add('Âmbito: '+_count(len(report['floor_order']), 'piso', 'pisos')+', '+
            _count(len(report['groups']), 'ligação', 'ligações')+' e '+
            _count(len(report['entries']), 'combinação incluída', 'combinações incluídas')+'.')
    pdf.add(report['scope'],'caption')
    pdf.add('Síntese dos resultados','heading')
    pdf.table(['Piso / apoio','Calculadas / total','Omitidas','Conclusão'],
        [[g['floor']+' / '+g['support'],f"{g['calculated_count']}/{g['total_count']}",g['omitted_count'],g['status']]
         for g in report['groups']], [.28,.22,.14,.36])
    if common_materials:
        pdf.add('Materiais comuns às ligações calculadas','heading')
        pdf.parameters(material_rows(snapshots[0]))
    pdf.add('Critérios de leitura','heading')
    pdf.add('Os esforços de cada combinação são concomitantes. A combinação condicionante é identificada separadamente para cada verificação.', 'caption')
    pdf.add('Utilização até 100 % satisfaz a verificação resistente apresentada. A conclusão da ligação inclui a cobertura das combinações e a conferência do pormenor de armadura.', 'caption')
    pdf.add('Conteúdo: '+('fichas de todas as combinações exportadas.' if report['full'] else
        'fichas das combinações condicionantes e dos casos que exigem conferência. As restantes combinações calculadas estão abrangidas pela síntese.'),'caption')
    if report.get('model_reference'):
        pdf.add('Referência do modelo: '+report['model_reference'],'caption')
    if common_notes:
        pdf.add('Hipóteses comuns','heading')
        for note in dict.fromkeys(common_notes):
            pdf.add(note,'caption')
    for group in report['groups']:
        items=[e for e in report['entries'] if (e['floor'],e['support'])==(group['floor'],group['support'])]
        pdf.story.append(PageBreak())
        pdf.add(group['floor']+' - '+group['support'],'title')
        pdf.add('Conclusão da ligação: '+group['status'],'heading')
        pdf.add(group['coverage']+'; '+_count(group['omitted_count'], 'combinação omitida', 'combinações omitidas')+'.', 'caption')
        category = group.get('group') or group.get('classification')
        if category:
            pdf.add('Grupo: '+str(category),'caption')
        if group['different_reinforcement_proposals']:
            pdf.state('Pormenor comum por conferir', 'Existem propostas de armadura distintas. É necessário conferir uma mesma disposição em todas as combinações; a maior área de aço, isoladamente, não resolve esta pendência.')
        pdf.table(['Verificação condicionante','Combinação','Utilização (%)'],
            [[g['name'],g['combination'],number(g['utilization'],1,100)] for g in group['governing'].values()], [.55,.25,.20])
        chosen=detail_combinations(items,group,report['full'])
        first=True
        for e in items:
            if not e.get('snapshot'):
                pdf.add(e['combination']+': '+PENDING_LABELS.get(e['status'],'Pendente')+'. '+(e.get('error') or ''),'caption')
                continue
            if e['combination'] not in chosen:
                continue
            if not first:
                pdf.story.append(PageBreak())
            first=False
            pdf.add('Combinação '+e['combination'],'heading')
            case_pages(pdf,e['snapshot'],not common_materials,common_notes)
    pdf.build()
