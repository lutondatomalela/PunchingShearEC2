from copy import deepcopy
from pathlib import Path
import json
import pytest
from punching.batch_workflow import (bulk_edit, assign_group, named_group, classification, seed_case,
    representatives, save_template, validate_settings, remove_group)
from punching.connections import ConnectionBook, provenance
from punching.collection_workflow import calculate_case, cached_calculation, rotate_joint, sync_joint, turn_of
from punching.collection_reports import build_report, is_calculated, export_collection_json, export_collection_pdf, export_collection_txt
from punching.table_import import key
from punching.model_workflow import rotate_forces
from Punching_EC2_GUI import DEFAULTS
from test_model_workflow import book_model, filled_case

DEMO=Path(__file__).resolve().parents[1]/'examples/importacao/Modelo_Ligacoes.json'


def many():
    b=ConnectionBook.from_payload(json.loads(DEMO.read_text()),DEFAULTS)
    return b


def ready(b,keys=None):
    bulk_edit(b,keys or list(b.cases),dict(project='Projeto de ensaio',pilar_tipo='interior',laje_d='.25',
        laje_As_lx_cm2pm='12',laje_As_ly_cm2pm='14',betão_fck='30'),DEFAULTS,only_empty=False)


def test_selection_expands_combinations_but_never_other_floors_or_pillars():
    b=many();target=key('Piso 1','P01','201 (C)');before=deepcopy(b.cases)
    changed=bulk_edit(b,[target],{'betão_fck':'35'},DEFAULTS)
    assert changed==1
    for k,c in b.cases.items():
        if (c['floor'],c['support'])==('Piso 1','P01'):assert c['draft']['betão_fck']=='35'
        else:assert c==before[k]
        assert c['candidates']==before[k]['candidates']
        assert c['draft']['V_Ed']==before[k]['draft']['V_Ed']


def test_only_empty_preserves_pillar_exceptions_update_changes_only_selected_fields():
    b=many();reps=representatives(b,list(b.cases));a,z=reps[:2]
    bulk_edit(b,[a],{'betão_fck':'40','reinforcement_s0_m':'.08'},DEFAULTS)
    bulk_edit(b,[a,z],{'betão_fck':'30','reinforcement_s0_m':'.09'},DEFAULTS)
    assert b.cases[a]['draft']['betão_fck']=='40' and b.cases[a]['draft']['reinforcement_s0_m']=='.08'
    assert b.cases[z]['draft']['betão_fck']=='30'
    bulk_edit(b,[a],{'betão_fck':'35'},DEFAULTS,only_empty=False)
    assert b.cases[a]['draft']['betão_fck']=='35' and b.cases[a]['draft']['reinforcement_s0_m']=='.08'


def test_common_templates_hierarchy_and_automatic_spacing_survive_reopen():
    b=many();k=next(iter(b.cases));c=b.cases[k];c['user_edited']=False
    assign_group(b,[k],'Bordo esquerdo')
    save_template(b,'project','',{'project':'Projeto comum','betão_fck':'30','reinforcement_s0_m':'','reinforcement_sr_m':'.12'})
    save_template(b,'floor',c['floor'],{'betão_fck':'35','laje_d':'.22'})
    save_template(b,'group','Bordo esquerdo',{'betão_fck':'40','pilar_tipo':'bordo'})
    restored=ConnectionBook.from_payload(json.loads(json.dumps(b.payload())),DEFAULTS)
    draft=seed_case(restored,restored.cases[k],DEFAULTS)
    assert (draft['project'],draft['betão_fck'],draft['laje_d'],draft['reinforcement_s0_m'],draft['reinforcement_sr_m'])==('Projeto comum','40','.22','','.12')
    restored.cases[k]['user_edited']=True
    assert seed_case(restored,restored.cases[k],DEFAULTS)==restored.cases[k]['draft']


def test_group_assignment_and_removal_preserve_physical_data_and_calculations():
    b=many();ready(b);k=next(iter(b.cases));calculate_case(b.cases[k],DEFAULTS);before=deepcopy(b.cases)
    assign_group(b,[k],'Grupo A');assert named_group(b,b.cases[k])=='Grupo A'
    assign_group(b,[k],'Grupo B');assert named_group(b,b.cases[k])=='Grupo B'
    remove_group(b,'Grupo B');assert named_group(b,b.cases[k])=='' and b.cases==before
    assert cached_calculation(b.cases[k]) is not None


def test_bulk_changes_invalidate_only_affected_joints():
    b=many();ready(b)
    for c in b.cases.values():calculate_case(c,DEFAULTS)
    k=next(iter(b.cases));bulk_edit(b,[k],{'laje_d':'.26'},DEFAULTS,only_empty=False)
    for c in b.cases.values():
        assert (cached_calculation(c) is None)==((c['floor'],c['support'])==(b.cases[k]['floor'],b.cases[k]['support']))


def test_batch_rotation_uses_each_original_frame_and_preserves_distinct_openings():
    b=many();ready(b);reps=representatives(b,list(b.cases))[:2]
    rotate_joint(b,reps[0],1,DEFAULTS)
    before=deepcopy(b.cases)
    bulk_edit(b,reps,{'pilar_tipo':'bordo'},DEFAULTS,only_empty=False,turn=3)
    for k in reps:
        case=b.cases[k];base=case['candidates']['columns']['frame']['base']['adopted']
        assert case['candidates']['columns']['adopted']==rotate_forces(base,3)
        assert classification(case)=='Bordo −X'
    for k,c in b.cases.items():
        if c['floor']=='Piso 2':assert c==before[k]


