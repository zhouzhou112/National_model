"""Prepare, validate and launch the authorized 2050 continuation.

Usage: python deploy.py inspect|prepare|close-state|audit|preflight|validate|submit|release|status|collect
Paths/settings are in launch_config.json. Mutating phases are explicit and guarded;
submit creates a held job, and release verifies its resource contract first.
"""
from pathlib import Path
import datetime
import importlib.util
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CFG=json.loads((HERE/'launch_config.json').read_text())
REMOTE=CFG['remote_base']+'/'+CFG['release']
SOURCE=CFG['remote_base']+'/'+CFG['source_release']
ENV_SOURCE=CFG['remote_base']+'/'+CFG['environment_release']
STATE=REMOTE+'/upstream_2040_bound_closed/planning_state_candidate'
PROFILE=CFG['profile']
spec=importlib.util.spec_from_file_location('previous_continuation',HERE.parent/'base_2040_continuation_20260919/deploy.py')
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
ENV=previous.ENV
HEADER='from pathlib import Path\nimport json,subprocess,hashlib,shutil,os,datetime,re\nroot=Path('+repr(REMOTE)+')\nsource=Path('+repr(SOURCE)+')\nenv_source=Path('+repr(ENV_SOURCE)+')\nsettings='+repr(CFG)+'\n'

def remote(code, label):
    compile(code,'<remote>','exec')
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20',CFG['ssh_host'],'python3 -'],
                        input=HEADER+code,capture_output=True,text=True,encoding='utf-8',timeout=1800)
    tag=label+'_'+datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    (HERE/(tag+'.stdout.log')).write_text(proc.stdout,encoding='utf-8')
    (HERE/(tag+'.stderr.log')).write_text(proc.stderr,encoding='utf-8')
    print(proc.stdout[-6500:])
    if proc.returncode:
        print(proc.stderr[-2500:])
    proc.check_returncode()
    return proc.stdout

