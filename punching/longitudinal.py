"""Longitudinal bar layouts, in mm, converted to the existing EC2 inputs.

One coplanar set of bar axes per direction; base and extra bars are alternated.
The two orthogonal layers are stacked without bundling. Cover is measured to
longitudinal bars, not to any enclosing transverse reinforcement.
"""
from copy import deepcopy
import math

DIAMETERS = (6, 8, 10, 12, 16, 20, 25, 32, 40)
SPACINGS = (100, 125, 150, 175, 200, 250, 300)
DERIVED_KEYS = ('laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm')
DEFAULTS = {
    'long_mode':'manual', 'long_h_mm':'', 'long_cover_mm':'',
    'long_outer_axis':'x', 'long_layer_gap_mm':'0',
    'long_x_base_mm':'10', 'long_x_extra_mm':'0', 'long_x_spacing_mm':'200',
    'long_y_base_mm':'10', 'long_y_extra_mm':'0', 'long_y_spacing_mm':'200',
}
CHOICES = {
    'long_mode': {'manual':'Manual · d e áreas de armadura', 'automatic':'Automático · base e reforço'},
    'long_outer_axis': {'x':'X mais próxima da face tracionada', 'y':'Y mais próxima da face tracionada'},
}
for _axis in ('x','y'):
    CHOICES[f'long_{_axis}_base_mm'] = {str(v):f'Ø{v}' for v in DIAMETERS}
    CHOICES[f'long_{_axis}_extra_mm'] = {'0':'Sem reforço', **{str(v):f'Ø{v}' for v in DIAMETERS}}
    CHOICES[f'long_{_axis}_spacing_mm'] = {str(v):str(v) for v in SPACINGS}


def num(value, label, low=0, high=5000):
    if isinstance(value,bool): raise ValueError(f'{label}: indique um número.')
    try: result=float(str(value).replace(',','.'))
    except (ValueError,TypeError): raise ValueError(f'{label}: valor numérico obrigatório.') from None
    if not math.isfinite(result) or not low<=result<=high:
        raise ValueError(f'{label}: indique um valor entre {low:g} e {high:g}.')
    return result


def upgrade_draft(draft):
    """Only complete the precise legacy field set, never hide damaged new files."""
    if draft is not None and not (set(draft)&set(DEFAULTS)):
        draft.update(deepcopy(DEFAULTS))
    return draft


def layout_from_draft(draft):
    mode=draft.get('long_mode','manual')
    if mode=='manual': return None
    if mode!='automatic': raise ValueError('Modo de armadura longitudinal desconhecido.')
    layout={name:draft['long_'+name] for name in ('h_mm','cover_mm','outer_axis','layer_gap_mm')}
    for axis in ('x','y'):
        layout[axis]={name:draft[f'long_{axis}_{name}'] for name in ('base_mm','extra_mm','spacing_mm')}
    return layout


def draft_from_layout(layout):
    if layout is None:return deepcopy(DEFAULTS)
    fields={'long_mode':'automatic'}
    for name in ('h_mm','cover_mm','outer_axis','layer_gap_mm'):
        fields['long_'+name]=str(layout[name])
    for axis in ('x','y'):
        for name in ('base_mm','extra_mm','spacing_mm'):
            fields[f'long_{axis}_{name}']=f'{float(layout[axis][name]):g}'
    return fields


