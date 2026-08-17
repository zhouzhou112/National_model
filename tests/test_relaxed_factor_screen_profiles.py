import json
import unittest
from pathlib import Path

from cispo_model.config import load_model_config


ROOT = Path(__file__).resolve().parents[1]
PROFILE_NAMES = (
    "barrier_16_engineering_factor_nf0_scale2_5iter_v1.json",
    "barrier_16_engineering_factor_nf1_scaleauto_5iter_v1.json",
    "barrier_16_engineering_factor_nf0_scaleauto_5iter_v1.json",
)
ROUND2_PROFILE_NAMES = (
    "barrier_16_engineering_factor_presparsify2_5iter_v1.json",
    "barrier_16_engineering_factor_barorder1_5iter_v1.json",
    "barrier_32_engineering_factor_threads32_5iter_v1.json",
)


class RelaxedFactorScreenProfileTests(unittest.TestCase):
    def test_factor_screens_change_only_numeric_focus_and_scaling(self) -> None:
        profiles = []
        for name in PROFILE_NAMES:
            path = ROOT / "config" / "solver_profiles" / name
            source = json.loads(path.read_text(encoding="utf-8"))
            config = load_model_config(
                ROOT / "config" / "optimization_2030.json",
                ROOT / "config" / "scenarios" / "base.json",
                path,
                None,
            )
            self.assertEqual(config.raw["solver_profile"]["id"], source["profile_id"])
            profiles.append(config.raw["numerics"])
        expected_pairs = ((0, 2), (1, -1), (0, -1))
        ignored = {"numeric_focus", "scale_flag"}
        reference = {key: value for key, value in profiles[0].items() if key not in ignored}
        for profile, expected_pair in zip(profiles, expected_pairs):
            self.assertEqual(
                (profile["numeric_focus"], profile["scale_flag"]), expected_pair
            )
            self.assertEqual(
                {key: value for key, value in profile.items() if key not in ignored},
                reference,
            )
            self.assertEqual(profile["bar_iter_limit"], 5)
            self.assertEqual(profile["crossover"], 0)
            self.assertEqual(profile["barrier_convergence_tolerance"], 1e-2)
            self.assertEqual(profile["feasibility_tolerance"], 1e-5)
            self.assertEqual(profile["optimality_tolerance"], 1e-5)

    def test_runner_builds_fail_closed_baseline_and_summary(self) -> None:
        runner = (
            ROOT / "scripts" / "run_fixed_server_relaxed_factor_screens.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("BASELINE_OUTPUT=", runner)
        self.assertIn("refuse_invalid_baseline_audit", runner)
        self.assertIn("baseline_solver_audit.json", runner)
        self.assertIn("summarize_relaxed_factor_screens.py", runner)
        self.assertIn("export CISPO_DATA_ROOT=", runner)
        self.assertIn("export CISPO_CF_ROOT=", runner)
        self.assertIn("export CISPO_HYDRO_ROOT=", runner)
        self.assertIn("export CISPO_RAW_GRFR_ROOT=", runner)
        self.assertIn("export CISPO_WAVE_ROOT=", runner)
        self.assertIn("factor_screen_summary.json", runner)
        self.assertIn("factor_screen_summary.csv", runner)

    def test_round2_profiles_change_only_targeted_factor_or_thread_parameter(self) -> None:
        profiles = []
        for name in ROUND2_PROFILE_NAMES:
            path = ROOT / "config" / "solver_profiles" / name
            profiles.append(
                load_model_config(
                    ROOT / "config" / "optimization_2030.json",
                    ROOT / "config" / "scenarios" / "base.json",
                    path,
                    None,
                ).raw["numerics"]
            )
        ignored = {"pre_sparsify", "bar_order", "threads"}
        reference = {
            key: value for key, value in profiles[0].items() if key not in ignored
        }
        expected = ((2, -1, 16), (-1, 1, 16), (-1, -1, 32))
        for profile, target in zip(profiles, expected):
            self.assertEqual(
                (
                    profile.get("pre_sparsify", -1),
                    profile.get("bar_order", -1),
                    profile["threads"],
                ),
                target,
            )
            self.assertEqual(
                {key: value for key, value in profile.items() if key not in ignored},
                reference,
            )
            self.assertEqual(profile["bar_iter_limit"], 5)
            self.assertEqual(profile["crossover"], 0)

    def test_round2_wrapper_freezes_cases_baseline_and_dual_gates(self) -> None:
        wrapper = (
            ROOT / "scripts" / "run_fixed_server_relaxed_factor_screens_round2.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("presparsify2,barorder1,threads32", wrapper)
        self.assertIn("relaxed_factor_screens_v0817_v1/nf1_scaleauto", wrapper)
        self.assertIn("MATERIAL_STRUCTURAL_REDUCTION_FRACTION=0.05", wrapper)
        self.assertIn("MATERIAL_RUNTIME_REDUCTION_FRACTION=0.10", wrapper)


if __name__ == "__main__":
    unittest.main()
