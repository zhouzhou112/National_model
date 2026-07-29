from __future__ import annotations

import unittest

from scripts.audit_release_contract import PROJECT_ROOT, build_audit


class ReleaseContractTests(unittest.TestCase):
    def test_current_code_and_external_data_match_release_contract(self) -> None:
        report = build_audit(PROJECT_ROOT / "data")
        self.assertEqual(report["status"], "PASS", report["failures"])


if __name__ == "__main__":
    unittest.main()
