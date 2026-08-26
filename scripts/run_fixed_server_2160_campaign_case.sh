#!/usr/bin/env bash
set -euo pipefail

# Run exactly one approved large-LP campaign case on the fixed server.  The
# Gurobi profiles intentionally have no SoftMemLimit.  The external 95% whole-
# host guard remains as the last-resort protection on this shared machine.
SERVER_ROOT=${CISPO_SERVER_ROOT:-/home/zz2/National_model_server}
ENV_FILE=${CISPO_SERVER_ENV:-$SERVER_ROOT/server_env_20260825.sh}
if [[ ! -f "$ENV_FILE" ]]; then
  printf 'missing server environment: %s\n' "$ENV_FILE" >&2
  exit 90
fi
set -a
source "$ENV_FILE"
set +a

REPO_ROOT=${CISPO_REPO_ROOT:-$SERVER_ROOT/repo}
PYTHON=${CISPO_PYTHON:-$SERVER_ROOT/envs/cispo-2030-v1/bin/python}
CASE_ID=${CASE_ID:-case1_v3_barrier16_stage_a}
HOURS=${HOURS:-2160}
START_HOUR=${START_HOUR:-2880}
SCENARIO=${SCENARIO:-config/scenarios/base.json}
MINIMUM_AVAILABLE_GIB=${MINIMUM_AVAILABLE_GIB:-96}
GPU_DEVICE=${GPU_DEVICE:-0}
GPU_RUNTIME_ROOT=${GPU_RUNTIME_ROOT:-$SERVER_ROOT/run_control/gpu${GPU_DEVICE}_runtime}

declare -a method_args=()
case "$CASE_ID" in
  case1_v3_barrier16_stage_a)
    PROFILE=config/solver_profiles/large_lp_2160_case1_v3_barrier16_stage_a_v1.json
    method_args+=(--engineering-barrier-checkpoint-only)
    method_args+=(--engineering-relaxed-barrier-analysis)
    ;;
  case2_v3_barrier32_screen)
    PROFILE=config/solver_profiles/large_lp_2160_case2_v3_barrier32_screen_v1.json
    method_args+=(--engineering-barrier-checkpoint-only)
    method_args+=(--engineering-relaxed-barrier-analysis)
    ;;
  case3_dual_simplex_screen)
    PROFILE=config/solver_profiles/large_lp_2160_case3_dual_simplex_screen_v1.json
    ;;
  case4_gpu_pdhg_screen)
    PROFILE=config/solver_profiles/large_lp_2160_case4_gpu_pdhg_screen_v1.json
    mkdir -p "$GPU_RUNTIME_ROOT/mps_pipe" "$GPU_RUNTIME_ROOT/mps_log"
    chmod 700 "$GPU_RUNTIME_ROOT" "$GPU_RUNTIME_ROOT/mps_pipe" \
      "$GPU_RUNTIME_ROOT/mps_log"
    export CUDA_VISIBLE_DEVICES="$GPU_DEVICE"
    # Isolate this user's CUDA client from another user's system-wide MPS
    # control socket.  An empty private pipe directory lets Gurobi use the GPU
    # directly and avoids a cross-user MPS connection failure.
    export CUDA_MPS_PIPE_DIRECTORY="$GPU_RUNTIME_ROOT/mps_pipe"
    export CUDA_MPS_LOG_DIRECTORY="$GPU_RUNTIME_ROOT/mps_log"
    ;;
  *)
    printf 'unsupported CASE_ID: %s\n' "$CASE_ID" >&2
    exit 91
    ;;
esac

TAG=${TAG:-2030_base_${HOURS}h_${CASE_ID}_v1}
OUTPUT_ROOT=${OUTPUT_ROOT:-$SERVER_ROOT/outputs/$TAG}
CONTROL_ROOT=${CONTROL_ROOT:-$SERVER_ROOT/run_control/$TAG}

