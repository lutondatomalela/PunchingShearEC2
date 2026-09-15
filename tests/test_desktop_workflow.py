"""Interaction regressions with real Tcl variables; no native visual assertion."""
import json
from types import SimpleNamespace
import tkinter as tk
import pytest
import Punching_EC2_GUI as gui
from punching.ui import CHOICES, ChoiceBinding, field_states
from punching.ui_dialogs import search_key
from test_interface_and_exports import app, ViewStub
from test_opening_gui import CanvasStub, controller


class Control(ViewStub):
    def __init__(self):super().__init__();self.visible=True
    def grid(self,**kw):self.visible=True
    def grid_remove(self):self.visible=False


@pytest.fixture
def desktop(app):
    app.master=None
    app.input_widgets={key:Control() for key in gui.DEFAULTS}
    app.field_rows={key:Control() for key in gui.DEFAULTS}
    app.method_panels={key:Control() for key in CHOICES['beta_mode']}
    app.longitudinal_panel=Control();app.footing_panel=Control();app.opening_button=Control();app.options_opening_button=Control()
    app.export_buttons=[Control() for _ in range(5)]
    for name in ('var_longitudinal','var_method_hint','var_context','var_openings','var_geometry_hint','var_beta_value','var_perimeter_value','var_usage_value'):
        setattr(app,name,tk.StringVar(master=app))
    app.var_edit_column=tk.BooleanVar(master=app,value=False);app.drag_mode=None
    app._sync_controls();app._result_tools(False)
    return app


@pytest.mark.parametrize('code',['ec2','simplificado','manual'])
def test_choice_labels_keep_canonical_saved_values(desktop,code,tmp_path,monkeypatch):
    app=desktop;binding=ChoiceBinding(app,app.vars['beta_mode'],CHOICES['beta_mode'])
    app.vars['beta_manual'].set('1,40');app.vars['beta_reference'].set('Ensaio de interface; fator prescrito.')
    app.vars['simplified_applicable'].set(True)
    binding.select(CHOICES['beta_mode'][code]);app.tk.eval('update idletasks')
    assert app.vars['beta_mode'].get()==code
    assert binding.display.get()==CHOICES['beta_mode'][code]
    assert [k for k,p in app.method_panels.items() if p.visible]==[code]
    assert app.input_widgets['beta_manual'].options['state']==('normal' if code=='manual' else 'disabled')
    path=tmp_path/'case.json';monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(path))
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(path))
    app.guardar_caso();assert json.loads(path.read_text())['beta_mode']==code
    app.limpar();app.abrir_caso();app.tk.eval('update idletasks')
    assert binding.display.get()==CHOICES['beta_mode'][code]
    assert app.vars['beta_manual'].get()=='1.4'
    binding.close();app.vars['beta_mode'].set('ec2')


def test_manual_value_does_not_switch_or_override_selected_method(desktop):
    app=desktop;app.calcular();ec2_beta=app.last_verif.beta
    app.vars['beta_manual'].set('1.8');app.vars['beta_reference'].set('Ensaio apenas.')
    app.calcular()
    assert app.vars['beta_mode'].get()=='ec2' and app.last_verif.beta==ec2_beta
    app.vars['beta_mode'].set('manual');app.calcular()
    assert app.last_verif.beta==1.8 and app.var_beta_value.get()=='1.800'
    assert 'Referência registada' in app.var_method_hint.get()
    app.vars['beta_reference'].set('');app.calcular()
    assert app.last_verif is None and all(b.options['state']=='disabled' for b in app.export_buttons)


def test_inactive_draft_is_retained_but_does_not_block_ec2(desktop):
    app=desktop;app.vars['beta_manual'].set('valor incompleto')
    app.calcular();assert app.last_verif.status=='PASS_WITHOUT'
    assert app.vars['beta_manual'].get()=='valor incompleto'
    app.vars['beta_mode'].set('manual');app.calcular()
    assert app.last_verif is None and app.dialogs


def test_dirty_results_and_export_controls_track_the_actual_execution(desktop):
    app=desktop;assert all(b.options['state']=='disabled' for b in app.export_buttons)
    app.calcular();assert all(b.options['state']=='normal' for b in app.export_buttons)
    assert app.var_beta_value.get()!='—' and app.var_usage_value.get()!='—'
    app.vars['V_Ed'].set('700')
    assert app.tree_summary.get_children()==[] and app.tree_steel.get_children()==[]
    assert app.var_beta_value.get()==app.var_usage_value.get()=='—'
    assert all(b.options['state']=='disabled' for b in app.export_buttons)
    app.calcular();assert app.last_verif is not None and not app.dirty
    assert all(b.options['state']=='normal' for b in app.export_buttons)
    app.limpar();assert app.var_beta_value.get()=='—' and app.last_verif is None


