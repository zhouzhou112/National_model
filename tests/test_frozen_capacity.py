"""Base-frozen fail-closed contracts, stable joins and bound changes."""
from pathlib import Path
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from cispo_model.frozen_capacity import align, apply_frozen_capacity, validate_mode, save_capacity_expectations


class FrozenCapacityTests(unittest.TestCase):
    def test_permuted_stable_keys_and_extra_or_duplicate_rejected(self):
        table=pd.DataFrame({'grid_uid':['b','a'],'technology':['pv','wind'],'new':[2.,1.]})
        target=[['a','wind'],['b','pv']]
        np.testing.assert_array_equal(align(table,['grid_uid','technology'],target,'new'),[1.,2.])
        with self.assertRaises(ValueError):align(table,['grid_uid','technology'],target[:1],'new')
        with self.assertRaises(ValueError):align(pd.concat([table,table.iloc[:1]]),['grid_uid','technology'],target,'new')
        with self.assertRaises(ValueError):align(table,['grid_uid','technology'],[['c','wind'],['b','pv']],'new')

    def test_missing_column_and_nonfinite_source_rejected(self):
        for table in [pd.DataFrame({'grid_uid':['a']}),pd.DataFrame({'grid_uid':['a'],'new':[float('nan')]})]:
            with self.assertRaises(ValueError):align(table,['grid_uid'],[['a']],'new')

    def artifacts(self):
        mv=SimpleNamespace(shape=(2,),LB=np.array([0.,0.]),UB=np.array([1.,2.]),VarName=np.array(['vre_new_gw[0]','vre_new_gw[1]']))
        dispatch=SimpleNamespace(LB=np.array([0.]),UB=np.array([10.]))
        return SimpleNamespace(model=SimpleNamespace(update=lambda:None),variables={'vre_new':mv,'dispatch':dispatch},index={})

    def test_clip_only_investment_preserving_original_audit(self):
        art=self.artifacts(); table=pd.DataFrame({'grid_uid':['b','a'],'technology':['pv','wind'],'new_capacity_gw':[2.000001,-.000001]})
        registry=[('vre_new','vre_capacity.csv','new_capacity_gw',[['a','wind'],['b','pv']],'GW',False)]
        with tempfile.TemporaryDirectory() as tmp, patch('cispo_model.frozen_capacity.investment_registry',return_value=registry):
            report=apply_frozen_capacity(art,None,{'vre_capacity.csv':table},{},tmp)
            np.testing.assert_array_equal(art.variables['vre_new'].LB,[0.,2.])
            np.testing.assert_array_equal(art.variables['vre_new'].UB,[0.,2.])
            np.testing.assert_array_equal(art.variables['dispatch'].UB,[10.])
            self.assertEqual(report['clip_statistics']['GW']['clipped_columns'],2)
            self.assertTrue((Path(tmp)/'frozen_capacity_audit.csv').exists())

    def test_clip_reporting_threshold_stops_before_any_mutation(self):
        art=self.artifacts();table=pd.DataFrame({'grid_uid':['a','b'],'technology':['wind','pv'],'new_capacity_gw':[-.1,1.]})
        registry=[('vre_new','vre_capacity.csv','new_capacity_gw',[['a','wind'],['b','pv']],'GW',False)]
        with tempfile.TemporaryDirectory() as tmp,patch('cispo_model.frozen_capacity.investment_registry',return_value=registry):
            with self.assertRaisesRegex(ValueError,'clip exceeds'):
                apply_frozen_capacity(art,None,{'vre_capacity.csv':table},{},tmp)
            np.testing.assert_array_equal(art.variables['vre_new'].UB,[1.,2.])
            self.assertTrue((Path(tmp)/'frozen_capacity_report.json').exists())

    def test_incompatible_inputs_rejected(self):
        cfg=SimpleNamespace(raw={'scenario':{'id':'case3_thermal_ev_v5'},'features':{'flexible_load':True}})
        for flag in ['state_in','vre_screen_csv','mga_spec','primal_dual_checkpoint_in','recover_stage_a_from','late_entry_base_state']:
            with self.subTest(flag=flag),self.assertRaises(ValueError):
                validate_mode(cfg,SimpleNamespace(**{flag:'not-allowed'}),test_only=True)

    def test_base_control_test_only(self):
        cfg=SimpleNamespace(raw={'scenario':{'id':'base'},'features':{'flexible_load':False}})
        validate_mode(cfg,SimpleNamespace(),test_only=True)
        with self.assertRaises(ValueError):validate_mode(cfg,SimpleNamespace(),test_only=False)

    def test_production_preflight_needs_no_write_flags_but_solve_requires_them(self):
        from cispo_model.frozen_capacity import PROFILE_ID
        profile=json.loads((Path(__file__).resolve().parents[1]/'config/solver_profiles'/f'{PROFILE_ID}.json').read_text())
        cfg=SimpleNamespace(raw={'scenario':{'id':'case3_thermal_ev_v5'},
            'solver_profile':{'id':PROFILE_ID},'numerics':profile['numerics']})
        args=SimpleNamespace(preflight_only=True,archive_original_model=False,export_barrier_checkpoint=False)
        validate_mode(cfg,args,test_only=False)
        args.preflight_only=False
        with self.assertRaisesRegex(ValueError,'preservation'):validate_mode(cfg,args,test_only=False)
        args.archive_original_model=True;args.export_barrier_checkpoint=True
        validate_mode(cfg,args,test_only=False)

    def test_accounting_total_must_match_source_plus_only_clips(self):
        art=self.artifacts()
        registry=[('vre_new','vre_capacity.csv','new_capacity_gw',[['a','wind'],['b','pv']],'GW',False)]
        table=pd.DataFrame({'grid_uid':['a','b'],'technology':['wind','pv'],
                            'new_capacity_gw':[-.000001,2.], 'capacity_gw':[.999999,5.]})
        with tempfile.TemporaryDirectory() as tmp,patch('cispo_model.frozen_capacity.investment_registry',return_value=registry):
            apply_frozen_capacity(art,None,{'vre_capacity.csv':table},{},tmp)
            expected={'vre_new':np.array([0.,2.]),'vre_capacity':np.array([1.,5.])}
            with patch('cispo_model.frozen_capacity.expected_capacity_variables',return_value=expected):
                save_capacity_expectations(art,None,tmp,{'vre_capacity.csv':table})
                self.assertEqual(json.loads((Path(tmp)/'frozen_capacity_source_alignment.json').read_text())['status'],'PASS')
                table.loc[1,'capacity_gw']=5.01
                with self.assertRaisesRegex(ValueError,'accounting mismatch'):
                    save_capacity_expectations(art,None,tmp,{'vre_capacity.csv':table})
                self.assertEqual(json.loads((Path(tmp)/'frozen_capacity_source_alignment.json').read_text())['status'],'FAIL')


if __name__=='__main__':unittest.main()
