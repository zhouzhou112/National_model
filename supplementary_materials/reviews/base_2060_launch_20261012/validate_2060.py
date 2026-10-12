"""Validate frozen 2060 continuation contract; never build or optimize."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'repo'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-only', action='store_true')
    parser.parse_args()
    from cispo_model.config import load_model_config
    from cispo_model.planning_state import PlanningState
    from cispo_model.run_contract import analysis_case_identity
    from cispo_model.diagnostics import configure_gurobi, validate_unlimited_stage_a_parameters
    import gurobipy as gp
    cfg = load_model_config(ROOT/'repo/config/optimization_numeric_dac_by_year_v9_a12.json',
        solver_path=ROOT/'repo/config/solver_profiles/barrier_checkpoint_full_year_cloud_2060_numeric_v1_threads48.json').for_planning_year(2060)
    assert cfg.planning_year == 2060 and cfg.boundary_year == 2050
    assert cfg.raw['scenario']['id'] == 'base' and cfg.raw['features']['dac']
    assert not cfg.raw['features']['flexible_load']
    state = PlanningState.load(os.environ['UPSTREAM_STATE'], expected_boundary_year=2050,
        expected_scenario_id='base', allow_unaccepted_candidate=True)
    launch = json.loads((ROOT/'launch_config.json').read_text())
    assert hashlib.sha256((state.root/'capacity_cohorts.csv.gz').read_bytes()).hexdigest() == launch['upstream_cohort_sha256']
    assert state.metadata['candidate_unaccepted'] and not state.metadata['scientifically_accepted']
    assert state.metadata['acceptance_relative_v1_sha256'] == launch['acceptance_sha256']['2050']
    profiles=ROOT/'repo/config/solver_profiles'
    old=json.loads((profiles/'barrier_checkpoint_full_year_cloud_2050_numeric_v1_threads48.json').read_text())
    new=json.loads((profiles/'barrier_checkpoint_full_year_cloud_2060_numeric_v1_threads48.json').read_text())
    assert old['numerics']==new['numerics'] and not new['stage_b_required']
    n=cfg.raw['numerics']
    for key in ['hydro_capacity_headroom_zero_gw','retrofit_upper_zero_gw','other_capacity_headroom_zero_gw_gwh']:
        assert n[key] == 1e-5
    assert n['capacity_cancellation_rhs_zero']==1e-12 and n.get('inherited_floor_overrun_clip_gw',0)==0
    with gp.Model() as model:
        configure_gurobi(model,cfg,ROOT/'contract_parameters.log')
        params=validate_unlimited_stage_a_parameters(model,cfg)
    result=dict(status='PASS',planning_year=2060,boundary_year=2050,cohort_rows=len(state.cohorts),
        source_commit=launch['source_commit'],scientific_identity=analysis_case_identity(cfg),
        actual_solver_parameters=params,upstream_remains_unaccepted_candidate=True,
        author_acceptance_sidecar_sha256=launch['acceptance_sha256']['2050'],optimize_called=False)
    (ROOT/'continuation_contract_check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
