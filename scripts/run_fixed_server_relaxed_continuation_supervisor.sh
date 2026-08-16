#!/usr/bin/env bash
set -uo pipefail

# Wait for the exact strict reference, validate it, then hand off to the
# strictly serial relaxed campaign.  Every path is explicit so the supervisor
# can be copied to an isolated run-control root without changing an active
# checkout.
REPO_ROOT=${REPO_ROOT:-/data/zz2/National_model/repo}
PYTHON=${CISPO_PYTHON:-/home/zz2/.local/envs/cispo-2030/bin/python}
CONTROL=${CONTROL:?CONTROL is required}
NEW=${NEW:?NEW is required}
REF_CONTROL=${REF_CONTROL:?REF_CONTROL is required}
REF_OUT=${REF_OUT:?REF_OUT is required}
OLD=${OLD:?OLD is required}
CAMPAIGN_SCRIPT=${CAMPAIGN_SCRIPT:?CAMPAIGN_SCRIPT is required}
AUDIT_SCRIPT=${AUDIT_SCRIPT:?AUDIT_SCRIPT is required}
POLL_SECONDS=${POLL_SECONDS:-300}
event_log="$CONTROL/supervisor_events.log"

printf '%s supervisor_start reference_pid=%s\n' \
  "$(date --iso-8601=seconds)" "$(cat "$REF_CONTROL/pid")" >>"$event_log"
refpid=$(cat "$REF_CONTROL/pid")
while kill -0 "$refpid" 2>/dev/null; do
  printf '%s waiting_reference pid=%s\n' \
    "$(date --iso-8601=seconds)" "$refpid" >>"$event_log"
  sleep "$POLL_SECONDS"
done
printf '%s reference_wrapper_exited\n' \
  "$(date --iso-8601=seconds)" >>"$event_log"

if [[ ! -f "$REF_CONTROL/wrapper_exit_code.txt" ]]; then
  printf '%s stop_missing_wrapper_rc\n' \
    "$(date --iso-8601=seconds)" >>"$event_log"
  exit 20
fi
ref_rc=$(tr -d '\r\n' <"$REF_CONTROL/wrapper_exit_code.txt")
if [[ "$ref_rc" != 0 ]]; then
  printf '%s stop_reference_rc=%s\n' \
    "$(date --iso-8601=seconds)" "$ref_rc" >>"$event_log"
  exit 21
fi
if [[ -s "$REF_CONTROL/stderr.log" ]]; then
  printf '%s stop_reference_stderr_nonempty\n' \
    "$(date --iso-8601=seconds)" >>"$event_log"
  exit 22
fi
for name in \
  solve_report.json solution_qc.json result_manifest.json \
  run_identity.json input_manifest.csv; do
  if [[ ! -f "$REF_OUT/$name" ]]; then
    printf '%s stop_reference_missing=%s\n' \
      "$(date --iso-8601=seconds)" "$name" >>"$event_log"
    exit 23
  fi
done

cd "$REPO_ROOT"
"$PYTHON" - "$REF_OUT" >"$CONTROL/strict_reference_contract.json" <<'PY'
import json
import sys
from pathlib import Path

from cispo_model.io_contract import validate_input_manifest, validate_result_manifest

root = Path(sys.argv[1])
payload = {
    "schema": "cispo_strict_exact_ab_reference_contract_v2",
    "accepted_for_exact_ab_reference": False,
}
exit_code = 24
try:
    solve = json.loads((root / "solve_report.json").read_text(encoding="utf-8"))
    qc = json.loads((root / "solution_qc.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / "result_manifest.json").read_text(encoding="utf-8")
    )
    hard_checks = qc.get("hard_checks")
    hard_count = len(hard_checks) if isinstance(hard_checks, dict) else None
    hard_pass = bool(
        isinstance(hard_checks, dict)
        and hard_count == 58
        and all(value is True for value in hard_checks.values())
    )
    shape_failures = []
    rows = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or not rows:
        shape_failures.append("files_not_nonempty_list")
    else:
        seen = set()
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                shape_failures.append(f"row_{index}_not_object")
                continue
            relative = row.get("path")
            if (
                not isinstance(relative, str)
                or not relative
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                shape_failures.append(f"row_{index}_unsafe_path")
            elif relative in seen:
                shape_failures.append(f"row_{index}_duplicate_path")
            else:
                seen.add(relative)
            try:
                recorded_bytes = int(row.get("bytes"))
            except (TypeError, ValueError):
                recorded_bytes = -1
            if recorded_bytes < 0:
                shape_failures.append(f"row_{index}_invalid_bytes")
            recorded_sha = row.get("sha256")
            if (
                not isinstance(recorded_sha, str)
                or len(recorded_sha) != 64
                or any(
                    character not in "0123456789abcdefABCDEF"
                    for character in recorded_sha
                )
            ):
                shape_failures.append(f"row_{index}_invalid_sha256")
    result_valid, result_failures = validate_result_manifest(root)
    input_valid, input_failures = validate_input_manifest(
        root / "input_manifest.csv"
    )
    accepted = bool(
        solve.get("status") == "OPTIMAL"
        and qc.get("status") == "PASS"
        and hard_pass
        and not shape_failures
        and result_valid
        and input_valid
    )
    payload.update(
        {
            "accepted_for_exact_ab_reference": accepted,
            "solver_status": solve.get("status"),
            "solution_qc_status": qc.get("status"),
            "hard_check_count": hard_count,
            "hard_checks_all_true": hard_pass,
            "result_manifest_file_count": (
                len(rows) if isinstance(rows, list) else None
            ),
            "result_manifest_shape_failures": shape_failures,
            "result_manifest_valid": result_valid,
            "result_manifest_failures": result_failures,
            "input_manifest_valid": input_valid,
            "input_manifest_failures": input_failures,
        }
    )
    if accepted:
        exit_code = 0
except Exception as error:
    payload["validator_exception"] = f"{type(error).__name__}: {error}"
print(json.dumps(payload, ensure_ascii=False, indent=2))
raise SystemExit(exit_code)
PY
validator_rc=$?
if (( validator_rc != 0 )); then
  printf '%s stop_reference_contract_rc=%s\n' \
    "$(date --iso-8601=seconds)" "$validator_rc" >>"$event_log"
  exit "$validator_rc"
fi

if [[ -e "$NEW" ]]; then
  printf '%s stop_new_output_root_exists=%s\n' \
    "$(date --iso-8601=seconds)" "$NEW" >>"$event_log"
  exit 25
fi
mkdir -p "$NEW"
for tag in \
  base_744h_bctol5e2 \
  base_744h_bctol1e2 \
  base_744h_bctol1e2_numeric1; do
  if [[ ! -f "$OLD/$tag/engineering_macro_analysis/engineering_analysis_contract.json" ]]; then
    printf '%s stop_candidate_missing=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" >>"$event_log"
    exit 26
  fi
  ln -s "$OLD/$tag" "$NEW/$tag"
done

printf '%s exact_ab_campaign_start\n' \
  "$(date --iso-8601=seconds)" >>"$event_log"
exec env \
  REPO_ROOT="$REPO_ROOT" \
  CISPO_PYTHON="$PYTHON" \
  OUTPUT_BASE="$NEW" \
  CONTROL_ROOT="$CONTROL/campaign" \
  REFERENCE_ROOT="$REF_OUT" \
  AUDIT_SCRIPT="$AUDIT_SCRIPT" \
  CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1 \
  CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf \
  CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse \
  CISPO_WAVE_ROOT=/data/zz2/National_model/data/wave_energy_20260727 \
  bash "$CAMPAIGN_SCRIPT"
