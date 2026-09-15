"""Optional desktop workflow for external column/connection tables."""
from copy import deepcopy
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .ui import ScrollTab, FlowLabel, COLORS
from .table_import import (MODES, MODE_FIELDS, FIELDS, REQUIRED, ImportConfig,
                           read_table, worksheets, suggest_mapping, prepare_import, token)
from .connections import describe_case, adopt, geometry_text
from .analysis_import import (profile, automatic_layout, prepare_analysis_table, parse_bars,
                           parse_nodes, members, column_map, detect_decimal, name_summary, modal_combination_issue)


def window(dialog, parent, title, width=1040, height=740):
    dialog.title(title); dialog.transient(parent)
    sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
    dialog.geometry(f'{min(width, sw-70)}x{min(height, sh-100)}')
    dialog.minsize(min(780, sw-70), min(560, sh-100))
    dialog.columnconfigure(0, weight=1); dialog.rowconfigure(1, weight=1)
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    dialog.grab_set()


def text_view(parent):
    frame = ttk.Frame(parent); frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
    text = tk.Text(frame, wrap='word', font=('Segoe UI', 10), padx=12, pady=10, borderwidth=0,
                   background=COLORS['surface'], foreground=COLORS['ink'], state='disabled')
    text.grid(row=0, column=0, sticky='nsew')
    bar = ttk.Scrollbar(frame, orient='vertical', command=text.yview); bar.grid(row=0, column=1, sticky='ns')
    text.configure(yscrollcommand=bar.set)
    return frame, text


def set_text(widget, text):
    widget.configure(state='normal'); widget.delete('1.0', 'end'); widget.insert('end', text); widget.configure(state='disabled')


class ImportDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.result = None; self.table = None; self.mapping = {}; self.mode_keys = list(MODES)
        window(self, parent, 'Importar tabela de pilares ou da ligação')
        top = ttk.Frame(self, padding=14); top.grid(row=0, column=0, sticky='ew'); top.columnconfigure(1, weight=1)
        ttk.Label(top, text='Tabela', style='Section.TLabel').grid(row=0, column=0, padx=(0, 10))
        self.path = tk.StringVar(self); ttk.Entry(top, textvariable=self.path).grid(row=0, column=1, sticky='ew')
        ttk.Button(top, text='Escolher…', command=self._choose).grid(row=0, column=2, padx=(8, 0))
        self.tabs = ttk.Notebook(self); self.tabs.grid(row=1, column=0, sticky='nsew', padx=14)
        source = ScrollTab(self.tabs); self.tabs.add(source, text='1 · Leitura e convenções')
        self.map_tab = ScrollTab(self.tabs); self.tabs.add(self.map_tab, text='2 · Associar colunas')
        preview, self.preview = text_view(self.tabs); self.tabs.add(preview, text='3 · Conferir importação')
        self.scroll_tabs = (source, self.map_tab)
        for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'): self.bind(seq, self._wheel)
        self.options = {}; self.option_widgets = {}
        form = source.body; form.columnconfigure(1, weight=1)
        choices = [
            ('mode', 'Conteúdo da tabela', list(MODES.values()), 0),
            ('sheet', 'Folha do XLSX', ['CSV'], 0), ('header', 'Linha dos cabeçalhos', None, '1'),
            ('delimiter', 'Separador CSV', ['Automático', ';', 'Tabulação', ','], 0),
            ('encoding', 'Codificação CSV', ['Automática (UTF-8 / BOM)', 'utf-8-sig', 'utf-16', 'cp1252'], 0),
            ('decimal', 'Separador decimal (sem milhares)', ['.', ','], 0),
            ('length_unit', 'Unidade das dimensões', ['m', 'cm', 'mm'], 0),
            ('force_unit', 'Unidade das forças', ['kN', 'N'], 0),
            ('moment_unit', 'Unidade dos momentos', ['kN.m', 'N.m', 'N.mm', 'kN.cm'], 0),
            ('compression', 'Sinal de N em compressão (pilares)', ['Positivo', 'Negativo'], 0),
            ('resultant_convention', 'Momentos da tabela de resultantes', ['Programa: ex=My/V; ey=Mx/V', 'Vetorial: reação sobre a laje, +Z para cima'], 0),
        ]
        for row, (k, label, options, initial) in enumerate(choices):
            caption = ttk.Label(form, text=label); caption.grid(row=row, column=0, sticky='w', padx=(12, 20), pady=5)
            var = tk.StringVar(self, value=options[initial] if options else initial); self.options[k] = var
            widget = ttk.Combobox(form, textvariable=var, values=options, state='readonly') if options else ttk.Entry(form, textvariable=var)
            widget.grid(row=row, column=1, sticky='ew', padx=(0, 15), pady=5)
            self.option_widgets[k] = (caption, widget)
            if k == 'sheet': self.sheet_box = widget
            if k == 'mode': widget.bind('<<ComboboxSelected>>', lambda e: self._mode_changed())
        self.declarations = {}
        self.declaration_frame = ttk.LabelFrame(form, text='Significado dos esforços exportados', padding=12)
        self.declaration_frame.grid(row=len(choices), column=0, columnspan=2, sticky='ew', pady=12, padx=12)
        self.declaration_frame.columnconfigure(1, weight=1)
        labels = {
            'same_combination': 'Esforços originais de análise, da mesma combinação ELU. Não são máximos independentes nem momentos de dimensionamento do pilar.',
            'axes_at_column': 'Esforços já no centro do pilar e na cota da laje. X paralelo a c1; Y paralelo a c2 (no bordo, +Y para o interior). Nos tramos: Mx/My são ações vetoriais DOS PILARES SOBRE O NÓ, com +Z para cima.',
            'isolated_joint': 'Tramos verticais alinhados; a laje é a única origem da transferência no nó. Sem vigas, pilares adicionais, excentricidades de eixos ou outras cargas nodais.',
            'full_connection': 'Resultante da ligação completa, em kN e kN.m nas unidades escolhidas. Sem dedução de cargas interiores a u1 e sem majoração por beta. Não são valores locais Mxx/Myy/Qx/Qy por metro.',
        }
        self.declaration_rows = {}
        for i, (name, label) in enumerate(labels.items()):
            row = ttk.Frame(self.declaration_frame); row.grid(row=i, column=0, columnspan=2, sticky='ew', pady=5); row.columnconfigure(1, weight=1)
            var = tk.BooleanVar(self, False); self.declarations[name] = var
            check = ttk.Checkbutton(row, variable=var); check.grid(row=0, column=0, sticky='n', padx=(0, 5))
            text = FlowLabel(row, text=label); text.grid(row=0, column=1, sticky='ew'); text.bind('<Button-1>', lambda e, c=check: c.invoke())
            self.declaration_rows[name] = row
        ttk.Label(form, text='Referência da exportação / observações').grid(row=len(choices)+1, column=0, columnspan=2, sticky='w', padx=12)
        self.reference = tk.StringVar(self); ttk.Entry(form, textvariable=self.reference).grid(row=len(choices)+2, column=0, columnspan=2, sticky='ew', padx=12, pady=(6, 12))
        footer = ttk.Frame(self, padding=14); footer.grid(row=2, column=0, sticky='ew'); footer.columnconfigure(0, weight=1)
        ttk.Button(footer, text='Ler tabela', command=self._read).grid(row=0, column=0, sticky='w')
        ttk.Button(footer, text='Conferir', command=self._preview).grid(row=0, column=1, padx=8)
        self.import_button = ttk.Button(footer, text='Importar', style='Primary.TButton', command=self._apply, state='disabled'); self.import_button.grid(row=0, column=2)
        ttk.Button(footer, text='Cancelar', command=self.destroy).grid(row=0, column=3, padx=(8, 0))
        for v in (*self.options.values(), *self.declarations.values(), self.reference, self.path): v.trace_add('write', self._invalidate)
        self._mode_changed()

    def _wheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        for tab in self.scroll_tabs:
            if widget is not None and str(widget).startswith(str(tab)):
                num = getattr(event, 'num', None); delta = getattr(event, 'delta', 0)
                step = -1 if num == 4 or delta > 0 else 1 if num == 5 or delta < 0 else 0
                if step: tab.canvas.yview_scroll(step*3, 'units')
                return 'break'

    def _invalidate(self, *_): self.import_button.configure(state='disabled')
    def _mode(self): return self.mode_keys[list(MODES.values()).index(self.options['mode'].get())]

    def _mode_changed(self):
        mode = self._mode()
        for name in ('decimal', 'length_unit', 'force_unit', 'moment_unit', 'compression', 'resultant_convention'):
            for widget in self.option_widgets[name]:
                if mode.startswith('analysis'): widget.grid_remove()
                else: widget.grid()
        for name, row in self.declaration_rows.items():
            if mode in ('columns', 'resultants') and (name in ('same_combination', 'axes_at_column') or (name=='isolated_joint' and mode=='columns') or (name=='full_connection' and mode=='resultants')): row.grid()
            else: row.grid_remove()
        if self.table: self._mapping()
        self._invalidate()

    def _choose(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('Tabelas', '*.xlsx *.csv *.tsv *.txt'), ('Todos os ficheiros', '*.*')])
        if not path: return
        try:
            sheets = worksheets(path); self.path.set(path); self.sheet_box.configure(values=sheets); self.options['sheet'].set(sheets[0])
            self.table = None
            self._read()
        except Exception as exc: messagebox.showerror('Ler tabela', str(exc), parent=self)

    def _read_signature(self):
        return tuple([self.path.get()] + [self.options[k].get() for k in ('sheet', 'header', 'delimiter', 'encoding')])

    def _read(self):
        try:
            # A recognized Modelo header is unambiguous even after title rows.
            layout = automatic_layout(self.path.get(), self.options['sheet'].get())
            if layout:
                self.options['header'].set(str(layout['header_row']))
                if 'delimiter' in layout: self.options['delimiter'].set('Tabulação' if layout['delimiter']=='\t' else layout['delimiter'])
                if 'encoding' in layout: self.options['encoding'].set(layout['encoding'])
            delimiter = {'Automático': 'auto', 'Tabulação': '\t'}.get(self.options['delimiter'].get(), self.options['delimiter'].get())
            encoding = self.options['encoding'].get(); encoding = 'auto' if encoding.startswith('Automática') else encoding
            self.table = read_table(self.path.get(), self.options['sheet'].get(), int(self.options['header'].get()), delimiter, encoding)
            detected = profile(self.table.headers)
            if detected: self.options['mode'].set(MODES[detected])
            self.read_signature = self._read_signature(); self._mode_changed(); self._mapping(); self.tabs.select(1)
        except Exception as exc: self.table = None; messagebox.showerror('Ler tabela', str(exc), parent=self)
        self._invalidate()

    def _mapping(self):
        for child in self.map_tab.body.winfo_children(): child.destroy()
        self.mapping = {}; form = self.map_tab.body; form.columnconfigure(1, weight=1)
        title = f'{self.table.file} · {self.table.sheet} · {len(self.table.rows)} linhas. * Campo obrigatório.'
        FlowLabel(form, text=title, style='Muted.TLabel').grid(row=0, column=0, columnspan=2, sticky='ew', padx=12, pady=12)
        if self._mode().startswith('analysis'):
            FlowLabel(form, text=self._analysis_summary(), style='Body.TLabel').grid(row=1, column=0, columnspan=2, sticky='ew', padx=12, pady=12)
            return
        suggestions = suggest_mapping(self.table, self._mode())
        for i, k in enumerate(MODE_FIELDS[self._mode()], 1):
            label = FIELDS[k] + (' *' if k in REQUIRED[self._mode()] else '')
            if self._mode() == 'resultants' and k in ('mx', 'my'): label = k.upper() + ' da ligação *'
            ttk.Label(form, text=label).grid(row=i, column=0, sticky='w', padx=(12, 20), pady=5)
            var = tk.StringVar(self, suggestions.get(k, '')); self.mapping[k] = var
            ttk.Combobox(form, textvariable=var, values=['']+self.table.headers, state='readonly').grid(row=i, column=1, sticky='ew', padx=(0, 15), pady=5)
            var.trace_add('write', self._invalidate)
        sample = '\n'.join('  |  '.join(str(x) if x is not None else '' for x in values) for _, values in self.table.rows[:4])
        FlowLabel(form, text='Primeiras linhas:\n' + sample, style='Muted.TLabel').grid(row=i+1, column=0, columnspan=2, sticky='ew', padx=12, pady=14)

    def _build(self):
        if not self.table or self.read_signature != self._read_signature(): raise ValueError('Clique «Ler tabela» para atualizar os dados do ficheiro.')
        if self._mode().startswith('analysis'): return prepare_analysis_table(self.table)
        config = ImportConfig(mode=self._mode(), **{k: self.options[k].get() for k in ('length_unit', 'force_unit', 'moment_unit', 'decimal')},
            compression='positive' if self.options['compression'].get() == 'Positivo' else 'negative',
            resultant_convention='program' if self.options['resultant_convention'].get().startswith('Programa') else 'vector',
            **{k: v.get() for k, v in self.declarations.items()}, reference=self.reference.get())
        return prepare_import(self.table, {k: v.get() for k, v in self.mapping.items()}, config)

    def _analysis_summary(self):
        try:
            if profile(self.table.headers) == 'analysis_nodes':
                nodes = parse_nodes(self.table)
                return f'Modelo reconhecido: {len(nodes)} nós.\nNode → identificação; X/Y/Z → coordenadas. As unidades dos cabeçalhos são convertidas para metros.\n\nA associação às barras usa o número exato do nó.'
            records = parse_bars(self.table); index = members(records)
            rows = [f'Modelo reconhecido: {len(index)} barras; {len({r["node"] for r in records})} nós; {len({r["combination"] for r in records})} casos/combinações.',
                'Member/Node/Case → Barra + Nó + Caso/combinação\nName → Pilar\nStory → Piso da barra\nFX → Axial local (compressão positiva)\nMY/MZ → Momentos locais\nHY/HZ + AX/IY/IZ → Dimensões e conferência da secção',
                f'Decimal reconhecido: «{detect_decimal(self.table, column_map(self.table))}». Unidades lidas de cada cabeçalho; apresentação em m, kN e kN.m.',
                'Depois de importar, abra «Barras e nós…» e selecione o nó da ligação. A ordem dos nós não define topo/base; Story identifica o piso da barra. A orientação dos eixos locais é conferida ao preparar a ligação.',
                'Primeiros registos:']
            rows[1:1] = name_summary(records)
            modal_cases = {r['combination'] for r in records if modal_combination_issue(r['combination'])}
            if modal_cases: rows[1:1] = [f'{len(modal_cases)} combinações CQC/SRSS conservadas para consulta. O equilíbrio direto Ninf−Nsup não é aplicado a esses resultados; é necessária uma resultante da ligação com tratamento modal adequado.']
            stories = {}
            for r in records: stories[r['story']] = stories.get(r['story'], 0)+1
            rows[1:1] = ['Pisos presentes: '+ '; '.join(f'{story}: {count} registos' for story, count in sorted(stories.items())) + '.']
            for r in records[:8]:
                v = r['values']; rows.append(f"{r['story']} · {r['support']} · barra {r['member']} · nó {r['node']} · {r['combination']}: FX={v['fx']:.6g}; MY={v['my']:.6g}; MZ={v['mz']:.6g} (kN; kN.m).")
            return '\n\n'.join(rows)
        except (ValueError, KeyError, TypeError) as exc: return 'Formato Modelo identificado.\n\n' + str(exc)

    def _preview(self):
        self._invalidate()
        try:
            batch = self._build()
            if batch['mode'].startswith('analysis'):
                set_text(self.preview, self._analysis_summary()); self.tabs.select(2); self.import_button.configure(state='normal'); return
            lines = [f"{batch['row_count']} linhas lidas. {len(batch['geometries'])} geometrias; {len(batch['loads'])} ligações/combinações."]
            for geom in batch['geometries'].values(): lines.append(f"Piso {geom['floor']}, pilar {geom['support']}: {geometry_text(geom['inputs'])}")
            for load in batch['loads'].values():
                values = '; '.join(f'{k}={v:.6g}' for k, v in (load['adopted'] or {}).items())
                lines.append(f"{load['floor']} / {load['support']} / {load['combination']}: {values or 'Esforços por resolver'} (kN; kN.m).")
                lines.extend(load['issues'])
            lines.append('A importação com pendências permite completar o caso manualmente; não autoriza o cálculo com esforços em falta.')
            set_text(self.preview, '\n\n'.join(lines)); self.tabs.select(2); self.import_button.configure(state='normal')
        except Exception as exc: set_text(self.preview, str(exc)); self.tabs.select(2)

    def _apply(self):
        try: self.result = self._build(); self.destroy()
        except Exception as exc: messagebox.showerror('Importar', str(exc), parent=self)


class ConnectionDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app); self.app = app; self.result = None
        window(self, app, 'Pilares e ligações laje–pilar')
        header = ttk.Frame(self, padding=14); header.grid(row=0, column=0, sticky='ew'); header.columnconfigure(0, weight=1)
        self.search = tk.StringVar(self); entry = ttk.Entry(header, textvariable=self.search); entry.grid(row=0, column=0, sticky='ew', padx=(0, 12))
        for i, (text, fn) in enumerate([('Novo', self._new), ('Importar tabela…', self._import), ('Abrir conjunto…', self._open), ('Guardar conjunto…', self._save)], 1):
            ttk.Button(header, text=text, command=fn).grid(row=0, column=i, padx=4)
        filters=ttk.Frame(header);filters.grid(row=1,column=0,columnspan=5,sticky='ew',pady=(10,0))
        self.floor=tk.StringVar(self,'Todos os pisos');self.kind=tk.StringVar(self,'Todas as posições');self.group=tk.StringVar(self,'Todos os grupos')
        for i,(var,attr) in enumerate([(self.floor,'floor_box'),(self.kind,'kind_box'),(self.group,'group_box')]):
            box=ttk.Combobox(filters,textvariable=var,state='readonly');box.grid(row=0,column=i,sticky='ew',padx=4);filters.columnconfigure(i,weight=1);setattr(self,attr,box)
            var.trace_add('write',self._filter)
        pane = ttk.Panedwindow(self, orient='vertical'); pane.grid(row=1, column=0, sticky='nsew', padx=14)
        table = ttk.Frame(pane); table.rowconfigure(0, weight=1); table.columnconfigure(0, weight=1); pane.add(table, weight=2)
        self.tree = ttk.Treeview(table, columns=('floor','support','combination','group','kind','status'),show='headings',height=8,selectmode='extended')
        for k, title, width in [('floor','Piso',100),('support','Pilar',75),('combination','Combinações',120),('group','Grupo',160),('kind','Posição / bordo',135),('status','Calculadas / total · Situação',220)]:
            self.tree.heading(k, text=title); self.tree.column(k, width=width, minwidth=80)
        app._tree_scrollbars(table, self.tree, 0, horizontal=True)
        detail, self.details = text_view(pane); pane.add(detail, weight=3)
        footer = ttk.Frame(self, padding=14); footer.grid(row=2, column=0, sticky='ew'); footer.columnconfigure(0, weight=1)
        FlowLabel(footer, text='Selecione uma ligação para completar a laje e calcular. Os dados de cada caso são conservados.').grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.open_button = ttk.Button(footer, text='Analisar ligação', style='Primary.TButton', command=self._select, state='disabled'); self.open_button.grid(row=0, column=1)
        ttk.Button(footer, text='Caso individual', command=self._individual).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(footer, text='Fechar', command=self.destroy).grid(row=0, column=3, padx=(8, 0))
        self.analysis_button = ttk.Button(footer, text='Barras e nós…', command=self._analysis)
        self.analysis_button.grid(row=1, column=0, sticky='w', pady=(10, 0))
        self.model_button=ttk.Button(footer,text='Preparar modelo…',command=self._model)
        self.model_button.grid(row=1,column=1,sticky='ew',pady=(10,0))
        self.report_button=ttk.Button(footer,text='Relatório do conjunto…',command=self._report)
        self.report_button.grid(row=1,column=2,columnspan=2,sticky='ew',padx=(8,0),pady=(10,0))
        actions=ttk.Frame(footer);actions.grid(row=2,column=0,columnspan=4,sticky='ew',pady=10)
        self.batch_buttons=[]
        for i,(label,fn) in enumerate([('Selecionar visíveis',self._all_visible),('Limpar seleção',self._clear_selection),('Agrupar…',self._group_selection),('Editar seleção…',self._edit_selection),('Calcular seleção',self._calculate_selection)]):
            button=ttk.Button(actions,text=label,command=fn);button.grid(row=0,column=i,padx=3)
            if i>=2:self.batch_buttons.append(button)
        self.remove_button=ttk.Button(actions,text='Dissolver grupo',command=self._remove_group);self.remove_button.grid(row=0,column=5,padx=3)
        self.selection_text=tk.StringVar(self)
        ttk.Label(footer,textvariable=self.selection_text).grid(row=3,column=0,columnspan=4,sticky='w')
        self.search.trace_add('write', self._filter); self.tree.bind('<<TreeviewSelect>>', self._detail); self.tree.bind('<Double-1>', lambda e: self._select())
        self._filter(); entry.focus_set()

    def _filter(self, *_):
        from .batch_workflow import named_group, classification
        from .collection_workflow import cached_calculation, summaries, group_keys
        from .collection_reports import is_calculated
        previous=set(self.tree.selection())
        for item in self.tree.get_children():self.tree.delete(item)
        book=self.app._book;query=token(self.search.get());seen=set()
        self.floor_box.configure(values=['Todos os pisos']+sorted({c['floor'] for c in book.cases.values()}))
        self.kind_box.configure(values=['Todas as posições']+sorted({classification(c) for c in book.cases.values()}))
        self.group_box.configure(values=['Todos os grupos','Sem grupo']+sorted(book.batch_settings['groups']))
        for ckey,case in book.cases.items():
            group=named_group(book,case);kind=classification(case)
            if self.floor.get()!='Todos os pisos' and case['floor']!=self.floor.get():continue
            if self.kind.get()!='Todas as posições' and kind!=self.kind.get():continue
            if self.group.get()=='Sem grupo' and group:continue
            if self.group.get() not in {'Todos os grupos','Sem grupo'} and group!=self.group.get():continue
            if query not in token(' '.join((case['floor'],case['support'],case['combination'],group,kind))):continue
            joint=(case['floor'],case['support'])
            if joint in seen:continue
            seen.add(joint);keys=group_keys(book,case);entries=[]
            for k in keys:
                c=book.cases[k]
                entries.append(cached_calculation(c) or dict(floor=c['floor'],support=c['support'],combination=c['combination'],status='NOT_EVALUATED',snapshot=None,error='Por calcular.'))
            count=sum(is_calculated(e) for e in entries)
            state=summaries(entries)[0]['status'] if count else 'Completar / calcular'
            source='Modelo de análise' if case.get('automated') else ('Manual' if case['choice']=='manual' else MODES.get(case['choice'],'Por selecionar'))
            self.tree.insert('','end',iid=ckey,values=(case['floor'],case['support'],f'{len(keys)} combinações',group or '—',kind,f'{count}/{len(keys)} · {state}'))
        visible=set(self.tree.get_children())
        if previous&visible:self.tree.selection_set([k for k in self.tree.get_children() if k in previous])
        self.analysis_button.configure(state='normal' if book.analysis_tables else 'disabled')
        self.model_button.configure(state='normal' if book.analysis_tables else 'disabled')
        self.report_button.configure(state='normal' if book.cases else 'disabled')
        self.remove_button.configure(state='normal' if self.group.get() in book.batch_settings['groups'] else 'disabled')
        set_text(self.details,'Selecione um ou vários pilares. Ctrl e Shift permitem alargar a seleção. Filtre por piso, posição/direção do bordo ou grupo. Os cálculos e as alterações em lote abrangem todas as combinações de cada pilar selecionado.')
        self._detail()

    def _detail(self, *_):
        selected=self.tree.selection()
        self.open_button.configure(state='normal' if len(selected)==1 else 'disabled')
        for button in self.batch_buttons:button.configure(state='normal' if selected else 'disabled')
        self.selection_text.set(f'{len(selected)} pilares selecionados · {len(self.tree.get_children())} visíveis')
        if len(selected)==1:set_text(self.details,describe_case(self.app._book.cases[selected[0]]))
        elif selected:set_text(self.details,'Seleção:\n'+'\n'.join(f"{self.app._book.cases[k]['floor']} / {self.app._book.cases[k]['support']}" for k in selected))

    def _selected_keys(self):
        from .batch_workflow import joint_selection
        return joint_selection(self.app._book,self.tree.selection())

    def _all_visible(self):
        self.tree.selection_set(self.tree.get_children());self._detail()

    def _clear_selection(self):
        self.tree.selection_remove(self.tree.selection());self._detail()

    def _group_selection(self):
        from .batch_dialogs import GroupDialog
        from .batch_workflow import assign_group
        keys=self._selected_keys()
        if not keys:return
        dialog=GroupDialog(self,self.app._book,keys);self.wait_window(dialog);self.grab_set()
        if dialog.result is not None:
            assign_group(self.app._book,keys,dialog.result);self.group.set(dialog.result);self._filter()

    def _remove_group(self):
        from .batch_workflow import remove_group
        name=self.group.get()
        if name in self.app._book.batch_settings['groups']:
            remove_group(self.app._book,name);self.group.set('Todos os grupos');self._filter()

    def _edit_selection(self):
        from .batch_dialogs import BulkEditDialog
        from .batch_workflow import bulk_edit
        from Punching_EC2_GUI import DEFAULTS
        keys=self._selected_keys()
        if not keys:return
        dialog=BulkEditDialog(self,self.app._book,keys);self.wait_window(dialog);self.grab_set()
        if dialog.result is None:return
        try:
            count=bulk_edit(self.app._book,keys,defaults=DEFAULTS,**dialog.result)
            active=self.app._book.active
            if active in keys:self.app._load_draft(self.app._book.cases[active]['draft'])
            self._filter();set_text(self.details,f'{count} pilares alterados. Calcule a seleção para atualizar os resultados.')
        except Exception as exc:messagebox.showerror('Editar seleção',str(exc),parent=self)

    def _calculate_selection(self):
        keys=self._selected_keys()
        if not keys:return
        def done(completed):
            self.grab_set();self._filter()
            set_text(self.details,'Cálculo da seleção concluído.' if completed else 'Cálculo interrompido. Os resultados já obtidos foram conservados.')
        self.app._run_collection(keys,done)

    def _import(self):
        dialog = ImportDialog(self); self.wait_window(dialog); self.grab_set()
        if dialog.result is not None:
            try:
                self.app._merge_import(dialog.result); self._filter()
                if dialog.result['mode'] in ('analysis','analysis_nodes') and self.app._book.analysis_tables:self._model()
            except Exception as exc: messagebox.showerror('Importar', str(exc), parent=self)

    def _analysis(self):
        from .analysis_dialogs import ModeloBrowser
        dialog = ModeloBrowser(self, self.app); self.wait_window(dialog); self.grab_set(); self._filter()

    def _model(self):
        self.app._prepare_model(parent=self);self._filter()

    def _report(self):
        self.app._export_collection(parent=self)

    def _open(self):
        if self.app._open_connections(parent=self): self._filter()

    def _save(self): self.app._save_connections(parent=self)

    def _new(self):
        if self.app._new_connections(parent=self): self._filter()

    def _select(self):
        selected = self.tree.selection()
        if len(selected)!=1:return
        self.result = selected[0]; self.destroy()

    def _individual(self):
        self.result = '__individual__'; self.destroy()


