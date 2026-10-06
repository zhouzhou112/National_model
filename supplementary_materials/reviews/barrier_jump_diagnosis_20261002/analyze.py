"""Read-only analysis of archived Barrier trajectories; never calls a solver.

Run: python supplementary_materials/reviews/barrier_jump_diagnosis_20261002/analyze.py
Inputs: the frozen evidence directory below and the named historical log archives.
Outputs: analysis.json, input_hashes.json. Python standard library only.
The factor-10 jump screen is descriptive, not a solver failure criterion.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import re

HERE = Path(__file__).resolve().parent
REVIEWS = HERE.parent
PAT = re.compile(
    r'^\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)'
    r'\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*$', re.M
)


def parse_log(path):
    content = path.read_text(encoding='utf-8')
    rows = [dict(zip(
        ['iteration', 'primal', 'dual', 'pinf', 'dinf', 'compl', 'seconds'],
        [int(m[0]), *map(float, m[1:6]), int(m[6])]
    )) for m in PAT.findall(content)]
    if not rows or [r['iteration'] for r in rows] != list(range(len(rows))):
        raise ValueError(f'Missing or non-contiguous iterations: {path}')
    for r in rows:
        r['absolute_objective_difference'] = abs(r['primal'] - r['dual'])
    jumps = []
    for a, b in zip(rows, rows[1:]):
        if b['compl'] > 10*a['compl'] or (b['pinf'] > 10*a['pinf'] and b['pinf'] > 1e-3):
            jumps.append({'before': a, 'after': b,
                          'compl_ratio': b['compl']/max(a['compl'], 1e-300),
                          'pinf_ratio': b['pinf']/max(a['pinf'], 1e-300)})
    status = 'RUNNING_SNAPSHOT'
    if 'Optimal objective' in content:
        status = 'OPTIMAL_LOG'
    elif re.search(r'Numerical trouble encountered|Numerical error', content, re.I):
        status = 'NUMERICAL_TERMINATION_LOG'
    summary = dict(first=rows[0], last=rows[-1], jumps=jumps, status=status,
                   stats=[line.strip() for line in content.splitlines() if any(
                       key in line for key in ['Matrix range', 'Bounds range', 'RHS range',
                                               'Dense cols', 'Factor NZ', 'Factor Ops'])])
    return rows, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, default=HERE/'evidence_20261002T221431Z')
    args = parser.parse_args()
    ev = args.evidence_dir.resolve()
    manifest = json.loads((ev/'manifest.json').read_text())
    for name, row in manifest['files'].items():
        raw = (ev/name.replace('/', '__')).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError(f'Source hash mismatch: {name}')
    paths = {
        '2050_v9': ev/'output_8760__gurobi.log',
        '2040_v9': REVIEWS/'thread_comparison_20260930/evidence/base2040_t44__output_8760__gurobi.log',
        '2030_v9': REVIEWS/'thread_comparison_20260930/evidence/base2030_t48__output_8760__gurobi.log',
        'thermal_old': REVIEWS/'cloud_failure_comparison_20260915/evidence/thermal/gurobi.log',
        'base_old': REVIEWS/'cloud_failure_comparison_20260915/evidence/base_old/gurobi.log',
    }
    result = {'collected_at': manifest['collected_at'], 'cases': {}}
    parsed = {}
    for label, path in paths.items():
        parsed[label], result['cases'][label] = parse_log(path)
    rows = parsed['2050_v9']
    latest = rows[-1]
    result['current_selected'] = [rows[i] for i in [0, 108, 116, 117, 118, 128, 132, latest['iteration']]]
    result['current_vs_prejump116'] = {k: latest[k]/rows[116][k] for k in
                                      ['pinf', 'dinf', 'compl', 'absolute_objective_difference']}
    result['decrease_since117_percent'] = {k: 100*(1-latest[k]/rows[117][k]) for k in ['pinf', 'compl']}
    result['recent10_decrease_percent'] = {k: 100*(1-latest[k]/rows[-11][k]) for k in
                                         ['pinf', 'dinf', 'compl', 'absolute_objective_difference']}
    result['recent10_minutes_per_iteration'] = (latest['seconds']-rows[-11]['seconds'])/600
    result['latest_residuals_monotonic_last10'] = {
        k: all(b[k] <= a[k] for a, b in zip(rows[-11:-1], rows[-10:]))
        for k in ['pinf', 'dinf', 'compl']}
    result['absolute_objective_difference_monotonic_since132'] = all(
        b['absolute_objective_difference'] <= a['absolute_objective_difference']
        for a, b in zip(rows[132:-1], rows[133:]))
    build = json.loads((ev/'output_8760__build_report.json').read_text())
    config = json.loads((ev/'output_8760__model_config_snapshot.json').read_text())['resolved_configuration']
    result['statistics'] = build['statistics']
    result['matrix_coefficient_ratio'] = build['statistics']['coefficient_max_abs']/build['statistics']['coefficient_min_abs']
    result['annual_scaling'] = {k: {key: row[key] for key in ['exponent','row_scale','original_coefficient_max_abs']}
                                for k,row in build['annual_capacity_link_row_scaling']['families'].items()}
    result['features'] = config['features']
    result['numerics'] = config['numerics']
    tables = json.loads((ev/'input_sources.json').read_text())
    limits = list(csv.DictReader(io.StringIO(tables['carbon/emissions_limits_by_scenario.csv']['text'])))
    result['carbon_limits'] = [r for r in limits if r['scenario'] == config['carbon_scenario'] and r['year'] in ['2040','2050']]
    factors = list(csv.DictReader(io.StringIO(tables['technology/emission_factors_by_year.csv']['text'])))
    gas = next(r for r in factors if r['technology']=='gas' and r['year']=='2050')
    result['gas_ccs_residual_coefficient'] = float(gas['emission_factor_mtco2_per_gwh'])*(1-float(gas['ccs_capture_fraction']))
    hashes = {str(path.relative_to(REVIEWS)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in paths.values()}
    for path in sorted(ev.iterdir()):
        if path.is_file(): hashes[str(path.relative_to(REVIEWS))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE/'input_hashes.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    (HERE/'analysis.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k,v in result.items() if k not in ['cases','features','numerics']}, indent=2))


if __name__ == '__main__':
    main()
