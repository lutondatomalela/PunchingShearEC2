"""Contornos de cálculo: comprimentos e integrais exatos de retas/arcos.

Coordenadas em metros, centradas no pilar. X paralelo a c1; Y paralelo a c2.
Bordo livre Y=-c2/2; canto também X=-c1/2. Ângulos desde +X para +Y.
Os setores são determinados pelo projetista segundo a Figura 6.14 do EC2.
"""
from dataclasses import dataclass
import math

PI = math.pi
TAU = 2*PI
EPS = 1e-10


def roots_angle(base, a, b):
    return [base+k*TAU for k in range(math.floor((a-base)/TAU)-1,
                                      math.ceil((b-base)/TAU)+2)
            if a+EPS < base+k*TAU < b-EPS]


@dataclass(frozen=True)
class Segment:
    kind: str
    x: float
    y: float
    p: float
    q: float
    a: float = 0.
    b: float = 0.

    @staticmethod
    def line(x0,y0,x1,y1): return Segment('line',x0,y0,x1,y1)
    @staticmethod
    def arc(cx,cy,r,a,b): return Segment('arc',cx,cy,r,0.,a,b)

    @property
    def length(self):
        return math.hypot(self.p-self.x,self.q-self.y) if self.kind=='line' else self.p*(self.b-self.a)

    def point(self,t):
        if self.kind=='line': return self.x+(self.p-self.x)*t, self.y+(self.q-self.y)*t
        angle=self.a+(self.b-self.a)*t
        return self.x+self.p*math.cos(angle),self.y+self.p*math.sin(angle)

    def slice(self,a,b):
        if self.kind=='line': return Segment.line(*self.point(a),*self.point(b))
        return Segment.arc(self.x,self.y,self.p,self.a+a*(self.b-self.a),self.a+b*(self.b-self.a))

    def integral(self,axis,origin=0.):
        if self.kind=='line':
            return self.length*((self.x+self.p)/2-origin if axis==0 else (self.y+self.q)/2-origin)
        if axis==0:
            return self.p*((self.x-origin)*(self.b-self.a)+self.p*(math.sin(self.b)-math.sin(self.a)))
        return self.p*((self.y-origin)*(self.b-self.a)-self.p*(math.cos(self.b)-math.cos(self.a)))

    def level_roots(self,axis,level):
        if self.kind=='line':
            p0,p1=(self.x,self.p) if axis==0 else (self.y,self.q)
            if abs(p1-p0)<EPS: return []
            t=(level-p0)/(p1-p0)
            return [t] if EPS<t<1-EPS else []
        v=(level-(self.x if axis==0 else self.y))/self.p
        if not -1<v<1: return []
        angles=[math.acos(v),-math.acos(v)] if axis==0 else [math.asin(v),PI-math.asin(v)]
        return [(t-self.a)/(self.b-self.a) for x in angles for t in roots_angle(x,self.a,self.b)]

    def abs_integral(self,axis,origin):
        ts=sorted([0.,1.]+self.level_roots(axis,origin))
        return sum(abs(self.slice(a,b).integral(axis,origin)) for a,b in zip(ts,ts[1:]))

    def ray_roots(self,angle):
        ux,uy=math.cos(angle),math.sin(angle)
        # Intersections with the line through the origin; the opposite ray merely adds a harmless split.
        if self.kind=='line':
            den=(self.p-self.x)*uy-(self.q-self.y)*ux
            if abs(den)<EPS: return []
            t=-(self.x*uy-self.y*ux)/den
            return [t] if EPS<t<1-EPS else []
        v=-(self.x*uy-self.y*ux)/self.p
        if not -1<v<1: return []
        z=math.asin(v)
        return [(t-self.a)/(self.b-self.a)
                for base in [angle-z,angle-PI+z] for t in roots_angle(base,self.a,self.b)]


def sectors_normalized(sectors):
    out=[]
    for pair in sectors:
        if len(pair)!=2 or not all(math.isfinite(float(v)) for v in pair):
            raise ValueError('Cada setor deve conter dois ângulos finitos em graus.')
        a,b=map(float,pair)
        width=b-a
        if abs(width)>=360-EPS: raise ValueError('Um setor não pode eliminar a volta completa.')
        width=width%360
        if width<EPS: raise ValueError('O setor tem amplitude nula.')
        start=a%360; end=start+width
        if end>360:
            out.extend([(start*PI/180,TAU),(0.,(end-360)*PI/180)])
        else: out.append((start*PI/180,end*PI/180))
    merged=[]
    for a,b in sorted(out):
        if merged and a<=merged[-1][1]+EPS: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else: merged.append((a,b))
    if sum(b-a for a,b in merged)>=TAU-EPS: raise ValueError('Os setores eliminam todo o contorno.')
    return tuple(merged)


