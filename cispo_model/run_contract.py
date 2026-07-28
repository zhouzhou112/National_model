"""Production-safe output-root and run-identity contracts."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from .config import ROOT, ModelConfig
from .io_contract import (
    RUNTIME_MANAGED_FILES,
    sha256_file,
    validate_input_manifest,
    write_run_provenance,
)


RUN_IDENTITY_SCHEMA_VERSION = "cispo_run_identity_v1"
RUN_CLAIM_FILENAME = "run_claim.json"
RUN_IDENTITY_FILENAME = "run_identity.json"
SEQUENCE_ACTIVE_CLAIM_FILENAME = "sequence_active_claim.json"
SEQUENCE_CLAIM_HISTORY_DIRNAME = "sequence_claim_history"
_PRECREATED_RUNTIME_FILES = (
    RUNTIME_MANAGED_FILES.difference({"result_manifest.json"})
    | {"sequence_attempt.json"}
)


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_identity(path: Path | None) -> dict[str, Any]:
    return {
        "path": str(path) if path else None,
        "sha256": sha256_file(path) if path else None,
    }


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNAVAILABLE"


def code_bundle_identity() -> dict[str, Any]:
    """Hash executable model/runner source independently of docs-only changes."""
    paths = sorted((ROOT / "cispo_model").rglob("*.py"))
    paths.extend(
        path
        for path in (
            ROOT / "scripts" / "run_cispo_2030_full_year.py",
            ROOT / "scripts" / "run_cispo_planning_sequence.py",
        )
        if path.is_file()
    )
    rows = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(set(paths))
    ]
    return {
        "git_commit": _git_commit(),
        "source_bundle_sha256": _canonical_json_sha256(rows),
        "source_file_count": len(rows),
    }


def runtime_data_roots(data_root: str | Path) -> dict[str, str | None]:
    """Return the exact data-root strings recorded by run provenance."""
    return {
        "CISPO_DATA_ROOT": str(Path(data_root).resolve()),
        "CISPO_CF_ROOT": os.environ.get("CISPO_CF_ROOT"),
        "CISPO_HYDRO_ROOT": os.environ.get("CISPO_HYDRO_ROOT"),
        "CISPO_RAW_GRFR_ROOT": os.environ.get("CISPO_RAW_GRFR_ROOT"),
        "CISPO_WAVE_ROOT": os.environ.get("CISPO_WAVE_ROOT"),
    }


def configuration_identity(
    config: ModelConfig,
    *,
    data_root: str | Path,
) -> dict[str, Any]:
    """Identify scientific/configuration inputs without coupling to docs-only Git."""
    return {
        "schema_version": RUN_IDENTITY_SCHEMA_VERSION,
        "configuration": _source_identity(config.path),
        "scenario_configuration": _source_identity(config.scenario_path),
        "solver_configuration": _source_identity(config.solver_path),
        "formulation_configuration": _source_identity(config.formulation_path),
        "resolved_configuration_sha256": _canonical_json_sha256(config.raw),
        "scenario_id": str(config.raw["scenario"]["id"]),
        "planning_years": [int(year) for year in config.planning_years],
        "data_roots": runtime_data_roots(data_root),
        "code": code_bundle_identity(),
    }


def capture_input_identity(
    config: ModelConfig,
    *,
    data_root: str | Path,
    planning_state: Any,
) -> dict[str, Any]:
    """Build the normal input manifest once and retain its deterministic hash."""
    with tempfile.TemporaryDirectory(prefix="cispo_sequence_identity_") as temporary:
        _, _, manifest_path = write_run_provenance(
            temporary,
            config,
            data_root=data_root,
            planning_state=planning_state,
        )
        row_count = max(
            0,
            sum(1 for _ in manifest_path.open(encoding="utf-8-sig")) - 1,
        )
        return {
            "input_manifest_sha256": sha256_file(manifest_path),
            "input_manifest_row_count": row_count,
            "integrity_scope": (
                "file_sha256 plus Zarr metadata SHA256; a release-level Zarr "
                "chunk-payload manifest remains required before 8760h production"
            ),
        }


def sequence_identity(
    config: ModelConfig,
    *,
    data_root: str | Path,
    input_identity: dict[str, Any],
    start_year: int,
    end_year: int,
    diagnostic_hours: int | None,
) -> dict[str, Any]:
    """Lock the complete execution scope of a sequential planning chain."""
    identity = configuration_identity(config, data_root=data_root)
    identity["sequence_scope"] = {
        "start_year": int(start_year),
        "end_year": int(end_year),
        "diagnostic_hours": (
            int(diagnostic_hours) if diagnostic_hours is not None else None
        ),
        "result_use": (
            "TEST_ONLY_TRUNCATED_HORIZON"
            if diagnostic_hours is not None
            else "SCIENTIFIC_PRODUCTION"
        ),
    }
    identity["input_identity"] = input_identity
    return identity


def output_matches_configuration(
    output_dir: str | Path,
    config: ModelConfig,
    *,
    data_root: str | Path,
) -> bool:
    """Check an accepted output against the current resolved run identity."""
    output_dir = Path(output_dir)
    try:
        recorded_identity = json.loads(
            (output_dir / RUN_IDENTITY_FILENAME).read_text(encoding="utf-8")
        )
        snapshot = json.loads(
            (output_dir / "model_config_snapshot.json").read_text(encoding="utf-8")
        )
        environment = json.loads(
            (output_dir / "run_environment.json").read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False
    expected = configuration_identity(config, data_root=data_root)
    if recorded_identity != expected:
        return False
    source_pairs = (
        ("configuration", "source_path", "source_sha256"),
        ("scenario_configuration", "scenario_source_path", "scenario_source_sha256"),
        ("solver_configuration", "solver_source_path", "solver_source_sha256"),
        (
            "formulation_configuration",
            "formulation_source_path",
            "formulation_source_sha256",
        ),
    )
    for identity_key, path_key, sha_key in source_pairs:
        source = expected[identity_key]
        if snapshot.get(path_key) != source["path"]:
            return False
        if snapshot.get(sha_key) != source["sha256"]:
            return False
    if snapshot.get("resolved_configuration") != config.raw:
        return False
    if environment.get("data_roots") != expected["data_roots"]:
        return False
    input_valid, _ = validate_input_manifest(output_dir / "input_manifest.csv")
    return input_valid


def claim_output_directory(output_dir: str | Path) -> Path:
    """Atomically claim a new output root while permitting wrapper-created logs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(
        item.name
        for item in output_dir.iterdir()
        if item.name not in _PRECREATED_RUNTIME_FILES
    )
    if unexpected:
        raise RuntimeError(
            f"Refusing non-empty output directory {output_dir}; "
            f"unexpected existing entries: {', '.join(unexpected[:10])}"
        )
    claim_path = output_dir / RUN_CLAIM_FILENAME
    payload = {
        "schema_version": RUN_IDENTITY_SCHEMA_VERSION,
        "claimed_at": datetime.now().astimezone().isoformat(),
        "process_id": os.getpid(),
        "output_dir": str(output_dir.resolve()),
    }
    try:
        with claim_path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except FileExistsError as error:
        raise RuntimeError(f"Output directory is already claimed: {output_dir}") from error
    return claim_path


