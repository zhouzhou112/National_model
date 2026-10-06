"""Audit the repaired full-year hydrology arrays without building an LP."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3
from cispo_model.monolithic import _reservoir_release_upper_scaled


def main():
    cfg=load_model_config(path='config/optimization_2030_numeric_repaired.json')
    data=load_model_data(cfg)
    with HydroProfileReader(cfg,data) as reader:h=reader.read_linear_block(TimeBlock(0,0,8760))
    s=data.hydro_stations.iloc[h.reservoir_station_rows][['hydrochn_row_id','plant_name_model']].copy()
    effective=cyclic_inventory_upper_m3(h)
    s['source_storage_m3']=h.reservoir_active_storage_m3
    s['effective_cyclic_storage_m3']=effective
    q=h.reservoir_local_inflow_m3s
    s['retained_local_water_m3']=q.sum(axis=1)*3600
    s['retained_positive_station_hours']=(q>0).sum(axis=1)
    out=Path(__file__).parent/'hydro'
    s.to_csv(out/'repaired_full_year_storage.csv',index=False)
    release=_reservoir_release_upper_scaled(h,flow_scale_m3s=1000,preserve_exact_hourly_zeros=True)
    rhs=q*3600/1e6
    station=s[s.hydrochn_row_id.eq('HydroCHN_00923')].iloc[0]
    assert station.source_storage_m3==4960000
    assert not ((q>0)&(q<0.01)).any()
    report=dict(status='PASS',hours=8760,reservoirs=len(s),lp_built=False,solver_called=False,
        jinping2_storage_m3=float(station.source_storage_m3),
        reduced_inventory_station_count=int((effective<h.reservoir_active_storage_m3).sum()),
        max_effective_inventory_m3=float(effective.max()),
        water_balance_local_rhs_min_positive=float(rhs[rhs>0].min()),
        water_balance_local_rhs_max=float(rhs.max()),
        release_upper_min_positive_scaled=float(release[release>0].min()),
        release_upper_max_scaled=float(release.max()),exact_zero_release_station_hours=int((release==0).sum()),
        no_positive_local_inflow_below_cutoff=True,
        notes='Reservoir block arrays only, not global LP or presolved statistics; cascade transfer is still explicit.')
    (out/'repaired_full_year_summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
