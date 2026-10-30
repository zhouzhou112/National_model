"""Guard the explicit C2060 preparation against reusing a 2050 screen."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class C2060PreparationTests(unittest.TestCase):
    def test_only_year_screen_and_description_change(self):
        folder = ROOT/'config/solver_profiles'
        old = json.loads((folder/'barrier_stagea_screened_agg0_case3_2050_v1_threads40.json').read_text())
        new = json.loads((folder/'barrier_stagea_screened_agg0_lateentry_2060_v1_threads40.json').read_text())
        changed = {k for k in old.keys() | new.keys() if old.get(k) != new.get(k)}
        self.assertEqual(changed, {'profile_id', 'description', 'candidate_screen'})
        self.assertEqual(new['numerics']['threads'], 40)
        self.assertEqual(new['numerics']['aggregate'], 0)
        self.assertEqual(new['candidate_screen']['margin'], .2)
        self.assertEqual(new['candidate_screen']['source_release'], '20261012_base2060_v9a12_t48_m750_tol1e4_v1')

    def test_ready_screen_identity(self):
        path = ROOT/'supplementary_materials/reviews/base_2060_screen_20261026/ready/source_screen.csv'
        if not path.exists():
            self.skipTest('Large source screen is kept in the local evidence archive')
        profile = json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_lateentry_2060_v1_threads40.json').read_text())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), profile['candidate_screen']['source_csv_sha256'])

    def test_2060_requires_explicit_inputs_before_creating_output(self):
        script = ROOT/'supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py'
        for additional in ([], ['--unscreened']):
            r = subprocess.run([sys.executable, str(script), '--year', '2060', '--hours', '1',
                                '--state', 'not-used', '--output', 'must-not-create']+additional,
                               cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(r.returncode, 2, r.stdout+r.stderr)
            self.assertIn('2060 requires an explicit solver profile', r.stderr)


if __name__ == '__main__':
    unittest.main()
