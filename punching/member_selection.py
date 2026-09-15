"""Explicit member selection and connected vertical alignments."""
from collections import defaultdict
import re


def select_members(text, available):
    """Resolve all identifiers before any axis assignment is changed."""
    text = str(text).strip().replace('–', '-').replace('−', '-')
    text = re.sub(r'(?<=\d)\s*(?:para|-)\s*(?=\d)', '-', text, flags=re.I)
    parts = re.split(r'[;,\s]+', text)
    if not text:
        raise ValueError('Indique as barras: 110para113 115 118-123, ou uma lista de números.')
    by_number = defaultdict(list)
    for member in available:
        by_number[int(member)].append(member)
    result = set(); missing = set()
    for part in parts:
        match = re.fullmatch(r'(\d+)(?:-(\d+))?', part)
        if not match:
            raise ValueError(f'Seleção de barras inválida: «{part}». Use números, intervalos com - ou para e espaços entre grupos.')
        lo, hi = int(match[1]), int(match[2] or match[1])
        if lo < 1 or lo > hi or hi-lo > 100000:
            raise ValueError('Intervalo de barras inválido: use números positivos, por ordem crescente, até 100 001 números por intervalo.')
        for number in range(lo, hi+1):
            matches = by_number.get(number, [])
            if len(matches) > 1:
                raise ValueError(f'Identificação ambígua da barra {number}: existem números com diferentes zeros iniciais na origem.')
            if matches: result.add(matches[0])
            else: missing.add(number)
        if len(result)+len(missing) > 100001:
            raise ValueError('Seleção demasiado extensa; divida as barras em grupos menores.')
    if missing:
        sample = ' '.join(map(str, sorted(missing)[:20]))
        raise ValueError('Barras não encontradas: '+sample+(' …' if len(missing)>20 else '')+'. Não foi aplicada nenhuma alteração.')
    return sorted(result, key=lambda m: (int(m), m))


def compact_members(identifiers):
    ids = sorted(set(identifiers), key=lambda m: (int(m), m))
    groups = []; start = last = None
    for member in ids:
        # Preserve unusual identifiers verbatim; ranges must be unambiguous.
        canonical = str(int(member)) == member
        if last is not None and canonical and str(int(last)) == last and int(member) == int(last)+1:
            last = member
            continue
        if last is not None: groups.append(start if start == last else start+'-'+last)
        start = last = member
    if last is not None: groups.append(start if start == last else start+'-'+last)
    return ' '.join(groups)


def alignment_members(selected, index, coordinates):
    """Expand through shared end nodes, stopping at gaps and offsets.

    Names and numbering never establish an alignment or an axis direction.
    """
    if not coordinates:
        raise ValueError('Importe as coordenadas dos nós para identificar a prumada. Pode continuar a selecionar barras por números ou intervalos.')
    vertical = {}; at_node = defaultdict(list)
    for member, info in index.items():
        ends = tuple(info['nodes'])
        if len(ends) != 2 or any(n not in coordinates for n in ends): continue
        a, b = (coordinates[n] for n in ends)
        if abs(a['x']-b['x']) > 1e-5 or abs(a['y']-b['y']) > 1e-5 or abs(a['z']-b['z']) < 1e-5: continue
        vertical[member] = ends
        for node in ends: at_node[node].append(member)
    result = set()
    for seed in selected:
        if seed not in vertical:
            raise ValueError(f'Barra {seed}: são necessários dois extremos com coordenadas e geometria vertical para estender à prumada.')
        reference = coordinates[vertical[seed][0]]
        queue = [seed]; visited = set()
        while queue:
            member = queue.pop()
            if member in visited: continue
            visited.add(member)
            if any(abs(coordinates[n][axis]-reference[axis]) > 1e-5 for n in vertical[member] for axis in ('x','y')): continue
            result.add(member)
            for node in vertical[member]:
                links = at_node[node]
                roles = []
                for m in links:
                    other = next(n for n in vertical[m] if n != node)
                    roles.append(coordinates[other]['z'] > coordinates[node]['z'])
                if len(roles) != len(set(roles)):
                    raise ValueError(f'Prumada ambígua no nó {node}: há barras verticais sobrepostas ou ramificadas. Selecione as barras explicitamente.')
                queue.extend(m for m in links if m not in visited)
    return sorted(result, key=lambda m: (int(m), m))
