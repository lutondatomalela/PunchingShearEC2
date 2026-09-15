"""Model setup, joint selection and combination results for the desktop GUI."""
from copy import deepcopy
import tkinter as tk
from tkinter import ttk, messagebox

from .import_dialogs import window, text_view, set_text, ImportDialog
from .ui import ScrollTab, FlowLabel
from .analysis_dialogs import table_view
from .analysis_import import all_records, members, parse_nodes, restore
from .model_workflow import topology, FRAME_LABELS
from .model_revision import prepare_revision
from .member_selection import select_members, alignment_members, compact_members
from .collection_workflow import turn_of, summaries, cached_calculation, group_keys, PENDING_LABELS
from .table_import import token, key


class ModelDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent);self.app=app;self.result=None;self.prepared=None;self.rows=[];self.current=None
        window(self,parent,'Modelo - preparar ligações por piso',1160,850)
        head=ttk.Frame(self,padding=14);head.grid(row=0,column=0,sticky='ew');head.columnconfigure(0,weight=1)
        FlowLabel(head,text='Configure os eixos, guarde a configuração ou prepare novas ligações por combinação.',style='Section.TLabel').grid(row=0,column=0,sticky='ew')
        ttk.Button(head,text='Importar nós…',command=self._nodes).grid(row=0,column=1,padx=(12,0))
        self.tabs=ttk.Notebook(self);self.tabs.grid(row=1,column=0,sticky='nsew',padx=14)
        config=ScrollTab(self.tabs);self.tabs.add(config,text='1 · Modelo e eixos')
        self.scroll_tab=config
        for event in ('<MouseWheel>','<Button-4>','<Button-5>'):self.bind(event,self._wheel,add='+')
        links=ttk.Frame(self.tabs,padding=10);links.columnconfigure(0,weight=1);links.rowconfigure(1,weight=1);self.tabs.add(links,text='2 · Ligações por piso')
        preview,self.preview=text_view(self.tabs);self.tabs.add(preview,text='3 · Conferência')
        cfg=deepcopy(app._book.model_setup['config']) if app._book.model_setup else {}
        self.axes=dict(cfg.get('member_axes',{}));self.options={};body=config.body;body.columnconfigure(1,weight=1)
        fields=[('x','x local dos pilares (axial)',['','+Z','-Z'],cfg.get('axes',{}).get('x','+Z')),
            ('y','y local dos pilares (transversal)',['','+X','-X','+Y','-Y'],cfg.get('axes',{}).get('y','')),
            ('combinations','Combinações: números / intervalos (vazio = todas)',None,cfg.get('combinations','')),
            ('reference','Referência do modelo e dos eixos',None,cfg.get('reference',''))]
        for i,(name,label,choices,value) in enumerate(fields):
            ttk.Label(body,text=label).grid(row=i,column=0,sticky='w',padx=10,pady=6)
            var=tk.StringVar(self,value);self.options[name]=var
            widget=ttk.Combobox(body,textvariable=var,values=choices,state='readonly') if choices else ttk.Entry(body,textvariable=var)
            widget.grid(row=i,column=1,sticky='ew',padx=10,pady=6)
        FlowLabel(body,text='X/Y/Z referem-se aqui ao modelo de referência: X/Y em planta, Z para cima. z local resulta de x × y. A direção y não é deduzida das cores. Posteriormente pode orientar o caso para o bordo escolhido, rodando conjuntamente geometria e esforços.',style='Muted.TLabel').grid(row=4,column=0,columnspan=2,sticky='ew',padx=10,pady=12)
        exception=ttk.Frame(body,padding=10);exception.grid(row=5,column=0,columnspan=2,sticky='ew')
        self.bar=tk.StringVar(self);self.bar_x=tk.StringVar(self,'+Z');self.bar_y=tk.StringVar(self,'+X')
        exception.columnconfigure(1,weight=1)
        ttk.Label(exception,text='Barras / intervalos').grid(row=0,column=0,sticky='w')
        self.bar_selector=ttk.Combobox(exception,textvariable=self.bar,values=[],state='normal',width=30);self.bar_selector.grid(row=0,column=1,padx=8,sticky='ew')
        ttk.Combobox(exception,textvariable=self.bar_x,values=['+Z','-Z'],state='readonly',width=8).grid(row=0,column=2,padx=4)
        ttk.Combobox(exception,textvariable=self.bar_y,values=['+X','-X','+Y','-Y'],state='readonly',width=8).grid(row=0,column=3,padx=4)
        actions=ttk.Frame(exception);actions.grid(row=1,column=0,columnspan=4,sticky='w',pady=6)
        ttk.Button(actions,text='Estender à prumada',command=self._alignment).grid(row=0,column=0,padx=(0,6))
        ttk.Button(actions,text='Aplicar eixos às barras',command=self._axis).grid(row=0,column=1,padx=6)
        ttk.Button(actions,text='Usar perfil comum',command=self._remove_axis).grid(row=0,column=2,padx=6)
        ttk.Button(actions,text='Ver exceções…',command=self._show_axes).grid(row=0,column=3,padx=6)
        FlowLabel(exception,text='Exemplos: 110para113 115 118para123; 110-113 115 118-123; 110 111 112. A prumada expande a seleção pelos nós ligados; confira os eixos de todas as barras antes de aplicar.',style='Muted.TLabel').grid(row=2,column=0,columnspan=4,sticky='ew')
        self.selection_text=tk.StringVar(self)
        FlowLabel(exception,textvariable=self.selection_text,style='Muted.TLabel').grid(row=3,column=0,columnspan=4,sticky='ew')
        self.axes_text=tk.StringVar(self);FlowLabel(body,textvariable=self.axes_text,style='Muted.TLabel').grid(row=6,column=0,columnspan=2,sticky='ew',padx=10,pady=5)
        self.checks={}
        declarations=[('analysis_3d','Modelo 3D: pilares verticais e alinhados.'),
            ('same_combination','Conferi as combinações selecionadas. O equilíbrio só se aplica a esforços ELU originais concomitantes; CQC/SRSS e envolventes ficam pendentes.'),
            ('isolated_joint','Nas ligações selecionadas, a laje é a única transferência entre os dois tramos. Não há outras vigas, pilares ou cargas nodais a incluir.'),
            ('at_joint','Esforços nos extremos reais à cota da laje, no centro do pilar, sem offsets ou braços rígidos; conferi tramos, cotas e pisos.'),
            ('axes_confirmed','Conferi o perfil comum e as exceções de eixos por barra no modelo de origem.')]
        for i,(name,label) in enumerate(declarations,7):
            line=ttk.Frame(body,padding=(10,5));line.grid(row=i,column=0,columnspan=2,sticky='ew');line.columnconfigure(1,weight=1)
            v=tk.BooleanVar(self,cfg.get(name,False));self.checks[name]=v
            ttk.Checkbutton(line,variable=v).grid(row=0,column=0,sticky='n')
            FlowLabel(line,text=label).grid(row=0,column=1,sticky='ew',padx=5)
        filterbar=ttk.Frame(links);filterbar.grid(row=0,column=0,sticky='ew');filterbar.columnconfigure(1,weight=1)
        ttk.Label(filterbar,text='Filtrar piso / pilar / nó').grid(row=0,column=0,sticky='w')
        self.search=tk.StringVar(self);ttk.Entry(filterbar,textvariable=self.search).grid(row=0,column=1,sticky='ew',padx=8)
        ttk.Button(filterbar,text='Incluir filtradas válidas',command=lambda:self._include(True)).grid(row=0,column=2,padx=4)
        ttk.Button(filterbar,text='Excluir filtradas',command=lambda:self._include(False)).grid(row=0,column=3)
        frame,self.tree=table_view(links,[('enabled','Incluir',60),('floor','Piso da ligação',115),('support','Pilar',90),('node','Nó',70),('z','Cota Z · m',90),('below','Inferior',75),('above','Superior',75),('issue','Conferência',320)])
        frame.grid(row=1,column=0,sticky='nsew',pady=10)
        form=ttk.Frame(links);form.grid(row=2,column=0,sticky='ew')
        self.link={};self.link_widgets={}
        for i,(name,label) in enumerate([('floor','Piso'),('support','Pilar'),('below','Tramo inferior'),('above','Tramo superior')]):
            ttk.Label(form,text=label).grid(row=0,column=i,sticky='w',padx=5)
            var=tk.StringVar(self);self.link[name]=var
            widget=ttk.Combobox(form,textvariable=var,values=[],state='readonly',width=18) if name in ('below','above') else ttk.Entry(form,textvariable=var,width=19)
            widget.grid(row=1,column=i,sticky='ew',padx=5);form.columnconfigure(i,weight=1);self.link_widgets[name]=widget
        self.include=tk.BooleanVar(self,False);self.absent=tk.BooleanVar(self,False)
        self.include_widget=ttk.Checkbutton(form,text='Incluir esta ligação',variable=self.include);self.include_widget.grid(row=2,column=0,columnspan=2,sticky='w',pady=8)
        self.absent_widget=ttk.Checkbutton(form,text='Tramo superior fisicamente ausente',variable=self.absent);self.absent_widget.grid(row=2,column=2,columnspan=2,sticky='w',pady=8)
        self.edit_widget=ttk.Button(form,text='Aplicar à ligação selecionada',command=self._edit);self.edit_widget.grid(row=3,column=0,columnspan=2,sticky='w')
        FlowLabel(links,text='O piso é sugerido a partir de Story do tramo inferior; confira-o com a cota da laje. Sem coordenadas, indique os tramos no nó. Um extremo isolado não é considerado cobertura automaticamente.',style='Muted.TLabel').grid(row=3,column=0,sticky='ew',pady=10)
        self.summary=tk.StringVar(self);FlowLabel(links,textvariable=self.summary).grid(row=4,column=0,sticky='ew')
        foot=ttk.Frame(self,padding=14);foot.grid(row=2,column=0,sticky='ew');foot.columnconfigure(0,weight=1)
        ttk.Button(foot,text='Conferir ligações',command=self._preview).grid(row=0,column=0,sticky='w')
        self.apply=ttk.Button(foot,text='Aplicar ligações conferidas',style='Primary.TButton',command=self._apply,state='disabled');self.apply.grid(row=0,column=1,sticky='e')
        self.save=ttk.Button(foot,text='Guardar configuração e fechar',command=self._save);self.save.grid(row=1,column=0,sticky='w',pady=(6,0))
        ttk.Button(foot,text='Cancelar',command=self.destroy).grid(row=1,column=1,sticky='e',pady=(6,0))
        FlowLabel(foot,text='Guardar atualiza os eixos das ligações existentes e grava o conjunto. Para criar as novas ligações selecionadas, use Conferir e Aplicar.',style='Muted.TLabel').grid(row=2,column=0,columnspan=2,sticky='ew',pady=(8,0))
        self.search.trace_add('write',self._filter);self.tree.bind('<<TreeviewSelect>>',self._detail)
        for v in (*self.options.values(),*self.checks.values()):v.trace_add('write',self._invalidate)
        for v in (*self.link.values(),self.include,self.absent):v.trace_add('write',self._invalidate)
        self._reload()

    def _invalidate(self,*_):self.prepared=None;self.apply.configure(state='disabled')

    def _wheel(self,event):
        target=self.winfo_containing(event.x_root,event.y_root)
        if target is not None and str(target).startswith(str(self.scroll_tab)):
            num=getattr(event,'num',None);delta=getattr(event,'delta',0)
            step=-1 if num==4 or delta>0 else 1 if num==5 or delta<0 else 0
            if step:self.scroll_tab.canvas.yview_scroll(step*3,'units')
            return 'break'

    def _reload(self):
        self.current=None
        self.rows=topology(self.app._book.analysis_tables,self.app._book.analysis_nodes)
        known={j['node']:j for j in (self.app._book.model_setup or {}).get('joints',[])}
        for j in self.rows:
            if j['node'] in known:
                j.update(deepcopy(known[j['node']]))
                j['enabled']=False;j['issue']='Preparada; os eixos podem ser atualizados ao guardar.';j['existing']=True
        self.member_index=members(all_records(self.app._book.analysis_tables))
        self.coordinates=parse_nodes(restore(self.app._book.analysis_nodes)) if self.app._book.analysis_nodes else {}
        self.bar_selector.configure(values=sorted(self.member_index,key=int))
        self._axis_summary();self._filter();self._invalidate()

    def _axis_summary(self):
        profiles={}
        for m,a in self.axes.items():profiles.setdefault((a['x'],a['y']),[]).append(m)
        lines=[]
        for (x,y),ids in sorted(profiles.items()):
            label=compact_members(ids)
            lines.append(f'{len(ids)} barras · x={x}, y={y}: '+(label if len(label)<=140 else label[:140]+'… (lista completa em Ver exceções)'))
        self.axes_text.set('\n'.join(lines) or 'Sem exceções; aplica-se o perfil comum.')

    def _axis(self):
        try:
            selected=select_members(self.bar.get(),self.member_index)
            profile={'x':self.bar_x.get(),'y':self.bar_y.get()}
            for m in selected:self.axes[m]=deepcopy(profile)
            self.selection_text.set(f'Eixos aplicados a {len(selected)} barras: '+compact_members(selected))
            self._axis_summary();self._invalidate()
        except ValueError as exc:messagebox.showerror('Selecionar barras',str(exc),parent=self)

    def _remove_axis(self):
        try:
            selected=select_members(self.bar.get(),self.member_index)
            for m in selected:self.axes.pop(m,None)
            self.selection_text.set(f'Perfil comum aplicado a {len(selected)} barras: '+compact_members(selected))
            self._axis_summary();self._invalidate()
        except ValueError as exc:messagebox.showerror('Selecionar barras',str(exc),parent=self)

    def _alignment(self):
        try:
            selected=alignment_members(select_members(self.bar.get(),self.member_index),self.member_index,self.coordinates)
            self.bar.set(compact_members(selected))
            self.selection_text.set(f'{len(selected)} barras selecionadas na prumada. Confira a lista e aplique os eixos pretendidos.')
        except ValueError as exc:messagebox.showerror('Estender à prumada',str(exc),parent=self)

    def _show_axes(self):
        dialog=tk.Toplevel(self);window(dialog,self,'Exceções de eixos',760,560)
        dialog.rowconfigure(0,weight=1);dialog.rowconfigure(1,weight=0)
        frame,view=text_view(dialog);frame.grid(row=0,column=0,sticky='nsew')
        set_text(view,'\n'.join(f"Barra {m}: x={a['x']}; y={a['y']}" for m,a in sorted(self.axes.items(),key=lambda p:int(p[0]))) or 'Sem exceções; aplica-se o perfil comum.')
        ttk.Button(dialog,text='Fechar',command=dialog.destroy).grid(row=1,column=0,sticky='e',padx=12,pady=12)
        self.wait_window(dialog);self.grab_set()

    def _filter(self,*_):
        self._save_detail()
        for k in self.tree.get_children():self.tree.delete(k)
        q=token(self.search.get());self.filtered=[]
        for i,j in enumerate(self.rows):
            if q not in token(' '.join((j['floor'],j['support'],j['node']))):continue
            self.filtered.append(i)
            self.tree.insert('','end',iid=str(i),values=('Preparada' if j.get('existing') else 'Sim' if j['enabled'] else 'Não',j['floor'],j['support'],j['node'],f"{j['z']:.3f}" if j['z'] is not None else 'Por definir',j['below'],j['above'] or ('Ausente' if j['upper_absent'] else 'Por definir'),j['issue']))
        self.summary.set(f"{sum(j['enabled'] for j in self.rows)} novas selecionadas; {sum(bool(j.get('existing')) for j in self.rows)} já preparadas; {len(self.filtered)} nós visíveis no filtro.")
        self.current=None

    def _include(self,value):
        self._save_detail();self.current=None
        for i in self.filtered:
            j=self.rows[i]
            if j.get('existing'):continue
            if not value or (j['below'] and (j['above'] or j['upper_absent']) and not j['issue']):j['enabled']=value
        self._filter();self._invalidate()

    def _detail(self,*_):
        selected=self.tree.selection()
        if not selected:return
        self._save_detail()
        self.current=int(selected[0]);j=self.rows[self.current]
        for name,var in self.link.items():var.set(j[name])
        for name in ('below','above'):self.link_widgets[name].configure(values=['']+j['members'])
        self.include.set(j['enabled']);self.absent.set(j['upper_absent'])
        locked=j.get('existing',False)
        for name,w in self.link_widgets.items():w.configure(state='disabled' if locked else 'readonly' if name in ('below','above') else 'normal')
        for w in (self.include_widget,self.absent_widget,self.edit_widget):w.configure(state='disabled' if locked else 'normal')

    def _save_detail(self):
        if self.current is None:return
        j=self.rows[self.current]
        if j.get('existing'):return
        values={k:v.get().strip() for k,v in self.link.items()}
        values.update(enabled=self.include.get(),upper_absent=self.absent.get())
        if any(j[k]!=v for k,v in values.items()):
            j.update(values);j['issue']='Associação indicada pelo utilizador; conferir no modelo.';self._invalidate()

    def _edit(self):
        self._save_detail()
        self._filter();self._invalidate()

    def _nodes(self):
        dialog=ImportDialog(self);self.wait_window(dialog);self.grab_set()
        if dialog.result is None:return
        try:
            if dialog.result['mode']!='analysis_nodes':raise ValueError('Selecione uma tabela Node/X/Y/Z, com as unidades das coordenadas.')
            self.app._merge_import(dialog.result);self._reload()
        except Exception as exc:messagebox.showerror('Importar nós',str(exc),parent=self)

    def _config(self):
        d={k:v.get() for k,v in self.checks.items()}
        d.update(axes={'x':self.options['x'].get(),'y':self.options['y'].get()},member_axes=deepcopy(self.axes),
            combinations=self.options['combinations'].get(),reference=self.options['reference'].get())
        return d

    def _preview(self):
        self._save_detail()
        self._invalidate()
        try:
            from Punching_EC2_GUI import DEFAULTS
            _,batch=prepare_revision(self.app._book,self._config(),self.rows,DEFAULTS)
            impact=batch['revision_impact']
            lines=['Conferência das ligações selecionadas','A adoção usa o equilíbrio no mesmo nó, por combinação, no referencial do modelo.',
                'VEd positivo corresponde à carga transferida pela laje; sem dedução de cargas interiores ao perímetro e sem majoração por beta.',
                f"Casos por combinação: {len(impact['added'])} novos; {len(impact['updated'])} atualizados e por recalcular; {len(impact['unchanged'])} sem alteração.",
                'As ligações já preparadas são conservadas. A revisão dos eixos atualiza a origem dos esforços e mantém o referencial de cada caso.','']
            for item in batch['model_review']:
                lines.append(f"{item['floor']} / {item['support']} / nó {item['node']}: {item['ready']} combinações com esforços; {item['pending']} pendentes.")
                for load in batch['loads'].values():
                    if (load['floor'],load['support'])!=(item['floor'],item['support']):continue
                    values=load['adopted']
                    lines.append('  '+load['combination']+': '+('; '.join(f'{k}={v:.3f}' for k,v in values.items())+' (kN; kN.m)' if values else 'PENDENTE - '+' '.join(load['issues'])))
            if impact['manual_geometry']:lines.append('Geometria definida pelo utilizador conservada em '+str(len(impact['manual_geometry']))+' casos; confira-a com a secção de origem revista.')
            lines.extend(['','Aplicar ligações conferidas cria as novas ligações selecionadas e atualiza as existentes. Os dados da laje, armaduras, aberturas e orientação existentes são conservados. Guarde o conjunto para conservar as alterações em ficheiro.'])
            set_text(self.preview,'\n'.join(lines));self.prepared=batch;self.apply.configure(state='normal');self.tabs.select(2)
        except Exception as exc:set_text(self.preview,str(exc));self.tabs.select(2)

    def _apply(self):
        if self.prepared is not None:self.result=self.prepared;self.destroy()

    def _save(self):
        if self.app._save_model_configuration(self._config(),parent=self):self.destroy()


