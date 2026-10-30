"""Finalize the C2060 R1, 1h identity and 24h engineering evidence on T550."""
from pathlib import Path
import argparse,hashlib,json,sys


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--commit',required=True);a=p.parse_args()
    work=a.work;root=work.parents[2];sys.path.insert(0,str(root))
    from cispo_model.factor_screen import mps_section_sha256
    target=work/'FINAL_GATES_PASSED.json';assert not target.exists()
    checks={};evidence={};audits={};sections={}
    for name in ['screen_1h','unscreen_1h','gate_24h']:
        out=work/name;gate=json.loads((out/'continuation_gate.json').read_text())
        checks[name+'.runner']=gate['runner_exit_code']==0
        checks[name+'.parameters']=gate['parameters']=='PASS' and gate['year']==2060
        checks[name+'.tiny_width']=not gate['tiny_capacity_columns']
        audit=json.loads((out/'build_report.json').read_text())['numerical_robustness_audit'];audits[name]=audit
        allowed={'retrofit_upper_cleanup','hydro_capacity_headroom_cleanup','other_capacity_headroom_cleanup','capacity_rhs_cleanup'}
        checks[name+'.whitelist']=set(audit)<=allowed
        for label in ['retrofit_upper_cleanup','hydro_capacity_headroom_cleanup']:
            items=audit.get(label,[]);items=[items] if isinstance(items,dict) else items
            checks[name+'.'+label]=all(x['cutoff_gw']==1e-5 and all(0<=v<=1e-5 for v in x['removed_gw']) for x in items)
        checks[name+'.rhs']=all(x['cleaned_rhs']==0 and abs(x['original_rhs'])<1e-12 and x['reason']=='OPPOSITE_SIGN_CAPACITY_CANCELLATION_ROUNDOFF' for x in audit.get('capacity_rhs_cleanup',[]))
        checks[name+'.other']=all(x['cutoff']==1e-5 and x['unit'] in ['GW','GWh'] and x['closed_upper']==x['inherited_lower'] for x in audit.get('other_capacity_headroom_cleanup',[]))
        if gate['hours']==1:
            archived=json.loads((out/'model_archive/archive_manifest.json').read_text())
            originals=[x for x in archived['files'] if x['path'] in ['original.mps','original.mps.gz']]
            assert len(originals)==1
            model_path=out/'model_archive'/originals[0]['path']
            assert hashlib.sha256(model_path.read_bytes()).hexdigest()==originals[0]['sha256']
            sections[name]=mps_section_sha256(model_path)
        else:
            checks['optimal']=gate['status_code']==2
            checks['service_M']=gate['M']<=1e-3
            checks['credit']=all(v<=1e-3 for v in gate['credit'].values())
            checks['relative_v1']=gate['solution_qc.json']['acceptance_profiles']['relative_v1']['status']=='PASS'
            pr=gate['preservation_report.json']
            checks['preservation']=pr['status']=='COMPLETE' and not pr['errors'] and pr['original_model_archived'] and pr['stages']['raw_checkpoint']=='COMPLETE' and pr['stages']['candidate_selection']=='COMPLETE'
        for n in ['continuation_gate.json','parameter_verification.json','input_manifest.csv','model_config_snapshot.json','model_archive/archive_manifest.json']:
            evidence[str((out/n).relative_to(root))]=hashlib.sha256((out/n).read_bytes()).hexdigest()
    before,after=sections['unscreen_1h'],sections['screen_1h']
    different=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
    checks['only_screened_new_bounds']=different==['BOUNDS_VRE_NEW']
    checks['R1']=json.loads((work/'R1_v1/evidence/cleanup_gate.json').read_text())['status']=='PASS'
    adoption=json.loads((work/'acceptance_author_20261030.json').read_text())
    checks['upstream_accepted']=adoption['status']=='PASS' and all(adoption['conditions'].values())
    hashes=json.loads((work/'tested_source_lf_sha256.json').read_text())
    for name,digest in hashes.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    result=dict(status='PASS' if all(checks.values()) else 'FAIL',framework='C',planning_year=2060,
                source_commit=a.commit,checks=checks,different_segments=different,mps_sections=sections,
                tested_source_lf_sha256=hashes,evidence_sha256=evidence,cleanup_audits=audits,
                result_use='TEST_ONLY_TRUNCATED_HORIZON')
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],failed={k:v for k,v in checks.items() if not v})))
    if result['status']!='PASS':raise SystemExit(2)


if __name__=='__main__':main()
