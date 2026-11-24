"""Freeze and launch only the author-approved B2030 pilot after all gates pass.

No successor submission or background watcher. Existing release => refuse.
Credentials are used through existing environment paths, never read/copied.
"""
import argparse
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
NAME='20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3'
ROOT=BASE+'/'+NAME
SOURCE_NAME='20260914_base_v9_t48_m750_tol1e4_v3'
SOURCE=BASE+'/'+SOURCE_NAME
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
PROFILE='config/solver_profiles/barrier_stagea_base_frozen_agg0_v1_threads48.json'
EVIDENCE=HERE/'deployment_v3'
LICENSE='/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def remote(code,label):
    EVIDENCE.mkdir(exist_ok=True)
    header='from pathlib import Path\nimport json,hashlib,subprocess,tarfile,os,re\nroot=Path('+repr(ROOT)+')\nsource=Path('+repr(SOURCE)+')\n'
    compile(header+code,'<B-pilot>','exec')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',HOST,'python3 -'],
        input=header+code,text=True,encoding='utf-8',capture_output=True,timeout=900)
    for suffix,txt in [('stdout',p.stdout),('stderr',p.stderr)]:
        with (EVIDENCE/(label+'.'+suffix+'.log')).open('x',encoding='utf-8') as f:f.write(txt)
    if p.returncode:print(p.stdout[-4000:],p.stderr[-2000:])
    p.check_returncode()
    return json.loads(p.stdout)


