"""Read only small continuation records and verify copied source identity."""
from pathlib import Path
import hashlib
import json
import subprocess
from deploy import HERE, HEADER

FILES = ['source_identity.json','release_files.sha256','preflight/preflight_report.json',
         'preflight/run_scope.json','preflight/model_config_snapshot.json','preflight/input_manifest.csv',
         'validation_2040.json','validation_2040.err','submission_test.json','held_submission.json','release_job.json',
         'compute_node_smoke.json','runtime_slurm_job.txt','continuation_contract_check.json','startup_regression.log',
         'output_8760/run_scope.json','output_8760/preflight_report.json','output_8760/model_config_snapshot.json',
         'output_8760/gurobi.log','batch_exit.json','stderr.log']
FILES += ['inherited_vre_audit.json','inherited_vre_violations.csv',
          'upstream_2030_bound_closed/bound_closure_audit.json',
          'upstream_2030_bound_closed/planning_state_candidate/state_metadata.json',
          'upstream_2030_bound_closed/result_manifest.json',
          'preflight_bound_closed/preflight_report.json','preflight_bound_closed/run_scope.json',
          'preflight_bound_closed/model_config_snapshot.json','preflight_bound_closed/input_manifest.csv']

def main():
    code = HEADER+'files='+repr(FILES)+'\n'+'''
records={rel:(root/rel).read_text() for rel in files if (root/rel).is_file()}
checked=0
mismatches=[]
for path in sorted((source/'repo').rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc': continue
    counterpart=root/'repo'/path.relative_to(source/'repo')
    checked+=1
    if not counterpart.is_file() or hashlib.sha256(path.read_bytes()).digest()!=hashlib.sha256(counterpart.read_bytes()).digest():
        mismatches.append(str(path.relative_to(source/'repo')))
audit=dict(status='PASS' if not mismatches else 'FAIL', original_repo_files_checked=checked, mismatches=mismatches,
           data_overlay_target=str((root/'data_overlay').resolve()))
print(json.dumps(dict(records=records,source_audit=audit),ensure_ascii=False))
'''
    p=subprocess.run(['ssh','-o','BatchMode=yes','paracloud-bscc-a8','python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=90)
    p.check_returncode()
    payload=json.loads(p.stdout)
    for rel, content in payload['records'].items():
        (HERE/'evidence'/rel.replace('/','__')).write_text(content,encoding='utf-8')
    (HERE/'source_audit.json').write_text(json.dumps(payload['source_audit'],indent=2),encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'evidence').glob('*')) if p.is_file()}
    (HERE/'evidence_sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(payload['source_audit'],indent=2))
    print('Small records collected:',len(payload['records']))

if __name__=='__main__': main()
