"""Actual proposed LATE-Open selection: 1h bounds-only and resource gate."""
from pathlib import Path
from unittest.mock import patch
import argparse,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state',type=Path,required=True);ap.add_argument('--selection',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert not out.exists()
    from scripts import run_cispo_2030_full_year as runner
    import cispo_model.monolithic as monolithic
    from cispo_model.frozen_capacity import investment_registry
    from cispo_model.factor_screen import mps_section_sha256
    from resource_audit_v2 import audit_resource_parameters
    original=monolithic.build_full_year_monolithic;captured={}
    def capture(config,data,**kw):
        art=original(config,data,**kw);art.model.update()
        preserved={k:(np.asarray(art.variables[k].LB).copy(),np.asarray(art.variables[k].UB).copy()) for k,*_ in investment_registry(art,data) if k not in {'vre_new','spur_augmentation'}}
        before=out.parent/(out.name+'_unrestricted.mps');art.model.write(str(before))
        captured.update(art=art,data=data,config=config,preserved=preserved,before=before)
        return art
    args=['runner','--config',str(ROOT/'config/optimization_numeric_dac_by_year_v9_a12.json'),'--solver-config',str(ROOT/'config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json'),'--scenario-config',str(ROOT/'config/scenarios/ops_open_resource_v1.json'),'--planning-year','2050','--state-in',str(a.state),'--allow-candidate-state-in','--late-entry-base-state','--capacity-bound-selection',str(a.selection),'--diagnostic-hours','1','--build-only','--archive-original-model','--output-dir',str(out)]
    code=0
    with patch.object(sys,'argv',args),patch.object(monolithic,'build_full_year_monolithic',capture):
        try:runner.main()
        except SystemExit as e:code=e.code
    if not captured:raise RuntimeError('Stopped before construction')
    art=captured['art'];audit=audit_resource_parameters(captured['config'],captured['data'],art,2050,'open')
    manifest=json.loads((out/'model_archive/archive_manifest.json').read_text());after=out/'model_archive'/next(x['path'] for x in manifest['files'] if x['path'].startswith('original.mps'))
    before_sections=mps_section_sha256(captured['before']);after_sections=mps_section_sha256(after)
    matrix_equal={k:v for k,v in before_sections.items() if not k.startswith('BOUNDS')}=={k:v for k,v in after_sections.items() if not k.startswith('BOUNDS')}
    other_bounds={k:bool(np.array_equal(art.variables[k].LB,v[0]) and np.array_equal(art.variables[k].UB,v[1])) for k,v in captured['preserved'].items()}
    selection=json.loads((out/'capacity_bound_selection_audit.json').read_text())
    report=dict(status='PASS' if code==0 and audit['status']=='PASS' and matrix_equal and all(other_bounds.values()) else 'STOP',runner_exit_code=code,resource_audit=audit,matrix_objective_rhs_and_senses_byte_identical=matrix_equal,other_investment_bounds_unchanged=other_bounds,selection_audit={k:v for k,v in selection.items() if k!='rows'},before_sections=before_sections,after_sections=after_sections)
    (out/'selection_build_gate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='resource_audit'}))
    if report['status']!='PASS':raise SystemExit(2)

if __name__=='__main__':main()
