"""Verify isolated spill reduction preserves dispatch, including dry intervals."""
from types import SimpleNamespace
import unittest
import numpy as np
import gurobipy as gp
from cispo_model.numerical_cleanup import independent_spill_upper_scaled


class IndependentSpillTests(unittest.TestCase):
    def test_cascade_sources_and_targets_are_both_excluded(self):
        h=SimpleNamespace(reservoir_local_inflow_m3s=np.array([[0,2],[0,0],[0,3]],float),
            cascade_edge_source_local_rows=[np.array([0])],
            cascade_edge_target_local_rows=[np.array([1])])
        original=np.full((3,2),100.0)
        bound,eligible=independent_spill_upper_scaled(h,original,1)
        np.testing.assert_array_equal(eligible,[False,False,True])
        np.testing.assert_array_equal(bound[:2],original[:2])
        self.assertEqual(bound[2,0],0)
        self.assertAlmostEqual(bound[2,1],3)
        np.testing.assert_array_equal(original,100)

    def test_invalid_input_is_rejected(self):
        h=SimpleNamespace(reservoir_local_inflow_m3s=np.array([[1.,0.]]),
            cascade_edge_source_local_rows=[],cascade_edge_target_local_rows=[])
        for scale in [0,-1,np.inf,np.nan]:
            with self.assertRaises(ValueError): independent_spill_upper_scaled(h,np.ones((1,2)),scale)
        with self.assertRaises(ValueError): independent_spill_upper_scaled(h,np.ones((1,3)),1)
        for floor in [-1,np.inf,np.nan]:
            with self.assertRaises(ValueError):
                independent_spill_upper_scaled(h,np.ones((1,2)),1,positive_bound_floor_m3s=floor)

    def test_positive_upper_floor_preserves_zero_and_original_release_cap(self):
        h=SimpleNamespace(reservoir_local_inflow_m3s=np.array([[0.,0.01,0.2,5.]]),
            cascade_edge_source_local_rows=[],cascade_edge_target_local_rows=[])
        original=np.array([[2.,2.,0.0002,2.]])
        v3,_=independent_spill_upper_scaled(h,original,1000.)
        v4,_=independent_spill_upper_scaled(h,original,1000.,positive_bound_floor_m3s=1.)
        np.testing.assert_allclose(v4,[[0.,0.001,0.0002,0.005]],rtol=1e-15,atol=0.)
        self.assertTrue(np.all(v3<=v4))
        self.assertTrue(np.all(v4<=original))
        np.testing.assert_array_equal(v3==0,v4==0)

    def test_positive_upper_floor_config_validation(self):
        from copy import deepcopy
        from cispo_model.config import load_model_config,ModelConfig
        cfg=load_model_config(path='config/optimization_2030_spill_tightened_v3.json')
        for floor,enabled,valid in [(0.,True,True),(1.,True,True),(-1.,True,False),
                                    (np.inf,True,False),(1.,False,False)]:
            raw=deepcopy(cfg.raw)
            raw['hydro']['independent_spill_positive_bound_floor_m3s']=floor
            raw['hydro']['limit_independent_spill_to_inflow']=enabled
            candidate=ModelConfig(cfg.path,raw)
            if valid: candidate.validate()
            else:
                with self.assertRaises(ValueError): candidate.validate()

    def test_generation_projection_for_varied_storage_and_signed_prices(self):
        rng=np.random.default_rng(20260913)
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start()
            for case in range(24):
                hours=48
                local=rng.uniform(0,5,hours)
                local[rng.random(hours)<0.6]=0
                storage=[0.,0.1,2.,10000.][case%4]
                cap=rng.uniform(0.1,6,hours)
                price=rng.uniform(-2,3,hours)
                old_bound=np.minimum(local+storage,local.sum())
                h=SimpleNamespace(reservoir_local_inflow_m3s=local[None,:],
                    cascade_edge_source_local_rows=[],cascade_edge_target_local_rows=[])
                new_bound,_=independent_spill_upper_scaled(h,old_bound[None,:],1)
                floor_bound,_=independent_spill_upper_scaled(h,old_bound[None,:],1,positive_bound_floor_m3s=1.)
                old_gen=None;old_obj=None
                for mode in ['original','tightened','fixed_original_generation','positive_floor','fixed_original_with_floor']:
                    m=gp.Model(env=env);m.Params.Method=1
                    m.Params.FeasibilityTol=1e-9;m.Params.OptimalityTol=1e-9
                    g=m.addMVar(hours,lb=0,ub=np.minimum(old_bound,cap))
                    bound=old_bound if mode=='original' else (floor_bound[0] if 'floor' in mode else new_bound[0])
                    spill=m.addMVar(hours,lb=0,ub=bound)
                    v=m.addMVar(hours,lb=0,ub=storage)
                    m.addConstr(v[0]-v[-1]+g[0]+spill[0]==local[0])
                    m.addConstr(v[1:]-v[:-1]+g[1:]+spill[1:]==local[1:])
                    if mode.startswith('fixed_original'): m.addConstr(g==old_gen)
                    m.setObjective(price@g,gp.GRB.MAXIMIZE);m.optimize()
                    self.assertEqual(m.Status,gp.GRB.OPTIMAL,(case,mode))
                    if mode=='original': old_obj=m.ObjVal;old_gen=g.X
                    else: self.assertAlmostEqual(m.ObjVal,old_obj,places=6)
                    residual=v.X-np.roll(v.X,1)+g.X+spill.X-local
                    self.assertLess(np.abs(residual).max(),1e-7)
                    m.dispose()


if __name__=='__main__': unittest.main()
