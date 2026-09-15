"""Real Tcl state/controller tests; widgets substituted, not visual GUI QA."""
from copy import deepcopy
import json
from pathlib import Path
import tkinter as tk
import pytest
import Punching_EC2_GUI as gui
from punching.connections import adopt, ConnectionBook
from punching.table_import import key
from punching.reports import export_json, export_txt, export_xlsx, export_pdf
from test_connection_import import book, batch, filled, EXAMPLES
from test_interface_and_exports import app


@pytest.fixture
def collection(app):
    app.master=None;app._ensure_book();app._book=book();app.var_origin=tk.StringVar(master=app)
    return app


def ready(app, ckey=key('Piso 1','P01','ELU 01'), source='columns'):
    app._select_connection(ckey);c=app._book.cases[ckey]
    adopt(c,source,filled(c));app._load_draft(c['draft']);app.calcular()
    return app._fresh_result()


def test_switching_preserves_per_connection_inputs_and_drafts(collection):
    a=key('Piso 1','P01','ELU 01');b=key('Piso 1','P01','ELU 02')
    collection._select_connection(a);collection.vars['laje_d'].set('0,27');collection.vars['openings'].set('[unfinished')
    collection._select_connection(b);assert collection.vars['laje_d'].get()==''
    collection.vars['laje_d'].set('0.23');collection._select_connection(a)
    assert collection.vars['laje_d'].get()=='0,27' and collection.vars['openings'].get()=='[unfinished'
    assert collection._book.cases[b]['draft']['laje_d']=='0.23'
    assert collection._fresh_result() is None


def test_imported_case_cannot_calculate_with_implicit_defaults(collection):
    collection._select_connection(key('Piso 1','P01','ELU 01'));collection.calcular()
    assert collection.last_verif is None and collection.dirty
    c=collection._current_connection();adopt(c,'columns',collection._raw_draft());collection._load_draft(c['draft']);collection.calcular()
    assert collection.last_verif is None  # slab and concrete still missing


def test_origin_is_frozen_for_reports_and_invalidated_with_input_changes(collection):
    result=ready(collection)
    assert result['inputs']['V_Ed']==450000 and result['load_trace']['adopted']['V_Ed']==450
    assert result['load_trace']['choice']=='columns' and 'Ninf-Nsup' in collection.last_report
    result['load_trace']['adopted']['V_Ed']=0
    assert collection._fresh_result()['load_trace']['adopted']['V_Ed']==450
    collection.vars['V_Ed'].set('460');collection.calcular()
    assert collection.last_verif is None and 'alterados' in collection.var_resultado.get()


def test_source_comparison_change_invalidates_current_result(collection):
    collection._book=ConnectionBook();collection._merge_import(batch('geometria_pilares.csv','geometry'));collection._merge_import(batch())
    assert ready(collection)
    collection._merge_import(batch('resultantes_ligacao.csv','resultants'))
    assert collection.dirty and collection._fresh_result() is None
    assert collection.vars['V_Ed'].get()=='450'


def test_individual_case_save_reopen_keeps_import_origin(collection,tmp_path,monkeypatch):
    ready(collection);p=tmp_path/'case.json'
    monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(p));monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(p))
    collection.guardar_caso();data=json.loads(p.read_text());assert 'import_case' in data
    collection.limpar();collection.abrir_caso();collection.calcular()
    assert not collection.dialogs and collection._fresh_result()['load_trace']['adopted']['V_Ed']==450


def test_project_save_open_keeps_incomplete_cases_and_requires_recalculation(collection,tmp_path,monkeypatch):
    ready(collection);collection.vars['laje_d'].set('0,')
    p=tmp_path/'connections.json'
    monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(p));monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(p))
    assert collection._save_connections()
    collection._book=ConnectionBook()
    assert collection._open_connections() and not collection.dialogs
    assert collection.vars['laje_d'].get()=='0,' and collection.last_verif is None and collection.dirty


