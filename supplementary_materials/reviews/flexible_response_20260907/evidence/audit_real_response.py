import json,sys,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
import numpy as np,gurobipy as gp
from scripts.validate_flexible_portfolios import read_service_inputs
from cispo_model.config import load_model_config
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.flexible_response import thermal_contract_profile, resolved_service_costs
from cispo_model.offline_solution import audit_saved_primal
data=read_service_inputs(2030)
report=dict(optimize_called=False,presolve_called=False,year=2030,hours=8760,provinces=len(data.provinces),thermal={},windows=[],costs={})
for c in ['heating','cooling']:
 s=data.flexible_load_v4
 annual,u,d=thermal_contract_profile(s.thermal_envelopes_gw[c+'_up'],s.thermal_envelopes_gw[c+'_down'],s.thermal_availability[c])
 nz=np.concatenate([u[u>0],d[d>0]])
 report['thermal'][c]=dict(annual_reference_contract_sum_gw=float(annual.sum()),minimum_positive_coefficient=float(nz.min()),maximum_coefficient=float(nz.max()),coefficients_below_1e_9=int((nz<1e-9).sum()),coefficients_below_1e_13=int((nz<1e-13).sum()))
with patch.object(gp.Model,'optimize',side_effect=AssertionError('forbidden')),patch.object(gp.Model,'presolve',side_effect=AssertionError('forbidden')):
 for c in ['case1_thermal_v5','case2_ev_v5','case3_thermal_ev_v5']:
  for suffix in ['', '_response_v1']:
   path=Path('config/scenarios')/('response_candidates_v1' if suffix else '')/(c+suffix+'.json')
   config=load_model_config(scenario_path=path)
   with gp.Model('real_readonly') as m:
    m.Params.OutputFlag=0
    block=attach_flexible_load(m,config,data,hours=168,hour_start=4368)
    m.setObjective(gp.quicksum(block.costs.values()));m.update()
    audit=audit_saved_primal(m,np.zeros(m.NumVars))
    report['windows'].append(dict(case=c+suffix,hours=168,start_hour=4368,variables=m.NumVars,rows=m.NumConstrs,nnz=m.NumNZs,binaries=m.NumBinVars,zero_contract_qc=audit['status'],max_residual=audit.get('maximum_constraint_violation')))
 for level in ['low','high']:
  cfg=load_model_config(scenario_path=f'config/scenarios/response_candidates_v1/case3_thermal_ev_v5_response_cost_{level}_v1.json')
  costs=resolved_service_costs(cfg.raw['flexible_load'],data.flexible_load_v4.service_costs)
  report['costs'][level]={service:{key:[float(np.min(value)),float(np.max(value))] for key,value in fields.items()} for service,fields in costs.items()}
Path('output/flex_literature_20260907/real_input_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
