"""Check correction identity and configuration; no optimization."""
from pathlib import Path
import copy
import hashlib
import json
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import pandas as pd
from cispo_model.config import load_model_config,ModelConfig


def main():
    folder=ROOT/'data/hydro/repaired_20260913'
    original=pd.read_csv(ROOT/'data/hydro/hydro_stations.csv')
    repaired=pd.read_csv(folder/'hydro_stations.csv')
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(ROOT/'data/hydro/hydro_stations.csv')==manifest['source_sha256']==digest(folder/'hydro_stations_original.csv')
    assert digest(folder/'hydro_stations.csv')==manifest['corrected_sha256']
    assert digest(ROOT/'config/hydro_storage_corrections_20260913.csv')==manifest['correction_authority_sha256']
    assert original.hydrochn_row_id.equals(repaired.hydrochn_row_id)
    permitted=['active_storage_gl','active_storage_duration_days_at_qrated']
    pd.testing.assert_frame_equal(original.drop(columns=permitted),repaired.drop(columns=permitted))
    changed=original.active_storage_gl.ne(repaired.active_storage_gl)
    assert repaired.loc[changed,'hydrochn_row_id'].tolist()==['HydroCHN_00923']
    assert repaired.loc[changed,'active_storage_gl'].iloc[0]==4.96
    cfg=load_model_config(path='config/optimization_2030_numeric_repaired.json')
    legacy=load_model_config()
    assert 'station_parameters_file' not in legacy.raw['hydro']
    assert not legacy.raw['hydro'].get('reduce_cyclic_inventory_range',False)
    for section,key,value in [('hydro','local_inflow_cleanup_m3s',0.011),
                              ('hydro','reduce_cyclic_inventory_range',1),
                              ('hydro','station_parameters_file','../outside.csv'),
                              ('numerics','capacity_headroom_zero_gw',0.001)]:
        raw=copy.deepcopy(cfg.raw);raw[section][key]=value
        try:ModelConfig(cfg.path,raw).validate()
        except ValueError:pass
        else:raise AssertionError(f'Invalid option accepted: {key}')
    result={'status':'PASS','rows':len(original),'changed_station_ids':['HydroCHN_00923'],
            'unchanged_columns':len(original.columns)-2,'source_backup_exact':True,
            'configuration_valid':True,'invalid_options_rejected':4,'legacy_defaults_preserved':True,
            'manifest':manifest}
    (Path(__file__).parent/'input_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
