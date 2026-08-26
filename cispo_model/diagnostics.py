"""Gurobi parameterization and reproducible model diagnostics."""
from __future__ import annotations

import json
import math
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Any

import gurobipy as gp
import numpy as np
from gurobipy import GRB

from .config import ModelConfig


SOLUTION_LOCATION_LOOKUP_MAX_OBJECTS = 6_000_000


class SolverTelemetry:
    """Persist low-overhead solver progress that survives a later hard kill."""

    def __init__(self, path: Path, *, progress_interval_seconds: float = 30.0):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.progress_interval_seconds = float(progress_interval_seconds)
        self._stream = path.open("w", encoding="utf-8", buffering=1)
        self._last_iteration: dict[str, float] = {}
        self._last_runtime: dict[str, float] = {}
        self._callback_error_recorded = False

    @staticmethod
    def _cb_get(model: gp.Model, code_name: str) -> float | None:
        code = getattr(GRB.Callback, code_name, None)
        if code is None:
            return None
        try:
            return float(model.cbGet(code))
        except gp.GurobiError:
            return None

    def write_event(self, event: str, **values: Any) -> None:
        record = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "event": event,
            **values,
        }
        self._stream.write(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
        self._stream.flush()

    def _should_record(
        self,
        phase: str,
        iteration: float | None,
        runtime: float | None,
        *,
        iteration_step: float,
    ) -> bool:
        previous_iteration = self._last_iteration.get(phase, float("-inf"))
        previous_runtime = self._last_runtime.get(phase, float("-inf"))
        iteration_due = (
            iteration is not None
            and iteration >= previous_iteration + iteration_step
        )
        time_due = (
            runtime is not None
            and runtime >= previous_runtime + self.progress_interval_seconds
        )
        if iteration_due or time_due:
            if iteration is not None:
                self._last_iteration[phase] = iteration
            if runtime is not None:
                self._last_runtime[phase] = runtime
            return True
        return False

    def __call__(self, model: gp.Model, where: int) -> None:
        try:
            phase: str | None = None
            iteration_code: str | None = None
            iteration_step = 1.0
            if where == getattr(GRB.Callback, "BARRIER", -1):
                phase = "barrier"
                iteration_code = "BARRIER_ITRCNT"
            elif where == getattr(GRB.Callback, "PDHG", -1):
                phase = "pdhg"
                iteration_code = "PDHG_ITRCNT"
                iteration_step = 1000.0
            elif where == getattr(GRB.Callback, "SIMPLEX", -1):
                phase = "simplex"
                iteration_code = "SPX_ITRCNT"
                iteration_step = 10000.0
            if phase is None or iteration_code is None:
                return
            iteration = self._cb_get(model, iteration_code)
            runtime = self._cb_get(model, "RUNTIME")
            if not self._should_record(
                phase, iteration, runtime, iteration_step=iteration_step
            ):
                return
            common = {
                "runtime_seconds": runtime,
                "work_units": self._cb_get(model, "WORK"),
                "memory_used_gb": self._cb_get(model, "MEMUSED"),
                "max_memory_used_gb": self._cb_get(model, "MAXMEMUSED"),
            }
            if phase == "barrier":
                self.write_event(
                    "solver_progress",
                    phase="barrier",
                    iteration=iteration,
                    primal_objective=self._cb_get(model, "BARRIER_PRIMOBJ"),
                    dual_objective=self._cb_get(model, "BARRIER_DUALOBJ"),
                    primal_infeasibility=self._cb_get(model, "BARRIER_PRIMINF"),
                    dual_infeasibility=self._cb_get(model, "BARRIER_DUALINF"),
                    complementarity=self._cb_get(model, "BARRIER_COMPL"),
                    **common,
                )
                return
            if phase == "pdhg":
                self.write_event(
                    "solver_progress",
                    phase="pdhg",
                    iteration=iteration,
                    primal_objective=self._cb_get(model, "PDHG_PRIMOBJ"),
                    dual_objective=self._cb_get(model, "PDHG_DUALOBJ"),
                    primal_infeasibility=self._cb_get(model, "PDHG_PRIMINF"),
                    dual_infeasibility=self._cb_get(model, "PDHG_DUALINF"),
                    **common,
                )
                return
            if phase == "simplex":
                self.write_event(
                    "solver_progress",
                    phase="simplex",
                    iteration=iteration,
                    objective=self._cb_get(model, "SPX_OBJVAL"),
                    primal_infeasibility=self._cb_get(model, "SPX_PRIMINF"),
                    dual_infeasibility=self._cb_get(model, "SPX_DUALINF"),
                    **common,
                )
        except Exception as error:  # telemetry must never abort optimization
            if not self._callback_error_recorded:
                self._callback_error_recorded = True
                self.write_event(
                    "telemetry_error",
                    error_type=type(error).__name__,
                    message=str(error),
                )

    def close(self) -> None:
        if not self._stream.closed:
            self._stream.close()


class GracefulSolverTermination:
    """Translate SIGTERM/SIGINT into Model.terminate() when supported."""

    def __init__(self, model: gp.Model, telemetry: SolverTelemetry):
        self.model = model
        self.telemetry = telemetry
        self.received_signal: str | None = None
        self._previous: dict[int, Any] = {}

    def _handler(self, signum: int, _frame: Any) -> None:
        self.received_signal = signal.Signals(signum).name
        self.telemetry.write_event(
            "termination_requested", signal=self.received_signal
        )
        self.model.terminate()

    def __enter__(self) -> GracefulSolverTermination:
        for signum in (signal.SIGINT, signal.SIGTERM):
            self._previous[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handler)
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        for signum, previous in self._previous.items():
            signal.signal(signum, previous)


def configure_gurobi(model: gp.Model, config: ModelConfig, log_path: Path) -> None:
    numerics = config.raw["numerics"]
    minimum_major = int(
        config.raw.get("solver_profile", {}).get(
            "minimum_gurobi_major_version"
        )
        or 0
    )
    installed_major = int(gp.gurobi.version()[0])
    if installed_major < minimum_major:
        raise RuntimeError(
            f"Solver profile requires Gurobi >= {minimum_major}; "
            f"installed major version is {installed_major}"
        )
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
    # A null profile value deliberately leaves Gurobi's default unlimited
    # TimeLimit in place.  This is distinct from choosing a very large but
    # still terminating wall-clock budget for a costly full-year solve.
    if numerics.get("time_limit_seconds") is not None:
        model.Params.TimeLimit = float(numerics["time_limit_seconds"])
    if numerics.get("soft_mem_limit_gb") is not None:
        model.Params.SoftMemLimit = float(numerics["soft_mem_limit_gb"])
    model.Params.OutputFlag = int(numerics["output_flag"])
    model.Params.DualReductions = int(numerics.get("dual_reductions", 1))
    model.Params.InfUnbdInfo = int(numerics.get("inf_unbd_info", 0))
    if "pdhg_gpu" in numerics:
        try:
            model.Params.PDHGGPU = int(numerics["pdhg_gpu"])
        except gp.GurobiError as error:
            raise RuntimeError(
                "numerics.pdhg_gpu requires a Gurobi version that exposes PDHGGPU"
            ) from error
    optional_parameters = {
        "aggregate": ("Aggregate", int),
        "agg_fill": ("AggFill", int),
        "bar_iter_limit": ("BarIterLimit", int),
        "bar_correctors": ("BarCorrectors", int),
        "bar_homogeneous": ("BarHomogeneous", int),
        "bar_order": ("BarOrder", int),
        "crossover_basis": ("CrossoverBasis", int),
        "lp_warm_start": ("LPWarmStart", int),
        "pre_dual": ("PreDual", int),
        "pre_passes": ("PrePasses", int),
        "pre_sparsify": ("PreSparsify", int),
        "pdhg_absolute_tolerance": ("PDHGAbsTol", float),
        "pdhg_convergence_tolerance": ("PDHGConvTol", float),
        "pdhg_iteration_limit": ("PDHGIterLimit", int),
        "pdhg_relative_tolerance": ("PDHGRelTol", float),
        "solution_target": ("SolutionTarget", int),
    }
    for config_key, (parameter_name, converter) in optional_parameters.items():
        if config_key in numerics:
            setattr(
                model.Params,
                parameter_name,
                converter(numerics[config_key]),
            )


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


def _safe_solution_attribute(item: object, name: str) -> float | None:
    try:
        return float(getattr(item, name))
    except (AttributeError, gp.GurobiError, TypeError, ValueError):
        return None


def _solution_quality_location(
    model: gp.Model,
    attribute: str,
    *,
    kind: str,
    variables: list[gp.Var] | None,
    constraints: list[gp.Constr] | None,
) -> dict[str, object] | None:
    """Resolve a quality-index attribute to the responsible named object."""
    try:
        index = int(getattr(model, attribute))
    except (AttributeError, gp.GurobiError, TypeError, ValueError):
        return None
    variable_count = int(model.NumVars)
    constraint_count = int(model.NumConstrs)
    if kind == "dual" and index >= variable_count:
        constraint_index = index - variable_count
        if not 0 <= constraint_index < constraint_count:
            return None
        if constraints is None:
            return {
                "kind": "constraint_slack",
                "index": constraint_index,
                "name": None,
                "lookup_status": "SKIPPED_MODEL_SIZE",
            }
        constraint = constraints[constraint_index]
        return {
            "kind": "constraint_slack",
            "index": constraint_index,
            "name": constraint.ConstrName,
        }
    if kind == "constraint":
        if not 0 <= index < constraint_count:
            return None
        if constraints is None:
            return {
                "kind": "constraint",
                "index": index,
                "name": None,
                "lookup_status": "SKIPPED_MODEL_SIZE",
            }
        constraint = constraints[index]
        return {
            "kind": "constraint",
            "index": index,
            "name": constraint.ConstrName,
            "sense": constraint.Sense,
            "rhs": float(constraint.RHS),
            "slack": _safe_solution_attribute(constraint, "Slack"),
        }
    if not 0 <= index < variable_count:
        return None
    if variables is None:
        return {
            "kind": "variable",
            "index": index,
            "name": None,
            "lookup_status": "SKIPPED_MODEL_SIZE",
        }
    variable = variables[index]
    return {
        "kind": "variable",
        "index": index,
        "name": variable.VarName,
        "lower_bound": float(variable.LB),
        "upper_bound": float(variable.UB),
        "value": _safe_solution_attribute(variable, "X"),
        "barrier_value": _safe_solution_attribute(variable, "BarX"),
        "reduced_cost": _safe_solution_attribute(variable, "RC"),
    }


def solve_and_report(
    model: gp.Model,
    config: ModelConfig,
    output_dir: Path,
    *,
    compute_iis: bool = True,
    warm_start: dict | None = None,
    primal_dual_start: dict | None = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    if warm_start is not None and primal_dual_start is not None:
        raise ValueError("Basis and primal/dual starts cannot be combined")
    configure_gurobi(model, config, output_dir / "gurobi.log")
    if warm_start is not None:
        from .basis_reuse import apply_basis_reuse

        apply_basis_reuse(model, warm_start)
    if primal_dual_start is not None:
        from .primal_dual_checkpoint import apply_primal_dual_crossover_start

        apply_primal_dual_crossover_start(model, primal_dual_start)
    before = model_statistics(model)
    telemetry = SolverTelemetry(output_dir / "solver_telemetry.jsonl")
    telemetry.write_event(
        "solver_start",
        model_statistics=before,
        process_id=os.getpid(),
    )
    termination: GracefulSolverTermination | None = None
    try:
        with GracefulSolverTermination(model, telemetry) as termination:
            model.optimize(telemetry)
        telemetry.write_event(
            "solver_end",
            status_code=int(model.Status),
            runtime_seconds=float(model.Runtime),
            work_units=float(model.Work),
        )
    finally:
        telemetry.close()
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
    crossover = int(model.Params.Crossover)
    solution_target = int(model.Params.SolutionTarget)
    nonbasic_primal_dual_contract = bool(
        not model.IsMIP
        and int(model.Params.Method) == 2
        and crossover == 0
        and solution_target == 1
    )
    barrier_status_code: int | None = None
    try:
        barrier_status_code = int(model.BarStatus)
    except (AttributeError, gp.GurobiError):
        # BarStatus was introduced in Gurobi 13.  Model.Status plus the
        # strict quality gate below remains the portable acceptance evidence.
        barrier_status_code = None
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
        "solver_telemetry_path": str(output_dir / "solver_telemetry.jsonl"),
        "termination_signal": (
            termination.received_signal if termination is not None else None
        ),
        "configuration": str(config.path),
        "solver_profile": (
            str(config.solver_path) if config.solver_path else None
        ),
        "solver_profile_id": config.raw.get("solver_profile", {}).get("id"),
        "formulation_profile": (
            str(config.formulation_path) if config.formulation_path else None
        ),
        "formulation_profile_id": config.raw.get("formulation_profile", {}).get(
            "id"
        ),
        "annual_emissions_accounting": config.raw["formulation"][
            "annual_emissions_accounting"
        ],
        "solver_parameters": {
            "method": int(model.Params.Method),
            "threads": int(model.Params.Threads),
            "available_logical_cpus": int(os.cpu_count() or 1),
            "crossover": int(model.Params.Crossover),
            "solution_target": solution_target,
            "numeric_focus": int(model.Params.NumericFocus),
            "scale_flag": int(model.Params.ScaleFlag),
            "feasibility_tolerance": float(model.Params.FeasibilityTol),
            "optimality_tolerance": float(model.Params.OptimalityTol),
            "barrier_convergence_tolerance": float(model.Params.BarConvTol),
            "pdhg_gpu": int(getattr(model.Params, "PDHGGPU", 0)),
            "pdhg_absolute_tolerance": float(
                getattr(model.Params, "PDHGAbsTol", 0.0)
            ),
            "pdhg_convergence_tolerance": float(
                getattr(model.Params, "PDHGConvTol", 0.0)
            ),
            "pdhg_relative_tolerance": float(
                getattr(model.Params, "PDHGRelTol", 0.0)
            ),
            "bar_homogeneous": int(model.Params.BarHomogeneous),
            "bar_correctors": int(model.Params.BarCorrectors),
            "bar_order": int(model.Params.BarOrder),
            "pre_sparsify": int(model.Params.PreSparsify),
            "aggregate": int(model.Params.Aggregate),
            "agg_fill": int(model.Params.AggFill),
            "crossover_basis": int(model.Params.CrossoverBasis),
            "pre_dual": int(model.Params.PreDual),
            "pre_passes": int(model.Params.PrePasses),
            "lp_warm_start": int(model.Params.LPWarmStart),
            "dual_reductions": int(model.Params.DualReductions),
            "inf_unbd_info": int(model.Params.InfUnbdInfo),
            "bar_iter_limit": int(model.Params.BarIterLimit),
            "time_limit_seconds": (
                None
                if config.raw["numerics"].get("time_limit_seconds") is None
                else float(model.Params.TimeLimit)
            ),
            "soft_mem_limit_gb": (
                None
                if config.raw["numerics"].get("soft_mem_limit_gb") is None
                else float(model.Params.SoftMemLimit)
            ),
        },
        "warm_start": warm_start,
        "primal_dual_start": primal_dual_start,
        "iteration_counts": {
            "simplex": float(model.IterCount),
            "barrier": int(model.BarIterCount),
            "pdhg": int(getattr(model, "PDHGIterCount", 0)),
        },
        "solution_contract": {
            "contract_version": "cispo_lp_solution_contract_v1",
            "mode": (
                "OPTIMAL_PRIMAL_DUAL_NONBASIC"
                if nonbasic_primal_dual_contract
                else "OPTIMAL_BASIC_OR_DEFAULT"
            ),
            "basis_required": not nonbasic_primal_dual_contract,
            "barrier_status_code": barrier_status_code,
            "strict_quality_pass": None,
            "acceptance_status": "PENDING_OR_NO_SOLUTION",
        },
    }
    if model.SolCount:
        kappa: float | None = None
        if not model.IsMIP:
            try:
                candidate = float(model.Kappa)
                if math.isfinite(candidate):
                    kappa = candidate
            except (AttributeError, gp.GurobiError):
                kappa = None
        solution_quality = {
            "maximum_constraint_violation": float(model.ConstrVio),
            "maximum_bound_violation": float(model.BoundVio),
            "maximum_dual_violation": float(model.DualVio),
            "maximum_complementarity_violation": float(model.ComplVio),
            "maximum_violation": float(model.MaxVio),
            "kappa": kappa,
            "kappa_exact_computed": False,
        }
        report["solution_quality"] = solution_quality
        variables_for_locations = (
            model.getVars()
            if int(model.NumVars) <= SOLUTION_LOCATION_LOOKUP_MAX_OBJECTS
            else None
        )
        constraints_for_locations = (
            model.getConstrs()
            if int(model.NumConstrs) <= SOLUTION_LOCATION_LOOKUP_MAX_OBJECTS
            else None
        )
        report["solution_quality_location_lookup"] = {
            "maximum_objects_per_collection": (
                SOLUTION_LOCATION_LOOKUP_MAX_OBJECTS
            ),
            "variable_names_resolved": variables_for_locations is not None,
            "constraint_names_resolved": constraints_for_locations is not None,
        }
        report["solution_quality_locations"] = {
            "maximum_bound_violation": _solution_quality_location(
                model,
                "BoundVioIndex",
                kind="variable",
                variables=variables_for_locations,
                constraints=constraints_for_locations,
            ),
            "maximum_constraint_violation": _solution_quality_location(
                model,
                "ConstrVioIndex",
                kind="constraint",
                variables=variables_for_locations,
                constraints=constraints_for_locations,
            ),
            "maximum_dual_violation": _solution_quality_location(
                model,
                "DualVioIndex",
                kind="dual",
                variables=variables_for_locations,
                constraints=constraints_for_locations,
            ),
            "maximum_complementarity_violation": (
                _solution_quality_location(
                    model,
                    "ComplVioIndex",
                    kind="variable",
                    variables=variables_for_locations,
                    constraints=constraints_for_locations,
                )
            ),
        }
        if nonbasic_primal_dual_contract:
            primal_limit = max(
                10.0 * float(model.Params.FeasibilityTol),
                1e-8,
            )
            dual_limit = max(
                10.0 * float(model.Params.OptimalityTol),
                1e-8,
            )
            strict_quality_pass = bool(
                float(model.ConstrVio) <= primal_limit
                and float(model.BoundVio) <= primal_limit
                and float(model.DualVio) <= dual_limit
                and status_name == "OPTIMAL"
            )
            barrier_primal_difference: float | None = None
            barrier_primal_difference_status = "COLLECTED"
            if variables_for_locations is None:
                barrier_primal_difference_status = "SKIPPED_MODEL_SIZE"
            else:
                try:
                    solution = np.asarray(
                        model.getAttr("X", variables_for_locations),
                        dtype=float,
                    )
                    barrier_solution = np.asarray(
                        model.getAttr("BarX", variables_for_locations),
                        dtype=float,
                    )
                    barrier_primal_difference = float(
                        np.max(np.abs(solution - barrier_solution))
                    ) if len(solution) else 0.0
                except (AttributeError, gp.GurobiError, ValueError):
                    barrier_primal_difference = None
                    barrier_primal_difference_status = "UNAVAILABLE"
            report["solution_contract"].update(
                strict_quality_pass=strict_quality_pass,
                acceptance_status=(
                    "PASS" if strict_quality_pass else "HARD_FAIL"
                ),
                maximum_primal_quality_limit=primal_limit,
                maximum_dual_quality_limit=dual_limit,
                maximum_x_barx_difference=barrier_primal_difference,
                maximum_x_barx_difference_status=(
                    barrier_primal_difference_status
                ),
                dual_attribute="BarPi",
            )
        else:
            report["solution_contract"].update(
                strict_quality_pass=(status_name == "OPTIMAL"),
                acceptance_status=(
                    "PASS" if status_name == "OPTIMAL" else "HARD_FAIL"
                ),
                dual_attribute="Pi",
            )
    if model.Status == GRB.INFEASIBLE and compute_iis:
        model.computeIIS()
        model.write(str(output_dir / "iis.ilp"))
        report["iis_path"] = str(output_dir / "iis.ilp")
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report
