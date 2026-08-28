"""Compare old/new local MPS; prove every bound change and solve only candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import gurobipy as gp
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cispo_model.zero_bound_certificate import certify
from cispo_model.lp_equilibration import matrix_summary, original_quality
from scripts.validate_lp_equilibration import arrays, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.before, args.after):
        if path.suffix != ".mps" or path.stat().st_size > 384 * 1024**2:
            raise ValueError("Only bounded local MPS regression supported")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    original = gp.read(str(args.before.resolve()), env=env)
    candidate = gp.read(str(args.after.resolve()), env=env)
    old, new = arrays(original), arrays(candidate)
    same = {"matrix_values": np.array_equal(old[0].data, new[0].data),
            "matrix_indices": np.array_equal(old[0].indices, new[0].indices),
            "matrix_indptr": np.array_equal(old[0].indptr, new[0].indptr),
            "rhs": np.array_equal(old[1], new[1]), "objective": np.array_equal(old[2], new[2]),
            "lower_bounds": np.array_equal(old[3], new[3]),
            "sense": original.getAttr("Sense") == candidate.getAttr("Sense"),
            "row_names": original.getAttr("ConstrName") == candidate.getAttr("ConstrName"),
            "variable_names": original.getAttr("VarName") == candidate.getAttr("VarName"),
            "objective_constant": original.ObjCon == candidate.ObjCon}
    if not all(same.values()):
        raise ValueError(f"Unexpected model change beyond zero upper bounds: {same}")
    proof = certify(old[0], old[1], old[3], old[4], new[4], np.array(original.getAttr("Sense")),
                    original.getAttr("ConstrName"), original.getAttr("VarName"))
    write_json(out / "zero_bound_certificate.json", proof)
    if proof["status"] != "PASS":
        raise ValueError("Bound changes are not proved by original LP equalities")
    params = dict(Method=2, Threads=2, Presolve=2, Aggregate=1, Crossover=0,
                  NumericFocus=1, ScaleFlag=2, BarConvTol=1e-8, FeasibilityTol=1e-6,
                  OptimalityTol=1e-6, TimeLimit=120, SolutionTarget=1, OutputFlag=1, LogToConsole=0)
    for key, value in params.items():
        candidate.setParam(key, value)
    candidate.Params.LogFile = str(out / "gurobi.log")
    p = candidate.presolve()
    presolved = matrix_summary(*arrays(p))
    p.dispose()
    candidate.optimize()
    report = {"scope": "LOCAL_24H_EXACT_ZERO_BOUND_REGRESSION_NOT_LARGE_SCALE_PERFORMANCE",
              "unchanged": {k: bool(v) for k, v in same.items()},
              "bound_certificate": proof["status"], "changed_upper_bounds": proof["changed_upper_bounds"],
              "params": params, "presolved": presolved, "status": candidate.Status,
              "runtime": candidate.Runtime, "barrier_iterations": candidate.BarIterCount,
              "sol_count": candidate.SolCount, "scientifically_accepted": False, "promotion_allowed": False,
              "input_sha256": {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (args.before, args.after)}}
    if candidate.SolCount:
        x, pi, rc = (np.array(candidate.getAttr(attr)) for attr in ("X", "Pi", "RC"))
        report["original_unit_quality"] = original_quality(*old, np.array(original.getAttr("Sense")), x, pi, rc, original.ObjCon)
        np.savez_compressed(out / "solution.npz", x=x, pi=pi, rc=rc)
    q = report.get("original_unit_quality", {})
    report["local_raw_quality_pass"] = bool(candidate.Status == gp.GRB.OPTIMAL and q and
        all(q[key] <= 1e-5 for key in ("maximum_constraint_violation", "maximum_bound_violation",
                                      "maximum_stationarity_residual", "maximum_dual_sign_violation"))
        and q["relative_objective_gap"] <= 1e-6)
    write_json(out / "report.json", report)
    candidate.dispose()
    original.dispose()
    env.dispose()
    print(json.dumps({"output": str(out), "status": report["status"], "changed_bounds": proof["changed_upper_bounds"]}))
    if not report["local_raw_quality_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
