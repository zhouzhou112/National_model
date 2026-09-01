from __future__ import annotations

import unittest
from copy import deepcopy

import gurobipy as gp
import numpy as np

from cispo_model.annual_energy_coordinate import (
    ANNUAL_ENERGY_SCALE_GWH,
    BINARY_8192_GWH_V1,
    PHYSICAL_GWH_V1,
    resolve_annual_energy_coordinate,
)
from cispo_model.config import ModelConfig, load_model_config


class AnnualEnergyCoordinateTests(unittest.TestCase):
    def test_default_is_physical_and_candidate_is_explicit(self):
        baseline = load_model_config()
        candidate = load_model_config(
            formulation_path=(
                "config/formulation_profiles/annual_energy_coordinate_8192_v1.json"
            )
        )
        physical = resolve_annual_energy_coordinate(baseline)
        scaled = resolve_annual_energy_coordinate(candidate)
        self.assertEqual(physical.profile, PHYSICAL_GWH_V1)
        self.assertEqual(physical.variable_scale_gwh, 1.0)
        self.assertFalse(physical.enabled)
        self.assertEqual(scaled.profile, BINARY_8192_GWH_V1)
        self.assertEqual(scaled.variable_scale_gwh, ANNUAL_ENERGY_SCALE_GWH)
        self.assertTrue(scaled.enabled)

    def test_unknown_coordinate_fails_closed(self):
        baseline = load_model_config()
        raw = deepcopy(baseline.raw)
        raw["formulation"]["annual_energy_coordinate"] = "guess_a_scale"
        invalid = ModelConfig(
            baseline.path,
            raw,
            baseline.scenario_path,
            baseline.solver_path,
            baseline.formulation_path,
        )
        with self.assertRaisesRegex(ValueError, "annual_energy_coordinate"):
            invalid.validate()

    def test_power_of_two_roundtrip_preserves_audited_extremes_bit_exact(self):
        candidate = load_model_config(
            formulation_path=(
                "config/formulation_profiles/annual_energy_coordinate_8192_v1.json"
            )
        )
        coordinate = resolve_annual_energy_coordinate(candidate)
        physical = np.asarray(
            [
                5.657607715647828e-11,  # smallest audited finite VRE-new bound
                2.522817799742793e-7,   # smallest audited reservoir RHS
                1.0004860087065026e-6, # smallest audited ROR hourly CF
                1.0016767646447988e-6, # smallest audited VRE hourly CF
                0.033354,              # reservoir annual conversion minimum
                0.042984772473573685,  # ROR annual FLH minimum
                4380.0,
                6250.0,
                1.14e6,
            ],
            dtype=np.float64,
        )
        restored = coordinate.to_physical(coordinate.to_internal(physical))
        self.assertTrue(np.array_equal(restored, physical))

    def test_diagonal_transform_preserves_activity_objective_dual_and_rc(self):
        coordinate_scale = ANNUAL_ENERGY_SCALE_GWH
        variable_scale = np.diag([coordinate_scale, coordinate_scale, 1.0])
        row_scale = np.diag([1.0 / coordinate_scale, 1.0 / coordinate_scale])
        matrix = np.asarray(
            [[1.0, -1.0, -6250.0], [1.0, 1.0, -4380.0]],
            dtype=float,
        )
        rhs = np.asarray([0.0, 0.0])
        objective = np.asarray([1e-6, 0.0, 321.2854953584793])
        physical_x = np.asarray([9000.0, 1000.0, 2.0])
        internal_x = np.linalg.solve(variable_scale, physical_x)
        scaled_matrix = row_scale @ matrix @ variable_scale
        scaled_rhs = row_scale @ rhs
        scaled_objective = variable_scale.T @ objective
        self.assertTrue(
            np.allclose(
                scaled_matrix @ internal_x - scaled_rhs,
                row_scale @ (matrix @ physical_x - rhs),
                rtol=0.0,
                atol=1e-15,
            )
        )
        self.assertAlmostEqual(
            float(scaled_objective @ internal_x),
            float(objective @ physical_x),
            places=12,
        )
        physical_dual = np.asarray([3.0, -4.0])
        internal_dual = np.linalg.solve(row_scale.T, physical_dual)
        restored_dual = row_scale.T @ internal_dual
        self.assertTrue(np.array_equal(restored_dual, physical_dual))
        physical_rc = np.asarray([2.0, -5.0, 7.0])
        internal_rc = variable_scale.T @ physical_rc
        restored_rc = np.linalg.solve(variable_scale.T, internal_rc)
        self.assertTrue(np.array_equal(restored_rc, physical_rc))

    def test_micro_lp_has_same_physical_solution_and_objective(self):
        physical = gp.Model("annual_energy_physical")
        physical.Params.OutputFlag = 0
        energy = physical.addVar(lb=0.0, name="annual_energy_gwh")
        capacity = physical.addVar(lb=0.0, name="capacity_gw")
        physical.addConstr(energy <= 6000.0 * capacity)
        physical.addConstr(energy >= 12000.0)
        physical.setObjective(1e-6 * energy + 300.0 * capacity)
        physical.optimize()

        scaled = gp.Model("annual_account_internal")
        scaled.Params.OutputFlag = 0
        internal = scaled.addVar(lb=0.0, name="annual_account_internal_8192gwh")
        scaled_capacity = scaled.addVar(lb=0.0, name="capacity_gw")
        # Resource availability stays in physical GWh. Only the downstream
        # annual account is represented in 8192-GWh units.
        resource = scaled.addVar(lb=0.0, name="resource_generation_gwh")
        scaled.addConstr(resource <= 6000.0 * scaled_capacity)
        scaled.addConstr(internal == resource / 8192.0)
        scaled.addConstr(internal >= 12000.0 / 8192.0)
        scaled.setObjective(1e-6 * 8192.0 * internal + 300.0 * scaled_capacity)
        scaled.optimize()

        self.assertEqual(physical.Status, gp.GRB.OPTIMAL)
        self.assertEqual(scaled.Status, gp.GRB.OPTIMAL)
        self.assertAlmostEqual(8192.0 * internal.X, energy.X, places=10)
        self.assertAlmostEqual(scaled_capacity.X, capacity.X, places=12)
        self.assertAlmostEqual(scaled.ObjVal, physical.ObjVal, places=10)

    def test_resource_coefficients_stay_physical_and_accounting_is_scaled(self):
        candidate = load_model_config(
            formulation_path=(
                "config/formulation_profiles/annual_energy_coordinate_8192_v1.json"
            )
        )
        coordinate = resolve_annual_energy_coordinate(candidate)
        audited_resource_values = np.asarray(
            [
                1.0004860087065026e-6,
                0.033354,
                0.042984772473573685,
            ]
        )
        # Resource generation/availability is intentionally not divided.
        self.assertTrue(
            np.array_equal(
                coordinate.variable_to_physical(
                    "load_center_vre_generation", audited_resource_values
                ),
                audited_resource_values,
            )
        )
        internal_account = np.asarray([0.125, 1.0, 10.0])
        self.assertTrue(
            np.array_equal(
                coordinate.variable_to_physical(
                    "load_center_annual_injection", internal_account
                ),
                internal_account * 8192.0,
            )
        )
        # Hourly aggregation and DAC annual accounting remain above 1e-6.
        self.assertGreater(1.0 / 8192.0, 1e-6)
        self.assertLess(6250.0 / 8192.0, 1.0)
        self.assertEqual(1e-6 * 8192.0, 0.008192)


if __name__ == "__main__":
    unittest.main()
