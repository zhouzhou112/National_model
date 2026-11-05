"""Read-only T9 inertia diagnostics from SHA-verified completed backups.

Run on T550: python t9_inertia.py --root BACKUP_RELEASE --out NEW_ANALYSIS_DIR.
No solver imports; original hourly arrays stay on T550. All capacities are GW,
inertia GW s, and raw duals million CNY/(GW s). RUC starts/stops are continuous
capacity changes, not counts of discrete physical unit starts.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def mean(a, mask):
    return float(np.mean(a[mask])) if np.any(mask) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    assert root.parent == Path('/home/zz2/National_model_server/cloud_backup')
    assert out.parent == Path('/home/zz2/National_model_server/analysis_tools_20261105_t9')
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    backup = json.loads((root / 'backup_manifest.json').read_text())
    src = root / 'output_8760'
    assert sha(src / 'result_manifest.json') == backup['source_result_manifest_sha256']
    manifest = json.loads((src / 'result_manifest.json').read_text())
    records = {r['path']: r for r in manifest['files']}
    brecords = {r['path']: r for r in backup['files']}
    names = ['hourly_province_security.csv.gz', 'hourly_province_balance.csv.gz',
             'hourly_marginal_prices.csv.gz', 'thermal_dispatch.npz', 'model_config_snapshot.json']
    inputs = {}
    for name in names:
        p = src / name
        record = records.get(name, brecords.get('output_8760/' + name))
        assert record is not None, 'Unanchored input: ' + name
        actual = sha(p)
        assert actual == record['sha256'], 'Input SHA mismatch: ' + name
        assert p.stat().st_size == record['bytes'], 'Input byte mismatch: ' + name
        inputs[name] = dict(source=str(p), sha256=actual, bytes=p.stat().st_size)
        print('SHA PASS', name, flush=True)
    save(out / 't9_input_identity.json', inputs)
    frames = [pd.read_csv(src / name) for name in names[:3]]
    keys = ['province_code', 'hour_index', 'datetime_bj']
    sec, bal, price = [f.sort_values(keys).reset_index(drop=True) for f in frames]
    assert sec[keys].equals(bal[keys]) and sec[keys].equals(price[keys]), 'hour/province/time mismatch'
    assert not sec.duplicated(keys[:2]).any() and len(sec) == 31 * 8760
    config = json.loads((src / 'model_config_snapshot.json').read_text())
    security = config.get('resolved_configuration', config)['security']
    coefficient = security.get('minimum_system_inertia_seconds')
    if coefficient is None:
        coefficient = float(security['inertia_reference_seconds']) * float(security['inertia_tolerance_fraction'])
    coefficient = float(coefficient)
    assert coefficient > 0
    thermal = np.load(src / 'thermal_dispatch.npz', allow_pickle=False)
    provinces = thermal['province_codes'].astype(int)
    hours = thermal['hour_index'].astype(int)
    techs = thermal['technologies'].astype(str)
    assert np.array_equal(hours, np.arange(8760)) and len(provinces) == 31
    assert sorted(provinces.tolist()) == sorted(sec.province_code.unique().tolist())
    arrays = {key: thermal[key] for key in ['online_capacity_gw', 'startup_capacity_gw', 'shutdown_capacity_gw', 'net_generation_gw']}
    for key, arr in arrays.items():
        assert arr.shape == (31, len(techs), 8760) and np.isfinite(arr).all(), key
    for f in [sec, bal, price]:
        numeric = f.select_dtypes(include='number').to_numpy()
        assert np.isfinite(numeric).all(), 'nonfinite source table'
    result, distribution, joint, by_tech = [], [], [], []
    max_gen_error = 0.
    max_inertia_closure = 0.
    max_requirement_error = 0.
    max_online_transition_error = float(np.abs(arrays['online_capacity_gw'] - np.roll(arrays['online_capacity_gw'], 1, axis=2) - arrays['startup_capacity_gw'] + arrays['shutdown_capacity_gw']).max())
    slack_bins = [-np.inf, 0., 1e-6, 1e-4, 1e-2, 1., np.inf]
    slack_labels = ['negative', '0_to_1e-6', '1e-6_to_1e-4', '1e-4_to_1e-2', '1e-2_to_1', 'above_1']
    price_labels = ['negative', 'zero', 'positive_le_1', 'above_1_le_10', 'above_10_le_100', 'above_100']
    for p, province in enumerate(provinces):
        s = sec[sec.province_code == province].sort_values('hour_index')
        b = bal[bal.province_code == province].sort_values('hour_index')
        d = price[price.province_code == province].sort_values('hour_index')
        assert np.array_equal(s.hour_index, hours)
        slack = s.inertia_margin_gw_s.to_numpy()
        required = s.inertia_required_gw_s.to_numpy()
        assert np.all(required > 0), 'nonpositive requirement needs explicit zero-denominator handling'
        pi = d.inertia_pi_million_cny_per_gw_s.to_numpy()
        component = coefficient * pi * 1000.
        bound = slack <= 1e-6 * required
        ratio = slack / required
        online = arrays['online_capacity_gw'][p].sum(axis=0)
        max_gen_error = max(max_gen_error, float(np.abs(arrays['net_generation_gw'][p].sum(axis=0) - b.thermal_net_generation_gw.to_numpy()).max()))
        max_inertia_closure = max(max_inertia_closure, float(np.abs(s.inertia_thermal_gw_s + s.inertia_hydro_gw_s + s.inertia_storage_gw_s - s.inertia_provided_gw_s).max()))
        max_requirement_error = max(max_requirement_error, float(np.abs(required - coefficient * b.load_gw.to_numpy()).max()))
        row = dict(province_code=int(province), hours=8760, binding_hours=int(bound.sum()), binding_share=float(bound.mean()),
                   negative_slack_hours=int((slack < 0).sum()), minimum_slack_gw_s=float(slack.min()),
                   maximum_slack_gw_s=float(slack.max()), minimum_relative_slack=float(ratio.min()),
                   high_dual_hours=int((component > 100).sum()),
                   complementarity_sum_million_cny=float(np.sum(slack*pi)),
                   complementarity_abs_sum_million_cny=float(np.sum(np.abs(slack*pi))),
                   complementarity_abs_max_million_cny=float(np.max(np.abs(slack*pi))))
        for group, mask in [('binding', bound), ('nonbinding', ~bound)]:
            for field in ['inertia_thermal_gw_s', 'inertia_hydro_gw_s', 'inertia_storage_gw_s']:
                row[f'{group}_mean_{field}'] = mean(s[field].to_numpy(), mask)
            for field in ['thermal_net_generation_gw', 'vre_generation_gw', 'storage_discharge_gw']:
                row[f'{group}_mean_{field}'] = mean(b[field].to_numpy(), mask)
            row[f'{group}_mean_thermal_nuclear_online_capacity_gw'] = mean(online, mask)
        result.append(row)
        dates = pd.to_datetime(s.datetime_bj)
        for dimension, vector in [('hour_of_day_bj', dates.dt.hour), ('month', dates.dt.month)]:
            for value in sorted(vector.unique()):
                mask = vector.to_numpy() == value
                distribution.append(dict(province_code=int(province), dimension=dimension, value=int(value),
                                         total_hours=int(mask.sum()), binding_hours=int((bound & mask).sum()),
                                         binding_share=float(bound[mask].mean())))
        # Explicit negative-slack and negative-price bins retain all anomalies.
        sb = np.searchsorted(np.asarray(slack_bins[1:-1]), ratio, side='left')
        sb[ratio == 0] = 1
        pb = np.select([component < 0, component == 0, component <= 1, component <= 10, component <= 100], [0, 1, 2, 3, 4], default=5)
        for si, slabel in enumerate(slack_labels):
            for di, dlabel in enumerate(price_labels):
                mask = (sb == si) & (pb == di)
                joint.append(dict(province_code=int(province), relative_slack_bin=slabel, inertia_price_component_bin_cny_per_mwh=dlabel,
                                  province_hours=int(mask.sum()), complementarity_sum_million_cny=float((slack*pi)[mask].sum()),
                                  complementarity_abs_sum_million_cny=float(np.abs(slack*pi)[mask].sum())))
        for j, tech in enumerate(techs):
            for group, mask in [('high_dual_above_100', component > 100), ('other', component <= 100)]:
                tr = dict(province_code=int(province), technology=str(tech), hour_group=group, hours=int(mask.sum()))
                for key, arr in arrays.items():
                    tr['mean_' + key] = mean(arr[p, j], mask)
                    if key in ['startup_capacity_gw', 'shutdown_capacity_gw']:
                        tr['sum_' + key] = float(arr[p, j, mask].sum())
                by_tech.append(tr)
    tables = {'inertia_binding_by_province.csv': result, 'inertia_binding_by_hour_month.csv': distribution,
              'inertia_slack_dual_joint_distribution.csv': joint, 'inertia_online_startup_by_technology.csv': by_tech}
    for name, rows in tables.items():
        pd.DataFrame(rows).to_csv(out / name, index=False)
        assert (out / name).stat().st_size <= 30_000_000
    assert sum(r['province_hours'] for r in joint) == 31 * 8760
    assert max_gen_error < 1e-8 and max_inertia_closure < 1e-8 and max_requirement_error < 1e-8
    summary = dict(status='PASS', task='T9', release=str(root), inputs=inputs, script_sha256=sha(__file__),
                   command=['t9_inertia.py', '--root', str(root), '--out', str(out)],
                   finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), seconds=time.monotonic()-start,
                   inertia_seconds=coefficient, binding_rule='margin <= 1e-6 * required',
                   price_component='inertia_seconds * raw inertia_pi * 1000 CNY/MWh',
                   self_check=dict(province_hours=31*8760, thermal_net_reconstruction_max_abs_gw=max_gen_error,
                                   inertia_components_max_abs_gw_s=max_inertia_closure, requirement_load_max_abs_gw_s=max_requirement_error,
                                   cyclic_online_startup_shutdown_max_abs_gw=max_online_transition_error),
                   binding_hours=sum(r['binding_hours'] for r in result), binding_share=sum(r['binding_hours'] for r in result)/(31*8760),
                   high_dual_hours=sum(r['high_dual_hours'] for r in result),
                   complementarity_sum_million_cny=sum(r['complementarity_sum_million_cny'] for r in result),
                   exceptions=[], notes=['Physical binding uses primal slack, independently of positive Barrier duals.',
                                         'Thermal export includes nuclear; technology rows separate every class.',
                                         'RUC startup/shutdown are continuous GW, not binary unit counts.',
                                         'Negative slack/duals retained; missing group means are blank, never zero.',
                                         'Slack ratio bin endpoints are right-closed; zero is in 0_to_1e-6.'])
    save(out / 't9_summary.json', summary)
    print(json.dumps({k: summary[k] for k in ['status', 'seconds', 'binding_share', 'high_dual_hours', 'self_check']}), flush=True)


if __name__ == '__main__':
    main()
