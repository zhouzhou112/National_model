"""Apply evidence-backed reservoir storage corrections to a new input table.

Preserves the source file. Writes a repaired CSV, exact change ledger and SHA
manifest in the destination directory. Usage: --source FILE --corrections CSV
--output-dir NEW_DIR. All paths supplied by caller; no optimization performed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--corrections',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    a=p.parse_args()
    original=pd.read_csv(a.source); fixes=pd.read_csv(a.corrections)
    if original.hydrochn_row_id.duplicated().any() or fixes.hydrochn_row_id.duplicated().any():
        raise ValueError('Station IDs must be unique')
    repaired=original.copy(); ledger=[]
    for row in fixes.itertuples(index=False):
        selected=repaired.index[repaired.hydrochn_row_id.eq(row.hydrochn_row_id)]
        if len(selected)!=1: raise ValueError(f'Missing station {row.hydrochn_row_id}')
        i=selected[0]; station=repaired.loc[i]
        if (station.plant_name_model != row.expected_plant_name
                or not np.isclose(station.capacity_potential_gw,row.expected_capacity_gw,rtol=0,atol=1e-12)
                or not np.isclose(station.active_storage_gl,row.expected_active_storage_gl,rtol=0,atol=1e-6)):
            raise ValueError(f'Source identity drift for {row.hydrochn_row_id}')
        value=float(row.corrected_active_storage_gl)
        if not np.isfinite(value) or value<0: raise ValueError('Invalid corrected storage')
        repaired.loc[i,'active_storage_gl']=value
        repaired.loc[i,'active_storage_duration_days_at_qrated']=value*1e6/(station.q_rated_m3s*86400)
        ledger.append(dict(hydrochn_row_id=row.hydrochn_row_id,old_active_storage_gl=float(station.active_storage_gl),
                           new_active_storage_gl=value,source_url=row.source_url,
                           note='v_max_gl/v_min_gl retain original inventory provenance; active storage is overridden by direct regulating-storage evidence'))
    unchanged=[c for c in original if c not in ('active_storage_gl','active_storage_duration_days_at_qrated')]
    pd.testing.assert_frame_equal(original[unchanged],repaired[unchanged])
    a.output_dir.mkdir(parents=True,exist_ok=False)
    repaired.to_csv(a.output_dir/'hydro_stations.csv',index=False)
    pd.DataFrame(ledger).to_csv(a.output_dir/'corrections.csv',index=False)
    shutil.copyfile(a.source,a.output_dir/'hydro_stations_original.csv')
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=dict(source_sha256=sha(a.source),corrected_sha256=sha(a.output_dir/'hydro_stations.csv'),
                  correction_authority_sha256=sha(a.corrections),changed_stations=len(ledger),
                  untouched_columns=unchanged,validation='PASS',source=str(a.source.resolve()))
    (a.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__': main()
