"""Independently validate the final 620x8760 water solution in physical units.

Newly solved affected groups override prior unchanged groups; every station
must occur exactly once. No national electrical optimality is inferred.
"""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3,independent_spill_upper_scaled
from cispo_model.monolithic import _reservoir_release_upper_scaled


def main():
    out=Path(__file__).resolve().parent;prior=out.parent/'numeric_resolution_20260913/annual_spill_v3'
    cfg=load_model_config(path='config/optimization_2030_numeric_final_v8.json');data=load_model_data(cfg)
    with HydroProfileReader(cfg,data) as r:h=r.read_linear_block(TimeBlock(0,0,8760))
    affected=json.loads((out/'transfer_cleanup_budget.json').read_text())['affected_groups']
    shape=h.reservoir_local_inflow_m3s.shape;g=np.zeros(shape);s=np.zeros(shape);v=np.zeros(shape);seen=np.zeros(shape[0],int)
    sources=[]
    for group in range(41):
        base=out/'annual_affected_v8' if group in affected else prior
        path=base/f'component_{group:03d}.npz'
        with np.load(path) as z:
            ids=z['station_rows'];seen[ids]+=1;g[ids]=z['turbine_m3s'];s[ids]=z['spill_m3s'];v[ids]=z['storage_m3']
        sources.append(dict(group=group,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if not np.all(seen==1):raise ValueError('Station coverage is incomplete or repeated')
    upstream=np.zeros(shape)
    for src,dst,weights,lag,f in zip(h.cascade_edge_source_local_rows,h.cascade_edge_target_local_rows,
            h.cascade_edge_target_weights,h.cascade_edge_lag_h,h.cascade_edge_transfer_fraction):
        flow=np.roll((g[src]+s[src]).sum(axis=0),int(lag))*f
        for target,w in zip(dst,weights):upstream[target]+=float(w)*flow
    balance=v-np.roll(v,1,axis=1)-3600*(h.reservoir_local_inflow_m3s+upstream-g-s)
    storage=cyclic_inventory_upper_m3(h)
    release=_reservoir_release_upper_scaled(h,flow_scale_m3s=1000,preserve_exact_hourly_zeros=True)
    spill,_=independent_spill_upper_scaled(h,release,1000,positive_bound_floor_m3s=1.)
    power=g*h.reservoir_generation_conversion_gw_per_m3s[:,None]
    cap=data.hydro_stations.existing_capacity_gw.to_numpy(float)[h.reservoir_station_rows]
    record=dict(stations=620,hours=8760,station_hours=620*8760,all_finite=bool(all(np.isfinite(a).all() for a in [g,s,v,balance])),
        maximum_water_residual_m3=float(np.abs(balance).max()),
        maximum_storage_lower_violation_m3=float(np.maximum(-v,0).max()),
        maximum_storage_upper_violation_m3=float(np.maximum(v-storage[:,None],0).max()),
        maximum_turbine_lower_violation_m3s=float(np.maximum(-g,0).max()),
        maximum_turbine_upper_violation_m3s=float(np.maximum(g-release*1000,0).max()),
        maximum_spill_lower_violation_m3s=float(np.maximum(-s,0).max()),
        maximum_spill_upper_violation_m3s=float(np.maximum(s-spill*1000,0).max()),
        maximum_generation_capacity_violation_gw=float(np.maximum(power-cap[:,None],0).max()),
        newly_solved_groups=affected,reused_unchanged_groups=[i for i in range(41) if i not in affected],sources=sources,
        total_diagnostic_generation_gwh=float(power.sum()),national_electricity_constraints_checked=False)
    record['passed']=record['all_finite'] and all(value<=1 for key,value in record.items() if key.endswith('_m3'))
    record['passed']=bool(record['passed'] and all(value<=1e-3 for key,value in record.items() if key.endswith('_m3s'))
        and record['maximum_generation_capacity_violation_gw']<=1e-6)
    (out/'annual_physical_qc_v8.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='sources'},indent=2),flush=True)
    if not record['passed']:raise SystemExit(1)


if __name__=='__main__':main()
