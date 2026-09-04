"""Build or solve the 2030 CISPO monolithic model at a controlled horizon."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import ROOT, load_model_config
from cispo_model.data import DATA_ROOT, load_model_data
from cispo_model.flexible_load_numerics import (
    assess_flexible_load_solver_compatibility,
    prebuild_flexible_load_solver_compatibility,
)
from cispo_model.io_contract import validate_result_manifest, write_run_provenance
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.result_dashboard import build_result_dashboard
from cispo_model.run_contract import (
    RUN_IDENTITY_FILENAME,
    claim_output_directory,
    configuration_identity,
    qc_hard_checks_are_strictly_true,
    solver_result_is_accepted,
)
from cispo_model.runtime_monitor import PeakMemoryMonitor


CLOUD_FULL_YEAR_STAGE_A_PROFILE_PREFIX = "barrier_checkpoint_full_year_cloud_"
CLOUD_FULL_YEAR_STAGE_B_PROFILE_PREFIX = "deferred_crossover2_full_year_cloud_"
CLOUD_FINAL_STAGE_A_PROFILE_IDS = frozenset(
    {
        "barrier_stagea_final_full_year_cloud_v6_threads32",
        "barrier_stagea_final_full_year_cloud_v7_threads32_no_softmem",
        "barrier_stagea_final_full_year_cloud_v8_threads64_no_softmem",
        "barrier_stagea_final_full_year_cloud_v9_threads54_no_softmem",
    }
)
CLOUD_NO_SOFTMEM_STAGE_A_PROFILE_IDS = frozenset(
    {
        "barrier_stagea_final_full_year_cloud_v7_threads32_no_softmem",
        "barrier_stagea_final_full_year_cloud_v8_threads64_no_softmem",
        "barrier_stagea_final_full_year_cloud_v9_threads54_no_softmem",
    }
)
CLOUD_FULL_YEAR_MIN_AVAILABLE_MEMORY_GIB = 640.0
CLOUD_NO_SOFTMEM_MIN_AVAILABLE_MEMORY_GIB = 500.0
OFFLINE_RECOVERY_MIN_AVAILABLE_MEMORY_GIB = 90.0
FIXED_SERVER_HOST_MEMORY_PROFILE_PREFIX = (
    "barrier_checkpoint_fixed_server_host_memory_"
)
DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS = frozenset(
    {
        "barrier_checkpoint_full_year_cloud_v4",
        "barrier_checkpoint_full_year_cloud_v5_threads32",
        "barrier_checkpoint_full_year_cloud_v5_threads64",
        "barrier_stagea_final_full_year_cloud_v6_threads32",
        "barrier_stagea_final_full_year_cloud_v7_threads32_no_softmem",
        "barrier_stagea_final_full_year_cloud_v8_threads64_no_softmem",
        "barrier_stagea_final_full_year_cloud_v9_threads54_no_softmem",
    }
)
CANONICAL_DIRECT_SOLVER_PROFILE_JSON_SHA256 = {
    "barrier_checkpoint_full_year_cloud_v4": (
        "694d920f7a6279c20c8316f574233a1bc86ed7c4391fda282bb5363c49a3fe8d"
    ),
    "barrier_checkpoint_full_year_cloud_v5_threads32": (
        "cf02b2c5552aeb1a73710bf177abfd46f0c2f1ac9ebd6f49fe1a4c2356ec8dbe"
    ),
    "barrier_checkpoint_full_year_cloud_v5_threads64": (
        "880caab8644cbd0fd03e392464ded86c7300c99b45799c2c74dbb92422e14118"
    ),
    "barrier_stagea_final_full_year_cloud_v6_threads32": (
        "289b43d461af93cfb42c287f8a4e62c4a7e96e540f6f5d014f54bfe664336aa5"
    ),
    "barrier_stagea_final_full_year_cloud_v7_threads32_no_softmem": (
        "017718ec2e263f928ce9ee6d223d7cc02a721cea54ea0034940c8af143aace50"
    ),
    "barrier_stagea_final_full_year_cloud_v8_threads64_no_softmem": (
        "c1f50c5c146f6ec9765bb871ccaaf65ed7512a599ce7c39478047e262093236b"
    ),
    "barrier_stagea_final_full_year_cloud_v9_threads54_no_softmem": (
        "da9cf36bacf1921535542be0ec466320b56086f0bfec1b147c48c5fce6f13260"
    ),
}
CANONICAL_DIRECT_FORMULATION_PROFILE_JSON_SHA256 = (
    "8f7dcb53cf45b41f9201d51fb527f3dbf6e2eb046e0db60de2a690b3267b09d7"
)
FINAL_STAGE_A_EXPECTED_LP_IDENTITY = {
    "constraints": 50_907_234,
    "variables": 41_458_383,
    "nonzeros": 492_835_195,
    "gurobi_fingerprint_unsigned_hex": "0x94cf2e50",
    "uncompressed_mps_sha256": (
        "8216816027025ffc16eb7fb80ce55d6beb822242f03f1a24433102248603713a"
    ),
}


def write_strict_json_atomic(path: str | Path, payload) -> None:
    """Write scientific control JSON without truncating the prior milestone."""
    target = Path(path)
    temporary = target.with_name(target.name + ".part")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def validate_final_stage_a_lp_identity(model, output_dir: str | Path) -> dict:
    """Fail before optimize if a paid final run is not the reviewed exact LP."""
    root = Path(output_dir)
    model.update()
    actual = {
        "constraints": int(model.NumConstrs),
        "variables": int(model.NumVars),
        "nonzeros": int(model.NumNZs),
        "gurobi_fingerprint_unsigned_hex": (
            f"0x{int(model.Fingerprint) & 0xffffffff:08x}"
        ),
    }
    archive_root = root / "model_archive"
    compressed = archive_root / "original.mps.gz"
    uncompressed = archive_root / "original.mps"
    source = compressed if compressed.is_file() else uncompressed
    digest = hashlib.sha256()
    stream_error = None
    try:
        opener = gzip.open if source == compressed else open
        with opener(source, "rb") as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                digest.update(chunk)
        actual["uncompressed_mps_sha256"] = digest.hexdigest()
    except (OSError, EOFError) as error:
        stream_error = repr(error)
        actual["uncompressed_mps_sha256"] = None
    expected = dict(FINAL_STAGE_A_EXPECTED_LP_IDENTITY)
    failures = [
        key
        for key, expected_value in expected.items()
        if actual.get(key) != expected_value
    ]
    if stream_error is not None:
        failures.append("mps_stream_read")
    report = {
        "schema_version": "cispo_final_stage_a_lp_identity_v1",
        "status": "PASS" if not failures else "FAIL",
        "expected": expected,
        "actual": actual,
        "archive_path": str(source),
        "mps_stream_error": stream_error,
        "failures": sorted(set(failures)),
    }
    write_strict_json_atomic(root / "final_stage_a_lp_identity.json", report)
    if failures:
        raise RuntimeError(
            "Final Stage A exact LP identity mismatch: "
            + ", ".join(sorted(set(failures)))
        )
    return report


def annotate_dual_publication_status(output_dir: str | Path, report: dict) -> None:
    """Keep dual availability separate from permission to publish prices."""
    path = Path(output_dir) / "dual_export_status.json"
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    allowed = bool(
        report.get("solution_contract", {}).get(
            "dual_publication_allowed", False
        )
    )
    payload["publication_allowed"] = allowed
    payload["publication_quality_checks"] = report.get(
        "solution_contract", {}
    ).get("dual_publication_checks")
    payload["publication_status"] = (
        "ALLOWED" if allowed else "WITHHELD_NUMERICAL_QUALITY"
    )
    write_strict_json_atomic(path, payload)


def persist_postsolve_finalization_error(
    output_dir: str | Path,
    *,
    failed_stage: str,
    error: Exception,
    report: dict,
) -> dict:
    """Retain immutable numerical evidence when only packaging fails."""
    root = Path(output_dir)
    evidence: dict[str, dict[str, object]] = {}
    for relative in (
        "solve_report.json",
        "solution_qc.json",
        "barrier_checkpoint/barrier_checkpoint_manifest.json",
    ):
        path = root / relative
        if path.is_file():
            evidence[relative] = {
                "bytes": int(path.stat().st_size),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
    payload = {
        "status": "POST_SOLVE_FINALIZATION_FAILED",
        "scientifically_accepted": False,
        "failed_stage": failed_stage,
        "error_type": type(error).__name__,
        "error": str(error),
        "accepted_checkpoint_retained": bool(
            report.get("barrier_checkpoint", {}).get(
                "scientifically_accepted"
            )
        ),
        "immutable_evidence": evidence,
        "recovery": (
            "Keep this output immutable. Repair/retry packaging from the "
            "checksummed checkpoint or use --recover-stage-a-from into a "
            "new output directory; never rerun into this directory."
        ),
    }
    write_strict_json_atomic(root / "finalization_error.json", payload)
    return payload


def _canonical_json_sha256(payload) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def require_canonical_direct_nonbasic_profiles(config) -> None:
    """Bind direct scientific acceptance to the reviewed profile contents."""
    profile_id = config.raw.get("solver_profile", {}).get("id")
    candidates = (
        (
            "solver",
            config.solver_path,
            CANONICAL_DIRECT_SOLVER_PROFILE_JSON_SHA256.get(profile_id),
        ),
        (
            "formulation",
            config.formulation_path,
            CANONICAL_DIRECT_FORMULATION_PROFILE_JSON_SHA256,
        ),
    )
    for label, candidate_path, expected_sha256 in candidates:
        if candidate_path is None or expected_sha256 is None:
            raise SystemExit(
                f"Direct nonbasic scientific acceptance requires the canonical "
                f"{label} profile"
            )
        try:
            candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SystemExit(
                f"Cannot validate canonical direct {label} profile: {error}"
            ) from error
        if _canonical_json_sha256(candidate) != expected_sha256:
            raise SystemExit(
                f"Direct nonbasic scientific acceptance {label} profile "
                "content differs from the reviewed canonical profile"
            )
    if config.raw.get("formulation", {}).get(
        "annual_capacity_link_row_scaling"
    ) != "binary_power2_safe_8192_v1":
        raise SystemExit(
            "Direct nonbasic scientific acceptance requires "
            "binary_power2_safe_8192_v1 annual capacity-link row scaling"
        )


def cloud_full_year_profile_role(profile_id: object) -> str | None:
    """Classify every version of the fail-closed cloud Stage A/B profiles."""
    if not isinstance(profile_id, str):
        return None
    if profile_id in CLOUD_FINAL_STAGE_A_PROFILE_IDS:
        return "STAGE_A"
    if profile_id.startswith(CLOUD_FULL_YEAR_STAGE_A_PROFILE_PREFIX):
        return "STAGE_A"
    if profile_id.startswith(CLOUD_FULL_YEAR_STAGE_B_PROFILE_PREFIX):
        return "STAGE_B"
    return None


def cloud_full_year_required_memory_gib(
    configured_required_gib: float,
    profile_role: str | None,
    profile_id: str | None = None,
) -> float:
    """Apply the cloud full-year memory floor to every Stage A/B version."""
    required_gib = float(configured_required_gib)
    if profile_id in CLOUD_NO_SOFTMEM_STAGE_A_PROFILE_IDS:
        return max(required_gib, CLOUD_NO_SOFTMEM_MIN_AVAILABLE_MEMORY_GIB)
    if profile_role is not None:
        required_gib = max(
            required_gib,
            CLOUD_FULL_YEAR_MIN_AVAILABLE_MEMORY_GIB,
        )
    return required_gib


def diagnostic_memory_requirement_gb(config, hours: int) -> float:
    """Map an arbitrary diagnostic length to the next validated memory tier."""
    for name in ("one_month", "six_months", "full_year"):
        horizon = config.horizon(name)
        if int(hours) <= int(horizon["hours"]):
            return float(horizon["minimum_available_memory_gb"])
    raise ValueError(f"Diagnostic horizon {hours} exceeds the configured full year")


def load_center_physical_qc_pass(qc: dict | None) -> bool:
    """Apply the original-unit hard gate used by master-solution export."""
    if not isinstance(qc, dict):
        return False
    return bool(
        float(qc.get("maximum_center_balance_residual_gwh", float("inf")))
        <= 1e-5
        and float(
            qc.get(
                "maximum_province_net_exchange_residual_gwh", float("inf")
            )
        )
        <= 1e-5
        and float(qc.get("maximum_intra_capacity_violation_gwh", float("inf")))
        <= 1e-5
        and float(
            qc.get(
                "maximum_vre_annual_availability_violation_gwh",
                float("inf"),
            )
        )
        <= 1e-5
        and float(
            qc.get(
                "maximum_ror_annual_availability_violation_gwh",
                float("inf"),
            )
        )
        <= 1e-5
        and int(qc.get("bidirectional_active_edge_count", -1)) == 0
        and float(qc.get("dpv_spur_augmentation_max_gw", float("inf")))
        <= 1e-8
    )


def resolve_host_memory_soft_limit_gb(
    total_physical_memory_bytes: int,
    fraction: float,
) -> float:
    """Translate a host-memory fraction to Gurobi's decimal-GB limit."""
    total_physical_memory_bytes = int(total_physical_memory_bytes)
    fraction = float(fraction)
    if total_physical_memory_bytes <= 0:
        raise ValueError("total physical memory must be positive")
    if not 0.0 < fraction <= 0.95:
        raise ValueError("host memory fraction must be in (0, 0.95]")
    return total_physical_memory_bytes * fraction / 1_000_000_000


