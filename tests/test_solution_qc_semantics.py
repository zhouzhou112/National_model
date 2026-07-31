from __future__ import annotations

import unittest

import numpy as np

from cispo_model.solution_export import _ev_v1g_daily_energy_residual_for_qc


class SolutionQcSemanticsTests(unittest.TestCase):
    def test_service_contract_marks_legacy_v1g_residual_not_applicable(self) -> None:
        value, applicability = _ev_v1g_daily_energy_residual_for_qc(
            np.asarray([5.999958]),
            service_contract_formulation=True,
        )
        self.assertIsNone(value)
        self.assertEqual(
            applicability,
            "NOT_APPLICABLE_SERVICE_CONSTRAINED_EV_SOC_ACCOUNTING",
        )

    def test_legacy_daily_charging_accounting_retains_residual(self) -> None:
        value, applicability = _ev_v1g_daily_energy_residual_for_qc(
            np.asarray([-2.0e-8, 1.0e-8]),
            service_contract_formulation=False,
        )
        self.assertAlmostEqual(value, 2.0e-8)
        self.assertEqual(
            applicability,
            "APPLICABLE_LEGACY_DAILY_CHARGING_ENERGY_ACCOUNTING",
        )


if __name__ == "__main__":
    unittest.main()
