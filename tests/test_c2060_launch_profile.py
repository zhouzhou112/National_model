"""Guard the explicit C2060 preparation against reusing a 2050 screen."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class C2060PreparationTests(unittest.TestCase):
    def test_production_contract_and_author_scope(self):
        from types import SimpleNamespace
        from cispo_model.config import load_model_config
        from cispo_model.factor_screen import validate_production_screen_contract, LATE_ENTRY_2060_40_PROFILE_ID
        from scripts.run_cispo_2030_full_year import DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS
        self.assertIn(LATE_ENTRY_2060_40_PROFILE_ID, DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS)
        cfg=load_model_config(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json',
            scenario_path=ROOT/'config/scenarios/case3_thermal_ev_v5.json',
            solver_path=ROOT/f'config/solver_profiles/{LATE_ENTRY_2060_40_PROFILE_ID}.json').for_planning_year(2060)
        args=SimpleNamespace(state_in='C2050_R1_candidate',late_entry_base_state=False,archive_original_model=True,
            vre_screen_csv=ROOT/'supplementary_materials/reviews/base_2060_screen_20261026/ready/source_screen.csv')
        validate_production_screen_contract(cfg,args)
        for attr,value in [('state_in',None),('late_entry_base_state',True)]:
            changed=SimpleNamespace(**vars(args));setattr(changed,attr,value)
            with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(cfg,changed)
        with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(cfg.for_planning_year(2050),args)
        cfg.raw['candidate_screen']['source_release']='wrong_year'
        with self.assertRaisesRegex(ValueError,'Base2060'):validate_production_screen_contract(cfg,args)

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
