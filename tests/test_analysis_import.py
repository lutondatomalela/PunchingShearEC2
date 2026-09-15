"""Modelo schema from the supplied screenshots; independent joint references."""
from copy import deepcopy
import csv
import json
import math
from pathlib import Path

import pytest
from punching.table_import import Table, read_table, key, source_lines
from punching.analysis_import import (archive, restore, profile, split_key, automatic_layout,
    parse_bars, parse_nodes, prepare_analysis_table, all_records, members, member_role,
    build_joint, validate_candidate, SIGN_REFERENCE)
from punching.connections import ConnectionBook, initial_draft, adopt, provenance, validate_case, trace_lines
from Punching_EC2_GUI import DEFAULTS

HEADERS = ['Member/Node/Case','FX (kN)','MY (kNm)','MZ (kNm)',
           'AX (cm2)','IY (cm4)','IZ (cm4)','HY (cm)','HZ (cm)','Name','Story']


def row(member, node, combo, n, my, mz):
    return [f'{member}/ {node}/{combo}',n,my,mz,1750.,714583.33,91145.83,25.,70.,'P103', 'PISO 2' if member=='2' else 'PISO 3']


def bars():
    rows = [row('2','7460','101 (C)',1800,18,-24), row('2','51520','101 (C)',1820,15,-20),
            row('3','7460','101 (C)',1350,6,-8), row('3','90000','101 (C)',1330,10,-5),
            row('2','7460','102 (C)',1700,22,-31), row('2','51520','102 (C)',1720,19,-25),
            row('3','7460','102 (C)',1300,4,-5), row('3','90000','102 (C)',1280,9,-2)]
    return Table('Modelo_Pilares_Exemplo.csv','a'*64,'CSV',HEADERS,[(i+2,r) for i,r in enumerate(rows)],set())


def nodes():
    return Table('Modelo_Nos_Exemplo.csv','b'*64,'CSV',['Node','X (m)','Y (m)','Z (m)'],
                 [(2,['51520',0,0,0]), (3,['7460',0,0,3]), (4,['90000',0,0,6])],set())


def setup(**changes):
    data = dict(floor='PISO 2', support='P103', node='7460', below='2', above='3',
        upper_absent=False, below_axes={'x':'+Z','y':'+X'}, above_axes={'x':'+Z','y':'+X'},
        analysis_3d=True, same_combination=True, isolated_joint=True, at_joint=True,
        axes_confirmed=True, reference='Modelo didático 3D; eixos e nós conferidos.', combination='')
    data.update(changes); return data


def joint(table=None, options=None, coordinates=True):
    return build_joint([archive(table or bars())], options or setup(), archive(nodes()) if coordinates else None)


def test_screenshot_schema_compound_key_values_and_rectangular_properties():
    table=Table('screenshot_fixture.csv','c'*64,'CSV',HEADERS,[(2,row('2','7460','101 (C)','724,19','33,52','7,44')),
        (3,row('2','51520','101 (C)','706,80','-18,60','-29,58'))],set())
    data=parse_bars(table)
    assert profile(table.headers)=='analysis'
    assert [(r['member'],r['node'],r['combination']) for r in data]==[('2','7460','101 (C)'),('2','51520','101 (C)')]
    assert data[0]['values']['fx']==724.19 and data[1]['values']['my']==-18.60
    assert data[0]['section']['shape']=='retangular'
    assert data[0]['section']['hy']==pytest.approx(.25) and data[0]['section']['hz']==pytest.approx(.7)
    batch=prepare_analysis_table(table)
    assert not batch['loads'] and not batch['geometries']  # no VEd = 724.19 - 706.80


@pytest.mark.parametrize('text,expected', [(' 2 / 7460 / 101 (C) ',('2','7460','101 (C)')),
    ('002/0007460/ ELU 101 (C)',('002','0007460','ELU 101 (C)')),
    ('2/7460/101 (CQC+)',('2','7460','101 (CQC+)'))])
def test_compound_key_preserves_case_variant_and_identifiers(text,expected): assert split_key(text)==expected


@pytest.mark.parametrize('text',['2/7460','2/7460/','2/x/101','0/7460/101','2/0/101','max/7460/101','2.0/7460/101'])
def test_bad_compound_keys_are_not_guessed(text):
    with pytest.raises(ValueError):split_key(text)


def test_preamble_units_decimal_csv_utf16_and_semicolon(tmp_path):
    p=tmp_path/'analysis.csv';t=bars()
    with p.open('w',encoding='utf-16',newline='') as f:
        f.write('Resultados de barras\nModelo didático\n');w=csv.writer(f,delimiter=';');w.writerow(t.headers)
        for _,r in t.rows:w.writerow([str(x).replace('.',',') if isinstance(x,(int,float)) else x for x in r])
    layout=automatic_layout(p);assert layout['header_row']==3 and layout['delimiter']==';'
    table=read_table(p,**layout);values=parse_bars(table)
    assert values[0]['source']['row']==4 and values[0]['values']['fx']==1800


