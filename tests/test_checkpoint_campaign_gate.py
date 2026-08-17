import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_barrier_checkpoint_eligibility import check_checkpoint_manifest


class CheckpointCampaignGateTests(unittest.TestCase):
    def _write_checkpoint(self, root: Path, *, eligible: bool, status: str) -> Path:
        checkpoint = root / "barrier_checkpoint"
        checkpoint.mkdir()
        vectors = {}
        for role, name in (("primal", "primal_barx.npy"), ("dual", "dual_barpi.npy")):
            payload = (role * 8).encode("ascii")
            path = checkpoint / name
            path.write_bytes(payload)
            vectors[role] = {
                "path": name,
                "entries": 8,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        manifest = {
            "schema_version": "cispo_barrier_primal_dual_checkpoint_v1",
            "checkpoint_status": status,
            "deferred_crossover_eligible": eligible,
            "scientifically_accepted": False,
            "solver_evidence": {"status_code": 2, "barrier_status_code": 2},
            "vectors": vectors,
        }
        path = checkpoint / "barrier_checkpoint_manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_complete_engineering_checkpoint_is_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = self._write_checkpoint(
                Path(raw),
                eligible=True,
                status="ENGINEERING_BARRIER_CHECKPOINT_ONLY",
            )
            report = check_checkpoint_manifest(manifest)
            self.assertTrue(report["eligible"])
            self.assertEqual(report["reasons"], [])

    def test_incomplete_recovery_is_not_eligible_even_when_vectors_exist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = self._write_checkpoint(
                Path(raw),
                eligible=False,
                status="RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT",
            )
            report = check_checkpoint_manifest(manifest)
            self.assertFalse(report["eligible"])
            self.assertIn("deferred_crossover_eligible", report["reasons"])
            self.assertIn("checkpoint_status", report["reasons"])

    def test_vector_hash_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            manifest = self._write_checkpoint(
                Path(raw),
                eligible=True,
                status="ENGINEERING_BARRIER_CHECKPOINT_ONLY",
            )
            (manifest.parent / "primal_barx.npy").write_bytes(b"changed")
            report = check_checkpoint_manifest(manifest)
            self.assertFalse(report["eligible"])
            self.assertIn("primal_size_mismatch", report["reasons"])
            self.assertIn("primal_sha256_mismatch", report["reasons"])


if __name__ == "__main__":
    unittest.main()
