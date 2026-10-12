"""Read-only diagnosis of the 6b cleanup build stop; no cohort or model edits."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parents[2]))
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.planning_state import PlanningState,stable_asset_id
from cispo_model.master import THERMAL_TECHS

def main():
    cfg=load_model_config(HERE.parents[2]/'config/optimization_numeric_dac_by_year_v9_a12.json').for_planning_year(2060)
    paths={k:HERE/v/'planning_state_candidate' for k,v in [('original','upstream_2050_source_capsule'),('prepared','upstream_2050_prepared')]}
    states={k:PlanningState.load(v,expected_boundary_year=2050,expected_scenario_id='base',allow_unaccepted_candidate=True) for k,v in paths.items()}
    data=load_model_data(cfg,planning_state=states['original'])
    provinces=data.province_codes.tolist()
    table=data.thermal_floor.pivot(index='province_code',columns='technology',values='capacity_floor_gw').reindex(index=provinces,columns=THERMAL_TECHS[:-1],fill_value=0.)
    nuclear=data.nuclear_floor.set_index('province_code').capacity_floor_gw.reindex(provinces).fillna(0.)
    base=np.column_stack([table.to_numpy(float),nuclear.to_numpy(float)])
    ids=[stable_asset_id(p,t) for p in provinces for t in THERMAL_TECHS]
    floors={k:base+s.active_adjustment('thermal',ids,planning_year=2060,unit='GW').reshape(base.shape) for k,s in states.items()}
    rows=[];cohort_evidence=[]
    for i,j in np.argwhere(floors['prepared'] < -1e-9):
        asset=ids[i*len(THERMAL_TECHS)+j];tech=THERMAL_TECHS[j]
        record=dict(province_code=int(provinces[i]),technology=tech,asset_id=asset,
            exogenous_2060_gw=float(base[i,j]),original_floor_gw=float(floors['original'][i,j]),
            prepared_floor_gw=float(floors['prepared'][i,j]),deficit_gw=-float(floors['prepared'][i,j]))
        for stage,state in states.items():
            c=state.cohorts
            selected=c[c.asset_class.eq('thermal')&c.asset_id.eq(asset)&c.build_year.le(2060)&c.retire_year.gt(2060)]
            record[stage+'_active_by_action_gw']=selected.groupby('action').capacity_delta.sum().to_dict()
            for row in selected.to_dict('records'):cohort_evidence.append(dict(stage=stage,**row))
        rows.append(record)
    report=dict(status='STOP_AUTHOR_REVIEW_REQUIRED',trigger='Inherited thermal retrofit/build cohorts make a capacity floor negative',
        builder_guard_gw=-1e-9,affected_province_technology_pairs=len(rows),
        original_negative_floor_count=int((floors['original']<-1e-9).sum()),
        total_deficit_gw=sum(r['deficit_gw'] for r in rows),maximum_deficit_gw=max((r['deficit_gw'] for r in rows),default=0),
        affected=rows,state_sha256={k:hashlib.sha256((v/'capacity_cohorts.csv.gz').read_bytes()).hexdigest() for k,v in paths.items()},
        no_rule_expansion=True,no_optimization=True,no_2060_submission=True)
    (HERE/'revision_6b/thermal_floor_stop.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    pd.DataFrame(cohort_evidence).to_csv(HERE/'revision_6b/thermal_floor_stop_cohorts.csv',index=False)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
