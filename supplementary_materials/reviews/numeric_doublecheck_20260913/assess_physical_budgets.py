"""Quantify cleanup at the old 8760h portfolio and a conservative DAC guard.

Read-only inputs; this does not certify the old portfolio feasible after edits.
"""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data,DAC_TECHS


def main():
    out=Path(__file__).resolve().parent
    cfg=load_model_config(path='config/optimization_2030_numeric_simplified_v5.json')
    data=load_model_data(cfg)
    old=ROOT/'downloads/2030_stage_a_first_result_visualization_v1/input'
    manifest=json.loads((old/'result_manifest.json').read_text())
    wanted=['vre_capacity.csv','hydro_capacity.csv','wave_capacity.csv','dac_capacity_capture.csv']
    hashes={x['path']:x['sha256'] for x in manifest['files']}
    verified={name:hashlib.sha256((old/name).read_bytes()).hexdigest()==hashes[name] for name in wanted}
    if not all(verified.values()): raise ValueError('Old capacity outputs do not match their manifest')
    vre=pd.read_csv(old/'vre_capacity.csv'); hydro=pd.read_csv(old/'hydro_capacity.csv'); wave=pd.read_csv(old/'wave_capacity.csv')
    print({name:list(frame.columns) for name,frame in [('vre',vre),('hydro',hydro),('wave',wave)]},flush=True)
    cfs=pd.read_csv(out/'cf_tradeoff_by_site.csv.gz',dtype={'id':str})
    v=vre.rename(columns={'grid_uid':'id'}).assign(id=lambda f:f.id.astype(str))
    w=wave.rename(columns={'grid_uid':'id'}).assign(id=lambda f:f.id.astype(str),technology='wave')
    h=hydro.rename(columns={'hydrochn_row_id':'id'}).assign(id=lambda f:f.id.astype(str),technology='ror')
    caps=pd.concat([f[['id','technology','capacity_gw']] for f in [v,w,h]],ignore_index=True)
    frame=cfs.merge(caps,on=['id','technology'],how='left',validate='many_to_one')
    if frame.capacity_gw.isna().any(): raise ValueError('Old portfolio capacity matching incomplete')
    frame['old_portfolio_available_gwh']=frame.full_load_hours*frame.capacity_gw
    energy=frame.groupby(['cutoff','technology']).old_portfolio_available_gwh.sum().unstack('technology')
    energy.to_csv(out/'old_portfolio_resource_budgets.csv')
    old_dac=pd.read_csv(old/'dac_capacity_capture.csv')
    power=data.dac.set_index('technology').average_power_gw_per_mtco2_per_year
    annual_load=float(data.load_gw.sum())
    guard=annual_load/(power*8760.)
    old_dac['guard_mtpa']=old_dac.technology.map(guard)
    old_dac['guard_utilization']=old_dac.annualized_capture_rate_mtpa/old_dac.guard_mtpa
    old_dac.to_csv(out/'old_portfolio_dac_guard.csv',index=False)
    floor=data.vre_sites.capacity_floor_gw.to_numpy(float).copy()
    floor[(floor>0)&(floor<1e-5)]=0
    room=data.vre_sites.capacity_upper_gw.to_numpy(float)-floor
    removed=room[(room>0)&(room<=1e-5)]
    totals=energy.sum(axis=1)
    report=dict(old_output_manifest_verified=verified,annual_load_gwh=annual_load,
        cf_energy_at_old_portfolio_gwh={str(k):float(v) for k,v in totals.items()},
        additional_loss_v3_to_v5_gwh=float(totals.loc[1e-4]-totals.loc[.01]),
        additional_loss_v3_to_v5_fraction=float(1-totals.loc[.01]/totals.loc[1e-4]),
        newly_rounded_headroom_sites=int(len(removed)),removed_headroom_gw=float(removed.sum()),
        headroom_8760_nameplate_energy_upper_gwh=float(removed.sum()*8760),
        dac_guard_candidate_mtpa=guard.to_dict(),old_dac_total_mtpa=float(old_dac.annualized_capture_rate_mtpa.sum()),
        old_dac_maximum_guard_utilization=float(old_dac.guard_utilization.max()),
        interpretation='DAC guard is an explicit modeling approximation, not implied by existing constraints; old portfolio energy figures are availability ceilings, not dispatch or reoptimized losses')
    (out/'physical_budgets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
