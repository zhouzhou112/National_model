from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cispo_model.io_contract import validate_result_manifest
from cispo_model.result_summary import finalize_result_manifest


class ResultManifestTests(unittest.TestCase):
    def test_runtime_managed_files_are_excluded_and_scientific_files_are_stable(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            scientific = output_dir / "solution_qc.json"
            scientific.write_text('{"status":"PASS"}\n', encoding="utf-8")
            for name in (
                "runner_stdout.log", "runner_stderr.log", "run.pid",
                "stdout.log", "stderr.log", "run.stdout", "run.time",
            ):
                (output_dir / name).write_text("runtime\n", encoding="utf-8")
            config = SimpleNamespace(
                boundary_year=2025,
                planning_year=2030,
                path=Path("config/optimization_2030.json"),
            )

            manifest_path = finalize_result_manifest(output_dir, config)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            rows = {row["path"]: row for row in manifest["files"]}

            self.assertEqual(set(rows), {"solution_qc.json"})
            self.assertEqual(
                set(manifest["excluded_runtime_files"]),
                {
                    "runner_stdout.log", "runner_stderr.log", "run.pid",
                    "stdout.log", "stderr.log", "run.stdout", "run.time",
                },
            )
            self.assertEqual(rows["solution_qc.json"]["bytes"], scientific.stat().st_size)
            self.assertEqual(
                rows["solution_qc.json"]["sha256"],
                hashlib.sha256(scientific.read_bytes()).hexdigest(),
            )
            # Wrappers can emit their final report after the scientific
            # manifest has been finalized. Their later writes must not alter
            # acceptance of the checksummed scientific artifacts.
            with (output_dir / "stdout.log").open("a", encoding="utf-8") as handle:
                handle.write("final report\n")
            with (output_dir / "stderr.log").open("a", encoding="utf-8") as handle:
                handle.write("wrapper note\n")
            manifest_ok, manifest_failures = validate_result_manifest(output_dir)
            self.assertTrue(manifest_ok, manifest_failures)


if __name__ == "__main__":
    unittest.main()
