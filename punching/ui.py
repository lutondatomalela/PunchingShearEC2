"""Desktop presentation helpers. No resistance or perimeter calculations."""
import tkinter as tk
from tkinter import ttk

COLORS = {
    'background': '#edf1f6', 'surface': '#ffffff', 'ink': '#172b43',
    'muted': '#5b6c80', 'line': '#d8e1eb', 'navy': '#14283f',
    'accent': '#1769c2', 'accent_hover': '#10569f', 'soft': '#eff6ff',
    'green': '#16734a', 'amber': '#956315', 'red': '#b12732',
}

from .longitudinal import CHOICES as LONG_CHOICES

CHOICES = {
    'beta_mode': {'ec2': 'EC2 · cálculo pelas expressões',
                  'simplificado': 'EC2 · valores simplificados',
                  'manual': 'Manual · valor e referência'},
    'interior_beta_method': {'ec2_643': 'Aproximação (6.43)',
                             'ec2_639': 'Expressão geral (6.39)'},
    'pilar_tipo': {'interior': 'Interior', 'bordo': 'Bordo', 'canto': 'Canto'},
    'pilar_forma': {'retangular': 'Retangular', 'circular': 'Circular'},
    'footing_shape': {'retangular': 'Retangular', 'circular': 'Circular'},
}

CHOICES.update(LONG_CHOICES)

def application_icon(master):
    """A small native Tk icon, generated without an image dependency."""
    icon = tk.PhotoImage(master=master, width=48, height=48)
    rows = []
    for y in range(48):
        row = []
        for x in range(48):
            radius = ((x-23.5)**2 + (y-23.5)**2)**.5
            color = COLORS['navy']
            if 18 <= radius <= 20 or (7 <= x <= 41 and 36 <= y <= 38): color = '#68acf4'
            if 18 <= x <= 29 and 15 <= y <= 32: color = '#e5f0ff'
            row.append(color)
        rows.append('{' + ' '.join(row) + '}')
    icon.put(' '.join(rows))
    return icon


