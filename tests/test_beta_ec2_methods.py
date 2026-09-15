"""Independent EC2 references and audit-trail checks for version 1.7.

The two-direction sum is tested as an explicitly selected conservative model,
not labelled as a biaxial equation printed in EC2 for an edge/corner column.
"""
import math
import json
from pathlib import Path
import pytest
from test_reference_cases import run,inputs
from punching.core import PuncoamentoEC2
from punching.reports import text_report,export_xlsx


@pytest.mark.parametrize('mx,my',[(15000,40000),(-15000,40000),(15000,-40000),(0,40000),(15000,0),(0,0),(1e-9,40000)])
def test_643_literal_axes_and_limits_for_non_square_column(mx,my):
    v=run(pilar_c1=.3,pilar_c2=.8,M_Edx=mx,M_Edy=my)
    expected=1+1.8*math.sqrt((my/300000/1.6)**2+(mx/300000/1.1)**2)
    assert v.beta==pytest.approx(expected,rel=1e-12)
    assert v.beta_terms['equation']=='6.43'
    assert v.beta_terms['basis']=='normative_approximation'
    assert v.beta_terms['bx']==pytest.approx(1.1)
    assert v.beta_terms['by']==pytest.approx(1.6)


def test_643_does_not_switch_formula_near_zero_second_moment():
    a=run(pilar_c1=.3,pilar_c2=.8,M_Edy=40000,M_Edx=0)
    b=run(pilar_c1=.3,pilar_c2=.8,M_Edy=40000,M_Edx=1e-8)
    assert a.beta==pytest.approx(b.beta,abs=1e-12)
    assert a.beta_terms['equation']==b.beta_terms['equation']=='6.43'


def test_639_closed_W_k_and_moment_reference():
    v=run(pilar_c1=.3,pilar_c2=.8,M_Edy=40000,interior_beta_method='ec2_639')
    W=.3**2/2+.3*.8+4*.8*.2+16*.2**2+2*math.pi*.2*.3
    u=2*(.3+.8)+4*math.pi*.2
    expected=1+.45*(40000/300000)*u/W
    assert v.beta==pytest.approx(expected)
    assert v.beta_terms['Wy']==pytest.approx(W)
    assert v.beta_terms['kx']==.45
    assert v.beta_terms['My_control_Nm']==pytest.approx(40000)
    assert v.beta_terms['Mx_control_Nm']==0


def sampled_contour(c1,c2,d,corner=False):
    # Independent midpoint quadrature of the physical U or corner path.
    N=12000;a=2*d;hx=c1/2;hy=c2/2;points=[]
    for i in range(N):
        t=(i+.5)/N
        points.extend([(hx+a,-hy+c2*t,c2/N),(hx-c1*t,hy+a,c1/N)])
        angle=math.pi*t/2
        points.append((hx+a*math.cos(angle),hy+a*math.sin(angle),a*math.pi/2/N))
        if not corner:
            points.append((-hx-a,hy-c2*t,c2/N))
            points.append((-hx+a*math.cos(angle+math.pi/2),hy+a*math.sin(angle+math.pi/2),a*math.pi/2/N))
    u=sum(w for x,y,w in points)
    cx=sum(x*w for x,y,w in points)/u;cy=sum(y*w for x,y,w in points)/u
    wx=sum(abs(y-cy)*w for x,y,w in points);wy=sum(abs(x-cx)*w for x,y,w in points)
    return u,cx,cy,wx,wy


def test_outward_uniaxial_edge_against_independent_quadrature_and_statics():
    v=run(pilar_tipo='bordo',pilar_c1=.3,pilar_c2=.5,laje_d=.22,
          V_Ed=200000,M_Edx=-18000,edge_perp_interior=False)
    u,cx,cy,wx,wy=sampled_contour(.3,.5,.22)
    mx=-18000-200000*cy
    expected=1+(2/3)*abs(mx)/200000*u/wx
    assert v.beta==pytest.approx(expected,rel=1e-8)
    t=v.beta_terms
    assert t['Mx_control_Nm']==pytest.approx(mx,abs=1e-4)
    assert t['ky']==pytest.approx(2/3)
    assert t['basis']=='normative_expression' and t['biaxial'] is False
    assert v.u1_star is None
    assert t['steps'][-1]['value']==v.beta
    assert any(s['symbol']=='Mx,G' and s['value']==pytest.approx(mx/1000,abs=1e-7) for s in t['steps'])


