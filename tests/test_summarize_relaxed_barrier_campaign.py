import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.summarize_relaxed_barrier_campaign import summarize, write_csv


class RelaxedBarrierCampaignSummaryTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_summary_joins_fallback_time_and_exact_macro(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output_base = root / "outputs"
            case = output_base / "base_744h_numeric1"
            control = root / "control"
            fallback = root / "old_control"
            case.mkdir(parents=True)
            (control / "base_744h_numeric1").mkdir(parents=True)
            (fallback / "base_744h_numeric1").mkdir(parents=True)
            (control / "base_744h_numeric1" / "return_code.txt").write_text(
                "7\n", encoding="utf-8"
            )
            self._write_json(
                case / "solve_report.json",
                {
                    "status": "OPTIMAL",
                    "planning_year": 2030,
                    "scenario_id": "base",
                    "optimization_hours": 744,
                    "optimization_start_hour": 0,
                    "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
                    "run_completion_status": "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE",
                    "solver_profile_id": "numeric1",
                    "runtime_seconds": 100.0,
                    "iteration_counts": {"barrier": 10},
                    "solver_parameters": {
                        "numeric_focus": 1,
                        "barrier_convergence_tolerance": 0.01,
                        "crossover": 0,
                    },
                    "solution_quality": {
                        "maximum_constraint_violation": 0.001,
                    },
                    "runtime_memory": {"peak_process_tree_rss_gib": 2.5},
                },
            )
            self._write_json(case / "run_identity.json", {"lp_model": {"gurobi_fingerprint": 7}})
            self._write_json(
                case
                / "engineering_macro_analysis"
                / "engineering_analysis_contract.json",
                {
                    "strict_solver_acceptance_status": "HARD_FAIL",
                    "raw_physical_qc_status": "STRICT_PHYSICAL_QC_EXPORT_FAILED",
                },
            )
            self._write_json(
                case
                / "barrier_checkpoint"
                / "barrier_checkpoint_manifest.json",
                {"status": "ENGINEERING_BARRIER_CHECKPOINT_ONLY"},
            )
            telemetry = [
                {"event": "solver_start"},
                {"event": "solver_progress", "phase": "barrier", "iteration": 0, "runtime_seconds": 10},
                {"event": "solver_progress", "phase": "barrier", "iteration": 10, "runtime_seconds": 60},
                {"event": "solver_end", "runtime_seconds": 100},
            ]
            (case / "solver_telemetry.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in telemetry),
                encoding="utf-8",
            )
            self._write_json(
                control / "base_744h_numeric1" / "macro_comparison.json",
                {
                    "status": "MACRO_PASS",
                    "exact_ab_identity": {"status": "EXACT_AB_IDENTITY_PASS", "matches": True},
                    "metrics": {"objective_relative_difference": 0.001},
                },
            )
            (fallback / "base_744h_numeric1" / "time.txt").write_text(
                "\tElapsed (wall clock) time (h:mm:ss or m:ss): 0:02:00\n"
                "\tMaximum resident set size (kbytes): 4096\n"
                "\tExit status: 0\n",
                encoding="utf-8",
            )
            report = summarize(output_base, control, [fallback])
            self.assertEqual(report["case_count"], 1)
            self.assertEqual(report["macro_pass_tags"], ["base_744h_numeric1"])
            row = report["cases"][0]
            self.assertEqual(row["gnu_time"]["elapsed_seconds"], 120.0)
            self.assertEqual(row["return_code"], 7)
            self.assertTrue(row["return_code_source"].endswith("return_code.txt"))
            self.assertEqual(
                row["telemetry"]["observed_barrier_seconds_per_iteration"],
                5.0,
            )
            self.assertEqual(row["exact_ab_identity_status"], "EXACT_AB_IDENTITY_PASS")
            self.assertTrue(row["barrier_checkpoint_manifest_present"])
            self.assertFalse(any(row["root_scientific_artifacts"].values()))
            self.assertFalse(row["scientifically_accepted"])

            csv_path = root / "summary.csv"
            write_csv(csv_path, report["cases"])
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["macro_status"], "MACRO_PASS")
            self.assertEqual(rows[0]["wall_elapsed_seconds"], "120.0")
            self.assertEqual(
                rows[0]["barrier_checkpoint_manifest_present"], "True"
            )


if __name__ == "__main__":
    unittest.main()
