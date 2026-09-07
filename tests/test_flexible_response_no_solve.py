"""Response contract adversarial checks; optimization is explicitly forbidden."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gurobipy as gp
import numpy as np

from cispo_model.config import load_model_config
from cispo_model.flexible_load import attach_flexible_load
from cispo_model.flexible_response import (
    RESPONSE_CONTRACT, audit_thermal_response, normal_participation_fraction,
    resolved_service_costs, thermal_contract_profile, validate_response_contract,
)
from cispo_model.flexible_portfolio import audit_ev_pools
from cispo_model.offline_solution import audit_saved_primal, offline_artifacts
from cispo_model.solution_export import _value
from test_flexible_portfolio import fixture, CASES

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "config/scenarios/response_candidates_v1"


class ResponseNoSolveTests(unittest.TestCase):
    def setUp(self):
        for method in ("optimize", "optimizeAsync", "presolve", "feasRelax", "feasRelaxS"):
            if hasattr(gp.Model, method):
                guard = patch.object(gp.Model, method, side_effect=AssertionError(method+" forbidden"))
                guard.start()
                self.addCleanup(guard.stop)

    def build(self, config, data=None, hours=24, start=0):
        model = gp.Model("response_no_solve")
        model.Params.OutputFlag = 0
        self.addCleanup(model.dispose)
        data = data or fixture()
        block = attach_flexible_load(model, config, data, hours=hours, hour_start=start)
        model.setObjective(gp.quicksum(block.costs.values()))
        model.update()
        return model, block

    def test_all_candidates_validate_and_recover_base_at_zero_contract(self):
        paths = [p for p in CANDIDATES.glob("*.json") if ".manifest." not in p.name]
        self.assertEqual(len(paths), 11)
        for path in paths:
            with self.subTest(path=path.name):
                config = load_model_config(scenario_path=path)
                data = fixture()
                model, block = self.build(config, data)
                vector = np.zeros(model.NumVars)
                self.assertEqual(audit_saved_primal(model, vector)["status"], "PASS")
                view = offline_artifacts(SimpleNamespace(model=model, variables={"effective": block.effective_load_gw},
                    cost_components=block.costs, index={}), vector, None)
                np.testing.assert_array_equal(_value(view.variables["effective"]), data.load_gw)
                self.assertEqual(view.model.ObjVal, 0)

    def test_central_refinement_adds_no_variables_rows_or_nonzeros(self):
        for case in CASES:
            old = load_model_config(scenario_path=f"config/scenarios/{case}.json")
            new = load_model_config(scenario_path=CANDIDATES/f"{case}_response_v1.json")
            old_model, _ = self.build(old)
            new_model, _ = self.build(new)
            self.assertEqual(old_model.NumVars, new_model.NumVars)
            self.assertEqual(old_model.NumConstrs, new_model.NumConstrs)
            self.assertEqual(old_model.NumNZs, new_model.NumNZs)
            self.assertEqual(new_model.NumBinVars, 0)
            np.testing.assert_allclose(old_model.getAttr("Obj"), new_model.getAttr("Obj"))

    def test_partial_thermal_contract_cannot_cherry_pick_full_population(self):
        annual, up_c, down_c = thermal_contract_profile(np.array([[.1, 1.]]), np.array([[.2, .5]]), np.ones((1, 2)))
        np.testing.assert_array_equal(annual, [1.])
        cfg = load_model_config(scenario_path=CANDIDATES/"case1_thermal_v5_response_v1.json")
        # K=.1 used to allow .1 GW in the low-response hour; proportional
        # enrollment permits only .01 GW. This is a tightening, not equivalence.
        qc = audit_thermal_response(cfg.raw["flexible_load"], component="heating",
            full_up=np.array([[.1, 1.]]), full_down=np.array([[.2, .5]]), full_availability=np.ones((1, 2)),
            selected_hours=slice(0, 1), capacity=np.array([.1]), up=np.array([[.1]]), down=np.array([[0.]]))
        self.assertAlmostEqual(qc["heating_proportional_up_violation_gw"], .09)
        self.assertTrue((up_c <= 1).all() and (down_c <= 1).all())

    def test_annual_normalization_survives_window_and_zero_profiles(self):
        data = fixture(hours=48, provinces=1)
        data.flexible_load_v4.thermal_envelopes_gw["heating_up"][:] = .1
        data.flexible_load_v4.thermal_envelopes_gw["heating_up"][0, 30] = 1.
        config = load_model_config(scenario_path=CANDIDATES/"case1_thermal_v5_response_v1.json")
        for start, name_index in [(0, 0), (24, 0)]:
            model, _ = self.build(config, data, start=start)
            row = model.getConstrByName(f"heating_contracted_increase_power[{name_index}]")
            k = model.getVarByName("flexible_service_capacity_gw[0,0]")
            self.assertAlmostEqual(model.getCoeff(row, k), -.1)
        zero = np.zeros((2, 3))
        result = thermal_contract_profile(zero, zero, zero)
        self.assertTrue(all(np.isfinite(x).all() and (x == 0).all() for x in result))

    def test_tiny_positive_profiles_normalize_without_large_lp_coefficients(self):
        tiny = np.array([[1e-100, 2e-100]])
        annual, up, down = thermal_contract_profile(tiny, tiny, np.ones_like(tiny))
        np.testing.assert_allclose(up, [[.5, 1.]])
        self.assertEqual(annual[0], 2e-100)

    def test_ev_willingness_and_infrastructure_are_independent_bounds(self):
        config = load_model_config(scenario_path=CANDIDATES/"case2_ev_v5_response_v1.json")
        response = config.raw["flexible_load"]["response_contract"]
        response["maximum_enrollment_fraction"]["ev_v2g"] = .5
        response["v2g_infrastructure_fraction"] = .25
        model, _ = self.build(config)
        beta = model.getVarByName("ev_bidirectional_service_fraction[0]")
        alpha = model.getVarByName("ev_enrolled_service_fraction[0]")
        row = model.getConstrByName("ev_pool_participation_nesting[0]")
        self.assertAlmostEqual(beta.UB, .25*.1/.15)
        self.assertAlmostEqual(model.getCoeff(row, alpha), -.5*.1/.15)

    def test_nonzero_ev_service_witness_and_adversarial_qc(self):
        config = load_model_config(scenario_path=CANDIDATES/"case3_thermal_ev_v5_response_sub1_v1.json")
        data = fixture()
        model, block = self.build(config, data)
        vector = np.zeros(model.NumVars)
        alpha, beta, rho = .6, .02, .1/.15
        for variable in model.getVars():
            name = variable.VarName
            if name.startswith("ev_enrolled_service_fraction["): vector[variable.index] = alpha
            elif name.startswith("ev_bidirectional_service_fraction["): vector[variable.index] = beta
            elif name.startswith("flexible_service_capacity_gw["):
                p, c = map(int, name.split("[")[1].rstrip("]").split(","))
                if c == 2: vector[variable.index] = .5*alpha
                elif c == 3: vector[variable.index] = .3*beta/rho
            elif name.startswith(("ev_v1g_pool_charge_gw[", "ev_v2g_pool_charge_gw[")):
                p, t = map(int, name.split("[")[1].rstrip("]").split(","))
                share = alpha-beta if "v1g" in name else beta
                vector[variable.index] = share*.15*data.load_components_gw["ev"][p,t]
        self.assertEqual(audit_saved_primal(model, vector)["status"], "PASS")
        view = offline_artifacts(SimpleNamespace(model=model, variables=block.variables, cost_components=block.costs, index={}), vector, None)
        values = {k: _value(v) for k,v in view.variables.items() if k.startswith("ev_") or k=="actual_ev_load"}
        service = data.flexible_load_v4
        args = dict(settings=config.raw["flexible_load"], baseline_ev=data.load_components_gw["ev"],
            availability=service.ev_availability, full_availability=service.ev_availability,
            mobility=service.ev_mobility, capacity=_value(view.variables["flexible_service_capacity"]), values=values)
        self.assertLessEqual(max(audit_ev_pools(**args).values()), 1e-12)
        values["ev_bidirectional_service_fraction"] = np.full(2, .2)
        self.assertGreater(audit_ev_pools(**args)["response_v2g_willingness_violation"], .1)

    def test_cost_sensitivity_uses_existing_ranges_without_mutating_input(self):
        config = load_model_config(scenario_path=CANDIDATES/"case3_thermal_ev_v5_response_cost_low_v1.json")
        costs = fixture().flexible_load_v4.service_costs
        original = deepcopy(costs)
        result = resolved_service_costs(config.raw["flexible_load"], costs)
        self.assertAlmostEqual(result["ev_v2g"]["degradation_cost_yuan_per_mwh"][0], 250/400)
        for service, fields in costs.items():
            for key, value in fields.items():
                np.testing.assert_array_equal(value, original[service][key])
        model, _ = self.build(config)
        # All costs in this fixture start at 1. Cost weights remain finite.
        self.assertTrue(np.isfinite(model.getAttr("Obj")).all())
        self.assertAlmostEqual(model.getVarByName("cooling_shift_up_gw_active[0]").Obj, .001*100/300)
        self.assertAlmostEqual(model.getVarByName("ev_mobility_discharge_gw[0,0]").Obj, .001*(100/150+250/400))

    def test_candidate_cannot_bypass_full_year_launch_guard(self):
        import sys
        from scripts import run_cispo_2030_full_year as runner
        argv = ["run_cispo_2030_full_year.py", "--horizon", "full_year", "--scenario-config",
                str(CANDIDATES/"case3_thermal_ev_v5_response_v1.json"),
                "--solver-config", "config/solver_profiles/portfolio_local_gate_v1.json"]
        with patch.object(sys, "argv", argv), patch.object(runner, "load_model_data", side_effect=AssertionError("Must block before data")):
            with self.assertRaisesRegex(SystemExit, "PORTFOLIO_STAGE_A_NOT_QUALIFIED"):
                runner.main()

    def test_invalid_or_silent_response_configuration_fails(self):
        config = load_model_config(scenario_path=CANDIDATES/"case3_thermal_ev_v5_response_v1.json")
        for change in ({"version": "typo"}, {"v2g_infrastructure_fraction": float("nan")},
                       {"maximum_enrollment_fraction": {"ev_v2g": 1.1}},
                       {"cost_multipliers": {"cooling": {"typo_cost": 1}}},
                       {"cost_multipliers": {"cooling": {"activation_cost_yuan_per_mwh": 0}}}):
            settings = deepcopy(config.raw["flexible_load"])
            settings["response_contract"].update(change)
            with self.assertRaises(ValueError): validate_response_contract(settings)
        settings["portfolio_contract"] = None
        with self.assertRaises(ValueError): validate_response_contract(settings)

    def test_paper_participation_distribution_is_transparent_and_monotone(self):
        observed = [normal_participation_fraction(g) for g in (.5, 1., 1.5, 2.)]
        np.testing.assert_allclose(observed, [.1586552539, .5, .8413447461, .9772498681], atol=1e-10)
        self.assertGreater(normal_participation_fraction(0), 0)  # untruncated paper normal


if __name__ == "__main__":
    unittest.main()
