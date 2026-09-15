"""Verificações de punçoamento EC2, com resultados e entradas por execução.

Unidades da API: N, m, N.m, MPa; armaduras longitudinais em cm²/m.
O cálculo é limitado a lajes de altura constante e estribos verticais.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from . import geometry as geo
from .version import VERSION, STANDARD


STATES = {
    'NOT_EVALUATED': ('NÃO AVALIADO','Verificação ainda não executada.'),
    'INVALID': ('DADOS INVÁLIDOS','Não foi possível concluir a verificação.'),
    'ERROR': ('ERRO','Cálculo interrompido; não existe conclusão de verificação.'),
    'BETA_PENDING': ('β POR FUNDAMENTAR','Geometria calculada; falta um coeficiente β aplicável e fundamentado. A resistência e a armadura não estão verificadas.'),
    'FAIL_U0': ('FALHA','Não verifica a resistência máxima na face do pilar.'),
    'FAIL_MAX': ('FALHA','Ultrapassa o limite resistente mesmo com armadura de punçoamento.'),
    'PASS_WITHOUT': ('VERIFICA','Verifica sem armadura específica de punçoamento.'),
    'REQUIRES_REINFORCEMENT': ('REQUER INTERVENÇÃO','A sapata não verifica sem armadura; rever a geometria ou dimensionar armadura por avaliação específica.'),
    'DETAIL_PENDING': ('PORMENOR PENDENTE','A solução proposta verifica resistência e distribuição; falta confirmar a amarração no pormenor construtivo.'),
    'EDGE_DETAIL_PENDING': ('PORMENOR ESPECÍFICO PENDENTE','A armadura necessária foi calculada para o pilar afastado do bordo; falta definir e verificar a distribuição dos estribos e a amarração.'),
    'PASS_WITH': ('VERIFICA','Verifica com a armadura proposta e a amarração declarada pelo projetista.'),
    'FAIL_DETAIL': ('FALHA','A solução de armadura não cumpre todas as verificações de pormenorização.'),
}


class BetaScopeRequired(Exception):
    """A valid geometry does not by itself establish an EC2 moment-transfer model."""


def number(value,name,lo=None,hi=None):
    if isinstance(value,bool): raise ValueError(f'{name}: introduza um número, não um valor lógico.')
    try: v=float(value)
    except (ValueError,TypeError): raise ValueError(f'{name}: valor numérico obrigatório.') from None
    if not math.isfinite(v): raise ValueError(f'{name}: o valor tem de ser finito.')
    if lo is not None and v<lo: raise ValueError(f'{name}: valor mínimo {lo:g}.')
    if hi is not None and v>hi: raise ValueError(f'{name}: valor máximo {hi:g}.')
    return v


def boolean(value,name):
    if not isinstance(value,bool): raise ValueError(f'{name}: utilize True ou False.')
    return value


class PuncoamentoEC2:
    def __init__(self,laje_d,betão_fck,aço_fyk,aço_fywk,pilar_tipo,pilar_forma,
                 V_Ed,pilar_c1,pilar_c2=None,M_Edx=0.,M_Edy=0.,sigma_cp=0.,
                 is_sapata=False,sigma_gd_kpa=0.,u1_ineffective=0.,gamma_C=1.5,gamma_S=1.15,
                 beta_mode='ec2',laje_As_lx_cm2pm=None,laje_As_ly_cm2pm=None,laje_rho_l=None,
                 edge_perp_interior=True,corner_interior=True,*,
                 simplified_applicable=False,opening_sectors=None,laje_dx=None,laje_dy=None,
                 reinforcement_diameter_mm=10.,reinforcement_sr_m=None,reinforcement_s0_m=None,
                 cover_mm=30.,anchorage_confirmed=False,aggregate_mm=20.,edge_distance_m=0.,
                 footing_shape='retangular',footing_bx=None,footing_by=None,footing_diameter=None,
                 project='',support='',combination='',beta_manual=None,beta_reference='',
                 interior_beta_method='ec2_643',allow_biaxial_envelope=False,openings=None,longitudinal_layout=None):
        self._inputs=copy.deepcopy({k:v for k,v in locals().items() if k!='self'})
        if longitudinal_layout is None:self._inputs.pop('longitudinal_layout',None)
        self._prepare()
        self._reset()

    def _prepare(self):
        p=self._inputs
        self.longitudinal_trace=None
        if p.get('longitudinal_layout') is not None:
            from .longitudinal import derive
            self.longitudinal_trace=derive(p['longitudinal_layout'],p['aggregate_mm'])
            p.update(self.longitudinal_trace['derived'])
            p['longitudinal_layout']=copy.deepcopy(self.longitudinal_trace['layout'])
            p['laje_rho_l']=None
        def finite_tree(value):
            if isinstance(value,float) and not math.isfinite(value):raise ValueError('As entradas não podem conter NaN ou infinito.')
            if isinstance(value,(list,tuple)):
                for item in value:finite_tree(item)
        for value in p.values():finite_tree(value)
        for name in ('project','support','combination','beta_reference'):
            if not isinstance(p[name],str):raise ValueError(f'{name}: utilize texto.')
        self.d=number(p['laje_d'],'d (m)',.01,5.)
        self.dx=self.dy=self.d
        if p['laje_dx'] is not None or p['laje_dy'] is not None:
            self.dx=number(p['laje_dx'],'dx (m)',.01,5.)
            self.dy=number(p['laje_dy'],'dy (m)',.01,5.)
            if not math.isclose(self.d,(self.dx+self.dy)/2,abs_tol=1e-7):
                raise ValueError('d deve ser a média de dx e dy. Corrija as alturas úteis.')
        self.fck=number(p['betão_fck'],'fck (MPa)',12,90)
        self.fyk=number(p['aço_fyk'],'fyk (MPa)',400,600)
        self.fywk=number(p['aço_fywk'],'fywk (MPa)',400,600)
        self.gamma_C=number(p['gamma_C'],'gamma_C',1.,2.)
        self.gamma_S=number(p['gamma_S'],'gamma_S',1.,2.)
        self.tipo_pilar=str(p['pilar_tipo']).strip().lower()
        self.forma_pilar=str(p['pilar_forma']).strip().lower()
        if self.tipo_pilar not in ('interior','bordo','canto'): raise ValueError('Tipo de pilar desconhecido.')
        if self.forma_pilar not in ('retangular','circular'): raise ValueError('Forma de pilar desconhecida.')
        if self.forma_pilar=='circular' and self.tipo_pilar!='interior':
            raise ValueError('Pilares circulares de bordo/canto não estão validados nesta versão; utilize uma verificação específica.')
        self.c1=number(p['pilar_c1'],'c1 / D (m)',.01,20.)
        self.c2=number(p['pilar_c2'],'c2 (m)',.01,20.) if self.forma_pilar=='retangular' else self.c1
        if self.forma_pilar=='retangular' and max(self.c1,self.c2)/min(self.c1,self.c2)>=4:
            raise ValueError('Apoios com razão entre dimensões igual ou superior a 4 não estão validados nesta versão. Paredes e apoios alongados requerem avaliação específica.')
        self.D=self.c1 if self.forma_pilar=='circular' else None
        self.edge_distance=number(p['edge_distance_m'],'afastamento da face do pilar ao bordo (m)',0.,100.)
        if self.edge_distance>0 and self.tipo_pilar!='bordo':
            raise ValueError('O afastamento ao bordo só se aplica ao tipo bordo. Selecione bordo e indique a distância livre da face do pilar ao bordo da laje.')
        self.V_Ed=number(p['V_Ed'],'VEd (N)',1e-6,1e12)
        self.M_Edx=number(p['M_Edx'],'MEdx (N.m)',-1e12,1e12)
        self.M_Edy=number(p['M_Edy'],'MEdy (N.m)',-1e12,1e12)
        self.sigma_cp=number(p['sigma_cp'],'sigma_cp (MPa)',0.,self.fck/self.gamma_C)
        self.is_sapata=boolean(p['is_sapata'],'is_sapata')
        self.sigma_gd=number(p['sigma_gd_kpa'],'sigma_gd líquido (kPa)',0,1e6)*1000
        self.u1_ineffective=number(p['u1_ineffective'],'u1 ineficaz (m)',0.)
        if self.u1_ineffective>0:
            raise ValueError('A dedução isolada de u1 deixou de ser admitida. Defina opening_sectors (ângulos das tangentes segundo a Figura 6.14), para avaliar todos os perímetros.')
        from .openings import derive_openings
        self.openings,self.opening_records,automatic=derive_openings(p['openings'],c1=self.c1,c2=self.c2,
            shape=self.forma_pilar,d=self.d,position=self.tipo_pilar,edge_distance=self.edge_distance)
        self.effective_sectors_deg=list(p['opening_sectors'] or [])+automatic
        self.sectors=geo.sectors_normalized(self.effective_sectors_deg)
        self.edge_perp_interior=boolean(p['edge_perp_interior'],'edge_perp_interior')
        self.corner_interior=boolean(p['corner_interior'],'corner_interior')
        if self.tipo_pilar=='canto' and not self.corner_interior and self.M_Edx>=0 and self.M_Edy>=0 and (self.M_Edx>0 or self.M_Edy>0):
            raise ValueError('Canto exterior: indique com sinal negativo a componente dirigida para fora nos eixos do esquema, ou selecione excentricidades interiores.')
        aliases={'calculado':'ec2','calculado_ec2':'ec2','2':'ec2','1':'simplificado',
                 'fib_mc10':'fib','fib_model_code':'fib','calculado_fib':'fib','3':'fib'}
        mode=str(p['beta_mode']).lower().strip()
        self.beta_mode=aliases.get(mode,mode)
        self.interior_beta_method=str(p['interior_beta_method']).strip().lower()
        if self.interior_beta_method not in ('ec2_643','ec2_639'):
            raise ValueError('Método do pilar interior retangular: ec2_643 ou ec2_639.')
        self.allow_biaxial_envelope=boolean(p['allow_biaxial_envelope'],'allow_biaxial_envelope')
        if self.beta_mode=='fib': raise ValueError('O modo fib anterior foi desativado por inconsistência de formulação. Selecione EC2.')
        if self.beta_mode not in ('ec2','simplificado','manual'): raise ValueError('Modo de beta desconhecido.')
        self.beta_manual=None
        if self.beta_mode=='manual':
            self.beta_manual=number(p['beta_manual'],'beta fundamentado pelo projetista',1.)
            if not p['beta_reference'].strip():
                raise ValueError('Beta manual: indique a referência da análise que fundamenta o valor para u0, u1 e os contornos exteriores desta geometria e combinação.')
        if self.beta_mode=='simplificado':
            if not boolean(p['simplified_applicable'],'simplified_applicable'):
                raise ValueError('Beta simplificado exige confirmar as condições de 6.4.3(6): estabilidade independente dos pórticos laje-pilar e diferença de vãos adjacentes até 25%.')
            if self.sectors: raise ValueError('Com setores ineficazes, beta exige fundamentação específica: utilize beta manual com referência, ou EC2 para registar a pendência.')
        self.Asx_cm2pm=p['laje_As_lx_cm2pm']; self.Asy_cm2pm=p['laje_As_ly_cm2pm']
        if self.Asx_cm2pm is not None or self.Asy_cm2pm is not None:
            self.Asx_cm2pm=number(self.Asx_cm2pm,'As,x (cm²/m)',1e-9,1000)
            self.Asy_cm2pm=number(self.Asy_cm2pm,'As,y (cm²/m)',1e-9,1000)
            self.rho_lx=self.Asx_cm2pm/10000/self.dx
            self.rho_ly=self.Asy_cm2pm/10000/self.dy
            self.rho_raw=math.sqrt(self.rho_lx*self.rho_ly)
        else:
            self.rho_raw=number(p['laje_rho_l'],'rho_l',1e-9,.10)
            self.rho_lx=self.rho_ly=None
        self.rho_l=min(self.rho_raw,.02)
        self.fcd=self.fck/self.gamma_C; self.fyd=self.fyk/self.gamma_S; self.fywd=self.fywk/self.gamma_S
        self.k_val=min(1+math.sqrt(.2/self.d),2.)
        self.C_Rd_c=.18/self.gamma_C; self.k1=.1; self.kmax=1.5
        self.v_min=.035*self.k_val**1.5*math.sqrt(self.fck)
        self.nu=.6*(1-self.fck/250)
        self.phi=number(p['reinforcement_diameter_mm'],'diâmetro de estribos (mm)')
        if self.phi not in (10.,12.,16.): raise ValueError('Diâmetros disponíveis para estribos: 10, 12 e 16 mm.')
        self.cover=number(p['cover_mm'],'recobrimento nominal (mm)',10,100)/1000
        self.aggregate=number(p['aggregate_mm'],'dimensão máxima do agregado (mm)',4,63)/1000
        self.sr=number(p['reinforcement_sr_m'],'sr (m)',.005,.75*self.d) if p['reinforcement_sr_m'] is not None else max(.005,math.floor((.75*self.d+1e-10)/.005)*.005)
        self.s0=number(p['reinforcement_s0_m'],'s0 (m)',.3*self.d,.5*self.d) if p['reinforcement_s0_m'] is not None else .5*self.d
        self.anchorage_confirmed=boolean(p['anchorage_confirmed'],'anchorage_confirmed')
        self.foot_shape=str(p['footing_shape']).strip().lower()
        self.foot_bx=self.foot_by=None
        if self.is_sapata:
            if self.beta_mode!='ec2':raise ValueError('Sapata concêntrica: utilize o modo EC2 (beta = 1).')
            if self.tipo_pilar!='interior' or self.sectors or self.openings: raise ValueError('Sapatas: esta versão admite apoios interiores centrados e sem aberturas.')
            if abs(self.M_Edx)>1e-9 or abs(self.M_Edy)>1e-9 or self.sigma_cp>0:
                raise ValueError('Sapatas com momentos ou compressão no plano requerem um modelo de pressão específico; o módulo atual verifica ações concêntricas e pressão líquida uniforme.')
            if self.foot_shape=='retangular':
                self.foot_bx=number(p['footing_bx'],'Bx da sapata (m)',.01,100)
                self.foot_by=number(p['footing_by'],'By da sapata (m)',.01,100)
                self.foot_area=self.foot_bx*self.foot_by
                fits=self.c1<self.foot_bx and self.c2<self.foot_by
            elif self.foot_shape=='circular':
                self.foot_bx=self.foot_by=number(p['footing_diameter'],'diâmetro da sapata (m)',.01,100)
                self.foot_area=math.pi*(self.foot_bx/2)**2
                fits=(self.c1 if self.forma_pilar=='circular' else math.hypot(self.c1,self.c2))<self.foot_bx
            else: raise ValueError('Forma da sapata: retangular ou circular.')
            if not fits: raise ValueError('O pilar tem de estar contido no interior da sapata.')
            equilibrium=self.V_Ed/self.foot_area
            if self.sigma_gd>0 and abs(self.sigma_gd-equilibrium)>equilibrium*.01:
                raise ValueError(f'A pressão líquida não equilibra VEd na área da sapata. Valor uniforme de equilíbrio: {equilibrium/1000:.3f} kPa. Introduza 0 para o calcular automaticamente.')
            self.soil_pressure_used=equilibrium

    def _reset(self):
        self.status='NOT_EVALUATED'; self.relatorio=[]; self.notes=[]; self.checks=[]
        self.reinforcement_rows=[]; self.footing_scan=[]; self.geometry={}; self.beta_terms={}; self.u0_terms={}
        self.contour_comparison=[];self.reinforcement_demands=[];self.detail_checks=[]
        self.armadura_necessaria=None; self.k_beta=None
        for field in ('u0','u1','u1_eff','u1_star','V_Ed_red','beta','v_Ed_u0','v_Ed_u1','v_Rd_max',
                      'v_Rd_c','v_Rd_cs_max','f_ywd_ef','Asw_sr_calc','Asw_sr_min','Asw_sr_req','Asw_sr_min_u1_reference',
                      'Asw_por_perimetro','u_out_ef','u_out_required','r_out_face','dist_zona_armar',
                      'n_perimetros','s0_max','sr_max','v_Rd_cs_provided','a_governing'):
            setattr(self,field,None)
        self._result=None

    @staticmethod
    def _interp_k_por_ratio(r):
        points=[(.5,.45),(1.,.60),(2.,.70),(3.,.80)]
        if r<=.5:return .45
        if r>=3:return .80
        for (a,x),(b,y) in zip(points,points[1:]):
            if r<=b:return x+(r-a)*(y-x)/(b-a)

    def _contour(self,a,reduced=False,face=False):
        if self.edge_distance>0:
            if reduced:raise ValueError('u1* da Figura 6.20 não é utilizado para pilares afastados do bordo.')
            if face:
                # Retain the edge-column capacity bound. A positive gap does not
                # automatically justify credit for the fourth face of the support.
                # This is a deliberately conservative assumption for setback cases,
                # not a claimed EC2 interpolation in g.
                raw=geo.contour(self.c1,self.c2,self.forma_pilar,'bordo',0.,self.d,face=True)
                return geo.trim_sectors(raw,self.sectors)
            return geo.select_edge_contour(self.c1,self.c2,a,self.edge_distance,self.sectors)[0]['segments']
        return geo.trim_sectors(geo.contour(self.c1,self.c2,self.forma_pilar,self.tipo_pilar,a,
                                          self.d,reduced,face),self.sectors)

    def _get_perimetros_criticos(self):
        self._u0_segments=self._contour(0.,face=True)
        self._u1_segments=self._contour(2*self.d)
        self.u0=geo.stats(self._u0_segments)['u']
        self.u0_terms={'adopted_m':self.u0,
            'full_face_m':math.pi*self.D if self.D else 2*(self.c1+self.c2),
            'conservative_edge_bound':self.edge_distance>0,
            'method':('Hipótese conservadora: mantém-se o limite de u0 do pilar de bordo de 6.4.5(3), sem crédito automático pela quarta face para g > 0.'
                      if self.edge_distance>0 else 'EC2 6.4.5(3); setores ineficazes aplicáveis.')}
        self.u1=sum(s.length for s in geo.contour(self.c1,self.c2,self.forma_pilar,self.tipo_pilar,2*self.d,self.d))
        if self.edge_distance>0:
            selected,candidates=geo.select_edge_contour(self.c1,self.c2,2*self.d,self.edge_distance,self.sectors)
            self.u1=selected['geometric_length']
            self.contour_comparison=[{k:v for k,v in c.items() if k not in ('segments','raw_segments')} for c in candidates]
            for c in self.contour_comparison:c['selected']=c['kind']==selected['kind']
        self.u1_eff=geo.stats(self._u1_segments)['u']
        self.u1_ineffective=self.u1-self.u1_eff
        self.geometry={'column':{'shape':self.forma_pilar,'c1':self.c1,'c2':self.c2,'position':self.tipo_pilar,
                                 'edge_distance_m':self.edge_distance},
                       'u0':geo.polylines(self._u0_segments),'u1':geo.polylines(self._u1_segments),
                       'opening_sectors':copy.deepcopy(self.effective_sectors_deg),
                       'openings':copy.deepcopy(self.opening_records)}
        inward=(self.tipo_pilar=='bordo' and self.edge_perp_interior) or (self.tipo_pilar=='canto' and self.corner_interior)
        if inward and self.beta_mode=='ec2' and not self.sectors and self.edge_distance==0:
            reduced=self._contour(2*self.d,reduced=True)
            self.u1_star=geo.stats(reduced)['u']; self.geometry['u1_star']=geo.polylines(reduced)

    def _eccentricidades_planas(self,V=None):
        V=self.V_Ed if V is None else V
        ex,ey=self.M_Edy/V,self.M_Edx/V
        if self.tipo_pilar=='bordo': ey=abs(ey) if self.edge_perp_interior else -abs(ey)
        if self.tipo_pilar=='canto' and self.corner_interior: ex,ey=abs(ex),abs(ey)
        return ex,ey

    def _general_beta_at(self,g,ex,ey):
        # Actions are entered at the column centre. Translate the resultant
        # ONCE to the control-perimeter centroid, in the documented convention
        # ex=My/V and ey=Mx/V. Do not translate an already translated moment.
        mx=self.V_Ed*(ey-g['cy']);my=self.V_Ed*(ex-g['cx'])
        # Remove roundoff from analytic integrals of symmetric contours only.
        tol=1e-12*self.V_Ed*max(self.c1,self.c2,self.d)
        if abs(mx)<tol:mx=0.
        if abs(my)<tol:my=0.
        biaxial=mx!=0. and my!=0.
        if (biaxial or self.tipo_pilar=='canto') and not self.allow_biaxial_envelope:
            raise BetaScopeRequired('A verificação geral desta ligação requer tratamento biaxial: duas componentes da resultante ou pilar de canto exterior. Para pilar interior pode selecionar (6.43). Para aplicar (6.39) por direção, selecione a combinação biaxial conservadora em Opções; esta combinação é uma hipótese adicional e não uma expressão biaxial literal do EC2. Em alternativa, indique beta fundamentado.')
        if min(g['Wx'],g['Wy'])<=1e-12:raise ValueError('Perímetro degenerado para transmissão de momentos.')
        kx=self._interp_k_por_ratio(self.c1/self.c2)
        ky=self._interp_k_por_ratio(self.c2/self.c1)
        tx=kx*abs(my)/self.V_Ed*g['u']/g['Wy']
        ty=ky*abs(mx)/self.V_Ed*g['u']/g['Wx']
        b=1+tx+ty
        return b,{'method':('EC2 (6.39) por direção; soma conservadora das majorações biaxiais, selecionada pelo projetista.' if biaxial else 'EC2 (6.39)-(6.40), transferência uniaxial referida ao centro do perímetro de controlo.'),
            'equation':'6.39','basis':'conservative_combination' if biaxial else 'normative_expression',
            'reference':'6.4.3(3)-(5); (6.39)-(6.40); Quadro 6.1',
            'kx':kx,'ky':ky,'ratio_kx':self.c1/self.c2,'ratio_ky':self.c2/self.c1,
            'k':kx if my and not mx else ky if mx and not my else None,
            'ex':ex,'ey':ey,'Mx_column_oriented_Nm':self.V_Ed*ey,'My_column_oriented_Nm':self.V_Ed*ex,
            'Mx_control_Nm':mx,'My_control_Nm':my,'delta_beta_x':tx,'delta_beta_y':ty,
            'biaxial':biaxial,**g}

    def _beta_at(self,a):
        seg=self._contour(a); g=geo.stats(seg); u=g['u']; ex,ey=self._eccentricidades_planas()
        if self.is_sapata:return 1.,{'method':'EC2 (6.49), sapata concêntrica','equation':'6.49','reference':'6.4.4(2), (6.49)','basis':'normative_expression'}
        if self.beta_mode in ('manual','simplificado'):
            b=self.beta_manual if self.beta_mode=='manual' else {'interior':1.15,'bordo':1.4,'canto':1.5}[self.tipo_pilar]
            method=('Beta indicado pelo projetista, aplicado a u0, u1 e contornos exteriores; referência: '+self._inputs['beta_reference'].strip()
                    if self.beta_mode=='manual' else 'EC2 6.4.3(6), Figura 6.21: beta simplificado, com condições de aplicabilidade declaradas.')
            terms={'method':method,'source':self.beta_mode,'ex':ex,'ey':ey,'beta_adopted':b,
                   'equation':self.beta_mode,'reference':self._inputs['beta_reference'].strip() if self.beta_mode=='manual' else '6.4.3(6), Figura 6.21N',
                   'basis':'user_supplied' if self.beta_mode=='manual' else 'normative_simplification'}
            if self.edge_distance>0:
                selected,candidates=geo.select_edge_contour(self.c1,self.c2,a,self.edge_distance,self.sectors)
                records=[]
                for c in candidates:
                    if c['admissible']:
                        s=geo.stats(c['segments'])
                        records.append({'kind':c['kind'],'beta':b,'beta_over_u':b/s['u'],'method':method,**s})
                governing=max(records,key=lambda c:c['beta_over_u'])
                terms.update(selected_contour=selected['kind'],governing_contour=governing['kind'],
                             edge_distance_m=self.edge_distance,candidates=records)
            return b,terms
        if self.edge_distance>0:
            raise BetaScopeRequired('Pilar afastado do bordo: a geometria foi calculada, mas esta ligação exige fundamentação específica de beta. Em Opções, introduza beta manual e a referência da análise, ou selecione o método simplificado apenas se cumprir 6.4.3(6). A resistência e a armadura ficam por verificar.')
        if self.sectors or self.tipo_pilar!='interior':
            if not self.sectors and self.tipo_pilar=='bordo' and self.edge_perp_interior:
                us=geo.stats(self._contour(a,reduced=True))['u']
                # c1 of Fig.6.20 is PERPENDICULAR to the edge: c2 in this UI.
                k=self._interp_k_por_ratio(self.c2/(2*self.c1))
                wy=sum(s.abs_integral(0,0.) for s in seg)
                b=u/us+k*abs(ex)*u/wy
                return b,{'method':'EC2 (6.44), bordo encostado e excentricidade perpendicular interior (inclui o limite de momento perpendicular nulo)',
                           'equation':'6.44','reference':'6.4.3(4), (6.44)-(6.45), Figura 6.20(a)','basis':'normative_expression',
                           'k':k,'ratio_k':self.c2/(2*self.c1),'Wy':wy,'u_star':us,'ex':ex,'ey':ey}
            if not self.sectors and self.tipo_pilar=='canto' and self.corner_interior:
                us=geo.stats(self._contour(a,reduced=True))['u']
                return u/us,{'method':'EC2 (6.46), excentricidades interiores','equation':'6.46','reference':'6.4.3(5), (6.46), Figura 6.20(b)',
                             'basis':'normative_expression','u_star':us,'ex':ex,'ey':ey}
            if self.sectors:
                raise BetaScopeRequired('Com setores ineficazes, a aplicação da transferência de momentos ao contorno recortado exige fundamentação específica. Indique beta manual e a referência da análise. As opções para contornos sem aberturas não eliminam esta pendência.')
            return self._general_beta_at(g,ex,ey)
        if self.forma_pilar=='circular':
            b=1+.6*math.pi*math.hypot(ex,ey)/(self.D+2*a)
            return b,{'method':'EC2 (6.42), pilar circular interior','equation':'6.42','reference':'6.4.3(3), (6.42)',
                       'basis':'normative_expression','ex':ex,'ey':ey}
        if self.interior_beta_method=='ec2_643':
            bx=self.c1+2*a;by=self.c2+2*a
            # Literal axes mapping of NP EN (6.43): normative y,z -> GUI X,Y.
            # Thus ey_NP/bz_NP -> ex_GUI/by_GUI, and ez_NP/by_NP -> ey_GUI/bx_GUI.
            b=1+1.8*math.hypot(ex/by,ey/bx)
            return b,{'method':'EC2 (6.43), aproximação biaxial para pilar retangular interior, incluindo os limites uniaxiais e concêntrico.',
                'equation':'6.43','reference':'6.4.3(3), (6.43)','basis':'normative_approximation',
                'ex':ex,'ey':ey,'bx':bx,'by':by,'axis_mapping':'y,z da norma correspondem a X,Y da interface; ey_NP=ex, ez_NP=ey, by_NP=bx, bz_NP=by.'}
        return self._general_beta_at(g,ex,ey)

    def _get_beta(self):
        b,terms=self._beta_at(2*self.d)
        if not math.isfinite(b) or b<1:raise ValueError('Beta inválido.')
        self.beta=b; self.beta_terms=terms; self.k_beta=terms.get('k',terms.get('kx'))
        from .beta_trace import build_trace
        terms.update(build_trace(self,terms))
        if self.edge_distance>0:
            self.geometry['u1_contour']=terms['selected_contour']
            raw_beta=max(c['beta_over_u'] for c in terms['candidates'])*self.u1_eff
            factor=max(1.,b/raw_beta)
            for candidate in self.contour_comparison:
                detail=next((c for c in terms['candidates'] if c['kind']==candidate['kind']),None)
                candidate['beta']=detail['beta']*factor if detail else None
                candidate['vEd']=detail['beta_over_u']*factor*self.V_Ed/self.d/1e6 if detail else None
                candidate['stress_governing']=detail is not None and detail['kind']==terms['governing_contour']

    def _get_v_Rd_c(self):
        self.v_Rd_c=max(self.C_Rd_c*self.k_val*(100*self.rho_l*self.fck)**(1/3)+.1*self.sigma_cp,
                        self.v_min+.1*self.sigma_cp)
        self.v_Rd_cs_max=self.kmax*self.v_Rd_c
        if self.is_sapata:self.v_Rd_cs_max=None

    def _check(self,key,name,demand,resistance,reference):
        if not all(math.isfinite(x) for x in [demand,resistance]) or resistance<=0 or demand<0:
            raise ValueError(f'{name}: valores inválidos na verificação.')
        self.checks.append({'id':key,'name':name,'demand':demand,'resistance':resistance,
                            'utilization':demand/resistance,'passed':demand<=resistance*(1+1e-10),
                            'reference':reference,'unit':'MPa'})
        return self.checks[-1]['passed']

    def _verificar_esmagamento(self):
        self.v_Rd_max=.4*self.nu*self.fcd
        self.v_Ed_u0=self.beta*self.V_Ed/(self.u0*self.d)/1e6
        return self._check('u0','Resistência máxima na face do pilar',self.v_Ed_u0,self.v_Rd_max,'6.4.5(3); AC:2012, correção 95')

    def _get_V_Ed_red_e_u1_efetivo(self):
        self.V_Ed_red=self.V_Ed
        if self.is_sapata:
            p=self._footing_point(2*self.d)
            self.V_Ed_red=p['V_red']; self.u1_eff=p['u']

    def _footing_point(self,a):
        if a<=0:return {'a':0.,'u':self.u0 or 0.,'area':0.,'V_red':self.V_Ed,'vEd':0.,'vRd':0.,'ratio':0.}
        seg=geo.clip_footing(self._contour(a),self.foot_shape,self.foot_bx,self.foot_by)
        u=sum(s.length for s in seg)
        area=geo.overlap_area(self.c1,self.c2,self.forma_pilar,a,self.foot_shape,self.foot_bx,self.foot_by)
        force=self.V_Ed-self.soil_pressure_used*area
        if force< -max(.01,self.V_Ed*1e-8):raise ValueError('Reação integrada superior ao equilíbrio da sapata.')
        force=max(0.,force)
        vr=(self.v_Rd_c or max(self.C_Rd_c*self.k_val*(100*self.rho_l*self.fck)**(1/3),self.v_min))*2*self.d/a
        if u<1e-9:
            if force>max(.1,self.V_Ed*1e-7):raise ValueError('Força útil remanescente com perímetro resistente nulo na sapata.')
            ve=0.
        else:ve=force/(u*self.d)/1e6
        return {'a':a,'u':u,'area':area,'V_red':force,'vEd':ve,'vRd':vr,'ratio':ve/vr}

    def _verify_footing(self):
        self.notes.append('Sapata centrada: pressão líquida uniforme de equilíbrio, deduzida do peso próprio. Não inclui capacidade geotécnica nem pormenorização automática de armadura de punçoamento da sapata.')
        if self.sigma_gd>0 and not math.isclose(self.sigma_gd,self.soil_pressure_used,rel_tol=1e-10):
            self.notes.append('A pressão introduzida difere até 1% do equilíbrio; adota-se VEd/área para fechar o equilíbrio.')
        self.notes.append('Perímetros equidistantes recortados pelo contorno da sapata, sem contar bordos livres. Resistência com 2d/a conforme (6.50).')
        step=2*self.d/600
        distances={i*step for i in range(1,601)}
        for contact in [(self.foot_bx-self.c1)/2,(self.foot_by-self.c2)/2]:
            for x in [contact-1e-8*self.d,contact,contact+1e-8*self.d]:
                if 0<x<=2*self.d: distances.add(x)
        points=[self._footing_point(a) for a in sorted(distances)]
        peak=max(points,key=lambda p:p['ratio'])
        left=max(1e-9*self.d,peak['a']-step);right=min(2*self.d,peak['a']+step)
        # Refine the sampled maximum; retain all samples at geometric discontinuities.
        for _ in range(36):
            x1=left+(right-left)*.3819660112501051; x2=left+(right-left)*.6180339887498949
            p1=self._footing_point(x1);p2=self._footing_point(x2)
            points.extend([p1,p2])
            if p1['ratio']<p2['ratio']:left=x1
            else:right=x2
        self.footing_scan=sorted(points,key=lambda p:p['a'])
        peak=max(points,key=lambda p:p['ratio']);self.a_governing=peak['a']
        end=self._footing_point(2*self.d); self.v_Ed_u1=end['vEd'];self.V_Ed_red=end['V_red'];self.u1_eff=end['u']
        self.geometry['footing']={'shape':self.foot_shape,'bx':self.foot_bx,'by':self.foot_by}
        self.geometry['u1']=geo.polylines(geo.clip_footing(self._contour(2*self.d),self.foot_shape,self.foot_bx,self.foot_by))
        self.geometry['governing']=geo.polylines(geo.clip_footing(self._contour(peak['a']),self.foot_shape,self.foot_bx,self.foot_by))
        passed=self._check('footing','Sapata: perímetro condicionante',peak['vEd'],peak['vRd'],'6.4.2(2); 6.4.4(2), (6.48)-(6.50)')
        self.armadura_necessaria=not passed
        self.status='PASS_WITHOUT' if passed else 'REQUIRES_REINFORCEMENT'

    def _dimensionar_armadura(self):
        self.armadura_necessaria=True
        if not self._check('kmax','Limite com armadura',self.v_Ed_u1,self.v_Rd_cs_max,'6.4.5(1), A1:2019; kmax=1,5'):
            self.status='FAIL_MAX';return
        self.f_ywd_ef=min(250+.25*self.d*1000,self.fywd)
        minimum_centres=self.phi/1000+max(.020,self.phi/1000,self.aggregate+.005)
        if self.sr<minimum_centres:
            raise ValueError('O espaçamento radial não permite a distância livre mínima entre ramos de estribos (8.2). Reveja o diâmetro e sr.')
        self.Asw_sr_calc=(self.v_Ed_u1-.75*self.v_Rd_c)*self.u1_eff/(1.5*self.f_ywd_ef)
        rho_min=.08*math.sqrt(self.fck)/self.fywk
        self.Asw_sr_min=rho_min*self.u1_eff/1.5
        self.Asw_sr_min_u1_reference=self.Asw_sr_min
        # (6.52) governs resistance. The 9.4.3 minimum is checked using the
        # actual sr and st of each row, not by imposing u1 on shorter rows.
        self.Asw_sr_req=self.Asw_sr_calc
        if self.edge_distance>0:
            candidates=self.beta_terms['candidates']
            raw_beta=max(c['beta_over_u'] for c in candidates)*self.u1_eff
            factor=max(1.,self.beta/raw_beta)
            for c in candidates:
                demand=factor*c['beta']*self.V_Ed/(c['u']*self.d)/1e6
                needs_steel=demand>self.v_Rd_c*(1+1e-10)
                calc=max(0.,(demand-.75*self.v_Rd_c)*c['u']/(1.5*self.f_ywd_ef)) if needs_steel else 0.
                minimum=rho_min*c['u']/1.5 if needs_steel else 0.
                self.reinforcement_demands.append({'contour':c['kind'],'u':c['u'],
                    'beta_adopted':factor*c['beta'],'vEd':demand,'requires_steel':needs_steel,
                    'Asw_sr_calc_m2pm':calc,'Asw_sr_min_m2pm':minimum,
                    'Asw_sr_min_reference_m2pm':minimum,'Asw_sr_req_m2pm':calc})
            self.Asw_sr_calc=max(self.Asw_sr_calc,max(c['Asw_sr_calc_m2pm'] for c in self.reinforcement_demands))
            self.Asw_sr_min=max(self.Asw_sr_min,max(c['Asw_sr_min_m2pm'] for c in self.reinforcement_demands))
            self.Asw_sr_req=self.Asw_sr_calc
        self.s0_max=.5*self.d;self.sr_max=.75*self.d
        self.u_out_required=self.beta*self.V_Ed/(self.v_Rd_c*self.d)/1e6
        def utilization(r):
            # Retain the u1 beta per (6.54); increase it if effective geometry governs.
            beta=max(self.beta,self._beta_at(r)[0])
            return beta*self.V_Ed/(geo.stats(self._contour(r))['u']*self.d)/1e6/self.v_Rd_c
        low=2*self.d;high=low*1.5
        while utilization(high)>1 and high<100*self.d:high*=1.5
        if utilization(high)>1:raise ValueError('Não foi encontrado um contorno exterior verificável.')
        for _ in range(55):
            mid=(low+high)/2
            if utilization(mid)>1:low=mid
            else:high=mid
        self.r_out_face=high;self.u_out_ef=geo.stats(self._contour(high))['u']
        self.dist_zona_armar=max(0.,high-1.5*self.d)
        self.n_perimetros=max(2,math.ceil(max(0.,self.dist_zona_armar-self.s0)/self.sr-1e-10)+1)
        if self.n_perimetros>100:raise ValueError('Número de fiadas fora do domínio de pormenorização.')
        self.geometry['u_out']=geo.polylines(self._contour(high))
        if self.edge_distance>0:
            _,outer_terms=self._beta_at(high)
            self.geometry['outer_contour']=outer_terms['selected_contour']
            self.geometry['u1_contour']=self.beta_terms['selected_contour']
            self.geometry['outer_utilization']=utilization(high)
            closed_only=(not self.sectors and all(terms[key]=='fechado'
                         for terms in (self.beta_terms,outer_terms)
                         for key in ('selected_contour','governing_contour')))
            if not closed_only:
                self._detail_offset(rho_min)
                return
        bar_area=math.pi*(self.phi/1000)**2/4
        # Open components leave nominal cover from the free end of the control path.
        for i in range(self.n_perimetros):
            radius=self.s0+i*self.sr; segments=self._contour(radius)
            perimeter=sum(s.length for s in segments)
            st_max=(1.5 if radius<=2*self.d+1e-10 else 2.)*self.d
            area_required=max(self.Asw_sr_calc*self.sr,rho_min*perimeter*self.sr/1.5)
            n_required=math.ceil(area_required/bar_area-1e-12)
            st_limit=min(st_max,1.5*bar_area/(rho_min*self.sr))
            coords=[];max_pitch=0.;comp_data=[];minimum_actual=float('inf')
            for group in geo.components(segments):
                length=sum(s.length for s in group)
                closed=math.dist(group[0].point(0),group[-1].point(1))<1e-8
                if closed:
                    n=max(4,math.ceil(length/st_limit),math.ceil(n_required*length/perimeter))
                    n=4*math.ceil(n/4)
                    pitch=length/n;distances=[j*pitch for j in range(n)]
                else:
                    end=self.cover+self.phi/2000
                    if length<=2*end or 2*end>st_limit:
                        raise ValueError('Um tramo de armadura é demasiado curto ou o recobrimento excede a distribuição admissível; reveja o pormenor.')
                    n=max(2,math.ceil((length-2*end)/st_limit)+1,math.ceil(n_required*length/perimeter))
                    pitch=(length-2*end)/(n-1)
                    distances=[end+j*pitch for j in range(n)]
                    pitch=max(pitch,2*end)
                local_coords=[geo.point_at(group,s) for s in distances]
                pairs=list(zip(local_coords,local_coords[1:]))
                if closed:pairs.append((local_coords[-1],local_coords[0]))
                minimum_actual=min(minimum_actual,min(math.dist(a,b) for a,b in pairs))
                coords.extend(local_coords)
                max_pitch=max(max_pitch,pitch)
                comp_data.append({'length':length,'n':n,'pitch':pitch,'closed':closed})
            total=len(coords)*bar_area
            min_per_branch=rho_min*self.sr*max_pitch/1.5
            passed=(total+1e-12>=area_required and bar_area+1e-12>=min_per_branch and max_pitch<=st_max+1e-10 and minimum_actual>=minimum_centres-1e-10)
            self.reinforcement_rows.append({'row':i+1,'r':radius,'sr':self.sr,'phi_mm':self.phi,
                'n_legs':len(coords),'Asw_m2':total,'Asw_required_m2':area_required,'Asw_min_branch_m2':min_per_branch,
                'u':perimeter,'st':max_pitch,'st_max':st_max,'passed':passed,'coordinates':coords,
                'components':comp_data,'minimum_centres_required':minimum_centres,'minimum_centres_actual':minimum_actual,
                'paths':geo.polylines(segments)})
        self.Asw_por_perimetro=min(r['Asw_m2'] for r in self.reinforcement_rows)
        supplied=min(r['Asw_m2']/r['sr'] for r in self.reinforcement_rows)
        self.v_Rd_cs_provided=min(self.kmax*self.v_Rd_c,.75*self.v_Rd_c+1.5*supplied*self.f_ywd_ef/self.u1_eff)
        ok=self._check('reinforced','Resistência com a armadura proposta',self.v_Ed_u1,self.v_Rd_cs_provided,'6.4.5(1), (6.52)')
        last=self.reinforcement_rows[-1]['r']
        placement_ok=last>=self.dist_zona_armar-1e-9 and all(r['passed'] for r in self.reinforcement_rows)
        outer_ok=utilization(self.r_out_face)<=1+1e-9
        self.notes.append('Estribos verticais: área contabilizada por ramo. Os pontos do esquema representam ramos; a forma dos estribos e a sua amarração nas armaduras longitudinais devem constar do pormenor construtivo.')
        self.notes.append(f'Distância livre mínima entre ramos segundo 8.2: max(phi; 20 mm; dg+5 mm), com dg = {self.aggregate*1000:.0f} mm. A condição foi avaliada nos espaçamentos radial e tangencial; o resultado de cada fiada consta do registo de pormenorização.')
        if not all(r['passed'] for r in self.reinforcement_rows):self.notes.append('A distribuição proposta não cumpre todas as condições de espaçamento/armadura. Reveja o diâmetro, a geometria ou os espaçamentos.')
        self.notes.append(f'Última fiada a {last:.3f} m da face; distância ao contorno exterior {self.r_out_face-last:.3f} m, limite 1,5d = {1.5*self.d:.3f} m.')
        self.status=('PASS_WITH' if self.anchorage_confirmed else 'DETAIL_PENDING') if ok and placement_ok and outer_ok else 'FAIL_DETAIL'

    def _detail_offset(self,rho_min):
        from .detailing import design_edge_rows,verify_edge_rows
        closed_needed=any(c['contour']=='fechado' and c['requires_steel'] for c in self.reinforcement_demands)
        config=dict(c1=self.c1,c2=self.c2,d=self.d,gap=self.edge_distance,s0=self.s0,sr=self.sr,
                    n_rows=self.n_perimetros,phi_mm=self.phi,cover=self.cover,aggregate=self.aggregate,
                    required_sr=self.Asw_sr_req,rho_min=rho_min,sectors=self.sectors,closed_needed=closed_needed)
        self.reinforcement_rows,errors=design_edge_rows(**config)
        self.detail_checks,families=verify_edge_rows(self.reinforcement_rows,outer_radius=self.r_out_face,**config)
        self.detail_checks.append({'id':'outer','name':'Utilização do contorno exterior sem armadura',
            'value':self.geometry['outer_utilization'],'limit':1.,'rule':'<=','unit':'',
            'passed':self.geometry['outer_utilization']<=1+1e-9})
        ok=True;ratios=[]
        for demand in self.reinforcement_demands:
            family=families[demand['contour']]
            supplied=min((row['Asw_sr_provided'] for row in family),default=0.)
            if not family or supplied<=0:
                capacity=self.v_Rd_c;reference='6.4.4(1), (6.47)'
            else:
                capacity=min(self.v_Rd_cs_max,.75*self.v_Rd_c+1.5*supplied*self.f_ywd_ef/demand['u'])
                reference='6.4.5(1), (6.52); ramos pertencentes a este contorno'
            name='aberto ao bordo' if demand['contour']=='aberto_bordo' else 'fechado'
            passed=self._check('reinforced_'+demand['contour'],'Resistência do contorno '+name,
                               demand['vEd'],capacity,reference)
            ok=ok and passed
            demand.update(Asw_sr_provided_m2pm=supplied,resistance_MPa=capacity,utilization=demand['vEd']/capacity)
            ratios.append(demand['utilization'])
        # Equivalent resistance uses the same reference stress as vEd,u1;
        # individual contour checks above retain their own perimeter and beta.
        self.v_Rd_cs_provided=min(self.v_Rd_cs_max,self.v_Ed_u1/max(ratios))
        self.Asw_por_perimetro=min((row['Asw_m2'] for row in self.reinforcement_rows),default=None)
        self.notes.extend(errors)
        self.notes.append('Pilar afastado do bordo: geram-se fiadas abertas em U até ao bordo e fechos adicionais quando o contorno fechado também exige armadura. Cada ramo comum é contado uma vez no inventário e em cada modo alternativo de verificação que atravessa; o total da fiada não é atribuído indiscriminadamente aos dois contornos.')
        self.notes.append('A conferência parte das coordenadas XY propostas: pertença aos contornos, área por contorno, armadura mínima por ramo, st ao longo de retas/arcos, sr, recobrimento e distância livre entre todos os ramos. Os prolongamentos do U junto ao bordo complementam a distribuição; s0 identifica a distância às faces laterais e interior do pilar.')
        self.notes.append('Os pontos representam ramos verticais, não estribos completos. A forma, os ganchos, a ligação às armaduras longitudinais e a amarração em altura devem ser definidos no pormenor construtivo; a declaração de amarração não altera as verificações geométricas ou resistentes.')
        if len(self.reinforcement_demands)>1:
            self.notes.append('vRd,cs fornecido no resumo é uma resistência equivalente referida a vEd,u1; as resistências efetivas e utilizações de cada contorno constam das verificações individuais.')
        if errors or not all(c['passed'] for c in self.detail_checks):
            self.notes.append('Não foi obtida uma distribuição que cumpra todas as condições. As posições eventualmente listadas são uma proposta incompleta ou não conforme; reveja o diâmetro, sr, s0 ou a geometria.')
        ready=ok and not errors and all(c['passed'] for c in self.detail_checks)
        self.status=('PASS_WITH' if self.anchorage_confirmed else 'DETAIL_PENDING') if ready else 'FAIL_DETAIL'

    def _check_opening_clearance(self):
        if not self.reinforcement_rows or not self.openings:return
        from .openings import point_clearance
        required=self.cover+self.phi/2000
        for opening in self.openings:
            actual=min(point_clearance(x,y,opening) for row in self.reinforcement_rows for x,y in row['coordinates'])
            passed=actual>=required-1e-9
            self.detail_checks.append({'id':'opening_clearance','name':'Recobrimento junto à abertura '+opening['id'],
                'value':actual,'limit':required,'rule':'>=','unit':'m','passed':passed})
            if not passed:
                self.status='FAIL_DETAIL'
                self.notes.append('A distribuição de ramos não assegura o recobrimento junto à abertura '+opening['id']+'. Rever o pormenor; a confirmação de amarração não elimina esta falha.')

    def verificar_puncoamento(self):
        self._reset()
        try:
            self._prepare()
            if self.rho_raw>.02:self.notes.append('A taxa média foi limitada a 2% conforme 6.4.4(1).')
            self.notes.append('As,x e As,y são armaduras de tração aderentes, médias nas faixas de largura do apoio acrescida de 3d para cada lado, limitadas pelos bordos livres. Confirmar a extensão e a amarração dos reforços.')
            if self.edge_distance>0:
                self.notes.append(f'Pilar retangular afastado de um bordo livre: g = {self.edge_distance:.3f} m, medido da face do pilar ao bordo; c1 paralelo e c2 perpendicular. Bordo em Y = -c2/2-g; lado interior +Y.')
                self.notes.append('EC2 6.4.2(4): compara-se o contorno fechado com o contorno aberto que termina no bordo, sem contar o bordo livre. O contorno fechado que toca ou ultrapassa o bordo não é resistente. Adota-se o menor comprimento efetivo. Com beta manual ou simplificado aplica-se o mesmo fator aos contornos; a sua origem fica registada.')
                self.notes.append('u0 para g > 0: conserva-se, por hipótese conservadora, o limite de capacidade do pilar de bordo de 6.4.5(3), c1 + 2 min(c2; 1,5d), antes das aberturas. Não se atribui capacidade adicional à quarta face apenas por existir afastamento. Esta hipótese não é uma interpolação normativa; pode ser restritiva, mesmo quando u1 é fechado.')
                if self.edge_distance<self.d:
                    self.notes.append('Afastamento inferior a d: prever e verificar armadura especial de bordo conforme 6.4.2(5) e 9.3.1.4. Esta armadura de bordo não é dimensionada pelo módulo de punçoamento.')
            elif self.tipo_pilar!='interior':self.notes.append('Geometria de bordo/canto encostado aos bordos livres. O seletor interior/exterior define o sentido normal; no canto exterior utilizam-se os momentos assinados nos eixos do esquema.')
            if self.sectors:self.notes.append('Setores ineficazes definidos pelo projetista conforme Figura 6.14 (aberturas até 6d); aplicados em u0, u1 e contornos exteriores, com união de setores sobrepostos.')
            if self.openings:
                self.notes.append('Aberturas definidas por geometria: distância mínima face a face e setores recalculados com d e o pilar atuais. Os setores manuais adicionais são unidos aos automáticos; não introduzir novamente os ângulos gerados. A geometria não fundamenta beta.')
            if self.beta_mode=='manual':
                self.notes.append('Beta manual é um dado de projeto, não validado automaticamente pelo programa. A referência deve abranger a geometria, os esforços concomitantes e o fator adotado na face, nos contornos de controlo e exteriores. Alterar os dados exige rever a sua aplicabilidade.')
            if self.beta_mode=='simplificado':
                self.notes.append('Beta simplificado substitui o cálculo explícito da transferência de momentos nos termos de 6.4.3(6). A declaração de aplicabilidade é do projetista; os momentos introduzidos ficam registados e não são somados novamente ao fator simplificado.')
            self._get_perimetros_criticos();self._get_v_Rd_c();self._get_beta()
            self.V_Ed_red=self.V_Ed
            if not self._verificar_esmagamento():self.status='FAIL_U0'
            elif self.is_sapata:self._verify_footing()
            else:
                self.v_Ed_u1=self.beta*self.V_Ed/(self.u1_eff*self.d)/1e6
                if self._check('u1','Resistência sem armadura',self.v_Ed_u1,self.v_Rd_c,'6.4.4(1), (6.47)'):
                    self.armadura_necessaria=False;self.status='PASS_WITHOUT'
                else:self._dimensionar_armadura()
            self._check_opening_clearance()
        except BetaScopeRequired as exc:
            self.status='BETA_PENDING'
            self.beta_terms={'method':'Coeficiente beta por fundamentar; não existe verificação resistente concluída.',
                             'source':'pending','reason':str(exc)}
            self.notes.append(str(exc))
        except ValueError as exc:
            self.status='INVALID';self.notes.append(str(exc))
        except Exception as exc:
            self.status='ERROR';self.notes.append(f'{type(exc).__name__}: {exc}')
        self._freeze_result()
        from .reports import text_report
        report=text_report(self._result)
        self.relatorio=report.splitlines()
        return report

    def _freeze_result(self):
        # Expose the actual minimum in (9.11), evaluated with sr and st.
        for row in self.reinforcement_rows:
            area=math.pi*(row['phi_mm']/1000)**2/4
            for item in [row]+row.get('families',[]):
                item['Asw_min_local_m2']=.08*math.sqrt(self.fck)/self.fywk*row['sr']*item['u']/1.5
                item['Asw_resistance_required_m2']=self.Asw_sr_calc*row['sr']
                item['Asw_branch_provided_m2']=area
                item['minimum_branch_utilization']=item['Asw_min_branch_m2']/area
        input_copy=copy.deepcopy(self._inputs)
        encoded=json.dumps(input_copy,ensure_ascii=False,sort_keys=True,allow_nan=False)
        names=('d','dx','dy','rho_lx','rho_ly','rho_raw','rho_l','fcd','fyd','fywd','k_val','C_Rd_c','k1','kmax',
               'v_min','nu','u0','u1','u1_eff','u1_star','V_Ed_red','beta','v_Ed_u0','v_Ed_u1',
               'v_Rd_max','v_Rd_c','v_Rd_cs_max','f_ywd_ef','Asw_sr_calc','Asw_sr_min','Asw_sr_req','Asw_sr_min_u1_reference',
               'Asw_por_perimetro','u_out_ef','u_out_required','r_out_face','dist_zona_armar','n_perimetros',
               's0_max','sr_max','v_Rd_cs_provided','a_governing')
        values={k:getattr(self,k,None) for k in names}
        if self.is_sapata:values['soil_pressure_used_kpa']=self.soil_pressure_used/1000
        badge,conclusion=STATES[self.status]
        self._result={'version':VERSION,'standard':STANDARD,
                      'calculated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
                      'input_hash':hashlib.sha256((VERSION+'\n'+encoded).encode()).hexdigest(),
                      'status':self.status,'badge':badge,'conclusion':conclusion,
                      'inputs':input_copy,'values':values,'beta_terms':copy.deepcopy(self.beta_terms),'u0_terms':copy.deepcopy(self.u0_terms),
                      'opening_records':copy.deepcopy(self.opening_records),
                      'checks':copy.deepcopy(self.checks),'notes':list(self.notes),
                      'reinforcement_rows':copy.deepcopy(self.reinforcement_rows),
                      'contour_comparison':copy.deepcopy(self.contour_comparison),
                      'reinforcement_demands':copy.deepcopy(self.reinforcement_demands),
                      'detail_checks':copy.deepcopy(self.detail_checks),
                      'footing_scan':copy.deepcopy(self.footing_scan),'geometry':copy.deepcopy(self.geometry)}

        if self.longitudinal_trace is not None:
            self._result['longitudinal_trace']=copy.deepcopy(self.longitudinal_trace)

    def snapshot(self):
        if self._result is None:raise ValueError('Execute verificar_puncoamento() antes de exportar.')
        return copy.deepcopy(self._result)
