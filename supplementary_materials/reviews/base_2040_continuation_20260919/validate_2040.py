"""Validate actual 2030 candidate, year transition and tiny 2040 build; never solve."""
from pathlib import Path
import argparse
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'repo'))
PROFILE = 'config/solver_profiles/barrier_checkpoint_full_year_cloud_2040_numeric_v1_threads44.json'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-only', action='store_true')
    args = parser.parse_args()
    from cispo_model.config import load_model_config
    from cispo_model.planning_state import PlanningState
    from cispo_model.run_contract import analysis_case_identity
    from cispo_model.diagnostics import configure_gurobi, validate_unlimited_stage_a_parameters
    import gurobipy as gp
    os.chdir(ROOT/'repo')
    cfg = load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path=PROFILE).for_planning_year(2040)
    old = load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path='config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json')
    assert analysis_case_identity(old)['resolved_scientific_configuration_sha256'] == '937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0'
    assert cfg.planning_year == 2040 and cfg.boundary_year == 2030
    assert cfg.raw['planning_interval_years'] == 10 and cfg.raw['features']['dac'] is True
    assert cfg.raw['scenario']['id'] == 'base' and not cfg.raw['features']['flexible_load']
    assert cfg.raw['formulation'].get('annual_capacity_link_row_scaling', 'physical_v1') == 'physical_v1'
    old_numeric, new_numeric = old.raw['numerics'], cfg.raw['numerics']
    differences = {k: [old_numeric.get(k), new_numeric.get(k)] for k in set(old_numeric)|set(new_numeric) if old_numeric.get(k) != new_numeric.get(k)}
    assert differences == {'threads': [48, 44]}, differences
    state = PlanningState.load(os.environ['UPSTREAM_STATE'], expected_boundary_year=2030,
                              expected_scenario_id='base', allow_unaccepted_candidate=True)
    assert state.metadata['candidate_unaccepted'] and state.metadata['scientifically_accepted'] is False
    assert state.metadata['cohort_rows'] == len(state.cohorts) == 86900
    try:
        PlanningState.load(os.environ['UPSTREAM_STATE'], expected_boundary_year=2030)
    except ValueError:
        pass
    else:
        raise AssertionError('Candidate incorrectly accepted without explicit acknowledgement')
    result = dict(status='PASS', planning_year=2040, boundary_year=2030,
                  upstream_state=str(state.root), upstream_candidate_unaccepted=True,
                  upstream_qc_status=state.metadata['source_qc_status'], cohort_rows=len(state.cohorts),
                  numerics_changes=differences, scientific_identity=analysis_case_identity(cfg))
    with gp.Model() as model:
        configure_gurobi(model, cfg, ROOT/('contract_parameters.log' if args.contract_only else 'validation_parameters.log'))
        result['actual_solver_parameters'] = validate_unlimited_stage_a_parameters(model, cfg)
    if not args.contract_only:
        from cispo_model.data import load_model_data
        from cispo_model.monolithic import build_full_year_monolithic
        from cispo_model.annual_capacity_link_scaling import validate_row_scaling_registry
        from scripts import run_cispo_2030_full_year as runner
        from types import SimpleNamespace
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from io import StringIO
        import runpy
        data = load_model_data(cfg, planning_state=state)
        art = build_full_year_monolithic(cfg, data, optimization_hours=1)
        art.model.update()
        result['one_hour_build_only'] = dict(rows=art.model.NumConstrs, columns=art.model.NumVars, nonzeros=art.model.NumNZs, optimize_called=False)
        validate_row_scaling_registry(art.index['annual_capacity_link_row_scaling'], model=art.model, allow_none=False)
        art.model.dispose()
        # Exercise the exact full-year runner and original-model archive branch.
        # Only the huge builder is substituted with a 2-row actual Gurobi fixture.
        fixture = runpy.run_path(str(ROOT/'repo/tests/test_numeric_repaired_formal_launch.py'))['annual_row_fixture']
        with gp.Model() as model:
            registry = fixture(model, cfg)
            art = SimpleNamespace(model=model, index={'annual_capacity_link_row_scaling': registry})
            output = ROOT/'runner_fixture_build_only'
            argv = ['runner', '--config', str(cfg.path), '--solver-config', PROFILE, '--planning-year', '2040',
                    '--horizon', 'full_year', '--state-in', str(state.root), '--allow-candidate-state-in',
                    '--engineering-barrier-checkpoint-only', '--archive-original-model', '--build-only', '--output-dir', str(output)]
            with patch('sys.argv', argv), patch.object(runner, 'cloud_full_year_required_memory_gib', return_value=0), \
                 patch('cispo_model.monolithic.build_full_year_monolithic', return_value=art), redirect_stdout(StringIO()):
                runner.main()
            scope = json.loads((output/'run_scope.json').read_text())
            assert scope['planning_year'] == 2040 and scope['boundary_year'] == 2030
            assert scope['barrier_first_workflow']['planning_state_policy'] == 'UPSTREAM_UNACCEPTED_CANDIDATE_CANNOT_BECOME_ACCEPTED_STATE'
            assert json.loads((output/'model_archive/archive_manifest.json').read_text())['status'] == 'COMPLETE'
            assert not (output/'solve_report.json').exists() and not (output/'planning_state').exists()
            result['full_year_entry_two_row_fixture'] = 'PASS_BUILD_ARCHIVE_NO_OPTIMIZE'
    name = 'continuation_contract_check.json' if args.contract_only else 'validation_2040.json'
    (ROOT/name).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
