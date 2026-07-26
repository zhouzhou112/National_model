from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cispo_model.config import load_model_config


class SolverProfileTests(unittest.TestCase):
    def test_solver_profile_changes_only_numerics_and_is_traced(self):
        base = load_model_config()
        profile_path = (
            Path(__file__).resolve().parents[1]
            / "config"
            / "solver_profiles"
            / "barrier_16_sparse_amd_v1.json"
        )
        profiled = load_model_config(solver_path=profile_path)
        self.assertEqual(base.raw["scenario"], profiled.raw["scenario"])
        self.assertEqual(profiled.raw["numerics"]["threads"], 16)
        self.assertEqual(profiled.raw["numerics"]["pre_sparsify"], 1)
        self.assertEqual(profiled.raw["numerics"]["bar_order"], 0)
        self.assertEqual(profiled.solver_path, profile_path.resolve())

        limited = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_32_limited_presolve_fast_basis_v1.json"
            )
        )
        self.assertEqual(limited.raw["numerics"]["pre_passes"], 3)
        self.assertEqual(limited.raw["numerics"]["crossover_basis"], 0)
        forced_dual = load_model_config(
            solver_path=profile_path.parent / "barrier_32_force_dual_v1.json"
        )
        self.assertEqual(forced_dual.raw["numerics"]["pre_dual"], 1)

    def test_solver_profile_rejects_scientific_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text(
                json.dumps(
                    {
                        "solver_profile_version": "v1",
                        "profile_id": "invalid",
                        "numerics": {"capacity_margin_fraction": 0.9},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError, "Unsupported solver-profile numerics keys"
            ):
                load_model_config(solver_path=path)


if __name__ == "__main__":
    unittest.main()
