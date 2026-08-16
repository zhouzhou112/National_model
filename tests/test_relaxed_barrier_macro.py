from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_relaxed_barrier_macro import audit
from scripts.run_cispo_2030_full_year import (
    export_engineering_relaxed_macro_analysis,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_series(path: Path, key: str, value: str, amount: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[key, value])
        writer.writeheader()
        writer.writerow({key: "onwind", value: amount})


def _write_input_manifest(path: Path, data_sha256: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind",
        "logical_path",
        "resolved_path",
        "required",
        "exists",
        "size_bytes",
        "sha256",
        "integrity_method",
        "role",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "kind": "model_table",
                "logical_path": "load/hourly.csv.gz",
                "resolved_path": "/data/root/load/hourly.csv.gz",
                "required": "True",
                "exists": "True",
                "size_bytes": "10",
                "sha256": data_sha256,
                "integrity_method": "sha256_file",
                "role": "load",
            }
        )
        writer.writerow(
            {
                "kind": "solver_configuration",
                "logical_path": "solver.json",
                "resolved_path": "/repo/solver.json",
                "required": "True",
                "exists": "True",
                "size_bytes": "10",
                "sha256": "solver-is-allowed-to-differ",
                "integrity_method": "sha256_file",
                "role": "",
            }
        )


def _write_run_identity(path: Path, fingerprint: int = 123) -> None:
    _write_json(
        path,
        {
            "baseline_contract": {"contract_sha256": "baseline"},
            "analysis_case": {
                "resolved_scientific_configuration_sha256": "science",
                "scenario_configuration": {"sha256": "scenario"},
                "formulation_configuration": {"sha256": None},
            },
            "implementation_bundle": {"source_bundle_sha256": "source"},
            "lp_model": {
                "variables": 10,
                "constraints": 20,
                "nonzeros": 30,
                "gurobi_fingerprint": fingerprint,
            },
        },
    )


