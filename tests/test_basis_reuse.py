from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from scipy import sparse

from cispo_model.basis_reuse import (
    BASIS_SCHEMA_VERSION,
    BasisReuseError,
    lp_topology_identity,
    prepare_basis_reuse,
)
from cispo_model.config import load_model_config
from cispo_model.io_contract import sha256_file
from cispo_model.result_summary import finalize_result_manifest


class _FakeModel:
    def __init__(self, *, sense: str = "=", pattern: str = "reference"):
        self.NumVars = 3
        self.NumConstrs = 2
        self.NumNZs = 4
        self._sense = sense
        matrices = {
            "reference": [[1.0, 1.0, 0.0], [0.0, 1.0, 1.0]],
            "different": [[1.0, 0.0, 1.0], [1.0, 1.0, 0.0]],
        }
        self._matrix = sparse.csr_matrix(matrices[pattern])

    def update(self):
        return None

    def getVars(self):
        return ["v0", "v1", "v2"]

    def getConstrs(self):
        return ["c0", "c1"]

    def getAttr(self, name, values):
        if name == "VarName":
            return ["x[0]", "x[1]", "x[2]"]
        if name == "ConstrName":
            return ["balance[0]", "balance[1]"]
        if name == "Sense":
            return [self._sense, self._sense]
        raise AssertionError(name)

    def getA(self):
        return self._matrix


class BasisReuseTests(unittest.TestCase):
    def test_named_structure_identity_is_sensitive_to_constraint_sense(self):
        equal_identity = lp_topology_identity(_FakeModel(sense="="))
        less_identity = lp_topology_identity(_FakeModel(sense="<"))
        self.assertEqual(equal_identity["variable_names_sha256"], less_identity["variable_names_sha256"])
        self.assertNotEqual(
            equal_identity["constraint_name_senses_sha256"],
            less_identity["constraint_name_senses_sha256"],
        )

    def test_lp_topology_identity_is_sensitive_to_raw_sparse_pattern(self):
        reference = lp_topology_identity(_FakeModel(pattern="reference"))
        changed = lp_topology_identity(_FakeModel(pattern="different"))
        self.assertEqual(reference["variables"], changed["variables"])
        self.assertEqual(reference["constraints"], changed["constraints"])
        self.assertEqual(reference["nonzeros"], changed["nonzeros"])
        self.assertEqual(
            reference["variable_names_sha256"], changed["variable_names_sha256"]
        )
        self.assertEqual(
            reference["constraint_name_senses_sha256"],
            changed["constraint_name_senses_sha256"],
        )
        self.assertNotEqual(
            reference["raw_csr_pattern_sha256"],
            changed["raw_csr_pattern_sha256"],
        )

    def test_prepare_rejects_cross_year_without_explicit_permission(self):
        config = load_model_config().for_planning_year(2040)
        source_identity = lp_topology_identity(_FakeModel())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            basis = root / "warm_start_basis.bas"
            basis.write_text("# test-only basis\n", encoding="utf-8")
            (root / "solve_report.json").write_text(
                json.dumps({"status": "OPTIMAL"}), encoding="utf-8"
            )
            (root / "solution_qc.json").write_text(
                json.dumps({"status": "PASS"}), encoding="utf-8"
            )
            (root / "warm_start_basis_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": BASIS_SCHEMA_VERSION,
                        "basis_file": basis.name,
                        "basis_sha256": sha256_file(basis),
                        "source": {
                            "planning_year": 2030,
                            "optimization_hours": 1,
                            "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
                            "git_commit": "deliberately_different_implementation_commit",
                        },
                        "identity_layers": {"lp_topology": source_identity},
                    }
                ),
                encoding="utf-8",
            )
            finalize_result_manifest(
                root,
                SimpleNamespace(
                    boundary_year=2025,
                    planning_year=2030,
                    path=Path("config/optimization_2030.json"),
                ),
            )
            with self.assertRaises(BasisReuseError):
                prepare_basis_reuse(
                    root,
                    _FakeModel(),
                    config,
                    optimization_hours=1,
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                    allow_cross_year=False,
                )
            prepared = prepare_basis_reuse(
                root,
                _FakeModel(),
                config,
                optimization_hours=1,
                result_use="TEST_ONLY_TRUNCATED_HORIZON",
                allow_cross_year=True,
            )
            self.assertTrue(prepared["cross_year"])
            self.assertEqual(prepared["lp_warm_start"], 2)
            self.assertFalse(prepared["audit_layer_matches"]["implementation_bundle"])

    def test_prepare_rejects_same_size_different_sparse_pattern(self):
        config = load_model_config().for_planning_year(2030)
        source_identity = lp_topology_identity(_FakeModel(pattern="reference"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            basis = root / "warm_start_basis.bas"
            basis.write_text("# test-only basis\n", encoding="utf-8")
            (root / "solve_report.json").write_text(
                json.dumps({"status": "OPTIMAL"}), encoding="utf-8"
            )
            (root / "solution_qc.json").write_text(
                json.dumps({"status": "PASS"}), encoding="utf-8"
            )
            (root / "warm_start_basis_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": BASIS_SCHEMA_VERSION,
                        "basis_file": basis.name,
                        "basis_sha256": sha256_file(basis),
                        "source": {
                            "planning_year": 2030,
                            "optimization_hours": 1,
                            "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
                        },
                        "identity_layers": {"lp_topology": source_identity},
                    }
                ),
                encoding="utf-8",
            )
            finalize_result_manifest(
                root,
                SimpleNamespace(
                    boundary_year=2025,
                    planning_year=2030,
                    path=Path("config/optimization_2030.json"),
                ),
            )
            with self.assertRaisesRegex(BasisReuseError, "raw LP topologies differ"):
                prepare_basis_reuse(
                    root,
                    _FakeModel(pattern="different"),
                    config,
                    optimization_hours=1,
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                    allow_cross_year=False,
                )


if __name__ == "__main__":
    unittest.main()
