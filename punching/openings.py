"""Aberturas físicas e setores angulares. Unidades: m e graus.

Retângulos alinhados com X/Y e círculos. Para retângulos oblíquos em relação
à direção radial, o ajuste de 6.14 usa uma envolvente radial conservadora,
identificada no resultado. O modelo não determina beta.
"""
import copy
import math

EPS=1e-9


def _number(value,name,minimum=None,maximum=100.):
    if isinstance(value,bool):raise ValueError(f'{name}: valor numérico obrigatório.')
    try:v=float(value)
    except (TypeError,ValueError):raise ValueError(f'{name}: valor numérico obrigatório.') from None
    if not math.isfinite(v) or abs(v)>maximum or (minimum is not None and v<minimum):
        raise ValueError(f'{name}: valor fora do intervalo admissível.')
    return v


def normalize_openings(raw):
    if raw is None:return []
    if not isinstance(raw,list) or len(raw)>100:raise ValueError('Aberturas: introduza uma lista com, no máximo, 100 aberturas.')
    out=[];ids=set()
    for i,item in enumerate(raw,1):
        if not isinstance(item,dict):raise ValueError('Cada abertura deve ter identificação, forma, posição e dimensões.')
        unknown=set(item)-{'id','shape','x','y','width','height','diameter'}
        if unknown:raise ValueError('Campos de abertura desconhecidos: '+', '.join(sorted(unknown)))
        label=item.get('id',f'A{i}')
        if not isinstance(label,str) or not label.strip() or len(label.strip())>40 or any(ord(c)<32 for c in label):
            raise ValueError('Identificação da abertura: texto de 1 a 40 caracteres, numa linha.')
        label=label.strip()
        if label.casefold() in ids:raise ValueError('Identificação de abertura repetida: '+label)
        ids.add(label.casefold());shape=item.get('shape','rectangular')
        if shape not in ('rectangular','circular'):raise ValueError(f'{label}: forma retangular ou circular.')
        o=dict(id=label,shape=shape,x=_number(item.get('x'),label+' X'),y=_number(item.get('y'),label+' Y'))
        if shape=='circular':o['diameter']=_number(item.get('diameter'),label+' D',.01,20.)
        else:
            o['width']=_number(item.get('width'),label+' largura X',.01,20.)
            o['height']=_number(item.get('height'),label+' altura Y',.01,20.)
        out.append(o)
    return out


def dimensions(o):
    return (o['diameter'],o['diameter']) if o['shape']=='circular' else (o['width'],o['height'])


def outline(o):
    x,y=o['x'],o['y'];w,h=dimensions(o)
    if o['shape']=='circular':return [(x+w/2*math.cos(i*math.pi/32),y+w/2*math.sin(i*math.pi/32)) for i in range(65)]
    return [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2),(x-w/2,y-h/2)]


def point_clearance(x,y,o):
    """Signed distance from a point to the physical opening boundary."""
    x=abs(x-o['x']);y=abs(y-o['y']);w,h=dimensions(o)
    if o['shape']=='circular':return math.hypot(x,y)-w/2
    dx=x-w/2;dy=y-h/2
    return math.hypot(max(dx,0),max(dy,0))+min(max(dx,dy),0)


def gap_between(a,b):
    aw,ah=dimensions(a);bw,bh=dimensions(b)
    if a['shape']=='circular' and b['shape']=='circular':return math.hypot(a['x']-b['x'],a['y']-b['y'])-(aw+bw)/2
    if a['shape']=='circular':return point_clearance(a['x'],a['y'],b)-aw/2
    if b['shape']=='circular':return point_clearance(b['x'],b['y'],a)-bw/2
    dx=abs(a['x']-b['x'])-(aw+bw)/2;dy=abs(a['y']-b['y'])-(ah+bh)/2
    return math.hypot(max(dx,0),max(dy,0))+min(max(dx,dy),0)


def _angular_hull(points):
    angles=sorted(math.atan2(y,x)%(2*math.pi) for x,y in points)
    gaps=[(angles[(i+1)%len(angles)]-a)%(2*math.pi) for i,a in enumerate(angles)]
    i=max(range(len(gaps)),key=gaps.__getitem__)
    start=angles[(i+1)%len(angles)];width=2*math.pi-gaps[i]
    if width>=math.pi-EPS:raise ValueError('A envolvente angular alcança o centro do pilar; este caso requer definição específica por ângulos.')
    start=math.degrees(start)
    if start>180:start-=360
    return [start,start+math.degrees(width)]