def derive(layout, aggregate_mm=20):
    if not isinstance(layout,dict) or set(layout)!={'h_mm','cover_mm','outer_axis','layer_gap_mm','x','y'}:
        raise ValueError('Definição da armadura longitudinal inválida.')
    h=num(layout['h_mm'],'Espessura da laje h (mm)',50)
    cover=num(layout['cover_mm'],'Recobrimento à armadura longitudinal (mm)')
    gap=num(layout['layer_gap_mm'],'Afastamento livre entre camadas X/Y (mm)')
    aggregate=num(aggregate_mm,'Dimensão máxima do agregado (mm)',0,100)
    outer=layout['outer_axis']
    if outer not in ('x','y'):raise ValueError('Escolha a camada longitudinal exterior: X ou Y.')
    normalized={'h_mm':h,'cover_mm':cover,'outer_axis':outer,'layer_gap_mm':gap}
    axes={}
    for axis in ('x','y'):
        item=layout[axis]
        if not isinstance(item,dict) or set(item)!={'base_mm','extra_mm','spacing_mm'}:
            raise ValueError(f'Definição da armadura {axis.upper()} inválida.')
        b=num(item['base_mm'],'Diâmetro da base (mm)');r=num(item['extra_mm'],'Diâmetro do reforço (mm)')
        s=num(item['spacing_mm'],'Espaçamento comum (mm)')
        if b not in DIAMETERS or r not in (0,*DIAMETERS):raise ValueError('Escolha diâmetros da série disponível.')
        if s not in SPACINGS:raise ValueError('Espaçamentos práticos: 100, 125, 150, 175, 200, 250 ou 300 mm.')
        pitch=s/2 if r else s
        if r and pitch not in SPACINGS:
            raise ValueError(f'Armadura {axis.upper()}: a intercalação daria {pitch:g} mm, fora da série prática. Com reforço, escolha 200, 250 ou 300 mm para cada malha; ou use o modo manual para outro pormenor.')
        clear=pitch-(b+r)/2 if r else s-b
        minimum=max(b,r,aggregate+5,20)
        if clear < minimum-1e-9:raise ValueError(f'Armadura {axis.upper()}: distância livre {clear:g} mm inferior a {minimum:g} mm (8.2).')
        area_b=math.pi*b*b/4*10/s
        area_r=math.pi*r*r/4*10/s
        label=f'Ø{b:g} // {s:g}' + (f' + Ø{r:g} // {s:g}' if r else '')
        equivalent=f'Ø{b:g} // {pitch:g}' if r==b else ''
        normalized[axis]={'base_mm':b,'extra_mm':r,'spacing_mm':s}
        axes[axis]={'base_area_cm2pm':area_b,'extra_area_cm2pm':area_r,
                    'area_cm2pm':area_b+area_r,'diameter_envelope_mm':max(b,r),
                    'label':label,'equivalent':equivalent,'pitch_mm':pitch,
                    'clear_mm':clear,'minimum_clear_mm':minimum}
    inner='y' if outer=='x' else 'x'
    axes[outer]['centroid_from_tension_face_mm']=cover+axes[outer]['diameter_envelope_mm']/2
    axes[inner]['centroid_from_tension_face_mm']=cover+axes[outer]['diameter_envelope_mm']+gap+axes[inner]['diameter_envelope_mm']/2
    if cover+axes[outer]['diameter_envelope_mm']+gap+axes[inner]['diameter_envelope_mm']>=h:
        raise ValueError('As camadas de armadura não cabem na espessura da laje.')
    for axis in ('x','y'):
        axes[axis]['d_m']=(h-axes[axis]['centroid_from_tension_face_mm'])/1000
        if axes[axis]['d_m']<.01:raise ValueError('Altura útil inferior a 10 mm: reveja h, recobrimento e camadas.')
    values={'laje_dx':axes['x']['d_m'],'laje_dy':axes['y']['d_m'],
            'laje_d':(axes['x']['d_m']+axes['y']['d_m'])/2,
            'laje_As_lx_cm2pm':axes['x']['area_cm2pm'],'laje_As_ly_cm2pm':axes['y']['area_cm2pm']}
    return {'layout':normalized,'axes':axes,'derived':values,
            'assumption':'Base e reforço intercalados com eixos coplanares em cada direção; duas camadas ortogonais. O maior diâmetro define a envolvente de cada camada.',
            'scope':'A combinação deve representar a armadura de tração aderente média em toda a faixa de cálculo. Reforços parciais, sobrepostos ou noutras camadas exigem definição manual equivalente.',
            'reference':'NP EN 1992-1-1:2010, 6.4.2(1), expressão (6.32); 6.4.4(1); 8.2.'}


def refresh_draft(draft):
    """Return a copy; stale derived numbers are never trusted in automatic mode."""
    layout=layout_from_draft(draft)
    if layout is None:return deepcopy(draft),None
    trace=derive(layout,draft.get('aggregate_mm','20'))
    updated=deepcopy(draft)
    updated.update({k:f'{v:.15g}' for k,v in trace['derived'].items()})
    return updated,trace


def trace_lines(trace):
    layout=trace['layout'];axes=trace['axes'];values=trace['derived']
    lines=[trace['assumption'],
           f"h = {layout['h_mm']:g} mm; distância à superfície da armadura longitudinal = {layout['cover_mm']:g} mm; camada exterior = {layout['outer_axis'].upper()}; afastamento X/Y = {layout['layer_gap_mm']:g} mm."]
    for axis in ('x','y'):
        a=axes[axis]
        lines.append(f"{axis.upper()}: {a['label']} mm" + (f" = {a['equivalent']} mm" if a['equivalent'] else '') + f"; As = {a['area_cm2pm']:.4f} cm²/m; distância livre = {a['clear_mm']:g} mm (mínimo {a['minimum_clear_mm']:g} mm).")
        lines.append(f"d{axis} = (h - a{axis}) / 1000 = ({layout['h_mm']:g} - {a['centroid_from_tension_face_mm']:g}) / 1000 = {a['d_m']:.6f} m.")
    lines.extend([f"d = (dx + dy) / 2 = {values['laje_d']:.6f} m.",trace['scope'],trace['reference']])
    return lines