def trim_sectors(segments,sectors):
    if not sectors: return list(segments)
    result=[]
    for seg in segments:
        ts=sorted(set([0.,1.]+[v for pair in sectors for angle in pair for v in seg.ray_roots(angle)]))
        for a,b in zip(ts,ts[1:]):
            x,y=seg.point((a+b)/2)
            angle=math.atan2(y,x)%TAU
            if not any(lo-EPS<=angle<=hi+EPS for lo,hi in sectors):
                piece=seg.slice(a,b)
                if piece.length>EPS: result.append(piece)
    return result


def stats(segments):
    length=sum(s.length for s in segments)
    if length<=EPS: raise ValueError('O perímetro resistente é nulo; reveja a geometria e os setores ineficazes.')
    cx=sum(s.integral(0) for s in segments)/length
    cy=sum(s.integral(1) for s in segments)/length
    return {'u':length,'cx':cx,'cy':cy,
            'Wy':sum(s.abs_integral(0,cx) for s in segments),
            'Wx':sum(s.abs_integral(1,cy) for s in segments)}


def contour(c1,c2,shape,position,a,d=None,reduced=False,face=False):
    if shape=='circular':
        if position!='interior':
            raise ValueError('Pilares circulares de bordo/canto: geometria fora do domínio validado desta versão.')
        return [Segment.arc(0.,0.,c1/2+a,0.,TAU)]
    hx,hy=c1/2,c2/2
    if position=='interior':
        pieces=[Segment.line(-hx,-hy-a,hx,-hy-a),Segment.arc(hx,-hy,a,-PI/2,0),
                Segment.line(hx+a,-hy,hx+a,hy),Segment.arc(hx,hy,a,0,PI/2),
                Segment.line(hx,hy+a,-hx,hy+a),Segment.arc(-hx,hy,a,PI/2,PI),
                Segment.line(-hx-a,hy,-hx-a,-hy),Segment.arc(-hx,-hy,a,PI,3*PI/2)]
    elif position=='bordo':
        side=min(c2/2,1.5*d) if reduced else (min(c2,1.5*d) if face else c2)
        pieces=[Segment.line(hx+a,hy-side,hx+a,hy),Segment.arc(hx,hy,a,0,PI/2),
                Segment.line(hx,hy+a,-hx,hy+a),Segment.arc(-hx,hy,a,PI/2,PI),
                Segment.line(-hx-a,hy,-hx-a,hy-side)]
    elif position=='canto':
        sx,sy=c1,c2
        if reduced: sx,sy=min(c1/2,1.5*d),min(c2/2,1.5*d)
        if face:
            factor=min(1.,3*d/(c1+c2)); sx,sy=c1*factor,c2*factor
        pieces=[Segment.line(hx+a,hy-sy,hx+a,hy),Segment.arc(hx,hy,a,0,PI/2),
                Segment.line(hx,hy+a,hx-sx,hy+a)]
    else: raise ValueError('Posição de pilar desconhecida.')
    return [s for s in pieces if s.length>EPS]


def area(c1,c2,shape,a):
    return PI*(c1/2+a)**2 if shape=='circular' else c1*c2+2*a*(c1+c2)+PI*a*a


def edge_candidates(c1, c2, a, gap, sectors=()):
    """Rectangular column inside a slab with its free edge at Y=-c2/2-gap.

    The open U ends orthogonally at the free edge; that edge contributes no
    resistance. The closed contour is admissible only strictly inside the slab.
    At a=gap its straight lower side lies ON the free edge and cannot be counted.
    The geometric minimum is chosen after applying any ineffective sectors.
    """
    hx, hy = c1/2, c2/2
    closed = contour(c1, c2, 'retangular', 'interior', a)
    pieces = [Segment.line(hx+a, -hy-gap, hx+a, hy),
              Segment.arc(hx, hy, a, 0, PI/2),
              Segment.line(hx, hy+a, -hx, hy+a),
              Segment.arc(-hx, hy, a, PI/2, PI),
              Segment.line(-hx-a, hy, -hx-a, -hy-gap)]
    opened = [s for s in pieces if s.length > EPS]
    candidates = []
    for kind, raw, admissible in [('fechado', closed, gap > a+EPS),
                                   ('aberto_bordo', opened, True)]:
        effective = trim_sectors(raw, sectors)
        candidates.append({'kind': kind, 'admissible': admissible,
                           'geometric_length': sum(s.length for s in raw),
                           'effective_length': sum(s.length for s in effective),
                           'raw_segments': raw, 'segments': effective})
    return candidates


def select_edge_contour(c1, c2, a, gap, sectors=()):
    candidates = edge_candidates(c1, c2, a, gap, sectors)
    eligible = [c for c in candidates if c['admissible']]
    selected = min(eligible, key=lambda c: (c['effective_length'], c['kind']!='aberto_bordo'))
    # An eliminated minimum must stop the calculation, rather than silently
    # fall back to a more favourable contour.
    stats(selected['segments'])
    return selected, candidates


