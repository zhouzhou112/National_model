"""Rebuild comparison table from preserved raw Gurobi logs and callback traces."""
from pathlib import Path
import json
import re
import pandas as pd
import numpy as np

HERE=Path(__file__).resolve().parent


def summarize(root):
    result=json.loads((root/'result.json').read_text())
    scope=json.loads((root/'scope.json').read_text())
    log=(root/'gurobi.log').read_text(encoding='utf-8',errors='replace')
    traces=pd.read_csv(root/'barrier_trajectory.csv')
    row={'case':root.name,'hours':scope['arguments']['hours'],'year':scope['arguments']['year'],
         'start':scope['arguments']['start'],'status':result['status'],'objective':result['objective'],
         'iterations':result['barrier_iterations'],'runtime_s':result['runtime'],'work':result['work'],
         'physical_qc':result.get('physical_qc'),'threads':result['parameters']['Threads'],
         'crossover':result['parameters']['Crossover'],'bar_conv_tol':result['parameters']['BarConvTol'],
         'bar_homogeneous':result['parameters']['BarHomogeneous'],'agg_fill':result['parameters']['AggFill']}
    for label in ['Dense cols','Factor NZ','Factor Ops']:
        match=re.search(re.escape(label)+r'\s*:\s*([\d.eE+\-]+)',log)
        row[label.lower().replace(' ','_')]=float(match[1]) if match else None
    match=re.search(r'Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros',log)
    if match:row.update(zip(['presolved_rows','presolved_columns','presolved_nnz'],[int(x.replace(',','')) for x in match.groups()]))
    deltas=traces.runtime.diff();selected=deltas[traces.iteration>=2]
    row['mean_iter_seconds_after_1']=float(selected.mean()) if len(selected) else None
    jumps=[]
    for metric in ['primal_inf','dual_inf','complementarity']:
        previous=traces[metric].shift(1)
        mask=(previous>0)&(traces[metric]>=10*previous)
        for i in traces.index[mask]:
            jumps.append(dict(metric=metric,iteration=int(traces.loc[i,'iteration']),
                previous=float(previous.loc[i]),current=float(traces.loc[i,metric]),ratio=float(traces.loc[i,metric]/previous.loc[i])))
    row['residual_jump_ge10_count']=len(jumps)
    (root/'trajectory_diagnostics.json').write_text(json.dumps({'jumps_ge10':jumps},indent=2)+'\n')
    return row


def main():
    roots=list(HERE.glob('*/result.json'))+list((HERE/'server_evidence').glob('*/result.json'))
    rows=[summarize(p.parent) for p in roots]
    pd.DataFrame(rows).sort_values('case').to_csv(HERE/'paired_evidence.csv',index=False)
    print(pd.DataFrame(rows)[['case','hours','status','iterations','runtime_s','residual_jump_ge10_count']].to_string(index=False))


if __name__=='__main__':main()
