#!/usr/bin/env bash
set -uo pipefail

# Run the one authorized 2160 h deferred-Crossover Stage B from the preserved
# Case 1 engineering Barrier checkpoint.  The source is read-only, the target
# roots must be new, and whole-host memory remains protected at 95%.
SERVER_ROOT=${CISPO_SERVER_ROOT:-/home/zz2/National_model_server}
REPO_ROOT=${CISPO_REPO_ROOT:-$SERVER_ROOT/repo}
ENV_FILE=${CISPO_SERVER_ENV:-$SERVER_ROOT/server_env_20260825.sh}
TOOLS_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
EXPECTED_HEAD=${EXPECTED_HEAD:-6065bfba34b76098e86307081323e8545a4d25ac}
SOURCE_TAG=${SOURCE_TAG:-2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1}
TAG=${TAG:-2030_base_2160h_case1_v3_stage_b_20260901_v1}
SOURCE_ROOT=${SOURCE_ROOT:-$SERVER_ROOT/outputs/$SOURCE_TAG}
OUTPUT_ROOT=${OUTPUT_ROOT:-$SERVER_ROOT/outputs/$TAG}
CONTROL_ROOT=${CONTROL_ROOT:-$SERVER_ROOT/run_control/$TAG}
PROFILE=${PROFILE:-config/solver_profiles/large_lp_2160_case1_v3_stage_b_v1.json}
MINIMUM_AVAILABLE_GIB=${MINIMUM_AVAILABLE_GIB:-96}

if [[ ! -f "$ENV_FILE" ]]; then
  printf 'missing server environment: %s\n' "$ENV_FILE" >&2
  exit 90
fi
set -a
source "$ENV_FILE"
set +a
PYTHON=${CISPO_PYTHON:-$SERVER_ROOT/envs/cispo-2030-v1/bin/python}

fail() {
  local code=$1
  shift
  if [[ -n "${event_log:-}" ]]; then
    printf '%s refuse_%s\n' "$(date --iso-8601=seconds)" "$*" >>"$event_log"
  fi
  printf 'refuse: %s\n' "$*" >&2
  exit "$code"
}

[[ ! -e "$OUTPUT_ROOT" && ! -e "$CONTROL_ROOT" ]] || \
  fail 91 "existing_target output=$OUTPUT_ROOT control=$CONTROL_ROOT"
mkdir -p "$CONTROL_ROOT"
event_log="$CONTROL_ROOT/events.log"
cd "$REPO_ROOT"

actual_head=$(git rev-parse HEAD)
[[ "$actual_head" == "$EXPECTED_HEAD" ]] || \
  fail 92 "head expected=$EXPECTED_HEAD actual=$actual_head"
git status --short >"$CONTROL_ROOT/git_status.txt"
[[ ! -s "$CONTROL_ROOT/git_status.txt" ]] || fail 93 dirty_checkout
printf '%s\n' "$actual_head" >"$CONTROL_ROOT/git_head.txt"
[[ -f "$PROFILE" ]] || fail 94 "missing_profile path=$PROFILE"
[[ -f "$SOURCE_ROOT/barrier_checkpoint/barrier_checkpoint_manifest.json" ]] || \
  fail 95 "missing_source_checkpoint path=$SOURCE_ROOT"
if pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py|[r]ecover_historical_stage_a.py|[r]un_historical_stage_a_recovery.sh' \
    >"$CONTROL_ROOT/preexisting_solver_processes.txt"; then
  fail 96 preexisting_solver
fi

