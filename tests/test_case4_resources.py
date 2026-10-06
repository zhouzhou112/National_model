from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from monitor_case_resources import gpu_rows, update_summary
from start_case4_after_recovery import claim_launch, gpu_gate, recovery_gate, readiness


GPU = "1, GPU-test, RTX 4090, 24564, 36, 24047, 0, 10, 24, 9.06, 450, P8\n"


class ResourceTests(unittest.TestCase):
    def test_unlimited_profile_changes_only_time_limit(self):
        root = Path(__file__).resolve().parents[1] / "config/solver_profiles"
        original = json.loads((root / "large_lp_2160_case4_gpu_pdhg_screen_v1.json").read_text())
        unlimited = json.loads((root / "large_lp_2160_case4_gpu_pdhg_unlimited_v2.json").read_text())
        self.assertEqual(unlimited["solver_profile_version"], "v1")
        self.assertIsNone(unlimited["numerics"]["time_limit_seconds"])
        expected = dict(original["numerics"], time_limit_seconds=None)
        self.assertEqual(unlimited["numerics"], expected)

    def test_gpu_memory_activity_is_not_capacity(self):
        gpu = gpu_rows(GPU)[0]
        self.assertEqual(gpu["memory_controller_util_percent"], 10)
        self.assertAlmostEqual(gpu["vram_used_percent"], 36 / 24564 * 100)

    def test_unsupported_sensor_is_null(self):
        self.assertIsNone(gpu_rows(GPU.replace("9.06", "[N/A]"))[0]["power_w"])

    def test_malformed_telemetry_rejected(self):
        with self.assertRaises(ValueError):
            gpu_rows("1, invalid\n")

    def test_gpu_gate_respects_other_clients(self):
        self.assertEqual(gpu_gate(gpu_rows(GPU), "GPU-test, 123, 10\n", "1"), "WAITING_GPU_CLIENTS")
        self.assertEqual(gpu_gate(gpu_rows(GPU), "GPU-other, 123, 10\n", "1"), "READY")
        self.assertEqual(gpu_gate(gpu_rows(GPU.replace("24047", "1000")), "", "1"), "WAITING_GPU_RESOURCES")
        self.assertEqual(gpu_gate(gpu_rows(GPU), "", "2"), "BLOCKED_GPU_MISSING")

    def test_summary_retains_peaks(self):
        summary = {}
        record = {"timestamp_utc": "now", "errors": [], "host": {
            "memory_used_percent": 50, "swap_used_bytes": 20, "memory_available_bytes": 100},
            "process_group": {"rss_bytes": 60}, "gpus": gpu_rows(GPU)}
        update_summary(summary, record)
        record["process_group"]["rss_bytes"] = 10
        record["host"]["memory_available_bytes"] = 80
        update_summary(summary, record)
        self.assertEqual(summary["job_rss_bytes_peak"], 60)
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["host_memory_available_bytes_min"], 80)

    def test_recovery_gate_waits_and_blocks_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(recovery_gate(root), "WAITING_RECOVERY")
            (root / "control").mkdir()
            (root / "control/return_code.txt").write_text("1")
            self.assertEqual(recovery_gate(root), "BLOCKED_RECOVERY_FAILED")
            (root / "control/return_code.txt").write_text("0")
            self.assertEqual(recovery_gate(root), "BLOCKED_RECOVERY_INCOMPLETE")

    def test_complete_recovery_can_have_failed_scientific_qc(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "control").mkdir()
            (root / "control/return_code.txt").write_text("0")
            out = root / "recovered_8760"
            out.mkdir()
            progress = {"status": "COMPLETE", "optimize_calls": 0, "presolve_calls": 0}
            (out / "recovery_progress.json").write_text(json.dumps(progress))
            (out / "preservation_report.json").write_text(json.dumps({"status": "COMPLETE", "qc_status": "FAIL"}))
            (out / "result_manifest.json").write_text("{}")
            self.assertEqual(recovery_gate(root), "READY")
            progress["optimize_calls"] = 1
            (out / "recovery_progress.json").write_text(json.dumps(progress))
            self.assertEqual(recovery_gate(root), "BLOCKED_RECOVERY_INCOMPLETE")

    def test_launch_claim_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "launch_claim.json"
            claim_launch(path, {"first": True})
            with self.assertRaises(FileExistsError):
                claim_launch(path, {"second": True})
            self.assertEqual(json.loads(path.read_text()), {"first": True})

    def test_independent_authorization_does_not_skip_running_process_gate(self):
        args = SimpleNamespace(recovery_root=Path("unused"), independent_after_failed_recovery=True)
        with patch("start_case4_after_recovery.recovery_gate", return_value="BLOCKED_RECOVERY_FAILED"), \
             patch("start_case4_after_recovery.model_processes", return_value=[{"pid": 123}]):
            result = readiness(args)
        self.assertEqual(result["status"], "WAITING_MODEL_PROCESS")
        self.assertEqual(result["recovery_status"], "BLOCKED_RECOVERY_FAILED")
        self.assertTrue(result["independent_after_failed_recovery"])

    def test_independent_authorization_cannot_skip_incomplete_or_running_recovery(self):
        args = SimpleNamespace(recovery_root=Path("unused"), independent_after_failed_recovery=True)
        for status in ("WAITING_RECOVERY", "BLOCKED_RECOVERY_INCOMPLETE"):
            with patch("start_case4_after_recovery.recovery_gate", return_value=status):
                self.assertEqual(readiness(args)["status"], status)


if __name__ == "__main__":
    unittest.main()
