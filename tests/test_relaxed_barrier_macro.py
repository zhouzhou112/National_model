from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

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
                    "runtime_seconds": 20.0,
                    "iteration_counts": {"barrier": 100},
                },
            )
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


if __name__ == "__main__":
    unittest.main()
