"""Read-only hydrology provenance and arithmetic ablations; never builds/solves an LP.

Run with the existing RL Python environment. All outputs stay beside this script.
Counterfactual columns are diagnostic arithmetic, not corrected production inputs.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PROCESS = ROOT.parent / 'Gis_process/hydro_power/process_hydro'
STAGE1 = PROCESS / 'hydro_model_2019_stage1_20260629'
RETURNS = ROOT.parent / 'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
EVIDENCE = ROOT / 'supplementary_materials/reviews/completed_acceptance_20261020/evidence/base2060'
sys.path.insert(0, str(ROOT))
from cispo_model.hydro import HydroProfileReader, _station_flow_share_by_comid
from cispo_model.timeblocks import TimeBlock


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def main():
    checks = {}
    cfg = json.loads((EVIDENCE / 'model_config_snapshot.json').read_text(encoding='utf-8'))['resolved_configuration']
    hydro_cfg = cfg['hydro']
    stations_path = ROOT / 'data/hydro/repaired_storage_audit_20260913_v2/hydro_stations.csv'
    st = pd.read_csv(stations_path)
    original_st = pd.read_csv(ROOT / 'data/hydro/hydro_stations.csv')
    inv_path = PROCESS / 'hydro_phs_module/data_output/hydrochn_ght2026_updated.csv'
    inv = pd.read_csv(inv_path)
    raw_path = PROCESS / 'HydroCHN-main/HydroCHN-main/Hydropower_resource_China.csv'
    raw = pd.read_csv(raw_path)
    checks['station_rows'] = len(st)
    checks['unique_comids'] = int(st.comid.nunique())
    checks['source_raw_rows'] = len(raw)
    checks['all_raw_comids_preserved'] = bool(np.array_equal(raw.comid, inv.comid))
    checks['all_raw_heads_preserved'] = bool(np.array_equal(raw['H_Max (m)'], inv['H_Max (m)']))
    checks['inventory_to_model_capacity_max_abs_gw'] = float(np.max(np.abs(st.capacity_potential_gw - inv.capacity_mw_model / 1000)))
    checks['inventory_to_model_head_max_abs_m'] = float(np.max(np.abs(st.head_m - inv['H_Max (m)'])))
    checks['repaired_vs_original_head_max_abs_m'] = float(np.max(np.abs(st.head_m - original_st.head_m)))
    checks['repaired_vs_original_qrated_max_abs_m3s'] = float(np.max(np.abs(st.q_rated_m3s - original_st.q_rated_m3s)))
    checks['existing_station_capacity_gw'] = float(st.existing_capacity_gw.sum())
    checks['pumped_label_rows'] = int(st.technology_type_ght.fillna('').str.contains('pumped', case=False).sum())
    implied_eta = st.capacity_potential_gw * 1e9 / (1000 * 9.81 * st.head_m * st.q_rated_m3s)
    checks['qrated_implied_eta_min_max'] = [float(implied_eta.min()), float(implied_eta.max())]
    checks['production_reservoir_eta'] = hydro_cfg['reservoir_efficiency']

    ts = pd.read_csv(ROOT / 'data/hydro/timeseries_index.csv')
    hourly_path = Path(ts.loc[ts.dataset.eq('hourly_discharge_2019'), 'path'].iloc[0])
    env_path = Path(ts.loc[ts.dataset.eq('monthly_environmental_flow_2019_p30'), 'path'].iloc[0])
    three_path = STAGE1 / 'data_intermediate/grfr_target_comids_3h_2019.nc'
    with Dataset(hourly_path) as ds:
        q = np.asarray(ds['qout_model_m3s'][:], dtype=float)
        comids = np.asarray(ds['comid'][:], dtype=np.int64)
        time = ds['time']
        checks['hourly_time_range'] = [str(v) for v in num2date(time[[0, -1]], time.units)]
        checks['hourly_time_steps_s'] = np.unique(np.diff(time[:])).tolist()
    with Dataset(three_path) as ds:
        qr = np.asarray(ds['qout_raw_m3s'][:], dtype=float)
        qc = np.asarray(ds['qout_model_m3s'][:], dtype=float)
        checks['three_hour_shape'] = list(qr.shape)
        checks['negative_raw_values'] = int((qr < 0).sum())
        checks['negative_clipping_max_error_m3s'] = float(np.max(np.abs(qc - np.maximum(qr, 0))))
        checks['hourly_hold_max_error_m3s'] = float(np.max(np.abs(q - np.repeat(qc, 3, axis=0))))
    checks['hourly_shape'] = list(q.shape)
    checks['hourly_nonfinite'] = int((~np.isfinite(q)).sum())
    checks['hourly_sha_matches_index'] = digest(hourly_path) == ts.loc[ts.dataset.eq('hourly_discharge_2019'), 'source_sha256'].iloc[0]
    with Dataset(env_path) as ds:
        env = np.asarray(ds['monthly_p30_proxy_m3s'][:], dtype=float)
        checks['environment_comid_axis_equal'] = bool(np.array_equal(comids, ds['comid'][:]))
    months = pd.date_range('2019-01-01', periods=8760, freq='h').month.to_numpy()
    p10 = np.stack([np.percentile(q[months == m], 10, axis=0) for m in range(1, 13)])
    p30 = np.stack([np.percentile(q[months == m], 30, axis=0).astype('float32') for m in range(1, 13)])
    checks['monthly_p30_recompute_max_error_m3s'] = float(np.max(np.abs(p30 - env)))
    position = pd.Index(comids).get_indexer(st.comid)
    checks['missing_station_comids'] = int((position < 0).sum())
    assert (position >= 0).all()
    qs = q[:, position]
    after10 = np.maximum(qs - p10[months-1][:, position], 0)
    after30 = np.maximum(qs - env[months-1][:, position], 0)
    share = _station_flow_share_by_comid(st)
    checks['duplicate_comid_station_rows'] = int(st.comid.duplicated(keep=False).sum())
    checks['duplicate_comid_existing_gw'] = float(st.loc[st.comid.duplicated(keep=False), 'existing_capacity_gw'].sum())
    checks['affected_existing_rows'] = int(((share < 1) & (st.existing_capacity_gw > 0)).sum())
    scenarios = {
        'raw_no_share': qs,
        'p10_no_share': after10,
        'p30_no_share': after30,
        'raw_with_share': qs * share,
        'p30_with_share': after30 * share,
    }
    cap_existing = st.existing_capacity_gw.to_numpy()
    cap2060 = pd.read_csv(EVIDENCE / 'hydro_capacity.csv').set_index('hydrochn_row_id').loc[st.hydrochn_row_id, 'capacity_gw'].to_numpy()
    conv = st.head_m.to_numpy() * 1000 * 9.81 * float(hydro_cfg['reservoir_efficiency']) / 1e9
    ror = st.operation_type_model.eq('run_of_river').to_numpy()
    result = st[['hydrochn_row_id', 'plant_name_model', 'province_code', 'province_name_zh', 'comid', 'operation_type_model', 'status_model', 'existing_capacity_gw', 'capacity_potential_gw', 'head_m', 'q_rated_m3s']].copy()
    result['flow_share'] = share
    result['base2060_capacity_gw'] = cap2060
    result['raw_mean_m3s'] = qs.mean(axis=0)
    result['p30_mean_available_m3s'] = after30.mean(axis=0)
    result['p30_zero_available_fraction'] = (after30 == 0).mean(axis=0)
    result['p30_water_removal_fraction'] = 1 - after30.sum(axis=0) / np.maximum(qs.sum(axis=0), 1e-30)
    aggregates = pd.read_csv(ROOT / 'data/hydro/provincial_aggregate_capacity_2025.csv')
    aggprofile = pd.read_csv(ROOT / 'data/hydro/provincial_aggregate_monthly_capacity_factor_2019.csv')
    agg_results = []
    national = []
    monthly_errors = []
    for name, flow in scenarios.items():
        # Reservoir is fixed-head power, ROR follows the production capacity/q_rated formula.
        cf = np.clip(flow / st.q_rated_m3s.to_numpy(), 0, 1)
        existing_natural_gwh = (cf * cap_existing).sum(axis=0)
        for capname, cap in [('existing', cap_existing), ('base2060', cap2060)]:
            energy = np.minimum(flow * conv, cap).sum(axis=0)
            energy[ror] = (cf[:, ror] * cap[ror]).sum(axis=0)
            result[f'{capname}_{name}_instant_gwh'] = energy
        result[f'existing_{name}_water_energy_gwh'] = (flow * conv).sum(axis=0) * (cap_existing > 0)
        result[f'existing_{name}_profile_gwh'] = existing_natural_gwh
        agg_energy = 0.0
        for a in aggregates.itertuples():
            selected = (st.province_code.to_numpy() == a.province_code) & (cap_existing > 0)
            if not selected.any():
                selected = cap_existing > 0
            profile = np.average(cf[:, selected], axis=1, weights=cap_existing[selected])
            energy = float(profile.sum() * a.provincial_aggregate_capacity_gw)
            agg_results.append({'province_code':a.province_code, 'scenario':name, 'capacity_gw':a.provincial_aggregate_capacity_gw, 'energy_gwh':energy})
            agg_energy += energy
            if name == 'p30_with_share':
                for m in range(1, 13):
                    expected = float(aggprofile.loc[(aggprofile.province_code == a.province_code) & (aggprofile.month == m), 'availability_capacity_factor'].iloc[0])
                    monthly_errors.append(abs(profile[months == m].mean() - expected))
        national.append({'scenario':name,
            'existing_station_instant_twh':result[f'existing_{name}_instant_gwh'].sum()/1000,
            'base2060_station_instant_twh':result[f'base2060_{name}_instant_gwh'].sum()/1000,
            'aggregate_proxy_twh':agg_energy/1000,
            'existing_total_instant_proxy_twh':result[f'existing_{name}_instant_gwh'].sum()/1000+agg_energy/1000,
            'base2060_total_instant_proxy_twh':result[f'base2060_{name}_instant_gwh'].sum()/1000+agg_energy/1000})
    checks['aggregate_profile_recompute_max_abs_cf_error'] = float(max(monthly_errors))
    result.to_csv(OUT / 'station_diagnostic.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(national).to_csv(OUT / 'national_arithmetic_ablations.csv', index=False)
    pd.DataFrame(agg_results).to_csv(OUT / 'aggregate_arithmetic_ablations.csv', index=False)

    # Call the production reader only: there is no Gurobi model or optimization.
    nodes = pd.read_csv(ROOT / 'data/hydro/cascade_topology_nodes.csv')
    edges = pd.read_csv(ROOT / 'data/hydro/cascade_topology_edges.csv')
    fake_data = SimpleNamespace(hydro_stations=st, province_codes=aggregates.province_code.to_numpy(),
        load=pd.DataFrame({'hour_index':np.arange(8760), 'datetime_bj':pd.date_range('2019-01-01', periods=8760, freq='h')}),
        hydro_cascade_nodes=nodes, hydro_cascade_edges=edges)
    config = SimpleNamespace(raw=cfg, hours=8760)
    with HydroProfileReader(config, fake_data) as reader:
        reader_q = reader._available_flow_for_rows(TimeBlock(0,0,8760), np.arange(len(st)))
        expected_q = after30.copy()
        expected_q[expected_q < hydro_cfg['hydrology_flow_zero_tolerance_m3s']] = 0
        expected_q *= share
        checks['independent_vs_production_available_flow_max_abs_m3s'] = float(np.max(np.abs(reader_q - expected_q)))
        block = reader.read_linear_block(TimeBlock(0,0,8760))
    save_json('cascade_reader_audit.json', block.cascade_reconciliation_audit)
    # Reconciliation identity: natural target = local + lagged upstream natural * transfer.
    node_rows = {str(n.node_id):np.flatnonzero(st.hydrochn_row_id.isin(str(n.hydrochn_row_ids).split(';'))) for n in nodes.itertuples()}
    natural = {k:reader_q[:,v].sum(axis=1) for k,v in node_rows.items()}
    localpos = {int(r):i for i,r in enumerate(block.reservoir_station_rows)}
    local = {k:block.reservoir_local_inflow_m3s[[localpos[int(r)] for r in v]].sum(axis=0) for k,v in node_rows.items()}
    for e, frac in zip(edges.itertuples(), block.cascade_edge_transfer_fraction):
        local[e.target_node_id] += np.roll(natural[e.source_node_id], e.travel_lag_h) * frac
    checks['cascade_natural_reconstruction_max_abs_m3s_after_cleanup'] = float(max(np.max(np.abs(natural[k]-local[k])) for k in local))
    checks['cascade_nodes'] = len(nodes)
    checks['cascade_edges'] = len(edges)
    checks['cascade_existing_capacity_gw'] = float(nodes.existing_capacity_gw.sum())

    # Actual exported results, separate from arithmetic diagnostic counterfactuals.
    annual = []
    province_actual = []
    for year in (2030,2040,2050,2060):
        folder = RETURNS / f'base{year}'
        gen = pd.read_csv(folder / 'annual_generation_by_province_technology.csv')
        cap = pd.read_csv(folder / 'annual_capacity_by_province_technology.csv')
        gen = gen[gen.technology.isin(['reservoir','ror','hydro_aggregate'])]
        cap = cap[cap.technology.isin(['reservoir','ror','hydro_aggregate'])]
        combined = gen.merge(cap[['province_code','technology','capacity']], on=['province_code','technology'])
        combined['year'] = year
        combined['utilization_h'] = combined.generation_gwh / combined.capacity.replace(0,np.nan)
        province_actual.append(combined)
        summary = combined.groupby('technology')[['generation_gwh','capacity']].sum().reset_index()
        summary['year'] = year
        summary['utilization_h'] = summary.generation_gwh / summary.capacity
        annual.append(summary)
    pd.concat(annual).to_csv(OUT / 'actual_national_by_technology.csv',index=False)
    actual = pd.concat(province_actual)
    actual.to_csv(OUT / 'actual_province_by_technology.csv',index=False)
    prov = result.groupby(['province_code','province_name_zh']).sum(numeric_only=True).reset_index()
    prov = prov[['province_code','existing_capacity_gw','base2060_capacity_gw'] + [c for c in prov if c.endswith('_instant_gwh')]]
    prov = aggregates[['province_code','province_name_zh']].merge(prov, on='province_code', how='left').fillna(0)
    for n in scenarios:
        ap = pd.DataFrame(agg_results).query('scenario == @n').set_index('province_code').energy_gwh
        prov[f'aggregate_{n}_gwh'] = prov.province_code.map(ap)
    act = actual.query('year == 2060').groupby('province_code')[['generation_gwh','capacity']].sum()
    prov['actual2060_generation_gwh'] = prov.province_code.map(act.generation_gwh)
    prov['actual2060_total_capacity_gw'] = prov.province_code.map(act.capacity)
    prov['actual2060_utilization_h'] = prov.actual2060_generation_gwh / prov.actual2060_total_capacity_gw
    # These two primary-source values are historical scale checks, not a same-fleet hindcast.
    benchmarks = {42: (133027.0, 'https://tjj.hubei.gov.cn/tjsj/tjgb/ndtjgb/qstjgb/202003/t20200323_2188487.shtml'),
                  53: (266566.0, 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjgb/202004/t20200414_1204433.html')}
    prov['official2019_generation_gwh'] = prov.province_code.map({k:v[0] for k,v in benchmarks.items()})
    prov['official2019_source_url'] = prov.province_code.map({k:v[1] for k,v in benchmarks.items()})
    prov['model2060_minus_official2019_gwh_scale_check_only'] = prov.actual2060_generation_gwh - prov.official2019_generation_gwh
    prov['official_comparison_status'] = np.where(prov.official2019_generation_gwh.notna(), 'HISTORICAL_SCALE_ONLY_DIFFERENT_FLEET_AND_SCOPE', 'NOT_VERIFIED_NO_VALUE_INVENTED')
    prov.to_csv(OUT / 'province_diagnostic.csv', index=False, encoding='utf-8-sig')
    save_json('checks.json', checks)
    inputs = [stations_path, inv_path, raw_path, hourly_path, env_path, three_path, EVIDENCE/'hydro_capacity.csv', EVIDENCE/'model_config_snapshot.json', ROOT/'cispo_model/hydro.py', ROOT/'scripts/build_cispo_data_package.py']
    save_json('input_manifest.json', [{'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)} for p in inputs])
    print(json.dumps({'checks':checks,'arithmetic':national},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
