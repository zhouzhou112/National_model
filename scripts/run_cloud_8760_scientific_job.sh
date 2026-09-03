#!/usr/bin/env bash
set -euo pipefail

# Single final 32-thread 8760 h Stage A payload.  It never launches Stage B.

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
expected_profile="config/solver_profiles/barrier_stagea_final_full_year_cloud_v6_threads32.json"

if [[ "$CISPO_SOLVER_PROFILE" != "$expected_profile" \
  || "$CISPO_EXPECTED_THREADS" != "32" ]]; then
  echo "final Stage A wrapper requires the canonical v6 32-thread profile" >&2
  exit 64
fi

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
assert profile["stage_b_required"] is False
assert profile["required_formulation_profile_id"] == "annual_capacity_link_rows_8192_v1"
assert int(numerics["threads"]) == int(sys.argv[2])
assert int(numerics["method"]) == 2
assert int(numerics["presolve"]) == 2
assert int(numerics["crossover"]) == 0
assert int(numerics["solution_target"]) == 1
assert numerics["time_limit_seconds"] is None
assert float(numerics["barrier_convergence_tolerance"]) == 1e-2
assert float(numerics["feasibility_tolerance"]) == 1e-6
assert float(numerics["optimality_tolerance"]) == 1e-6
assert int(numerics["numeric_focus"]) == 1
assert int(numerics["scale_flag"]) == 2
assert int(numerics["aggregate"]) == 1
PY

allocated_cpus=${SLURM_CPUS_PER_TASK:-0}
if (( allocated_cpus < CISPO_EXPECTED_THREADS )); then
  echo "Slurm CPU allocation is smaller than Gurobi Threads" >&2
  exit 68
fi

cgroup_memory_file=""
cgroup_relative=$(awk -F: '$1 == "0" {print $3}' /proc/self/cgroup 2>/dev/null || true)
if [[ -n "$cgroup_relative" \
  && -f "/sys/fs/cgroup${cgroup_relative}/memory.max" ]]; then
  cgroup_memory_file="/sys/fs/cgroup${cgroup_relative}/memory.max"
fi
if [[ -z "$cgroup_memory_file" ]]; then
  cgroup_relative=$(awk -F: '$2 ~ /(^|,)memory(,|$)/ {print $3}' /proc/self/cgroup 2>/dev/null || true)
  if [[ -n "$cgroup_relative" \
    && -f "/sys/fs/cgroup/memory${cgroup_relative}/memory.limit_in_bytes" ]]; then
    cgroup_memory_file="/sys/fs/cgroup/memory${cgroup_relative}/memory.limit_in_bytes"
  fi
fi
cgroup_memory_limit_bytes=""
if [[ -n "$cgroup_memory_file" ]]; then
  raw_cgroup_limit=$(<"$cgroup_memory_file")
  if [[ "$raw_cgroup_limit" =~ ^[0-9]+$ ]]; then
    cgroup_memory_limit_bytes=$raw_cgroup_limit
  fi
fi
if [[ -z "$cgroup_memory_limit_bytes" \
  && "${SLURM_MEM_PER_NODE:-}" =~ ^[0-9]+$ ]]; then
  cgroup_memory_limit_bytes=$((SLURM_MEM_PER_NODE * 1024 * 1024))
fi
if [[ -z "$cgroup_memory_limit_bytes" ]]; then
  echo "cannot resolve the Slurm cgroup memory limit" >&2
  exit 69
fi
soft_mem_limit_gb=$(
  "$PYTHON" - "$cgroup_memory_limit_bytes" <<'PY'
import sys

limit = int(sys.argv[1])
reserve = 64 * 1024**3
soft_bytes = min(int(0.85 * limit), limit - reserve)
if soft_bytes <= 0:
    raise SystemExit("Slurm memory allocation is too small for the 64 GiB reserve")
print(f"{soft_bytes / 1_000_000_000:.9f}")
PY
)

