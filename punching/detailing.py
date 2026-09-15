"""Distribuição e conferência geométrica de ramos junto a um bordo afastado.

Os contornos abertos e fechados são modos alternativos de verificação. Um ramo
comum conta uma vez no inventário e uma vez em cada contorno que atravessa.
As posições são verificadas novamente depois da geração; a confirmação de
amarração não altera nenhuma condição geométrica ou resistente.
"""
import math
from . import geometry as geo

TOL = 1e-8


class LayoutError(ValueError):
    pass


def path_position(segments, point):
    """Abscissa de um ponto que pertence ao caminho analítico; None se exterior."""
    offset = 0.
    for seg in segments:
        if seg.kind == 'line':
            dx, dy = seg.p-seg.x, seg.q-seg.y
            t = ((point[0]-seg.x)*dx+(point[1]-seg.y)*dy)/(seg.length**2)
            if -TOL <= t <= 1+TOL and math.dist(point, seg.point(t)) <= TOL:
                return offset+max(0., min(1., t))*seg.length
        else:
            if abs(math.hypot(point[0]-seg.x, point[1]-seg.y)-seg.p) <= TOL:
                angle = math.atan2(point[1]-seg.y, point[0]-seg.x)
                for k in range(-2, 3):
                    theta = angle+k*2*math.pi
                    if seg.a-TOL <= theta <= seg.b+TOL:
                        return offset+max(0., min(seg.b-seg.a, theta-seg.a))*seg.p
        offset += seg.length
    return None


def closest_distance(points):
    """Distância mínima euclidiana, por divisão e conquista."""
    points = sorted(points)
    if len(points) < 2:
        return None
    def solve(p):
        if len(p) <= 12:
            return min((math.dist(a,b) for i,a in enumerate(p) for b in p[i+1:]), default=float('inf'))
        middle = len(p)//2
        best = min(solve(p[:middle]), solve(p[middle:]))
        if best == 0:
            return 0.
        strip = sorted((q for q in p if abs(q[0]-p[middle][0]) < best), key=lambda q:q[1])
        for i,a in enumerate(strip):
            for b in strip[i+1:i+8]:
                if b[1]-a[1] >= best:
                    break
                best = min(best, math.dist(a,b))
        return best
    return solve(points)


class BarCloud:
    def __init__(self, minimum, boundary, end_cover):
        self.minimum = minimum
        self.boundary = boundary
        self.end_cover = end_cover
        self.bars = []
        self.buckets = {}

    def key(self, point):
        return tuple(math.floor(x/self.minimum) for x in point)

    def neighbours(self, point):
        x,y = self.key(point)
        for i in range(x-1,x+2):
            for j in range(y-1,y+2):
                yield from self.buckets.get((i,j), [])

    def admissible(self, point, row):
        if point[1] < self.boundary+self.end_cover-TOL:
            return False
        for idx in self.neighbours(point):
            bar = self.bars[idx]
            distance = math.dist(point, bar['point'])
            if distance <= TOL and bar['row'] == row:
                continue
            if distance < self.minimum-1e-10:
                return False
        return True

    def add(self, point, row):
        for idx in self.neighbours(point):
            if self.bars[idx]['row'] == row and math.dist(point, self.bars[idx]['point']) <= TOL:
                return idx
        if not self.admissible(point, row):
            raise LayoutError('Não foi encontrada uma posição compatível com o recobrimento e a distância livre mínima entre ramos.')
        idx = len(self.bars)
        self.bars.append({'point': tuple(point), 'row': row})
        self.buckets.setdefault(self.key(point), []).append(idx)
        return idx

    def truncate(self, size):
        self.bars = self.bars[:size]
        self.buckets = {}
        for idx,bar in enumerate(self.bars):
            self.buckets.setdefault(self.key(bar['point']), []).append(idx)


def family_paths(c1, c2, radius, gap, sectors, end_cover, closed_needed):
    candidates = geo.edge_candidates(c1,c2,radius,gap,sectors)
    result = {}
    # Closed rows are added only where needed and where their lower branches
    # can actually fit between the column and the edge with nominal cover.
    if closed_needed and radius+end_cover <= gap+TOL:
        result['fechado'] = candidates[0]['segments']
    result['aberto_bordo'] = candidates[1]['segments']
    return result


