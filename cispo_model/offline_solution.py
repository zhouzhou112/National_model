"""Read saved LP values without optimize, presolve, PStart or DStart.

Only the original, index-identical LP may be used. This adapter evaluates
linear expressions directly; it cannot repair an infeasible solution.
"""
from __future__ import annotations

import json
import csv
import gzip
import math
from pathlib import Path
from types import SimpleNamespace

import gurobipy as gp
import numpy as np

from .planning_state import sha256_file
from .solution_preservation import CHUNK_SIZE, model_order
from .annual_capacity_link_scaling import (
    active_row_scaling_registry,
    validate_row_scaling_registry,
)


def linear_value(expression, primal):
    if isinstance(expression, gp.Var):
        return float(primal[expression.index])
    if isinstance(expression, gp.LinExpr):
        # Constant memory; no dense coefficient or model matrix copy.
        return float(expression.getConstant() + sum(
            expression.getCoeff(i) * primal[expression.getVar(i).index]
            for i in range(expression.size())))
    if isinstance(expression, gp.MLinExpr):
        result = np.empty(expression.shape, dtype=float)
        for index in np.ndindex(expression.shape):
            result[index] = linear_value(expression[index].item(), primal)
        return result
    if isinstance(expression, gp.MVar):
        flat = expression.reshape(-1)
        result = np.empty(flat.size, dtype=float)
        for start in range(0, flat.size, CHUNK_SIZE):
            indices = [v.index for v in flat[start:start + CHUNK_SIZE].tolist()]
            result[start:start + len(indices)] = primal[indices]
        return result.reshape(expression.shape)
    return np.asarray(expression)


class SavedValue:
    def __init__(self, expression, primal):
        self.expression, self.primal = expression, primal

    @property
    def X(self):
        return linear_value(self.expression, self.primal)

    def getValue(self):
        return self.X

    def __getitem__(self, key):
        return SavedValue(self.expression[key], self.primal)


class SavedDual:
    def __init__(self, constraint, dual):
        self.constraint, self.dual = constraint, dual

    @property
    def BarPi(self):
        if self.dual is None:
            raise AttributeError("Saved dual unavailable")
        if isinstance(self.constraint, gp.Constr):
            return float(self.dual[self.constraint.index])
        handles = np.asarray(self.constraint.tolist(), dtype=object)
        return np.asarray([self.dual[c.index] for c in handles.flat]).reshape(handles.shape)

    Pi = BarPi


def offline_artifacts(artifacts, primal, dual, *, objective=None):
    """Provide the existing exporters with read-only values, never a solver start."""
    if len(primal) != artifacts.model.NumVars or not np.isfinite(primal).all():
        raise ValueError("Invalid saved primal vector")
    if dual is not None and (len(dual) != artifacts.model.NumConstrs or not np.isfinite(dual).all()):
        raise ValueError("Invalid saved dual vector")

    def wrap(value):
        if isinstance(value, (gp.Var, gp.MVar, gp.LinExpr, gp.MLinExpr)):
            return SavedValue(value, primal)
        if isinstance(value, (gp.Constr, gp.MConstr)):
            return SavedDual(value, dual)
        if isinstance(value, dict):
            return {key: wrap(item) for key, item in value.items()}
        if isinstance(value, list):
            return [wrap(item) for item in value]
        if isinstance(value, tuple):
            return tuple(wrap(item) for item in value)
        return value

    computed = (
        float(objective)
        if objective is not None
        else linear_value(artifacts.model.getObjective(), primal)
    )
    model = SimpleNamespace(ObjVal=computed, Params=SimpleNamespace(Method=2, Crossover=0, SolutionTarget=1))
    return SimpleNamespace(model=model, variables=wrap(artifacts.variables),
                           cost_components=wrap(artifacts.cost_components), index=wrap(artifacts.index))


