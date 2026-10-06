#!/bin/bash
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=750G
#SBATCH --time=0
#SBATCH --no-requeue
#SBATCH --job-name=cispo_factor_8760
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
set -euo pipefail
umask 027
RELEASE_ROOT="${SLURM_SUBMIT_DIR:?}"
trap 'rc=$?; printf "{\"exit_code\":%s,\"job_id\":\"%s\"}\n" "$rc" "$SLURM_JOB_ID" > "$RELEASE_ROOT/batch_exit.json"' EXIT
cd "$RELEASE_ROOT"
test ! -e output_8760
sha256sum -c release_files.sha256 > runtime_hash_check.log
set -a
source /publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3/manifests/cloud_environment_paths.env
set +a
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
export GRB_LICENSE_FILE="${CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}"
export http_proxy="${CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUNBUFFERED=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=48 OPENBLAS_NUM_THREADS=48 MKL_NUM_THREADS=48
export CISPO_DATA_ROOT="$RELEASE_ROOT/data_overlay"
export PYTHONPATH="$RELEASE_ROOT/repo${PYTHONPATH:+:$PYTHONPATH}"
"$PYTHON" - "$RELEASE_ROOT" <<'PY'
import json,os,re,subprocess,sys
from pathlib import Path
import psutil
root=Path(sys.argv[1])
record=subprocess.check_output(['scontrol','show','job','-o',os.environ['SLURM_JOB_ID']],text=True)
(root/'runtime_slurm_job.txt').write_text(record)
def field(key):return re.search(r'\b'+key+r'=(\S+)',record).group(1)
tres=dict(x.split('=',1) for x in field('AllocTRES').split(','))
assert tres.get('cpu')=='64' and tres.get('billing')=='64' and tres.get('mem') in ('750G','768000M'),tres
assert field('TimeLimit')=='UNLIMITED' and field('Partition')=='amd_a8_768'
assert int(os.environ['SLURM_CPUS_PER_TASK'])==64 and len(os.sched_getaffinity(0))>=48
assert psutil.virtual_memory().available>=500*2**30
node=subprocess.check_output(['scontrol','show','node',field('NodeList')],text=True)
(root/'runtime_node.txt').write_text(node)
(root/'allocation_gate.json').write_text(json.dumps(dict(status='PASS',allocation=tres,node=field('NodeList'),available_gib=psutil.virtual_memory().available/2**30),indent=2))
PY
cd "$RELEASE_ROOT/repo"
"$PYTHON" -m unittest discover -s tests -p test_factor_screen.py -v > "$RELEASE_ROOT/startup_regression.log" 2>&1
screen=()
if [[ "$(basename "$RELEASE_ROOT")" == member_S ]]; then screen=(--vre-screen-csv "$RELEASE_ROOT/source_screen.csv"); fi
/usr/bin/time -v -o "$RELEASE_ROOT/resource_usage.txt" \
 "$PYTHON" scripts/run_cispo_2030_full_year.py \
 --config config/optimization_numeric_dac_by_year_v9.json \
 --scenario-config config/scenarios/case3_thermal_ev_v9_factor.json \
 --solver-config config/solver_profiles/barrier_factor_screen_8760_v1_threads48.json \
 --planning-year 2030 --horizon full_year --archive-original-model \
 "${screen[@]}" --output-dir "$RELEASE_ROOT/output_8760" \
 > "$RELEASE_ROOT/stdout.log" 2> "$RELEASE_ROOT/stderr.log"
