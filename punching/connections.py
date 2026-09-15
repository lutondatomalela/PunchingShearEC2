"""Connection workspaces and provenance. Numeric engine inputs stay unchanged."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from .table_import import key, source_lines, comparison_lines, MODES, numeric


SCHEMA = 'PunchingShearEC2.connections/1'
FORCE_KEYS = ('V_Ed', 'M_Edx', 'M_Edy')


def geometry_text(inputs):
    def dimension(k):
        value=inputs.get(k)
        if value in ('',None): return 'por definir'
        try:return f'{float(str(value).replace(",", ".")):.3f} m'
        except ValueError:return str(value)
    if inputs.get('pilar_forma')=='circular':return 'Pilar circular: D = '+dimension('pilar_c1')
    return 'Pilar retangular: c1 = '+dimension('pilar_c1')+'; c2 = '+dimension('pilar_c2')


def fresh_case(floor, support, combination):
    return {'floor': floor, 'support': support, 'combination': combination, 'candidates': {},
            'geometry': None, 'choice': '', 'reference': '', 'draft': None, 'last_status': None}


def initial_draft(defaults, case):
    draft = deepcopy(defaults)
    for k in ('pilar_tipo', 'pilar_c1', 'pilar_c2', 'laje_d', 'laje_dx', 'laje_dy',
              'laje_As_lx_cm2pm', 'laje_As_ly_cm2pm', 'betão_fck', *FORCE_KEYS): draft[k] = ''
    draft['support'] = f"{case['support']} / {case['floor']}"
    draft['combination'] = case['combination']
    if case['geometry']:
        for k, value in case['geometry']['inputs'].items(): draft[k] = '' if value is None else str(value)
    return draft


def force_values(draft):
    return {k: numeric(str(draft[k]).replace(',', '.'), k) for k in FORCE_KEYS}


def adopt(case, choice, current_draft, reference=''):
    """Explicit source choice; never overwrite the slab definition."""
    draft = deepcopy(current_draft)
    if choice == 'manual':
        force_values(draft)
        if not reference.strip(): raise ValueError('Indique a origem e a fundamentação dos esforços introduzidos manualmente.')
    elif choice in case['candidates'] and case['candidates'][choice]['adopted'] is not None:
        for k, v in case['candidates'][choice]['adopted'].items(): draft[k] = f'{v:.15g}'
        # The engine's explicit orientation flags follow its eccentricity convention.
        draft['edge_perp_interior'] = float(draft['M_Edx']) >= 0
        draft['corner_interior'] = float(draft['M_Edx']) >= 0 and float(draft['M_Edy']) >= 0
    else: raise ValueError('Esta fonte não permite obter esforços. Resolva as pendências ou introduza esforços fundamentados.')
    case['choice'] = choice; case['reference'] = reference.strip(); case['draft'] = draft; case['last_status'] = None
    return draft


def provenance(case, draft, *, check_sense=True):
    actual = force_values(draft)
    choice = case['choice']
    if not choice: raise ValueError('Selecione a origem dos esforços em «Origem dos esforços…». A carga axial acumulada não é adotada como VEd.')
    if choice == 'manual':
        if not case['reference'].strip(): raise ValueError('Falta a fundamentação dos esforços manuais.')
    else:
        candidate = case['candidates'].get(choice)
        if not candidate or candidate['adopted'] is None: raise ValueError('A fonte selecionada tem pendências.')
        for k, v in actual.items():
            if not math.isclose(v, candidate['adopted'][k], rel_tol=1e-12, abs_tol=1e-9):
                raise ValueError('Os esforços foram alterados após a importação. Em «Origem dos esforços…», reponha a fonte ou escolha «Introdução manual» e registe a alteração.')
        if check_sense and candidate.get('adapter') == 'Modelo.joint-frame/1':
            if draft.get('pilar_tipo') == 'bordo' and draft.get('edge_perp_interior',True) != (actual['M_Edx'] >= 0):
                raise ValueError('O sentido da excentricidade difere dos esforços no referencial do caso. Reponha a fonte ou corrija a orientação da ligação.')
            if draft.get('pilar_tipo') == 'canto' and draft.get('corner_interior',True) != (actual['M_Edx'] >= 0 and actual['M_Edy'] >= 0):
                raise ValueError('Os sentidos das excentricidades diferem dos esforços no referencial do caso. Reponha a fonte ou corrija a orientação da ligação.')
    # Combination labels are not allowed to quietly relabel imported actions.
    if choice != 'manual' and str(draft['combination']).strip() != case['combination']:
        raise ValueError('A combinação difere da origem. Selecione a ligação/combinação correta ou fundamente a introdução manual.')
    trace = {'floor': case['floor'], 'support': case['support'], 'combination': case['combination'],
             'adopted_combination': str(draft['combination']).strip(), 'choice': choice, 'reference': case['reference'],
             'adopted': actual, 'candidates': deepcopy(case['candidates']), 'geometry': deepcopy(case['geometry'])}
    if case['geometry']:
        trace['adopted_geometry'] = {k: draft[k] for k in ('pilar_forma', 'pilar_c1', 'pilar_c2')}
    trace['hash'] = hashlib.sha256(json.dumps(trace, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return trace


def trace_lines(trace):
    lines = [f"Ligação: piso {trace['floor']}, pilar {trace['support']}, combinação de origem {trace['combination'] or '(por definir)'}." ,
             'Fonte adotada: ' + ('Introdução manual' if trace['choice']=='manual' else MODES[trace['choice']]),
             f"Combinação adotada: {trace['adopted_combination']}.",
             'Esforços usados no cálculo: ' + '; '.join(f'{k}={v:.6g}' for k, v in trace['adopted'].items()) + ' (kN; kN.m).',
             'Eixos da planta: X paralelo a c1, Y paralelo a c2; ex=MEdy/VEd e ey=MEdx/VEd.']
    if trace['reference']: lines.append('Fundamentação da adoção: ' + trace['reference'])
    if trace.get('geometry'):
        g = trace['geometry']; s = g['source']
        lines.append(f"Geometria de origem: {geometry_text(g['inputs'])}. Ficheiro {s['file']}, folha {s['sheet']}, linha {s['row']}; SHA-256 {s['sha256']}.")
        lines.append(f"Geometria adotada: {geometry_text(trace['adopted_geometry'])}. A posição relativamente aos bordos, d e As são definidos no caso.")
    for kind, candidate in trace['candidates'].items():
        lines.append('Fonte ' + ('adotada' if kind == trace['choice'] else 'de comparação, não adotada') + ':')
        lines.extend(source_lines(candidate))
    lines.extend(comparison_lines(trace['candidates']))
    lines.append('Identificador da proveniência: ' + trace['hash'])
    return lines


def describe_case(case):
    lines = [f"Piso {case['floor']} · Pilar {case['support']} · {case['combination'] or 'Combinação por definir'}"]
    if case['geometry']: lines.append('Geometria importada: ' + geometry_text(case['geometry']['inputs']))
    else: lines.append('Geometria por definir no caso ou por importar.')
    for candidate in case['candidates'].values(): lines.extend(source_lines(candidate))
    if not case['candidates']: lines.append('Sem esforços importados. Pode acrescentar uma tabela ou definir esforços manuais fundamentados.')
    lines.extend(comparison_lines(case['candidates']))
    lines.append('A laje, as armaduras, os bordos e as aberturas são definidos para cada ligação. Guarde o conjunto para conservar o trabalho.')
    return '\n\n'.join(lines)


class ConnectionBook:
    def __init__(self):
        self.cases = {}; self.geometries = {}; self.active = None
        self.analysis_tables = []; self.analysis_nodes = None
        self.model_setup = None
        self.batch_settings = {'project':{}, 'floors':{}, 'groups':{}}

    def merge(self, batch):
        """Commit all records or none. Existing work is never replaced silently."""
        if batch.get('model_revision'):
            from .model_revision import prepare_revision
            from Punching_EC2_GUI import DEFAULTS
            proposed, _ = prepare_revision(self, **batch['model_setup'], defaults=DEFAULTS)
            self.__dict__.update(proposed.__dict__)
            return
        proposed = deepcopy(self)
        if batch.get('model_setup'):
            model = deepcopy(batch['model_setup'])
            if proposed.model_setup:
                if proposed.model_setup['config'] != model['config']:
                    raise ValueError('O conjunto já tem uma configuração de modelo. Para rever os eixos ou acrescentar combinações, use «Preparar modelo…» e confira a atualização das ligações existentes.')
                known = {j['node'] for j in proposed.model_setup['joints']}
                if any(j['node'] in known for j in model['joints']): raise ValueError('Já existem ligações preparadas nesses nós.')
                proposed.model_setup['joints'].extend(model['joints'])
            else: proposed.model_setup = model
        if 'analysis_table' in batch:
            from .analysis_import import all_records
            proposed.analysis_tables.append(deepcopy(batch['analysis_table']))
            all_records(proposed.analysis_tables)
        if 'analysis_nodes_table' in batch:
            from .analysis_import import restore, parse_nodes
            if proposed.analysis_nodes is not None: raise ValueError('A tabela de nós já existe. Para outra revisão, crie um novo conjunto.')
            parse_nodes(restore(batch['analysis_nodes_table']))
            proposed.analysis_nodes = deepcopy(batch['analysis_nodes_table'])
        for gkey, geom in batch['geometries'].items():
            if gkey in proposed.geometries and proposed.geometries[gkey]['inputs'] != geom['inputs']:
                raise ValueError(f"Geometria incompatível: {geom['floor']} / {geom['support']}. Use um novo conjunto para uma revisão da origem.")
            proposed.geometries.setdefault(gkey, deepcopy(geom))
        for ckey, load in batch['loads'].items():
            case = proposed.cases.setdefault(ckey, fresh_case(load['floor'], load['support'], load['combination']))
            if load['kind'] in case['candidates']:
                raise ValueError(f"A fonte {MODES[load['kind']]} já existe para {load['floor']} / {load['support']} / {load['combination']}.")
            case['candidates'][load['kind']] = deepcopy(load); case['last_status'] = None
            empty_key = key(load['floor'], load['support'], '')
            if empty_key in proposed.cases and proposed.cases[empty_key]['draft'] is None and empty_key != proposed.active:
                del proposed.cases[empty_key]
        for gkey, geom in proposed.geometries.items():
            matches = [c for c in proposed.cases.values() if (c['floor'], c['support']) == (geom['floor'], geom['support'])]
            if not matches:
                case = fresh_case(geom['floor'], geom['support'], ''); proposed.cases[key(geom['floor'], geom['support'], '')] = case; matches = [case]
            for case in matches:
                was_missing = case['geometry'] is None
                case['geometry'] = deepcopy(geom)
                if was_missing and case['draft'] is not None and not case['draft']['pilar_c1'].strip() and not case['draft']['pilar_c2'].strip():
                    for k, value in geom['inputs'].items(): case['draft'][k] = '' if value is None else str(value)
        self.cases = proposed.cases; self.geometries = proposed.geometries
        self.analysis_tables = proposed.analysis_tables; self.analysis_nodes = proposed.analysis_nodes
        self.model_setup = proposed.model_setup
        if batch.get('model_setup'):
            from Punching_EC2_GUI import DEFAULTS
            for ckey in batch['loads']:
                case = self.cases[ckey]; case['automated'] = True
                from .batch_workflow import seed_case
                draft = seed_case(self, case, DEFAULTS)
                if case['candidates']['columns']['adopted'] is not None:
                    adopt(case, 'columns', draft, batch['model_setup']['config']['reference'])
                else: case['draft'] = draft

    def payload(self):
        cases = deepcopy(self.cases)
        for c in cases.values():
            c['last_status'] = None
            c.pop('_calculation', None); c.pop('_calculation_hash', None)
            if self.model_setup and c.get('automated'):
                candidate = c['candidates']['columns']
                c['candidates']['columns'] = {'adapter':'Modelo.model-ref/1',
                    'node':candidate['frame']['base']['analysis']['setup']['node'], 'turn':candidate['frame']['turn']}
        from .collection_workflow import cached_calculation
        receipts = {k: self.cases[k]['_calculation_hash'] for k in self.cases if cached_calculation(self.cases[k]) is not None}
        data = {'schema': SCHEMA, 'cases': cases, 'geometries': deepcopy(self.geometries), 'active': self.active}
        if self.model_setup:
            data['schema'] = 'PunchingShearEC2.connections/2'
            data['model_setup'] = deepcopy(self.model_setup)
        if self.analysis_tables: data['analysis_tables'] = deepcopy(self.analysis_tables)
        if self.analysis_nodes: data['analysis_nodes'] = deepcopy(self.analysis_nodes)
        data.update(schema='PunchingShearEC2.connections/3', batch_settings=deepcopy(self.batch_settings),
                    calculated_cases=receipts)
        return data

    @classmethod
    def from_payload(cls, data, defaults):
        from .migrations import normalize_archive
        data = normalize_archive(data)
        if not isinstance(data, dict) or data.get('schema') not in (SCHEMA,'PunchingShearEC2.connections/2','PunchingShearEC2.connections/3'): raise ValueError('Formato de conjunto não reconhecido.')
        if not isinstance(data.get('cases'), dict) or not isinstance(data.get('geometries'), dict): raise ValueError('Conjunto incompleto.')
        book = cls()
        if data.get('model_setup') is not None:
            from .model_workflow import prepare_model, frame_candidate, frame_geometry
            data = deepcopy(data)
            book.model_setup = deepcopy(data['model_setup'])
            batch = prepare_model(data['analysis_tables'], data.get('analysis_nodes'), **book.model_setup, allow_empty=True)
            automated = {k for k,c in data['cases'].items() if c.get('automated')}
            if automated != set(batch['loads']):
                raise ValueError('O conjunto não conserva todas as ligações e combinações preparadas a partir das tabelas.')
            for ckey, case in data['cases'].items():
                if not case.get('automated'): continue
                marker = case['candidates']['columns']
                expected = batch['loads'].get(ckey)
                if not expected or marker.get('adapter') != 'Modelo.model-ref/1' or marker.get('node') != expected['frame']['base']['analysis']['setup']['node']:
                    raise ValueError('A ligação guardada não corresponde às tabelas e aos nós preparados.')
                candidate = frame_candidate(expected, marker['turn'])
                case['candidates']['columns'] = candidate
                geometry = frame_geometry(batch['geometries'].get(key(case['floor'],case['support'])), marker['turn'])
                if case['geometry'] != geometry: raise ValueError('Geometria da ligação incompatível com a orientação guardada.')
                if data['geometries'].get(key(case['floor'],case['support'])) != geometry:
                    raise ValueError('A geometria do conjunto difere da ligação preparada.')
        from .longitudinal import upgrade_draft
        for ckey, case in data['cases'].items():
            upgrade_draft(case.get('draft'))
            validate_case(case, defaults)
            if ckey != key(case['floor'], case['support'], case['combination']): raise ValueError('Identificação de ligação inconsistente.')
            book.cases[ckey] = deepcopy(case); book.cases[ckey]['last_status'] = None
            book.cases[ckey].pop('_calculation',None); book.cases[ckey].pop('_calculation_hash',None)
        for gkey, geom in data['geometries'].items():
            if gkey != key(geom['floor'], geom['support']): raise ValueError('Identificação de geometria inconsistente.')
        book.geometries = deepcopy(data['geometries'])
        if data.get('active') is not None and data['active'] not in book.cases: raise ValueError('Ligação ativa inexistente.')
        book.active = data.get('active')
        from .analysis_import import all_records, restore, parse_nodes
        book.analysis_tables = deepcopy(data.get('analysis_tables', []))
        book.analysis_nodes = deepcopy(data.get('analysis_nodes'))
        all_records(book.analysis_tables)
        if book.analysis_nodes: parse_nodes(restore(book.analysis_nodes))
        if book.model_setup:
            from .collection_workflow import SEPARATE_KEYS, turn_of
            groups = {}
            for case in book.cases.values():
                if not case.get('automated'): continue
                signature = (turn_of(case), {k:v for k,v in (case['draft'] or {}).items() if k not in SEPARATE_KEYS})
                gkey = key(case['floor'],case['support'])
                if gkey in groups and groups[gkey] != signature: raise ValueError('Os dados comuns de uma ligação diferem entre combinações.')
                groups[gkey] = signature
        from .batch_workflow import empty_settings, validate_settings, remember_project
        book.batch_settings = deepcopy(data.get('batch_settings',empty_settings()))
        validate_settings(book.batch_settings,book)
        if 'batch_settings' not in data:
            # Preserve all old drafts as exceptions; infer initial project defaults
            # from the active connection, without modifying any old calculation input.
            sample=book.cases.get(book.active) or next(iter(book.cases.values()),None)
            if sample and sample.get('draft'):remember_project(book,sample['draft'])
            for c in book.cases.values():c['user_edited']=c['draft'] is not None
        # Rebuild only previously executed, unchanged cases; never trust stored
        # result numbers or execute unfinished pillars when reopening a collection.
        from .collection_workflow import case_signature, calculate_case
        receipts=data.get('calculated_cases',{})
        if not isinstance(receipts,dict):raise ValueError('Registo de cálculos inválido.')
        for k,signature in receipts.items():
            if k in book.cases and signature==case_signature(book.cases[k]):calculate_case(book.cases[k],defaults)
        # Refuse non-JSON values and NaN even in otherwise unused metadata.
        json.dumps(book.payload(), allow_nan=False)
        return book


def validate_case(case, defaults=None):
    try:
        if not all(isinstance(case[k], str) for k in ('floor', 'support', 'combination', 'choice', 'reference')): raise ValueError()
        if not case['floor'].strip() or not case['support'].strip(): raise ValueError()
        if case['choice'] not in ('', 'manual', 'columns', 'resultants'): raise ValueError()
        if not isinstance(case['candidates'], dict) or set(case['candidates']) - {'columns', 'resultants'}: raise ValueError()
        if case.get('draft') is not None:
            if not isinstance(case['draft'], dict): raise ValueError()
            if defaults is not None and set(case['draft']) != set(defaults): raise ValueError('Campos do caso incompatíveis com esta versão.')
            for k, v in case['draft'].items():
                if defaults is None:
                    if not isinstance(v, (str, bool)): raise ValueError()
                elif isinstance(defaults[k], bool):
                    if type(v) is not bool: raise ValueError()
                elif not isinstance(v, str): raise ValueError()
        for kind, candidate in case['candidates'].items():
            if (candidate['floor'], candidate['support'], candidate['combination']) != (case['floor'], case['support'], case['combination']): raise ValueError()
            if candidate['kind'] != kind: raise ValueError()
            if candidate.get('adapter'):
                from .analysis_import import validate_candidate
                validate_candidate(candidate)
                continue
            # Rebuild from the archived raw rows and mapping to detect edited derived values.
            from .table_import import Table, ImportConfig, prepare_import
            records = candidate['records']; source = records[0]['source']; headers = list(source['raw'])
            if any(r['source']['config'] != source['config'] or r['source']['mapping'] != source['mapping'] or list(r['source']['raw']) != headers for r in records): raise ValueError()
            rows = [(r['source']['row'], list(r['source']['raw'].values())) for r in records]
            table = Table(source['file'], source['sha256'], source['sheet'], headers, rows, set())
            rebuilt = prepare_import(table, source['mapping'], ImportConfig(**source['config']))['loads'][key(case['floor'], case['support'], case['combination'])]
            for k in ('adopted', 'method', 'issues', 'records', 'reference'):
                if candidate[k] != rebuilt[k]: raise ValueError('Os esforços derivados não correspondem às linhas de origem guardadas.')
        json.dumps(case, allow_nan=False)
    except (KeyError, TypeError, IndexError, ValueError) as exc:
        raise ValueError('Registo de ligação inválido. ' + str(exc)) from exc


def case_from_payload(payload, defaults=None):
    from .migrations import normalize_archive
    payload=normalize_archive(payload)
    case = payload.get('import_case')
    if case is None and payload.get('load_trace') is not None:
        trace=payload['load_trace'];case=fresh_case(trace['floor'],trace['support'],trace['combination'])
        case.update({k:deepcopy(trace[k]) for k in ('choice','reference','candidates','geometry')})
    if case is not None:
        from .longitudinal import upgrade_draft
        upgrade_draft(case.get('draft'))
        validate_case(case, defaults)
    return deepcopy(case)


def trace_for_api_inputs(payload, inputs):
    case=case_from_payload(payload)
    if case is None: return None
    draft={k:str(inputs.get(k, '') if inputs.get(k) is not None else '') for k in ('combination','pilar_forma','pilar_c1','pilar_c2')}
    for k in FORCE_KEYS: draft[k]=str(float(inputs[k])/1000)
    for k in ('pilar_tipo','edge_perp_interior','corner_interior'):
        if k in inputs:draft[k]=inputs[k]
    return provenance(case,draft)