def polylines(segments,step_angle=PI/48):
    groups=[]
    for s in segments:
        n=1 if s.kind=='line' else max(2,math.ceil((s.b-s.a)/step_angle))
        pts=[s.point(i/n) for i in range(n+1)]
        if groups and math.dist(groups[-1][-1],pts[0])<1e-8: groups[-1].extend(pts[1:])
        else: groups.append(pts)
    if len(groups)>1 and math.dist(groups[-1][-1],groups[0][0])<1e-8:
        groups=[groups[-1]+groups[0][1:]]+groups[1:-1]
    return groups


def components(segments):
    groups=[]
    for seg in segments:
        if groups and math.dist(groups[-1][-1].point(1),seg.point(0))<1e-8: groups[-1].append(seg)
        else: groups.append([seg])
    if len(groups)>1 and math.dist(groups[-1][-1].point(1),groups[0][0].point(0))<1e-8:
        groups=[groups[-1]+groups[0]]+groups[1:-1]
    return groups


def point_at(segments,distance):
    for s in segments:
        if distance<=s.length+EPS: return s.point(max(0.,min(1.,distance/s.length)))
        distance-=s.length
    return segments[-1].point(1.)


def clip_footing(segments,shape,bx,by):
    """Recorta apenas as partes resistentes; o bordo livre não integra u."""
    out=[]
    for s in segments:
        roots=[0.,1.]
        if shape=='retangular':
            for axis,half in [(0,bx/2),(1,by/2)]:
                roots+=s.level_roots(axis,-half)+s.level_roots(axis,half)
            inside=lambda x,y: abs(x)<bx/2-1e-11 and abs(y)<by/2-1e-11
        else:
            R=bx/2
            inside=lambda x,y: x*x+y*y<(R-1e-11)**2
            if s.kind=='line':
                dx,dy=s.p-s.x,s.q-s.y
                aa=dx*dx+dy*dy; bb=2*(s.x*dx+s.y*dy); cc=s.x*s.x+s.y*s.y-R*R
                disc=bb*bb-4*aa*cc
                if disc>0:
                    roots.extend(t for t in [(-bb-math.sqrt(disc))/(2*aa),(-bb+math.sqrt(disc))/(2*aa)] if EPS<t<1-EPS)
            else:
                r0=math.hypot(s.x,s.y)
                if r0>EPS:
                    v=(R*R-r0*r0-s.p*s.p)/(2*s.p*r0)
                    if -1<v<1:
                        phase=math.atan2(s.y,s.x)
                        roots.extend((t-s.a)/(s.b-s.a) for a in [phase-math.acos(v),phase+math.acos(v)] for t in roots_angle(a,s.a,s.b))
        ts=sorted(set(roots))
        for a,b in zip(ts,ts[1:]):
            if inside(*s.point((a+b)/2)):
                piece=s.slice(a,b)
                if piece.length>EPS: out.append(piece)
    return out


def overlap_area(c1,c2,column_shape,a,footing_shape,bx,by):
    """Área da interseção centrada, por integração adaptativa em quadrantes.

    Pressão uniforme: exige-se erro de área muito inferior ao arredondamento do relatório.
    """
    if column_shape==footing_shape=='circular': return PI*min(c1/2+a,bx/2)**2
    xmax=min(c1/2+a,bx/2)
    def height(x):
        yc=math.sqrt(max(0.,(c1/2+a)**2-x*x)) if column_shape=='circular' else c2/2+math.sqrt(max(0.,a*a-max(0.,x-c1/2)**2))
        yf=by/2 if footing_shape=='retangular' else math.sqrt(max(0.,(bx/2)**2-x*x))
        return min(yc,yf)
    def simpson(l,r,fl,fm,fr): return (r-l)*(fl+4*fm+fr)/6
    def integrate(l,r,fl,fm,fr,whole,tol,depth):
        mid=(l+r)/2; f1=height((l+mid)/2); f2=height((mid+r)/2)
        left=simpson(l,mid,fl,f1,fm); right=simpson(mid,r,fm,f2,fr)
        if depth<=0 or abs(left+right-whole)<15*tol: return left+right+(left+right-whole)/15
        return integrate(l,mid,fl,f1,fm,left,tol/2,depth-1)+integrate(mid,r,fm,f2,fr,right,tol/2,depth-1)
    cuts=sorted(set([0.,xmax]+([c1/2] if column_shape=='retangular' and c1/2<xmax else [])))
    total=0.
    for l,r in zip(cuts,cuts[1:]):
        fl,fm,fr=height(l),height((l+r)/2),height(r)
        total+=integrate(l,r,fl,fm,fr,simpson(l,r,fl,fm,fr),max(1e-11,bx*by*1e-10),24)
    return max(0.,min(4*total,area(c1,c2,column_shape,a),bx*by if footing_shape=='retangular' else PI*(bx/2)**2))
