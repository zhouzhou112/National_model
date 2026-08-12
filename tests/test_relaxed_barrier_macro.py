from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_relaxed_barrier_macro import audit


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
