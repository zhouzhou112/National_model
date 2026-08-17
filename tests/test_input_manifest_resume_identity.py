from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from cispo_model.io_contract import input_manifest_scientific_resume_identity


COLUMNS = (
    "kind",
    "logical_path",
    "resolved_path",
    "required",
    "exists",
    "size_bytes",
    "sha256",
    "integrity_method",
    "role",
)


def write_manifest(
    path: Path,
    *,
    solver_sha: str,
    scientific_sha: str = "scientific-sha",
) -> None:
    rows = [
        {
            "kind": "configuration",
            "logical_path": "config/optimization_2030.json",
            "resolved_path": "/repo/config/optimization_2030.json",
            "required": "True",
            "exists": "True",
            "size_bytes": "100",
            "sha256": scientific_sha,
            "integrity_method": "sha256_file",
            "role": "",
        },
        {
            "kind": "solver_configuration",
            "logical_path": f"config/solver/{solver_sha}.json",
            "resolved_path": f"/repo/config/solver/{solver_sha}.json",
            "required": "True",
            "exists": "True",
            "size_bytes": "10",
            "sha256": solver_sha,
            "integrity_method": "sha256_file",
            "role": "",
        },
    ]
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)


class InputManifestResumeIdentityTests(unittest.TestCase):
    def test_only_solver_configuration_may_differ(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage_a = root / "stage_a.csv"
            stage_b = root / "stage_b.csv"
            write_manifest(stage_a, solver_sha="barrier")
            write_manifest(stage_b, solver_sha="crossover2")
            source = input_manifest_scientific_resume_identity(stage_a)
            target = input_manifest_scientific_resume_identity(stage_b)
            self.assertEqual(source["sha256"], target["sha256"])
            self.assertEqual(source["row_count"], 1)
            self.assertNotEqual(
                source["full_manifest_sha256"], target["full_manifest_sha256"]
            )
            self.assertEqual(
                source["excluded_runtime_kinds"], ["solver_configuration"]
            )

    def test_scientific_input_change_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage_a = root / "stage_a.csv"
            changed = root / "changed.csv"
            write_manifest(stage_a, solver_sha="barrier")
            write_manifest(
                changed,
                solver_sha="crossover2",
                scientific_sha="different-scientific-input",
            )
            self.assertNotEqual(
                input_manifest_scientific_resume_identity(stage_a)["sha256"],
                input_manifest_scientific_resume_identity(changed)["sha256"],
            )

    def test_exactly_one_solver_configuration_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing_solver.csv"
            pd.DataFrame(
                [
                    {
                        "kind": "configuration",
                        "logical_path": "config.json",
                        "resolved_path": "/repo/config.json",
                        "required": "True",
                        "exists": "True",
                        "size_bytes": "1",
                        "sha256": "x",
                        "integrity_method": "sha256_file",
                        "role": "",
                    }
                ],
                columns=COLUMNS,
            ).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "exactly one"):
                input_manifest_scientific_resume_identity(path)


if __name__ == "__main__":
    unittest.main()