def apply_theme(root):
    """A single palette, also inherited by the opening editor and dialogs."""
    c = COLORS
    root.configure(background=c['background'])
    root.option_add('*Font', '{Segoe UI} 10')
    root.option_add('*TCombobox*Listbox.font', '{Segoe UI} 10')
    root.option_add('*TCombobox*Listbox.background', c['surface'])
    root.option_add('*TCombobox*Listbox.selectBackground', c['accent'])
    root.option_add('*TCombobox*Listbox.selectForeground', 'white')
    style = ttk.Style(root)
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=c['surface'], foreground=c['ink'])
    style.configure('TFrame', background=c['surface'])
    style.configure('App.TFrame', background=c['background'])
    style.configure('Header.TFrame', background=c['navy'])
    style.configure('Soft.TFrame', background=c['soft'])
    style.configure('TLabel', background=c['surface'], foreground=c['ink'])
    style.configure('Muted.TLabel', foreground=c['muted'], font=('Segoe UI', 9))
    style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'))
    style.configure('Metric.TLabel', font=('Segoe UI', 18, 'bold'))
    style.configure('Header.TLabel', background=c['navy'], foreground='white', font=('Segoe UI', 17, 'bold'))
    style.configure('HeaderSub.TLabel', background=c['navy'], foreground='#b8cce3', font=('Segoe UI', 9))
    style.configure('Soft.TLabel', background=c['soft'], foreground=c['accent'])
    style.configure('Footer.TLabel', background=c['background'], foreground=c['muted'], font=('Segoe UI', 9))
    style.configure('TLabelframe', background=c['surface'], bordercolor=c['line'], relief='solid', borderwidth=1)
    style.configure('TLabelframe.Label', background=c['surface'], foreground=c['ink'], font=('Segoe UI', 10, 'bold'))
    style.configure('TButton', padding=(12, 8), background=c['surface'], foreground=c['ink'],
                    bordercolor=c['line'], lightcolor=c['surface'], darkcolor=c['surface'],
                    relief='flat', borderwidth=1)
    style.map('TButton', background=[('disabled', '#f3f5f8'), ('pressed', '#dfeafa'), ('active', '#edf4fd')],
              foreground=[('disabled', '#8a96a6')], bordercolor=[('focus', c['accent'])])
    style.configure('Primary.TButton', background=c['accent'], foreground='white',
                    bordercolor=c['accent'], font=('Segoe UI', 10, 'bold'))
    style.map('Primary.TButton', background=[('disabled', '#c3d4e7'), ('pressed', '#0e4d91'), ('active', c['accent_hover'])],
              foreground=[('disabled', '#eef3fa'), ('!disabled', 'white')])
    style.configure('Header.TButton', background='#203a55', foreground='#eff5fd', bordercolor='#34516d')
    style.map('Header.TButton', background=[('pressed', '#31516f'), ('active', '#2c4967')], foreground=[('!disabled', '#eff5fd')])
    style.configure('Link.TButton', padding=(4, 5), borderwidth=0, foreground=c['accent'])
    style.configure('TEntry', padding=7, fieldbackground='#fafbfd', bordercolor=c['line'],
                    lightcolor=c['line'], darkcolor=c['line'], insertcolor=c['ink'])
    style.map('TEntry', bordercolor=[('focus', c['accent'])],
              fieldbackground=[('disabled', '#eff2f6'), ('readonly', '#f3f6fa')],
              foreground=[('disabled', '#8693a3')])
    style.configure('TCombobox', padding=6, fieldbackground='#fafbfd', background='#f3f6fa',
                    arrowcolor=c['muted'], bordercolor=c['line'], lightcolor=c['line'], darkcolor=c['line'])
    style.map('TCombobox', fieldbackground=[('disabled', '#eff2f6'), ('readonly', '#fafbfd')],
              foreground=[('disabled', '#8693a3'), ('readonly', c['ink'])],
              selectbackground=[('readonly', '#fafbfd')], selectforeground=[('readonly', c['ink'])],
              bordercolor=[('focus', c['accent'])])
    style.configure('TCheckbutton', padding=(0, 4), background=c['surface'])
    style.map('TCheckbutton', background=[('active', c['surface'])], foreground=[('disabled', '#8693a3')])
    style.configure('TNotebook', background=c['surface'], borderwidth=0, tabmargins=(0, 0, 0, 4))
    style.configure('TNotebook.Tab', background='#f1f4f8', foreground=c['muted'], padding=(13, 10), borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', c['soft']), ('active', '#e7eef7')],
              foreground=[('selected', c['accent'])])
    style.configure('Treeview', background=c['surface'], fieldbackground=c['surface'], foreground=c['ink'],
                    rowheight=30, borderwidth=0)
    style.map('Treeview', background=[('selected', '#dceafd')], foreground=[('selected', '#133e6c')])
    style.configure('Treeview.Heading', background='#edf2f8', foreground=c['muted'],
                    font=('Segoe UI', 9, 'bold'), padding=(8, 9), relief='flat')
    style.map('Treeview.Heading', background=[('active', '#e3ebf5')])
    style.configure('TPanedwindow', background=c['background'], sashwidth=8)
    style.configure('TScrollbar', background='#c8d3df', troughcolor='#f3f6fa', borderwidth=0,
                    arrowcolor=c['muted'], arrowsize=12)
    style.configure('TSeparator', background=c['line'])
    return style


class ChoiceBinding:
    """Keep display labels separate from the canonical JSON/API values."""
    def __init__(self, master, variable, choices):
        self.variable, self.choices = variable, dict(choices)
        self.display = tk.StringVar(master)
        self._trace = variable.trace_add('write', self.sync)
        self.sync()

    def sync(self, *_):
        code = self.variable.get()
        self.display.set(self.choices.get(code, code))

    def select(self, label=None):
        label = self.display.get() if label is None else label
        code = next((key for key, value in self.choices.items() if value == label), None)
        if code is None:
            raise ValueError('Seleção desconhecida.')
        if self.variable.get() != code:
            self.variable.set(code)

    def close(self):
        self.variable.trace_remove('write', self._trace)


