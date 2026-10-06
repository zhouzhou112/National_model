"""Stream full-year resource deltas and storage bounds; never build/solve an LP."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3


def main():
    cfg=load_model_config();data=load_model_data(cfg);out=Path(__file__).parent
    with HydroProfileReader(cfg,data) as reader:hydro=reader.read_linear_block(TimeBlock(0,0,8760))
    rows=[]
    for technology,group in data.vre_sites.groupby('technology',sort=False):
        discarded=np.zeros(len(group));retained=np.zeros(len(group));count=np.zeros(len(group),dtype=np.int64)
        for start in range(0,8760,168):
            for source,sub in group.groupby('cf_source_technology',sort=False):
                pos=group.index.get_indexer(sub.index)
                cf=data.cf.read(source,sub.cf_grid_id.to_numpy(np.int64),start,min(start+168,8760))
                keep=np.where(cf>=1e-6,cf,0);dust=(cf>=1e-6)&(cf<1e-4)
                discarded[pos]+=np.where(dust,cf,0).sum(axis=0)
                retained[pos]+=keep.sum(axis=0);count[pos]+=dust.sum(axis=0)
        for i,(_,site) in enumerate(group.iterrows()):
            rows.append(dict(kind='vre',id=site.grid_uid,technology=technology,province=int(site.province_code),
                removed_entries=int(count[i]),removed_flh=float(discarded[i]),old_flh=float(retained[i]),
                upper_gw=float(site.capacity_upper_gw),removed_potential_gwh=float(discarded[i]*site.capacity_upper_gw),
                old_potential_gwh=float(retained[i]*site.capacity_upper_gw)))
        print('SCANNED',technology,flush=True)
    if data.wave is not None:
        sites=data.wave.sites
        discarded=np.zeros(len(sites));retained=np.zeros(len(sites));count=np.zeros(len(sites),dtype=np.int64)
        for start in range(0,8760,168):
            cf=data.wave.cf.read(sites.wave_source_grid_id.to_numpy(np.int64),start,min(start+168,8760))
            dust=(cf>=1e-6)&(cf<1e-4)
            discarded+=np.where(dust,cf,0).sum(axis=0)
            retained+=np.where(cf>=1e-6,cf,0).sum(axis=0);count+=dust.sum(axis=0)
        for i,site in sites.iterrows():
            upper=float(site.capacity_upper_gw)
            rows.append(dict(kind='wave',id=site.grid_uid,technology='wave',province=int(site.province_code),
                removed_entries=int(count[i]),removed_flh=float(discarded[i]),old_flh=float(retained[i]),
                upper_gw=upper,removed_potential_gwh=float(discarded[i]*upper),old_potential_gwh=float(retained[i]*upper)))
        print('SCANNED wave',flush=True)
    for p,cf in hydro.ror_capacity_factor.items():
        stations=hydro.ror_station_rows[p]
        removed=np.where((cf>=1e-6)&(cf<1e-4),cf,0).sum(axis=0,dtype=np.float64)
        old=np.where(cf>=1e-6,cf,0).sum(axis=0,dtype=np.float64)
        count=((cf>=1e-6)&(cf<1e-4)).sum(axis=0)
        for i,s in enumerate(stations):
            site=data.hydro_stations.iloc[s];upper=float(site.capacity_potential_gw)
            rows.append(dict(kind='ror',id=site.hydrochn_row_id,technology='ror',province=int(site.province_code),
                removed_entries=int(count[i]),removed_flh=float(removed[i]),old_flh=float(old[i]),upper_gw=upper,
                removed_potential_gwh=float(removed[i]*upper),old_potential_gwh=float(old[i]*upper)))
    frame=pd.DataFrame(rows);frame.to_csv(out/'resource_cleanup_by_site.csv',index=False)
    agg=frame.groupby('technology')[['removed_entries','removed_potential_gwh','old_potential_gwh']].sum()
    agg['fraction_removed']=agg.removed_potential_gwh/agg.old_potential_gwh;agg.to_csv(out/'resource_cleanup_summary.csv')
    source_storage=hydro.reservoir_active_storage_m3.copy();cap=cyclic_inventory_upper_m3(hydro)
    q=hydro.reservoir_local_inflow_m3s;mask=(q>0)&(q<0.01);removed_q=np.where(mask,q,0)
    # Maximal downstream energy effect: propagate each discarded water budget,
    # allowing the same water to generate once at each downstream station.
    import copy
    loss=copy.copy(hydro);loss.reservoir_local_inflow_m3s=removed_q
    loss.reservoir_active_storage_m3=np.full(len(source_storage),np.finfo(float).max/10)
    water_budgets=cyclic_inventory_upper_m3(loss)
    storage=data.hydro_stations.iloc[hydro.reservoir_station_rows][['hydrochn_row_id','plant_name_model']].copy()
    storage['source_storage_m3']=source_storage;storage['effective_8760_storage_m3']=cap
    storage.to_csv(out/'cyclic_storage_bounds_8760.csv',index=False)
    headroom=data.vre_sites.capacity_upper_gw-data.vre_sites.capacity_floor_gw
    tiny=headroom[(headroom>1e-12)&(headroom<=1e-8)]
    summary=dict(resource=agg.reset_index().to_dict('records'),
        inflow_removed_station_hours=int(mask.sum()),inflow_removed_m3=float(removed_q.sum()*3600),
        inflow_local_energy_gwh=float(removed_q.sum(axis=1)@hydro.reservoir_generation_conversion_gw_per_m3s),
        inflow_including_downstream_energy_upper_gwh=float(water_budgets@hydro.reservoir_generation_conversion_gw_per_m3s/3600),
        reservoirs=int(len(cap)),storage_bounds_reduced=int((cap<source_storage).sum()),
        max_source_storage_m3=float(source_storage.max()),max_effective_storage_m3=float(cap.max()),
        tiny_headroom_sites=int(len(tiny)),discarded_headroom_gw=float(tiny.sum()),
        notes='Resource delta is at all-site technical upper capacities, not predicted dispatch; source correction impact must be evaluated separately. Stock cap preserves dispatch projection under current cyclic equations.')
    (out/'cleanup_budget.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
