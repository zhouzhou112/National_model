"""Read-only audit of inherited VRE site floors under the actual 2040 inputs."""
from pathlib import Path
import json
import os
import sys
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'repo'))
os.chdir(ROOT/'repo')
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.planning_state import PlanningState, stable_asset_id
cfg=load_model_config('config/optimization_numeric_dac_by_year_v9.json').for_planning_year(2040)
state=PlanningState.load(os.environ['UPSTREAM_STATE'],expected_boundary_year=2030,allow_unaccepted_candidate=True,expected_scenario_id='base')
data=load_model_data(cfg,planning_state=state)
ids=[stable_asset_id(r.grid_uid,r.technology) for r in data.vre_sites.itertuples(index=False)]
inherited=state.active_adjustment('vre',ids,planning_year=2040,unit='GW')
floor=data.vre_sites.capacity_floor_gw.to_numpy(float)+inherited
upper=data.vre_sites.capacity_upper_gw.to_numpy(float)
cutoff=cfg.raw['numerics'].get('capacity_floor_zero_gw',0)
floor[(floor>0)&(floor<cutoff)]=0
bad=(floor < -1e-9)|(floor > upper+1e-9)
rows=data.vre_sites.copy()
rows['asset_id']=ids
rows['inherited_gw']=inherited
rows['effective_floor_gw']=floor
rows['lower_violation_gw']=np.maximum(-floor,0)
rows['upper_violation_gw']=np.maximum(floor-upper,0)
rows.loc[bad].to_csv(ROOT/'inherited_vre_violations.csv',index=False)
report=dict(rows=int(bad.sum()),negative_rows=int((floor < -1e-9).sum()),upper_rows=int((floor>upper+1e-9).sum()),
            max_lower_gw=float(np.maximum(-floor,0).max()),max_upper_gw=float(np.maximum(floor-upper,0).max()),
            total_lower_gw=float(np.maximum(-floor,0).sum()),total_upper_gw=float(np.maximum(floor-upper,0).sum()),
            capacity_floor_zero_gw=cutoff,examples=rows.loc[bad,['asset_id','capacity_floor_gw','capacity_upper_gw','inherited_gw','effective_floor_gw']].head(12).to_dict('records'))
(ROOT/'inherited_vre_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
