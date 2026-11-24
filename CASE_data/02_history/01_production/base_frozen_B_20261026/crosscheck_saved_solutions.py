"""Evaluate preserved solutions in both original models without optimizing.

This is evidence for the identity-gate failure, not an alternative gate.
Both original models and solutions remain unchanged.
"""
import json
from pathlib import Path
import sys

import gurobipy as gp
import numpy as np


def main(root):
    folders = {key:root/name for key,name in [('base','base_control_24h'),('zero','zero_24h')]}
    values = {}
    for key, path in folders.items():
        with (path/'gate_values.jsonl').open() as f:
            values[key] = dict(json.loads(line) for line in f)
    checks = []
    for key,path in folders.items():
        archive = path/'model_archive/original.mps.gz'
        if not archive.exists():archive = archive.with_suffix('')
        model = gp.read(str(archive))
        names = model.getAttr('VarName')
        other = 'zero' if key=='base' else 'base'
        # B-only flexible auxiliaries retain their zero-contract solved values.
        own = np.array([values[key][n] for n in names])
        cross = np.array([values[other].get(n, values[key][n]) for n in names])
        rhs = np.asarray(model.RHS)
        sense = np.asarray(model.Sense)
        lb,ub = np.asarray(model.LB),np.asarray(model.UB)
        matrix = model.getA()
        objectives = []
        for label,x in [('own',own),('cross',cross)]:
            residual = matrix @ x-rhs
            violation = np.where(sense=='=',abs(residual),np.where(sense=='<',residual,-residual))
            bound = np.maximum(lb-x,x-ub)
            objective = float(np.dot(np.asarray(model.Obj),x)+model.ObjCon)
            objectives.append(objective)
            checks.append(dict(model=key,solution=label,max_constraint_violation=float(max(0,violation.max())),
                               max_bound_violation=float(max(0,bound.max())),objective=objective,
                               missing_other_variables=sum(n not in values[other] for n in names)))
        model.dispose()
    result=dict(optimized=False,gate_waived=False,checks=checks,
                interpretation='Cross feasibility and equal cost support multiple optima; the authored hourly-identity gate remains unmet.')
    with (root/'saved_solution_crosscheck.json').open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main(Path(sys.argv[1]))
