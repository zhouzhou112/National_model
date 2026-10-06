"""Tiny fixtures for byte-integrity checks; no annual model or solver needed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("backup_verifier", Path(__file__).parents[1] / "scripts/verify_preserved_backup.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BackupVerifierTest(unittest.TestCase):
    def make_fixture(self, root):
        (root / "result.csv").write_bytes(b"value\n3\n")
        manifest = {"scientifically_accepted": False, "files": [{"path": "result.csv", "bytes": 8,
                    "sha256": hashlib.sha256(b"value\n3\n").hexdigest()}]}
        (root / "result_manifest.json").write_text(json.dumps(manifest))

    def test_complete_unaccepted_is_integrity_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            result = module.verify(root)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["scientific_acceptance"])

    def test_same_size_corruption_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            (root / "result.csv").write_bytes(b"value\n4\n")
            self.assertEqual(module.verify(root)["status"], "FAIL")

    def test_missing_file_is_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            (root / "result.csv").unlink()
            self.assertEqual(module.verify(root)["status"], "FAIL")
            self.assertEqual(module.verify(root, subset=True)["status"], "SUBSET_PASS")

    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "result_manifest.json").write_text(json.dumps({"files": [{"path": "../other"}]}))
            with self.assertRaises(ValueError):
                module.verify(root)


if __name__ == "__main__":
    unittest.main()
