"""Real two-row runner gate plus strict screening/profile boundaries."""
import copy
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.factor_screen import apply_vre_screen, validate_factor_screen_contract, PROFILE_ID

ROOT = Path(__file__).resolve().parents[1]


class FactorScreenTests(unittest.TestCase):
    def config(self, folder):
        payload = json.loads((ROOT / 'config/scenarios/case3_thermal_ev_v5.json').read_text())
        payload['parent_baseline_case_id'] = 'base_2024_numeric_water_dac_by_year_20260913_v9'
        path = folder / 'scenario.json'
        path.write_text(json.dumps(payload))
        return load_model_config('config/optimization_numeric_dac_by_year_v9.json',
            scenario_path=path, solver_path=f'config/solver_profiles/{PROFILE_ID}.json')

    def test_exact_identity_alignment_and_only_upper_bounds_change(self):
        with tempfile.TemporaryDirectory() as temporary, gp.Model() as model:
            model.Params.OutputFlag = 0
            folder = Path(temporary)
            v = model.addMVar(3, ub=[2, 3, 0], name='vre_new')
            model.addConstr(v.sum() <= 4)
            model.setObjective(v.sum())
            model.update()
            sites = pd.DataFrame({'grid_uid':['a','b','c'], 'technology':['upv']*3})
            source = folder/'screen.csv'
            sites.assign(rc_ratio=[0.1,0.2,0.9]).iloc[::-1].to_csv(source,index=False)
            before = model.getA().toarray()
            report=apply_vre_screen(SimpleNamespace(model=model,variables={'vre_new':v}),sites,source,folder)
            np.testing.assert_equal(v.UB, [2,0,0])
            np.testing.assert_equal(model.getA().toarray(),before)
            self.assertEqual(report['fixed_columns'],1)
            self.assertEqual(report['fixed_headroom_gw'],3)
            sites.assign(rc_ratio=[0.1,0.2,0.9]).iloc[:2].to_csv(source,index=False)
            with self.assertRaisesRegex(ValueError,'mismatch'):
                apply_vre_screen(SimpleNamespace(model=model,variables={'vre_new':v}),sites,source,folder)

    def test_parameters_and_state_exports_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            cfg=self.config(Path(temporary))
            validate_factor_screen_contract(cfg,SimpleNamespace())
            with self.assertRaises(ValueError):
                validate_factor_screen_contract(cfg,SimpleNamespace(export_diagnostic_state=True))
            cfg.raw['numerics']['bar_iter_limit']=6
            with self.assertRaisesRegex(ValueError,'parameter drift'):
                validate_factor_screen_contract(cfg,SimpleNamespace())

    def test_real_runner_two_row_solve_never_exports_qc_or_state(self):
        from scripts import run_cispo_2030_full_year as runner
        with tempfile.TemporaryDirectory() as temporary, gp.Model() as model:
            folder=Path(temporary); cfg=self.config(folder)
            model.Params.OutputFlag=0
            v=model.addMVar(2,ub=[1,2],name='vre_new')
            model.addConstr(v[0]+v[1]>=1,name='fixture_supply')
            model.addConstr(v[0]+2*v[1]<=3,name='fixture_upper')
            model.setObjective(v.sum());model.update()
            art=SimpleNamespace(model=model,index={},variables={'vre_new':v})
            out=folder/'output'
            args=['runner','--config',str(cfg.path),'--solver-config',str(cfg.solver_path),
                '--diagnostic-hours','1','--archive-original-model','--output-dir',str(out)]
            with patch('sys.argv',args),patch.object(runner,'load_model_config',return_value=cfg),\
                 patch('cispo_model.monolithic.build_full_year_monolithic',return_value=art),\
                 patch.object(runner,'prebuild_flexible_load_solver_compatibility',return_value={'status':'PASS'}),\
                 patch.object(runner,'assess_flexible_load_solver_compatibility',return_value={'status':'PASS'}),\
                 redirect_stdout(StringIO()):
                runner.main()
            scope=json.loads((out/'run_scope.json').read_text())
            report=json.loads((out/'solve_report.json').read_text())
            self.assertEqual(scope['scientific_acceptance_mode'],'NONE')
            self.assertFalse(report['production_state_written'])
            self.assertFalse((out/'solution_qc.json').exists())
            self.assertFalse((out/'planning_state').exists())
            self.assertTrue((out/'solver_telemetry.jsonl').is_file())
            params=json.loads((out/'solver_parameters_before_optimize.json').read_text())
            self.assertEqual(params['BarIterLimit'],5)
            self.assertEqual(params['Threads'],48)


if __name__=='__main__': unittest.main()
