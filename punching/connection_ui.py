"""Application integration, isolated from the numerical verification engine."""
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
import tempfile
from tkinter import filedialog, messagebox
from .connections import ConnectionBook, initial_draft, provenance


def write_json_atomic(path, payload):
    path = Path(path)
    contents = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, prefix=path.name+'.', suffix='.tmp', delete=False) as f:
            tmp = Path(f.name); f.write(contents); f.flush(); os.fsync(f.fileno())
        tmp.replace(path)
    finally:
        if tmp is not None and tmp.exists(): tmp.unlink()


class ConnectionUI:
    def _ensure_book(self):
        if '_book' not in self.__dict__: self._book = ConnectionBook()
        if '_standalone_case' not in self.__dict__: self._standalone_case = None

    def _current_connection(self):
        self._ensure_book()
        return self._book.cases.get(self._book.active) if self._book.active else self._standalone_case

    def _raw_draft(self): return {k: v.get() for k, v in self.vars.items()}

    def _commit_connection(self):
        case = self._current_connection()
        if case is not None:
            from .collection_workflow import sync_joint, invalidate
            from Punching_EC2_GUI import DEFAULTS
            draft = self._raw_draft()
            if self._book.active: sync_joint(self._book, self._book.active, draft, DEFAULTS)
            else:
                if case['draft'] != draft: invalidate(case)
                case['draft'] = draft

    def _detach_connection(self):
        self._commit_connection(); self._book.active = None; self._standalone_case = None; self._last_load_trace = None
        self._sync_origin()

    def _load_draft(self, draft):
        self._loading = True
        try:
            for k, value in draft.items(): self.vars[k].set(value)
        finally: self._loading = False
        self.last_verif = None; self.last_report = ''; self._last_load_trace = None
        self._mark_dirty(); self._sync_origin()

    def _select_connection(self, ckey):
        from Punching_EC2_GUI import DEFAULTS
        self._ensure_book()
        if ckey not in self._book.cases: raise ValueError('Ligação não encontrada.')
        self._commit_connection()
        if not self._book.active:
            self._individual_draft = self._raw_draft(); self._individual_case = deepcopy(self._standalone_case)
        self._standalone_case = None; self._book.active = ckey; case = self._book.cases[ckey]
        from .batch_workflow import seed_case
        case['draft'] = seed_case(self._book,case,DEFAULTS)
        from .collection_workflow import sync_joint
        sync_joint(self._book,ckey,case['draft'],DEFAULTS)
        self._load_draft(case['draft'])
        self.var_status.set('Ligação carregada. Complete a laje, materiais e bordos. F5 calcula as combinações desta ligação.' if case.get('automated') else 'Ligação carregada. Selecione a origem dos esforços e complete os dados da laje, materiais e bordos.')

    def _show_connections(self):
        from .import_dialogs import ConnectionDialog
        self._ensure_book(); self._commit_connection()
        dialog = ConnectionDialog(self); self.wait_window(dialog)
        if dialog.result == '__individual__':
            self._detach_connection()
            self._standalone_case = deepcopy(self.__dict__.get('_individual_case'))
            if '_individual_draft' in self.__dict__: self._load_draft(self._individual_draft)
        elif dialog.result is not None: self._select_connection(dialog.result)

    def _merge_import(self, batch):
        self._ensure_book(); self._commit_connection()
        self._book.merge(batch)
        if self._book.active:
            # No result remains fresh after its imported context changes.
            self._load_draft(self._book.cases[self._book.active]['draft'])
        if batch.get('model_revision'):
            self.var_status.set('Modelo atualizado. Os casos afetados exigem novo cálculo; os dados individuais foram conservados. Guarde o conjunto para conservar as alterações.')
        else:self.var_status.set(f"Tabela importada: {batch['file']}. Selecione uma ligação em «Pilares…».")

    def _edit_force_origin(self):
        from .import_dialogs import OriginDialog
        case = self._current_connection()
        if case is None:
            messagebox.showinfo('Origem dos esforços', 'As tabelas são opcionais. Para associar uma origem importada, abra «Pilares…».', parent=self); return
        dialog = OriginDialog(self, case, self._raw_draft()); self.wait_window(dialog)
        if dialog.result is None: return
        if self._book.active: self._book.cases[self._book.active] = dialog.result
        else: self._standalone_case = dialog.result
        self._load_draft(dialog.result['draft'])
        self.var_status.set('Origem registada. Confira os dados da ligação e execute a verificação.')

    def _sync_origin(self):
        case = self._current_connection()
        if 'origin_button' in self.__dict__: self.origin_button.configure(state='normal' if case is not None else 'disabled')
        for name in ('frame_button','group_button'):
            if name in self.__dict__:getattr(self,name).configure(state='normal' if case and self._book.active and (name=='group_button' or case.get('automated')) else 'disabled')
        if 'var_origin' not in self.__dict__: return
        if case is None: self.var_origin.set('Caso individual · esforços introduzidos pelo utilizador')
        else:
            from .table_import import MODES
            source = 'Introdução manual' if case['choice'] == 'manual' else MODES.get(case['choice'], 'Origem por selecionar')
            self.var_origin.set(f"{case['floor']} / {case['support']} · {source}")

    def _connection_trace(self):
        case = self._current_connection()
        return provenance(case, self._raw_draft()) if case is not None else None

    def _prepare_model(self, parent=None):
        from .model_dialogs import ModelDialog
        self._ensure_book();self._commit_connection()
        parent = parent or self
        if not self._book.analysis_tables:
            messagebox.showinfo('Modelo', 'Importe primeiro a tabela de esforços dos pilares.', parent=parent); return
        dialog = ModelDialog(parent,self); self.wait_window(dialog)
        if parent is not self: parent.grab_set()
        if dialog.result is not None:
            try:self._merge_import(dialog.result)
            except Exception as exc:messagebox.showerror('Preparar modelo',str(exc),parent=parent)

    def _save_model_configuration(self, config, parent=None):
        """Save an axis revision to disk before replacing the live collection."""
        from .model_revision import prepare_revision
        from Punching_EC2_GUI import DEFAULTS
        self._ensure_book();self._commit_connection();parent=parent or self
        try:
            proposed,batch=prepare_revision(self._book,config,[],DEFAULTS)
            path=self.__dict__.get('_book_path')
            if not path:
                path=filedialog.asksaveasfilename(parent=parent,defaultextension='.json',initialfile='Ligacoes_puncoamento.json',filetypes=[('Conjunto de ligações','*.json')])
            if not path:return False
            payload=proposed.payload()
            write_json_atomic(path,payload)
            self._book=proposed;self._book_path=str(path)
            if self._book.active:self._load_draft(self._book.cases[self._book.active]['draft'])
            self._book_saved_digest=self._collection_digest()
            impact=batch['revision_impact']
            self.var_status.set(f"Configuração e conjunto guardados: {Path(path).name}. {len(impact['updated'])} casos por combinação atualizados; volte a calcular as ligações afetadas.")
            return True
        except Exception as exc:
            messagebox.showerror('Guardar configuração',str(exc),parent=parent);return False

    def _orient_connection(self):
        from .model_dialogs import FrameDialog
        from .collection_workflow import rotate_joint
        from Punching_EC2_GUI import DEFAULTS
        self._commit_connection();case=self._current_connection()
        if case is None or not self._book.active:return
        dialog=FrameDialog(self,case);self.wait_window(dialog)
        if dialog.result is None:return
        try:
            rotate_joint(self._book,self._book.active,dialog.result,DEFAULTS)
            self._load_draft(self._book.cases[self._book.active]['draft'])
            self.var_status.set('Referencial atualizado nas combinações da ligação. Confira o bordo e execute F5.')
        except Exception as exc:messagebox.showerror('Orientar ligação',str(exc),parent=self)

    def _show_group_results(self):
        from .model_dialogs import GroupResultsDialog
        self._commit_connection();case=self._current_connection()
        if case is None:return
        dialog=GroupResultsDialog(self,self._book,case);self.wait_window(dialog)
        if dialog.result is not None:
            self._select_connection(dialog.result)
            self._display_group_case()

    def _run_collection(self, keys, on_done):
        from .model_dialogs import CalculationProgress
        from .collection_workflow import calculate_case
        from Punching_EC2_GUI import DEFAULTS
        if self.__dict__.get('_workflow_busy'):return
        from .batch_workflow import seed_case
        from .collection_workflow import sync_joint
        keys=list(dict.fromkeys(keys))
        for k in keys:
            c=self._book.cases[k]
            if not c.get('user_edited'):sync_joint(self._book,k,seed_case(self._book,c,DEFAULTS),DEFAULTS)
        if self._book.active in keys:self._load_draft(self._book.cases[self._book.active]['draft'])
        self._workflow_busy=True;progress=CalculationProgress(self,len(keys));position=0
        def step():
            nonlocal position
            if progress.cancelled or position==len(keys):
                completed=not progress.cancelled
                progress.destroy();self._workflow_busy=False
                on_done(completed);return
            case=self._book.cases[keys[position]]
            progress.text.set(f"{position+1}/{len(keys)} · {case['floor']} / {case['support']} · {case['combination']}")
            calculate_case(case,DEFAULTS);position+=1
            self.after(1,step)
        self.after(1,step)

    def _calculate_active_group(self):
        from .collection_workflow import group_keys
        self._update_derived();self._commit_connection();case=self._current_connection()
        def done(completed):
            self._display_group_case()
            if not completed:self.var_status.set('Cálculo interrompido. As combinações não executadas permanecem por calcular.')
            self._show_group_results()
        self._run_collection(group_keys(self._book,case),done)

    def _display_group_case(self):
        from .collection_workflow import cached_calculation, summaries, group_keys
        case=self._current_connection()
        if case is None:return
        cached=cached_calculation(case)
        if cached and cached['snapshot']:
            self._rendering_group_case=True
            try:self.calcular()
            finally:self._rendering_group_case=False
        else:
            self.last_verif=None;self.last_report='';self.dirty=True;self._result_tools(False)
            self._set_text(self.txt_output,cached['error'] if cached else 'Calcule as combinações desta ligação.')
            self._set_text(self.txt_diag,'')
            for tree in (self.tree_summary,self.tree_steel):
                for item in tree.get_children():tree.delete(item)
            self.var_steel.set('Sem proposta atualizada para a combinação selecionada.')
        entries=[]
        for k in group_keys(self._book,case):
            c=self._book.cases[k]
            entries.append(cached_calculation(c) or dict(floor=c['floor'],support=c['support'],combination=c['combination'],status='NOT_EVALUATED',snapshot=None,error='Por calcular.'))
        summary=summaries(entries)[0]
        color='#23744f' if summary['status']=='VERIFICA' else '#b12732' if summary['status']=='NÃO VERIFICA' else '#956315'
        self.lbl_badge.configure(text='LIGAÇÃO: '+summary['status'],foreground=color)
        self.var_resultado.set(f"{summary['count']} combinações · {summary['failed']} com falha · {summary['pending']} pendentes. Combinação apresentada: {case['combination']}.")
        self.var_status.set('A conclusão da ligação considera todas as combinações selecionadas. Consulte «Combinações…» para os valores e condicionantes.')

    def _save_connections(self, parent=None):
        self._ensure_book(); self._commit_connection(); parent = parent or self
        path = filedialog.asksaveasfilename(parent=parent, defaultextension='.json', initialfile='Ligacoes_puncoamento.json', filetypes=[('Conjunto de ligações', '*.json')])
        if not path: return False
        try:
            write_json_atomic(path, self._book.payload()); self._book_path=str(path);self._book_saved_digest=self._collection_digest()
            self.var_status.set('Conjunto guardado: ' + Path(path).name); return True
        except Exception as exc: messagebox.showerror('Guardar conjunto', str(exc), parent=parent); return False

    def _open_connections(self, parent=None):
        from Punching_EC2_GUI import DEFAULTS
        self._ensure_book()
        parent = parent or self
        path = filedialog.askopenfilename(parent=parent, filetypes=[('Conjunto de ligações', '*.json')])
        if not path: return False
        try:
            if Path(path).stat().st_size > 64*1024*1024: raise ValueError('Conjunto demasiado grande (limite 64 MB).')
            book = ConnectionBook.from_payload(json.loads(Path(path).read_text(encoding='utf-8-sig')), DEFAULTS)
            # Opening a project replaces a collection; offer saving concrete existing work first.
            if not self._offer_save_connections(parent): return False
            self._commit_connection()
            if not self._book.active:
                self._individual_draft = self._raw_draft(); self._individual_case = deepcopy(self._standalone_case)
            self._book = book; self._standalone_case = None
            if book.active:
                case = book.cases[book.active]
                if case['draft'] is None: case['draft'] = initial_draft(DEFAULTS, case)
                self._load_draft(case['draft'])
            else:
                # Detach old imported values as well as the old identity.
                self._standalone_case = deepcopy(self.__dict__.get('_individual_case'))
                self._load_draft(self.__dict__.get('_individual_draft', DEFAULTS))
            self._book_path=str(path);self._book_saved_digest=self._collection_digest()
            self._sync_origin(); self.var_status.set('Conjunto aberto. Cálculos guardados compatíveis recuperados; dados alterados ou de versões anteriores exigem novo cálculo.'); return True
        except Exception as exc: messagebox.showerror('Abrir conjunto', str(exc), parent=parent); return False

    def _new_connections(self, parent=None):
        from Punching_EC2_GUI import DEFAULTS
        if not self._offer_save_connections(parent): return False
        had_active=self._book.active is not None
        self._book=ConnectionBook();self._book_saved_digest=None;self._book_path=None
        if had_active:
            self._standalone_case=deepcopy(self.__dict__.get('_individual_case'))
            self._load_draft(self.__dict__.get('_individual_draft',DEFAULTS))
        self._sync_origin();self.var_status.set('Novo conjunto. Importe as tabelas da revisão pretendida.');return True

    def _collection_digest(self):
        self._commit_connection()
        return hashlib.sha256(json.dumps(self._book.payload(), sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()

    def _offer_save_connections(self, parent=None):
        self._ensure_book(); parent=parent or self
        if not (self._book.cases or self._book.analysis_tables or self._book.analysis_nodes) or self._collection_digest()==self.__dict__.get('_book_saved_digest'): return True
        answer=messagebox.askyesnocancel('Conjunto de ligações', 'Existem alterações no conjunto de ligações. Guardar antes de continuar?', parent=parent)
        return answer is not None and (not answer or self._save_connections(parent=parent))

    def _on_close(self):
        if self._offer_save_connections(): self.destroy()

    def _export_collection(self, parent=None):
        from .model_dialogs import CollectionReportDialog
        from .collection_reports import build_report, export_collection_pdf, export_collection_txt, export_collection_json
        self._commit_connection();parent=parent or self
        dialog=CollectionReportDialog(parent,self._book,parent._selected_keys() if hasattr(parent,'_selected_keys') else None);self.wait_window(dialog)
        if parent is not self:parent.grab_set()
        if dialog.result is None:return
        selection=dialog.result;kind=selection['format']
        path=filedialog.asksaveasfilename(parent=parent,defaultextension='.'+kind,initialfile='Puncoamento_por_piso.'+kind,filetypes=[(kind.upper(),'*.'+kind)])
        if not path:return
        def done(completed):
            if parent is not self:parent.grab_set()
            if not completed:
                self.var_status.set('Exportação cancelada após interrupção do cálculo.');return
            try:
                report=build_report(self._book,selection['keys'],selection['full'],only_calculated=selection.get('only_calculated',True))
                writer={'pdf':export_collection_pdf,'txt':export_collection_txt,'json':export_collection_json}[kind]
                target=Path(path);temp=None
                try:
                    with tempfile.NamedTemporaryFile(dir=target.parent,prefix=target.stem+'_',suffix='.'+kind,delete=False) as f:temp=Path(f.name)
                    writer(report,temp);temp.replace(target)
                finally:
                    if temp and temp.exists():temp.unlink()
                self.var_status.set(f'Relatório do conjunto exportado: {target.name}.')
                messagebox.showinfo('Relatório do conjunto','Relatório exportado com o âmbito e a cobertura indicados.',parent=parent)
                if hasattr(parent,'_filter'):parent._filter()
            except Exception as exc:messagebox.showerror('Relatório do conjunto',str(exc),parent=parent)
        done(True)