class FrameDialog(tk.Toplevel):
    def __init__(self,parent,case):
        super().__init__(parent);self.result=None
        window(self,parent,'Orientação da ligação no modelo',850,380)
        frame=ttk.Frame(self,padding=20);frame.grid(row=0,column=0,sticky='nsew');frame.columnconfigure(0,weight=1)
        FlowLabel(frame,text=f"{case['floor']} / {case['support']}: escolha o referencial do caso.",style='Section.TLabel').grid(row=0,column=0,sticky='ew',pady=10)
        self.value=tk.StringVar(self,FRAME_LABELS[turn_of(case)])
        ttk.Combobox(frame,textvariable=self.value,values=list(FRAME_LABELS.values()),state='readonly',width=65).grid(row=1,column=0,sticky='ew',pady=10)
        FlowLabel(frame,text='Num bordo, Y do caso aponta para o interior da laje; X é paralelo ao bordo. Num canto, os dois bordos ficam em -X e -Y do caso. A operação roda esforços, secção, direções de armadura e aberturas de todas as combinações desta ligação. Confira a localização do bordo e volte a calcular.',style='Muted.TLabel').grid(row=2,column=0,sticky='ew',pady=10)
        ttk.Button(frame,text='Aplicar orientação',command=self._apply,style='Primary.TButton').grid(row=3,column=0,sticky='e',pady=10)
        ttk.Button(frame,text='Cancelar',command=self.destroy).grid(row=4,column=0,sticky='e')

    def _apply(self):
        self.result=next(k for k,v in FRAME_LABELS.items() if v==self.value.get());self.destroy()


