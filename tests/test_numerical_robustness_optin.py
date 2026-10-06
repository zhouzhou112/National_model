"""Opt-in numerical controls preserve the disabled Base and physical units."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import gurobipy as gp
import numpy as np

from cispo_model.config import ModelConfig, load_model_config
from cispo_model.numerical_cleanup import zero_capacity_headroom, zero_retrofit_upper
from cispo_model.planning_state import clip_inherited_floor_overrun
from cispo_model.run_contract import analysis_case_identity
from cispo_model.annual_dense_split import annual_sum


class NumericalRobustnessTests(unittest.TestCase):
    def test_hydro_and_retrofit_cleanup_bounds_and_audit(self):
        floor=np.array([1.,2.,3.]); upper=floor+np.array([1e-8,1e-7,1e-3]);ids=['a','b','c']
        head,actual,audit=zero_capacity_headroom(floor,upper,0,ids)
        np.testing.assert_array_equal(actual,upper);np.testing.assert_array_equal(head,upper-floor)
        self.assertEqual(audit['site_rows'],[])
        head,actual,audit=zero_capacity_headroom(floor,upper,1e-6,ids)
        np.testing.assert_array_equal(head[:2],0);np.testing.assert_array_equal(actual[:2],floor[:2])
        self.assertEqual(audit['asset_ids'],ids[:2]);self.assertAlmostEqual(audit['total_removed_gw'],1.1e-7)
        actual,audit=zero_retrofit_upper([1e-16,1e-6,0],1e-6,ids)
        np.testing.assert_array_equal(actual,[0,1e-6,0]);self.assertEqual(audit['asset_ids'],['a'])
        actual,_=zero_retrofit_upper([1e-16],0,['a']);self.assertEqual(actual[0],1e-16)

    def test_inherited_clipping_repeatable_without_altering_original_and_fails_closed(self):
        original=np.array([1.0000002,2.]);upper=np.array([1.,2.])
        for _ in range(2):
            actual,audit=clip_inherited_floor_overrun(original,upper,threshold_gw=1e-5,asset_ids=['x','y'],asset_class='hydro')
            np.testing.assert_array_equal(actual,upper);self.assertEqual(audit['asset_ids'],['x'])
            self.assertEqual(original[0],1.0000002)
        actual,audit=clip_inherited_floor_overrun(original,upper,threshold_gw=0,asset_ids=['x','y'],asset_class='hydro')
        np.testing.assert_array_equal(actual,original);self.assertIsNone(audit)
        with self.assertRaises(ValueError):
            clip_inherited_floor_overrun([1.1],[1.],threshold_gw=1e-5,asset_ids=['x'],asset_class='hydro')

    def test_disabled_keys_preserve_historical_scientific_fingerprint(self):
        cfg=load_model_config('config/optimization_numeric_dac_by_year_v9.json')
        key='resolved_scientific_configuration_sha256'
        baseline=analysis_case_identity(cfg)[key]
        self.assertEqual(baseline,'937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0')
        raw=copy.deepcopy(cfg.raw)
        controls=['hydro_capacity_headroom_zero_gw','retrofit_upper_zero_gw','inherited_floor_overrun_clip_gw']
        raw['numerics'].update({k:0. for k in controls})
        raw['formulation']['annual_dense_row_split']={'enabled':False,'block_hours':730}
        self.assertEqual(analysis_case_identity(ModelConfig(cfg.path,raw))[key],baseline)
        for k in controls:
            candidate=copy.deepcopy(raw);candidate['numerics'][k]=1e-6
            self.assertNotEqual(analysis_case_identity(ModelConfig(cfg.path,candidate))[key],baseline)
            for bad in [-1,1e-3,float('nan')]:
                candidate['numerics'][k]=bad
                with self.assertRaises(ValueError):ModelConfig(cfg.path,candidate).validate()

    def test_block_projection_signed_account_and_partial_final_block(self):
        cfg=load_model_config();raw=copy.deepcopy(cfg.raw)
        raw['formulation']['annual_dense_row_split']={'enabled':True,'block_hours':3}
        cfg=ModelConfig(cfg.path,raw);cfg.validate()
        with gp.Model() as m:
            m.Params.OutputFlag=0
            x=m.addMVar(7,lb=-gp.GRB.INFINITY)
            total=annual_sum(m,cfg,7,'signed',lambda t: x[t].sum(),unit='mtco2')
            m.addConstr(x==np.array([-2.,1.,0.,3.,-4.,1.,-6.]))
            m.setObjective(total);m.optimize()
            self.assertEqual(m.Status,gp.GRB.OPTIMAL);self.assertEqual(m.ObjVal,-7.)
            aux=[v for v in m.getVars() if v.VarName.startswith('annual_block_')]
            self.assertEqual(len(aux),3);self.assertTrue(all(v.LB<=-gp.GRB.INFINITY for v in aux))
            self.assertEqual(m._annual_dense_split_audit['families'][0]['unit'],'mtco2')

    def test_homogeneous_profile_only_changes_solver_parameter(self):
        folder=Path(__file__).resolve().parents[1]/'config/solver_profiles'
        ref=json.loads((folder/'barrier_stagea_numeric_repaired_v1_threads48.json').read_text())
        candidate=json.loads((folder/'barrier_stagea_homogeneous_v1_threads48.json').read_text())
        self.assertFalse(candidate['direct_nonbasic_scientific_acceptance'])
        self.assertEqual(candidate['numerics'].pop('bar_homogeneous'),1)
        self.assertEqual(candidate['numerics'],ref['numerics'])
        cfg=load_model_config('config/optimization_numeric_dac_by_year_v9.json',solver_path=folder/'barrier_stagea_homogeneous_v1_threads48.json')
        from cispo_model.diagnostics import configure_gurobi
        with tempfile.TemporaryDirectory() as tmp, gp.Model() as m:
            configure_gurobi(m,cfg,Path(tmp)/'parameters.log')
            self.assertEqual(m.Params.BarHomogeneous,1)

    def test_block_constants_retain_legacy_annual_rhs_exactly(self):
        cfg=load_model_config();raw=copy.deepcopy(cfg.raw)
        raw['formulation']['annual_dense_row_split']={'enabled':True,'block_hours':1}
        cfg=ModelConfig(cfg.path,raw)
        constants=np.array([1e16,1.,-1e16])
        with gp.Model() as m:
            m.Params.OutputFlag=0
            x=m.addMVar(3,lb=0)
            total=annual_sum(m,cfg,3,'constant_test',lambda t: x[t].sum()+float(constants[t].sum()))
            annual=m.addConstr(total==42,name='original_annual')
            m.update()
            self.assertEqual(annual.RHS,42.-float(constants.sum()))
            for row in m.getConstrs():
                if row.ConstrName.startswith('annual_block_'):self.assertEqual(row.RHS,0.)

    def test_small_bound_changes_without_builder_audit_are_rejected(self):
        import runpy
        from scipy import sparse
        from cispo_model.physical_lp_diff import compare_physical_lp_arrays
        root=Path(__file__).resolve().parents[1]
        helper=runpy.run_path(str(root/'supplementary_materials/reviews/numerical_robustness_20261005/compare_probes.py'))['audited_capacity_closures']
        reference={'variable_names':np.array(['thermal_retrofit_to_ccs_gw[0,0]','thermal_retrofit_to_ccs_gw[1,0]']),
                   'lower':np.zeros(2),'upper':np.array([1e-7,1e-7])}
        candidate=dict(reference,upper=np.zeros(2))
        audit={'retrofit_upper_cleanup':[{'site_rows':[0],'removed_gw':[1e-7],'cutoff_gw':1e-6}]}
        allowed=helper(reference,candidate,audit)
        self.assertEqual(set(allowed),{'thermal_retrofit_to_ccs_gw[0,0]'})
        result=compare_physical_lp_arrays(reference_matrix=sparse.csr_matrix((1,2)),candidate_matrix=sparse.csr_matrix((1,2)),
            reference_rhs=np.zeros(1),candidate_rhs=np.zeros(1),reference_lower=np.zeros(2),candidate_lower=np.zeros(2),
            reference_upper=reference['upper'],candidate_upper=candidate['upper'],reference_objective=np.zeros(2),candidate_objective=np.zeros(2),
            reference_senses=['='],candidate_senses=['='],row_names=['row'],variable_names=reference['variable_names'],
            whitelist={'capacity_interval_closures':allowed})
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['failures'][0]['variable'],'thermal_retrofit_to_ccs_gw[1,0]')


if __name__=='__main__':unittest.main()

