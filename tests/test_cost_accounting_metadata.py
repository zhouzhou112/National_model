import unittest

from cispo_model.master import cost_component_accounting_scope


class CostAccountingMetadataTests(unittest.TestCase):
    def test_operation_rows_separate_composite_and_annualized_costs(self) -> None:
        self.assertEqual(
            cost_component_accounting_scope("annual_operation"),
            "COMPOSITE_SEE_COMPONENT_ROWS",
        )
        self.assertEqual(
            cost_component_accounting_scope("operating_flexible_load_v4_enablement"),
            "ANNUALIZED_PLANNING_COST",
        )
        self.assertEqual(
            cost_component_accounting_scope("operating_fuel"),
            "SELECTED_HORIZON_OPERATION_COST",
        )

    def test_planning_rows_use_annualized_scope(self) -> None:
        self.assertEqual(
            cost_component_accounting_scope("vre_investment"),
            "ANNUALIZED_PLANNING_COST",
        )
