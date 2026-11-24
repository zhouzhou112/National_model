"""Check whether short-horizon cyclic bounds exercise the physical corrections."""
from pathlib import Path
import sys
import copy
import json
import hashlib
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3


def main():
    cfg=load_model_config(path='config/optimization_2030_storage_audited_v2.json')
    data=load_model_data(cfg)
    original=pd.read_csv(ROOT/'data/hydro/hydro_stations.csv').set_index('hydrochn_row_id')
    v1=pd.read_csv(ROOT/'data/hydro/repaired_20260913/hydro_stations.csv').set_index('hydrochn_row_id')
    reports=[]
    detail=[]
    with HydroProfileReader(cfg,data) as reader:
        for hours in [24,168,744,2160,8760]:
            h=reader.read_linear_block(TimeBlock(0,0,hours))
            ids=data.hydro_stations.iloc[h.reservoir_station_rows].hydrochn_row_id
            original_storage=original.loc[ids,'active_storage_gl'].to_numpy()*1e6
            v1_storage=v1.loc[ids,'active_storage_gl'].to_numpy()*1e6
            caps=[]
            for label,storage in [('original',original_storage),('v1',v1_storage),('v2',h.reservoir_active_storage_m3)]:
                variant=copy.copy(h)
                variant.reservoir_active_storage_m3=storage
                cap=cyclic_inventory_upper_m3(variant)
                caps.append(cap)
                reports.append(dict(hours=hours,storage_table=label,
                    clipped_reservoirs=int((cap < storage*(1-1e-10)).sum()),
                    summed_source_storage_m3=float(storage.sum()), summed_effective_bound_m3=float(cap.sum()),
                    fraction_of_summed_source_storage_remaining=float(cap.sum()/storage.sum()),
                    maximum_effective_bound_m3=float(cap.max())))
            for i,station_id in enumerate(ids):
                if original_storage[i] != h.reservoir_active_storage_m3[i]:
                    detail.append(dict(hours=hours,hydrochn_row_id=station_id,
                        original_with_cyclic_bound_m3=float(caps[0][i]),v1_bound_m3=float(caps[1][i]),v2_bound_m3=float(caps[2][i]),
                        v2_differs_from_v1=bool(not np.isclose(caps[1][i],caps[2][i],rtol=1e-10,atol=1e-6))))
    pd.DataFrame(reports).to_csv(HERE/'horizon_storage_bounds.csv',index=False)
    pd.DataFrame(detail).to_csv(HERE/'corrected_station_bounds_by_horizon.csv',index=False)
    models=[ROOT/'supplementary_materials/reviews/numeric_repair_20260913/probes/cleaned_nf2_24h_s0_cross2_fullcf_final/model.mps',
            HERE/'probes/cleaned_nf2_24h_s0_cross2_storage_v2/model.mps']
    hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in models]
    comparison=dict(v1_24h_mps_sha256=hashes[0],v2_24h_mps_sha256=hashes[1],
        identical_24h_lp=hashes[0]==hashes[1],
        interpretation='A regression solve of an identical truncated LP cannot demonstrate improved full-year solvability from the new physical corrections.',
        all_horizons_use_local_cleanup_m3s=cfg.raw['hydro']['local_inflow_cleanup_m3s'],
        only_water_arrays_built=True)
    (HERE/'short_horizon_limit.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    print(pd.DataFrame(reports).to_string(index=False),flush=True)
    print(json.dumps(comparison,indent=2),flush=True)


if __name__=='__main__':main()
