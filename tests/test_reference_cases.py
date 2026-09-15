"""Referências independentes: EC2 6.4, AC:2012 e A1:2019.

Resultados numéricos calculados com expressões fechadas/integração independente;
as conclusões não são verificadas por procurar palavras vagas no relatório.
"""
import math
import pytest
from punching.core import PuncoamentoEC2
from punching import geometry as geo
from punching.reports import sections,text_report


def inputs(**changes):
    p=dict(laje_d=.2,betão_fck=30.,aço_fyk=500.,aço_fywk=500.,
           pilar_tipo='interior',pilar_forma='retangular',V_Ed=300000.,
           pilar_c1=.4,pilar_c2=.4,laje_As_lx_cm2pm=10.,laje_As_ly_cm2pm=10.)
    p.update(changes);return p


def run(**changes):
    v=PuncoamentoEC2(**inputs(**changes));v.verificar_puncoamento();return v


@pytest.mark.parametrize('position,expected',[
    ('interior',1.6+.8*math.pi),('bordo',1.2+.4*math.pi),('canto',.8+.2*math.pi)])
def test_u1_exact_ec2(position,expected):
    v=run(pilar_tipo=position,M_Edx=30000,M_Edy=30000)
    assert v.u1==pytest.approx(expected,abs=1e-12)


@pytest.mark.parametrize('position,expected',[
    ('bordo',.8+.4*math.pi),('canto',.4+.2*math.pi)])
def test_reduced_perimeter_fig_620(position,expected):
    v=run(pilar_tipo=position,M_Edx=30000,M_Edy=30000)
    assert v.u1_star==pytest.approx(expected,abs=1e-12)


def test_edge_audit_false_pass_corrected():
    v=run(pilar_tipo='bordo',M_Edx=30000.)
    assert v.beta==pytest.approx(1.1944922648241716)
    assert v.v_Ed_u1==pytest.approx(.7293459930906426)
    assert v.v_Rd_c==pytest.approx(.5918908978393127)
    assert v.status=='DETAIL_PENDING'
    assert v.armadura_necessaria is True


def test_corner_audit_geometry():
    v=run(pilar_tipo='canto',V_Ed=150000.,M_Edx=15000.,M_Edy=15000.)
    assert v.v_Ed_u1==pytest.approx(.7293459930906426)
    assert v.beta==pytest.approx(1.388984529648343)


def test_edge_u0_axes_of_interface():
    v=run(pilar_tipo='bordo',pilar_c1=.25,pilar_c2=.70,M_Edx=30000.)
    assert v.u0==pytest.approx(.85)


def test_edge_moment_static_and_k_axes():
    v=run(pilar_tipo='bordo',pilar_c1=.3,pilar_c2=.6,M_Edx=30000.,M_Edy=10000.)
    # Normative c1=0.6 perpendicular, c2=0.3 parallel to edge.
    wy=.3**2/4+.6*.3+4*.6*.2+8*.2**2+math.pi*.2*.3
    assert v.beta_terms['Wy']==pytest.approx(wy)
    assert v.beta_terms['k']==pytest.approx(.60) # c_perp / (2 c_parallel) = 1


@pytest.mark.parametrize('c1,c2,d',[(.4,.4,.2),(.25,.7,.22),(.8,.3,.35)])
def test_W1_closed_form_641(c1,c2,d):
    actual=geo.stats(geo.contour(c1,c2,'retangular','interior',2*d))['Wy']
    expected=c1*c1/2+c1*c2+4*c2*d+16*d*d+2*math.pi*d*c1
    assert actual==pytest.approx(expected,abs=1e-11)


def test_uniaxial_beta_639():
    v=run(M_Edy=90000.,interior_beta_method='ec2_639')
    expected=1+.6*(90000/300000)*(1.6+.8*math.pi)/(1.2+.16*math.pi)
    assert v.beta==pytest.approx(expected)


def test_circular_beta_642():
    v=run(pilar_forma='circular',M_Edx=30000.,M_Edy=40000.)
    assert v.beta==pytest.approx(1+.6*math.pi*(50000/300000)/1.2)
    assert v.u1==pytest.approx(math.pi*1.2)


def test_biaxial_rotation_preserves_result():
    a=run(pilar_c1=.3,pilar_c2=.8,M_Edx=15000.,M_Edy=40000.)
    b=run(pilar_c1=.8,pilar_c2=.3,M_Edx=40000.,M_Edy=15000.)
    assert a.beta==pytest.approx(b.beta)
    assert a.v_Ed_u1==pytest.approx(b.v_Ed_u1)


