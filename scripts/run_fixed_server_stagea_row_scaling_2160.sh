#!/usr/bin/env bash
set -euo pipefail

# Sole fixed-server qualification route: 2160h Base, exact annual-row scaling,
# 32 physical cores, Barrier-only preservation. No Stage B is launched.
SERVER_ROOT=${CISPO_SERVER_ROOT:-/home/zz2/National_model_server}
ENV_FILE=${CISPO_SERVER_ENV:-$SERVER_ROOT/server_env_20260825.sh}
REQUESTED_REPO_ROOT=${CISPO_REPO_ROOT:-}
REQUESTED_PYTHON=${CISPO_PYTHON:-}
REQUESTED_EXPECTED_GIT_SHA=${EXPECTED_GIT_SHA:?EXPECTED_GIT_SHA is required}
readonly REQUESTED_EXPECTED_GIT_SHA
if [[ ! -f "$ENV_FILE" ]]; then
  printf 'missing server environment: %s\n' "$ENV_FILE" >&2
  exit 90
fi
set -a
source "$ENV_FILE"
set +a
EXPECTED_GIT_SHA=$REQUESTED_EXPECTED_GIT_SHA
readonly EXPECTED_GIT_SHA
REPO_ROOT=${REQUESTED_REPO_ROOT:-${CISPO_REPO_ROOT:-$SERVER_ROOT/repo}}
PYTHON=${REQUESTED_PYTHON:-${CISPO_PYTHON:-$SERVER_ROOT/envs/cispo-2030-v1/bin/python}}

HOURS=2160
START_HOUR=2880
SCENARIO=config/scenarios/base.json
SOLVER_PROFILE=config/solver_profiles/barrier_checkpoint_fixed_server_host_memory_95_v2.json
FORMULATION_PROFILE=config/formulation_profiles/annual_capacity_link_rows_8192_v1.json
TAG=${TAG:-2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1}
OUTPUT_ROOT=${OUTPUT_ROOT:-$SERVER_ROOT/outputs/$TAG}
CONTROL_ROOT=${CONTROL_ROOT:-$SERVER_ROOT/run_control/$TAG}
MINIMUM_AVAILABLE_GIB=${MINIMUM_AVAILABLE_GIB:-100}

mkdir -p "$SERVER_ROOT/run_control"
exec 9>"$SERVER_ROOT/run_control/stagea_2160_qualification.lock"
if ! flock -n 9; then
  printf 'refuse concurrent Stage A qualification launcher\n' >&2
  exit 90
