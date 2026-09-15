from copy import deepcopy
import json
import pytest

from test_analysis_import import bars, nodes, setup
from punching.analysis_import import archive, prepare_analysis_table
from punching.model_workflow import (topology, prepare_model, frame_candidate,
    validate_frame, rotate_forces, combo_filter, FRAME_ADAPTER)
from punching.connections import ConnectionBook, initial_draft, adopt, provenance
from punching.collection_workflow import (rotate_joint, sync_joint, calculate_case,
    cached_calculation, summaries, group_keys)
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS


def config(**changes):
    data=setup();data={k:data[k] for k in ('analysis_3d','same_combination','isolated_joint','at_joint','axes_confirmed','reference')}
    data.update(axes={'x':'+Z','y':'+X'},member_axes={},combinations='')
    data.update(changes);return data


def model(table=None, coords=None, cfg=None):
    table=table or bars();coords=coords or nodes()
    tables=[archive(table)];nt=archive(coords)
    return prepare_model(tables,nt,cfg or config(),topology(tables,nt))


def book_model(table=None):
    table=table or bars();b=ConnectionBook()
    b.merge(prepare_analysis_table(table));b.merge(prepare_analysis_table(nodes()));b.merge(model(table))
    return b


def filled_case(book):
    k=key('PISO 2','P103','101 (C)');c=book.cases[k]
    d=deepcopy(c['draft']);d.update(pilar_tipo='interior',laje_d='0.2',laje_As_lx_cm2pm='10',laje_As_ly_cm2pm='12',betão_fck='30')
    sync_joint(book,k,d,DEFAULTS);return k


def test_topology_uses_coordinates_and_shared_nodes_without_order_assumptions():
    t=bars();t.rows.reverse();n=nodes();n.rows.reverse()
    found=topology([archive(t)],archive(n));active=[j for j in found if j['enabled']]
    assert len(active)==1 and active[0]['node']=='7460'
    assert active[0]['below']=='2' and active[0]['above']=='3'
    assert {j['node'] for j in found if not j['enabled']}=={'51520','90000'}
    assert not any(j['enabled'] for j in topology([archive(t)]))


def test_model_prepares_and_adopts_matching_combinations_but_leaves_slab_blank():
    b=book_model();assert len(b.cases)==2
    c=b.cases[key('PISO 2','P103','101 (C)')]
    assert c['choice']=='columns' and c['draft']['V_Ed']=='450'
    assert c['draft']['laje_d']=='' and c['draft']['pilar_tipo']==''
    assert c['candidates']['columns']['adapter']==FRAME_ADAPTER
    entry=calculate_case(c,DEFAULTS)
    assert entry['status']=='INPUT_PENDING'
    assert entry['actions']=={'V_Ed':450.,'M_Edx':12.,'M_Edy':16.}


def test_selected_combination_absent_from_both_members_cannot_disappear_silently():
    t=bars()
    for _,raw in t.rows:
        if '102 (C)' in raw[0]:
            fields=raw[0].split('/');fields[0]=str(int(fields[0])+10)
            fields[1]=str(int(fields[1])+100000);raw[0]='/'.join(fields)
    with pytest.raises(ValueError,match='faltam inteiramente.*102'):
        model(table=t)


@pytest.mark.parametrize('turn,expected',[(0,(12,16)),(1,(-16,12)),(2,(-12,-16)),(3,(16,-12))])
def test_cardinal_rotation_matches_independent_node_moment_reference(turn,expected):
    candidate=next(iter(model()['loads'].values()))
    rotated=frame_candidate(candidate,turn);validate_frame(rotated)
    assert rotated['adopted']=={'V_Ed':450.,'M_Edx':expected[0],'M_Edy':expected[1]}


def test_rotation_preserves_sources_rotates_geometry_reinforcement_and_openings():
    b=book_model();k=filled_case(b);d=deepcopy(b.cases[k]['draft'])
    d.update(laje_dx='0.19',laje_dy='0.21',openings=json.dumps([{'id':'A1','shape':'rectangular','x':.9,'y':-.4,'width':.2,'height':.3}]),opening_sectors='10;20')
    sync_joint(b,k,d,DEFAULTS);before=deepcopy(b.cases[k]['candidates']['columns']['frame']['base'])
    rotate_joint(b,k,1,DEFAULTS)
    d=b.cases[k]['draft'];assert float(d['pilar_c1'])==pytest.approx(.7) and float(d['pilar_c2'])==.25
    assert (d['laje_dx'],d['laje_dy'],d['laje_As_lx_cm2pm'],d['laje_As_ly_cm2pm'])==('0.21','0.19','12','10')
    opening=json.loads(d['openings'])[0]
    assert (opening['x'],opening['y'],opening['width'],opening['height'])==(-.4,-.9,.3,.2)
    assert d['opening_sectors']=='-80;-70'
    assert b.cases[k]['candidates']['columns']['frame']['base']==before
    assert b.cases[k]['draft']['M_Edx']=='-16'
    assert b.cases[key('PISO 2','P103','102 (C)')]['draft']['M_Edx']=='-26'
    rotate_joint(b,k,0,DEFAULTS)
    assert b.cases[k]['draft']['M_Edx']=='12' and json.loads(b.cases[k]['draft']['openings'])[0]['x']==.9


