"""One immutable F-series truncated solve; never a production planning run.

Example: python scripts/run_flex_full_diagnostic.py --hours 744 --start 4344
         --threads 16 --output NEW_DIRECTORY
Inputs use existing CISPO_* environment paths. No screening or inherited state.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import psutil
from flex_numerics_diagnostics import save, before_solve, after_solve, service_diagnostics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hours", type=int, required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--threads", type=int, default=16)
    p.add_argument("--case", choices=["base", "case3_thermal_ev_v5"], default="case3_thermal_ev_v5")
    p.add_argument("--aggregate", type=int, default=1, choices=[0,1])
    p.add_argument("--agg-fill", type=int, default=None, help="Diagnostic AggFill override; omitted keeps solver default")
    p.add_argument("--presolve", type=int, default=2, choices=[0,2])
    p.add_argument("--reserve-gib", type=float, default=15, help="Host reserve; use 2 only for local <=24h smoke tests")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not 1 <= a.hours <= 2016 or not 0 <= a.start <= 8760-a.hours:
        p.error("Requires contiguous diagnostic window within the non-leap year")
    if a.reserve_gib < (2 if a.hours <= 24 else 15):
        p.error("Memory reserve below diagnostic contract")
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    from cispo_model.config import load_model_config, ModelConfig
    from cispo_model.data import load_model_data, DATA_ROOT
    from cispo_model.io_contract import write_run_provenance
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import configure_gurobi, model_statistics
    from cispo_model.solution_preservation import preserve_stage_a
    import gurobipy as gp
    cfg = load_model_config(ROOT / "config/optimization_numeric_dac_by_year_v9.json",
        scenario_path=ROOT / "config/scenarios/case3_thermal_ev_v5.json" if a.case != "base" else None,
        solver_path=ROOT / "config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json").for_planning_year(2030)
    raw = copy.deepcopy(cfg.raw)
    raw["numerics"].update(threads=a.threads, aggregate=a.aggregate, presolve=a.presolve)
    cfg = ModelConfig(cfg.path, raw, scenario_path=cfg.scenario_path, solver_path=cfg.solver_path, formulation_path=cfg.formulation_path)
    cfg.validate()
    save(out / "scope.json", dict(case=a.case, hours=a.hours, start=a.start,
        result_use="TEST_ONLY_TRUNCATED_HORIZON", annual_flows="hours/8760", annualized_costs="unscaled",
        boundary="cyclic selected window", state_in=None, screening=False, seed=0,
        started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        code_sha256={str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in list((ROOT / "cispo_model").glob("*.py")) + list((ROOT / "scripts").glob("*flex*diagnostic*.py"))}))
    save(out / "effective_config.json", raw)
    t0 = time.monotonic(); data = load_model_data(cfg)
    write_run_provenance(out, cfg, data_root=DATA_ROOT, planning_state=data.planning_state)
    art = build_full_year_monolithic(cfg, data, compute_max_cf=True, optimization_hours=a.hours, optimization_start_hour=a.start)
    m = art.model; configure_gurobi(m, cfg, out / "gurobi.log"); m.update()
    if a.agg_fill is not None:
        m.Params.AggFill = a.agg_fill
    save(out / "build_report.json", dict(build_seconds=time.monotonic()-t0, statistics=model_statistics(m)))
    before_solve(m, out)
    resource_stop = []
    last = [0.0]
    with (out / "barrier.jsonl").open("w") as trace:
        def callback(model, where):
            now = time.monotonic()
            if now-last[0] > 5:
                last[0] = now
                if psutil.virtual_memory().available < a.reserve_gib*2**30:
                    resource_stop.append(dict(available_bytes=psutil.virtual_memory().available, elapsed=now-t0))
                    model.terminate()
            if where == gp.GRB.Callback.BARRIER:
                row = {k: model.cbGet(getattr(gp.GRB.Callback, v)) for k,v in
                       (("iteration","BARRIER_ITRCNT"),("runtime","RUNTIME"),("primal","BARRIER_PRIMOBJ"),
                        ("dual","BARRIER_DUALOBJ"),("primal_inf","BARRIER_PRIMINF"),("dual_inf","BARRIER_DUALINF"),("complementarity","BARRIER_COMPL"))}
                trace.write(json.dumps(row)+"\n"); trace.flush()
        try:
            m.optimize(callback)
        finally:
            result = after_solve(m, out, art.index.get("annual_capacity_link_row_scaling"))
            result["resource_stop"] = resource_stop
            result.update(result_use="TEST_ONLY_TRUNCATED_HORIZON", planning_year=2030,
                          optimization_hours=a.hours, optimization_start_hour=a.start,
                          status_code=int(m.Status), solution_count=int(m.SolCount),
                          status="OPTIMAL" if m.Status == gp.GRB.OPTIMAL else str(m.Status))
            save(out / "result.json", result)
            # QC is always a label. All independent semantic/state exports run.
            preserve_stage_a(art, data, cfg, out, result, snapshot=False)
    if m.SolCount and a.case != "base":
        keys = {k:v for k,v in art.variables.items() if k.startswith(("heating_","cooling_","ev_","actual_","flexible_service_","firm_flexible_")) or k=="effective_load"}
        diag = service_diagnostics(cfg, data, SimpleNamespace(variables=keys), a.hours, a.start, out)
        from cispo_model.flexible_credit import audit_optional_credit
        from cispo_model.solution_export import _value
        values = {k:_value(v) for k,v in keys.items()}
        credit = audit_optional_credit(cfg.raw["flexible_load"], data, values["flexible_service_capacity"],
            values["ev_enrolled_service_fraction"], values["ev_bidirectional_service_fraction"], values["firm_flexible_capacity_credit"])
        diag["physical_qc"].update(credit)
        diag["capacity_credit"] = "AUDITED_FULL_YEAR_PEAK_LIMITS"
        diag["maximum_service_residual_gw_gwh"] = max(diag["maximum_service_residual_gw_gwh"], credit["firm_credit_bound_violation_gw"])
        save(out / "service_diagnostics.json", diag)
    m.dispose()


if __name__ == "__main__":
    main()