def test_tab_export_bom_and_uppercase_headers(tmp_path):
    p=tmp_path/'analysis.txt';t=bars()
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter='\t');w.writerow([h.upper() for h in t.headers]);w.writerows(r for _,r in t.rows)
    layout=automatic_layout(p);assert layout['delimiter']=='\t'
    assert len(parse_bars(read_table(p,**layout)))==8


def test_local_units_independent_each_column_and_unicode_powers():
    t=bars();t.headers=list(t.headers)
    changes={1:('FX (N)',1000),2:('MY [N.mm]',1e6),3:('MZ (kN.cm)',100),4:('AX (mm²)',100),7:('HY (mm)',10),8:('HZ (m)',.01)}
    for c,(h,scale) in changes.items():
        t.headers[c]=h
        for _,r in t.rows:r[c]*=scale
    assert joint(t)['loads'][key('PISO 2','P103','101 (C)')]['adopted']==pytest.approx({'V_Ed':450,'M_Edx':12,'M_Edy':16})


@pytest.mark.parametrize('change',['missing_unit','duplicate','missing_value','mixed_decimal','bad_grouping','formula','section_varies'])
def test_invalid_rows_block_the_whole_import(change):
    t=bars();t.headers=list(t.headers)
    if change=='missing_unit':t.headers[1]='FX'
    elif change=='duplicate':t.rows.append((10,deepcopy(t.rows[0][1])))
    elif change=='missing_value':t.rows[2][1][1]=''
    elif change=='mixed_decimal':t.rows[0][1][1]='1800.0';t.rows[1][1][1]='1820,0'
    elif change=='bad_grouping':t.rows[0][1][1]='18 00'
    elif change=='formula':t.formulas.add((2,1))
    elif change=='section_varies':t.rows[0][1][7]=30
    with pytest.raises(ValueError):parse_bars(t)


def test_valid_space_thousands_preserves_sign():
    t=bars();t.rows[0][1][1]='1\u00a0800,00';t.rows[0][1][2]='−18,00'
    values=parse_bars(t)[0]['values'];assert values['fx']==1800 and values['my']==-18


def test_inconsistent_hollow_section_is_not_assumed_solid():
    t=bars()
    for _,r in t.rows:r[4]=1000
    assert all(r['section'] is None for r in parse_bars(t))
    assert not joint(t)['geometries']


def test_solid_circular_section_independent_properties():
    t=bars()
    for _,r in t.rows:r[4:9]=[math.pi*40**2/4,math.pi*40**4/64,math.pi*40**4/64,40.,40.]
    assert parse_bars(t)[0]['section']['shape']=='circular'
    g=next(iter(joint(t)['geometries'].values()))['inputs'];assert g=={'pilar_forma':'circular','pilar_c1':.4,'pilar_c2':None}


def test_equilibrium_uses_one_common_node_and_same_combination():
    loads=joint()['loads'];a=loads[key('PISO 2','P103','101 (C)')];b=loads[key('PISO 2','P103','102 (C)')]
    # Independent free body: +1800 Z -1350 Z and joint couples (18,-24),(-6,+8).
    assert a['adopted']=={'V_Ed':450.,'M_Edx':12.,'M_Edy':16.}
    assert b['adopted']=={'V_Ed':400.,'M_Edx':18.,'M_Edy':26.}
    assert [r['node'] for r in a['records']]==['7460','7460']
    assert [r['endpoint'] for r in a['records']]==['end','begin']
    assert not any(r['node']=='51520' for r in a['records'])


def test_reverse_longitudinal_directions_and_rotate_transverse_axes():
    t=bars()
    for _,r in t.rows:r[2]=-r[2]
    data=joint(t,setup(below_axes={'x':'-Z','y':'+X'},above_axes={'x':'-Z','y':'+X'}))
    assert data['loads'][key('PISO 2','P103','101 (C)')]['adopted']=={'V_Ed':450.,'M_Edx':12.,'M_Edy':16.}
    t=bars()
    for _,r in t.rows:r[2],r[3]=r[3],-r[2]
    data=joint(t,setup(below_axes={'x':'+Z','y':'+Y'},above_axes={'x':'+Z','y':'+Y'}))
    assert data['loads'][key('PISO 2','P103','101 (C)')]['adopted']=={'V_Ed':450.,'M_Edx':12.,'M_Edy':16.}
    g=next(iter(data['geometries'].values()))['inputs'];assert g['pilar_c1']==pytest.approx(.7) and g['pilar_c2']==.25


def test_nodes_establish_top_base_without_number_or_row_order():
    records=parse_bars(bars());index=members(records);coords=parse_nodes(nodes())
    assert member_role('2','7460',index,coords)[0]=='below'
    assert member_role('2','51520',index,coords)[0]=='above'
    assert member_role('3','7460',index,coords)[0]=='above'
    assert member_role('2','7460',index,{})[0]==''


