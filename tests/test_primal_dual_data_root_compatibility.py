from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from cispo_model.primal_dual_checkpoint import (
    PrimalDualCheckpointError,
    validate_checkpoint_data_root_compatibility,
)


class PrimalDualDataRootCompatibilityTests(unittest.TestCase):
    @staticmethod
    def write_manifest(path: Path, resolved_paths: list[str]) -> None:
        fieldnames = ("kind", "resolved_path")
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for resolved_path in resolved_paths:
                writer.writerow(
                    {"kind": "data", "resolved_path": resolved_path}
                )
            writer.writerow(
                {
                    "kind": "solver_configuration",
                    "resolved_path": "/runtime/solver.json",
                }
            )

    def test_unused_optional_raw_root_difference_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_manifest = root / "source.csv"
            target_manifest = root / "target.csv"
            paths = ["/science/model_ready/input.csv"]
            self.write_manifest(source_manifest, paths)
            self.write_manifest(target_manifest, paths)
            report = validate_checkpoint_data_root_compatibility(
                {
                    "CISPO_DATA_ROOT": "/science/model_ready",
                    "CISPO_RAW_GRFR_ROOT": None,
                },
                {
                    "CISPO_DATA_ROOT": "/science/model_ready",
                    "CISPO_RAW_GRFR_ROOT": "/raw/grfr",
                },
                source_manifest,
                target_manifest,
            )
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["exact_match"])
        self.assertEqual(
            report["allowed_unused_optional_differences"],
            [
                {
                    "key": "CISPO_RAW_GRFR_ROOT",
                    "source": None,
                    "target": "/raw/grfr",
                    "source_scientific_manifest_path_count": 0,
                    "target_scientific_manifest_path_count": 0,
                }
            ],
        )

    def test_consumed_optional_raw_root_difference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_manifest = root / "source.csv"
            target_manifest = root / "target.csv"
            self.write_manifest(source_manifest, ["/science/input.csv"])
            self.write_manifest(target_manifest, ["/raw/grfr/input.csv"])
            with self.assertRaisesRegex(
                PrimalDualCheckpointError,
                "CISPO_RAW_GRFR_ROOT: source_usage=0, target_usage=1",
            ):
                validate_checkpoint_data_root_compatibility(
                    {"CISPO_RAW_GRFR_ROOT": None},
                    {"CISPO_RAW_GRFR_ROOT": "/raw/grfr"},
                    source_manifest,
                    target_manifest,
                )

    def test_unconsumed_nonallowlisted_root_difference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_manifest = root / "source.csv"
            target_manifest = root / "target.csv"
            self.write_manifest(source_manifest, ["/science/input.csv"])
            self.write_manifest(target_manifest, ["/science/input.csv"])
            with self.assertRaisesRegex(
                PrimalDualCheckpointError,
                "CISPO_DATA_ROOT: source_usage=0, target_usage=0",
            ):
                validate_checkpoint_data_root_compatibility(
                    {"CISPO_DATA_ROOT": "/old/unused"},
                    {"CISPO_DATA_ROOT": "/new/unused"},
                    source_manifest,
                    target_manifest,
                )

    def test_exact_root_identity_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_manifest = root / "source.csv"
            target_manifest = root / "target.csv"
            self.write_manifest(source_manifest, ["/science/input.csv"])
            self.write_manifest(target_manifest, ["/science/input.csv"])
            report = validate_checkpoint_data_root_compatibility(
                {"CISPO_DATA_ROOT": "/science"},
                {"CISPO_DATA_ROOT": "/science"},
                source_manifest,
                target_manifest,
            )
        self.assertTrue(report["exact_match"])
        self.assertEqual(report["allowed_unused_optional_differences"], [])


if __name__ == "__main__":
    unittest.main()