{
  echo "recorded_at=$(date --iso-8601=seconds)"
  echo "host=$(hostname -f)"
  echo "job_id=${SLURM_JOB_ID:-UNSET}"
  echo "slurm_cpus_per_task=$allocated_cpus"
  echo "slurm_mem_per_node_mb=${SLURM_MEM_PER_NODE:-UNSET}"
  echo "cgroup_memory_file=${cgroup_memory_file:-UNAVAILABLE}"
  echo "cgroup_memory_limit_bytes=$cgroup_memory_limit_bytes"
  echo "resolved_soft_mem_limit_gb_decimal=$soft_mem_limit_gb"
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
terminal_status_written=false

write_terminal_status() {
  local wrapper_rc=$1
  "$PYTHON" - "$output_root" "$control_root" "$wrapper_rc" <<'PY'
import json
import os
import sys
from datetime import datetime
from pathlib import Path

output = Path(sys.argv[1])
control = Path(sys.argv[2])
wrapper_rc = int(sys.argv[3])

def read(relative):
    path = output / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None

solve = read("solve_report.json")
qc = read("solution_qc.json")
checkpoint = read("barrier_checkpoint/barrier_checkpoint_manifest.json")
preservation = read("preservation_report.json")
result_manifest = read("result_manifest.json")
stage = solve.get("stage_a_completion_status") if solve else None
checkpoint_complete = bool(
    checkpoint
    and checkpoint.get("checkpoint_status") in {
        "ACCEPTED_PRIMARY_BARRIER_SOLUTION",
        "PENDING_ORIGINAL_UNIT_QC",
        "ENGINEERING_BARRIER_CHECKPOINT",
    }
)
if (
    wrapper_rc == 0
    and stage == "STAGE_A_PRIMAL_FINAL_ACCEPTED"
    and qc
    and qc.get("status") == "PASS"
    and checkpoint_complete
    and result_manifest
):
    status = "COMPLETED_ACCEPTED"
elif checkpoint_complete and solve:
    status = "COMPLETED_PRESERVED_REVIEW_REQUIRED"
else:
    status = "INCOMPLETE_NO_USABLE_STAGEA"
payload = {
    "generated_at": datetime.now().astimezone().isoformat(),
    "status": status,
    "wrapper_return_code_before_classification": wrapper_rc,
    "solve_status": solve.get("status") if solve else None,
    "stage_a_completion_status": stage,
    "solution_qc_status": qc.get("status") if qc else None,
    "checkpoint_status": checkpoint.get("checkpoint_status") if checkpoint else None,
    "preservation_status": preservation.get("status") if preservation else None,
    "stage_b_started": False,
}
target = control / "terminal_status.json"
temporary = target.with_suffix(".json.part")
with temporary.open("w", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
temporary.replace(target)
(control / "terminal_status.txt").write_text(
    "\n".join(f"{key}={value}" for key, value in payload.items()) + "\n",
    encoding="utf-8",
)
print(status)
PY
}

finalize_wrapper() {
  local wrapper_rc=$1
  set +e
  if [[ -n "$stop_watcher_pid" ]]; then
    kill "$stop_watcher_pid" 2>/dev/null || true
    wait "$stop_watcher_pid" 2>/dev/null || true
  fi
  if [[ "$terminal_status_written" != true ]]; then
    write_terminal_status "$wrapper_rc" >/dev/null 2>&1 || true
  fi
}
trap 'finalize_wrapper "$?"' EXIT
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
  --runtime-soft-mem-limit-gb "$soft_mem_limit_gb" \
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
terminal_classification=$(write_terminal_status "$runner_rc")
terminal_status_written=true
if [[ "$terminal_classification" == "COMPLETED_ACCEPTED" \
  || "$terminal_classification" == "COMPLETED_PRESERVED_REVIEW_REQUIRED" ]]; then
  exit 0
fi
if (( runner_rc == 0 )); then
  exit 2
fi
exit "$runner_rc"
