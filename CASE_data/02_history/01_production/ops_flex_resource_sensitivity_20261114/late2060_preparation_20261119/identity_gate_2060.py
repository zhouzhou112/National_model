"""24h central-resource LATE identity gate; never an annual solve or release.

The identity probe fixes only numerically active bounds (1e-9 GW), distinct
from the documented 10 MW three-production-case classification heuristic.
"""
from pathlib import Path
from unittest.mock import patch
import argparse,gzip,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    work=a.output.resolve();work.mkdir(parents=True,exist_ok=False)
    profile=json.loads((ROOT/'config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json').read_text())
    profile.update(profile_id='resource_identity_cross2_1e8_threads44',direct_nonbasic_scientific_acceptance=False)
    profile['numerics'].update(threads=44,crossover=2,solution_target=0,barrier_convergence_tolerance=1e-8,feasibility_tolerance=1e-9,optimality_tolerance=1e-9,time_limit_seconds=3600,soft_mem_limit_gb=24)
    save(work/'identity_profile.json',profile)
    from scripts import run_cispo_2030_full_year as runner
    import cispo_model.monolithic as monolithic
    original=monolithic.build_full_year_monolithic
    keys=['vre_capacity','vre_new','thermal_capacity','thermal_new','thermal_retrofit_to_ccs','storage_capacity','storage_new','phs_energy_capacity','line_capacity','line_new','intra_load_center_capacity','intra_load_center_new','hydro_capacity','hydro_new','wave_capacity','wave_new','dac_capacity','dac_new','spur_augmentation','hydro_spur_augmentation','trunk_augmentation']
    results={};values={}
    for name,selection in [('unrestricted',None),('fixed_from_own_solution',work/'own_solution_selection.json')]:
        captured={}
        def capture(config,data,**kw):
            art=original(config,data,**kw);captured.update(art=art,data=data);return art
        argv=['runner','--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json'),'--scenario-config',str(ROOT/'config/scenarios/case3_thermal_ev_v5.json'),'--solver-config',str(work/'identity_profile.json'),'--planning-year','2060','--state-in',str(a.state.resolve()),'--allow-candidate-state-in','--diagnostic-hours','24','--archive-original-model','--output-dir',str(work/name)]
        if selection is not None:argv+=['--capacity-bound-selection',str(selection)]
        save(work/(name+'_command.json'),argv)
        code=0
        with patch.object(sys,'argv',argv),patch.object(monolithic,'build_full_year_monolithic',capture):
            try:runner.main()
            except SystemExit as e:code=e.code
        if not captured:raise RuntimeError('Identity gate stopped before model construction')
        art=captured['art'];m=art.model
        results[name]=dict(exit_code=code,status=int(m.Status),solution_count=int(m.SolCount),variables=int(m.NumVars),constraints=int(m.NumConstrs))
        solve=json.loads((work/name/'solve_report.json').read_text())
        qc=json.loads((work/name/'solution_qc.json').read_text())
        preserved=json.loads((work/name/'preservation_report.json').read_text())
        quality_ok=(qc['acceptance_profiles']['relative_v1']['status']=='PASS' and solve['solution_contract']['acceptance_status']=='PASS' and preserved['status']=='COMPLETE' and not preserved['errors'])
        # The unchanged legacy runner intentionally exits 2 for an unpromoted
        # candidate upstream even when this engineering solve/QC is complete.
        candidate_preservation_exit=(code==2 and bool(solve.get('upstream_candidate_state')) and quality_ok and not any((work/name/f).exists() for f in ['semantic_export_error.json','finalization_error.json','barrier_checkpoint_error.json']))
        results[name].update(relative_qc=qc['acceptance_profiles']['relative_v1']['status'],complete_preservation=preserved['status'],candidate_preservation_exit=candidate_preservation_exit)
        if (code and not candidate_preservation_exit) or m.Status!=2 or not m.SolCount or not quality_ok:
            save(work/'identity_gate.json',dict(status='STOP',runs=results));raise SystemExit(2)
        results[name]['objective']=float(m.ObjVal)
        values[name]={k:np.asarray(art.variables[k].X).copy() for k in keys if k in art.variables}
        if selection is None:
            cap=art.variables['vre_capacity'];x=np.asarray(cap.X);lo=np.asarray(cap.LB);up=np.asarray(cap.UB)
            state=np.full(len(x),'free',dtype=object);state[np.abs(x-up)<=1e-9]='upper';state[np.abs(x-lo)<=1e-9]='lower'
            sites=captured['data'].vre_sites
            payload=dict(schema_version='capacity_bound_selection_v1',planning_year=2060,mode='vre_boundary_states',source_references=dict(scope='24h entry identity only; exact active bounds, not production 10MW heuristic',active_bound_tolerance_gw=1e-9,source_result_manifest_sha256=hashlib.sha256((work/name/'result_manifest.json').read_bytes()).hexdigest()),columns=[dict(grid_uid=str(r.grid_uid),technology=str(r.technology),state=str(state[i])) for i,r in enumerate(sites.itertuples(index=False))])
            save(work/'own_solution_selection.json',payload);results[name]['state_counts']={s:int((state==s).sum()) for s in ['lower','upper','free']}
        m.dispose()
    left,right=results['unrestricted']['objective'],results['fixed_from_own_solution']['objective']
    difference=abs(left-right)/max(abs(left),1.)
    caps={k:float(np.max(np.abs(values['unrestricted'][k]-values['fixed_from_own_solution'][k]),initial=0.)) for k in values['unrestricted']}
    report=dict(status='PASS' if difference<=1e-7 and all(v<=1e-9 for v in caps.values()) else 'STOP_IDENTITY_GATE',runs=results,relative_objective_difference=difference,objective_tolerance=1e-7,maximum_capacity_difference_by_family=caps,capacity_tolerance=1e-9,scope='TEST_ONLY_TRUNCATED_HORIZON',no_original_model_or_input_changed=True)
    save(work/'identity_gate.json',report);print(json.dumps(report))
    if report['status']!='PASS':raise SystemExit(2)

if __name__=='__main__':main()