fi
canonical_output=$(readlink -m "$OUTPUT_ROOT")
canonical_control=$(readlink -m "$CONTROL_ROOT")
if [[ "$canonical_output" == "$canonical_control" \
   || "$canonical_output" == "$canonical_control"/* \
   || "$canonical_control" == "$canonical_output"/* ]]; then
  printf 'output/control roots must be distinct and non-nested\n' >&2
  exit 91
fi
OUTPUT_ROOT=$canonical_output
CONTROL_ROOT=$canonical_control
if [[ -e "$OUTPUT_ROOT" || -e "$CONTROL_ROOT" ]]; then
  printf 'refuse existing output/control root: %s %s\n' "$OUTPUT_ROOT" "$CONTROL_ROOT" >&2
  exit 91
fi
mkdir -p "$CONTROL_ROOT"
if [[ ! -d "$REPO_ROOT" || ! -x "$PYTHON" ]]; then
  printf 'missing repository or Python runtime: %s %s\n' \
    "$REPO_ROOT" "$PYTHON" >&2
  exit 92
fi
canonical_repo=$(readlink -e "$REPO_ROOT")
repo_owner_uid=$(stat -c '%u' "$canonical_repo")
current_uid=$(id -u)
if [[ "$repo_owner_uid" != "$current_uid" ]]; then
  printf 'refuse repository not owned by launcher user: repo=%s owner=%s user=%s\n' \
    "$canonical_repo" "$repo_owner_uid" "$current_uid" >&2
  exit 92
fi
cd "$canonical_repo"
git_top=$(git rev-parse --show-toplevel)
if [[ "$(readlink -e "$git_top")" != "$canonical_repo" ]]; then
  printf 'refuse non-root or redirected Git checkout: %s %s\n' \
    "$canonical_repo" "$git_top" >&2
  exit 92
fi
if [[ "$OUTPUT_ROOT" == "$canonical_repo" \
   || "$OUTPUT_ROOT" == "$canonical_repo"/* ]]; then
  printf 'refuse output root inside Git checkout: %s %s\n' \
    "$OUTPUT_ROOT" "$canonical_repo" >&2
  exit 92
fi
if [[ "$CONTROL_ROOT" == "$canonical_repo" \
   || "$CONTROL_ROOT" == "$canonical_repo"/* ]]; then
  printf 'refuse control root inside Git checkout: %s %s\n' \
    "$CONTROL_ROOT" "$canonical_repo" >&2
  exit 92
fi
actual_sha=$(git rev-parse HEAD)
printf '%s\n' "$actual_sha" >"$CONTROL_ROOT/git_head.txt"
git status --short >"$CONTROL_ROOT/git_status.txt"
if [[ "$actual_sha" != "$EXPECTED_GIT_SHA" || -s "$CONTROL_ROOT/git_status.txt" ]]; then
  printf 'refuse checkout mismatch or dirty tree: actual=%s expected=%s\n' \
    "$actual_sha" "$EXPECTED_GIT_SHA" >&2
  exit 92
fi
if pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py|[r]ecover_historical_stage_a.py|[r]un_fixed_server_2160_campaign_case.sh|[s]tart_case4_after_recovery.py|[w]atch.*2160' \
    >"$CONTROL_ROOT/preexisting_solver_processes.txt"; then
  printf 'refuse pre-existing CISPO solver/recovery\n' >&2
  exit 93
fi

/usr/bin/lscpu -p=CPU,SOCKET,CORE,NODE \
  >"$CONTROL_ROOT/cpu_topology.csv"
"$PYTHON" - "$CONTROL_ROOT/cpu_topology.csv" \
  >"$CONTROL_ROOT/cpu_topology_validation.json" <<'PY'
import collections
import json
import os
from pathlib import Path
import sys

rows = []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#"):
        continue
    cpu, socket, core, node = map(int, line.split(","))
    if 0 <= cpu <= 31:
        rows.append((cpu, socket, core, node))
expected_cpus = set(range(32))
actual_cpus = {row[0] for row in rows}
physical_cores = {(row[1], row[2]) for row in rows}
node_counts = collections.Counter(row[3] for row in rows)
allowed_cpus = set(os.sched_getaffinity(0))
payload = {
    "selected_cpu_range": "0-31",
    "selected_logical_cpus": len(rows),
    "unique_physical_cores": len(physical_cores),
    "numa_node_counts": dict(sorted(node_counts.items())),
    "launcher_allowed_cpu_count": len(allowed_cpus),
    "selected_cpus_allowed": expected_cpus.issubset(allowed_cpus),
    "status": "PASS",
}
if (
    actual_cpus != expected_cpus
    or len(rows) != 32
    or len(physical_cores) != 32
    or node_counts != {0: 16, 1: 16}
    or not expected_cpus.issubset(allowed_cpus)
):
    payload["status"] = "FAIL"
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(1)
print(json.dumps(payload, indent=2, sort_keys=True))
PY

{
  date --iso-8601=seconds
  free -h
  vmstat 1 4
  cat /proc/pressure/memory
} >"$CONTROL_ROOT/preflight_resources.txt"
available_gib=$(awk '/MemAvailable:/ {printf "%.3f", $2/1048576}' /proc/meminfo)
"$PYTHON" - "$available_gib" "$MINIMUM_AVAILABLE_GIB" <<'PY'
import sys
available, required = map(float, sys.argv[1:])
raise SystemExit(0 if available >= required else 1)
PY
if ! vmstat 1 4 | awk 'NR > 2 && ($7 != 0 || $8 != 0) {bad=1} END {exit bad+0}'; then
  printf 'refuse active swap-in/swap-out pressure\n' >&2
  exit 94
fi
"$PYTHON" - <<'PY' >"$CONTROL_ROOT/python_environment.txt"
import gurobipy as gp
import platform
print(platform.python_version())
print(".".join(map(str, gp.gurobi.version())))
assert gp.gurobi.version() == (13, 0, 2)
PY

printf '%s start sha=%s hours=%s start=%s threads=32 output=%s\n' \
  "$(date --iso-8601=seconds)" "$actual_sha" "$HOURS" "$START_HOUR" \
  "$OUTPUT_ROOT" >"$CONTROL_ROOT/events.log"

# Install supervision traps before the solver exists. A signal in the narrow
# fork/setsid/PGID-validation window is remembered and applied immediately once
# the child PID is known, so it cannot leave an unguarded detached solver.
run_pid=
wrapper_signal_name=
wrapper_signal_rc=0
supervision_failure_rc=0
supervision_failure_reason=

request_solver_termination() {
  local reason=$1
  if [[ -z "${run_pid:-}" ]] || ! kill -0 "$run_pid" 2>/dev/null; then
    return 0
  fi
  local live_pgid
  live_pgid=$(ps -o pgid= -p "$run_pid" 2>/dev/null | tr -d ' ' || true)
  printf '%s termination_requested reason=%s pid=%s pgid=%s\n' \
    "$(date --iso-8601=seconds)" "$reason" "$run_pid" \
    "${live_pgid:-UNAVAILABLE}" >>"$CONTROL_ROOT/events.log"
  if [[ "$live_pgid" == "$run_pid" ]]; then
    kill -TERM -- "-$run_pid" 2>/dev/null || true
  else
    # run_pid is an unreaped child of this wrapper, so it cannot have been
    # reused. Signal that exact child if its group identity changed or vanished.
    kill -TERM "$run_pid" 2>/dev/null || true
  fi
}

handle_wrapper_signal() {
  local name=$1
  local code=$2
  if [[ -z "$wrapper_signal_name" ]]; then
    wrapper_signal_name=$name
    wrapper_signal_rc=$code
  fi
  request_solver_termination "wrapper_signal_$name"
}

trap 'handle_wrapper_signal HUP 129' HUP
trap 'handle_wrapper_signal INT 130' INT
trap 'handle_wrapper_signal TERM 143' TERM

setsid /usr/bin/numactl --interleave=0,1 /usr/bin/taskset -c 0-31 \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --planning-year 2030 \
    --diagnostic-hours "$HOURS" \
    --diagnostic-start-hour "$START_HOUR" \
    --scenario-config "$SCENARIO" \
    --solver-config "$SOLVER_PROFILE" \
    --formulation-config "$FORMULATION_PROFILE" \
    --engineering-barrier-checkpoint-only \
    --output-dir "$OUTPUT_ROOT" \
    >"$CONTROL_ROOT/stdout.log" 2>"$CONTROL_ROOT/stderr.log" &
run_pid=$!
printf '%s\n' "$run_pid" >"$CONTROL_ROOT/run.pid"
if [[ -n "$wrapper_signal_name" ]]; then
  request_solver_termination "wrapper_signal_$wrapper_signal_name"
fi
actual_pgid=$(ps -o pgid= -p "$run_pid" 2>/dev/null | tr -d ' ' || true)
if [[ "$actual_pgid" != "$run_pid" ]]; then
  printf 'solver process-group setup failed pid=%s pgid=%s\n' "$run_pid" "$actual_pgid" >&2
  if kill -0 "$run_pid" 2>/dev/null; then
    kill -TERM "$run_pid" 2>/dev/null || true
  fi
  set +e
  wait "$run_pid"
  solver_rc=$?
  set -e
  printf '%s\n' "$solver_rc" >"$CONTROL_ROOT/return_code.txt"
  printf '%s\n' 95 >"$CONTROL_ROOT/final_return_code.txt"
  exit 95
fi

# Verify the affinity that taskset actually installed, not only static lscpu
# topology.  A cgroup/cpuset restriction may silently reduce the requested set.
solver_affinity=
for _ in $(seq 1 50); do
  if ! kill -0 "$run_pid" 2>/dev/null; then
    break
  fi
  solver_affinity=$(awk '/^Cpus_allowed_list:/ {print $2}' \
    "/proc/$run_pid/status" 2>/dev/null || true)
  if [[ "$solver_affinity" == "0-31" ]]; then
    break
  fi
  sleep 0.1 || true
done
printf '%s\n' "${solver_affinity:-UNAVAILABLE}" \
  >"$CONTROL_ROOT/solver_cpus_allowed_list.txt"
if [[ "$solver_affinity" != "0-31" ]]; then
  supervision_failure_rc=95
  supervision_failure_reason=SOLVER_CPU_AFFINITY_VALIDATION_FAILED
  request_solver_termination "$supervision_failure_reason"
  while kill -0 "$run_pid" 2>/dev/null; do
    sleep 1 || true
  done
  set +e
  wait "$run_pid"
  solver_rc=$?
  set -e
  trap - HUP INT TERM
  printf '%s\n' "$solver_rc" >"$CONTROL_ROOT/return_code.txt"
  printf '%s\n' 95 >"$CONTROL_ROOT/final_return_code.txt"
  exit 95
fi

"$PYTHON" scripts/guard_stagea_row_scaling_2160.py \
  --process-group "$run_pid" --output-dir "$OUTPUT_ROOT" \
  --control-dir "$CONTROL_ROOT" --interval 10 \
  >"$CONTROL_ROOT/qualification_guard.stdout.log" \
  2>"$CONTROL_ROOT/qualification_guard.stderr.log" &
guard_pid=$!
printf '%s\n' "$guard_pid" >"$CONTROL_ROOT/qualification_guard.pid"
{
  printf 'wrapper\n'
  ps -o pid=,ppid=,pgid=,sid=,lstart=,cmd= -p "$$" || true
  printf 'solver\n'
  ps -o pid=,ppid=,pgid=,sid=,lstart=,cmd= -p "$run_pid" || true
  printf 'guard\n'
  ps -o pid=,ppid=,pgid=,sid=,lstart=,cmd= -p "$guard_pid" || true
} >"$CONTROL_ROOT/process_identity.txt"
{
  printf 'wrapper\n'
  cat "/proc/$$/cgroup" || true
  printf 'solver\n'
  cat "/proc/$run_pid/cgroup" || true
  printf 'guard\n'
  cat "/proc/$guard_pid/cgroup" || true
} >"$CONTROL_ROOT/process_cgroups.txt"

while true; do
  solver_alive=0
  guard_alive=0
  kill -0 "$run_pid" 2>/dev/null && solver_alive=1
  kill -0 "$guard_pid" 2>/dev/null && guard_alive=1
  if (( solver_alive == 1 && guard_alive == 0 \
        && supervision_failure_rc == 0 )); then
    supervision_failure_rc=96
    supervision_failure_reason=QUALIFICATION_GUARD_EXITED_WHILE_SOLVER_ALIVE
    request_solver_termination "$supervision_failure_reason"
  fi
  if (( solver_alive == 0 )); then
    break
  fi
  sleep 2 || true
done

# Reap the Python leader first so a graceful solver termination and all
# preservation exports finish before the wrapper closes its control record.
set +e
wait "$run_pid"
solver_rc=$?
set -e

# Once the solver group has disappeared, the guard should close within one
# sampling interval.  Bound this final bookkeeping wait so a wedged guard
# cannot keep the service alive indefinitely.
guard_wait_deadline=$((SECONDS + 60))
while kill -0 "$guard_pid" 2>/dev/null && (( SECONDS < guard_wait_deadline )); do
  sleep 1 || true
done
if kill -0 "$guard_pid" 2>/dev/null; then
  supervision_failure_rc=97
  supervision_failure_reason=QUALIFICATION_GUARD_DID_NOT_EXIT_AFTER_SOLVER
  printf '%s guard_termination_requested pid=%s\n' \
    "$(date --iso-8601=seconds)" "$guard_pid" \
    >>"$CONTROL_ROOT/events.log"
  kill -TERM "$guard_pid" 2>/dev/null || true
fi
guard_term_deadline=$((SECONDS + 10))
while kill -0 "$guard_pid" 2>/dev/null \
  && (( SECONDS < guard_term_deadline )); do
  sleep 1 || true
done
if kill -0 "$guard_pid" 2>/dev/null; then
  printf '%s guard_kill_required pid=%s preservation_unaffected=true\n' \
    "$(date --iso-8601=seconds)" "$guard_pid" \
    >>"$CONTROL_ROOT/events.log"
  kill -KILL "$guard_pid" 2>/dev/null || true
fi
while kill -0 "$guard_pid" 2>/dev/null; do
  sleep 0.1 || true
done
set +e
wait "$guard_pid"
guard_rc=$?
set -e
trap - HUP INT TERM
printf '%s\n' "$solver_rc" >"$CONTROL_ROOT/return_code.txt"
printf '%s\n' "$guard_rc" >"$CONTROL_ROOT/qualification_guard_return_code.txt"
final_rc=$solver_rc
if (( wrapper_signal_rc != 0 )); then
  final_rc=$wrapper_signal_rc
elif (( supervision_failure_rc != 0 )); then
  final_rc=$supervision_failure_rc
elif (( final_rc == 0 && guard_rc != 0 )); then
  final_rc=$guard_rc
fi
printf '%s\n' "$final_rc" >"$CONTROL_ROOT/final_return_code.txt"
printf '%s end solver_rc=%s guard_rc=%s final_rc=%s signal=%s supervision=%s\n' \
  "$(date --iso-8601=seconds)" "$solver_rc" "$guard_rc" "$final_rc" \
  "${wrapper_signal_name:-NONE}" "${supervision_failure_reason:-NONE}" \
  >>"$CONTROL_ROOT/events.log"
exit "$final_rc"
