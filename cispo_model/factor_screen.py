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
PRODUCTION_PROFILE_ID = "barrier_stagea_screened_agg0_v1_threads48"
LATE_ENTRY_40_PROFILE_ID = "barrier_stagea_screened_agg0_2050_v1_threads40"
CASE3_2050_40_PROFILE_ID = "barrier_stagea_screened_agg0_case3_2050_v1_threads40"
PRODUCTION_PROFILE_IDS = frozenset({PRODUCTION_PROFILE_ID,
    "barrier_stagea_screened_agg0_2040_v1_threads48",
    "barrier_stagea_screened_agg0_2050_v1_threads48",
    LATE_ENTRY_40_PROFILE_ID, CASE3_2050_40_PROFILE_ID})


def validate_production_screen_contract(config, args):
    """Author 2026-10-14 authorization; fail closed outside reviewed scope."""
    raw = config.raw
    profile_id = raw.get('solver_profile', {}).get('id')
    for year in (2040, 2050):
        if profile_id == f'barrier_stagea_screened_agg0_{year}_v1_threads48':
            if config.planning_year != year or raw['scenario']['id'] != 'case3_thermal_ev_v5':
                raise ValueError('Continuation screening profile year/scenario mismatch')
    reference = json.loads((Path(__file__).resolve().parents[1] /
        'config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json').read_text())
    expected = dict(reference['numerics'], aggregate=0)
    if profile_id == LATE_ENTRY_40_PROFILE_ID:
        # Author 2026-10-20: only the C2050 OOM retry may use this profile.
        if (config.planning_year != 2050
                or raw['scenario']['id'] != 'case3_thermal_ev_v5'
                or not getattr(args, 'late_entry_base_state', False)):
            raise ValueError('40-thread profile requires C2050 late-entry year/scenario')
        expected['threads'] = 40
    if profile_id == CASE3_2050_40_PROFILE_ID:
        # Author 2026-10-26: framework A, inheriting the accepted case3 2040 state.
        if (config.planning_year != 2050
                or raw['scenario']['id'] != 'case3_thermal_ev_v5'
                or getattr(args, 'late_entry_base_state', False)
                or not getattr(args, 'state_in', None)):
            raise ValueError('40-thread case3 2050 requires same-scenario continuation state')
        expected['threads'] = 40
    diagnostic = getattr(args, 'diagnostic_hours', None) is not None
    if diagnostic:
        threads = raw['numerics']['threads']
        if not isinstance(threads, int) or not 1 <= threads <= 48:
            raise ValueError('Screen diagnostic threads must be in [1, 48]')
        expected['threads'] = threads
    for key, value in expected.items():
        if raw['numerics'].get(key) != value:
            raise ValueError(f'Production screen parameter drift: {key}')
    payload = json.loads(Path(config.solver_path).read_text(encoding='utf-8'))
    if payload.get('numerics') != expected:
        raise ValueError('Production screen profile must change only Aggregate (diagnostic threads excepted)')
    for key in ('minimum_gurobi_major_version', 'direct_nonbasic_scientific_acceptance',
                'stage_b_required', 'stage_a_acceptance'):
        if payload.get(key) != reference[key]:
            raise ValueError(f'Production screen acceptance drift: {key}')
    if payload.get('result_use') != 'SCIENTIFIC_PRODUCTION':
        raise ValueError('Production screen requires SCIENTIFIC_PRODUCTION profile')
    if raw['scenario']['id'] not in {'case3_thermal_ev_v5', 'case3_thermal_ev_v5_nocredit'}:
        raise ValueError('Production screen scenario is outside the author whitelist')
    if raw['formulation'].get('annual_capacity_link_row_scaling', 'physical_v1') != 'physical_v1':
        raise ValueError('Production screen requires physical_v1')
    forbidden = ('mga_spec', 'mga_baseline', 'primal_dual_checkpoint_in',
                 'recover_stage_a_from', 'basis_in', 'export_warm_start_basis',
                 'formulation_config', 'archive_presolved_model')
    if any(getattr(args, name, None) for name in forbidden):
        raise ValueError('Production screen forbids MGA, Stage B/resume and alternate formulation')
    if not getattr(args, 'archive_original_model', False) and not getattr(args, 'preflight_only', False):
        raise ValueError('Production screen requires original model preservation')
    screen = raw.get('candidate_screen', {})
    if screen.get('enabled') is not True or not getattr(args, 'vre_screen_csv', None):
        raise ValueError('Production screen requires enabled candidate_screen and --vre-screen-csv')
    margin = screen.get('margin')
    if isinstance(margin, bool) or not isinstance(margin, (float, int)) or not np.isfinite(margin) or margin < 0:
        raise ValueError('Production screen margin must be finite and nonnegative')
    import re
    for key in ('source_dual_sha256', 'source_csv_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', str(screen.get(key, ''))):
            raise ValueError(f'Production screen requires {key}')
    if not screen.get('source_release'):
        raise ValueError('Production screen requires source_release')
    if hashlib.sha256(Path(args.vre_screen_csv).read_bytes()).hexdigest() != screen['source_csv_sha256']:
        raise ValueError('Production screen source CSV SHA mismatch')


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


def apply_vre_screen(artifacts, sites, source, output_dir, *, margin=0.2):
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
    if not np.isfinite(margin) or margin < 0:
        raise ValueError('Screen margin must be finite and nonnegative')
    excluded = (aligned.rc_ratio.to_numpy() >= margin) & (ub > 0)
    new.UB = np.where(excluded, 0.0, ub)
    model.update()
    aligned["original_new_ub_gw"] = ub
    aligned["screened_out"] = excluded
    aligned.to_csv(Path(output_dir) / "candidate_selection.csv", index=False)
    return dict(source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        source=str(Path(source).resolve()), margin=margin, alignment="grid_uid × technology; exact one-to-one",
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
