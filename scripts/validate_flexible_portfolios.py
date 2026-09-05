"""Local Gurobi gates on real V5 inputs; this is NOT a power-system solve.

Run from the repository, optionally with CISPO_DATA_ROOT set. Outputs contain
input/code hashes, numeric and physical residuals, costs, sizes and logs.
"""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gurobipy as gp
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import DATA_ROOT, _load_flexible_load_v4_data
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.flexible_portfolio import audit_ev_pools
from cispo_model.flexible_load_numerics import prebuild_flexible_load_solver_compatibility
from cispo_model.solution_export import _value

CASES = ('case1_thermal_v5', 'case2_ev_v5', 'case3_thermal_ev_v5')


def read_service_inputs(year: int):
    config = load_model_config(scenario_path=ROOT/'config/scenarios/case3_thermal_ev_v5.json').for_planning_year(year)
    provinces = pd.read_csv(DATA_ROOT/'sets/provinces.csv').sort_values('province_code').reset_index(drop=True)
    frames = [frame.loc[frame.year.eq(year)] for frame in pd.read_csv(
        DATA_ROOT/'load/hourly_load_2025_2060.csv.gz', chunksize=100000)]
    frame = pd.concat(frames, ignore_index=True)
    if frame.duplicated(['province_code','hour_index']).any():
        raise ValueError('Duplicate baseline province/hour')
    components = {}
    for component in ('base_residual','heating','cooling','ev'):
        values = frame.pivot(index='province_code', columns='hour_index', values=f'{component}_gw').reindex(
            index=provinces.province_code, columns=range(8760)).to_numpy(float)
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError(f'Invalid {component} baseline')
        components[component] = values
    demand = frame.pivot(index='province_code', columns='hour_index', values='demand_gw').reindex(
        index=provinces.province_code, columns=range(8760)).to_numpy(float)
    if np.max(np.abs(demand-sum(components.values()))) > 1e-9:
        raise ValueError('Baseline component closure failure')
    service = _load_flexible_load_v4_data(config, provinces=provinces,
        load_components_gw=components, expected_rows=31*8760, require_manifest=True)
    return SimpleNamespace(provinces=provinces, load_gw=demand,
        load_components_gw=components, flexible_load_v4=service)


def select_provinces(data, codes):
    mask = data.provinces.province_code.isin(codes).to_numpy() if codes else np.ones(31,dtype=bool)
    if codes and int(mask.sum()) != len(codes):
        raise ValueError('Unknown or duplicate province codes')
    v = data.flexible_load_v4
    selected = replace(v,
        thermal_envelopes_gw={k:a[mask] for k,a in v.thermal_envelopes_gw.items()},
        thermal_availability={k:a[mask] for k,a in v.thermal_availability.items()},
        thermal_parameters={k:{n:a[mask] for n,a in p.items()} for k,p in v.thermal_parameters.items()},
        service_costs={k:{n:a[mask] for n,a in p.items()} for k,p in v.service_costs.items()},
        ev_availability={k:a[mask] for k,a in v.ev_availability.items()},
        ev_mobility={k:a[mask] for k,a in v.ev_mobility.items()})
    return SimpleNamespace(provinces=data.provinces.loc[mask].reset_index(drop=True),
        load_gw=data.load_gw[mask], load_components_gw={k:a[mask] for k,a in data.load_components_gw.items()},
        flexible_load_v4=selected)


