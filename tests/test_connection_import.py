"""Independent equilibrium references and data-loss/error boundaries."""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import pytest
from punching.table_import import (Table, ImportConfig, numeric, read_table, suggest_mapping,
    prepare_import, key, source_lines, comparison_lines)
from punching.connections import ConnectionBook, initial_draft, adopt, provenance, validate_case, trace_lines
from punching.connection_ui import write_json_atomic
from Punching_EC2_GUI import DEFAULTS

EXAMPLES = Path(__file__).resolve().parents[1]/'examples'/'importacao'


def config(mode='columns', **changes):
    data = dict(mode=mode, same_combination=True, axes_at_column=True, isolated_joint=True, full_connection=True)
    data.update(changes); return ImportConfig(**data)


def batch(name='esforcos_pilares.csv', mode='columns', **changes):
    t = read_table(EXAMPLES/name)
    return prepare_import(t, suggest_mapping(t, mode), config(mode, **changes))


def synthetic(rows, **kwargs):
    headers = ['piso','pilar','combinacao','barra','tramo','extremo','sem_superior','n','mx_no','my_no']
    table = Table('source.csv','a'*64,'CSV',headers,[(i+2, row) for i,row in enumerate(rows)],set())
    return prepare_import(table, suggest_mapping(table,'columns'), config(**kwargs))


def pair():
    return [['01','P01','ELU01','B1','inferior','topo','nao',1800,18,-24],
            ['01','P01','ELU01','B2','superior','base','nao',1350,-6,8]]


def test_signed_joint_equilibrium_and_engine_axes():
    result = synthetic(pair())['loads'][key('01','P01','ELU01')]
    assert result['adopted'] == {'V_Ed':450,'M_Edx':12,'M_Edy':16}
    # Independent reference: two upward/downward force vectors on the slab.
    # Their resultant can act at x=16/450, y=12/450: r cross F = (12,-16,0).
    assert result['adopted']['M_Edx']/450 == pytest.approx(12/450)
    assert result['adopted']['M_Edy']/450 == pytest.approx(16/450)
    assert 'Ninf-Nsup' in result['method']


def test_negative_compression_and_unit_conversion_do_not_flip_moments():
    rows=pair()
    for r in rows: r[7]*=-1000; r[8]*=1e6; r[9]*=1e6
    result=synthetic(rows,compression='negative',force_unit='N',moment_unit='N.mm')['loads'][key('01','P01','ELU01')]
    assert result['adopted']==pytest.approx({'V_Ed':450,'M_Edx':12,'M_Edy':16})


@pytest.mark.parametrize('absence,ready', [('nao',False),('',False),('sim',True)])
def test_missing_upper_is_not_automatically_roof(absence,ready):
    rows=pair()[:1];rows[0][6]=absence
    load=next(iter(synthetic(rows)['loads'].values()))
    assert (load['adopted'] is not None)==ready
    if ready: assert load['adopted']['V_Ed']==1800
    else: assert 'ausência física' in ' '.join(load['issues'])


def test_combinations_never_mix_or_take_independent_maxima():
    rows=pair(); rows[1][2]='ELU02'
    loads=synthetic(rows)['loads']
    assert len(loads)==2 and all(x['adopted'] is None for x in loads.values())
    loads=batch()['loads']
    assert loads[key('Piso 1','P01','ELU 01')]['adopted']['V_Ed']==450
    assert loads[key('Piso 1','P01','ELU 02')]['adopted']=={'V_Ed':400,'M_Edx':18,'M_Edy':26}


@pytest.mark.parametrize('change', ['duplicate','false_roof','same_member','uplift'])
def test_ambiguous_or_reversed_equilibrium_remains_pending(change):
    rows=pair()
    if change=='duplicate':rows.append(deepcopy(rows[0]))
    if change=='false_roof':rows[0][6]='sim'
    if change=='same_member':rows[1][3]='B1'
    if change=='uplift':rows[0][7]=1000
    load=next(iter(synthetic(rows)['loads'].values()))
    assert load['adopted'] is None and load['issues']


def test_wrong_column_end_fails_atomically():
    rows=pair();rows[0][5]='base'
    with pytest.raises(ValueError,match='topo'): synthetic(rows)


@pytest.mark.parametrize('declaration', ['same_combination','axes_at_column','isolated_joint'])
def test_column_scope_must_be_declared(declaration):
    with pytest.raises(ValueError):synthetic(pair(),**{declaration:False})


