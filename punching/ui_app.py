"""Presentation of the desktop application; numeric inputs remain canonical."""
import json
import tkinter as tk
from tkinter import ttk, messagebox
from .ui import COLORS, CHOICES, apply_theme, application_icon, FlowLabel, LabelCombo, ScrollTab, Disclosure, field_states


class DesktopUI:
    def __init__(self, defaults, examples, version):
        super().__init__()
        self._ui_version = version; self._examples = examples
        self.title(f'PunchingShearEC2 {version}')
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f'{min(1460, sw-50)}x{min(940, sh-90)}')
        self.minsize(min(1060, sw-50), min(650, sh-90))
        self.last_verif = None; self.last_report = ''; self.dirty = True
        self._redraw_job = None; self._loading = True; self.drag_mode = None
        self.style = apply_theme(self)
        self._window_icon = application_icon(self); self.iconphoto(True, self._window_icon)
        self.vars = {k: (tk.BooleanVar(self, value=v) if isinstance(v, bool) else tk.StringVar(self, value=v)) for k, v in defaults.items()}
        for name, value in {
            'var_resultado': 'Introduza os dados e execute a verificação.',
            'var_status': 'Pronto para definir um caso.', 'var_exemplo': next(iter(examples)),
            'var_rho': '', 'var_longitudinal':'', 'var_steel': 'Calcule para obter a proposta de fiadas.',
            'var_context': 'Novo caso', 'var_method_hint': '', 'var_active_method': '', 'var_openings': '',
            'var_geometry_hint': 'Pré-visualização dos dados · cálculo por executar',
            'var_beta_value': '—', 'var_perimeter_value': '—', 'var_usage_value': '—',
            'var_origin': 'Caso individual · esforços introduzidos pelo utilizador',
        }.items():
            setattr(self, name, tk.StringVar(self, value=value))
        self.var_edit_column = tk.BooleanVar(self, value=False)
        self.input_widgets = {}; self.field_rows = {}; self.method_panels = {}; self.export_buttons = []
        self.columnconfigure(0, weight=1); self.rowconfigure(2, weight=1)
        self._build_header()
        context = ttk.Frame(self, style='App.TFrame', padding=(20, 10, 20, 8))
        context.grid(row=1, column=0, sticky='ew'); context.columnconfigure(0, weight=1)
        FlowLabel(context, textvariable=self.var_context, style='Footer.TLabel').grid(row=0, column=0, sticky='ew')
        ttk.Button(context, text='Pilares…', command=self._show_connections).grid(row=0, column=1, padx=(12, 0))
        ttk.Label(context, text='NP EN 1992-1-1 · Anexo Nacional PT', style='Footer.TLabel').grid(row=0, column=2, padx=(12, 0))
        self.main_pane = ttk.Panedwindow(self, orient='horizontal')
        self.main_pane.grid(row=2, column=0, sticky='nsew', padx=16)
        left = ttk.Frame(self.main_pane, width=450, padding=(6, 10, 6, 6))
        right = ttk.Frame(self.main_pane, padding=(12, 10, 12, 10))
        self.main_pane.add(left, weight=0); self.main_pane.add(right, weight=1)
        left.columnconfigure(0, weight=1); left.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1); right.rowconfigure(2, weight=1)
        ttk.Label(left, text='DEFINIÇÃO DO CASO', style='Section.TLabel', padding=(12, 6, 0, 14)).grid(row=0, column=0, sticky='w')
        self.input_notebook = ttk.Notebook(left); self.input_notebook.grid(row=1, column=0, sticky='nsew')
        self.scroll_tabs = []
        for title, builder in [('Dados', self._data_tab), ('Método β', self._options_tab), ('Armadura', self._detail_tab)]:
            tab = ScrollTab(self.input_notebook); self.scroll_tabs.append(tab)
            self.input_notebook.add(tab, text=title); builder(tab.body)
        self._build_results(right)
        footer = ttk.Frame(self, style='App.TFrame', padding=(20, 6, 16, 7))
        footer.grid(row=3, column=0, sticky='ew'); footer.columnconfigure(0, weight=1)
        FlowLabel(footer, textvariable=self.var_status, style='Footer.TLabel').grid(row=0, column=0, sticky='ew')
        ttk.Button(footer, text='Ajuda · F1', style='Link.TButton', command=self._show_help).grid(row=0, column=1, padx=(10, 0))
        for var in self.vars.values(): var.trace_add('write', self._mark_dirty)
        for sequence, action in [('<Control-o>', self.abrir_caso), ('<Control-s>', self.guardar_caso),
                                  ('<Control-n>', self.limpar), ('<F5>', self.calcular), ('<F1>', self._show_help)]:
            self.bind(sequence, lambda event, fn=action: self._shortcut(fn))
        self.bind_all('<MouseWheel>', self._mousewheel)
        self.bind_all('<Button-4>', self._mousewheel); self.bind_all('<Button-5>', self._mousewheel)
        self._loading = False; self._update_derived(); self._sync_controls(); self._result_tools(False)
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self.after_idle(self._initial_layout)

    def _initial_layout(self):
        self.main_pane.sashpos(0, max(390, min(470, int(self.winfo_width() * .36))))
        self._draw_scheme()

    def _shortcut(self, action):
        # Do not operate on the main case while a modal editor has the grab.
        if self.grab_current() in (None, self): action()
        return 'break'

    def _build_header(self):
        header = ttk.Frame(self, style='Header.TFrame', padding=(20, 16))
        header.grid(row=0, column=0, sticky='ew'); header.columnconfigure(1, weight=1)
        mark = tk.Canvas(header, width=43, height=43, bg=COLORS['navy'], highlightthickness=0)
        mark.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        mark.create_oval(2, 2, 41, 41, outline='#68acf4', width=2)
        mark.create_rectangle(15, 13, 28, 30, fill='#d9eafb', outline='')
        mark.create_line(2, 35, 41, 35, fill='#68acf4', width=2)
        ttk.Label(header, text='PunchingShearEC2', style='Header.TLabel').grid(row=0, column=1, sticky='w')
        ttk.Label(header, text=f'Verificação ao punçoamento  /  {self._ui_version}', style='HeaderSub.TLabel').grid(row=1, column=1, sticky='w', pady=(3, 0))
        actions = ttk.Frame(header, style='Header.TFrame'); actions.grid(row=0, column=2, rowspan=2, padx=(18, 0))
        for i, (label, fn) in enumerate([('Novo', self.limpar), ('Abrir', self.abrir_caso), ('Guardar', self.guardar_caso), ('Exemplos…', self._show_examples)]):
            ttk.Button(actions, text=label, width=8, style='Header.TButton', command=fn).grid(row=0, column=i, padx=3)
        ttk.Button(actions, text='Calcular  F5', style='Primary.TButton', command=self.calcular).grid(row=0, column=4, padx=(14, 0))

    def _build_results(self, right):
        status = ttk.Frame(right, padding=(4, 2, 4, 8)); status.grid(row=0, column=0, sticky='ew'); status.columnconfigure(0, weight=1)
        self.lbl_badge = ttk.Label(status, text='NÃO CALCULADO', foreground=COLORS['muted'], font=('Segoe UI', 12, 'bold'))
        self.lbl_badge.grid(row=0, column=0, sticky='w')
        ttk.Label(status, textvariable=self.var_active_method, style='Muted.TLabel').grid(row=0, column=1, sticky='e', padx=(10, 0))
        FlowLabel(status, textvariable=self.var_resultado).grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        metrics = ttk.Frame(right, padding=(0, 6, 0, 14)); metrics.grid(row=1, column=0, sticky='ew')
        for i, (label, variable) in enumerate([('β adotado', self.var_beta_value), ('u1 efetivo · m', self.var_perimeter_value), ('Utilização resistente máx.', self.var_usage_value)]):
            metrics.columnconfigure(i, weight=1, uniform='metric')
            card = ttk.Frame(metrics, padding=(14, 8), style='Soft.TFrame'); card.grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else 6, 0))
            card.columnconfigure(0, weight=1)
            FlowLabel(card, text=label, style='Soft.TLabel', font=('Segoe UI', 9)).grid(row=0, column=0, sticky='ew')
            ttk.Label(card, textvariable=variable, style='Metric.TLabel', background=COLORS['soft']).grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.result_notebook = ttk.Notebook(right); self.result_notebook.grid(row=2, column=0, sticky='nsew')
        self._geometry_tab(self.result_notebook)
        summary = ttk.Frame(self.result_notebook, padding=(6, 10)); self.result_notebook.add(summary, text='Verificações')
        summary.columnconfigure(0, weight=1); summary.rowconfigure(0, weight=3); summary.rowconfigure(3, weight=1)
        self.tree_summary = ttk.Treeview(summary, columns=('name', 'value'), show='headings', height=9)
        for key, label, width in [('name', 'Grandeza / verificação', 270), ('value', 'Resultado', 230)]:
            self.tree_summary.heading(key, text=label); self.tree_summary.column(key, width=width, minwidth=width, stretch=True)
        self._tree_scrollbars(summary, self.tree_summary, 0, horizontal=True)
        ttk.Label(summary, text='Notas da verificação', style='Section.TLabel').grid(row=2, column=0, sticky='w', pady=(14, 6))
        diag = ttk.Frame(summary); diag.grid(row=3, column=0, columnspan=2, sticky='nsew'); diag.rowconfigure(0, weight=1); diag.columnconfigure(0, weight=1)
        self.txt_diag = tk.Text(diag, height=4, wrap='word', font=('Segoe UI', 10), state='disabled',
                                bg=COLORS['surface'], fg=COLORS['muted'], borderwidth=0, padx=6, pady=5)
        self.txt_diag.grid(row=0, column=0, sticky='nsew')
        bar = ttk.Scrollbar(diag, orient='vertical', command=self.txt_diag.yview); bar.grid(row=0, column=1, sticky='ns'); self.txt_diag.configure(yscrollcommand=bar.set)
        steel = ttk.Frame(self.result_notebook, padding=(6, 10)); self.result_notebook.add(steel, text='Fiadas')
        steel.columnconfigure(0, weight=1); steel.rowconfigure(1, weight=1)
        FlowLabel(steel, textvariable=self.var_steel).grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        self.tree_steel = ttk.Treeview(steel, columns=('row', 'r', 'n', 'area', 'st', 'state'), show='headings', height=10)
        for key, label, width in [('row', 'Fiada', 48), ('r', 'r (m)', 75), ('n', 'Ramos', 65), ('area', 'Asw (cm²)', 92), ('st', 'st (m)', 75), ('state', 'Local', 66)]:
            self.tree_steel.heading(key, text=label); self.tree_steel.column(key, width=width, minwidth=width, anchor='center')
        self._tree_scrollbars(steel, self.tree_steel, 1, horizontal=True)
        FlowLabel(steel, text='Ramos e Asw: totais físicos de cada fiada. «OK» refere-se à fiada; a conclusão global permanece no topo. Contribuições por contorno na Memória e no XLSX.', style='Muted.TLabel').grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        mem = ttk.Frame(self.result_notebook, padding=(6, 10)); self.result_notebook.add(mem, text='Memória')
        mem.columnconfigure(0, weight=1); mem.rowconfigure(0, weight=1)
        self.txt_output = tk.Text(mem, wrap='word', font=('Courier New', 10), state='disabled',
                                  borderwidth=0, padx=10, pady=10, bg=COLORS['surface'], fg=COLORS['ink'])
        self.txt_output.grid(row=0, column=0, sticky='nsew')
        bar = ttk.Scrollbar(mem, orient='vertical', command=self.txt_output.yview); bar.grid(row=0, column=1, sticky='ns'); self.txt_output.configure(yscrollcommand=bar.set)
        exports = ttk.Frame(right, padding=(0, 12, 0, 0)); exports.grid(row=3, column=0, sticky='ew'); exports.columnconfigure(0, weight=1)
        ttk.Label(exports, text='Relatórios', style='Muted.TLabel').grid(row=0, column=0, sticky='w')
        for i, (label, kind) in enumerate([('PDF', 'pdf'), ('XLSX', 'xlsx'), ('TXT', 'txt'), ('JSON', 'json')], 1):
            btn = ttk.Button(exports, text=label, width=5, command=lambda k=kind: self._export(k))
            btn.grid(row=0, column=i, padx=(6, 0)); self.export_buttons.append(btn)
        btn = ttk.Button(exports, text='Copiar', width=7, command=self.copiar_relatorio)
        btn.grid(row=0, column=5, padx=(6, 0)); self.export_buttons.append(btn)
        for tree in (self.tree_summary, self.tree_steel):
            tree.tag_configure('alternate', background='#f5f8fc')
            tree.tag_configure('fail', foreground=COLORS['red'])
            tree.tag_configure('pass', foreground=COLORS['green'])

    @staticmethod
    def _tree_scrollbars(parent, tree, row, horizontal=False):
        tree.grid(row=row, column=0, sticky='nsew')
        bar = ttk.Scrollbar(parent, orient='vertical', command=tree.yview); bar.grid(row=row, column=1, sticky='ns'); tree.configure(yscrollcommand=bar.set)
        if horizontal:
            bar = ttk.Scrollbar(parent, orient='horizontal', command=tree.xview); bar.grid(row=row+1, column=0, sticky='ew'); tree.configure(xscrollcommand=bar.set)

    def _geometry_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=(6, 10)); notebook.add(tab, text='Planta')
        tab.columnconfigure(0, weight=1); tab.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(tab); toolbar.grid(row=0, column=0, sticky='ew', pady=(0, 8)); toolbar.columnconfigure(0, weight=1)
        FlowLabel(toolbar, textvariable=self.var_geometry_hint, style='Muted.TLabel').grid(row=0, column=0, sticky='ew')
        ttk.Checkbutton(toolbar, text='Editar pilar', variable=self.var_edit_column, command=self._toggle_column_edit).grid(row=0, column=1, padx=10)
        self.opening_button = ttk.Button(toolbar, text='Aberturas…', command=self._edit_openings); self.opening_button.grid(row=0, column=2)
        self.canvas_scheme = tk.Canvas(tab, bg='#fbfcfe', highlightthickness=1, highlightbackground=COLORS['line'], width=540, height=350)
        self.canvas_scheme.grid(row=1, column=0, sticky='nsew')
        self.canvas_scheme.bind('<Configure>', lambda e: self._draw_scheme())
        self.canvas_scheme.bind('<Button-1>', self._on_canvas_press); self.canvas_scheme.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas_scheme.bind('<ButtonRelease-1>', self._on_canvas_release)
        FlowLabel(tab, text='Planta em metros · X paralelo a c1; Y paralelo a c2. Ative «Editar pilar» para arrastar as pegas azuis.', style='Muted.TLabel').grid(row=2, column=0, sticky='ew', pady=(8, 0))

    def _group(self, parent, title, row):
        group = ttk.LabelFrame(parent, text=title, padding=(12, 10))
        group.grid(row=row, column=0, sticky='ew', pady=(0, 16)); group.columnconfigure(0, weight=1)
        return group

    def _entry(self, parent, key, label, row, values=None, unit=None, stacked=False):
        field = ttk.Frame(parent); field.grid(row=row, column=0, sticky='ew', pady=4)
        field.columnconfigure(1, weight=1)
        if stacked:
            field.columnconfigure(0, weight=1)
            FlowLabel(field, text=label, style='Muted.TLabel').grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 5))
        else:
            FlowLabel(field, text=label, width=21).grid(row=0, column=0, sticky='w', padx=(0, 10))
        if key in CHOICES: widget = LabelCombo(field, self.vars[key], CHOICES[key], width=15)
        elif values: widget = ttk.Combobox(field, textvariable=self.vars[key], values=values, state='readonly', width=12)
        else: widget = ttk.Entry(field, textvariable=self.vars[key], width=13, justify='left' if stacked else 'right')
        if key in CHOICES or values:
            for event in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                widget.bind(event, self._mousewheel)
        widget.grid(row=1 if stacked else 0, column=0 if stacked else 1, columnspan=2 if stacked else 1, sticky='ew')
        if unit: ttk.Label(field, text=unit, style='Muted.TLabel', width=5).grid(row=0, column=2, padx=(7, 0))
        self.input_widgets[key] = widget; self.field_rows[key] = field
        return widget

    def _checkbutton(self, parent, key, text, row):
        # A wrapping label next to the indicator avoids clipped long declarations.
        field = ttk.Frame(parent); field.grid(row=row, column=0, sticky='ew', pady=5); field.columnconfigure(1, weight=1)
        check = ttk.Checkbutton(field, variable=self.vars[key]); check.grid(row=0, column=0, sticky='n', padx=(0, 5))
        label = FlowLabel(field, text=text); label.grid(row=0, column=1, sticky='ew')
        label.bind('<Button-1>', lambda e: check.invoke())
        self.input_widgets[key] = check; self.field_rows[key] = field

    def _note(self, parent, text, row):
        FlowLabel(parent, text=text, style='Muted.TLabel').grid(row=row, column=0, sticky='ew', pady=6)

    def _help_note(self, parent, title, text, row):
        Disclosure(parent, title, text).grid(row=row, column=0, sticky='ew', pady=(2, 0))

    def _data_tab(self, parent):
        g = self._group(parent, 'Identificação', 0)
        for i, (key, label) in enumerate([('project', 'Projeto'), ('support', 'Apoio / laje'), ('combination', 'Combinação ELU')]):
            self._entry(g, key, label, i, stacked=True)
        g = self._group(parent, 'Pilar e bordo da laje', 1)
        self._entry(g, 'pilar_tipo', 'Posição do pilar', 0); self._entry(g, 'pilar_forma', 'Secção', 1)
        self._entry(g, 'pilar_c1', 'Dimensão c1 / D', 2, unit='m'); self._entry(g, 'pilar_c2', 'Dimensão c2', 3, unit='m')
        self._entry(g, 'edge_distance_m', 'Face ao bordo · g', 4, unit='m')
        self._checkbutton(g, 'edge_perp_interior', 'Excentricidade perpendicular dirigida para o interior da laje', 5)
        self._checkbutton(g, 'corner_interior', 'Ambas as excentricidades dirigidas para o interior da laje', 6)
        self._help_note(g, 'Convenções geométricas', 'Bordo: c1 paralelo e c2 perpendicular ao bordo. g mede-se à face do pilar: 0 = encostado. Canto: apenas encostado. Pilares circulares: apenas interiores. Razão entre dimensões < 4. No canto exterior, os sinais dos momentos definem os sentidos em +X/+Y da planta.', 7)
        g = self._group(parent, 'Laje e armadura longitudinal', 2)
        self._entry(g, 'long_mode', 'Introdução da armadura', 0, stacked=True)
        f=ttk.Frame(g);f.grid(row=1,column=0,sticky='ew');f.columnconfigure(0,weight=1);self.longitudinal_panel=f
        for i,(key,label,unit) in enumerate([
            ('long_h_mm','Espessura da laje · h','mm'),('long_cover_mm','Recobrimento longitudinal','mm'),
            ('long_outer_axis','Camada exterior',None),('long_layer_gap_mm','Afastamento X/Y','mm'),
            ('long_x_base_mm','X · diâmetro base','mm'),('long_x_extra_mm','X · diâmetro reforço','mm'),('long_x_spacing_mm','X · passo comum','mm'),
            ('long_y_base_mm','Y · diâmetro base','mm'),('long_y_extra_mm','Y · diâmetro reforço','mm'),('long_y_spacing_mm','Y · passo comum','mm')]):
            self._entry(f,key,label,i,unit=unit,stacked=key=='long_outer_axis')
        self._help_note(f,'Disposição das camadas','Base e reforço são intercalados, com eixos à mesma cota em cada direção. X e Y formam duas camadas; o maior diâmetro define a envolvente de cada camada. O recobrimento é a distância da face tracionada à superfície dos varões longitudinais: inclua a espessura de armaduras exteriores, se existirem. Afastamento X/Y = 0 para camadas ortogonais em contacto. Com reforço, use passo comum 200, 250 ou 300 mm para obter intercalação prática de 100, 125 ou 150 mm.',10)
        FlowLabel(g,textvariable=self.var_longitudinal,style='Muted.TLabel').grid(row=2,column=0,sticky='ew',pady=6)
        for i, (key, label, unit) in enumerate([
            ('laje_d', 'Altura útil média · d', 'm'), ('laje_dx', 'Altura útil · dx', 'm'), ('laje_dy', 'Altura útil · dy', 'm'),
            ('laje_As_lx_cm2pm', 'Armadura As,x', 'cm²/m'), ('laje_As_ly_cm2pm', 'Armadura As,y', 'cm²/m'),
            ('sigma_cp', 'Compressão no plano', 'MPa')],3): self._entry(g, key, label, i, unit=unit)
        FlowLabel(g, textvariable=self.var_rho, style='Soft.TLabel', padding=8).grid(row=9, column=0, sticky='ew', pady=6)
        self._help_note(g, 'Altura útil e faixa de armadura', 'Manual: dx/dy são opcionais; com ambos preenchidos, d é a média. Automático: a combinação deve representar a armadura aderente de tração média na faixa do apoio acrescida de 3d para cada lado, limitada pelos bordos livres. Se o reforço ocupar apenas parte dessa faixa ou estiver noutra camada, introduza manualmente as áreas médias e alturas úteis equivalentes.', 10)
        g = self._group(parent, 'Esforços ELU concomitantes', 3)
        for i, (key, label, unit) in enumerate([('V_Ed', 'Esforço transverso · VEd', 'kN'), ('M_Edx', 'Momento · MEdx', 'kN·m'), ('M_Edy', 'Momento · MEdy', 'kN·m')]):
            self._entry(g, key, label, i, unit=unit)
        self._help_note(g, 'Eixos, sinais e combinação', 'ex = MEdy/VEd; ey = MEdx/VEd. Introduza os momentos de transferência referidos ao centro do pilar, da mesma combinação que VEd. Utilize zero apenas quando o momento é nulo. O campo Combinação identifica o caso; não calcula envolventes.', 3)
        FlowLabel(g, textvariable=self.var_origin, style='Muted.TLabel').grid(row=4, column=0, sticky='ew', pady=(10, 6))
        self.origin_button = ttk.Button(g, text='Origem dos esforços…', command=self._edit_force_origin, state='disabled')
        self.origin_button.grid(row=5, column=0, sticky='ew')
        actions=ttk.Frame(g);actions.grid(row=6,column=0,sticky='ew',pady=(8,0));actions.columnconfigure(0,weight=1);actions.columnconfigure(1,weight=1)
        self.frame_button=ttk.Button(actions,text='Orientar ligação…',command=self._orient_connection,state='disabled');self.frame_button.grid(row=0,column=0,sticky='ew',padx=(0,5))
        self.group_button=ttk.Button(actions,text='Combinações…',command=self._show_group_results,state='disabled');self.group_button.grid(row=0,column=1,sticky='ew')
        g = self._group(parent, 'Materiais e coeficientes parciais', 4)
        for i, (key, label, unit) in enumerate([('betão_fck', 'Betão · fck', 'MPa'), ('aço_fyk', 'Aço longitudinal · fyk', 'MPa'), ('aço_fywk', 'Estribos · fywk', 'MPa'), ('gamma_C', 'Coeficiente γC', '—'), ('gamma_S', 'Coeficiente γS', '—')]):
            self._entry(g, key, label, i, unit=unit)
        g = self._group(parent, 'Fundação', 5)
        self._checkbutton(g, 'is_sapata', 'Verificar uma sapata centrada', 0)
        f = ttk.Frame(g); f.grid(row=1, column=0, sticky='ew'); f.columnconfigure(0, weight=1); self.footing_panel = f
        self._entry(f, 'footing_shape', 'Forma da sapata', 0)
        for i, (key, label, unit) in enumerate([('footing_bx', 'Dimensão Bx', 'm'), ('footing_by', 'Dimensão By', 'm'), ('footing_diameter', 'Diâmetro', 'm'), ('sigma_gd_kpa', 'Pressão líquida', 'kPa')], 1): self._entry(f, key, label, i, unit=unit)
        self._note(f, 'Pressão 0: cálculo uniforme por VEd/área. Apoio interior centrado, carga concêntrica, sem aberturas e método EC2. A verificação não inclui capacidade geotécnica.', 5)

    def _options_tab(self, parent):
        g = self._group(parent, 'Coeficiente de excentricidade β', 0)
        self._entry(g, 'beta_mode', 'Método de determinação', 0, stacked=True)
        FlowLabel(g, textvariable=self.var_method_hint, style='Soft.TLabel', padding=10).grid(row=1, column=0, sticky='ew', pady=(8, 0))
        for mode in ('ec2', 'simplificado', 'manual'):
            p = ttk.Frame(parent); p.grid(row=1, column=0, sticky='ew'); p.columnconfigure(0, weight=1); self.method_panels[mode] = p
        g = self._group(self.method_panels['ec2'], 'Cálculo pelas expressões do EC2', 0)
        self._entry(g, 'interior_beta_method', 'Pilar interior retangular', 0, stacked=True)
        self._note(g, 'A geometria e a orientação das excentricidades determinam o âmbito. O afastamento ao bordo e os setores de aberturas ativos requerem fundamentação específica.', 1)
        self._checkbutton(g, 'allow_biaxial_envelope', 'Adotar a soma conservadora das majorações biaxiais de (6.39)', 2)
        self._help_note(g, 'Expressões e hipótese de combinação', '(6.43): aproximação para o interior retangular, incluindo os limites uniaxiais. (6.39): expressão geral uniaxial. A soma das majorações por direção é uma hipótese adicional, identificada na memória. Não elimina as limitações para g > 0 ou aberturas. O método escolhido mantém-se quando um momento tende para zero.', 3)
        g = self._group(self.method_panels['simplificado'], 'Condições de aplicabilidade', 0)
        self._note(g, 'EC2 6.4.3(6): estabilidade independente dos pórticos laje-pilar e diferença entre vãos adjacentes até 25%.', 0)
        self._checkbutton(g, 'simplified_applicable', 'Confirmo que ambas as condições se verificam neste projeto', 1)
        self._note(g, 'Valores: interior 1,15 · bordo 1,40 · canto 1,50. A declaração fica registada no caso. Este método não está disponível com setores ineficazes.', 2)
        g = self._group(self.method_panels['manual'], 'Valor definido pelo projetista', 0)
        self._entry(g, 'beta_manual', 'Coeficiente β ≥ 1', 0)
        self._entry(g, 'beta_reference', 'Referência da análise de β · obrigatória', 1, stacked=True)
        self._note(g, 'Identifique a análise ou memória de cálculo que fundamenta o fator para esta geometria, esforços e contornos u0, u1 e exteriores.', 2)
        self._help_note(g, 'Como é utilizada a referência', 'O programa verifica o valor e a existência da referência; não valida o seu conteúdo técnico. A referência é incluída na memória e nas exportações. Reveja-a quando alterar o caso.', 3)
        g = self._group(parent, 'Aberturas e setores ineficazes', 2)
        self.options_opening_button = ttk.Button(g, text='Definir aberturas na planta…', style='Primary.TButton', command=self._edit_openings)
        self.options_opening_button.grid(row=0, column=0, sticky='ew')
        FlowLabel(g, textvariable=self.var_openings, style='Muted.TLabel').grid(row=1, column=0, sticky='ew', pady=8)
        self._entry(g, 'opening_sectors', 'Setores manuais adicionais · graus', 2, stacked=True)
        self._help_note(g, 'Entrada avançada de setores', 'Formato: -20;20 | 100;125. Ângulos de +X para +Y. Estes setores unem-se aos calculados pelas aberturas físicas. No editor gráfico não é necessário introduzir ou copiar os ângulos.', 3)

    def _detail_tab(self, parent):
        g = self._group(parent, 'Estribos verticais', 0)
        self._entry(g, 'reinforcement_diameter_mm', 'Diâmetro dos ramos', 0, values=['10', '12', '16'], unit='mm')
        for i, (key, label, unit) in enumerate([('reinforcement_s0_m', 'Primeira fiada · s0', 'm'), ('reinforcement_sr_m', 'Passo radial · sr', 'm'), ('cover_mm', 'Recobrimento nominal', 'mm'), ('aggregate_mm', 'Agregado · dimensão máx.', 'mm')], 1): self._entry(g, key, label, i, unit=unit)
        self._note(g, 'Deixe s0 e sr vazios para escolha automática.', 5)
        self._help_note(g, 'Distribuição e espaçamentos', 's0 automático = 0,5d. sr automático ≤ 0,75d, arredondado por defeito a 5 mm. O programa calcula os ramos e verifica distribuição tangencial e distância livre mínima. Com afastamento ao bordo, inclui fiadas abertas e os fechos necessários. Consulte a Planta, Fiadas e Memória.', 6)
        g = self._group(parent, 'Pormenor construtivo', 1)
        self._checkbutton(g, 'anchorage_confirmed', 'Confirmo a amarração no pormenor construtivo do projeto', 0)
        self._note(g, 'A confirmação abrange a ancoragem nas armaduras longitudinais, dobras, espessura e recobrimento. A pormenorização permanece pendente enquanto não for confirmada.', 1)
        self._help_note(g, 'Âmbito da proposta', 'O desenho representa ramos verticais de estribos convencionais. Sistemas comerciais exigem a avaliação técnica aplicável. Sapatas requerem pormenorização específica. A confirmação da amarração só conclui uma proposta que cumpra as verificações.', 2)

    def _sync_controls(self):
        if 'input_widgets' not in self.__dict__: return
        values = {key: variable.get() for key, variable in self.vars.items()}
        states = field_states(values)
        for key, enabled in states.items():
            widget = self.input_widgets[key]
            state = ('readonly' if key in CHOICES else 'normal') if enabled else ('readonly' if key in ('laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm') else 'disabled')
            widget.configure(state=state)
        for key in ('interior_beta_method', 'allow_biaxial_envelope', 'edge_perp_interior', 'corner_interior', 'pilar_c2', 'footing_bx', 'footing_by', 'footing_diameter'):
            if states[key]: self.field_rows[key].grid()
            else: self.field_rows[key].grid_remove()
        if values.get('long_mode')=='automatic':self.longitudinal_panel.grid()
        else:self.longitudinal_panel.grid_remove()
        for mode, panel in self.method_panels.items():
            if values['beta_mode'] == mode: panel.grid()
            else: panel.grid_remove()
        if values['is_sapata']: self.footing_panel.grid()
        else: self.footing_panel.grid_remove()
        for button in (self.opening_button, self.options_opening_button):
            button.configure(state='disabled' if values['is_sapata'] else 'normal')
        context = '  /  '.join(str(values[k]).strip() for k in ('project', 'support', 'combination') if str(values[k]).strip()) or 'Novo caso · identificação por preencher'
        self.var_context.set(context if len(context) <= 115 else context[:112] + '…')
        mode = values['beta_mode']
        if 'var_active_method' in self.__dict__:
            self.var_active_method.set({'ec2': 'Método: EC2', 'simplificado': 'Método: simplificado', 'manual': 'Método: manual'}.get(mode, 'Método: ' + mode))
        if values['is_sapata']:
            hint = 'Sapata concêntrica: selecione o método EC2. O cálculo adota β = 1 dentro do âmbito admitido.'
        elif mode == 'manual':
            beta = str(values['beta_manual']).strip(); ref = str(values['beta_reference']).strip()
            hint = 'Manual ativo. ' + (f'β introduzido: {beta}. ' if beta else 'Introduza o valor de β. ')
            hint += 'Referência registada; reveja-a para os dados atuais.' if ref else 'Falta indicar a referência da análise.'
        elif mode == 'simplificado':
            hint = 'Valores simplificados selecionados. ' + ('Condições declaradas pelo projetista.' if values['simplified_applicable'] else 'Confirme as condições abaixo antes de calcular.')
        else: hint = 'Cálculo EC2 selecionado. O valor manual não é utilizado neste modo. Consulte na Memória a expressão efetivamente aplicada.'
        self.var_method_hint.set(hint)
        try:
            count = len(json.loads(values['openings'] or '[]'))
            message = f'{count} abertura(s) definida(s). Posição e dimensões editáveis na planta.' if count else 'Sem aberturas físicas. Adicione um retângulo ou um círculo no editor.'
            if values['is_sapata']:
                message = 'O módulo de sapatas admite apenas casos sem aberturas.'
                if count: message += ' Desative «Verificar uma sapata centrada» para editar ou remover as aberturas existentes.'
            self.var_openings.set(message)
        except (ValueError, TypeError): self.var_openings.set('Definição de aberturas inválida; reveja os dados do caso.')

    def _result_tools(self, available):
        for button in self.__dict__.get('export_buttons', []): button.configure(state='normal' if available else 'disabled')
        if 'var_geometry_hint' in self.__dict__:
            self.var_geometry_hint.set('Geometria da verificação atual' if available else 'Pré-visualização dos dados · requer cálculo')
        if not available:
            for key in ('var_beta_value', 'var_perimeter_value', 'var_usage_value'):
                if key in self.__dict__: getattr(self, key).set('—')

    def _result_cards(self, result):
        if 'var_beta_value' not in self.__dict__: return
        v = result['values']
        self.var_beta_value.set('—' if v['beta'] is None else f"{v['beta']:.3f}")
        self.var_perimeter_value.set('—' if v['u1_eff'] is None else f"{v['u1_eff']:.3f}")
        ratios = [c['utilization'] for c in result['checks'] if c.get('utilization') is not None]
        self.var_usage_value.set(f'{max(ratios)*100:.1f} %' if ratios else '—')

    def _toggle_column_edit(self):
        self.drag_mode = None; self._drag_transform = None; self._draw_scheme()

    def _on_canvas_release(self, event=None):
        self.drag_mode = None; self._drag_transform = None; self._draw_scheme()

    def _show_examples(self):
        from .ui_dialogs import ExampleDialog
        dialog = ExampleDialog(self, self._examples)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.var_exemplo.set(dialog.result); self.carregar_exemplo()

    def _show_help(self):
        from .ui_dialogs import HelpDialog
        HelpDialog(self, self._ui_version)
