"""Execution scope tests; no solve/presolve is performed."""
from copy import deepcopy
import unittest
from cispo_model.config import load_model_config
from cispo_model.portfolio_release import require_qualified_portfolio_stage_a, validate_cloud_budget
from cispo_model.flexible_load_numerics import assess_flexible_load_solver_compatibility
from scripts.run_cispo_2030_full_year import require_canonical_direct_nonbasic_profiles


class AuthorizedThermalLaunchTests(unittest.TestCase):
    def setUp(self):
        self.config = load_model_config(scenario_path='config/scenarios/case1_thermal_v5.json',
            solver_path='config/solver_profiles/barrier_stagea_portfolio_v1_threads44.json',
            formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')

    def test_canonical_exact_scope_and_default_rejection(self):
        require_canonical_direct_nonbasic_profiles(self.config)
        require_qualified_portfolio_stage_a(self.config, author_authorized=True)
        with self.assertRaises(ValueError):
            require_qualified_portfolio_stage_a(self.config)
        for key, value in (('threads', 32), ('barrier_convergence_tolerance', .01), ('aggregate', 0)):
            config = deepcopy(self.config)
            config.raw['numerics'][key] = value
            with self.assertRaisesRegex(ValueError, 'SCOPE_MISMATCH'):
                require_qualified_portfolio_stage_a(config, author_authorized=True)

    def test_other_year_and_scenarios_remain_blocked(self):
        with self.assertRaises(ValueError):
            require_qualified_portfolio_stage_a(self.config.for_planning_year(2040), author_authorized=True)
        for case in ('case2_ev_v5', 'case3_thermal_ev_v5', 'base'):
            config = deepcopy(self.config)
            config.raw['scenario']['id'] = case
            with self.assertRaises(ValueError):
                require_qualified_portfolio_stage_a(config, author_authorized=True)

    def test_explicit_numerical_route_does_not_waive_uncompressed_risk(self):
        risk = dict(formulation='integrated_service_constrained_v5', heating_state_chain_numerical_risk={
            'automatic_presolve_aggregation_risk': True, 'aggregate_zero_required_for_solve': False})
        self.assertEqual(assess_flexible_load_solver_compatibility(risk, self.config.raw['numerics'])['status'], 'BLOCKED')
        result = assess_flexible_load_solver_compatibility(risk, self.config.raw['numerics'],
                                                          allow_authorized_thermal_nonbasic=True)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['scientific_acceptance_established'])
        risk['heating_state_chain_numerical_risk']['aggregate_zero_required_for_solve'] = True
        self.assertEqual(assess_flexible_load_solver_compatibility(risk, self.config.raw['numerics'],
            allow_authorized_thermal_nonbasic=True)['status'], 'BLOCKED')

    def test_unlimited_only_when_explicit_and_test_budget_unchanged(self):
        self.assertEqual(validate_cloud_budget('UNLIMITED', authorized_seconds=0), 0)
        self.assertEqual(validate_cloud_budget('04:00:00'), 14400)
        for value in ('UNLIMITED', '04:00:01', '14-00:00:00'):
            with self.assertRaises(ValueError):
                validate_cloud_budget(value)
        with self.assertRaises(ValueError):
            validate_cloud_budget('14-00:00:00', authorized_seconds=0)


if __name__ == '__main__':
    unittest.main()
