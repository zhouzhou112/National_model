from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.audit_m2_model_boundary import build_audit


class M2ModelBoundaryAuditTests(unittest.TestCase):
    def test_audit_reports_current_open_evidence_without_lp_build(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            summary = build_audit(
                root / "config/m2_model_boundary_audit_v1.json",
                Path(temporary),
            )
            self.assertEqual(summary["finding_count"], 11)
            self.assertEqual(
                summary["snapshot_status"],
                "HISTORICAL_20260728_SUPERSEDED",
            )
            self.assertEqual(
                summary["superseded_by"],
                "config/release_contract_v0729.json",
            )
            self.assertEqual(summary["contract_checks"]["hard_fail"], 0)
            self.assertEqual(summary["contract_checks"]["open"], 0)
            self.assertTrue((Path(temporary) / "m2_decision_register.csv").is_file())
            self.assertTrue((Path(temporary) / "M2_AUDIT_REPORT_ZH.md").is_file())


if __name__ == "__main__":
    unittest.main()
