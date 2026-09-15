import argparse
import json
from pathlib import Path
from .core import PuncoamentoEC2
from .reports import export_json,export_txt,export_pdf,export_xlsx,text_report
from .connections import trace_for_api_inputs


def main():
    parser=argparse.ArgumentParser(description='PunchingShearEC2 - cálculo de um caso JSON')
    parser.add_argument('input',help='JSON com os argumentos de PuncoamentoEC2')
    parser.add_argument('--out',default='resultados',help='Diretório dos resultados')
    parser.add_argument('--pdf',action='store_true');parser.add_argument('--xlsx',action='store_true')
    args=parser.parse_args()
    try:
        payload=json.loads(Path(args.input).read_text(encoding='utf-8-sig'));data=payload
        if isinstance(data,dict) and 'inputs' in data:data=data['inputs']
        engine=PuncoamentoEC2(**data)
        trace=trace_for_api_inputs(payload,{**data,'V_Ed':engine.V_Ed,'M_Edx':engine.M_Edx,'M_Edy':engine.M_Edy,
            'pilar_tipo':engine.tipo_pilar,'edge_perp_interior':engine.edge_perp_interior,'corner_interior':engine.corner_interior})
        report=engine.verificar_puncoamento();r=engine.snapshot()
        if trace is not None:r['load_trace']=trace;report=text_report(r)
        print(report)
        target=Path(args.out);target.mkdir(parents=True,exist_ok=True)
        export_json(r,target/'resultado.json');export_txt(r,target/'memoria.txt')
        if args.pdf:export_pdf(r,target/'memoria.pdf')
        if args.xlsx:export_xlsx(r,target/'memoria.xlsx')
    except (ValueError,TypeError,KeyError) as exc:parser.exit(2,f'Erro de entrada: {exc}\n')
    except OSError as exc:parser.exit(3,f'Erro de leitura ou escrita: {exc}\n')
    if r['status'] in ('INVALID','ERROR'):
        parser.exit(2 if r['status']=='INVALID' else 3)
    if r['status'] not in ('PASS_WITH','PASS_WITHOUT'):parser.exit(1)


if __name__=='__main__':main()
