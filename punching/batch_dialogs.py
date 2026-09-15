"""Selection-based input editing for projects, floors and named pillar groups."""
import tkinter as tk
from .longitudinal import CHOICES as LONG_CHOICES
from .ui import LabelCombo
from tkinter import ttk, messagebox
from .import_dialogs import window
from .ui import ScrollTab, FlowLabel
from .batch_workflow import (validate_fields, representatives, named_group, PROJECT_KEYS,
                             FLOOR_KEYS, SHARED_KEYS)
from .model_workflow import FRAME_LABELS

FIELDS = [
 ('Projeto e materiais',[
  ('project','Nome do projeto',''),('betão_fck','Betão · fck','MPa'),('aço_fyk','Aço longitudinal · fyk','MPa'),
  ('aço_fywk','Estribos · fywk','MPa'),('gamma_C','Coeficiente γC',''),('gamma_S','Coeficiente γS','')]),
 ('Laje',[
  ('long_mode','Modo de armadura longitudinal',''),
  ('laje_d','Altura útil média · d','m'),('laje_dx','Altura útil · dx','m; vazio = usar d'),
  ('laje_dy','Altura útil · dy','m; vazio = usar d'),('laje_As_lx_cm2pm','Armadura As,x','cm²/m'),
  ('laje_As_ly_cm2pm','Armadura As,y','cm²/m'),('sigma_cp','Compressão no plano','MPa')]),
 ('Armadura longitudinal automática',[
  ('long_h_mm','Espessura da laje · h','mm'),('long_cover_mm','Recobrimento à armadura longitudinal','mm'),
  ('long_outer_axis','Camada mais próxima da face tracionada',''),('long_layer_gap_mm','Afastamento livre entre camadas X/Y','mm'),
  ('long_x_base_mm','X · diâmetro base','mm'),('long_x_extra_mm','X · diâmetro reforço','mm'),('long_x_spacing_mm','X · espaçamento comum','mm'),
  ('long_y_base_mm','Y · diâmetro base','mm'),('long_y_extra_mm','Y · diâmetro reforço','mm'),('long_y_spacing_mm','Y · espaçamento comum','mm')]),
 ('Armadura de punçoamento',[
  ('reinforcement_diameter_mm','Diâmetro dos ramos','mm'),('reinforcement_s0_m','Primeira fiada · s0','m; vazio = automático'),
  ('reinforcement_sr_m','Espaçamento radial · sr','m; vazio = automático'),
  ('cover_mm','Recobrimento','mm'),('aggregate_mm','Dimensão máxima do agregado','mm')]),
 ('Posição e bordo',[('pilar_tipo','Posição do pilar',''),('edge_distance_m','Face ao bordo · g','m')])]


