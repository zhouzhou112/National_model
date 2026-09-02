from __future__ import annotations

import os
import math
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.guard_stagea_row_scaling_2160 import (
    EXPECTED_ORIGINAL,
    FACTOR_UPPER_BOUNDS,
    _barrier_records,
    evaluate_qualification,
)


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "run_fixed_server_stagea_row_scaling_2160.sh"


def bash_path():
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git:
        candidate = Path(git).resolve().parents[1] / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None


class StageARowScalingQualificationTests(unittest.TestCase):
    def complete_log_metrics(self):
        return {
            **EXPECTED_ORIGINAL,
            **{key: value * 0.99 for key, value in FACTOR_UPPER_BOUNDS.items()},
            "numerical_trouble_count": 0,
            "suboptimal_termination_warning": False,
        }

    def test_iteration_30_passes_only_with_all_factor_evidence(self):
        decision = evaluate_qualification(
            self.complete_log_metrics(),
            {"iteration": 30, "runtime_seconds": 11_999, "work_units": 18_960},
            process_group_rss_bytes=74 * 1024**3,
            host_memory_used_percent=80.0,
        )
        self.assertEqual(decision["status"], "PASS_ITERATION_30_CONTINUE")
        missing = self.complete_log_metrics()
        missing.pop("factor_operations")
        decision = evaluate_qualification(
            missing,
            {"iteration": 30, "runtime_seconds": 11_000, "work_units": 18_000},
            process_group_rss_bytes=70 * 1024**3,
            host_memory_used_percent=80.0,
        )
        self.assertEqual(decision["status"], "FAIL")
        self.assertTrue(
            any("missing_factor_evidence" in row for row in decision["failures"])
        )

    def test_any_runtime_work_memory_or_factor_regression_fails(self):
        cases = (
            ("runtime", {"runtime_seconds": 12_001, "work_units": 10_000}, 70),
            ("work", {"runtime_seconds": 10_000, "work_units": 18_962}, 70),
            ("rss", {"runtime_seconds": 10_000, "work_units": 10_000}, 76),
        )
        for label, barrier_values, rss in cases:
            with self.subTest(label=label):
                decision = evaluate_qualification(
                    self.complete_log_metrics(),
                    {"iteration": 29, **barrier_values},
                    process_group_rss_bytes=rss * 1024**3,
                    host_memory_used_percent=80.0,
                )
                self.assertEqual(decision["status"], "FAIL")
        metrics = self.complete_log_metrics()
        metrics["factor_nonzeros"] = FACTOR_UPPER_BOUNDS["factor_nonzeros"] + 1
        decision = evaluate_qualification(
            metrics,
            None,
            process_group_rss_bytes=1,
            host_memory_used_percent=80.0,
        )
        self.assertEqual(decision["status"], "FAIL")

    def test_iteration_budget_is_locked_after_the_same_run_passes(self):
        decision = evaluate_qualification(
            self.complete_log_metrics(),
            {
                "iteration": 31,
                "runtime_seconds": 12_500,
                "work_units": 19_500,
            },
            process_group_rss_bytes=70 * 1024**3,
            host_memory_used_percent=80.0,
            iteration_gate_already_passed=True,
        )
        self.assertEqual(decision["status"], "PASS_ITERATION_30_CONTINUE")
        self.assertTrue(decision["iteration_gate_passed"])
        self.assertEqual(decision["failures"], [])

        metrics = self.complete_log_metrics()
        metrics["numerical_trouble_count"] = 1
        decision = evaluate_qualification(
            metrics,
            {
                "iteration": 31,
                "runtime_seconds": 12_500,
                "work_units": 19_500,
            },
            process_group_rss_bytes=70 * 1024**3,
            host_memory_used_percent=80.0,
            iteration_gate_already_passed=True,
        )
        self.assertEqual(decision["status"], "FAIL")

    def test_gate_uses_first_record_at_iteration_30(self):
        with tempfile.TemporaryDirectory() as temporary:
            telemetry = Path(temporary) / "solver_telemetry.jsonl"
            rows = [
                {
                    "event": "solver_progress",
                    "phase": "barrier",
                    "iteration": 29,
                    "runtime_seconds": 11_900,
                    "work_units": 18_800,
                },
                {
                    "event": "solver_progress",
                    "phase": "barrier",
                    "iteration": 30,
                    "runtime_seconds": 11_999,
                    "work_units": 18_960,
                },
                {
                    "event": "solver_progress",
                    "phase": "barrier",
                    "iteration": 31,
                    "runtime_seconds": 12_500,
                    "work_units": 19_500,
                },
            ]
            telemetry.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            latest, gate = _barrier_records(telemetry)
        decision = evaluate_qualification(
            self.complete_log_metrics(),
            latest,
            iteration_gate_barrier=gate,
            process_group_rss_bytes=70 * 1024**3,
            host_memory_used_percent=80.0,
        )
        self.assertEqual(decision["status"], "PASS_ITERATION_30_CONTINUE")
        self.assertEqual(decision["iteration_gate_evidence"]["iteration"], 30)

    def test_nonfinite_or_malformed_metrics_fail_closed(self):
        for label, metrics, barrier in (
            (
                "factor_nan",
                {**self.complete_log_metrics(), "factor_operations": math.nan},
                None,
            ),
            (
                "runtime_nan",
                self.complete_log_metrics(),
                {
                    "iteration": 30,
                    "runtime_seconds": math.nan,
                    "work_units": 1,
                },
            ),
            (
                "iteration_text",
                self.complete_log_metrics(),
                {
                    "iteration": "not-a-number",
                    "runtime_seconds": 1,
                    "work_units": 1,
                },
            ),
        ):
            with self.subTest(label=label):
                decision = evaluate_qualification(
                    metrics,
                    barrier,
                    process_group_rss_bytes=70 * 1024**3,
                    host_memory_used_percent=80.0,
                )
                self.assertEqual(decision["status"], "FAIL")

    def test_guard_cli_is_self_contained_without_pythonpath(self):
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "guard_stagea_row_scaling_2160.py"),
                "--help",
            ],
            cwd=Path(tempfile.gettempdir()),
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--process-group", result.stdout)

    @unittest.skipUnless(bash_path(), "Bash is required for syntax validation")
    def test_dedicated_launcher_is_single_route_and_shell_valid(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        result = subprocess.run(
            [bash_path(), "-n"],
            input=source,
            text=True,
            capture_output=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("barrier_checkpoint_fixed_server_host_memory_95_v2.json", source)
        self.assertIn("annual_capacity_link_rows_8192_v1.json", source)
        self.assertIn("--engineering-barrier-checkpoint-only", source)
        self.assertIn("taskset -c 0-31", source)
        self.assertIn("unique_physical_cores", source)
        self.assertIn("node_counts != {0: 16, 1: 16}", source)
        self.assertIn("expected_cpus.issubset(allowed_cpus)", source)
        self.assertIn('solver_affinity" != "0-31"', source)
        self.assertIn("repo_owner_uid", source)
        self.assertIn("REQUESTED_EXPECTED_GIT_SHA", source)
        self.assertIn("gp.gurobi.version() == (13, 0, 2)", source)
        self.assertIn("OUTPUT_ROOT=$canonical_output", source)
        self.assertIn("refuse output root inside Git checkout", source)
        self.assertIn("refuse control root inside Git checkout", source)
        self.assertIn("process_cgroups.txt", source)
        self.assertIn("QUALIFICATION_GUARD_EXITED_WHILE_SOLVER_ALIVE", source)
        self.assertIn("trap 'handle_wrapper_signal TERM 143' TERM", source)
        self.assertIn('kill -TERM -- "-$run_pid"', source)
        self.assertLess(
            source.index("trap 'handle_wrapper_signal TERM 143' TERM"),
            source.index("setsid /usr/bin/numactl"),
        )
        self.assertIn("guard_kill_required", source)
        self.assertIn("NR > 3 && ($7 != 0 || $8 != 0)", source)
        self.assertNotIn("NR > 2 && ($7 != 0 || $8 != 0)", source)
        self.assertNotIn("Stage B", source.replace("No Stage B", ""))
        self.assertNotIn("/usr/bin/time", source)


if __name__ == "__main__":
    unittest.main()
