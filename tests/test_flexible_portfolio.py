"""Physical adversarial gates for the three optional V5 portfolios."""
from __future__ import annotations
from types import SimpleNamespace
import copy
import json
import unittest
import gurobipy as gp
import numpy as np
import pandas as pd
from cispo_model.config import load_model_config
from cispo_model.data import FlexibleLoadV4Data
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.flexible_portfolio import audit_ev_pools
from cispo_model.solution_export import _value

CASES = ('case1_thermal_v5', 'case2_ev_v5', 'case3_thermal_ev_v5')


def fixture(hours=24, provinces=2):
    shape = (provinces, hours)
    load_ev = np.broadcast_to((1 + .3 * np.sin(np.arange(hours) * 2 * np.pi / 24))[None, :], shape).copy()
    load_ev *= np.arange(1, provinces + 1)[:, None]
    components = dict(base_residual=np.full(shape, 3.), heating=np.full(shape, .5),
                      cooling=np.full(shape, .5), ev=load_ev)
    parameters = {c: {key: np.full(provinces, value) for key, value in dict(
        retention_per_hour=.94 if c == 'heating' else .92,
        charge_efficiency=.98, discharge_efficiency=.97,
        positive_state_duration_hours=4., negative_state_duration_hours=4.).items()}
        for c in ('heating', 'cooling')}
    costs = {c: {key: np.full(provinces, value) for key, value in dict(
        enablement_cost_yuan_per_kw_year=1., activation_cost_yuan_per_mwh=1.,
        comfort_debt_cost_yuan_per_gwh_hour=0., infrastructure_cost_yuan_per_kw_year=1.,
        degradation_cost_yuan_per_mwh=1.).items()} for c in ('heating','cooling','ev_v1g','ev_v2g')}
    v5 = FlexibleLoadV4Data(
        thermal_envelopes_gw={f'{c}_{d}': np.full(shape, .25) for c in ('heating','cooling') for d in ('up','down')},
        thermal_availability={c: np.ones(shape) for c in ('heating','cooling')},
        thermal_parameters=parameters,
        ev_availability=dict(connected_vehicle_fraction=np.ones(shape),
                             available_charge_power_gw=np.full(shape,.5),
                             available_discharge_power_gw=np.full(shape,.3),
                             fleet_energy_capacity_gwh=np.full(shape,2.)),
        ev_mobility=dict(driving_energy_withdrawal_gwh=.94*.15*load_ev,
                         minimum_departure_energy_gwh=np.zeros(shape)),
        service_costs=costs, contract_version='v5')
    return SimpleNamespace(load_gw=sum(components.values()), load_components_gw=components,
                           flexible_load_v4=v5, provinces=pd.DataFrame({'province_code': np.arange(11,11+provinces)}))


