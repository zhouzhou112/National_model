"""Parse archived Barrier logs without Gurobi; emit iteration CSV and audit JSON.

Usage: python analyze_log.py [--evidence-dir PATH]
Inputs: evidence/gurobi.log and solve_report.json. Outputs: barrier_iterations.csv,
analysis.json beside evidence. No solver, data mutation or remote operation.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, default=Path(__file__).parent / 'evidence')
    args = parser.parse_args()
    ev = args.evidence_dir
    pattern = re.compile(r'^\s*(\d+)\s+((?:[-+\d.eE]+\s+){5})(\d+)s\s*$')
    rows = []
    for line in (ev / 'gurobi.log').read_text(encoding='utf-8').splitlines():
        match = pattern.match(line)
        if not match:
            continue
        p, d, pr, dr, comp = map(float, match[2].split())
        rows.append(dict(iteration=int(match[1]), primal_objective=p, dual_objective=d,
                         primal_residual=pr, dual_residual=dr, complementarity=comp,
                         runtime_seconds=int(match[3]),
                         relative_objective_gap=abs(p-d)/max(1.0, abs(p), abs(d))))
    if len(rows) != 655 or [r['iteration'] for r in rows] != list(range(655)):
        raise ValueError('Expected complete Base trajectory 0..654; inspect source identity')
    report = json.loads((ev / 'solve_report.json').read_text(encoding='utf-8'))
    if report['status_code'] != 12 or report['solution_count'] != 0:
        raise ValueError('Unexpected terminal status; inspect source identity')
    with (ev.parent / 'barrier_iterations.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(
        gap_definition='abs(primal-dual)/max(1,abs(primal),abs(dual)); log-rounded diagnostic, not a certified optimality gap',
        selected_iterations=[rows[i] for i in [481, 550, 600, 633, 634, 654]],
        complementarity_jump_633_to_634=rows[634]['complementarity']/rows[633]['complementarity'],
        min_log_relative_objective_gap=min(r['relative_objective_gap'] for r in rows),
        matrix_coefficient_ratio=report['model_statistics']['coefficient_max_abs']/report['model_statistics']['coefficient_min_abs'],
        evidence_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ev.iterdir()) if p.is_file()},
        validation='PASS: 655 consecutive iterations; NUMERIC and no solution verified')
    (ev.parent / 'analysis.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'evidence_sha256'}, indent=2))


if __name__ == '__main__':
    main()