read -r available_gib swap_in swap_out psi_some < <(
  available=$(awk '/MemAvailable:/ {printf "%.3f", $2/1048576}' /proc/meminfo)
  read -r si so < <(vmstat 1 2 | tail -1 | awk '{print $7, $8}')
  psi=$(awk '/^some / {for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/memory)
  printf '%s %s %s %s\n' "$available" "$si" "$so" "$psi"
)
"$PYTHON" - "$available_gib" "$MINIMUM_AVAILABLE_GIB" "$swap_in" "$swap_out" "$psi_some" <<'PY'
import sys
available, minimum, swap_in, swap_out, psi = map(float, sys.argv[1:])
raise SystemExit(
    0 if available >= minimum and swap_in == 0 and swap_out == 0 and psi == 0 else 1
)
PY
[[ $? -eq 0 ]] || fail 97 "resource_gate available_gib=$available_gib si=$swap_in so=$swap_out psi=$psi_some"

"$PYTHON" scripts/check_barrier_checkpoint_eligibility.py \
  "$SOURCE_ROOT/barrier_checkpoint/barrier_checkpoint_manifest.json" \
  --output "$CONTROL_ROOT/source_checkpoint_eligibility.json"
[[ $? -eq 0 ]] || fail 98 source_checkpoint_ineligible

snapshot() {
  local label=$1
  {
    printf 'timestamp='; date --iso-8601=seconds
    printf 'label=%s\n' "$label"
    free -h
    vmstat 1 3
    cat /proc/pressure/memory
    cat /proc/pressure/io
    nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu \
      --format=csv,noheader,nounits 2>/dev/null || true
    ps -eo user:16,pid,ppid,pgid,%cpu,%mem,rss,etimes,comm --sort=-rss | sed -n '1,25p'
  } >"$CONTROL_ROOT/resource_${label}.txt" 2>&1
}

snapshot before
printf '%s start source=%s profile=%s output=%s available_gib=%s\n' \
  "$(date --iso-8601=seconds)" "$SOURCE_ROOT" "$PROFILE" "$OUTPUT_ROOT" \
  "$available_gib" >>"$event_log"

setsid /usr/bin/time -v -o "$CONTROL_ROOT/time.txt" \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --planning-year 2030 \
    --diagnostic-hours 2160 \
    --diagnostic-start-hour 2880 \
    --scenario-config config/scenarios/base.json \
    --solver-config "$PROFILE" \
    --primal-dual-checkpoint-in "$SOURCE_ROOT" \
    --allow-primal-dual-crossover \
    --allow-engineering-barrier-checkpoint \
    --output-dir "$OUTPUT_ROOT" \
    >"$CONTROL_ROOT/stdout.log" 2>"$CONTROL_ROOT/stderr.log" &
run_pid=$!
printf '%s\n' "$run_pid" >"$CONTROL_ROOT/run.pid"

test -f "$TOOLS_ROOT/monitor_case_resources.py" || fail 99 missing_resource_monitor
"$PYTHON" "$TOOLS_ROOT/monitor_case_resources.py" \
  --process-group "$run_pid" --output-dir "$CONTROL_ROOT" --gpu-device 0 \
  --interval 2 --stop-file "$CONTROL_ROOT/telemetry.stop" \
  >"$CONTROL_ROOT/telemetry.stdout.log" 2>"$CONTROL_ROOT/telemetry.stderr.log" &
telemetry_pid=$!
printf '%s\n' "$telemetry_pid" >"$CONTROL_ROOT/telemetry.pid"

printf 'timestamp\tmem_total_kib\tmem_available_kib\thost_used_percent\tswap_used_kib\tpsi_some_avg10\tprocess_group_rss_kib\n' \
  >"$CONTROL_ROOT/resource_monitor.tsv"
guard_triggered=0
while kill -0 "$run_pid" 2>/dev/null; do
  read -r mem_total mem_available swap_total swap_free < <(
    awk '
      /MemTotal:/ {mt=$2}
      /MemAvailable:/ {ma=$2}
      /SwapTotal:/ {st=$2}
      /SwapFree:/ {sf=$2}
      END {print mt, ma, st, sf}
    ' /proc/meminfo
  )
  used_percent=$("$PYTHON" - "$mem_total" "$mem_available" <<'PY'
import sys
total, available = map(float, sys.argv[1:])
print(f"{100.0 * (total - available) / total:.6f}")
PY
  )
  psi=$(awk '/^some / {for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/memory)
  group_rss=$(ps -eo pgid=,rss= | awk -v pg="$run_pid" '$1==pg {sum+=$2} END {print sum+0}')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date --iso-8601=seconds)" "$mem_total" "$mem_available" "$used_percent" \
    "$((swap_total-swap_free))" "$psi" "$group_rss" >>"$CONTROL_ROOT/resource_monitor.tsv"
  "$PYTHON" - "$used_percent" <<'PY'
import sys
raise SystemExit(0 if float(sys.argv[1]) >= 95.0 else 1)
PY
  if [[ $? -eq 0 ]]; then
    guard_triggered=1
    printf '%s host_memory_guard_triggered used_percent=%s\n' \
      "$(date --iso-8601=seconds)" "$used_percent" >>"$event_log"
    kill -TERM -- "-$run_pid" 2>/dev/null || true
    break
  fi
  sleep 2
done

set +e
wait "$run_pid"
runner_rc=$?
touch "$CONTROL_ROOT/telemetry.stop"
wait "$telemetry_pid"
telemetry_rc=$?
set +e
printf '%s\n' "$runner_rc" >"$CONTROL_ROOT/return_code.txt"
printf '%s\n' "$telemetry_rc" >"$CONTROL_ROOT/telemetry_return_code.txt"

audit_rc=42
if (( runner_rc == 0 )); then
  PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" - \
    "$OUTPUT_ROOT" >"$CONTROL_ROOT/strict_terminal_audit.json" <<'PY'
import json
import sys
from pathlib import Path

from cispo_model.io_contract import validate_input_manifest, validate_result_manifest

root = Path(sys.argv[1])
payload = {
    "schema_version": "cispo_deferred_crossover2_2160_terminal_audit_v1",
    "strict_test_result_accepted": False,
    "scientifically_accepted": False,
    "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
}
exit_code = 41
try:
    solve = json.loads((root / "solve_report.json").read_text(encoding="utf-8"))
    qc = json.loads((root / "solution_qc.json").read_text(encoding="utf-8"))
    start = json.loads((root / "primal_dual_start_input.json").read_text(encoding="utf-8"))
    hard = qc.get("hard_checks")
    hard_pass = bool(isinstance(hard, dict) and hard and all(value is True for value in hard.values()))
    result_valid, result_failures = validate_result_manifest(root)
    input_valid, input_failures = validate_input_manifest(root / "input_manifest.csv")
    accepted = bool(
        solve.get("status") == "OPTIMAL"
        and solve.get("solution_contract", {}).get("acceptance_status") == "PASS"
        and qc.get("status") == "PASS"
        and hard_pass
        and result_valid
        and input_valid
        and start.get("lp_warm_start") == 2
        and start.get("engineering_checkpoint_explicitly_allowed") is True
    )
    payload.update({
        "strict_test_result_accepted": accepted,
        "solver_status": solve.get("status"),
        "solver_acceptance_status": solve.get("solution_contract", {}).get("acceptance_status"),
        "solution_qc_status": qc.get("status"),
        "hard_check_count": len(hard) if isinstance(hard, dict) else None,
        "hard_checks_all_true": hard_pass,
        "result_manifest_valid": result_valid,
        "result_manifest_failures": result_failures,
        "input_manifest_valid": input_valid,
        "input_manifest_failures": input_failures,
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
fi
printf '%s\n' "$audit_rc" >"$CONTROL_ROOT/strict_terminal_audit_rc.txt"
snapshot after
printf '%s end runner_rc=%s audit_rc=%s telemetry_rc=%s host_guard_triggered=%s\n' \
  "$(date --iso-8601=seconds)" "$runner_rc" "$audit_rc" "$telemetry_rc" \
  "$guard_triggered" >>"$event_log"

(( runner_rc == 0 )) || exit "$runner_rc"
(( audit_rc == 0 )) || exit "$audit_rc"
printf '%s validation_complete\n' "$(date --iso-8601=seconds)" >>"$event_log"
