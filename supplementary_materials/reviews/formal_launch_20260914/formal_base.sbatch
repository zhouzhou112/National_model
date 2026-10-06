#!/bin/bash
# Author-authorized full 2030 v9 Base; no wall-time budget or successor job.
#SBATCH --account=bscc-a8
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=750G
#SBATCH --time=0
#SBATCH --no-requeue
#SBATCH --job-name=cispo2030_base_v9_t48
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
set -euo pipefail
umask 027
: "${SLURM_SUBMIT_DIR:?Fresh immutable release required}"
: "${SOURCE_RELEASE:?Immutable data/environment source required}"
RELEASE_ROOT="$SLURM_SUBMIT_DIR"
trap 'rc=$?; printf "{\"exit_code\":%s,\"job_id\":\"%s\"}\n" "$rc" "$SLURM_JOB_ID" > "$RELEASE_ROOT/batch_exit.json"' EXIT
cd "$RELEASE_ROOT"
test ! -e output_8760
sha256sum -c release_files.sha256 > runtime_hash_check.log
set -a
source "$SOURCE_RELEASE/manifests/cloud_environment_paths.env"
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
test -d "$CISPO_DATA_ROOT"
test -r "$GRB_LICENSE_FILE"
"$PYTHON" - "$RELEASE_ROOT" <<'PY'
import json, os, re, subprocess, sys
from pathlib import Path
import gurobipy as gp
import psutil
root = Path(sys.argv[1])
record = subprocess.check_output(['scontrol', 'show', 'job', '-o', os.environ['SLURM_JOB_ID']], text=True)
(root/'runtime_slurm_job.txt').write_text(record)
def field(name):
    match = re.search(r'\b' + name + r'=(\S+)', record)
    if not match:
        raise RuntimeError('Missing Slurm field ' + name)
    return match.group(1)
tres = dict(item.split('=', 1) for item in field('AllocTRES').split(','))
if tres.get('cpu') != '64' or tres.get('billing') != '64' or tres.get('mem') not in {'750G','768000M'}:
    raise RuntimeError('Allocation must be cpu64/mem750G/billing64: ' + str(tres))
if field('TimeLimit') != 'UNLIMITED':
    raise RuntimeError('Job time limit must be UNLIMITED')
if int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) != 64 or len(os.sched_getaffinity(0)) < 48:
    raise RuntimeError('Insufficient assigned/available CPU affinity')
if psutil.virtual_memory().available < 500 * 2**30:
    raise RuntimeError('Available memory is below the reviewed build threshold')
if gp.gurobi.version()[0] < 13:
    raise RuntimeError('Production requires Gurobi 13 or later')
with gp.Env(empty=True) as env:
    env.setParam('OutputFlag', 0)
    env.start()
    with gp.Model(env=env) as model:
        x = model.addVar(lb=0)
        model.addConstr(x >= 1)
        model.setObjective(x)
        model.optimize()
        if model.Status != gp.GRB.OPTIMAL or abs(x.X - 1) > 1e-8:
            raise RuntimeError('Compute-node license/solver smoke failed')
(root/'compute_node_smoke.json').write_text(json.dumps(dict(status='PASS',
    job_id=os.environ['SLURM_JOB_ID'], gurobi_version=list(gp.gurobi.version()),
    allocation=tres, time_limit=field('TimeLimit'),
    available_memory_gib=psutil.virtual_memory().available/2**30), indent=2))
PY
cd "$RELEASE_ROOT/repo"
/usr/bin/time -v -o "$RELEASE_ROOT/resource_usage.txt" \
  "$PYTHON" scripts/run_cispo_2030_full_year.py \
    --config config/optimization_numeric_dac_by_year_v9.json \
    --solver-config config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json \
    --horizon full_year --archive-original-model --allow-nonbasic-planning-state \
    --output-dir "$RELEASE_ROOT/output_8760" \
    > "$RELEASE_ROOT/stdout.log" 2> "$RELEASE_ROOT/stderr.log"
