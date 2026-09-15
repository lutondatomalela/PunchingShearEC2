# -*- coding: utf-8 -*-
"""Interface Tkinter: dados da execução, resultados e exportações consistentes."""
import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from punching.core import PuncoamentoEC2,number
from punching import geometry as geo
from punching.openings import normalize_openings,derive_openings,dimensions
from punching.version import VERSION
from punching.ui_app import DesktopUI
from punching.ui import COLORS
from punching.reports import export_pdf,export_xlsx,export_txt,export_json,sections,text_report
from punching.connection_ui import ConnectionUI,write_json_atomic
from punching.connections import case_from_payload
from copy import deepcopy
from punching.longitudinal import DEFAULTS as LONG_DEFAULTS, refresh_draft, draft_from_layout

DEFAULTS={
    'project':'','support':'','combination':'','laje_d':'0.20','laje_dx':'','laje_dy':'',
    'betão_fck':'30','aço_fyk':'500','aço_fywk':'500','pilar_tipo':'interior','pilar_forma':'retangular',
    'pilar_c1':'0.40','pilar_c2':'0.40','edge_distance_m':'0','V_Ed':'300','M_Edx':'0','M_Edy':'0','sigma_cp':'0',
    'gamma_C':'1.5','gamma_S':'1.15','beta_mode':'ec2','beta_manual':'','beta_reference':'','laje_As_lx_cm2pm':'10','laje_As_ly_cm2pm':'10',
    'interior_beta_method':'ec2_643','allow_biaxial_envelope':False,
    'is_sapata':False,'sigma_gd_kpa':'0','edge_perp_interior':True,'corner_interior':True,
    'simplified_applicable':False,'opening_sectors':'','openings':'[]','reinforcement_diameter_mm':'10',
    'reinforcement_sr_m':'','reinforcement_s0_m':'','cover_mm':'30','anchorage_confirmed':False,'aggregate_mm':'20',
    'footing_shape':'retangular','footing_bx':'','footing_by':'','footing_diameter':''}
DEFAULTS.update(LONG_DEFAULTS)

def _read_examples():
    """One catalogue supplies the GUI and the distributable JSON cases."""
    directory=Path(__file__).resolve().parent/'examples'
    catalog=json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
    examples={};descriptions={}
    for entry in catalog:
        values=json.loads((directory/entry['file']).read_text(encoding='utf-8'))
        converted={}
        for key,value in values.items():
            if key not in DEFAULTS:continue
            if key in ('V_Ed','M_Edx','M_Edy'):value=float(value)/1000
            if key=='opening_sectors':value=' | '.join(f'{a:g};{b:g}' for a,b in (value or []))
            if key=='openings':value=json.dumps(value or [],ensure_ascii=False)
            converted[key]=value if isinstance(value,bool) else ('' if value is None else str(value))
        if values.get('longitudinal_layout') is not None:converted.update(draft_from_layout(values['longitudinal_layout']))
        examples[entry['title']]=converted
        descriptions[entry['title']]=entry['description']
    return examples,descriptions


EXAMPLES,EXAMPLE_DESCRIPTIONS=_read_examples()