def export_engineering_relaxed_macro_analysis(
    artifacts,
    data,
    config,
    engineering_dir: Path,
    *,
    master_exporter,
    operational_exporter,
    summary_exporter,
):
    """Export unaccepted macro evidence while preserving strict-QC failures."""
    engineering_dir.mkdir(parents=True, exist_ok=True)
    export_errors = []

    def record_expected_qc_failure(stage: str, error: Exception) -> None:
        message = str(error)
        expected_prefixes = (
            "Load-center solution QC failed:",
            "Production solution QC failed:",
        )
        if not isinstance(error, RuntimeError) or not message.startswith(
            expected_prefixes
        ):
            raise error
        export_errors.append(
            {
                "stage": stage,
                "error_type": type(error).__name__,
                "error": message,
            }
        )

    try:
        master_exporter(artifacts, data, engineering_dir)
    except Exception as error:
        record_expected_qc_failure("MASTER_SOLUTION_EXPORT", error)

    engineering_qc = None
    try:
        engineering_qc = operational_exporter(
            artifacts,
            data,
            config,
            engineering_dir,
        )
    except Exception as error:
        record_expected_qc_failure("OPERATIONAL_SOLUTION_EXPORT", error)

    engineering_qc_error = None
    if export_errors:
        first_error = export_errors[0]
        engineering_qc_error = {
            "status": "STRICT_PHYSICAL_QC_EXPORT_FAILED",
            "error_stage": first_error["stage"],
            "error_type": first_error["error_type"],
            "error": first_error["error"],
            "errors": export_errors,
            "scientifically_accepted": False,
        }
        (engineering_dir / "engineering_raw_qc_error.json").write_text(
            json.dumps(
                engineering_qc_error,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    summary_exporter(
        artifacts,
        data,
        config,
        engineering_dir,
    )
    return engineering_qc, engineering_qc_error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sequential CISPO planning-year expansion plus chronological operation"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--scenario-config",
        help="Optional v1 partial override under config/scenarios; recorded in provenance.",
    )
    parser.add_argument(
        "--solver-config",
        help=(
            "Optional v1 numerics-only solver profile. It cannot change the "
            "scientific scenario and is recorded with a SHA256 snapshot."
        ),
    )
    parser.add_argument(
        "--formulation-config",
        help=(
            "Optional v1 algebraically equivalent formulation profile. It may "
            "change matrix structure only and is recorded with a SHA256 snapshot."
        ),
    )
    parser.add_argument(
        "--planning-year",
        type=int,
        choices=(2030, 2040, 2050, 2060),
        help="Override the base configuration with one sequential planning year.",
    )
    parser.add_argument(
        "--state-in",
        help=(
            "Prior accepted full-year planning_state directory. Required after 2030."
        ),
    )
    parser.add_argument(
        "--horizon",
        choices=("one_month", "six_months", "full_year"),
        default="full_year",
        help="744h and 4344h runs are code tests only; full_year is the scientific run.",
    )
    parser.add_argument(
        "--diagnostic-hours",
        type=int,
        help=(
            "Build/solve an exact contiguous-hour diagnostic in [1, 8759]. "
            "Annual flow policy/resource limits use hours/8760 scaling, while "
            "annualized planning costs remain unscaled; never interpret it scientifically."
        ),
    )
    parser.add_argument(
        "--diagnostic-start-hour",
        type=int,
        default=0,
        help=(
            "Zero-based model-year start hour for --diagnostic-hours. "
            "The selected window must remain within [0, 8760); default 0."
        ),
    )
    parser.add_argument(
        "--export-diagnostic-state",
        action="store_true",
        help=(
            "Export an explicitly test-only state for a diagnostic sequence. "
            "That state is rejected by production runs."
        ),
    )
    parser.add_argument(
        "--export-warm-start-basis",
        action="store_true",
        help=(
            "Export a post-crossover Gurobi .bas file plus a strict named-LP "
            "identity manifest. Restricted to diagnostic horizons."
        ),
    )
    parser.add_argument(
        "--export-scientific-solver-artifacts",
        action="store_true",
        help=(
            "After an accepted full-year Base solve, export selective .sol, "
            ".bas, .prm and lightweight fingerprint artifacts. Never valid "
            "for truncated horizons, non-Base cases or MGA outputs."
        ),
    )
    parser.add_argument(
        "--export-barrier-checkpoint",
        action="store_true",
        help=(
            "Legacy flag: nonbasic Stage A now always preserves available "
            "raw vectors and candidate outputs independently of acceptance."
        ),
    )
    parser.add_argument(
        "--engineering-barrier-checkpoint-only",
        action="store_true",
        help=(
            "Treat a Crossover=0 solve as Stage A only: persist finite ordered "
            "BarX/BarPi first, then all results and candidate capacity state. "
            "Preservation is independent of acceptance and does not auto-adopt the state."
        ),
    )
    parser.add_argument(
        "--engineering-relaxed-barrier-analysis",
        action="store_true",
        help=(
            "For an explicitly test-only Stage A run, export the unaccepted "
            "Barrier solution into engineering_macro_analysis/ for macro-scale "
            "capacity, energy, carbon and cost comparison. This never creates "
            "a scientific result manifest or planning state."
        ),
    )
    parser.add_argument(
        "--allow-nonbasic-planning-state",
        action="store_true",
        help=(
            "Explicitly allow a scientifically accepted Crossover=0 Stage A "
            "capacity solution with a closed checkpoint to form the next-year state."
        ),
    )
    parser.add_argument(
        "--primal-dual-checkpoint-in",
        help=(
            "Accepted Barrier-first output root used to seed a separate exact-LP "
            "deferred crossover run. Never overwrites the source result."
        ),
    )
    parser.add_argument(
        "--allow-primal-dual-crossover",
        action="store_true",
        help="Explicitly acknowledge exact-LP deferred crossover from BarX/BarPi.",
    )
    parser.add_argument(
        "--allow-engineering-barrier-checkpoint",
        action="store_true",
        help=(
            "Explicitly allow Stage B to consume a non-scientific "
            "ENGINEERING_BARRIER_CHECKPOINT_ONLY source."
        ),
    )
    parser.add_argument(
        "--allow-compatible-primal-dual-implementation",
        action="store_true",
        help=(
            "Explicitly allow a checkpoint created by another Git/source bundle "
            "only when scientific inputs, layered case identity, exact Gurobi "
            "Fingerprint, dimensions and variable/constraint ordering all match."
        ),
    )
    parser.add_argument(
        "--allow-deferred-crossover-planning-state",
        action="store_true",
        help=(
            "After Stage B alone reaches full scientific acceptance, allow its "
            "basic solution to export the next-year planning state."
        ),
    )
    parser.add_argument(
        "--allow-inline-crossover",
        action="store_true",
        help=(
            "Explicitly permit Barrier and crossover in one solve for horizons "
            "longer than 744h. The default long-horizon contract is Barrier-first."
        ),
    )
    parser.add_argument(
        "--basis-in",
        help=(
            "Accepted diagnostic output directory containing warm_start_basis.bas "
            "and warm_start_basis_manifest.json."
        ),
    )
    parser.add_argument(
        "--allow-basis-reuse",
        action="store_true",
        help="Explicitly acknowledge test-only LP basis reuse for this run.",
    )
    parser.add_argument(
        "--allow-cross-year-basis",
        action="store_true",
        help="Permit a checked diagnostic basis from another planning year.",
    )
    parser.add_argument(
        "--allow-diagnostic-state-in",
        action="store_true",
        help="Allow a test-only predecessor state; valid only for a test horizon.",
    )
    parser.add_argument(
        "--mga-spec",
        help=(
            "Explicit MGA secondary-objective JSON. It is valid only with an "
            "accepted scientific full-year Base baseline."
        ),
    )
    parser.add_argument(
        "--mga-baseline",
        help=(
            "Accepted least-cost Base result root used to set the MGA cost cap."
        ),
    )
    parser.add_argument("--output-dir")
    parser.add_argument(
        "--runtime-soft-mem-limit-gb",
        type=float,
        help=(
            "Runtime Gurobi SoftMemLimit derived from the current Slurm "
            "cgroup. Restricted to the canonical final cloud Stage A profile."
        ),
    )
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--write-mps", action="store_true")
    parser.add_argument(
        "--archive-original-model",
        action="store_true",
        help=(
            "Explicitly archive the original MPS and parameter file. This is "
            "off by default because an 8760h MPS is multi-gigabyte."
        ),
    )
    parser.add_argument(
        "--archive-model-name-catalog",
        action="store_true",
        help=(
            "Also archive ordered variable/constraint name catalogs; implies "
            "--archive-original-model and may require substantial memory/I/O."
        ),
    )
    parser.add_argument("--archive-presolved-model", action="store_true",
                        help="Also run a separate diagnostic presolve archive; implies --archive-original-model and is not an internal restart state.")
    parser.add_argument("--recover-stage-a-from",
                        help="Read-only exact-LP recovery from a result root; never optimize or presolve.")
    parser.add_argument("--allow-candidate-state-in", action="store_true",
                        help="Explicitly use an unaccepted candidate capacity state; retain all upstream QC failures.")
    parser.add_argument(
        "--constraint-family-audit",
        action="store_true",
        help=(
            "Write a raw LP row/column sparsity census by model family. "
            "It does not modify the model and reports presolve only globally."
        ),
    )
    parser.add_argument(
        "--constraint-family-audit-max-nonzeros",
        type=int,
        default=50_000_000,
        help=(
            "Safety limit for the audit's explicit sparse-matrix access; "
            "default 50,000,000."
        ),
    )
    parser.add_argument(
        "--skip-full-max-cf",
        action="store_true",
        help="Developer-only structural build; never use for a production solve.",
    )
    args = parser.parse_args()
    archive_original_model = bool(
        args.archive_original_model
        or args.archive_model_name_catalog
        or args.archive_presolved_model
    )
    if args.recover_stage_a_from:
        if not args.output_dir:
            raise SystemExit("Offline recovery requires an explicit independent --output-dir")
        if Path(args.output_dir).resolve().is_relative_to(Path(args.recover_stage_a_from).resolve()):
            raise SystemExit("Recovery output must not overwrite or be inside the source root")
    if args.skip_full_max_cf and not args.build_only:
        raise SystemExit("--skip-full-max-cf requires --build-only")
    if args.preflight_only and (
        args.build_only or args.write_mps or archive_original_model
    ):
        raise SystemExit(
            "--preflight-only cannot be combined with build/write/archive options"
        )
    if args.diagnostic_hours is not None and not 1 <= args.diagnostic_hours < 8760:
        raise SystemExit("--diagnostic-hours must be in [1, 8759]")
    if args.diagnostic_start_hour < 0:
        raise SystemExit("--diagnostic-start-hour must be nonnegative")
    if args.diagnostic_hours is None and args.diagnostic_start_hour != 0:
        raise SystemExit(
            "--diagnostic-start-hour requires --diagnostic-hours"
        )
    if (
        args.diagnostic_hours is not None
        and args.diagnostic_start_hour + args.diagnostic_hours > 8760
    ):
        raise SystemExit(
            "--diagnostic-start-hour + --diagnostic-hours must not exceed 8760"
        )
    if args.export_diagnostic_state and args.diagnostic_hours is None:
        raise SystemExit("--export-diagnostic-state requires --diagnostic-hours")
    if args.export_warm_start_basis and args.diagnostic_hours is None:
        raise SystemExit("--export-warm-start-basis requires --diagnostic-hours")
    if args.basis_in and not args.allow_basis_reuse:
        raise SystemExit("--basis-in requires explicit --allow-basis-reuse")
    if args.allow_basis_reuse and not args.basis_in:
        raise SystemExit("--allow-basis-reuse requires --basis-in")
    if args.allow_cross_year_basis and not args.basis_in:
        raise SystemExit("--allow-cross-year-basis requires --basis-in")
    if args.primal_dual_checkpoint_in and not args.allow_primal_dual_crossover:
        raise SystemExit(
            "--primal-dual-checkpoint-in requires --allow-primal-dual-crossover"
        )
    if args.allow_primal_dual_crossover and not args.primal_dual_checkpoint_in:
        raise SystemExit(
            "--allow-primal-dual-crossover requires --primal-dual-checkpoint-in"
        )
    if (
        args.allow_engineering_barrier_checkpoint
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            "--allow-engineering-barrier-checkpoint requires "
            "--primal-dual-checkpoint-in"
        )
    if (
        args.allow_compatible_primal_dual_implementation
        and not (args.primal_dual_checkpoint_in or args.recover_stage_a_from)
    ):
        raise SystemExit(
            "--allow-compatible-primal-dual-implementation requires "
            "--primal-dual-checkpoint-in"
        )
    if (
        args.allow_deferred_crossover_planning_state
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            "--allow-deferred-crossover-planning-state requires "
            "--primal-dual-checkpoint-in"
        )
    if bool(args.mga_spec) != bool(args.mga_baseline):
        raise SystemExit("--mga-spec and --mga-baseline must be supplied together")
    if args.constraint_family_audit_max_nonzeros < 1:
        raise SystemExit("--constraint-family-audit-max-nonzeros must be positive")

    base_config = load_model_config(
        args.config,
        args.scenario_config,
        args.solver_config,
        args.formulation_config,
    )
    config = (
        base_config.for_planning_year(args.planning_year)
        if args.planning_year is not None
        else base_config
    )
    requested_test_only = bool(
        args.diagnostic_hours is not None
        or config.horizon(args.horizon)["test_only"]
    )
    profile_id = config.raw.get("solver_profile", {}).get("id")
    runtime_soft_mem_limit_policy = None
    if args.runtime_soft_mem_limit_gb is not None:
        if profile_id in CLOUD_NO_SOFTMEM_STAGE_A_PROFILE_IDS:
            raise SystemExit(
                f"{profile_id} forbids --runtime-soft-mem-limit-gb"
            )
        if profile_id not in CLOUD_FINAL_STAGE_A_PROFILE_IDS:
            raise SystemExit(
                "--runtime-soft-mem-limit-gb is restricted to the final "
                "cloud Stage A profile"
            )
        runtime_soft_mem_limit_gb = float(args.runtime_soft_mem_limit_gb)
        profile_soft_mem_limit_gb = float(
            config.raw["numerics"]["soft_mem_limit_gb"]
        )
        if (
            not np.isfinite(runtime_soft_mem_limit_gb)
            or runtime_soft_mem_limit_gb <= 0.0
        ):
            raise SystemExit(
                "Runtime SoftMemLimit must be finite and positive"
            )
        config.raw["numerics"]["soft_mem_limit_gb"] = (
            runtime_soft_mem_limit_gb
        )
        runtime_soft_mem_limit_policy = {
            "policy": "SLURM_CGROUP_DERIVED_BY_CLOUD_WRAPPER",
            "profile_declared_soft_mem_limit_gb_decimal": (
                profile_soft_mem_limit_gb
            ),
            "resolved_gurobi_soft_mem_limit_gb_decimal": (
                runtime_soft_mem_limit_gb
            ),
        }
    required_formulation_profile_id = config.raw.get(
        "solver_profile", {}
    ).get("required_formulation_profile_id")
    actual_formulation_profile_id = config.raw.get(
        "formulation_profile", {}
    ).get("id")
    if (
        required_formulation_profile_id is not None
        and actual_formulation_profile_id != required_formulation_profile_id
    ):
        raise SystemExit(
            f"{profile_id} requires formulation profile "
            f"{required_formulation_profile_id}; got "
            f"{actual_formulation_profile_id or 'physical_v1/default'}"
        )
    host_memory_soft_limit_fraction = config.raw.get(
        "solver_profile", {}
    ).get("host_memory_soft_limit_fraction")
    host_memory_soft_limit_policy = None
    if host_memory_soft_limit_fraction is not None:
        if not isinstance(profile_id, str) or not profile_id.startswith(
            FIXED_SERVER_HOST_MEMORY_PROFILE_PREFIX
        ):
            raise SystemExit(
                "host_memory_soft_limit_fraction is restricted to the "
                "fixed-server host-memory profile family"
            )
        if not requested_test_only:
            raise SystemExit(
                f"{profile_id} is restricted to test-only truncated horizons"
            )
        total_physical_memory_bytes = int(psutil.virtual_memory().total)
        configured_soft_limit_gb = float(
            config.raw["numerics"]["soft_mem_limit_gb"]
        )
        resolved_soft_limit_gb = resolve_host_memory_soft_limit_gb(
            total_physical_memory_bytes,
            float(host_memory_soft_limit_fraction),
        )
        config.raw["numerics"]["soft_mem_limit_gb"] = (
            resolved_soft_limit_gb
        )
        host_memory_soft_limit_policy = {
            "policy": "GUROBI_SOFT_LIMIT_AS_FRACTION_OF_HOST_PHYSICAL_MEMORY",
            "maximum_fraction": float(host_memory_soft_limit_fraction),
            "host_total_memory_bytes": total_physical_memory_bytes,
            "host_total_memory_gib": round(
                total_physical_memory_bytes / 1024**3, 3
            ),
            "profile_fallback_soft_mem_limit_gb": configured_soft_limit_gb,
            "resolved_gurobi_soft_mem_limit_gb_decimal": round(
                resolved_soft_limit_gb, 6
            ),
            "time_limit_seconds": config.raw["numerics"].get(
                "time_limit_seconds"
            ),
            "interpretation": (
                "The solver may use up to the declared fraction of installed "
                "physical memory. This is an upper allowance, not a target or "
                "a requirement to consume that amount."
            ),
        }
    numerics = config.raw["numerics"]
    nonbasic_primal_dual_requested = bool(
        int(numerics.get("method", -1)) == 2
        and int(numerics.get("crossover", -1)) == 0
        and int(numerics.get("solution_target", -1)) == 1
    )
    direct_nonbasic_scientific_acceptance = bool(
        config.raw.get("solver_profile", {}).get(
            "direct_nonbasic_scientific_acceptance", False
        )
    )
    if (
        direct_nonbasic_scientific_acceptance
        and profile_id not in DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS
    ):
        raise SystemExit(
            "direct_nonbasic_scientific_acceptance is reserved for the "
            "reviewed full-year Stage A profile"
        )
    if direct_nonbasic_scientific_acceptance:
        require_canonical_direct_nonbasic_profiles(config)
    requested_optimization_hours = int(
        args.diagnostic_hours
        if args.diagnostic_hours is not None
        else config.horizon(args.horizon)["hours"]
    )
    if nonbasic_primal_dual_requested and (
        args.basis_in
        or args.export_warm_start_basis
        or args.export_scientific_solver_artifacts
        or args.mga_spec
    ):
        raise SystemExit(
            "The optimal primal-dual nonbasic contract cannot be combined "
            "with basis import/export, scientific .bas artifacts, or MGA"
        )
    if args.export_barrier_checkpoint and not nonbasic_primal_dual_requested:
        raise SystemExit(
            "--export-barrier-checkpoint requires Method=2, Crossover=0, "
            "SolutionTarget=1"
        )
    if (
        args.engineering_barrier_checkpoint_only
        and not nonbasic_primal_dual_requested
    ):
        raise SystemExit(
            "--engineering-barrier-checkpoint-only requires Method=2, "
            "Crossover=0, SolutionTarget=1"
        )
    if args.allow_candidate_state_in and not args.state_in:
        raise SystemExit("--allow-candidate-state-in requires --state-in")
    if args.recover_stage_a_from and any((args.archive_presolved_model, args.primal_dual_checkpoint_in,
                                        args.basis_in, args.mga_spec, args.build_only, args.preflight_only)):
        raise SystemExit("Offline recovery cannot be combined with presolve, starts, MGA, build-only or preflight-only")
    if args.allow_candidate_state_in and args.mga_spec:
        raise SystemExit("Unaccepted candidate state cannot define an accepted MGA baseline")
    if (
        args.engineering_relaxed_barrier_analysis
        and not args.engineering_barrier_checkpoint_only
    ):
        raise SystemExit(
            "--engineering-relaxed-barrier-analysis requires "
            "--engineering-barrier-checkpoint-only"
        )
    if args.engineering_relaxed_barrier_analysis and not requested_test_only:
        raise SystemExit(
            "--engineering-relaxed-barrier-analysis is restricted to "
            "test-only truncated horizons"
        )
    if args.allow_nonbasic_planning_state and not nonbasic_primal_dual_requested:
        raise SystemExit(
            "--allow-nonbasic-planning-state requires Method=2, Crossover=0, "
            "SolutionTarget=1"
        )
    if (
        args.allow_nonbasic_planning_state
        and args.engineering_barrier_checkpoint_only
    ):
        raise SystemExit(
            "A preservation-only engineering Stage A cannot export planning_state"
        )
    if args.allow_nonbasic_planning_state and requested_test_only and not (
        args.export_diagnostic_state
    ):
        raise SystemExit(
            "A diagnostic nonbasic planning state also requires "
            "--export-diagnostic-state"
        )
    if args.allow_nonbasic_planning_state and not (
        args.export_barrier_checkpoint or requested_optimization_hours > 744
    ):
        raise SystemExit(
            "A nonbasic planning state requires a closed accepted Barrier "
            "checkpoint; pass --export-barrier-checkpoint for horizons up to 744h"
        )
    if args.primal_dual_checkpoint_in:
        if args.basis_in or args.mga_spec or nonbasic_primal_dual_requested:
            raise SystemExit(
                "Deferred primal/dual crossover cannot be combined with a basis, "
                "MGA, or another Crossover=0 solve"
            )
        if (
            int(numerics.get("method", -1)) != 2
            or int(numerics.get("crossover", 0)) <= 0
            or int(numerics.get("lp_warm_start", -1)) != 2
        ):
            raise SystemExit(
                "Deferred crossover requires Method=2, Crossover>0 and LPWarmStart=2"
            )
    cloud_full_year_role = cloud_full_year_profile_role(profile_id)
    if host_memory_soft_limit_policy is not None:
        if cloud_full_year_role is not None:
            raise SystemExit(
                "The fixed-server host-memory policy cannot be combined with "
                "a cloud full-year profile"
            )
        if not args.engineering_barrier_checkpoint_only:
            raise SystemExit(
                f"{profile_id} requires "
                "--engineering-barrier-checkpoint-only"
            )
        if (
            int(numerics.get("method", -1)) != 2
            or int(numerics.get("crossover", -1)) != 0
            or int(numerics.get("solution_target", -1)) != 1
            or numerics.get("time_limit_seconds") is not None
        ):
            raise SystemExit(
                f"{profile_id} requires Method=2, Crossover=0, "
                "SolutionTarget=1 and no solver time limit"
            )
    if (
        cloud_full_year_role == "STAGE_B"
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            f"{profile_id} requires "
            "--primal-dual-checkpoint-in"
        )
    if (
        nonbasic_primal_dual_requested
        and not args.engineering_barrier_checkpoint_only
        and not direct_nonbasic_scientific_acceptance
    ):
        raise SystemExit(
            f"{profile_id} requires --engineering-barrier-checkpoint-only; "
            "this solver profile does not authorize direct scientific "
            "nonbasic acceptance"
        )
    if cloud_full_year_role is not None and requested_test_only:
        raise SystemExit(
            f"{profile_id} is restricted to the scientific full-year horizon"
        )
    if (
        requested_optimization_hours > 744
        and not args.preflight_only
        and not args.build_only
        and int(numerics.get("crossover", 0)) > 0
        and not args.primal_dual_checkpoint_in
        and not args.allow_inline_crossover
    ):
        raise SystemExit(
            "HARD_FAIL: horizons longer than 744h use Barrier-first acceptance. "
            "Select the nonbasic primal/dual profile, seed a deferred crossover, "
            "or explicitly pass --allow-inline-crossover."
        )
    if args.export_scientific_solver_artifacts and requested_test_only:
        raise SystemExit(
            "--export-scientific-solver-artifacts requires the full-year horizon"
        )
    if (
        args.export_scientific_solver_artifacts
        and base_config.raw["scenario"].get("analysis_role") != "BASELINE"
    ):
        raise SystemExit(
            "--export-scientific-solver-artifacts is restricted to Base"
        )
    if args.export_scientific_solver_artifacts and args.mga_spec:
        raise SystemExit(
            "--export-scientific-solver-artifacts cannot be used for MGA"
        )
    if args.allow_diagnostic_state_in and not requested_test_only:
        raise SystemExit(
            "--allow-diagnostic-state-in cannot be used for a scientific full-year run"
        )
    if args.mga_spec and requested_test_only:
        raise SystemExit("MGA requires the configured scientific full-year horizon")
    if args.mga_spec and (
        args.export_diagnostic_state
        or args.export_warm_start_basis
        or args.basis_in
        or args.allow_diagnostic_state_in
    ):
        raise SystemExit("MGA cannot be combined with diagnostic state or basis reuse")
    from cispo_model.planning_state import PlanningState

    if config.boundary_year == 2025:
        if args.state_in:
            raise SystemExit("2030 uses the 2025 data boundary and must not receive --state-in")
        planning_state = PlanningState.empty(config.boundary_year)
    else:
        if not args.state_in:
            raise SystemExit(
                f"{config.planning_year} requires --state-in from accepted "
                f"{config.boundary_year} full-year results"
            )
        planning_state = PlanningState.load(
            args.state_in,
            expected_boundary_year=config.boundary_year,
            allow_test_only=args.allow_diagnostic_state_in,
            allow_unaccepted_candidate=args.allow_candidate_state_in,
        )
        if (
            planning_state.metadata.get("state_use")
            == "TEST_ONLY_TRUNCATED_HORIZON"
            and not requested_test_only
        ):
            raise SystemExit("A diagnostic planning state cannot enter a production run")
    if args.diagnostic_hours is None:
        horizon_name = args.horizon
        horizon = config.horizon(args.horizon)
        optimization_hours = int(horizon["hours"])
        optimization_start_hour = 0
        test_only = bool(horizon["test_only"])
        definition = str(horizon["definition"])
        required_gb = float(horizon["minimum_available_memory_gb"])
    else:
        horizon_name = f"diagnostic_{args.diagnostic_hours}h"
        optimization_hours = int(args.diagnostic_hours)
        optimization_start_hour = int(args.diagnostic_start_hour)
        test_only = True
        definition = (
            f"{optimization_hours} chronological hours starting at zero-based "
            f"model hour {optimization_start_hour}; cyclic over the selected "
            "diagnostic horizon"
        )
        required_gb = diagnostic_memory_requirement_gb(
            config, optimization_hours
        )
    required_gb = cloud_full_year_required_memory_gib(
        required_gb,
        cloud_full_year_role,
        profile_id,
    )
    output_dir = Path(
        args.output_dir or f"outputs/{config.planning_year}_{horizon_name}"
    )
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    try:
        claim_output_directory(output_dir)
    except RuntimeError as error:
        raise SystemExit(f"HARD_FAIL: {error}") from error

    available_gb = psutil.virtual_memory().available / 1024**3
    write_run_provenance(
        output_dir,
        config,
        data_root=DATA_ROOT,
        planning_state=planning_state,
    )
    (output_dir / RUN_IDENTITY_FILENAME).write_text(
        json.dumps(
            configuration_identity(config, data_root=DATA_ROOT),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    data = load_model_data(config, planning_state=planning_state)
    time_rows = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
    )
    optimization_stop_hour = optimization_start_hour + optimization_hours
    selected_time_rows = time_rows.iloc[
        optimization_start_hour:optimization_stop_hour
    ]
    if len(selected_time_rows) != optimization_hours:
        raise SystemExit("Selected diagnostic time window is incomplete")
    selected_time_start_bj = str(selected_time_rows.datetime_bj.iloc[0])
    selected_time_end_bj = str(selected_time_rows.datetime_bj.iloc[-1])
    prebuild_solver_numerical_compatibility = (
        prebuild_flexible_load_solver_compatibility(
            config,
            data,
            hours=optimization_hours,
            hour_start=optimization_start_hour,
            allow_engineering_relaxed_nonbasic=bool(
                args.engineering_relaxed_barrier_analysis
            ),
        )
    )
    preflight = run_preflight(config, data, output_dir / "preflight_report.json")
    if preflight["status"] != "PASS":
        raise SystemExit("Preflight HARD_FAIL; model was not built")
    selected_scale = estimate_full_model_scale(config, data, optimization_hours)
    scope_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "optimization_start_hour": optimization_start_hour,
        "optimization_stop_hour_exclusive": optimization_stop_hour,
        "selected_time_start_bj": selected_time_start_bj,
        "selected_time_end_bj": selected_time_end_bj,
        "configured_full_year_hours": config.hours,
        "definition": definition,
        "result_use": "TEST_ONLY_TRUNCATED_HORIZON" if test_only else "SCIENTIFIC_PRODUCTION",
        "offline_recovery": ({
            "source": str(Path(args.recover_stage_a_from).resolve()),
            "minimum_available_memory_gib": (OFFLINE_RECOVERY_MIN_AVAILABLE_MEMORY_GIB if optimization_hours > 744 else required_gb),
            "optimize_called": False, "presolve_called": False,
        } if args.recover_stage_a_from else None),
        "scientific_acceptance_mode": (
            "ENGINEERING_RELAXED_BARRIER_MACRO_ANALYSIS"
            if args.engineering_relaxed_barrier_analysis
            else "ENGINEERING_BARRIER_CHECKPOINT_ONLY"
            if args.engineering_barrier_checkpoint_only
            else "OFFLINE_RECOVERY_UNACCEPTED"
            if args.recover_stage_a_from
            else "UPSTREAM_CANDIDATE_REMAINS_UNACCEPTED"
            if args.allow_candidate_state_in
            else "STRICT_NONBASIC_STAGE_A_DIRECT_ACCEPTANCE"
            if nonbasic_primal_dual_requested
            else "STANDARD_STRICT_ACCEPTANCE"
        ),
        "annual_cost_and_policy_scaling": (
            "annualized planning costs unscaled; annual flow policy and resource "
            "accounts scaled by optimization_hours/configured_full_year_hours"
            if test_only
            else "full annual accounting"
        ),
        "annualized_planning_cost_scaling_factor": 1.0,
        "annual_flow_policy_resource_scaling_factor": (
            float(optimization_hours) / float(config.hours)
        ),
        "time_boundary": "cyclic_over_selected_horizon",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "scenario_id": config.raw["scenario"]["id"],
        "scenario_family": config.raw["scenario"]["family"],
        "analysis_role": config.raw["scenario"]["analysis_role"],
        "publication_status": config.raw["scenario"]["publication_status"],
        "baseline_contract_case_id": config.raw["scientific_case"]["case_id"],
        "formulation_profile_id": config.raw.get("formulation_profile", {}).get(
            "id"
        ),
        "annual_emissions_accounting": config.raw["formulation"][
            "annual_emissions_accounting"
        ],
        "annual_capacity_link_row_scaling": config.raw["formulation"].get(
            "annual_capacity_link_row_scaling", "physical_v1"
        ),
        "state_in": str(planning_state.root) if planning_state.root else None,
        "state_format": planning_state.metadata.get("format"),
        "available_memory_gb": round(available_gb, 2),
        "minimum_available_memory_gb": required_gb,
        "memory_gate_pass": available_gb >= required_gb,
        "host_memory_soft_limit_policy": host_memory_soft_limit_policy,
        "runtime_soft_mem_limit_policy": runtime_soft_mem_limit_policy,
        "scale_estimate": selected_scale.__dict__,
        "gurobi_required_for_build": True,
        "solution_contract_requested": {
            "mode": (
                "OPTIMAL_PRIMAL_DUAL_NONBASIC"
                if nonbasic_primal_dual_requested
                else "OPTIMAL_BASIC_OR_DEFAULT"
            ),
            "basis_required": not nonbasic_primal_dual_requested,
            "dual_attribute": (
                "BarPi" if nonbasic_primal_dual_requested else "Pi"
            ),
        },
        "basis_reuse_request": {
            "basis_in": str(args.basis_in) if args.basis_in else None,
            "allow_basis_reuse": bool(args.allow_basis_reuse),
            "allow_cross_year_basis": bool(args.allow_cross_year_basis),
            "export_warm_start_basis": bool(args.export_warm_start_basis),
        },
        "barrier_first_workflow": {
            "nonbasic_primal_dual_requested": nonbasic_primal_dual_requested,
            "primary_checkpoint_requested": bool(
                nonbasic_primal_dual_requested
                and not args.engineering_barrier_checkpoint_only
                and (
                    args.export_barrier_checkpoint
                    or optimization_hours > 744
                )
            ),
            "engineering_checkpoint_requested": bool(
                nonbasic_primal_dual_requested
                and args.engineering_barrier_checkpoint_only
            ),
            "deferred_crossover_source": (
                str(args.primal_dual_checkpoint_in)
                if args.primal_dual_checkpoint_in
                else None
            ),
            "engineering_checkpoint_only": bool(
                args.engineering_barrier_checkpoint_only
            ),
            "engineering_checkpoint_source_explicitly_allowed": bool(
                args.allow_engineering_barrier_checkpoint
            ),
            "compatible_implementation_bundle_explicitly_allowed": bool(
                args.allow_compatible_primal_dual_implementation
            ),
            "inline_crossover_explicitly_allowed": bool(
                args.allow_inline_crossover
            ),
            "nonbasic_planning_state_explicitly_allowed": bool(
                args.allow_nonbasic_planning_state
            ),
            "deferred_crossover_planning_state_explicitly_allowed": bool(
                args.allow_deferred_crossover_planning_state
            ),
            "planning_state_policy": (
                "UPSTREAM_UNACCEPTED_CANDIDATE_CANNOT_BECOME_ACCEPTED_STATE"
                if args.allow_candidate_state_in
                else (
                    "ACCEPTED_STAGE_B_BASIC_CAPACITY_STATE"
                    if args.allow_deferred_crossover_planning_state
                    else (
                        "ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE"
                        if args.allow_nonbasic_planning_state
                        else (
                            "POSTHOC_CROSSOVER_ANALYSIS_DERIVATIVE_NO_STATE"
                            if args.primal_dual_checkpoint_in
                            else "DEFAULT_BASIC_OR_NO_STATE"
                        )
                    )
                )
            ),
        },
        "analysis_mode": "BASE_MINIMUM_COST",
        "mga": None,
        "scientific_solver_artifacts_requested": bool(
            args.export_scientific_solver_artifacts
        ),
        "solver_numerical_compatibility_prebuild": (
            prebuild_solver_numerical_compatibility
        ),
    }
    (output_dir / "run_scope.json").write_text(
        json.dumps(scope_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    mga_request = None
    if args.mga_spec:
        from cispo_model.mga import prepare_mga_request

        mga_request = prepare_mga_request(
            args.mga_spec,
            args.mga_baseline,
            config,
            output_dir / "input_manifest.csv",
        )
        scope_report["analysis_mode"] = mga_request["analysis_mode"]
        scope_report["mga"] = {
            key: value
            for key, value in mga_request.items()
            if key not in {"baseline"}
        }
        scope_report["mga"]["baseline_result_manifest_sha256"] = mga_request[
            "baseline"
        ]["baseline_result_manifest_sha256"]
        (output_dir / "mga_request.json").write_text(
            json.dumps(mga_request, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_dir / "run_scope.json").write_text(
            json.dumps(scope_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.preflight_only:
        print(json.dumps(scope_report, ensure_ascii=False, indent=2))
        if prebuild_solver_numerical_compatibility["status"] != "PASS":
            raise SystemExit(
                "Preflight numerical compatibility HARD_FAIL: "
                + str(prebuild_solver_numerical_compatibility["reason"])
            )
        return
    if (
        not args.build_only
        and not args.recover_stage_a_from
        and prebuild_solver_numerical_compatibility["status"] != "PASS"
    ):
        raise RuntimeError(
            str(prebuild_solver_numerical_compatibility["reason"])
        )
    if args.recover_stage_a_from and optimization_hours > 744:
        # Recovery only builds the original LP; it never allocates Barrier factors.
        required_gb = OFFLINE_RECOVERY_MIN_AVAILABLE_MEMORY_GIB
    if args.recover_stage_a_from:
        from cispo_model.offline_solution import verify_recovery_inputs
        verify_recovery_inputs(args.recover_stage_a_from, output_dir,
            allow_compatible_implementation=args.allow_compatible_primal_dual_implementation, check_lp=False)
    if available_gb < required_gb:
        raise SystemExit(
            f"HARD_FAIL: available memory {available_gb:.1f} GiB < "
            f"{required_gb:.1f} GiB required for {horizon_name}"
        )

    # Lazy imports let data/horizon preflight run before Gurobi is installed.
    from cispo_model.diagnostics import model_statistics, solve_and_report
    from cispo_model.model_structure_audit import audit_model_structure
    from cispo_model.master import export_master_solution
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.solution_export import export_operational_solution
    from cispo_model.result_summary import export_result_summary, finalize_result_manifest
    from cispo_model.io_contract import write_output_catalog
    from cispo_model.planning_state import export_solution_planning_state

    started = datetime.now().astimezone()
    memory_monitor = PeakMemoryMonitor().start()
    artifacts = build_full_year_monolithic(
        config,
        data,
        compute_max_cf=not args.skip_full_max_cf,
        optimization_hours=optimization_hours,
        optimization_start_hour=optimization_start_hour,
    )
    row_scaling_registry = artifacts.index.get(
        "annual_capacity_link_row_scaling"
    )
    requested_row_scaling = config.raw["formulation"].get(
        "annual_capacity_link_row_scaling", "physical_v1"
    )
    if (
        requested_row_scaling != "physical_v1"
        and not isinstance(row_scaling_registry, dict)
    ):
        raise RuntimeError(
            "Requested annual capacity-link row scaling has no runtime registry"
        )
    if direct_nonbasic_scientific_acceptance:
        from cispo_model.annual_capacity_link_scaling import (
            BINARY_POWER2_SAFE_8192_V1,
            MAX_BINARY_EXPONENT,
            validate_row_scaling_registry,
        )

        validated_direct_registry = validate_row_scaling_registry(
            row_scaling_registry,
            model=artifacts.model,
            allow_none=False,
        )
        if (
            validated_direct_registry["profile"]
            != BINARY_POWER2_SAFE_8192_V1
            or any(
                int(family["exponent"]) != MAX_BINARY_EXPONENT
                for family in validated_direct_registry["families"].values()
            )
        ):
            raise RuntimeError(
                "Direct nonbasic scientific acceptance requires exact VRE/ROR "
                "annual capacity-link exponent 13 runtime evidence"
            )
    row_scaling_manifest_path = None
    if row_scaling_registry is not None:
        row_scaling_manifest_path = (
            output_dir / "annual_capacity_link_row_scaling.json"
        )
        row_scaling_manifest_path.write_text(
            json.dumps(row_scaling_registry, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    # Every run records a constant-memory Gurobi identity. Exact ordered names
    # and the raw CSR pattern are materialized only for explicit guarded basis
    # import/export, never merely because a long-horizon solve was requested.
    from cispo_model.basis_reuse import (
        lightweight_lp_identity,
        lp_topology_identity,
    )

    lp_model = lightweight_lp_identity(artifacts.model)
    lp_topology = (
        lp_topology_identity(artifacts.model)
        if args.basis_in or args.export_warm_start_basis
        else None
    )
    (output_dir / RUN_IDENTITY_FILENAME).write_text(
        json.dumps(
            configuration_identity(
                config,
                data_root=DATA_ROOT,
                lp_model=lp_model,
                lp_topology=lp_topology,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    mga_run = None
    if mga_request is not None:
        from cispo_model.mga import apply_mga_secondary_objective

        mga_run = apply_mga_secondary_objective(artifacts, data, mga_request)
        (output_dir / "mga_run.json").write_text(
            json.dumps(mga_run, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    warm_start = None
    if args.basis_in:
        from cispo_model.basis_reuse import prepare_basis_reuse

        warm_start = prepare_basis_reuse(
            args.basis_in,
            artifacts.model,
            config,
            optimization_hours=optimization_hours,
            optimization_start_hour=optimization_start_hour,
            result_use=scope_report["result_use"],
            allow_cross_year=bool(args.allow_cross_year_basis),
        )
        (output_dir / "warm_start_input.json").write_text(
            json.dumps(warm_start, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    primal_dual_start = None
    if args.primal_dual_checkpoint_in:
        from cispo_model.primal_dual_checkpoint import (
            prepare_primal_dual_crossover,
        )

        primal_dual_start = prepare_primal_dual_crossover(
            args.primal_dual_checkpoint_in,
            output_dir,
            artifacts.model,
            config,
            optimization_hours=optimization_hours,
            optimization_start_hour=optimization_start_hour,
            result_use=scope_report["result_use"],
            allow_engineering_checkpoint=bool(
                args.allow_engineering_barrier_checkpoint
            ),
            allow_compatible_implementation_bundle=bool(
                args.allow_compatible_primal_dual_implementation
            ),
            row_scaling_registry=row_scaling_registry,
        )
        (output_dir / "primal_dual_start_input.json").write_text(
            json.dumps(primal_dual_start, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    structure_audit_path = output_dir / "constraint_family_audit.json"
    structure_audit = None
    if args.constraint_family_audit:
        structure_audit = audit_model_structure(
            artifacts.model,
            max_matrix_nonzeros=args.constraint_family_audit_max_nonzeros,
        )
        structure_audit_path.write_text(
            json.dumps(structure_audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    statistics = model_statistics(artifacts.model)
    flexible_load_structural_audit = artifacts.index.get(
        "flexible_load_structural_audit", {}
    )
    flexible_formulation = str(
        config.raw["flexible_load"].get("formulation")
    )
    compatibility_structural_audit = (
        flexible_load_structural_audit
        if bool(config.raw["features"]["flexible_load"])
        and flexible_formulation == "integrated_service_constrained_v5"
        else {}
    )
    solver_numerical_compatibility = (
        assess_flexible_load_solver_compatibility(
            compatibility_structural_audit,
            config.raw["numerics"],
            allow_engineering_relaxed_nonbasic=bool(
                args.engineering_relaxed_barrier_analysis
            ),
        )
    )
    build_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "build_started_at": started.isoformat(),
        "architecture": "full_year_monolithic_lp",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "scenario_id": config.raw["scenario"]["id"],
        "formulation_profile_id": config.raw.get("formulation_profile", {}).get(
            "id"
        ),
        "annual_emissions_accounting": config.raw["formulation"][
            "annual_emissions_accounting"
        ],
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "optimization_start_hour": optimization_start_hour,
        "optimization_stop_hour_exclusive": optimization_stop_hour,
        "selected_time_start_bj": selected_time_start_bj,
        "selected_time_end_bj": selected_time_end_bj,
        "result_use": scope_report["result_use"],
        "available_memory_gb_before_build": round(available_gb, 2),
        "full_max_cf_used": not args.skip_full_max_cf,
        "constraint_family_audit": {
            "enabled": bool(args.constraint_family_audit),
            "path": str(structure_audit_path) if structure_audit else None,
            "matrix_nonzero_safety_limit": (
                int(args.constraint_family_audit_max_nonzeros)
                if args.constraint_family_audit
                else None
            ),
        },
        "flexible_load_structural_audit": (
            flexible_load_structural_audit
        ),
        "solver_numerical_compatibility": (
            solver_numerical_compatibility
        ),
        "solver_numerical_compatibility_prebuild": (
            prebuild_solver_numerical_compatibility
        ),
        "solver_numerical_compatibility_gate_consistent": (
            solver_numerical_compatibility
            == prebuild_solver_numerical_compatibility
        ),
        "memory_after_build": memory_monitor.snapshot(),
        "statistics": statistics,
        "annual_capacity_link_row_scaling": row_scaling_registry,
        "annual_capacity_link_row_scaling_path": (
            str(row_scaling_manifest_path)
            if row_scaling_manifest_path is not None
            else None
        ),
        "warm_start": warm_start,
        "primal_dual_start": primal_dual_start,
        "mga": mga_run,
    }
    (output_dir / "build_report.json").write_text(
        json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.write_mps:
        artifacts.model.write(
            str(output_dir / f"cispo_{config.planning_year}_{optimization_hours}h.mps")
        )
    from cispo_model.solution_preservation import archive_model, preserve_stage_a, write_json
    if (
        not args.recover_stage_a_from
        and (not args.build_only or archive_original_model)
    ):
        from cispo_model.diagnostics import configure_gurobi
        configure_gurobi(artifacts.model, config, output_dir / "gurobi.log")
    if archive_original_model:
        archive_model(
            artifacts.model,
            output_dir,
            presolved=args.archive_presolved_model,
            include_name_catalog=args.archive_model_name_catalog,
        )
    if profile_id in CLOUD_FINAL_STAGE_A_PROFILE_IDS:
        if not archive_original_model:
            raise RuntimeError(
                "Final Stage A requires --archive-original-model for exact LP identity"
            )
        build_report["final_stage_a_lp_identity"] = (
            validate_final_stage_a_lp_identity(artifacts.model, output_dir)
        )
        write_strict_json_atomic(output_dir / "build_report.json", build_report)
    if args.recover_stage_a_from:
        import shutil
        from cispo_model.offline_solution import (
            offline_artifacts, read_snapshot, read_legacy_checkpoint, verify_recovery_inputs, audit_saved_primal,
        )
        from cispo_model.solution_preservation import write_json
        source_root = Path(args.recover_stage_a_from).resolve()
        evidence = verify_recovery_inputs(source_root, output_dir,
            allow_compatible_implementation=args.allow_compatible_primal_dual_implementation)
        if (source_root / "solution_snapshot" / "snapshot_manifest.json").is_file():
            primal, dual = read_snapshot(
                artifacts.model,
                source_root / "solution_snapshot",
                expected_row_scaling_registry=row_scaling_registry,
            )
            source_vectors = source_root / "solution_snapshot"
        else:
            primal, dual = read_legacy_checkpoint(
                artifacts.model,
                source_root,
                expected_row_scaling_registry=row_scaling_registry,
            )
            source_vectors = source_root / "barrier_checkpoint"
        view = offline_artifacts(artifacts, primal, dual)
        source_report = json.loads((source_root / "solve_report.json").read_text(encoding="utf-8"))
        write_json(output_dir / "raw_lp_qc.json", audit_saved_primal(
            artifacts.model, primal,
            tolerance=float((source_report.get("solution_contract") or {}).get("maximum_primal_quality_limit") or 1e-5),
            violations_path=output_dir / "raw_lp_violations.csv.gz",
            row_scaling_registry=row_scaling_registry))
        evidence["source_solve_report_sha256"] = hashlib.sha256(
            (source_root / "solve_report.json").read_bytes()).hexdigest()
        evidence["recomputed_objective"] = float(view.model.ObjVal)
        evidence["source_objective"] = source_report.get("objective_value_million_cny")
        if evidence["source_objective"] is not None:
            evidence["objective_difference"] = float(view.model.ObjVal - evidence["source_objective"])
        shutil.copytree(source_vectors, output_dir / "source_checkpoint")
        shutil.copy2(source_root / "solve_report.json", output_dir / "source_solve_report.json")
        write_json(output_dir / "offline_recovery.json", evidence)
        recovered = preserve_stage_a(view, data, config, output_dir,
                                    dict(source_report, recovery="offline_recovery.json"), snapshot=False)
        write_json(output_dir / "preservation_runtime_memory.json", memory_monitor.stop())
        finalize_result_manifest(output_dir, config)
        print(json.dumps(recovered, ensure_ascii=False, indent=2))
        if recovered["status"] != "COMPLETE":
            raise SystemExit(2)
        return
    if args.build_only:
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(build_report, ensure_ascii=False, indent=2))
        return
    if not build_report["solver_numerical_compatibility_gate_consistent"]:
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            "Flexible-load numerical compatibility changed between "
            "prebuild and postbuild audits"
        )
    if solver_numerical_compatibility["status"] != "PASS":
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            str(solver_numerical_compatibility["reason"])
        )
    report = solve_and_report(
        artifacts.model,
        config,
        output_dir,
        compute_iis=bool(config.raw["construction"]["compute_iis_on_infeasible"]),
        warm_start=warm_start,
        primal_dual_start=primal_dual_start,
    )
    report.update(
        boundary_year=config.boundary_year,
        planning_year=config.planning_year,
        scenario_id=config.raw["scenario"]["id"],
        scenario_family=config.raw["scenario"]["family"],
        analysis_role=config.raw["scenario"]["analysis_role"],
        publication_status=config.raw["scenario"]["publication_status"],
        baseline_contract_case_id=config.raw["scientific_case"]["case_id"],
        horizon=horizon_name,
        optimization_hours=optimization_hours,
        optimization_start_hour=optimization_start_hour,
        result_use=scope_report["result_use"],
        upstream_candidate_state=(planning_state.metadata if planning_state.metadata.get("candidate_unaccepted") else None),
        annual_capacity_link_row_scaling=row_scaling_registry,
    )
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    solver_solution_accepted = bool(
        report["status"] == "OPTIMAL"
        and report.get("solution_contract", {}).get(
            "acceptance_status"
        ) == "PASS"
    )
    if direct_nonbasic_scientific_acceptance:
        report["stage_a_completion_status"] = (
            "PENDING_CHECKPOINT"
            if report.get("status") == "OPTIMAL"
            else "STAGE_A_INFRASTRUCTURE_FAILED"
        )
    engineering_checkpoint_completed = False
    raw_checkpoint_saved = False
    semantic_artifacts = artifacts
    barrier_status_code = report.get("solution_contract", {}).get(
        "barrier_status_code"
    )
    barrier_iterations = int(
        report.get("iteration_counts", {}).get("barrier", 0)
    )
    if (
        nonbasic_primal_dual_requested
        and (
            args.engineering_barrier_checkpoint_only
            or not solver_solution_accepted
        )
        and (barrier_status_code == 2 or barrier_iterations > 0)
    ):
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )

            complete_barrier = barrier_status_code == 2
            engineering_checkpoint = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=None,
                accepted_primary=False,
                engineering_only=complete_barrier,
                allow_incomplete_barrier=not complete_barrier,
                row_scaling_registry=row_scaling_registry,
            )
            engineering_checkpoint_completed = complete_barrier
            raw_checkpoint_saved = True
            if complete_barrier:
                from cispo_model.offline_solution import offline_artifacts

                checkpoint_root = output_dir / CHECKPOINT_DIRECTORY
                checkpoint_primal = np.load(
                    checkpoint_root
                    / engineering_checkpoint["vectors"]["primal"]["path"],
                    mmap_mode="r",
                    allow_pickle=False,
                )
                checkpoint_dual = np.load(
                    checkpoint_root
                    / engineering_checkpoint["vectors"]["dual"]["path"],
                    mmap_mode="r",
                    allow_pickle=False,
                )
                semantic_artifacts = offline_artifacts(
                    artifacts,
                    checkpoint_primal,
                    checkpoint_dual,
                    objective=report.get("objective_value_million_cny"),
                )
            report["barrier_checkpoint"] = {
                "status": engineering_checkpoint["checkpoint_status"],
                "scientifically_accepted": False,
                "deferred_crossover_eligible": complete_barrier,
                "engineering_shadow_prices_available": True,
                "semantic_export_primal_attribute": (
                    "BarX" if complete_barrier else "LIVE_SOLVER_VALUES"
                ),
                "semantic_export_dual_attribute": (
                    "BarPi" if complete_barrier else "LIVE_SOLVER_VALUES"
                ),
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
            raw_checkpoint_saved = True
            report["run_completion_status"] = (
                "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
                if complete_barrier
                else "INCOMPLETE_BARRIER_RECOVERY_SAVED"
            )
            if direct_nonbasic_scientific_acceptance:
                report["stage_a_completion_status"] = (
                    "STAGE_A_COMPLETED_REVIEW_REQUIRED"
                    if complete_barrier
                    else "STAGE_A_INFRASTRUCTURE_FAILED"
                )
            # Persist this milestone before any optional downstream export.
            (output_dir / "solve_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception as error:
            checkpoint_error = {
                "status": "ENGINEERING_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
    if (
        int(report.get("solver_parameters", {}).get("method", -1)) == 2
        and int(report.get("solver_parameters", {}).get("crossover", 0)) > 0
        and report.get("solution_contract", {}).get("barrier_status_code") == 2
        and report.get("status") != "OPTIMAL"
    ):
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )

            recovery = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=None,
                accepted_primary=False,
                row_scaling_registry=row_scaling_registry,
            )
            report["barrier_checkpoint"] = {
                "status": recovery["checkpoint_status"],
                "scientifically_accepted": False,
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
        except Exception as error:
            checkpoint_error = {
                "status": "RECOVERY_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
    primary_checkpoint_requested = bool(
        nonbasic_primal_dual_requested
        and not args.engineering_barrier_checkpoint_only
        and (args.export_barrier_checkpoint or optimization_hours > 744)
    )
    if primary_checkpoint_requested and solver_solution_accepted:
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )
            from cispo_model.offline_solution import offline_artifacts

            pending_checkpoint = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=None,
                accepted_primary=False,
                pending_qc=True,
                row_scaling_registry=row_scaling_registry,
            )
            raw_checkpoint_saved = True
            checkpoint_root = output_dir / CHECKPOINT_DIRECTORY
            checkpoint_primal = np.load(
                checkpoint_root
                / pending_checkpoint["vectors"]["primal"]["path"],
                mmap_mode="r",
                allow_pickle=False,
            )
            checkpoint_dual = np.load(
                checkpoint_root
                / pending_checkpoint["vectors"]["dual"]["path"],
                mmap_mode="r",
                allow_pickle=False,
            )
            semantic_artifacts = offline_artifacts(
                artifacts,
                checkpoint_primal,
                checkpoint_dual,
                objective=report.get("objective_value_million_cny"),
            )
            report["barrier_checkpoint"] = {
                "status": pending_checkpoint["checkpoint_status"],
                "scientifically_accepted": False,
                "deferred_crossover_eligible": False,
                "stage_b_required": False,
                "semantic_export_primal_attribute": "BarX",
                "semantic_export_dual_attribute": "BarPi",
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
            (output_dir / "solve_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception as error:
            checkpoint_error = {
                "status": "PENDING_QC_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
                "scientifically_accepted": False,
            }
            write_json(
                output_dir / "barrier_checkpoint_error.json",
                checkpoint_error,
            )
            report["barrier_checkpoint"] = checkpoint_error
            report["runtime_memory"] = memory_monitor.snapshot()
            preserved = preserve_stage_a(
                artifacts,
                data,
                config,
                output_dir,
                report,
                snapshot=not raw_checkpoint_saved,
            )
            write_json(
                output_dir / "preservation_runtime_memory.json",
                memory_monitor.stop(),
            )
            finalize_result_manifest(output_dir, config)
            print(json.dumps(preserved, ensure_ascii=False, indent=2))
            raise SystemExit(2)
    export_state = False
    state_export_requested = False
    qc = None
    if (
        args.engineering_relaxed_barrier_analysis
        and engineering_checkpoint_completed
        and artifacts.model.SolCount
    ):
        engineering_dir = output_dir / "engineering_macro_analysis"
        try:
            engineering_qc, engineering_qc_error = (
                export_engineering_relaxed_macro_analysis(
                    artifacts,
                    data,
                    config,
                    engineering_dir,
                    master_exporter=export_master_solution,
                    operational_exporter=export_operational_solution,
                    summary_exporter=export_result_summary,
                )
            )
            engineering_contract = {
                "schema_version": "cispo_engineering_relaxed_barrier_analysis_v1",
                "generated_at": datetime.now().astimezone().isoformat(),
                "scientifically_accepted": False,
                "result_manifest_created": False,
                "planning_state_created": False,
                "basis_created": False,
                "result_use": scope_report["result_use"],
                "solver_status": report.get("status"),
                "barrier_status_code": barrier_status_code,
                "solver_profile_id": report.get("solver_profile_id"),
                "solver_parameters": report.get("solver_parameters"),
                "solution_quality": report.get("solution_quality"),
                "strict_solver_acceptance_status": report.get(
                    "solution_contract", {}
                ).get("acceptance_status"),
                "raw_physical_qc_status": (
                    engineering_qc.get("status")
                    if engineering_qc is not None
                    else "STRICT_PHYSICAL_QC_EXPORT_FAILED"
                ),
                "raw_hard_check_count": (
                    len(engineering_qc.get("hard_checks", {}))
                    if engineering_qc is not None
                    else None
                ),
                "raw_physical_qc_error": engineering_qc_error,
                "analysis_directory": str(engineering_dir),
                "interpretation": (
                    "Engineering macro-comparison evidence only. Values must be "
                    "compared against a strict accepted root before selecting a "
                    "production tolerance and cannot anchor a planning sequence."
                ),
            }
            contract_path = engineering_dir / "engineering_analysis_contract.json"
            contract_path.write_text(
                json.dumps(engineering_contract, ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            report["engineering_relaxed_barrier_analysis"] = {
                "status": "EXPORTED_UNACCEPTED_ENGINEERING_ANALYSIS",
                "scientifically_accepted": False,
                "path": str(contract_path),
                "raw_physical_qc_status": engineering_contract[
                    "raw_physical_qc_status"
                ],
            }
        except Exception as error:
            analysis_error = {
                "status": "ENGINEERING_RELAXED_ANALYSIS_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
                "scientifically_accepted": False,
            }
            (output_dir / "engineering_relaxed_analysis_error.json").write_text(
                json.dumps(analysis_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["engineering_relaxed_barrier_analysis"] = analysis_error
    # Explicit engineering runs, failed strict Stage A solves, and tainted
    # upstream candidate sequences are preserved but never scientifically
    # accepted. A strict nonbasic Stage A continues to physical QC below.
    if (
        args.engineering_barrier_checkpoint_only
        or (nonbasic_primal_dual_requested and not solver_solution_accepted)
        or planning_state.metadata.get("candidate_unaccepted")
    ):
        if direct_nonbasic_scientific_acceptance:
            report["stage_a_completion_status"] = (
                "STAGE_A_COMPLETED_REVIEW_REQUIRED"
                if raw_checkpoint_saved
                else "STAGE_A_INFRASTRUCTURE_FAILED"
            )
        report["runtime_memory"] = memory_monitor.snapshot()
        preserved = preserve_stage_a(
            semantic_artifacts,
            data,
            config,
            output_dir,
            report,
            snapshot=not raw_checkpoint_saved,
        )
        write_json(output_dir / "preservation_runtime_memory.json", memory_monitor.stop())
        finalize_result_manifest(output_dir, config)
        print(json.dumps(preserved, ensure_ascii=False, indent=2))
        # Success here means complete preservation, never scientific acceptance.
        if preserved["status"] != "COMPLETE":
            raise SystemExit(2)
        if (
            args.engineering_barrier_checkpoint_only
            and engineering_checkpoint_completed
        ):
            return
        raise SystemExit(2)
    if (
        artifacts.model.SolCount
        and solver_solution_accepted
        and not args.engineering_barrier_checkpoint_only
    ):
        try:
            master_qc = export_master_solution(
                semantic_artifacts,
                data,
                output_dir,
                enforce_qc=not nonbasic_primal_dual_requested,
            )
            qc = export_operational_solution(
                semantic_artifacts,
                data,
                config,
                output_dir,
                enforce_qc=not nonbasic_primal_dual_requested,
            )
            if nonbasic_primal_dual_requested:
                annotate_dual_publication_status(output_dir, report)
            if nonbasic_primal_dual_requested:
                master_qc_pass = load_center_physical_qc_pass(master_qc)
                qc["load_center_physical_qc"] = master_qc
                qc.setdefault("hard_checks", {})[
                    "load_center_annual_capacity_link_physical_units"
                ] = master_qc_pass
                if not master_qc_pass:
                    qc["status"] = "FAIL"
                (output_dir / "solution_qc.json").write_text(
                    json.dumps(
                        qc,
                        ensure_ascii=False,
                        indent=2,
                        allow_nan=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            export_result_summary(
                semantic_artifacts, data, config, output_dir
            )
        except Exception as error:
            semantic_error = {
                "status": "SEMANTIC_EXPORT_FAILED_PRESERVED_UNACCEPTED",
                "error_type": type(error).__name__,
                "error": str(error),
                "scientifically_accepted": False,
            }
            write_json(output_dir / "semantic_export_error.json", semantic_error)
            report["semantic_export_error"] = semantic_error
            report["solution_export_status"] = semantic_error["status"]
            report["runtime_memory"] = memory_monitor.snapshot()
            preserved = preserve_stage_a(
                semantic_artifacts,
                data,
                config,
                output_dir,
                report,
                snapshot=not raw_checkpoint_saved,
            )
            write_json(
                output_dir / "preservation_runtime_memory.json",
                memory_monitor.stop(),
            )
            finalize_result_manifest(output_dir, config)
            print(json.dumps(preserved, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        state_export_requested = bool(
            (not test_only or args.export_diagnostic_state)
            and report["status"] == "OPTIMAL"
            and report.get("solution_contract", {}).get(
                "acceptance_status"
            ) == "PASS"
            and qc["status"] == "PASS"
            and mga_request is None
        )
        export_state = bool(
            state_export_requested
            and not nonbasic_primal_dual_requested
            and (
                not args.primal_dual_checkpoint_in
                or args.allow_deferred_crossover_planning_state
            )
        )
        if nonbasic_primal_dual_requested and not (
            args.allow_nonbasic_planning_state
        ):
            report["planning_state_export_status"] = (
                "NOT_REQUESTED_NONBASIC_STATE_REQUIRES_EXPLICIT_SEQUENCE_POLICY"
            )
        elif nonbasic_primal_dual_requested and state_export_requested:
            report["planning_state_export_status"] = (
                "PENDING_ACCEPTED_BARRIER_CHECKPOINT"
            )
        if (
            args.primal_dual_checkpoint_in
            and state_export_requested
            and not args.allow_deferred_crossover_planning_state
        ):
            report["planning_state_export_status"] = (
                "NOT_EXPORTED_POSTHOC_CROSSOVER_ANALYSIS_DERIVATIVE"
            )
        elif (
            args.primal_dual_checkpoint_in
            and state_export_requested
            and args.allow_deferred_crossover_planning_state
        ):
            report["planning_state_export_status"] = (
                "ACCEPTED_STAGE_B_BASIC_CAPACITY_STATE"
            )
        if mga_request is not None:
            report["solver_secondary_objective_value_gw"] = report[
                "objective_value_million_cny"
            ]
            report["objective_value_million_cny"] = qc["objective_value_million_cny"]
            report["mga"] = qc["mga"]
            (output_dir / "mga_run.json").write_text(
                json.dumps(qc["mga"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        report["solution_qc_status"] = qc["status"]
        report["solution_qc_path"] = str(output_dir / "solution_qc.json")
        report["solution_export_status"] = "COMPLETE"
    elif artifacts.model.SolCount and args.engineering_barrier_checkpoint_only:
        report["solution_export_status"] = (
            "SKIPPED_ENGINEERING_BARRIER_CHECKPOINT_ONLY"
        )
    elif artifacts.model.SolCount:
        report["solution_export_status"] = (
            "SKIPPED_UNACCEPTED_SOLVER_RESULT"
        )
    if (
        nonbasic_primal_dual_requested
        and qc is not None
        and (
            qc.get("status") != "PASS"
            or not qc_hard_checks_are_strictly_true(qc)
        )
    ):
        if direct_nonbasic_scientific_acceptance:
            report["stage_a_completion_status"] = (
                "STAGE_A_COMPLETED_REVIEW_REQUIRED"
            )
        report["solution_export_status"] = (
            "PRESERVED_UNACCEPTED_ORIGINAL_UNIT_QC_FAIL"
        )
        report["runtime_memory"] = memory_monitor.snapshot()
        preserved = preserve_stage_a(
            semantic_artifacts,
            data,
            config,
            output_dir,
            report,
            snapshot=not raw_checkpoint_saved,
        )
        write_json(
            output_dir / "preservation_runtime_memory.json",
            memory_monitor.stop(),
        )
        finalize_result_manifest(output_dir, config)
        print(json.dumps(preserved, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    if primary_checkpoint_requested and qc is not None and qc.get("status") == "PASS":
        checkpoint_promoted = False
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                promote_pending_qc_checkpoint,
            )

            checkpoint = promote_pending_qc_checkpoint(
                output_dir,
                solve_report=report,
                solution_qc=qc,
            )
            checkpoint_promoted = True
            report["barrier_checkpoint"] = {
                "status": checkpoint["checkpoint_status"],
                "scientifically_accepted": True,
                "deferred_crossover_eligible": True,
                "stage_b_required": False,
                "semantic_export_primal_attribute": "BarX",
                "semantic_export_dual_attribute": "BarPi",
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
            if direct_nonbasic_scientific_acceptance:
                report["stage_a_completion_status"] = (
                    "STAGE_A_PRIMAL_FINAL_ACCEPTED"
                )
                report["scientifically_accepted"] = True
            # Persist the accepted solver/QC/checkpoint milestone before any
            # planning-state, dashboard, catalog, or presentation packaging.
            # A later packaging failure must never obscure the costly accepted
            # numerical evidence or silently rewrite it as unaccepted.
            write_strict_json_atomic(
                output_dir / "solve_report.json",
                report,
            )
        except Exception as error:
            if checkpoint_promoted:
                try:
                    finalization_error = persist_postsolve_finalization_error(
                        output_dir,
                        failed_stage="accepted_checkpoint_solve_report",
                        error=error,
                        report=report,
                    )
                except Exception as sidecar_error:
                    print(
                        "Failed to persist finalization_error.json: "
                        + repr(sidecar_error),
                        file=sys.stderr,
                    )
                    finalization_error = {
                        "status": "POST_SOLVE_FINALIZATION_FAILED",
                        "failed_stage": "accepted_checkpoint_solve_report",
                        "error_type": type(error).__name__,
                        "error": str(error),
                        "accepted_checkpoint_retained": True,
                    }
                print(
                    json.dumps(
                        finalization_error,
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                raise SystemExit(2) from error
            checkpoint_error = {
                "status": "PRIMARY_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
                "scientifically_accepted": False,
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
            report["solution_export_status"] = (
                "PRESERVED_UNACCEPTED_CHECKPOINT_PROMOTION_FAILED"
            )
            report["runtime_memory"] = memory_monitor.snapshot()
            preserved = preserve_stage_a(
                # Promotion can fail because the persisted pending vectors are
                # unreadable or no longer match their checksums.  Re-read the
                # live solver model and create an independent snapshot instead
                # of treating the suspect checkpoint as complete preservation.
                artifacts,
                data,
                config,
                output_dir,
                report,
                snapshot=True,
            )
            write_json(
                output_dir / "preservation_runtime_memory.json",
                memory_monitor.stop(),
            )
            finalize_result_manifest(output_dir, config)
            print(json.dumps(preserved, ensure_ascii=False, indent=2))
            raise SystemExit(2)
    if (
        state_export_requested
        and nonbasic_primal_dual_requested
        and args.allow_nonbasic_planning_state
    ):
        checkpoint_status = report.get("barrier_checkpoint", {}).get("status")
        export_state = bool(
            checkpoint_status == "ACCEPTED_PRIMARY_BARRIER_SOLUTION"
        )
        report["planning_state_export_status"] = (
            "ACCEPTED_NONBASIC_BARRIER_CAPACITY_STATE"
            if export_state
            else "BLOCKED_MISSING_ACCEPTED_BARRIER_CHECKPOINT"
        )
    if export_state:
        report["planning_state_path"] = str(output_dir / "planning_state")
    manifest_valid = False
    finalization_stage = "runtime_memory"
    try:
        report["runtime_memory"] = memory_monitor.stop()
        finalization_stage = "warm_start_basis"
        if (
            args.export_warm_start_basis
            and qc is not None
            and report["status"] == "OPTIMAL"
            and qc["status"] == "PASS"
        ):
            from cispo_model.basis_reuse import export_warm_start_basis

            report["warm_start_basis"] = export_warm_start_basis(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                solution_qc=qc,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
            )
        finalization_stage = "scientific_solver_artifacts"
        if (
            args.export_scientific_solver_artifacts
            and qc is not None
            and report["status"] == "OPTIMAL"
            and qc["status"] == "PASS"
        ):
            from cispo_model.solver_artifacts import (
                export_scientific_base_solver_artifacts,
            )

            report["scientific_solver_artifacts"] = (
                export_scientific_base_solver_artifacts(
                    artifacts.model,
                    config,
                    output_dir,
                    solve_report=report,
                    solution_qc=qc,
                    result_use=scope_report["result_use"],
                )
            )
        if qc is not None:
            report["result_manifest_path"] = str(
                output_dir / "result_manifest.json"
            )
        finalization_stage = "solve_report"
        write_strict_json_atomic(
            output_dir / "solve_report.json",
            report,
        )
        finalization_stage = "constraint_family_audit"
        if structure_audit is not None:
            from cispo_model.solver_audit import parse_gurobi_log

            structure_audit["solver_log_global"] = parse_gurobi_log(
                (output_dir / "gurobi.log").read_text(
                    encoding="utf-8", errors="replace"
                )
            )
            structure_audit["solve_summary"] = {
                "status": report.get("status"),
                "runtime_seconds": report.get("runtime_seconds"),
                "objective_value_million_cny": report.get(
                    "objective_value_million_cny"
                ),
                "peak_process_tree_rss_gib": report.get(
                    "runtime_memory", {}
                ).get("peak_process_tree_rss_gib"),
            }
            structure_audit_path.write_text(
                json.dumps(
                    structure_audit,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )
                + "\n",
                encoding="utf-8",
            )
        finalization_stage = "planning_state"
        if export_state:
            export_solution_planning_state(
                semantic_artifacts,
                data,
                config,
                output_dir,
                state_use=scope_report["result_use"],
                retain_all_capacity_deltas=(
                    direct_nonbasic_scientific_acceptance
                ),
            )
        if qc is not None:
            finalization_stage = "result_dashboard"
            build_result_dashboard(output_dir)
            finalization_stage = "output_catalog"
            write_output_catalog(output_dir)
            finalization_stage = "result_manifest"
            finalize_result_manifest(output_dir, config)
            manifest_valid, manifest_failures = validate_result_manifest(
                output_dir
            )
            if not manifest_valid:
                raise RuntimeError(
                    "Final result manifest validation failed: "
                    + "; ".join(manifest_failures)
                )
    except Exception as error:
        try:
            finalization_error = persist_postsolve_finalization_error(
                output_dir,
                failed_stage=finalization_stage,
                error=error,
                report=report,
            )
        except Exception as sidecar_error:
            print(
                "Failed to persist finalization_error.json: "
                + repr(sidecar_error),
                file=sys.stderr,
            )
            finalization_error = {
                "status": "POST_SOLVE_FINALIZATION_FAILED",
                "failed_stage": finalization_stage,
                "error_type": type(error).__name__,
                "error": str(error),
                "accepted_checkpoint_retained": bool(
                    report.get("barrier_checkpoint", {}).get(
                        "scientifically_accepted"
                    )
                ),
            }
        print(json.dumps(finalization_error, ensure_ascii=False, indent=2))
        raise SystemExit(2) from error
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.engineering_barrier_checkpoint_only:
        if engineering_checkpoint_completed:
            return
        raise SystemExit(2)
    if not solver_result_is_accepted(
        report,
        qc,
        result_manifest_valid=manifest_valid,
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
