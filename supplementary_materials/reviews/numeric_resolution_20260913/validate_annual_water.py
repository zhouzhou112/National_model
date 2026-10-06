"""Reconstruct every station-hour in physical units from the solved components."""
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3


def main():
    cfg=load_model_config(path='config/optimization_2030_spill_tightened_v3.json')
    data=load_model_data(cfg)
    with HydroProfileReader(cfg,data) as reader:h=reader.read_linear_block(TimeBlock(0,0,8760))
    shape=h.reservoir_local_inflow_m3s.shape
    turbine=np.zeros(shape);spill=np.zeros(shape);volume=np.zeros(shape);seen=np.zeros(shape[0],int)
    for path in sorted((HERE/'annual_spill_v3').glob('component_*.npz')):
        with np.load(path) as d:
            rows=d['station_rows'];seen[rows]+=1
            turbine[rows]=d['turbine_m3s'];spill[rows]=d['spill_m3s'];volume[rows]=d['storage_m3']
    if not np.all(seen==1):raise ValueError('Missing or repeated station outputs')
    upstream=np.zeros(shape)
    for src,dst,w,lag,f in zip(h.cascade_edge_source_local_rows,h.cascade_edge_target_local_rows,
            h.cascade_edge_target_weights,h.cascade_edge_lag_h,h.cascade_edge_transfer_fraction):
        transmitted=np.roll((turbine[src]+spill[src]).sum(axis=0),int(lag))*f
        for target,weight in zip(dst,w):upstream[target]+=float(weight)*transmitted
    water=volume-np.roll(volume,1,axis=1)-3600*(h.reservoir_local_inflow_m3s+upstream-turbine-spill)
    generation=turbine*h.reservoir_generation_conversion_gw_per_m3s[:,None]
    capacity=data.hydro_stations.existing_capacity_gw.to_numpy(float)[h.reservoir_station_rows]
    bound=cyclic_inventory_upper_m3(h)
    report=dict(stations=shape[0],hours=shape[1],station_hours=int(np.prod(shape)),
        maximum_water_residual_m3=float(np.abs(water).max()),
        maximum_storage_upper_violation_m3=float(np.maximum(volume-bound[:,None],0).max()),
        maximum_storage_lower_violation_m3=float(np.maximum(-volume,0).max()),
        maximum_generation_upper_violation_gw=float(np.maximum(generation-capacity[:,None],0).max()),
        maximum_generation_lower_violation_gw=float(np.maximum(-generation,0).max()),
        maximum_spill_lower_violation_m3s=float(np.maximum(-spill,0).max()),
        all_values_finite=bool(all(np.isfinite(x).all() for x in [volume,turbine,spill,water])),
        total_generation_gwh=float(generation.sum()),national_electricity_constraints_checked=False)
    report['pass']=bool(report['all_values_finite'] and report['maximum_water_residual_m3']<=1
        and report['maximum_storage_upper_violation_m3']<=1 and report['maximum_storage_lower_violation_m3']<=1
        and report['maximum_generation_upper_violation_gw']<=1e-6 and report['maximum_generation_lower_violation_gw']<=1e-8
        and report['maximum_spill_lower_violation_m3s']<=1e-3)
    (HERE/'annual_physical_qc.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    if not report['pass']:raise SystemExit(1)


if __name__=='__main__':main()