class PuncoamentoApp(ConnectionUI, DesktopUI, tk.Tk):
    def __init__(self):
        super().__init__(DEFAULTS, EXAMPLES, VERSION)

    @staticmethod
    def _parse_sectors(text):
        if not text.strip():return []
        pairs=[]
        for part in text.replace('\n','|').split('|'):
            bits=part.strip().split(';')
            if len(bits)!=2:raise ValueError('Setores: use início;fim, separados por |. Exemplo: -20;20 | 100;125.')
            pairs.append([number(x.replace(',','.'),'Ângulo') for x in bits])
        geo.sectors_normalized(pairs);return pairs

    def _collect_inputs(self):
        from punching.input_data import collect_inputs
        return collect_inputs(self._raw_draft(), DEFAULTS)

    def _opening_context(self):
        def num(key):return number(self.vars[key].get().replace(',','.'),key)
        shape=self.vars['pilar_forma'].get();c1=num('pilar_c1')
        return dict(c1=c1,c2=c1 if shape=='circular' else num('pilar_c2'),shape=shape,d=num('laje_d'),
                    position=self.vars['pilar_tipo'].get(),edge_distance=num('edge_distance_m'))

    def _edit_openings(self):
        try:
            if self.vars['is_sapata'].get():raise ValueError('O módulo de sapatas admite apenas casos sem aberturas.')
            self._update_derived();context=self._opening_context()
            items=normalize_openings(json.loads(self.vars['openings'].get() or '[]'))
            manual=self._parse_sectors(self.vars['opening_sectors'].get())
            from punching.opening_editor import OpeningEditor
            editor=OpeningEditor(self,items,context,manual)
            self.wait_window(editor)
            if editor.result is not None:self.vars['openings'].set(json.dumps(editor.result,ensure_ascii=False))
        except (ValueError,TypeError) as exc:messagebox.showerror('Definir aberturas',str(exc),parent=self)

    def _update_derived(self):
        if self.vars['long_mode'].get()=='automatic':
            try:
                draft, trace = refresh_draft(self._raw_draft())
                for key in ('laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm'):
                    if self.vars[key].get()!=draft[key]:self.vars[key].set(draft[key])
                labels=[]
                for axis in ('x','y'):
                    item=trace['axes'][axis]
                    labels.append(axis.upper()+': '+item['label']+((' = '+item['equivalent']) if item['equivalent'] else ''))
                if 'var_longitudinal' in self.__dict__:self.var_longitudinal.set('\n'.join(labels)+'\nAs e alturas úteis calculadas automaticamente.')
            except (ValueError,KeyError,TypeError) as exc:
                for key in ('laje_d','laje_dx','laje_dy','laje_As_lx_cm2pm','laje_As_ly_cm2pm'):
                    if self.vars[key].get():self.vars[key].set('')
                self.var_rho.set('Armadura automática: '+str(exc))
                if 'var_longitudinal' in self.__dict__:self.var_longitudinal.set(str(exc))
                return
        elif 'var_longitudinal' in self.__dict__:self.var_longitudinal.set('Modo manual: introduza d ou dx/dy e as áreas médias de armadura.')
        try:
            dx=self.vars['laje_dx'].get();dy=self.vars['laje_dy'].get()
            if dx and dy:
                d=(float(dx.replace(',','.'))+float(dy.replace(',','.')))/2
                if self.vars['long_mode'].get()!='automatic' and math.isfinite(d) and self.vars['laje_d'].get()!=f'{d:.6g}':self.vars['laje_d'].set(f'{d:.6g}')
            else:d=float(self.vars['laje_d'].get().replace(',','.'))
            ax=float(self.vars['laje_As_lx_cm2pm'].get().replace(',','.'));ay=float(self.vars['laje_As_ly_cm2pm'].get().replace(',','.'))
            ddx=float(dx.replace(',','.')) if dx else d;ddy=float(dy.replace(',','.')) if dy else d
            rho=min(.02,math.sqrt(ax*ay/(ddx*ddy))/10000)
            self.var_rho.set(f'Taxa média rho_l = {rho*100:.3f} %' if d>0 and math.isfinite(rho) else 'Taxa não calculada')
        except (ValueError,ZeroDivisionError):self.var_rho.set('Taxa não calculada: reveja d e as armaduras.')

    def _mark_dirty(self,*_):
        if self._loading:return
        case=self._current_connection()
        if case is not None:
            from punching.collection_workflow import invalidate
            if case['draft']!=self._raw_draft():invalidate(case)
        self._sync_origin()
        self.dirty=True;self.lbl_badge.configure(text='DADOS ALTERADOS',foreground='#956315')
        self._result_tools(False)
        for tree in (self.tree_summary,self.tree_steel):
            for item in tree.get_children():tree.delete(item)
        self._set_text(self.txt_output,'Dados alterados. Execute novamente o cálculo para atualizar a memória.')
        self._set_text(self.txt_diag,'')
        self.var_resultado.set('Execute novamente a verificação. As exportações ficam indisponíveis até ao novo cálculo.')
        self.var_steel.set('Dados alterados: recalcule para atualizar as fiadas.')
        if self._redraw_job is not None:self.after_cancel(self._redraw_job)
        self._redraw_job=self.after_idle(self._refresh)

    def _refresh(self):
        self._redraw_job=None;self._update_derived();self._sync_controls();self._draw_scheme()

    def calcular(self):
        if self.__dict__.get('_workflow_busy'):return
        case=self._current_connection()
        if case and case.get('automated') and self._book.active and not self.__dict__.get('_rendering_group_case'):
            self._calculate_active_group();return
        try:
            # Synchronize derived d before freezing this execution. A queued idle
            # redraw must not mark a freshly calculated result as out of date.
            self._update_derived()
            trace=self._connection_trace()
            inputs=self._collect_inputs();verif=PuncoamentoEC2(**inputs)
            report=verif.verificar_puncoamento();self.last_verif=verif;self._last_load_trace=deepcopy(trace);self.dirty=False
            if trace is not None:
                result=verif.snapshot();result['load_trace']=trace;report=text_report(result)
            self.last_report=report
            case=self._current_connection()
            if case is not None:
                from punching.collection_workflow import case_signature
                case['draft']=self._raw_draft();case['last_status']=verif.snapshot()['badge']
                snapshot=verif.snapshot();snapshot['load_trace']=deepcopy(trace)
                case['_calculation']={'floor':case['floor'],'support':case['support'],'combination':case['combination'],'status':snapshot['status'],'error':'','snapshot':snapshot}
                case['_calculation_hash']=case_signature(case)
            self._fill_summary(verif);self._set_text(self.txt_output,report)
            self._set_text(self.txt_diag,'\n\n'.join(verif.snapshot()['notes']))
            self._sync_controls();self._result_tools(True);self._result_cards(verif.snapshot())
            self._draw_scheme(verif);self.var_status.set('Verificação concluída. Consulte os resultados e a memória de cálculo.')
        except Exception as exc:
            self.last_verif=None;self.last_report='';self.dirty=True;self._last_load_trace=None
            self._result_tools(False)
            self.lbl_badge.configure(text='DADOS INVÁLIDOS',foreground='#b12732');self.var_resultado.set(str(exc))
            self._set_text(self.txt_output,'Cálculo não executado.\n'+str(exc));self._set_text(self.txt_diag,'')
            for item in self.tree_summary.get_children():self.tree_summary.delete(item)
            for item in self.tree_steel.get_children():self.tree_steel.delete(item)
            self.var_steel.set('Sem proposta: dados inválidos.')
            self.var_status.set('Corrija os dados para executar a verificação.')
            messagebox.showerror('Não foi possível calcular',str(exc),parent=self)

    @staticmethod
    def _set_text(widget,text):
        widget.configure(state='normal');widget.delete('1.0',tk.END);widget.insert(tk.END,text);widget.configure(state='disabled')

    def _fill_summary(self,verif):
        r=verif.snapshot();v=r['values']
        for item in self.tree_summary.get_children():self.tree_summary.delete(item)
        for name,key,unit in [('Beta','beta',''),('u0','u0','m'),('u1 geométrico','u1','m'),('u1 efetivo','u1_eff','m'),('u1*','u1_star','m'),('vRd,c','v_Rd_c','MPa'),('Limite com armadura','v_Rd_cs_max','MPa')]:
            value='Não calculado' if v[key] is None else f'{v[key]:.3f} {unit}'
            self.tree_summary.insert('',tk.END,values=(name,value),tags=('alternate',) if len(self.tree_summary.get_children())%2 else ())
        if r['inputs'].get('edge_distance_m',0)>0:
            self.tree_summary.insert('',tk.END,values=('Afastamento ao bordo',f"{r['inputs']['edge_distance_m']:.3f} m"))
            for c in r['contour_comparison']:
                name='Contorno fechado' if c['kind']=='fechado' else 'Contorno aberto ao bordo'
                desc=f"{c['effective_length']:.3f} m"
                if not c['admissible']:desc+=' | toca/ultrapassa bordo'
                elif c['selected']:desc+=' | mínimo adotado'
                self.tree_summary.insert('',tk.END,values=(name,desc))
        for c in r['checks']:
            self.tree_summary.insert('',tk.END,values=(c['name'],f"{'Verifica' if c['passed'] else 'Não verifica'} | {c['utilization']:.3f}"),tags=('pass' if c['passed'] else 'fail',))
        for c in r.get('detail_checks',[]):
            value='Não calculado' if c['value'] is None else f"{c['value']:.3f} {c['rule']} {c['limit']:.3f} {c['unit']}"
            if c['id'] in ('paths','families','radii'):value='Conferência das posições'
            self.tree_summary.insert('',tk.END,values=(c['name'],f"{'OK' if c['passed'] else 'Rever'} | {value}"))
        for item in self.tree_steel.get_children():self.tree_steel.delete(item)
        if r['reinforcement_rows']:
            rows=r['reinforcement_rows'];first=rows[0]
            self.var_steel.set(f"{len(rows)} fiadas | Ø{first['phi_mm']:.0f} | s0 = {first['r']:.3f} m | sr = {first['sr']:.3f} m\n{sum(x['n_legs'] for x in rows)} ramos verticais no total.")
            for row in rows:
                self.tree_steel.insert('',tk.END,values=(row['row'],f"{row['r']:.3f}",row['n_legs'],f"{row['Asw_m2']*1e4:.3f}",f"{row['st']:.3f}",'OK' if row['passed'] else 'Rever'))
        else:self.var_steel.set('Sem armadura específica necessária.' if r['status']=='PASS_WITHOUT' else 'Não foi obtida uma distribuição de ramos.')
        color='#16734a' if r['status'] in ('PASS_WITH','PASS_WITHOUT') else ('#956315' if r['status'] in ('BETA_PENDING','DETAIL_PENDING','EDGE_DETAIL_PENDING') else '#b12732')
        self.var_resultado.set(r['conclusion']);self.lbl_badge.configure(text=r['badge'],foreground=color)

    def _fresh_result(self):
        if self.last_verif is None or self.dirty:
            messagebox.showinfo('Resultado indisponível','Execute o cálculo com os dados atuais antes de exportar ou copiar.',parent=self);return None
        r=self.last_verif.snapshot()
        if self.__dict__.get('_last_load_trace') is not None:r['load_trace']=deepcopy(self._last_load_trace)
        return r

    def _export(self,kind):
        r=self._fresh_result()
        if r is None:return
        target=filedialog.asksaveasfilename(parent=self,defaultextension='.'+kind,filetypes=[(kind.upper(),'*.'+kind)],initialfile='Puncoamento_'+kind+'.'+kind)
        if not target:return
        try:
            {'pdf':export_pdf,'xlsx':export_xlsx,'txt':export_txt,'json':export_json}[kind](r,target)
            self.var_status.set('Relatório exportado: '+Path(target).name)
        except Exception as exc:messagebox.showerror('Exportação',str(exc)+'\nVerifique a instalação de requirements.txt.',parent=self)

    def guardar_relatorio_pdf(self):self._export('pdf')
    def guardar_relatorio_xlsx(self):self._export('xlsx')
    def guardar_relatorio_txt(self):self._export('txt')
    def _build_professional_report_sections(self,emitted_at=None):
        r=self._fresh_result()
        if r is None:raise ValueError('Não existe resultado atualizado para exportar.')
        return sections(r)

    def _create_pdf(self,filepath,content=None):
        r=self._fresh_result()
        if r is None:raise ValueError('Não existe resultado atualizado para exportar.')
        export_pdf(r,filepath)

    def copiar_relatorio(self):
        if self._fresh_result() is not None:
            self.clipboard_clear();self.clipboard_append(self.last_report);self.var_status.set('Memória copiada.')

    def guardar_caso(self):
        try:
            p=self._collect_inputs();PuncoamentoEC2(**p)
            case=self._current_connection()
            if case is not None:
                self._commit_connection();p={'schema':'PunchingShearEC2.case/1','inputs':p,'import_case':deepcopy(case)}
        except Exception as exc:messagebox.showerror('Guardar caso',str(exc),parent=self);return
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.json',filetypes=[('Caso JSON','*.json')])
        if path:
            try:
                write_json_atomic(path,p)
                self.var_status.set('Caso guardado: '+Path(path).name)
            except OSError as exc:messagebox.showerror('Guardar caso',str(exc),parent=self)

    def abrir_caso(self):
        path=filedialog.askopenfilename(parent=self,filetypes=[('Caso JSON','*.json')])
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
            imported=case_from_payload(data,DEFAULTS)
            if 'inputs' in data:data=data['inputs']
            PuncoamentoEC2(**data)
            if data.get('laje_rho_l') is not None and data.get('laje_As_lx_cm2pm') is None:
                raise ValueError('Este caso usa rho diretamente. Execute-o pela API/CLI ou introduza as áreas de armadura na interface.')
            self.limpar();self._loading=True
            self._standalone_case=deepcopy(imported)
            for k,v in draft_from_layout(data.get('longitudinal_layout')).items():self.vars[k].set(v)
            for k,v in data.items():
                if k not in self.vars:continue
                if k in ('V_Ed','M_Edx','M_Edy'):v=float(v)/1000
                if k=='opening_sectors':v=' | '.join(f'{a:g};{b:g}' for a,b in (v or []))
                if k=='openings':v=json.dumps(v or [],ensure_ascii=False)
                self.vars[k].set(v if v is not None else '')
        except Exception as exc:messagebox.showerror('Abrir caso',str(exc),parent=self)
        finally:self._loading=False;self._mark_dirty();self._sync_origin()

    def limpar(self):
        self._detach_connection()
        self._loading=True
        for k,v in DEFAULTS.items():self.vars[k].set(v)
        self.last_verif=None;self.last_report='';self.dirty=True;self._loading=False
        self._set_text(self.txt_output,'');self._set_text(self.txt_diag,'')
        for item in self.tree_summary.get_children():self.tree_summary.delete(item)
        for item in self.tree_steel.get_children():self.tree_steel.delete(item)
        self.var_steel.set('Execute a verificação para obter as fiadas.')
        self.lbl_badge.configure(text='NÃO CALCULADO',foreground='#526773');self.var_resultado.set('Aguardando cálculo')
        self._result_tools(False);self._sync_controls()
        self._update_derived();self._draw_scheme();self.var_status.set('Novo caso. Introduza os dados ou carregue um exemplo.')

    def carregar_exemplo(self):
        self.limpar();self._loading=True
        for k,v in EXAMPLES[self.var_exemplo.get()].items():self.vars[k].set(v)
        self._loading=False;self._mark_dirty();self.var_status.set(EXAMPLE_DESCRIPTIONS[self.var_exemplo.get()]+' Execute a verificação.')

    def _draw_scheme(self,verif=None):
        if not hasattr(self,'canvas_scheme'):return
        cv=self.canvas_scheme;cv.delete('all');w=cv.winfo_width();h=cv.winfo_height()
        if w<160 or h<150:
            self._transform=None
            if w>40:cv.create_text(w/2,h/2,text='Aumente o painel para ver a planta.',width=max(40,w-20),fill=COLORS['muted'])
            return
        try:
            if not self.dirty and self.last_verif is not None:
                result=self.last_verif.snapshot();g=result['geometry'];rows=result['reinforcement_rows']
            else:
                c1=number(self.vars['pilar_c1'].get().replace(',','.'),'c1',.01,20)
                shape=self.vars['pilar_forma'].get();c2=c1 if shape=='circular' else number(self.vars['pilar_c2'].get().replace(',','.'),'c2',.01,20)
                d=number(self.vars['laje_d'].get().replace(',','.'),'d',.01,5);pos=self.vars['pilar_tipo'].get()
                gap=number(self.vars['edge_distance_m'].get().replace(',','.'),'g (m)',0,100)
                if gap>0 and (pos!='bordo' or shape!='retangular'):
                    raise ValueError('Afastamento ao bordo: selecione pilar retangular de bordo.')
                _,opening_records,automatic=derive_openings(json.loads(self.vars['openings'].get() or '[]'),**self._opening_context())
                sectors=geo.sectors_normalized(self._parse_sectors(self.vars['opening_sectors'].get())+automatic)
                seg=geo.select_edge_contour(c1,c2,2*d,gap,sectors)[0]['segments'] if gap>0 else geo.trim_sectors(geo.contour(c1,c2,shape,pos,2*d,d),sectors)
                g={'column':{'c1':c1,'c2':c2,'shape':shape,'position':pos,'edge_distance_m':gap},'u1':geo.polylines(seg),'openings':opening_records};rows=[]
            c=g['column'];layers=[('u0','#7442a3'),('u1','#c53030'),('u1_star','#ad741c'),('u_out','#19835b'),('governing','#176eaa')]
            pts=[p for key,_ in layers for path in g.get(key,[]) for p in path]+[(-c['c1']/2,-c['c2']/2),(c['c1']/2,c['c2']/2)]
            for opening in g.get('openings',[]):pts.extend(opening['outline']+opening['equivalent_outline'])
            if c['position']=='bordo':pts.append((0,-c['c2']/2-c.get('edge_distance_m',0)))
            if g.get('footing'):
                f=g['footing'];pts.extend([(-f['bx']/2,-f['by']/2),(f['bx']/2,f['by']/2)])
            xmin=min(x for x,y in pts);xmax=max(x for x,y in pts);ymin=min(y for x,y in pts);ymax=max(y for x,y in pts)
            scale=min((w-90)/max(xmax-xmin,.1),(h-85)/max(ymax-ymin,.1))
            ox=w/2-(xmin+xmax)/2*scale;oy=(h-30)/2+(ymin+ymax)/2*scale
            def pt(x,y):return ox+x*scale,oy-y*scale
            if self.drag_mode and getattr(self,'_drag_transform',None):ox,oy,scale=self._drag_transform
            self._transform=(ox,oy,scale)
            if g.get('footing'):
                f=g['footing'];coords=(*pt(-f['bx']/2,f['by']/2),*pt(f['bx']/2,-f['by']/2))
                (cv.create_oval if f['shape']=='circular' else cv.create_rectangle)(*coords,outline='#9cabb4')
            if c['position'] in ('bordo','canto'):
                gap=c.get('edge_distance_m',0)
                yy=pt(0,-c['c2']/2-gap)[1];cv.create_line(12,yy,w-12,yy,fill='#7c858b',width=2)
                if gap>0:
                    x,y=pt(0,-c['c2']/2)
                    cv.create_line(x,y,x,yy,fill='#176eaa',arrow='both')
                    cv.create_text(x+9,(y+yy)/2,anchor='w',text=f'g = {gap:.3f} m',fill='#176eaa',font=('Segoe UI',10))
            if c['position']=='canto':
                xx=pt(-c['c1']/2,0)[0];cv.create_line(xx,10,xx,h-45,fill='#7c858b',width=2)
            coords=(*pt(-c['c1']/2,c['c2']/2),*pt(c['c1']/2,-c['c2']/2))
            (cv.create_oval if c['shape']=='circular' else cv.create_rectangle)(*coords,fill='#e1ebf0',outline='#173c4b',width=2)
            for key,color in layers:
                for path in g.get(key,[]):cv.create_line(*[z for x,y in path for z in pt(x,y)],fill=color,width=2)
            for opening in g.get('openings',[]):
                for end in opening['tangent_points']:cv.create_line(*pt(0,0),*pt(*end),fill='#bd8b49',dash=(4,4))
                eq=opening['equivalent_outline']
                if eq:cv.create_line(*[v for p in eq for v in pt(*p)],fill='#a35d05',dash=(3,3))
                ow,oh=dimensions(opening);x,y=opening['x'],opening['y'];box=(*pt(x-ow/2,y+oh/2),*pt(x+ow/2,y-oh/2))
                (cv.create_oval if opening['shape']=='circular' else cv.create_rectangle)(*box,fill='#fff3df' if opening['active'] else '#f0f2f4',outline='#a35d05' if opening['active'] else '#697781',width=2)
                cv.create_text(*pt(x,y),text=opening['id'] if len(opening['id'])<=12 else opening['id'][:9]+'...',fill='#173c4b')
            for row in rows:
                for x,y in row['coordinates']:
                    xx,yy=pt(x,y);cv.create_oval(xx-2,yy-2,xx+2,yy+2,fill='#173c4b',outline='')
            handles=[(c['c1']/2,0,'c1'),(0,c['c2']/2,'c2')] if self.var_edit_column.get() else []
            for x,y,key in handles:
                if key=='c2' and c['shape']=='circular':continue
                xx,yy=pt(x,y);cv.create_oval(xx-5,yy-5,xx+5,yy+5,fill='#2563eb',outline='white',tags=('handle_'+key,))
            cv.create_text(12,h-32,anchor='w',text='u0 roxo | u1 vermelho | u1* ocre | u_out verde',font=('Segoe UI',9),fill='#526773')
            cv.create_text(w-15,15,anchor='ne',text='+X →  +Y ↑',font=('Segoe UI',10))
        except (ValueError,KeyError,TypeError) as exc:cv.create_text(18,30,anchor='nw',text=str(exc),width=w-36,fill='#956315',font=('Segoe UI',10))

    def _on_canvas_press(self,event):
        self.drag_mode=None
        if not self.var_edit_column.get():return
        items=self.canvas_scheme.find_overlapping(event.x-7,event.y-7,event.x+7,event.y+7)
        for item in reversed(items):
            tags=self.canvas_scheme.gettags(item)
            if 'handle_c1' in tags:self.drag_mode='c1';break
            if 'handle_c2' in tags:self.drag_mode='c2';break
        if self.drag_mode:self._drag_transform=self._transform

    def _on_canvas_drag(self,event):
        if not self.var_edit_column.get() or self.drag_mode is None or not getattr(self,'_transform',None):return
        ox,oy,scale=self._transform
        value=2*abs((event.x-ox) if self.drag_mode=='c1' else (oy-event.y))/scale
        self.vars['pilar_'+self.drag_mode].set(f'{max(.05,min(10.,value)):.3f}')

    def _mousewheel(self,event):
        widget=self.winfo_containing(event.x_root,event.y_root)
        for tab in self.scroll_tabs:
            if widget is not None and str(widget).startswith(str(tab)):
                num=getattr(event,'num',None);delta=getattr(event,'delta',0)
                step=(-1 if num==4 else 1) if num in (4,5) else (-1 if delta>0 else 1) if delta else 0
                if step:tab.canvas.yview_scroll(step*max(1,int(abs(delta)/120)),'units')
                return 'break'


def main():
    app=PuncoamentoApp();app.mainloop()


if __name__=='__main__':main()
