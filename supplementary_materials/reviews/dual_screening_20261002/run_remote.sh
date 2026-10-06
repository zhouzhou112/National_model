#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT=$(realpath "$1")
CASE_NAME=$2
shift 2
SERVER_ROOT=$(realpath "$TASK_ROOT/../..")
set -a
source "$SERVER_ROOT/server_env_20260825.sh"
set +a
export CISPO_DATA_ROOT="$TASK_ROOT/data"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 OMP_NUM_THREADS=12 OPENBLAS_NUM_THREADS=1
cd "$TASK_ROOT/repo"
TOOLS=supplementary_materials/reviews/dual_screening_20261002
exec "$CISPO_PYTHON" "$TOOLS/supervise_probe.py" --control "$TASK_ROOT/control_$CASE_NAME" --wall-seconds 7200 -- \
  taskset -c 0-11 nice -n 10 "$CISPO_PYTHON" "$TOOLS/run_screen_probe.py" --output "$TASK_ROOT/$CASE_NAME" "$@"
