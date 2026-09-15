from copy import deepcopy
import json
import tkinter as tk
import pytest
from test_connection_gui import dialogs, collection, Widget
from test_interface_and_exports import app
from test_model_workflow import book_model, filled_case, config
from test_analysis_import import bars, nodes
from punching.analysis_import import prepare_analysis_table
from punching.connections import ConnectionBook
from punching.collection_workflow import calculate_case, cached_calculation
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS


@pytest.fixture
def model_dialogs(dialogs,monkeypatch,collection):
    from punching import model_dialogs as module
    monkeypatch.setattr(module,'window',lambda *a,**kw:None)
    monkeypatch.setattr(module,'FlowLabel',Widget)
    monkeypatch.setattr(module,'ScrollTab',dialogs.ScrollTab)
    monkeypatch.setattr(collection,'wait_window',lambda *args:None)
    return module


def test_model_wizard_requires_axes_and_adopts_after_review(model_dialogs,collection):
    collection._book=ConnectionBook()
    for table in (bars(),nodes()):collection._merge_import(prepare_analysis_table(table))
    d=model_dialogs.ModelDialog(collection,collection)
    assert len(d.rows)==3 and sum(j['enabled'] for j in d.rows)==1
    d._preview();assert d.apply.options['state']=='disabled'
    d.options['y'].set('+X');d.options['reference'].set('Modèle fictício 3D; eixos conferidos')
    for flag in d.checks.values():flag.set(True)
    d._preview();assert d.apply.options['state']=='normal' and 'V_Ed=450.000' in d.preview.text
    d._apply();collection._merge_import(d.result)
    assert len(collection._book.cases)==2
    assert all(c['automated'] for c in collection._book.cases.values())
    assert collection._book.cases[key('PISO 2','P103','101 (C)')]['draft']['V_Ed']=='450'


def test_pillar_manager_groups_model_combinations_in_one_row(dialogs,collection):
    collection._book=book_model();d=dialogs.ConnectionDialog(collection)
    assert len(d.tree.rows)==1
    row=next(iter(d.tree.rows.values()));assert row[:3]==('PISO 2','P103','2 combinações')


def test_model_preview_preserves_edited_floor_without_separate_apply(model_dialogs,collection):
    collection._book=ConnectionBook()
    for table in (bars(),nodes()):collection._merge_import(prepare_analysis_table(table))
    d=model_dialogs.ModelDialog(collection,collection)
    d.options['y'].set('+X');d.options['reference'].set('Modelo de demonstração; eixos conferidos')
    for flag in d.checks.values():flag.set(True)
    index=next(i for i,j in enumerate(d.rows) if j['enabled'])
    d.tree.selected=(str(index),);d._detail();d.link['floor'].set('Piso revisto')
    d._preview()
    assert d.prepared and {c['floor'] for c in d.prepared['loads'].values()}=={'Piso revisto'}
    d.link['floor'].set('Piso seguinte')
    assert d.prepared is None and d.apply.options['state']=='disabled'


def test_shared_data_survive_switching_between_combinations(collection):
    collection._book=book_model();a=key('PISO 2','P103','101 (C)');b=key('PISO 2','P103','102 (C)')
    collection._select_connection(a);collection.vars['laje_d'].set('0,26')
    collection._select_connection(b)
    assert collection.vars['laje_d'].get()=='0,26' and collection.vars['V_Ed'].get()=='400'
    collection.vars['laje_As_lx_cm2pm'].set('14');collection._select_connection(a)
    assert collection.vars['laje_As_lx_cm2pm'].get()=='14' and collection.vars['V_Ed'].get()=='450'


def test_frame_dialog_rotates_all_combinations_and_invalidates(collection,model_dialogs,monkeypatch):
    collection._book=book_model();a=filled_case(collection._book);collection._select_connection(a)
    class Pick:
        def __init__(self,*a):self.result=1
    monkeypatch.setattr(model_dialogs,'FrameDialog',Pick)
    collection._orient_connection()
    assert float(collection.vars['pilar_c1'].get())==pytest.approx(.7)
    assert collection.vars['M_Edx'].get()=='-16'
    assert collection._fresh_result() is None


