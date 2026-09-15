"""Editor transacional de aberturas: planta, medidas e arrastamento."""
import copy
import math
import tkinter as tk
from tkinter import ttk
from .ui import COLORS,FlowLabel
from . import geometry as geo
from .openings import normalize_openings,derive_openings,outline,dimensions,point_clearance,placed_opening,dragged_opening


class OpeningEditor(tk.Toplevel):
    def __init__(self,parent,openings,context,manual_sectors=()):
        super().__init__(parent);self.title('Aberturas na laje');self.transient(parent);self.configure(bg=COLORS['surface'])
        self.geometry(f'{min(1120,self.winfo_screenwidth()-50)}x{min(810,self.winfo_screenheight()-70)}');self.minsize(850,580)
        self.context=dict(context);self.manual_sectors=list(manual_sectors)
        self.items=normalize_openings(copy.deepcopy(openings));self.result=None;self.selected=None
        self._loading=False;self._selecting=False;self._form_dirty=False;self._drag=None;self._drawing=False;self._new_start=None;self._transform=None
        self.columnconfigure(0,weight=1);self.rowconfigure(1,weight=1)
        head=ttk.Frame(self,padding=(18,14));head.grid(row=0,column=0,sticky='ew');head.columnconfigure(0,weight=1)
        ttk.Label(head,text='Aberturas na laje',font=('Segoe UI',16,'bold')).grid(row=0,column=0,sticky='w')
        FlowLabel(head,text='Desenhe ou introduza medidas exatas. Arraste para mover; use a pega azul para redimensionar.\nOrigem no centro do pilar · coordenadas em metros · ajuste do rato a 1 cm.',style='Muted.TLabel').grid(row=1,column=0,sticky='ew',pady=(6,0))
        pane=ttk.Panedwindow(self,orient='horizontal');pane.grid(row=1,column=0,sticky='nsew',padx=10)
        left=ttk.Frame(pane,width=335);left.rowconfigure(0,weight=1);left.columnconfigure(0,weight=1);pane.add(left,weight=0)
        # Scrollable controls keep exact measurements accessible on small screens.
        sc=tk.Canvas(left,width=330,highlightthickness=0,bg=COLORS['surface']);sc.grid(row=0,column=0,sticky='nsew')
        sb=ttk.Scrollbar(left,orient='vertical',command=sc.yview);sb.grid(row=0,column=1,sticky='ns');sc.configure(yscrollcommand=sb.set)
        def wheel(event):
            if str(event.widget).startswith(str(sc)):
                delta=(-1 if event.num==4 else 1) if getattr(event,'num',None) in (4,5) else int(-event.delta/120)
                sc.yview_scroll(delta,'units');return 'break'
        self.bind('<MouseWheel>',wheel);self.bind('<Button-4>',wheel);self.bind('<Button-5>',wheel)
        body=ttk.Frame(sc,padding=5);body.columnconfigure(1,weight=1);win=sc.create_window(0,0,window=body,anchor='nw')
        body.bind('<Configure>',lambda e:sc.configure(scrollregion=sc.bbox('all')));sc.bind('<Configure>',lambda e:sc.itemconfigure(win,width=e.width))
        self.tree=ttk.Treeview(body,columns=('shape',),show='tree headings',height=5,selectmode='browse')
        self.tree.heading('#0',text='Abertura');self.tree.heading('shape',text='Forma');self.tree.column('#0',width=95);self.tree.column('shape',width=115)
        self.tree.grid(row=0,column=0,columnspan=2,sticky='ew');self.tree.bind('<<TreeviewSelect>>',self._tree_select)
        actions=ttk.Frame(body);actions.grid(row=1,column=0,columnspan=2,sticky='ew',pady=5)
        for label,fn in [('Retângulo',lambda:self._add('rectangular')),('Círculo',lambda:self._add('circular')),('Eliminar',self._delete)]:ttk.Button(actions,text=label,command=fn).pack(side='left',padx=1)
        self.fields={k:tk.StringVar(self,value=v) for k,v in dict(id='',shape='Retangular',x='0',y='0',width='.4',height='.4',diameter='.4').items()}
        self.widgets={}
        for row,(key,label) in enumerate([('id','Identificação'),('shape','Forma'),('x','Centro X (m)'),('y','Centro Y (m)'),('width','Dimensão X (m)'),('height','Dimensão Y (m)'),('diameter','Diâmetro (m)')],2):
            ttk.Label(body,text=label).grid(row=row,column=0,sticky='w',pady=4)
            w=ttk.Combobox(body,textvariable=self.fields[key],values=['Retangular','Circular'],state='readonly',width=13) if key=='shape' else ttk.Entry(body,textvariable=self.fields[key],width=14)
            if key=='shape':
                for event in ('<MouseWheel>','<Button-4>','<Button-5>'):w.bind(event,wheel)
            w.grid(row=row,column=1,sticky='ew',padx=4);w.bind('<Return>',lambda e:self._apply_fields());self.widgets[key]=w
        for var in self.fields.values():var.trace_add('write',self._field_changed)
        ttk.Button(body,text='Aplicar medidas',command=self._apply_fields).grid(row=9,column=0,columnspan=2,sticky='ew',pady=6)
        ttk.Separator(body).grid(row=10,column=0,columnspan=2,sticky='ew',pady=8)
        ttk.Label(body,text='Posição pela distância livre à face',wraplength=255).grid(row=11,column=0,columnspan=2,sticky='w')
        self.side=tk.StringVar(self,value='+Y' if context['position'] in ('bordo','canto') else '+X');self.gap=tk.StringVar(self,value='0.60')
        ttk.Label(body,text='Face do pilar').grid(row=12,column=0,sticky='w',pady=5)
        side_combo=ttk.Combobox(body,textvariable=self.side,values=['+X','-X','+Y','-Y'],state='readonly',width=12)
        side_combo.grid(row=12,column=1,sticky='ew',padx=4)
        for event in ('<MouseWheel>','<Button-4>','<Button-5>'):side_combo.bind(event,wheel)
        ttk.Label(body,text='Distância livre (m)').grid(row=13,column=0,sticky='w',pady=5)
        ttk.Entry(body,textvariable=self.gap,width=14).grid(row=13,column=1,sticky='ew',padx=4)
        ttk.Button(body,text='Posicionar na face escolhida',command=self._place).grid(row=14,column=0,columnspan=2,sticky='ew',pady=6)
        ttk.Label(body,text='As medidas de posição são exatas. Não é necessário introduzir ângulos. Os setores manuais existentes mantêm-se como adicionais.',wraplength=255).grid(row=15,column=0,columnspan=2,sticky='w',pady=8)
        right=ttk.Frame(pane);right.rowconfigure(1,weight=1);right.columnconfigure(0,weight=1);pane.add(right,weight=1)
        toolbar=ttk.Frame(right);toolbar.grid(row=0,column=0,sticky='ew')
        ttk.Button(toolbar,text='Desenhar retângulo',command=self._begin_drawing).pack(side='left',padx=3,pady=4)
        ttk.Button(toolbar,text='Enquadrar',command=lambda:self._draw(fit=True)).pack(side='left',padx=3)
        self.canvas=tk.Canvas(right,bg='white',highlightthickness=1,highlightbackground='#cbd5dd',width=520,height=430)
        self.canvas.grid(row=1,column=0,sticky='nsew');self.canvas.bind('<Configure>',lambda e:self._draw(fit=True))
        self.canvas.bind('<Button-1>',self._press);self.canvas.bind('<B1-Motion>',self._motion);self.canvas.bind('<ButtonRelease-1>',self._release)
        self.status=tk.StringVar(self);self.sector_text=tk.StringVar(self)
        self.status_label=ttk.Label(right,textvariable=self.status,wraplength=600);self.status_label.grid(row=2,column=0,sticky='ew',padx=6,pady=6)
        ttk.Label(right,text='Setores automáticos (graus):').grid(row=3,column=0,sticky='w',padx=6)
        ttk.Entry(right,textvariable=self.sector_text,state='readonly').grid(row=4,column=0,sticky='ew',padx=6,pady=(0,6))
        bottom=ttk.Frame(self,padding=10);bottom.grid(row=2,column=0,sticky='ew');bottom.columnconfigure(0,weight=1)
        FlowLabel(bottom,text='O método e a fundamentação de β são definidos em «Método β» no caso.',style='Muted.TLabel').grid(row=0,column=0,sticky='ew')
        ttk.Button(bottom,text='Cancelar',command=self.destroy).grid(row=0,column=1,padx=5)
        self.ok=ttk.Button(bottom,text='Aplicar ao caso',command=self._save,style='Primary.TButton');self.ok.grid(row=0,column=2)
        self.bind('<Escape>',lambda e:self._escape());self.protocol('WM_DELETE_WINDOW',self.destroy)
        self._refresh_list();self.after_idle(lambda:self._select(self.items[0]['id'] if self.items else None));self.grab_set()

    def _field_changed(self,*_):
        if not self._loading:
            self._form_dirty=True
            self._field_states()

    def _field_states(self):
        for key,widget in self.widgets.items():
            enabled=self.selected is not None
            if key in ('width','height'):enabled=enabled and self.fields['shape'].get()=='Retangular'
            if key=='diameter':enabled=enabled and self.fields['shape'].get()=='Circular'
            widget.configure(state=('readonly' if key=='shape' else 'normal') if enabled else 'disabled')

    @staticmethod
    def _float(text):
        value=float(text.replace(',','.'))
        if not math.isfinite(value):raise ValueError('As medidas têm de ser finitas.')
        return value

    def _error(self,message):
        self.status.set(str(message));self.status_label.configure(foreground='#b12732')

    def _current(self):return next((o for o in self.items if o['id']==self.selected),None)

    def _read_form(self):
        shape='circular' if self.fields['shape'].get()=='Circular' else 'rectangular'
        item=dict(id=self.fields['id'].get(),shape=shape,x=self._float(self.fields['x'].get()),y=self._float(self.fields['y'].get()))
        for k in (('diameter',) if shape=='circular' else ('width','height')):item[k]=self._float(self.fields[k].get())
        return item

    def _apply_fields(self):
        if not self._form_dirty or self.selected is None:return True
        try:
            item=self._read_form();candidate=[item if o['id']==self.selected else o for o in self.items]
            self.items=normalize_openings(candidate);self.selected=item['id'].strip();self._form_dirty=False
            self._refresh_list();self._load_fields();self._draw(fit=True);return True
        except (ValueError,TypeError) as exc:self._error(exc);return False

    def _refresh_list(self):
        self._selecting=True
        for item in self.tree.get_children():self.tree.delete(item)
        for o in self.items:self.tree.insert('',tk.END,iid=o['id'],text=o['id'],values=('Circular' if o['shape']=='circular' else 'Retangular',))
        if self.selected and self.tree.exists(self.selected):self.tree.selection_set(self.selected)
        self._selecting=False

    def _load_fields(self):
        o=self._current();self._loading=True
        if o:
            w,h=dimensions(o)
            data=dict(id=o['id'],shape='Circular' if o['shape']=='circular' else 'Retangular',x=o['x'],y=o['y'],width=w,height=h,diameter=w)
            for k,v in data.items():self.fields[k].set(f'{v:.9g}' if isinstance(v,(int,float)) else v)
        self._form_dirty=False;self._loading=False
        self._field_states()

    def _select(self,identifier):
        self.selected=identifier;self._refresh_list();self._load_fields();self._draw(fit=True)

    def _tree_select(self,event=None):
        if self._selecting:return
        values=self.tree.selection()
        if not values or values[0]==self.selected:return
        new=values[0]
        if self._apply_fields():self._select(new)

    def _next_id(self):
        ids={o['id'].casefold() for o in self.items};i=1
        while f'a{i}' in ids:i+=1
        return f'A{i}'

    def _add(self,shape):
        if not self._apply_fields():return
        try:
            c=self.context
            item=placed_opening(self._next_id(),shape,self.side.get(),self._float(self.gap.get()),c['c1'],c['c2'])
            # A new default at a corner must start inside both free edges.
            # Exact face placement remains available separately in _place.
            if c['position']=='canto' and self.side.get()=='+Y':
                item['x']=max(item['x'],-c['c1']/2+dimensions(item)[0]/2+.10)
            # Offset subsequent defaults along the same face, avoiding exact duplicates.
            while any(math.hypot(item['x']-o['x'],item['y']-o['y'])<.41 for o in self.items):
                item['y' if self.side.get().endswith('X') else 'x']+=.5
            self.items=normalize_openings(self.items+[item]);self._select(item['id'])
        except ValueError as exc:self._error(exc)

    def _delete(self):
        if self.selected is None:return
        self.items=[o for o in self.items if o['id']!=self.selected];self._form_dirty=False
        self._select(self.items[0]['id'] if self.items else None)

    def _place(self):
        if not self._apply_fields():return
        o=self._current()
        if o is None:self._error('Selecione ou adicione uma abertura.');return
        try:
            c=self.context;w,h=dimensions(o)
            item=placed_opening(o['id'],o['shape'],self.side.get(),self._float(self.gap.get()),c['c1'],c['c2'],w,h,w)
            self.items=[item if x['id']==self.selected else x for x in self.items];self._load_fields();self._draw(fit=True)
        except ValueError as exc:self._error(exc)

    def _begin_drawing(self):
        if not self._apply_fields():return
        self._drawing=True;self._new_start=None;self.canvas.configure(cursor='crosshair')
        self.status.set('Clique num canto da abertura e arraste até ao canto oposto. Escape cancela o desenho.');self.status_label.configure(foreground='#173c4b')

    def _escape(self):
        if self._drawing:self._drawing=False;self._new_start=None;self.canvas.configure(cursor='');self._draw()
        else:self.destroy()

    def _world(self,x,y):
        ox,oy,s=self._transform;return (x-ox)/s,(oy-y)/s

    def _pixel(self,x,y):
        ox,oy,s=self._transform;return ox+x*s,oy-y*s

    def _press(self,event):
        if not self._apply_fields() or not self._transform:return
        p=self._world(event.x,event.y)
        if self._drawing:self._new_start=p;return
        o=self._current()
        if o:
            w,h=dimensions(o);handle=(o['x']+w/2,o['y']+(h/2 if o['shape']=='rectangular' else 0))
            if math.dist(self._pixel(*handle),(event.x,event.y))<=10:
                self._drag=(copy.deepcopy(o),'resize',p);return
        o=next((o for o in reversed(self.items) if point_clearance(*p,o)<=0),None)
        if o:
            self.selected=o['id'];self._refresh_list();self._load_fields();self._drag=(copy.deepcopy(o),'move',p);self._draw()

    def _motion(self,event):
        if not self._transform:return
        p=self._world(event.x,event.y)
        if self._drawing and self._new_start:
            self.canvas.delete('new_opening');a=self._pixel(*self._new_start);b=self._pixel(*p)
            self.canvas.create_rectangle(*a,*b,outline='#176eaa',dash=(4,3),width=2,tags='new_opening');return
        if self._drag:
            original,mode,start=self._drag
            try:
                changed=dragged_opening(original,mode,start,p)
                self.items=[changed if o['id']==original['id'] else o for o in self.items]
                self._load_fields();self._draw()
            except ValueError as exc:self._error(exc)

    def _release(self,event):
        if self._drawing and self._new_start:
            x0,y0=self._new_start;x1,y1=self._world(event.x,event.y)
            if abs(x1-x0)>=.01 and abs(y1-y0)>=.01:
                item=dict(id=self._next_id(),shape='rectangular',x=round((x0+x1)/2,2),y=round((y0+y1)/2,2),width=max(.01,round(abs(x1-x0),2)),height=max(.01,round(abs(y1-y0),2)))
                try:self.items=normalize_openings(self.items+[item]);self.selected=item['id'];self._refresh_list();self._load_fields()
                except ValueError as exc:self._error(exc)
            self._drawing=False;self._new_start=None;self.canvas.configure(cursor='')
        self._drag=None;self._draw(fit=True)

    def _draw(self,fit=False):
        if not hasattr(self,'canvas'):return
        cv=self.canvas;cv.delete('all');w=cv.winfo_width();h=cv.winfo_height();c=self.context
        if w<160 or h<150:
            self._transform=None
            if w>40:cv.create_text(w/2,h/2,text='Aumente o painel para ver a planta.',width=max(40,w-20),fill=COLORS['muted'])
            return
        records=[];error=None;sectors=[];effective=[]
        try:
            _,records,sectors=derive_openings(self.items,**c)
            normalized=geo.sectors_normalized(self.manual_sectors+sectors)
            if c['edge_distance']>0:
                raw=geo.select_edge_contour(c['c1'],c['c2'],2*c['d'],c['edge_distance'],[])[0]['segments']
                effective=geo.polylines(geo.select_edge_contour(c['c1'],c['c2'],2*c['d'],c['edge_distance'],normalized)[0]['segments'])
            else:
                raw=geo.contour(c['c1'],c['c2'],c['shape'],c['position'],2*c['d'],c['d'])
                effective=geo.polylines(geo.trim_sectors(raw,normalized))
        except ValueError as exc:error=str(exc);raw=[]
        self.sector_text.set(' | '.join(f'{a:.5f};{b:.5f}' for a,b in sectors))
        self.ok.configure(state='disabled' if error else 'normal')
        pts=[(-c['c1']/2-2*c['d'],-c['c2']/2-2*c['d']),(c['c1']/2+2*c['d'],c['c2']/2+2*c['d'])]
        for o in self.items:pts.extend(outline(o))
        for o in records:pts.extend(o['equivalent_outline'])
        if c['position'] in ('bordo','canto'):pts.append((0,-c['c2']/2-c['edge_distance']))
        if fit or self._transform is None:
            xmin=min(x for x,y in pts);xmax=max(x for x,y in pts);ymin=min(y for x,y in pts);ymax=max(y for x,y in pts)
            scale=min((w-100)/max(xmax-xmin,.5),(h-100)/max(ymax-ymin,.5))
            self._transform=(w/2-scale*(xmin+xmax)/2,h/2+scale*(ymin+ymax)/2,scale)
        def line(path,**kw):
            if len(path)>1:cv.create_line(*[v for p in path for v in self._pixel(*p)],**kw)
        ox,oy,scale=self._transform
        cv.create_line(20,oy,w-20,oy,fill='#d1d9df',arrow='last');cv.create_line(ox,h-25,ox,20,fill='#d1d9df',arrow='last')
        cv.create_text(w-28,oy-12,text='+X',fill='#173c4b');cv.create_text(ox+15,22,text='+Y',fill='#173c4b')
        if c['position'] in ('bordo','canto'):
            yy=self._pixel(0,-c['c2']/2-c['edge_distance'])[1];cv.create_line(10,yy,w-10,yy,fill='#697781',width=2)
        if c['position']=='canto':
            xx=self._pixel(-c['c1']/2,0)[0];cv.create_line(xx,10,xx,h-10,fill='#697781',width=2)
        box=(*self._pixel(-c['c1']/2,c['c2']/2),*self._pixel(c['c1']/2,-c['c2']/2))
        (cv.create_oval if c['shape']=='circular' else cv.create_rectangle)(*box,fill='#e3ebf0',outline='#173c4b',width=2)
        cv.create_text(ox,oy,text='Pilar',fill='#173c4b')
        for path in geo.polylines(raw):line(path,fill='#b8c2ca',dash=(3,3))
        for path in effective:line(path,fill='#c53030',width=2)
        by_id={r['id']:r for r in records}
        for o in self.items:
            record=by_id.get(o['id']);active=record and record['active'];color='#a35d05' if active else '#697781'
            if record:
                line(record['equivalent_outline'],fill='#a35d05',dash=(3,3))
                if active:
                    for end in record['tangent_points']:line([(0,0),end],fill='#bd8b49',dash=(4,4))
            ow,oh=dimensions(o);box=(*self._pixel(o['x']-ow/2,o['y']+oh/2),*self._pixel(o['x']+ow/2,o['y']-oh/2))
            (cv.create_oval if o['shape']=='circular' else cv.create_rectangle)(*box,fill='#fff3df' if active else '#f0f2f4',outline=color,width=2)
            cv.create_text(*self._pixel(o['x'],o['y']),text=o['id'] if len(o['id'])<=12 else o['id'][:9]+'...',fill='#173c4b')
            if o['id']==self.selected:
                x,y=self._pixel(o['x']+ow/2,o['y']+(oh/2 if o['shape']=='rectangular' else 0));cv.create_rectangle(x-5,y-5,x+5,y+5,fill='#2875ce',outline='white')
        cv.create_text(12,h-40,text='u1 eficaz: vermelho | contorno sem aberturas: tracejado | aberturas: áreas preenchidas',anchor='nw',width=w-24,fill='#526773',font=('Segoe UI',9))
        if error:self._error(error)
        else:
            self.status_label.configure(foreground='#173c4b');record=by_id.get(self.selected)
            if record:
                msg=f"{record['id']}: distância livre = {record['distance_m']:.3f} m; 6d = {record['limit_6d_m']:.3f} m. "+record['method']
                if record['active']:msg+=' Setor considerado no cálculo.'
                self.status.set(msg)
            else:self.status.set('Adicione uma abertura ou desenhe um retângulo na planta.')
        self.status_label.configure(wraplength=max(300,w-20))

    def _save(self):
        if not self._apply_fields():return
        try:
            normalized,_,sectors=derive_openings(self.items,**self.context)
            geo.sectors_normalized(self.manual_sectors+sectors)
            self.result=copy.deepcopy(normalized);self.destroy()
        except ValueError as exc:self._error(exc)
