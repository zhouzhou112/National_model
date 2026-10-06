"""Audit every reservoir and all 8760 input hours, without building an LP.

Usage: python scripts/audit_reservoir_storage.py --output-dir NEW_DIRECTORY
Optional --config selects a corrected station table. Original and selected
storage are compared against the same unmodified hydrology. CSV summaries,
hourly NPZ evidence, source hashes and a JSON report are written to a new folder.
No capacity, inflow, source CSV or solver parameter is changed by this audit.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from cispo_model.config import ModelConfig, load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.monolithic import _reservoir_release_upper_scaled
from cispo_model.numerical_cleanup import cyclic_inventory_upper_m3
from cispo_model.timeblocks import TimeBlock


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def longest_cyclic_true_run(mask: np.ndarray) -> int:
    if mask.all():
        return len(mask)
    if not mask.any():
        return 0
    changes = np.diff(np.r_[False, mask, mask, False].astype(np.int8))
    return int(min(len(mask), (np.flatnonzero(changes == -1)
                              - np.flatnonzero(changes == 1)).max()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/optimization_2030_numeric_repaired.json')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    cfg = load_model_config(path=args.config)
    if cfg.hours != 8760 or cfg.raw['time_boundary'] != 'cyclic_year':
        raise ValueError('This audit requires the existing cyclic 8760h contract')
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    # Isolate storage: keep the old hydrology, including the old source-unit
    # zero rule. The optional newer local-inflow dust filter is disabled here.
    raw = copy.deepcopy(cfg.raw)
    raw['hydro']['local_inflow_cleanup_m3s'] = 0.0
    cfg = ModelConfig(cfg.path, raw, formulation_path=cfg.formulation_path)
    cfg.validate()
    data = load_model_data(cfg)
    original_path = ROOT / 'data/hydro/hydro_stations.csv'
    original = pd.read_csv(original_path).set_index('hydrochn_row_id')
    package = json.loads((ROOT / 'config/model_data_config.json').read_text(encoding='utf-8-sig'))
    inventory_path = Path(package['sources']['hydro_updated_inventory'])
    stage2_path = Path(package['sources']['hydro_stage2'])
    backbone_path = inventory_path.parents[2] / 'HydroCHN-main/HydroCHN-main/Hydropower_resource_China.csv'
    inventory = pd.read_csv(inventory_path).set_index('hydrochn_row_id')
    stage2 = pd.read_csv(stage2_path).set_index('hydrochn_row_id')
    backbone = pd.read_csv(backbone_path)
    backbone.index = [f'HydroCHN_{i:05d}' for i in range(len(backbone))]
    source_ids = original.index
    if not source_ids.is_unique or not inventory.index.is_unique or not stage2.index.is_unique:
        raise ValueError('Source station IDs must be unique')
    lineage = []
    for name, model_col, source_col in [
        ('normal_storage', 'v_max_gl', 'V_Max (GL)'),
        ('dead_storage', 'v_min_gl', 'V_Min (GL)'),
        ('head', 'head_m', 'H_Max (m)'), ('comid', 'comid', 'comid')]:
        values = original[model_col].to_numpy(float)
        for label, table in [('HydroCHN_backbone', backbone), ('GHT_updated_inventory', inventory)]:
            source_values = table.loc[source_ids, source_col].to_numpy(float)
            equal = np.isclose(values, source_values, rtol=1e-12, atol=1e-8, equal_nan=True)
            lineage.append(dict(field=name, source=label, rows=len(equal), mismatches=int((~equal).sum()),
                                maximum_absolute_difference=float(np.nanmax(np.abs(values-source_values)))))
    lineage.append(dict(field='active_storage', source='stage2', rows=len(original),
                        mismatches=int((~np.isclose(original.active_storage_gl,
                            stage2.loc[source_ids, 'active_storage_gl'], rtol=1e-12, atol=1e-8)).sum())))
    pd.DataFrame(lineage).to_csv(out / 'source_lineage.csv', index=False)

    print('Reading 620 reservoirs x 8760 original hydrology hours', flush=True)
    with HydroProfileReader(cfg, data) as reader:
        h = reader.read_linear_block(TimeBlock(0, 0, 8760))
        station_rows = h.reservoir_station_rows
        s = data.hydro_stations.iloc[station_rows].copy().reset_index(drop=True)
        available = reader._available_flow_for_rows(TimeBlock(0, 0, 8760), station_rows).T
        positions = s.comid.map(reader.comid_position)
        if positions.isna().any():
            raise ValueError('Reservoir COMID absent from the discharge input')
        natural = np.asarray(reader.discharge.variables['qout_model_m3s'][:, positions.to_numpy(int)], float).T
        time_variable = reader.discharge.variables['time']
        time_values = np.asarray(time_variable[:], float)
        time_audit = dict(units=getattr(time_variable, 'units', None),
                          calendar=getattr(time_variable, 'calendar', 'standard'),
                          count=len(time_values), start=float(time_values[0]), end=float(time_values[-1]),
                          time_step_values=np.unique(np.diff(time_values)).tolist(),
                          timezone='Source-native GRFR timezone undocumented; no timezone conversion in this audit')
        station_share = reader.station_flow_share[station_rows].copy()
    q = h.reservoir_local_inflow_m3s
    if q.shape != (len(s), 8760) or not np.isfinite(q).all() or (q < 0).any():
        raise ValueError('Invalid hourly reservoir water block')
    ids = s.hydrochn_row_id
    old_storage = original.loc[ids, 'active_storage_gl'].to_numpy(float) * 1e6
    selected_storage = h.reservoir_active_storage_m3.copy()
    budget_hydro = copy.copy(h)
    budget_hydro.reservoir_active_storage_m3 = np.full(len(s), 1e100)
    safe_budget = cyclic_inventory_upper_m3(budget_hydro)
    old_effective = np.minimum(old_storage, safe_budget)
    selected_effective = np.minimum(selected_storage, safe_budget)
    cascades = set(h.cascade_station_local_rows.tolist())
    source_info = inventory.loc[ids].reset_index(drop=True)
    for column in ['plant_name_local_ght', 'hydrochn_capacity_mw_original',
                   'hydrochn_status_standard', 'match_distance_km', 'match_rule']:
        s[column] = source_info[column]
    s['source_v_max_gl'] = original.loc[ids, 'v_max_gl'].to_numpy()
    s['source_v_min_gl'] = original.loc[ids, 'v_min_gl'].to_numpy()
    s['source_active_storage_m3'] = old_storage
    s['selected_active_storage_m3'] = selected_storage
    s['source_dead_fraction'] = s.source_v_min_gl / s.source_v_max_gl
    s['source_dead_fraction_rounded7'] = s.source_dead_fraction.round(7)
    # Detect a repeated affine signature already present in the original CSV.
    # This is a data-pattern diagnostic, not a claimed reconstruction of the
    # unpublished imputation algorithm and not a rule for correcting volumes.
    anchors = backbone.loc[['HydroCHN_00807', 'HydroCHN_01147']]
    slope, intercept = np.polyfit(anchors['InsCap(MW)'], anchors['V_Max (GL)'], 1)
    predicted = slope * s.hydrochn_capacity_mw_original + intercept
    s['affine_volume_pattern'] = np.isclose(s.source_v_max_gl, predicted, rtol=1e-8, atol=1e-5)
    s['current_to_source_capacity_ratio'] = s.capacity_potential_gw * 1000 / s.hydrochn_capacity_mw_original
    s['is_cascade'] = [i in cascades for i in range(len(s))]
    s['flow_allocation_share'] = station_share
    s['natural_reach_volume_m3'] = natural.sum(axis=1) * 3600
    s['available_station_volume_before_cascade_m3'] = available.sum(axis=1) * 3600
    s['local_volume_after_cascade_m3'] = q.sum(axis=1) * 3600
    s['safe_total_incoming_budget_m3'] = safe_budget
    s['source_storage_to_safe_annual_water'] = np.divide(old_storage, safe_budget,
        out=np.full(len(s), np.inf), where=safe_budget > 0)
    s['source_effective_cyclic_bound_m3'] = old_effective
    s['selected_effective_cyclic_bound_m3'] = selected_effective
    s['source_storage_exceeds_annual_budget'] = old_storage > safe_budget * (1 + 1e-10)
    s['source_storage_exceeds_10annual_budgets'] = old_storage > safe_budget * 10
    s['source_storage_exceeds_100annual_budgets'] = old_storage > safe_budget * 100
    s['source_rated_emptying_days'] = old_storage / (s.q_rated_m3s.to_numpy() * 86400)
    s['source_storage_energy_gwh'] = old_storage * h.reservoir_generation_conversion_gw_per_m3s / 3600
    s['input_water_energy_gwh'] = q.sum(axis=1) * h.reservoir_generation_conversion_gw_per_m3s
    s['positive_local_hours'] = (q > 0).sum(axis=1)
    s['local_flow_max_m3s'] = q.max(axis=1)
    s['local_flow_min_positive_m3s'] = np.where(q > 0, q, np.inf).min(axis=1)
    s['longest_cyclic_zero_local_hours'] = [longest_cyclic_true_run(row == 0) for row in q]
    s['local_hours_below_1m3s'] = ((q > 0) & (q < 1)).sum(axis=1)
    s['rhs_min_positive_million_m3'] = s.local_flow_min_positive_m3s * .0036
    s['storage_to_smallest_positive_hour_inflow'] = old_storage / (s.local_flow_min_positive_m3s * 3600)
    # Existing flow bounds are already finite. Audit the independent influence
    # of original vs corrected storage on those same all-hour bounds.
    old_hydro = copy.copy(h)
    old_hydro.reservoir_active_storage_m3 = old_storage
    release_original = _reservoir_release_upper_scaled(old_hydro, flow_scale_m3s=1000,
                                                       preserve_exact_hourly_zeros=True)
    release_selected = _reservoir_release_upper_scaled(h, flow_scale_m3s=1000,
                                                       preserve_exact_hourly_zeros=True)
    s['release_bound_original_max_1000m3s'] = release_original.max(axis=1)
    s['release_bound_selected_max_1000m3s'] = release_selected.max(axis=1)
    s['release_bound_tightened_hours'] = (release_selected < release_original * (1-1e-10)).sum(axis=1)
    s.to_csv(out / 'reservoirs_620.csv', index=False)
    s[s.source_storage_exceeds_annual_budget].sort_values('source_storage_to_safe_annual_water', ascending=False).to_csv(
        out / 'excess_inventory_stations.csv', index=False)
    s[s.affine_volume_pattern].to_csv(out / 'affine_volume_pattern_stations.csv', index=False)
    pd.DataFrame(dict(hour_index=np.arange(8760), positive_local_station_count=(q > 0).sum(axis=0),
                     local_flow_sum_m3s=q.sum(axis=0), local_rhs_min_positive_million_m3=np.where(q>0,q,np.inf).min(axis=0)*.0036,
                     local_rhs_max_million_m3=q.max(axis=0)*.0036,
                     reservoir_release_ub_max_1000m3s=release_selected.max(axis=0))).to_csv(out / 'hours_8760.csv', index=False)
    np.savez_compressed(out / 'hourly_water_evidence.npz', hydrochn_row_id=ids.to_numpy(str),
                        hour_index=np.arange(8760), natural_reach_m3s=natural,
                        available_station_m3s=available, local_after_cascade_m3s=q,
                        source_storage_m3=old_storage, selected_storage_m3=selected_storage,
                        safe_incoming_budget_m3=safe_budget)
    time_audit['station_hour_count'] = int(q.size)
    invalids = dict(nonfinite_storage=int((~np.isfinite(old_storage)).sum()),
                   negative_active_storage=int((old_storage < 0).sum()),
                   dead_above_normal=int((s.source_v_min_gl > s.source_v_max_gl).sum()),
                   inconsistent_active_identity=int((np.abs(old_storage/1e6-(s.source_v_max_gl-s.source_v_min_gl))>1e-7).sum()),
                   invalid_hourly_inflow=int(((~np.isfinite(q)) | (q<0)).sum()))
    report = dict(generated_at=datetime.now(timezone.utc).isoformat(), audit_status='COMPLETE',
                  physical_input_certification='NOT_CERTIFIED', lp_built=False, solver_called=False,
                  source_rows=len(original), reservoirs=len(s), hours=8760, station_hours=int(q.size),
                  hydrology_dust_cleanup_disabled=True, time_axis=time_audit, invalid_counts=invalids,
                  lineage=lineage,
                  repeated_dead_fraction_counts=s.source_dead_fraction_rounded7.value_counts().head(2).to_dict(),
                  affine_signature=dict(slope_gl_per_original_mw=float(slope), intercept_gl=float(intercept),
                                        matching_reservoirs=int(s.affine_volume_pattern.sum()),
                                        matching_with_changed_capacity=int((s.affine_volume_pattern & ~np.isclose(s.current_to_source_capacity_ratio,1)).sum()),
                                        interpretation='Observed original-file pattern, not verified physical data or an approved correction rule'),
                  source_storage_above_safe_annual_water=int(s.source_storage_exceeds_annual_budget.sum()),
                  source_storage_above_10annual_water=int(s.source_storage_exceeds_10annual_budgets.sum()),
                  source_storage_above_100annual_water=int(s.source_storage_exceeds_100annual_budgets.sum()),
                  avoidable_large_inventory_bound_entries=int(s.source_storage_exceeds_annual_budget.sum()*8760),
                  source_storage_rated_emptying_above_year=int((s.source_rated_emptying_days>365).sum()),
                  source_total_active_storage_m3=float(old_storage.sum()),
                  selected_total_active_storage_m3=float(selected_storage.sum()),
                  source_max_inventory_m3=float(old_storage.max()),
                  selected_max_effective_inventory_m3=float(selected_effective.max()),
                  corrected_storage_stations=int((selected_storage != old_storage).sum()),
                  missing_raw_hydrology_comids=0,
                  limitations=['All-hour input audit, not a full-year optimization or a condition-number estimate.',
                               'Large storage-to-local-inflow ratio alone cannot establish an error at a cascade station.',
                               'Annual-water bound removes unnecessary inventory offsets under the current cyclic equations; it is not measured regulating storage.',
                               'Affine and repeated-ratio patterns flag missing engineering provenance, not automatic numerical corruption.'])
    (out / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (out / 'effective_config.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    index = pd.read_csv(ROOT / 'data/hydro/timeseries_index.csv')
    files = [original_path, ROOT/'data'/raw['hydro'].get('station_parameters_file','hydro/hydro_stations.csv'),
             inventory_path, stage2_path, backbone_path, Path(__file__), cfg.path]
    files += [Path(value) for value in index.loc[index.dataset.isin(['hourly_discharge_2019','monthly_environmental_flow_2019_p30']), 'path']]
    provenance = dict(git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                      sources=[dict(path=str(f.resolve()), bytes=f.stat().st_size, sha256=sha256(f)) for f in dict.fromkeys(files)])
    (out / 'source_manifest.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
