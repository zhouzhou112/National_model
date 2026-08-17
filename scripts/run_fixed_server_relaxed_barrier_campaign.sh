#!/usr/bin/env bash
set -uo pipefail

# Fixed-server, strictly serial engineering campaign.  It never touches the
# active ParaCloud job, never runs crossover, and never exports planning state.
REPO_ROOT=${REPO_ROOT:-/data/zz2/National_model/repo}
PYTHON=${CISPO_PYTHON:-/home/zz2/.local/envs/cispo-2030/bin/python}
AUDIT_SCRIPT=${AUDIT_SCRIPT:-$REPO_ROOT/scripts/audit_relaxed_barrier_macro.py}
OUTPUT_BASE=${OUTPUT_BASE:-/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1}
CONTROL_ROOT=${CONTROL_ROOT:-/data/zz2/National_model/run_control/relaxed_barrier_campaign_v0812_v1}
REFERENCE_ROOT=${REFERENCE_ROOT:-/data/zz2/National_model/outputs/planning_sequence_2030_2060_744h_jan0_3f123f0_base_v1/2030}

mkdir -p "$CONTROL_ROOT"
cd "$REPO_ROOT"

snapshot() {
  local label=$1
  {
    printf 'timestamp='; date --iso-8601=seconds
    printf 'label=%s\n' "$label"
    git rev-parse HEAD
    git status --short
    free -h
    vmstat 1 3
    cat /proc/pressure/memory
    cat /proc/pressure/io
    df -h /data
    ps -eo pid,ppid,%cpu,%mem,rss,etimes,cmd --sort=-rss | head -20
  } >"$CONTROL_ROOT/resource_${label}.txt" 2>&1
}

available_gib() {
  awk '/MemAvailable:/ {printf "%.3f", $2/1048576}' /proc/meminfo
}

resource_safe() {
  local minimum=$1
  local available si so psi
  available=$(available_gib)
  read -r si so < <(vmstat 1 2 | tail -1 | awk '{print $7, $8}')
  psi=$(awk '/^some / {for(i=1;i<=NF;i++) if($i ~ /^avg10=/){split($i,a,"="); print a[2]}}' /proc/pressure/memory)
  "$PYTHON" - "$available" "$minimum" "$si" "$so" "$psi" <<'PY'
import sys
available, minimum, si, so, psi = map(float, sys.argv[1:])
raise SystemExit(0 if available >= minimum and si == 0 and so == 0 and psi == 0 else 1)
PY
}

wait_for_resources() {
  local minimum=$1
  local waited=0
  while ! resource_safe "$minimum"; do
    printf '%s waiting_for_resources minimum_gib=%s available_gib=%s\n' \
      "$(date --iso-8601=seconds)" "$minimum" "$(available_gib)" \
      >>"$CONTROL_ROOT/campaign_events.log"
    sleep 60
    waited=$((waited + 60))
    if (( waited >= 43200 )); then
      printf '%s resource_wait_timeout\n' "$(date --iso-8601=seconds)" \
        >>"$CONTROL_ROOT/campaign_events.log"
      return 1
    fi
  done
}

run_case() {
  local tag=$1 profile=$2 hours=$3 start=$4 scenario=$5 minimum_memory=$6
  local output="$OUTPUT_BASE/$tag"
  local control="$CONTROL_ROOT/$tag"
  mkdir -p "$control"
  if [[ -e "$output" ]]; then
    printf '%s refuse_existing_output tag=%s path=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" "$output" \
      >>"$CONTROL_ROOT/campaign_events.log"
    return 90
  fi
  if pgrep -af 'run_cispo_2030_full_year.py|run_cispo_planning_sequence.py' \
      >"$control/preexisting_solver_processes.txt"; then
    printf '%s refuse_preexisting_solver tag=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" \
      >>"$CONTROL_ROOT/campaign_events.log"
    return 91
  fi
  wait_for_resources "$minimum_memory" || return 92
  snapshot "${tag}_before"
  printf '%s start tag=%s profile=%s hours=%s start_hour=%s scenario=%s\n' \
    "$(date --iso-8601=seconds)" "$tag" "$profile" "$hours" "$start" "$scenario" \
    >>"$CONTROL_ROOT/campaign_events.log"
  set +e
  /usr/bin/time -v -o "$control/time.txt" \
    "$PYTHON" scripts/run_cispo_2030_full_year.py \
      --planning-year 2030 \
      --diagnostic-hours "$hours" \
      --diagnostic-start-hour "$start" \
      --scenario-config "$scenario" \
      --solver-config "$profile" \
      --engineering-barrier-checkpoint-only \
      --engineering-relaxed-barrier-analysis \
      --output-dir "$output" \
      >"$control/stdout.log" 2>"$control/stderr.log"
  local rc=$?
  set +e
  printf '%s\n' "$rc" >"$control/return_code.txt"
  snapshot "${tag}_after"
  printf '%s end tag=%s rc=%s\n' "$(date --iso-8601=seconds)" "$tag" "$rc" \
    >>"$CONTROL_ROOT/campaign_events.log"
  return "$rc"
}

export CISPO_DATA_ROOT=${CISPO_DATA_ROOT:-/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1}
export CISPO_CF_ROOT=${CISPO_CF_ROOT:-/data/zz2/National_model/data/hourly_cf}
export CISPO_HYDRO_ROOT=${CISPO_HYDRO_ROOT:-/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse}
export CISPO_WAVE_ROOT=${CISPO_WAVE_ROOT:-/data/zz2/National_model/data/wave_energy_20260727}

