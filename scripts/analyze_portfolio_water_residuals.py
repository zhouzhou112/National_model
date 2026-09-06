"""Inspect saved independent-reservoir balance scales; no solver is imported.

Input: existing reservoir_dispatch.npz and reservoir_station_index.csv.
Output: a new directory with per-reservoir scale/residual CSV and JSON summary.
The hourly-transition row index refers to the independent subset; its second
index starts at model hour 1. This script maps both explicitly.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with np.load(args.source/'reservoir_dispatch.npz', allow_pickle=False) as data:
        index = pd.read_csv(args.source/'reservoir_station_index.csv')
        volume = data['active_storage_m3']
        incoming = data['local_inflow_m3s']
        outflow = data['turbine_flow_m3s'] + data['spill_flow_m3s']
        previous = np.roll(volume, 1, axis=1)
        independent = np.setdiff1d(np.arange(volume.shape[0]), data['core_cascade_local_rows'])
        residual = volume - previous - 3600.0 * (incoming - outflow)
        rows = []
        for position, reservoir in enumerate(independent):
            hour = int(np.abs(residual[reservoir]).argmax())
            station = index.loc[index.reservoir_local_index.eq(reservoir)].iloc[0]
            inflow = float(3600 * incoming[reservoir].sum())
            maximum = float(abs(residual[reservoir, hour]))
            rows.append(dict(independent_subset_index=position, reservoir_local_index=int(reservoir),
                hydrochn_row_id=station.hydrochn_row_id, plant_name_model=station.plant_name_model,
                maximum_residual_hour_index=int(data['hour_index'][hour]),
                constraint_name=(f'reservoir_independent_cyclic_first_hour[{position}]' if hour == 0 else
                    f'reservoir_independent_hourly_transition[{position},{hour-1}]'),
                max_absolute_balance_residual_m3=maximum,
                max_absolute_balance_residual_million_m3=maximum/1e6,
                selected_horizon_inflow_m3=inflow,
                active_storage_upper_m3=float(data['active_storage_upper_m3'][reservoir]),
                storage_at_max_residual_m3=float(volume[reservoir,hour]),
                previous_storage_at_max_residual_m3=float(previous[reservoir,hour]),
                inflow_at_max_residual_m3s=float(incoming[reservoir,hour]),
                total_release_at_max_residual_m3s=float(outflow[reservoir,hour]),
                residual_to_selected_inflow=maximum/inflow if inflow > 0 else None,
                exact_zero_selected_inflow=bool(np.all(incoming[reservoir] == 0)),
                violated_hour_count=int((np.abs(residual[reservoir])/1e6 > 1e-5).sum())))
    frame = pd.DataFrame(rows).sort_values('max_absolute_balance_residual_m3', ascending=False)
    frame.to_csv(output/'independent_reservoir_residual_scales.csv', index=False)
    report = dict(status='OFFLINE_DIAGNOSTIC_ONLY', optimize_called=False,
        source=str(args.source.resolve()), independent_reservoirs=len(frame),
        violated_independent_hours=int(frame.violated_hour_count.sum()),
        threshold_million_m3=1e-5, threshold_relaxed=False,
        worst=frame.iloc[0].where(pd.notna(frame.iloc[0]), None).to_dict(),
        observations=[
            'Large free cyclic inventories coexist with small hourly inflows; this is a numerical-scale diagnostic, not proof of the sole solver failure cause.',
            'Do not map independent subset row indices directly to the full reservoir table.',
            'A fixed affine coordinate shift x=z+c is mathematically equivalent if ALL bounds, RHS, objective constant and exports are transformed. No such transformation is applied here.',
            'Fixing initial inventory to zero or enlarging feasibility tolerance is not an equivalent substitute and is not authorized.'])
    (output/'water_scale_diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
