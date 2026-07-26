from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cispo_model.diagnostics import SolverTelemetry


class SolverTelemetryTests(unittest.TestCase):
    def test_jsonl_events_are_flushed_and_machine_readable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "solver_telemetry.jsonl"
            telemetry = SolverTelemetry(path)
            telemetry.write_event(
                "solver_progress",
                phase="barrier",
                iteration=7.0,
                memory_used_gb=12.5,
            )
            records = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(records[0]["event"], "solver_progress")
            self.assertEqual(records[0]["phase"], "barrier")
            self.assertEqual(records[0]["iteration"], 7.0)
            telemetry.close()

    def test_progress_throttling_keeps_each_barrier_iteration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            telemetry = SolverTelemetry(Path(temp_dir) / "telemetry.jsonl")
            self.assertTrue(
                telemetry._should_record(
                    "barrier", 0.0, 10.0, iteration_step=1.0
                )
            )
            self.assertFalse(
                telemetry._should_record(
                    "barrier", 0.0, 11.0, iteration_step=1.0
                )
            )
            self.assertTrue(
                telemetry._should_record(
                    "barrier", 1.0, 12.0, iteration_step=1.0
                )
            )
            telemetry.close()


if __name__ == "__main__":
    unittest.main()
