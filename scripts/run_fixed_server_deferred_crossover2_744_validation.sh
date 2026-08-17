#!/usr/bin/env bash
set -uo pipefail

# Rebuild the exact Base/744 LP and validate that a saved relaxed Barrier
# checkpoint can seed an independently accepted Crossover=2 result.  The
# source is never overwritten and the target cannot export planning state.
REPO_ROOT=${REPO_ROOT:-/data/zz2/National_model/repo}
PYTHON=${CISPO_PYTHON:-/home/zz2/.local/envs/cispo-2030/bin/python}
SOURCE_ROOT=${SOURCE_ROOT:-/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1/base_744h_bctol1e2_numeric1}
REFERENCE_ROOT=${REFERENCE_ROOT:-/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2}
OUTPUT_ROOT=${OUTPUT_ROOT:-/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v1}
CONTROL_ROOT=${CONTROL_ROOT:-/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v1}
PROFILE=${PROFILE:-config/solver_profiles/barrier_16_deferred_crossover2_744_validation_v1.json}
EXPECTED_HEAD=${EXPECTED_HEAD:-}
MINIMUM_AVAILABLE_GIB=${MINIMUM_AVAILABLE_GIB:-64}

export CISPO_DATA_ROOT=${CISPO_DATA_ROOT:-/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1}
export CISPO_CF_ROOT=${CISPO_CF_ROOT:-/data/zz2/National_model/data/hourly_cf}
export CISPO_HYDRO_ROOT=${CISPO_HYDRO_ROOT:-/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse}
export CISPO_RAW_GRFR_ROOT=${CISPO_RAW_GRFR_ROOT:-/data/zz2/National_model/data/grfr_raw_2019}
export CISPO_WAVE_ROOT=${CISPO_WAVE_ROOT:-/data/zz2/National_model/data/wave_energy_20260727}

mkdir -p "$CONTROL_ROOT"
event_log="$CONTROL_ROOT/events.log"
cd "$REPO_ROOT"

fail() {
  local code=$1
  shift
  printf '%s refuse_%s\n' "$(date --iso-8601=seconds)" "$*" >>"$event_log"
  exit "$code"
}

record_resources() {
  local label=$1
  {
    printf 'timestamp='; date --iso-8601=seconds
    printf 'label=%s\n' "$label"
    git rev-parse HEAD
    git status --short
    free -h
    vmstat 1 3
    cat /proc/pressure/memory
    ps -eo pid,ppid,%cpu,%mem,rss,etimes,args --sort=-rss | head -20
  } >"$CONTROL_ROOT/resource_${label}.txt" 2>&1
}