def test_rotation_does_not_mask_manually_edited_forces_and_is_atomic():
    b=book_model();k=filled_case(b);b.cases[k]['draft']['V_Ed']='1';before=deepcopy(b.payload())
    with pytest.raises(ValueError,match='alterados'):rotate_joint(b,k,1,DEFAULTS)
    assert b.payload()==before


def test_schema_two_compresses_model_sources_and_rebuilds_rotated_cases():
    b=book_model();k=filled_case(b);rotate_joint(b,k,1,DEFAULTS)
    payload=b.payload();assert payload['schema'].endswith('/3')
    assert payload['cases'][k]['candidates']['columns']['adapter']=='Modelo.model-ref/1'
    restored=ConnectionBook.from_payload(json.loads(json.dumps(payload)),DEFAULTS)
    assert restored.payload()==json.loads(json.dumps(payload))
    assert restored.cases[k]['draft']['M_Edx']=='-16'
    validate_frame(restored.cases[k]['candidates']['columns'])
    # Individually saved cases carry full proof, independent of the collection.
    from punching.connections import validate_case
    validate_case(restored.cases[k],DEFAULTS)


def test_common_data_changes_invalidate_other_combinations_but_keep_their_forces():
    b=book_model();k=filled_case(b);other=key('PISO 2','P103','102 (C)')
    assert calculate_case(b.cases[other],DEFAULTS)['snapshot']
    assert cached_calculation(b.cases[other])
    d=deepcopy(b.cases[k]['draft']);d['laje_d']='0.25';sync_joint(b,k,d,DEFAULTS)
    assert b.cases[other]['draft']['laje_d']=='0.25' and b.cases[other]['draft']['V_Ed']=='400'
    assert cached_calculation(b.cases[other]) is None


def test_modal_entries_are_kept_pending_and_never_declared_successful():
    t=bars()
    for _,r in t.rows:r[0]=r[0].replace('102 (C)','118 (C) (CQC)')
    b=book_model(t);filled_case(b)
    entries=[calculate_case(c,DEFAULTS) for c in b.cases.values()]
    assert {e['status'] for e in entries}=={'PASS_WITHOUT','FORCES_PENDING'}
    summary=summaries(entries)[0];assert summary['status']=='PENDENTE' and summary['pending']==1
    assert 'u0' in summary['governing']


def test_roof_requires_explicit_absence_and_base_is_not_a_roof():
    tables=[archive(bars())];nt=archive(nodes());joints=topology(tables,nt)
    for j in joints:j['enabled']=False
    roof=next(j for j in joints if j['node']=='90000');roof['enabled']=True
    pending=prepare_model(tables,nt,config(),joints)
    assert all(c['adopted'] is None for c in pending['loads'].values())
    roof['upper_absent']=True
    ready=prepare_model(tables,nt,config(),joints)
    assert next(iter(ready['loads'].values()))['adopted']['V_Ed']==1330


def test_explicit_manual_topology_without_coordinates_uses_confirmed_roles():
    joints=topology([archive(bars())]);j=next(j for j in joints if j['node']=='7460')
    j.update(enabled=True,below='2',above='3',floor='Piso confirmado')
    batch=prepare_model([archive(bars())],None,config(),joints)
    assert next(iter(batch['loads'].values()))['adopted']['V_Ed']==450


@pytest.mark.parametrize('change',[{'axes':{'x':'','y':'+X'}},{'axes_confirmed':False},{'reference':''},{'member_axes':{'999':{'x':'+Z','y':'+X'}}}])
def test_invalid_model_configuration_is_blocked(change):
    with pytest.raises(ValueError):model(cfg=config(**change))


