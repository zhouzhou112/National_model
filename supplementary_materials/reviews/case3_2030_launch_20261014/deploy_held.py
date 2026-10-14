"""Freeze committed, locally gated case3 sources and submit HELD only.

Usage: python deploy_held.py prepare|preflight|submit --case case3|nocredit
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
PROFILE='config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json'


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
    p.add_argument('--case',required=True,choices=['case3','nocredit']);a=p.parse_args()
    gates=json.loads((HERE/'final_gates.json').read_text(encoding='utf-8'))
    assert gates['status']=='PASS','All L gates must pass before deployment'
    scenario='case3_thermal_ev_v5'+('_nocredit' if a.case=='nocredit' else '')
    name='20261014_'+('case3nocredit' if a.case=='nocredit' else 'case3')+'_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1'
    root=BASE+'/'+name;evidence=HERE/('deployment_'+a.case);evidence.mkdir(exist_ok=True)
    if a.mode=='prepare':
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        for path, expected_hash in gates['tested_source_lf_sha256'].items():
            blob=subprocess.check_output(['git','show',commit+':'+path],cwd=REPO)
            assert hashlib.sha256(blob).hexdigest()==expected_hash,path
        paths=['cispo_model','config','scripts','tests','AGENTS.md',str(HERE.relative_to(REPO)/'case3_2030.sbatch')]
        assert not subprocess.check_output(['git','diff','HEAD','--',*paths],cwd=REPO).strip(),'Commit reviewed source first'
        archive=subprocess.check_output(['git','archive',commit,'cispo_model','config','scripts','tests','AGENTS.md'],cwd=REPO)
        expected={k.replace('\\','/'):v for k,v in json.loads((HERE/'expected_data_files.json').read_text()).items()}
        payload=evidence/'release_payload.tar.gz';hashes={}
        launch=dict(release=name,source_commit=commit,scenario=scenario,planning_year=2030,boundary_year=2025,
            source_release=SOURCE,solver_profile=PROFILE,screen_margin=.2,automatic_release=False,
            automatic_successor=False,stage_b=False,authorization='Author 2026-10-14: held only; release requires 放行',
            resources=dict(cpus=64,memory='750G',time_limit='UNLIMITED',requeue=False,solver_threads=48,minimum_available_memory_gib=700),
            gates_sha256=sha(HERE/'final_gates.json'))
        save(evidence/'launch_config.json',launch)
        with tarfile.open(fileobj=io.BytesIO(archive)) as source,tarfile.open(payload,'w:gz') as target:
            def add(name,data):
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o640;target.addfile(item,io.BytesIO(data))
            for item in source.getmembers():
                if item.isfile():
                    data=source.extractfile(item).read();add('repo/'+item.name,data);hashes[item.name]=hashlib.sha256(data).hexdigest()
            batch=subprocess.check_output(['git','show',commit+':'+(HERE.relative_to(REPO)/'case3_2030.sbatch').as_posix()],cwd=REPO)
            assert batch==(HERE/'case3_2030.sbatch').read_bytes()
            add('case3_2030.sbatch',batch)
            add('launch_config.json',(evidence/'launch_config.json').read_bytes())
            add('local_engineering_gates.json',(HERE/'final_gates.json').read_bytes())
            add('source_screen.csv',(REPO/'supplementary_materials/reviews/factor_pair_8760_20261005/cloud_payload/source_screen.csv').read_bytes())
            for path,v in expected.items():
                if path.startswith('flexibility/participation_pathway_v2/'):
                    assert sha(v['local_path'])==v['sha256'];add('additional_data/'+path,Path(v['local_path']).read_bytes())
        remote("assert not root.exists(), 'Refuse existing release'\nroot.mkdir()\nprint(json.dumps({'created':str(root)}))",root,evidence,'create')
        subprocess.run(['scp','-o','BatchMode=yes',str(payload),HOST+':'+root+'/release_payload.tar.gz'],check=True)
        identity=dict(source_commit=commit,files=hashes,method='git archive committed blobs; exact deployed SHA256')
        code='identity='+repr(identity)+'\nexpected='+repr({k:v['sha256'] for k,v in expected.items()})+'\npayload_sha='+repr(sha(payload))+'\n'+r'''
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
    if child.name!='flexibility':(overlay/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
flex=overlay/'flexibility';flex.mkdir()
for child in (source/'data_overlay/flexibility').iterdir():
    if child.name!='participation_pathway_v2':(flex/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
(flex/'participation_pathway_v2').symlink_to(root/'additional_data/flexibility/participation_pathway_v2',target_is_directory=True)
for path,h in expected.items():assert hashlib.sha256((overlay/path).read_bytes()).hexdigest()==h,path
(root/'data_overlay_sha256.json').write_text(json.dumps(expected,indent=2)+'\n')
profile=json.loads((root/'repo/config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json').read_text())
assert hashlib.sha256((root/'source_screen.csv').read_bytes()).hexdigest()==profile['candidate_screen']['source_csv_sha256']
subprocess.check_call(['bash','-n','case3_2030.sbatch'],cwd=str(root))
paths=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and 'data_overlay' not in p.relative_to(root).parts]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(paths)))
print(json.dumps(dict(status='FROZEN',release=str(root),source_commit=identity['source_commit'],repo_files=len(identity['files']),data_files=len(expected),source_manifest_sha256=hashlib.sha256((root/'cloud_source_repo_sha256.json').read_bytes()).hexdigest(),release_manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
'''
        result=remote(code,root,evidence,'freeze');save(evidence/'frozen_release.json',result);print(result)
    elif a.mode=='preflight':
        script=environment(root)+f'''"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --scenario-config config/scenarios/{scenario}.json --solver-config {PROFILE} --vre-screen-csv "{root}/source_screen.csv" --horizon full_year --archive-original-model --allow-nonbasic-planning-state --preflight-only --output-dir "{root}/preflight" > "{root}/preflight.log" 2>&1
'''
        result=remote('script='+repr(script)+'\n'+r'''
assert not (root/'submission_attempt.json').exists()
p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:print((root/'preflight.log').read_text()[-4500:]);raise SystemExit(p.returncode)
report=json.loads((root/'preflight/preflight_report.json').read_text());assert report['status']=='PASS'
print(json.dumps(dict(status='PASS',report=report)))
''',root,evidence,'preflight');save(evidence/'cloud_preflight.json',result);print('Cloud preflight PASS')
    else:
        exports='ALL,SOURCE_RELEASE='+ENV_SOURCE
        result=remote('exports='+repr(exports)+'\n'+r'''
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(),'No blind repeat submission'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
test=subprocess.run(['sbatch','--test-only','--export='+exports,'case3_2030.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(test_stdout=test.stdout,test_stderr=test.stderr)))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'case3_2030.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
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
