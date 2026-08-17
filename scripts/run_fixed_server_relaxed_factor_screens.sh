#!/usr/bin/env bash
set -uo pipefail

# Strictly serial 744 h factor screens. These runs deliberately terminate
# after five Barrier iterations and are never complete checkpoints or science.
REPO_ROOT=${REPO_ROOT:-/data/zz2/National_model/repo}
PYTHON=${CISPO_PYTHON:-/home/zz2/.local/envs/cispo-2030/bin/python}
OUTPUT_BASE=${OUTPUT_BASE:-/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v1}
CONTROL_ROOT=${CONTROL_ROOT:-/data/zz2/National_model/run_control/relaxed_factor_screens_v0817_v1}
BASELINE_OUTPUT=${BASELINE_OUTPUT:-/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1/base_744h_bctol1e2_numeric1}
MINIMUM_AVAILABLE_GIB=${MINIMUM_AVAILABLE_GIB:-64}
EXPECTED_HEAD=${EXPECTED_HEAD:-}

export CISPO_DATA_ROOT=${CISPO_DATA_ROOT:-/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1}
export CISPO_CF_ROOT=${CISPO_CF_ROOT:-/data/zz2/National_model/data/hourly_cf}
export CISPO_HYDRO_ROOT=${CISPO_HYDRO_ROOT:-/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse}
export CISPO_RAW_GRFR_ROOT=${CISPO_RAW_GRFR_ROOT:-/data/zz2/National_model/data/grfr_raw_2019}
export CISPO_WAVE_ROOT=${CISPO_WAVE_ROOT:-/data/zz2/National_model/data/wave_energy_20260727}

mkdir -p "$CONTROL_ROOT"
cd "$REPO_ROOT"

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
    ps -eo pid,ppid,%cpu,%mem,rss,etimes,cmd --sort=-rss | head -20
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
  printf '%s refuse_head expected=%s actual=%s\n' \
    "$(date --iso-8601=seconds)" "$EXPECTED_HEAD" "$(git rev-parse HEAD)" \
    >>"$CONTROL_ROOT/events.log"
  exit 90
fi
if [[ -n "$(git status --porcelain)" ]]; then
  printf '%s refuse_dirty_checkout\n' "$(date --iso-8601=seconds)" >>"$CONTROL_ROOT/events.log"
  exit 91
fi
if pgrep -af 'run_cispo_2030_full_year.py|run_cispo_planning_sequence.py' \
    >"$CONTROL_ROOT/preexisting_solver_processes.txt"; then
  printf '%s refuse_preexisting_solver\n' "$(date --iso-8601=seconds)" >>"$CONTROL_ROOT/events.log"
  exit 92
fi
if ! resource_safe; then
  printf '%s refuse_resources minimum_available_gib=%s\n' \
    "$(date --iso-8601=seconds)" "$MINIMUM_AVAILABLE_GIB" >>"$CONTROL_ROOT/events.log"
  exit 93
fi
if [[ ! -f "$BASELINE_OUTPUT/solve_report.json" ]]; then
  printf '%s refuse_missing_baseline path=%s\n' \
    "$(date --iso-8601=seconds)" "$BASELINE_OUTPUT" >>"$CONTROL_ROOT/events.log"
  exit 98
fi

set +e
PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" - \
    "$BASELINE_OUTPUT" "$CONTROL_ROOT/baseline_solver_audit.json" <<'PY'
import json
import sys
from pathlib import Path
from cispo_model.solver_audit import collect_solver_run

root, destination = map(Path, sys.argv[1:])
report = collect_solver_run(root)
required = (
    "lp_gurobi_fingerprint", "lp_identity_variables",
    "lp_identity_constraints", "lp_identity_nonzeros",
    "original_rows", "original_columns", "original_nonzeros",
    "resolved_scientific_configuration_sha256",
    "scenario_configuration_sha256", "presolved_rows",
    "presolved_columns", "presolved_nonzeros", "dense_columns",
    "aa_transpose_nonzeros", "factor_nonzeros", "factor_operations",
)
missing = [field for field in required if report.get(field) is None]
if missing:
    raise SystemExit("baseline audit missing: " + ", ".join(missing))
