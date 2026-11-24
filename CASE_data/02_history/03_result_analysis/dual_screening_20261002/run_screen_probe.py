"""Isolated V9 candidate-screen experiment; never writes a planning state.

--mode solve: 24/168h full or restricted solve with iterative exact-column pricing.
--mode factor: up to 2016h bounded five-iteration structural screen, not a solution.
All existing capacity, physical rows, costs and potential bounds are preserved.
The only experimental restriction is UB(vre_new)=0 for initially omitted sites.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import psutil

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=["solve", "factor", "inputs"], required=True)
    p.add_argument("--scenario", choices=["base", "case3_thermal_ev_v5"], default="base")
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--start", type=int, default=3960)
    p.add_argument("--screen-csv", type=Path)
    p.add_argument("--margin", type=float, default=0.2)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--threads", type=int, default=12)
    p.add_argument("--time-limit", type=int, default=1800)
    p.add_argument("--memory-gb", type=float, default=72)
    p.add_argument("--max-rounds", type=int, default=4)
    a = p.parse_args()
    if not (1 <= a.hours <= (168 if a.mode == "solve" else 2016)):
        p.error("solve <=168h; factor <=2016h")
    if not (0 <= a.start <= 8760-a.hours and 1 <= a.threads <= 16 and 1 <= a.time_limit <= 5400 and 1 <= a.memory_gb <= 75):
        p.error("Invalid bounded diagnostic resource/window contract")
    if not (np.isfinite(a.margin) and a.margin >= 0 and 1 <= a.max_rounds <= 8):
        p.error("Margin must be finite/nonnegative; pricing rounds must be between 1 and 8")
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    save(out/"scope.json", dict(arguments={k: str(v) if isinstance(v, Path) else v for k,v in vars(a).items()},
         production=False, publication_accepted=False, seed=0, horizon_note="Contiguous cyclic engineering window; annualized capacity costs unscaled; annual flow budgets scaled by hours/8760 per existing master.py",
         script_sha256=sha(Path(__file__)), python=sys.version, cpu_affinity=psutil.Process().cpu_affinity(),
         utc_started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    from cispo_model.config import load_model_config, ModelConfig
    from cispo_model.data import load_model_data, DATA_ROOT
    from cispo_model.io_contract import write_run_provenance
    cfg_path = ROOT/"config/optimization_numeric_dac_by_year_v9.json"
    scenario = None
    if a.scenario != "base":
        # Explicit derived overlay, preserving EVERY physical override. The old
        # September portfolio is parented to the pre-repair baseline, not V9.
        source = ROOT/"config/scenarios"/(a.scenario+".json")
        payload = json.loads(source.read_text(encoding="utf-8"))
        parent = json.loads(cfg_path.read_text(encoding="utf-8"))["scientific_case"]["case_id"]
        old_parent = payload["parent_baseline_case_id"]
        payload["parent_baseline_case_id"] = parent
        scenario = out/"scenario_v9_diagnostic.json"
        save(scenario, payload)
        save(out/"scenario_parent_migration.json", dict(source=str(source), source_sha256=sha(source),
             old_parent=old_parent, diagnostic_parent=parent, physical_overrides_changed=False))
    cfg = load_model_config(path=cfg_path, scenario_path=scenario)
    raw = copy.deepcopy(cfg.raw)
    raw["numerics"].update(threads=a.threads, method=2, numeric_focus=2, crossover=2 if a.mode=="solve" else 0,
        crossover_basis=1, solution_target=0 if a.mode=="solve" else 1,
        barrier_convergence_tolerance=1e-8 if a.mode=="solve" else 1e-4,
        feasibility_tolerance=1e-6, optimality_tolerance=1e-6, time_limit_seconds=a.time_limit,
        soft_mem_limit_gb=a.memory_gb, bar_iter_limit=1000 if a.mode=="solve" else 5)
    cfg = ModelConfig(cfg.path, raw, scenario_path=scenario); cfg.validate()
    save(out/"effective_config.json", raw)
    if a.hours > 168 and psutil.virtual_memory().available < 90*2**30:
        raise RuntimeError("Large probe requires >=90GiB available host RAM")
    t0 = time.perf_counter()
    data = load_model_data(cfg)
    write_run_provenance(out, cfg, data_root=DATA_ROOT, planning_state=data.planning_state)
    if a.mode == "inputs":
        save(out/"result.json", dict(status="INPUTS_PASS", scenario=a.scenario, no_lp_built=True)); return
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import configure_gurobi, model_statistics
    import gurobipy as gp
    art = build_full_year_monolithic(cfg, data, compute_max_cf=True,
          optimization_hours=a.hours, optimization_start_hour=a.start)
    m = art.model; m.update()
    new = art.variables["vre_new"] if hasattr(art, "variables") else None
    if new is None: raise RuntimeError("Missing VRE variable mapping")
    cap = art.variables["vre_capacity"]
    ub = np.asarray(new.UB).copy()
    floor = np.asarray(cap.LB).copy()
    keep = np.ones(len(ub), dtype=bool)
    screening_source = None
    if a.screen_csv:
        table = pd.read_csv(a.screen_csv)
        keys = ["grid_uid", "technology"]
        if table.duplicated(keys).any(): raise ValueError("Duplicate stable site identities")
        aligned = data.vre_sites[keys].merge(table[keys+["rc_ratio"]], how="left", on=keys, validate="one_to_one")
        if len(aligned) != len(table) or not np.isfinite(aligned.rc_ratio).all():
            raise ValueError("Screen identity/finite-price mismatch; refuse positional join")
        keep = (aligned.rc_ratio.to_numpy() < a.margin) | (ub <= 0)
        screening_source = dict(path=str(a.screen_csv), sha256=sha(a.screen_csv), margin=a.margin)
    initial_keep = keep.copy()
    report = dict(mode=a.mode, scenario=a.scenario, hours=a.hours, start=a.start, gurobi_version=gp.gurobi.version(),
        build_seconds=time.perf_counter()-t0, raw=model_statistics(m), screening_source=screening_source,
        sites=len(ub), expandable_sites=int((ub>0).sum()), initial_retained_expandable=int((keep & (ub>0)).sum()),
        excluded_sites=int((~keep).sum()), original_headroom_gw=float(ub.sum()), rounds=[],
        production_state_written=False, publication_accepted=False)
    save(out/"build.json", report)
    ids = data.vre_sites[["grid_uid", "technology"]].copy()
    ids["original_new_ub_gw"]=ub; ids["capacity_floor_gw"]=floor; ids["initial_keep"]=keep
    ids.to_csv(out/"candidate_selection.csv", index=False)
    for k in range(a.max_rounds if a.mode=="solve" else 1):
        rd = out/f"round_{k:02d}"; rd.mkdir()
        new.UB = np.where(keep, ub, 0.0)
        m.update(); m.reset()
        configure_gurobi(m, cfg, rd/"gurobi.log")
        m.Params.Seed=0
        m.Params.BarIterLimit=1000 if a.mode=="solve" else 5
        if a.mode=="solve": m.write((rd/"model.mps").as_posix())
        telemetry=[]
        with (rd/"barrier.jsonl").open("w", encoding="utf-8") as log:
            def callback(model, where):
                if where == gp.GRB.Callback.BARRIER:
                    r=dict(iteration=int(model.cbGet(gp.GRB.Callback.BARRIER_ITRCNT)),
                        runtime=model.cbGet(gp.GRB.Callback.RUNTIME), work=model.cbGet(gp.GRB.Callback.WORK),
                        primal=model.cbGet(gp.GRB.Callback.BARRIER_PRIMOBJ), dual=model.cbGet(gp.GRB.Callback.BARRIER_DUALOBJ),
                        primal_inf=model.cbGet(gp.GRB.Callback.BARRIER_PRIMINF), dual_inf=model.cbGet(gp.GRB.Callback.BARRIER_DUALINF),
                        complementarity=model.cbGet(gp.GRB.Callback.BARRIER_COMPL))
                    if not telemetry or r["iteration"]!=telemetry[-1]["iteration"]:
                        telemetry.append(r); log.write(json.dumps(r)+"\n"); log.flush()
            m.optimize(callback)
        result=dict(round=k, status=m.Status, solution_count=m.SolCount, runtime=m.Runtime, work=m.Work,
            barrier_iterations=m.BarIterCount, retained_expandable=int((keep & (ub>0)).sum()),
            excluded=int((~keep).sum()), factor_screen_only=a.mode=="factor")
        if m.SolCount:
            result.update(objective=m.ObjVal, constraint_violation=m.ConstrVio, bound_violation=m.BoundVio, dual_violation=m.DualVio)
        if a.mode=="solve" and m.Status==gp.GRB.OPTIMAL and m.SolCount:
            rc = np.asarray(cap.RC)+np.asarray(new.RC)
            # Pair direction d(cap)=d(new)=1 cancels capacity-accounting dual.
            # Remaining columns must separately satisfy the solver dual checks.
            eps=1e-6
            reenter=(~keep)&(rc < -eps)
            result.update(min_excluded_rc=float(rc[~keep].min()) if (~keep).any() else None,
                reenter_count=int(reenter.sum()), pricing_epsilon_million_cny_per_gw=eps,
                excluded_improvement_bound_million_cny=float(np.dot(np.maximum(-rc[~keep],0),ub[~keep])),
                numerical_pricing_gate=bool(not reenter.any() and m.ConstrVio<=1e-5 and m.BoundVio<=1e-5 and m.DualVio<=1e-5))
            pricing=ids.copy(); pricing["retained"]=keep; pricing["rc_build"]=rc
            pricing["new_capacity_gw"]=np.asarray(new.X); pricing["reenter"]=reenter
            pricing.to_csv(rd/"pricing.csv", index=False)
            if k==0:
                # Independently verify RC=c-A^T Pi on deterministic site samples.
                pi=np.asarray(m.getAttr("Pi")); checks=[]
                for z in np.linspace(0,len(ub)-1,8,dtype=int):
                    direct=0.0
                    for mv in [cap,new]:
                        v=mv[z].item(); col=m.getCol(v)
                        direct += v.Obj-sum(col.getCoeff(j)*pi[col.getConstr(j).index] for j in range(col.size()))
                    checks.append(dict(site=int(z), rc_pair=float(rc[z]), direct=float(direct), error=float(abs(direct-rc[z]))))
                save(rd/"pricing_identity_checks.json",checks)
            from cispo_model.master import export_master_solution
            from cispo_model.solution_export import export_operational_solution
            try:
                master=export_master_solution(art,data,rd/"physical_export",enforce_qc=False)
                operational=export_operational_solution(art,data,cfg,rd/"physical_export",enforce_qc=False)
                result["physical_qc_status"]=operational.get("status")
                result["master_qc"]=master
            except Exception as err:
                result["physical_export_error"]=str(err)
            keep |= reenter
        else:
            reenter=np.zeros(len(ub),dtype=bool)
        report["rounds"].append(result)
        save(rd/"result.json",result); save(out/"result.json",report)
        print(json.dumps(result), flush=True)
        if not reenter.any(): break
    report["total_seconds"]=time.perf_counter()-t0
    report["screen_reentry_added"]=int((keep & ~initial_keep).sum())
    save(out/"result.json",report)
    m.dispose()


if __name__=="__main__":
    main()
