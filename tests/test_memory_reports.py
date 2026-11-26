"""Preserve the engineering evidence while changing the PDF presentation."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from punching.core import PuncoamentoEC2
from punching.reports import export_pdf, export_xlsx, export_json, export_txt
from punching.collection_reports import build_report, detail_combinations, export_collection_pdf
from punching.collection_workflow import calculate_case, summaries
from punching.report_parameters import VALUE_NAMES
from test_reference_cases import run
from test_model_workflow import book_model, filled_case
from test_batch_workflow import many
from Punching_EC2_GUI import DEFAULTS


def pdf_text(path):
    return ' '.join(' '.join(p.extract_text() for p in PdfReader(path).pages).split())


def entry(combination, **changes):
    r = run(combination=combination, support='P01', **changes).snapshot()
    return dict(floor='Piso 1', support='P01', combination=combination,
                status=r['status'], snapshot=r, error='')


@pytest.mark.parametrize('load,anchorage,status', [
    (300000, False, 'PASS_WITHOUT'), (600000, True, 'PASS_WITH'),
    (600000, False, 'DETAIL_PENDING'), (1000000, False, 'FAIL_MAX'),
    (2000000, False, 'FAIL_U0'),
])
def test_pdf_preserves_result_and_values_without_internal_codes(tmp_path, load, anchorage, status):
    r = run(V_Ed=load, anchorage_confirmed=anchorage,
            project='Ensaio A & B <1>', support='P01').snapshot()
    assert r['status'] == status
    original = deepcopy(r)
    out = tmp_path/'report.pdf'
    export_pdf(r, out)
    text = pdf_text(out)
    assert r == original
    assert r['conclusion'] in text
    assert 'Ensaio A & B <1>' in text
    assert 'Resistência característica à compressão do betão' in text
    assert 'fck 30,0 MPa' in text
    assert f'{load/1000:.2f}'.replace('.', ',') in text
    for check in r['checks']:
        assert f"{check['demand']:.3f}".replace('.', ',') in text
        assert f"{100*check['utilization']:.1f}".replace('.', ',') in text
    assert r['input_hash'] not in text
    assert status not in text and 'ec2_643' not in text
    if status == 'DETAIL_PENDING':
        assert 'Amarração confirmada pelo projetista: Não.' in text
    if status.startswith('FAIL'):
        assert 'Não verifica' in text


def test_signed_concomitant_forces_are_not_replaced_by_an_envelope(tmp_path):
    r = run(V_Ed=123450, M_Edx=-45670, M_Edy=8910, combination='C017').snapshot()
    export_pdf(r, tmp_path/'signed.pdf')
    assert 'C017 123,45 -45,67 8,91' in pdf_text(tmp_path/'signed.pdf')


def test_pending_beta_is_not_a_zero_or_a_success(tmp_path):
    r = run(opening_sectors=[[-20, 20]]).snapshot()
    assert r['status'] == 'BETA_PENDING' and r['values']['beta'] is None
    export_pdf(r, tmp_path/'pending.pdf')
    text = pdf_text(tmp_path/'pending.pdf')
    assert 'Não existem verificações resistentes concluídas' in text
    assert 'Não calculado' in text and 'β POR FUNDAMENTAR' in text
    assert 'BETA_PENDING' not in text


def test_automatic_layers_are_readable_and_remain_in_audit_exports(tmp_path):
    layout = dict(h_mm=250, cover_mm=30, outer_axis='x', layer_gap_mm=0,
                  x=dict(base_mm=10, extra_mm=10, spacing_mm=200),
                  y=dict(base_mm=10, extra_mm=12, spacing_mm=200))
    r = run(longitudinal_layout=layout).snapshot()
    export_pdf(r, tmp_path/'auto.pdf')
    export_json(r, tmp_path/'auto.json')
    export_txt(r, tmp_path/'auto.txt')
    text = pdf_text(tmp_path/'auto.pdf')
    assert 'Ø10 // 200 + Ø10 // 200' in text
    assert 'Ø10 // 100' in text
    assert 'Espessura da laje' in text and 'Recobrimento' in text
    assert 'h_mm' not in text and 'base_mm' not in text
    assert json.loads((tmp_path/'auto.json').read_text(encoding='utf-8')) == json.loads(json.dumps(r))
    assert r['input_hash'][:16] in (tmp_path/'auto.txt').read_text(encoding='utf-8')


def test_condensed_selection_retains_pending_failures_and_distinct_geometry():
    items = [entry('C1', V_Ed=300000), entry('C2', V_Ed=200000),
             entry('C3', V_Ed=100000, pilar_c1=.5),
             entry('C4', V_Ed=600000), entry('C5', V_Ed=2000000)]
    group = summaries(items)[0]
    selected = detail_combinations(items, group, False)
    assert {'C3', 'C4', 'C5'} <= selected
    assert {g['combination'] for g in group['governing'].values()} <= selected
    assert 'C2' not in selected
    assert detail_combinations(items, group, True) == {'C1','C2','C3','C4','C5'}


def test_partial_collection_cannot_claim_all_combinations_pass(tmp_path):
    book = book_model()
    k = filled_case(book)
    calculate_case(book.cases[k], DEFAULTS)
    report = build_report(book)
    original = deepcopy(report)
    export_collection_pdf(report, tmp_path/'partial.pdf')
    text = pdf_text(tmp_path/'partial.pdf')
    assert report == original
    assert 'PARCIAL' in text and 'PENDENTE' in text
    assert '1/2 combinações calculadas; 1 combinação omitida.' in text
    assert '450,00 12,00 16,00' in text
    assert 'INPUT_PENDING' not in text


def test_tracking_report_with_no_calculation_is_explicit(tmp_path):
    report = build_report(many(), only_calculated=False)
    export_collection_pdf(report, tmp_path/'tracking.pdf')
    text = pdf_text(tmp_path/'tracking.pdf')
    assert 'POR CALCULAR' in text and 'PARCIAL' in text
    assert 'NOT_EVALUATED' not in text
    assert not any(e.get('snapshot') for e in report['entries'])


def test_different_passing_reinforcement_proposals_keep_common_detail_pending(tmp_path):
    from punching.version import VERSION, STANDARD
    items = [entry('C1', V_Ed=600000, anchorage_confirmed=True, reinforcement_diameter_mm=12),
             entry('C2', V_Ed=600000, anchorage_confirmed=True, reinforcement_diameter_mm=10)]
    assert all(e['status']=='PASS_WITH' for e in items)
    group = summaries(items)[0]
    assert group['status'] == 'PORMENOR COMUM POR CONFERIR'
    group.update(calculated_count=2, total_count=2, omitted_count=0, group='Interior',
                 coverage='2/2 combinações calculadas')
    report = dict(version=VERSION, standard=STANDARD, emitted_at='2026-11-26T10:00:00+00:00',
                  projects=['Ensaio'], full=False, floor_order=['Piso 1'], groups=[group],
                  entries=items, scope='Duas combinações calculadas.')
    export_collection_pdf(report, tmp_path/'common.pdf')
    text = pdf_text(tmp_path/'common.pdf')
    assert 'PORMENOR COMUM POR CONFERIR' in text
    assert 'Existem propostas de armadura distintas.' in text
    assert 'Combinação C1' in text and 'Combinação C2' in text
    assert 'PASS_WITH' not in text


def test_spreadsheet_parameters_keep_numeric_types_and_document_conversions(tmp_path):
    from openpyxl import load_workbook
    r = run(V_Ed=600000).snapshot()
    export_xlsx(r, tmp_path/'report.xlsx')
    ws = load_workbook(tmp_path/'report.xlsx')['Parametros']
    data = {row[1]: row for row in list(ws.values)[1:]}
    assert data['ρl'][2] == pytest.approx(.5)
    assert data['ρl'][3] == '%'
    assert data['Asw/sr,req'][2] == pytest.approx(r['values']['Asw_sr_req']*10000)
    assert data['Asw/sr,req'][3] == 'cm²/m'
    assert data['fcd'][0] == 'Resistência de cálculo à compressão do betão'


def test_all_public_example_values_have_names_and_pdf_exports(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for source in (root/'examples').glob('*.json'):
        data = json.loads(source.read_text(encoding='utf-8'))
        if 'laje_d' not in data:
            continue
        engine = PuncoamentoEC2(**data)
        engine.verificar_puncoamento()
        r = engine.snapshot()
        assert set(r['values']) <= VALUE_NAMES.keys()
        target = tmp_path/(source.stem+'.pdf')
        export_pdf(r, target)
        text = pdf_text(target)
        assert ' '.join(r['conclusion'].split()) in text
        assert r['input_hash'] not in text
