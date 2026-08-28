"""Local archived-LP A/B gate; never connects to a server or production runner.

Example: python scripts/validate_lp_equilibration.py --input saved/original.mps
  --output-dir outputs/scaling_gate --solve
Default is scaling/presolve diagnosis only. Rejects input over 384 MiB before
loading, and LPs over 2 million nonzeros before getA; not a full-size solver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import gurobipy as gp
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cispo_model.lp_equilibration import (matrix_summary, original_quality,
    propose_scaling, transform, verify_roundtrip, pulled_back_tolerances)


def arrays(model):
    model.update()
    lb, ub = np.array(model.getAttr("LB")), np.array(model.getAttr("UB"))
    lb[lb <= -gp.GRB.INFINITY] = -np.inf
    ub[ub >= gp.GRB.INFINITY] = np.inf
    return model.getA().tocsr(), np.array(model.getAttr("RHS")), np.array(model.getAttr("Obj")), lb, ub


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--exponent-limit", type=int, default=9)
    parser.add_argument("--legacy-unbudgeted-diagnostic", action="store_true",
                        help="Only reproduce rejected v1; never a promotion candidate")
    args = parser.parse_args()
    source = args.input.resolve()
    if not source.is_file() or source.stat().st_size > 384 * 1024**2 or source.suffix != ".mps":
        raise ValueError("This bounded local gate accepts only plain archived MPS <=384 MiB")
    out = args.output_dir.resolve()
    if source == out or out in source.parents:
        raise ValueError("Output must not contain/overwrite the source archive")
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    original = gp.read(str(source), env=env)
    original.update()
    if (original.IsMIP or original.NumQNZs or original.NumQConstrs or original.NumGenConstrs
            or original.NumPWLObjVars or original.ModelSense != gp.GRB.MINIMIZE
            or original.DNumNZs > 2_000_000):
        raise ValueError("Only bounded-size, single-objective continuous linear minimization supported")
    data = arrays(original)
    if not np.all(np.isfinite(data[0].data)):
        raise ValueError("Nonfinite source matrix")
    scaling = propose_scaling(data[0], data[2], exponent_limit=args.exponent_limit)
    tolerance_budget = None if args.legacy_unbudgeted_diagnostic else pulled_back_tolerances(scaling)
    transformed = transform(*data, scaling)
    roundtrip = verify_roundtrip(data, transformed, scaling)
    if not all(roundtrip.values()):
        raise ValueError(f"Exact inverse verification failed: {roundtrip}")
    np.savez_compressed(out / "scaling_map.npz", row_exponents=scaling.row_exponents,
                        column_exponents=scaling.column_exponents)
    candidate = gp.Model("binary_equilibrated_archived_lp", env=env)
    a, b, c, lower, upper = transformed
    z = candidate.addMVar(a.shape[1], lb=lower, ub=upper, obj=c, name="z")
    senses = np.array(original.getAttr("Sense"))
    candidate.addMConstr(a, z, senses, b, name="scaled")
    candidate.ObjCon = original.ObjCon
    candidate.update()
    candidate.setAttr("VarName", candidate.getVars(), original.getAttr("VarName"))
    candidate.setAttr("ConstrName", candidate.getConstrs(), original.getAttr("ConstrName"))
    candidate.update()
    candidate.write(str(out / "scaled.mps"))
    reread = gp.read(str(out / "scaled.mps"), env=env)
    reread_data = arrays(reread)
    exported_roundtrip = verify_roundtrip(data, reread_data, scaling)
    exported_roundtrip["row_senses"] = reread.getAttr("Sense") == original.getAttr("Sense")
    exported_roundtrip["variable_names"] = reread.getAttr("VarName") == original.getAttr("VarName")
    exported_roundtrip["constraint_names"] = reread.getAttr("ConstrName") == original.getAttr("ConstrName")
    exported_roundtrip["objective_constant"] = reread.ObjCon == original.ObjCon
    reread.dispose()
    if not all(exported_roundtrip.values()):
        raise ValueError(f"Export/readback changed model: {exported_roundtrip}")
    params = dict(Method=2, Threads=2, Presolve=2, Aggregate=1, Crossover=0,
                  NumericFocus=1, ScaleFlag=2, BarConvTol=1e-8,
                  FeasibilityTol=1e-6, OptimalityTol=1e-6, TimeLimit=120,
                  SolutionTarget=1, OutputFlag=1, LogToConsole=0)
    report = {"scope": "LOCAL_BOUNDED_ARCHIVE_EQUIVALENCE_GATE_NOT_LARGE_SCALE_BENCHMARK",
              "input": str(source), "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "gurobi_version": list(gp.gurobi.version()), "python": sys.version,
              "recipe": {"name": "binary_geometric_center_tolerance_budget_v2", "iterations": 8,
                         "exponent_limit": args.exponent_limit,
                         "independent_objective_scaling": False, "coefficient_dropping": False},
              "base_params": params, "scaled_tolerance_budget": tolerance_budget, "roundtrip": roundtrip,
              "exported_roundtrip": exported_roundtrip,
              "source_fingerprint": original.Fingerprint,
              "before": matrix_summary(*data), "after": matrix_summary(*transformed),
              "scale_ranges": {"row_exponents": [int(scaling.row_exponents.min()), int(scaling.row_exponents.max())],
                               "column_exponents": [int(scaling.column_exponents.min()), int(scaling.column_exponents.max())]},
              "cases": {}, "scientifically_accepted": False}
    write_json(out / "report.json", report)
    for name, model in (("original", original), ("scaled", candidate)):
        actual_params = dict(params)
        if name == "scaled" and tolerance_budget:
            actual_params.update({key: tolerance_budget[key] for key in ("FeasibilityTol", "OptimalityTol")})
        for key, value in actual_params.items():
            model.setParam(key, value)
        model.setParam("LogFile", str(out / f"{name}.log"))
        case_start = time.monotonic()
        p = model.presolve()
        presolve_seconds = time.monotonic() - case_start
        presolved_data = arrays(p)
        presolve_stats = matrix_summary(*presolved_data)
        p.write(str(out / f"{name}_presolved.mps"))
        p.dispose()
        entry = {"actual_params": actual_params, "diagnostic_presolve_seconds": presolve_seconds, "presolved": presolve_stats}
        report["cases"][name] = entry
        if args.solve:
            model.optimize()
            entry.update(status=int(model.Status), runtime_seconds=float(model.Runtime),
                         barrier_iterations=int(model.BarIterCount), solutions=int(model.SolCount))
            if model.SolCount:
                x = np.array(model.getAttr("X"))
                pi = np.array(model.getAttr("Pi"))
                rc = np.array(model.getAttr("RC"))
                if name == "scaled":
                    x = scaling.primal_to_original(x)
                    pi = scaling.dual_to_original(pi)
                    rc = scaling.reduced_cost_to_original(rc)
                np.savez_compressed(out / f"{name}_mapped_solution.npz", x=x, pi=pi, rc=rc)
                entry["original_unit_quality"] = original_quality(*data, senses, x, pi, rc, original.ObjCon)
                q = entry["original_unit_quality"]
                entry["raw_quality_gate_1e_minus5"] = bool(
                    model.Status == gp.GRB.OPTIMAL and all(q[key] <= 1e-5 for key in (
                        "maximum_constraint_violation", "maximum_bound_violation",
                        "maximum_stationarity_residual", "maximum_dual_sign_violation"))
                    and q["relative_objective_gap"] <= 1e-6)
        write_json(out / "report.json", report)
    report["wall_seconds"] = time.monotonic() - start
    report["gate"] = "EQUIVALENCE_PASS_NOT_SCIENTIFIC_ACCEPTANCE"
    report["promotion_allowed"] = False
    if args.solve:
        report["local_raw_quality_pair_pass"] = all(
            entry.get("raw_quality_gate_1e_minus5", False) for entry in report["cases"].values())
        if not report["local_raw_quality_pair_pass"]:
            report["gate"] = "EQUIVALENCE_PASS_BUT_SOLVE_OR_RAW_QUALITY_REJECTED"
    if args.solve and all("original_unit_quality" in v for v in report["cases"].values()):
        q0, q1 = (report["cases"][key]["original_unit_quality"] for key in ("original", "scaled"))
        report["paired_objective_relative_difference"] = abs(q0["primal_objective"] - q1["primal_objective"]) / max(1, abs(q0["primal_objective"]))
    write_json(out / "report.json", report)
    candidate.dispose()
    original.dispose()
    env.dispose()
    print(json.dumps({"output": str(out), "gate": report["gate"], "wall_seconds": report["wall_seconds"]}))
    if args.solve and not report["local_raw_quality_pair_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
