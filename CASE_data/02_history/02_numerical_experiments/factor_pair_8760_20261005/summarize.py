"""Recompute factor evidence from a SHA-verified status directory; never extrapolate."""
from pathlib import Path
import argparse
import csv
import json
import re


def extract(folder):
    out=folder/'output_8760'
    log=(out/'gurobi.log').read_text(encoding='utf-8',errors='replace') if (out/'gurobi.log').exists() else ''
    row={'member':folder.name}
    for label in ("Dense cols","AA' NZ","Factor NZ","Factor Ops"):
        match=re.search(re.escape(label)+r'\s*:\s*([\d.eE+\-]+)',log)
        row[label]=float(match[1]) if match else None
    match=re.search(r'Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros',log)
    if match:row.update(zip(('presolved_rows','presolved_cols','presolved_nnz'),(int(x.replace(',','')) for x in match.groups())))
    for label,pattern in [('presolve_seconds',r'Presolve time:\s*([\d.]+)s'),('ordering_seconds',r'Ordering time:\s*([\d.]+)s')]:
        m=re.search(pattern,log);row[label]=float(m[1]) if m else None
    cpu=re.search(r'CPU model:\s*(.*)',log);row['cpu_model']=cpu[1] if cpu else None
    iterations={}
    telemetry=out/'solver_telemetry.jsonl'
    if telemetry.exists():
        for line in telemetry.read_text(encoding='utf-8').splitlines():
            try:r=json.loads(line)
            except json.JSONDecodeError:continue # retain partial source; do not synthesize its last record
            if r.get('phase')=='barrier' and r.get('iteration') is not None:
                iterations.setdefault(int(r['iteration']),r)
    for i,r in sorted(iterations.items()):
        if i-1 in iterations:
            r['iteration_seconds']=r['runtime_seconds']-iterations[i-1]['runtime_seconds']
            r['iteration_work_units']=r['work_units']-iterations[i-1]['work_units']
    row['complete_iterations_0_to_5']=all(i in iterations for i in range(6))
    row['iteration_1_seconds']=iterations.get(1,{}).get('iteration_seconds')
    row['mean_iteration_2_to_5_seconds']=(iterations[5]['runtime_seconds']-iterations[1]['runtime_seconds'])/4 if row['complete_iterations_0_to_5'] else None
    row['mean_iteration_2_to_5_work']=(iterations[5]['work_units']-iterations[1]['work_units'])/4 if row['complete_iterations_0_to_5'] else None
    params=out/'solver_parameters_before_optimize.json'
    if params.exists():row['actual_parameters']=json.loads(params.read_text(encoding='utf-8'))
    solved=out/'solve_report.json'
    if solved.exists():row['terminal']=json.loads(solved.read_text(encoding='utf-8'))
    gate=folder/'allocation_gate.json'
    if gate.exists():row['allocation']=json.loads(gate.read_text(encoding='utf-8'))
    return row,[dict(member=folder.name,**r) for _,r in sorted(iterations.items())]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);a=p.parse_args()
    rows=[];iterations=[]
    for member in ('member_F','member_S'):
        row,it=extract(a.snapshot/member);rows.append(row);iterations.extend(it)
    result={'members':rows,'iteration_rule':'iteration i = Runtime_i - Runtime_(i-1); mean 2..5 = (Runtime_5 - Runtime_1)/4; same for Work',
        'decision':'PENDING_COMPLETE_EVIDENCE','scientific_interpretation':'No convergence or full-year speed extrapolation.'}
    full,screen=rows
    if all(r['complete_iterations_0_to_5'] for r in rows):
        result['time_ratio_S_over_F']=screen['mean_iteration_2_to_5_seconds']/full['mean_iteration_2_to_5_seconds']
        result['time_criterion_pass']=result['time_ratio_S_over_F']<=.75
    if full["Dense cols"] is not None and screen["Dense cols"] is not None:
        result['dense_cols_ratio_S_over_F']=screen['Dense cols']/full['Dense cols']
        result['mechanism_review_required']='Judge clear decline against task section 0; no new arbitrary numeric threshold.'
    sections=[]
    for m in ('member_F','member_S'):
        path=a.snapshot/m/'output_8760/mps_section_sha256.json'
        if path.exists():sections.append(json.loads(path.read_text(encoding='utf-8')))
    if len(sections)==2:
        keys=set(sections[0])|set(sections[1]);result['mps_section_comparison']={k:sections[0].get(k)==sections[1].get(k) for k in sorted(keys)}
        result['only_vre_new_bounds_can_differ']=all(v for k,v in result['mps_section_comparison'].items() if k!='BOUNDS_VRE_NEW')
    inputs=[]
    identities=[]
    for member in ('member_F','member_S'):
        path=a.snapshot/member/'output_8760/input_manifest.csv'
        if path.exists():
            with path.open(encoding='utf-8-sig',newline='') as stream:
                inputs.append([{k:v.replace(member,'member_PAIR') for k,v in r.items()} for r in csv.DictReader(stream)])
        path=a.snapshot/member/'source_identity.json'
        if path.exists():identities.append(json.loads(path.read_text(encoding='utf-8')))
    if len(inputs)==2:
        result['input_manifest_records']=len(inputs[0])
        result['input_identity_equal_after_member_path_normalization']=inputs[0]==inputs[1]
    if len(identities)==2:
        result['source_files_sha_equal']=identities[0]['actual_repo_sha256']==identities[1]['actual_repo_sha256']
    (a.snapshot/'factor_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if iterations:
        keys=list(dict.fromkeys(k for r in iterations for k in r))
        with (a.snapshot/'barrier_iterations.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(iterations)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
