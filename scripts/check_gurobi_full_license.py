"""Verify the Gurobi version and reject a size-limited fallback license.

The bundled restricted license cannot solve a model with more than 2,000
variables. This script constructs 2,501 variables, solves a deterministic LP,
and exits non-zero unless Gurobi 13.0.2 and a full license are both active.
"""
from __future__ import annotations

import json
import math

import gurobipy as gp
from gurobipy import GRB


EXPECTED_VERSION = (13, 0, 2)
N_VARIABLES = 2_501


def check_full_license() -> dict[str, object]:
    version = tuple(gp.gurobi.version())
    if version != EXPECTED_VERSION:
        raise RuntimeError(
            f"Expected gurobipy {EXPECTED_VERSION}, found {version}."
        )

    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model("cispo_full_license_gate", env=env) as model:
            model.Params.Threads = 1
            x = model.addVars(N_VARIABLES, lb=0.0, name="x")
            model.addConstr(gp.quicksum(x.values()) >= 1.0, name="minimum_activity")
            model.setObjective(gp.quicksum(x.values()), GRB.MINIMIZE)
            model.optimize()

            if model.Status != GRB.OPTIMAL:
                raise RuntimeError(
                    f"License gate model status is {model.Status}, not OPTIMAL."
                )
            if not math.isclose(model.ObjVal, 1.0, rel_tol=0.0, abs_tol=1e-9):
                raise RuntimeError(f"Unexpected objective value: {model.ObjVal}.")
            variables = model.NumVars
            constraints = model.NumConstrs
            objective = model.ObjVal

    return {
        "status": "PASS",
        "gurobi_version": ".".join(map(str, version)),
        "variables": variables,
        "constraints": constraints,
        "objective": objective,
        "license_gate": "FULL_LICENSE_CONFIRMED_ABOVE_2000_VARIABLES",
    }


def main() -> None:
    result = check_full_license()

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