def test_orientation_repairs_stale_sense_flags_without_overwriting_modified_forces():
    b=book_model();k=filled_case(b);rotate_joint(b,k,1,DEFAULTS)
    for c in b.cases.values():c['draft']['pilar_tipo']='bordo';c['draft']['edge_perp_interior']=True
    rotate_joint(b,k,3,DEFAULTS)
    for c in b.cases.values():
        assert c['draft']['edge_perp_interior'] is True
        provenance(c,c['draft'])
    b.cases[k]['draft']['V_Ed']='1';before=deepcopy(b.payload())
    with pytest.raises(ValueError,match='alterados'):rotate_joint(b,k,0,DEFAULTS)
    assert b.payload()==before


def test_same_orientation_can_repair_flags():
    b=book_model();k=filled_case(b)
    for c in b.cases.values():c['draft']['pilar_tipo']='bordo';c['draft']['edge_perp_interior']=False
    rotate_joint(b,k,0,DEFAULTS)
    assert all(c['draft']['edge_perp_interior'] for c in b.cases.values())


def test_bulk_rotation_is_atomic_if_a_later_pillar_has_modified_actions():
    b=many();ready(b);reps=representatives(b,list(b.cases));b.cases[reps[-1]]['draft']['V_Ed']='1'
    before=deepcopy(b.payload())
    with pytest.raises(ValueError):bulk_edit(b,reps,{'betão_fck':'40'},DEFAULTS,False,turn=3)
    assert b.payload()==before


@pytest.mark.parametrize('fields',[{'V_Ed':'0'},{'pilar_c1':'.9'},{'openings':'[]'},{'anchorage_confirmed':True},
                                  {'betão_fck':'nan'},{'reinforcement_sr_m':'-1'},{'reinforcement_diameter_mm':'8'}])
def test_bulk_editor_rejects_forces_geometry_confirmations_and_invalid_numbers(fields):
    b=many();before=deepcopy(b.payload())
    with pytest.raises(ValueError):bulk_edit(b,list(b.cases),fields,DEFAULTS,False)
    assert b.payload()==before


def test_saved_calculated_scope_is_rebuilt_and_unrun_pillars_stay_unrun():
    b=many();ready(b);ks=list(b.cases);k=ks[0]
    calculate_case(b.cases[k],DEFAULTS)
    payload=json.loads(json.dumps(b.payload()));restored=ConnectionBook.from_payload(payload,DEFAULTS)
    assert cached_calculation(restored.cases[k])['snapshot']
    assert all(cached_calculation(restored.cases[x]) is None for x in ks[1:])
    assert len(build_report(restored)['entries'])==1
    assert build_report(restored)['groups'][0]['coverage']=='1/3 combinações calculadas'


def test_saved_receipt_with_changed_source_or_input_cannot_restore_a_success():
    b=book_model();k=filled_case(b);calculate_case(b.cases[k],DEFAULTS);p=b.payload()
    for c in p['cases'].values():c['draft']['laje_d']='.3'
    restored=ConnectionBook.from_payload(p,DEFAULTS)
    assert cached_calculation(restored.cases[k]) is None
    p=b.payload();p['cases'][k]['candidates']['columns']['node']='999'
    with pytest.raises(ValueError):ConnectionBook.from_payload(p,DEFAULTS)


def test_calculated_only_export_contains_failures_and_marks_missing_combos_partial(tmp_path):
    b=many();ready(b);ks=list(b.cases);first=ks[0]
    calculate_case(b.cases[first],DEFAULTS)
    # Retain a real failing result, not a fabricated snapshot.
    second=representatives(b,ks)[1]
    bulk_edit(b,[second],{'laje_d':'.06'},DEFAULTS,False)
    failed=calculate_case(b.cases[second],DEFAULTS);assert failed['status'].startswith('FAIL')
    report=build_report(b)
    assert len(report['entries'])==2 and any(e['status'].startswith('FAIL') for e in report['entries'])
    assert all(g['status'].startswith('PARCIAL') for g in report['groups'])
    assert all(g['omitted_count']==2 for g in report['groups'])
    for ext,writer in [('json',export_collection_json),('txt',export_collection_txt),('pdf',export_collection_pdf)]:writer(report,tmp_path/('partial.'+ext))
    assert '1/3 combinações calculadas' in (tmp_path/'partial.txt').read_text()
    full=build_report(b,only_calculated=False)
    assert len(full['entries'])==len(b.cases)
    assert any(e['status']=='NOT_EVALUATED' for e in full['entries'])


def test_expired_results_are_omitted_instead_of_recalculated_during_export():
    b=book_model();k=filled_case(b)
    for c in b.cases.values():calculate_case(c,DEFAULTS)
    b.cases[k]['draft']['laje_d']='.5'
    report=build_report(b);assert len(report['entries'])==1
    assert report['groups'][0]['status']=='PARCIAL — PENDENTE'
    assert report['groups'][0]['calculated_count']==1


def test_empty_general_report_does_not_execute_unfinished_pillars():
    b=many();report=build_report(b,only_calculated=False)
    assert all(e['snapshot'] is None for e in report['entries'])
    assert not any(cached_calculation(c) for c in b.cases.values())


def test_legacy_adapter_prefix_migration_retains_all_source_validations():
    b=book_model();k=filled_case(b)
    p=b.payload();p['schema']='PunchingShearEC2.connections/2';p.pop('batch_settings');p.pop('calculated_cases')
    text=json.dumps(p).replace('Modelo.model-ref/1','Legacy.model-ref/1').replace('analysis_tables','legacy_tables').replace('analysis_nodes','legacy_nodes')
    restored=ConnectionBook.from_payload(json.loads(text),DEFAULTS)
    assert restored.cases[k]['draft']==b.cases[k]['draft']
    assert len(restored.analysis_tables)==1
    assert restored.batch_settings['project']['betão_fck']=='30'
