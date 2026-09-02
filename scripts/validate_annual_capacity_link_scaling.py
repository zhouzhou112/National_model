"""Validate the single targeted Stage A row-scaling formulation.

The default 24h run is a correctness smoke test, not a performance verdict.
It builds physical and scaled LPs from the same data, proves that only the
registered VRE/ROR rows differ, and optionally solves both models for an
original-unit QC comparison.  It deliberately refuses horizons above 168h:
formal 2160h performance qualification uses one isolated model/process, not
two co-resident models and duplicate sparse matrices.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import gurobipy as gp

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config
from cispo_model.annual_capacity_link_scaling import (
    validate_row_scaling_registry,
)
from cispo_model.data import load_model_data
from cispo_model.diagnostics import configure_gurobi
from cispo_model.master import export_master_solution
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.solution_export import export_operational_solution
from scripts.run_cispo_2030_full_year import load_center_physical_qc_pass


FORMULATION_PROFILE = (
    PROJECT_ROOT
    / "config"
    / "formulation_profiles"
    / "annual_capacity_link_rows_8192_v1.json"
)


def _names(model, kind: str) -> list[str]:
    objects = model.getVars() if kind == "variable" else model.getConstrs()
    attribute = "VarName" if kind == "variable" else "ConstrName"
    return list(model.getAttr(attribute, objects))


def _column_span(matrix, variable_names: list[str], prefix: str) -> dict:
    columns = np.asarray(
        [i for i, name in enumerate(variable_names) if name.startswith(prefix)],
        dtype=np.int64,
    )
    csc = matrix[:, columns].tocsc()
    ratios = []
    family_min = float("inf")
    family_max = 0.0
    for column in range(csc.shape[1]):
        values = np.abs(csc.data[csc.indptr[column]:csc.indptr[column + 1]])
        values = values[values > 0.0]
        if not len(values):
            continue
        minimum = float(values.min())
        maximum = float(values.max())
        family_min = min(family_min, minimum)
        family_max = max(family_max, maximum)
        ratios.append(maximum / minimum)
    return {
        "columns": int(len(columns)),
        "coefficient_min_abs": family_min if np.isfinite(family_min) else 0.0,
        "coefficient_max_abs": family_max,
        "maximum_column_span": float(max(ratios) if ratios else 1.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--diagnostic-start-hour", type=int, default=0)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--time-limit-seconds", type=float, default=3600.0)
    args = parser.parse_args()
    if not 1 <= args.hours <= 168:
        raise SystemExit(
            "--hours must be in [1, 168]; use the isolated single-model "
            "runner for 2160h/8760h performance qualification"
        )
    if not 0 <= args.diagnostic_start_hour <= 8760 - args.hours:
        raise SystemExit("Invalid diagnostic window")

    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    baseline_config = load_model_config()
    candidate_config = load_model_config(formulation_path=FORMULATION_PROFILE)
    data = load_model_data(baseline_config)
    models = {}
    try:
        for role, config in (
            ("physical", baseline_config),
            ("scaled", candidate_config),
        ):
            models[role] = build_full_year_monolithic(
                config,
                data,
                optimization_hours=args.hours,
                optimization_start_hour=args.diagnostic_start_hour,
            )
            models[role].model.update()

        physical = models["physical"].model
        scaled = models["scaled"].model
        variable_names = _names(physical, "variable")
        scaled_variable_names = _names(scaled, "variable")
        constraint_names = _names(physical, "constraint")
        scaled_constraint_names = _names(scaled, "constraint")
        physical_constraints = physical.getConstrs()
        scaled_constraints = scaled.getConstrs()
        physical_variables = physical.getVars()
        scaled_variables = scaled.getVars()
        physical_matrix = physical.getA().tocsr()
        scaled_matrix = scaled.getA().tocsr()
        registry = models["scaled"].index[
            "annual_capacity_link_row_scaling"
        ]
        registry_model_binding_error = None
        try:
            validate_row_scaling_registry(registry, model=scaled)
        except ValueError as error:
            registry_model_binding_error = str(error)

        row_factors = np.ones(len(constraint_names), dtype=float)
        target_rows = np.zeros(len(constraint_names), dtype=bool)
        family_rows = {}
        for family, metadata in registry["families"].items():
            prefix = str(metadata["constraint_prefix"])
            mask = np.fromiter(
                (name.startswith(prefix) for name in constraint_names),
                dtype=bool,
                count=len(constraint_names),
            )
            row_factors[mask] = float(metadata["row_scale"])
            target_rows |= mask
            family_rows[family] = int(mask.sum())
        expected_data = physical_matrix.data * np.repeat(
            row_factors, np.diff(physical_matrix.indptr)
        )
        same_support = bool(
            np.array_equal(physical_matrix.indptr, scaled_matrix.indptr)
            and np.array_equal(physical_matrix.indices, scaled_matrix.indices)
        )
        matrix_exact = bool(
            same_support and np.array_equal(expected_data, scaled_matrix.data)
        )
        unscaled_exact = bool(
            np.array_equal(
                physical_matrix[~target_rows].data,
                scaled_matrix[~target_rows].data,
            )
        )
        target_values = np.abs(scaled_matrix[target_rows].data)
        target_values = target_values[target_values > 0.0]
        physical_rhs = np.asarray(
            physical.getAttr("RHS", physical_constraints), dtype=float
        )
        scaled_rhs = np.asarray(
            scaled.getAttr("RHS", scaled_constraints), dtype=float
        )
        checks = {
            "both_models_are_continuous_lp": bool(
                not physical.IsMIP
                and not scaled.IsMIP
                and set(physical.getAttr("VType", physical_variables)) == {"C"}
                and set(scaled.getAttr("VType", scaled_variables)) == {"C"}
                and int(physical.NumQNZs) == 0
                and int(scaled.NumQNZs) == 0
                and int(physical.NumQConstrs) == 0
                and int(scaled.NumQConstrs) == 0
            ),
            "objective_direction_and_constant_identical": bool(
                int(physical.ModelSense) == int(scaled.ModelSense)
                and float(physical.ObjCon) == float(scaled.ObjCon)
            ),
            "variable_names_identical": variable_names == scaled_variable_names,
            "constraint_names_identical": constraint_names
            == scaled_constraint_names,
            "constraint_senses_identical": physical.getAttr(
                "Sense", physical_constraints
            )
            == scaled.getAttr("Sense", scaled_constraints),
            "matrix_support_identical": same_support,
            "only_registered_rows_scaled_exactly": matrix_exact
            and unscaled_exact,
            "rhs_scaled_exactly": np.array_equal(
                row_factors * physical_rhs, scaled_rhs
            ),
            "lower_bounds_identical": np.array_equal(
                np.asarray(physical.getAttr("LB", physical_variables)),
                np.asarray(scaled.getAttr("LB", scaled_variables)),
            ),
            "upper_bounds_identical": np.array_equal(
                np.asarray(physical.getAttr("UB", physical_variables)),
                np.asarray(scaled.getAttr("UB", scaled_variables)),
            ),
            "objective_identical": np.array_equal(
                np.asarray(physical.getAttr("Obj", physical_variables)),
                np.asarray(scaled.getAttr("Obj", scaled_variables)),
            ),
            "fingerprint_changed": int(physical.Fingerprint)
            != int(scaled.Fingerprint),
            "no_new_target_coefficient_below_1e_6": bool(
                len(target_values) and target_values.min() >= 1e-6
            ),
            "registry_row_counts_match": all(
                family_rows[family] == int(metadata["constraint_rows"])
                for family, metadata in registry["families"].items()
            ),
            "registry_deep_model_binding": (
                registry_model_binding_error is None
            ),
        }
        report = {
            "schema_version": "cispo_annual_capacity_link_validation_v1",
            "generated_at": datetime.now().astimezone().isoformat(),
            "status": "PASS" if all(checks.values()) else "FAIL",
            "interpretation": (
                "Correctness evidence only; short-horizon solve speed is not "
                "a 32-thread or 8760h performance gate."
            ),
            "hours": args.hours,
            "diagnostic_start_hour": args.diagnostic_start_hour,
            "checks": checks,
            "registry": registry,
            "registry_model_binding_error": registry_model_binding_error,
            "model_counts": {
                "variables": int(physical.NumVars),
                "constraints": int(physical.NumConstrs),
                "nonzeros": int(physical.NumNZs),
                "target_rows": int(target_rows.sum()),
                "target_nonzeros": int(len(target_values)),
            },
            "target_scaled_coefficient_min_abs": float(target_values.min()),
            "target_scaled_coefficient_max_abs": float(target_values.max()),
            "capacity_column_spans": {
                "physical": {
                    "vre": _column_span(
                        physical_matrix, variable_names, "vre_capacity_gw["
                    ),
                    "hydro": _column_span(
                        physical_matrix, variable_names, "hydro_capacity_gw["
                    ),
                },
                "scaled": {
                    "vre": _column_span(
                        scaled_matrix, variable_names, "vre_capacity_gw["
                    ),
                    "hydro": _column_span(
                        scaled_matrix, variable_names, "hydro_capacity_gw["
                    ),
                },
            },
            "solve": {"requested": bool(args.solve)},
        }
        if args.solve:
            solve_results = {}
            for role, config in (
                ("physical", baseline_config),
                ("scaled", candidate_config),
            ):
                artifact = models[role]
                config.raw["numerics"]["time_limit_seconds"] = float(
                    args.time_limit_seconds
                )
                configured_threads = int(config.raw["numerics"]["threads"])
                config.raw["numerics"]["threads"] = min(
                    4,
                    configured_threads if configured_threads > 0 else 4,
                )
                configure_gurobi(
                    artifact.model, config, output / f"{role}_gurobi.log"
                )
                artifact.model.Params.OutputFlag = 0
                artifact.model.optimize()
                role_output = output / role
                role_output.mkdir()
                master_qc = None
                operational_qc = None
                if artifact.model.Status == gp.GRB.OPTIMAL:
                    master_qc = export_master_solution(
                        artifact, data, role_output, enforce_qc=False
                    )
                    operational_qc = export_operational_solution(
                        artifact,
                        data,
                        config,
                        role_output,
                        enforce_qc=False,
                    )
                solve_results[role] = {
                    "status": int(artifact.model.Status),
                    "objective": (
                        float(artifact.model.ObjVal)
                        if artifact.model.SolCount
                        else None
                    ),
                    "runtime_seconds": float(artifact.model.Runtime),
                    "barrier_iterations": int(artifact.model.BarIterCount),
                    "master_physical_qc": master_qc,
                    "operational_qc_status": (
                        operational_qc.get("status")
                        if operational_qc is not None
                        else None
                    ),
                }
            report["solve"].update(results=solve_results)
            both_optimal = all(
                row["status"] == int(gp.GRB.OPTIMAL)
                for row in solve_results.values()
            )
            objectives_match = bool(
                both_optimal
                and np.isclose(
                    solve_results["physical"]["objective"],
                    solve_results["scaled"]["objective"],
                    rtol=1e-8,
                    atol=1e-5,
                )
            )
            report["solve"]["both_optimal"] = both_optimal
            report["solve"]["objectives_match"] = objectives_match
            physical_qc_pass = bool(
                load_center_physical_qc_pass(
                    solve_results["physical"]["master_physical_qc"]
                )
                and solve_results["physical"]["operational_qc_status"]
                == "PASS"
            )
            scaled_qc_pass = bool(
                load_center_physical_qc_pass(
                    solve_results["scaled"]["master_physical_qc"]
                )
                and solve_results["scaled"]["operational_qc_status"]
                == "PASS"
            )
            report["solve"]["physical_original_unit_qc_pass"] = (
                physical_qc_pass
            )
            report["solve"]["scaled_original_unit_qc_pass"] = scaled_qc_pass
            report["status"] = (
                "PASS"
                if report["status"] == "PASS"
                and both_optimal
                and objectives_match
                and physical_qc_pass
                and scaled_qc_pass
                else "FAIL"
            )
        (output / "validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["status"] != "PASS":
            raise SystemExit(2)
    finally:
        for artifacts in models.values():
            artifacts.model.dispose()


if __name__ == "__main__":
    main()
