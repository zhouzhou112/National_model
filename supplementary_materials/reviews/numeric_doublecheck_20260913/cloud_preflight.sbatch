#!/bin/bash
# Prepared bounded diagnostic; never chain or launch a production successor.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=700G
#SBATCH --time=02:00:00
#SBATCH --job-name=cispo_numeric_gate
set -euo pipefail
umask 027
: "${SLURM_SUBMIT_DIR:?Submit from a fresh unpacked gate release}"
: "${SOURCE_RELEASE:?Set the existing immutable source release}"
GATE_ROOT="$SLURM_SUBMIT_DIR"
test ! -e "$GATE_ROOT/output_8760"
test ! -e "$GATE_ROOT/data_overlay"
cd "$GATE_ROOT"
sha256sum -c release_files.sha256 > release_hash_check.log
set -a
source "$SOURCE_RELEASE/manifests/cloud_environment_paths.env"
set +a
BASE_DATA_ROOT="$CISPO_DATA_ROOT"
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
export GRB_LICENSE_FILE="${CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}"
export http_proxy="${CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=32 OPENBLAS_NUM_THREADS=32 MKL_NUM_THREADS=32
test -r "$GRB_LICENSE_FILE"
"$PYTHON" prepare_cloud_data_overlay.py --base-data "$BASE_DATA_ROOT" \
  --output-data "$GATE_ROOT/data_overlay" --overrides "$GATE_ROOT/data_overrides"
export CISPO_DATA_ROOT="$GATE_ROOT/data_overlay"
cd "$GATE_ROOT/repo"
/usr/bin/time -v -o "$GATE_ROOT/resource_usage.txt" \
  "$PYTHON" scripts/probe_full_year_numerics.py \
    --config config/optimization_2030_numeric_final_v8.json \
    --output-dir "$GATE_ROOT/output_8760" --threads 32 --time-limit 900 \
    --soft-mem-limit-gb 550 \
    > "$GATE_ROOT/stdout.log" 2> "$GATE_ROOT/stderr.log"
