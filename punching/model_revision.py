"""Transactional revision of model axes without dropping individual design data."""
from copy import deepcopy
import math

from .connections import FORCE_KEYS, adopt, fresh_case, initial_draft, provenance
from .collection_workflow import SEPARATE_KEYS, invalidate, turn_of
from .model_workflow import prepare_model, frame_candidate, frame_geometry
from .table_import import key


def _uses_imported_geometry(draft, geometry):
    if not geometry: return False
    for name, expected in geometry['inputs'].items():
        actual = draft.get(name)
        if expected is None:
            if actual not in ('', None): return False
        elif isinstance(expected, (int, float)):
            try:
                if not math.isclose(float(str(actual).replace(',', '.')), expected, rel_tol=1e-10, abs_tol=1e-10): return False
            except (TypeError, ValueError): return False
        elif actual != expected: return False
    return True


def prepare_revision(book, config, joints, defaults):
    """Return a reviewed replacement book and its input-derived preview.

    Existing joints stay included. A narrower combination filter may not delete
    their saved work. Original tables, connectivity and case frames stay fixed.
    """
    existing = deepcopy((book.model_setup or {}).get('joints', []))
    known = {j['node'] for j in existing}
    for j in existing: j['enabled'] = True; j.pop('existing', None)
    added = [deepcopy(j) for j in joints if j.get('enabled') and j['node'] not in known]
    for j in added: j.pop('existing', None)
    batch = prepare_model(book.analysis_tables, book.analysis_nodes, config, existing+added, allow_empty=True)
    old_keys = {k for k, c in book.cases.items() if c.get('automated')}
    removed = old_keys-set(batch['loads'])
    if removed:
        labels = sorted({book.cases[k]['combination'] for k in removed})
        raise ValueError('O filtro retiraria combinações já preparadas: '+', '.join(labels)+'. Mantenha-as no filtro para conservar os dados e cálculos existentes; use o filtro do relatório para limitar a exportação.')
    proposed = deepcopy(book)
    groups = {}
    for c in book.cases.values():
        if c.get('automated'): groups.setdefault(key(c['floor'], c['support']), c)
    impact = {'updated': [], 'added': [], 'unchanged': [], 'manual_geometry': []}
    for ckey, source in batch['loads'].items():
        old = book.cases.get(ckey)
        if old is not None and not old.get('automated'):
            raise ValueError(f"{source['floor']} / {source['support']} / {source['combination']}: já existe um caso independente com esta identificação. Não foi substituído.")
        gkey = key(source['floor'], source['support'])
        sample = old or groups.get(gkey)
        turn = turn_of(sample) if sample else 0
        candidate = frame_candidate(source, turn)
        geometry = frame_geometry(batch['geometries'].get(gkey), turn)
        case = deepcopy(old) if old else fresh_case(source['floor'], source['support'], source['combination'])
        draft = deepcopy(case['draft'] or initial_draft(defaults, dict(case, geometry=geometry)))
        if not old:
            from .batch_workflow import seed_case
            case['geometry'] = geometry
            draft = seed_case(proposed, case, defaults)
            if sample and sample.get('draft'):
                for name, value in sample['draft'].items():
                    if name not in SEPARATE_KEYS: draft[name] = deepcopy(value)
                case['user_edited'] = sample.get('user_edited', False)
                if geometry and sample['geometry'] != geometry and _uses_imported_geometry(sample['draft'], sample['geometry']):
                    for name, value in geometry['inputs'].items(): draft[name] = '' if value is None else str(value)
        previous_candidate = case['candidates'].get('columns')
        changed = not old or previous_candidate != candidate or case['geometry'] != geometry
        if not changed:
            impact['unchanged'].append(ckey)
            continue
        if old and case['choice'] == 'columns':
            # An axis revision must not hide force edits made without a source.
            provenance(case, draft, check_sense=False)
        if old and case['geometry'] != geometry:
            if _uses_imported_geometry(draft, case['geometry']):
                if geometry:
                    for name, value in geometry['inputs'].items(): draft[name] = '' if value is None else str(value)
            elif geometry:
                impact['manual_geometry'].append(ckey)
        case['geometry'] = geometry
        case['candidates']['columns'] = candidate
        case['automated'] = True
        if not old or case['choice'] == 'columns' or (not case['choice'] and not (previous_candidate or {}).get('adopted')):
            if candidate['adopted'] is not None:
                adopt(case, 'columns', draft, config['reference'])
            else:
                for name in FORCE_KEYS: draft[name] = ''
                case.update(choice='', reference=config['reference'], draft=draft)
        else:
            # Manual and independently imported resultants remain the chosen source.
            case['draft'] = draft
        invalidate(case)
        proposed.cases[ckey] = case
        if geometry: proposed.geometries[gkey] = deepcopy(geometry)
        impact['updated' if old else 'added'].append(ckey)
    proposed.model_setup = deepcopy(batch['model_setup'])
    batch.update(model_revision=True, revision_impact=impact)
    return proposed, batch
