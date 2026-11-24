"""Read the archived 20-day run's 8760h water trajectories; no solver call."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    source = HERE / 'sources/old_4139552_reservoir_dispatch.npz'
    expected = 'c3f02bb01044ea40b43ec1a5e759a79cfcd4b1dc6327081ef7c4dcd90978d07e'
    digest = hashlib.sha256()
    with source.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError('Archived reservoir export differs from the recovered result manifest')
    table = pd.read_csv(HERE/'original_vs_v2/reservoirs_620.csv')
    with np.load(source, allow_pickle=False) as a:
        ids = a['hydrochn_row_id'].astype(str)
        if not np.array_equal(ids, table.hydrochn_row_id.to_numpy(str)):
            raise ValueError('Station ordering drift')
        v = a['active_storage_m3']
        if v.shape != (620, 8760) or not np.isfinite(v).all():
            raise ValueError('Unexpected historical storage array')
        local = a['local_inflow_m3s']
        with np.load(HERE/'original_vs_v2/hourly_water_evidence.npz') as current:
            current_local = current['local_after_cascade_m3s']
            max_input_difference = float(np.abs(current_local-local).max())
            if max_input_difference > 1e-9:
                raise ValueError('Old and audited hydrology differ; comparison must not be treated as paired')
        releases = a['turbine_flow_m3s'] + a['spill_flow_m3s']
        incoming = local + a['upstream_release_m3s']
        residual = v - np.roll(v, 1, axis=1) - (incoming-releases)*3600
        absolute = np.abs(residual)
        shifted = v - v.min(axis=1, keepdims=True)
        shifted_residual = shifted - np.roll(shifted, 1, axis=1) - (incoming-releases)*3600
        bounds = np.asarray(a['active_storage_upper_m3'])
        if not np.allclose(bounds, table.source_active_storage_m3, atol=1e-5, rtol=1e-12):
            raise ValueError('Historical storage upper bound differs from original input')
        table['old_volume_min_m3'] = v.min(axis=1)
        table['old_volume_max_m3'] = v.max(axis=1)
        table['old_volume_excursion_m3'] = np.ptp(v, axis=1)
        table['old_unnecessary_offset_m3'] = v.min(axis=1)
        table['old_offset_to_excursion'] = np.divide(v.min(axis=1), np.ptp(v, axis=1),
            out=np.full(len(v), np.inf), where=np.ptp(v, axis=1)>0)
        table['old_max_water_residual_m3'] = absolute.max(axis=1)
        table['old_worst_water_hour'] = absolute.argmax(axis=1)
        table['old_hours_water_residual_above_1m3'] = (absolute > 1).sum(axis=1)
        table['old_hours_water_residual_above_10m3'] = (absolute > 10).sum(axis=1)
        table['old_annual_water_residual_m3'] = residual.sum(axis=1)
        table['old_generation_gwh'] = a['generation_gw'].sum(axis=1)
        table['old_shifted_excursion_exceeds_selected_physical_m3'] = np.maximum(np.ptp(v, axis=1)-table.selected_active_storage_m3,0)
        table['old_shifted_excursion_exceeds_safe_bound_m3'] = np.maximum(np.ptp(v, axis=1)-table.selected_effective_cyclic_bound_m3,0)
    table.to_csv(HERE/'old_4139552_storage_trajectories.csv', index=False)
    worst = table.nlargest(12, 'old_max_water_residual_m3')
    report = dict(source_sha256=digest.hexdigest(), source_run=4139552,
        scope='Old nonbasic engineering result, not a scientifically accepted solution',
        hours=8760, reservoirs=620, checked_station_hours=5431200,
        original_input_hydrology_max_difference_m3s=max_input_difference,
        maximum_water_residual_m3=float(absolute.max()),
        reservoirs_with_water_residual_above_1m3=int((absolute.max(axis=1)>1).sum()),
        station_hours_with_water_residual_above_1m3=int((absolute>1).sum()),
        station_hours_with_water_residual_above_10m3=int((absolute>10).sum()),
        offset_above_10times_excursion_reservoirs=int((table.old_offset_to_excursion>10).sum()),
        offset_above_100times_excursion_reservoirs=int((table.old_offset_to_excursion>100).sum()),
        largest_offset_m3=float(table.old_unnecessary_offset_m3.max()),
        largest_offset_to_excursion=float(table.old_offset_to_excursion.max()),
        residual_change_from_subtracting_constant_offset_m3=float(np.abs(shifted_residual-residual).max()),
        notes=['Subtracting a constant inventory offset preserves flows and exact equations but does not repair pre-existing infeasibility.',
               'A corrected physical regulating volume can require redispatch; it is different from an equivalent offset removal.',
               'Large offsets and residuals are evidence of exposure to cancellation; they do not establish the unique cause of the failed 9-day run.'],
        worst_stations=worst[['hydrochn_row_id','plant_name_local_ght','old_max_water_residual_m3',
                              'old_worst_water_hour','source_storage_to_safe_annual_water']].to_dict('records'))
    (HERE/'old_4139552_storage_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
