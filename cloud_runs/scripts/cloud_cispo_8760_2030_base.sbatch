#!/bin/bash
# User-authorized scientific single-year 2030 Base 8760h solve on the 768G node.
# It keeps the production model unchanged and only aligns Gurobi resources with
# the Slurm allocation.  Output is isolated from all build-only and diagnostic gates.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=128
#SBATCH --mem=700G
#SBATCH --time=24:00:00
#SBATCH --job-name=cispo_8760_base
#SBATCH --output=cloud_cispo_8760_base-%j.out
#SBATCH --error=cloud_cispo_8760_base-%j.err

set -euo pipefail

RELEASE=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493
ENV_ROOT=/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310
GUROBI_HOME=/publicfs01/fs1-a8/home/a8s001819/staging/gurobi1302/gurobi1302install/gurobi1302/linux64
WLS_LICENSE=/publicfs01/fs1-a8/home/a8s001819/gurobipy-test-gcs/gurobi.lic
PROXY=http://172.16.110.3:8888

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
export CISPO_DATA_ROOT="$RELEASE/data/model_ready_20260723_v0722_city337"
export CISPO_CF_ROOT="$RELEASE/data/hourly_cf"
export CISPO_HYDRO_ROOT="$RELEASE/data/hydro_timeseries_20260719_sequential_sparse"

OUT="$RELEASE/outputs/full_year_2030_base_22fb493_128cpu_700g"
CONFIG="$OUT/optimization_2030_cloud_${SLURM_CPUS_PER_TASK}threads_640gsoft.json"
mkdir -p "$OUT"
cd "$RELEASE/repo"

"$ENV_ROOT/bin/python" - "$CONFIG" "$SLURM_CPUS_PER_TASK" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path("config/optimization_2030.json").read_text(encoding="utf-8"))
config["numerics"]["threads"] = int(sys.argv[2])
config["numerics"]["soft_mem_limit_gb"] = 640
Path(sys.argv[1]).write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo "FULL_SOLVE_HOST $(hostname)"
echo "FULL_SOLVE_CPUS $SLURM_CPUS_PER_TASK"
echo "FULL_SOLVE_MEMORY_REQUEST 700G"
echo "FULL_SOLVE_SOFT_MEMORY_LIMIT_GB 640"
echo "FULL_SOLVE_GUROBI_TIME_LIMIT_SECONDS 86400"
"$ENV_ROOT/bin/python" -m unittest discover -s tests -q
"$ENV_ROOT/bin/python" scripts/run_cispo_2030_full_year.py \
  --config "$CONFIG" \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir "$OUT"