def _claim_process_is_active(payload: dict[str, Any]) -> bool:
    if payload.get("host") != platform.node():
        return False
    try:
        process = psutil.Process(int(payload["process_id"]))
        recorded_start = float(payload["process_create_time"])
    except (KeyError, TypeError, ValueError, psutil.Error):
        return False
    return abs(process.create_time() - recorded_start) < 1.0


def claim_sequence_directory(
    output_root: str | Path,
    *,
    recover_stale: bool = False,
) -> str:
    """Atomically claim a sequence root before any attempt/report log is written."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    claim_path = output_root / SEQUENCE_ACTIVE_CLAIM_FILENAME
    token = str(uuid.uuid4())
    payload = {
        "schema_version": RUN_IDENTITY_SCHEMA_VERSION,
        "claim_token": token,
        "claimed_at": datetime.now().astimezone().isoformat(),
        "host": platform.node(),
        "process_id": os.getpid(),
        "process_create_time": psutil.Process(os.getpid()).create_time(),
        "output_root": str(output_root.resolve()),
    }

    def create_claim() -> None:
        with claim_path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")

    try:
        create_claim()
    except FileExistsError as error:
        if not recover_stale:
            raise RuntimeError(
                f"Sequence root is already claimed: {output_root}"
            ) from error
        try:
            recorded = json.loads(claim_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as read_error:
            raise RuntimeError(
                f"Cannot verify existing sequence claim: {claim_path}"
            ) from read_error
        if _claim_process_is_active(recorded):
            raise RuntimeError(
                f"Sequence claim is still active: {claim_path}"
            ) from error
        history = output_root / SEQUENCE_CLAIM_HISTORY_DIRNAME
        history.mkdir(exist_ok=True)
        stale_token = str(recorded.get("claim_token", "unknown"))
        claim_path.replace(history / f"stale_{stale_token}.json")
        try:
            create_claim()
        except FileExistsError as race_error:
            raise RuntimeError(
                f"Another process reclaimed the sequence root: {output_root}"
            ) from race_error
    return token


def release_sequence_directory(output_root: str | Path, claim_token: str) -> bool:
    """Archive this process's sequence claim; never remove another process's claim."""
    output_root = Path(output_root)
    claim_path = output_root / SEQUENCE_ACTIVE_CLAIM_FILENAME
    try:
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False
    if payload.get("claim_token") != claim_token:
        return False
    history = output_root / SEQUENCE_CLAIM_HISTORY_DIRNAME
    history.mkdir(exist_ok=True)
    claim_path.replace(history / f"released_{claim_token}.json")
    return True


def solver_result_is_accepted(
    solve_report: dict[str, Any],
    solution_qc: dict[str, Any] | None,
    *,
    result_manifest_valid: bool,
) -> bool:
    """Return the exact success condition expected by wrappers and Slurm."""
    return bool(
        solve_report.get("status") == "OPTIMAL"
        and solution_qc is not None
        and solution_qc.get("status") == "PASS"
        and result_manifest_valid
    )
