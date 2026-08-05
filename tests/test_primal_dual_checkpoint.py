from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import gurobipy as gp

from cispo_model.config import load_model_config
from cispo_model.planning_state import (
    DIAGNOSTIC_STATE_USE,
    PlanningState,
    STATE_COLUMNS,
    write_planning_state,
)
from cispo_model.primal_dual_checkpoint import (
    CHECKPOINT_DIRECTORY,
    ENGINEERING_CHECKPOINT_STATUS,
    PrimalDualCheckpointError,
    apply_primal_dual_crossover_start,
    export_barrier_primal_dual_checkpoint,
    prepare_primal_dual_crossover,
    validate_barrier_primal_dual_checkpoint,
)
from cispo_model.result_summary import finalize_result_manifest
from scripts.run_cispo_2030_full_year import diagnostic_memory_requirement_gb


class FakeModel:
    def __init__(self) -> None:
        self.IsMIP = 0
        self.NumVars = 3
        self.NumConstrs = 2
        self.NumNZs = 4
        self.Fingerprint = 123
        self.Params = SimpleNamespace(LPWarmStart=-1)
        self.assigned: dict[str, np.ndarray] = {}

    def update(self) -> None:
        return None

    def getAttr(self, name: str, objects=None):
        if name == "BarX":
            return [1.0, 2.0, 3.0]
        if name == "BarPi":
            return [-4.0, 5.0]
        if name == "VarName":
            return list(objects)
        if name == "ConstrName":
            return list(objects)
        if name == "Sense":
            return ["=" for _ in objects]
        raise AttributeError(name)

    def getVars(self):
        return ["v0", "v1", "v2"]

    def getConstrs(self):
        return ["c0", "c1"]

    def setAttr(self, name: str, objects, values) -> None:
        self.assigned[name] = np.asarray(values, dtype=float).copy()


class PrimalDualCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_model_config(
            solver_path=(
                Path(__file__).resolve().parents[1]
                / "config"
                / "solver_profiles"
                / "barrier_16_nonbasic_primal_dual_v1.json"
            )
        )

    def test_diagnostic_memory_uses_next_validated_tier(self) -> None:
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 744), 8.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 745), 32.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 4344), 32.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 4345), 96.0)

    def test_export_prepare_and_apply_exact_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            identity = {
                "baseline_contract": {"id": "baseline"},
                "analysis_case": {"id": "analysis"},
                "scientific_case": {"id": "analysis"},
                "implementation_bundle": {"sha": "code"},
                "data_roots": {"root": "data"},
                "lp_model": {
                    "variables": 3,
                    "constraints": 2,
                    "nonzeros": 4,
                    "gurobi_fingerprint": 123,
                },
            }
            for output in (source, target):
                (output / "run_identity.json").write_text(
                    json.dumps(identity), encoding="utf-8"
                )
                (output / "input_manifest.csv").write_text(
                    "same,input,manifest\n", encoding="utf-8"
                )
                (output / "run_environment.json").write_text(
                    json.dumps(
                        {
                            "packages": {"gurobipy": "13.0.2"},
                            "planning_state_in": None,
                        }
                    ),
                    encoding="utf-8",
                )
            (source / "run_scope.json").write_text(
                json.dumps({"result_use": "TEST_ONLY_TRUNCATED_HORIZON"}),
                encoding="utf-8",
            )
            solve_report = {
                "status": "OPTIMAL",
                "status_code": 2,
                "planning_year": 2030,
                "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
                "runtime_seconds": 1.0,
                "iteration_counts": {"barrier": 4},
                "solution_contract": {
                    "mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                    "acceptance_status": "PASS",
                    "barrier_status_code": 2,
                },
                "solution_quality": {"maximum_constraint_violation": 0.0},
            }
            qc = {"status": "PASS", "hard_checks": {"balance": True}}
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ):
                metadata = export_barrier_primal_dual_checkpoint(
                    FakeModel(),
                    self.config,
                    source,
                    solve_report=solve_report,
                    optimization_hours=744,
                    optimization_start_hour=3960,
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                    solution_qc=qc,
                    accepted_primary=True,
                )
            self.assertTrue(metadata["scientifically_accepted"])
            np.testing.assert_allclose(
                np.load(source / CHECKPOINT_DIRECTORY / "primal_barx.npy"),
                [1.0, 2.0, 3.0],
            )
            (source / "solve_report.json").write_text(
                json.dumps(solve_report), encoding="utf-8"
            )
            (source / "solution_qc.json").write_text(
                json.dumps(qc), encoding="utf-8"
            )
            (source / "result_manifest.json").write_text("{}", encoding="utf-8")
            target_model = FakeModel()
            with (
                patch(
                    "cispo_model.primal_dual_checkpoint.validate_result_manifest",
                    return_value=(True, []),
                ),
                patch(
                    "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                    return_value=(True, []),
                ),
            ):
                prepared = prepare_primal_dual_crossover(
                    source,
                    target,
                    target_model,
                    self.config,
                    optimization_hours=744,
                    optimization_start_hour=3960,
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                )
                checkpoint_valid, checkpoint_failures = (
                    validate_barrier_primal_dual_checkpoint(
                        source,
                        require_result_manifest=True,
                    )
                )
            self.assertTrue(checkpoint_valid, checkpoint_failures)
            apply_primal_dual_crossover_start(target_model, prepared)
            np.testing.assert_allclose(target_model.assigned["PStart"], [1, 2, 3])
            np.testing.assert_allclose(target_model.assigned["DStart"], [-4, 5])
            self.assertEqual(target_model.Params.LPWarmStart, 2)

            new_cohorts = pd.DataFrame(
                [
                    {
                        "asset_class": "vre",
                        "asset_id": "site-1",
                        "province_code": 11,
                        "technology": "onwind",
                        "build_year": 2030,
                        "retire_year": 2055,
                        "capacity_delta": 1.25,
                        "unit": "GW",
                        "action": "new_build",
                    }
                ],
                columns=STATE_COLUMNS,
            )
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ):
                state_dir = write_planning_state(
                    source,
                    config=self.config,
                    previous_state=PlanningState.empty(2025),
                    new_cohorts=new_cohorts,
                    source_solution_qc="solution_qc.json",
                    state_use=DIAGNOSTIC_STATE_USE,
                )
            state_metadata = json.loads(
                (state_dir / "state_metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                state_metadata["source_capacity_state_policy"],
                "ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE",
            )
            self.assertFalse(state_metadata["posthoc_crossover_required_for_state"])
            self.assertTrue(
                state_metadata["source_barrier_checkpoint_manifest_sha256"]
            )
            finalize_result_manifest(source, self.config)
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ):
                loaded = PlanningState.load(
                    state_dir,
                    expected_boundary_year=2030,
                    allow_test_only=True,
                )
            self.assertAlmostEqual(float(loaded.cohorts.capacity_delta.sum()), 1.25)

    def test_engineering_checkpoint_requires_explicit_stage_b_allow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            identity = {
                "baseline_contract": {"id": "baseline"},
                "analysis_case": {"id": "analysis"},
                "scientific_case": {"id": "analysis"},
                "implementation_bundle": {"sha": "code"},
                "data_roots": {"root": "data"},
                "lp_model": {
                    "variables": 3,
                    "constraints": 2,
                    "nonzeros": 4,
                    "gurobi_fingerprint": 123,
                },
            }
            for output in (source, target):
                (output / "run_identity.json").write_text(
                    json.dumps(identity), encoding="utf-8"
                )
                (output / "input_manifest.csv").write_text(
                    "same,input,manifest\n", encoding="utf-8"
                )
                (output / "run_environment.json").write_text(
                    json.dumps(
                        {
                            "packages": {"gurobipy": "13.0.2"},
                            "planning_state_in": None,
                        }
                    ),
                    encoding="utf-8",
                )
            (source / "run_scope.json").write_text(
                json.dumps({"result_use": "SCIENTIFIC_PRODUCTION"}),
                encoding="utf-8",
            )
            solve_report = {
                "status": "SUBOPTIMAL",
                "status_code": 13,
                "runtime_seconds": 10.0,
                "iteration_counts": {"barrier": 100},
                "solver_parameters": {
                    "method": 2,
                    "crossover": 0,
                    "solution_target": 1,
                },
                "solution_contract": {
                    "mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                    "acceptance_status": "PENDING_OR_NO_SOLUTION",
                    "barrier_status_code": 2,
                },
                "solution_quality": {"maximum_constraint_violation": 1e-6},
            }
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ):
                metadata = export_barrier_primal_dual_checkpoint(
                    FakeModel(),
                    self.config,
                    source,
                    solve_report=solve_report,
                    optimization_hours=8760,
                    optimization_start_hour=0,
                    result_use="SCIENTIFIC_PRODUCTION",
                    solution_qc=None,
                    accepted_primary=False,
                    engineering_only=True,
                )
            self.assertEqual(
                metadata["checkpoint_status"], ENGINEERING_CHECKPOINT_STATUS
            )
            self.assertFalse(metadata["scientifically_accepted"])
            self.assertTrue(metadata["deferred_crossover_eligible"])
            (source / "solve_report.json").write_text(
                json.dumps(solve_report), encoding="utf-8"
            )
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ):
                valid, failures = validate_barrier_primal_dual_checkpoint(
                    source,
                    require_result_manifest=False,
                    allow_engineering=True,
                )
                self.assertTrue(valid, failures)
                with self.assertRaisesRegex(
                    PrimalDualCheckpointError, "explicit acknowledgement"
                ):
                    prepare_primal_dual_crossover(
                        source,
                        target,
                        FakeModel(),
                        self.config,
                        optimization_hours=8760,
                        optimization_start_hour=0,
                        result_use="SCIENTIFIC_PRODUCTION",
                    )
                prepared = prepare_primal_dual_crossover(
                    source,
                    target,
                    FakeModel(),
                    self.config,
                    optimization_hours=8760,
                    optimization_start_hour=0,
                    result_use="SCIENTIFIC_PRODUCTION",
                    allow_engineering_checkpoint=True,
                )
            self.assertTrue(prepared["engineering_checkpoint_explicitly_allowed"])
            self.assertIsNone(prepared["source_result_manifest_sha256"])

    def test_real_gurobi_accepts_memmapped_pstart_and_dstart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = gp.Model("barrier_source")
            x = source.addMVar(3, lb=0.0, name="x")
            source.addMConstr(
                np.asarray([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]]),
                x,
                ">",
                np.asarray([1.0, 0.5]),
                name="demand",
            )
            source.setObjective(x[0] + 2.0 * x[1] + 3.0 * x[2])
            source.Params.Method = 2
            source.Params.Crossover = 0
            source.Params.OutputFlag = 0
            source.optimize()
            self.assertEqual(source.Status, gp.GRB.OPTIMAL)
            primal_path = root / "primal.npy"
            dual_path = root / "dual.npy"
            np.save(primal_path, np.asarray(source.getAttr("BarX"), dtype="<f8"))
            np.save(dual_path, np.asarray(source.getAttr("BarPi"), dtype="<f8"))

            target = gp.Model("deferred_crossover")
            y = target.addMVar(3, lb=0.0, name="x")
            target.addMConstr(
                np.asarray([[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]]),
                y,
                ">",
                np.asarray([1.0, 0.5]),
                name="demand",
            )
            target.setObjective(y[0] + 2.0 * y[1] + 3.0 * y[2])
            target.Params.Method = 2
            target.Params.Crossover = 1
            target.Params.OutputFlag = 0
            apply_primal_dual_crossover_start(
                target,
                {
                    "primal_path": str(primal_path),
                    "dual_path": str(dual_path),
                    "lp_warm_start": 2,
                },
            )
            target.optimize()
            self.assertEqual(target.Status, gp.GRB.OPTIMAL)
            self.assertEqual(target.Params.LPWarmStart, 2)
            source.dispose()
            target.dispose()


if __name__ == "__main__":
    unittest.main()
