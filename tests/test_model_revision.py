"""Selection, source revision and preservation of completed project work."""
from copy import deepcopy
import json
import pytest

from test_analysis_import import bars, nodes
from test_model_workflow import book_model, filled_case, config, model
from punching.analysis_import import all_records, members, archive, parse_nodes, prepare_analysis_table
from punching.member_selection import select_members, alignment_members, compact_members
from punching.model_revision import prepare_revision
from punching.model_workflow import topology
from punching.connections import ConnectionBook, FORCE_KEYS, adopt, provenance
from punching.collection_workflow import calculate_case, cached_calculation, rotate_joint, sync_joint
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS


@pytest.mark.parametrize('text',[
    '110para113 115 118para123', '110-113 115 118-123',
    '110 111 112 113 115 118 119 120 121 122 123',
    '110 PARA 113;115,118 - 123', '110–113 115 118−123 110 115',
])
def test_requested_selection_forms_have_identical_members(text):
    wanted=list(map(str,[110,111,112,113,115,118,119,120,121,122,123]))
    assert select_members(text,wanted)==wanted
    assert compact_members(wanted)=='110-113 115 118-123'


@pytest.mark.parametrize('text',['','110-109','110para','110..113','110-113foo','110 114','0','-110','110.0','1-999999999','110para111para112'])
def test_invalid_and_missing_members_are_not_silently_selected(text):
    with pytest.raises(ValueError):select_members(text,['110','111','112','113'])


def test_member_identifiers_preserve_source_zeros_and_reject_ambiguity():
    assert select_members('2-3',['002','003'])==['002','003']
    assert compact_members(['002','003'])=='002 003'
    with pytest.raises(ValueError,match='ambígua'):select_members('2',['2','002'])


def test_alignment_follows_connected_vertical_members_only():
    index=members(all_records([archive(bars())]));coords=parse_nodes(nodes())
    # A disconnected segment with identical plan coordinates/name is not connected.
    index['4']=dict(index['2'],nodes={'100','101'})
    coords.update({'100':dict(x=0,y=0,z=9),'101':dict(x=0,y=0,z=12)})
    # A horizontal member at the same joint is outside a vertical alignment.
    index['5']=dict(index['2'],nodes={'7460','102'})
    coords['102']=dict(x=3,y=0,z=3)
    assert alignment_members(['2'],index,coords)==['2','3']
    assert alignment_members(['2','4'],index,coords)==['2','3','4']
    with pytest.raises(ValueError,match='geometria vertical'):alignment_members(['5'],index,coords)


def test_alignment_requires_coordinates_and_stops_on_ambiguity():
    index=members(all_records([archive(bars())]));coords=parse_nodes(nodes())
    with pytest.raises(ValueError,match='coordenadas'):alignment_members(['2'],index,{})
    index['4']=dict(index['3'],nodes=set(index['3']['nodes']))
    with pytest.raises(ValueError,match='ambígua'):alignment_members(['2'],index,coords)
    del coords['51520']
    with pytest.raises(ValueError,match='dois extremos'):alignment_members(['2'],index,coords)


def test_save_without_new_joints_preserves_fresh_results():
    book=book_model();filled_case(book)
    for case in book.cases.values():calculate_case(case,DEFAULTS)
    before=deepcopy(book.payload())
    proposed,batch=prepare_revision(book,book.model_setup['config'],[],DEFAULTS)
    assert proposed.payload()==before and book.payload()==before
    assert len(batch['revision_impact']['unchanged'])==2
    assert not batch['revision_impact']['added'] and not batch['revision_impact']['updated']
    assert all(cached_calculation(c)['snapshot'] for c in proposed.cases.values())
    restored=ConnectionBook.from_payload(json.loads(json.dumps(proposed.payload())),DEFAULTS)
    assert all(cached_calculation(c)['snapshot'] for c in restored.cases.values())


