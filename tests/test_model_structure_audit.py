from __future__ import annotations

import unittest

import gurobipy as gp

from cispo_model.model_structure_audit import audit_model_structure, family_for_name


class ModelStructureAuditTests(unittest.TestCase):
    def test_family_prefixes_are_stable(self):
        self.assertEqual(
            family_for_name("reservoir_cascade_s4_8_9_12_row5_h4[0]"),
            "hydro_reservoir_cascade",
        )
        self.assertEqual(
            family_for_name("load_center_annual_energy_balance_2"),
            "load_center_annual_network",
        )
        self.assertEqual(
            family_for_name("dac_capacity_accounting[0,0]"),
            "dac_annual_accounting",
        )
        self.assertEqual(
            family_for_name("flexible_service_capacity_gw[0,0]"),
            "demand_and_flexibility",
        )
        self.assertEqual(
            family_for_name("firm_flexible_capacity_credit_gw[0,0]"),
            "demand_and_flexibility",
        )
        self.assertEqual(
            family_for_name("v5_ev_v2g_firm_credit_contract_bound[0]"),
            "demand_and_flexibility",
        )
        self.assertEqual(family_for_name("unknown_row"), "other_unclassified")

    def test_audit_counts_raw_rows_columns_and_nonzeros(self):
        model = gp.Model("structure_audit_test")
        model.Params.OutputFlag = 0
        reservoir_flow = model.addVars(2, name="reservoir_turbine_flow_1000m3s")
        load_center_balance = model.addVar(name="load_center_annual_injection_gwh")
        model.addConstr(
            reservoir_flow[0] + reservoir_flow[1] == 1.0,
            name="reservoir_independent_hourly_transition",
        )
        model.addConstr(
            load_center_balance == reservoir_flow[0],
            name="load_center_annual_energy_balance_0",
        )
        audit = audit_model_structure(model, max_matrix_nonzeros=10)
        self.assertEqual(audit["raw_model"]["constraints"], 2)
        self.assertEqual(audit["raw_model"]["variables"], 3)
        self.assertEqual(audit["raw_model"]["matrix_nonzeros"], 4)
        families = {row["family"]: row for row in audit["constraint_families"]}
        self.assertEqual(
            families["hydro_reservoir_independent"]["matrix_nonzeros"], 2
        )
        self.assertEqual(
            families["load_center_annual_network"]["matrix_nonzeros"], 2
        )
        largest_constraint = audit["largest_constraints"][0]
        self.assertEqual(largest_constraint["matrix_nonzeros"], 2)
        self.assertIn(
            largest_constraint["constraint_name"],
            {
                "reservoir_independent_hourly_transition",
                "load_center_annual_energy_balance_0",
            },
        )

    def test_audit_refuses_matrix_above_explicit_limit(self):
        model = gp.Model("structure_audit_limit_test")
        model.Params.OutputFlag = 0
        first = model.addVar(name="storage_charge_gw")
        second = model.addVar(name="storage_discharge_gw")
        model.addConstr(
            first + second <= 1.0,
            name="storage_charge_power",
        )
        with self.assertRaisesRegex(ValueError, "safety limit"):
            audit_model_structure(model, max_matrix_nonzeros=1)

    def test_audit_reports_fixed_and_unconstrained_variables(self):
        model = gp.Model("structure_audit_variable_status_test")
        model.Params.OutputFlag = 0
        model.addVar(
            lb=0.0,
            ub=0.0,
            name="heating_shift_up_gw",
        )
        model.addVar(
            lb=0.0,
            ub=1.0,
            name="ev_mobility_charge_gw",
        )
        audit = audit_model_structure(model, max_matrix_nonzeros=1)
        self.assertEqual(audit["variable_status"]["fixed_variables"], 1)
        self.assertEqual(audit["variable_status"]["fixed_zero_variables"], 1)
        self.assertEqual(
            audit["variable_status"][
                "unconstrained_zero_objective_variables"
            ],
            1,
        )
        self.assertEqual(
            audit["variable_status_examples"]["fixed_zero_variables"][0][
                "variable_name"
            ],
            "heating_shift_up_gw",
        )
        self.assertEqual(
            audit["variable_status_examples"][
                "unconstrained_zero_objective_variables"
            ][0]["variable_name"],
            "ev_mobility_charge_gw",
        )


if __name__ == "__main__":
    unittest.main()
