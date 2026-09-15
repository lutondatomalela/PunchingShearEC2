from copy import deepcopy
import pytest
from test_connection_gui import dialogs, collection, Widget
from test_interface_and_exports import app
from test_model_gui import model_dialogs
from test_batch_workflow import many, ready
from punching.batch_workflow import representatives, assign_group
from punching.collection_workflow import cached_calculation, calculate_case
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS


@pytest.fixture
def batch_dialogs(dialogs,monkeypatch):
    from punching import batch_dialogs as module
    monkeypatch.setattr(module,'window',lambda *a,**kw:None)
    monkeypatch.setattr(module,'FlowLabel',Widget)
    monkeypatch.setattr(module,'LabelCombo',lambda master,var,choices: Widget(master,textvariable=var,values=list(choices)))
    monkeypatch.setattr(module,'ScrollTab',dialogs.ScrollTab)
    return module


def test_manager_selection_filters_and_grouping_keep_floor_identity(dialogs,collection,batch_dialogs,monkeypatch):
    collection._book=many();d=dialogs.ConnectionDialog(collection)
    assert len(d.tree.rows)==4
    d.floor.set('Piso 1');assert len(d.tree.rows)==2
    d._all_visible();assert len(d._selected_keys())==6
    class Group:
        def __init__(self,*args):self.result='Primeiro piso'
    monkeypatch.setattr(batch_dialogs,'GroupDialog',Group)
    d._group_selection();assert len(collection._book.batch_settings['groups']['Primeiro piso']['members'])==2
    d.floor.set('Piso 2');assert not d.tree.rows
    d.group.set('Todos os grupos');assert len(d.tree.rows)==2
    d._clear_selection();assert not d._selected_keys()


def test_bulk_editor_is_opt_in_and_retains_automatic_spacing(batch_dialogs,collection):
    b=many();k=next(iter(b.cases));d=batch_dialogs.BulkEditDialog(collection,b,[k])
    assert not any(v.get() for v in d.enabled.values())
    d.enabled['reinforcement_s0_m'].set(True);d.values['reinforcement_s0_m'].set('')
    d.values['betão_fck'].set('99')
    d._apply();assert d.result['fields']=={'reinforcement_s0_m':''} and d.result['only_empty']


def test_bulk_controller_updates_active_form_without_later_overwrite(dialogs,batch_dialogs,collection,monkeypatch):
    b=many();ready(b);collection._book=b;k=next(iter(b.cases));collection._select_connection(k)
    d=dialogs.ConnectionDialog(collection);d.tree.selected=(k,)
    class Edit:
        def __init__(self,*args):self.result=dict(fields={'betão_fck':'40'},only_empty=False,turn=None,template=('project',''))
    monkeypatch.setattr(batch_dialogs,'BulkEditDialog',Edit)
    d._edit_selection()
    assert collection.vars['betão_fck'].get()=='40'
    collection._commit_connection();assert b.cases[k]['draft']['betão_fck']=='40'
    assert b.batch_settings['project']['betão_fck']=='40'


def test_calculate_selection_executes_all_combos_of_selected_pillars_only(dialogs,collection,monkeypatch):
    b=many();ready(b);collection._book=b;d=dialogs.ConnectionDialog(collection)
    k=next(iter(d.tree.rows));d.tree.selected=(k,)
    def run(keys,done):
        for ckey in keys:calculate_case(b.cases[ckey],DEFAULTS)
        done(True)
    monkeypatch.setattr(collection,'_run_collection',run)
    d._calculate_selection()
    assert sum(cached_calculation(c) is not None for c in b.cases.values())==3


def test_project_name_concrete_and_spacing_reused_without_copying_slab(collection):
    b=many();collection._book=b;reps=representatives(b,list(b.cases))
    # Old projects are preserved as exceptions; simulate the untouched cases of a new import.
    for c in b.cases.values():c['user_edited']=False
    collection._select_connection(reps[0]);collection.vars['project'].set('Obra A');collection.vars['betão_fck'].set('35')
    collection.vars['reinforcement_s0_m'].set('.08');collection.vars['reinforcement_sr_m'].set('.12');collection.vars['laje_d'].set('.21')
    collection._select_connection(reps[1])
    assert collection.vars['project'].get()=='Obra A' and collection.vars['betão_fck'].get()=='35'
    assert collection.vars['reinforcement_s0_m'].get()=='.08' and collection.vars['reinforcement_sr_m'].get()=='.12'
    assert collection.vars['laje_d'].get()==''


def test_report_dialog_selected_scope_defaults_to_current_calculations(model_dialogs,collection):
    b=many();ready(b);collection._book=b;k=next(iter(b.cases));calculate_case(b.cases[k],DEFAULTS)
    from punching.batch_workflow import joint_selection
    keys=joint_selection(b,[k]);d=model_dialogs.CollectionReportDialog(collection,b,keys)
    assert d.only_calculated.get() and d.selection_only.get()
    assert d._keys()==keys
    assert '1 combinações calculadas de 3' in d.count.get()
    d._apply();assert d.result['only_calculated'] and d.result['keys']==keys


def test_export_without_results_stays_disabled(model_dialogs,collection):
    b=many();d=model_dialogs.CollectionReportDialog(collection,b)
    assert d.export_button.options['state']=='disabled'
    d.only_calculated.set(False);assert d.export_button.options['state']=='normal'
