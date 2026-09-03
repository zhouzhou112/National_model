from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cispo_model.config import load_model_config
from scripts.run_cispo_2030_full_year import (
    cloud_full_year_profile_role,
    cloud_full_year_required_memory_gib,
    persist_postsolve_finalization_error,
    require_canonical_direct_nonbasic_profiles,
    resolve_host_memory_soft_limit_gb,
    write_strict_json_atomic,
)


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

    def test_strict_atomic_json_failure_preserves_prior_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "solve_report.json"
            target.write_text('{"status": "accepted"}\n', encoding="utf-8")

            with self.assertRaises(ValueError):
                write_strict_json_atomic(target, {"invalid": float("nan")})

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                '{"status": "accepted"}\n',
            )

    def test_postsolve_error_retains_accepted_checkpoint_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            checkpoint = output / "barrier_checkpoint"
            checkpoint.mkdir()
            evidence_paths = (
                output / "solve_report.json",
                output / "solution_qc.json",
                checkpoint / "barrier_checkpoint_manifest.json",
            )
            for index, path in enumerate(evidence_paths):
                path.write_text(
                    json.dumps({"evidence": index}) + "\n",
                    encoding="utf-8",
                )

            payload = persist_postsolve_finalization_error(
                output,
                failed_stage="dashboard",
                error=RuntimeError("packaging failed"),
                report={
                    "barrier_checkpoint": {
                        "scientifically_accepted": True,
                    }
                },
            )

            self.assertTrue(payload["accepted_checkpoint_retained"])
            self.assertEqual(
                set(payload["immutable_evidence"]),
                {
                    "solve_report.json",
                    "solution_qc.json",
                    "barrier_checkpoint/barrier_checkpoint_manifest.json",
                },
            )
            self.assertTrue(
                all(
                    len(item["sha256"]) == 64 and item["bytes"] > 0
                    for item in payload["immutable_evidence"].values()
                )
            )
            self.assertEqual(
                json.loads(
                    (output / "finalization_error.json").read_text(
                        encoding="utf-8"
                    )
                ),
                payload,
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
            cloud_full_year_profile_role("barrier_checkpoint_full_year_cloud_v3"),
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
        self.assertEqual(
            cloud_full_year_profile_role("deferred_crossover2_full_year_cloud_v3"),
            "STAGE_B",
        )
        self.assertIsNone(cloud_full_year_profile_role("barrier_16_auto_order_v2"))
        self.assertIsNone(cloud_full_year_profile_role(None))

    def test_all_cloud_profile_versions_receive_memory_floor(self) -> None:
        for profile_id in (
            "barrier_checkpoint_full_year_cloud_v1",
            "barrier_checkpoint_full_year_cloud_v2",
            "barrier_checkpoint_full_year_cloud_v3",
            "barrier_checkpoint_full_year_cloud_v99",
            "deferred_crossover2_full_year_cloud_v2",
            "deferred_crossover2_full_year_cloud_v3",
        ):
            with self.subTest(profile_id=profile_id):
                self.assertEqual(
                    cloud_full_year_required_memory_gib(
                        80.0,
                        cloud_full_year_profile_role(profile_id),
                    ),
                    640.0,
                )
        self.assertEqual(
            cloud_full_year_required_memory_gib(
                80.0,
                cloud_full_year_profile_role("barrier_16_auto_order_v2"),
            ),
            80.0,
        )
        self.assertEqual(
            cloud_full_year_required_memory_gib("700", "STAGE_A"),
            700.0,
        )

    def test_host_memory_fraction_resolves_to_decimal_gb(self) -> None:
        gib = 1024**3
        self.assertAlmostEqual(
            resolve_host_memory_soft_limit_gb(128 * gib, 0.95),
            130.5670057984,
        )
        for invalid in (0.0, -0.1, 0.951, 1.0):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    resolve_host_memory_soft_limit_gb(128 * gib, invalid)

    def test_fixed_server_host95_profile_requires_stage_a_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--diagnostic-hours",
                "2160",
                "--solver-config",
                str(
                    PROFILES
                    / "barrier_checkpoint_fixed_server_host_memory_95_v1.json"
                ),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "barrier_checkpoint_fixed_server_host_memory_95_v1 requires "
            "--engineering-barrier-checkpoint-only",
            result.stdout + result.stderr,
        )

    def test_fixed_server_host95_profile_rejects_full_year(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--horizon",
                "full_year",
                "--solver-config",
                str(
                    PROFILES
                    / "barrier_checkpoint_fixed_server_host_memory_95_v1.json"
                ),
                "--engineering-barrier-checkpoint-only",
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "barrier_checkpoint_fixed_server_host_memory_95_v1 is restricted "
            "to test-only truncated horizons",
            result.stdout + result.stderr,
        )

    def test_fixed_server_v2_requires_row_scaling_formulation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--diagnostic-hours",
                "2160",
                "--solver-config",
                str(
                    PROFILES
                    / "barrier_checkpoint_fixed_server_host_memory_95_v2.json"
                ),
                "--engineering-barrier-checkpoint-only",
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "requires formulation profile annual_capacity_link_rows_8192_v1",
            result.stdout + result.stderr,
        )

    def test_preflight_rejects_archive_flags_instead_of_ignoring_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--preflight-only",
                "--archive-original-model",
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "cannot be combined with build/write/archive options",
            result.stdout + result.stderr,
        )

    def test_historical_stage_a_profiles_retain_engineering_only_contract(
        self,
    ) -> None:
        for version in ("v1", "v2", "v3"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                result = self.run_runner(
                    "--horizon",
                    "full_year",
                    "--solver-config",
                    str(
                        PROFILES
                        / f"barrier_checkpoint_full_year_cloud_{version}.json"
                    ),
                    "--output-dir",
                    str(Path(temporary) / "output"),
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "requires --engineering-barrier-checkpoint-only",
                result.stdout + result.stderr,
            )

    def test_strict_stage_a_v4_can_attempt_direct_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--horizon",
                "full_year",
                "--solver-config",
                str(PROFILES / "barrier_checkpoint_full_year_cloud_v4.json"),
                "--formulation-config",
                str(
                    ROOT
                    / "config"
                    / "formulation_profiles"
                    / "annual_capacity_link_rows_8192_v1.json"
                ),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertNotIn(
            "requires --engineering-barrier-checkpoint-only", combined
        )
        # The next fail-closed boundary is environment-dependent (scientific
        # input provenance on a clean test host, or the 640 GiB memory floor
        # where all inputs are mounted).  Reaching either proves that v4 alone
        # passed the explicit direct-nonbasic authorization gate.
        self.assertTrue(
            "< 640.0 GiB required for full_year" in combined
            or "Missing required input" in combined
            or "Required input root" in combined
            or "Required provenance inputs are missing" in combined,
            combined,
        )

    def test_v5_thread_pair_is_canonical_and_differs_only_by_resource_fields(
        self,
    ) -> None:
        formulation = (
            ROOT
            / "config"
            / "formulation_profiles"
            / "annual_capacity_link_rows_8192_v1.json"
        )
        profiles = []
        for suffix in ("threads32", "threads64"):
            path = (
                PROFILES
                / f"barrier_checkpoint_full_year_cloud_v5_{suffix}.json"
            )
            config = load_model_config(
                solver_path=path,
                formulation_path=formulation,
            )
            require_canonical_direct_nonbasic_profiles(config)
            profiles.append(json.loads(path.read_text(encoding="utf-8")))

        left = profiles[0]["numerics"]
        right = profiles[1]["numerics"]
        differing = {
            key
            for key in set(left) | set(right)
            if left.get(key) != right.get(key)
        }
        self.assertEqual(differing, {"threads", "soft_mem_limit_gb"})
        self.assertEqual(left["threads"], 32)
        self.assertEqual(right["threads"], 64)
        self.assertIsNone(left["time_limit_seconds"])
        self.assertIsNone(right["time_limit_seconds"])
        self.assertLessEqual(left["soft_mem_limit_gb"], 520)
        self.assertLessEqual(right["soft_mem_limit_gb"], 700)

    def test_final_v6_profile_is_canonical_and_uses_split_acceptance(self) -> None:
        formulation = (
            ROOT
            / "config"
            / "formulation_profiles"
            / "annual_capacity_link_rows_8192_v1.json"
        )
        profile = PROFILES / "barrier_stagea_final_full_year_cloud_v6_threads32.json"
        config = load_model_config(
            solver_path=profile,
            formulation_path=formulation,
        )
        require_canonical_direct_nonbasic_profiles(config)
        self.assertEqual(
            cloud_full_year_profile_role(config.raw["solver_profile"]["id"]),
            "STAGE_A",
        )
        self.assertFalse(config.raw["solver_profile"]["stage_b_required"])
        self.assertEqual(
            config.raw["numerics"]["barrier_convergence_tolerance"], 1e-2
        )
        self.assertEqual(
            config.raw["solver_profile"]["stage_a_acceptance"]
            ["maximum_relative_primal_dual_objective_gap"],
            1e-2,
        )

    def test_final_cloud_wrapper_is_single_stage_a_and_cgroup_limited(self) -> None:
        source = (ROOT / "scripts" / "run_cloud_8760_scientific_job.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("barrier_stagea_final_full_year_cloud_v6_threads32", source)
        self.assertIn("memory.max", source)
        self.assertIn("memory.limit_in_bytes", source)
        self.assertIn("0.85 * limit", source)
        self.assertIn("64 * 1024**3", source)
        self.assertIn("terminal_status.json", source)
        self.assertIn("wrapper_rc == 0", source)
        self.assertIn('result_manifest = read("result_manifest.json")', source)
        self.assertIn('trap \'finalize_wrapper "$?"\' EXIT', source)
        self.assertNotIn("Stage B watcher", source)

    def test_noncloud_nonbasic_profile_cannot_enter_direct_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--diagnostic-hours",
                "24",
                "--solver-config",
                str(PROFILES / "barrier_16_nonbasic_primal_dual_v1.json"),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "requires --engineering-barrier-checkpoint-only",
            result.stdout + result.stderr,
        )

    def test_custom_profile_cannot_self_authorize_direct_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = json.loads(
                (PROFILES / "barrier_16_nonbasic_primal_dual_v1.json").read_text(
                    encoding="utf-8"
                )
            )
            payload["profile_id"] = "unreviewed_direct_profile"
            payload["direct_nonbasic_scientific_acceptance"] = True
            profile = root / "solver.json"
            profile.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_runner(
                "--diagnostic-hours",
                "24",
                "--solver-config",
                str(profile),
                "--output-dir",
                str(root / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "reserved for the reviewed full-year Stage A profile",
            result.stdout + result.stderr,
        )

    def test_same_id_modified_solver_profile_cannot_self_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = json.loads(
                (PROFILES / "barrier_checkpoint_full_year_cloud_v4.json").read_text(
                    encoding="utf-8"
                )
            )
            payload["numerics"]["threads"] = 16
            candidate = root / "solver.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            config = load_model_config(
                solver_path=candidate,
                formulation_path=(
                    ROOT
                    / "config"
                    / "formulation_profiles"
                    / "annual_capacity_link_rows_8192_v1.json"
                ),
            )
            with self.assertRaisesRegex(
                SystemExit,
                "solver profile content differs",
            ):
                require_canonical_direct_nonbasic_profiles(config)

    def test_same_id_modified_formulation_cannot_self_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = (
                ROOT
                / "config"
                / "formulation_profiles"
                / "annual_capacity_link_rows_8192_v1.json"
            )
            payload = json.loads(canonical.read_text(encoding="utf-8"))
            payload["formulation"]["annual_capacity_link_row_scaling"] = (
                "physical_v1"
            )
            candidate = root / "formulation.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            config = load_model_config(
                solver_path=(
                    PROFILES / "barrier_checkpoint_full_year_cloud_v4.json"
                ),
                formulation_path=candidate,
            )
            with self.assertRaisesRegex(
                SystemExit,
                "formulation profile content differs",
            ):
                require_canonical_direct_nonbasic_profiles(config)

    def test_stage_a_v4_rejects_missing_required_formulation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_runner(
                "--horizon",
                "full_year",
                "--solver-config",
                str(PROFILES / "barrier_checkpoint_full_year_cloud_v4.json"),
                "--output-dir",
                str(Path(temporary) / "output"),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "requires formulation profile annual_capacity_link_rows_8192_v1",
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