def audit_saved_primal(
    model,
    primal,
    *,
    tolerance=1e-5,
    violations_path=None,
    row_scaling_registry=None,
):
    if violations_path is not None:
        with gzip.open(violations_path, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["kind", "index", "name", "sense", "value", "limit", "violation"])
            return _audit_saved_primal(
                model,
                primal,
                tolerance,
                writer,
                row_scaling_registry=row_scaling_registry,
            )
    return _audit_saved_primal(
        model,
        primal,
        tolerance,
        None,
        row_scaling_registry=row_scaling_registry,
    )


def _audit_saved_primal(
    model,
    primal,
    tolerance,
    writer,
    *,
    row_scaling_registry=None,
):
    """Evaluate every original LP row and bound, without changing the saved x.

One CSR copy is required (about 5.7--7.7 GiB for historical 8760h), while
residuals are evaluated in bounded row blocks. No solver routine is called.
"""
    if np.shape(primal) != (int(model.NumVars),) or not np.isfinite(primal).all():
        raise ValueError("Raw LP audit requires a complete finite primal vector")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Raw LP audit requires a finite nonnegative tolerance")
    matrix = model.getA()
    constraints = model.getConstrs()
    scaling_families = {}
    if row_scaling_registry is not None:
        validated_registry = validate_row_scaling_registry(
            row_scaling_registry,
            model=model,
            allow_none=False,
        )
        scaling_families = validated_registry["families"]
    maximum, location, violated = 0.0, None, 0
    for start in range(0, len(constraints), CHUNK_SIZE):
        block = constraints[start:start + CHUNK_SIZE]
        rhs = np.asarray(model.getAttr("RHS", block))
        senses = np.asarray(model.getAttr("Sense", block))
        residual = matrix[start:start + len(block)] @ primal - rhs
        physical_multiplier = np.ones(len(block), dtype=float)
        if scaling_families:
            names = [constraint.ConstrName for constraint in block]
            for family in scaling_families.values():
                prefix = str(family["constraint_prefix"])
                exponent = int(family["exponent"])
                matched = np.fromiter(
                    (name.startswith(prefix) for name in names),
                    dtype=bool,
                    count=len(names),
                )
                physical_multiplier[matched] = math.ldexp(1.0, exponent)
        residual = residual * physical_multiplier
        physical_rhs = rhs * physical_multiplier
        violation = np.where(senses == "=", np.abs(residual),
                             np.where(senses == "<", np.maximum(residual, 0), np.maximum(-residual, 0)))
        violated += int(np.count_nonzero(violation > tolerance))
        if writer is not None:
            for offset in np.flatnonzero(violation > tolerance):
                writer.writerow(["constraint", start + int(offset), block[offset].ConstrName,
                                 senses[offset], float(residual[offset] + physical_rhs[offset]),
                                 float(physical_rhs[offset]), float(violation[offset])])
        if len(violation) and float(violation.max()) > maximum:
            offset = int(np.argmax(violation))
            maximum, location = float(violation[offset]), {
                "index": start + offset, "name": block[offset].ConstrName,
                "sense": str(senses[offset]), "rhs": float(physical_rhs[offset]),
                "lhs_minus_rhs": float(residual[offset])}
    del constraints, matrix
    variables = model.getVars()
    bound_maximum, bound_location, bound_violated = 0.0, None, 0
    for start in range(0, len(variables), CHUNK_SIZE):
        block = variables[start:start + CHUNK_SIZE]
        values = primal[start:start + len(block)]
        lower = np.asarray(model.getAttr("LB", block))
        upper = np.asarray(model.getAttr("UB", block))
        violation = np.maximum(np.maximum(lower - values, values - upper), 0)
        bound_violated += int(np.count_nonzero(violation > tolerance))
        if writer is not None:
            for offset in np.flatnonzero(violation > tolerance):
                is_lower = lower[offset] - values[offset] >= values[offset] - upper[offset]
                writer.writerow(["bound", start + int(offset), block[offset].VarName,
                                 ">=" if is_lower else "<=", float(values[offset]),
                                 float(lower[offset] if is_lower else upper[offset]), float(violation[offset])])
        if len(violation) and float(violation.max()) > bound_maximum:
            offset = int(np.argmax(violation))
            bound_maximum = float(violation[offset])
            bound_location = {"index": start + offset, "name": block[offset].VarName,
                              "value": float(values[offset]), "lower": float(lower[offset]),
                              "upper": float(upper[offset])}
    return {"status": "FAIL" if violated or bound_violated else "PASS", "tolerance": tolerance,
            "maximum_constraint_violation": maximum, "constraint_location": location,
            "violated_constraint_count": violated, "maximum_bound_violation": bound_maximum,
            "bound_location": bound_location, "violated_bound_count": bound_violated,
            "constraints_checked": int(model.NumConstrs), "variables_checked": int(model.NumVars),
            "annual_capacity_link_row_scaling_applied": any(
                int(family["exponent"]) > 0
                for family in scaling_families.values()
            ),
            "optimize_called": False, "presolve_called": False}


