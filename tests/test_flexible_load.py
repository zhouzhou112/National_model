from __future__ import annotations

from types import SimpleNamespace
import unittest

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import FlexibleLoadV4Data
from cispo_model.flexible_load import (
    _capacity_upper_from_profile,
    _ev_backlog_bounds,
    _ev_deadline_backlog_bounds,
    _ev_v1g_shift_bounds,
    _attach_compressed_thermal_state_transitions,
    _add_sparse_hourly_control,
    _thermal_envelope_state_bounds,
    _thermal_state_bounds,
    _thermal_shift_bounds,
    attach_flexible_load,
    make_day_slices,
    SparseThermalStateView,
)
from cispo_model.flexible_load_numerics import (
    _compressed_thermal_state_audit,
    _compressed_thermal_state_mask,
    _maximum_cyclic_true_run,
    _retained_transition_incoming_gaps,
    _service_effective_load_lower_bound,
    assess_flexible_load_solver_compatibility,
    prebuild_flexible_load_solver_compatibility,
)


class FlexibleLoadContractTests(unittest.TestCase):
    def test_disabled_flexibility_selects_exact_nonleading_window(self):
        config = load_model_config()
        load = np.arange(12, dtype=float).reshape(2, 6)
        components = {
            "base_residual": load.copy(),
            "heating": np.zeros_like(load),
            "cooling": np.zeros_like(load),
            "ev": np.zeros_like(load),
        }
        data = SimpleNamespace(
            load_gw=load,
            load_components_gw=components,
        )
        model = gp.Model("nonleading_flexible_load_window")
        model.Params.OutputFlag = 0
        try:
            block = attach_flexible_load(
                model,
                config,
                data,
                hours=3,
                hour_start=2,
            )
            np.testing.assert_array_equal(
                block.baseline_load_gw,
                load[:, 2:5],
            )
            np.testing.assert_array_equal(
                block.actual_components_gw["base_residual"],
                load[:, 2:5],
            )
        finally:
            model.dispose()

    def test_cyclic_run_and_solver_compatibility_gate_are_explicit(self):
        self.assertEqual(
            _maximum_cyclic_true_run(
                np.array([True, True, False, True])
            ),
            3,
        )
        structural_audit = {
            "formulation": "integrated_service_constrained_v5",
            "heating_state_chain_numerical_risk": {
                "aggregate_zero_required_for_solve": False,
                "automatic_presolve_aggregation_risk": False,
            },
            "cooling_state_chain_numerical_risk": {
                "aggregate_zero_required_for_solve": False,
                "automatic_presolve_aggregation_risk": True,
                "automatic_presolve_aggregation_risk_mitigated": True,
            },
        }
        blocked = assess_flexible_load_solver_compatibility(
            structural_audit,
            {},
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["aggregate_parameter"], 1)
        passed = assess_flexible_load_solver_compatibility(
            structural_audit,
            {
                "crossover": 1,
                "crossover_basis": 1,
            },
        )
        self.assertEqual(passed["status"], "PASS")
        self.assertFalse(passed["aggregate_zero_required"])
        self.assertEqual(passed["accepted_basic_crossover_orders"], [1, 2, 4])
        self.assertEqual(
            passed["required_long_horizon_settings"]["aggregate"],
            "automatic_allowed",
        )
        nonbasic = assess_flexible_load_solver_compatibility(
            structural_audit,
            {
                "method": 2,
                "crossover": 0,
                "solution_target": 1,
                "barrier_convergence_tolerance": 1e-10,
            },
        )
        self.assertEqual(nonbasic["status"], "PASS")
        self.assertTrue(nonbasic["strict_nonbasic_primal_dual_route"])
        self.assertFalse(nonbasic["stable_basic_route"])
        for crossover in (2, 4):
            with self.subTest(crossover=crossover):
                alternative_basic = assess_flexible_load_solver_compatibility(
                    structural_audit,
                    {
                        "method": 2,
                        "crossover": crossover,
                        "crossover_basis": 1,
                    },
                )
                self.assertEqual(alternative_basic["status"], "PASS")
                self.assertTrue(alternative_basic["stable_basic_route"])
        rejected_crossover_three = assess_flexible_load_solver_compatibility(
            structural_audit,
            {
                "method": 2,
                "crossover": 3,
                "crossover_basis": 1,
            },
        )
        self.assertEqual(rejected_crossover_three["status"], "BLOCKED")
        self.assertFalse(rejected_crossover_three["stable_basic_route"])
        legacy = assess_flexible_load_solver_compatibility(
            {
                "formulation": "service_constrained_v4",
                "cooling_state_chain_numerical_risk": {
                    "automatic_presolve_aggregation_risk": True,
                    "aggregate_zero_required_for_solve": True,
                },
            },
            {},
        )
        self.assertEqual(legacy["status"], "PASS")
        self.assertFalse(legacy["stable_crossover_required"])

    def test_prebuild_base_has_no_v5_numerical_contract(self):
        base = load_model_config()
        result = prebuild_flexible_load_solver_compatibility(
            base,
            SimpleNamespace(),
            hours=168,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["formulation"])
        self.assertFalse(result["stable_crossover_required"])

    def test_prebuild_v5_gate_detects_selected_horizon_chain_risk(self):
        service = SimpleNamespace(
            contract_version="v5",
            thermal_envelopes_gw={
                "heating_up": np.array([[1.0, 0.0, 0.0, 0.0, 0.0]]),
                "heating_down": np.zeros((1, 5)),
                "cooling_up": np.ones((1, 5)),
                "cooling_down": np.zeros((1, 5)),
            },
            thermal_parameters={
                "heating": {"retention_per_hour": np.array([0.1])},
                "cooling": {"retention_per_hour": np.array([0.9])},
            },
        )
        data = SimpleNamespace(
            flexible_load_v4=service,
            provinces=pd.DataFrame({"province_code": [11]}),
        )
        common_raw = {
            "features": {"flexible_load": True},
            "flexible_load": {
                "formulation": "integrated_service_constrained_v5",
            },
        }
        unsafe = SimpleNamespace(
            raw={**common_raw, "numerics": {}},
        )
        blocked = prebuild_flexible_load_solver_compatibility(
            unsafe,
            data,
            hours=5,
        )
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertFalse(blocked["aggregate_zero_required"])
        self.assertTrue(blocked["stable_crossover_required"])

        stable = SimpleNamespace(
            raw={
                **common_raw,
                "numerics": {
                    "crossover": 1,
                    "crossover_basis": 1,
                },
            },
        )
        passed = prebuild_flexible_load_solver_compatibility(
            stable,
            data,
            hours=5,
        )
        self.assertEqual(passed["status"], "PASS")
        self.assertFalse(passed["aggregate_zero_required"])

        nonbasic = SimpleNamespace(
            raw={
                **common_raw,
                "numerics": {
                    "method": 2,
                    "crossover": 0,
                    "solution_target": 1,
                    "barrier_convergence_tolerance": 1e-10,
                },
            },
        )
        nonbasic_passed = prebuild_flexible_load_solver_compatibility(
            nonbasic,
            data,
            hours=5,
        )
        self.assertEqual(nonbasic_passed["status"], "PASS")
        self.assertTrue(
            nonbasic_passed["strict_nonbasic_primal_dual_route"]
        )

    def test_sparse_hourly_control_omits_exact_zero_bound_variables(self):
        model = gp.Model("sparse_hourly_control")
        model.Params.OutputFlag = 0
        upper = np.array([[1.0, 0.0], [0.0, 2.0]])
        expression, active, mask = _add_sparse_hourly_control(
            model,
            upper_bound=upper,
            name="test_control",
        )
        model.update()
        self.assertEqual(expression.shape, upper.shape)
        self.assertIsNotNone(active)
        self.assertEqual(active.shape, (2,))
        self.assertEqual(model.NumVars, 2)
        np.testing.assert_array_equal(mask, upper > 0.0)

    def test_compressed_thermal_state_eliminates_only_zero_control_hours(self):
        support = np.array(
            [
                [True, False, False, True, False, False],
                [False, False, False, False, False, False],
            ]
        )
        retained = _compressed_thermal_state_mask(
            support,
            np.array([0.9, 0.9]),
            minimum_transition_coefficient=0.5,
        )
        self.assertTrue(np.all(retained[support]))
        self.assertFalse(retained[1].any())
        audit = _compressed_thermal_state_audit(
            support,
            retained,
            np.array([0.9, 0.9]),
        )
        self.assertEqual(audit["control_support_state_variables"], 2)
        self.assertGreaterEqual(
            audit["minimum_retained_transition_coefficient"],
            0.5,
        )
        self.assertEqual(
            audit["retained_state_variables"]
            + audit["redundant_inactive_state_variables_omitted"],
            support.size,
        )

    def test_sparse_thermal_state_view_reconstructs_hourly_decay(self):
        retained = np.array([[True, False, True, False]])
        view = SparseThermalStateView(
            active=SimpleNamespace(X=np.array([4.0, 2.0])),
            retained_mask=retained,
            retention_per_hour=np.array([0.5]),
        )
        np.testing.assert_allclose(
            view.getValue(),
            np.array([[4.0, 2.0, 2.0, 1.0]]),
        )

    def test_compressed_state_uses_predecessor_to_current_cyclic_gaps(self):
        np.testing.assert_array_equal(
            _retained_transition_incoming_gaps(
                np.array([0, 1, 4]),
                6,
            ),
            np.array([2, 1, 3]),
        )

    def test_compressed_state_matrix_uses_nonuniform_incoming_gaps(self):
        model = gp.Model("compressed_nonuniform_gaps")
        model.Params.OutputFlag = 0
        state = model.addMVar(3, name="state")
        capacity = model.addMVar(1, name="capacity")
        zero_control = gp.MLinExpr.zeros((1, 6))
        _attach_compressed_thermal_state_transitions(
            model,
            active_state=state,
            retained_state_mask=np.array(
                [[True, True, False, False, True, False]]
            ),
            retention_per_hour=np.array([0.5]),
            charge=zero_control,
            discharge=zero_control,
            charge_efficiency=np.array([1.0]),
            discharge_efficiency=np.array([1.0]),
            capacity=capacity,
            positive_duration_hours=np.array([1.0]),
            name="thermal",
        )
        model.update()
        expected_predecessor_coefficients = (0.25, 0.5, 0.125)
        predecessor_names = ("state[2]", "state[0]", "state[1]")
        for row, expected, predecessor_name in zip(
            range(3),
            expected_predecessor_coefficients,
            predecessor_names,
        ):
            constraint = model.getConstrByName(
                f"thermal_compressed_transition_p0[{row}]"
            )
            expression = model.getRow(constraint)
            coefficients = {
                expression.getVar(index).VarName: expression.getCoeff(index)
                for index in range(expression.size())
            }
            self.assertAlmostEqual(
                coefficients[predecessor_name],
                -expected,
            )

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
            provinces=pd.DataFrame({"province_code": [11, 12]}),
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
        self.assertIn(
            "ev_mobility_charge_deviation", block.variables
        )
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
            provinces=pd.DataFrame({"province_code": [11, 12]}),
            load_gw=np.full(shape, 5.0),
            load_components_gw={
                "base_residual": np.full(shape, 3.0),
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
        np.testing.assert_array_less(
            block.variables["ev_mobility_charge"].X
            + block.variables["ev_mobility_discharge"].X,
            np.broadcast_to(
                capacities[:, 2, None],
                block.variables["ev_mobility_charge"].shape,
            )
            + 1e-8,
        )
        self.assertEqual(
            block.structural_audit[
                "ev_shared_connection_power_contract"
            ],
            "charge_plus_discharge_within_nested_smart_charging_contract_v1",
        )
        firm = block.variables["firm_flexible_capacity_credit"].X
        upper = block.variables["firm_flexible_capacity_credit_upper"]
        self.assertTrue(np.all(firm <= upper + 1e-9))
        self.assertNotIn(
            "ev_mobility_charge_deviation", block.variables
        )
        derived_charge_deviation = np.abs(
            block.variables["ev_mobility_charge"].X
            - 0.15 * data.load_components_gw["ev"]
        )
        self.assertGreater(
            float(derived_charge_deviation.sum()),
            0.0,
        )
        expected_v1g_relocated = np.maximum(
            0.15 * data.load_components_gw["ev"]
            - block.variables["ev_mobility_charge"].X,
            0.0,
        )
        np.testing.assert_allclose(
            block.variables["ev_mobility_v1g_relocated"].X,
            expected_v1g_relocated,
            atol=1e-8,
        )
        expected_v1g_relocation_cost = float(
            (
                1e-3
                * service_costs["ev_v1g"][
                    "activation_cost_yuan_per_mwh"
                ]
                * expected_v1g_relocated.sum(axis=1)
            ).sum()
        )
        self.assertAlmostEqual(
            float(
                block.costs[
                    "flexible_load_v5_ev_v1g_relocation"
                ].getValue()
            ),
            expected_v1g_relocation_cost,
            places=10,
        )
        self.assertEqual(
            block.structural_audit[
                "ev_charge_deviation_representation"
            ],
            "postsolve_derived_absolute_deviation",
        )
        self.assertEqual(
            block.structural_audit[
                "ev_charge_deviation_variables_omitted"
            ],
            8,
        )
        self.assertEqual(
            block.structural_audit[
                "ev_charge_deviation_constraints_omitted"
            ],
            16,
        )
        self.assertEqual(
            block.structural_audit[
                "departure_soc_constraint_rows_omitted_as_redundant"
            ],
            8,
        )
        self.assertEqual(
            block.structural_audit[
                "effective_load_nonnegative_constraint_rows_omitted"
            ],
            8,
        )
        self.assertEqual(
            block.structural_audit["net_raw_variables_removed"],
            8,
        )
        self.assertEqual(
            block.structural_audit["net_raw_constraint_rows_removed"],
            32,
        )

    def test_v5_effective_load_nonnegative_row_can_be_proven_redundant(self):
        shape = (2, 3)
        lower = _service_effective_load_lower_bound(
            components={
                "base_residual": np.full(shape, 2.0),
                "heating": np.full(shape, 0.5),
                "cooling": np.full(shape, 0.5),
            },
            thermal_down_upper={
                "heating": np.full(shape, 0.1),
                "cooling": np.full(shape, 0.2),
            },
            fixed_ev_baseline=np.full(shape, 0.4),
            ev_discharge_upper=np.full(shape, 0.3),
        )
        np.testing.assert_allclose(lower, np.full(shape, 2.8))

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