def test_cancel_replacing_collection_does_not_drop_work(collection,tmp_path,monkeypatch):
    ready(collection);before=collection._raw_draft();p=tmp_path/'project.json';p.write_text(json.dumps(book().payload()))
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(p))
    monkeypatch.setattr(gui.messagebox,'askyesnocancel',lambda *a,**kw:None)
    assert not collection._open_connections() and collection._raw_draft()==before


def test_reports_all_retain_source_units_row_equilibrium_and_adopted_values(collection,tmp_path):
    result=ready(collection)
    for suffix,fn in [('json',export_json),('txt',export_txt),('xlsx',export_xlsx),('pdf',export_pdf)]:fn(result,tmp_path/('report.'+suffix))
    assert json.loads((tmp_path/'report.json').read_text())['load_trace']==result['load_trace']
    assert 'Ninf-Nsup' in (tmp_path/'report.txt').read_text()
    from openpyxl import load_workbook
    wb=load_workbook(tmp_path/'report.xlsx');lines='\n'.join(str(row[0]) for row in wb['OrigemEsforcos'].values);wb.close()
    assert 'linha 2' in lines and 'V_Ed=450' in lines and 'não adotada' in lines
    assert (tmp_path/'report.pdf').stat().st_size>15000


def test_result_json_can_reopen_with_provenance(collection,tmp_path,monkeypatch):
    result=ready(collection);p=tmp_path/'result.json';export_json(result,p)
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(p))
    collection.limpar();collection.abrir_caso();collection.calcular()
    assert not collection.dialogs
    assert collection._fresh_result()['load_trace']['adopted']==result['load_trace']['adopted']


def test_cli_retains_origin_and_blocks_changed_imported_force(collection,tmp_path):
    import subprocess,sys
    result=ready(collection);p=tmp_path/'result.json';export_json(result,p)
    target=tmp_path/'valid'
    run=subprocess.run([sys.executable,'-m','punching.cli',str(p),'--out',str(target)],capture_output=True,text=True)
    assert run.returncode in (0,1)
    assert json.loads((target/'resultado.json').read_text())['load_trace']['adopted']['V_Ed']==450
    result['inputs']['V_Ed']=200000;export_json(result,p);target=tmp_path/'invalid'
    run=subprocess.run([sys.executable,'-m','punching.cli',str(p),'--out',str(target)],capture_output=True,text=True)
    assert run.returncode==2 and not target.exists() and 'alterados' in run.stderr


def test_close_with_unsaved_collection_can_cancel(collection,monkeypatch,tmp_path):
    ready(collection);calls=[];collection.destroy=lambda:calls.append('closed')
    monkeypatch.setattr(gui.messagebox,'askyesnocancel',lambda *a,**kw:None)
    collection._on_close();assert not calls
    monkeypatch.setattr(gui.messagebox,'askyesnocancel',lambda *a,**kw:True)
    p=tmp_path/'saved.json';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(p))
    collection._on_close();assert calls==['closed'] and p.exists()


def test_new_collection_protects_unsaved_work_and_releases_old_force_source(collection,monkeypatch):
    ready(collection);active=collection._book.active
    monkeypatch.setattr(gui.messagebox,'askyesnocancel',lambda *a,**kw:None)
    assert not collection._new_connections() and collection._book.active==active
    monkeypatch.setattr(gui.messagebox,'askyesnocancel',lambda *a,**kw:False)
    assert collection._new_connections() and not collection._book.cases
    assert collection._current_connection() is None and collection.last_verif is None


