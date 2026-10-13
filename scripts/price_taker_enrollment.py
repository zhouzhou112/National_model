"""Price-taker enrollment test for the V5 flexibility block (NOT a system solve).

Builds the real case3 service block for all 31 provinces over a full 8760h year
and lets it respond to an exogenous hourly price series taken from a solved Base
year (Barrier duals of the provincial power balance). Enrollment (contract
capacity, alpha/beta) is endogenous. Service costs can be overridden to test
alternative parameter sets. Output is a JSON report plus a per-province CSV.

Usage (from National_model, with the RL env and PYTHONPATH as in the
validation_coordination README):
  python ../claude_workspace/scripts/price_taker_enrollment.py \
      --prices ../claude_workspace/evidence/base2030_prices/hourly_marginal_prices.csv.gz \
      --year 2030 --cost-set current --output ../claude_workspace/evidence/price_taker_2030_current
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import gurobipy as gp
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import DATA_ROOT
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.solution_export import _value
from validate_flexible_portfolios import read_service_inputs, select_provinces, physical_qc

COST_SETS = {
    "current": {},
    "literature": {
        "heating": {"activation_cost_yuan_per_mwh": 43.0},
        "cooling": {"activation_cost_yuan_per_mwh": 43.0},
        "ev_v1g": {"activation_cost_yuan_per_mwh": 43.0},
        "ev_v2g": {"activation_cost_yuan_per_mwh": 150.0, "degradation_cost_yuan_per_mwh": 50.0},
    },
    "half": {
        "heating": {"activation_cost_yuan_per_mwh": 150.0},
        "cooling": {"activation_cost_yuan_per_mwh": 150.0},
        "ev_v1g": {"activation_cost_yuan_per_mwh": 150.0},
        "ev_v2g": {"activation_cost_yuan_per_mwh": 150.0, "degradation_cost_yuan_per_mwh": 200.0},
    },
}
SERVICES = ("heating", "cooling", "ev_v1g", "ev_v2g")


def load_prices(path: Path, provinces: pd.Series, normalize: str) -> np.ndarray:
    frame = pd.read_csv(path)
    price = frame.pivot(index="province_code", columns="hour_index",
                        values="marginal_energy_price_cny_per_mwh")
    price = price.reindex(index=provinces, columns=range(8760)).to_numpy(float)
    if not np.isfinite(price).all():
        raise ValueError("Non-finite or missing prices")
    if normalize == "median_zero_floor":
        # Remove a province-wide constant dual offset (degenerate annual-row direction)
        # by shifting each province so that its 5th percentile is zero.
        price = price - np.percentile(price, 5, axis=1, keepdims=True)
    return price


def apply_cost_set(service, cost_set: dict) -> dict:
    applied = {}
    for svc, overrides in cost_set.items():
        overrides = dict(overrides)
        if svc in ("heating", "cooling") and "activation_cost_yuan_per_mwh" in overrides:
            # Historical named overrides are bidirectional by definition.
            for direction in ("release", "precondition"):
                key = f"activation_cost_{direction}_yuan_per_mwh"
                if key in service.service_costs[svc]:
                    overrides[key] = overrides["activation_cost_yuan_per_mwh"]
        for key, value in overrides.items():
            arr = service.service_costs[svc][key]
            applied[f"{svc}.{key}"] = dict(before=float(np.unique(arr)[0]) if len(np.unique(arr)) == 1 else "varies", after=float(value))
            service.service_costs[svc][key] = np.full_like(arr, float(value))
    return applied


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prices", type=Path, required=True)
    p.add_argument("--year", type=int, default=2030)
    p.add_argument("--case", default="case3_thermal_ev_v5")
    p.add_argument("--cost-set", choices=sorted(COST_SETS), default="current")
    p.add_argument("--normalize", choices=["none", "median_zero_floor"], default="none")
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--time-limit", type=float, default=2400)
    p.add_argument("--bar-tol", type=float, default=1e-8)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--single-factor", choices=["none", "cost_only", "participation_only"], default="none")
    p.add_argument("--price-year", type=int, default=2030)
    p.add_argument("--numeric-focus", type=int, default=1, choices=[0,1,2,3])
    p.add_argument("--scale-flag", type=int, default=2, choices=[-1,0,1,2,3])
    p.add_argument("--presolve", type=int, default=2, choices=[-1,0,1,2])
    p.add_argument("--aggregate", type=int, default=1, choices=[0,1,2])
    p.add_argument("--agg-fill", type=int, default=None, help="Diagnostic AggFill override; omitted keeps solver default")
    p.add_argument("--preserve-diagnostic", action="store_true", help="Archive original LP, all available vectors and hourly residuals regardless of QC")
    p.add_argument("--method", type=int, default=2, choices=[1,2], help="Single-stage local diagnostic solver; never launches production Stage B")
    p.add_argument("--basis-in", type=Path, help="Optional local simplex basis for the same service-block layout")
    args = p.parse_args()
    import hashlib
    code_paths = sorted((ROOT / "cispo_model").glob("*.py")) + [Path(__file__), ROOT / "scripts/validate_flexible_portfolios.py"]
    code_sha = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in code_paths}
    args.output.mkdir(parents=True, exist_ok=False)

    config = load_model_config(scenario_path=ROOT / f"config/scenarios/{args.case}.json").for_planning_year(args.year)
    data = select_provinces(read_service_inputs(args.year, config), None)
    input_files = [DATA_ROOT / "load/hourly_load_2025_2060.csv.gz"]
    for directory in (DATA_ROOT / "flexibility/participation_pathway_v2", DATA_ROOT / "flexibility"):
        input_files.extend(p for p in directory.glob("*v5*") if p.is_file())
    input_sha = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_files}
    provinces = data.provinces.province_code
    price = load_prices(args.prices, provinces, args.normalize)
    # Cost-only and participation-only both use the old compensation case as reference.
    # No capacity credit is priced by this service-block experiment.
    if args.single_factor != "none":
        old = load_model_config(scenario_path=ROOT / "config/scenarios/case3_thermal_ev_v5_compensation_basis.json").for_planning_year(args.year)
        old_data = read_service_inputs(args.year, old)
        if args.single_factor == "cost_only":
            new_costs = data.flexible_load_v4.service_costs
            new_legacy_flag = data.flexible_load_v4.legacy_bidirectional_activation
            data = old_data
            data.flexible_load_v4.service_costs = new_costs
            data.flexible_load_v4.legacy_bidirectional_activation = new_legacy_flag
            old.raw["flexible_load"]["thermal_activation_contract"] = "directional_resource_cost_v1"
            config = old
        else:
            data.flexible_load_v4.service_costs = old_data.flexible_load_v4.service_costs
            config.raw["flexible_load"].pop("thermal_activation_contract", None)
            # Hold V2G national cap and all non-participation assumptions at the old values.
            config.raw["flexible_load"]["ev_v2g"]["national_contracted_power_cap_gw_by_planning_year"] = old.raw["flexible_load"]["ev_v2g"]["national_contracted_power_cap_gw_by_planning_year"]
    config.raw["security"]["capacity_margin_load_basis"] = "baseline_peak_v1"
    cost_changes = apply_cost_set(data.flexible_load_v4, COST_SETS[args.cost_set])
    config.raw["numerics"].update(method=args.method, crossover=0, solution_target=1,
                                  barrier_convergence_tolerance=args.bar_tol, aggregate=args.aggregate)
    baseline_cost = float((1e-3 * price * data.load_gw).sum())
    before = time.perf_counter()
    with gp.Model(args.case) as model:
        model.Params.OutputFlag = 1
        model.Params.LogToConsole = 0
        model.Params.LogFile = str(args.output / "gurobi.log")
        model.Params.Method = args.method
        model.Params.Crossover = 0
        model.Params.SolutionTarget = 1
        model.Params.Threads = args.threads
        model.Params.TimeLimit = args.time_limit
        model.Params.BarConvTol = args.bar_tol
        model.Params.FeasibilityTol = 1e-6
        model.Params.OptimalityTol = 1e-6
        model.Params.NumericFocus = args.numeric_focus
        model.Params.ScaleFlag = args.scale_flag
        model.Params.Presolve = args.presolve
        model.Params.Aggregate = args.aggregate
        if args.agg_fill is not None:
            model.Params.AggFill = args.agg_fill
        block = attach_flexible_load(model, config, data, hours=8760, hour_start=0)
        energy_cost = (1e-3 * price * block.effective_load_gw).sum()
        model.setObjective(gp.quicksum(block.costs.values()) + energy_cost)
        model.update()
        if args.basis_in:
            if args.method != 1:
                raise ValueError("A local basis warm start requires --method 1")
            model.read(str(args.basis_in))
        build_seconds = time.perf_counter() - before
        print(f"built {model.NumConstrs} rows x {model.NumVars} cols, {model.NumNZs} nnz in {build_seconds:.0f}s", flush=True)
        if args.preserve_diagnostic:
            from flex_numerics_diagnostics import before_solve, after_solve, service_diagnostics
            before_solve(model, args.output)
        try:
            model.optimize()
        finally:
            if args.preserve_diagnostic:
                after_solve(model, args.output)
        if args.method == 1 and model.Status == gp.GRB.OPTIMAL:
            model.write(str(args.output / "solution.bas"))
        report = dict(generated_at=datetime.now().astimezone().isoformat(),
                      code_sha256=code_sha,
                      input_sha256=input_sha,
                      solver_settings=dict(method=args.method, crossover=0, seed=int(model.Params.Seed),
                          bar_tol=args.bar_tol, numeric_focus=args.numeric_focus,
                          scale_flag=args.scale_flag, presolve=args.presolve, aggregate=args.aggregate, threads=args.threads),
                      scope="PRICE_TAKER_SERVICE_BLOCK_ONLY_NOT_SYSTEM_PLANNING",
                      case=args.case, year=args.year, cost_set=args.cost_set, cost_changes=cost_changes,
                      prices=str(args.prices.resolve()), normalize=args.normalize, single_factor=args.single_factor,
                      price_year=args.price_year, result_use="TEST_ONLY_PRICE_TAKER", capacity_credit_value_included=False,
                      status=int(model.Status), rows=model.NumConstrs, variables=model.NumVars,
                      nonzeros=model.NumNZs, build_seconds=build_seconds, solve_seconds=model.Runtime,
                      baseline_energy_cost_million_cny=baseline_cost)
        if model.SolCount:
            qc, values = physical_qc(config, data, block, 8760, 0)
            if args.preserve_diagnostic:
                report["overnight_diagnostics"] = service_diagnostics(config, data, block, 8760, 0, args.output)
            report["gurobi_quality"] = {key: float(getattr(model,key)) for key in ("ConstrVio","BoundVio","DualVio","ComplVio")}
            if max(qc.values()) > 1e-6:
                debug = {k: np.asarray(values[k]) for k in ("heating_state", "heating_shift_up", "heating_shift_down",
                    "cooling_state", "cooling_shift_up", "cooling_shift_down", "flexible_service_capacity")}
                for component in ("heating","cooling"):
                    view=block.variables[component+"_state"]
                    if hasattr(view,"retained_mask"):
                        debug[component+"_retained_mask"]=view.retained_mask
                        debug[component+"_retained_values"]=np.asarray(view.active.X) if view.active is not None else np.empty(0)
                np.savez_compressed(args.output/"physical_qc_debug.npz", **debug)
            cap = values["flexible_service_capacity"]
            costs = {k: float(_value(v)) for k, v in block.costs.items()}
            energy = float(_value(energy_cost))
            details = {k: float(_value(v)) for k,v in block.cost_details.items()}
            relocated = np.asarray(values["ev_mobility_v1g_relocated"])
            eligible = float(config.raw["flexible_load"]["ev_v1g"]["shiftable_energy_fraction"]) * data.load_components_gw["ev"]
            report["directional_cost_details_million_cny"] = details
            report["v1g_relocated_gwh"] = float(relocated.sum())
            report["v1g_reference_pool_gwh"] = float(eligible.sum())
            report["v1g_relocation_fraction_of_reference_pool"] = float(relocated.sum()/eligible.sum())
            report["source_sha256"] = {str(path): __import__("hashlib").sha256(path.read_bytes()).hexdigest() for path in [args.prices, Path(__file__), config.scenario_path]}
            report["resolved_configuration"] = config.raw
            report.update(objective=model.ObjVal, service_costs_million_cny=costs,
                          energy_cost_million_cny=energy,
                          net_saving_million_cny=baseline_cost - model.ObjVal,
                          physical_qc=qc, max_qc_residual=max(qc.values()),
                          national_contract_gw={s: float(cap[:, i].sum()) for i, s in enumerate(SERVICES)},
                          provinces_enrolled={s: int((cap[:, i] > 1e-3).sum()) for i, s in enumerate(SERVICES)})
            alpha = values.get("ev_enrolled_service_fraction")
            beta = values.get("ev_bidirectional_service_fraction")
            table = pd.DataFrame({"province_code": provinces.to_numpy()})
            for i, s in enumerate(SERVICES):
                table[f"{s}_contract_gw"] = cap[:, i]
            if alpha is not None:
                table["alpha"] = np.asarray(alpha).ravel()
                # RC is the objective derivative at the upper bound; negate for expansion value.
                bounds = block.variables["ev_enrolled_service_fraction"]
                table["alpha_upper_expansion_value_million_cny"] = np.maximum(-np.asarray(bounds.RC).ravel(),0)
                report["alpha_min"] = float(np.min(alpha)); report["alpha_max"] = float(np.max(alpha))
                report["alpha_upper_expansion_value_sum_million_cny"] = float(table["alpha_upper_expansion_value_million_cny"].sum())
                table["v1g_relocated_gwh"] = relocated.sum(axis=1)
                table["v1g_reference_pool_gwh"] = eligible.sum(axis=1)
            if beta is not None:
                table["beta"] = np.asarray(beta).ravel()
            for key in ("heating_shift_up", "heating_shift_down", "cooling_shift_up", "cooling_shift_down",
                        "ev_mobility_discharge", "ev_v1g_pool_charge", "ev_v2g_pool_charge"):
                if key in values:
                    table[f"{key}_gwh"] = np.asarray(values[key]).sum(axis=1)
            table.to_csv(args.output / "province_enrollment.csv", index=False)
            report["enrollment_table"] = str(args.output / "province_enrollment.csv")
        report["local_diagnostic_qc_tolerance"] = 1e-5
        report["local_diagnostic_passed"] = bool(model.Status == gp.GRB.OPTIMAL
            and report.get("max_qc_residual", float("inf")) <= 1e-5
            and report.get("gurobi_quality", {}).get("ConstrVio", float("inf")) <= 1e-5
            and report.get("gurobi_quality", {}).get("BoundVio", float("inf")) <= 1e-5)
        (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: report.get(k) for k in ("status", "solve_seconds", "national_contract_gw",
                                                        "provinces_enrolled", "net_saving_million_cny", "max_qc_residual")},
                         ensure_ascii=False), flush=True)
    return 0 if report["local_diagnostic_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
