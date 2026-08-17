from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.run_cispo_2030_full_year import cloud_full_year_profile_role


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_cispo_2030_full_year.py"
PROFILES = ROOT / "config" / "solver_profiles"


class CloudFullYearProfileGuardTests(unittest.TestCase):
    def run_runner(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNNER), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_all_profile_versions_are_classified_by_role(self) -> None:
        self.assertEqual(
            cloud_full_year_profile_role("barrier_checkpoint_full_year_cloud_v1"),
            "STAGE_A",
        )
        self.assertEqual(
            cloud_full_year_profile_role("barrier_checkpoint_full_year_cloud_v2"),
            "STAGE_A",
        )
        self.assertEqual(
            cloud_full_year_profile_role("barrier_checkpoint_full_year_cloud_v99"),
            "STAGE_A",
        )
        self.assertEqual(
            cloud_full_year_profile_role("deferred_crossover2_full_year_cloud_v2"),
            "STAGE_B",
        )
        self.assertIsNone(cloud_full_year_profile_role("barrier_16_auto_order_v2"))
        self.assertIsNone(cloud_full_year_profile_role(None))

    def test_stage_a_v2_requires_engineering_checkpoint_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--horizon",
                "full_year",
                "--solver-config",
                str(PROFILES / "barrier_checkpoint_full_year_cloud_v2.json"),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "barrier_checkpoint_full_year_cloud_v2 requires "
            "--engineering-barrier-checkpoint-only",
            result.stdout + result.stderr,
        )

    def test_stage_b_v2_requires_checkpoint_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--horizon",
                "full_year",
                "--solver-config",
                str(PROFILES / "deferred_crossover2_full_year_cloud_v2.json"),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "deferred_crossover2_full_year_cloud_v2 requires "
            "--primal-dual-checkpoint-in",
            result.stdout + result.stderr,
        )

    def test_stage_a_v2_is_rejected_for_a_truncated_horizon(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--diagnostic-hours",
                "24",
                "--solver-config",
                str(PROFILES / "barrier_checkpoint_full_year_cloud_v2.json"),
                "--engineering-barrier-checkpoint-only",
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "barrier_checkpoint_full_year_cloud_v2 is restricted to the "
            "scientific full-year horizon",
            result.stdout + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
