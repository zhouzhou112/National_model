"""Check diagnostic launch parameters, exit semantics and archive protection."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import gurobipy as gp

from cispo_model.config import ModelConfig, load_model_config
from cispo_model.diagnostics import configure_gurobi
from scripts.probe_full_year_numerics import (diagnostic_exit_code, solver_parameter_snapshot,
    preserve_diagnostic_vectors, export_physical_diagnostics, write)


ROOT = Path(__file__).resolve().parents[1]


class FullYearNumericProbeTests(unittest.TestCase):
    def test_only_optimal_plus_qc_pass_returns_success(self):
        self.assertEqual(diagnostic_exit_code(2, True), 0)
        self.assertEqual(diagnostic_exit_code(2, False), 2)
        for status in [3, 4, 5, 12, 13]:
            self.assertEqual(diagnostic_exit_code(status, False), 2)
        for status in [7, 8, 9, 10, 11, 16, 17]:
            self.assertEqual(diagnostic_exit_code(status, False), 3)

    def test_cloud_parameters_are_actually_accepted_and_raw_archive_is_readable(self):
        cfg=load_model_config('config/optimization_numeric_dac_by_year_v9.json')
        raw=deepcopy(cfg.raw)
        raw['numerics'].update(threads=44,time_limit_seconds=900,soft_mem_limit_gb=None,
                               barrier_convergence_tolerance=1e-4,crossover=0,solution_target=1)
        cfg=ModelConfig(cfg.path,raw);cfg.validate()
        with tempfile.TemporaryDirectory() as tmp, gp.Model() as model:
            path=Path(tmp)
            configure_gurobi(model,cfg,path/'gurobi.log')
            snapshot=solver_parameter_snapshot(model,cfg)
            self.assertEqual(snapshot['Threads'],44)
            self.assertIsNone(snapshot['SoftMemLimit'])
            self.assertEqual(snapshot['BarConvTol'],1e-4)
            self.assertEqual(snapshot['NumericFocus'],2)
            self.assertEqual(snapshot['Crossover'],0)
            self.assertEqual(snapshot['SolutionTarget'],1)
            x=model.addVar(lb=1,ub=2,obj=1)
            model.addConstr(x<=1.5)
            model.write((path/'raw_model.mps').as_posix())
            with gp.read((path/'raw_model.mps').as_posix()) as reloaded:
                reloaded.Params.OutputFlag=0
                reloaded.optimize()
                self.assertEqual(reloaded.Status,gp.GRB.OPTIMAL)
                self.assertAlmostEqual(reloaded.ObjVal,1.)
            model.Params.Threads=8
            with self.assertRaisesRegex(RuntimeError,'Threads mismatch'):
                solver_parameter_snapshot(model,cfg)

    def test_dry_run_selects_v9_and_never_builds_or_writes_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'fresh'
            run=subprocess.run([sys.executable,'scripts/probe_full_year_numerics.py',
                '--output-dir',str(out),'--dry-run'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',
                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
            self.assertEqual(run.returncode,0,run.stderr)
            cfg=json.loads((out/'effective_config.json').read_text())
            self.assertEqual(cfg['features']['dac_by_planning_year'],
                             {'2030':False,'2040':True,'2050':True,'2060':True})
            self.assertFalse((out/'build.json').exists())
            self.assertFalse((out/'planning_state').exists())
            self.assertEqual(cfg['numerics']['threads'],44)
            self.assertIsNone(cfg['numerics']['soft_mem_limit_gb'])
            self.assertEqual(cfg['numerics']['barrier_convergence_tolerance'],1e-4)
            self.assertEqual(cfg['numerics']['crossover'],0)
            self.assertEqual(cfg['numerics']['solution_target'],1)
            plan=json.loads((out/'plan.json').read_text())
            self.assertEqual(plan['slurm_cpus_per_task'],64)
            self.assertEqual(plan['slurm_memory_gib'],700)
            self.assertEqual(plan['crossover'],0)
            self.assertEqual(plan['solution_target'],1)

    def test_existing_output_is_never_overwritten_even_when_launch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            for name in ['plan.json','terminal.json']:
                (out/name).write_text('{"historical":true}',encoding='utf-8')
            run=subprocess.run([sys.executable,'scripts/probe_full_year_numerics.py',
                '--output-dir',str(out),'--dry-run'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',
                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
            self.assertNotEqual(run.returncode,0)
            self.assertEqual((out/'terminal.json').read_text(),'{"historical":true}')

    def test_atomic_write_preserves_last_record_when_value_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'record.json'
            write(path,{'state':'RUNNING'})
            with self.assertRaises(ValueError):
                write(path,{'bad':float('nan')})
            self.assertEqual(json.loads(path.read_text()),{'state':'RUNNING'})

    def test_master_qc_failure_does_not_suppress_hourly_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('cispo_model.master.export_master_solution',side_effect=RuntimeError('network QC')):
                with patch('cispo_model.solution_export.export_operational_solution',return_value={'status':'HARD_FAIL'}) as hourly:
                    result=export_physical_diagnostics(None,None,None,Path(tmp))
            hourly.assert_called_once_with(None,None,None,Path(tmp),enforce_qc=True)
            self.assertIn('network QC',result['master_error'])
            self.assertEqual(result['operational_status'],'HARD_FAIL')
            self.assertFalse(result['accepted'])

    def test_no_solution_still_produces_snapshot_unavailability_record(self):
        with tempfile.TemporaryDirectory() as tmp, gp.Model() as model:
            model.Params.OutputFlag=0
            x=model.addVar(lb=0,obj=1)
            model.addConstr(x>=1)
            model.update()
            self.assertEqual(model.SolCount,0)
            snapshot=preserve_diagnostic_vectors(model,Path(tmp))
            self.assertEqual(snapshot['status'],'PARTIAL')
            self.assertIn('BarX',snapshot['unavailable'])
            self.assertFalse((Path(tmp)/'solution.npy').exists())

    def test_barrier_vectors_are_saved_without_crossover_or_basis(self):
        with tempfile.TemporaryDirectory() as tmp, gp.Model() as model:
            model.Params.OutputFlag=0
            model.Params.Method=2
            model.Params.Crossover=0
            model.Params.Presolve=0
            x=model.addVar(lb=0,obj=1)
            y=model.addVar(lb=0,obj=2)
            model.addConstr(x+y>=1)
            model.optimize()
            snapshot=preserve_diagnostic_vectors(model,Path(tmp))
            self.assertEqual(snapshot['status'],'COMPLETE')
            self.assertTrue(snapshot['attributes']['BarX']['finite'])
            self.assertFalse(snapshot['scientifically_accepted'])
            self.assertEqual((Path(tmp)/'solution.npy').read_bytes(),
                             (Path(tmp)/'solution_snapshot/X.npy').read_bytes())


if __name__=='__main__':
    unittest.main()
