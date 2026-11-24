"""Freeze committed code, preflight, and submit Base2060 HELD, never release.

Usage: python deploy_2060.py prepare|preflight|submit|collect
Requires revision_6d_general/final_gates.json PASS. Uses existing SSH only.
Refuses replacement of a release or blind resubmission after an attempt.
"""
from pathlib import Path
import base64
import csv
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
EVIDENCE=HERE/'revision_6d_general'
HOST='paracloud-bscc-a8'
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
NAME='20261012_base2060_v9a12_t48_m750_tol1e4_v1'
REMOTE=BASE+'/'+NAME
SOURCE=BASE+'/20260930_base2050_v9_t48_m750_tol1e4_v1'
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
PROFILE='config/solver_profiles/barrier_checkpoint_full_year_cloud_2060_numeric_v1_threads48.json'
CONFIG='config/optimization_numeric_dac_by_year_v9_a12.json'
STATE=REMOTE+'/upstream_2050_prepared/planning_state_candidate'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote(code,label):
    header='from pathlib import Path\nimport json,os,hashlib,subprocess,re,tarfile\nroot=Path('+repr(REMOTE)+')\nsource=Path('+repr(SOURCE)+')\n'
    compile(header+code,'<remote>','exec')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20',HOST,'python3 -'],
        input=header+code,text=True,encoding='utf-8',capture_output=True,timeout=900)
    (EVIDENCE/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8')
    (EVIDENCE/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:
        print(p.stderr[-3500:])
    p.check_returncode()
    return p.stdout


def environment():
    return f'''set -euo pipefail
set -a
source "{ENV_SOURCE}/manifests/cloud_environment_paths.env"
set +a
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${{LD_LIBRARY_PATH:-}}"
export GRB_LICENSE_FILE="${{CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}}"
export http_proxy="${{CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export CISPO_DATA_ROOT="{REMOTE}/data_overlay"
export PYTHONPATH="{REMOTE}/repo${{PYTHONPATH:+:$PYTHONPATH}}"
export UPSTREAM_STATE="{STATE}"
cd "{REMOTE}/repo"
'''


def main():
    mode=sys.argv[1]
    gates=json.loads((EVIDENCE/'final_gates.json').read_text())
    assert gates['status']=='PASS'
    if mode=='prepare':
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        assert not subprocess.check_output(['git','diff','HEAD','--','cispo_model','config','scripts','tests','AGENTS.md'],cwd=REPO).strip()
        acceptance=HERE.parent/'base_acceptance_relative_v1_20261012/assessments'
        state=HERE/'upstream_2050_prepared_6d'
        launch=dict(release=NAME,source_commit=commit,planning_year=2060,boundary_year=2050,
            authorization='Author 2026-10-12 task 6b/6c/6d and conversation: submit --hold only; release requires explicit 放行',
            automatic_release=False,automatic_successor=False,candidate_screening=False,stage_b=False,
            upstream_cohort_sha256=sha(state/'planning_state_candidate/capacity_cohorts.csv.gz'),
            acceptance_sha256={str(y):sha(acceptance/str(y)/'acceptance_relative_v1.json') for y in [2030,2040,2050]},
            cleanup=json.loads((state/'planning_state_candidate/state_metadata.json').read_text())['continuation_cleanup'],
            bound_closure=json.loads((state/'bound_closure_audit.json').read_text()),
            numerical_robustness_audit=json.loads((EVIDENCE/'2060_on_v2/build_report.json').read_text())['numerical_robustness_audit'],
            resources=dict(cpus=64,memory='750G',time_limit='UNLIMITED',requeue=False,solver_threads=48,minimum_available_memory_gib=700),
            final_gates_sha256=sha(EVIDENCE/'final_gates.json'))
        (EVIDENCE/'launch_config.json').write_text(json.dumps(launch,indent=2)+'\n')
        archived=subprocess.check_output(['git','archive',commit,'cispo_model','config','scripts','tests','AGENTS.md'],cwd=REPO)
        payload=EVIDENCE/'release_payload.tar.gz'
        repo_hashes={}
        with tarfile.open(fileobj=io.BytesIO(archived)) as source_tar, tarfile.open(payload,'w:gz') as target:
            for member in source_tar.getmembers():
                if not member.isfile():continue
                data=source_tar.extractfile(member).read()
                name='repo/'+member.name
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o640
                target.addfile(item,io.BytesIO(data));repo_hashes[member.name]=hashlib.sha256(data).hexdigest()
            paths={p:'upstream_2050_prepared/'+p.relative_to(state).as_posix() for p in state.rglob('*') if p.is_file()}
            for name in ['base_2060.sbatch','validate_2060.py']:
                # Operational entry points must also come from this commit.
                data=subprocess.check_output(['git','show',commit+':'+(HERE.relative_to(REPO)/name).as_posix()],cwd=REPO)
                assert data== (HERE/name).read_bytes(),name
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o640;target.addfile(item,io.BytesIO(data))
            paths[EVIDENCE/'launch_config.json']='launch_config.json'
            paths[EVIDENCE/'final_gates.json']='local_engineering_gates.json'
            paths[REPO/'data/thermal/retirement_schedule.csv']='additional_data/thermal/retirement_schedule.csv'
            for year in [2030,2040,2050]:
                paths[acceptance/str(year)/'acceptance_relative_v1.json']=f'acceptance/{year}/acceptance_relative_v1.json'
            for path,name in paths.items():
                target.add(path,arcname=name,recursive=False)
        identity=dict(source_commit=commit,files=repo_hashes,method='git archive committed blobs; SHA256 exact deployed bytes')
        print(remote("assert not root.exists(), 'Refuse existing release'\nroot.mkdir()\nprint(str(root))\n",'create_release').strip())
        subprocess.run(['scp','-o','BatchMode=yes',str(payload),HOST+':'+REMOTE+'/release_payload.tar.gz'],check=True)
        rows=list(csv.DictReader((EVIDENCE/'2060_on_v2/input_manifest.csv').open(encoding='utf-8-sig')))
        expected={r['logical_path']:r['sha256'] for r in rows if r['kind'] in ['model_table','capacity_rhs_cancellation_evidence'] and r['sha256']}
        code='identity='+repr(identity)+'\nexpected='+repr(expected)+'\npayload_sha='+repr(sha(payload))+'\n'+'''
archive=root/'release_payload.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==payload_sha
with tarfile.open(str(archive)) as tf:
    for member in tf.getmembers():
        p=Path(member.name)
        assert not p.is_absolute() and '..' not in p.parts and member.isfile(),member.name
        assert not (root/p).exists(),member.name
    tf.extractall(str(root))
for name,value in identity['files'].items():
    assert hashlib.sha256((root/'repo'/name).read_bytes()).hexdigest()==value,name
(root/'cloud_source_repo_sha256.json').write_text(json.dumps(identity,indent=2)+'\\n')
overlay=root/'data_overlay';overlay.mkdir()
for child in (source/'data_overlay').iterdir():
    if child.name!='thermal':(overlay/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
thermal=overlay/'thermal';thermal.mkdir()
for child in (source/'data_overlay/thermal').iterdir():
    if child.name!='retirement_schedule.csv':(thermal/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
(thermal/'retirement_schedule.csv').symlink_to(root/'additional_data/thermal/retirement_schedule.csv')
for name,value in expected.items():
    assert hashlib.sha256((overlay/name).read_bytes()).hexdigest()==value,name
(root/'data_overlay_sha256.json').write_text(json.dumps(expected,indent=2)+'\\n')
subprocess.check_call(['bash','-n','base_2060.sbatch'],cwd=str(root))
paths=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and 'data_overlay' not in p.relative_to(root).parts]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\\n' for p in sorted(paths)))
print(json.dumps(dict(status='FROZEN',source_commit=identity['source_commit'],repo_files=len(identity['files']),data_files=len(expected),release_manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
'''
        result=json.loads(remote(code,'freeze_release'))
        (EVIDENCE/'frozen_release.json').write_text(json.dumps(result,indent=2)+'\n')
        print(result)
    elif mode=='preflight':
        script=environment()+f'''
"$PYTHON" "{REMOTE}/validate_2060.py" --contract-only > "{REMOTE}/contract.log" 2>&1
"$PYTHON" scripts/run_cispo_2030_full_year.py --config {CONFIG} --solver-config {PROFILE} --planning-year 2060 --horizon full_year --state-in "$UPSTREAM_STATE" --allow-candidate-state-in --engineering-barrier-checkpoint-only --preflight-only --output-dir "{REMOTE}/preflight_v2" > "{REMOTE}/preflight.log" 2>&1
'''
        code='script='+repr(script)+'\n'+'''
assert not (root/'submission_attempt.json').exists()
p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:
    for name in ['contract.log','preflight.log']:
        if (root/name).exists():print((root/name).read_text()[-4500:])
    raise SystemExit(p.returncode)
assert json.loads((root/'preflight_v2/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'continuation_contract_check.json').read_text())['status']=='PASS'
print(json.dumps(dict(status='PASS',contract=json.loads((root/'continuation_contract_check.json').read_text()),preflight=json.loads((root/'preflight_v2/preflight_report.json').read_text()))))
'''
        result=json.loads(remote(code,'cloud_preflight'));(EVIDENCE/'cloud_preflight.json').write_text(json.dumps(result,indent=2)+'\n');print('Cloud contract and preflight PASS')
    elif mode=='submit':
        exports='ALL,SOURCE_RELEASE='+ENV_SOURCE+',UPSTREAM_STATE='+STATE
        code='exports='+repr(exports)+'\n'+'''
assert json.loads((root/'preflight_v2/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'continuation_contract_check.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(),'No blind repeat submissions'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
test=subprocess.run(['sbatch','--test-only','--export='+exports,'base_2060.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(test_stdout=test.stdout,test_stderr=test.stderr)))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'base_2060.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
receipt=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2))
assert p.returncode==0,receipt
job=p.stdout.strip().split(';')[0];assert job.isdigit()
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
receipt.update(job_id=job,scontrol=record)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\\n')
tres=dict(x.split('=',1) for x in re.search(r'\\bReqTRES=(\\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['mem'] in ['750G','768000M'] and tres['billing']=='64',tres
assert 'JobState=PENDING' in record and 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record and 'Requeue=0' in record,record
receipt['resource_check']='PASS';receipt['released']=False
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''
        result=json.loads(remote(code,'submit_held'));(EVIDENCE/'held_submission.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    elif mode=='collect':
        result=json.loads(remote("print(json.dumps({n:json.loads((root/n).read_text()) for n in ['held_submission.json','cloud_source_repo_sha256.json','continuation_contract_check.json']}))",'collect_release'))
        for name,value in result.items():(EVIDENCE/name).write_text(json.dumps(value,indent=2)+'\n')
        print('Collected frozen identity, contract and held receipt')
    else:
        raise SystemExit('Expected prepare|preflight|submit|collect; release is deliberately unavailable')


if __name__=='__main__':
    main()
