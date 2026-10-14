"""Verify author-approved 2030 inputs and two actual 1h build-only artifacts.

Usage: python scripts/verify_case3_parameters.py --output NEW_DIRECTORY
Uses the local configured data roots. Never solves or changes source inputs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def differences(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return sum((differences(a.get(k), b.get(k), prefix+'.'+k)
                    for k in sorted(a.keys() | b.keys())), [])
    return [] if a == b else [{'key': prefix.lstrip('.'), 'case3': a, 'nocredit': b}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-root', type=Path, help='Reuse retained build-only evidence; never overwrites it')
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    from cispo_model.config import load_model_config
    from cispo_model.data import load_model_data, DATA_ROOT
    from cispo_model.run_contract import analysis_case_identity
    scenarios = ['case3_thermal_ev_v5', 'case3_thermal_ev_v5_nocredit']
    configs = [load_model_config('config/optimization_numeric_dac_by_year_v9.json',
        scenario_path=f'config/scenarios/{s}.json') for s in scenarios]
    rows = []
    def check(label, actual, expected, source):
        if isinstance(expected, (float, int)) and not isinstance(expected, bool):
            arr = np.asarray(actual)
            passed = bool(np.isfinite(arr).all() and np.allclose(arr, expected, rtol=1e-12, atol=1e-12))
            actual = float(arr) if arr.ndim == 0 else {'min':float(arr.min()),'max':float(arr.max())}
        else:
            passed = actual == expected
        rows.append(dict(parameter=label, actual=actual, expected=expected, passed=passed, source=source))
    diff = differences(configs[0].raw, configs[1].raw)
    allowed = {'scenario.id', 'scenario.description', 'scenario.analysis_role', 'security.capacity_margin_load_basis'}
    check('resolved_config_difference_scope', all(d['key'] in allowed for d in diff), True,
          'resolved configuration; identity labels reported separately')
    data = load_model_data(configs[0]); service = data.flexible_load_v4
    settings = configs[0].raw['flexible_load']
    check('base_case', configs[0].raw['scenario']['parent_baseline_case_id'],
          'base_2024_numeric_water_dac_by_year_20260913_v9', 'resolved configuration')
    check('v1g_fraction', settings['ev_v1g']['shiftable_energy_fraction'], .2, 'resolved configuration')
    check('v2g_fraction_total_fleet', settings['ev_v2g']['participation_fraction'], .1, 'resolved configuration')
    check('v2g_cap_gw', settings['ev_v2g']['national_contracted_power_cap_gw_by_planning_year']['2030'], 10., 'resolved configuration')
    check('legacy_bidirectional_activation', service.legacy_bidirectional_activation, False, 'loaded service costs')
    for component, retention, duration in [('heating',.94,4),('cooling',.92,5)]:
        for key, expected in [('retention_per_hour',retention), ('positive_state_duration_hours',duration),
                              ('negative_state_duration_hours',duration)]:
            check(component+'.'+key, service.thermal_parameters[component][key], expected, 'loaded thermal parameters')
        upstream_manifest = json.loads((DATA_ROOT/'load/flexible_load_envelope_v3.manifest.json').read_text())
        check(component+'.comfort_band_delta_c', upstream_manifest[component+'_comfort_band_c'], 1., 'SHA-linked upstream envelope manifest')
    cost_expected = {'heating':(40,300,0,0), 'cooling':(40,300,0,0),
                     'ev_v1g':(40,30,0,0), 'ev_v2g':(50,150,40,150)}
    for s, expected in cost_expected.items():
        for field, val in zip(('enablement_cost_yuan_per_kw_year','activation_cost_yuan_per_mwh',
                               'infrastructure_cost_yuan_per_kw_year','degradation_cost_yuan_per_mwh'),expected):
            check(s+'.'+field, service.service_costs[s][field], val, 'loaded service costs; thermal legacy activation unused')
    for s in ('heating','cooling'):
        for direction, val in [('release',40),('precondition',0)]:
            check(s+'.activation_'+direction, service.service_costs[s]['activation_cost_'+direction+'_yuan_per_mwh'], val, 'loaded directional costs')
    check('v1g.power_ratio', settings['ev_v1g']['maximum_power_to_daily_average_ratio'], 2., 'resolved configuration')
    check('ev.charge_efficiency', settings['ev_v2g']['charge_efficiency'], .94, 'resolved configuration')
    check('ev.discharge_efficiency', settings['ev_v2g']['discharge_efficiency'], .94, 'resolved configuration')
    check('v2g.duration_h', settings['ev_v2g']['power_duration_hours'], 4., 'resolved configuration')
    baseline = data.load_components_gw['ev']
    daily = baseline.reshape(31,365,24).mean(axis=2).repeat(24,axis=1)
    check('ev.actual_charge_envelope_error_gw', service.ev_availability['available_charge_power_gw'] - np.maximum(.2*baseline, 2*.2*daily), 0., 'loaded 8760h inputs')
    check('ev.actual_24h_inventory_error_gwh', service.ev_availability['fleet_energy_capacity_gwh'] - .94*.2*daily*24, 0., 'loaded 8760h inputs')
    upstream = pd.read_csv(DATA_ROOT/'load/flexible_load_envelope_v3.csv.gz')
    upstream = upstream.loc[upstream.year == 2030]
    for c, fraction in [('heating',.25),('cooling',.2)]:
        for short, long in [('up','increase'),('down','reduction')]:
            values = upstream.pivot(index='province_code',columns='hour_index',values=f'{c}_{long}_limit_gw').reindex(data.provinces.province_code).to_numpy()
            check(c+'.participation_'+short+'_error_gw', service.thermal_envelopes_gw[c+'_'+short] - fraction*values, 0., 'loaded 8760h envelopes versus upstream envelope')
    firm = settings['firm_capacity_credit']
    check('credit.duration_h', firm['required_event_duration_hours'], 4., 'resolved configuration')
    for s, val in [('heating',.5),('cooling',.6),('ev_v1g',.5),('ev_v2g',.5)]:
        check('credit.'+s, firm['derating_fraction'][s], val, 'resolved configuration')
    check('credit.peak_reference', firm['peak_reference'], 'four_hour_window_containing_immutable_full_year_province_baseline_peak_v1', 'resolved configuration')
    for cfg, s in zip(configs, scenarios):
        build_root = args.build_root.resolve() if args.build_root else out
        command = [sys.executable,'-B',str(ROOT/'scripts/run_cispo_2030_full_year.py'),
            '--config',str(cfg.path),'--scenario-config',str(cfg.scenario_path),'--diagnostic-hours','1',
            '--build-only','--archive-original-model','--output-dir',str(out/s)]
        (out/(s+'_command.json')).write_text(json.dumps(command,indent=2))
        if not args.build_root:
            with (out/(s+'.stdout.log')).open('w',encoding='utf-8') as stdout, (out/(s+'.stderr.log')).open('w',encoding='utf-8') as stderr:
                result = subprocess.run(command,cwd=ROOT,stdout=stdout,stderr=stderr)
            if result.returncode:
                raise RuntimeError(s+' build failed; all logs retained')
        snapshot = json.loads((build_root/s/'model_config_snapshot.json').read_text(encoding='utf-8'))
        check(s+'.build_resolved_config_identity', snapshot['resolved_configuration'] == cfg.raw, True, 'retained build configuration')
        build = json.loads((build_root/s/'build_report.json').read_text(encoding='utf-8'))
        check(s+'.legacy_branch', build['flexible_load_structural_audit']['legacy_bidirectional_activation'], False, 'actual build_report')
        import gurobipy as gp
        model = gp.read(str(next((build_root/s/'model_archive').glob('original.mps*'))))
        variables = model.getVars()
        for prefix, coefficient in [('heating_shift_up_gw_active[',0),('heating_shift_down_gw_active[',.04),
                                    ('cooling_shift_up_gw_active[',0),('cooling_shift_down_gw_active[',.04),
                                    ('ev_mobility_v1g_relocated_gw[',.03),('ev_mobility_discharge_gw[',.30)]:
            values = [v.Obj for v in variables if v.VarName.startswith(prefix)]
            expected_present = True
            if prefix.startswith(('heating_', 'cooling_')):
                component, _, direction, *_ = prefix.split('_')
                expected_present = bool(np.any(service.thermal_envelopes_gw[component+'_'+direction][:,0] > 0))
            check(s+'.objective_present.'+prefix, bool(values), expected_present, 'actual original MPS versus nonzero control support in selected hour')
            if values:
                check(s+'.objective.'+prefix, values, coefficient, 'actual original MPS objective, million CNY/GWh')
        credit = [v for v in variables if v.VarName.startswith('firm_flexible_capacity_credit_gw[')]
        check(s+'.credit_variables', len(credit), 124 if s == scenarios[0] else 0, 'actual original MPS')
        model.dispose()
        print(s+' parameter build complete',flush=True)
    manifest = DATA_ROOT/settings['v5_input_files']['input_manifest_file']
    report = dict(status='PASS' if all(r['passed'] for r in rows) else 'FAIL', checks=rows,
        build_root=str(build_root),
        resolved_differences=diff, input_manifest_sha256=sha(manifest),
        scientific_fingerprints={s:analysis_case_identity(c)['resolved_scientific_configuration_sha256'] for s,c in zip(scenarios,configs)},
        scope='1h build-only; production screening adds its own scientific identity; no planning conclusions',
        legacy_cost_note='Config 300/400 legacy scalars and thermal legacy activation 300 are unused by V5 directional/EV objective; actual MPS coefficients checked.')
    (out/'parameter_verification_2030.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 2030 参数核准','', '|参数|实际值|核准值|判定|','|---|---|---|---|']
    lines += [f"|{r['parameter']}|{r['actual']}|{r['expected']}|{'PASS' if r['passed'] else 'FAIL'}|" for r in rows]
    (out/'PARAMETERS_ZH.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(report['status'],flush=True)
    if report['status'] != 'PASS': raise SystemExit(2)


if __name__ == '__main__':
    main()
