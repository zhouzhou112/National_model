"""Author-scoped 2050 continuation guard, without constructing or solving an LP."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from cispo_model.config import load_model_config
from cispo_model.factor_screen import CASE3_2050_40_PROFILE_ID, PRODUCTION_PROFILE_IDS, validate_production_screen_contract

ROOT=Path(__file__).resolve().parents[1]

class Case32050PreparationTests(unittest.TestCase):
    def config(self):
        return load_model_config('config/optimization_numeric_dac_by_year_v9_a12.json',
            scenario_path='config/scenarios/case3_thermal_ev_v5.json',
            solver_path=f'config/solver_profiles/{CASE3_2050_40_PROFILE_ID}.json').for_planning_year(2050)

    def args(self):
        return SimpleNamespace(archive_original_model=True,state_in='accepted_case3_2040_R1',
            late_entry_base_state=False,vre_screen_csv=ROOT/'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2050_20261015/source_screen.csv')

    def test_only_authorized_profile_changes(self):
        base=json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json').read_text())
        actual=json.loads((ROOT/f'config/solver_profiles/{CASE3_2050_40_PROFILE_ID}.json').read_text())
        expected=copy.deepcopy(base);expected['numerics']['threads']=40;expected['profile_id']=CASE3_2050_40_PROFILE_ID
        expected['candidate_screen']=json.loads((ROOT/'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready2050_20261015/candidate_screen_fragment.json').read_text())['candidate_screen']
        self.assertEqual(actual,expected)
        self.assertIn(CASE3_2050_40_PROFILE_ID,PRODUCTION_PROFILE_IDS)
        validate_production_screen_contract(self.config(),self.args())

    def test_reject_wrong_year_scenario_and_upstream_mode(self):
        for year in [2030,2040,2060]:
            with self.assertRaisesRegex(ValueError,'same-scenario'):
                validate_production_screen_contract(self.config().for_planning_year(year),self.args())
        cfg=self.config();cfg.raw['scenario']['id']='case3_thermal_ev_v5_nocredit'
        with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(cfg,self.args())
        for key,value in [('state_in',None),('late_entry_base_state',True)]:
            args=self.args();setattr(args,key,value)
            with self.assertRaisesRegex(ValueError,'same-scenario'):validate_production_screen_contract(self.config(),args)

    def test_reject_numerical_drift(self):
        for key,value in [('threads',48),('aggregate',1),('crossover',2),('barrier_convergence_tolerance',1e-3)]:
            cfg=self.config();cfg.raw['numerics'][key]=value
            with self.assertRaisesRegex(ValueError,'drift'):validate_production_screen_contract(cfg,self.args())

if __name__=='__main__':unittest.main()
