"""Single bounded Base-frozen engineering gate; always uses a fresh output.

Run with the existing Gurobi 13 Python overlay and CISPO_WAVE_ROOT. No scheduler.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['old-default','default','frozen','zero','base-control'],required=True)
    parser.add_argument('--hours',type=int,choices=[1,24],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--baseline-runner',type=Path,help='Read-only db1a7b4 runner reference for a non-Git validation copy')
    parser.add_argument('--saved-source',type=Path,help='Build only; evaluate preserved X costs without optimizing or modifying source')
    parser.add_argument('--year',type=int,choices=[2030,2040,2050,2060],default=2030)
    parser.add_argument('--source-release',type=Path,help='Verified Base release with original packaged upstream')
    parser.add_argument('--supplement',type=Path,help='Verified hydro-spur sidecar outside source output')
    parser.add_argument('--closure',type=Path,help='Explicit source-bound static closure payload')
    parser.add_argument('--window-carbon-budget',type=Path)
    args=parser.parse_args()
    if args.window_carbon_budget and (args.hours!=24 or args.mode not in {'base-control','zero','frozen'}):parser.error('Budget only for 24h frozen gates')
    out=args.output.resolve()
    if out.exists():raise FileExistsError(out)
    profile=json.loads((ROOT/'config/solver_profiles/barrier_stagea_base_frozen_agg0_v1_threads48.json').read_text())
    profile.update(profile_id='base_frozen_identity_cross2_1e8',direct_nonbasic_scientific_acceptance=False)
    profile['numerics'].update(threads=8,crossover=2,solution_target=0,barrier_convergence_tolerance=1e-8,
                               feasibility_tolerance=1e-9,optimality_tolerance=1e-9,time_limit_seconds=3600,
                               soft_mem_limit_gb=24)
    profilepath=out.parent/(out.name+'_profile.json');save(profilepath,profile)
    config_name='optimization_numeric_dac_by_year_v9.json' if args.year==2030 else 'optimization_numeric_dac_by_year_v9_a12.json'
    argv=['runner','--config',str(ROOT/'config'/config_name),
          '--solver-config',str(profilepath),'--planning-year',str(args.year),'--diagnostic-hours',str(args.hours),
          '--archive-original-model','--output-dir',str(out)]
    if args.mode!='base-control':argv+=['--scenario-config',str(ROOT/'config/scenarios/case3_thermal_ev_v5.json')]
    if args.hours==1 or args.saved_source:argv+=['--build-only']
    frozen=args.mode in {'frozen','zero','base-control'}
    if frozen:
        if args.year!=2030 and (args.source_release is None or args.supplement is None):
            parser.error('Later years require explicit Base release and supplement')
        source=args.source_release or HERE/'source_base/20260914_base_v9_t48_m750_tol1e4_v3'
        supplement=args.supplement or source/'frozen_capacity_B_20261026'
        argv+=['--frozen-capacity-from',str(source/'output_8760'),'--frozen-capacity-supplement',str(supplement)]
        if args.closure:argv+=['--frozen-capacity-closure',str(args.closure)]
    if args.mode=='zero':
        override=out.parent/(out.name+'_override.json')
        save(override,dict(contract_upper_fraction={key:0 for key in ['heating','cooling','ev_v1g','ev_v2g']}))
        argv+=['--frozen-parameters',str(override)]
    save(out.parent/(out.name+'_command.json'),argv)
    if args.mode=='old-default':
        baseline=out.parent/(out.name+'_baseline_runner.py')
        baseline.write_bytes(args.baseline_runner.read_bytes() if args.baseline_runner else subprocess.check_output(['git','show','db1a7b4:scripts/run_cispo_2030_full_year.py'],cwd=ROOT))
        spec=importlib.util.spec_from_file_location('base_frozen_old_runner',baseline)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    else:
        from scripts import run_cispo_2030_full_year as runner
    import cispo_model.monolithic as monolithic
    original=monolithic.build_full_year_monolithic
    captured={}
    def capture(config,data,**kw):
        art=original(config,data,**kw)
        if args.window_carbon_budget:
            from window_gate import apply_window_budget
            apply_window_budget(art,args.window_carbon_budget,source/'output_8760',args.year,args.hours,out)
        captured.update(art=art,data=data,config=config);return art
    code=0
    with patch.object(sys,'argv',argv),patch.object(monolithic,'build_full_year_monolithic',capture):
        try:runner.main()
        except SystemExit as exc:code=exc.code
    if not captured:raise RuntimeError('Gate stopped before build; retained evidence')
    art=captured['art'];model=art.model
    result=dict(mode=args.mode,planning_year=args.year,hours=args.hours,runner_exit_code=code,variables=model.NumVars,constraints=model.NumConstrs,
                result_use='TEST_ONLY_TRUNCATED_HORIZON')
    if frozen:
        from cispo_model.frozen_capacity import investment_registry
        result['investment_fixed']={key:bool(np.array_equal(art.variables[key].LB,art.variables[key].UB))
                                    for key,*_ in investment_registry(art,captured['data'])}
        result['all_investment_families_fixed']=all(result['investment_fixed'].values())
    if args.mode=='frozen' and args.year>=2040:
        spec=importlib.util.spec_from_file_location('continuation_parameters',ROOT/'supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py')
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        parameter_check=checker.parameters(captured['config'],captured['data'],model,args.year)
        save(out/'parameter_verification.json',parameter_check)
        result['parameters']=parameter_check['status']
        if result['parameters']!='PASS':code=2
    if args.hours==24 and model.SolCount:
        result.update(status=int(model.Status),objective=float(model.ObjVal),barrier_iterations=int(model.BarIterCount),runtime_seconds=float(model.Runtime))
        # Preserve named values for independent shared operational-variable comparison.
        variables=model.getVars()
        with (out/'gate_values.jsonl').open('x',encoding='utf-8') as f:
            for start in range(0,len(variables),50000):
                block=variables[start:start+50000]
                for name,value in zip(model.getAttr('VarName',block),model.getAttr('X',block)):
                    f.write(json.dumps([name,value])+'\n')
        if args.year>=2040 and args.mode in {'base-control','zero'}:
            from cispo_model.offline_solution import offline_artifacts
            from cispo_model.master import export_cost_components
            costroot=out.parent/(out.name+'_Xcost')
            costroot.mkdir(exist_ok=False)
            export_cost_components(offline_artifacts(art,np.asarray(model.X),None),costroot/'cost_from_X')
            save(costroot/'identity.json',dict(attribute='X',source=str(out/'solution_snapshot'),optimized_again=False))
    if args.saved_source:
        from cispo_model.offline_solution import read_snapshot,offline_artifacts
        from cispo_model.master import export_cost_components
        from cispo_model.frozen_capacity import digest
        source=args.saved_source/'solution_snapshot'
        read_snapshot(model,source,expected_row_scaling_registry=art.index.get('annual_capacity_link_row_scaling'))
        manifest=json.loads((source/'snapshot_manifest.json').read_text())
        record=manifest['attributes']['X'];vector=source/record['path']
        assert digest(vector)==record['sha256'] and vector.stat().st_size==record['bytes']
        x=np.load(vector,allow_pickle=False)
        export_cost_components(offline_artifacts(art,x,None),out/'cost_from_X')
        result.update(evaluated_attribute='X',vector_sha256=digest(vector),optimized=False)
    save(out/'identity_gate_probe.json',result)
    print(json.dumps(result,indent=2))
    if code:raise SystemExit(code)


if __name__=='__main__':main()