def derive_openings(raw,*,c1,c2,shape,d,position='interior',edge_distance=0.):
    """Normalize physical data and derive angles anew for each geometry/depth."""
    c1=_number(c1,'c1',.01,20);c2=_number(c2,'c2',.01,20);d=_number(d,'d',.01,5)
    edge_distance=_number(edge_distance,'g',0,100)
    if shape not in ('retangular','circular') or position not in ('interior','bordo','canto'):raise ValueError('Geometria do pilar inválida para definir aberturas.')
    openings=normalize_openings(raw)
    col=dict(x=0.,y=0.,shape='circular' if shape=='circular' else 'rectangular',width=c1,height=c2,diameter=c1)
    records=[];sectors=[]
    for i,o in enumerate(openings):
        w,h=dimensions(o);distance=gap_between(col,o)
        if distance<=EPS:raise ValueError(f"{o['id']}: a abertura toca ou intersecta o pilar.")
        if position in ('bordo','canto') and o['y']-h/2<=-c2/2-edge_distance+EPS:
            raise ValueError(f"{o['id']}: a abertura toca ou ultrapassa o bordo livre Y. Reentrâncias no bordo exigem geometria específica.")
        if position=='canto' and o['x']-w/2<=-c1/2+EPS:
            raise ValueError(f"{o['id']}: a abertura toca ou ultrapassa o bordo livre X.")
        for other in openings[:i]:
            if gap_between(o,other)<=EPS:raise ValueError(f"{o['id']} e {other['id']}: aberturas sobrepostas ou contíguas; defina a abertura resultante por avaliação específica.")
        record=dict(o,distance_m=distance,limit_6d_m=6*d,active=distance<=6*d+EPS,
                    outline=outline(o),equivalent_outline=[],tangent_points=[],l1_m=None,l2_m=None,equivalent_width_m=None,
                    sector_deg=None,tangent_sector_deg=None,method='',reference='6.4.2(3), Figura 6.14')
        if not record['active']:
            record['method']='Distância superior a 6d: sem dedução por 6.4.2(3).'
            records.append(record);continue
        if o['shape']=='circular':
            radius=w/2;R=math.hypot(o['x'],o['y']);theta=math.atan2(o['y'],o['x']);alpha=math.asin(radius/R)
            angles=[math.degrees(theta-alpha),math.degrees(theta+alpha)]
            record['method']='Tangentes exatas ao círculo.'
            record['tangent_sector_deg']=angles[:]
        else:
            angles=_angular_hull(record['outline'][:-1]);record['tangent_sector_deg']=angles[:]
            R=math.hypot(o['x'],o['y']);ux=o['x']/R;uy=o['y']/R
            l1=abs(ux)*w+abs(uy)*h;l2=abs(uy)*w+abs(ux)*h
            record.update(l1_m=l1,l2_m=l2,equivalent_width_m=l2,method='Tangentes exatas ao retângulo.')
            if l1>l2+EPS:
                width=math.sqrt(l1*l2);near=R-l1/2
                if near<=EPS:raise ValueError(f"{o['id']}: a envolvente radial do retângulo alcança o centro do pilar. Utilize setores definidos por avaliação específica.")
                eq=[(ux*r-uy*t,uy*r+ux*t) for r,t in [(near,-width/2),(R+l1/2,-width/2),(R+l1/2,width/2),(near,width/2)]]
                angles=_angular_hull(eq);record['equivalent_outline']=eq+[eq[0]];record['equivalent_width_m']=width
                aligned=min(abs(ux),abs(uy))<EPS
                record['method']=('Largura equivalente sqrt(l1*l2), Figura 6.14.' if aligned else
                                  'Envolvente retangular radial conservadora e largura sqrt(l1*l2); hipótese geométrica adicional para posição oblíqua.')
        if o['shape']=='circular':
            length=math.sqrt(R*R-radius*radius)
            record['tangent_points']=[(length*math.cos(math.radians(a)),length*math.sin(math.radians(a))) for a in angles]
        else:
            polygon=(record['equivalent_outline'] or record['outline'])[:-1]
            def difference(p,angle):return abs(math.atan2(math.sin(math.atan2(p[1],p[0])-math.radians(angle)),math.cos(math.atan2(p[1],p[0])-math.radians(angle))))
            record['tangent_points']=[min(polygon,key=lambda p:(round(difference(p,a),10),math.hypot(*p))) for a in angles]
        record['sector_deg']=angles;sectors.append(angles);records.append(record)
    return openings,records,sectors


def placed_opening(identifier,shape,side,gap,c1,c2,width=.4,height=.4,diameter=.4):
    """Convenient placement by face-to-face distance; axes stay fixed."""
    gap=_number(gap,'Distância livre',.001,100)
    if side not in ('+X','-X','+Y','-Y'):raise ValueError('Escolha uma das quatro faces do pilar.')
    o=dict(id=identifier,shape=shape,x=0.,y=0.)
    if shape=='circular':o['diameter']=diameter
    else:o.update(width=width,height=height)
    w,h=dimensions(o)
    if side.endswith('X'):o['x']=(1 if side[0]=='+' else -1)*(c1/2+gap+w/2)
    else:o['y']=(1 if side[0]=='+' else -1)*(c2/2+gap+h/2)
    return normalize_openings([o])[0]


def dragged_opening(original,mode,start,end,snap=.01):
    """Pure controller for move/resize, used by the GUI and interaction tests."""
    o=copy.deepcopy(original)
    def quantize(v):return round(v/snap)*snap if snap else v
    if mode=='move':
        o['x']=quantize(original['x']+end[0]-start[0]);o['y']=quantize(original['y']+end[1]-start[1])
    elif mode=='resize':
        if o['shape']=='circular':o['diameter']=max(.01,quantize(2*math.hypot(end[0]-o['x'],end[1]-o['y'])))
        else:
            o['width']=max(.01,quantize(2*abs(end[0]-o['x'])));o['height']=max(.01,quantize(2*abs(end[1]-o['y'])))
    else:raise ValueError('Operação de arrastamento desconhecida.')
    return normalize_openings([o])[0]
