"""Freeze, preflight and explicitly launch the four author-approved continuations.

Each phase is finite, refuses duplicate mutation, and targets only its new
release. No running releases are changed; no scheduler/watch service is made.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
HOST='paracloud-bscc-a8'
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
SOURCES={2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):Path(p).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',choices=['B2040','B2050','B2060'])
    parser.add_argument('phase',choices=['prepare','preflight','submit','release','status'])
    parser.add_argument('--version',type=int,default=1)
    args=parser.parse_args();year=int(args.case[1:]);is_a=args.case[0]=='A';threads=40 if is_a else 48
    assert args.version>=1
    work=HERE.parent/'case3_2050_launch_20261027' if is_a else HERE/str(year)
    evidence=work/('deployment' if args.version==1 else f'deployment_v{args.version}');evidence.mkdir(parents=True,exist_ok=True)
    name=('20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1' if is_a else
          f'20261027_basefrozen_{year}_v9a12_agg0_t48_m750_tol1e4_v1')
    name=name[:-1]+str(args.version)
    root=BASE+'/'+name
    profile=('config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json' if is_a else
             'config/solver_profiles/barrier_stagea_base_frozen_agg0_v1_threads48.json')
    batch=work/'continuation.sbatch' if is_a else HERE/f'B{year}.sbatch'
    gates_path=(HERE.parent/'base_frozen_closure_20261027/2060/attempt_2/FINAL_GATES_PASSED.json') if year==2060 else work/'FINAL_GATES_PASSED.json'
    closure_path=HERE.parent/'base_frozen_closure_20261027'/str(year)/'derived_static/closure.json'
    license_path=json.loads((HERE.parent/'base_frozen_B_20261026/deployment_v3/launch_config.json').read_text())['license_path']
    def remote(code,label):
        header='from pathlib import Path\nimport json,hashlib,subprocess,os,re,tarfile\nroot=Path('+repr(root)+')\n'
        p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',HOST,'python3 -'],input=header+code,text=True,capture_output=True,timeout=900)
        (evidence/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(evidence/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
        if p.returncode:raise RuntimeError(p.stderr[-2500:]+p.stdout[-4500:])
        result=json.loads(p.stdout);save(evidence/(label+'.json'),result);return result
    if is_a:
        scientific_args=f'--vre-screen-csv "{root}/source_screen.csv" --state-in "{root}/upstream_state/planning_state_candidate" --allow-candidate-state-in'
    else:
        source=SOURCES[year]
        scientific_args=f'--frozen-capacity-from "{root}/frozen_source/{source}/output_8760" --frozen-capacity-supplement "{root}/frozen_source/{source}/frozen_capacity_B_20261027" --frozen-capacity-closure "{root}/frozen_closure.json"'
    if args.phase=='prepare':
        gates=json.loads(gates_path.read_text());assert gates['status']=='PASS' and gates['planning_year']==year and gates['framework']==args.case[0]
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        assert not subprocess.check_output(['git','diff','HEAD','--','cispo_model','scripts','config','tests'],cwd=REPO).strip()
        for path,h in gates['tested_source_lf_sha256'].items():
            assert hashlib.sha256(subprocess.check_output(['git','show',commit+':'+path],cwd=REPO)).hexdigest()==h,path
        assert subprocess.check_output(['git','show',commit+':'+batch.relative_to(REPO).as_posix()],cwd=REPO)==batch.read_bytes().replace(b'\r\n',b'\n')
        if is_a:
            cert=json.loads((HERE.parent/'completed_results_20261027/case3_2040/price_receipt.json').read_text())
            assert cert['scope']=='FULL_YEAR' and cert['B_over_objective']<=1e-2
        else:
            performance=json.loads((HERE.parent/'completed_results_20261027/B2030_performance_summary.json').read_text())
            assert performance['peak_rss_gib']<=650 and performance['threads']==48
        expected=json.loads((HERE.parent/'case3_2050_preparation_20261026/expected_data_files.json').read_text())
        launch=dict(release=name,source_commit=commit,framework=args.case[0],planning_year=year,
                    boundary_year=year-10,scenario='case3_thermal_ev_v5',solver_profile=profile,
                    license_path=license_path,author_authorization='AGENTS.md 2026-10-27 second batch: each year independently releases after gates',
                    static_closure_payload_sha256=sha(closure_path),annual_carbon_limit_unchanged=True,
                    template_release='20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',
                    frozen_capacity_from=None if is_a else SOURCES[year],
                    state_input='upstream_state/planning_state_candidate' if is_a else 'AUTO_RECOVER_FROM_FROZEN_SOURCE',
                    candidate_screen=is_a,automatic_successor=False,
                    resources=dict(cpus=64,memory='750G',billing=64,solver_threads=threads,time_limit='UNLIMITED',requeue=False,minimum_available_memory_gib=700))
        save(evidence/'launch_config.json',launch)
        payload=evidence/'release_payload.tar.gz';assert not payload.exists()
        archive=subprocess.check_output(['git','archive',commit,'cispo_model','config','scripts','tests','AGENTS.md'],cwd=REPO)
        source_hashes={};payload_hashes={}
        with tarfile.open(fileobj=io.BytesIO(archive)) as src,tarfile.open(payload,'w:gz') as dst:
            def add(name,raw):
                item=tarfile.TarInfo(name);item.size=len(raw);item.mode=0o640;dst.addfile(item,io.BytesIO(raw));payload_hashes[name]=hashlib.sha256(raw).hexdigest()
            for item in src.getmembers():
                if item.isfile():
                    raw=src.extractfile(item).read();add('repo/'+item.name,raw);source_hashes[item.name]=hashlib.sha256(raw).hexdigest()
            add('continuation.sbatch',batch.read_bytes().replace(b'\r\n',b'\n'))
            add('launch_config.json',(evidence/'launch_config.json').read_bytes());add('FINAL_GATES_PASSED.json',gates_path.read_bytes())
            for name,row in expected.items():
                path=REPO/'data'/name;assert sha(path)==row['sha256'] and path.stat().st_size==row['bytes'],name
            add('expected_data_files.json',json.dumps(expected,indent=2).encode())
            if is_a:
                for path in sorted((work/'R1_v2/prepared_state').rglob('*')):
                    if path.is_file():add('upstream_state/'+path.relative_to(work/'R1_v2/prepared_state').as_posix(),path.read_bytes())
                add('source_screen.csv',(HERE.parent/'case3_2030_launch_20261014/P4_ready2050_20261015/source_screen.csv').read_bytes())
                add('upstream_pricing_receipt.json',(HERE.parent/'completed_results_20261027/case3_2040/price_receipt.json').read_bytes())
            else:
                add('frozen_closure.json',closure_path.read_bytes())
                srcroot=HERE.parent/'base_frozen_followups_20261027/source_base'/SOURCES[year]
                for path in sorted(srcroot.rglob('*')):
                    if path.is_file():add('frozen_source/'+SOURCES[year]+'/'+path.relative_to(srcroot).as_posix(),path.read_bytes())
        remote("assert not root.exists()\nroot.mkdir()\nprint(json.dumps({'created':str(root)}))",'create')
        subprocess.run(['scp','-o','BatchMode=yes',str(payload),HOST+':'+root+'/release_payload.tar.gz'],check=True)
        remote('payload_sha='+repr(sha(payload))+'\nexpected='+repr(payload_hashes)+'\nsource_hashes='+repr(source_hashes)+'\n'+r'''
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(str(root/'release_payload.tar.gz')) as archive:
 for item in archive.getmembers():
  path=Path(item.name);assert item.isfile() and not path.is_absolute() and '..' not in path.parts and not (root/path).exists()
 archive.extractall(str(root))
for name,h in expected.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h,name
import shutil
data_source=root.parent/'_preparations/20261026_case3_2050_t40_v1/data_overlay'
data_expected=json.loads((root/'expected_data_files.json').read_text())
for name,row in data_expected.items():
 source=data_source/name;target=root/'data_overlay'/name
 assert source.stat().st_size==row['bytes'] and hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'],name
 assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(str(source),str(target))
 assert not target.is_symlink() and target.stat().st_size==row['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256'],name
(root/'data_copy_verification.json').write_text(json.dumps({'status':'PASS','source':str(data_source),'files':len(data_expected),'method':'SHA_VERIFIED_INDEPENDENT_COPIES'},indent=2))
launch=json.loads((root/'launch_config.json').read_text());batch=(root/'continuation.sbatch').read_text()
registered=json.loads((root.parent/'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3/launch_config.json').read_text())['license_path']
assert re.findall(r'^export GRB_LICENSE_FILE="([^"\n]+)"$',batch,re.M)==[registered] and launch['license_path']==registered
(root/'license_path_preflight.json').write_text(json.dumps({'status':'PASS','comparison':'STRING_ONLY','credential_contents_read':False,'registered_path':registered},indent=2))
(root/'cloud_source_repo_sha256.json').write_text(json.dumps(source_hashes,indent=2))
subprocess.check_call(['bash','-n',str(root/'continuation.sbatch')])
paths=[p for p in root.rglob('*') if p.is_file()]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(paths)))
print(json.dumps({'status':'FROZEN','release':str(root),'files':len(paths),'source_commit':launch['source_commit'],'release_manifest_sha256':hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest()}))
''','freeze')
    elif args.phase=='preflight':
        script=f'''set -euo pipefail
set -a
source "{ENV_SOURCE}/manifests/cloud_environment_paths.env"
set +a
export PATH="$GUROBI_HOME/bin:$PATH" LD_LIBRARY_PATH="$GUROBI_HOME/lib:${{LD_LIBRARY_PATH:-}}"
export GRB_LICENSE_FILE="{license_path}"
export http_proxy="${{CISPO_CLOUD_PROXY:-http://172.16.110.3:8888}}"
export https_proxy="$http_proxy" HTTP_PROXY="$http_proxy" HTTPS_PROXY="$http_proxy"
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS={threads} OPENBLAS_NUM_THREADS={threads} MKL_NUM_THREADS={threads}
export CISPO_DATA_ROOT="{root}/data_overlay" PYTHONPATH="{root}/repo${{PYTHONPATH:+:$PYTHONPATH}}"
cd "{root}/repo"
"$PYTHON" scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9_a12.json --scenario-config config/scenarios/case3_thermal_ev_v5.json --solver-config {profile} --planning-year {year} {scientific_args} --horizon full_year --allow-nonbasic-planning-state --preflight-only --output-dir "{root}/preflight" > "{root}/preflight.log" 2>&1
'''
        remote('script='+repr(script)+'\n'+r'''
assert not (root/'preflight').exists() and not (root/'submission_attempt.json').exists()
assert json.loads((root/'license_path_preflight.json').read_text())['status']=='PASS'
p=subprocess.run(['bash'],input=script,universal_newlines=True)
if p.returncode:raise RuntimeError((root/'preflight.log').read_text()[-6000:])
r=json.loads((root/'preflight/preflight_report.json').read_text());assert r['status']=='PASS'
print(json.dumps({'status':'PASS','report':r}))
''','preflight')
    elif args.phase=='submit':
        remote('exports='+repr('ALL,SOURCE_RELEASE='+ENV_SOURCE)+'\n'+r'''
assert json.loads((root/'preflight/preflight_report.json').read_text())['status']=='PASS'
assert not (root/'submission_attempt.json').exists(),'Never repeat uncertain submission'
subprocess.check_call(['sha256sum','--quiet','-c','release_files.sha256'],cwd=str(root))
queue=subprocess.check_output(['squeue','--me','--noheader','-o','%i'],universal_newlines=True).splitlines();assert len(queue)<10
p=subprocess.run(['sbatch','--test-only','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True);assert p.returncode==0,p.stderr
(root/'submission_attempt.json').write_text(json.dumps({'test_stdout':p.stdout,'test_stderr':p.stderr}))
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'continuation.sbatch'],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
r={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'released':False};(root/'held_submission.json').write_text(json.dumps(r));assert p.returncode==0,r
job=p.stdout.strip().split(';')[0];assert job.isdigit() and job not in {'5207165','5294579'}
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
tres=dict(v.split('=',1) for v in re.search(r'\bReqTRES=(\S+)',record).group(1).split(','))
assert tres['cpu']=='64' and tres['billing']=='64' and tres['mem'] in ['750G','768000M']
assert 'TimeLimit=UNLIMITED' in record and 'Requeue=0' in record and 'Reason=JobHeldUser' in record
r.update(job_id=job,scontrol=record,resource_check='PASS');(root/'held_submission.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
''','held_submission')
    elif args.phase=='release':
        remote(r'''
r=json.loads((root/'held_submission.json').read_text());assert r['resource_check']=='PASS' and not r['released']
assert not (root/'release_attempt.json').exists()
job=r['job_id'];assert job.isdigit() and job not in {'5207165','5294579'}
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert 'Reason=JobHeldUser' in record and ('WorkDir='+str(root)) in record
(root/'release_attempt.json').write_text(json.dumps({'job_id':job}))
subprocess.check_call(['scontrol','release',job]);r['released']=True
(root/'released_submission.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
''','released_submission')
    else:
        remote(r'''
r=json.loads((root/'held_submission.json').read_text());job=r['job_id'];assert job not in {'5207165','5294579'}
r['scontrol_current']=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
for name in ['compute_node_smoke.json','startup_resources.json','batch_exit.json']:
 if (root/name).exists():r[name]=json.loads((root/name).read_text())
for name in ['stdout.log','stderr.log']:
 p=root/name
 if p.exists():
  with p.open('rb') as stream:stream.seek(max(0,p.stat().st_size-2500));r[name]=stream.read().decode('utf-8',errors='replace')
print(json.dumps(r))
''','status')
    print(args.case,args.phase,'completed')


if __name__=='__main__':main()
