"""Safety checks for the one-shot completed-result backup workflow."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "completed_backup", Path(__file__).parents[1] / "scripts/backup_completed_cloud.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class CompletedCloudBackupTests(unittest.TestCase):
    def config(self):
        return dict(operation="test_operation", releases=["release1"],
                    destination="/backup", source="/cloud",
                    ssh_config="/ssh/config", authorization="test")

    def test_reject_traversal_and_duplicate_releases(self):
        for releases in [["../elsewhere"], ["release1", "release1"], []]:
            with self.subTest(releases=releases), self.assertRaises(AssertionError):
                backup.configure(dict(self.config(), releases=releases))

    def test_cannot_reduce_reserve(self):
        with self.assertRaises(AssertionError):
            backup.configure(dict(self.config(), minimum_free_fraction=0.1))

    def test_plan_rejects_existing_destination_before_network(self):
        backup.configure(self.config())
        with TemporaryDirectory() as folder:
            backup.DEST = Path(folder)
            backup.OP = backup.DEST / "_operations/new"
            (backup.DEST / "release1").mkdir()
            with patch.object(backup, "inventory") as inventory:
                with self.assertRaises(AssertionError):
                    backup.plan()
                inventory.assert_not_called()

    def inventory_fixture(self, active="", manifest_path="solve_report.json",
                          preservation="COMPLETE", marker=True):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "release1"
            out = root / "output_8760"
            out.mkdir(parents=True)
            # Complete preservation is independent of OPTIMAL and QC acceptance.
            solve = out / "solve_report.json"
            solve.write_text('{"status":"SUBOPTIMAL","solution_qc_status":"HARD_FAIL"}')
            (out / "preservation_report.json").write_text(
                json.dumps({"status": preservation}))
            (out / "result_manifest.json").write_text(json.dumps({"files": [{
                "path": manifest_path, "bytes": solve.stat().st_size,
                "sha256": backup.digest(solve)}]}))
            if marker:
                (root / "batch_exit.json").write_text('{"exit_code":0}')
            namespace = dict(source=folder, releases=["release1"])
            with patch("subprocess.check_output", side_effect=[
                    "testuser\n", str(root) + "\n" if active else ""]):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    exec(backup.INVENTORY, namespace)
            return json.loads(output.getvalue())

    def test_complete_suboptimal_hard_fail_output_is_preserved(self):
        result = self.inventory_fixture()
        self.assertIn("release1", result["releases"])
        self.assertTrue(result["releases"]["release1"]["files"])

    def test_reject_live_release(self):
        with self.assertRaises(AssertionError):
            self.inventory_fixture(active=True)

    def test_reject_unfinished_preservation_or_missing_terminal_marker(self):
        for kwargs in [dict(preservation="RUNNING"), dict(marker=False)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(AssertionError):
                self.inventory_fixture(**kwargs)

    def test_reject_unsafe_manifest_member(self):
        with self.assertRaises(AssertionError):
            self.inventory_fixture(manifest_path="../solve_report.json")


if __name__ == "__main__":
    unittest.main()