def test_f5_calculates_the_whole_joint_and_results_can_be_selected(collection,model_dialogs,monkeypatch):
    collection._book=book_model();a=filled_case(collection._book);collection._select_connection(a)
    def run(keys,done):
        for k in keys:calculate_case(collection._book.cases[k],DEFAULTS)
        done(True)
    monkeypatch.setattr(collection,'_run_collection',run)
    class Results:
        def __init__(self,*args):self.result=None
    monkeypatch.setattr(model_dialogs,'GroupResultsDialog',Results)
    collection.calcular()
    assert not collection.dialogs
    assert all(cached_calculation(c)['snapshot'] for c in collection._book.cases.values())
    assert 'LIGAÇÃO: VERIFICA' in collection.lbl_badge.options['text']
    assert '2 combinações' in collection.var_resultado.get()


def test_progress_uses_callbacks_can_cancel_and_keeps_unrun_cases_pending(collection,model_dialogs,monkeypatch):
    collection._book=book_model();filled_case(collection._book)
    callbacks=[];finished=[];progress_views=[]
    class Progress:
        def __init__(self,*args):self.cancelled=False;self.text=tk.StringVar(collection);progress_views.append(self)
        def destroy(self):pass
    monkeypatch.setattr(model_dialogs,'CalculationProgress',Progress)
    monkeypatch.setattr(collection,'after',lambda delay,callback:callbacks.append(callback))
    collection._run_collection(list(collection._book.cases),finished.append)
    callbacks.pop(0)();progress_views[0].cancelled=True;callbacks.pop(0)()
    assert finished==[False] and not collection._workflow_busy
    assert sum(cached_calculation(c) is not None for c in collection._book.cases.values())==1


def test_results_dialog_includes_pending_combinations(model_dialogs,collection):
    t=bars()
    for _,r in t.rows:r[0]=r[0].replace('102 (C)','118 (C) (CQC)')
    collection._book=book_model(t);a=filled_case(collection._book)
    for c in collection._book.cases.values():calculate_case(c,DEFAULTS)
    d=model_dialogs.GroupResultsDialog(collection,collection._book,collection._book.cases[a])
    assert len(d.tree.rows)==2
    modal=key('PISO 2','P103','118 (C) (CQC)')
    assert d.tree.rows[modal][1:4]==('—','—','—')
    d.tree.selected=(modal,);d._detail();assert 'CQC/SRSS' in d.details.text


def test_report_controller_exports_fresh_results_and_selected_scope(model_dialogs,collection,monkeypatch,tmp_path):
    from punching import connection_ui
    collection._book=book_model();a=filled_case(collection._book);collection._select_connection(a)
    target=tmp_path/'conjunto.json'
    class Choose:
        def __init__(self,*args):self.result={'keys':list(collection._book.cases),'format':'json','full':True}
    monkeypatch.setattr(model_dialogs,'CollectionReportDialog',Choose)
    monkeypatch.setattr(connection_ui.filedialog,'asksaveasfilename',lambda **kw:str(target))
    def run(keys,done):
        for k in keys:calculate_case(collection._book.cases[k],DEFAULTS)
        done(True)
    monkeypatch.setattr(collection,'_run_collection',run)
    for c in collection._book.cases.values():calculate_case(c,DEFAULTS)
    monkeypatch.setattr(collection,'_run_collection',lambda *a:pytest.fail('A exportação não deve iniciar cálculos.'))
    collection._export_collection()
    report=json.loads(target.read_text(encoding='utf-8'));assert len(report['entries'])==2
    assert {e['snapshot']['load_trace']['adopted']['V_Ed'] for e in report['entries']}=={400,450}
