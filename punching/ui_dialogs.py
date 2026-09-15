"""Case catalogue and desktop help dialogs."""
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import unicodedata
from .ui import COLORS, FlowLabel


def search_key(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


class ExampleDialog(tk.Toplevel):
    def __init__(self, parent, examples):
        super().__init__(parent)
        self.title('Casos de exemplo'); self.transient(parent); self.configure(bg=COLORS['surface'])
        self.geometry(f'{min(900, self.winfo_screenwidth()-80)}x{min(650, self.winfo_screenheight()-100)}')
        self.minsize(650, 470); self.result = None
        self.names = list(examples)
        catalog = json.loads((Path(__file__).resolve().parent.parent/'examples/catalog.json').read_text(encoding='utf-8'))
        self.descriptions = {item['title']: item['description'] for item in catalog}
        self.columnconfigure(0, weight=1); self.rowconfigure(2, weight=1)
        head = ttk.Frame(self, padding=(20, 16)); head.grid(row=0, column=0, sticky='ew'); head.columnconfigure(0, weight=1)
        ttk.Label(head, text='Casos de exemplo', font=('Segoe UI', 16, 'bold')).grid(row=0, column=0, sticky='w')
        FlowLabel(head, text='Selecione uma configuração e consulte a sua descrição técnica antes de a carregar.', style='Muted.TLabel').grid(row=1, column=0, sticky='ew', pady=(6, 0))
        search = ttk.Frame(self, padding=(20, 0, 20, 10)); search.grid(row=1, column=0, sticky='ew'); search.columnconfigure(1, weight=1)
        ttk.Label(search, text='Pesquisar').grid(row=0, column=0, padx=(0, 12))
        self.query = tk.StringVar(self); entry = ttk.Entry(search, textvariable=self.query)
        entry.grid(row=0, column=1, sticky='ew'); self.query.trace_add('write', self._filter)
        table = ttk.Frame(self, padding=(20, 0)); table.grid(row=2, column=0, sticky='nsew'); table.columnconfigure(0, weight=1); table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=('name',), show='headings', selectmode='browse', height=10)
        self.tree.heading('name', text='Configuração estrutural'); self.tree.column('name', width=680, minwidth=350)
        self.tree.grid(row=0, column=0, sticky='nsew')
        bar = ttk.Scrollbar(table, orient='vertical', command=self.tree.yview); bar.grid(row=0, column=1, sticky='ns'); self.tree.configure(yscrollcommand=bar.set)
        self.description = tk.StringVar(self)
        FlowLabel(self, textvariable=self.description, padding=(20, 12), style='Muted.TLabel').grid(row=3, column=0, sticky='ew')
        footer = ttk.Frame(self, padding=(20, 4, 20, 16)); footer.grid(row=4, column=0, sticky='ew'); footer.columnconfigure(0, weight=1)
        self.count = tk.StringVar(self); ttk.Label(footer, textvariable=self.count, style='Muted.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Button(footer, text='Cancelar', command=self.destroy).grid(row=0, column=1, padx=8)
        self.apply_button = ttk.Button(footer, text='Carregar exemplo', style='Primary.TButton', command=self._apply)
        self.apply_button.grid(row=0, column=2)
        self.tree.bind('<<TreeviewSelect>>', self._select)
        self.tree.bind('<Double-1>', lambda e: self._apply()); self.bind('<Return>', lambda e: self._apply())
        self.bind('<Escape>', lambda e: self.destroy()); self._filter(); self.grab_set(); entry.focus_set()

    def _filter(self, *_):
        query = search_key(self.query.get())
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, name in enumerate(self.names):
            if query in search_key(name + ' ' + self.descriptions.get(name, '')):
                self.tree.insert('', tk.END, iid=str(i), values=(name,))
        children = self.tree.get_children(); self.count.set(f'{len(children)} de {len(self.names)} exemplos')
        self.apply_button.configure(state='normal' if children else 'disabled')
        if children: self.tree.selection_set(children[0]); self.tree.focus(children[0]); self._select()
        else: self.description.set('Nenhum caso corresponde à pesquisa.')

    def _select(self, event=None):
        selected = self.tree.selection()
        if selected: self.description.set(self.descriptions.get(self.names[int(selected[0])], ''))

    def _apply(self):
        selected = self.tree.selection()
        if selected: self.result = self.names[int(selected[0])]; self.destroy()


class HelpDialog(tk.Toplevel):
    def __init__(self, parent, version):
        super().__init__(parent)
        self.title('Ajuda · PunchingShearEC2'); self.transient(parent); self.configure(bg=COLORS['surface'])
        self.geometry(f'{min(770, self.winfo_screenwidth()-80)}x{min(680, self.winfo_screenheight()-100)}')
        self.columnconfigure(0, weight=1); self.rowconfigure(1, weight=1)
        ttk.Label(self, text=f'PunchingShearEC2 {version}', font=('Segoe UI', 16, 'bold'), padding=(20, 18)).grid(row=0, column=0, sticky='w')
        body = ttk.Frame(self, padding=(20, 0)); body.grid(row=1, column=0, sticky='nsew'); body.columnconfigure(0, weight=1); body.rowconfigure(0, weight=1)
        text = tk.Text(body, wrap='word', bg=COLORS['surface'], fg=COLORS['ink'], font=('Segoe UI', 10), borderwidth=0, padx=4, pady=8, spacing3=8)
        text.grid(row=0, column=0, sticky='nsew')
        bar = ttk.Scrollbar(body, orient='vertical', command=text.yview); bar.grid(row=0, column=1, sticky='ns'); text.configure(yscrollcommand=bar.set)
        text.tag_configure('heading', font=('Segoe UI', 11, 'bold'), foreground=COLORS['accent'], spacing1=12)
        entries = [
            ('Definir e verificar', '1. Em Dados, introduza a geometria, materiais e esforços da mesma combinação.\n2. Escolha o Método β. Os campos visíveis acompanham a seleção.\n3. Consulte a Planta e defina as aberturas, se existirem.\n4. Prima Calcular (F5). Confira o estado global, Verificações, Fiadas e Memória.\n5. Exporte os relatórios da execução atual.'),
            ('Importar pilares e esforços', 'Em «Pilares…», importe as tabelas de geometria, extremos dos pilares ou resultantes integrais da ligação. Associe as colunas, confira unidades e convenções e selecione uma ligação/combinação. Em Dados, use «Origem dos esforços…» para adotar a fonte. Complete d, As, betão e posição do pilar. «Guardar conjunto…» conserva todas as ligações. IMPORTACAO.md explica os formatos e os exemplos. N acumulado não equivale à carga da laje; resultados locais Mxx/Myy/Qx/Qy por metro não são resultantes da ligação.'),
            ('Modelo por piso e pilar', 'Após importar a tabela de barras, use «Preparar modelo…». Configure os eixos comuns e as exceções por barra; com Node/X/Y/Z, os tramos são reconhecidos pelas coordenadas. Sem coordenadas, associe-os no nó. Confira as ligações e adote os esforços por combinação. Depois escolha piso/pilar, complete os dados comuns da laje e use F5. «Orientar ligação…» roda esforços, secção, armaduras e aberturas. «Combinações…» mostra os casos condicionantes; «Relatório do conjunto…» exporta por piso. CQC/SRSS ficam pendentes. MODELO_POR_PISO.md inclui o guia e o exemplo com dois pisos. A consulta individual continua em «Barras e nós…»; ver MODELO_IMPORTACAO.md.'),
            ('β manual', 'Escolha «Manual · valor e referência» no separador Método β. Preencha o valor e a referência da análise que o fundamenta. Um número introduzido no modo manual não é utilizado quando está selecionado EC2 ou Simplificado. A existência da referência não valida o conteúdo técnico da análise.'),
            ('Planta e aberturas', 'A planta acompanha as entradas. Ative «Editar pilar» para arrastar as pegas azuis. Em «Aberturas…», pode desenhar, mover ou redimensionar retângulos e círculos, ou introduzir medidas exatas. «Aplicar ao caso» confirma as alterações; «Cancelar» conserva a definição anterior.'),
            ('Resultados e atualização', 'Qualquer alteração de entradas retira os resultados do ecrã e desativa as exportações até ao novo cálculo. O cartão de utilização mostra o máximo das verificações resistentes calculadas; a conclusão global considera também as pendências de β e pormenorização. «OK» numa fiada não equivale a aprovação global.'),
            ('Navegação e atalhos', 'Ctrl+N · Novo caso\nCtrl+O · Abrir caso JSON\nCtrl+S · Guardar caso JSON\nF5 · Calcular\nF1 · Ajuda\nTab / Shift+Tab · Navegar pelos campos\nOs painéis são redimensionáveis pela divisória vertical. A roda do rato desloca o formulário sob o ponteiro.'),
            ('Documentação', 'GUI_TESTES.md contém o guião de testes da interface. README.md descreve as entradas e a instalação. METODOS_BETA.md, ABERTURAS_GUI.md e VALIDACAO.md documentam os métodos, exemplos e limites.\nReferencial: NP EN 1992-1-1:2010 + AC:2012 + A1:2019, com Anexo Nacional português.'),
        ]
        for heading, paragraph in entries:
            text.insert(tk.END, heading + '\n', 'heading'); text.insert(tk.END, paragraph + '\n')
        text.configure(state='disabled')
        ttk.Button(self, text='Fechar', command=self.destroy).grid(row=2, column=0, sticky='e', padx=20, pady=16)
        self.bind('<Escape>', lambda e: self.destroy()); self.grab_set()
