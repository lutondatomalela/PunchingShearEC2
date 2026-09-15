"""Real Tcl controllers; widgets substituted. Native Ambiente de trabalho QA is separate."""
import csv
import json
import pytest

from test_connection_gui import dialogs, collection, Widget
from test_interface_and_exports import app
from test_analysis_import import bars, nodes, setup, joint
from punching.analysis_import import prepare_analysis_table, SIGN_REFERENCE
from punching.table_import import key
from punching.connections import ConnectionBook, initial_draft, adopt
from Punching_EC2_GUI import DEFAULTS


@pytest.fixture
def analysis_dialogs(dialogs, monkeypatch):
    from punching import analysis_dialogs as module
    monkeypatch.setattr(module, 'window', lambda *a,**kw:None)
    monkeypatch.setattr(module, 'FlowLabel', Widget)
    monkeypatch.setattr(module, 'ScrollTab', dialogs.ScrollTab)
    return module


def loaded(collection):
    collection._book=ConnectionBook()
    collection._merge_import(prepare_analysis_table(bars()))
    collection._merge_import(prepare_analysis_table(nodes()))
    return collection


def test_choose_analysis_table_auto_detects_profile_without_manual_mapping(dialogs,collection,tmp_path):
    p=tmp_path/'analysis.csv';t=bars()
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(t.headers);w.writerows(r for _,r in t.rows)
    dialog=dialogs.ImportDialog(collection);dialog.path.set(str(p));dialog._read()
    assert dialog._mode()=='analysis' and dialog.mapping=={}
    assert 'Barra + Nó + Caso' in dialog._analysis_summary()
    assert not dialog.option_widgets['length_unit'][0].visible
    dialog._preview();assert dialog.import_button.options['state']=='normal'
    dialog._apply();assert len(dialog.result['analysis_table']['rows'])==8
    assert not dialog.result['loads']


def test_unknown_units_analysis_table_stays_blocked(dialogs,collection,tmp_path):
    p=tmp_path/'bad.csv';t=bars();headers=list(t.headers);headers[1]='FX (tf)'
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(headers);w.writerows(r for _,r in t.rows)
    dialog=dialogs.ImportDialog(collection);dialog.path.set(str(p));dialog._read();dialog._preview()
    assert dialog.import_button.options['state']=='disabled' and 'unidade' in dialog.preview.text


def test_browser_displays_node_elevations_original_forces_and_sources(analysis_dialogs,collection):
    loaded(collection);dialog=analysis_dialogs.ModeloBrowser(collection,collection)
    assert len(dialog.tree.rows)==8 and dialog.tree.rows['0'][4]=='Topo'
    assert dialog.tree.rows['1'][4]=='Base'
    dialog.tree.selected=('0',);dialog._detail()
    assert '7460' in dialog.details.text and 'FX=1800' in dialog.details.text and 'linha 2' in dialog.details.text
    dialog.search.set('PISO 3');assert len(dialog.tree.rows)==4
    dialog.search.set('inexistente');assert len(dialog.tree.rows)==0 and dialog.prepare.options['state']=='disabled'


def test_joint_dialog_suggests_roles_by_nodes_but_requires_orientation(analysis_dialogs,collection):
    loaded(collection);r=analysis_dialogs.all_records(collection._book.analysis_tables)[0]
    dialog=analysis_dialogs.ModeloJointDialog(collection,collection,r)
    assert dialog.options['below'].get().startswith('2 ·') and dialog.options['above'].get().startswith('3 ·')
    dialog._preview();assert dialog.apply.options['state']=='disabled'
    for k,v in dialog.checks.items():v.set(k!='upper_absent')
    for role in ('below','above'):
        dialog.options[role+'_x'].set('+Z');dialog.options[role+'_y'].set('+X')
    dialog.options['reference'].set('Modelo de exemplo; eixos conferidos')
    dialog._preview();assert dialog.apply.options['state']=='normal'
    assert 'V_Ed=450' in dialog.preview.text and SIGN_REFERENCE in dialog.preview.text
    dialog.options['below_x'].set('-Z');assert dialog.apply.options['state']=='disabled'
    dialog.options['below_x'].set('+Z');dialog._preview();dialog._apply()
    assert len(dialog.result['loads'])==1
    collection._merge_import(dialog.result)
    collection._select_connection(key('PISO 2','P103','101 (C)'))
    assert collection.vars['pilar_c1'].get()=='0.25' and collection.vars['V_Ed'].get()==''