def test_axis_revision_rebuilds_only_affected_sources_and_survives_save():
    book=book_model();k=filled_case(book)
    # Also prepare the top joint, which uses only member 3.
    rows=topology(book.analysis_tables,book.analysis_nodes)
    for j in rows:j.update(enabled=j['node']=='90000',upper_absent=j['node']=='90000')
    book,batch=prepare_revision(book,config(),rows,DEFAULTS)
    for case in book.cases.values():calculate_case(case,DEFAULTS)
    old_top=deepcopy(book.cases[key('PISO 3','P103','101 (C)')])
    cfg=config(member_axes={'2':{'x':'+Z','y':'+Y'}})
    proposed,batch=prepare_revision(book,cfg,[],DEFAULTS)
    assert len(batch['revision_impact']['updated'])==2
    assert len(batch['revision_impact']['unchanged'])==2
    assert proposed.cases[key('PISO 3','P103','101 (C)')]==old_top
    c=proposed.cases[k]
    assert c['candidates']['columns']['adopted']=={'V_Ed':450.,'M_Edx':18.,'M_Edy':-26.}
    assert c['draft']['laje_d']=='0.2' and c['draft']['betão_fck']=='30'
    assert (float(c['draft']['pilar_c1']),float(c['draft']['pilar_c2']))==pytest.approx((.7,.25))
    assert cached_calculation(c) is None
    restored=ConnectionBook.from_payload(json.loads(json.dumps(proposed.payload())),DEFAULTS)
    assert restored.cases[k]['draft']==c['draft']
    assert cached_calculation(restored.cases[k]) is None


def test_revision_keeps_case_frame_auto_reinforcement_openings_and_groups():
    from punching.batch_workflow import bulk_edit,assign_group
    book=book_model();k=filled_case(book)
    bulk_edit(book,list(book.cases),{'long_mode':'automatic','long_h_mm':'250','long_cover_mm':'30',
        'long_x_extra_mm':'12','long_y_extra_mm':'16','long_x_spacing_mm':'200','long_y_spacing_mm':'200'},DEFAULTS)
    d=deepcopy(book.cases[k]['draft']);d.update(project='Projeto revisto',reinforcement_s0_m='0.10',reinforcement_sr_m='0.15',openings='[{"id":"A1","shape":"rectangular","x":1,"y":1,"width":0.2,"height":0.3}]')
    sync_joint(book,k,d,DEFAULTS);assign_group(book,list(book.cases),'Grupo A')
    rotate_joint(book,k,3,DEFAULTS)
    old=deepcopy(book.cases[k]);settings=deepcopy(book.batch_settings)
    proposed,batch=prepare_revision(book,config(member_axes={'3':{'x':'+Z','y':'-X'}}),[],DEFAULTS)
    c=proposed.cases[k]
    assert c['candidates']['columns']['frame']['turn']==3
    for name in old['draft']:
        if name not in {*FORCE_KEYS,'edge_perp_interior','corner_interior'}:assert c['draft'][name]==old['draft'][name]
    assert proposed.batch_settings==settings
    assert c['candidates']['columns']['adopted']=={'V_Ed':450.,'M_Edx':32.,'M_Edy':-24.}
    ConnectionBook.from_payload(json.loads(json.dumps(proposed.payload())),DEFAULTS)


def test_manual_geometry_and_manual_source_remain_explicit_exceptions():
    book=book_model();k=filled_case(book)
    d=deepcopy(book.cases[k]['draft']);d['pilar_c1']='0.4';sync_joint(book,k,d,DEFAULTS)
    d=deepcopy(book.cases[k]['draft']);d.update(V_Ed='333',M_Edx='1',M_Edy='2')
    adopt(book.cases[k],'manual',d,'Resultante local conferida no referencial do caso.')
    cfg=config(member_axes={'2':{'x':'+Z','y':'+Y'}})
    proposed,batch=prepare_revision(book,cfg,[],DEFAULTS)
    c=proposed.cases[k]
    assert c['draft']['pilar_c1']=='0.4' and c['choice']=='manual' and c['draft']['V_Ed']=='333'
    assert k in batch['revision_impact']['manual_geometry']
    assert provenance(c,c['draft'])['adopted']['V_Ed']==333
    ConnectionBook.from_payload(proposed.payload(),DEFAULTS)