destination.write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
PY
baseline_audit_rc=$?
if (( baseline_audit_rc != 0 )); then
  printf '%s refuse_invalid_baseline_audit rc=%s path=%s\n' \
    "$(date --iso-8601=seconds)" "$baseline_audit_rc" "$BASELINE_OUTPUT" \
    >>"$CONTROL_ROOT/events.log"
  exit 98
fi

declare -a tags=(nf0_scale2 nf1_scaleauto nf0_scaleauto)
declare -a profiles=(
  config/solver_profiles/barrier_16_engineering_factor_nf0_scale2_5iter_v1.json
  config/solver_profiles/barrier_16_engineering_factor_nf1_scaleauto_5iter_v1.json
  config/solver_profiles/barrier_16_engineering_factor_nf0_scaleauto_5iter_v1.json
)

record_resources campaign_before
printf '%s\n' "$(git rev-parse HEAD)" >"$CONTROL_ROOT/git_head.txt"
for i in "${!tags[@]}"; do
  tag=${tags[$i]}
  output="$OUTPUT_BASE/$tag"
  control="$CONTROL_ROOT/$tag"
  mkdir -p "$control"
  if [[ -e "$output" ]]; then
    printf '%s refuse_existing_output tag=%s path=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" "$output" >>"$CONTROL_ROOT/events.log"
    exit 94
  fi
  if pgrep -af 'run_cispo_2030_full_year.py|run_cispo_planning_sequence.py' \
      >"$control/preexisting_solver_processes.txt"; then
    printf '%s refuse_preexisting_solver tag=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" >>"$CONTROL_ROOT/events.log"
    exit 95
  fi
  if ! resource_safe; then
    printf '%s refuse_resources tag=%s\n' \
      "$(date --iso-8601=seconds)" "$tag" >>"$CONTROL_ROOT/events.log"
    exit 96
  fi
  printf '%s start tag=%s profile=%s\n' \
    "$(date --iso-8601=seconds)" "$tag" "${profiles[$i]}" >>"$CONTROL_ROOT/events.log"
  /usr/bin/time -v -o "$control/time.txt" \
    "$PYTHON" scripts/run_cispo_2030_full_year.py \
      --planning-year 2030 \
      --diagnostic-hours 744 \
      --diagnostic-start-hour 0 \
      --scenario-config config/scenarios/base.json \
      --solver-config "${profiles[$i]}" \
      --output-dir "$output" \
      >"$control/stdout.log" 2>"$control/stderr.log"
  rc=$?
  printf '%s\n' "$rc" >"$control/return_code.txt"
  PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" - "$output" \
      "$control/solver_audit.json" <<'PY'
import json
import sys
from pathlib import Path
from cispo_model.solver_audit import collect_solver_run

root, destination = map(Path, sys.argv[1:])
report = collect_solver_run(root)
destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
iterations = report.get("barrier_iterations")
if iterations is None or not (1 <= int(iterations) <= 5):
    raise SystemExit(f"unexpected Barrier iteration count: {iterations!r}")
for field in ("factor_nonzeros", "factor_operations", "dense_columns"):
    if report.get(field) is None:
        raise SystemExit(f"missing factor-screen field: {field}")
PY
  audit_rc=$?
  printf '%s end tag=%s runner_rc=%s audit_rc=%s\n' \
    "$(date --iso-8601=seconds)" "$tag" "$rc" "$audit_rc" >>"$CONTROL_ROOT/events.log"
  if (( audit_rc != 0 )); then
    exit 97
  fi
  record_resources "${tag}_after"
done
record_resources campaign_after
PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" \
  scripts/summarize_relaxed_factor_screens.py \
  --baseline-audit "$CONTROL_ROOT/baseline_solver_audit.json" \
  --control-root "$CONTROL_ROOT" \
  --output-json "$CONTROL_ROOT/factor_screen_summary.json" \
  --output-csv "$CONTROL_ROOT/factor_screen_summary.csv" || exit 99
printf '%s campaign_complete\n' "$(date --iso-8601=seconds)" >>"$CONTROL_ROOT/events.log"