snapshot campaign_start
printf '%s\n' "$(git rev-parse HEAD)" >"$CONTROL_ROOT/git_head.txt"

declare -a tags=(bctol5e2 bctol1e2 bctol1e2_numeric1)
declare -a profiles=(
  config/solver_profiles/barrier_16_engineering_relaxed_bctol5e2_v1.json
  config/solver_profiles/barrier_16_engineering_relaxed_bctol1e2_v1.json
  config/solver_profiles/barrier_16_engineering_relaxed_bctol1e2_numeric1_v1.json
)
declare -a long_profiles=(
  config/solver_profiles/barrier_16_engineering_relaxed_bctol5e2_long_v1.json
  config/solver_profiles/barrier_16_engineering_relaxed_bctol1e2_long_v1.json
  config/solver_profiles/barrier_16_engineering_relaxed_bctol1e2_numeric1_long_v1.json
)

for i in "${!tags[@]}"; do
  tag="base_744h_${tags[$i]}"
  mkdir -p "$CONTROL_ROOT/$tag"
  candidate_root="$OUTPUT_BASE/$tag"
  candidate_contract="$candidate_root/engineering_macro_analysis/engineering_analysis_contract.json"
  if [[ -L "$candidate_root" && -f "$candidate_contract" ]]; then
    printf '%s reuse_supervisor_candidate tag=%s target=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" "$(readlink -f "$candidate_root")" \
      >>"$CONTROL_ROOT/campaign_events.log"
  else
    run_case "$tag" "${profiles[$i]}" 744 0 config/scenarios/base.json 64 || true
  fi
  if [[ -f "$OUTPUT_BASE/$tag/engineering_macro_analysis/engineering_analysis_contract.json" ]]; then
    PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
      "$PYTHON" "$AUDIT_SCRIPT" \
      --candidate-root "$OUTPUT_BASE/$tag" \
      --reference-root "$REFERENCE_ROOT" \
      --output "$CONTROL_ROOT/$tag/macro_comparison.json" \
      >"$CONTROL_ROOT/$tag/macro_comparison_stdout.log" 2>&1 || true
  fi
done

"$PYTHON" - "$CONTROL_ROOT" "${tags[@]}" <<'PY' >"$CONTROL_ROOT/winner.json"
import json, sys
from pathlib import Path
control = Path(sys.argv[1])
candidates = []
for index, short_tag in enumerate(sys.argv[2:]):
    tag = f"base_744h_{short_tag}"
    path = control / tag / "macro_comparison.json"
    if not path.is_file():
        continue
    report = json.loads(path.read_text())
    if report.get("status") == "MACRO_PASS":
        candidates.append((float(report["metrics"]["candidate_solver_runtime_seconds"]), index, short_tag))
payload = {"status": "WINNER_SELECTED" if candidates else "NO_MACRO_PASS"}
if candidates:
    runtime, index, short_tag = min(candidates)
    payload.update(index=index, short_tag=short_tag, runtime_seconds=runtime)
print(json.dumps(payload, indent=2))
PY

winner_status=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$CONTROL_ROOT/winner.json")
if [[ "$winner_status" != WINNER_SELECTED ]]; then
  printf '%s no_macro_winner_stop\n' "$(date --iso-8601=seconds)" >>"$CONTROL_ROOT/campaign_events.log"
  snapshot campaign_stop_no_winner
  exit 0
fi
winner_index=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["index"])' "$CONTROL_ROOT/winner.json")
winner_tag=${tags[$winner_index]}
winner_profile=${profiles[$winner_index]}
winner_long_profile=${long_profiles[$winner_index]}

# Validate the same relaxed route on the more complex V5 topology.  Failure is
# retained but does not erase a valid Base winner.
run_case "v5_744h_${winner_tag}" "$winner_profile" 744 0 \
  config/scenarios/flex_integrated_v5_central.json 64 || true

run_case "base_1488h_${winner_tag}" "$winner_long_profile" 1488 3624 \
  config/scenarios/base.json 96 || true
checkpoint_manifest="$OUTPUT_BASE/base_1488h_${winner_tag}/barrier_checkpoint/barrier_checkpoint_manifest.json"
checkpoint_gate="$CONTROL_ROOT/base_1488h_${winner_tag}/checkpoint_campaign_gate.json"
if "$PYTHON" scripts/check_barrier_checkpoint_eligibility.py \
    "$checkpoint_manifest" --output "$checkpoint_gate"; then
  printf '%s checkpoint_eligible_continue tag=base_1488h_%s\n' \
    "$(date --iso-8601=seconds)" "$winner_tag" >>"$CONTROL_ROOT/campaign_events.log"
  run_case "base_2160h_${winner_tag}" "$winner_long_profile" 2160 2880 \
    config/scenarios/base.json 96 || true
else
  printf '%s checkpoint_ineligible_stop tag=base_1488h_%s manifest=%s gate=%s\n' \
    "$(date --iso-8601=seconds)" "$winner_tag" "$checkpoint_manifest" "$checkpoint_gate" \
    >>"$CONTROL_ROOT/campaign_events.log"
fi

snapshot campaign_end
printf '%s campaign_complete\n' "$(date --iso-8601=seconds)" >>"$CONTROL_ROOT/campaign_events.log"