def test_combination_filter_preserves_labels_and_rejects_missing_numbers():
    labels={'101 (C)','102 (C)','118 (C) (CQC)'}
    assert combo_filter('101-102',labels)=={'101 (C)','102 (C)'}
    assert combo_filter('118',labels)=={'118 (C) (CQC)'}
    with pytest.raises(ValueError):combo_filter('101-103',labels)


def test_axes_exception_applies_to_the_specified_member_only():
    batch=model(cfg=config(member_axes={'3':{'x':'+Z','y':'+Y'}}))
    c=batch['loads'][key('PISO 2','P103','101 (C)')]
    # Below: (Mx,My)=(18,-24); above action=(-8,-6) in model coordinates.
    assert c['adopted']=={'V_Ed':450.,'M_Edx':10.,'M_Edy':30.}


def test_schema_rejects_changed_node_frame_and_inconsistent_common_inputs():
    b=book_model();k=filled_case(b)
    for change in ('node','turn','common','missing_combo','geometry'):
        data=b.payload();case=data['cases'][k]
        if change=='node':case['candidates']['columns']['node']='999'
        elif change=='turn':case['candidates']['columns']['turn']=True
        elif change=='common':case['draft']['laje_d']='0.5'
        elif change=='missing_combo':del data['cases'][k]
        else:data['geometries'][key('PISO 2','P103')]['inputs']['pilar_c1']=1
        with pytest.raises(ValueError):ConnectionBook.from_payload(data,DEFAULTS)


def test_source_and_axis_sign_disagreement_cannot_be_exported_as_success():
    b=book_model();k=filled_case(b);rotate_joint(b,k,1,DEFAULTS)
    c=b.cases[k];c['draft']['pilar_tipo']='bordo';c['draft']['edge_perp_interior']=True
    assert calculate_case(c,DEFAULTS)['snapshot'] is None
    c['draft']['edge_perp_interior']=False
    c['candidates']['columns']['adopted']['V_Ed']=1
    c['draft']['V_Ed']='1'
    assert calculate_case(c,DEFAULTS)['snapshot'] is None


def test_reporting_requires_fresh_calculations_and_preserves_pending_cases(tmp_path):
    from punching.collection_reports import build_report,export_collection_json,export_collection_txt,export_collection_pdf
    t=bars()
    for _,r in t.rows:r[0]=r[0].replace('102 (C)','118 (C) (CQC)')
    b=book_model(t);k=filled_case(b)
    with pytest.raises(ValueError,match='atualizados'):build_report(b)
    for c in b.cases.values():calculate_case(c,DEFAULTS)
    report=build_report(b,full=True,only_calculated=False);assert report['groups'][0]['status']=='PARCIAL — PENDENTE'
    for ext,writer in [('json',export_collection_json),('txt',export_collection_txt),('pdf',export_collection_pdf)]:writer(report,tmp_path/('conjunto.'+ext))
    loaded=json.loads((tmp_path/'conjunto.json').read_text());assert len(loaded['entries'])==2
    assert loaded['entries'][0]['snapshot']['load_trace']['adopted']['V_Ed']==450
    assert loaded['entries'][1]['snapshot'] is None
    assert 'CQC/SRSS' in (tmp_path/'conjunto.txt').read_text()
    b.cases[k]['draft']['laje_d']='0.5'
    with pytest.raises(ValueError,match='atualizados'):build_report(b)


def test_governing_is_selected_by_verification_without_artificial_force_envelope():
    entries=[]
    for combo,n,util0,util1 in [('A',450,.5,.9),('B',400,.8,.7)]:
        entries.append({'floor':'P1','support':'P01','combination':combo,'status':'PASS_WITHOUT','error':'',
            'snapshot':{'checks':[{'id':'u0','name':'Face','utilization':util0},{'id':'u1','name':'Contorno','utilization':util1}],
                        'reinforcement_rows':[],'values':{'V_Ed':n}}})
    s=summaries(entries)[0]
    assert s['governing']['u0']['combination']=='B' and s['governing']['u1']['combination']=='A'
    assert s['status']=='VERIFICA'


def test_multiple_distinct_reinforcement_proposals_are_not_a_single_verified_detail():
    entries=[]
    for combo,radius in [('A',.1),('B',.12)]:
        entries.append({'floor':'P1','support':'P01','combination':combo,'status':'PASS_WITH','error':'',
            'snapshot':{'checks':[],'reinforcement_rows':[{'r':radius,'sr':.15,'phi_mm':10,'n_legs':8,'coordinates':[]}],'values':{}}})
    s=summaries(entries)[0]
    assert s['status']=='PORMENOR COMUM POR CONFERIR'
    assert s['different_reinforcement_proposals']
