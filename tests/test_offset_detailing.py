"""Conferência das posições propostas, com referências geométricas independentes.

Os ensaios de corrupção passam posições alteradas à conferência final do motor:
uma declaração de amarração não pode transformar essas propostas em aprovação.
"""
import copy
import math
import pytest
from punching.core import PuncoamentoEC2
from punching import detailing
from test_reference_cases import inputs


def biaxial_edge_case(**changes):
    p=inputs(laje_d=.202,pilar_tipo='bordo',pilar_c1=.25,pilar_c2=.70,
             edge_distance_m=.40,V_Ed=371000,M_Edx=-10000,M_Edy=-65000,
             laje_As_lx_cm2pm=13.98,laje_As_ly_cm2pm=13.98,anchorage_confirmed=True,
             beta_mode='manual',beta_manual=1.65,beta_reference='Ensaio numérico com beta prescrito; não constitui fundamentação do fator para projeto.')
    p.update(changes)
    v=PuncoamentoEC2(**p);v.verificar_puncoamento();return v


def open_abscissa(point,c1,c2,gap,r):
    """U analítico independente, desde o extremo direito até ao esquerdo."""
    x,y=point;hx,hy=c1/2,c2/2;side=c2+gap;edge=-hy-gap;tol=1e-7
    if abs(x-hx-r)<tol and edge-tol<=y<=hy+tol:
        return y-edge
    if x>=hx-tol and y>=hy-tol and abs(math.hypot(x-hx,y-hy)-r)<tol:
        return side+r*math.atan2(y-hy,x-hx)
    if abs(y-hy-r)<tol and -hx-tol<=x<=hx+tol:
        return side+math.pi*r/2+hx-x
    if x<=-hx+tol and y>=hy-tol and abs(math.hypot(x+hx,y-hy)-r)<tol:
        return side+c1+r*math.atan2(y-hy,x+hx)
    if abs(x+hx+r)<tol and edge-tol<=y<=hy+tol:
        return side+c1+math.pi*r+hy-y
    return None


@pytest.mark.parametrize('phi',[10,12,16])
def test_prescribed_beta_reference_positions_area_pitch_cover_and_extent(phi):
    v=biaxial_edge_case(reinforcement_diameter_mm=phi)
    assert v.status=='PASS_WITH'
    assert v.beta==1.65
    u=.25+2*(.70+.40)+2*math.pi*.202
    assert v.v_Ed_u1==pytest.approx(1.65*371000/(u*.202)/1e6)
    assert v.v_Rd_c==pytest.approx(.6579980312807339)
    assert v.Asw_sr_req==pytest.approx((v.v_Ed_u1-.75*v.v_Rd_c)*u/(1.5*(250+.25*202)))
    expected_radius=(1.65*371000/(v.v_Rd_c*.202)/1e6-.25-2*(.7+.4))/math.pi
    assert len(v.reinforcement_rows)==max(2,math.ceil((expected_radius-1.5*.202-.101)/.15)+1)
    assert v.r_out_face==pytest.approx(expected_radius)
    a=math.pi*(phi/1000)**2/4;rho_min=.08*math.sqrt(30)/500
    points=[];areas=[]
    for i,row in enumerate(v.reinforcement_rows):
        r=.101+i*.15;coords=row['coordinates'];points.extend(coords)
        assert row['r']==pytest.approx(r)
        abscissas=[open_abscissa(p,.25,.7,.4,r) for p in coords]
        assert all(s is not None for s in abscissas)
        abscissas.sort();length=.25+2*(.7+.4)+math.pi*r
        st=max([b-a for a,b in zip(abscissas,abscissas[1:])]+[2*abscissas[0],2*(length-abscissas[-1])])
        assert st<=(1.5 if r<=.404 else 2)*.202+1e-8
        assert a>=rho_min*.15*st/1.5-1e-12
        assert len(coords)*a>=max(v.Asw_sr_req*.15,rho_min*length*.15/1.5)-1e-12
        assert row['families'][0]['Asw_m2']==pytest.approx(len(coords)*a)
        assert row['families'][0]['st']==pytest.approx(st)
        assert min(y+.35+.4-phi/2000 for x,y in coords)>=.03-1e-8
        areas.append(len(coords)*a)
    actual=min(math.dist(a,b) for i,a in enumerate(points) for b in points[i+1:])
    assert actual>=phi/1000+max(.020,phi/1000,.025)-1e-8
    assert v.reinforcement_rows[-1]['r']>=v.r_out_face-1.5*.202
    capacity=min(1.5*v.v_Rd_c,.75*v.v_Rd_c+1.5*min(areas)/.15*(250+.25*202)/v.u1_eff)
    assert v.reinforcement_demands[0]['resistance_MPa']==pytest.approx(capacity)
    assert v.reinforcement_demands[0]['utilization']<=1


def test_anchorage_is_the_only_remaining_pending_item_for_valid_edge_layout():
    pending=biaxial_edge_case(anchorage_confirmed=False);approved=biaxial_edge_case()
    assert pending.status=='DETAIL_PENDING' and approved.status=='PASS_WITH'
    assert pending.reinforcement_rows==approved.reinforcement_rows
    assert pending.detail_checks==approved.detail_checks
    assert pending.checks==approved.checks
    assert all(c['passed'] for c in pending.detail_checks)


