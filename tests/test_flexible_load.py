from __future__ import annotations

from types import SimpleNamespace
import unittest

import gurobipy as gp
import numpy as np

from cispo_model.config import load_model_config
from cispo_model.data import FlexibleLoadV4Data
from cispo_model.flexible_load import (
    _capacity_upper_from_profile,
    _ev_backlog_bounds,
    _ev_deadline_backlog_bounds,
    _ev_v1g_shift_bounds,
    _thermal_envelope_state_bounds,
    _thermal_state_bounds,
    _thermal_shift_bounds,
    attach_flexible_load,
    make_day_slices,
)


class FlexibleLoadContractTests(unittest.TestCase):
    def test_wave_integrated_base_and_v3_v2g_overlay_are_explicit(self):
        base = load_model_config()
        comfort_v2g = load_model_config(
            scenario_path=(
                "config/scenarios/flexible_load_comfort_v3_v2g_5pct.json"
            )
        )
        self.assertEqual(base.raw["scenario"]["id"], "base")
        self.assertFalse(base.raw["features"]["flexible_load"])
        self.assertTrue(base.raw["features"]["wave_energy"])
        self.assertTrue(comfort_v2g.raw["features"]["wave_energy"])
        self.assertTrue(comfort_v2g.raw["features"]["flexible_load"])
        self.assertEqual(
            comfort_v2g.raw["flexible_load"]["formulation"],
            "comfort_envelope_v3",
        )
        self.assertTrue(comfort_v2g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertEqual(
            comfort_v2g.raw["flexible_load"]["ev_v2g"][
                "power_fraction_of_daily_baseline_peak"
            ],
            0.05,
        )

    def test_v4_is_separate_with_v1g_central_and_v2g_sensitivity(self):
        v4_v1g = load_model_config(
            scenario_path="config/scenarios/flexible_load_comfort_v4_v1g.json"
        )
        v4_v2g = load_model_config(
            scenario_path=(
                "config/scenarios/flexible_load_comfort_v4_v2g_sensitivity.json"
            )
        )
        self.assertEqual(
            v4_v1g.raw["flexible_load"]["formulation"],
            "service_constrained_v4",
        )
        self.assertEqual(
            v4_v1g.raw["flexible_load"]["state_boundary"],
            "periodic_selected_horizon_v1",
        )
        self.assertFalse(v4_v1g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(v4_v2g.raw["flexible_load"]["ev_v2g"]["enabled"])

    def test_v4_contract_capacity_upper_follows_connection_availability(self):
        upper = _capacity_upper_from_profile(
            np.asarray([[0.0, 2.0, 1.0]]),
            np.asarray([[0.0, 0.5, 0.25]]),
            label="test",
        )
        np.testing.assert_allclose(upper, [4.0])

    def test_v4_two_province_fleet_soc_small_linear_gate(self):
        config = load_model_config(
            scenario_path="config/scenarios/flexible_load_comfort_v4_v1g.json"
        )
        shape = (2, 4)
        thermal_parameters = {
            component: {
                "retention_per_hour": np.asarray([1.0, 1.0]),
                "charge_efficiency": np.asarray([1.0, 1.0]),
                "discharge_efficiency": np.asarray([1.0, 1.0]),
                "positive_state_duration_hours": np.asarray([2.0, 2.0]),
                "negative_state_duration_hours": np.asarray([2.0, 2.0]),
            }
            for component in ("heating", "cooling")
        }
        service_costs = {
            service: {
                "enablement_cost_yuan_per_kw_year": np.asarray([1.0, 2.0]),
                "activation_cost_yuan_per_mwh": np.asarray([1.0, 2.0]),
                "comfort_debt_cost_yuan_per_gwh_hour": np.asarray([1.0, 2.0]),
            }
            for service in ("heating", "cooling", "ev_v1g", "ev_v2g")
        }
        v4 = FlexibleLoadV4Data(
            thermal_envelopes_gw={
                "heating_up": np.ones(shape),
                "heating_down": np.ones(shape),
                "cooling_up": np.ones(shape),
                "cooling_down": np.ones(shape),
            },
            thermal_availability={"heating": np.ones(shape), "cooling": np.ones(shape)},
            thermal_parameters=thermal_parameters,
            ev_availability={
                "connected_vehicle_fraction": np.ones(shape),
                "available_charge_power_gw": np.full(shape, 2.0),
                "available_discharge_power_gw": np.full(shape, 1.0),
                "fleet_energy_capacity_gwh": np.full(shape, 10.0),
            },
            ev_mobility={
                "driving_energy_withdrawal_gwh": np.full(shape, 0.235),
                "minimum_departure_energy_gwh": np.zeros(shape),
            },
            service_costs=service_costs,
        )
        data = SimpleNamespace(
            load_gw=np.full(shape, 3.0),
            load_components_gw={
                "base_residual": np.ones(shape),
                "heating": np.zeros(shape),
                "cooling": np.zeros(shape),
                "ev": np.ones(shape),
            },
            flexible_load_v4=v4,
        )
        model = gp.Model("v4_small_gate")
        model.Params.OutputFlag = 0
        block = attach_flexible_load(model, config, data, hours=shape[1])
        model.update()
        self.assertTrue(
            all(hasattr(expression, "getValue") for expression in block.costs.values())
        )
        # A correct two-province formulation has no accidental p-by-p
        # first-hour transition block.
        self.assertEqual(model.NumConstrs, 56 * shape[0])
        model.setObjective(gp.quicksum(block.costs.values()), gp.GRB.MINIMIZE)
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        np.testing.assert_allclose(
            block.variables["ev_mobility_charge"].X.sum(axis=1),
            [1.0, 1.0],
            atol=1e-8,
        )

    def test_v5_integrates_paid_v1g_v2g_and_derated_firm_credit(self):
        config = load_model_config(
            scenario_path="config/scenarios/flex_integrated_v5_central.json"
        )
        self.assertEqual(
            config.raw["flexible_load"]["shift_throughput_cost_yuan_per_mwh"],
            300.0,
        )
        self.assertEqual(
            config.raw["flexible_load"]["degradation_cost_yuan_per_mwh"],
            400.0,
        )
        shape = (2, 4)
        thermal_parameters = {
            component: {
                "retention_per_hour": np.asarray([1.0, 1.0]),
                "charge_efficiency": np.asarray([1.0, 1.0]),
                "discharge_efficiency": np.asarray([1.0, 1.0]),
                "positive_state_duration_hours": np.asarray([2.0, 2.0]),
                "negative_state_duration_hours": np.asarray([2.0, 2.0]),
            }
            for component in ("heating", "cooling")
        }
        service_costs = {
            service: {
                "enablement_cost_yuan_per_kw_year": np.asarray([1.0, 2.0]),
                "activation_cost_yuan_per_mwh": np.asarray([1.0, 2.0]),
                "comfort_debt_cost_yuan_per_gwh_hour": np.zeros(2),
                "infrastructure_cost_yuan_per_kw_year": (
                    np.asarray([1.0, 2.0])
                    if service == "ev_v2g"
                    else np.zeros(2)
                ),
                "degradation_cost_yuan_per_mwh": (
                    np.asarray([1.0, 2.0])
                    if service == "ev_v2g"
                    else np.zeros(2)
                ),
            }
            for service in ("heating", "cooling", "ev_v1g", "ev_v2g")
        }
        v5 = FlexibleLoadV4Data(
            thermal_envelopes_gw={
                "heating_up": np.ones(shape),
                "heating_down": np.ones(shape),
                "cooling_up": np.ones(shape),
                "cooling_down": np.ones(shape),
            },
            thermal_availability={
                "heating": np.ones(shape),
                "cooling": np.ones(shape),
            },
            thermal_parameters=thermal_parameters,
            ev_availability={
                "connected_vehicle_fraction": np.ones(shape),
                "available_charge_power_gw": np.full(shape, 2.0),
                "available_discharge_power_gw": np.full(shape, 1.0),
                "fleet_energy_capacity_gwh": np.full(shape, 10.0),
            },
            ev_mobility={
                "driving_energy_withdrawal_gwh": np.full(shape, 0.141),
                "minimum_departure_energy_gwh": np.zeros(shape),
            },
            service_costs=service_costs,
            contract_version="v5",
        )
        data = SimpleNamespace(
            load_gw=np.full(shape, 3.0),
            load_components_gw={
                "base_residual": np.ones(shape),
                "heating": np.full(shape, 0.5),
                "cooling": np.full(shape, 0.5),
                "ev": np.ones(shape),
            },
            flexible_load_v4=v5,
        )
        model = gp.Model("v5_small_gate")
        model.Params.OutputFlag = 0
        block = attach_flexible_load(model, config, data, hours=shape[1])
        model.update()
        self.assertEqual(
            set(block.costs),
            {
                "flexible_load_v5_enablement",
                "flexible_load_v5_v2g_infrastructure",
                "flexible_load_v5_thermal_activation",
                "flexible_load_v5_ev_v1g_relocation",
                "flexible_load_v5_ev_v2g_participation",
                "flexible_load_v5_ev_v2g_degradation",
            },
        )
        model.addConstr(
            block.variables["ev_mobility_discharge"][0, 0] >= 0.1,
            name="force_v2g_replenishment_test",
        )
        model.setObjective(gp.quicksum(block.costs.values()), gp.GRB.MINIMIZE)
        model.optimize()
        self.assertEqual(model.Status, gp.GRB.OPTIMAL)
        capacities = block.variables["flexible_service_capacity"].X
        self.assertTrue(np.all(capacities[:, 3] <= capacities[:, 2] + 1e-9))
        firm = block.variables["firm_flexible_capacity_credit"].X
        upper = block.variables["firm_flexible_capacity_credit_upper"]
        self.assertTrue(np.all(firm <= upper + 1e-9))
        self.assertGreater(
            float(block.variables["ev_mobility_charge_deviation"].X.sum()),
            0.0,
        )
        np.testing.assert_allclose(
            block.variables["ev_mobility_v1g_relocated"].X,
            0.0,
            atol=1e-8,
        )
        self.assertAlmostEqual(
            float(
                block.costs[
                    "flexible_load_v5_ev_v1g_relocation"
                ].getValue()
            ),
            0.0,
            places=8,
        )

    def test_day_slices_cover_partial_horizon_once(self):
        slices = make_day_slices(25, 24)
        covered = [hour for item in slices for hour in range(item.start, item.stop)]
        self.assertEqual(covered, list(range(25)))
        self.assertEqual([(item.start, item.stop) for item in slices], [(0, 24), (24, 25)])

    def test_thermal_shift_bounds_follow_daily_peak_and_baseline(self):
        baseline = np.asarray([[0.0, 2.0, 4.0, 1.0]])
        up, down = _thermal_shift_bounds(
            baseline, (slice(0, 4),), 0.25, 0.5
        )
        np.testing.assert_allclose(down, 0.25 * baseline)
        np.testing.assert_allclose(up, np.full_like(baseline, 2.0))

    def test_ev_v1g_bounds_preserve_fixed_share_and_power_envelope(self):
        baseline = np.asarray([[0.0, 1.0, 2.0, 1.0]])
        up, down = _ev_v1g_shift_bounds(
            baseline, (slice(0, 4),), 0.5, 2.0
        )
        np.testing.assert_allclose(down, 0.5 * baseline)
        np.testing.assert_allclose(up, [[2.0, 1.0, 0.0, 1.0]])

    def test_thermal_state_bounds_add_duration_scaled_inventory(self):
        baseline = np.asarray([[0.0, 2.0, 4.0, 1.0]])
        up, down, state = _thermal_state_bounds(
            baseline,
            (slice(0, 4),),
            maximum_reduction_fraction=0.25,
            maximum_increase_fraction_of_daily_peak=0.5,
            duration_hours=3.0,
        )
        np.testing.assert_allclose(down, 0.25 * baseline)
        np.testing.assert_allclose(up, np.full_like(baseline, 2.0))
        np.testing.assert_allclose(state, np.full_like(baseline, 6.0))

    def test_ev_backlog_bounds_keep_baseline_feasible(self):
        baseline = np.asarray([[0.0, 1.0, 4.0, 1.0]])
        up, down, queue = _ev_backlog_bounds(
            baseline,
            (slice(0, 4),),
            shiftable_energy_fraction=0.5,
            maximum_power_to_daily_average_ratio=2.0,
            maximum_queue_duration_hours=6.0,
        )
        np.testing.assert_allclose(down, 0.5 * baseline)
        # The observed baseline peak is retained even when it exceeds
        # ratio * daily mean, so the zero-shift solution remains feasible.
        np.testing.assert_allclose(up, [[4.0, 3.0, 0.0, 3.0]])
        np.testing.assert_allclose(queue, np.full_like(baseline, 4.5))

    def test_external_thermal_envelope_gets_duration_scaled_state(self):
        up = np.asarray([[0.0, 2.0, 1.0, 0.0]])
        down = np.asarray([[1.0, 0.0, 3.0, 0.0]])
        state = _thermal_envelope_state_bounds(
            up, down, (slice(0, 4),), duration_hours=2.0
        )
        np.testing.assert_allclose(state, np.full_like(up, 6.0))

    def test_ev_deadline_backlog_uses_rolling_movable_energy(self):
        baseline = np.asarray([[1.0, 2.0, 3.0, 4.0, 5.0]])
        _, down, queue = _ev_deadline_backlog_bounds(
            baseline,
            (slice(0, 5),),
            shiftable_energy_fraction=0.5,
            maximum_power_to_daily_average_ratio=2.0,
            maximum_queue_duration_hours=3.0,
        )
        np.testing.assert_allclose(down, 0.5 * baseline)
        np.testing.assert_allclose(queue, [[0.5, 1.5, 3.0, 4.5, 6.0]])


if __name__ == "__main__":
    unittest.main()
