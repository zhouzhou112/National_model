#!/usr/bin/env bash
set -euo pipefail

# Concurrent matched 744 h Stage A screens.  They run relaxed Barrier to its
# configured termination and persist engineering checkpoints.  They are still
# test-only and cannot be scientifically accepted without Stage B and QC.
SERVER_ROOT=${CISPO_SERVER_ROOT:-/home/zz2/National_model_server}
REPO_ROOT=$SERVER_ROOT/repo
TOOL_ROOT=$SERVER_ROOT/campaign_tools/cf_744_stagea_pair_20260901_v1
CONTROL_ROOT=$TOOL_ROOT/run_control
PROFILE_ROOT=$TOOL_ROOT/profiles
PYTHON=$SERVER_ROOT/envs/cispo-2030-v1/bin/python
MONITOR_SCRIPT=$SERVER_ROOT/campaign_tools/case1_stage_b_20260901_v1/scripts/monitor_case_resources.py
EXPECTED_HEAD=6065bfba34b76098e86307081323e8545a4d25ac
STAGE_B_TAG=2030_base_2160h_case1_v3_stage_b_20260901_v1
BASELINE_TAG=2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1
CANDIDATE_TAG=2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1
BASELINE_CPUS=0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30
CANDIDATE_CPUS=1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31

mkdir -p "$CONTROL_ROOT"
if [[ -e "$CONTROL_ROOT/claim" ]]; then
  printf 'pair already claimed: %s\n' "$CONTROL_ROOT/claim" >&2
  exit 90
fi
( set -o noclobber; printf '%s\n' "$(date --iso-8601=seconds)" >"$CONTROL_ROOT/claim" ) 2>/dev/null || {
  printf 'pair claim race\n' >&2
  exit 90
}

set -a
source "$SERVER_ROOT/server_env_20260825.sh"
set +a
cd "$REPO_ROOT"
head=$(git rev-parse HEAD)
status=$(git status --short)
printf '%s\n' "$head" >"$CONTROL_ROOT/git_head.txt"
printf '%s' "$status" >"$CONTROL_ROOT/git_status.txt"
if [[ "$head" != "$EXPECTED_HEAD" || -n "$status" ]]; then
  printf '%s blocked repo head=%s dirty=%s\n' \
    "$(date --iso-8601=seconds)" "$head" "$([[ -n "$status" ]] && echo yes || echo no)" \
    >>"$CONTROL_ROOT/events.log"
  exit 91
fi

for profile in \
  "$PROFILE_ROOT/large_lp_744_v3_baseline_stage_a_v1.json" \
  "$PROFILE_ROOT/large_lp_744_cf1e4_stage_a_v1.json"; do
  test -f "$profile" || { printf 'missing profile %s\n' "$profile" >&2; exit 92; }
done
test -f "$MONITOR_SCRIPT" || { printf 'missing monitor %s\n' "$MONITOR_SCRIPT" >&2; exit 92; }
for tag in "$BASELINE_TAG" "$CANDIDATE_TAG"; do
  if [[ -e "$SERVER_ROOT/outputs/$tag" || -e "$SERVER_ROOT/run_control/$tag" ]]; then
    printf 'refuse existing tag %s\n' "$tag" >&2
    exit 93
  fi
done

pgrep -af 'run_cispo_2030_full_year.py|run_cispo_planning_sequence.py' \
  >"$CONTROL_ROOT/preexisting_solver_processes.txt" || true
if [[ -s "$CONTROL_ROOT/preexisting_solver_processes.txt" ]] && \
   grep -v "$STAGE_B_TAG" "$CONTROL_ROOT/preexisting_solver_processes.txt" | grep -q .; then
  printf '%s blocked unknown preexisting solver\n' "$(date --iso-8601=seconds)" \
    >>"$CONTROL_ROOT/events.log"
  exit 94
fi

read -r mem_total mem_available < <(
  awk '/MemTotal:/ {t=$2} /MemAvailable:/ {a=$2} END {print t,a}' /proc/meminfo
)
used_percent=$($PYTHON - "$mem_total" "$mem_available" <<'PY'
import sys
t, a = map(float, sys.argv[1:])
print(100.0 * (t-a) / t)
PY
)
if ! "$PYTHON" - "$used_percent" "$mem_available" <<'PY'
import sys
used = float(sys.argv[1])
available_gib = float(sys.argv[2]) / 1048576.0
raise SystemExit(0 if used < 90.0 and available_gib >= 60.0 else 1)
PY
then
  printf '%s blocked resources used_percent=%s available_kib=%s\n' \
    "$(date --iso-8601=seconds)" "$used_percent" "$mem_available" \
    >>"$CONTROL_ROOT/events.log"
  exit 95
fi

