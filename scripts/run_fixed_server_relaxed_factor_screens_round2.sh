#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=${REPO_ROOT:-/data/zz2/National_model/repo}
export REPO_ROOT
export OUTPUT_BASE=${OUTPUT_BASE:-/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v2}
export CONTROL_ROOT=${CONTROL_ROOT:-/data/zz2/National_model/run_control/relaxed_factor_screens_v0817_v2}
export BASELINE_OUTPUT=${BASELINE_OUTPUT:-/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v1/nf1_scaleauto}
export CASE_TAGS_CSV=presparsify2,barorder1,threads32
export PROFILE_PATHS_CSV=config/solver_profiles/barrier_16_engineering_factor_presparsify2_5iter_v1.json,config/solver_profiles/barrier_16_engineering_factor_barorder1_5iter_v1.json,config/solver_profiles/barrier_32_engineering_factor_threads32_5iter_v1.json
export MATERIAL_STRUCTURAL_REDUCTION_FRACTION=0.05
export MATERIAL_RUNTIME_REDUCTION_FRACTION=0.10

exec bash "$REPO_ROOT/scripts/run_fixed_server_relaxed_factor_screens.sh"