class LabelCombo(ttk.Combobox):
    def __init__(self, master, variable, choices, **kw):
        self.binding = ChoiceBinding(master, variable, choices)
        super().__init__(master, textvariable=self.binding.display, values=list(choices.values()), state='readonly', **kw)
        self.bind('<<ComboboxSelected>>', lambda event: self.binding.select())
        self.bind('<Destroy>', lambda event: self.binding.close() if event.widget is self else None)


class FlowLabel(ttk.Label):
    """Wrap explanatory text to the available panel width, also after resizing."""
    def __init__(self, master, **kw):
        kw.setdefault('wraplength', 300)
        super().__init__(master, **kw)
        self.bind('<Configure>', self._resize)

    def _resize(self, event):
        width = max(80, event.width - 8)
        if int(float(self.cget('wraplength'))) != width:
            self.configure(wraplength=width)


class ScrollTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=COLORS['surface'], width=400)
        bar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew'); bar.grid(row=0, column=1, sticky='ns')
        self.body = ttk.Frame(self.canvas, padding=(12, 16, 12, 12)); self.body.columnconfigure(0, weight=1)
        win = self.canvas.create_window(0, 0, window=self.body, anchor='nw')
        self.body.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(win, width=e.width))


class Disclosure(ttk.Frame):
    """Secondary instructions stay accessible without occupying the form."""
    def __init__(self, master, title, text):
        super().__init__(master)
        self.columnconfigure(0, weight=1); self.open = False; self.title = title
        self.button = ttk.Button(self, text='+  ' + title, command=self.toggle, style='Link.TButton')
        self.button.grid(row=0, column=0, sticky='w')
        self.body = FlowLabel(self, text=text, style='Muted.TLabel')

    def toggle(self):
        self.open = not self.open
        self.button.configure(text=('−  ' if self.open else '+  ') + self.title)
        if self.open: self.body.grid(row=1, column=0, sticky='ew', pady=(4, 8))
        else: self.body.grid_remove()


def field_states(values):
    """Presentation availability only; the calculation engine validates inputs."""
    mode = values['beta_mode']; pos = values['pilar_tipo']; shape = values['pilar_forma']
    ec2 = mode == 'ec2' and not values['is_sapata']
    rectangular = shape == 'retangular'
    general = ((pos == 'interior' and rectangular and values['interior_beta_method'] == 'ec2_639')
               or (pos == 'bordo' and not values['edge_perp_interior'])
               or (pos == 'canto' and not values['corner_interior']))
    # Retain an editable non-zero or invalid g after a position change; users
    # must be able to correct it rather than being trapped by a disabled field.
    try: has_gap = float(str(values['edge_distance_m']).replace(',', '.')) != 0
    except ValueError: has_gap = True
    both_depths = bool(str(values['laje_dx']).strip() and str(values['laje_dy']).strip())
    foot = bool(values['is_sapata'])
    return {
        'beta_manual': mode == 'manual', 'beta_reference': mode == 'manual',
        'simplified_applicable': mode == 'simplificado',
        'interior_beta_method': ec2 and pos == 'interior' and rectangular,
        'allow_biaxial_envelope': ec2 and general,
        'edge_perp_interior': pos == 'bordo', 'corner_interior': pos == 'canto',
        'pilar_c2': rectangular, 'edge_distance_m': pos == 'bordo' or has_gap,
        'laje_d': not both_depths and values.get('long_mode','manual')!='automatic',
        **{k:values.get('long_mode','manual')!='automatic' for k in ('laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm')},
        'footing_shape': foot, 'footing_bx': foot and values['footing_shape'] == 'retangular',
        'footing_by': foot and values['footing_shape'] == 'retangular',
        'footing_diameter': foot and values['footing_shape'] == 'circular', 'sigma_gd_kpa': foot,
    }