class GroupResultsDialog(tk.Toplevel):
    def __init__(self,parent,book,case):
        super().__init__(parent);self.result=None;self.book=book
        window(self,parent,'Combinações da ligação',1080,740)
        keys=group_keys(book,case);entries=[]
        for k in keys:
            c=book.cases[k];entry=cached_calculation(c)
            entries.append(entry or dict(floor=c['floor'],support=c['support'],combination=c['combination'],status='NOT_EVALUATED',error='Calcular a ligação para atualizar.',snapshot=None))
        s=summaries(entries)[0]
        title=ttk.Frame(self,padding=14);title.grid(row=0,column=0,sticky='ew');title.columnconfigure(0,weight=1)
        FlowLabel(title,text=f"{case['floor']} / {case['support']} · {s['status']} · {s['count']} combinações",style='Section.TLabel').grid(row=0,column=0,sticky='ew')
        frame,self.tree=table_view(self,[('combo','Combinação',150),('v','VEd · kN',105),('mx','MEdx · kN.m',115),('my','MEdy · kN.m',115),('beta','Beta',85),('status','Situação',220)])
        frame.grid(row=1,column=0,sticky='nsew',padx=14)
        self.entries={}
        for k,e in zip(keys,entries):
            self.entries[k]=e;source=book.cases[k]['candidates'].get(book.cases[k]['choice'],{}).get('adopted');r=e['snapshot']
            values=r['load_trace']['adopted'] if r else (source if e['status']=='NOT_EVALUATED' else e.get('actions'))
            self.tree.insert('','end',iid=k,values=(e['combination'],*(f'{values[f]:.3f}' if values else '—' for f in ('V_Ed','M_Edx','M_Edy')),f"{r['values']['beta']:.3f}" if r and r['values']['beta'] is not None else '—',r['badge'] if r else PENDING_LABELS[e['status']]))
        details,self.details=text_view(self);details.grid(row=2,column=0,sticky='ew',padx=14)
        lines=[f"{v['name']}: combinação {v['combination']}, utilização {v['utilization']:.3f}." for v in s['governing'].values()]
        if s['different_reinforcement_proposals']:lines.append('Existem propostas de armadura distintas. O pormenor comum deve ser conferido em todas as combinações.')
        set_text(self.details,'\n'.join(lines))
        foot=ttk.Frame(self,padding=14);foot.grid(row=3,column=0,sticky='ew');foot.columnconfigure(0,weight=1)
        ttk.Button(foot,text='Apresentar combinação',command=self._choose,style='Primary.TButton').grid(row=0,column=1)
        ttk.Button(foot,text='Fechar',command=self.destroy).grid(row=0,column=2,padx=8)
        self.tree.bind('<<TreeviewSelect>>',self._detail);self.tree.bind('<Double-1>',lambda e:self._choose())

    def _detail(self,*_):
        selection=self.tree.selection()
        if not selection:return
        e=self.entries[selection[0]];r=e['snapshot']
        set_text(self.details,r['conclusion']+'\n'+'\n'.join(r['notes']) if r else e['error'])

    def _choose(self):
        selection=self.tree.selection()
        if selection:self.result=selection[0];self.destroy()


