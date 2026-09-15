"""Actual Tcl/controller callbacks; native desktop layout is checked separately."""
from copy import deepcopy
import json
import pytest

from test_connection_gui import dialogs,collection
from test_interface_and_exports import app
from test_model_gui import model_dialogs
from test_model_workflow import book_model,filled_case,config
from test_analysis_import import bars,nodes
from punching.connections import ConnectionBook
from punching.analysis_import import prepare_analysis_table
from punching.collection_workflow import calculate_case,cached_calculation
from punching.table_import import key
from Punching_EC2_GUI import DEFAULTS


def test_ranges_apply_remove_atomically_and_alignment_expands_only_selection(model_dialogs,collection):
    collection._book=book_model();d=model_dialogs.ModelDialog(collection,collection)
    assert d.bar_selector.options['state']=='normal'
    d.bar.set('2para3');d.bar_y.set('-Y');d._axis()
    assert d.axes=={'2':{'x':'+Z','y':'-Y'},'3':{'x':'+Z','y':'-Y'}}
    d._preview();assert d.prepared
    previous=deepcopy(d.axes);d.bar.set('2-4');d._axis()
    assert d.axes==previous and 'não encontradas' in collection.dialogs[-1][1]
    d.bar.set('2 3');d._remove_axis();assert not d.axes and d.prepared is None
    d.bar.set('2');d._alignment();assert d.bar.get()=='2-3' and not d.axes
    d._axis();assert set(d.axes)=={'2','3'}


def test_existing_joint_is_visible_as_prepared_and_review_needs_no_new_selection(model_dialogs,collection):
    collection._book=book_model();d=model_dialogs.ModelDialog(collection,collection)
    i=next(i for i,j in enumerate(d.rows) if j.get('existing'))
    assert d.tree.rows[str(i)][0]=='Preparada'
    d.tree.selected=(str(i),);d._detail()
    assert d.include_widget.options['state']=='disabled'
    assert d.link_widgets['below'].options['state']=='disabled'
    assert not any(j['enabled'] for j in d.rows)
    d._preview();assert d.prepared and d.apply.options['state']=='normal'
    assert '2 sem alteração' in d.preview.text and 'Selecione pelo menos' not in d.preview.text


@pytest.mark.parametrize('automatic',[False,True])
def test_save_from_model_window_updates_file_without_new_joints(model_dialogs,collection,tmp_path,monkeypatch,automatic):
    from punching import connection_ui
    collection._book=book_model();k=filled_case(collection._book)
    if automatic:
        from punching.batch_workflow import bulk_edit
        bulk_edit(collection._book,list(collection._book.cases),{'long_mode':'automatic','long_h_mm':'250','long_cover_mm':'30','long_x_extra_mm':'12','long_y_extra_mm':'12'},DEFAULTS)
    collection._select_connection(k)
    collection.vars['project'].set('Projeto preservado')
    collection._commit_connection()
    for c in collection._book.cases.values():calculate_case(c,DEFAULTS)
    target=tmp_path/'conjunto.json'
    monkeypatch.setattr(connection_ui.filedialog,'asksaveasfilename',lambda **kw:str(target))
    d=model_dialogs.ModelDialog(collection,collection);d.bar.set('3');d.bar_y.set('+Y');d._axis();d._save()
    assert target.exists() and collection.vars['M_Edx'].get()=='10'
    assert collection.vars['project'].get()=='Projeto preservado'
    assert collection._fresh_result() is None
    payload=json.loads(target.read_text(encoding='utf-8'))
    restored=ConnectionBook.from_payload(payload,DEFAULTS)
    assert len(restored.cases)==2 and restored.cases[k]['draft']==collection._book.cases[k]['draft']
    assert cached_calculation(restored.cases[k]) is None
    assert payload==collection._book.payload()
    # Future saves reuse the actual set path and keep unchanged calculation records.
    for c in collection._book.cases.values():calculate_case(c,DEFAULTS)
    monkeypatch.setattr(connection_ui.filedialog,'asksaveasfilename',lambda **kw:pytest.fail('Já existe um caminho do conjunto.'))
    assert collection._save_model_configuration(collection._book.model_setup['config'])
    restored=ConnectionBook.from_payload(json.loads(target.read_text(encoding='utf-8')),DEFAULTS)
    assert all(cached_calculation(c) for c in restored.cases.values())


@pytest.mark.parametrize('failure',['cancel','write_error','invalid_config'])
def test_cancel_or_failed_save_does_not_apply_configuration(model_dialogs,collection,tmp_path,monkeypatch,failure):
    from punching import connection_ui
    collection._book=book_model();k=filled_case(collection._book);collection._select_connection(k)
    collection._commit_connection();before=deepcopy(collection._book.payload());draft=collection._raw_draft()
    cfg=config(member_axes={'3':{'x':'+Z','y':'+Y'}})
    path=tmp_path/'preservado.json';path.write_text('original')
    monkeypatch.setattr(connection_ui.filedialog,'asksaveasfilename',lambda **kw:'' if failure=='cancel' else str(path))
    if failure=='write_error':
        def fail(*args):raise OSError('Escrita indisponível')
        monkeypatch.setattr(connection_ui,'write_json_atomic',fail)
    if failure=='invalid_config':cfg['axes_confirmed']=False
    assert not collection._save_model_configuration(cfg)
    assert collection._book.payload()==before and collection._raw_draft()==draft
    assert path.read_text(encoding='utf-8')=='original'


def test_save_initial_configuration_does_not_create_auto_selected_new_joints(model_dialogs,collection,tmp_path,monkeypatch):
    from punching import connection_ui
    collection._book=ConnectionBook()
    for t in (bars(),nodes()):collection._merge_import(prepare_analysis_table(t))
    target=tmp_path/'eixos.json';monkeypatch.setattr(connection_ui.filedialog,'asksaveasfilename',lambda **kw:str(target))
    d=model_dialogs.ModelDialog(collection,collection)
    assert any(j['enabled'] for j in d.rows)
    d.options['y'].set('+X');d.options['reference'].set('Modelo de referência')
    for v in d.checks.values():v.set(True)
    d.bar.set('2-3');d.bar_y.set('-Y');d._axis();d._save()
    restored=ConnectionBook.from_payload(json.loads(target.read_text(encoding='utf-8')),DEFAULTS)
    assert not restored.cases and set(restored.model_setup['config']['member_axes'])=={'2','3'}
    assert not collection.dialogs
