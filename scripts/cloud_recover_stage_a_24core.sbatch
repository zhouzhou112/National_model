#!/bin/bash
# Author-authorized historical Stage A recovery only. No optimization or successor.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=128G
#SBATCH --time=04:00:00
#SBATCH --job-name=cispo_8760_recover

set -euo pipefail
umask 027
: "${SLURM_SUBMIT_DIR:?Submit from the isolated recovery release}"
: "${SOURCE_RELEASE:?Set the immutable original release}"
RECOVERY_ROOT=$SLURM_SUBMIT_DIR
CONTROL="$RECOVERY_ROOT/control"
OUTPUT="$RECOVERY_ROOT/recovered_8760"
test ! -e "$OUTPUT"
test ! -e "$CONTROL/run_started.txt"
test "$SLURM_CPUS_PER_TASK" = 24
set -a
source "$SOURCE_RELEASE/manifests/cloud_environment_paths.env"
set +a
unset CISPO_RAW_GRFR_ROOT
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
export GRB_LICENSE_FILE="${CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}"
export http_proxy="${CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=24 OPENBLAS_NUM_THREADS=24 MKL_NUM_THREADS=24
test -r "$GRB_LICENSE_FILE"
mkdir -p "$CONTROL"
date -Is > "$CONTROL/run_started.txt"
cd "$RECOVERY_ROOT"
sha256sum -c release_files.sha256 > "$CONTROL/release_hash_check.log"
cd "$RECOVERY_ROOT/repo"

# Only tiny synthetic LP checks (seconds), never another national-model solve.
set +e
"$PYTHON" -m unittest discover -s tests -p test_solution_preservation.py -v \
  > "$CONTROL/tiny_tests.stdout.log" 2> "$CONTROL/tiny_tests.stderr.log"
test_rc=$?
if (( test_rc == 0 )); then
  /usr/bin/time -v -o "$CONTROL/time.txt" \
    "$PYTHON" scripts/recover_historical_stage_a.py \
      --source-backup "$RECOVERY_ROOT/source_backup" \
      --path-map "$RECOVERY_ROOT/path_mapping.json" \
      --allow-fingerprint-mismatch \
      --output-dir "$OUTPUT" \
      > "$CONTROL/stdout.log" 2> "$CONTROL/stderr.log"
  rc=$?
else
  rc=$test_rc
fi
set -e
printf '%s\n' "$rc" > "$CONTROL/return_code.txt"
printf '%s rc=%s tiny_test_rc=%s stage_b_started=false\n' "$(date -Is)" "$rc" "$test_rc" \
  > "$CONTROL/terminal_status.txt"
exit "$rc"