@pytest.mark.parametrize('changes',[{'below':'3','above':'2'}, {'below':'2','above':'2'}, {'node':'51520'},
    {'below_axes':{'x':'','y':'+X'}}, {'above_axes':{'x':'+Z','y':'30°'}}, {'analysis_3d':False},
    {'axes_confirmed':False}, {'at_joint':False}, {'same_combination':False}, {'isolated_joint':False}, {'reference':''}])
def test_unsupported_or_unconfirmed_joint_is_blocked(changes):
    with pytest.raises(ValueError):joint(options=setup(**changes))


def test_known_inclined_member_cannot_be_confirmed_away():
    n=nodes();n.rows[0][1][1]=.5
    with pytest.raises(ValueError,match='coordenadas'):build_joint([archive(bars())],setup(),archive(n))


def test_known_extra_member_or_upper_is_not_silently_discarded():
    with pytest.raises(ValueError,match='outras barras'):joint(options=setup(above='',upper_absent=True))


def test_missing_combination_is_pending_and_roof_needs_explicit_absence():
    t=bars();t.rows=[(i,r) for i,r in t.rows if not (r[0].startswith('3/') and '102 (C)' in r[0])]
    loads=joint(t)['loads'];assert loads[key('PISO 2','P103','101 (C)')]['adopted']['V_Ed']==450
    assert loads[key('PISO 2','P103','102 (C)')]['adopted'] is None
    validate_candidate(loads[key('PISO 2','P103','102 (C)')])
    t=bars();t.rows=[(i,r) for i,r in t.rows if r[0].startswith('2/')]
    assert all(r['adopted'] is None for r in joint(t,setup(above=''))['loads'].values())
    assert joint(t,setup(above='',upper_absent=True))['loads'][key('PISO 2','P103','101 (C)')]['adopted']['V_Ed']==1800


def test_uplift_not_abs_and_envelopes_remain_pending():
    t=bars();t.rows[0][1][1]=1000
    assert joint(t)['loads'][key('PISO 2','P103','101 (C)')]['adopted'] is None
    for _,r in t.rows:r[0]=r[0].replace('101 (C)','ELU max')
    assert joint(t)['loads'][key('PISO 2','P103','ELU max')]['adopted'] is None


def test_archive_roundtrip_rebuild_and_provenance_keep_original_source():
    b=ConnectionBook();b.merge(prepare_analysis_table(bars()));b.merge(prepare_analysis_table(nodes()));b.merge(joint())
    c=b.cases[key('PISO 2','P103','101 (C)')];adopt(c,'columns',initial_draft(DEFAULTS,c))
    restored=ConnectionBook.from_payload(json.loads(json.dumps(b.payload())),DEFAULTS)
    assert restored.payload()==json.loads(json.dumps(b.payload()))
    trace=provenance(c,c['draft']);text='\n'.join(trace_lines(trace))
    assert 'Member/Node/Case' in text and 'FXinf-FXsup' in text and SIGN_REFERENCE in text
    assert 'linha 2' in text and 'MX' not in c['candidates']['columns']['records'][0]['source']['raw']


@pytest.mark.parametrize('field',['adopted','axes','node'])
def test_saved_derived_analysis_actions_are_rebuilt_not_trusted(field):
    c=next(iter(joint()['loads'].values()))
    if field=='adopted':c['adopted']['V_Ed']=1
    elif field=='axes':c['analysis']['setup']['below_axes']['x']='-Z'
    else:c['analysis']['setup']['node']='51520'
    with pytest.raises(ValueError):validate_candidate(c)


def test_catalog_merge_is_atomic_and_preserves_old_project_compatibility():
    b=ConnectionBook();b.merge(prepare_analysis_table(bars()));before=b.payload()
    with pytest.raises(ValueError):b.merge(prepare_analysis_table(bars()))
    assert b.payload()==before
    old={'schema':'PunchingShearEC2.connections/1','cases':{},'geometries':{},'active':None}
    restored=ConnectionBook.from_payload(old,DEFAULTS).payload()
    assert restored['schema'].endswith('/3') and restored['cases']==old['cases'] and restored['geometries']==old['geometries']


def test_each_candidate_archives_only_relevant_cases_and_endpoint_nodes():
    data=joint()
    for c in data['loads'].values():
        assert sum(len(t['rows']) for t in c['analysis']['tables'])==4
        assert len(c['analysis']['nodes']['rows'])==3
        validate_candidate(json.loads(json.dumps(c)))


def test_xlsx_reader_recognizes_numeric_cells_and_rejects_mapped_formula(tmp_path):
    # Test fixture only; no user workbook is authored here.
    from openpyxl import Workbook
    t=bars();p=tmp_path/'analysis.xlsx';wb=Workbook();ws=wb.active;ws.title='Barras'
    ws.append(['Resultados de barras']);ws.append(t.headers)
    for _,r in t.rows:ws.append(r)
    wb.save(p);layout=automatic_layout(p,'Barras');assert layout['header_row']==2
    assert len(parse_bars(read_table(p,'Barras',**layout)))==8
    ws['B3']='=1800';wb.save(p)
    with pytest.raises(ValueError,match='XLSX'):parse_bars(read_table(p,'Barras',**layout))