def populate_component(segments, cloud, row, pitch_limit, end_cover, pins):
    length = sum(s.length for s in segments)
    closed = math.dist(segments[0].point(0),segments[-1].point(1)) <= TOL
    lo,hi = (0.,length) if closed else (end_cover,length-end_cover)
    if hi-lo < cloud.minimum or (not closed and 2*end_cover > pitch_limit+TOL):
        raise LayoutError('Tramo demasiado curto para os ramos e o recobrimento; reveja geometria, diâmetro ou espaçamentos.')
    anchors = [lo] if closed else [lo,hi]
    for point in pins:
        pos = path_position(segments,point)
        if pos is not None and lo-TOL <= pos <= hi+TOL:
            anchors.append(pos % length if closed else pos)
    for bar in list(cloud.bars):
        if bar['row'] != row:
            continue
        pos = path_position(segments,bar['point'])
        if pos is not None and lo-TOL <= pos <= hi+TOL:
            anchors.append(pos % length if closed else pos)
    anchors = sorted(set(round(x,11) for x in anchors))
    for pos in anchors:
        cloud.add(geo.point_at(segments,pos),row)
    boundaries = anchors+[anchors[0]+length] if closed else anchors
    for start,end in zip(boundaries,boundaries[1:]):
        current = start
        while end-current > pitch_limit+1e-10:
            far = min(current+pitch_limit,end-cloud.minimum)
            found = False
            # A bounded search shifts positions around crossings between paths;
            # all other rows and all fixed points remain in the exclusion cloud.
            for j in range(161):
                pos = far-j*(far-current)/160
                if pos-current < cloud.minimum-1e-10:
                    break
                point = geo.point_at(segments,pos % length if closed else pos)
                if cloud.admissible(point,row):
                    cloud.add(point,row)
                    current = pos
                    found = True
                    break
            if not found:
                raise LayoutError('A distribuição automática não consegue satisfazer simultaneamente st e a distância livre entre ramos. Reveja sr ou o diâmetro.')


def design_edge_rows(*, c1,c2,d,gap,s0,sr,n_rows,phi_mm,cover,aggregate,required_sr,rho_min,sectors,closed_needed):
    phi = phi_mm/1000
    area = math.pi*phi**2/4
    end_cover = cover+phi/2
    minimum = phi+max(.020,phi,aggregate+.005)
    cloud = BarCloud(minimum,-c2/2-gap,end_cover)
    rows = []
    errors = []
    for index in range(n_rows):
        radius = s0+index*sr
        st_max = (1.5 if radius <= 2*d+TOL else 2.)*d
        paths = family_paths(c1,c2,radius,gap,sectors,end_cover,closed_needed)
        checkpoint = len(cloud.bars)
        for density in (1.,.9,.8):
            cloud.truncate(checkpoint)
            try:
                for kind,segments in paths.items():
                    perimeter = sum(s.length for s in segments)
                    required = max(required_sr*sr,rho_min*perimeter*sr/1.5)
                    target = min(st_max,1.5*area/(rho_min*sr),perimeter/(math.ceil(required/area)+2))*density
                    pins = [(c1/2+radius,-c2/2),(-c1/2-radius,-c2/2)]
                    for group in geo.components(segments):
                        populate_component(group,cloud,index+1,target,end_cover,pins)
                break
            except LayoutError as exc:
                last_error = str(exc)
        else:
            cloud.truncate(checkpoint)
            errors.append(f'Fiada {index+1}: {last_error}')
            break
        coords = [b['point'] for b in cloud.bars[checkpoint:]]
        rows.append({'row':index+1,'r':radius,'sr':sr,'phi_mm':phi_mm,
                     'coordinates':coords,'n_legs':len(coords),'Asw_m2':len(coords)*area,
                     'Asw_required_m2':max(required_sr*sr,max(rho_min*sum(s.length for s in p)*sr/1.5 for p in paths.values())),
                     'u':sum(s.length for s in paths['aberto_bordo']),
                     'st_max':st_max,'paths':[line for segments in paths.values() for line in geo.polylines(segments)]})
    return rows,errors


