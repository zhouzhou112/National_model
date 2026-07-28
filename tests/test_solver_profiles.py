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

        auto_order = load_model_config(
            solver_path=profile_path.parent / "barrier_16_auto_order_v1.json"
        )
        self.assertEqual(auto_order.raw["numerics"]["threads"], 16)
        self.assertNotIn("bar_order", auto_order.raw["numerics"])
        self.assertNotIn("pre_sparsify", auto_order.raw["numerics"])

        production = load_model_config(
            solver_path=profile_path.parent / "barrier_16_auto_order_v2.json"
        )
        self.assertEqual(production.raw["numerics"]["dual_reductions"], 1)
        self.assertEqual(production.raw["numerics"]["inf_unbd_info"], 0)
        crossover_profiles = {
            "barrier_16_crossover_2_v1.json": (2, None),
            "barrier_16_crossover_3_v1.json": (3, None),
            "barrier_16_crossover_4_v1.json": (4, None),
            "barrier_16_crossover_fast_basis_v1.json": (1, 0),
            "barrier_16_crossover_stable_basis_v1.json": (1, 1),
        }
        for filename, (strategy, basis_strategy) in crossover_profiles.items():
            with self.subTest(filename=filename):
                candidate = load_model_config(
                    solver_path=profile_path.parent / filename
                )
                self.assertEqual(candidate.raw["scenario"], base.raw["scenario"])
                self.assertEqual(candidate.raw["numerics"]["method"], 2)
                self.assertEqual(candidate.raw["numerics"]["threads"], 16)
                self.assertEqual(candidate.raw["numerics"]["presolve"], 2)
                self.assertEqual(candidate.raw["numerics"]["crossover"], strategy)
                self.assertEqual(candidate.raw["numerics"]["dual_reductions"], 1)
                self.assertEqual(candidate.raw["numerics"]["inf_unbd_info"], 0)
                if basis_strategy is None:
                    self.assertNotIn("crossover_basis", candidate.raw["numerics"])
                else:
                    self.assertEqual(
                        candidate.raw["numerics"]["crossover_basis"],
                        basis_strategy,
                    )
        sparsified = load_model_config(
            solver_path=profile_path.parent / "barrier_16_presparsify_lp_v1.json"
        )
        self.assertEqual(sparsified.raw["numerics"]["pre_sparsify"], 2)
        self.assertEqual(
            load_model_config(
                solver_path=profile_path.parent / "barrier_16_predual1_v1.json"
            ).raw["numerics"]["pre_dual"],
            1,
        )
        self.assertEqual(
            load_model_config(
                solver_path=profile_path.parent / "barrier_16_predual2_v1.json"
            ).raw["numerics"]["pre_dual"],
            2,
        )
        diagnostic = load_model_config(
            solver_path=(
                profile_path.parent / "barrier_16_infeasibility_diagnostic_v1.json"
            )
        )
        self.assertEqual(diagnostic.raw["numerics"]["dual_reductions"], 0)
        self.assertEqual(diagnostic.raw["numerics"]["inf_unbd_info"], 1)

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
        pdhg = load_model_config(
            solver_path=profile_path.parent / "pdhg_cpu_32_v1.json"
        )
        self.assertEqual(pdhg.raw["numerics"]["method"], 6)
        self.assertEqual(pdhg.raw["numerics"]["pdhg_gpu"], 0)

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

    def test_solver_profile_rejects_invalid_crossover_basis(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid_crossover_basis.json"
            path.write_text(
                json.dumps(
                    {
                        "solver_profile_version": "v1",
                        "profile_id": "invalid_crossover_basis",
                        "numerics": {"crossover_basis": 2},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError, "crossover_basis is outside"
            ):
                load_model_config(solver_path=path)

    def test_formulation_profile_is_structural_only_and_traced(self):
        root = Path(__file__).resolve().parents[1]
        profile_path = (
            root
            / "config"
            / "formulation_profiles"
            / "annual_emissions_province_hierarchy_v1.json"
        )
        base = load_model_config()
        profiled = load_model_config(formulation_path=profile_path)
        self.assertEqual(base.raw["scenario"], profiled.raw["scenario"])
        self.assertEqual(base.raw["numerics"], profiled.raw["numerics"])
        self.assertEqual(
            profiled.raw["formulation"]["annual_emissions_accounting"],
            "province_hierarchical_v2",
        )
        self.assertEqual(profiled.formulation_path, profile_path.resolve())

    def test_formulation_profile_rejects_nonstructural_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid_formulation.json"
            path.write_text(
                json.dumps(
                    {
                        "formulation_profile_version": "v1",
                        "profile_id": "invalid",
                        "formulation": {"carbon_limit": 0.0},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError, "Unsupported formulation-profile keys"
            ):
                load_model_config(formulation_path=path)


if __name__ == "__main__":
    unittest.main()
