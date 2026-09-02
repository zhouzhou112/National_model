"""Compare two archived diagnostic physical LPs against the reviewed whitelist."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

import gurobipy as gp
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.physical_lp_diff import compare_physical_lp_arrays
from cispo_model.zero_bound_certificate import certify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-mps", type=Path, required=True)
    parser.add_argument("--candidate-mps", type=Path, required=True)
    parser.add_argument(
        "--whitelist",
        type=Path,
        default=PROJECT_ROOT / "config" / "physical_lp_diff_whitelist_v1.json",
    )
    parser.add_argument("--reference-commit", required=True)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--reference-formulation", default="physical_v1")
    parser.add_argument("--candidate-formulation", default="physical_v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    whitelist = json.loads(args.whitelist.read_text(encoding="utf-8"))
    if whitelist.get("schema_version") != "cispo_physical_lp_diff_whitelist_v1":
        raise SystemExit("Unsupported physical-LP diff whitelist")
    if args.reference_formulation != whitelist["required_reference_formulation"]:
        raise SystemExit("Reference LP is not declared physical_v1")
    if args.candidate_formulation != whitelist["required_candidate_formulation"]:
        raise SystemExit("Candidate LP is not declared physical_v1")
    if args.reference_commit == args.candidate_commit:
        raise SystemExit("Reference and candidate commits must differ")

    reference = gp.read(str(args.reference_mps.resolve()))
    candidate = gp.read(str(args.candidate_mps.resolve()))
    try:
        reference.update()
        candidate.update()
        reference_variables = reference.getVars()
        candidate_variables = candidate.getVars()
        reference_constraints = reference.getConstrs()
        candidate_constraints = candidate.getConstrs()
        variable_names = reference.getAttr("VarName", reference_variables)
        row_names = reference.getAttr("ConstrName", reference_constraints)
        identity_checks = {
            "variable_names_identical": variable_names
            == candidate.getAttr("VarName", candidate_variables),
            "constraint_names_identical": row_names
            == candidate.getAttr("ConstrName", candidate_constraints),
            "model_sense_identical": int(reference.ModelSense)
            == int(candidate.ModelSense),
            "objective_constant_identical": float(reference.ObjCon)
            == float(candidate.ObjCon),
            "both_continuous_linear": bool(
                not reference.IsMIP
                and not candidate.IsMIP
                and int(reference.NumQNZs) == int(candidate.NumQNZs) == 0
                and int(reference.NumQConstrs)
                == int(candidate.NumQConstrs)
                == 0
            ),
        }
        if not all(identity_checks.values()):
            report = {
                "schema_version": "cispo_physical_lp_release_diff_v1",
                "status": "FAIL",
                "identity_checks": identity_checks,
                "reason": "Physical LP identities differ; indexed comparison refused",
            }
        else:
            reference_matrix = reference.getA().tocsr()
            candidate_matrix = candidate.getA().tocsr()
            reference_lower = np.asarray(
                reference.getAttr("LB", reference_variables), dtype=float
            )
            reference_upper = np.asarray(
                reference.getAttr("UB", reference_variables), dtype=float
            )
            candidate_upper = np.asarray(
                candidate.getAttr("UB", candidate_variables), dtype=float
            )
            report = compare_physical_lp_arrays(
                reference_matrix=reference_matrix,
                candidate_matrix=candidate_matrix,
                reference_rhs=np.asarray(
                    reference.getAttr("RHS", reference_constraints), dtype=float
                ),
                candidate_rhs=np.asarray(
                    candidate.getAttr("RHS", candidate_constraints), dtype=float
                ),
                reference_lower=reference_lower,
                candidate_lower=np.asarray(
                    candidate.getAttr("LB", candidate_variables), dtype=float
                ),
                reference_upper=reference_upper,
                candidate_upper=candidate_upper,
                reference_objective=np.asarray(
                    reference.getAttr("Obj", reference_variables), dtype=float
                ),
                candidate_objective=np.asarray(
                    candidate.getAttr("Obj", candidate_variables), dtype=float
                ),
                reference_senses=reference.getAttr("Sense", reference_constraints),
                candidate_senses=candidate.getAttr("Sense", candidate_constraints),
                row_names=row_names,
                variable_names=variable_names,
                whitelist=whitelist,
            )
            zero_certificate = certify(
                reference_matrix,
                np.asarray(reference.getAttr("RHS", reference_constraints)),
                reference_lower,
                reference_upper,
                candidate_upper,
                np.asarray(reference.getAttr("Sense", reference_constraints)),
                row_names,
                variable_names,
            )
            report["exact_zero_bound_certificate"] = zero_certificate
            report["identity_checks"] = identity_checks
            if zero_certificate["status"] != "PASS":
                report["status"] = "FAIL"
        report.update(
            generated_at=datetime.now().astimezone().isoformat(),
            reference_commit=args.reference_commit,
            candidate_commit=args.candidate_commit,
            reference_mps=str(args.reference_mps.resolve()),
            candidate_mps=str(args.candidate_mps.resolve()),
            whitelist=str(args.whitelist.resolve()),
        )
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
        if report["status"] != "PASS":
            raise SystemExit(2)
    finally:
        reference.dispose()
        candidate.dispose()


if __name__ == "__main__":
    main()
