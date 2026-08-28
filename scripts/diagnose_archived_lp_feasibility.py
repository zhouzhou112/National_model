"""Bounded homogeneous-Barrier feasibility diagnosis of a failed LOCAL LP.

No model relaxation. If INFEASIBLE, request IIS within the same bounded local
diagnostic policy and preserve its members. This is not a performance case.
"""
import argparse
import json
from pathlib import Path
import time

import gurobipy as gp
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.input.stat().st_size > 384 * 1024**2 or args.input.suffix != ".mps":
        raise ValueError("Only bounded local plain MPS supported")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    model = gp.read(str(args.input.resolve()), env=env)
    params = {"Method": 2, "Threads": 2, "Crossover": 0, "Presolve": 2,
              "NumericFocus": 1, "ScaleFlag": 2, "Aggregate": 1,
              "FeasibilityTol": 1e-6, "OptimalityTol": 1e-6, "BarConvTol": 1e-8,
              "BarHomogeneous": 1, "DualReductions": 0, "InfUnbdInfo": 1,
              "TimeLimit": 120, "OutputFlag": 1, "LogToConsole": 0}
    for key, value in params.items():
        model.setParam(key, value)
    model.Params.LogFile = str(out / "gurobi.log")
    model.optimize()
    report = {"scope": "LOCAL_FEASIBILITY_DIAGNOSIS_NOT_PARAMETER_SCREEN",
              "input": str(args.input.resolve()), "fingerprint": model.Fingerprint,
              "params": params, "status": int(model.Status), "runtime": model.Runtime,
              "sol_count": model.SolCount, "relaxation_performed": False,
              "scientifically_accepted": False}
    if model.Status == gp.GRB.INFEASIBLE:
        started = time.monotonic()
        model.computeIIS()
        report.update(iis_seconds=time.monotonic()-started, iis_minimal=bool(model.IISMinimal),
                      iis_constraints=[c.ConstrName for c in model.getConstrs() if c.IISConstr],
                      iis_lower_bounds=[v.VarName for v in model.getVars() if v.IISLB],
                      iis_upper_bounds=[v.VarName for v in model.getVars() if v.IISUB])
        model.write(str(out / "conflict.ilp"))
    elif model.SolCount:
        report["objective"] = model.ObjVal
        report["quality"] = {key: model.getAttr(key) for key in ("ConstrVio", "BoundVio", "DualVio", "ComplVio")}
        x = np.array(model.getAttr("X"))
        pi = np.array(model.getAttr("Pi"))
        rc = np.array(model.getAttr("RC"))
        np.savez_compressed(out / "diagnostic_vectors.npz", x=x, pi=pi, rc=rc)
        matrix = model.getA().tocsr()
        rhs = np.array(model.getAttr("RHS"))
        sense = np.array(model.getAttr("Sense"))
        residual = matrix @ x - rhs
        violation = np.where(sense == "<", np.maximum(residual, 0),
                             np.where(sense == ">", np.maximum(-residual, 0), np.abs(residual)))
        names = model.getAttr("ConstrName")
        report["worst_original_rows"] = []
        for i in np.argsort(violation)[-20:][::-1]:
            values = np.abs(matrix.data[matrix.indptr[i]:matrix.indptr[i+1]])
            report["worst_original_rows"].append({"row": names[i], "violation": float(violation[i]),
                "rhs": float(rhs[i]), "minimum_coefficient": float(values.min()) if len(values) else None,
                "maximum_coefficient": float(values.max()) if len(values) else None})
    (out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(out)}))
    model.dispose()
    env.dispose()


if __name__ == "__main__":
    main()
