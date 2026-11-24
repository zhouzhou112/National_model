"""Classify a preserved IIS and derive a carbon lower bound in a separate model.

The IIS/source and gate remain immutable. Removing the carbon limit solely to
minimize its left-hand side yields a diagnostic lower bound, not a gate solve.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import gurobipy as gp


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(exist_ok=False)
    source=args.run/'iis.ilp';sha=hashlib.sha256(source.read_bytes()).hexdigest()
    model=gp.read(str(source))
    names=[v.VarName for v in model.getVars()]
    rows=[c.ConstrName for c in model.getConstrs()]
    report=dict(source=str(source),source_sha256=sha,rows=len(rows),columns=len(names),
        network_variables=[n for n in names if any(t in n for t in ['spur','trunk'])],
        network_rows=[n for n in rows if any(t in n for t in ['spur','trunk'])],
        row_families=dict(Counter(n.split('[')[0].rsplit('_',1)[0] for n in rows)),
        diagnostic_only=True,gate_unchanged=True,tolerances_relaxed=False)
    model.Params.FeasibilityTol=1e-9;model.Params.OptimalityTol=1e-9
    model.Params.NumericFocus=2;model.Params.Aggregate=0
    model.Params.Threads=8;model.Params.TimeLimit=180
    model.Params.LogFile=str(args.output/'iis_replay.log');model.optimize()
    report['iis_replay_status']=int(model.Status)
    constraint=model.getConstrByName('annual_net_carbon_limit')
    if constraint is not None:
        report['original_carbon_limit_mt']=constraint.RHS
        model.setObjective(model.getRow(constraint),gp.GRB.MINIMIZE)
        model.remove(constraint)
        model.Params.LogFile=str(args.output/'carbon_lower_bound.log');model.optimize()
        report['carbon_lower_bound_status']=int(model.Status)
        if model.Status==gp.GRB.OPTIMAL:
            report['minimum_iis_net_emissions_mt']=model.ObjVal
            report['carbon_excess_lower_bound_mt']=model.ObjVal-report['original_carbon_limit_mt']
            # Weak-duality bound only: do not change any capacity bound.
            # Increasing an upper bound by d changes this minimization dual
            # certificate by d * min(0, RC). Tightening the lower bound to Base
            # can only increase the minimum, so omitting it is conservative.
            marginal=[dict(variable=v.VarName,upper=v.UB,reduced_cost_mt_per_gw=v.RC)
                for v in model.getVars() if v.VarName.startswith(('spur_augmentation_gw[','trunk_augmentation_gw['))
                and v.UB<gp.GRB.INFINITY]
            report['network_upper_bound_duals']=marginal
            report['carbon_lower_bound_with_1mw_network_headroom_mt']=model.ObjVal+sum(
                min(0.,v['reduced_cost_mt_per_gw'])*1e-3 for v in marginal)
            report['network_bound_diagnostic']='Dual certificate for up to +1e-3 GW per spur/trunk upper bound; no bounds changed'
        report['carbon_diagnostic_scope']='IIS subset without carbon cap; lower bound, not accepted dispatch'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
    report['source_unchanged']=True
    (args.output/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['row_families']},indent=2))
    model.dispose()


if __name__=='__main__':main()
