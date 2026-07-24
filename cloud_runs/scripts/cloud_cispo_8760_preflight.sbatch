#!/bin/bash
# 8760-hour data-and-scale preflight only.  This does not import or call Gurobi.
# Submit from the cloud release scripts directory with: sbatch cloud_cispo_8760_preflight.sbatch
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_384
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --job-name=cispo_8760_preflight
#SBATCH --output=cloud_cispo_8760_preflight-%j.out
#SBATCH --error=cloud_cispo_8760_preflight-%j.err

set -euo pipefail

RELEASE=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493
ENV_ROOT=/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310

export CISPO_DATA_ROOT="$RELEASE/data/model_ready_20260723_v0722_city337"
export CISPO_CF_ROOT="$RELEASE/data/hourly_cf"
export CISPO_HYDRO_ROOT="$RELEASE/data/hydro_timeseries_20260719_sequential_sparse"
export PYTHONUNBUFFERED=1

cd "$RELEASE/repo"
mkdir -p "$RELEASE/outputs/8760_preflight_2030_22fb493"
echo "PRELIGHT_HOST $(hostname)"
echo "PRELIGHT_START_UTC $(date -u +%FT%TZ)"
"$ENV_ROOT/bin/python" scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --preflight-only \
  --output-dir "$RELEASE/outputs/8760_preflight_2030_22fb493"
echo "PRELIGHT_END_UTC $(date -u +%FT%TZ)"
