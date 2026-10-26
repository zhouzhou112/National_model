"""Author-revised gate on preserved Cross2 X; does not optimize or alter sources."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import gurobipy as gp
import numpy as np


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main(root):
    destination=root/'revised_identity_20261026'
    destination.mkdir(exist_ok=False)
    source_folders=[root/'base_control_24h',root/'zero_24h']
    cost_paths=[root/(p.name+'_Xcost')/'cost_from_X/cost_components.csv' for p in source_folders]
    costs=[]
    for p in cost_paths:
        with p.open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        assert len({r['cost_component'] for r in rows})==len(rows)
        costs.append({r['cost_component']:float(r['value_million_cny_model_accounting_period']) for r in rows})
    records=[]
    for key in sorted(costs[0].keys()|costs[1].keys()):
        if key not in costs[0]:assert 'flexible_load_v5_' in key and costs[1][key]==0
        else:assert key in costs[1]
        a,b=costs[0].get(key,0.),costs[1].get(key,0.)
        difference=abs(a-b);denominator=max(abs(a),abs(b))
        relative=difference/denominator if denominator else 0.
        records.append(dict(component=key,base=a,zero=b,absolute_difference=difference,
                            relative_difference=relative,passed=relative<=1e-7,
                            base_structurally_disabled=key not in costs[0]))
    comparison=json.loads((root/'identity_gate_comparison.json').read_text())
    cross=json.loads((root/'saved_solution_crosscheck.json').read_text())
    xcheck={}
    for p in source_folders:
        model=gp.read(str(p/'model_archive/original.mps.gz'))
        metadata=json.loads((p/'solution_snapshot/snapshot_manifest.json').read_text())
        rc_record=metadata['attributes']['RC'];rc_path=p/'solution_snapshot'/rc_record['path']
        assert sha(rc_path)==rc_record['sha256']
        rc=np.load(rc_path,allow_pickle=False)
        names=model.getAttr('VarName');coeff=model.getAttr('Obj')
        with (source_folders[0]/'gate_values.jsonl').open() as f:base=dict(json.loads(line) for line in f)
        with (source_folders[1]/'gate_values.jsonl').open() as f:zero=dict(json.loads(line) for line in f)
        families={}
        for i,name in enumerate(names):
            if name not in base or name not in zero:continue
            delta=zero[name]-base[name]
            if abs(delta)<=1e-6:continue
            family=name.split('[')[0]
            item=families.setdefault(family,dict(changed_entries=0,max_abs_reduced_cost=0.,
                                                max_abs_direct_objective_coefficient=0.,direct_cost_difference=0.))
            item['changed_entries']+=1
            item['max_abs_reduced_cost']=max(item['max_abs_reduced_cost'],abs(float(rc[i])))
            item['max_abs_direct_objective_coefficient']=max(item['max_abs_direct_objective_coefficient'],abs(coeff[i]))
            item['direct_cost_difference']+=coeff[i]*delta
        xcheck[p.name]=dict(rc_sha256=sha(rc_path),families=families)
        model.dispose()
    feasible=all(c['max_constraint_violation']<=1e-8 and c['max_bound_violation']<=1e-8 for c in cross['checks'])
    cross_cost_equal=all(abs(cross['checks'][i]['objective']-cross['checks'][i+1]['objective'])<=1e-8 for i in [0,2])
    result=dict(status='PASS' if comparison['objective_pass'] and feasible and cross_cost_equal and all(c['passed'] for c in records) else 'FAIL',
                primal_attribute='X',objective_relative_difference=comparison['objective_relative_difference'],
                cross_feasibility_pass=feasible,cross_objective_equal=cross_cost_equal,
                cost_component_tolerance=1e-7,cost_components=records,cost_source_sha256={str(p):sha(p) for p in cost_paths},
                reduced_cost_disclosure=xcheck,
                note='Zero marginal cost means zero reduced cost along feasible alternative dispatch; direct flow regularization coefficients can be nonzero. Original BarX-derived tables are retained.')
    (destination/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['cost_components','reduced_cost_disclosure']},indent=2))
    print('Failed cost components:',json.dumps([r for r in records if not r['passed']],indent=2))
    print('Maximum changed-column reduced costs:',{k:max((r['max_abs_reduced_cost'] for r in v['families'].values()),default=0) for k,v in xcheck.items()})


if __name__=='__main__':main(Path(sys.argv[1]))