def test_pending_beta_keeps_geometry_and_report_without_implying_pass(desktop):
    app=desktop;app.vars['pilar_tipo'].set('bordo');app.vars['edge_distance_m'].set('0.4');app.calcular()
    assert app.last_verif.status=='BETA_PENDING'
    assert app.var_beta_value.get()==app.var_usage_value.get()=='—'
    assert app.var_perimeter_value.get()!='—'
    assert all(b.options['state']=='normal' for b in app.export_buttons)


def test_conditional_fields_do_not_trap_geometry_or_change_declarations(desktop):
    app=desktop
    assert not app.field_rows['edge_perp_interior'].visible and not app.field_rows['corner_interior'].visible
    assert not app.field_rows['allow_biaxial_envelope'].visible
    app.vars['pilar_tipo'].set('bordo');app.vars['edge_distance_m'].set('0.343');app.tk.eval('update idletasks')
    assert app.field_rows['edge_perp_interior'].visible
    app.vars['pilar_tipo'].set('interior');app.tk.eval('update idletasks')
    assert app.input_widgets['edge_distance_m'].options['state']=='normal'
    app.vars['edge_distance_m'].set('0');app.vars['pilar_forma'].set('circular');app.tk.eval('update idletasks')
    assert not app.field_rows['pilar_c2'].visible
    assert not app.field_rows['interior_beta_method'].visible
    assert app.vars['pilar_c2'].get()=='0.40'
    assert not app.vars['allow_biaxial_envelope'].get() and not app.vars['simplified_applicable'].get()


def test_derived_depth_and_footing_fields_remain_accessible(desktop):
    app=desktop;app.vars['laje_dx'].set('0.19');app.vars['laje_dy'].set('0.21');app.tk.eval('update idletasks')
    assert app.input_widgets['laje_d'].options['state']=='readonly'
    assert float(app.vars['laje_d'].get())==pytest.approx(.2)
    app.vars['laje_dy'].set('');app.tk.eval('update idletasks')
    assert app.input_widgets['laje_d'].options['state']=='normal'
    app.vars['is_sapata'].set(True);app.vars['footing_shape'].set('circular');app.tk.eval('update idletasks')
    assert app.footing_panel.visible and app.field_rows['footing_diameter'].visible
    assert not app.field_rows['footing_bx'].visible and not app.field_rows['footing_by'].visible
    assert app.opening_button.options['state']=='disabled'
    app.vars['is_sapata'].set(False);app.tk.eval('update idletasks')
    assert not app.footing_panel.visible and app.opening_button.options['state']=='normal'


class PlanCanvas(CanvasStub):
    def __init__(self):super().__init__();self.hits=()
    def find_overlapping(self,*args):return self.hits
    def gettags(self,item):return ('handle_c1',) if item==1 else ()


def test_column_edit_requires_explicit_mode_and_a_handle_hit(desktop):
    app=desktop;app.canvas_scheme=PlanCanvas();app._transform=(300,200,100)
    app.canvas_scheme.hits=(1,);point=SimpleNamespace(x=330,y=200)
    app._on_canvas_press(point);app._on_canvas_drag(point)
    assert app.vars['pilar_c1'].get()=='0.40'
    app.var_edit_column.set(True);app.canvas_scheme.hits=();app._on_canvas_press(point);app._on_canvas_drag(point)
    assert app.vars['pilar_c1'].get()=='0.40'
    app.canvas_scheme.hits=(1,);app._on_canvas_press(point);app._on_canvas_drag(point)
    assert float(app.vars['pilar_c1'].get())==pytest.approx(.6)
    app._on_canvas_release();assert app.drag_mode is None and app._drag_transform is None


def test_small_geometry_view_uses_actual_canvas_bounds(desktop):
    app=desktop;app.canvas_scheme=PlanCanvas();app.canvas_scheme.winfo_height=lambda:205
    gui.PuncoamentoApp._draw_scheme(app)
    ys=[]
    for name,args,kw in app.canvas_scheme.calls:
        if name in ('create_line','create_rectangle','create_oval'):ys.extend(args[1::2])
    assert ys and min(ys)>=0 and max(ys)<=205


def test_opening_editor_does_not_claim_to_assess_beta(controller):
    controller._draw()
    assert 'Setor considerado' in controller.status.get()
    assert 'beta por fundamentar' not in controller.status.get()


def test_catalogue_search_accepts_unaccented_portuguese():
    assert search_key('EXCENTRICIDADE / flexão')=='excentricidade / flexao'