def environment():
    return f'''set -euo pipefail
set -a
source "{ENV_SOURCE}/manifests/cloud_environment_paths.env"
set +a
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${{LD_LIBRARY_PATH:-}}"
export GRB_LICENSE_FILE="{LICENSE}"
export http_proxy="${{CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=48 OMP_NUM_THREADS=48 MKL_NUM_THREADS=48
export CISPO_DATA_ROOT="{ROOT}/data_overlay"
export PYTHONPATH="{ROOT}/repo${{PYTHONPATH:+:$PYTHONPATH}}"
cd "{ROOT}/repo"
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','preflight','submit-release','status'])
    parser.add_argument('--label',default='status_01')
    args=parser.parse_args()
    gates=json.loads((HERE/'FINAL_GATES_PASSED.json').read_text())
    assert gates['status']=='PASS' and gates['framework']=='B' and gates['planning_year']==2030
    EVIDENCE.mkdir(exist_ok=True)
    if args.mode=='prepare':
        commit='9f0a042cbad241b13351b36dd68f3680666d42fb'
        for path,expected in gates['tested_source_lf_sha256'].items():
            blob=subprocess.check_output(['git','show',commit+':'+path],cwd=REPO)
            assert hashlib.sha256(blob).hexdigest()==expected,path
        assert not subprocess.check_output(['git','diff','HEAD','--','cispo_model','scripts','config','tests'],cwd=REPO).strip()
        archive=subprocess.check_output(['git','archive',commit,'cispo_model','scripts','config','tests','AGENTS.md'],cwd=REPO)
        expected=json.loads((HERE/'expected_data_files.json').read_text())
        payload=EVIDENCE/'release_payload.tar.gz';assert not payload.exists()
        launch=dict(release=NAME,source_commit=commit,framework='B',description='框架 B（Base-frozen）',
            scenario='case3_thermal_ev_v5',planning_year=2030,boundary_year=2025,solver_profile=PROFILE,
            license_path=LICENSE,license_comparison='STRING_ONLY',template_release='20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2',previous_failed_job='5276670',scientific_gates_reused=True,frozen_capacity_from=SOURCE_NAME,upstream=None,candidate_screen=False,automatic_successor=False,
            author_authorization='2026-10-26: all gates passed => submit and release B2030 only',
            resources=dict(cpus=64,memory='750G',time_limit='UNLIMITED',requeue=False,solver_threads=48,minimum_available_memory_gib=700))
        save(EVIDENCE/'launch_config.json',launch)
        source_hashes={}
        with tarfile.open(fileobj=io.BytesIO(archive)) as src,tarfile.open(payload,'w:gz') as dst:
            def add(name,data):
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o640;dst.addfile(item,io.BytesIO(data))
            for item in src.getmembers():
                if item.isfile():
                    data=src.extractfile(item).read();add('repo/'+item.name,data);source_hashes[item.name]=hashlib.sha256(data).hexdigest()
            for name in ['base_frozen_2030.sbatch','FINAL_GATES_PASSED.json']:
                rel=(HERE/name).relative_to(REPO).as_posix()
                if name=='base_frozen_2030.sbatch':
                    data=(HERE/'base_frozen_2030_v3.sbatch').read_bytes()
                    recorded=subprocess.check_output(['git','show','HEAD:'+str((HERE/'base_frozen_2030_v3.sbatch').relative_to(REPO).as_posix())],cwd=REPO)
                    assert data==recorded,'Commit reviewed launch script before freezing'
                else:
                    data=subprocess.check_output(['git','show',commit+':'+rel],cwd=REPO)
                    assert data==(HERE/name).read_bytes()
                add(name,data)
            add('launch_config.json',(EVIDENCE/'launch_config.json').read_bytes())
            for relative,record in expected.items():
                p=REPO/record['local_path'];assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],relative
                add('additional_data/'+relative,p.read_bytes())
            # Exact small source inventory, not unrestricted recursive inclusion.
            frozen=HERE/'source_base'/SOURCE_NAME
            names=['result_manifest.json','run_identity.json','run_environment.json','input_manifest.csv',
                'vre_capacity.csv','thermal_nuclear_capacity.csv','storage_capacity.csv','transmission_capacity.csv',
                'load_center_intra_transmission.csv','intra_grid_vre_site_design.csv','intra_grid_substation_design.csv',
                'hydro_capacity.csv','wave_capacity.csv','dac_capacity_capture.csv']
            for name in names:add('frozen_source/'+SOURCE_NAME+'/output_8760/'+name,(frozen/'output_8760'/name).read_bytes())
            for name in ['hydro_spur_capacity.csv','supplement_manifest.json']:
                add('frozen_source/'+SOURCE_NAME+'/frozen_capacity_B_20261026/'+name,(frozen/'frozen_capacity_B_20261026'/name).read_bytes())
        remote("assert not root.exists(),'Refuse existing release'\nroot.mkdir()\nprint(json.dumps({'created':str(root)}))",'create')
        subprocess.run(['scp','-o','BatchMode=yes',str(payload),HOST+':'+ROOT+'/release_payload.tar.gz'],check=True)
        code='expected='+repr(expected)+'\nsource_hashes='+repr(source_hashes)+'\npayload_sha='+repr(sha(payload))+'\n'+r'''
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(str(root/'release_payload.tar.gz')) as tf:
 for item in tf.getmembers():
  p=Path(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts and not (root/p).exists()
 tf.extractall(str(root))
for rel,h in source_hashes.items():assert hashlib.sha256((root/'repo'/rel).read_bytes()).hexdigest()==h,rel
overlay=root/'data_overlay';overlay.mkdir()
# Link inherited input files individually, substituting only private validated copies.
for directory,dirs,files in os.walk(str(source/'data_overlay'),followlinks=True):
 relative=Path(directory).relative_to(source/'data_overlay');target=overlay/relative;target.mkdir(exist_ok=True,parents=True)
 for name in files:
  rel=(relative/name).as_posix();p=target/name
  actual=root/'additional_data'/rel if rel in expected else (Path(directory)/name).resolve()
  p.symlink_to(actual)
for rel,record in expected.items():
 p=overlay/rel
 if not p.exists():p.parent.mkdir(exist_ok=True,parents=True);p.symlink_to(root/'additional_data'/rel)
 assert p.stat().st_size==record['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],rel
oldroot=root.parent/'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2'
assert source_hashes==json.loads((oldroot/'cloud_source_repo_sha256.json').read_text())
assert {k:v['sha256'] for k,v in expected.items()}==json.loads((oldroot/'data_overlay_sha256.json').read_text())
same=[]
for folder in ['repo','additional_data','frozen_source']:
 for p in (root/folder).rglob('*'):
  if p.is_file():
   rel=p.relative_to(root);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((oldroot/rel).read_bytes()).digest(),str(rel)
   same.append(str(rel))
assert (root/'FINAL_GATES_PASSED.json').read_bytes()==(oldroot/'FINAL_GATES_PASSED.json').read_bytes()
(root/'v2_identity_reuse.json').write_text(json.dumps(dict(status='PASS',unchanged_file_count=len(same),source_commit='9f0a042cbad241b13351b36dd68f3680666d42fb',gates_identical=True),indent=2)+'\n')
(root/'cloud_source_repo_sha256.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
(root/'data_overlay_sha256.json').write_text(json.dumps({k:v['sha256'] for k,v in expected.items()},indent=2)+'\n')
subprocess.check_call(['bash','-n',str(root/'base_frozen_2030.sbatch')])
paths=[p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and 'data_overlay' not in p.relative_to(root).parts]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(paths)))
print(json.dumps(dict(status='FROZEN',release=str(root),repo_files=len(source_hashes),data_files=len(expected),payload_sha256=payload_sha,release_manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
'''
        result=remote(code,'freeze');save(EVIDENCE/'frozen_release.json',result);print(result)
    elif args.mode=='preflight':
        command=f'''"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --scenario-config config/scenarios/case3_thermal_ev_v5.json --solver-config {PROFILE} --planning-year 2030 --horizon full_year --allow-nonbasic-planning-state --frozen-capacity-from "{ROOT}/frozen_source/{SOURCE_NAME}/output_8760" --frozen-capacity-supplement "{ROOT}/frozen_source/{SOURCE_NAME}/frozen_capacity_B_20261026" --preflight-only --output-dir "{ROOT}/preflight" > "{ROOT}/preflight.log" 2>&1
'''
        result=remote('script='+repr(environment()+command)+'\n'+r'''
assert not (root/'submission_attempt.json').exists() and not (root/'preflight').exists()
launch=json.loads((root/'launch_config.json').read_text())
batch=(root/'base_frozen_2030.sbatch').read_text()
matches=re.findall(r'^export GRB_LICENSE_FILE="([^"\n]+)"$',batch,re.M)
registered=json.loads((root.parent/'20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'/'launch_config.json').read_text())['license_path']
assert matches==[registered] and launch['license_path']==registered,'WLS path string mismatch'
license_check=dict(status='PASS',mode='STRING_ONLY',sbatch_license_path=matches[0],registered_license_path=registered,credential_contents_read=False)
(root/'license_path_preflight.json').write_text(json.dumps(license_check,indent=2)+'\n')

p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:print((root/'preflight.log').read_text()[-4000:]);raise SystemExit(p.returncode)
report=json.loads((root/'preflight/preflight_report.json').read_text());assert report['status']=='PASS'
print(json.dumps(dict(status='PASS',report=report,license_path_check=license_check)))
''','preflight');save(EVIDENCE/'cloud_preflight.json',result);print('Cloud preflight PASS')
    elif args.mode=='submit-release':
        result=remote('exports='+repr('ALL,SOURCE_RELEASE='+ENV_SOURCE)+'\n'+r'''
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'license_path_preflight.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(),'Do not repeat an uncertain submission'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
queue=subprocess.check_output(['squeue','--me','--noheader','-o','%i %T'],universal_newlines=True)
assert len(queue.strip().splitlines())<10,'Author quota: no more than 10 jobs'
test=subprocess.run(['sbatch','--test-only','--export='+exports,'base_frozen_2030.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
assert test.returncode==0,test.stderr
(root/'submission_attempt.json').write_text(json.dumps(dict(test_stdout=test.stdout,test_stderr=test.stderr)))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'base_frozen_2030.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
receipt=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2));assert p.returncode==0,receipt
job=p.stdout.strip().split(';')[0];assert job.isdigit() and job not in {'5201318','5207165'}
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
receipt.update(job_id=job,scontrol=record,released=False)
(root/'held_submission.json').write_text(json.dumps(receipt,indent=2)+'\n')
tres=dict(v.split('=',1) for v in re.search(r'\bReqTRES=(\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['billing']=='64' and tres['mem'] in {'750G','768000M'}
assert 'Reason=JobHeldUser' in record and 'TimeLimit=UNLIMITED' in record and 'Requeue=0' in record
subprocess.check_call(['scontrol','release',job])
receipt.update(released=True,resource_check='PASS',release_authority='Author 2026-10-26 all B2030 gates passed')
(root/'released_submission.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
''','submit_release');save(EVIDENCE/'released_submission.json',result);print(result)
    else:
        result=remote(r'''
receipt=json.loads((root/'held_submission.json').read_text());job=receipt['job_id']
assert job.isdigit() and job not in {'5201318','5207165'}
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
result=dict(job_id=job,scontrol=record)
for name in ['compute_node_smoke.json','startup_resources.json','batch_exit.json']:
 if (root/name).exists():result[name]=json.loads((root/name).read_text())
for name in ['stdout.log','stderr.log','resource_usage.txt','output_8760/gurobi.log']:
 if (root/name).exists():
  p=root/name
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-12000));result[name]=f.read().decode('utf-8',errors='replace')
print(json.dumps(result))
''',args.label);save(EVIDENCE/(args.label+'.json'),result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
