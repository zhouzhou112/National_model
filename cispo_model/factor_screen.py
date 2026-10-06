"""Explicit TEST_ONLY five-iteration experiment; no solution/QC/state export."""
from __future__ import annotations

import hashlib
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROFILE_ID = "barrier_factor_screen_8760_v1_threads48"
RESULT_USE = "TEST_ONLY_FACTOR_SCREEN"


def mps_section_sha256(path):
    """Stream archive sections, splitting new-VRE bounds from all other bounds."""
    parts = {}
    section = None
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rb') as stream:
        for line in stream:
            if not line.strip() or line.startswith(b'*'):
                continue
            if line[:1] not in (b' ', b'\t'):
                section = line.split()[0].decode('ascii')
            key = section
            if section == 'BOUNDS' and line[:1] in (b' ', b'\t'):
                key = 'BOUNDS_VRE_NEW' if line.split()[2].startswith(b'vre_new_gw[') else 'BOUNDS_OTHER'
            parts.setdefault(key, hashlib.sha256()).update(line)
    return {key: value.hexdigest() for key, value in parts.items()}


def validate_factor_screen_contract(config, args):
    """Fail closed on altered parameters or any scientific-result request."""
    reference = json.loads((Path(__file__).resolve().parents[1] /
        "config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json").read_text())
    expected = dict(reference["numerics"], bar_iter_limit=5)
    for key, value in expected.items():
        if config.raw["numerics"].get(key) != value:
            raise ValueError(f"Factor-screen parameter drift: {key}")
    if config.raw["solver_profile"].get("direct_nonbasic_scientific_acceptance"):
        raise ValueError("Factor screen forbids scientific acceptance")
    forbidden = ("export_diagnostic_state", "allow_nonbasic_planning_state",
        "export_scientific_solver_artifacts", "export_barrier_checkpoint",
        "primal_dual_checkpoint_in", "recover_stage_a_from", "mga_spec",
        "basis_in", "export_warm_start_basis", "state_in", "formulation_config",
        "authorize_thermal_stage_a_1e4", "archive_presolved_model")
    if any(getattr(args, name, None) for name in forbidden):
        raise ValueError("Factor screen forbids state, recovery, scientific export and alternate formulation")
    if config.planning_year != 2030 or config.boundary_year != 2025:
        raise ValueError("Factor screen requires 2030 with the common 2025 boundary")
    if config.raw["scenario"]["id"] != "case3_thermal_ev_v5":
        raise ValueError("Factor screen requires case3_thermal_ev_v5")
    if getattr(args, "diagnostic_start_hour", 0) != 0:
        raise ValueError("Factor screen starts at model hour zero")


def apply_vre_screen(artifacts, sites, source, output_dir):
    """Join exact stable identities; change only positive vre_new upper bounds."""
    model = artifacts.model
    model.update()
    new = artifacts.variables["vre_new"]
    ub = np.asarray(new.UB, dtype=float).copy()
    keys = ["grid_uid", "technology"]
    if len(ub) != len(sites) or sites.duplicated(keys).any():
        raise ValueError("Invalid model site identities/variable dimensions")
    table = pd.read_csv(source)
    if table.duplicated(keys).any() or table[keys].isna().any().any():
        raise ValueError("Duplicate or missing screen identities")
    aligned = sites[keys].merge(table[keys + ["rc_ratio"]], on=keys,
        how="left", validate="one_to_one", sort=False)
    if len(aligned) != len(table) or not np.isfinite(aligned.rc_ratio).all():
        raise ValueError("Screen identity/finite-price mismatch; positional joins forbidden")
    if not np.isfinite(ub).all() or (ub < 0).any():
        raise ValueError("Nonfinite or negative VRE headroom")
    excluded = (aligned.rc_ratio.to_numpy() >= 0.2) & (ub > 0)
    new.UB = np.where(excluded, 0.0, ub)
    model.update()
    aligned["original_new_ub_gw"] = ub
    aligned["screened_out"] = excluded
    aligned.to_csv(Path(output_dir) / "candidate_selection.csv", index=False)
    return dict(source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        source=str(Path(source).resolve()), margin=0.2, alignment="grid_uid × technology; exact one-to-one",
        sites=len(ub), expandable_sites=int((ub > 0).sum()),
        retained_expandable=int(((ub > 0) & ~excluded).sum()),
        fixed_columns=int(excluded.sum()), fixed_headroom_gw=float(ub[excluded].sum()),
        original_headroom_gw=float(ub.sum()))


def solve_factor_screen(model, config, output_dir):
    """Optimize with telemetry, never evaluate or export a primal/dual solution."""
    from .diagnostics import SolverTelemetry, GracefulSolverTermination
    telemetry = SolverTelemetry(Path(output_dir) / "solver_telemetry.jsonl")
    try:
        with GracefulSolverTermination(model, telemetry):
            telemetry.write_event("solver_start", result_use=RESULT_USE)
            try:
                model.optimize(telemetry)
            finally:
                telemetry.write_event("solver_end", status_code=int(model.Status),
                    runtime_seconds=float(model.Runtime), work_units=float(model.Work))
    finally:
        telemetry.close()
    report = dict(result_use=RESULT_USE, scientific_acceptance_mode="NONE",
        publication_accepted=False, production_state_written=False, qc="NOT_EVALUATED",
        status_code=int(model.Status), barrier_iterations=int(model.BarIterCount),
        runtime_seconds=float(model.Runtime), work_units=float(model.Work))
    (Path(output_dir) / "solve_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