class OriginDialog(tk.Toplevel):
    def __init__(self, app, case, draft):
        super().__init__(app); self.result = None; self.case = deepcopy(case); self.draft = deepcopy(draft)
        window(self, app, 'Origem dos esforços da ligação', 980, 760)
        title = ttk.Frame(self, padding=14); title.grid(row=0, column=0, sticky='ew'); title.columnconfigure(0, weight=1)
        FlowLabel(title, text=f"Piso {case['floor']} · Pilar {case['support']} · {case['combination'] or 'Combinação por definir'}", style='Section.TLabel').grid(row=0, column=0, sticky='ew')
        body, text = text_view(self); body.grid(row=1, column=0, sticky='nsew', padx=14); set_text(text, describe_case(case))
        footer = ttk.Frame(self, padding=14); footer.grid(row=2, column=0, sticky='ew'); footer.columnconfigure(1, weight=1)
        ttk.Label(footer, text='Fonte a adotar').grid(row=0, column=0, sticky='w', padx=(0, 12))
        self.choices = {'Introdução manual': 'manual'}
        for kind, candidate in case['candidates'].items():
            if candidate['adopted'] is not None: self.choices[MODES[kind]] = kind
        self.choice = tk.StringVar(self, next((label for label, k in self.choices.items() if k == case['choice']), ''))
        ttk.Combobox(footer, textvariable=self.choice, values=list(self.choices), state='readonly').grid(row=0, column=1, columnspan=2, sticky='ew')
        self.forces = {}
        forcebar = ttk.Frame(footer); forcebar.grid(row=1, column=0, columnspan=3, sticky='ew', pady=10)
        for i, (k, label) in enumerate((('V_Ed', 'VEd · kN'), ('M_Edx', 'MEdx · kN.m'), ('M_Edy', 'MEdy · kN.m'))):
            forcebar.columnconfigure(i*2+1, weight=1); ttk.Label(forcebar, text=label).grid(row=0, column=i*2, padx=(8, 5))
            var = tk.StringVar(self, str(draft[k])); self.forces[k] = (var, ttk.Entry(forcebar, textvariable=var, width=12))
            self.forces[k][1].grid(row=0, column=i*2+1, sticky='ew')
        ttk.Label(footer, text='Fundamentação / referência').grid(row=2, column=0, sticky='w', padx=(0, 12))
        self.reference = tk.StringVar(self, case['reference']); ttk.Entry(footer, textvariable=self.reference).grid(row=2, column=1, columnspan=2, sticky='ew')
        FlowLabel(footer, text='Em modo manual, descreva a origem e as alterações. As fontes importadas atualizam VEd/MEd e os sentidos das excentricidades; reveja-os no caso.', style='Muted.TLabel').grid(row=3, column=0, columnspan=3, sticky='ew', pady=8)
        ttk.Button(footer, text='Aplicar ao caso', style='Primary.TButton', command=self._apply).grid(row=4, column=1, sticky='e')
        ttk.Button(footer, text='Cancelar', command=self.destroy).grid(row=4, column=2, padx=(8, 0))
        self.choice.trace_add('write', self._update); self._update()

    def _update(self, *_):
        selected = self.choices.get(self.choice.get())
        values = self.case['candidates'][selected]['adopted'] if selected in self.case['candidates'] else None
        for k, (var, widget) in self.forces.items():
            widget.configure(state='normal' if selected == 'manual' else 'readonly')
            if values: var.set(f'{values[k]:.15g}')

    def _apply(self):
        try:
            draft = deepcopy(self.draft)
            for k, (var, _) in self.forces.items(): draft[k] = var.get()
            adopt(self.case, self.choices.get(self.choice.get(), ''), draft, self.reference.get())
            self.result = self.case; self.destroy()
        except Exception as exc: messagebox.showerror('Origem dos esforços', str(exc), parent=self)
