"""Build the actual annual capacity layer and inspect full-year resource data.

Does NOT build/solve the complete national hourly LP. Separately records the
annual water-bound arrays and input-derived resource-link extremes.
"""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.master import build_master
from cispo_model.timeblocks import TimeBlock
from cispo_model.diagnostics import model_statistics


def main():
    out=Path(__file__).resolve().parent
    cfg=load_model_config(path='config/optimization_2030_numeric_final_v8.json')
    data=load_model_data(cfg)
    art=build_master(cfg,data,[TimeBlock(0,0,8760)],compute_max_cf=True)
    m=art.model;m.update()
    raw=model_statistics(m);raw.update(min_bound=m.MinBound,max_bound=m.MaxBound)
    v=m.getVars();c=m.getConstrs()
    upper=np.asarray(m.getAttr('UB',v));rhs=np.asarray(m.getAttr('RHS',c))
    bounded=np.flatnonzero((upper>0)&(upper<1e90)); ranked=bounded[np.argsort(upper[bounded])[-5:][::-1]]
    record=dict(scope='ANNUAL_CAPACITY_LAYER_ONLY',hours=8760,compute_max_cf=True,
        national_hourly_lp_built=False,solver_called=False,raw=raw,
        maximum_bound_variables=[dict(name=v[i].VarName,value=float(upper[i])) for i in ranked],
        dac_all_bounds_zero=bool(all(np.all(art.variables[k].UB==0) for k in ['dac_new','dac_capacity','dac_capture'])),
        largest_rhs=[dict(name=c[i].ConstrName,value=float(rhs[i])) for i in np.argsort(np.abs(rhs))[-5:][::-1]])
    cf=pd.read_csv(out/'cf_tradeoff_by_site.csv.gz',dtype={'id':str})
    old=cf[cf.cutoff==1e-4].set_index(['technology','id']);new=cf[cf.cutoff==.01].set_index(['technology','id'])
    added_zero=new.loc[(new.nonzeros==0)&(old.nonzeros>0)].reset_index()
    capacities=[]
    for row in added_zero.itertuples(index=False):
        if row.technology=='ror':
            station=data.hydro_stations.set_index('hydrochn_row_id').loc[row.id]
            floor=float(station.existing_capacity_gw);potential=float(station.capacity_potential_gw)
        elif row.technology=='wave':
            station=data.wave.sites.set_index('grid_uid').loc[row.id]
            floor=0.;potential=float(station.capacity_upper_gw)
        else:
            station=data.vre_sites.set_index(['technology','grid_uid']).loc[(row.technology,row.id)]
            floor=float(station.capacity_floor_gw);potential=float(station.capacity_upper_gw)
        capacities.append(dict(technology=row.technology,id=row.id,floor_gw=floor,potential_gw=potential,
            old_flh=float(old.loc[(row.technology,row.id),'full_load_hours'])))
    pd.DataFrame(capacities).to_csv(out/'new_zero_annual_resource_sites.csv',index=False)
    record['resource_link_full_year']=dict(maximum_flh=float(new.full_load_hours.max()),
        maximum_flh_to_min_positive_cf=float(new.annual_hourly_link_span.max()),
        newly_all_zero_sites=len(capacities),newly_all_zero_capacity_floor_gw=sum(x['floor_gw'] for x in capacities),
        newly_all_zero_capacity_potential_gw=sum(x['potential_gw'] for x in capacities),
        interpretation='Input-based annual/hourly link coefficients, not a full national MPS measurement')
    (out/'annual_capacity_layer_v8.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record,indent=2),flush=True)
    m.dispose()


if __name__=='__main__':main()
