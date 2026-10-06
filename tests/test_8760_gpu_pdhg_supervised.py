"""No model construction or server access in these deployment checks."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock
import tempfile
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("supervisor", Path(__file__).parents[1] / "scripts/run_8760_gpu_pdhg_supervised.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class DeploymentTests(unittest.TestCase):
    def test_only_admission_floor_changes(self):
        source = {"construction": {"horizons": {"full_year": {"hours": 8760, "minimum_available_memory_gb": 96, "test_only": False}}}, "features": {"carbon": True}}
        original = copy.deepcopy(source)
        result = mod.derive_config(source)
        self.assertEqual(source, original)
        self.assertEqual(result["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"], 1)
        result["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"] = 96
        self.assertEqual(result, source)

    def test_profile_exact_numerics(self):
        profile = {"profile_id": "old", "numerics": {"method": 6, "threads": 32, "crossover": 0, "pdhg_gpu": 1, "time_limit_seconds": None, "soft_mem_limit_gb": None}}
        self.assertEqual(mod.derive_profile(profile)["numerics"], profile["numerics"])
        self.assertEqual(profile["profile_id"], "old")

    def test_reject_old_time_limit(self):
        profile = {"numerics": {"method": 6, "threads": 32, "crossover": 0, "pdhg_gpu": 1, "time_limit_seconds": 21600, "soft_mem_limit_gb": None}}
        with self.assertRaises(AssertionError):
            mod.derive_profile(profile)

    def test_refuse_signal_finished_process(self):
        class Finished:
            def poll(self):
                return 0
        self.assertFalse(mod.signal_owned(Finished(), 0, 9))

    def exercise_supervisor(self, used_percent):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "run_control").mkdir()
            (root / "outputs").mkdir()
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "preparation.json").write_text("{}")
            child = mock.Mock(pid=10001)
            child.poll.side_effect = [None, 0]
            child.wait.return_value = 0
            monitor = mock.Mock(pid=10002)
            monitor.poll.return_value = None
            monitor.wait.return_value = 0
            memory = SimpleNamespace(total=100 * 2**30, available=(100 - used_percent) * 2**30)
            with mock.patch.object(mod, "validate", return_value={}), \
                 mock.patch.object(mod.subprocess, "Popen", side_effect=[child, monitor]) as popen, \
                 mock.patch.object(mod.psutil, "Process", return_value=mock.Mock(create_time=lambda: 123)), \
                 mock.patch.object(mod.psutil, "virtual_memory", return_value=memory), \
                 mock.patch.object(mod.psutil, "swap_memory", return_value=SimpleNamespace(used=0)), \
                 mock.patch.object(mod, "signal_owned", return_value=True) as send_signal, \
                 mock.patch.object(mod.signal, "SIGKILL", 9, create=True), \
                 mock.patch.object(mod.time, "sleep"):
                self.assertEqual(mod.supervise(root, bundle), 0)
                monitor_args = popen.call_args_list[1].args[0]
                self.assertIn("--interval", monitor_args)
                self.assertEqual(monitor_args[monitor_args.index("--interval") + 1], "2")
                control = root / "run_control" / mod.TAG
                self.assertTrue((control / "return_code.txt").exists())
                if used_percent >= 94:
                    send_signal.assert_called_once_with(child, 123, mod.signal.SIGKILL)
                    self.assertTrue((control / "guard_trigger.json").exists())
                else:
                    send_signal.assert_not_called()

    def test_supervisor_launches_resource_monitor_and_finishes(self):
        self.exercise_supervisor(40)

    def test_memory_guard_targets_new_child_only(self):
        self.exercise_supervisor(94.2)


if __name__ == "__main__":
    unittest.main()
