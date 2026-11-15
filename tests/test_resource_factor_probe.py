from pathlib import Path
from types import SimpleNamespace
import copy,json,tempfile,unittest
import numpy as np
from cispo_model.frozen_capacity import (validate_resource_factor_mode,
    RESOURCE_FACTOR_PROFILE_ID,RESTRICTED_RESOURCE_PROFILE_ID)

class ResourceFactorContractTests(unittest.TestCase):
    def test_resource_profiles_preserve_physical_annual_rows(self):
        from scripts.run_cispo_2030_full_year import direct_nonbasic_row_scaling_contract
        from cispo_model.frozen_capacity import PROFILE_IDS
        for profile in [*PROFILE_IDS, RESTRICTED_RESOURCE_PROFILE_ID, RESOURCE_FACTOR_PROFILE_ID]:
            cfg=SimpleNamespace(raw={'solver_profile': {'id':profile}})
            self.assertEqual(direct_nonbasic_row_scaling_contract(cfg), ('physical_v1',0))
        legacy=SimpleNamespace(raw={'solver_profile': {'id':'barrier_checkpoint_full_year_cloud_v4'}})
        self.assertEqual(direct_nonbasic_row_scaling_contract(legacy), ('binary_power2_safe_8192_v1',13))

    def fixture(self):
        root=Path(__file__).resolve().parents[1]
        p=json.loads((root/'config/solver_profiles'/f'{RESTRICTED_RESOURCE_PROFILE_ID}.json').read_text())
        cfg=SimpleNamespace(planning_year=2050,raw=dict(scenario=dict(id='case3_thermal_ev_v5'),numerics=p['numerics'],solver_profile=dict(id=RESOURCE_FACTOR_PROFILE_ID,direct_nonbasic_scientific_acceptance=False)))
        args=SimpleNamespace(state_in='approved-R1',late_entry_base_state=True,horizon='full_year',archive_original_model=True,preflight_only=False)
        return cfg,args

    def test_probe_keeps_all_production_numeric_parameters(self):
        cfg,args=self.fixture();before=copy.deepcopy(cfg.raw);validate_resource_factor_mode(cfg,args);self.assertEqual(cfg.raw,before)
        for key,value in [('threads',48),('bar_iter_limit',5),('barrier_convergence_tolerance',1e-3)]:
            changed=copy.deepcopy(cfg);changed.raw['numerics'][key]=value
            with self.assertRaises(ValueError):validate_resource_factor_mode(changed,args)

    def test_scope_and_scientific_export_are_rejected(self):
        cfg,args=self.fixture()
        for key,value in [('allow_nonbasic_planning_state',True),('export_barrier_checkpoint',True),('horizon','test_24h'),('diagnostic_hours',24)]:
            changed=copy.copy(args);setattr(changed,key,value)
            with self.assertRaises(ValueError):validate_resource_factor_mode(cfg,changed)
        cfg.planning_year=2060;args.late_entry_base_state=False
        with self.assertRaises(ValueError):validate_resource_factor_mode(cfg,args)

    def test_real_barrier_stops_at_five_without_changing_parameters(self):
        try:import gurobipy as gp
        except ImportError:self.skipTest('Gurobi required for bounded probe')
        from cispo_model.factor_screen import solve_factor_screen
        with gp.Env(empty=True) as env:
            env.setParam('OutputFlag',0);env.start()
            with gp.Model(env=env) as model,tempfile.TemporaryDirectory() as tmp:
                model.Params.Method=2;model.Params.Presolve=0;model.Params.Crossover=0;model.Params.BarConvTol=1e-10;model.Params.Threads=2
                rng=np.random.default_rng(42);a=rng.uniform(.1,1.,(120,300));x=model.addMVar(300,lb=0,ub=1)
                model.addConstr(a@x>=a.sum(axis=1)*.7);model.setObjective(rng.uniform(.1,1.,300)@x)
                names=['Method','Presolve','Crossover','BarConvTol','Threads','BarIterLimit']
                before={n:getattr(model.Params,n) for n in names}
                result=solve_factor_screen(model,None,tmp,stop_after_barrier_iterations=5)
                self.assertEqual(before,{n:getattr(model.Params,n) for n in names})
                self.assertTrue(result['requested_stop_observed']);self.assertIsNone(result['callback_stop_error'])
                self.assertEqual(result['barrier_iterations'],5);self.assertFalse(result['production_state_written'])
                events=[json.loads(s) for s in (Path(tmp)/'solver_telemetry.jsonl').read_text().splitlines()]
                self.assertTrue(any(e['event']=='author_factor_probe_stop' and e['iteration']==5 for e in events))

if __name__=='__main__':unittest.main()