def test_resultants_require_full_connection_and_explicit_sign_frame():
    with pytest.raises(ValueError,match='completa'):batch('resultantes_ligacao.csv','resultants',full_connection=False)
    values=batch('resultantes_ligacao.csv','resultants',resultant_convention='vector')['loads'][key('Piso 1','P01','ELU 01')]['adopted']
    assert values=={'V_Ed':450,'M_Edx':12,'M_Edy':-16}


@pytest.mark.parametrize('value', ['',None,True,'NaN','Infinity','1e500','1 000','1,000.0','1.000,0','=1+2'])
def test_invalid_numeric_never_zero(value):
    with pytest.raises(ValueError): numeric(value,'N')


def test_blank_moment_is_not_zero():
    rows=pair();rows[1][8]=''
    with pytest.raises(ValueError,match='Linha 3'):synthetic(rows)


def test_utf16_tab_decimal_comma_and_text_identifiers(tmp_path):
    p=tmp_path/'export.csv';p.write_text('piso\tpilar\tforma\tc1\tc2\n01\t0007\tretangular\t400,0\t600,0\n',encoding='utf-16')
    t=read_table(p); b=prepare_import(t,suggest_mapping(t,'geometry'),config('geometry',decimal=',',length_unit='mm'))
    g=b['geometries'][key('01','0007')]
    assert g['inputs']=={'pilar_forma':'retangular','pilar_c1':.4,'pilar_c2':.6}
    assert g['source']['row']==2 and len(g['source']['sha256'])==64


def test_custom_header_mapping_with_preamble(tmp_path):
    p=tmp_path/'model.csv';p.write_text('Relatorio\nNivel;Elemento;Tipo;Lado A;Lado B\nP1;C1;retangular;30;50\n')
    t=read_table(p,header_row=2)
    m=dict(floor='Nivel',support='Elemento',shape='Tipo',c1='Lado A',c2='Lado B')
    g=next(iter(prepare_import(t,m,config('geometry',length_unit='cm'))['geometries'].values()))
    assert g['inputs']['pilar_c2']==.5 and g['source']['row']==3


@pytest.mark.parametrize('contents', ['a;a\n1;2\n','a;;c\n1;2;3\n','a;b\n1;2;3\n'])
def test_bad_headers_or_extra_cells_rejected(tmp_path,contents):
    p=tmp_path/'bad.csv';p.write_text(contents)
    with pytest.raises(ValueError):read_table(p,delimiter=';')


def test_mapping_cannot_use_same_column_twice():
    t=read_table(EXAMPLES/'geometria_pilares.csv');m=suggest_mapping(t,'geometry');m['c2']=m['c1']
    with pytest.raises(ValueError,match='uma grandeza'):prepare_import(t,m,config('geometry'))


def test_scalar_slab_results_are_not_aliased_to_resultants(tmp_path):
    p=tmp_path/'slab.csv';p.write_text('piso;pilar;combinacao;Qx;Qy;Mxx;Myy\nP1;P1;ELU1;5;6;7;8\n')
    t=read_table(p);m=suggest_mapping(t,'resultants')
    assert not any(m[k] for k in ('v','mx','my'))
    with pytest.raises(ValueError,match='obrigatórios'):prepare_import(t,m,config('resultants'))


def filled(case):
    draft=initial_draft(DEFAULTS,case)
    draft.update(laje_d='0.2',laje_As_lx_cm2pm='10',laje_As_ly_cm2pm='10',betão_fck='30',pilar_tipo='interior',pilar_c1='0.4',pilar_c2='0.4')
    return draft


def book():
    b=ConnectionBook();b.merge(batch('geometria_pilares.csv','geometry'));b.merge(batch());b.merge(batch('resultantes_ligacao.csv','resultants'));return b


def test_matching_by_floor_pillar_combination_retains_sources_and_difference():
    b=book();assert len(b.cases)==4
    c=b.cases[key('Piso 1','P01','ELU 02')]
    assert set(c['candidates'])=={'columns','resultants'}
    assert 'V_Ed: +5' in comparison_lines(c['candidates'])[0]
    assert c['choice']=='' and c['draft'] is None
    d=filled(c);adopt(c,'columns',d)
    trace=provenance(c,c['draft']);assert trace['adopted']['V_Ed']==400
    assert 'não adotada' in '\n'.join(trace_lines(trace))


