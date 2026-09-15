"""Actual Tcl/controller regressions; these do not claim a native visual review."""
import json
import pytest
from test_interface_and_exports import app
from test_desktop_workflow import desktop
from test_longitudinal import auto_draft
from test_batch_gui import batch_dialogs
from test_connection_gui import dialogs,collection,Widget
from test_batch_workflow import many
from punching.longitudinal import DERIVED_KEYS
from Punching_EC2_GUI import DEFAULTS,EXAMPLES


def load_auto(app):
    app._loading=True
    for key,value in auto_draft().items():app.vars[key].set(value)
    app._loading=False;app._mark_dirty();app._update_derived()


def test_diameter_edit_refreshes_areas_depths_and_invalidates_exports(desktop):
    load_auto(desktop);desktop._sync_controls()
    assert desktop.longitudinal_panel.visible
    for k in DERIVED_KEYS:assert desktop.input_widgets[k].options['state']=='readonly'
    desktop.calcular();assert not desktop.dirty and desktop._fresh_result()
    assert float(desktop.vars['laje_d'].get())==pytest.approx(.208)
    desktop.vars['long_x_extra_mm'].set('16');assert desktop._fresh_result() is None
    desktop._update_derived();desktop.calcular()
    assert desktop.last_verif.snapshot()['inputs']['laje_As_lx_cm2pm']==pytest.approx(13.980087308)
    assert desktop.last_verif.snapshot()['values']['dx']==pytest.approx(.212)
    desktop.vars['long_mode'].set('manual');desktop._sync_controls()
    assert not desktop.longitudinal_panel.visible and desktop.input_widgets['laje_dx'].options['state']=='normal'
    desktop.vars['laje_dx'].set('');desktop.vars['laje_dy'].set('');desktop.vars['laje_d'].set('.23')
    desktop.calcular();assert desktop.last_verif.d==.23 and 'longitudinal_trace' not in desktop._fresh_result()


def test_invalid_automatic_geometry_clears_stale_readouts_without_using_manual_numbers(desktop):
    load_auto(desktop);desktop.calcular()
    desktop.vars['long_h_mm'].set('');desktop._update_derived()
    assert all(desktop.vars[k].get()=='' for k in DERIVED_KEYS)
    desktop.calcular();assert desktop.last_verif is None and desktop._fresh_result() is None
    assert 'Espessura' in desktop.var_resultado.get()


def test_individual_save_open_preserves_automatic_mode_layers_and_exact_calculation(app,tmp_path,monkeypatch):
    import Punching_EC2_GUI as gui
    path=tmp_path/'automatic_case.json'
    load_auto(app);app.vars['long_outer_axis'].set('y')
    monkeypatch.setattr(gui.filedialog,'asksaveasfilename',lambda **kw:str(path))
    app.guardar_caso();assert path.exists()
    app.limpar()
    monkeypatch.setattr(gui.filedialog,'askopenfilename',lambda **kw:str(path))
    app.abrir_caso();app.calcular()
    assert app.vars['long_mode'].get()=='automatic' and app.vars['long_outer_axis'].get()=='y'
    assert app.last_verif.d==pytest.approx(.208)
    assert app._fresh_result()['longitudinal_trace']['axes']['x']['label']=='Ø10 // 200 + Ø12 // 200'
    assert not app.dialogs


def test_automatic_examples_reach_the_gui_in_automatic_mode(app):
    name='Armadura longitudinal - base e reforço, altura útil automática'
    assert EXAMPLES[name]['long_mode']=='automatic'
    app.var_exemplo.set(name);app.carregar_exemplo();app.calcular()
    assert app._fresh_result()['values']['d']==pytest.approx(.208)
    assert app._fresh_result()['longitudinal_trace']


def test_bulk_dialog_returns_only_selected_layout_fields(batch_dialogs,collection):
    b=many();k=next(iter(b.cases));d=batch_dialogs.BulkEditDialog(collection,b,[k])
    for name,value in {'long_mode':'automatic','long_h_mm':'250','long_cover_mm':'30','long_x_extra_mm':'16'}.items():
        d.enabled[name].set(True);d.values[name].set(value)
    d.mode.set('Atualizar os campos assinalados');d._apply()
    assert d.result['fields']==dict(long_mode='automatic',long_h_mm='250',long_cover_mm='30',long_x_extra_mm='16')
    assert not d.result['only_empty']
