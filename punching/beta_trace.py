"""Numeric audit trail for the beta actually used by a calculation.

This module formats already evaluated quantities; it never selects a different
factor or recalculates resistance for reports.
"""
import math


def build_trace(v,terms):
    rows=[]
    ref=terms['reference']
    def n(x):return f'{x:.9g}'
    def step(symbol,expression,substitution,value,unit='',reference=ref):
        rows.append(dict(symbol=symbol,expression=expression,substitution=substitution,
                         value=value,unit=unit,reference=reference))
    ex,ey=v._eccentricidades_planas()
    step('VEd','Esforço transverso concomitante',n(v.V_Ed/1000),v.V_Ed/1000,'kN','Entradas')
    step('MEdx','Momento introduzido no centro do pilar',n(v.M_Edx/1000),v.M_Edx/1000,'kN.m','Entradas')
    step('MEdy','Momento introduzido no centro do pilar',n(v.M_Edy/1000),v.M_Edy/1000,'kN.m','Entradas')
    step('ex','MEdy/VEd, com o sentido declarado',f'{n(v.V_Ed*ex/1000)} / {n(v.V_Ed/1000)}',ex,'m','Convenção de eixos')
    step('ey','MEdx/VEd, com o sentido declarado',f'{n(v.V_Ed*ey/1000)} / {n(v.V_Ed/1000)}',ey,'m','Convenção de eixos')
    if not v.is_sapata:
        step('u1','Comprimento do contorno efetivo a 2d',n(v.u1_eff),v.u1_eff,'m','6.4.2')
    eq=terms['equation'];u=v.u1_eff
    applicability=['Esforços referidos ao centro do pilar; X paralelo a c1 e Y a c2. O sentido normal do bordo e os sentidos interiores do canto seguem as opções declaradas.']
    if eq=='6.43':
        bx,by=terms['bx'],terms['by']
        step('bx','c1 + 4d',f'{n(v.c1)} + 4*{n(v.d)}',bx,'m')
        step('by','c2 + 4d',f'{n(v.c2)} + 4*{n(v.d)}',by,'m')
        formula='beta = 1 + 1,8*sqrt((ex/by)^2 + (ey/bx)^2)'
        substitution=f'1 + 1,8*sqrt(({n(ex)}/{n(by)})^2 + ({n(ey)}/{n(bx)})^2)'
        applicability.extend(['Pilar retangular interior, sem setores ineficazes. Aproximação de (6.43), incluindo os limites de uma ou ambas as componentes nulas.',terms['axis_mapping'],
                              'O método selecionado mantém-se quando uma componente de momento tende para zero; não alterna automaticamente entre (6.39) e (6.43).'])
    elif eq=='6.39':
        for axis in ('x','y'):
            step(axis+'G',f'integral({axis} dl)/u1',f'{n(terms["c"+axis]*u)} / {n(u)}',terms['c'+axis],'m','Centro geométrico do contorno')
        step('Mx,G','Mx,orientado - VEd*yG',f'{n(terms["Mx_column_oriented_Nm"]/1000)} - {n(v.V_Ed/1000)}*{n(terms["cy"])}',terms['Mx_control_Nm']/1000,'kN.m','Transporte estático para o centro do contorno')
        step('My,G','My,orientado - VEd*xG',f'{n(terms["My_column_oriented_Nm"]/1000)} - {n(v.V_Ed/1000)}*{n(terms["cx"])}',terms['My_control_Nm']/1000,'kN.m','Transporte estático para o centro do contorno')
        for axis,coord in [('x','y'),('y','x')]:
            step('W'+axis,f'integral(abs({coord}-{coord}G) dl)',n(terms['W'+axis]),terms['W'+axis],'m²','(6.40)')
        for axis,num,den in [('x',v.c1,v.c2),('y',v.c2,v.c1)]:
            step('r'+axis,'Dimensão paralela / perpendicular à excentricidade',f'{n(num)} / {n(den)}',num/den,'','Quadro 6.1')
            step('k'+axis,'Quadro 6.1; interpolação linear',f'r{axis} = {n(num/den)}',terms['k'+axis],'','Quadro 6.1')
        for axis,moment,W,k in [('x',terms['My_control_Nm'],terms['Wy'],terms['kx']),('y',terms['Mx_control_Nm'],terms['Wx'],terms['ky'])]:
            step('delta_beta_'+axis,'k*abs(MG)/VEd * u1/W',f'{n(k)}*{n(abs(moment)/1000)}/{n(v.V_Ed/1000)} * {n(u)}/{n(W)}',terms['delta_beta_'+axis],'','(6.39), por direção')
        formula='beta = 1 + delta_beta_x + delta_beta_y'
        substitution=f'1 + {n(terms["delta_beta_x"])} + {n(terms["delta_beta_y"])}'
        applicability.append('Contorno sem aberturas e sem afastamento ao bordo. W é integrado em retas e arcos, relativamente ao centro do perímetro. Não introduzir momentos previamente transportados para esse centro.')
        if terms['biaxial']:
            applicability.append('Soma conservadora dos módulos das duas majorações de (6.39), selecionada pelo projetista. É uma hipótese de combinação do programa, não uma expressão biaxial literal do EC2 nem a fórmula (6.43).')
        else:applicability.append('Apenas uma componente de momento não nula relativamente ao centro do perímetro, ou caso concêntrico.')
    elif eq=='6.44':
        step('u1*','c1 + 2*min(c2/2;1,5d) + 2*pi*d',f'{n(v.c1)} + 2*min({n(v.c2/2)};{n(1.5*v.d)}) + 2*pi*{n(v.d)}',terms['u_star'],'m','Figura 6.20(a)')
        step('Wy','c1²/4 + c2*c1 + 4*c2*d + 8*d² + pi*d*c1',f'{n(v.c1)}²/4 + {n(v.c2)}*{n(v.c1)} + 4*{n(v.c2)}*{n(v.d)} + 8*{n(v.d)}² + pi*{n(v.d)}*{n(v.c1)}',terms['Wy'],'m²','(6.45), eixos da interface')
        step('r','c2/(2*c1)',f'{n(v.c2)}/(2*{n(v.c1)})',terms['ratio_k'],'','6.4.3(4)')
        step('k','Quadro 6.1 com r = c2/(2*c1)',f'r = {n(terms["ratio_k"])}',terms['k'],'','Quadro 6.1; 6.4.3(4)')
        formula='beta = u1/u1* + k*abs(ex)*u1/Wy'
        substitution=f'{n(u)}/{n(terms["u_star"])} + {n(terms["k"])}*{n(abs(ex))}*{n(u)}/{n(terms["Wy"])}'
        applicability.append('Pilar de bordo encostado, sem aberturas, com excentricidade perpendicular interior. Na Figura 6.20(a), c1 da norma corresponde a c2 da interface, e c2 da norma a c1 da interface. ex é a excentricidade paralela ao bordo.')
    elif eq=='6.46':
        step('u1*','min(c1/2;1,5d) + min(c2/2;1,5d) + pi*d',f'min({n(v.c1/2)};{n(1.5*v.d)}) + min({n(v.c2/2)};{n(1.5*v.d)}) + pi*{n(v.d)}',terms['u_star'],'m','Figura 6.20(b)')
        formula='beta = u1/u1*';substitution=f'{n(u)}/{n(terms["u_star"])}'
        applicability.append('Pilar de canto encostado a ambos os bordos, sem aberturas, com excentricidades interiores.')
    elif eq=='6.42':
        ecc=math.hypot(ex,ey)
        step('e','sqrt(ex² + ey²)',f'sqrt({n(ex)}² + {n(ey)}²)',ecc,'m')
        formula='beta = 1 + 0,6*pi*e/(D + 4d)'
        substitution=f'1 + 0,6*pi*{n(ecc)}/({n(v.D)} + 4*{n(v.d)})'
        applicability.append('Pilar circular interior, sem aberturas.')
    else:
        formula='beta = valor adotado';substitution=n(v.beta)
        if eq=='manual':applicability.append('Fator fornecido pelo projetista; a referência deve abranger u0, u1 e contornos exteriores. O conteúdo técnico da referência não é validado automaticamente.')
        elif eq=='simplificado':applicability.append('Condições declaradas de 6.4.3(6): estabilidade lateral independente dos pórticos laje-pilar e diferença entre vãos adjacentes até 25%. Sem aberturas.')
        else:applicability.append('Sapata concêntrica, com pressão líquida uniforme de equilíbrio.')
    step('beta',formula,substitution,v.beta)
    return {'formula':formula,'substitution':substitution,'steps':rows,'applicability':applicability}
