"""Serial real-runner A/C 1h builds and B identity/parameter entry fixture.

A/C use the actual national model builder with one chronological hour; neither
calls optimize. B substitutes only the builder with two actual Gurobi rows.
The real CLI, input loader, parameter application and report writer still run.
"""
from pathlib import Path
import copy
import json
import os
import runpy
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))


def main():
    env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(ROOT/'data'),CISPO_WAVE_ROOT=str(ROOT.parent/'wave_energy'),PYTHONUTF8='1')
    os.environ.update(env)
    base=json.loads((ROOT/'config/optimization_numeric_dac_by_year_v9.json').read_text())
    a=copy.deepcopy(base);a['numerics'].update(hydro_capacity_headroom_zero_gw=1e-6,retrofit_upper_zero_gw=1e-6,inherited_floor_overrun_clip_gw=0.)
    a_path=HERE/'runner_A_config.json';a_path.write_text(json.dumps(a,indent=2)+'\n')
    solver=json.loads((ROOT/'config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json').read_text())
    solver.update(profile_id='numerical_robustness_build_only_audit_v1',direct_nonbasic_scientific_acceptance=False,
        description='TEST_ONLY audit: actual one-hour build, no optimize or scientific acceptance')
    solver['numerics'].update(threads=8,soft_mem_limit_gb=8)
    solver_path=HERE/'runner_build_solver.json';solver_path.write_text(json.dumps(solver,indent=2)+'\n')
    common=['--solver-config',str(solver_path),'--diagnostic-hours','1','--diagnostic-start-hour','2880',
            '--build-only','--archive-original-model','--engineering-barrier-checkpoint-only']
    cases=[('real_runner_A1h',['--config',str(a_path),'--planning-year','2040','--state-in',
            str(HERE/'upstream_2030_bound_closed/planning_state_candidate'),'--allow-candidate-state-in'],
            'numerical_robustness_audit'),
           ('real_runner_C1h',['--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9.json'),
            '--formulation-config',str(ROOT/'config/formulation_profiles/annual_dense_row_split_v1.json')],
            'annual_dense_row_split')]
    only_b='--only-b' in sys.argv
    results=json.loads((HERE/'real_runner_entry_audit.json').read_text()) if only_b else []
    for name,args,key in ([] if only_b else cases):
        out=HERE/name
        if out.exists():raise FileExistsError(out)
        command=[sys.executable,str(ROOT/'scripts/run_cispo_2030_full_year.py'),*common,*args,'--output-dir',str(out)]
        with (HERE/(name+'.console.log')).open('w',encoding='utf-8') as log:
            completed=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if completed.returncode:raise RuntimeError(f'{name} exited {completed.returncode}')
        report=json.loads((out/'build_report.json').read_text())
        assert report[key] and report['optimization_hours']==1
        assert not (out/'solve_report.json').exists() and not (out/'planning_state').exists()
        results.append(dict(case=name,command=command,actual_national_builder=True,optimize_called=False,
                            audit_key=key,audit=report[key],statistics=report['statistics']))
        (HERE/'real_runner_entry_audit.json').write_text(json.dumps(results,indent=2)+'\n')
    from cispo_model.config import load_model_config
    from scripts import run_cispo_2030_full_year as runner
    import gurobipy as gp
    profile=ROOT/'config/solver_profiles/barrier_stagea_homogeneous_v1_threads48.json'
    cfg=load_model_config(ROOT/'config/optimization_numeric_dac_by_year_v9.json',solver_path=profile)
    out=HERE/('real_runner_B_fixture_v2' if only_b else 'real_runner_B_fixture')
    if out.exists():raise FileExistsError(out)
    annual_row_fixture=runpy.run_path(str(ROOT/'tests/test_numeric_repaired_formal_launch.py'))['annual_row_fixture']
    with gp.Model() as model, (HERE/(out.name+'.console.log')).open('w',encoding='utf-8') as log:
        model.Params.OutputFlag=0
        art=SimpleNamespace(model=model,index={'annual_capacity_link_row_scaling':annual_row_fixture(model,cfg)})
        args=['runner','--config',str(cfg.path),'--solver-config',str(profile),'--diagnostic-hours','1',
              '--build-only','--archive-original-model','--engineering-barrier-checkpoint-only','--output-dir',str(out)]
        with patch('sys.argv',args),patch('cispo_model.monolithic.build_full_year_monolithic',return_value=art),redirect_stdout(log):
            runner.main()
        params={key:getattr(model.Params,key) for key in ['Method','Threads','BarHomogeneous','Crossover','SolutionTarget','BarConvTol','NumericFocus','ScaleFlag','Presolve','Aggregate']}
        (out/'actual_parameter_readback.json').write_text(json.dumps(params,indent=2)+'\n')
        report=json.loads((out/'build_report.json').read_text())
        assert params['BarHomogeneous']==1 and not cfg.raw['solver_profile']['direct_nonbasic_scientific_acceptance']
        assert not (out/'solve_report.json').exists()
        assert 'numerical_robustness_audit' not in report and 'annual_dense_row_split' not in report
        results.append(dict(case=out.name,mock_scope='Only builder replaced with 2 actual Gurobi annual rows',
            optimize_called=False,direct_scientific_acceptance=False,parameters=params))
    (HERE/'real_runner_entry_audit.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS',[(r['case'],r['optimize_called']) for r in results])


if __name__=='__main__':main()
