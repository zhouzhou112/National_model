"""Independently read original GRFR/GHT/MERIT files; write audit sidecars only."""
import importlib.util
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from netCDF4 import Dataset

from audit_hydro import OUT, ROOT, PROCESS, STAGE1, EVIDENCE, digest, save_json


def main():
    inventory = pd.read_csv(PROCESS/'hydro_phs_module/data_output/hydrochn_ght2026_updated.csv')
    matching_script = PROCESS/'hydro_phs_module/scripts/run_hydro_phs_pipeline.py'
    spec = importlib.util.spec_from_file_location('hydro_matching_readonly', matching_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    config = json.loads((PROCESS/'hydro_phs_module/config/hydro_phs_config.json').read_text())
    hydro = mod.load_hydrochn(PROCESS/config['inputs']['hydrochn_csv'])
    ght = mod.load_ght_operating(PROCESS/config['inputs']['ght_xlsx'], config['inputs']['ght_sheet'], config)
    candidates = mod.build_candidates(hydro, ght, config)
    pairs = mod.select_one_to_one_matches(candidates)
    old = pd.read_csv(PROCESS/'hydro_phs_module/data_output/hydrochn_ght2026_match_pairs.csv')
    identity = lambda x: set(zip(x.hydrochn_row_id, x.ght_record_id))
    check = {'ght_operating_count':len(ght), 'matched_count':len(pairs),
             'match_pair_sets_equal':identity(pairs)==identity(old),
             'ght_operating_gw':float(ght.ght_capacity_mw.sum()/1000),
             'matched_ght_gw':float(pairs.ght_capacity_mw.sum()/1000)}
    # River attributes substantiate whether the inherited COMID represents a major river.
    reaches_path = STAGE1/'data_intermediate/merit_target_reaches.gpkg'
    reaches = gpd.read_file(reaches_path)
    diag = pd.read_csv(OUT/'station_diagnostic.csv')
    joined = diag.merge(inventory[['hydrochn_row_id','hydrochn_capacity_mw_original','match_distance_km','match_capacity_rel_diff','match_rule','ght_record_id','longitude_ght','latitude_ght']], on='hydrochn_row_id')
    joined = joined.merge(reaches[['COMID','uparea','order','NextDownID']],left_on='comid',right_on='COMID',validate='many_to_one')
    joined['original_to_updated_capacity_ratio'] = joined.existing_capacity_gw * 1000 / joined.hydrochn_capacity_mw_original
    joined['raw_no_share_utilization_h'] = joined.existing_raw_no_share_instant_gwh / joined.existing_capacity_gw.replace(0,np.nan)
    joined.to_csv(OUT/'station_matching_reach_audit.csv',index=False,encoding='utf-8-sig')
    risk = joined[(joined.existing_capacity_gw >= .5) & (joined.raw_no_share_utilization_h < 500)].copy()
    risk.sort_values('existing_capacity_gw',ascending=False).to_csv(OUT/'large_station_low_raw_flow_review.csv',index=False,encoding='utf-8-sig')
    check['large_station_low_raw_flow_count'] = len(risk)
    check['large_station_low_raw_flow_capacity_gw'] = float(risk.existing_capacity_gw.sum())
    check['low_flow_screen_definition'] = 'existing >= 0.5 GW and instantaneous raw-flow no-share energy / capacity < 500 h; screening only, not proof each station is mis-mapped'

    # Trace every retained target-COMID value to the original two GRFR files.
    with Dataset(STAGE1/'data_intermediate/grfr_target_comids_3h_2019.nc') as ds:
        ids = np.asarray(ds['comid'][:],dtype=np.int64)
        reference = np.asarray(ds['qout_raw_m3s'][:])
        t_ref = np.asarray(ds['time'][:])
    raw_receipts = []
    for pfaf in ('03','04'):
        path = Path('D:/National_model/Data/Gis/grfr_3hourly/discharge')/f'output_pfaf_{pfaf}_2019.nc'
        print(f'Reading original GRFR {pfaf}',flush=True)
        with Dataset(path) as ds:
            source_ids = np.asarray(ds['rivid'][:],dtype=np.int64)
            select = np.flatnonzero(np.isin(source_ids,ids))
            dest = pd.Index(ids).get_indexer(source_ids[select])
            values = np.ma.filled(ds['Qout'][:,select],np.nan)
            raw_receipts.append({'file':str(path),'bytes':path.stat().st_size,'sha256':digest(path),
                'target_comids':len(select),'compared_values':int(values.size),
                'all_values_equal':bool(np.array_equal(values,reference[:,dest],equal_nan=True)),
                'max_abs_error_m3s':float(np.nanmax(np.abs(values-reference[:,dest]))),
                'time_axis_equal':bool(np.array_equal(ds['time'][:],t_ref)),
                'Qout_units':getattr(ds['Qout'],'units',None),'Qout_long_name':getattr(ds['Qout'],'long_name',None)})
    save_json('original_grfr_verification.json',raw_receipts)

    # Compare exact local input bytes to the archived production manifest.
    manifest_path = ROOT/'supplementary_materials/reviews/base_frozen_followups_20261027/source_base/20261012_base2060_v9a12_t48_m750_tol1e4_v1/output_8760/input_manifest.csv'
    manifest = pd.read_csv(manifest_path)
    identities=[]
    timeseries=pd.read_csv(ROOT/'data/hydro/timeseries_index.csv').set_index('dataset')
    for row in manifest.itertuples():
        logical = str(row.logical_path)
        if logical.startswith('hydro/'):
            path = ROOT/'data'/logical
        elif row.kind == 'hydrology_timeseries':
            path = Path(timeseries.loc[logical,'path'])
        else:
            continue
        identities.append({'logical_path':logical,'local_path':str(path),'archived_sha256':row.sha256,
                           'local_sha256':digest(path),'match':digest(path)==row.sha256})
    save_json('production_input_identity.json',identities)
    check['all_archived_production_hydro_inputs_match'] = all(x['match'] for x in identities)
    check['production_hydro_inputs_compared'] = len(identities)
    # Verify annual output bytes against their archived manifests when available.
    save_json('provenance_checks.json',check)
    print(json.dumps(check,ensure_ascii=False,indent=2))
    print(risk[['plant_name_model','existing_capacity_gw','raw_mean_m3s','uparea','match_distance_km','original_to_updated_capacity_ratio']].to_string(index=False))


if __name__=='__main__':
    main()
