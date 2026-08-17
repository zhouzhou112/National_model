import json
import tempfile
import unittest
from pathlib import Path

from scripts.summarize_relaxed_factor_screens import CASE_TAGS, summarize


def audit(*, factor_ops: float, factor_nz: float, fingerprint: int = 7) -> dict:
    return {
        "solver_profile_id": "profile",
        "lp_gurobi_fingerprint": fingerprint,
        "lp_identity_variables": 10,
        "lp_identity_constraints": 20,
        "lp_identity_nonzeros": 30,
        "original_rows": 20,
        "original_columns": 10,
        "original_nonzeros": 30,
        "resolved_scientific_configuration_sha256": "science",
        "scenario_configuration_sha256": "scenario",
        "presolved_rows": 18,
        "presolved_columns": 9,
        "presolved_nonzeros": 25,
        "dense_columns": 2,
        "aa_transpose_nonzeros": 50.0,
        "factor_nonzeros": factor_nz,
        "factor_operations": factor_ops,
        "barrier_iterations": 5,
        "numerical_trouble_count": 0,
        "telemetry_phase_summaries": {
            "barrier": {
                "observed_seconds_per_iteration": factor_ops / 100.0,
                "last_primal_infeasibility": 1.0,
                "last_dual_infeasibility": 0.1,
                "last_complementarity": 2.0,
                "last_raw_primal_dual_objective_gap": 3.0,
            }
        },
    }


class RelaxedFactorScreenSummaryTests(unittest.TestCase):
    def _write_case(self, control: Path, tag: str, payload: dict) -> None:
        case = control / tag
        case.mkdir(parents=True)
        (case / "solver_audit.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        (case / "return_code.txt").write_text("2\n", encoding="utf-8")
        (case / "stderr.log").write_text("", encoding="utf-8")

    def test_shortlist_requires_material_structural_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            baseline_path = root / "baseline.json"
            baseline_path.write_text(
                json.dumps(audit(factor_ops=1000.0, factor_nz=100.0)),
                encoding="utf-8",
            )
            control = root / "control"
            values = ((800.0, 90.0), (970.0, 96.0), (1100.0, 105.0))
            for tag, (ops, nz) in zip(CASE_TAGS, values):
                self._write_case(
                    control, tag, audit(factor_ops=ops, factor_nz=nz)
                )
            report = summarize(baseline_path, control)

        self.assertEqual(report["status"], "SHORTLIST_READY")
        self.assertTrue(report["all_paired_screens_valid"])
        self.assertEqual(report["shortlist_tags"], ["nf0_scale2"])
        self.assertFalse(report["automatic_winner_selected"])
        self.assertFalse(report["scientifically_accepted"])

    def test_identity_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            baseline_path = root / "baseline.json"
            baseline_path.write_text(
                json.dumps(audit(factor_ops=1000.0, factor_nz=100.0)),
                encoding="utf-8",
            )
            control = root / "control"
            for tag in CASE_TAGS:
                payload = audit(factor_ops=800.0, factor_nz=90.0)
                if tag == "nf0_scaleauto":
                    payload["lp_gurobi_fingerprint"] = 8
                self._write_case(control, tag, payload)
            report = summarize(baseline_path, control)

        self.assertEqual(report["status"], "SCREEN_AUDIT_INCOMPLETE")
        bad = next(case for case in report["cases"] if case["tag"] == "nf0_scaleauto")
        self.assertIn("lp_or_scientific_identity_mismatch", bad["screen_failures"])
        self.assertFalse(bad["shortlist_eligible"])


if __name__ == "__main__":
    unittest.main()
