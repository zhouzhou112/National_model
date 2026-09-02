#!/usr/bin/env bash
set -euo pipefail

# Generic Slurm payload for one member of the author-approved 8760 h
# 32/64-thread comparison.  Resource requests stay in the sbatch command so
# the same immutable script is used by both jobs.

require_env() {
  local name=$1
  if [[ -z "${!name:-}" ]]; then
    echo "missing required environment variable: $name" >&2
    exit 64
  fi
}

for name in \
  CISPO_RELEASE_ROOT \
  CISPO_CASE_ID \
  CISPO_SOLVER_PROFILE \
  CISPO_EXPECTED_GIT_SHA \
  CISPO_EXPECTED_THREADS; do
  require_env "$name"
done

release_root=$CISPO_RELEASE_ROOT
repo_root="$release_root/repo"
output_root="$release_root/outputs/$CISPO_CASE_ID"
control_root="$release_root/run_control/$CISPO_CASE_ID"
environment_file="$release_root/manifests/cloud_environment_paths.env"
formulation_profile="$repo_root/config/formulation_profiles/annual_capacity_link_rows_8192_v1.json"
solver_profile="$repo_root/$CISPO_SOLVER_PROFILE"

if [[ ! -d "$repo_root" || ! -f "$environment_file" ]]; then
  echo "release repository or environment manifest is missing" >&2
  exit 65
fi
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse output root: $output_root" >&2
  exit 66
fi
mkdir -p "$control_root"

set -a
# shellcheck disable=SC1090
source "$environment_file"
set +a
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"

cd "$repo_root"

actual_sha=$(<"$release_root/manifests/git_commit.txt")
if [[ "$actual_sha" != "$CISPO_EXPECTED_GIT_SHA" ]]; then
  echo "release Git identity mismatch" >&2
  exit 67
fi

"$PYTHON" - "$solver_profile" "$CISPO_EXPECTED_THREADS" <<'PY'
import json
import sys

profile = json.load(open(sys.argv[1], encoding="utf-8"))
numerics = profile["numerics"]
assert profile["direct_nonbasic_scientific_acceptance"] is True
assert profile["required_formulation_profile_id"] == "annual_capacity_link_rows_8192_v1"
assert int(numerics["threads"]) == int(sys.argv[2])
assert int(numerics["method"]) == 2
assert int(numerics["presolve"]) == 2
assert int(numerics["crossover"]) == 0
assert int(numerics["solution_target"]) == 1
assert numerics["time_limit_seconds"] is None
assert float(numerics["barrier_convergence_tolerance"]) == 1e-9
assert float(numerics["feasibility_tolerance"]) == 1e-9
assert float(numerics["optimality_tolerance"]) == 1e-8
PY

allocated_cpus=${SLURM_CPUS_PER_TASK:-0}
if (( allocated_cpus < CISPO_EXPECTED_THREADS )); then
  echo "Slurm CPU allocation is smaller than Gurobi Threads" >&2
  exit 68
fi

{
  echo "recorded_at=$(date --iso-8601=seconds)"
  echo "host=$(hostname -f)"
  echo "job_id=${SLURM_JOB_ID:-UNSET}"
  echo "slurm_cpus_per_task=$allocated_cpus"
  echo "slurm_mem_per_node_mb=${SLURM_MEM_PER_NODE:-UNSET}"
  echo "gurobi_threads=$CISPO_EXPECTED_THREADS"
  echo "git_commit=$actual_sha"
  echo "solver_profile=$CISPO_SOLVER_PROFILE"
  echo "slurm_time_limit=$(squeue -h -j "${SLURM_JOB_ID:-0}" -o %l 2>/dev/null || true)"
  taskset -pc $$ 2>/dev/null || true
  scontrol show job "${SLURM_JOB_ID:-0}" 2>/dev/null || true
  sha256sum "$solver_profile" "$formulation_profile"
} > "$control_root/launch_identity.txt"

runner_pid=""
stop_watcher_pid=""
forward_signal() {
  local signal_name=$1
  printf '%s wrapper_received_%s\n' "$(date --iso-8601=seconds)" "$signal_name" \
    >> "$control_root/events.log"
  if [[ -n "$runner_pid" ]] && kill -0 "$runner_pid" 2>/dev/null; then
    kill -TERM "$runner_pid" 2>/dev/null || true
  fi
}
trap 'forward_signal TERM' TERM
trap 'forward_signal INT' INT
trap 'forward_signal HUP' HUP

"$PYTHON" scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --solver-config "$solver_profile" \
  --formulation-config "$formulation_profile" \
  --archive-original-model \
  --allow-nonbasic-planning-state \
  --output-dir "$output_root" \
  > "$control_root/wrapper_stdout.log" \
  2> "$control_root/wrapper_stderr.log" &
runner_pid=$!
echo "$runner_pid" > "$control_root/runner.pid"

# A controlled human stop is requested by creating STOP_REQUESTED.  If that
# happens during build/archive, delay SIGTERM until solve_and_report has
# installed Gurobi's graceful termination handler.  This preserves the raw
# model archive before asking Gurobi for the best available BarX/BarPi state.
(
  while kill -0 "$runner_pid" 2>/dev/null; do
    if [[ -f "$control_root/STOP_REQUESTED" ]]; then
      printf '%s controlled_stop_seen\n' "$(date --iso-8601=seconds)" \
        >> "$control_root/events.log"
      while kill -0 "$runner_pid" 2>/dev/null \
        && ! grep -q '"event":"solver_start"' \
          "$output_root/solver_telemetry.jsonl" 2>/dev/null; do
        sleep 10
      done
      if kill -0 "$runner_pid" 2>/dev/null; then
        printf '%s controlled_sigterm_forwarded\n' "$(date --iso-8601=seconds)" \
          >> "$control_root/events.log"
        kill -TERM "$runner_pid"
      fi
      exit 0
    fi
    sleep 30
  done
) &
stop_watcher_pid=$!

set +e
wait "$runner_pid"
runner_rc=$?
set -e
kill "$stop_watcher_pid" 2>/dev/null || true
wait "$stop_watcher_pid" 2>/dev/null || true

echo "$runner_rc" > "$control_root/return_code.txt"
{
  echo "finished_at=$(date --iso-8601=seconds)"
  echo "runner_return_code=$runner_rc"
  for relative in \
    build_report.json \
    solve_report.json \
    solution_qc.json \
    result_manifest.json \
    model_archive/archive_manifest.json \
    barrier_checkpoint/barrier_checkpoint_manifest.json \
    preservation_report.json; do
    if [[ -f "$output_root/$relative" ]]; then
      sha256sum "$output_root/$relative"
    else
      echo "MISSING $relative"
    fi
  done
} > "$control_root/terminal_status.txt"

exit "$runner_rc"