class BulkEditDialog(tk.Toplevel):
    def __init__(self,parent,book,keys):
        super().__init__(parent);self.result=None;self.book=book;self.keys=keys
        window(self,parent,'Editar pilares selecionados',990,780)
        head=ttk.Frame(self,padding=16);head.grid(row=0,column=0,sticky='ew');head.columnconfigure(0,weight=1)
        reps=representatives(book,keys)
        FlowLabel(head,text=f'{len(reps)} pilares selecionados. Assinale os campos a aplicar.',style='Section.TLabel').grid(row=0,column=0,sticky='ew')
        self.mode=tk.StringVar(self,'Preencher apenas campos vazios')
        ttk.Combobox(head,textvariable=self.mode,values=['Preencher apenas campos vazios','Atualizar os campos assinalados'],state='readonly').grid(row=1,column=0,sticky='ew',pady=8)
        tabs=ttk.Notebook(self);tabs.grid(row=1,column=0,sticky='nsew',padx=16)
        self.values={};self.enabled={};self.scroll_tabs=[]
        for title,fields in FIELDS:
            tab=ScrollTab(tabs);tabs.add(tab,text=title);self.scroll_tabs.append(tab);body=tab.body;body.columnconfigure(2,weight=1)
            for row,(name,label,unit) in enumerate(fields):
                enabled=tk.BooleanVar(self,False);self.enabled[name]=enabled
                options={(book.cases[k].get('draft') or {}).get(name,'') for k in reps}
                value=next(iter(options)) if len(options)==1 else ''
                var=tk.StringVar(self,value);self.values[name]=var
                ttk.Checkbutton(body,variable=enabled).grid(row=row,column=0,padx=8,pady=9)
                ttk.Label(body,text=label).grid(row=row,column=1,sticky='w',padx=6)
                choices={'pilar_tipo':['interior','bordo','canto'],'reinforcement_diameter_mm':['10','12','16']}.get(name)
                widget=LabelCombo(body,var,LONG_CHOICES[name]) if name in LONG_CHOICES else ttk.Combobox(body,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(body,textvariable=var)
                widget.grid(row=row,column=2,sticky='ew',padx=8)
                ttk.Label(body,text=unit+(' · valores distintos' if len(options)>1 else '')).grid(row=row,column=3,sticky='w',padx=8)
        for event in ('<MouseWheel>','<Button-4>','<Button-5>'):self.bind(event,self._wheel,add='+')
        foot=ttk.Frame(self,padding=16);foot.grid(row=2,column=0,sticky='ew');foot.columnconfigure(1,weight=1)
        ttk.Label(foot,text='Orientação no modelo').grid(row=0,column=0,sticky='w',pady=6)
        self.turn=tk.StringVar(self,'Manter em cada pilar')
        ttk.Combobox(foot,textvariable=self.turn,values=['Manter em cada pilar']+list(FRAME_LABELS.values()),state='readonly').grid(row=0,column=1,columnspan=2,sticky='ew',padx=8)
        self.templates={'Apenas nesta seleção':None,'Guardar predefinição do projeto':('project','')}
        floors={book.cases[k]['floor'] for k in reps};groups={named_group(book,book.cases[k]) for k in reps}
        if len(floors)==1:
            floor=next(iter(floors));self.templates['Guardar predefinição do piso: '+floor]=('floor',floor)
        if len(groups)==1 and next(iter(groups)):
            group=next(iter(groups));self.templates['Guardar predefinição do grupo: '+group]=('group',group)
        self.template=tk.StringVar(self,'Apenas nesta seleção')
        ttk.Label(foot,text='Reutilizar parâmetros').grid(row=1,column=0,sticky='w',pady=6)
        ttk.Combobox(foot,textvariable=self.template,values=list(self.templates),state='readonly').grid(row=1,column=1,columnspan=2,sticky='ew',padx=8)
        FlowLabel(foot,text='Os valores de As,x, As,y, dx e dy referem-se aos eixos de cada caso após a orientação escolhida. A rotação atua em todas as combinações dos pilares selecionados. No modo automático, defina h, recobrimento e base/reforço por direção; d e As serão recalculados. A combinação deve representar a armadura média em toda a faixa de cálculo. As predefinições serão usadas nos pilares ainda não editados; os restantes conservam as suas exceções.',style='Muted.TLabel').grid(row=2,column=0,columnspan=3,sticky='ew',pady=10)
        ttk.Button(foot,text='Aplicar à seleção',command=self._apply,style='Primary.TButton').grid(row=3,column=1,sticky='e')
        ttk.Button(foot,text='Cancelar',command=self.destroy).grid(row=3,column=2,padx=8)

    def _wheel(self,event):
        widget=self.winfo_containing(event.x_root,event.y_root)
        for tab in self.scroll_tabs:
            if widget is not None and str(widget).startswith(str(tab)):
                num=getattr(event,'num',None);delta=getattr(event,'delta',0)
                step=-1 if num==4 or delta>0 else 1 if num==5 or delta<0 else 0
                if step:tab.canvas.yview_scroll(step*3,'units')
                return 'break'

    def _apply(self):
        try:
            fields={k:self.values[k].get() for k,v in self.enabled.items() if v.get()}
            template=self.templates[self.template.get()]
            allowed=PROJECT_KEYS if template and template[0]=='project' else PROJECT_KEYS|FLOOR_KEYS if template and template[0]=='floor' else SHARED_KEYS
            validate_fields(fields,allowed)
            turn=next((k for k,v in FRAME_LABELS.items() if v==self.turn.get()),None)
            if not fields and turn is None:raise ValueError('Assinale os campos a aplicar ou escolha uma orientação.')
            self.result=dict(fields=fields,only_empty=self.mode.get().startswith('Preencher'),turn=turn,template=template)
            self.destroy()
        except ValueError as exc:messagebox.showerror('Editar seleção',str(exc),parent=self)


class GroupDialog(tk.Toplevel):
    def __init__(self,parent,book,keys):
        super().__init__(parent);self.result=None
        window(self,parent,'Agrupar pilares',740,380)
        body=ttk.Frame(self,padding=20);body.grid(row=0,column=0,sticky='ew');body.columnconfigure(0,weight=1)
        FlowLabel(body,text=f'{len(representatives(book,keys))} pilares: escreva um nome ou escolha um grupo existente.',style='Section.TLabel').grid(row=0,column=0,sticky='ew',pady=10)
        self.name=tk.StringVar(self)
        ttk.Combobox(body,textvariable=self.name,values=sorted(book.batch_settings['groups'])).grid(row=1,column=0,sticky='ew',pady=10)
        FlowLabel(body,text='Exemplo: COBERTURA · Bordo −X. A atribuição do grupo organiza a seleção; use «Editar seleção…» para aplicar parâmetros comuns.',style='Muted.TLabel').grid(row=2,column=0,sticky='ew',pady=10)
        ttk.Button(body,text='Atribuir grupo',command=self._apply,style='Primary.TButton').grid(row=3,column=0,sticky='e',pady=8)
        ttk.Button(body,text='Cancelar',command=self.destroy).grid(row=4,column=0,sticky='e')

    def _apply(self):
        if not self.name.get().strip():messagebox.showerror('Grupo','Indique o nome do grupo.',parent=self);return
        self.result=self.name.get().strip();self.destroy()