def test_unknown_node_elevations_do_not_infer_roles_from_rows(analysis_dialogs,collection):
    loaded(collection);collection._book.analysis_nodes=None
    r=analysis_dialogs.all_records(collection._book.analysis_tables)[0]
    dialog=analysis_dialogs.ModeloJointDialog(collection,collection,r)
    assert dialog.options['below'].get()=='' and dialog.options['above'].get()==''


def test_catalog_only_project_is_saved_and_restored_and_close_can_cancel(collection,monkeypatch,tmp_path):
    loaded(collection);p=tmp_path/'analysis.json'
    from punching import connection_ui as module
    monkeypatch.setattr(module.filedialog,'asksaveasfilename',lambda **kw:str(p))
    monkeypatch.setattr(module.filedialog,'askopenfilename',lambda **kw:str(p))
    monkeypatch.setattr(module.messagebox,'askyesnocancel',lambda *a,**kw:None)
    assert not collection._offer_save_connections()
    assert collection._save_connections()
    collection._book=ConnectionBook();assert collection._open_connections()
    assert len(collection._book.analysis_tables)==1 and collection._book.analysis_nodes
    assert not collection._book.cases


def test_analysis_origin_survives_calculation_exports_and_reopen(collection,tmp_path,monkeypatch):
    loaded(collection);collection._merge_import(joint())
    ckey=key('PISO 2','P103','101 (C)');collection._select_connection(ckey)
    c=collection._current_connection();draft=dict(DEFAULTS);draft.update(c['draft'])
    for k in ('pilar_tipo','laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm','betão_fck'):draft[k]=DEFAULTS[k]
    adopt(c,'columns',draft);collection._load_draft(c['draft']);collection.calcular()
    result=collection._fresh_result();assert result is not None and result['inputs']['V_Ed']==450000
    assert result['load_trace']['adopted']['M_Edy']==16 and 'Modelo 3D' in collection.last_report
    from punching.reports import export_json,export_xlsx,export_pdf,export_txt
    for ext,fn in [('json',export_json),('xlsx',export_xlsx),('pdf',export_pdf),('txt',export_txt)]:fn(result,tmp_path/('analysis.'+ext))
    text=(tmp_path/'analysis.txt').read_text();assert 'Member/Node/Case' in text and 'linha 2' in text
    from openpyxl import load_workbook
    wb=load_workbook(tmp_path/'analysis.xlsx');source='\n'.join(str(r[0]) for r in wb['OrigemEsforcos'].values);wb.close()
    assert 'FXinf-FXsup' in source
    import Punching_EC2_GUI as gui
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(tmp_path/'analysis.json'))
    collection.limpar();collection.abrir_caso();collection.calcular()
    assert collection._fresh_result()['load_trace']['adopted']['V_Ed']==450


def test_blank_names_in_utf16_file_allow_import_and_are_explained(dialogs,collection,tmp_path):
    from test_analysis_optional_names import unnamed
    p=tmp_path/'piso2.csv';t=unnamed()
    for _,raw in t.rows:raw[0]=raw[0].replace('102 (C)','118 (C) (CQC)')
    with p.open('w',encoding='utf-16',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(t.headers);w.writerows(r for _,r in t.rows)
    dialog=dialogs.ImportDialog(collection);dialog.path.set(str(p));dialog._read();dialog._preview()
    assert dialog.import_button.options['state']=='normal'
    summary=dialog._analysis_summary()
    assert '8 registos' in summary and 'Barra 2' in summary and 'Barra 3' in summary
    assert 'PISO 2' in summary and 'PISO 3' in summary and 'CQC/SRSS' in summary
    dialog._apply();assert len(dialog.result['analysis_table']['rows'])==8


def test_browser_filters_fallback_label_and_displays_original_name_state(analysis_dialogs,collection):
    from test_analysis_optional_names import unnamed
    collection._book=ConnectionBook();collection._merge_import(prepare_analysis_table(unnamed()))
    dialog=analysis_dialogs.ModeloBrowser(collection,collection)
    dialog.search.set('Barra 2');assert len(dialog.tree.rows)==4
    selected=next(iter(dialog.tree.rows));dialog.tree.selected=(selected,);dialog._detail()
    assert 'Name não preenchido' in dialog.details.text
    assert 'FX=1800' in dialog.details.text
