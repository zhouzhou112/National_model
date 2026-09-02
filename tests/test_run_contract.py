from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.io_contract import sha256_file, validate_input_manifest
from cispo_model.run_contract import (
    claim_output_directory,
    claim_sequence_directory,
    configuration_identity,
    release_sequence_directory,
    sequence_identity,
    solver_result_is_accepted,
)


class RunContractTests(unittest.TestCase):
    def test_output_claim_allows_wrapper_logs_but_never_reuses_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "output"
            root.mkdir()
            (root / "stdout.log").write_text("", encoding="utf-8")
            claim = claim_output_directory(root)
            self.assertTrue(claim.is_file())
            with self.assertRaisesRegex(RuntimeError, "non-empty|already claimed"):
                claim_output_directory(root)

    def test_output_claim_rejects_existing_scientific_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "solve_report.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "non-empty"):
                claim_output_directory(root)

    def test_solver_success_requires_optimal_qc_and_manifest(self):
        report = {"status": "OPTIMAL"}
        qc = {"status": "PASS", "hard_checks": {"power_balance": True}}
        self.assertTrue(
            solver_result_is_accepted(
                report, qc, result_manifest_valid=True
            )
        )
        self.assertTrue(
            solver_result_is_accepted(
                {
                    "status": "OPTIMAL",
                    "solution_contract": {"acceptance_status": "PASS"},
                },
                qc,
                result_manifest_valid=True,
            )
        )
        for changed_report, changed_qc, manifest in (
            ({"status": "TIME_LIMIT"}, qc, True),
            (
                {
                    "status": "OPTIMAL",
                    "solution_contract": {"acceptance_status": "HARD_FAIL"},
                },
                qc,
                True,
            ),
            (report, {"status": "FAIL"}, True),
            (
                report,
                {"status": "PASS", "hard_checks": {"power_balance": False}},
                True,
            ),
            (report, {"status": "PASS", "hard_checks": {}}, True),
            (
                report,
                {"status": "PASS", "hard_checks": {"power_balance": 1}},
                True,
            ),
            (
                report,
                {
                    "status": "PASS",
                    "hard_checks": {"power_balance": float("nan")},
                },
                True,
            ),
            (
                report,
                {
                    "status": "PASS",
                    "hard_checks": {"power_balance": True},
                    "maximum_power_balance_residual_gw": float("nan"),
                },
                True,
            ),
            (report, {"status": "PASS"}, True),
            (report, qc, False),
            (report, None, True),
        ):
            with self.subTest(
                report=changed_report, qc=changed_qc, manifest=manifest
            ):
                self.assertFalse(
                    solver_result_is_accepted(
                        changed_report,
                        changed_qc,
                        result_manifest_valid=manifest,
                    )
                )

    def test_configuration_identity_changes_with_solver_profile(self):
        root = Path(__file__).resolve().parents[1]
        base = load_model_config()
        candidate = load_model_config(
            solver_path=(
                root
                / "config"
                / "solver_profiles"
                / "barrier_16_crossover_3_v1.json"
            )
        )
        base_identity = configuration_identity(base, data_root=root / "data")
        candidate_identity = configuration_identity(
            candidate, data_root=root / "data"
        )
        self.assertEqual(
            base_identity["scientific_case"],
            candidate_identity["scientific_case"],
        )
        self.assertNotEqual(
            base_identity["solver_runtime"],
            candidate_identity["solver_runtime"],
        )
        self.assertEqual(
            json.dumps(base_identity, sort_keys=True),
            json.dumps(
                configuration_identity(base, data_root=root / "data"),
                sort_keys=True,
            ),
        )
        self.assertEqual(
            base_identity["implementation_bundle"]["source_file_count"] > 0,
            True,
        )
        self.assertEqual(
            len(base_identity["implementation_bundle"]["source_bundle_sha256"]),
            64,
        )

    def test_baseline_contract_is_immutable_while_analysis_case_changes(self):
        root = Path(__file__).resolve().parents[1]
        base = load_model_config(
            scenario_path=root / "config" / "scenarios" / "base.json"
        )
        effective = load_model_config(
            scenario_path=(
                root
                / "config"
                / "scenarios"
                / "flexible_load_comfort_v4_v1g_effective_peak_sensitivity.json"
            )
        )
        base_identity = configuration_identity(base, data_root=root / "data")
        effective_identity = configuration_identity(
            effective, data_root=root / "data"
        )
        self.assertEqual(
            base_identity["baseline_contract"],
            effective_identity["baseline_contract"],
        )
        self.assertNotEqual(
            base_identity["analysis_case"],
            effective_identity["analysis_case"],
        )
        self.assertEqual(
            effective_identity["analysis_case"]["parent_baseline_case_id"],
            base_identity["baseline_contract"]["case_id"],
        )

    def test_sequence_identity_locks_horizon_and_year_range(self):
        root = Path(__file__).resolve().parents[1]
        config = load_model_config()
        kwargs = {
            "data_root": root / "data",
            "input_identity": {
                "input_manifest_sha256": "a" * 64,
                "input_manifest_row_count": 3,
            },
            "start_year": 2030,
            "end_year": 2060,
            "diagnostic_hours": 168,
            "diagnostic_start_hour": 3960,
        }
        reference = sequence_identity(config, **kwargs)
        for changed in (
            {"diagnostic_hours": 24},
            {"diagnostic_start_hour": 4344},
            {"start_year": 2040},
            {"end_year": 2050},
            {
                "input_identity": {
                    "input_manifest_sha256": "b" * 64,
                    "input_manifest_row_count": 3,
                }
            },
        ):
            with self.subTest(changed=changed):
                candidate = sequence_identity(config, **(kwargs | changed))
                self.assertNotEqual(candidate, reference)

    def test_sequence_claim_is_atomic_and_releasable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "sequence"
            first = claim_sequence_directory(root)
            with self.assertRaisesRegex(RuntimeError, "already claimed"):
                claim_sequence_directory(root)
            self.assertTrue(release_sequence_directory(root, first))
            second = claim_sequence_directory(root)
            self.assertNotEqual(first, second)
            self.assertTrue(release_sequence_directory(root, second))

    def test_input_manifest_detects_same_path_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            source.write_text("alpha\n", encoding="utf-8")
            manifest = root / "input_manifest.csv"
            pd.DataFrame(
                [
                    {
                        "kind": "model_table",
                        "logical_path": "input.csv",
                        "resolved_path": str(source),
                        "required": True,
                        "exists": True,
                        "size_bytes": source.stat().st_size,
                        "sha256": sha256_file(source),
                        "integrity_method": "sha256_file",
                        "role": "test",
                    }
                ]
            ).to_csv(manifest, index=False)
            valid, failures = validate_input_manifest(manifest)
            self.assertTrue(valid, failures)
            source.write_text("bravo\n", encoding="utf-8")
            valid, failures = validate_input_manifest(manifest)
            self.assertFalse(valid)
            self.assertIn("sha256:input.csv", failures)


if __name__ == "__main__":
    unittest.main()
