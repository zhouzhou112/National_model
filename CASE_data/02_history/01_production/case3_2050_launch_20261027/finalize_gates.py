"""Audit new framework-A 2050 gates; never reuse framework-C gate receipts."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from cispo_model.factor_screen import mps_section_sha256


def main():
    target=HERE/'FINAL_GATES_PASSED.json'
    assert not target.exists()
    names=['screen_1h_v1','unscreen_1h_v1','gate_24h_v1']
    checks={};evidence={};audits={};sections={}
    for name in names:
        out=HERE/name;gate=json.loads((out/'continuation_gate.json').read_text())
        checks[name+'.runner']=gate['runner_exit_code']==0
        checks[name+'.parameters']=gate['parameters']=='PASS'
        checks[name+'.tiny_width']=not gate['tiny_capacity_columns']
        audit=json.loads((out/'build_report.json').read_text())['numerical_robustness_audit']
        audits[name]=audit
        allowed={'retrofit_upper_cleanup','hydro_capacity_headroom_cleanup','other_capacity_headroom_cleanup','capacity_rhs_cleanup'}
        checks[name+'.whitelist']=set(audit)<=allowed
        for label in ['retrofit_upper_cleanup','hydro_capacity_headroom_cleanup']:
            items=audit.get(label,[]);items=[items] if isinstance(items,dict) else items
            checks[name+'.'+label]=all(x['cutoff_gw']==1e-5 and all(0<=v<=1e-5 for v in x['removed_gw']) for x in items)
        checks[name+'.rhs']=all(x['cleaned_rhs']==0 and abs(x['original_rhs'])<1e-12 and x['reason']=='OPPOSITE_SIGN_CAPACITY_CANCELLATION_ROUNDOFF' for x in audit.get('capacity_rhs_cleanup',[]))
        checks[name+'.other']=all(x['cutoff']==1e-5 and x['unit'] in ['GW','GWh'] and x['closed_upper']==x['inherited_lower'] for x in audit.get('other_capacity_headroom_cleanup',[]))
        if gate['hours']==1:
            sections[name]=mps_section_sha256(out/'model_archive/original.mps')
        else:
            checks['optimal']=gate['status_code']==2
            checks['service_M']=gate['M']<=1e-3
            checks['credit']=all(v<=1e-3 for v in gate['credit'].values())
            checks['relative_v1']=gate['solution_qc.json']['acceptance_profiles']['relative_v1']['status']=='PASS'
            pres=gate['preservation_report.json']
            checks['preservation']=pres['status']=='COMPLETE' and not pres['errors'] and pres['original_model_archived'] and pres['stages']['raw_checkpoint']=='COMPLETE' and pres['stages']['candidate_selection']=='COMPLETE'
        for n in ['continuation_gate.json','parameter_verification.json','input_manifest.csv','model_config_snapshot.json','model_archive/archive_manifest.json']:
            evidence[str((out/n).relative_to(ROOT))]=hashlib.sha256((out/n).read_bytes()).hexdigest()
    a,b=(sections[n] for n in names[:2])
    different=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
    checks['only_screened_new_bounds']=different==['BOUNDS_VRE_NEW']
    checks['R1']=json.loads((HERE/'R1_v2/evidence/cleanup_gate.json').read_text())['status']=='PASS'
    paths=subprocess.check_output(['git','ls-files','cispo_model','config','scripts','tests'],cwd=ROOT,text=True).splitlines()
    # New focused tests are included before their first commit as well.
    paths+=['tests/test_relative_acceptance_mt.py']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sorted(set(paths)) if (ROOT/p).is_file()}
    result=dict(status='PASS' if all(checks.values()) else 'FAIL',framework='A',planning_year=2050,
                checks=checks,different_segments=different,mps_sections=sections,
                tested_source_lf_sha256=hashes,evidence_sha256=evidence,cleanup_audits=audits,
                result_use='TEST_ONLY_TRUNCATED_HORIZON')
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'],{k:v for k,v in checks.items() if not v})
    if result['status']!='PASS':raise SystemExit(2)


if __name__=='__main__':main()