class Widget:
    """Nonvisual layout/callback recorder for constructing each new dialog."""
    def __init__(self,master=None,**kw):
        self.options=dict(kw);self.children_list=[];self.rows={};self.selected=();self.visible=True;self.text='';self.master=master
        if hasattr(master,'children_list'):master.children_list.append(self)
    def __getattr__(self,name):
        if name in ('grid','pack','columnconfigure','rowconfigure','bind','focus_set','yview','xview','yview_scroll','set','heading','column','add','select'):return lambda *a,**kw:None
        raise AttributeError(name)
    def configure(self,**kw):self.options.update(kw)
    def grid_remove(self):self.visible=False
    def winfo_children(self):return self.children_list
    def destroy(self):pass
    def delete(self,*items):
        self.text=''
        for k in items:self.rows.pop(k,None)
    def insert(self,*args,**kw):
        if 'values' in kw:self.rows[kw['iid']]=kw['values']
        elif len(args)>1:self.text+=str(args[1])
    def get_children(self):return list(self.rows)
    def selection(self):return self.selected
    def selection_set(self,items):self.selected=tuple(items)
    def selection_remove(self,items):self.selected=tuple(k for k in self.selected if k not in items)


@pytest.fixture
def dialogs(monkeypatch,collection):
    from punching import import_dialogs as module
    interpreter=tk.Tcl()
    def top_init(self,master=None,**kw):self.tk=interpreter.tk;self._w='.';self.master=None
    monkeypatch.setattr(tk.Toplevel,'__init__',top_init)
    for name in ('bind','destroy','wait_window','grab_set'):
        monkeypatch.setattr(tk.Toplevel,name,lambda self,*a,**kw:None)
    monkeypatch.setattr(module,'window',lambda *a,**kw:None)
    for name in ('Frame','Label','LabelFrame','Entry','Combobox','Button','Checkbutton','Notebook','Panedwindow','Treeview','Scrollbar'):
        monkeypatch.setattr(module.ttk,name,Widget)
    monkeypatch.setattr(module.tk,'Text',Widget)
    monkeypatch.setattr(module,'FlowLabel',Widget)
    class Scroll(Widget):
        def __init__(self,master=None,**kw):super().__init__(master,**kw);self.body=Widget(self);self.canvas=Widget(self)
    monkeypatch.setattr(module,'ScrollTab',Scroll)
    return module


def test_import_dialog_construct_map_preview_and_apply(dialogs,collection):
    dialog=dialogs.ImportDialog(collection)
    dialog.path.set(str(EXAMPLES/'geometria_pilares.csv'));dialog._read()
    assert dialog.options['sheet'].get()=='CSV' and dialog.mapping['c1'].get()=='c1'
    dialog._preview();assert dialog.import_button.options['state']=='normal'
    dialog.options['length_unit'].set('cm');assert dialog.import_button.options['state']=='disabled'
    dialog.options['length_unit'].set('m');dialog._preview();dialog._apply()
    assert len(dialog.result['geometries'])==3


def test_force_dialog_cannot_import_unconfirmed_conventions(dialogs,collection):
    dialog=dialogs.ImportDialog(collection);dialog.path.set(str(EXAMPLES/'esforcos_pilares.csv'))
    dialog.options['mode'].set(dialogs.MODES['columns']);dialog._mode_changed();dialog._read();dialog._preview()
    assert dialog.import_button.options['state']=='disabled'
    for k in ('same_combination','axes_at_column','isolated_joint'):dialog.declarations[k].set(True)
    dialog._preview();assert dialog.import_button.options['state']=='normal'
    dialog._apply();assert len(dialog.result['loads'])==4


def test_browser_and_origin_dialog_construct_and_apply_transaction(dialogs,collection):
    dialog=dialogs.ConnectionDialog(collection)
    assert len(dialog.tree.rows)==3
    k=key('Piso 1','P01','ELU 01');dialog.tree.selected=(k,);dialog._detail();dialog._select();assert dialog.result==k
    c=collection._book.cases[k];origin=dialogs.OriginDialog(collection,c,filled(c))
    assert origin.result is None and c['choice']==''
    origin.choice.set(dialogs.MODES['columns']);assert origin.forces['V_Ed'][0].get()=='450'
    origin._apply();assert origin.result['choice']=='columns' and c['choice']==''
