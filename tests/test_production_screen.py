"""Author-scoped production screening; legacy and unscreened identities survive."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import gurobipy as gp
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.factor_screen import (PRODUCTION_PROFILE_ID, apply_vre_screen,
                                       validate_production_screen_contract)
from cispo_model.run_contract import configuration_identity, analysis_case_identity

ROOT = Path(__file__).resolve().parents[1]


class ProductionScreenTests(unittest.TestCase):
    def config(self):
        return load_model_config('config/optimization_numeric_dac_by_year_v9.json',
            scenario_path='config/scenarios/case3_thermal_ev_v5.json',
            solver_path=f'config/solver_profiles/{PRODUCTION_PROFILE_ID}.json')

    def args(self):
        return SimpleNamespace(archive_original_model=True,
            vre_screen_csv=ROOT/'supplementary_materials/reviews/factor_pair_8760_20261005/cloud_payload/source_screen.csv')

    def test_profile_and_author_scope(self):
        cfg = self.config()
        validate_production_screen_contract(cfg, self.args())
        args = self.args(); args.state_in = 'candidate'; args.allow_candidate_state_in = True
        validate_production_screen_contract(cfg, args)
        for bad in ('mga_spec', 'primal_dual_checkpoint_in', 'recover_stage_a_from'):
            args = self.args(); setattr(args, bad, 'bad')
            with self.assertRaises(ValueError):
                validate_production_screen_contract(cfg, args)
        cfg.raw['scenario']['id'] = 'base'
        with self.assertRaisesRegex(ValueError, 'whitelist'):
            validate_production_screen_contract(cfg, self.args())

    def test_continuation_profile_identity_year_and_numerics(self):
        from scripts.run_cispo_2030_full_year import direct_nonbasic_row_scaling_contract, DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS
        baseline=json.loads((ROOT/'config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json').read_text())
        for year in (2040,2050):
            profile_id=f'barrier_stagea_screened_agg0_{year}_v1_threads48'
            profile=json.loads((ROOT/f'config/solver_profiles/{profile_id}.json').read_text())
            self.assertEqual(profile['numerics'],baseline['numerics'])
            self.assertEqual({k:v for k,v in profile.items() if k not in ('profile_id','candidate_screen')},
                             {k:v for k,v in baseline.items() if k not in ('profile_id','candidate_screen')})
            cfg=load_model_config('config/optimization_numeric_dac_by_year_v9_a12.json',
                scenario_path='config/scenarios/case3_thermal_ev_v5.json',
                solver_path=f'config/solver_profiles/{profile_id}.json').for_planning_year(year)
            args=self.args();args.vre_screen_csv=ROOT/f'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready{year}_20261015/source_screen.csv'
            validate_production_screen_contract(cfg,args)
            self.assertIn(profile_id,DIRECT_NONBASIC_SCIENTIFIC_PROFILE_IDS)
            self.assertEqual(direct_nonbasic_row_scaling_contract(cfg),('physical_v1',0))
            with self.assertRaisesRegex(ValueError,'year/scenario'):
                validate_production_screen_contract(cfg.for_planning_year(2030),args)

    def test_identity_changes_with_screen_but_base_retains_historical_hash(self):
        base = load_model_config('config/optimization_numeric_dac_by_year_v9.json')
        self.assertEqual(analysis_case_identity(base)['resolved_scientific_configuration_sha256'],
            '937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0')
        cfg = self.config()
        identity = configuration_identity(cfg, data_root=ROOT/'data')
        self.assertEqual(identity['candidate_screen'], cfg.raw['candidate_screen'])
        before = identity['analysis_case']['resolved_scientific_configuration_sha256']
        cfg.raw['candidate_screen']['margin'] = .3
        self.assertNotEqual(before, analysis_case_identity(cfg)['resolved_scientific_configuration_sha256'])
        cfg.raw['numerics']['aggregate'] = 1
        with self.assertRaisesRegex(ValueError, 'aggregate'):
            validate_production_screen_contract(cfg, self.args())

    def test_margin_and_original_headroom_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder, gp.Model() as m:
            m.Params.OutputFlag = 0
            path = Path(folder)
            sites = pd.DataFrame({'grid_uid':['a','b'], 'technology':['upv','upv']})
            sites.assign(rc_ratio=[.2,.4]).to_csv(path/'screen.csv',index=False)
            v = m.addMVar(2,ub=[2,3]); m.update()
            result = apply_vre_screen(SimpleNamespace(model=m,variables={'vre_new':v}),
                sites,path/'screen.csv',path,margin=.3)
            self.assertEqual(list(v.UB),[2,0])
            self.assertEqual(result['margin'],.3)
            selected = pd.read_csv(path/'candidate_selection.csv')
            self.assertEqual(list(selected.original_new_ub_gw),[2,3])

    def test_manifest_contains_actual_v5_override_files(self):
        from cispo_model.io_contract import write_run_provenance
        with tempfile.TemporaryDirectory() as temporary:
            cfg = self.config()
            write_run_provenance(temporary, cfg, data_root=ROOT/'data',
                                 planning_state=SimpleNamespace(root=None, metadata={}))
            rows = pd.read_csv(Path(temporary)/'input_manifest.csv')
            for name in cfg.raw['flexible_load']['v5_input_files'].values():
                matched = rows.loc[rows.logical_path == name]
                self.assertEqual(len(matched),1,name)
                self.assertTrue(bool(matched.iloc[0]['exists']))
                self.assertEqual(len(matched.iloc[0]['sha256']),64)


if __name__ == '__main__':
    unittest.main()
