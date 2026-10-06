"""Exercise launcher setup/gates in isolation; never start a solver or use SSH."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "run_fixed_server_2160_campaign_case.sh"


def bash_path():
    explicit = os.environ.get("CISPO_TEST_BASH")
    if explicit:
        return explicit
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git:
        candidate = Path(git).resolve().parents[1] / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None  # Do not accidentally invoke Windows' WSL bash launcher.


def shell_path(path):
    path = Path(path).resolve()
    if os.name == "nt":
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return path.as_posix()


@unittest.skipUnless(bash_path(), "Bash is required for launcher tests")
class CampaignLauncherTests(unittest.TestCase):
    def run_setup(self, case_id, requested_python=None, process=""):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            environment = root / "server_env.sh"
            environment.write_text(
                'export CISPO_PYTHON="/mock/cpu/bin/python"\n', encoding="utf-8"
            )
            env = os.environ.copy()
            for key in (
                "CISPO_PYTHON", "GPU_RUNTIME_ROOT", "OUTPUT_ROOT", "CONTROL_ROOT",
                "TAG", "HOURS", "START_HOUR", "SCENARIO",
            ):
                env.pop(key, None)
            env.update(
                CISPO_SERVER_ROOT=shell_path(root),
                CISPO_SERVER_ENV=shell_path(environment),
                CISPO_REPO_ROOT=shell_path(repo),
                CASE_ID=case_id,
                GPU_DEVICE="1",
                TEST_PROCESS=process,
            )
            if requested_python is not None:
                env["CISPO_PYTHON"] = requested_python
            source = LAUNCHER.read_text(encoding="utf-8")
            prefix, marker, _ = source.partition("\navailable_gib=")
            self.assertTrue(marker, "test boundary must precede memory probe/launch")
            mocks = '''
git() { return 0; }
pgrep() { printf '%s\\n' "$TEST_PROCESS" | grep -E -- "$2"; }
'''
            # Run actual case selection and process gate, but stop before any
            # interpreter invocation, memory probe, monitoring or solver launch.
            script = mocks + prefix + '''
printf 'selected_python=%s\\n' "$PYTHON"
printf 'visible_devices=%s\\n' "${CUDA_VISIBLE_DEVICES:-}"
'''
            setup_path = root / "setup.sh"
            setup_path.write_text(script, encoding="utf-8", newline="\n")
            result = subprocess.run(
                [bash_path(), "--noprofile", "--norc", shell_path(setup_path)],
                text=True, capture_output=True, env=env, timeout=15,
            )
            return result, shell_path(root)

    def test_shell_syntax(self):
        result = subprocess.run(
            [bash_path(), "-n"], input=LAUNCHER.read_text(encoding="utf-8"),
            text=True, capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_cpu_case_uses_shared_cpu_environment(self):
        result, _ = self.run_setup("case1_v3_barrier16_stage_a")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("selected_python=/mock/cpu/bin/python", result.stdout)

    def test_gpu_case_defaults_to_gpu_environment(self):
        result, root = self.run_setup("case4_gpu_pdhg_screen")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            f"selected_python={root}/envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python",
            result.stdout,
        )
        self.assertIn("visible_devices=1", result.stdout)

    def test_explicit_interpreter_survives_environment_source(self):
        for case in ("case1_v3_barrier16_stage_a", "case4_gpu_pdhg_screen"):
            with self.subTest(case=case):
                result, _ = self.run_setup(case, "/mock/explicit/bin/python")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("selected_python=/mock/explicit/bin/python", result.stdout)

    def test_existing_solver_or_recovery_blocks_launch(self):
        for process in (
            "123 python scripts/run_cispo_2030_full_year.py",
            "124 python scripts/run_cispo_planning_sequence.py",
            "125 python scripts/recover_historical_stage_a.py",
            "126 bash scripts/run_historical_stage_a_recovery.sh",
        ):
            with self.subTest(process=process):
                result, _ = self.run_setup("case4_gpu_pdhg_screen", process=process)
                self.assertEqual(result.returncode, 96, result.stderr)
                self.assertIn("refuse pre-existing", result.stderr)
                self.assertNotIn("selected_python=", result.stdout)

    def test_unrelated_process_does_not_block_setup(self):
        result, _ = self.run_setup("case4_gpu_pdhg_screen", process="127 python other.py")
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(sys.platform == "linux", "Linux /proc integration test")
    def test_detached_dummy_job_records_and_closes_telemetry(self):
        import json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            (repo / "scripts").mkdir(parents=True)
            (repo / "scripts/run_cispo_2030_full_year.py").write_text(
                "import time\ntime.sleep(5)\nprint('DUMMY_JOB_ONLY')\n", encoding="utf-8")
            env_file = root / "env.sh"
            env_file.write_text(f'export CISPO_PYTHON="{sys.executable}"\n', encoding="utf-8")
            env = os.environ.copy()
            env.update(CISPO_SERVER_ROOT=str(root), CISPO_SERVER_ENV=str(env_file),
                       CISPO_REPO_ROOT=str(repo), CISPO_PYTHON=sys.executable,
                       CASE_ID="case1_v3_barrier16_stage_a", TAG="dummy_telemetry",
                       OUTPUT_ROOT=str(root / "output"), CONTROL_ROOT=str(root / "control"),
                       MINIMUM_AVAILABLE_GIB="0")
            command = '''git() { return 0; }
pgrep() { return 1; }
export -f git pgrep
exec bash "$1"
'''
            result = subprocess.run([bash_path(), "-c", command, "test", str(LAUNCHER)],
                                    env=env, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            control = root / "control"
            self.assertEqual((control / "return_code.txt").read_text().strip(), "0")
            self.assertEqual((control / "telemetry_return_code.txt").read_text().strip(), "0")
            rows = (control / "resource_pressure.jsonl").read_text().splitlines()
            self.assertGreaterEqual(len(rows), 2)
            self.assertIn("DUMMY_JOB_ONLY", (control / "stdout.log").read_text())
            summary = json.loads((control / "resource_pressure_summary.json").read_text())
            self.assertGreater(summary["job_rss_bytes_peak"], 0)


if __name__ == "__main__":
    unittest.main()