def test_alternative_contours_count_only_actual_members_and_deduplicate_inventory():
    p=inputs(pilar_tipo='bordo',pilar_c1=.25,pilar_c2=.7,edge_distance_m=.8,V_Ed=500000,anchorage_confirmed=True,
             beta_mode='manual',beta_manual=1.4,beta_reference='Ensaio de contornos alternativos com beta prescrito.')
    v=PuncoamentoEC2(**p);v.verificar_puncoamento()
    assert v.status=='PASS_WITH'
    both=0;area=math.pi*.01**2/4;provided={'fechado':[],'aberto_bordo':[]}
    for row in v.reinforcement_rows:
        coords=row['coordinates'];r=row['r']
        assert len(set(coords))==row['n_legs']
        members={}
        for family in row['families']:
            if family['kind']=='fechado':
                ids={i+1 for i,(x,y) in enumerate(coords) if abs(math.hypot(max(abs(x)-.125,0),max(abs(y)-.35,0))-r)<1e-7}
            else:
                ids={i+1 for i,p in enumerate(coords) if open_abscissa(p,.25,.7,.8,r) is not None}
            assert ids==set(family['leg_indices'])
            assert family['Asw_m2']==pytest.approx(len(ids)*area)
            provided[family['kind']].append(len(ids)*area/.15)
            members[family['kind']]=ids
        assert set.union(*members.values())==set(range(1,len(coords)+1))
        if len(members)==2:
            both+=1
            assert members['fechado'] & members['aberto_bordo']
            assert len(members['fechado'])<len(coords) and len(members['aberto_bordo'])<len(coords)
    assert both>=2
    for c in v.reinforcement_demands:
        assert c['Asw_sr_provided_m2pm']==pytest.approx(min(provided[c['contour']]))
        expected=min(v.v_Rd_cs_max,.75*v.v_Rd_c+1.5*min(provided[c['contour']])*v.f_ywd_ef/c['u'])
        assert c['resistance_MPa']==pytest.approx(expected)


@pytest.mark.parametrize('damage,failed_check',[
    ('outside_edge','cover'),('duplicate','centres'),('empty_inner','families'),
    ('missing_last','complete'),('shifted_radius','radii')])
def test_invalid_coordinates_never_approved_by_anchorage(monkeypatch,damage,failed_check):
    original=detailing.design_edge_rows
    def damaged(**config):
        rows,errors=original(**config)
        if damage=='outside_edge':rows[0]['coordinates'][0]=(0.,-1.)
        elif damage=='duplicate':rows[0]['coordinates'][1]=rows[0]['coordinates'][0]
        elif damage=='empty_inner':rows[0]['coordinates']=[]
        elif damage=='missing_last':rows.pop()
        else:rows[0]['r']+=.01
        return rows,errors
    monkeypatch.setattr(detailing,'design_edge_rows',damaged)
    v=biaxial_edge_case(anchorage_confirmed=True)
    assert v.status=='FAIL_DETAIL'
    assert any(c['id']==failed_check and not c['passed'] for c in v.detail_checks)


def test_counts_areas_and_pass_flags_are_recomputed_from_coordinates(monkeypatch):
    original=detailing.design_edge_rows
    def wrong_inventory(**config):
        rows,errors=original(**config)
        for row in rows:row.update(n_legs=99999,Asw_m2=99999,passed=True)
        return rows,errors
    monkeypatch.setattr(detailing,'design_edge_rows',wrong_inventory)
    v=biaxial_edge_case()
    assert v.status=='PASS_WITH'
    assert all(row['n_legs']==len(row['coordinates'])<99999 for row in v.reinforcement_rows)
    assert all(row['Asw_m2']==pytest.approx(len(row['coordinates'])*math.pi*.01**2/4) for row in v.reinforcement_rows)


def test_generation_failure_is_reportable_and_not_approved(monkeypatch):
    monkeypatch.setattr(detailing,'design_edge_rows',lambda **kw:([] ,['Fiada 1: distribuição impossível neste ensaio.']))
    v=biaxial_edge_case()
    assert v.status=='FAIL_DETAIL'
    assert v.reinforcement_rows==[] and v.Asw_por_perimetro is None
    assert 'distribuição impossível' in '\n'.join(v.notes)


def test_cover_incompatible_with_tangential_limit_returns_failed_detail():
    # d=0.10 gives st<=0.15 inside 2d, whereas the required distance to an
    # open end is 0.105 m; twice that distance exceeds the admissible pitch.
    v=biaxial_edge_case(laje_d=.1,pilar_c1=.7,pilar_c2=.25,cover_mm=100,
                       V_Ed=200000,M_Edx=0,M_Edy=0,beta_manual=1.4)
    assert v.status=='FAIL_DETAIL' and not v.reinforcement_rows
    assert any('recobrimento' in note and note.startswith('Fiada ') for note in v.notes)
    assert any(c['id']=='complete' and not c['passed'] for c in v.detail_checks)


def test_offset_opening_clips_members_and_preserves_clearance():
    v=biaxial_edge_case(opening_sectors=[[20,35]])
    assert v.status=='PASS_WITH'
    points=[p for row in v.reinforcement_rows for p in row['coordinates']]
    assert all(not 20-1e-7<=math.degrees(math.atan2(y,x))%360<=35+1e-7 for x,y in points)
    assert min(math.dist(a,b) for i,a in enumerate(points) for b in points[i+1:])>=.035-1e-8


def test_detail_snapshot_does_not_alias_live_rows():
    v=biaxial_edge_case();snapshot=v.snapshot();old=copy.deepcopy(snapshot)
    snapshot['reinforcement_rows'][0]['families'][0]['leg_indices'].clear()
    snapshot['detail_checks'][0]['passed']=False
    assert v.snapshot()==old


def test_closest_distance_matches_all_pairs_with_duplicates_and_near_crossings():
    points=[(i*.04+(j%3)*.013,j*.04) for i in range(12) for j in range(9)]
    points.extend([(.1,.1),(.100001,.100001)])
    assert detailing.closest_distance(points)==pytest.approx(min(math.dist(a,b) for i,a in enumerate(points) for b in points[i+1:]))
    points.append(points[0]);assert detailing.closest_distance(points)==0