def test_new_case_requires_slab_fields_and_has_no_default_300kN():
    c=next(iter(book().cases.values()));d=initial_draft(DEFAULTS,c)
    assert all(d[k]=='' for k in ('laje_d','laje_As_lx_cm2pm','pilar_tipo','V_Ed','M_Edx','M_Edy'))


def test_duplicate_import_cannot_replace_completed_draft():
    b=book();c=b.cases[key('Piso 1','P01','ELU 01')];adopt(c,'columns',filled(c));before=b.payload()
    with pytest.raises(ValueError,match='já existe'):b.merge(batch())
    assert b.payload()==before


def test_manual_override_retains_original_forces_and_reference():
    c=book().cases[key('Piso 1','P01','ELU 01')];adopt(c,'columns',filled(c));d=deepcopy(c['draft']);d['V_Ed']='465'
    with pytest.raises(ValueError,match='alterados'):provenance(c,d)
    with pytest.raises(ValueError,match='fundamentação'):adopt(c,'manual',d)
    adopt(c,'manual',d,'Resultante revista na análise global, ELU 01.')
    trace=provenance(c,c['draft'])
    assert trace['adopted']['V_Ed']==465 and trace['candidates']['columns']['adopted']['V_Ed']==450


def test_imported_combination_cannot_be_relabelled_silently():
    c=book().cases[key('Piso 1','P01','ELU 01')];adopt(c,'columns',filled(c));c['draft']['combination']='ELU99'
    with pytest.raises(ValueError,match='combinação'):provenance(c,c['draft'])


def test_missing_geometry_can_be_imported_after_forces():
    b=ConnectionBook();b.merge(batch());c=b.cases[key('Piso 1','P01','ELU 01')];c['draft']=initial_draft(DEFAULTS,c)
    assert c['draft']['pilar_c1']==''
    b.merge(batch('geometria_pilares.csv','geometry'));c=b.cases[key('Piso 1','P01','ELU 01')]
    assert float(c['draft']['pilar_c1'])==.4


def test_project_round_trip_preserves_unfinished_drafts_and_validates_derived_loads(tmp_path):
    b=book();ckey=key('Piso 1','P01','ELU 01');c=b.cases[ckey];adopt(c,'columns',filled(c));c['draft']['laje_d']='0,';b.active=ckey
    path=tmp_path/'project.json';write_json_atomic(path,b.payload())
    restored=ConnectionBook.from_payload(json.loads(path.read_text(encoding='utf-8')),DEFAULTS)
    assert restored.payload()==b.payload()
    broken=json.loads(path.read_text(encoding='utf-8'));broken['cases'][ckey]['candidates']['columns']['adopted']['V_Ed']=200
    with pytest.raises(ValueError,match='origem'):ConnectionBook.from_payload(broken,DEFAULTS)


def test_atomic_save_does_not_truncate_previous_file_on_error(tmp_path):
    path=tmp_path/'project.json';path.write_text('original')
    with pytest.raises(ValueError):write_json_atomic(path,{'value':float('nan')})
    assert path.read_text(encoding='utf-8')=='original'


@pytest.mark.parametrize('sheet,name,mode', [('Geometria','geometria_pilares.csv','geometry'),('Tramos','esforcos_pilares.csv','columns'),('Resultantes','resultantes_ligacao.csv','resultants')])
def test_xlsx_template_agrees_with_csv_and_preserves_source_rows(sheet,name,mode):
    t=read_table(EXAMPLES/'Exemplo_importacao.xlsx',sheet=sheet)
    imported=prepare_import(t,suggest_mapping(t,mode),config(mode))
    original=batch(name,mode)
    assert imported['row_count']==original['row_count']
    assert {k:g['inputs'] for k,g in imported['geometries'].items()}=={k:g['inputs'] for k,g in original['geometries'].items()}
    assert {k:g['adopted'] for k,g in imported['loads'].items()}=={k:g['adopted'] for k,g in original['loads'].items()}


def test_xlsx_formulas_cannot_supply_imported_actions():
    t=read_table(EXAMPLES/'Exemplo_importacao.xlsx',sheet='Tramos');t.formulas.add((2,7))
    with pytest.raises(ValueError,match='fórmula'):prepare_import(t,suggest_mapping(t,'columns'),config())