resource_safe() {
  local available si so psi
  available=$(awk '/MemAvailable:/ {printf "%.3f", $2/1048576}' /proc/meminfo)
  read -r si so < <(vmstat 1 2 | tail -1 | awk '{print $7, $8}')
  psi=$(awk '/^some / {for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/memory)
  "$PYTHON" - "$available" "$MINIMUM_AVAILABLE_GIB" "$si" "$so" "$psi" <<'PY'
import sys
available, minimum, si, so, psi = map(float, sys.argv[1:])
raise SystemExit(0 if available >= minimum and si == 0 and so == 0 and psi == 0 else 1)
PY
}

if [[ -n "$EXPECTED_HEAD" && "$(git rev-parse HEAD)" != "$EXPECTED_HEAD" ]]; then
  fail 90 "head expected=$EXPECTED_HEAD actual=$(git rev-parse HEAD)"
fi
[[ -z "$(git status --porcelain)" ]] || fail 91 dirty_checkout
[[ ! -e "$OUTPUT_ROOT" ]] || fail 92 "existing_output path=$OUTPUT_ROOT"
[[ -f "$REPO_ROOT/$PROFILE" ]] || fail 93 "missing_profile path=$PROFILE"
[[ -f "$SOURCE_ROOT/barrier_checkpoint/barrier_checkpoint_manifest.json" ]] || \
  fail 94 "missing_source_checkpoint path=$SOURCE_ROOT"
[[ -f "$REFERENCE_ROOT/result_manifest.json" ]] || \
  fail 95 "missing_strict_reference path=$REFERENCE_ROOT"
if pgrep -af 'run_cispo_2030_full_year.py|run_cispo_planning_sequence.py' \
    >"$CONTROL_ROOT/preexisting_solver_processes.txt"; then
  fail 96 preexisting_solver
fi
resource_safe || fail 97 "resources minimum_available_gib=$MINIMUM_AVAILABLE_GIB"

"$PYTHON" scripts/check_barrier_checkpoint_eligibility.py \
  "$SOURCE_ROOT/barrier_checkpoint/barrier_checkpoint_manifest.json" \
  --output "$CONTROL_ROOT/source_checkpoint_eligibility.json"
eligibility_rc=$?
(( eligibility_rc == 0 )) || fail 98 "source_checkpoint_ineligible rc=$eligibility_rc"

record_resources before
printf '%s\n' "$(git rev-parse HEAD)" >"$CONTROL_ROOT/git_head.txt"
printf '%s start source=%s profile=%s output=%s\n' \
  "$(date --iso-8601=seconds)" "$SOURCE_ROOT" "$PROFILE" "$OUTPUT_ROOT" \
  >>"$event_log"

set +e
/usr/bin/time -v -o "$CONTROL_ROOT/time.txt" \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --planning-year 2030 \
    --diagnostic-hours 744 \
    --diagnostic-start-hour 0 \
    --scenario-config config/scenarios/base.json \
    --solver-config "$PROFILE" \
    --primal-dual-checkpoint-in "$SOURCE_ROOT" \
    --allow-primal-dual-crossover \
    --allow-engineering-barrier-checkpoint \
    --allow-compatible-primal-dual-implementation \
    --output-dir "$OUTPUT_ROOT" \
    >"$CONTROL_ROOT/stdout.log" 2>"$CONTROL_ROOT/stderr.log"
runner_rc=$?
printf '%s\n' "$runner_rc" >"$CONTROL_ROOT/return_code.txt"

PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" - \
  "$OUTPUT_ROOT" >"$CONTROL_ROOT/strict_terminal_audit.json" <<'PY'
import json
import sys
from pathlib import Path

from cispo_model.io_contract import validate_input_manifest, validate_result_manifest

root = Path(sys.argv[1])
payload = {
    "schema_version": "cispo_deferred_crossover2_744_terminal_audit_v1",
    "strict_test_result_accepted": False,
    "scientifically_accepted": False,
    "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
}
exit_code = 41
try:
    solve = json.loads((root / "solve_report.json").read_text(encoding="utf-8"))
    qc = json.loads((root / "solution_qc.json").read_text(encoding="utf-8"))
    start = json.loads(
        (root / "primal_dual_start_input.json").read_text(encoding="utf-8")
    )
    hard = qc.get("hard_checks")
    hard_pass = bool(
        isinstance(hard, dict)
        and len(hard) == 58
        and all(value is True for value in hard.values())
    )
    result_valid, result_failures = validate_result_manifest(root)
    input_valid, input_failures = validate_input_manifest(
        root / "input_manifest.csv"
    )
    state_absent = not (root / "planning_state").exists()
    basis_absent = not (root / "warm_start_basis.bas").exists()
    accepted = bool(
        solve.get("status") == "OPTIMAL"
        and solve.get("solution_contract", {}).get("acceptance_status") == "PASS"
        and qc.get("status") == "PASS"
        and hard_pass
        and result_valid
        and input_valid
        and state_absent
        and basis_absent
        and start.get("lp_warm_start") == 2
        and start.get("engineering_checkpoint_explicitly_allowed") is True
    )
    payload.update({
        "strict_test_result_accepted": accepted,
        "solver_status": solve.get("status"),
        "solver_acceptance_status": solve.get("solution_contract", {}).get(
            "acceptance_status"
        ),
        "solution_qc_status": qc.get("status"),
        "hard_check_count": len(hard) if isinstance(hard, dict) else None,
        "hard_checks_all_true": hard_pass,
        "result_manifest_valid": result_valid,
        "result_manifest_failures": result_failures,
        "input_manifest_valid": input_valid,
        "input_manifest_failures": input_failures,
        "planning_state_absent": state_absent,
        "basis_absent": basis_absent,
        "solver_profile_id": solve.get("solver_profile_id"),
        "solver_runtime_seconds": solve.get("runtime_seconds"),
        "barrier_iterations": solve.get("iteration_counts", {}).get("barrier"),
        "simplex_iterations": solve.get("iteration_counts", {}).get("simplex"),
        "objective_value_million_cny": solve.get("objective_value_million_cny"),
        "primal_dual_start": start,
    })
    if accepted:
        exit_code = 0
except Exception as error:
    payload["validator_exception"] = f"{type(error).__name__}: {error}"
print(json.dumps(payload, ensure_ascii=False, indent=2))
raise SystemExit(exit_code)
PY
audit_rc=$?

macro_rc=42
if (( audit_rc == 0 )); then
  PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" \
    scripts/audit_accepted_deferred_crossover_pair.py \
      --candidate-root "$OUTPUT_ROOT" \
      --reference-root "$REFERENCE_ROOT" \
      --output "$CONTROL_ROOT/macro_comparison.json"
  macro_rc=$?
fi
printf '%s\n' "$audit_rc" >"$CONTROL_ROOT/strict_terminal_audit_rc.txt"
printf '%s\n' "$macro_rc" >"$CONTROL_ROOT/macro_comparison_rc.txt"
record_resources after
printf '%s end runner_rc=%s audit_rc=%s macro_rc=%s\n' \
  "$(date --iso-8601=seconds)" "$runner_rc" "$audit_rc" "$macro_rc" \
  >>"$event_log"

(( runner_rc == 0 )) || exit "$runner_rc"
(( audit_rc == 0 )) || exit "$audit_rc"
(( macro_rc == 0 )) || exit "$macro_rc"
printf '%s validation_complete\n' "$(date --iso-8601=seconds)" >>"$event_log"
