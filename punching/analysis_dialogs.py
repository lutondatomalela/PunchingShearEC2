"""Review recognized Modelo records and prepare one physical joint at a time."""
import tkinter as tk
from tkinter import ttk, messagebox

from .import_dialogs import window, text_view, set_text, ImportDialog
from .ui import ScrollTab, FlowLabel
from .analysis_import import all_records, members, parse_nodes, restore, member_role, build_joint, AXES, name_note, name_summary, modal_combination_issue
from .table_import import token


def table_view(parent, columns, height=9):
    frame = ttk.Frame(parent); frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=[k for k, _, _ in columns], show='headings', height=height, selectmode='browse')
    tree.grid(row=0, column=0, sticky='nsew')
    for k, title, width in columns:
        tree.heading(k, text=title); tree.column(k, width=width, minwidth=65)
    y = ttk.Scrollbar(frame, orient='vertical', command=tree.yview); y.grid(row=0, column=1, sticky='ns')
    x = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview); x.grid(row=1, column=0, sticky='ew')
    tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    return frame, tree


class ModeloBrowser(tk.Toplevel):
    PAGE_SIZE = 250

    def __init__(self, parent, app):
        super().__init__(parent); self.app = app; self.page = 0
        window(self, parent, 'Modelo · barras, nós e esforços', 1140, 790)
        header = ttk.Frame(self, padding=14); header.grid(row=0, column=0, sticky='ew'); header.columnconfigure(1, weight=1)
        ttk.Label(header, text='Filtrar piso, pilar, barra, nó ou combinação').grid(row=0, column=0, sticky='w', padx=(0, 12))
        self.search = tk.StringVar(self); ttk.Entry(header, textvariable=self.search).grid(row=0, column=1, sticky='ew')
        ttk.Button(header, text='Adicionar tabela…', command=self._import).grid(row=0, column=2, padx=(10, 0))
        self.summary = tk.StringVar(self)
        ttk.Label(header, textvariable=self.summary, style='Muted.TLabel').grid(row=1, column=0, columnspan=3, sticky='w', pady=(10, 0))
        pane = ttk.Panedwindow(self, orient='vertical'); pane.grid(row=1, column=0, sticky='nsew', padx=14)
        frame, self.tree = table_view(pane, [('story', 'Piso da barra', 110), ('name', 'Pilar', 75),
            ('member', 'Barra', 70), ('node', 'Nó', 75), ('position', 'Posição do nó', 100),
            ('combo', 'Caso / combinação', 145), ('n', 'FX · kN', 100),
            ('my', 'MY local · kN.m', 115), ('mz', 'MZ local · kN.m', 115), ('section', 'Secção · cm', 140)])
        pane.add(frame, weight=3)
        details, self.details = text_view(pane); pane.add(details, weight=2)
        footer = ttk.Frame(self, padding=14); footer.grid(row=2, column=0, sticky='ew'); footer.columnconfigure(2, weight=1)
        self.previous = ttk.Button(footer, text='Anterior', command=lambda: self._page(-1)); self.previous.grid(row=0, column=0)
        self.next = ttk.Button(footer, text='Seguinte', command=lambda: self._page(1)); self.next.grid(row=0, column=1, padx=8)
        self.page_label = tk.StringVar(self); ttk.Label(footer, textvariable=self.page_label).grid(row=0, column=2, sticky='w')
        self.prepare = ttk.Button(footer, text='Preparar ligação neste nó…', style='Primary.TButton', command=self._prepare, state='disabled')
        self.prepare.grid(row=0, column=3, padx=8)
        ttk.Button(footer, text='Fechar', command=self.destroy).grid(row=0, column=4)
        self.tree.bind('<<TreeviewSelect>>', self._detail); self.tree.bind('<Double-1>', lambda e: self._prepare())
        self.search.trace_add('write', self._filter); self._reload()

    def _reload(self):
        self.records = all_records(self.app._book.analysis_tables); self.index = members(self.records)
        self.nodes = parse_nodes(restore(self.app._book.analysis_nodes)) if self.app._book.analysis_nodes else {}
        unnamed = len({r['member'] for r in self.records if r.get('name_resolution')})
        self.summary.set(f"{len(self.records)} resultados · {len(self.index)} barras · {len({r['node'] for r in self.records})} nós de resultados · " + (f'{len(self.nodes)} nós com coordenadas' if self.nodes else 'Coordenadas por importar (opcional)') + (f' · {unnamed} barras com Name em falta' if unnamed else ''))
        self._filter()

    def _filter(self, *_):
        query = token(self.search.get())
        self.filtered = [i for i, r in enumerate(self.records) if query in token(' '.join(r[k] for k in ('story', 'support', 'member', 'node', 'combination')))]
        self.page = 0; self._render()

    def _page(self, step):
        self.page = max(0, min(self.page+step, max(0, (len(self.filtered)-1)//self.PAGE_SIZE))); self._render()

    def _render(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        start = self.page*self.PAGE_SIZE
        for i in self.filtered[start:start+self.PAGE_SIZE]:
            r = self.records[i]; v = r['values']; sec = r['section']
            role, _ = member_role(r['member'], r['node'], self.index, self.nodes)
            position = {'below': 'Topo', 'above': 'Base', 'unsupported': 'Não vertical'}.get(role, 'Por confirmar')
            section = (f"{sec['hy']*100:g} × {sec['hz']*100:g}" if sec['shape']=='retangular' else f"Ø {sec['hy']*100:g}") if sec else 'Por confirmar'
            self.tree.insert('', 'end', iid=str(i), values=(r['story'], r['support'], r['member'], r['node'], position,
                r['combination'], f"{v['fx']:.3f}", f"{v['my']:.3f}", f"{v['mz']:.3f}", section))
        self.previous.configure(state='normal' if self.page else 'disabled')
        self.next.configure(state='normal' if start+self.PAGE_SIZE < len(self.filtered) else 'disabled')
        self.page_label.set(f'{start+1 if self.filtered else 0}–{min(start+self.PAGE_SIZE,len(self.filtered))} de {len(self.filtered)}')
        self.prepare.configure(state='disabled')
        guidance = 'Selecione um resultado para conferir a origem e preparar a ligação no nó. FX é o axial acumulado da barra. MY/MZ são momentos locais. A carga transferida pela laje é obtida posteriormente pelo equilíbrio no nó, com as orientações conferidas.'
        notes = name_summary(self.records)
        set_text(self.details, '\n\n'.join(notes + [guidance]))

    def _detail(self, *_):
        selection = self.tree.selection(); self.prepare.configure(state='normal' if selection else 'disabled')
        if not selection: return
        r = self.records[int(selection[0])]; s = r['source']; v = r['values']
        connected = [m for m, data in self.index.items() if r['node'] in data['nodes']]
        coords = self.nodes.get(r['node'])
        lines = [f"{r['support']} · {r['story']} · barra {r['member']} · nó {r['node']} · {r['combination']}",
            'Barras presentes na tabela que chegam a este nó: ' + ', '.join(connected),
            ('Coordenadas (m): ' + '; '.join(f'{k.upper()}={value:g}' for k, value in coords.items())) if coords else 'Coordenadas não carregadas. Não se deduz topo/base pela ordem das linhas ou pela numeração.',
            f"FX={v['fx']:.6g} kN; MY={v['my']:.6g}; MZ={v['mz']:.6g} kN.m, nos eixos locais da barra.",
            r['section_issue'] or 'Secção maciça compatível com HY/HZ, AX, IY e IZ. A correspondência com c1/c2 será definida pelos eixos locais.',
            f"Origem: {s['file']} · {s['sheet']} · linha {s['row']}",
            'Valores originais: ' + '; '.join(f'{k}={value}' for k, value in s['raw'].items()),
            'SHA-256: ' + s['sha256']]
        if name_note(r): lines.insert(1, name_note(r))
        if modal_combination_issue(r['combination']): lines.insert(1, modal_combination_issue(r['combination']))
        set_text(self.details, '\n\n'.join(lines))

    def _prepare(self):
        selection = self.tree.selection()
        if not selection: return
        dialog = ModeloJointDialog(self, self.app, self.records[int(selection[0])])
        self.wait_window(dialog); self.grab_set()
        if dialog.result is not None:
            try:
                self.app._merge_import(dialog.result)
                set_text(self.details, f"Ligação preparada: {len(dialog.result['loads'])} caso(s)/combinação(ões). Feche esta janela e selecione a ligação em «Pilares…» para definir a laje e adotar a origem dos esforços.")
            except Exception as exc: messagebox.showerror('Preparar ligação', str(exc), parent=self)

    def _import(self):
        dialog = ImportDialog(self); self.wait_window(dialog); self.grab_set()
        if dialog.result is not None:
            try: self.app._merge_import(dialog.result); self._reload()
            except Exception as exc: messagebox.showerror('Importar tabela', str(exc), parent=self)


class ModeloJointDialog(tk.Toplevel):
    def __init__(self, parent, app, selected):
        super().__init__(parent); self.app = app; self.result = None; self.options = {}; self.checks = {}
        window(self, parent, 'Preparar ligação laje–pilar a partir do Modelo', 1080, 830)
        records = all_records(app._book.analysis_tables); self.index = members(records)
        nodes = parse_nodes(restore(app._book.analysis_nodes)) if app._book.analysis_nodes else {}
        self.node = selected['node']
        self.connected = {m: data for m, data in self.index.items() if self.node in data['nodes']}
        title = ttk.Frame(self, padding=14); title.grid(row=0, column=0, sticky='ew'); title.columnconfigure(0, weight=1)
        FlowLabel(title, text=f"Nó {self.node} · {len(self.connected)} barra(s) com resultados neste nó. Associe os tramos na cota da laje.", style='Section.TLabel').grid(row=0, column=0, sticky='ew')
        self.tabs = ttk.Notebook(self); self.tabs.grid(row=1, column=0, sticky='nsew', padx=14)
        source = ScrollTab(self.tabs); self.tabs.add(source, text='1 · Associação e eixos')
        preview, self.preview = text_view(self.tabs); self.tabs.add(preview, text='2 · Equilíbrio e conferência')
        form = source.body; form.columnconfigure(1, weight=1)
        self.scroll_tab = source
        for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'): self.bind(seq, self._wheel)
        self.member_labels = {'': ''}
        for m, data in self.connected.items(): self.member_labels[f"{m} · {data['support']} · {data['story']}"] = m
        suggestions = {}
        for role in ('below', 'above'):
            match = [m for m in self.connected if member_role(m, self.node, self.index, nodes)[0] == role]
            suggestions[role] = match[0] if len(match)==1 else ''
        combo_labels = ['Todas as combinações deste par', 'Apenas '+selected['combination']]
        self.selected_combo = selected['combination']
        fields = [('floor', 'Piso da ligação (confirmar a cota)', None, selected['story']),
            ('support', 'Identificação do pilar / ligação', None, selected['support']),
            ('below', 'Tramo inferior · nó selecionado no topo', list(self.member_labels), self._label(suggestions['below'])),
            ('above', 'Tramo superior · nó selecionado na base', list(self.member_labels), self._label(suggestions['above'])),
            ('below_x', 'Inferior: x local longitudinal', ['', '+Z', '-Z'], ''),
            ('below_y', 'Inferior: y local transversal', ['']+list(AXES), ''),
            ('above_x', 'Superior: x local longitudinal', ['', '+Z', '-Z'], ''),
            ('above_y', 'Superior: y local transversal', ['']+list(AXES), ''),
            ('combination', 'Casos a preparar', combo_labels, combo_labels[1]),
            ('reference', 'Referência do modelo / conferência', None, '')]
        for i, (name, label, choices, initial) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky='w', padx=(12, 18), pady=5)
            var = tk.StringVar(self, initial); self.options[name] = var
            widget = ttk.Combobox(form, textvariable=var, values=choices, state='readonly') if choices else ttk.Entry(form, textvariable=var)
            widget.grid(row=i, column=1, sticky='ew', padx=(0, 12), pady=5)
        i = len(fields)
        FlowLabel(form, text='Eixos do caso: X paralelo a c1; Y paralelo a c2; +Z para cima. Indique as direções locais observadas no Modelo. O eixo z local resulta de x × y. Só se admitem aqui eixos transversais paralelos a X/Y; para outras orientações, importe resultantes já convertidas.\nStory pertence à barra; a designação do piso da ligação deve corresponder ao nó escolhido.', style='Muted.TLabel').grid(row=i, column=0, columnspan=2, sticky='ew', padx=12, pady=12)
        declarations = [
            ('upper_absent', 'Não existe fisicamente tramo superior neste nó (por exemplo, cobertura).'),
            ('analysis_3d', 'Os esforços são de barras de um modelo 3D Modelo. Este adaptador não aplica a convenção especial dos pórticos 2D.'),
            ('same_combination', 'Conferi as combinações e a natureza dos esforços. Para obter resultantes por equilíbrio, os esforços têm de ser originais ELU concomitantes, e não momentos de dimensionamento. Envolventes e combinações CQC/SRSS ficam pendentes.'),
            ('isolated_joint', 'Os tramos são verticais e alinhados; a laje é a única transferência de carga no nó. Conferi que não há vigas, outros pilares ou cargas nodais a incluir.'),
            ('at_joint', 'Os resultados são nos extremos reais, no centro do pilar e na cota da laje, sem offsets ou ligações rígidas que exijam transporte de esforços. Conferi inferior/superior.'),
            ('axes_confirmed', 'Conferi x/y locais de cada barra no Modelo e a sua correspondência com os eixos do caso. A classificação da secção por AX/IY/IZ foi conferida no modelo.')]
        for j, (name, label) in enumerate(declarations, i+1):
            line = ttk.Frame(form); line.grid(row=j, column=0, columnspan=2, sticky='ew', padx=12, pady=5); line.columnconfigure(1, weight=1)
            var = tk.BooleanVar(self, False); self.checks[name] = var
            check = ttk.Checkbutton(line, variable=var); check.grid(row=0, column=0, sticky='n', padx=(0, 5))
            caption = FlowLabel(line, text=label); caption.grid(row=0, column=1, sticky='ew'); caption.bind('<Button-1>', lambda e, c=check: c.invoke())
        footer = ttk.Frame(self, padding=14); footer.grid(row=2, column=0, sticky='ew'); footer.columnconfigure(0, weight=1)
        ttk.Button(footer, text='Conferir equilíbrio', command=self._preview).grid(row=0, column=0, sticky='w')
        self.apply = ttk.Button(footer, text='Adicionar ligação', style='Primary.TButton', command=self._apply, state='disabled'); self.apply.grid(row=0, column=1)
        ttk.Button(footer, text='Cancelar', command=self.destroy).grid(row=0, column=2, padx=(8, 0))
        for var in (*self.options.values(), *self.checks.values()): var.trace_add('write', self._invalidate)

    def _label(self, member): return next((label for label, m in self.member_labels.items() if m == member), '')

    def _wheel(self, event):
        target = self.winfo_containing(event.x_root, event.y_root)
        if target is not None and str(target).startswith(str(self.scroll_tab)):
            num = getattr(event, 'num', None); delta = getattr(event, 'delta', 0)
            step = -1 if num == 4 or delta > 0 else 1 if num == 5 or delta < 0 else 0
            if step: self.scroll_tab.canvas.yview_scroll(step*3, 'units')
            return 'break'

    def _invalidate(self, *_): self.apply.configure(state='disabled')

    def _build(self):
        setup = {k: v.get() for k, v in self.checks.items()}
        setup.update({k: self.options[k].get().strip() for k in ('floor', 'support', 'reference')})
        setup['node'] = self.node
        setup['combination'] = self.selected_combo if self.options['combination'].get().startswith('Apenas ') else ''
        for role in ('below', 'above'):
            setup[role] = self.member_labels.get(self.options[role].get(), '')
            setup[role+'_axes'] = {axis: self.options[role+'_'+axis].get() for axis in ('x', 'y')}
        return build_joint(self.app._book.analysis_tables, setup, self.app._book.analysis_nodes)

    def _preview(self):
        self._invalidate()
        try:
            from .analysis_import import analysis_source_lines
            batch = self._build(); lines = []
            for load in batch['loads'].values():
                lines.append(load['combination'] + (' · Esforços obtidos' if load['adopted'] else ' · Esforços pendentes'))
                lines.extend(analysis_source_lines(load)); lines.append('')
            lines.append('A adição cria casos por combinação. A laje, os bordos, as aberturas e a adoção dos esforços são definidos na ligação.')
            set_text(self.preview, '\n\n'.join(lines)); self.tabs.select(1); self.apply.configure(state='normal')
        except Exception as exc: set_text(self.preview, str(exc)); self.tabs.select(1)

    def _apply(self):
        try: self.result = self._build(); self.destroy()
        except Exception as exc: messagebox.showerror('Preparar ligação', str(exc), parent=self)
