"""Gera uma amostra pública do relatório a partir do exemplo fictício de grupos."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Punching_EC2_GUI import DEFAULTS
from punching.connections import ConnectionBook
from punching.collection_workflow import calculate_case
from punching.collection_reports import build_report, export_collection_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = ROOT/'examples/importacao/Grupos_Ligacoes.json'
    book = ConnectionBook.from_payload(json.loads(source.read_text(encoding='utf-8')), DEFAULTS)
    keys = [k for k,c in book.cases.items() if c['floor']=='Piso 1']
    for k in keys:
        calculate_case(book.cases[k], DEFAULTS)
    report = build_report(book, keys=keys)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_collection_pdf(report, args.output)
    print(f'Relatório de demonstração: {args.output}')
    print('4 combinações calculadas / 6 previstas. Duas fontes modais permanecem pendentes; a conclusão é parcial.')


if __name__ == '__main__':
    main()