if (( HOURS < 1 || HOURS >= 8760 )); then
  printf 'HOURS must be in [1, 8759], got %s\n' "$HOURS" >&2
  exit 92
fi
if (( START_HOUR < 0 || START_HOUR + HOURS > 8760 )); then
  printf 'invalid window start=%s hours=%s\n' "$START_HOUR" "$HOURS" >&2
  exit 93
fi
if [[ -e "$OUTPUT_ROOT" || -e "$CONTROL_ROOT" ]]; then
  printf 'refuse existing output/control root: %s %s\n' \
    "$OUTPUT_ROOT" "$CONTROL_ROOT" >&2
  exit 94
fi

mkdir -p "$CONTROL_ROOT"
cd "$REPO_ROOT"
git rev-parse HEAD >"$CONTROL_ROOT/git_head.txt"
git status --short >"$CONTROL_ROOT/git_status.txt"
if [[ -s "$CONTROL_ROOT/git_status.txt" ]]; then
  printf 'refuse dirty server checkout\n' >&2
  exit 95
fi
if pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py' \
    >"$CONTROL_ROOT/preexisting_solver_processes.txt"; then
  printf 'refuse pre-existing CISPO solver\n' >&2
  exit 96
fi

available_gib=$(awk '/MemAvailable:/ {printf "%.3f", $2/1048576}' /proc/meminfo)
"$PYTHON" - "$available_gib" "$MINIMUM_AVAILABLE_GIB" <<'PY'
import sys
available, required = map(float, sys.argv[1:])
raise SystemExit(0 if available >= required else 1)
PY

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
    # Do not persist other users' complete command lines on this shared host.
    ps -eo user:16,pid,ppid,pgid,%cpu,%mem,rss,etimes,comm --sort=-rss | head -25
  } >"$CONTROL_ROOT/resource_${label}.txt" 2>&1
}

snapshot before
printf '%s start case=%s hours=%s start_hour=%s profile=%s python=%s output=%s\n' \
  "$(date --iso-8601=seconds)" "$CASE_ID" "$HOURS" "$START_HOUR" \
  "$PROFILE" "$PYTHON" "$OUTPUT_ROOT" >"$CONTROL_ROOT/events.log"

setsid /usr/bin/time -v -o "$CONTROL_ROOT/time.txt" \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --planning-year 2030 \
    --diagnostic-hours "$HOURS" \
    --diagnostic-start-hour "$START_HOUR" \
    --scenario-config "$SCENARIO" \
    --solver-config "$PROFILE" \
    "${method_args[@]}" \
    --output-dir "$OUTPUT_ROOT" \
    >"$CONTROL_ROOT/stdout.log" 2>"$CONTROL_ROOT/stderr.log" &
run_pid=$!
printf '%s\n' "$run_pid" >"$CONTROL_ROOT/run.pid"

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
    "$(date --iso-8601=seconds)" "$mem_total" "$mem_available" \
    "$used_percent" "$((swap_total-swap_free))" "$psi" "$group_rss" \
    >>"$CONTROL_ROOT/resource_monitor.tsv"
  if "$PYTHON" - "$used_percent" <<'PY'
import sys
raise SystemExit(0 if float(sys.argv[1]) >= 95.0 else 1)
PY
  then
    guard_triggered=1
    printf '%s host_memory_guard_triggered used_percent=%s\n' \
      "$(date --iso-8601=seconds)" "$used_percent" \
      >>"$CONTROL_ROOT/events.log"
    kill -TERM -- "-$run_pid" 2>/dev/null || true
    break
  fi
  sleep 2
done

set +e
wait "$run_pid"
rc=$?
set -e
printf '%s\n' "$rc" >"$CONTROL_ROOT/return_code.txt"
printf '%s end rc=%s host_guard_triggered=%s\n' \
  "$(date --iso-8601=seconds)" "$rc" "$guard_triggered" \
  >>"$CONTROL_ROOT/events.log"
snapshot after
exit "$rc"
