"""Isolated A/B/C engineering probe; never writes planning state or production results.

Example: python run_probe.py --variant A --year 2040 --state-in PATH
         --hours 24 --start 2880 --strict-equivalence --output NEW_DIRECTORY
744h requires >=90GiB available RAM and must run under the server solver lock.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import psutil


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--code-root", type=Path, default=Path(__file__).resolve().parents[3])
    p.add_argument("--variant", choices=["off", "explicit_off", "A", "B", "C"], required=True)
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--start", type=int, default=2880)
    p.add_argument("--year", type=int, choices=[2030, 2040], default=2030)
    p.add_argument("--state-in", type=Path)
    p.add_argument("--threads", type=int, default=8)
    p.add_argument("--block-hours", type=int, default=730)
    p.add_argument("--factor", action="store_true")
    p.add_argument("--build-only", action="store_true")
    p.add_argument("--strict-equivalence", action="store_true")
    p.add_argument("--agg-fill", type=int)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if not 1 <= a.hours <= 744 or not 0 <= a.start <= 8760-a.hours:
        p.error("Only contiguous <=744h engineering windows are allowed")
    if a.hours > 168 and psutil.virtual_memory().available < 90 * 2**30:
        raise RuntimeError("744h requires >=90GiB available host memory")
    out=a.output.resolve();out.mkdir(parents=True, exist_ok=False)
    root=a.code_root.resolve();sys.path.insert(0,str(root))
    from cispo_model.config import load_model_config, ModelConfig
    from cispo_model.data import load_model_data, DATA_ROOT
    from cispo_model.planning_state import PlanningState
    from cispo_model.run_contract import analysis_case_identity
    from cispo_model.io_contract import write_run_provenance
    cfg=load_model_config(root/"config/optimization_numeric_dac_by_year_v9.json",
        solver_path=root/"config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json").for_planning_year(a.year)
    raw=copy.deepcopy(cfg.raw)
    raw["numerics"].update(threads=a.threads, time_limit_seconds=None,
        soft_mem_limit_gb=72 if a.hours>168 else 8,
        bar_iter_limit=5 if a.factor else 2000000000)
    if a.strict_equivalence:
        raw["numerics"].update(crossover=2, solution_target=0, barrier_convergence_tolerance=1e-8)
    if a.variant in {"A","explicit_off"}:
        for key in ["hydro_capacity_headroom_zero_gw", "retrofit_upper_zero_gw", "inherited_floor_overrun_clip_gw"]:
            # A3 is tested independently at the state/floor interface; these
            # archived-state probes isolate A1/A2 capacity interval closure.
            raw["numerics"][key]=0.0 if a.variant=="explicit_off" or key=="inherited_floor_overrun_clip_gw" else 1e-6
    if a.variant=="B":raw["numerics"]["bar_homogeneous"]=1
    if a.variant in {"C","explicit_off"}:
        raw["formulation"]["annual_dense_row_split"]={"enabled":a.variant=="C","block_hours":a.block_hours}
    if a.agg_fill is not None:raw["numerics"]["agg_fill"]=a.agg_fill
    cfg=ModelConfig(cfg.path,raw);cfg.validate()
    state=None
    if a.state_in:
        state=PlanningState.load(a.state_in,expected_boundary_year=cfg.boundary_year,
            expected_scenario_id="base",allow_unaccepted_candidate=True)
    save(out/"scope.json",dict(arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},
        result_use="TEST_ONLY_TRUNCATED_HORIZON",scientific_acceptance=False,seed=0,
        utc_started=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),available_memory_bytes=psutil.virtual_memory().available,
        inherited_source_qc=state.metadata.get("source_qc_status") if state else None,
        annual_flows="hours/8760",annualized_costs="unscaled",boundary="cyclic selected window"))
    save(out/"effective_config.json",raw);save(out/"scientific_identity.json",analysis_case_identity(cfg))
    t0=time.perf_counter();data=load_model_data(cfg,planning_state=state)
    write_run_provenance(out,cfg,data_root=DATA_ROOT,planning_state=data.planning_state)
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import configure_gurobi,model_statistics
    import gurobipy as gp
    art=build_full_year_monolithic(cfg,data,compute_max_cf=True,optimization_hours=a.hours,optimization_start_hour=a.start)
    m=art.model;m.update();configure_gurobi(m,cfg,out/"gurobi.log");m.Params.Seed=0
    lo=np.asarray(m.getAttr("LB"));up=np.asarray(m.getAttr("UB"));names=m.getAttr("VarName")
    small=(up-lo>0)&(up-lo<1e-6)
    gw_columns=np.array([str(n).split('[')[0].endswith('_gw') for n in names])
    report=dict(variant=a.variant,hours=a.hours,year=a.year,start=a.start,build_seconds=time.perf_counter()-t0,
        gurobi_version=gp.gurobi.version(),statistics=model_statistics(m),tiny_interval_count=int(small.sum()),
        tiny_gw_interval_count=int((small & gw_columns).sum()),
        numerical_robustness_audit=art.index.get("numerical_robustness_audit"),annual_dense_row_split=art.index.get("annual_dense_row_split"))
    pd.DataFrame({"variable":np.asarray(names)[small],"lb":lo[small],"ub":up[small],"range":(up-lo)[small]}).to_csv(out/"tiny_intervals.csv",index=False)
    save(out/"build_report.json",report)
    if a.hours<=24:
        from scipy import sparse
        m.write(str(out/"model.mps"))
        sparse.save_npz(out/"matrix.npz",m.getA())
        np.savez(out/"lp_arrays.npz",lower=lo,upper=up,rhs=m.getAttr("RHS"),objective=m.getAttr("Obj"),
            senses=m.getAttr("Sense"),row_names=m.getAttr("ConstrName"),variable_names=names)
    if a.build_only:m.dispose();return
    traces=[]
    with (out/"barrier.jsonl").open("w",encoding="utf-8") as log:
        def callback(model,where):
            if where==gp.GRB.Callback.BARRIER:
                record={key:float(model.cbGet(getattr(gp.GRB.Callback,attr))) for key,attr in
                    [("iteration","BARRIER_ITRCNT"),("runtime","RUNTIME"),("work","WORK"),("primal","BARRIER_PRIMOBJ"),
                     ("dual","BARRIER_DUALOBJ"),("primal_inf","BARRIER_PRIMINF"),("dual_inf","BARRIER_DUALINF"),("complementarity","BARRIER_COMPL")]}
                if not traces or record["iteration"]!=traces[-1]["iteration"]:
                    traces.append(record);log.write(json.dumps(record)+"\n");log.flush()
        m.optimize(callback)
    pd.DataFrame(traces).to_csv(out/"barrier_trajectory.csv",index=False)
    result=dict(status=int(m.Status),solution_count=int(m.SolCount),runtime=m.Runtime,work=m.Work,barrier_iterations=m.BarIterCount,
        objective=float(m.ObjVal) if m.SolCount else None,production_result=False,parameters={k:getattr(m.Params,k) for k in
        ["Method","Threads","Crossover","SolutionTarget","BarConvTol","NumericFocus","BarHomogeneous","AggFill","BarIterLimit","Seed"]})
    if m.SolCount:
        result.update(constraint_violation=m.ConstrVio,bound_violation=m.BoundVio)
        from cispo_model.master import export_master_solution
        from cispo_model.solution_export import export_operational_solution
        try:
            export_master_solution(art,data,out/"physical_export",enforce_qc=False)
            result["physical_qc"]=export_operational_solution(art,data,cfg,out/"physical_export",enforce_qc=False).get("status")
        except Exception as exc:result["physical_export_error"]=str(exc)
        if a.hours<=24:np.save(out/"solution.npy",m.getAttr("X"))
    save(out/"result.json",result);print(json.dumps(result),flush=True);m.dispose()


if __name__=="__main__":main()