def test_outward_edge_distinguishes_uniaxial_from_biaxial_combination():
    v=run(pilar_tipo='bordo',edge_perp_interior=False,M_Edx=-30000.)
    assert v.beta_terms['equation']=='6.39' and v.beta is not None
    v=run(pilar_tipo='bordo',edge_perp_interior=False,M_Edx=-30000.,M_Edy=90000.)
    assert v.status=='BETA_PENDING'
    assert v.beta is None and not v.checks


def test_general_centroid_against_numerical_line_integration():
    # Independent midpoint quadrature over the U path of a flush edge column.
    d=.2;c=.4;r=2*d;N=16000
    points=[]
    for i in range(N):
        t=(i+.5)/N
        points.extend([(.6,-.2+.4*t,.4/N),(-.6,.2-.4*t,.4/N),(.2-.4*t,.6,.4/N)])
        theta=math.pi*t/2
        points.extend([(.2+r*math.cos(theta),.2+r*math.sin(theta),r*math.pi/2/N),
                       (-.2+r*math.cos(theta+math.pi/2),.2+r*math.sin(theta+math.pi/2),r*math.pi/2/N)])
    u=sum(w for x,y,w in points);cy=sum(y*w for x,y,w in points)/u
    wx=sum(abs(y-cy)*w for x,y,w in points)
    result=geo.stats(geo.contour(c,c,'retangular','bordo',r,d))
    assert result['cy']==pytest.approx(cy,abs=1e-8)
    assert result['Wx']==pytest.approx(wx,abs=1e-8)


def test_independent_depths_and_rho():
    v=run(laje_dx=.19,laje_dy=.21,laje_As_lx_cm2pm=12.,laje_As_ly_cm2pm=8.)
    assert v.rho_l==pytest.approx(math.sqrt(12/10000/.19*8/10000/.21))


def test_correct_amendment_coefficients():
    v=run(V_Ed=1000000.)
    assert v.v_Rd_max==pytest.approx(4.224)
    assert v.v_Rd_cs_max==pytest.approx(.887836346758969)
    assert v.status=='FAIL_MAX'


def test_failed_face_has_no_fictitious_u1_or_steel():
    v=run(V_Ed=2000000.);r=v.snapshot()
    assert v.status=='FAIL_U0';assert v.v_Ed_u1 is None
    assert v.armadura_necessaria is None
    assert not r['reinforcement_rows']
    assert 'Não foi obtida uma solução de armadura aprovada' in text_report(r)
    assert 'Não é necessária armadura específica' not in text_report(r)


def test_kmax_failure_never_becomes_reinforcement_proposal():
    v=run(V_Ed=1000000.);r=v.snapshot()
    assert r['status']=='FAIL_MAX';assert r['values']['Asw_sr_req'] is None
    assert r['reinforcement_rows']==[]


@pytest.mark.parametrize('diameter',[10,12,16])
def test_adopted_rows_resistance_and_detailing(diameter):
    v=run(V_Ed=600000,reinforcement_diameter_mm=diameter)
    assert v.status=='DETAIL_PENDING'
    assert v.v_Rd_cs_provided>=v.v_Ed_u1
    assert v.n_perimetros>=2
    assert v.reinforcement_rows[-1]['r']>=v.r_out_face-1.5*v.d-1e-9
    for row in v.reinforcement_rows:
        assert row['sr']<=.75*v.d+1e-12
        assert row['st']<=row['st_max']+1e-12
        assert row['Asw_m2']>=row['Asw_required_m2']-1e-12
        assert math.pi*(diameter/1000)**2/4>=row['Asw_min_branch_m2']-1e-12
        assert row['passed']


def test_anchorage_confirmation_is_required_for_pass_with_steel():
    assert run(V_Ed=600000).status=='DETAIL_PENDING'
    assert run(V_Ed=600000,anchorage_confirmed=True).status=='PASS_WITH'


def test_opening_sector_union_and_exact_circle_length():
    segments=geo.contour(.4,.4,'circular','interior',.4)
    ss=geo.sectors_normalized([(350,10),(0,30),(20,40)])
    effective=geo.trim_sectors(segments,ss)
    assert sum(x.length for x in effective)==pytest.approx(.6*math.radians(310),abs=1e-12)


