"""Compare saved Barrier trajectories and calculate conditional historical ETAs.

Run: python supplementary_materials/reviews/convergence_eta_20261004/estimate.py
Uses only archived logs; does not connect to the server or invoke a solver.
Outputs: estimate.json and input_hashes.json in this directory.
These are historical analogues, not a statistical confidence interval.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import math
import re

HERE = Path(__file__).resolve().parent
REVIEWS = HERE.parent
SNAPSHOT = REVIEWS/'base_2050_continuation_20260930/status_20261004T125431Z'
HISTORY = REVIEWS/'thread_comparison_20260930/evidence'
PAT = re.compile(r'^\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)'
                 r'\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*$', re.M)


def parse(path):
    rows = []
    for match in PAT.findall(path.read_text(encoding='utf-8')):
        row = dict(zip(['iteration','primal','dual','pinf','dinf','compl','seconds'],
                       [int(match[0]), *map(float,match[1:6]), int(match[6])]))
        row['absolute_objective_difference'] = abs(row['primal']-row['dual'])
        rows.append(row)
    if not rows or [r['iteration'] for r in rows] != list(range(len(rows))):
        raise ValueError(f'Non-contiguous or empty trajectory: {path}')
    return rows


def main():
    summary_path = SNAPSHOT/'summary.json'
    summary = json.loads(summary_path.read_text())
    current_path = SNAPSHOT/'output_8760__gurobi.log'
    current = parse(current_path)[-1]
    assert current['iteration'] == summary['last_log']['iteration'] == 250
    per_iter = summary['windows']['240-250']['minutes_per_iteration']
    inputs = [summary_path,current_path]
    result = dict(as_of_uk=summary['collected_at_uk'], current=current,
                  recent_minutes_per_iteration=per_iter,
                  method='Individual log-scale nearest matches; DInf reported separately because it is non-monotonic. No fitted statistical model.',
                  scope='Conditional time to Barrier termination analogous to OPTIMAL historical solves; excludes postprocessing/QC acceptance.',
                  cases={})
    for year,label in [(2030,'base2030_t48'),(2040,'base2040_t44')]:
        log_path = HISTORY/(label+'__output_8760__gurobi.log')
        report_path = HISTORY/(label+'__output_8760__solve_report.json')
        qc_path = HISTORY/(label+'__output_8760__solution_qc.json')
        inputs.extend([log_path,report_path,qc_path])
        rows = parse(log_path)
        report = json.loads(report_path.read_text())
        qc = json.loads(qc_path.read_text())
        assert report['status']=='OPTIMAL'
        item = dict(terminal_iteration=rows[-1]['iteration'],terminal_status=report['status'],
                    qc_status=qc['status'],individual_matches={})
        for metric in ['pinf','dinf','compl','absolute_objective_difference']:
            best = min(rows,key=lambda r:abs(math.log10(max(r[metric],1e-300)/current[metric])))
            first = next((r['iteration'] for r in rows if r[metric]<=current[metric]),None)
            item['individual_matches'][metric] = dict(nearest=best,first_at_or_below=first)
        indexes = [item['individual_matches'][k]['nearest']['iteration']
                   for k in ['pinf','compl','absolute_objective_difference']]
        lo,hi = min(indexes),max(indexes)
        item['primary_stage_range'] = [lo,hi]
        remaining = [rows[-1]['iteration']-hi,rows[-1]['iteration']-lo]
        item['remaining_iterations_range'] = remaining
        item['historical_remaining_days_range'] = [
            (report['runtime_seconds']-rows[hi]['seconds'])/86400,
            (report['runtime_seconds']-rows[lo]['seconds'])/86400]
        item['remaining_days_at_current_speed_range'] = [n*per_iter/1440 for n in remaining]
        item['2050_total_iterations_if_analogue_holds'] = [current['iteration']+n for n in remaining]
        result['cases'][str(year)] = item
    wall = summary['job']['RunTime']
    days,clock = wall.split('-')
    hours,minutes,seconds = map(int,clock.split(':'))
    elapsed_days = int(days)+(hours*3600+minutes*60+seconds)/86400
    asof = dt.datetime.fromisoformat(summary['collected_at_uk'])
    result['elapsed_wall_days'] = elapsed_days
    result['rounded_planning_scenarios'] = dict(
        remaining_days=[4,8],midpoint_days=6,
        total_wall_days=[elapsed_days+4,elapsed_days+8],
        calendar_window_uk=[(asof+dt.timedelta(days=n)).isoformat() for n in [4,8]],
        conditions=['No further major numerical reset or stagnation.',
                    '2050 remaining iteration trajectory resembles one of the two successful historical solves.',
                    'Per-iteration cost stays within the recent/historical range.'],
        caveat='Not a guaranteed upper bound or success probability. A further NUMERIC failure or long plateau remains possible.')
    (HERE/'estimate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    hashes={str(p.relative_to(REVIEWS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (HERE/'input_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({year:{k:v for k,v in case.items() if k!='individual_matches'}
                      for year,case in result['cases'].items()},indent=2))
    print(json.dumps(result['rounded_planning_scenarios'],indent=2))


if __name__=='__main__':
    main()
