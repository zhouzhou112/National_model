#!/usr/bin/env bash
#SBATCH --job-name=cispo2030_thermal_t44
#SBATCH --partition=amd_a8_768
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=700G
#SBATCH --time=0
#SBATCH --no-requeue
#SBATCH --output=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260907_thermal_stagea_1e4_t44_ffd651a_v2/run_control/2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2/slurm-%j.out
#SBATCH --error=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260907_thermal_stagea_1e4_t44_ffd651a_v2/run_control/2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2/slurm-%j.err
set -euo pipefail
export CISPO_RELEASE_ROOT=/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260907_thermal_stagea_1e4_t44_ffd651a_v2
export CISPO_CASE_ID=2030_case1_thermal_v5_8760_rows8192_t44_m700_tol1e4_ffd651a_v2
export CISPO_SCENARIO_ID=case1_thermal_v5
export CISPO_SOLVER_PROFILE=config/solver_profiles/barrier_stagea_portfolio_v1_threads44.json
export CISPO_EXPECTED_GIT_SHA=ffd651aded605568bc1e02cc460eae5ecd113b5b
export CISPO_EXPECTED_THREADS=44
export CISPO_AUTHORIZED_WALL_SECONDS=0
exec bash "$CISPO_RELEASE_ROOT/repo/scripts/run_cloud_portfolio_job.sh"