class RelaxedBarrierMacroAuditTests(unittest.TestCase):
    def test_master_qc_failure_does_not_block_engineering_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            analysis = Path(temporary) / "engineering_macro_analysis"
            calls = []

            def master_exporter(*_args):
                calls.append("master")
                raise RuntimeError(
                    "Load-center solution QC failed: directionality"
                )

            def operational_exporter(*_args):
                calls.append("operational")
                return {"status": "PASS", "hard_checks": {"example": True}}

            def summary_exporter(*_args):
                calls.append("summary")
                _write_json(analysis / "annual_summary.json", {"ok": True})

            qc, error = export_engineering_relaxed_macro_analysis(
                object(),
                object(),
                object(),
                analysis,
                master_exporter=master_exporter,
                operational_exporter=operational_exporter,
                summary_exporter=summary_exporter,
            )

            self.assertEqual(calls, ["master", "operational", "summary"])
            self.assertEqual(qc["status"], "PASS")
            self.assertEqual(
                error["status"], "STRICT_PHYSICAL_QC_EXPORT_FAILED"
            )
            self.assertEqual(error["error_stage"], "MASTER_SOLUTION_EXPORT")
            self.assertTrue((analysis / "annual_summary.json").is_file())
            persisted = json.loads(
                (analysis / "engineering_raw_qc_error.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(persisted["scientifically_accepted"])

    def test_unexpected_engineering_export_error_is_not_suppressed(self):
        with tempfile.TemporaryDirectory() as temporary:
            analysis = Path(temporary) / "engineering_macro_analysis"

            def master_exporter(*_args):
                raise OSError("disk write failed")

            with self.assertRaisesRegex(OSError, "disk write failed"):
                export_engineering_relaxed_macro_analysis(
                    object(),
                    object(),
                    object(),
                    analysis,
                    master_exporter=master_exporter,
                    operational_exporter=lambda *_args: {},
                    summary_exporter=lambda *_args: None,
                )

    def test_missing_strict_qc_is_preserved_without_losing_macro_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            analysis = candidate / "engineering_macro_analysis"
            reference = root / "reference"
            common_summary = {
                "planning_year": 2030,
                "scenario_id": "base",
                "optimization_hours": 744,
                "optimization_start_hour": 0,
                "objective_million_cny_per_year": 100.0,
                "period_generation_gwh": 1000.0,
                "period_load_gwh": 900.0,
            }
            _write_json(
                analysis / "engineering_analysis_contract.json",
                {"scientifically_accepted": False},
            )
            _write_json(analysis / "annual_summary.json", common_summary)
            _write_json(reference / "annual_summary.json", common_summary)
            _write_json(
                candidate / "solve_report.json",
                {
                    "run_completion_status": (
                        "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
                    ),
                    "runtime_seconds": 10.0,
                    "iteration_counts": {"barrier": 40},
                },
            )
            _write_json(
                reference / "solve_report.json",
                {
                    "status": "OPTIMAL",
                    "runtime_seconds": 20.0,
                    "iteration_counts": {"barrier": 100},
                },
            )
            _write_json(reference / "solution_qc.json", {"status": "PASS"})
            _write_json(reference / "result_manifest.json", {"valid": True})
            _write_run_identity(candidate / "run_identity.json")
            _write_run_identity(reference / "run_identity.json")
            _write_input_manifest(candidate / "input_manifest.csv", "same-data")
            _write_input_manifest(reference / "input_manifest.csv", "same-data")
            _write_json(
                analysis / "engineering_raw_qc_error.json",
                {
                    "status": "STRICT_PHYSICAL_QC_EXPORT_FAILED",
                    "error": "directionality check",
                },
            )
            for directory in (analysis, reference):
                _write_series(
                    directory / "annual_capacity_by_technology.csv",
                    "technology",
                    "capacity",
                    100.0,
                )
                _write_series(
                    directory / "annual_generation_by_technology.csv",
                    "technology",
                    "generation_gwh",
                    1000.0,
                )

            with patch(
                "scripts.audit_relaxed_barrier_macro.validate_result_manifest",
                return_value=(True, []),
            ):
                report = audit(
                    candidate,
                    reference,
                    objective_limit=0.01,
                    capacity_l1_limit=0.02,
                    generation_l1_limit=0.02,
                    period_generation_limit=0.005,
                )

            self.assertEqual(report["status"], "MACRO_PASS")
            self.assertFalse(report["scientifically_accepted"])
            self.assertEqual(
                report["candidate_raw_qc_status"],
                "STRICT_PHYSICAL_QC_EXPORT_FAILED",
            )
            self.assertEqual(
                report["candidate_raw_qc_error"]["error"],
                "directionality check",
            )
            self.assertTrue(report["exact_ab_identity"]["matches"])
            self.assertTrue(report["reference_contract"]["accepted"])
            self.assertTrue(
                report["reference_contract"]["result_manifest_valid"]
            )

    def test_mismatched_lp_or_input_cannot_macro_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            analysis = candidate / "engineering_macro_analysis"
            reference = root / "reference"
            common_summary = {
                "planning_year": 2030,
                "scenario_id": "base",
                "optimization_hours": 744,
                "optimization_start_hour": 0,
                "objective_million_cny_per_year": 100.0,
                "period_generation_gwh": 1000.0,
                "period_load_gwh": 900.0,
            }
            _write_json(
                analysis / "engineering_analysis_contract.json",
                {"scientifically_accepted": False},
            )
            _write_json(analysis / "annual_summary.json", common_summary)
            _write_json(reference / "annual_summary.json", common_summary)
            _write_json(
                candidate / "solve_report.json",
                {
                    "run_completion_status": (
                        "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
                    )
                },
            )
            _write_json(reference / "solve_report.json", {"status": "OPTIMAL"})
            _write_json(reference / "solution_qc.json", {"status": "PASS"})
            _write_json(reference / "result_manifest.json", {"valid": True})
            _write_run_identity(candidate / "run_identity.json", fingerprint=123)
            _write_run_identity(reference / "run_identity.json", fingerprint=456)
            _write_input_manifest(candidate / "input_manifest.csv", "new-load")
            _write_input_manifest(reference / "input_manifest.csv", "old-load")
            for directory in (analysis, reference):
                _write_series(
                    directory / "annual_capacity_by_technology.csv",
                    "technology",
                    "capacity",
                    100.0,
                )
                _write_series(
                    directory / "annual_generation_by_technology.csv",
                    "technology",
                    "generation_gwh",
                    1000.0,
                )

            report = audit(
                candidate,
                reference,
                objective_limit=0.01,
                capacity_l1_limit=0.02,
                generation_l1_limit=0.02,
                period_generation_limit=0.005,
            )

            self.assertEqual(report["status"], "MACRO_FAIL")
            self.assertFalse(report["exact_ab_identity"]["matches"])
            self.assertFalse(
                report["exact_ab_identity"]["input_manifest_matches"]
            )
            self.assertFalse(
                report["exact_ab_identity"]["fields"][
                    "gurobi_fingerprint"
                ]["matches"]
            )

    def test_invalid_reference_manifest_cannot_macro_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            analysis = candidate / "engineering_macro_analysis"
            reference = root / "reference"
            common_summary = {
                "planning_year": 2030,
                "scenario_id": "base",
                "optimization_hours": 744,
                "optimization_start_hour": 0,
                "objective_million_cny_per_year": 100.0,
                "period_generation_gwh": 1000.0,
                "period_load_gwh": 900.0,
            }
            _write_json(
                analysis / "engineering_analysis_contract.json",
                {"scientifically_accepted": False},
            )
            _write_json(analysis / "annual_summary.json", common_summary)
            _write_json(reference / "annual_summary.json", common_summary)
            _write_json(
                candidate / "solve_report.json",
                {
                    "run_completion_status": (
                        "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
                    )
                },
            )
            _write_json(reference / "solve_report.json", {"status": "OPTIMAL"})
            _write_json(reference / "solution_qc.json", {"status": "PASS"})
            _write_json(reference / "result_manifest.json", {"valid": True})
            _write_run_identity(candidate / "run_identity.json")
            _write_run_identity(reference / "run_identity.json")
            _write_input_manifest(candidate / "input_manifest.csv", "same-data")
            _write_input_manifest(reference / "input_manifest.csv", "same-data")
            for directory in (analysis, reference):
                _write_series(
                    directory / "annual_capacity_by_technology.csv",
                    "technology",
                    "capacity",
                    100.0,
                )
                _write_series(
                    directory / "annual_generation_by_technology.csv",
                    "technology",
                    "generation_gwh",
                    1000.0,
                )

            report = audit(
                candidate,
                reference,
                objective_limit=0.01,
                capacity_l1_limit=0.02,
                generation_l1_limit=0.02,
                period_generation_limit=0.005,
            )

            self.assertEqual(report["status"], "MACRO_FAIL")
            self.assertFalse(report["reference_contract"]["accepted"])
            self.assertFalse(
                report["reference_contract"]["result_manifest_valid"]
            )
            self.assertIn(
                "result_manifest.json files is not a list",
                report["reference_contract"]["result_manifest_failures"],
            )


if __name__ == "__main__":
    unittest.main()