def test_corner_biaxial_sum_uses_actual_centroid_and_normative_k():
    v=run(pilar_tipo='canto',pilar_c1=.3,pilar_c2=.5,laje_d=.22,
          V_Ed=60000,M_Edx=-4000,M_Edy=-6000,corner_interior=False,allow_biaxial_envelope=True)
    u,cx,cy,wx,wy=sampled_contour(.3,.5,.22,corner=True)
    mx=-4000-60000*cy;my=-6000-60000*cx
    expected=1+.48*abs(my)/60000*u/wy+(2/3)*abs(mx)/60000*u/wx
    assert v.beta==pytest.approx(expected,rel=2e-8)
    assert v.beta_terms['basis']=='conservative_combination'
    assert v.beta_terms['kx']==pytest.approx(.48)
    assert v.beta_terms['ky']==pytest.approx(2/3)
    assert v.u1_star is None
    assert 'não uma expressão biaxial literal' in text_report(v.snapshot())


@pytest.mark.parametrize('position',['bordo','canto'])
def test_general_biaxial_combination_requires_explicit_selection(position):
    changes=dict(pilar_tipo=position,M_Edx=-5000,M_Edy=-7000,
                 edge_perp_interior=False,corner_interior=False,V_Ed=60000)
    pending=run(**changes)
    assert pending.status=='BETA_PENDING' and pending.beta is None and not pending.checks
    calculated=run(**changes,allow_biaxial_envelope=True)
    assert calculated.beta is not None and calculated.beta_terms['biaxial'] is True
    assert calculated.beta_terms['equation']=='6.39'


def test_general_combination_does_not_enable_setback_or_openings():
    for changes in [dict(pilar_tipo='bordo',edge_distance_m=.343),dict(opening_sectors=[(-20,20)])]:
        v=run(**changes,allow_biaxial_envelope=True)
        assert v.status=='BETA_PENDING' and v.beta is None


def test_interior_639_biaxial_requires_selected_extension_or_643():
    p=dict(M_Edx=15000,M_Edy=40000,interior_beta_method='ec2_639')
    assert run(**p).status=='BETA_PENDING'
    v=run(**p,allow_biaxial_envelope=True)
    assert v.beta_terms['basis']=='conservative_combination'
    assert v.beta==pytest.approx(1+v.beta_terms['delta_beta_x']+v.beta_terms['delta_beta_y'])


@pytest.mark.parametrize('changes',[{'interior_beta_method':'auto'}, {'allow_biaxial_envelope':'True'}])
def test_invalid_method_inputs_are_rejected(changes):
    with pytest.raises(ValueError):PuncoamentoEC2(**inputs(**changes))


@pytest.mark.parametrize('file',[
    '19_interior_flexao_biaxial_643.json','20_interior_flexao_uniaxial_639.json',
    '21_bordo_excentricidade_exterior_uniaxial.json','22_bordo_exterior_combinacao_biaxial.json',
    '23_canto_exterior_combinacao_biaxial.json'])
def test_detailed_beta_trace_matches_engine_and_xlsx(file,tmp_path):
    p=json.loads((Path('examples')/file).read_text(encoding='utf-8'));v=PuncoamentoEC2(**p);v.verificar_puncoamento();r=v.snapshot()
    assert v.beta is not None
    last=r['beta_terms']['steps'][-1]
    assert last['symbol']=='beta' and last['value']==v.beta
    assert 'Substituição:' in text_report(r)
    export_xlsx(r,tmp_path/'trace.xlsx')
    from openpyxl import load_workbook
    wb=load_workbook(tmp_path/'trace.xlsx')
    rows=list(wb['Beta'].values)
    assert rows[-1][0]=='beta' and rows[-1][3]==pytest.approx(v.beta)
    assert len(rows)==len(r['beta_terms']['steps'])+1