def read_snapshot(
    model,
    source_root,
    *,
    expected_row_scaling_registry=None,
):
    """Validate hashes, original LP dimensions/fingerprint/order; load read-only."""
    root = Path(source_root)
    metadata = json.loads((root / "snapshot_manifest.json").read_text(encoding="utf-8"))
    stored_registry = validate_row_scaling_registry(
        metadata.get("annual_capacity_link_row_scaling"), model=model
    )
    expected_registry = validate_row_scaling_registry(
        expected_row_scaling_registry
    )
    if active_row_scaling_registry(stored_registry) != (
        active_row_scaling_registry(expected_registry)
    ):
        raise ValueError("Snapshot annual capacity-link row scaling mismatch")
    model.update()
    for name, actual in (("variables", model.NumVars), ("constraints", model.NumConstrs),
                         ("nonzeros", model.NumNZs), ("gurobi_fingerprint", model.Fingerprint)):
        if int(metadata[name]) != int(actual):
            raise ValueError(f"Snapshot LP mismatch: {name}")
    for kind in ("variable", "constraint"):
        if model_order(model, kind) != metadata[f"{kind}_order_digest"]:
            raise ValueError(f"Snapshot {kind} order mismatch")
    values = []
    for role in ("primal", "dual"):
        attribute = metadata.get(f"{role}_attribute")
        if not attribute:
            if role == "dual":
                values.append(None)
                continue
            raise ValueError("Snapshot primal unavailable")
        entry = metadata["attributes"][attribute]
        path = (root / entry["path"]).resolve()
        path.relative_to(root.resolve())
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"Snapshot {role} checksum mismatch")
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        if array.shape != (int(entry["entries"]),) or array.dtype != np.dtype("<f8"):
            raise ValueError(f"Snapshot {role} array metadata mismatch")
        if any(
            not np.isfinite(array[start : start + CHUNK_SIZE]).all()
            for start in range(0, len(array), CHUNK_SIZE)
        ):
            raise ValueError(f"Snapshot {role} vector is not finite")
        values.append(array)
    return tuple(values)


