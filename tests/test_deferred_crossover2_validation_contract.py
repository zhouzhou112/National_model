from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.audit_accepted_deferred_crossover_pair import audit_pair
from scripts.audit_relaxed_barrier_macro import (
    CARBON_ACCOUNT_FIELDS,
    OPERATION_ACCOUNT_FIELDS,
)


ROOT = Path(__file__).resolve().parents[1]


class DeferredCrossover2ValidationContractTests(unittest.TestCase):
    def test_runner_is_fail_closed_and_never_exports_state_or_basis(self) -> None:
        text = (
            ROOT
            / "scripts"
            / "run_fixed_server_deferred_crossover2_744_validation.sh"
        ).read_text(encoding="utf-8")
        for required in (
            "check_barrier_checkpoint_eligibility.py",
            "--primal-dual-checkpoint-in",
            "--allow-primal-dual-crossover",
            "--allow-engineering-barrier-checkpoint",
            "--allow-compatible-primal-dual-implementation",
            "strict_terminal_audit.json",
            "hard_check_count",
            "len(hard) == 58",
            "validate_result_manifest",
            "validate_input_manifest",
            "audit_accepted_deferred_crossover_pair.py",
        ):
            self.assertIn(required, text)
        self.assertNotIn("--export-diagnostic-state", text)
        self.assertNotIn("--export-warm-start-basis", text)

    def test_pair_audit_keeps_truncated_horizon_boundary(self) -> None:
        text = (
            ROOT / "scripts" / "audit_accepted_deferred_crossover_pair.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"scientifically_accepted": False', text)
        self.assertIn('"TEST_ONLY_TRUNCATED_HORIZON"', text)
        self.assertIn("exact_identity[\"matches\"]", text)
        self.assertIn("source_checkpoint_manifest_sha256", text)

    def test_pair_audit_accepts_identical_strict_macro_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate"
            reference = root / "reference"
            candidate.mkdir()
            reference.mkdir()
            identity = {
                "baseline_contract": {"contract_sha256": "baseline"},
                "analysis_case": {
                    "resolved_scientific_configuration_sha256": "science",
                    "scenario_configuration": {"sha256": "scenario"},
                    "formulation_configuration": {"sha256": None},
                },
                "lp_model": {
                    "variables": 3,
                    "constraints": 2,
                    "nonzeros": 4,
                    "gurobi_fingerprint": 123,
                },
            }
            summary = {
                "objective_million_cny_per_year": 100.0,
                "period_load_gwh": 200.0,
                "period_generation_gwh": 200.0,
                **{name: 1.0 for name in OPERATION_ACCOUNT_FIELDS},
            }
            carbon = {name: 1.0 for name in CARBON_ACCOUNT_FIELDS}
            hard = {f"check_{index}": True for index in range(58)}
            solve = {
                "status": "OPTIMAL",
                "solution_contract": {"acceptance_status": "PASS"},
            }
            qc = {"status": "PASS", "hard_checks": hard}
            for index, output in enumerate((candidate, reference)):
                run_identity = dict(identity)
                run_identity["implementation_bundle"] = {
                    "source_bundle_sha256": f"bundle-{index}"
                }
                (output / "run_identity.json").write_text(
                    json.dumps(run_identity), encoding="utf-8"
                )
                (output / "solve_report.json").write_text(
                    json.dumps(solve), encoding="utf-8"
                )
                (output / "solution_qc.json").write_text(
                    json.dumps(qc), encoding="utf-8"
                )
                (output / "annual_summary.json").write_text(
                    json.dumps(summary), encoding="utf-8"
                )
                (output / "annual_carbon_ccs.json").write_text(
                    json.dumps(carbon), encoding="utf-8"
                )
                pd.DataFrame(
                    [{"technology": "wind", "capacity": 10.0}]
                ).to_csv(
                    output / "annual_capacity_by_technology.csv", index=False
                )
                pd.DataFrame(
                    [{"technology": "wind", "generation_gwh": 20.0}]
                ).to_csv(
                    output / "annual_generation_by_technology.csv", index=False
                )
                pd.DataFrame(
                    [
                        {
                            "kind": "configuration",
                            "logical_path": "config.json",
                            "resolved_path": "/repo/config.json",
                            "required": "True",
                            "exists": "True",
                            "size_bytes": "1",
                            "sha256": "same",
                            "integrity_method": "sha256_file",
                            "role": "",
                        },
                        {
                            "kind": "solver_configuration",
                            "logical_path": f"solver-{index}.json",
                            "resolved_path": f"/repo/solver-{index}.json",
                            "required": "True",
                            "exists": "True",
                            "size_bytes": "1",
                            "sha256": f"solver-{index}",
                            "integrity_method": "sha256_file",
                            "role": "",
                        },
                    ]
                ).to_csv(output / "input_manifest.csv", index=False)
                (output / "result_manifest.json").write_text(
                    "{}", encoding="utf-8"
                )
            (candidate / "primal_dual_start_input.json").write_text(
                json.dumps(
                    {
                        "lp_warm_start": 2,
                        "engineering_checkpoint_explicitly_allowed": True,
                        "source_checkpoint_manifest_sha256": "checkpoint",
                        "scientific_input_manifest_identity": {
                            "sha256": "science-inputs"
                        },
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch(
                    "scripts.audit_accepted_deferred_crossover_pair.validate_result_manifest",
                    return_value=(True, []),
                ),
                patch(
                    "scripts.audit_accepted_deferred_crossover_pair.validate_input_manifest",
                    return_value=(True, []),
                ),
            ):
                result = audit_pair(candidate, reference)
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["strict_test_result_accepted"])
            self.assertTrue(result["exact_ab_identity"]["matches"])
            self.assertFalse(
                result["exact_ab_identity"]["source_bundle_matches"]
            )


if __name__ == "__main__":
    unittest.main()
