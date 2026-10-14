"""Author-defined relative_v1 assessment, independent of legacy QC/state policy.

Only the acceptance_profiles.relative_v1 subtree may be added. No archived
file, strict hard check, or candidate-state acceptance flag is changed here.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

VERSION = 'relative_v1_author_20261014_extended'
DEFERRED = 'DEFERRED_BY_AUTHOR_20261012'
REPLACED = {'power_balance', 'objective_components',
            'unidirectional_interprovincial_flow', 'reservoir_transition'}

# Only physical GW/GWh residuals are relaxed. Inertia (GW*s), water (m3),
# emissions, fuel, costs and dimensionless fractions retain their old checks.
PHYSICAL_METRICS = {
    'load_component_input_closure': 'maximum_load_component_input_closure_error_gw',
    'effective_load_reconstruction': 'maximum_effective_load_reconstruction_error_gw',
    'effective_load_nonnegative': 'minimum_effective_load_gw',
    'ev_v2g_transition': 'maximum_ev_v2g_transition_residual_gwh',
    'up_reserve': 'minimum_up_reserve_margin_gw',
    'down_reserve': 'minimum_down_reserve_margin_gw',
    'capacity_margin': 'minimum_capacity_margin_gw',
    'ruc_transition': 'maximum_ruc_transition_residual_gw',
    'thermal_online_capacity': 'maximum_thermal_online_capacity_violation_gw',
    'thermal_minimum_generation': 'maximum_thermal_minimum_generation_violation_gw',
    'thermal_maximum_generation': 'maximum_thermal_maximum_generation_violation_gw',
    'vre_availability': 'maximum_vre_availability_violation_gw',
    'wave_availability': 'maximum_wave_availability_violation_gw',
    'hydro_aggregate_availability': 'maximum_hydro_aggregate_availability_violation_gw',
    'hydro_aggregate_monthly_energy_budget': 'maximum_hydro_aggregate_monthly_energy_budget_violation_gwh',
    'line_capacity': 'maximum_line_capacity_violation_gw',
    'nuclear_capacity_floor': 'maximum_nuclear_capacity_floor_violation_gw',
    'nuclear_capacity_upper': 'maximum_nuclear_capacity_upper_violation_gw',
    'biomass_beccs_capacity_upper': 'maximum_biomass_beccs_capacity_upper_violation_gw',
    'storage_capacity_floor': 'maximum_storage_capacity_floor_violation_gw',
    'dc_fixed_direction': 'maximum_dc_reverse_flow_gw',
    'storage_transition': 'maximum_storage_transition_residual_gwh',
    'storage_soc': 'maximum_storage_soc_upper_violation_gwh',
    'reservoir_energy': 'maximum_reservoir_energy_upper_violation_gwh',
}


def extended_physical_checks(qc):
    """Re-evaluate archived semantic residuals, preserving formulation branches.

    Strict tolerances mirror solution_export.py (1e-5; DC direction 1e-6).
    Missing/nonfinite evidence raises rather than promoting a strict failure.
    Unknown hard checks remain strict in assess_relative_v1.
    """
    hard = qc['hard_checks']
    definitions = {k: [v] for k, v in PHYSICAL_METRICS.items()}
    formulation = qc.get('flexible_load_formulation')
    service = formulation in {'service_constrained_v4', 'integrated_service_constrained_v5'}
    thermal = formulation in {'state_envelope_v2', 'comfort_envelope_v3'}
    for component in ('heating', 'cooling'):
        key = component + '_service_accounting'
        if key in hard and formulation is None:
            raise ValueError('Missing flexible_load_formulation for service assessment')
        if service:
            definitions[key] = ['maximum_v4_' + component + '_' + suffix + '_gwh'
                for suffix in ('state_transition_residual', 'periodic_boundary_residual',
                               'positive_state_bound_violation', 'negative_state_bound_violation',
                               'comfort_debt_violation')]
        elif thermal:
            definitions[key] = ['maximum_' + component + '_state_transition_residual_gwh',
                'maximum_' + component + '_daily_terminal_state_gwh',
                'minimum_' + component + '_daily_net_energy_change_gwh']
        else:
            definitions[key] = ['maximum_' + component + '_daily_energy_residual_gwh']
        for check, metric in [('state_transition', 'maximum_' + component + '_state_transition_residual_gwh'),
                              ('daily_state_reset', 'maximum_' + component + '_daily_terminal_state_gwh'),
                              ('state_loss_accounting', 'minimum_' + component + '_daily_net_energy_change_gwh')]:
            definitions[component + '_' + check] = [metric] if thermal else []
    definitions.update({
        'ev_v1g_daily_energy_conservation': [] if service else ['maximum_ev_v1g_daily_energy_residual_gwh'],
        'ev_v1g_backlog_transition': ['maximum_ev_v1g_backlog_transition_residual_gwh'] if thermal else [],
        'ev_v1g_daily_backlog_reset': ['maximum_ev_v1g_daily_terminal_backlog_gwh'] if thermal else [],
        'ev_v2g_daily_state_reset': ['maximum_ev_v2g_daily_terminal_state_gwh'] if formulation == 'comfort_envelope_v3' else [],
        'ev_combined_grid_charging_power': ['maximum_ev_combined_grid_charging_power_violation_gw'] if service or formulation == 'comfort_envelope_v3' else [],
        'v4_ev_mobility_service': ['maximum_v4_ev_' + suffix for suffix in (
            'soc_transition_residual_gwh', 'departure_soc_violation_gwh', 'soc_upper_violation_gwh',
            'charge_power_violation_gw', 'discharge_power_violation_gw')] if service else [],
    })
    for check, metric in {
        'v5_v2g_contract_nesting': 'nested_v2g_contract_violation_gw',
        'v5_v2g_national_power_cap': 'national_v2g_cap_violation_gw',
        'v5_shared_bidirectional_connection_power': 'shared_connection_power_violation_gw',
        'v5_firm_capacity_credit_physical_bound': 'firm_capacity_credit_bound_violation_gw',
    }.items():
        definitions[check] = ['maximum_v5_' + metric] if formulation == 'integrated_service_constrained_v5' else []
    checks = {}
    if (set(definitions) - set(PHYSICAL_METRICS)) & set(hard):
        if formulation not in {'daily_energy_shift_v1', 'state_envelope_v2',
                               'comfort_envelope_v3', 'service_constrained_v4',
                               'integrated_service_constrained_v5'}:
            raise ValueError('Missing or unknown flexible_load_formulation')
    for key, metrics in definitions.items():
        if key not in hard:
            continue
        strict = number(qc.get('bidirectional_flow_tolerance_gw', 1e-6), nonnegative=True) if key == 'dc_fixed_direction' else 1e-5
        limit = max(strict, 1e-3)
        observations = []
        for metric in metrics:
            value = number(qc[metric], nonnegative=not metric.startswith('minimum_'))
            violation = max(0., -value) if metric.startswith('minimum_') else value
            observations.append(dict(metric=metric, value=value, violation=violation,
                                     limit=limit, passed=violation <= limit))
        checks[key] = dict(passed=all(v['passed'] for v in observations),
            strict_passed=hard[key], strict_tolerance=strict, relative_tolerance=limit,
            observations=observations, applicable=bool(metrics))
    if 'optional_portfolio_physical_contract' in hard:
        observations = []
        for metric, raw in qc['optional_portfolio_qc'].items():
            limit = max(1e-5, 1e-3) if metric.endswith(('_gw', '_gwh')) else 1e-5
            value = number(raw, nonnegative=True)
            observations.append(dict(metric=metric, value=value, limit=limit, passed=value <= limit))
        checks['optional_portfolio_physical_contract'] = dict(
            passed=all(v['passed'] for v in observations),
            strict_passed=hard['optional_portfolio_physical_contract'], observations=observations)
    return checks


def number(value, *, nonnegative=False):
    value = float(value)
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError('Missing, nonfinite or invalid acceptance input')
    return value


def assess_relative_v1(qc, solve=None, inputs=None):
    """Pure evaluator; raises on incomplete/invalid evidence, never guesses PASS."""
    solve = solve or {}
    inputs = inputs or {}
    checks = {}
    residual = number(qc['maximum_power_balance_residual_gw'], nonnegative=True)
    by_province = inputs.get('power_by_province', [])
    if by_province:
        observations = []
        for row in by_province:
            peak = number(row['annual_peak_load_gw'], nonnegative=True)
            maximum = number(row['maximum_residual_gw'], nonnegative=True)
            limit = max(1e-3, 1e-6 * peak)
            observations.append(dict(row, limit_gw=limit, passed=maximum <= limit))
        if abs(max(r['maximum_residual_gw'] for r in observations)-residual) > 1e-12:
            raise ValueError('Province residual maxima disagree with archived QC')
        checks['power_balance'] = dict(passed=all(r['passed'] for r in observations),
                                      by_province=observations, maximum_residual_gw=residual)
    elif residual <= 1e-3:
        checks['power_balance'] = dict(passed=True, maximum_residual_gw=residual,
            proof='Global maximum <= universal 1e-3 GW floor; hence every province-hour satisfies max(1e-3,1e-6*annual_peak)',
            minimum_limit_gw=1e-3)
    else:
        raise ValueError('Per-province residual maxima and annual peaks required above universal floor')
    objective = abs(number(qc['objective_value_million_cny']))
    cost_residual = abs(number(qc['objective_component_residual_million_cny']))
    checks['objective_components'] = dict(passed=cost_residual <= 1e-7*objective,
        residual_million_cny=cost_residual, limit_million_cny=1e-7*objective,
        relative_residual=cost_residual/objective if objective else None)
    flow = copy.deepcopy(qc['interprovincial_directionality_assessment']['observed'])
    fraction = number(flow['excess_loss_share_of_system_load'], nonnegative=True)
    checks['unidirectional_interprovincial_flow'] = dict(passed=fraction <= 1e-4,
        extra_loss_share_of_load=fraction, limit=1e-4, observed=flow,
        result_reporting='NET_FLOW', denominator_scope='SELECTED_HORIZON_SYSTEM_LOAD')
    reservoir = copy.deepcopy(inputs.get('reservoir_worst', {}))
    checks['reservoir_transition'] = dict(status=DEFERRED, passed=None,
        maximum_residual_m3=number(qc['maximum_reservoir_transition_residual_m3'],nonnegative=True),
        station=reservoir, disclosure_complete=bool(reservoir))
    hard = qc['hard_checks']
    if not hard or not all(isinstance(v, bool) for v in hard.values()):
        raise ValueError('Strict hard_checks must be a nonempty boolean mapping')
    extended = extended_physical_checks(qc)
    checks['extended_gw_gwh_physical_checks'] = dict(
        passed=all(v['passed'] for v in extended.values()), checks=extended,
        failed=[k for k,v in extended.items() if not v['passed']],
        rule='max(strict_tolerance, 1e-3 GW or GWh); reference label only')
    remaining = {k:v for k,v in hard.items() if k not in REPLACED and k not in extended}
    checks['remaining_physical_hard_checks'] = dict(passed=all(remaining.values()),
        checks=remaining, failed=[k for k,v in remaining.items() if not v])
    contract = solve.get('solution_contract') or qc.get('solver_contract') or {}
    metrics = contract['barrier_primal_dual_metrics']
    pinf = number(metrics['primal_infeasibility'],nonnegative=True)
    gap = number(metrics['relative_primal_dual_objective_gap'],nonnegative=True)
    optimal = solve.get('status') == 'OPTIMAL' if solve.get('status') else contract.get('barrier_status_code') == 2
    checks['solver'] = dict(passed=optimal and pinf <= 1e-2 and gap <= 1e-2,
        optimal=optimal, barrier_primal_infeasibility=pinf, primal_limit=1e-2,
        relative_primal_dual_gap=gap, relative_gap_limit=1e-2,
        mixed_unit_quality_record_only=copy.deepcopy(solve.get('solution_quality') or qc.get('solver_quality')))
    parameters = solve.get('solver_parameters') or {}
    tolerance = parameters.get('BarConvTol', parameters.get('barrier_convergence_tolerance',
                                                          inputs.get('barrier_convergence_tolerance')))
    if tolerance is not None:
        tolerance = number(tolerance,nonnegative=True)
    disclosures = {k:copy.deepcopy(v) for k,v in qc.items()
                   if any(term in k for term in ['overlap','simultaneous','bidirectional'])}
    disclosures.update(copy.deepcopy(inputs.get('disclosures', {})))
    passed = all(row.get('passed') is not False for row in checks.values())
    return dict(version=VERSION,status='PASS' if passed else 'HARD_FAIL',checks=checks,
        strict_status_unchanged=qc['status'],
        dual=dict(grade='BARRIER_DUAL_ENGINEERING_GRADE',BarConvTol=tolerance),
        disclosures=disclosures,inputs=copy.deepcopy(inputs),
        scope='FULL_YEAR' if qc.get('optimization_hours')==8760 else 'ENGINEERING_WINDOW_ONLY',
        author_decision_reference='AGENTS.md 2026-10-12; no automatic legacy-state promotion')


def add_relative_profile(qc, solve=None, *, inputs=None, inputs_factory=None):
    """Exception-isolated extension. Errors cannot reject legacy preservation."""
    try:
        if inputs_factory is not None:
            inputs = inputs_factory()
        if inputs is None:
            inputs = qc.get('acceptance_profiles', {}).get('relative_v1', {}).get('inputs', {})
        profile = assess_relative_v1(qc, solve, inputs)
        json.dumps(profile, allow_nan=False)
    except Exception as error:
        profile = dict(version=VERSION,status='ERROR',error_type=type(error).__name__,
                       error=str(error),strict_qc_unchanged=True)
        # Keep valid context for the final preservation step, where the solver
        # report is complete even if it was unavailable during semantic export.
        try:
            json.dumps(inputs, allow_nan=False)
            profile['inputs'] = inputs
        except Exception:
            pass
    qc.setdefault('acceptance_profiles', {})['relative_v1'] = profile
    return profile


def capacity_disclosures(root):
    import pandas as pd
    result = {}
    for filename in ['vre_capacity.csv','hydro_capacity.csv','thermal_nuclear_capacity.csv',
                     'storage_capacity.csv','wave_capacity.csv','transmission_capacity.csv']:
        path = Path(root)/filename
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        values = frame['new_capacity_gw']
        selected = values[(values > 0) & (values < 1e-3)]
        result[filename] = dict(asset_rows=int(len(selected)),total_gw=float(selected.sum()),
                                negative_rows=int((values < 0).sum()))
    return result


def archived_inputs(root):
    """Optional detailed evidence, read-only and bounded to a single output."""
    import numpy as np
    import pandas as pd
    root = Path(root)
    result = {'disclosures': {'new_build_below_1mw':capacity_disclosures(root)}}
    path = root/'hourly_province_balance.csv.gz'
    if path.exists():
        maxima = {}; peaks = {}
        for chunk in pd.read_csv(path,usecols=['province_code','baseline_load_gw','balance_residual_gw'],chunksize=40000):
            for province,frame in chunk.groupby('province_code'):
                key = str(province)
                maxima[key] = max(maxima.get(key,0),float(frame.balance_residual_gw.abs().max()))
                peaks[key] = max(peaks.get(key,0),float(frame.baseline_load_gw.max()))
        qc = json.loads((root/'solution_qc.json').read_text(encoding='utf-8'))
        if qc.get('optimization_hours') == 8760:
            result['power_by_province'] = [dict(province_code=k,annual_peak_load_gw=peaks[k],
                maximum_residual_gw=maxima[k]) for k in sorted(maxima)]
    path = root/'reservoir_dispatch.npz'
    if path.exists():
        with np.load(path,allow_pickle=False) as arrays:
            volume = arrays['active_storage_m3']
            residual = volume-np.roll(volume,1,axis=1)
            residual -= (arrays['local_inflow_m3s']+arrays['upstream_release_m3s']
                         -arrays['turbine_flow_m3s']-arrays['spill_flow_m3s'])*3600
            row,hour = np.unravel_index(np.abs(residual).argmax(),residual.shape)
            result['reservoir_worst'] = dict(hydrochn_row_id=str(arrays['hydrochn_row_id'][row]),
                hour_index=int(arrays['hour_index'][hour]),
                residual_m3=float(residual[row,hour]),active_storage_m3=float(arrays['active_storage_upper_m3'][row]))
    for filename,key in [('build_report.json','numerical_robustness_audit'),
                         ('planning_state_candidate/state_metadata.json','continuation_cleanup')]:
        path=root/filename
        if path.exists():
            payload=json.loads(path.read_text(encoding='utf-8'))
            result['disclosures'][key]=payload.get(key, {'status':'NOT_RECORDED_IN_SOURCE'})
            if 'state_metadata' in filename:
                result['disclosures']['continuation_bound_closure']=payload.get('continuation_bound_closure', {'status':'NOT_RECORDED_IN_SOURCE'})
    return result
