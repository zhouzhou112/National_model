"""Prelaunch checks: optimizer and presolve entry points are forbidden."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.flexible_load import attach_flexible_load, SparseThermalStateView
from cispo_model.offline_solution import offline_artifacts, audit_saved_primal
from cispo_model.planning_state import PlanningState, STATE_COLUMNS, write_planning_state
from cispo_model.portfolio_release import require_qualified_portfolio_stage_a
from cispo_model.result_summary import finalize_result_manifest
from cispo_model.solution_export import _value
from test_flexible_portfolio import fixture, CASES


class NoSolvePortfolioTests(unittest.TestCase):
    def setUp(self):
        for method in ('optimize', 'optimizeAsync', 'presolve', 'feasRelax', 'feasRelaxS'):
            if hasattr(gp.Model, method):
                guard = patch.object(gp.Model, method,
                    side_effect=AssertionError(f'{method} forbidden in no-solve audit'))
                guard.start()
                self.addCleanup(guard.stop)

    def model(self):
        model = gp.Model('portfolio_no_solve')
        model.Params.OutputFlag = 0
        self.addCleanup(model.dispose)
        return model

    def test_zero_contract_vector_is_feasible_and_reconstructs_base_in_all_cases(self):
        for case in CASES:
            with self.subTest(case=case):
                config = load_model_config(scenario_path=f'config/scenarios/{case}.json')
                data = fixture()
                model = self.model()
                block = attach_flexible_load(model, config, data, hours=24)
                model.setObjective(gp.quicksum(block.costs.values()))
                model.update()
                view = offline_artifacts(SimpleNamespace(model=model,
                    variables=dict(block.variables, effective=block.effective_load_gw),
                    cost_components=block.costs, index={}), np.zeros(model.NumVars), None)
                self.assertEqual(audit_saved_primal(model, np.zeros(model.NumVars))['status'], 'PASS')
                np.testing.assert_array_equal(_value(view.variables['effective']), data.load_gw)
                self.assertEqual(view.model.ObjVal, 0)
                for value in view.cost_components.values():
                    self.assertEqual(float(_value(value)), 0)
                # Sparse thermal views inside the variables must also be detached.
                for value in view.variables.values():
                    if isinstance(value, SparseThermalStateView):
                        np.testing.assert_array_equal(_value(value), np.zeros(value.shape))

    def test_sparse_thermal_recovery_uses_saved_vector_and_cyclic_decay(self):
        model = self.model()
        nodes = model.addMVar(2, name='retained')
        mask = np.array([[True, False, True, False]])
        original = SparseThermalStateView(nodes, mask, np.array([.5]))
        model.update()
        view = offline_artifacts(SimpleNamespace(model=model,
            variables={'thermal': original}, cost_components={}, index={}), np.array([8., 4.]), None)
        np.testing.assert_array_equal(_value(view.variables['thermal']), [[8., 4., 4., 2.]])
        self.assertIs(original.active, nodes)
        self.assertEqual(model.SolCount, 0)

    def test_raw_violation_with_infinite_bound_is_strict_json_serializable(self):
        model = self.model()
        model.addVar(lb=0, ub=gp.GRB.INFINITY, name='nonnegative')
        model.update()
        audit = audit_saved_primal(model, np.array([-1.]))
        self.assertEqual(audit['status'], 'FAIL')
        self.assertIsNone(audit['bound_location']['upper'])
        json.dumps(audit, allow_nan=False)

    def test_service_output_dictionary_has_units_and_dimensions(self):
        from cispo_model.io_contract import _infer_unit, NPZ_DIMENSIONS
        for field, unit, dimensions in (
            ('ev_enrolled_service_fraction', 'fraction_of_eligible_service_pool', 'province'),
            ('ev_bidirectional_service_fraction', 'fraction_of_eligible_service_pool', 'province'),
            ('ev_v1g_pool_charge', 'GW', 'province,hour'),
            ('ev_v2g_pool_charge', 'GW', 'province,hour'),
            ('ev_v1g_pool_inventory', 'GWh', 'province,hour'),
            ('ev_v2g_pool_inventory', 'GWh', 'province,hour')):
            self.assertEqual(_infer_unit(field), unit)
            self.assertEqual(NPZ_DIMENSIONS['flexible_load_dispatch.npz'][field], dimensions)

    def test_unqualified_formal_profile_cannot_launch(self):
        with self.assertRaisesRegex(ValueError, 'PORTFOLIO_STAGE_A_NOT_QUALIFIED'):
            require_qualified_portfolio_stage_a()

    def test_formal_cli_blocks_before_loading_inputs(self):
        from scripts import run_cispo_2030_full_year as runner
        argv = ['run_cispo_2030_full_year.py', '--horizon', 'full_year',
            '--scenario-config', 'config/scenarios/case3_thermal_ev_v5.json',
            '--solver-config', 'config/solver_profiles/barrier_stagea_portfolio_v1_threads44.json',
            '--formulation-config', 'config/formulation_profiles/annual_capacity_link_rows_8192_v1.json',
            '--archive-original-model']
        with patch.object(sys, 'argv', argv), patch.object(runner, 'load_model_data',
                side_effect=AssertionError('input loading must not be reached')):
            with self.assertRaisesRegex(SystemExit, 'PORTFOLIO_STAGE_A_NOT_QUALIFIED'):
                runner.main()

    def test_full_year_portfolio_cannot_bypass_guard_with_other_solver_profile(self):
        from scripts import run_cispo_2030_full_year as runner
        argv = ['run_cispo_2030_full_year.py', '--horizon', 'full_year',
            '--scenario-config', 'config/scenarios/case2_ev_v5.json']
        with patch.object(sys, 'argv', argv), patch.object(runner, 'load_model_data',
                side_effect=AssertionError('input loading must not be reached')):
            with self.assertRaisesRegex(SystemExit, 'PORTFOLIO_STAGE_A_NOT_QUALIFIED'):
                runner.main()

    def test_state_cannot_cross_scenarios_or_same_name_configuration_changes(self):
        config = load_model_config(scenario_path='config/scenarios/case1_thermal_v5.json')
        scenario_id = config.raw['scenario']['id']
        sha = hashlib.sha256(config.scenario_path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'solve_report.json').write_text(json.dumps(dict(status='OPTIMAL',
                result_use='SCIENTIFIC_PRODUCTION', planning_year=2030, scenario_id=scenario_id)), encoding='utf-8')
            (root/'solution_qc.json').write_text(
                '{"status":"PASS","hard_checks":{"physical":true}}', encoding='utf-8')
            (root/'run_identity.json').write_text(json.dumps(dict(analysis_case=dict(
                scenario_configuration=dict(sha256=sha)))), encoding='utf-8')
            state = write_planning_state(root, config=config, previous_state=PlanningState.empty(2025),
                new_cohorts=pd.DataFrame(columns=STATE_COLUMNS), source_solution_qc='solution_qc.json',
                state_use='SCIENTIFIC_PRODUCTION')
            finalize_result_manifest(root, config)
            PlanningState.load(state, expected_boundary_year=2030,
                expected_scenario_id=scenario_id, expected_scenario_sha256=sha)
            with self.assertRaisesRegex(ValueError, 'scenario mismatch'):
                PlanningState.load(state, expected_boundary_year=2030, expected_scenario_id=CASES[1])
            with self.assertRaisesRegex(ValueError, 'configuration SHA256 mismatch'):
                PlanningState.load(state, expected_boundary_year=2030,
                    expected_scenario_id=scenario_id, expected_scenario_sha256='changed')
            # Even internally rehashed preservation evidence is not acceptance.
            solve = json.loads((root/'solve_report.json').read_text(encoding='utf-8'))
            solve['scientifically_accepted'] = False
            (root/'solve_report.json').write_text(json.dumps(solve), encoding='utf-8')
            metadata_path = state/'state_metadata.json'
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            metadata['source_solve_report_sha256'] = hashlib.sha256(
                (root/'solve_report.json').read_bytes()).hexdigest()
            metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
            finalize_result_manifest(root, config)
            with self.assertRaisesRegex(ValueError, 'strict scientific acceptance'):
                PlanningState.load(state, expected_boundary_year=2030,
                    expected_scenario_id=scenario_id, expected_scenario_sha256=sha)


if __name__ == '__main__':
    unittest.main()
