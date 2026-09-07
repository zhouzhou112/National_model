"""Recompute water balances from existing physical exports without a solver.

Input: reservoir_dispatch.npz, optional station index and solution_qc.json.
Output: a new per-station CSV and JSON audit; source files remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=False)
    source=args.source/'reservoir_dispatch.npz'
    with np.load(source,allow_pickle=False) as data:
        volume=data['active_storage_m3']
        residual=volume-np.roll(volume,1,axis=1)
        for key,sign in (('local_inflow_m3s',-1),('upstream_release_m3s',-1),
                         ('turbine_flow_m3s',1),('spill_flow_m3s',1)):
            values=data[key]
            if values.shape!=volume.shape or not np.isfinite(values).all():
                raise ValueError('Invalid saved water array: '+key)
            residual+=sign*3600.0*values
        if not np.isfinite(volume).all(): raise ValueError('Nonfinite storage')
        absolute=np.abs(residual)
        cascade=set(data['core_cascade_local_rows'].astype(int).tolist())
        station_ids=data['hydrochn_row_id'].astype(str)
        hours=data['hour_index']
        positions=absolute.argmax(axis=1)
        frame=pd.DataFrame(dict(reservoir_local_index=np.arange(volume.shape[0]),
            hydrochn_row_id=station_ids,
            is_cascade=[i in cascade for i in range(volume.shape[0])],
            maximum_residual_hour_index=hours[positions],
            maximum_absolute_residual_m3=absolute.max(axis=1),
            hours_above_1m3=(absolute>1).sum(axis=1),
            hours_above_10m3=(absolute>10).sum(axis=1)))
    index_path=args.source/'reservoir_station_index.csv'
    if index_path.is_file():
        index=pd.read_csv(index_path)
        frame=frame.merge(index[['hydrochn_row_id','plant_name_model']],on='hydrochn_row_id',validate='one_to_one')
    frame.sort_values('maximum_absolute_residual_m3',ascending=False).to_csv(output/'water_residual_by_station.csv',index=False)
    qc_path=args.source/'solution_qc.json'
    qc=json.loads(qc_path.read_text(encoding='utf-8')) if qc_path.is_file() else {}
    digest=hashlib.sha256()
    with source.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''): digest.update(chunk)
    worst=frame.loc[frame.maximum_absolute_residual_m3.idxmax()].to_dict()
    report=dict(status='OFFLINE_WATER_AUDIT',optimize_called=False,presolve_called=False,
        source=str(source.resolve()),source_sha256=digest.hexdigest(),hours=volume.shape[1],
        reservoirs=volume.shape[0],maximum_water_residual_m3=float(absolute.max()),
        stations_above_1m3=int((frame.hours_above_1m3>0).sum()),
        station_hours_above_1m3=int((absolute>1).sum()),
        stations_above_10m3=int((frame.hours_above_10m3>0).sum()),
        station_hours_above_10m3=int((absolute>10).sum()),worst=worst,
        reported_maximum_water_residual_m3=qc.get('maximum_reservoir_transition_residual_m3'),
        reported_overall_qc=qc.get('status'),
        water_pass_at_current_physical_qc_1m3=bool(absolute.max()<=1),
        interpretation='Audit of saved physical arrays, not an LP solve or certification of the complete result. The raw-LP generic 1e-5 million-m3 tolerance corresponds to 10 m3; the separate physical water QC is stricter at 1 m3.')
    (output/'water_balance_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__': main()
