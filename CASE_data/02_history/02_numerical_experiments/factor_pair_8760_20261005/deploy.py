"""Explicit immutable prepare/preflight/held-submit/release/status; no credential access."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
REMOTE=BASE+'/claude_workspace/factor_pair_8760_20261005'
SOURCE=BASE+'/20260930_base2050_v9_t48_m750_tol1e4_v1'
HEADER='from pathlib import Path\nimport json,subprocess,hashlib,shutil,os,datetime,re,base64\nroot=Path('+repr(REMOTE)+')\nsource=Path('+repr(SOURCE)+')\n'


def remote(code,label):
    compile(HEADER+code,'remote','exec')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],
        input=HEADER+code,capture_output=True,text=True,encoding='utf-8',timeout=1800)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (HERE/(label+'_'+stamp+'.stdout.log')).write_text(p.stdout,encoding='utf-8')
    (HERE/(label+'_'+stamp+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if label in ('status','collect') and p.returncode == 0:
        decoded=json.loads(p.stdout);print(decoded['accounting']);print(json.dumps(decoded['jobs']))
    else: print(p.stdout[-10000:])
    print(p.stderr[-3000:]);p.check_returncode()
    return p.stdout


def main():
    mode=sys.argv[1]
    if mode=='prepare':
        files={p.relative_to(HERE/'cloud_payload').as_posix():base64.b64encode(p.read_bytes()).decode() for p in (HERE/'cloud_payload').rglob('*') if p.is_file()}
        expected=json.loads((HERE/'cloud_source_repo_sha256.json').read_text())
        remote('files='+repr(files)+'\nexpected='+repr(expected)+'\n'+r'''
assert not root.exists(), 'Never overwrite immutable release'
for rel,sha in expected.items():
    assert hashlib.sha256((source/'repo'/rel).read_bytes()).hexdigest()==sha,rel
root.mkdir(parents=True)
for name in ('member_F','member_S'):
    member=root/name;member.mkdir()
    shutil.copytree(source/'repo',member/'repo',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (member/'data_overlay').symlink_to(source/'data_overlay',target_is_directory=True)
    for rel,data in files.items():
        p=member/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
    actual={str(p.relative_to(member/'repo')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (member/'repo').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.csv','.sh','.sbatch')}
    delta={rel:{'old':expected.get(rel),'new':sha} for rel,sha in actual.items() if expected.get(rel)!=sha}
    allowed={'scripts/run_cispo_2030_full_year.py','cispo_model/factor_screen.py','config/solver_profiles/barrier_factor_screen_8760_v1_threads48.json','config/scenarios/case3_thermal_ev_v9_factor.json','tests/test_factor_screen.py'}
    assert set(delta)==allowed,delta
    identity=dict(source=str(source),baseline_repo_sha256=expected,delta_allowlist=delta,actual_repo_sha256=actual,
        input_root=str((member/'data_overlay').resolve()),result_use='TEST_ONLY_FACTOR_SCREEN',scientific_acceptance_mode='NONE')
    (member/'source_identity.json').write_text(json.dumps(identity,indent=2))
    lines=[]
    for p in sorted(member.rglob('*')):
        if p.is_file() and not p.is_symlink():lines.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(member)))
    (member/'release_files.sha256').write_text('\n'.join(lines)+'\n')
    subprocess.check_call(['bash','-n','factor.sbatch'],cwd=str(member))
print(json.dumps({'status':'PREPARED','source':str(source),'root':str(root),'repo_files':len(expected),'delta_allowlist':sorted(allowed)},indent=2))
''',mode)
    elif mode=='preflight':
        # Data/compatibility only on login node: no LP construction or optimize.
        script=(HERE/'factor.sbatch').read_text().split('"$PYTHON" - "$RELEASE_ROOT"')[0]
        script=script[script.index('set -euo pipefail'):]
        script=script.replace('RELEASE_ROOT="${SLURM_SUBMIT_DIR:?}"', 'RELEASE_ROOT='+repr(REMOTE+'/member_F'))
        script='\n'.join(x for x in script.splitlines() if not x.startswith('trap '))
        script+='\ncd "$RELEASE_ROOT/repo"\n"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --scenario-config config/scenarios/case3_thermal_ev_v9_factor.json --solver-config config/solver_profiles/barrier_factor_screen_8760_v1_threads48.json --planning-year 2030 --horizon full_year --preflight-only --output-dir "$RELEASE_ROOT/preflight"\n'
        remote('script='+repr(script)+'\nsubprocess.check_call(["bash"],input=script)\n'.replace('subprocess.check_call(["bash"],input=script)','p=subprocess.run(["bash"],input=script,universal_newlines=True);p.check_returncode()'),mode)
    elif mode=='submit':
        remote(r'''
assert json.loads((root/'member_F/preflight/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(), 'Submission already attempted; inspect, never retry blindly'
(root/'submission_attempt.json').write_text(json.dumps({'utc':datetime.datetime.utcnow().isoformat()}))
jobs={}
for name in ('member_F','member_S'):
    member=root/name
    subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(member))
    p=subprocess.run(['sbatch','--hold','--parsable','--job-name=cispo_factor_'+name[-1],'factor.sbatch'],cwd=str(member),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    (member/'submission.json').write_text(json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)))
    p.check_returncode();job=p.stdout.strip().split(';')[0];assert job.isdigit()
    jobs[name]=job
    record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
    (member/'held_job.txt').write_text(record)
    assert 'JobState=PENDING' in record and 'JobHeldUser' in record
    assert re.search(r'\bReqTRES=cpu=64,mem=750G,node=1,billing=64(?:\s|$)',record),record
    assert 'TimeLimit=UNLIMITED' in record and 'Partition=amd_a8_768' in record
    (root/'held_submission.json').write_text(json.dumps(jobs,indent=2))
    print('HELD '+name+' '+job,flush=True)
print(json.dumps(jobs))
''',mode)
    elif mode=='release':
        remote(r'''
jobs=json.loads((root/'held_submission.json').read_text());assert set(jobs)=={'member_F','member_S'}
assert not (root/'release_attempt.json').exists()
for name,job in jobs.items():
    record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
    assert 'JobHeldUser' in record and 'JobState=PENDING' in record
    assert 'ReqTRES=cpu=64,mem=750G,node=1,billing=64' in record
    assert 'TimeLimit=UNLIMITED' in record and 'Partition=amd_a8_768' in record
(root/'release_attempt.json').write_text(json.dumps({'utc':datetime.datetime.utcnow().isoformat(),'jobs':jobs}))
for name,job in jobs.items():
    subprocess.check_call(['scontrol','release',job])
    print('RELEASED '+name+' '+job,flush=True)
''',mode)
    elif mode in ('status','collect'):
        result=remote('mode='+repr(mode)+'\n'+r'''
jobs=json.loads((root/'held_submission.json').read_text())
report={'jobs':jobs,'files':{}}
report['sstat']=subprocess.check_output(['sstat','-j',','.join(j+'.batch' for j in jobs.values()),'--format=JobID,AveCPU,MaxRSS,AveRSS','-P'],universal_newlines=True)
report['accounting']=subprocess.check_output(['sacct','-j',','.join(jobs.values()),'--format=JobID,State,ExitCode,Elapsed,NodeList,AllocTRES,MaxRSS','-P'],universal_newlines=True)
for name,job in jobs.items():
    member=root/name
    report['files'][name]={}
    paths=['source_identity.json','held_job.txt','runtime_slurm_job.txt','runtime_node.txt','allocation_gate.json','startup_regression.log','batch_exit.json','resource_usage.txt','stdout.log','stderr.log','output_8760/build_report.json','output_8760/run_scope.json','output_8760/solver_parameters_before_optimize.json','output_8760/gurobi.log','output_8760/solver_telemetry.jsonl','output_8760/solve_report.json','output_8760/mps_section_sha256.json','output_8760/input_manifest.csv','output_8760/model_archive/archive_manifest.json']
    if mode=='collect':paths.append('output_8760/candidate_selection.csv')
    for rel in paths:
        p=member/rel
        if p.is_file():
            snapshot=p.read_bytes()
            report['files'][name][rel]={'sha256':hashlib.sha256(snapshot).hexdigest(),'base64':base64.b64encode(snapshot).decode()}
print(json.dumps(report))
''',mode)
        d=json.loads(result);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');folder=HERE/('status_'+stamp);folder.mkdir()
        (folder/'accounting.txt').write_text(d['accounting'])
        (folder/'sstat.txt').write_text(d['sstat'])
        for member,files in d['files'].items():
            for rel,record in files.items():
                p=folder/member/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(record['base64']));assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
        (folder/'receipt.json').write_text(json.dumps({'jobs':d['jobs'],'sha256_verified':{m:{r:v['sha256'] for r,v in fs.items()} for m,fs in d['files'].items()}},indent=2))
    else:raise ValueError(mode)


if __name__=='__main__':main()