def test_effective_contours_not_only_u1():
    a=run(V_Ed=420000.,opening_sectors=[(-20,20)],beta_mode='manual',beta_manual=1.2,beta_reference='Ensaio de geometria e distribuição com fator prescrito, sem aprovação do fator para projeto.')
    assert a.status=='DETAIL_PENDING'
    assert a.u1_eff<a.u1
    assert a.u0<1.6
    assert a.r_out_face>=2*a.d
    assert a.reinforcement_rows[-1]['r']>=a.r_out_face-1.5*a.d-1e-9


def test_no_resistant_contour_is_invalid_not_pass():
    v=run(pilar_tipo='canto',opening_sectors=[(-89,179)],M_Edx=15000.,M_Edy=15000.)
    assert v.status=='INVALID'
    assert v.snapshot()['badge']!='VERIFICA'


def test_rectangular_area_with_rounded_corners():
    assert geo.area(.4,.4,'retangular',.4)==pytest.approx(1.302654824574367)


def test_footing_audit_critical_before_2d():
    diameter=2*math.sqrt(1000/(660*math.pi))
    v=run(pilar_forma='circular',is_sapata=True,V_Ed=1000000.,
          laje_As_lx_cm2pm=2.,laje_As_ly_cm2pm=2.,sigma_gd_kpa=660.,
          footing_shape='circular',footing_diameter=diameter)
    assert v.status=='REQUIRES_REINFORCEMENT'
    assert v.v_Ed_u1==pytest.approx(.33629119243246086)
    assert v.a_governing==pytest.approx(.200571,abs=1e-6)
    assert max(p['ratio'] for p in v.footing_scan)==pytest.approx(1.22593157594,rel=1e-9)
    assert min(p['V_red'] for p in v.footing_scan)>=0


def test_footing_critical_scan_with_clipped_free_edges():
    v=run(is_sapata=True,V_Ed=400000.,laje_d=.3,footing_bx=1.,footing_by=1.)
    assert v.status=='PASS_WITHOUT'
    assert v.u1_eff<v.u1
    assert all(p['V_red']>=0 and p['u']>=0 for p in v.footing_scan)
    assert all(p['area']<=1+1e-9 for p in v.footing_scan)


def test_overlap_area_against_independent_square_corner_integral():
    # .4 square dilated by .4, intersected with a 1.0 square.
    N=40000;step=.5/N
    expected=4*sum(min(.5,.2+math.sqrt(max(0.,.16-max(0.,(i+.5)*step-.2)**2)))*step for i in range(N))
    assert geo.overlap_area(.4,.4,'retangular',.4,'retangular',1.,1.)==pytest.approx(expected,abs=1e-8)


def test_snapshot_is_detached_and_repeated_runs_reset():
    v=run(V_Ed=600000.);a=v.snapshot();a['inputs']['V_Ed']=1.;a['values']['beta']=0
    assert v.snapshot()['inputs']['V_Ed']==600000.
    n=len(v.reinforcement_rows);before=v.snapshot()['values'];v.verificar_puncoamento()
    assert v.snapshot()['values']==before
    assert len(v.reinforcement_rows)==n


@pytest.mark.parametrize('changes',[
    {'laje_d':0},{'laje_d':float('nan')},{'V_Ed':float('inf')},{'V_Ed':0},{'V_Ed':-1},
    {'betão_fck':100},{'gamma_C':0},{'laje_As_lx_cm2pm':-1},
    {'pilar_tipo':'unknown'},{'pilar_forma':'unknown'},{'beta_mode':'unknown'},
    {'beta_mode':'fib'},{'beta_mode':'simplificado'},
    {'u1_ineffective':4.113274122871834},{'u1_ineffective':4.613274122871834},
    {'opening_sectors':[(0,180),(180,360)]},{'opening_sectors':[(20,20)]},
    {'reinforcement_diameter_mm':14},{'reinforcement_sr_m':.3},{'reinforcement_s0_m':.15},
    {'pilar_forma':'circular','pilar_tipo':'bordo'},
    {'pilar_c1':1.6,'pilar_c2':.4},
    {'is_sapata':True},{'is_sapata':True,'footing_bx':1.,'footing_by':1.,'M_Edx':1000},
    {'is_sapata':True,'footing_bx':1.,'footing_by':1.,'sigma_gd_kpa':900},
    {'laje_dx':.2,'laje_dy':.3},{'edge_perp_interior':'False'},
    {'footing_bx':float('nan')},
])
def test_invalid_or_unvalidated_inputs_are_rejected(changes):
    with pytest.raises(ValueError):PuncoamentoEC2(**inputs(**changes))


def test_simplified_beta_is_not_one_when_moments_are_zero():
    v=run(beta_mode='simplificado',simplified_applicable=True)
    assert v.beta==pytest.approx(1.15)
