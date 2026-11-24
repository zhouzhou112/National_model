"""Recompute this frozen read-only status snapshot; no SSH or solver calls.

Run: python <snapshot-directory>/analyze.py
Inputs: scheduler.json, saved logs, previous snapshot, archived 2030/2040 logs.
Output: summary.json. Missing files or inconsistent hashes fail explicitly.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import math
import re

HERE = Path(__file__).resolve().parent
REVIEWS = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('eta', REVIEWS/'convergence_eta_20261004/estimate.py')
    eta = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eta)
    scheduler = json.loads((HERE/'scheduler.json').read_text(encoding='utf-8'))
    for rel, expected in scheduler['source_sha256'].items():
        assert sha(HERE/rel.replace('/', '__')) == expected, rel
    rows = eta.parse(HERE/'output_8760__gurobi.log')
    assert [r['iteration'] for r in rows] == list(range(rows[-1]['iteration']+1)), 'noncontiguous iterations'
    current = rows[-1]
    previous_path = HERE.parent/'status_20261010T110156Z/summary.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8'))
    metrics = ['pinf', 'dinf', 'compl', 'absolute_objective_difference']
    window = rows[-11:]
    cost = (window[-1]['seconds']-window[0]['seconds'])/600
    callbacks = [json.loads(line) for line in (HERE/'output_8760__solver_telemetry.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    barrier = {int(x['iteration']): x for x in callbacks if x.get('phase') == 'barrier' and 'iteration' in x}
    queue = dict(zip(['JobID', 'State', 'Elapsed', 'TimeLimit', 'CPUs', 'Memory', 'Node'], scheduler['queue'].strip().split('|')))
    result = dict(collected_at_server=scheduler['collected_at'],
        collected_at_uk=dt.datetime.fromisoformat(scheduler['collected_at']).astimezone(dt.timezone(dt.timedelta(hours=1))).isoformat(),
        last_log=current, previous_log=previous['last_log'], queue=queue,
        source_sha256_verified=True, iteration_count=len(rows),
        recent_minutes_per_iteration=cost, recent_window=[window[0]['iteration'], current['iteration']],
        previous_recent_minutes_per_iteration=previous['recent_minutes_per_iteration'],
        reduction_percent_since_610={m: 100*(1-current[m]/previous['last_log'][m]) for m in metrics},
        recent_metrics_monotonic={m: all(b[m] <= a[m] for a,b in zip(window, window[1:])) for m in metrics},
        recent_increase_iterations={m: [b['iteration'] for a,b in zip(window,window[1:]) if b[m]>a[m]] for m in metrics},
        large_jumps_after_117=[b['iteration'] for a,b in zip(rows,rows[1:]) if b['iteration']>117 and (b['compl']>10*max(a['compl'],1e-300) or (b['pinf']>10*max(a['pinf'],1e-300) and b['pinf']>1e-3))],
        last_callback=barrier.get(current['iteration']), terminal_artifacts=scheduler['terminal_artifacts'],
        stderr_bytes={n: (HERE/n).stat().st_size for n in ['stderr.log', 'slurm-4844528.err']},
        historical_alignment={}, previous_summary_sha256=sha(previous_path))
    result['recent_work_per_iteration'] = (barrier[current['iteration']]['work_units']-barrier[window[0]['iteration']]['work_units'])/10
    resource = scheduler['resources'].splitlines()[1].split('|')
    assert resource[1].endswith('K') and resource[2].endswith('K')
    result['rss_gib'] = dict(peak=float(resource[1][:-1])/1048576, current=float(resource[2][:-1])/1048576)
    result['warning_lines'] = [line for line in (HERE/'output_8760__gurobi.log').read_text(encoding='utf-8').splitlines() if re.search(r'warning|numerical trouble|numerical difficulties|sub.optimal|infeasible|unbounded|error|optimal objective|barrier solved', line, re.I)]
    for year,label in [('2030','base2030_t48'),('2040','base2040_t44')]:
        log_path = eta.HISTORY/(label+'__output_8760__gurobi.log')
        report_path = eta.HISTORY/(label+'__output_8760__solve_report.json')
        history = eta.parse(log_path)
        report = json.loads(report_path.read_text(encoding='utf-8'))
        assert report['status'] == 'OPTIMAL'
        matches = {m: min(history, key=lambda r: abs(math.log10(max(r[m],1e-300)/current[m])))['iteration'] for m in metrics}
        indexes = [matches[m] for m in ['pinf','compl','absolute_objective_difference']]
        lo,hi = min(indexes),max(indexes)
        remaining = [history[-1]['iteration']-hi, history[-1]['iteration']-lo]
        result['historical_alignment'][year] = dict(nearest_iterations=matches, stage_range=[lo,hi],
            remaining_iterations=remaining, days_at_current_speed=[n*cost/1440 for n in remaining],
            historical_remaining_days=[(report['runtime_seconds']-history[i]['seconds'])/86400 for i in [hi,lo]],
            historical_log_sha256=sha(log_path), historical_report_sha256=sha(report_path))
    result['dual_increase_events_since_610'] = [dict(iteration=b['iteration'], before=a['dinf'], after=b['dinf'], factor=b['dinf']/a['dinf']) for a,b in zip(rows,rows[1:]) if b['iteration']>610 and b['dinf']>2*a['dinf']]
    result['dual_all_increase_events_since_610'] = [dict(iteration=b['iteration'], before=a['dinf'], after=b['dinf'], factor=b['dinf']/a['dinf']) for a,b in zip(rows,rows[1:]) if b['iteration']>610 and b['dinf']>a['dinf']]
    result['dual_current_ratio_to_610'] = current['dinf']/previous['last_log']['dinf']
    result['dual_drop_from_latest_peak_percent'] = 100*(1-current['dinf']/max(r['dinf'] for r in rows[610:]))
    result['dual_drop_since_424_peak_percent'] = 100*(1-current['dinf']/rows[424]['dinf'])
    result['dual_continuous_decline_iterations_since_424'] = current['iteration']-424 if all(b['dinf']<=a['dinf'] for a,b in zip(rows[424:],rows[425:])) else None
    result['exponential_fit'] = {}
    for lo,hi in [(350,399),(610,current['iteration']),(611,current['iteration']),(424,current['iteration'])]:
        block=rows[lo:hi+1]; n=len(block)
        xs=[r['iteration'] for r in block]; xm=sum(xs)/n
        fits={}
        for metric in ['pinf','dinf','compl','absolute_objective_difference']:
            ys=[math.log10(r[metric]) for r in block]; ym=sum(ys)/n
            slope=sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/sum((x-xm)**2 for x in xs)
            intercept=ym-slope*xm
            sse=sum((y-intercept-slope*x)**2 for x,y in zip(xs,ys)); sst=sum((y-ym)**2 for y in ys)
            fits[metric]=dict(per_iter_factor=10**slope, per_iter_decline_pct=100*(1-10**slope), r_squared_log10=1-sse/sst,
                halving_iterations=-math.log10(2)/slope if slope<0 else None,
                halving_hours=(-math.log10(2)/slope)*(block[-1]['seconds']-block[0]['seconds'])/(hi-lo)/3600 if slope<0 else None)
        result['exponential_fit'][str(lo)+'-'+str(hi)]=fits
    (HERE/'summary.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
