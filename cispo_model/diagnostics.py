"""Gurobi parameterization and reproducible model diagnostics."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from .config import ModelConfig


def configure_gurobi(model: gp.Model, config: ModelConfig, log_path: Path) -> None:
    numerics = config.raw["numerics"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    model.Params.LogFile = str(log_path)
    model.Params.FeasibilityTol = float(numerics["feasibility_tolerance"])
    model.Params.OptimalityTol = float(numerics["optimality_tolerance"])
    model.Params.MarkowitzTol = float(numerics["markowitz_tolerance"])
    model.Params.NumericFocus = int(numerics["numeric_focus"])
    model.Params.ScaleFlag = int(numerics["scale_flag"])
    model.Params.Presolve = int(numerics["presolve"])
    model.Params.Method = int(numerics["method"])
    model.Params.BarConvTol = float(numerics["barrier_convergence_tolerance"])
    model.Params.Crossover = int(numerics["crossover"])
    configured_threads = int(numerics["threads"])
    if configured_threads == -1 and gp.gurobi.version()[0] < 13:
        # Gurobi 13 defines -1 as all virtual processors. Older supported
        # local installations require the explicit logical-CPU count.
        configured_threads = int(os.cpu_count() or 1)
    model.Params.Threads = configured_threads
    model.Params.TimeLimit = float(numerics["time_limit_seconds"])
    model.Params.SoftMemLimit = float(numerics["soft_mem_limit_gb"])
    model.Params.OutputFlag = int(numerics["output_flag"])
    model.Params.DualReductions = 0
    model.Params.InfUnbdInfo = 1
    if "pdhg_gpu" in numerics:
        try:
            model.Params.PDHGGPU = int(numerics["pdhg_gpu"])
        except gp.GurobiError as error:
            raise RuntimeError(
                "numerics.pdhg_gpu requires a Gurobi version that exposes PDHGGPU"
            ) from error


def model_statistics(model: gp.Model) -> dict:
    model.update()
    return {
        "variables": int(model.NumVars),
        "constraints": int(model.NumConstrs),
        "nonzeros": int(model.NumNZs),
        "coefficient_min_abs": float(model.MinCoeff) if model.NumNZs else 0.0,
        "coefficient_max_abs": float(model.MaxCoeff) if model.NumNZs else 0.0,
        "objective_coefficient_min_abs": float(model.MinObjCoeff) if model.NumVars else 0.0,
        "objective_coefficient_max_abs": float(model.MaxObjCoeff) if model.NumVars else 0.0,
        "rhs_min_abs": float(model.MinRHS) if model.NumConstrs else 0.0,
        "rhs_max_abs": float(model.MaxRHS) if model.NumConstrs else 0.0,
        "quadratic_constraints": int(model.NumQConstrs),
        "integer_variables": int(model.NumIntVars),
        "binary_variables": int(model.NumBinVars),
    }


def solve_and_report(
    model: gp.Model,
    config: ModelConfig,
    output_dir: Path,
    *,
    compute_iis: bool = True,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_gurobi(model, config, output_dir / "gurobi.log")
    before = model_statistics(model)
    model.optimize()
    status_name = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.MEM_LIMIT: "MEM_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }.get(model.Status, str(model.Status))
    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status_name,
        "status_code": int(model.Status),
        "runtime_seconds": float(model.Runtime),
        "work_units": float(model.Work),
        "model_statistics": before,
        "objective_value_million_cny": float(model.ObjVal) if model.SolCount else None,
        "best_bound_million_cny": float(model.ObjBound) if model.IsMIP and model.SolCount else None,
        "solution_count": int(model.SolCount),
        "configuration": str(config.path),
        "solver_parameters": {
            "method": int(model.Params.Method),
            "threads": int(model.Params.Threads),
            "available_logical_cpus": int(os.cpu_count() or 1),
            "crossover": int(model.Params.Crossover),
            "numeric_focus": int(model.Params.NumericFocus),
            "scale_flag": int(model.Params.ScaleFlag),
            "feasibility_tolerance": float(model.Params.FeasibilityTol),
            "optimality_tolerance": float(model.Params.OptimalityTol),
            "barrier_convergence_tolerance": float(model.Params.BarConvTol),
            "pdhg_gpu": int(getattr(model.Params, "PDHGGPU", 0)),
        },
        "iteration_counts": {
            "simplex": float(model.IterCount),
            "barrier": int(model.BarIterCount),
            "pdhg": int(getattr(model, "PDHGIterCount", 0)),
        },
    }
    if model.SolCount:
        report["solution_quality"] = {
            "maximum_constraint_violation": float(model.ConstrVio),
            "maximum_bound_violation": float(model.BoundVio),
            "maximum_dual_violation": float(model.DualVio),
        }
    if model.Status == GRB.INFEASIBLE and compute_iis:
        model.computeIIS()
        model.write(str(output_dir / "iis.ilp"))
        report["iis_path"] = str(output_dir / "iis.ilp")
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
