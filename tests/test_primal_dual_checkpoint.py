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
from cispo_model.io_contract import sha256_file
from cispo_model.planning_state import (
    DIAGNOSTIC_STATE_USE,
    PlanningState,
    STATE_COLUMNS,
    write_planning_state,
)
from cispo_model.primal_dual_checkpoint import (
    CHECKPOINT_DIRECTORY,
    CHECKPOINT_MANIFEST,
    ENGINEERING_CHECKPOINT_STATUS,
    PENDING_QC_CHECKPOINT_STATUS,
    PrimalDualCheckpointError,
    RECOVERY_CHECKPOINT_STATUS,
    _current_solution_comparison_failures,
    apply_primal_dual_crossover_start,
    export_barrier_primal_dual_checkpoint,
    promote_pending_qc_checkpoint,
    prepare_primal_dual_crossover,
    validate_barrier_primal_dual_checkpoint,
)
from cispo_model.result_summary import finalize_result_manifest
from scripts.run_cispo_2030_full_year import diagnostic_memory_requirement_gb


class FakeModel:
    def __init__(
        self,
        *,
        current_primal: list[float] | None = None,
        current_dual: list[float] | None = None,
    ) -> None:
        self.IsMIP = 0
        self.NumVars = 3
        self.NumConstrs = 2
        self.NumNZs = 4
        self.Fingerprint = 123
        self.Params = SimpleNamespace(LPWarmStart=-1)
        self.assigned: dict[str, np.ndarray] = {}
        self.current_primal = current_primal or [1.0, 2.0, 3.0]
        self.current_dual = current_dual or [-4.0, 5.0]

    def update(self) -> None:
        return None

    def getAttr(self, name: str, objects=None):
        if name == "BarX":
            return [1.0, 2.0, 3.0]
        if name == "X":
            return self.current_primal
        if name == "BarPi":
            return [-4.0, 5.0]
        if name == "Pi":
            return self.current_dual
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

    @staticmethod
    def _write_input_manifest(
        output: Path,
        *,
        solver_logical_path: str = "solver/barrier.json",
        solver_sha256: str = "solver-barrier",
    ) -> None:
        rows = [
            {
                "kind": "configuration",
                "logical_path": "config/optimization_2030.json",
                "resolved_path": "/same/config/optimization_2030.json",
                "required": "True",
                "exists": "True",
                "size_bytes": "100",
                "sha256": "scientific-config",
                "integrity_method": "sha256_file",
                "role": "",
            },
            {
                "kind": "solver_configuration",
                "logical_path": solver_logical_path,
                "resolved_path": f"/runtime/{solver_logical_path}",
                "required": "True",
                "exists": "True",
                "size_bytes": "10",
                "sha256": solver_sha256,
                "integrity_method": "sha256_file",
                "role": "",
            },
        ]
        pd.DataFrame(rows).to_csv(output / "input_manifest.csv", index=False)

    def test_diagnostic_memory_uses_next_validated_tier(self) -> None:
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 744), 8.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 745), 32.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 4344), 32.0)
        self.assertEqual(diagnostic_memory_requirement_gb(self.config, 4345), 96.0)

    def test_current_solution_identity_evidence_binds_attribute_and_count(self):
        vectors = {
            "primal": {
                "entries": 3,
                "current_solution_comparison": {
                    "status": "COLLECTED",
                    "current_attribute": "X",
                    "maximum_absolute_difference": 0.0,
                    "entries_compared": 3,
                },
            },
            "dual": {
                "entries": 2,
                "current_solution_comparison": {
                    "status": "COLLECTED",
                    "current_attribute": "Pi",
                    "maximum_absolute_difference": 0.0,
                    "entries_compared": 2,
                },
            },
        }
        expected = {"primal": 3, "dual": 2}
        self.assertEqual(
            _current_solution_comparison_failures(
                vectors, expected_entries=expected
            ),
            [],
        )
        for role, field, value in (
            ("primal", "current_attribute", "BarX"),
            ("dual", "entries_compared", 0),
        ):
            changed = json.loads(json.dumps(vectors))
            changed[role]["current_solution_comparison"][field] = value
            with self.subTest(role=role, field=field):
                self.assertTrue(
                    _current_solution_comparison_failures(
                        changed, expected_entries=expected
                    )
                )

    def test_pending_checkpoint_rejects_barrier_vector_identity_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
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
            (source / "run_identity.json").write_text(
                json.dumps(identity), encoding="utf-8"
            )
            (source / "run_environment.json").write_text(
                json.dumps({"packages": {"gurobipy": "13.0.2"}}),
                encoding="utf-8",
            )
            (source / "run_scope.json").write_text(
                json.dumps({"result_use": "TEST_ONLY_TRUNCATED_HORIZON"}),
                encoding="utf-8",
            )
            self._write_input_manifest(source)
            solve_report = {
                "status": "OPTIMAL",
                "solution_contract": {
                    "mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                    "acceptance_status": "PASS",
                    "barrier_status_code": 2,
                    "maximum_primal_quality_limit": 1e-5,
                    "maximum_dual_quality_limit": 1e-5,
                },
            }
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_input_manifest",
                return_value=(True, []),
            ), self.assertRaisesRegex(
                PrimalDualCheckpointError,
                "vectors differ",
            ):
                export_barrier_primal_dual_checkpoint(
                    # The 1e-6 drift is smaller than the 1e-5 solver-quality
                    # contract, but still cannot transfer X quality to BarX.
                    FakeModel(current_primal=[1.0, 2.0, 3.000001]),
                    self.config,
                    source,
                    solve_report=solve_report,
                    optimization_hours=744,
                    optimization_start_hour=3960,
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                    solution_qc=None,
                    accepted_primary=False,
                    pending_qc=True,
                )

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
                (output / "run_environment.json").write_text(
                    json.dumps(
                        {
                            "packages": {"gurobipy": "13.0.2"},
                            "planning_state_in": None,
                        }
                    ),
                    encoding="utf-8",
                )
            self._write_input_manifest(source)
            self._write_input_manifest(
                target,
                solver_logical_path="solver/crossover2.json",
                solver_sha256="solver-crossover2",
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
                "objective_value_million_cny": 7.5,
                "solution_contract": {
                    "mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                    "acceptance_status": "PASS",
                    "barrier_status_code": 2,
                    "maximum_primal_quality_limit": 1e-5,
                    "maximum_dual_quality_limit": 1e-5,
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
                    solution_qc=None,
                    accepted_primary=False,
                    pending_qc=True,
                )
            self.assertEqual(
                metadata["checkpoint_status"], PENDING_QC_CHECKPOINT_STATUS
            )
            self.assertFalse(metadata["scientifically_accepted"])
            np.testing.assert_allclose(
                np.load(source / CHECKPOINT_DIRECTORY / "primal_barx.npy"),
                [1.0, 2.0, 3.0],
            )
            (source / "solve_report.json").write_text(
                json.dumps(solve_report), encoding="utf-8"
            )
            (source / "solution_qc.json").write_text(
                json.dumps(
                    {"status": "FAIL", "hard_checks": {"balance": False}}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                PrimalDualCheckpointError,
                "solver-contract PASS and every original-unit QC",
            ):
                promote_pending_qc_checkpoint(
                    source,
                    solve_report=solve_report,
                    solution_qc=qc,
                )
            (source / "solution_qc.json").write_text(
                json.dumps(qc), encoding="utf-8"
            )
            different_report = json.loads(json.dumps(solve_report))
            different_report["objective_value_million_cny"] = 8.5
            with self.assertRaisesRegex(
                PrimalDualCheckpointError,
                "solver evidence differs",
            ):
                promote_pending_qc_checkpoint(
                    source,
                    solve_report=different_report,
                    solution_qc=qc,
                )
            metadata = promote_pending_qc_checkpoint(
                source,
                solve_report=solve_report,
                solution_qc=qc,
            )
            self.assertTrue(metadata["scientifically_accepted"])
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
            different_report["objective_value_million_cny"] = 8.5
            (source / "solve_report.json").write_text(
                json.dumps(different_report), encoding="utf-8"
            )
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
                tampered_valid, tampered_failures = (
                    validate_barrier_primal_dual_checkpoint(
                        source,
                        require_result_manifest=True,
                    )
                )
            self.assertFalse(tampered_valid)
            self.assertIn(
                "solver_evidence_mismatch:objective_value_million_cny",
                tampered_failures,
            )
            (source / "solve_report.json").write_text(
                json.dumps(solve_report), encoding="utf-8"
            )
            self.assertTrue(prepared["implementation_bundle_matches"])
            self.assertNotEqual(
                prepared["scientific_input_manifest_identity"][
                    "source_full_manifest_sha256"
                ],
                prepared["scientific_input_manifest_identity"][
                    "target_full_manifest_sha256"
                ],
            )
            apply_primal_dual_crossover_start(target_model, prepared)
            np.testing.assert_allclose(target_model.assigned["PStart"], [1, 2, 3])
            np.testing.assert_allclose(target_model.assigned["DStart"], [-4, 5])
            self.assertEqual(target_model.Params.LPWarmStart, 2)
            (source / "solution_qc.json").write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "hard_checks": {"balance": True},
                        "maximum_residual": float("nan"),
                    }
                ),
                encoding="utf-8",
            )
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
                checkpoint_valid, checkpoint_failures = (
                    validate_barrier_primal_dual_checkpoint(
                        source,
                        require_result_manifest=True,
                    )
                )
            self.assertFalse(checkpoint_valid)
            self.assertIn("solution_qc_nonfinite", checkpoint_failures)
            self.assertIn(
                "acceptance_evidence_solution_qc_sha256",
                checkpoint_failures,
            )
            (source / "solution_qc.json").write_text(
                json.dumps(qc), encoding="utf-8"
            )

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
                (output / "run_environment.json").write_text(
                    json.dumps(
                        {
                            "packages": {"gurobipy": "13.0.2"},
                            "planning_state_in": None,
                        }
                    ),
                    encoding="utf-8",
                )
            self._write_input_manifest(source)
            self._write_input_manifest(
                target,
                solver_logical_path="solver/crossover2.json",
                solver_sha256="solver-crossover2",
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
            target_identity = dict(identity)
            target_identity["implementation_bundle"] = {"sha": "new-code"}
            target_identity["data_roots"] = {
                **identity["data_roots"],
                "CISPO_RAW_GRFR_ROOT": "/unused/raw/grfr",
            }
            (target / "run_identity.json").write_text(
                json.dumps(target_identity), encoding="utf-8"
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
                with self.assertRaisesRegex(
                    PrimalDualCheckpointError, "implementation bundle differs"
                ):
                    prepare_primal_dual_crossover(
                        source,
                        target,
                        FakeModel(),
                        self.config,
                        optimization_hours=8760,
                        optimization_start_hour=0,
                        result_use="SCIENTIFIC_PRODUCTION",
                        allow_engineering_checkpoint=True,
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
                    allow_compatible_implementation_bundle=True,
                )
            self.assertTrue(prepared["engineering_checkpoint_explicitly_allowed"])
            self.assertTrue(
                prepared[
                    "compatible_implementation_bundle_explicitly_allowed"
                ]
            )
            self.assertFalse(prepared["implementation_bundle_matches"])
            self.assertIsNone(prepared["source_result_manifest_sha256"])
            self.assertFalse(
                prepared["data_root_compatibility"]["exact_match"]
            )
            self.assertEqual(
                prepared["data_root_compatibility"][
                    "allowed_unused_optional_differences"
                ][0]["key"],
                "CISPO_RAW_GRFR_ROOT",
            )
            checkpoint_root = source / CHECKPOINT_DIRECTORY
            primal_path = checkpoint_root / "primal_barx.npy"
            primal = np.load(primal_path)
            primal[0] = np.nan
            np.save(primal_path, primal, allow_pickle=False)
            manifest_path = checkpoint_root / CHECKPOINT_MANIFEST
            checkpoint_manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            checkpoint_manifest["vectors"]["primal"]["bytes"] = (
                primal_path.stat().st_size
            )
            checkpoint_manifest["vectors"]["primal"]["sha256"] = (
                sha256_file(primal_path)
            )
            manifest_path.write_text(
                json.dumps(checkpoint_manifest), encoding="utf-8"
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
                self.assertFalse(valid)
                self.assertIn("vector_nonfinite:primal", failures)
                with self.assertRaisesRegex(
                    PrimalDualCheckpointError, "not eligible"
                ):
                    prepare_primal_dual_crossover(
                        source,
                        target,
                        FakeModel(),
                        self.config,
                        optimization_hours=8760,
                        optimization_start_hour=0,
                        result_use="SCIENTIFIC_PRODUCTION",
                        allow_engineering_checkpoint=True,
                        allow_compatible_implementation_bundle=True,
                    )

    def test_incomplete_barrier_vector_export_is_recovery_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
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
            (source / "run_identity.json").write_text(
                json.dumps(identity), encoding="utf-8"
            )
            (source / "input_manifest.csv").write_text(
                "same,input,manifest\n", encoding="utf-8"
            )
            (source / "run_environment.json").write_text(
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
                "status": "INTERRUPTED",
                "status_code": 11,
                "runtime_seconds": 10.0,
                "iteration_counts": {"barrier": 7},
                "solver_parameters": {
                    "method": 2,
                    "crossover": 0,
                    "solution_target": 1,
                },
                "solution_contract": {
                    "mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                    "acceptance_status": "PENDING_OR_NO_SOLUTION",
                    "barrier_status_code": 11,
                },
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
                    allow_incomplete_barrier=True,
                )
            self.assertEqual(
                metadata["checkpoint_status"], RECOVERY_CHECKPOINT_STATUS
            )
            self.assertFalse(metadata["scientifically_accepted"])
            self.assertFalse(metadata["deferred_crossover_eligible"])
            self.assertTrue(
                (source / CHECKPOINT_DIRECTORY / "primal_barx.npy").is_file()
            )
            self.assertTrue(
                (source / CHECKPOINT_DIRECTORY / "dual_barpi.npy").is_file()
            )

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
            target.Params.Crossover = 2
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