def main():
    mode=sys.argv[1]
    if mode=='inspect':
        remote('''
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(source))
out=source/'output_8760'
solve=json.loads((out/'solve_report.json').read_text())
qc=json.loads((out/'solution_qc.json').read_text())
state=json.loads((out/'planning_state_candidate/state_metadata.json').read_text())
preservation=json.loads((out/'preservation_report.json').read_text())
assert solve['planning_year']==2040 and solve['status']=='OPTIMAL'
assert state['planning_year']==2040 and state['candidate_unaccepted'] and state['scientifically_accepted'] is False
assert preservation['status']=='COMPLETE' and not preservation['errors']
result=dict(source=str(source),target_exists=root.exists(),source_release_hash_check='PASS',
            solve_status=solve['status'],qc_status=qc['status'],cohort_rows=state['cohort_rows'],
            preservation_status=preservation['status'],parameters=solve['solver_parameters'],
            queue=subprocess.check_output(['squeue','-u','a8s001819'],universal_newlines=True))
print(json.dumps(result,indent=2))
''',mode)
    elif mode=='prepare':
        files={'repo/'+PROFILE:(REPO/PROFILE).read_text()}
        for name in ['base_2050.sbatch','validate_2050.py','audit_state_bounds.py','launch_config.json']:
            files[name]=(HERE/name).read_text()
        remote('files='+repr(files)+'\n'+'''
assert not root.exists(), 'Refuse to overwrite existing release'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(source))
root.mkdir()
shutil.copytree(source/'repo',root/'repo',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(root/'data_overlay').symlink_to(source/'data_overlay',target_is_directory=True)
for rel,content in files.items():
    path=root/rel
    assert not path.exists(),rel
    path.write_text(content)
checked=0
for old in sorted((source/'repo').rglob('*')):
    if not old.is_file() or '__pycache__' in old.parts or old.suffix=='.pyc': continue
    new=root/'repo'/old.relative_to(source/'repo')
    assert hashlib.sha256(old.read_bytes()).digest()==hashlib.sha256(new.read_bytes()).digest(),str(old)
    checked+=1
state=source/'output_8760/planning_state_candidate'
identity=dict(created_at=datetime.datetime.now().astimezone().isoformat(),predecessor_job=settings['predecessor_job'],
              predecessor_release=str(source),predecessor_state=str(state),authorization=settings['authorization'],
              state_acceptance='UNACCEPTED_CANDIDATE_RETAIN_UPSTREAM_QC',planning_year=2050,
              automatic_successor=False,production_model_code_changed=False,original_repo_files_sha_checked=checked,
              upstream_state_metadata_sha256=hashlib.sha256((state/'state_metadata.json').read_bytes()).hexdigest())
(root/'source_identity.json').write_text(json.dumps(identity,indent=2)+'\\n')
lines=[]
for path in sorted(root.rglob('*')):
    if path.is_file() and not path.is_symlink():
        lines.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(root)))
(root/'release_files.sha256').write_text('\\n'.join(lines)+'\\n')
subprocess.check_call(['bash','-n','base_2050.sbatch'],cwd=str(root))
print(json.dumps(identity,indent=2))
''',mode)
    elif mode=='close-state':
        bash=ENV.format(root=REMOTE,source=SOURCE,env_source=ENV_SOURCE)
        bash+='"$PYTHON" "'+REMOTE+'/prepare_bound_closed_state.py"\n'
        remote('content='+repr((HERE/'prepare_bound_closed_state.py').read_text())+'\nscript='+repr(bash)+'\n'+'''
assert not (root/'held_submission.json').exists()
assert not (root/'prepare_bound_closed_state.py').exists()
(root/'prepare_bound_closed_state.py').write_text(content)
p=subprocess.run(['bash'],input=script,universal_newlines=True)
assert p.returncode==0
manifest=root/'release_files.sha256'
lines=manifest.read_text().splitlines()
paths=list((root/'upstream_2040_bound_closed').rglob('*'))+[root/'prepare_bound_closed_state.py',root/'original_inherited_vre_audit.json',root/'original_inherited_vre_violations.csv']
for path in sorted(paths):
    if path.is_file(): lines.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+str(path.relative_to(root)))
manifest.write_text('\\n'.join(lines)+'\\n')
''',mode)
    elif mode in ('audit','preflight','validate'):
        bash=ENV.format(root=REMOTE,source=SOURCE,env_source=ENV_SOURCE)
        bash+='export UPSTREAM_STATE="'+STATE+'"\n'
        if mode=='preflight':
            command='"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --solver-config '+PROFILE+' --planning-year 2050 --horizon full_year --state-in "$UPSTREAM_STATE" --allow-candidate-state-in --engineering-barrier-checkpoint-only --preflight-only --output-dir "'+REMOTE+'/preflight"'
            result='preflight/preflight_report.json'
        else:
            command='"$PYTHON" "'+REMOTE+('/audit_state_bounds.py"' if mode=='audit' else '/validate_2050.py"')
            result='inherited_vre_audit.json' if mode=='audit' else 'validation_2050.json'
        bash+=command+' > "'+REMOTE+'/'+mode+'.log" 2> "'+REMOTE+'/'+mode+'.err"\n'
        remote('script='+repr(bash)+'\n'+'''
assert not (root/'held_submission.json').exists(), 'Prelaunch only'
p=subprocess.run(['bash'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
print(json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)))
'''+ 'path=root/'+repr(result)+'\nif path.exists(): print(path.read_text())\n'+
               'if p.returncode: print((root/'+repr(mode+'.err')+').read_text()[-3500:])\nraise SystemExit(p.returncode)\n',mode)
    elif mode=='submit':
        remote('''
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'validation_2050.json').read_text())['status']=='PASS'
assert json.loads((root/'inherited_vre_audit.json').read_text())['rows']==0
assert not (root/'held_submission.json').exists()
assert not (root/'submission_attempt.json').exists(), 'Review previous attempt; never submit twice blindly'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
exports='ALL,SOURCE_RELEASE='+str(env_source)+',UPSTREAM_STATE='+str(root/'upstream_2040_bound_closed/planning_state_candidate')
test=subprocess.run(['sbatch','--test-only','--export='+exports,'base_2050.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
(root/'submission_test.json').write_text(json.dumps(dict(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr),indent=2))
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(attempted_at=datetime.datetime.now().astimezone().isoformat())))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'base_2050.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
record=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,submitted_at=datetime.datetime.now().astimezone().isoformat())
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
assert p.returncode==0,record
job=p.stdout.strip().split(';')[0]
assert job.isdigit()
record['job_id']=job
record['scontrol']=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
(root/'held_submission.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
''',mode)
    elif mode=='release':
        remote('''
assert not (root/'release_job.json').exists()
job=json.loads((root/'held_submission.json').read_text())['job_id']
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record,record
tres=dict(x.split('=',1) for x in re.search(r'\\bReqTRES=(\\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['billing']=='64' and tres['mem']=='750G',tres
subprocess.check_call(['scontrol','release',job])
after=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
result=dict(job_id=job,released_at=datetime.datetime.now().astimezone().isoformat(),scontrol=after)
(root/'release_job.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
''',mode)
    elif mode in ('status','collect'):
        names=['source_identity.json','release_files.sha256','original_inherited_vre_audit.json','original_inherited_vre_violations.csv',
               'bound_closure_diagnosis.json','upstream_2040_bound_closed/bound_closure_audit.json',
               'upstream_2040_bound_closed/planning_state_candidate/state_metadata.json','upstream_2040_bound_closed/result_manifest.json',
               'preflight/preflight_report.json','preflight/run_scope.json',
               'preflight/input_manifest.csv','preflight/model_config_snapshot.json','inherited_vre_audit.json',
               'inherited_vre_violations.csv','validation_2050.json','held_submission.json','release_job.json',
               'submission_test.json','compute_node_smoke.json','runtime_slurm_job.txt','continuation_contract_check.json',
               'startup_regression.log','batch_exit.json','stderr.log','output_8760/run_scope.json',
               'output_8760/preflight_report.json','output_8760/build_report.json','output_8760/gurobi.log']
        code='names='+repr(names)+'\n'+'''
job=json.loads((root/'held_submission.json').read_text())['job_id'] if (root/'held_submission.json').exists() else None
result=dict(job_id=job,records={})
if job:
    result['scontrol']=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
for rel in names:
    p=root/rel
    if p.is_file(): result['records'][rel]=p.read_text()
print(json.dumps(result))
'''
        result=json.loads(remote(code,mode))
        if mode=='collect':
            import hashlib
            evidence=HERE/'evidence';evidence.mkdir(exist_ok=True)
            for rel,content in result['records'].items():
                (evidence/rel.replace('/','__')).write_text(content,encoding='utf-8',newline='\n')
            (evidence/'scheduler.json').write_text(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2),encoding='utf-8')
            hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(evidence.iterdir()) if p.is_file()}
            (HERE/'evidence_sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    else: raise SystemExit('Unknown mode')

if __name__=='__main__': main()