def read_legacy_checkpoint(
    model,
    source_output,
    *,
    allow_fingerprint_mismatch=False,
    order_digests=None,
    expected_row_scaling_registry=None,
):
    """Recover original-order vectors; scientific acceptance is never inferred.

    Fingerprint differences require explicit author acknowledgement. Dimensions,
    ordered names/senses, vector hashes and finite values remain mandatory.
    order_digests may reuse archive_model's digests for this SAME unmodified model
    to avoid traversing tens of millions of names twice.
    """
    root = Path(source_output) / "barrier_checkpoint"
    metadata = json.loads((root / "barrier_checkpoint_manifest.json").read_text(encoding="utf-8"))
    stored_registry = validate_row_scaling_registry(
        metadata.get("annual_capacity_link_row_scaling"), model=model
    )
    expected_registry = validate_row_scaling_registry(
        expected_row_scaling_registry
    )
    if active_row_scaling_registry(stored_registry) != (
        active_row_scaling_registry(expected_registry)
    ):
        raise ValueError("Checkpoint annual capacity-link row scaling mismatch")
    ordering = metadata["lp_ordering"]
    model.update()
    for name, actual in (("variables", model.NumVars), ("constraints", model.NumConstrs),
                         ("nonzeros", model.NumNZs), ("gurobi_fingerprint", model.Fingerprint)):
        if int(ordering[name]) != int(actual):
            if name == "gurobi_fingerprint" and allow_fingerprint_mismatch:
                continue
            raise ValueError(f"Legacy checkpoint LP mismatch: {name}")
    for kind in ("variable", "constraint"):
        actual = (order_digests or {}).get(f"{kind}_order_digest")
        if actual is None:
            actual = model_order(model, kind)
        if any(actual[key] != ordering[f"{kind}_order_digest"][key] for key in ("entries", "sha256")):
            raise ValueError(f"Legacy checkpoint {kind} order mismatch")
    arrays = []
    for role, expected in (("primal", model.NumVars), ("dual", model.NumConstrs)):
        row = metadata["vectors"][role]
        path = (root / row["path"]).resolve()
        path.relative_to(root.resolve())
        if path.stat().st_size != row["bytes"] or sha256_file(path) != row["sha256"]:
            raise ValueError(f"Legacy checkpoint {role} checksum mismatch")
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        if array.shape != (expected,) or array.dtype != np.dtype("<f8"):
            raise ValueError(f"Legacy checkpoint {role} array mismatch")
        if not np.isfinite(array).all():
            raise ValueError(f"Legacy checkpoint {role} vector is not finite")
        arrays.append(array)
    return tuple(arrays)


def verify_recovery_inputs(source, target, *, allow_compatible_implementation=False, check_lp=True):
    """Validate input identity before attaching meanings to the saved numbers.

Path migration is deliberately not inferred; it requires a separate audited
mapping. A changed implementation needs explicit acknowledgement AND exact LP
checks. Neither option bypasses model, data or time-window identity.
"""
    from .io_contract import validate_input_manifest, input_manifest_scientific_resume_identity
    source, target = Path(source), Path(target)
    manifests = []
    for root in (source, target):
        ok, failures = validate_input_manifest(root / "input_manifest.csv")
        if not ok:
            raise ValueError(f"Recovery input files invalid in {root}: {failures[:5]}")
        manifests.append(input_manifest_scientific_resume_identity(root / "input_manifest.csv"))
    if any(manifests[0][key] != manifests[1][key] for key in ("sha256", "row_count")):
        raise ValueError("Recovery source/target scientific inputs differ")
    identities = [json.loads((root / "run_identity.json").read_text(encoding="utf-8")) for root in (source, target)]
    keys = ["baseline_contract", "analysis_case", "scientific_case", "data_roots"]
    if check_lp:
        keys.append("lp_model")
    if not allow_compatible_implementation:
        keys.append("implementation_bundle")
    for key in keys:
        if identities[0].get(key) != identities[1].get(key):
            raise ValueError(f"Recovery identity mismatch: {key}")
    scopes = [json.loads((root / "run_scope.json").read_text(encoding="utf-8")) for root in (source, target)]
    for key in ("planning_year", "optimization_hours", "optimization_start_hour", "result_use"):
        if scopes[0].get(key) != scopes[1].get(key):
            raise ValueError(f"Recovery scope mismatch: {key}")
    environments = [json.loads((root / "run_environment.json").read_text(encoding="utf-8")) for root in (source, target)]
    if environments[0].get("packages", {}).get("gurobipy") != environments[1].get("packages", {}).get("gurobipy"):
        raise ValueError("Recovery source/target Gurobi versions differ")
    return {"source_output": str(source.resolve()), "identity_validated": True,
            "compatible_implementation_explicitly_allowed": allow_compatible_implementation,
            "source_implementation": identities[0].get("implementation_bundle"),
            "target_implementation": identities[1].get("implementation_bundle"),
            "optimize_called": False, "presolve_called": False}
