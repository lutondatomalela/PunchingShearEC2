"""Blank Modelo display names must not remove or misassociate structural data."""
from copy import deepcopy
import json

import pytest
from punching.analysis_import import (parse_bars, all_records, members, archive,
    prepare_analysis_table, build_joint, validate_candidate, name_summary, name_note,
    analysis_source_lines)
from punching.connections import ConnectionBook, adopt, initial_draft, provenance, trace_lines
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS
from test_analysis_import import bars, nodes, setup, joint


def unnamed():
    table = bars()
    for _, raw in table.rows: raw[9] = ''
    return table


def test_blank_names_keep_every_record_and_original_cell():
    table = unnamed(); original = deepcopy(table)
    records = parse_bars(table)
    assert table == original
    assert len(records) == 8 and set(members(records)) == {'2', '3'}
    assert {r['support'] for r in records} == {'Barra 2', 'Barra 3'}
    assert all(r['source']['raw']['Name'] == '' for r in records)
    assert all(r['name_resolution'] == {'method': 'member_id'} for r in records)
    assert '8 registos' in name_summary(records)[0]
    assert '2 barras' in name_summary(records)[0]
    assert joint(table)['loads'][key('PISO 2', 'P103', '101 (C)')]['adopted'] == {
        'V_Ed': 450., 'M_Edx': 12., 'M_Edy': 16.}


@pytest.mark.parametrize('blank', [None, '', '  ', '\t'])
def test_empty_name_forms_use_member_identity(blank):
    table = unnamed()
    for _, raw in table.rows: raw[9] = blank
    assert parse_bars(table)[0]['support'] == 'Barra 2'


def test_optional_name_header_absent_does_not_invent_a_raw_column():
    table = bars(); table.headers = table.headers[:9] + table.headers[10:]
    for _, raw in table.rows: del raw[9]
    records = parse_bars(table)
    assert len(records) == 8 and records[0]['support'] == 'Barra 2'
    assert 'Name' not in records[0]['source']['raw']


@pytest.mark.parametrize('invalid', [False, float('nan'), float('inf')])
def test_nonempty_invalid_names_are_not_treated_as_blanks(invalid):
    table = unnamed(); table.rows[0][1][9] = invalid
    with pytest.raises(ValueError): parse_bars(table)


def test_formula_in_name_and_missing_force_still_block_import():
    table = unnamed(); table.formulas.add((2, 9))
    with pytest.raises(ValueError, match='XLSX'): parse_bars(table)
    table.formulas.clear(); table.rows[0][1][1] = ''
    with pytest.raises(ValueError, match='FX'): parse_bars(table)


def test_partial_name_is_recovered_only_from_same_member_with_evidence():
    table = unnamed(); table.rows[4][1][9] = 'Pilar P02'
    records = parse_bars(table)
    assert {r['support'] for r in records if r['member'] == '2'} == {'Pilar P02'}
    assert {r['support'] for r in records if r['member'] == '3'} == {'Barra 3'}
    assert records[0]['name_resolution']['evidence']['row'] == 6
    assert 'linha 6' in name_note(records[0])
    assert 'name_resolution' not in records[4]
    assert records[0]['source']['raw']['Name'] == ''


def test_conflicting_explicit_names_are_not_resolved_by_row_order():
    table = bars(); table.rows[4][1][9] = 'Outro pilar'
    with pytest.raises(ValueError, match='nomes de pilar incompatíveis'): parse_bars(table)


@pytest.mark.parametrize('split_files', [False, True])
def test_name_evidence_outside_selected_combination_survives_compact_archive(split_files):
    table = unnamed(); table.rows[4][1][9] = 'Pilar P02'
    if split_files:
        later = deepcopy(table); later.file = 'Modelo_outras_combinacoes.csv'; later.sha256 = 'd'*64
        later.rows = later.rows[4:]; table.rows = table.rows[:4]
        tables = [archive(table), archive(later)]
    else: tables = [archive(table)]
    records = all_records(tables)
    assert records[0]['support'] == 'Pilar P02'
    batch = build_joint(tables, setup(support='Pilar P02', combination='101 (C)'), archive(nodes()))
    candidate = next(iter(batch['loads'].values()))
    retained = [i for t in candidate['analysis']['tables'] for i, _ in t['rows']]
    assert len(retained) == 5 and 6 in retained
    validate_candidate(json.loads(json.dumps(candidate)))
    book = ConnectionBook()
    for t in tables:
        from punching.analysis_import import restore
        book.merge(prepare_analysis_table(restore(t)))
    book.merge(batch)
    case = next(iter(book.cases.values()))
    adopt(case, 'columns', initial_draft(DEFAULTS, case))
    restored = ConnectionBook.from_payload(json.loads(json.dumps(book.payload())), DEFAULTS)
    assert restored.payload() == json.loads(json.dumps(book.payload()))
    text = '\n'.join(trace_lines(provenance(case, case['draft'])))
    assert 'Nome «Pilar P02» recuperado' in text and 'linha 6' in text
    assert 'Identificação=Barra 3' in text and 'Name=' in text


@pytest.mark.parametrize('label', ['118 (C) (CQC)', '119 (CQC+)', 'Sismo (srss)'])
def test_modal_combination_keeps_geometry_and_sources_without_derived_actions(label):
    table = unnamed()
    for _, raw in table.rows: raw[0] = raw[0].replace('102 (C)', label)
    batch = joint(table)
    static = batch['loads'][key('PISO 2', 'P103', '101 (C)')]
    modal = batch['loads'][key('PISO 2', 'P103', label)]
    assert static['adopted'] == {'V_Ed': 450., 'M_Edx': 12., 'M_Edy': 16.}
    assert modal['adopted'] is None and len(modal['records']) == 2
    assert all(r['joint_mx'] is None and r['joint_my'] is None for r in modal['records'])
    assert modal['records'][0]['values']['fx'] == 1700.
    assert modal['records'][1]['values']['fx'] == 1300.
    assert 'CQC/SRSS' in modal['issues'][0]
    assert batch['geometries'][key('PISO 2', 'P103')]['inputs']['pilar_c1'] == .25
    validate_candidate(json.loads(json.dumps(modal)))
    text = '\n'.join(analysis_source_lines(modal))
    assert 'Concomitância não estabelecida' in text and 'Resultante:' not in text
    assert 'Name não preenchido' in text
    book = ConnectionBook(); book.merge(batch)
    restored = ConnectionBook.from_payload(json.loads(json.dumps(book.payload())), DEFAULTS)
    assert len(restored.cases) == 2
    case = restored.cases[key('PISO 2', 'P103', label)]
    with pytest.raises(ValueError): adopt(case, 'columns', initial_draft(DEFAULTS, case))


def test_saved_modal_direct_equilibrium_result_is_rejected_explicitly():
    table = bars()
    for _, raw in table.rows: raw[0] = raw[0].replace('101 (C)', '118 (C) (CQC)')
    old = joint(table)['loads'][key('PISO 2', 'P103', '118 (C) (CQC)')]
    old['adopted'] = {'V_Ed': 450., 'M_Edx': 12., 'M_Edy': 16.}
    with pytest.raises(ValueError, match='CQC/SRSS por equilíbrio direto'): validate_candidate(old)