def verify_edge_rows(rows, *, c1,c2,d,gap,s0,sr,n_rows,phi_mm,cover,aggregate,required_sr,rho_min,sectors,closed_needed,outer_radius):
    """Recalcula áreas, pertença aos contornos, passos e distâncias a partir de XY."""
    area = math.pi*(phi_mm/1000)**2/4
    end_cover = cover+phi_mm/2000
    minimum = phi_mm/1000+max(.020,phi_mm/1000,aggregate+.005)
    summaries = {'aberto_bordo':[], 'fechado':[]}
    all_points = []
    all_members = True
    for row in rows:
        radius = row['r']
        coords = row['coordinates']
        all_points.extend(coords)
        paths = family_paths(c1,c2,radius,gap,sectors,end_cover,closed_needed)
        row_families = []
        membership = set()
        for kind,segments in paths.items():
            ids = set()
            maximum_pitch = 0.
            components = []
            complete = True
            for group in geo.components(segments):
                length = sum(s.length for s in group)
                closed = math.dist(group[0].point(0),group[-1].point(1)) <= TOL
                positions = []
                for i,point in enumerate(coords):
                    pos = path_position(group,point)
                    if pos is not None:
                        positions.append(pos % length if closed else pos)
                        ids.add(i)
                positions.sort()
                if len(positions)<2:
                    complete = False
                    components.append({'length':length,'n':len(positions),'closed':closed,'pitch':None})
                    continue
                gaps = [b-a for a,b in zip(positions,positions[1:])]
                gaps += [length-positions[-1]+positions[0]] if closed else [2*positions[0],2*(length-positions[-1])]
                pitch = max(gaps)
                maximum_pitch = max(maximum_pitch,pitch)
                components.append({'length':length,'n':len(positions),'closed':closed,'pitch':pitch})
            membership.update(ids)
            perimeter = sum(s.length for s in segments)
            required = max(required_sr*sr,rho_min*perimeter*sr/1.5)
            provided = len(ids)*area
            st_limit = (1.5 if radius<=2*d+TOL else 2.)*d
            minimum_branch = rho_min*sr*maximum_pitch/1.5
            passed = complete and provided>=required-1e-12 and maximum_pitch<=st_limit+TOL and area>=minimum_branch-1e-12
            family = {'kind':kind,'n_legs':len(ids),'leg_indices':sorted(i+1 for i in ids),
                      'Asw_m2':provided,'Asw_required_m2':required,'Asw_min_branch_m2':minimum_branch,
                      'u':perimeter,'st':maximum_pitch if complete else None,'st_max':st_limit,
                      'passed':passed,'components':components}
            row_families.append(family)
            summaries[kind].append({'row':row['row'],'r':radius,'Asw_sr_provided':provided/sr,'passed':passed})
        all_members = all_members and len(membership)==len(coords)
        row['families'] = row_families
        row['Asw_m2'] = len(coords)*area
        row['n_legs'] = len(coords)
        row['st'] = max((f['st'] or 0 for f in row_families),default=0.)
        row['Asw_min_branch_m2'] = max((f['Asw_min_branch_m2'] for f in row_families),default=0.)
        row['components'] = [p for f in row_families for p in f['components']]
        row['minimum_centres_required'] = minimum
        row['minimum_centres_actual'] = closest_distance(coords)
        row['passed'] = bool(row_families) and all(f['passed'] for f in row_families)
    checks = []
    def check(key,name,value,limit,rule,unit):
        passed = value is not None and (value<=limit+TOL if rule=='<=' else value>=limit-TOL)
        checks.append({'id':key,'name':name,'value':value,'limit':limit,'rule':rule,'unit':unit,'passed':passed})
    check('complete','Fiadas geradas',len(rows),n_rows,'>=','fiadas')
    check('first','Primeira fiada às faces laterais e interior',rows[0]['r'] if rows else None,.5*d,'<=','m')
    planned=bool(rows) and all(row['row']==i+1 and abs(row['r']-(s0+i*sr))<=TOL for i,row in enumerate(rows))
    check('radii','Posições radiais correspondem a s0 e sr',int(planned),1,'>=','')
    check('radial','Espaçamento radial máximo',max([sr]+[b['r']-a['r'] for a,b in zip(rows,rows[1:])]) if rows else None,.75*d,'<=','m')
    check('centres','Distância mínima entre centros de ramos',closest_distance(all_points),minimum,'>=','m')
    check('cover','Recobrimento efetivo junto ao bordo',min((y+c2/2+gap-phi_mm/2000 for x,y in all_points),default=None),cover,'>=','m')
    check('paths','Pertença dos ramos aos contornos previstos',int(bool(all_points) and all_members),1,'>=','')
    check('families','Condições de área, st e mínimo por ramo',int(bool(rows) and all(r['passed'] for r in rows)),1,'>=','')
    for kind in ('aberto_bordo','fechado'):
        if kind=='fechado' and not closed_needed:
            continue
        family = summaries[kind]
        label='contorno aberto' if kind=='aberto_bordo' else 'contorno fechado'
        check('count_'+kind,'Número de fiadas no '+label,len(family),2,'>=','fiadas')
        limit_radius = outer_radius if kind=='aberto_bordo' else min(outer_radius,gap)
        target = max(0.,limit_radius-1.5*d)
        check('extent_'+kind,'Extensão da armadura no '+label,family[-1]['r'] if family else None,target,'>=','m')
    return checks,summaries