class CalculationProgress(tk.Toplevel):
    def __init__(self,parent,count):
        super().__init__(parent);self.cancelled=False
        window(self,parent,'Calcular ligações',680,250)
        f=ttk.Frame(self,padding=20);f.grid(row=0,column=0,sticky='nsew');f.columnconfigure(0,weight=1)
        self.text=tk.StringVar(self,f'A preparar {count} combinações…')
        FlowLabel(f,textvariable=self.text).grid(row=0,column=0,sticky='ew',pady=15)
        ttk.Button(f,text='Interromper após esta combinação',command=self._cancel).grid(row=1,column=0,sticky='e',pady=15)
        self.protocol('WM_DELETE_WINDOW',self._cancel)
        self.bind('<Escape>',lambda e:self._cancel())

    def _cancel(self):self.cancelled=True


class CollectionReportDialog(tk.Toplevel):
    def __init__(self,parent,book,selected_keys=None):
        super().__init__(parent);self.result=None;self.book=book;self.selected_keys=selected_keys or []
        window(self,parent,'Relatório do conjunto',860,610)
        frame=ttk.Frame(self,padding=20);frame.grid(row=0,column=0,sticky='nsew');frame.columnconfigure(1,weight=1)
        FlowLabel(frame,text='Exportar os resultados atuais por piso, grupo ou seleção de pilares.',style='Section.TLabel').grid(row=0,column=0,columnspan=2,sticky='ew',pady=10)
        self.floor=tk.StringVar(self,'Todos os pisos');self.group=tk.StringVar(self,'Todos os grupos')
        self.format=tk.StringVar(self,'PDF');self.full=tk.BooleanVar(self,False)
        self.only_calculated=tk.BooleanVar(self,True);self.selection_only=tk.BooleanVar(self,bool(self.selected_keys))
        for row,(label,var,choices) in enumerate([
            ('Piso',self.floor,['Todos os pisos']+sorted({c['floor'] for c in book.cases.values()})),
            ('Grupo',self.group,['Todos os grupos']+sorted(book.batch_settings['groups'])),
            ('Formato',self.format,['PDF','TXT','JSON'])],1):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',pady=8)
            ttk.Combobox(frame,textvariable=var,values=choices,state='readonly').grid(row=row,column=1,sticky='ew',padx=10)
        ttk.Checkbutton(frame,text='Apenas os pilares selecionados na lista',variable=self.selection_only,state='normal' if self.selected_keys else 'disabled').grid(row=4,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Checkbutton(frame,text='Apenas resultados calculados e atualizados',variable=self.only_calculated).grid(row=5,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Checkbutton(frame,text='PDF: memória detalhada de todas as combinações exportadas',variable=self.full).grid(row=6,column=0,columnspan=2,sticky='w',pady=8)
        FlowLabel(frame,text='Inclui resultados favoráveis e desfavoráveis. As ligações com combinações por resolver são identificadas como parciais. Desative o filtro de calculados para obter um mapa de acompanhamento com pendências. A exportação não inicia novos cálculos.',style='Muted.TLabel').grid(row=7,column=0,columnspan=2,sticky='ew',pady=10)
        self.count=tk.StringVar(self);ttk.Label(frame,textvariable=self.count).grid(row=8,column=0,columnspan=2,sticky='w',pady=8)
        self.export_button=ttk.Button(frame,text='Exportar…',command=self._apply,style='Primary.TButton');self.export_button.grid(row=9,column=1,sticky='e',pady=8)
        ttk.Button(frame,text='Cancelar',command=self.destroy).grid(row=10,column=1,sticky='e')
        for v in (self.floor,self.group,self.selection_only,self.only_calculated):v.trace_add('write',self._refresh)
        self._refresh()

    def _keys(self):
        from .batch_workflow import named_group
        selected=set(self.selected_keys) if self.selection_only.get() else set(self.book.cases)
        return [k for k,c in self.book.cases.items() if k in selected
                and (self.floor.get()=='Todos os pisos' or c['floor']==self.floor.get())
                and (self.group.get()=='Todos os grupos' or named_group(self.book,c)==self.group.get())]

    def _refresh(self,*_):
        from .collection_reports import is_calculated
        keys=self._keys();calculated=sum(is_calculated(cached_calculation(self.book.cases[k])) for k in keys)
        count=calculated if self.only_calculated.get() else len(keys)
        self.count.set(f'{calculated} combinações calculadas de {len(keys)} na seleção; {count} a exportar.')
        self.export_button.configure(state='normal' if count else 'disabled')

    def _apply(self):
        self.result={'keys':self._keys(),'format':self.format.get().lower(),'full':self.full.get(),'only_calculated':self.only_calculated.get()};self.destroy()
