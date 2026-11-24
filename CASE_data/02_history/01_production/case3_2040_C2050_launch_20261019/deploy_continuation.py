"""Freeze gated continuation sources; submit HELD for resource validation.

Usage: python deploy_continuation.py prepare|preflight|submit --case case3_2040|C2050
Never releases jobs, overwrites releases, or inspects other jobs/credentials.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
HOST='paracloud-bscc-a8'
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
SOURCE=BASE+'/20260914_base_v9_t48_m750_tol1e4_v3'
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
CONTINUATION_INPUTS=('thermal/existing_capacity_2025.csv', 'thermal/retirement_schedule.csv',
                     'hydro/grfr_monthly_p30_single_year_proxy_2019.nc')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def remote(code,root,evidence,label):
    header='from pathlib import Path\nimport json,hashlib,subprocess,tarfile,re,os\nroot=Path('+repr(root)+')\nsource=Path('+repr(SOURCE)+')\n'
    compile(header+code,'<remote>','exec')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12',HOST,'python3 -'],
        input=header+code,text=True,encoding='utf-8',capture_output=True,timeout=600)
    (evidence/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8')
    (evidence/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:print(p.stderr[-2500:]);print(p.stdout[-2500:])
    p.check_returncode();return json.loads(p.stdout)


def environment(root):
    return f'''set -euo pipefail
set -a
source "{ENV_SOURCE}/manifests/cloud_environment_paths.env"
set +a
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${{LD_LIBRARY_PATH:-}}"
export GRB_LICENSE_FILE="${{CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}}"
export http_proxy="${{CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export CISPO_DATA_ROOT="{root}/data_overlay"
export PYTHONPATH="{root}/repo${{PYTHONPATH:+:$PYTHONPATH}}"
cd "{root}/repo"
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','preflight','submit'])
    p.add_argument('--case',required=True,choices=['case3_2040','C2050']);a=p.parse_args()
    year=2040 if a.case=='case3_2040' else 2050
    profile=f'config/solver_profiles/barrier_stagea_screened_agg0_{year}_v1_threads48.json'
    state_dir=HERE/('R1_case3_2040_02' if year==2040 else 'R1_C2050_01')/'prepared_state'
    gates_path=HERE/(a.case+'_final_gates.json')
    gates=json.loads(gates_path.read_text(encoding='utf-8'))
    assert gates['status']=='PASS','All L gates must pass before deployment'
    scenario='case3_thermal_ev_v5'
    name='20261020_'+('case3_2040' if year==2040 else 'lateentry_2050')+'_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1'
    root=BASE+'/'+name;evidence=HERE/('deployment_'+a.case);evidence.mkdir(exist_ok=True)
    if a.mode=='prepare':
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        for path, expected_hash in gates['tested_source_lf_sha256'].items():
            blob=subprocess.check_output(['git','show',commit+':'+path],cwd=REPO)
            assert hashlib.sha256(blob).hexdigest()==expected_hash,path
        paths=['cispo_model','config','scripts','tests','AGENTS.md',str(HERE.relative_to(REPO)/'continuation.sbatch')]
        assert not subprocess.check_output(['git','diff','HEAD','--',*paths],cwd=REPO).strip(),'Commit reviewed source first'
        archive=subprocess.check_output(['git','archive',commit,'cispo_model','config','scripts','tests','AGENTS.md'],cwd=REPO)
        expected={k.replace('\\','/'):v for k,v in json.loads((REPO/'supplementary_materials/reviews/case3_2030_launch_20261014/expected_data_files.json').read_text()).items()}
        # These continuation-only files are absent from the 2030 manifest.
        for key in CONTINUATION_INPUTS:
            local=REPO/'data'/key
            expected[key]=dict(local_path=str(local),sha256=sha(local))
        manifest=list(csv.DictReader((HERE/gates['gate_paths'][-1]/'input_manifest.csv').open(encoding='utf-8-sig')))
        for row in manifest:
            local=Path(row['resolved_path'])
            if row['required']=='True' and local.is_relative_to(REPO/'data'):
                key=local.relative_to(REPO/'data').as_posix()
                assert expected[key]['sha256']==row['sha256'],key
        save(evidence/'expected_data_files.json',expected)
        payload=evidence/'release_payload.tar.gz';hashes={}
        launch=dict(release=name,source_commit=commit,scenario=scenario,planning_year=year,boundary_year=year-10,framework='A' if year==2040 else 'C_Late-entry',state_input='upstream_state/planning_state_candidate',
            source_release=SOURCE,solver_profile=profile,screen_margin=.2,automatic_release=True,
            automatic_successor=False,stage_b=False,authorization='Author 2026-10-19: gated submit and release',
            resources=dict(cpus=64,memory='750G',time_limit='UNLIMITED',requeue=False,solver_threads=48,minimum_available_memory_gib=700),
            gates_sha256=sha(gates_path))
        save(evidence/'launch_config.json',launch)
        with tarfile.open(fileobj=io.BytesIO(archive)) as source,tarfile.open(payload,'w:gz') as target:
            def add(name,data):
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o640;target.addfile(item,io.BytesIO(data))
            for item in source.getmembers():
                if item.isfile():
                    data=source.extractfile(item).read();add('repo/'+item.name,data);hashes[item.name]=hashlib.sha256(data).hexdigest()
            batch=subprocess.check_output(['git','show',commit+':'+(HERE.relative_to(REPO)/'continuation.sbatch').as_posix()],cwd=REPO)
            assert batch==(HERE/'continuation.sbatch').read_bytes()
            add('continuation.sbatch',batch)
            add('launch_config.json',(evidence/'launch_config.json').read_bytes())
            add('local_engineering_gates.json',gates_path.read_bytes())
            add('source_screen.csv',(REPO/f'supplementary_materials/reviews/case3_2030_launch_20261014/P4_ready{year}_20261015/source_screen.csv').read_bytes())
            for item in sorted(state_dir.rglob('*')):
                if item.is_file():add('upstream_state/'+item.relative_to(state_dir).as_posix(),item.read_bytes())
            for path,v in expected.items():
                if path.startswith('flexibility/participation_pathway_v2/') or path in CONTINUATION_INPUTS:
                    assert sha(v['local_path'])==v['sha256'];add('additional_data/'+path,Path(v['local_path']).read_bytes())
        remote("assert not root.exists(), 'Refuse existing release'\nroot.mkdir()\nprint(json.dumps({'created':str(root)}))",root,evidence,'create')
        subprocess.run(['scp','-o','BatchMode=yes',str(payload),HOST+':'+root+'/release_payload.tar.gz'],check=True)
        identity=dict(source_commit=commit,files=hashes,method='git archive committed blobs; exact deployed SHA256')
        code='profile_path='+repr(profile)+'\nidentity='+repr(identity)+'\nexpected='+repr({k:v['sha256'] for k,v in expected.items()})+'\npayload_sha='+repr(sha(payload))+'\n'+r'''
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(str(root/'release_payload.tar.gz')) as tf:
    for item in tf.getmembers():
        p=Path(item.name)
        assert item.isfile() and not p.is_absolute() and '..' not in p.parts
        assert not (root/p).exists()
    tf.extractall(str(root))
for path,h in identity['files'].items():assert hashlib.sha256((root/'repo'/path).read_bytes()).hexdigest()==h,path
(root/'cloud_source_repo_sha256.json').write_text(json.dumps(identity,indent=2)+'\n')
overlay=root/'data_overlay';overlay.mkdir()
for child in (source/'data_overlay').iterdir():
    if child.name not in {'flexibility','thermal','hydro'}:(overlay/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
flex=overlay/'flexibility';flex.mkdir()
for child in (source/'data_overlay/flexibility').iterdir():
    if child.name!='participation_pathway_v2':(flex/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
(flex/'participation_pathway_v2').symlink_to(root/'additional_data/flexibility/participation_pathway_v2',target_is_directory=True)
for family in ('thermal','hydro'):
    target=overlay/family;target.mkdir()
    extra=root/'additional_data'/family
    overrides={p.name:p for p in extra.iterdir()}
    for child in (source/'data_overlay'/family).iterdir():
        if child.name not in overrides:(target/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
    for name,path in overrides.items():(target/name).symlink_to(path)
for path,h in expected.items():assert hashlib.sha256((overlay/path).read_bytes()).hexdigest()==h,path
(root/'data_overlay_sha256.json').write_text(json.dumps(expected,indent=2)+'\n')
profile=json.loads((root/'repo'/profile_path).read_text())
assert hashlib.sha256((root/'source_screen.csv').read_bytes()).hexdigest()==profile['candidate_screen']['source_csv_sha256']
subprocess.check_call(['bash','-n','continuation.sbatch'],cwd=str(root))
paths=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and 'data_overlay' not in p.relative_to(root).parts]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(paths)))
print(json.dumps(dict(status='FROZEN',release=str(root),source_commit=identity['source_commit'],repo_files=len(identity['files']),data_files=len(expected),source_manifest_sha256=hashlib.sha256((root/'cloud_source_repo_sha256.json').read_bytes()).hexdigest(),release_manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
'''
        result=remote(code,root,evidence,'freeze');save(evidence/'frozen_release.json',result);print(result)
    elif a.mode=='preflight':
        script=environment(root)+f'''"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9_a12.json --scenario-config config/scenarios/{scenario}.json --solver-config {profile} --planning-year {year} --state-in "{root}/upstream_state/planning_state_candidate" --allow-candidate-state-in {('--late-entry-base-state' if year==2050 else '')} --vre-screen-csv "{root}/source_screen.csv" --horizon full_year --allow-nonbasic-planning-state --preflight-only --output-dir "{root}/preflight_v2" > "{root}/preflight_v2.log" 2>&1
'''
        result=remote('script='+repr(script)+'\n'+r'''
assert not (root/'submission_attempt.json').exists()
p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:print((root/'preflight_v2.log').read_text()[-4500:]);raise SystemExit(p.returncode)
report=json.loads((root/'preflight_v2/preflight_report.json').read_text());assert report['status']=='PASS'
print(json.dumps(dict(status='PASS',report=report)))
''',root,evidence,'preflight_v2');save(evidence/'cloud_preflight.json',result);print('Cloud preflight PASS')
    else:
        exports='ALL,SOURCE_RELEASE='+ENV_SOURCE
        result=remote('exports='+repr(exports)+'\n'+r'''
assert json.loads((root/'preflight_v2/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(),'No blind repeat submission'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
test=subprocess.run(['sbatch','--test-only','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(test_stdout=test.stdout,test_stderr=test.stderr)))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
receipt=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2))
assert p.returncode==0,receipt
job=p.stdout.strip().split(';')[0];assert job.isdigit()
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
receipt.update(job_id=job,scontrol=record,released=False)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\n')
tres=dict(x.split('=',1) for x in re.search(r'\bReqTRES=(\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['mem'] in ['750G','768000M'] and tres['billing']=='64'
assert 'JobState=PENDING' in record and 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record and 'Requeue=0' in record
receipt['resource_check']='PASS'
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
''',root,evidence,'submit');save(evidence/'held_submission.json',result);print(result)


if __name__=='__main__':main()