def physical_qc(config, data, block, hours, start):
    selected = slice(start,start+hours)
    service = data.flexible_load_v4
    values = {key:_value(value) for key,value in block.variables.items()}
    capacity = values['flexible_service_capacity']
    qc = audit_ev_pools(settings=config.raw['flexible_load'],
        baseline_ev=data.load_components_gw['ev'][:,selected],
        availability={k:a[:,selected] for k,a in service.ev_availability.items()},
        full_availability=service.ev_availability,
        mobility={k:a[:,selected] for k,a in service.ev_mobility.items()}, values=values, capacity=capacity)
    for column, component in enumerate(('heating','cooling')):
        state, up, down = [values[f'{component}_{key}'] for key in ('state','shift_up','shift_down')]
        p = service.thermal_parameters[component]
        residual = state - p['retention_per_hour'][:,None]*np.roll(state,1,axis=1) - p['charge_efficiency'][:,None]*up + down/p['discharge_efficiency'][:,None]
        qc[f'{component}_transition_gwh'] = float(np.abs(residual).max())
        qc[f'{component}_inventory_gwh'] = float(np.maximum(state - p['positive_state_duration_hours'][:,None]*capacity[:,column,None],0).max())
        qc[f'{component}_contract_power_gw'] = float(np.maximum(up+down - service.thermal_availability[component][:,selected]*capacity[:,column,None],0).max())
    qc['load_reconstruction_gw'] = float(np.abs(values['effective_load'] - (
        data.load_components_gw['base_residual'][:,selected] + values['actual_heating_load']
        + values['actual_cooling_load'] + values['actual_ev_load'] - values['ev_mobility_discharge'])).max())
    return qc, values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--year', type=int, default=2030)
    parser.add_argument('--hours', type=int, default=168)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--provinces', type=int, nargs='+')
    parser.add_argument('--cases', choices=CASES, nargs='+', default=list(CASES))
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--time-limit', type=float, default=300)
    parser.add_argument('--bar-tol', type=float, default=.01)
    parser.add_argument('--force-enrollment', action='store_true', help='Adversarial diagnostic: force half of eligible EV enrollment and one-quarter of permitted V2G share.')
    args = parser.parse_args()
    if not 1 <= args.hours <= 8760 or not 0 <= args.start <= 8760-args.hours:
        parser.error('Invalid chronological window')
    if not 0 < args.time_limit <= 3600 or not 1 <= args.threads <= 16:
        parser.error('Local per-case budget must be <=3600s and 1..16 threads')
    args.output.mkdir(parents=True, exist_ok=False)
    data = select_provinces(read_service_inputs(args.year), args.provinces)
    reports = []
    for case in args.cases:
        print(f'Building {case}: {len(data.provinces)} provinces x {args.hours} hours', flush=True)
        config = load_model_config(scenario_path=ROOT/f'config/scenarios/{case}.json').for_planning_year(args.year)
        config.raw['numerics'].update(method=2, crossover=0, solution_target=1,
            barrier_convergence_tolerance=args.bar_tol, aggregate=1)
        before = time.perf_counter()
        with gp.Model(case) as model:
            model.Params.OutputFlag = 0
            model.Params.LogFile = str(args.output/f'{case}.log')
            model.Params.Method = 2
            model.Params.Crossover = 0
            model.Params.SolutionTarget = 1
            model.Params.Threads = args.threads
            model.Params.TimeLimit = args.time_limit
            model.Params.BarConvTol = args.bar_tol
            model.Params.FeasibilityTol = 1e-6
            model.Params.OptimalityTol = 1e-6
            model.Params.NumericFocus = 1
            model.Params.ScaleFlag = 2
            model.Params.Presolve = 2
            model.Params.Aggregate = 1
            block = attach_flexible_load(model, config, data, hours=args.hours, hour_start=args.start)
            if args.force_enrollment and config.raw['flexible_load']['ev_v1g']['enabled']:
                model.addConstr(block.variables['ev_enrolled_service_fraction'] == .5)
                rho = config.raw['flexible_load']['ev_v2g']['participation_fraction']/config.raw['flexible_load']['ev_v1g']['shiftable_energy_fraction']
                model.addConstr(block.variables['ev_bidirectional_service_fraction'] == .25*rho)
            # A deterministic artificial price exposes shifting and round-trip losses.
            price = 450 + 400*np.sin((np.arange(args.start,args.start+args.hours)-9)*2*np.pi/24)
            model.setObjective(gp.quicksum(block.costs.values()) + (1e-3*price*block.effective_load_gw).sum())
            model.update()
            build_seconds = time.perf_counter()-before
            model.optimize()
            report = dict(case=case, solver_version=gp.gurobi.version(), status=int(model.Status),
                rows=model.NumConstrs, variables=model.NumVars, nonzeros=model.NumNZs,
                build_seconds=build_seconds, solve_seconds=model.Runtime,
                matrix_min=model.MinCoeff, matrix_max=model.MaxCoeff,
                structural_audit=block.structural_audit,
                prebuild_legacy_guard=prebuild_flexible_load_solver_compatibility(config,data,hours=args.hours,hour_start=args.start))
            if model.SolCount:
                qc, values = physical_qc(config,data,block,args.hours,args.start)
                report.update(objective=model.ObjVal, physical_qc=qc,
                    max_qc_residual=max(qc.values()),
                    gurobi_quality={k:float(model.getAttr(k)) for k in ('ConstrVio','ConstrResidual','BoundVio')},
                    capacity_gw=values['flexible_service_capacity'].tolist(),
                    costs_million_cny={k:float(_value(v)) for k,v in block.costs.items()})
                report['passed'] = model.Status == gp.GRB.OPTIMAL and max(qc.values()) <= 1e-5 and max(report['gurobi_quality'].values()) <= 1e-5
            else:
                report['passed'] = False
                if model.Status == gp.GRB.INFEASIBLE:
                    model.computeIIS()
                    model.write(str(args.output/f'{case}.ilp'))
            reports.append(report)
            print(json.dumps({k:report.get(k) for k in ('case','status','rows','variables','solve_seconds','max_qc_residual','passed')}),flush=True)
    hash_paths = [DATA_ROOT/'load/hourly_load_2025_2060.csv.gz'] + list((DATA_ROOT/'flexibility').glob('*v5*'))
    hash_paths += [ROOT/f'cispo_model/{name}.py' for name in ('flexible_portfolio','flexible_load','flexible_load_numerics','config','solution_export')]
    payload = dict(generated_at=datetime.now().astimezone().isoformat(),
        scope='LOCAL_REAL_INPUT_SERVICE_BLOCK_ONLY_NOT_SYSTEM_PLANNING',
        arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},
        province_codes=data.provinces.province_code.tolist(),
        hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in hash_paths if p.is_file()},
        cases=reports, passed=all(r['passed'] for r in reports))
    (args.output/'report.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if payload['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
