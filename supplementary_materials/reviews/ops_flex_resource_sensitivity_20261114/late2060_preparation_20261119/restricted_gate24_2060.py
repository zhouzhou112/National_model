"""Actual restricted LATE-Open2060 24h engineering gate; no annual solve."""
from pathlib import Path
from unittest.mock import patch
import argparse,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state',type=Path,required=True);ap.add_argument('--selection',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert not out.exists()
    profile=json.loads((ROOT/'config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json').read_text())
    profile.update(profile_id='lateopen2060_engineering_cross2_1e8_threads44',direct_nonbasic_scientific_acceptance=False)
    profile['numerics'].update(threads=44,crossover=2,solution_target=0,barrier_convergence_tolerance=1e-8,feasibility_tolerance=1e-9,optimality_tolerance=1e-9,time_limit_seconds=3600,soft_mem_limit_gb=24)
    profilepath=out.parent/(out.name+'_profile.json');profilepath.write_text(json.dumps(profile,indent=2)+'\n')
    from scripts import run_cispo_2030_full_year as runner
    import cispo_model.monolithic as monolithic
    from cispo_model.frozen_capacity import investment_registry
    from cispo_model.factor_screen import mps_section_sha256
    from resource_audit_batch2 import audit_resource_parameters
    original=monolithic.build_full_year_monolithic;captured={}
    def capture(config,data,**kw):
        art=original(config,data,**kw);art.model.update()
        preserved={k:(np.asarray(art.variables[k].LB).copy(),np.asarray(art.variables[k].UB).copy()) for k,*_ in investment_registry(art,data) if k not in {'vre_new','spur_augmentation'}}
        before=out.parent/(out.name+'_unrestricted.mps');art.model.write(str(before))
        captured.update(art=art,data=data,config=config,preserved=preserved,before=before)
        return art
    args=['runner','--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json'),'--solver-config',str(profilepath),'--scenario-config',str(ROOT/'config/scenarios/ops_open_resource_v1.json'),'--planning-year','2060','--state-in',str(a.state),'--allow-candidate-state-in','--capacity-bound-selection',str(a.selection),'--diagnostic-hours','24','--archive-original-model','--output-dir',str(out)]
    code=0
    with patch.object(sys,'argv',args),patch.object(monolithic,'build_full_year_monolithic',capture):
        try:runner.main()
        except SystemExit as e:code=e.code
    if not captured:raise RuntimeError('Stopped before construction')
    art=captured['art'];audit=audit_resource_parameters(captured['config'],captured['data'],art,2060,'open')
    manifest=json.loads((out/'model_archive/archive_manifest.json').read_text());after=out/'model_archive'/next(x['path'] for x in manifest['files'] if x['path'].startswith('original.mps'))
    before_sections=mps_section_sha256(captured['before']);after_sections=mps_section_sha256(after)
    matrix_equal={k:v for k,v in before_sections.items() if not k.startswith('BOUNDS')}=={k:v for k,v in after_sections.items() if not k.startswith('BOUNDS')}
    other_bounds={k:bool(np.array_equal(art.variables[k].LB,v[0]) and np.array_equal(art.variables[k].UB,v[1])) for k,v in captured['preserved'].items()}
    selection=json.loads((out/'capacity_bound_selection_audit.json').read_text())
    qc=json.loads((out/'solution_qc.json').read_text());solve=json.loads((out/'solve_report.json').read_text());pres=json.loads((out/'preservation_report.json').read_text())
    quality_ok=qc['acceptance_profiles']['relative_v1']['status']=='PASS' and solve['solution_contract']['acceptance_status']=='PASS' and pres['status']=='COMPLETE' and not pres['errors']
    candidate_exit=code==2 and bool(solve.get('upstream_candidate_state')) and quality_ok and not any((out/f).exists() for f in ['semantic_export_error.json','finalization_error.json','barrier_checkpoint_error.json'])
    solver_ok=solve['status']=='OPTIMAL' and quality_ok and (code==0 or candidate_exit)
    report=dict(status='PASS' if solver_ok and audit['status']=='PASS' and matrix_equal and all(other_bounds.values()) else 'STOP',runner_exit_code=code,quality_ok=quality_ok,candidate_preservation_exit=candidate_exit,objective=solve['objective_value_million_cny'],resource_audit=audit,matrix_objective_rhs_and_senses_byte_identical=matrix_equal,other_investment_bounds_unchanged=other_bounds,selection_audit={k:v for k,v in selection.items() if k!='rows'},before_sections=before_sections,after_sections=after_sections)
    (out/'selection_build_gate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='resource_audit'}))
    if report['status']!='PASS':raise SystemExit(2)

if __name__=='__main__':main()