launch_case() {
  local tag=$1
  local profile=$2
  local cpus=$3
  local control=$SERVER_ROOT/run_control/$tag
  local output=$SERVER_ROOT/outputs/$tag
  mkdir -p "$control"
  printf '%s start tag=%s profile=%s cpus=%s\n' \
    "$(date --iso-8601=seconds)" "$tag" "$profile" "$cpus" \
    >"$control/events.log"
  setsid taskset -c "$cpus" /usr/bin/time -v -o "$control/time.txt" \
    "$PYTHON" scripts/run_cispo_2030_full_year.py \
      --planning-year 2030 \
      --diagnostic-hours 744 \
      --diagnostic-start-hour 2880 \
      --scenario-config config/scenarios/base.json \
      --solver-config "$profile" \
      --engineering-barrier-checkpoint-only \
      --engineering-relaxed-barrier-analysis \
      --output-dir "$output" \
      >"$control/stdout.log" 2>"$control/stderr.log" &
  local pid=$!
  printf '%s\n' "$pid" >"$control/run.pid"
  "$PYTHON" "$MONITOR_SCRIPT" \
    --process-group "$pid" --output-dir "$control" --gpu-device 0 \
    --interval 2 --stop-file "$control/telemetry.stop" \
    >"$control/telemetry.stdout.log" 2>"$control/telemetry.stderr.log" &
  printf '%s\n' "$!" >"$control/telemetry.pid"
  LAUNCHED_PID=$pid
}

launch_case \
  "$BASELINE_TAG" "$PROFILE_ROOT/large_lp_744_v3_baseline_stage_a_v1.json" \
  "$BASELINE_CPUS"
baseline_pid=$LAUNCHED_PID
launch_case \
  "$CANDIDATE_TAG" "$PROFILE_ROOT/large_lp_744_cf1e4_stage_a_v1.json" \
  "$CANDIDATE_CPUS"
candidate_pid=$LAUNCHED_PID
printf '%s\n' "$baseline_pid" >"$CONTROL_ROOT/baseline.pid"
printf '%s\n' "$candidate_pid" >"$CONTROL_ROOT/candidate.pid"
printf '%s pair_started baseline_pid=%s candidate_pid=%s\n' \
  "$(date --iso-8601=seconds)" "$baseline_pid" "$candidate_pid" \
  >>"$CONTROL_ROOT/events.log"

printf 'timestamp\tmem_total_kib\tmem_available_kib\thost_used_percent\tpsi_some_avg10\tbaseline_rss_kib\tcandidate_rss_kib\n' \
  >"$CONTROL_ROOT/resource_monitor_pair.tsv"
guard_triggered=0
while kill -0 "$baseline_pid" 2>/dev/null || kill -0 "$candidate_pid" 2>/dev/null; do
  read -r mem_total mem_available < <(
    awk '/MemTotal:/ {t=$2} /MemAvailable:/ {a=$2} END {print t,a}' /proc/meminfo
  )
  used_percent=$($PYTHON - "$mem_total" "$mem_available" <<'PY'
import sys
t, a = map(float, sys.argv[1:])
print(f"{100.0 * (t-a) / t:.6f}")
PY
  )
  psi=$(awk '/^some / {for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/memory)
  baseline_rss=$(ps -eo pgid=,rss= | awk -v pg="$baseline_pid" '$1==pg {s+=$2} END {print s+0}')
  candidate_rss=$(ps -eo pgid=,rss= | awk -v pg="$candidate_pid" '$1==pg {s+=$2} END {print s+0}')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date --iso-8601=seconds)" "$mem_total" "$mem_available" \
    "$used_percent" "$psi" "$baseline_rss" "$candidate_rss" \
    >>"$CONTROL_ROOT/resource_monitor_pair.tsv"
  if "$PYTHON" - "$used_percent" <<'PY'
import sys
raise SystemExit(0 if float(sys.argv[1]) >= 95.0 else 1)
PY
  then
    guard_triggered=1
    printf '%s host95_guard_triggered used_percent=%s\n' \
      "$(date --iso-8601=seconds)" "$used_percent" >>"$CONTROL_ROOT/events.log"
    kill -TERM -- "-$baseline_pid" 2>/dev/null || true
    kill -TERM -- "-$candidate_pid" 2>/dev/null || true
    break
  fi
  sleep 2
done

set +e
wait "$baseline_pid"; baseline_rc=$?
wait "$candidate_pid"; candidate_rc=$?
set -e
for tag in "$BASELINE_TAG" "$CANDIDATE_TAG"; do
  control=$SERVER_ROOT/run_control/$tag
  touch "$control/telemetry.stop"
  telemetry_pid=$(cat "$control/telemetry.pid")
  set +e
  wait "$telemetry_pid"; telemetry_rc=$?
  set -e
  printf '%s\n' "$telemetry_rc" >"$control/telemetry_return_code.txt"
done
printf '%s\n' "$baseline_rc" >"$SERVER_ROOT/run_control/$BASELINE_TAG/return_code.txt"
printf '%s\n' "$candidate_rc" >"$SERVER_ROOT/run_control/$CANDIDATE_TAG/return_code.txt"
printf '%s pair_end baseline_rc=%s candidate_rc=%s guard=%s\n' \
  "$(date --iso-8601=seconds)" "$baseline_rc" "$candidate_rc" "$guard_triggered" \
  >>"$CONTROL_ROOT/events.log"
exit 0
