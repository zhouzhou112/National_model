#!/bin/bash
# Single authorized 2030 Base / 8760 h Stage A.  This job performs only a
# Barrier solve and save-first checkpoint export.  It has deliberately no
# Slurm or Gurobi TimeLimit and cannot launch Stage B or another planning year.
# Submit with explicit --output/--error paths under the versioned control root.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=96
#SBATCH --mem=700G
#SBATCH --job-name=cispo_8760_a_v2

set -euo pipefail
umask 027

# Slurm executes a private spool copy of the submitted script, so $0 cannot
# identify the immutable release.  Submission is contractually performed from
# RELEASE/repo and SLURM_SUBMIT_DIR preserves that original directory.
test -n "${SLURM_SUBMIT_DIR:-}"
RELEASE="$(cd "$SLURM_SUBMIT_DIR/.." && pwd)"
test -d "$RELEASE/repo"
ENV_FILE="$RELEASE/manifests/cloud_environment_paths.env"
CONTROL_ROOT="$RELEASE/run_control/2030_8760_base_stage_a_barrier_v2"
OUT="$RELEASE/outputs/2030_8760_base_stage_a_barrier_v2"
PROFILE="config/solver_profiles/barrier_checkpoint_full_year_cloud_v2.json"
WLS_LICENSE=/publicfs01/fs1-a8/home/a8s001819/gurobipy-test-gcs/gurobi.lic
PROXY=http://172.16.110.3:8888

test -f "$ENV_FILE"
# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a
test -x "$PYTHON"
test -d "$CISPO_DATA_ROOT"
test -d "$CISPO_CF_ROOT"
test -d "$CISPO_HYDRO_ROOT"
test -d "$CISPO_WAVE_ROOT"
test ! -e "$OUT"
mkdir -p "$CONTROL_ROOT"

export GUROBI_HOME
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
export GRB_LICENSE_FILE="$WLS_LICENSE"
export http_proxy="$PROXY"
export https_proxy="$PROXY"
export ftp_proxy="$PROXY"
export HTTP_PROXY="$PROXY"
export HTTPS_PROXY="$PROXY"
export FTP_PROXY="$PROXY"
export PYTHONUNBUFFERED=1

cd "$RELEASE/repo"
{
  echo "started_at=$(date --iso-8601=seconds)"
  echo "host=$(hostname)"
  echo "job_id=${SLURM_JOB_ID:-UNKNOWN}"
  echo "allocated_cpus=${SLURM_CPUS_ON_NODE:-UNKNOWN}"
  echo "gurobi_threads=16"
  echo "requested_memory=700G"
  echo "gurobi_soft_memory_gb=600"
  echo "gurobi_time_limit=UNSET"
  echo "slurm_time_limit=UNLIMITED"
  echo "stage_b_auto_start=false"
  echo "output_root=$OUT"
  sha256sum "$PROFILE"
} > "$CONTROL_ROOT/launch_identity.txt"

"$PYTHON" - "$PROFILE" <<'PY'
import sys
from pathlib import Path

from cispo_model.config import load_model_config

profile = Path(sys.argv[1])
config = load_model_config(solver_path=profile)
numerics = config.raw["numerics"]
assert config.raw["scenario"]["id"] == "base"
assert numerics["method"] == 2
assert numerics["threads"] == 16
assert numerics["crossover"] == 0
assert numerics["solution_target"] == 1
assert numerics["time_limit_seconds"] is None
assert numerics["soft_mem_limit_gb"] == 600
print("STAGE_A_PROFILE_PREFLIGHT_PASS")
PY

set +e
/usr/bin/time -v -o "$CONTROL_ROOT/wrapper_time.txt" \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --planning-year 2030 \
    --horizon full_year \
    --solver-config "$PROFILE" \
    --engineering-barrier-checkpoint-only \
    --output-dir "$OUT" \
  > >(tee "$CONTROL_ROOT/wrapper_stdout.log") \
  2> >(tee "$CONTROL_ROOT/wrapper_stderr.log" >&2)
RUN_RC=$?
set -e

{
  echo "finished_at=$(date --iso-8601=seconds)"
  echo "wrapper_exit_code=$RUN_RC"
} > "$CONTROL_ROOT/terminal_status.txt"
exit "$RUN_RC"
