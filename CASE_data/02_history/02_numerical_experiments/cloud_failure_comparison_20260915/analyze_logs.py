"""Recompute comparison from saved log snapshots; no solve, no model changes."""
from pathlib import Path
import csv
import json
import re

ROOT = Path(__file__).resolve().parent
PAT = re.compile(r'^\s*(\d+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s+(\d+)s\s*$', re.M)

def main():
    summary = {}
    all_rows = []
    for case in ['base_old', 'thermal', 'base_v9']:
        folder = ROOT/'evidence'/case
        log = (folder/'gurobi.log').read_text(encoding='utf-8')
        rows = []
        for match in PAT.finditer(log):
            v = match.groups()
            r = dict(zip(['iteration','primal','dual','primal_residual','dual_residual','complementarity','seconds'],[int(v[0]),*map(float,v[1:6]),int(v[6])]))
            r['absolute_objective_difference'] = abs(r['primal']-r['dual'])
            r['relative_objective_difference'] = r['absolute_objective_difference']/max(1,abs(r['primal']),abs(r['dual']))
            rows.append(r)
            all_rows.append({'case':case,**r})
        assert [r['iteration'] for r in rows] == list(range(len(rows))), case
        raw = re.search(r'Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros',log)
        pre = re.search(r'Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros',log)
        item = {'raw':dict(zip(['rows','columns','nonzeros'],map(int,raw.groups()))),'presolved':dict(zip(['rows','columns','nonzeros'],map(int,pre.groups())))}
        for label, pattern in [('factor_nz',r'Factor NZ\s*:\s*(\S+)'),('factor_ops',r'Factor Ops\s*:\s*(\S+)'),('aa_nz',r"AA' NZ\s*:\s*(\S+)"),('presolve_seconds',r'Presolve time: ([\d.]+)s'),('ordering_seconds',r'Ordering time: ([\d.]+)s')]:
            item[label] = float(re.search(pattern,log).group(1))
        item['selected_iterations'] = [r for r in rows if r['iteration'] in [0,20,50,77,97,366,367,568,633,634,654] or r==rows[-1]]
        item['average_seconds_per_iteration_50_to_97']=(rows[97]['seconds']-rows[50]['seconds'])/47
        item['average_seconds_per_iteration_77_to_97']=(rows[97]['seconds']-rows[77]['seconds'])/20
        item['best_relative_objective_difference']=min(r['relative_objective_difference'] for r in rows)
        item['same_solver_time_as_current'] = min(rows,key=lambda r:abs(r['seconds']-128993))
        item['large_complementarity_jumps']=[{'from':a['iteration'],'to':b['iteration'],'ratio':b['complementarity']/a['complementarity']} for a,b in zip(rows,rows[1:]) if b['complementarity']>10*a['complementarity']]
        build=json.loads((folder/'build_report.json').read_text(encoding='utf-8'))
        item['model_statistics']=build.get('statistics',build.get('model_statistics',{}))
        item['iteration_count']=len(rows)
        summary[case]=item
    comparison={}
    for ref in ['base_old','thermal']:
        comparison[ref]={}
        for stage in ['raw','presolved']:
            comparison[ref][stage]={k:100*(summary['base_v9'][stage][k]/v-1) for k,v in summary[ref][stage].items()}
        for k in ['factor_nz','factor_ops','presolve_seconds','ordering_seconds','average_seconds_per_iteration_50_to_97']:
            comparison[ref][k]=100*(summary['base_v9'][k]/summary[ref][k]-1)
    summary['current_change_percent']=comparison
    (ROOT/'analysis.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'barrier_iterations.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