def test_bad_force_edits_do_not_get_overwritten_by_axis_revision():
    book=book_model();k=filled_case(book);book.cases[k]['draft']['V_Ed']='999'
    before=deepcopy(book.payload())
    with pytest.raises(ValueError,match='alterados'):
        prepare_revision(book,config(member_axes={'3':{'x':'+Z','y':'-X'}}),[],DEFAULTS)
    assert book.payload()==before


def test_combination_extension_copies_common_data_without_losing_existing_work():
    book=ConnectionBook()
    for table in (bars(),nodes()):book.merge(prepare_analysis_table(table))
    book.merge(model(cfg=config(combinations='101')));k=filled_case(book)
    calculate_case(book.cases[k],DEFAULTS)
    before=deepcopy(book.cases[k])
    proposed,batch=prepare_revision(book,config(combinations='101-102'),[],DEFAULTS)
    assert len(batch['revision_impact']['added'])==1
    assert proposed.cases[k]==before
    added=proposed.cases[key('PISO 2','P103','102 (C)')]
    assert added['draft']['V_Ed']=='400' and added['draft']['laje_d']=='0.2'
    assert cached_calculation(added) is None
    ConnectionBook.from_payload(proposed.payload(),DEFAULTS)
    with pytest.raises(ValueError,match='retiraria combinações'):
        prepare_revision(proposed,config(combinations='101'),[],DEFAULTS)


def test_configuration_can_be_saved_before_any_joint_is_prepared():
    book=ConnectionBook()
    for t in (bars(),nodes()):book.merge(prepare_analysis_table(t))
    proposed,batch=prepare_revision(book,config(member_axes={'3':{'x':'+Z','y':'-Y'}}),[],DEFAULTS)
    assert not proposed.cases and not proposed.model_setup['joints']
    restored=ConnectionBook.from_payload(json.loads(json.dumps(proposed.payload())),DEFAULTS)
    assert restored.payload()==proposed.payload()
    restored.merge(model(cfg=proposed.model_setup['config']))
    assert len(restored.cases)==2


@pytest.mark.parametrize('reverse',[False,True])
def test_adding_combinations_while_revising_axes_keeps_one_shared_geometry(reverse):
    book=ConnectionBook();table=bars()
    if reverse:table.rows.reverse()
    for t in (table,nodes()):book.merge(prepare_analysis_table(t))
    book.merge(model(table=table,cfg=config(combinations='101')));k=filled_case(book)
    rotate_joint(book,k,1,DEFAULTS)
    cfg=config(combinations='101-102',member_axes={'2':{'x':'+Z','y':'+Y'}})
    proposed,batch=prepare_revision(book,cfg,[],DEFAULTS)
    assert len(batch['revision_impact']['added'])==1 and len(batch['revision_impact']['updated'])==1
    for c in proposed.cases.values():
        assert (float(c['draft']['pilar_c1']),float(c['draft']['pilar_c2']))==pytest.approx((.25,.7))
        assert c['draft']['laje_As_lx_cm2pm']=='12' and c['draft']['laje_As_ly_cm2pm']=='10'
        assert c['candidates']['columns']['frame']['turn']==1
    restored=ConnectionBook.from_payload(proposed.payload(),DEFAULTS)
    assert restored.payload()==proposed.payload()


def test_revision_merge_is_atomic_and_preserves_existing_joint_identity():
    book=book_model();before=deepcopy(book.payload())
    rows=topology(book.analysis_tables,book.analysis_nodes)
    for j in rows:
        j['enabled']=False
        if j['node']=='7460':j.update(enabled=True,floor='Nome acidental',below='3',above='2')
    _,batch=prepare_revision(book,config(member_axes={'3':{'x':'+Z','y':'+Y'}}),rows,DEFAULTS)
    book.merge(batch)
    assert len(book.cases)==2 and {c['floor'] for c in book.cases.values()}=={'PISO 2'}
    assert book.payload()!=before
    assert book.cases[key('PISO 2','P103','101 (C)')]['draft']['M_Edx']=='10'
    before=deepcopy(book.payload());bad=deepcopy(batch);bad['model_setup']['config']['member_axes']['999']={'x':'+Z','y':'+X'}
    with pytest.raises(ValueError,match='não encontrada'):book.merge(bad)
    assert book.payload()==before
