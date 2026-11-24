"""Stream all 8760 resource hours; price explicit CF cleanup alternatives.

No input changes or LP build. Reports resource-energy ceilings at technical
capacity, not national dispatch losses. Also measures annual/hourly links.
"""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock


def main():
    cfg=load_model_config(path='config/optimization_2030_spill_tightened_v3.json')
    data=load_model_data(cfg)
    thresholds=np.array([1e-6,1e-4,1e-3,5e-3,1e-2])
    rows=[]
    def scan(technology,ids,capacity,read):
        sums=np.zeros((len(thresholds),len(ids)))
        minima=np.full_like(sums,np.inf)
        counts=np.zeros_like(sums,dtype=np.int64)
        for start in range(0,8760,168):
            cf=read(start,min(start+168,8760))
            if not np.isfinite(cf).all() or (cf<0).any() or (cf>1.000001).any():
                raise ValueError('Invalid resource capacity factor')
            for k,cutoff in enumerate(thresholds):
                keep=cf>=cutoff
                sums[k]+=np.where(keep,cf,0).sum(axis=0)
                minima[k]=np.minimum(minima[k],np.where(keep,cf,np.inf).min(axis=0))
                counts[k]+=keep.sum(axis=0)
        for k,cutoff in enumerate(thresholds):
            for i,identity in enumerate(ids):
                rows.append(dict(technology=technology,id=str(identity),cutoff=float(cutoff),
                    nonzeros=int(counts[k,i]),full_load_hours=float(sums[k,i]),
                    minimum_positive_cf=float(minima[k,i]) if counts[k,i] else None,
                    annual_hourly_link_span=float(sums[k,i]/minima[k,i]),
                    potential_energy_gwh=float(sums[k,i]*capacity[i])))
        print('scanned',technology,len(ids),flush=True)
    for (tech,source),group in data.vre_sites.groupby(['technology','cf_source_technology'],sort=False):
        ids=group.cf_grid_id.to_numpy(np.int64)
        scan(tech,group.grid_uid.to_numpy(),group.capacity_upper_gw.to_numpy(float),
             lambda start,stop,ids=ids,source=source:data.cf.read(source,ids,start,stop))
    if data.wave is not None:
        sites=data.wave.sites;ids=sites.wave_source_grid_id.to_numpy(np.int64)
        scan('wave',sites.grid_uid.to_numpy(),sites.capacity_upper_gw.to_numpy(float),
             lambda start,stop:data.wave.cf.read(ids,start,stop))
    with HydroProfileReader(cfg,data) as reader: h=reader.read_linear_block(TimeBlock(0,0,8760))
    for province,cf in h.ror_capacity_factor.items():
        stations=data.hydro_stations.iloc[h.ror_station_rows[province]]
        scan('ror',stations.hydrochn_row_id.to_numpy(),stations.capacity_potential_gw.to_numpy(float),
             lambda start,stop,cf=cf:cf[start:stop])
    frame=pd.DataFrame(rows)
    out=Path(__file__).resolve().parent
    frame.to_csv(out/'cf_tradeoff_by_site.csv.gz',index=False)
    totals=frame.groupby(['cutoff','technology']).agg(nonzeros=('nonzeros','sum'),potential_energy_gwh=('potential_energy_gwh','sum'),
        maximum_annual_hourly_link_span=('annual_hourly_link_span','max')).reset_index()
    totals.to_csv(out/'cf_tradeoff_summary.csv',index=False)
    base=totals[totals.cutoff==1e-4].set_index('technology')
    comparison=[]
    for cutoff,group in totals.groupby('cutoff'):
        current=group.set_index('technology')
        lost=(base.potential_energy_gwh-current.potential_energy_gwh).sum()
        comparison.append(dict(cutoff=float(cutoff),resource_potential_gwh=float(current.potential_energy_gwh.sum()),
            additional_lost_potential_gwh=float(lost),additional_loss_fraction=float(lost/base.potential_energy_gwh.sum()),
            coefficient_nonzeros=int(current.nonzeros.sum()),
            max_annual_hourly_link_span=float(current.maximum_annual_hourly_link_span.max())))
    (out/'cf_tradeoffs.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    print(json.dumps(comparison,indent=2),flush=True)


if __name__=='__main__':main()