class PortfolioTests(unittest.TestCase):
    def build(self, case='case3_thermal_ev_v5', hours=24, data=None, mutate=None, start=0):
        config = load_model_config(scenario_path=f'config/scenarios/{case}.json')
        if mutate:
            mutate(config.raw)
            config.validate()
        data = data or fixture(hours)
        model = gp.Model('portfolio_gate')
        model.Params.OutputFlag = 0
        model.Params.Threads = 2
        self.addCleanup(model.dispose)
        block = attach_flexible_load(model, config, data, hours=hours, hour_start=start)
        return config, data, model, block

    def check_pools(self, config, data, block, hours=24, start=0):
        v5 = data.flexible_load_v4
        values = {key: _value(value) for key, value in block.variables.items() if key.startswith('ev_') or key == 'actual_ev_load'}
        qc = audit_ev_pools(settings=config.raw['flexible_load'],
            baseline_ev=data.load_components_gw['ev'][:, start:start+hours],
            availability={k:v[:, start:start+hours] for k,v in v5.ev_availability.items()},
            full_availability=v5.ev_availability,
            mobility={k:v[:, start:start+hours] for k,v in v5.ev_mobility.items()},
            capacity=_value(block.variables['flexible_service_capacity']), values=values)
        self.assertLessEqual(max(qc.values()), 1e-7, qc)
        return qc

    def test_all_cases_zero_contract_recover_identical_base_demand_and_zero_cost(self):
        for case in CASES:
            with self.subTest(case=case):
                config, data, model, block = self.build(case)
                model.addConstr(block.variables['flexible_service_capacity'] == 0)
                model.setObjective(gp.quicksum(block.costs.values()))
                model.optimize()
                self.assertEqual(model.Status, gp.GRB.OPTIMAL)
                np.testing.assert_allclose(_value(block.effective_load_gw), data.load_gw, atol=1e-9)
                self.assertAlmostEqual(model.ObjVal, 0.)
                self.assertTrue(all(hasattr(value, 'getValue') for value in block.costs.values()))
                self.check_pools(config, data, block)

    def test_disabled_services_have_no_hourly_decisions(self):
        for case in CASES[:2]:
            config, data, model, block = self.build(case)
            model.update()
            from cispo_model.flexible_portfolio import estimate_portfolio_size
            self.assertEqual(estimate_portfolio_size(config.raw['flexible_load'], data, 24),
                             (model.NumVars, model.NumConstrs))
            names = [v.VarName for v in model.getVars()]
            if case == CASES[0]:
                self.assertFalse(any(name.startswith('ev_') for name in names))
            else:
                self.assertFalse(any(name.startswith(('heating_', 'cooling_')) for name in names))
            self.assertNotIn('firm_flexible_capacity_credit', block.variables)

    def test_v2g_energy_losses_and_separate_pool_qc(self):
        config, data, model, block = self.build()
        model.addConstr(block.variables['ev_mobility_discharge'][:, 12] >= .02)
        model.setObjective(gp.quicksum(block.costs.values()))
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        self.check_pools(config, data, block)
        d = _value(block.variables['ev_mobility_discharge']).sum(axis=1)
        net_delta = (_value(block.actual_components_gw['ev']) - data.load_components_gw['ev']).sum(axis=1) - d
        np.testing.assert_allclose(net_delta, (1/(.94*.94)-1)*d, atol=1e-8)

    def test_small_v2g_contract_cannot_borrow_v1g_inventory(self):
        config, data, model, block = self.build()
        model.addConstr(block.variables['ev_enrolled_service_fraction'] == 1.)
        model.addConstr(block.variables['ev_bidirectional_service_fraction'] == .01)
        model.addConstr(block.variables['ev_v2g_pool_inventory'][0, 0] >= .1)
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.INFEASIBLE)

    def test_v2g_disabled_is_valid_v1g_and_no_discharge(self):
        config, data, model, block = self.build(mutate=lambda raw: raw['flexible_load']['ev_v2g'].update(enabled=False))
        model.addConstr(block.variables['ev_enrolled_service_fraction'] == .5)
        model.setObjective(gp.quicksum(block.costs.values()))
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        self.check_pools(config, data, block)
        self.assertEqual(_value(block.variables['ev_mobility_discharge']).sum(), 0)

    def test_thermal_shared_contract_cannot_be_used_twice(self):
        config, data, model, block = self.build(CASES[0])
        model.addConstr(block.variables['flexible_service_capacity'][:, 0] == .1)
        model.addConstr(block.variables['heating_shift_up'][0, 0] >= .08)
        model.addConstr(block.variables['heating_shift_down'][0, 0] >= .08)
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.INFEASIBLE)

    def test_annual_enrollment_normalization_does_not_change_in_nonleading_window(self):
        data = fixture(48)
        data.flexible_load_v4.ev_availability['available_charge_power_gw'][:, 0] = 1.
        config, data, model, block = self.build(CASES[1], hours=12, data=data, start=24)
        model.addConstr(block.variables['ev_enrolled_service_fraction'] == .5)
        model.setObjective(gp.quicksum(block.costs.values()))
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        np.testing.assert_allclose(_value(block.variables['flexible_service_capacity'])[:, 2], .5)
        self.check_pools(config, data, block, hours=12, start=24)

    def test_optional_portfolio_cannot_silently_enable_unproven_firm_credit(self):
        with self.assertRaisesRegex(ValueError, 'separately qualified'):
            self.build(mutate=lambda raw: raw['security'].update(capacity_margin_load_basis='firm_flexibility_derated_v1'))

    def test_unbounded_quality_location_is_strict_json_serializable(self):
        from cispo_model.diagnostics import _solution_quality_location
        model = SimpleNamespace(NumVars=1, NumConstrs=0, DualVioIndex=0)
        variable = SimpleNamespace(VarName='unbounded', LB=0., UB=float('inf'), X=0., RC=0.)
        row = _solution_quality_location(model, 'DualVioIndex', kind='dual',
                                         variables=[variable], constraints=[])
        self.assertIsNone(row['upper_bound'])
        self.assertTrue(row['upper_bound_unbounded'])
        json.dumps(row, allow_nan=False)

    def test_cloud_budget_fails_closed_above_four_hours(self):
        from cispo_model.portfolio_release import validate_cloud_budget
        self.assertEqual(validate_cloud_budget('04:00:00'), 14400)
        self.assertEqual(validate_cloud_budget('00:15:00'), 900)
        for invalid in ('04:00:01', '1-00:00:00', 'UNLIMITED', '', '00:00:00', '03:60:00'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_cloud_budget(invalid)

    def test_portfolio_stage_a_uses_its_own_canonical_identity(self):
        from scripts.run_cispo_2030_full_year import (
            require_canonical_direct_nonbasic_profiles, cloud_full_year_profile_role,
            CLOUD_FINAL_STAGE_A_PROFILE_IDS, PORTFOLIO_STAGE_A_PROFILE_ID)
        cfg = load_model_config(scenario_path='config/scenarios/case3_thermal_ev_v5.json',
            solver_path='config/solver_profiles/barrier_stagea_portfolio_v1_threads44.json',
            formulation_path='config/formulation_profiles/annual_capacity_link_rows_8192_v1.json')
        require_canonical_direct_nonbasic_profiles(cfg)
        self.assertEqual(cloud_full_year_profile_role(PORTFOLIO_STAGE_A_PROFILE_ID), 'STAGE_A')
        self.assertNotIn(PORTFOLIO_STAGE_A_PROFILE_ID, CLOUD_FINAL_STAGE_A_PROFILE_IDS)
        # The author-selected stopping target was changed on 2026-09-07;
        # canonical-profile validation must preserve that recorded choice.
        self.assertEqual(cfg.raw['numerics']['barrier_convergence_tolerance'], 1e-4)


if __name__ == '__main__':
    unittest.main()
