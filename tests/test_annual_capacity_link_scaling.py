from __future__ import annotations

from copy import deepcopy
import tempfile
import unittest

import gurobipy as gp
import numpy as np

from cispo_model.annual_capacity_link_scaling import (
    BINARY_POWER2_SAFE_8192_V1,
    MINIMUM_SCALED_ABS_COEFFICIENT,
    PHYSICAL_V1,
    active_row_scaling_registry,
    ordered_name_sha256,
    row_scaling_metadata,
    select_annual_capacity_link_row_scale,
    validate_row_scaling_registry,
)
from cispo_model.config import ModelConfig, load_model_config
from cispo_model.master import require_finite_load_center_qc_inputs
from cispo_model.run_contract import analysis_case_identity
from scripts.run_cispo_2030_full_year import load_center_physical_qc_pass


PROFILE = "config/formulation_profiles/annual_capacity_link_rows_8192_v1.json"


class AnnualCapacityLinkScalingTests(unittest.TestCase):
    def test_default_is_exact_physical_and_candidate_is_explicit(self):
        baseline = load_model_config()
        candidate = load_model_config(formulation_path=PROFILE)
        physical = select_annual_capacity_link_row_scale(
            baseline, "vre", [1.0, 5925.0]
        )
        scaled = select_annual_capacity_link_row_scale(
            candidate, "vre", [1.0, 5925.0]
        )
        self.assertEqual(physical.profile, PHYSICAL_V1)
        self.assertEqual(physical.exponent, 0)
        self.assertEqual(physical.factor, 1.0)
        self.assertEqual(scaled.profile, BINARY_POWER2_SAFE_8192_V1)
        self.assertEqual(scaled.exponent, 13)
        self.assertEqual(scaled.factor, 1.0 / 8192.0)

    def test_short_window_uses_largest_safe_family_exponent(self):
        candidate = load_model_config(formulation_path=PROFILE)
        ror = select_annual_capacity_link_row_scale(
            candidate, "ror", [1.0, 4.6169e-6]
        )
        self.assertEqual(ror.exponent, 2)
        self.assertGreaterEqual(
            ror.original_min_abs * ror.factor,
            MINIMUM_SCALED_ABS_COEFFICIENT,
        )
        self.assertLess(
            ror.original_min_abs * (ror.factor / 2.0),
            MINIMUM_SCALED_ABS_COEFFICIENT,
        )

    def test_power_of_two_roundtrip_dual_and_slack_mappings(self):
        candidate = load_model_config(formulation_path=PROFILE)
        scale = select_annual_capacity_link_row_scale(
            candidate,
            "ror",
            [1.0, 0.042984772473573685, 5945.849],
        )
        values = np.asarray(
            [1.0e-6, 0.042984772473573685, 5945.849], dtype=np.float64
        )
        transformed = scale.coefficients(values)
        self.assertTrue(
            np.array_equal(np.ldexp(transformed, scale.exponent), values)
        )
        solver_dual = np.asarray([-8192.0, 4096.0])
        np.testing.assert_array_equal(
            scale.dual_to_physical(solver_dual), [-1.0, 0.5]
        )
        solver_slack = np.asarray([0.125, 0.25])
        np.testing.assert_array_equal(
            scale.slack_to_physical(solver_slack), [1024.0, 2048.0]
        )

    def test_micro_lp_preserves_primal_objective_and_physical_dual(self):
        candidate = load_model_config(formulation_path=PROFILE)
        scale = select_annual_capacity_link_row_scale(
            candidate, "vre", [1.0, 6000.0]
        )
        physical = gp.Model("physical_capacity_link")
        transformed = gp.Model("scaled_capacity_link")
        try:
            for model in (physical, transformed):
                model.Params.OutputFlag = 0
            energy = physical.addVar(lb=0.0, name="energy_gwh")
            capacity = physical.addVar(lb=0.0, name="capacity_gw")
            physical_link = physical.addConstr(
                energy <= 6000.0 * capacity, name="annual_link"
            )
            physical.addConstr(energy >= 12000.0, name="demand")
            physical.setObjective(1.0e-6 * energy + 300.0 * capacity)

            scaled_energy = transformed.addVar(lb=0.0, name="energy_gwh")
            scaled_capacity = transformed.addVar(lb=0.0, name="capacity_gw")
            scaled_link = transformed.addConstr(
                scale.factor * scaled_energy
                <= float(scale.coefficients([6000.0])[0]) * scaled_capacity,
                name="annual_link",
            )
            transformed.addConstr(scaled_energy >= 12000.0, name="demand")
            transformed.setObjective(
                1.0e-6 * scaled_energy + 300.0 * scaled_capacity
            )
            physical.optimize()
            transformed.optimize()
            self.assertEqual(physical.Status, gp.GRB.OPTIMAL)
            self.assertEqual(transformed.Status, gp.GRB.OPTIMAL)
            self.assertAlmostEqual(energy.X, scaled_energy.X, places=8)
            self.assertAlmostEqual(capacity.X, scaled_capacity.X, places=12)
            self.assertAlmostEqual(physical.ObjVal, transformed.ObjVal, places=9)
            self.assertAlmostEqual(
                physical_link.Pi,
                float(scale.dual_to_physical([scaled_link.Pi])[0]),
                places=8,
            )
        finally:
            physical.dispose()
            transformed.dispose()

    def test_registry_is_fail_closed_and_unscaled_legacy_is_normalized(self):
        candidate = load_model_config(formulation_path=PROFILE)
        scales = {
            family: select_annual_capacity_link_row_scale(
                candidate, family, [1.0, 10.0]
            )
            for family in ("vre", "ror")
        }
        registry = row_scaling_metadata(candidate, scales)
        self.assertIs(active_row_scaling_registry(registry), registry)
        with self.assertRaisesRegex(ValueError, "Missing"):
            row_scaling_metadata(candidate, {"vre": scales["vre"]})
        baseline = load_model_config()
        unscaled = row_scaling_metadata(
            baseline,
            {
                family: select_annual_capacity_link_row_scale(
                    baseline, family, [1.0]
                )
                for family in ("vre", "ror")
            },
        )
        self.assertIsNone(active_row_scaling_registry(unscaled))

    def test_registry_tampering_and_model_mismatch_fail_closed(self):
        candidate = load_model_config(formulation_path=PROFILE)
        scales = {
            family: select_annual_capacity_link_row_scale(
                candidate, family, [1.0, 10.0]
            )
            for family in ("vre", "ror")
        }
        registry = row_scaling_metadata(candidate, scales)
        mutations = (
            ("schema", lambda row: row.__setitem__("schema_version", "v0")),
            ("profile", lambda row: row.__setitem__("profile", "unknown")),
            (
                "transformation",
                lambda row: row.__setitem__("transformation", "wrong"),
            ),
            (
                "feasible_set_claim",
                lambda row: row.__setitem__(
                    "feasible_set_and_objective_unchanged", 1
                ),
            ),
            (
                "exclusion_scope",
                lambda row: row.__setitem__("explicitly_not_scaled", []),
            ),
            (
                "family",
                lambda row: row["families"]["vre"].__setitem__(
                    "family", "ror"
                ),
            ),
            (
                "prefix",
                lambda row: row["families"]["vre"].__setitem__(
                    "constraint_prefix", "wrong_"
                ),
            ),
            (
                "primal_units",
                lambda row: row["families"]["vre"].__setitem__(
                    "primal_variables_remain_in_physical_units", False
                ),
            ),
            (
                "dual_mapping",
                lambda row: row["families"]["vre"].__setitem__(
                    "physical_dual_mapping",
                    "pi_physical = pi_solver / row_scale",
                ),
            ),
            (
                "slack_mapping",
                lambda row: row["families"]["vre"].__setitem__(
                    "physical_slack_mapping", "wrong"
                ),
            ),
            (
                "reduced_cost_mapping",
                lambda row: row["families"]["vre"].__setitem__(
                    "reduced_cost_mapping", "scaled"
                ),
            ),
            (
                "boolean_exponent",
                lambda row: row["families"]["vre"].__setitem__(
                    "exponent", True
                ),
            ),
            (
                "large_exponent",
                lambda row: row["families"]["vre"].__setitem__(
                    "exponent", 14
                ),
            ),
            (
                "row_scale",
                lambda row: row["families"]["vre"].__setitem__(
                    "row_scale", 1.0
                ),
            ),
            (
                "negative_count",
                lambda row: row["families"]["vre"].__setitem__(
                    "constraint_rows", -1
                ),
            ),
            (
                "digest",
                lambda row: row["families"]["vre"].__setitem__(
                    "constraint_name_order_sha256", "bad"
                ),
            ),
            (
                "coefficient_range",
                lambda row: row["families"]["vre"].__setitem__(
                    "scaled_coefficient_min_abs", 2.0
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                changed = deepcopy(registry)
                mutate(changed)
                with self.assertRaises(ValueError):
                    validate_row_scaling_registry(changed)

        model = gp.Model("row_registry_binding")
        model.Params.OutputFlag = 0
        try:
            vre_generation = model.addVar(
                name="load_center_vre_generation_gwh[0,0]"
            )
            vre_capacity = model.addVar(name="vre_capacity_gw[0]")
            ror_generation = model.addVar(
                name="load_center_ror_generation_gwh[0]"
            )
            ror_capacity = model.addVar(name="hydro_capacity_gw[0]")
            vre_name = "load_center_vre_availability_0_onwind"
            ror_name = "load_center_ror_availability_0"
            model.addConstr(
                scales["vre"].factor * vre_generation
                <= float(scales["vre"].coefficients([10.0])[0])
                * vre_capacity,
                name=vre_name,
            )
            model.addConstr(
                scales["ror"].factor * ror_generation
                <= float(scales["ror"].coefficients([10.0])[0])
                * ror_capacity,
                name=ror_name,
            )
            model.update()
            bound = deepcopy(registry)
            for family, name in (("vre", vre_name), ("ror", ror_name)):
                bound["families"][family]["constraint_rows"] = 1
                bound["families"][family]["matrix_nonzeros_scaled"] = 2
                bound["families"][family]["constraint_names"] = [name]
                bound["families"][family][
                    "constraint_name_order_sha256"
                ] = ordered_name_sha256([name])
            self.assertIs(
                validate_row_scaling_registry(bound, model=model), bound
            )
            changed = deepcopy(bound)
            changed["families"]["vre"]["constraint_rows"] = 2
            with self.assertRaises(ValueError):
                validate_row_scaling_registry(changed, model=model)
            self_consistent = deepcopy(bound)
            family = self_consistent["families"]["vre"]
            family["exponent"] = 12
            family["row_scale"] = 2.0**-12
            family["scaled_coefficient_min_abs"] = np.ldexp(
                family["original_coefficient_min_abs"], -12
            )
            family["scaled_coefficient_max_abs"] = np.ldexp(
                family["original_coefficient_max_abs"], -12
            )
            with self.assertRaisesRegex(ValueError, "anchor|range"):
                validate_row_scaling_registry(self_consistent, model=model)
        finally:
            model.dispose()

    def test_unknown_profile_and_preexisting_tiny_coefficient_fail(self):
        baseline = load_model_config()
        raw = deepcopy(baseline.raw)
        raw["formulation"]["annual_capacity_link_row_scaling"] = "guess"
        invalid = ModelConfig(
            baseline.path,
            raw,
            baseline.scenario_path,
            baseline.solver_path,
            baseline.formulation_path,
        )
        with self.assertRaisesRegex(ValueError, "annual_capacity_link"):
            invalid.validate()
        candidate = load_model_config(formulation_path=PROFILE)
        with self.assertRaisesRegex(ValueError, "already below"):
            select_annual_capacity_link_row_scale(
                candidate, "vre", [1.0, 0.5e-6]
            )

    def test_resource_screening_threshold_is_in_scientific_identity(self):
        baseline = load_model_config()
        raw = deepcopy(baseline.raw)
        raw["numerics"]["coefficient_zero_tolerance"] = 1.0e-5
        changed = ModelConfig(
            baseline.path,
            raw,
            baseline.scenario_path,
            baseline.solver_path,
            baseline.formulation_path,
        )
        changed.validate()
        self.assertNotEqual(
            analysis_case_identity(baseline)[
                "resolved_scientific_configuration_sha256"
            ],
            analysis_case_identity(changed)[
                "resolved_scientific_configuration_sha256"
            ],
        )

    def test_original_unit_load_center_qc_is_mandatory(self):
        qc = {
            "maximum_center_balance_residual_gwh": 0.0,
            "maximum_province_net_exchange_residual_gwh": 0.0,
            "maximum_intra_capacity_violation_gwh": 0.0,
            "maximum_vre_annual_availability_violation_gwh": 9.9e-6,
            "maximum_ror_annual_availability_violation_gwh": 0.0,
            "bidirectional_active_edge_count": 0,
            "dpv_spur_augmentation_max_gw": 0.0,
        }
        self.assertTrue(load_center_physical_qc_pass(qc))
        qc["maximum_vre_annual_availability_violation_gwh"] = 1.01e-5
        self.assertFalse(load_center_physical_qc_pass(qc))
        with self.assertRaisesRegex(RuntimeError, "vre_availability_residual"):
            require_finite_load_center_qc_inputs(
                vre_availability_residual=np.nan
            )

    def test_only_one_qualification_and_one_production_profile(self):
        qualification = load_model_config(
            solver_path=(
                "config/solver_profiles/"
                "barrier_checkpoint_fixed_server_host_memory_95_v2.json"
            )
        )
        production = load_model_config(
            solver_path=(
                "config/solver_profiles/"
                "barrier_checkpoint_full_year_cloud_v4.json"
            )
        )
        self.assertEqual(qualification.raw["numerics"]["threads"], 32)
        self.assertIsNone(
            qualification.raw["numerics"]["time_limit_seconds"]
        )
        self.assertEqual(production.raw["numerics"]["threads"], 32)
        self.assertEqual(
            production.raw["numerics"]["barrier_convergence_tolerance"],
            1e-9,
        )
        self.assertTrue(
            production.raw["solver_profile"][
                "direct_nonbasic_scientific_acceptance"
            ]
        )
        self.assertEqual(
            production.raw["solver_profile"][
                "required_formulation_profile_id"
            ],
            "annual_capacity_link_rows_8192_v1",
        )
        self.assertEqual(
            production.raw["numerics"]["feasibility_tolerance"], 1e-9
        )
        self.assertIsNone(production.raw["numerics"]["time_limit_seconds"])


if __name__ == "__main__":
    unittest.main()
