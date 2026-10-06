#!/bin/bash
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_m8_768-a
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --job-name=tiny_bound_2030
#SBATCH --output=tiny_bound_2030-%j.out
#SBATCH --error=tiny_bound_2030-%j.err
set -euo pipefail
BASE=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud
WORK="$BASE/claude_workspace/tiny_bound_audit_20261004"
cd "$WORK"
set -a
source "$BASE/20260903_8760_stagea_final_2820fc3_v3/manifests/cloud_environment_paths.env"
set +a
export PYTHONUNBUFFERED=1 PYTHONUTF8=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
hostname
date -Is
"$PYTHON" --version
"$PYTHON" audit_bounds.py --inputs inputs.json --year 2030 --out result_2030
date -Is
