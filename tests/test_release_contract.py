from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from scripts.audit_release_contract import PROJECT_ROOT, build_audit


class ReleaseContractTests(unittest.TestCase):
    def test_current_code_and_external_data_match_release_contract(self) -> None:
        data_root = Path(
            os.environ.get("CISPO_DATA_ROOT", str(PROJECT_ROOT / "data"))
        )
        report = build_audit(data_root)
        self.assertEqual(report["status"], "PASS", report["failures"])

    def test_v4_upstream_manifest_is_in_server_bundle_contract(self) -> None:
        contract = json.loads(
            (PROJECT_ROOT / "config" / "model_input_files.json").read_text(
                encoding="utf-8"
            )
        )
        deployable = set(contract["required_model_tables"])
        deployable.update(contract["server_validation_sidecars"])
        scenario = json.loads(
            (
                PROJECT_ROOT
                / "config"
                / "scenarios"
                / "flexible_load_comfort_v4_v1g.json"
            ).read_text(encoding="utf-8")
        )
        scenario_files = set(
            scenario["overrides"]["flexible_load"]["v4_input_files"].values()
        )
        self.assertTrue(
            scenario_files.issubset(deployable),
            scenario_files - deployable,
        )
        self.assertIn(
            "load/flexible_load_envelope_v3.manifest.json",
            contract["server_validation_sidecars"],
        )
        self.assertIn("wave/wave_sites.csv", contract["required_model_tables"])
        self.assertIn(
            "wave/wave_input_manifest.json",
            contract["server_validation_sidecars"],
        )


if __name__ == "__main__":
    unittest.main()
