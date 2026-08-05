from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import gurobipy as gp
import numpy as np

from cispo_model.config import load_model_config
from cispo_model.diagnostics import solve_and_report


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
        auto_stable = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_16_auto_order_stable_basis_v3.json"
            )
        )
        self.assertEqual(auto_stable.raw["numerics"]["method"], 2)
        self.assertEqual(auto_stable.raw["numerics"]["threads"], 16)
        self.assertEqual(auto_stable.raw["numerics"]["presolve"], 2)
        self.assertNotIn("aggregate", auto_stable.raw["numerics"])
        self.assertEqual(auto_stable.raw["numerics"]["crossover"], 1)
        self.assertEqual(
            auto_stable.raw["numerics"]["crossover_basis"],
            1,
        )
        self.assertEqual(
            auto_stable.raw["numerics"]["dual_reductions"],
            1,
        )
        self.assertEqual(
            auto_stable.raw["numerics"]["inf_unbd_info"],
            0,
        )

        nonbasic = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_16_nonbasic_primal_dual_v1.json"
            )
        )
        self.assertEqual(nonbasic.raw["numerics"]["method"], 2)
        self.assertEqual(nonbasic.raw["numerics"]["crossover"], 0)
        self.assertEqual(nonbasic.raw["numerics"]["solution_target"], 1)
        self.assertEqual(
            nonbasic.raw["solver_profile"][
                "minimum_gurobi_major_version"
            ],
            13,
        )
        self.assertLessEqual(
            nonbasic.raw["numerics"]["barrier_convergence_tolerance"],
            1e-9,
        )
        nonbasic_long = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_16_nonbasic_primal_dual_long_v1.json"
            )
        )
        self.assertEqual(nonbasic_long.raw["numerics"]["crossover"], 0)
        self.assertEqual(nonbasic_long.raw["numerics"]["solution_target"], 1)
        self.assertEqual(nonbasic_long.raw["numerics"]["time_limit_seconds"], 86400)
        self.assertEqual(nonbasic_long.raw["numerics"]["soft_mem_limit_gb"], 80)
        deferred = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_16_deferred_crossover_v1.json"
            )
        )
        self.assertEqual(deferred.raw["numerics"]["method"], 2)
        self.assertEqual(deferred.raw["numerics"]["crossover"], 1)
        self.assertEqual(deferred.raw["numerics"]["crossover_basis"], 1)
        self.assertEqual(deferred.raw["numerics"]["lp_warm_start"], 2)

        stage_a = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_checkpoint_full_year_cloud_v1.json"
            )
        )
        self.assertEqual(stage_a.raw["numerics"]["method"], 2)
        self.assertEqual(stage_a.raw["numerics"]["threads"], 16)
        self.assertEqual(stage_a.raw["numerics"]["presolve"], 2)
        self.assertEqual(stage_a.raw["numerics"]["crossover"], 0)
        self.assertEqual(stage_a.raw["numerics"]["solution_target"], 1)
        self.assertEqual(
            stage_a.raw["numerics"]["barrier_convergence_tolerance"], 1e-9
        )
        self.assertEqual(stage_a.raw["numerics"]["aggregate"], 1)
        self.assertEqual(stage_a.raw["numerics"]["time_limit_seconds"], 604800)
        self.assertEqual(stage_a.raw["numerics"]["soft_mem_limit_gb"], 600)

        stage_a_v2 = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_checkpoint_full_year_cloud_v2.json"
            )
        )
        self.assertEqual(stage_a_v2.raw["numerics"]["method"], 2)
        self.assertEqual(stage_a_v2.raw["numerics"]["threads"], 16)
        self.assertEqual(stage_a_v2.raw["numerics"]["crossover"], 0)
        self.assertEqual(stage_a_v2.raw["numerics"]["solution_target"], 1)
        self.assertEqual(
            stage_a_v2.raw["numerics"]["barrier_convergence_tolerance"],
            1e-8,
        )
        self.assertEqual(
            stage_a_v2.raw["numerics"]["feasibility_tolerance"], 1e-6
        )
        self.assertEqual(
            stage_a_v2.raw["numerics"]["optimality_tolerance"], 1e-6
        )
        self.assertEqual(
            stage_a_v2.raw["numerics"]["markowitz_tolerance"], 0.01
        )
        self.assertIsNone(stage_a_v2.raw["numerics"]["time_limit_seconds"])
        self.assertEqual(stage_a_v2.raw["numerics"]["soft_mem_limit_gb"], 600)

        stage_b = load_model_config(
            solver_path=(
                profile_path.parent
                / "deferred_crossover2_full_year_cloud_v1.json"
            )
        )
        self.assertEqual(stage_b.raw["numerics"]["method"], 2)
        self.assertEqual(stage_b.raw["numerics"]["crossover"], 2)
        self.assertEqual(stage_b.raw["numerics"]["crossover_basis"], 1)
        self.assertEqual(stage_b.raw["numerics"]["lp_warm_start"], 2)
        self.assertEqual(stage_b.raw["numerics"]["solution_target"], 0)
        self.assertEqual(stage_b.raw["numerics"]["aggregate"], 1)
        self.assertEqual(stage_b.raw["numerics"]["time_limit_seconds"], 604800)
        self.assertEqual(stage_b.raw["numerics"]["soft_mem_limit_gb"], 600)

        stage_b_v2 = load_model_config(
            solver_path=(
                profile_path.parent
                / "deferred_crossover2_full_year_cloud_v2.json"
            )
        )
        self.assertEqual(stage_b_v2.raw["numerics"]["crossover"], 2)
        self.assertEqual(stage_b_v2.raw["numerics"]["crossover_basis"], 1)
        self.assertEqual(stage_b_v2.raw["numerics"]["lp_warm_start"], 2)
        self.assertEqual(
            stage_b_v2.raw["numerics"]["feasibility_tolerance"], 1e-6
        )
        self.assertEqual(
            stage_b_v2.raw["numerics"]["optimality_tolerance"], 1e-6
        )
        self.assertIsNone(stage_b_v2.raw["numerics"]["time_limit_seconds"])

        tuning_profiles = sorted(profile_path.parent.glob("tuning_barrier_nonbasic_*.json"))
        self.assertEqual(len(tuning_profiles), 8)
        for tuning_profile in tuning_profiles:
            with self.subTest(tuning_profile=tuning_profile.name):
                candidate = load_model_config(solver_path=tuning_profile)
                self.assertEqual(candidate.raw["scenario"], base.raw["scenario"])
                self.assertEqual(candidate.raw["numerics"]["method"], 2)
                self.assertEqual(candidate.raw["numerics"]["crossover"], 0)
                self.assertEqual(candidate.raw["numerics"]["solution_target"], 1)
                self.assertLessEqual(
                    candidate.raw["numerics"]["barrier_convergence_tolerance"],
                    1e-9,
                )
                self.assertEqual(
                    candidate.raw["solver_profile"][
                        "minimum_gurobi_major_version"
                    ],
                    13,
                )

        tuning2_profiles = sorted(profile_path.parent.glob("tuning2_*.json"))
        self.assertEqual(len(tuning2_profiles), 12)
        for tuning_profile in tuning2_profiles:
            with self.subTest(tuning2_profile=tuning_profile.name):
                candidate = load_model_config(solver_path=tuning_profile)
                self.assertEqual(candidate.raw["scenario"], base.raw["scenario"])
                self.assertEqual(
                    candidate.raw["solver_profile"][
                        "minimum_gurobi_major_version"
                    ],
                    13,
                )
                if "dual_simplex" in tuning_profile.name:
                    self.assertEqual(candidate.raw["numerics"]["method"], 1)
                    self.assertEqual(candidate.raw["numerics"]["solution_target"], 0)
                else:
                    self.assertEqual(candidate.raw["numerics"]["method"], 2)
                    self.assertEqual(candidate.raw["numerics"]["crossover"], 0)
                    self.assertEqual(candidate.raw["numerics"]["solution_target"], 1)

        tuning3_profiles = sorted(profile_path.parent.glob("tuning3_*.json"))
        self.assertEqual(len(tuning3_profiles), 3)
        for crossover, tuning_profile in zip((1, 2, 4), tuning3_profiles):
            with self.subTest(tuning3_profile=tuning_profile.name):
                candidate = load_model_config(solver_path=tuning_profile)
                self.assertEqual(candidate.raw["scenario"], base.raw["scenario"])
                self.assertEqual(candidate.raw["numerics"]["method"], 2)
                self.assertEqual(candidate.raw["numerics"]["crossover"], crossover)
                self.assertEqual(candidate.raw["numerics"]["crossover_basis"], 1)
                self.assertEqual(
                    candidate.raw["solver_profile"][
                        "minimum_gurobi_major_version"
                    ],
                    13,
                )

        production_crossover = load_model_config(
            solver_path=(
                profile_path.parent
                / "barrier_16_crossover2_stable_basis_long_v1.json"
            )
        )
        self.assertEqual(production_crossover.raw["numerics"]["method"], 2)
        self.assertEqual(production_crossover.raw["numerics"]["threads"], 16)
        self.assertEqual(production_crossover.raw["numerics"]["crossover"], 2)
        self.assertEqual(
            production_crossover.raw["numerics"]["crossover_basis"], 1
        )
        self.assertEqual(
            production_crossover.raw["numerics"]["time_limit_seconds"],
            86400,
        )
        self.assertEqual(
            production_crossover.raw["numerics"]["soft_mem_limit_gb"],
            80,
        )

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

    def test_solver_profile_rejects_invalid_aggregate(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid_aggregate.json"
            path.write_text(
                json.dumps(
                    {
                        "solver_profile_version": "v1",
                        "profile_id": "invalid_aggregate",
                        "numerics": {"aggregate": 3},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "numerics.aggregate is outside",
            ):
                load_model_config(solver_path=path)

    def test_solver_profile_rejects_invalid_solution_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "invalid_solution_target.json"
            path.write_text(
                json.dumps(
                    {
                        "solver_profile_version": "v1",
                        "profile_id": "invalid_solution_target",
                        "numerics": {"solution_target": 2},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "numerics.solution_target is outside",
            ):
                load_model_config(solver_path=path)

    def test_nonbasic_primal_dual_contract_solves_without_basis(self):
        root = Path(__file__).resolve().parents[1]
        config = load_model_config(
            solver_path=(
                root
                / "config"
                / "solver_profiles"
                / "barrier_16_nonbasic_primal_dual_v1.json"
            )
        )
        model = gp.Model("nonbasic_primal_dual_contract")
        x = model.addMVar(2, lb=0.0, name="x")
        constraints = model.addMConstr(
            np.asarray([[1.0, 1.0]]),
            x,
            ">",
            np.asarray([1.0]),
            name="demand",
        )
        model.setObjective(x[0] + 2.0 * x[1], gp.GRB.MINIMIZE)
        temporary = tempfile.TemporaryDirectory()
        try:
            if gp.gurobi.version()[0] < 13:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "requires Gurobi >= 13",
                ):
                    solve_and_report(
                        model,
                        config,
                        Path(temporary.name),
                        compute_iis=False,
                    )
                return
            report = solve_and_report(
                model,
                config,
                Path(temporary.name),
                compute_iis=False,
            )
            self.assertEqual(report["status"], "OPTIMAL")
            self.assertEqual(
                report["solution_contract"]["mode"],
                "OPTIMAL_PRIMAL_DUAL_NONBASIC",
            )
            self.assertFalse(report["solution_contract"]["basis_required"])
            self.assertEqual(
                report["solution_contract"]["acceptance_status"],
                "PASS",
            )
            self.assertEqual(
                report["solution_contract"]["dual_attribute"],
                "BarPi",
            )
            self.assertEqual(
                set(report["solution_quality_locations"]),
                {
                    "maximum_bound_violation",
                    "maximum_constraint_violation",
                    "maximum_dual_violation",
                    "maximum_complementarity_violation",
                },
            )
            self.assertTrue(float(constraints.BarPi[0]) > 0.0)
        finally:
            model.dispose()
            temporary.cleanup()

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
