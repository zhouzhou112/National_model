#!/bin/bash
# Cloud engineering gate: solves a single 2030 Base diagnostic horizon only.
# Submit with, for example:
#   sbatch --export=ALL,CISPO_DIAGNOSTIC_HOURS=24 cloud_cispo_diagnostic_gate.sbatch
# The runtime config changes only the Gurobi thread count to the Slurm allocation.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_384
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --job-name=cispo_cloud_gate
#SBATCH --output=cloud_cispo_gate-%j.out
#SBATCH --error=cloud_cispo_gate-%j.err

set -euo pipefail

RELEASE=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493
ENV_ROOT=/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310
GUROBI_HOME=/publicfs01/fs1-a8/home/a8s001819/staging/gurobi1302/gurobi1302install/gurobi1302/linux64
WLS_LICENSE=/publicfs01/fs1-a8/home/a8s001819/gurobipy-test-gcs/gurobi.lic
PROXY=http://172.16.110.3:8888
HOURS="${CISPO_DIAGNOSTIC_HOURS:?set CISPO_DIAGNOSTIC_HOURS to 24 or 168}"

case "$HOURS" in
  24|168) ;;
  *) echo "Unsupported CISPO_DIAGNOSTIC_HOURS=$HOURS" >&2; exit 2 ;;
esac

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

OUT="$RELEASE/outputs/cloud_gate_${HOURS}h_base_2030_22fb493"
CONFIG="$OUT/optimization_2030_cloud_${SLURM_CPUS_PER_TASK}threads.json"
mkdir -p "$OUT"
cd "$RELEASE/repo"

"$ENV_ROOT/bin/python" - "$CONFIG" "$SLURM_CPUS_PER_TASK" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path("config/optimization_2030.json").read_text(encoding="utf-8"))
config["numerics"]["threads"] = int(sys.argv[2])
Path(sys.argv[1]).write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo "CLOUD_GATE_HOST $(hostname)"
echo "CLOUD_GATE_HOURS $HOURS"
echo "CLOUD_GATE_THREADS $SLURM_CPUS_PER_TASK"
"$ENV_ROOT/bin/python" -m unittest discover -s tests -q
"$ENV_ROOT/bin/python" scripts/run_cispo_2030_full_year.py \
  --config "$CONFIG" \
  --planning-year 2030 \
  --diagnostic-hours "$HOURS" \
  --output-dir "$OUT"
