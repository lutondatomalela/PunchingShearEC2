"""Tcl/controller tests. They do not replace visual testing of native Ambiente de trabalho Tk."""
import copy
import json
from types import SimpleNamespace
import tkinter as tk
import pytest
import Punching_EC2_GUI as gui
import punching.opening_editor as editor_module
from punching.opening_editor import OpeningEditor
from test_interface_and_exports import app,ViewStub
from test_opening_geometry import rectangle,CTX


def test_gui_editor_apply_and_cancel_are_transactional(app,monkeypatch):
    app.calcular();original=[rectangle()]
    def dialog(parent,items,context,manual):
        assert not items and context['d']==.2
        return SimpleNamespace(result=copy.deepcopy(original))
    monkeypatch.setattr(editor_module,'OpeningEditor',dialog);app.wait_window=lambda obj:None
    app._edit_openings()
    assert app.dirty and app._fresh_result() is None
    assert app._collect_inputs()['openings']==original
    app.calcular();assert app.last_verif.status=='BETA_PENDING'
    monkeypatch.setattr(editor_module,'OpeningEditor',lambda *a:SimpleNamespace(result=None))
    before=app.vars['openings'].get();app._edit_openings();assert app.vars['openings'].get()==before and not app.dirty


def test_physical_openings_round_trip_without_copying_generated_angles(app,tmp_path,monkeypatch):
    app.vars['openings'].set(json.dumps([rectangle()]));app.vars['opening_sectors'].set('80;100')
    path=tmp_path/'caso.json';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(path))
    app.guardar_caso();data=json.loads(path.read_text(encoding='utf-8'))
    assert data['opening_sectors']==[[80.,100.]] and data['openings']==[rectangle()]
    app.limpar();assert app.vars['openings'].get()=='[]'
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(path));app.abrir_caso();app.calcular()
    assert not app.dialogs and app.last_verif.status=='BETA_PENDING'
    assert len(app.last_verif.effective_sectors_deg)==2
    # New d changes sectors/scope from source geometry, without stale angles.
    app.vars['laje_d'].set('.08');assert app._fresh_result() is None
    app.calcular();assert app.last_verif.opening_records[0]['active'] is False
    assert len(app.last_verif.effective_sectors_deg)==1


def test_opening_collision_prevents_reuse_of_old_pass(app):
    app.calcular();app.vars['openings'].set(json.dumps([dict(rectangle(),x=.1)]));app.calcular()
    assert app.last_verif is None and app.dirty and app.dialogs
    assert app._fresh_result() is None


class CanvasStub:
    def __init__(self):self.calls=[];self.options={}
    def winfo_width(self):return 800
    def winfo_height(self):return 460
    def configure(self,**kw):self.options.update(kw)
    def delete(self,*args):self.calls=[]
    def __getattr__(self,name):
        if name.startswith('create_'):
            def record(*args,**kw):self.calls.append((name,args,kw));return len(self.calls)
            return record
        raise AttributeError(name)


@pytest.fixture
def controller():
    interpreter=tk.Tcl();o=OpeningEditor.__new__(OpeningEditor);o.tk=interpreter.tk;o._w='.';o.master=interpreter
    o.items=[rectangle()];o.selected='A1';o.context=CTX.copy();o.manual_sectors=[];o.result=None
    o._loading=False;o._form_dirty=False;o._selecting=False;o._drag=None;o._drawing=False;o._new_start=None;o._transform=(300,220,100)
    o.fields={k:tk.StringVar(master=interpreter) for k in ['id','shape','x','y','width','height','diameter']}
    o.widgets={k:ViewStub() for k in o.fields};o.status=tk.StringVar(master=interpreter);o.sector_text=tk.StringVar(master=interpreter)
    o.status_label=ViewStub();o.ok=ViewStub();o.canvas=CanvasStub();o._refresh_list=lambda:None
    o.destroyed=False
    def destroy():o.destroyed=True
    o.destroy=destroy;o._load_fields()
    return o


def event(o,x,y):
    px,py=o._pixel(x,y);return SimpleNamespace(x=px,y=py)


def test_canvas_move_updates_physical_geometry_and_recomputes_angles(controller):
    o=controller;initial=copy.deepcopy(o.items)
    o._press(event(o,1,0));o._motion(event(o,1.3,.2));o._release(event(o,1.3,.2))
    assert o.items[0]['x']==pytest.approx(1.3) and o.items[0]['y']==pytest.approx(.2)
    assert initial[0]['x']==1 and o.sector_text.get()
    assert o.ok.options['state']=='normal'


def test_canvas_resize_and_draw_new_rectangle(controller):
    o=controller;o._press(event(o,1.2,.2));assert o._drag[1]=='resize'
    o._motion(event(o,1.3,.3));o._release(event(o,1.3,.3))
    assert (o.items[0]['width'],o.items[0]['height'])==pytest.approx((.6,.6))
    o._begin_drawing();o._press(event(o,.7,.7));o._release(event(o,1.1,1.1))
    assert len(o.items)==2 and o.items[1]['id']=='A2'
    assert o.items[1]['width']==pytest.approx(.4) and o.items[1]['x']==pytest.approx(.9)
    assert not o._drawing


def test_invalid_location_is_visible_and_cannot_be_applied(controller):
    o=controller;o.items[0]['x']=.1;o._draw()
    assert o.ok.options['state']=='disabled' and 'pilar' in o.status.get()
    o._save();assert o.result is None and not o.destroyed
    assert any(name=='create_rectangle' for name,args,kw in o.canvas.calls)


def test_unapplied_invalid_measure_cannot_silently_save_old_geometry(controller):
    o=controller;o.fields['width'].set('abc');o._form_dirty=True;o._save()
    assert o.result is None and not o.destroyed and o._form_dirty


def test_controller_save_copies_and_escape_cancels(controller):
    o=controller;o._save();assert o.destroyed and o.result==[rectangle()]
    o.items[0]['x']=8;assert o.result[0]['x']==1


def test_deleted_all_openings_can_be_saved(controller):
    o=controller;o._delete();o._save();assert o.result==[]

@pytest.mark.parametrize('position',['bordo','canto'])
def test_new_default_opening_is_inside_free_edges(controller,position):
    o=controller;o.items=[];o.selected=None;o.context=dict(CTX,position=position)
    o.side=tk.StringVar(master=o,value='+Y');o.gap=tk.StringVar(master=o,value='.6')
    o._add('rectangular')
    assert len(o.items)==1 and o.ok.options['state']=='normal'
