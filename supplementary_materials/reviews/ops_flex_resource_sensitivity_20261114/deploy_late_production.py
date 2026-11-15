"""Single LATE-Open 2050 launch authorized explicitly on 2026-11-15.

Only this explicitly authorized production case is representable. Releases are never
overwritten. Each launch requires its own PASS gate and the common five items.
"""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
B_SOURCE=BASE+'/20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1'
LATE_SOURCE=BASE+'/20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'
TEMPLATE=HERE/'deployment/late_open_2050_factor5/job.sbatch'
INPUT_STAGE=BASE+'/_staging/ops_resource_sensitivity_20261114'
LICENSE_PATH='/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic'
CASES={
 'late_open_2050':dict(resource='open',kind='LATE_RESTRICTED_PRODUCTION',release='20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1'),
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def remote(root,code,dest,label,timeout=900):
    header='from pathlib import Path\nimport json,hashlib,subprocess,os,re,tarfile,shutil\nroot=Path('+repr(root)+')\n'
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=header+code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    (dest/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(dest/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr[-2000:]+p.stdout[-4000:])
    result=json.loads(p.stdout);save(dest/(label+'.json'),result);return result

def scientific_args(case,root,preflight=False):
    assert case=='late_open_2050'
    profile='barrier_stagea_resource_restricted_agg0_v1_threads44';scenario='ops_open_resource_v1'
    args=['--config','config/optimization_numeric_dac_by_year_v9_a12.json','--scenario-config','config/scenarios/'+scenario+'.json','--solver-config','config/solver_profiles/'+profile+'.json','--planning-year','2050','--horizon','full_year','--state-in',root+'/upstream_state/planning_state_candidate','--allow-candidate-state-in','--late-entry-base-state','--capacity-bound-selection',root+'/capacity_selection.json']
    if preflight:args+=['--preflight-only']
    else:args+=['--archive-original-model','--export-barrier-checkpoint','--allow-nonbasic-planning-state']
    args+=['--output-dir',root+('/preflight_v2' if preflight else '/output_8760')]
    return args,profile,scenario


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=CASES);p.add_argument('phase',choices=['prepare','preflight','submit-release','status']);a=p.parse_args()
    c=CASES[a.case];root=BASE+'/'+c['release'];dest=HERE/'deployment'/a.case;dest.mkdir(parents=True,exist_ok=True)
    args,profile,scenario=scientific_args(a.case,root)
    if a.phase=='prepare':
        gates=json.loads((HERE/'LATE_PRODUCTION_LAUNCH_GATES.json').read_text(encoding='utf-8'));assert gates['common_pre_submission']=='PASS' and gates['cases'][a.case]['status']=='PASS'
        assert gates['batch']==2 and gates['other_batch2_cases_authorized'] is False and gates['explicit_late_launch_authorization']=='启动LATE-Open，可以考量48核心吧'
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
        assert not subprocess.check_output(['git','diff','HEAD','--','cispo_model','scripts','config','tests'],cwd=REPO).strip(),'Commit reviewed executable sources first'
        tested=json.loads((HERE/'full_tests_v7.json').read_text())['tested_source_lf_sha256']
        template=TEMPLATE.read_bytes().replace(b'\r\n',b'\n').decode()
        expected_template=gates['template_sha256']
        assert hashlib.sha256(template.encode()).hexdigest()==expected_template
        marker='/usr/bin/time -v -o "$RELEASE_ROOT/resource_usage.txt"'
        assert template.count(marker)==1
        prefix=template[:template.index(marker)].replace('#SBATCH --job-name=late_open_2050_factor5_t44','#SBATCH --job-name='+a.case+'_t44')
        import shlex
        command=['scripts/run_resource_sensitivity_case.py','--resource',c['resource'],'--reference',root+'/resource_contract_reference.csv','--']+args
        batch=prefix+marker+' \\\n  "$PYTHON" '+shlex.join(command)+' \\\n  > "$RELEASE_ROOT/stdout.log" 2> "$RELEASE_ROOT/stderr.log"\n'
        (dest/'job.sbatch').write_bytes(batch.encode())
        launch=dict(release=c['release'],source_commit=commit,framework=c['kind'],resource_scenario=c['resource'],scenario='case3_thermal_ev_v5',scenario_config='config/scenarios/'+scenario+'.json',solver_profile='config/solver_profiles/'+profile+'.json',planning_year=2050,boundary_year=2040,batch=2,automatic_successor=False,license_path=LICENSE_PATH,template_release='20261115_lateopen_2050_restricted_factor5_t44_m750_v1',author_authorization='User 2026-11-15 explicitly authorized this LATE-Open 2050 launch before first batch ends; other batch2 cases remain unauthorized; retain validated 44 threads after assessing 48',resources=dict(cpus=64,memory='750G',billing=64,solver_threads=44,time_limit='UNLIMITED',requeue=False,minimum_available_memory_gib=700),diagnostic_only=False,maximum_barrier_iterations=None)
        save(dest/'launch_config.json',launch)
        gate=dict(status='PASS',framework=c['kind'],planning_year=2050,batch=2,case=a.case,common_gate_sha256=sha(HERE/'LATE_PRODUCTION_LAUNCH_GATES.json'),checks=gates['cases'][a.case],author_report_checkpoint_sha256=sha(HERE/'LATE_PRODUCTION_AUTHORIZATION.json'))
        save(dest/'FINAL_GATES_PASSED.json',gate)
        archive=subprocess.check_output(['git','archive',commit,'cispo_model','scripts','config','tests','AGENTS.md'],cwd=REPO)
        payload=dest/'release_payload.tar.gz';assert not payload.exists();hashes={};sources={}
        with tarfile.open(fileobj=io.BytesIO(archive)) as src,tarfile.open(payload,'w:gz') as dst:
            def add(n,raw):
                entry=tarfile.TarInfo(n);entry.size=len(raw);entry.mode=0o640;dst.addfile(entry,io.BytesIO(raw));hashes[n]=hashlib.sha256(raw).hexdigest()
            for e in src.getmembers():
                if e.isfile():
                    raw=src.extractfile(e).read();add('repo/'+e.name,raw);sources[e.name]=hashlib.sha256(raw).hexdigest()
                    if e.name.split('/')[0] in {'cispo_model','scripts','config','tests'} and Path(e.name).suffix in {'.py','.json'}:
                        assert tested.get(e.name)==sources[e.name], 'Committed source differs from complete regression: '+e.name
            for n in ['launch_config.json','FINAL_GATES_PASSED.json']:add(n,(dest/n).read_bytes())
            add('continuation.sbatch',batch.encode());add('resource_contract_reference.csv',(HERE/'contractable_total_national_source.csv').read_bytes())
            add('source_code_sha256.json',json.dumps(sources,indent=2).encode())
            if c['kind']=='LATE_RESTRICTED_PRODUCTION':
                selection=HERE/('D1_intra_selection.json' if c['kind']=='C5_DIAGNOSTIC' else 'LATE_Open_2050_fixed_selection.json');add('capacity_selection.json',selection.read_bytes())
        remote(root,"assert not root.exists()\nroot.mkdir()\nprint(json.dumps({'status':'CREATED','root':str(root)}))",dest,'create')
        subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',str(payload),'paracloud-bscc-a8:'+root+'/release_payload.tar.gz'],check=True)
        code='expected='+repr(hashes)+'\nexpected_data='+repr(json.loads((HERE.parent/'case3_2050_preparation_20261026/expected_data_files.json').read_text()))+'\nsource_b='+repr(B_SOURCE)+'\nsource_c='+repr(LATE_SOURCE)+'\ninput_stage='+repr(INPUT_STAGE)+'\nresource='+repr(c['resource'])+'\nkind='+repr(c['kind'])+'\npayload_sha='+repr(sha(payload))+'\n'+r'''
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(root/'release_payload.tar.gz') as tf:
 for e in tf.getmembers():assert e.isfile() and root.resolve() in (root/e.name).resolve().parents
 tf.extractall(root)
for n,h in expected.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
source=Path(source_b);data=root/'data_overlay';shutil.copytree(source/'data_overlay',data,symlinks=False)
for n,e in expected_data.items():
 p=data/n;assert p.stat().st_size==e['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],n
installed={}
if resource!='base':
 bundle=Path(input_stage)/'inputs'/resource;a=json.loads((bundle/'BUILD_AUDIT.json').read_text())
 for n,e in a['files'].items():
  p=bundle/n;assert p.stat().st_size==e['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],n
  if n.startswith(('load/','flexibility/')):
   target=data/n;target.parent.mkdir(parents=True,exist_ok=True);assert not target.is_symlink();shutil.copy2(p,target);assert hashlib.sha256(target.read_bytes()).hexdigest()==e['sha256'];installed[n]=e
 shutil.copy2(bundle/'BUILD_AUDIT.json',root/'input_BUILD_AUDIT.json')
import csv,gzip,itertools
with gzip.open(source/'data_overlay/load/hourly_load_2025_2060.csv.gz','rt') as f,gzip.open(data/'load/hourly_load_2025_2060.csv.gz','rt') as g:
 count=0
 for x,y in itertools.zip_longest(csv.DictReader(f),csv.DictReader(g)):
  assert x is not None and y is not None and x['demand_gw']==y['demand_gw'];count+=1
def check_copy(source,target):
 records={}
 for p in source.rglob('*'):
  if p.is_file():
   rel=p.relative_to(source);q=target/rel;h=hashlib.sha256(p.read_bytes()).hexdigest()
   assert q.stat().st_size==p.stat().st_size and hashlib.sha256(q.read_bytes()).hexdigest()==h,str(rel)
   records[str(rel)]=h
 return records
if kind=='LATE_RESTRICTED_PRODUCTION':
 shutil.copytree(Path(source_c)/'upstream_state',root/'upstream_state')
 upstream=check_copy(Path(source_c)/'upstream_state',root/'upstream_state')
 assert upstream['planning_state_candidate/state_metadata.json']=='2fe97c255aaed7329d5617ae858c0b97b31937b95c1ae41852750c36c2e48c63'
else:
 shutil.copytree(source/'frozen_source',root/'frozen_source');shutil.copy2(source/'frozen_closure.json',root/'frozen_closure.json')
 upstream=check_copy(source/'frozen_source',root/'frozen_source')
 assert hashlib.sha256((root/'frozen_closure.json').read_bytes()).hexdigest()=='ec2b4195fb82b2d39add75c6a0c043b1669150eb3f5a8123d661cbf92c6fac9a'
(root/'data_copy_verification.json').write_text(json.dumps(dict(status='PASS',production_files=len(expected_data),scenario_files=installed,inputs_regenerated=False,source_unchanged=True,demand_gw_rows=count,demand_gw_text_identical=True,upstream_sha256=upstream),indent=2)+'\n')
launch=json.loads((root/'launch_config.json').read_text());text=(root/'continuation.sbatch').read_text();assert ('export GRB_LICENSE_FILE="'+launch['license_path']+'"') in text
(root/'license_path_preflight.json').write_text(json.dumps(dict(status='PASS',path_only_checked=True,contents_read=False))+'\n')
files=[p for p in root.rglob('*') if p.is_file() and p.name not in ['release_files.sha256','release_payload.tar.gz']]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(files)))
print(json.dumps(dict(status='FROZEN',release=str(root),files=len(files),manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest())))
'''
        remote(root,code,dest,'freeze')
    elif a.phase=='preflight':
        import shlex
        argv,_,_=scientific_args(a.case,root,preflight=True)
        shell='set -euo pipefail\nset -a\nsource '+shlex.quote(ENV_SOURCE+'/manifests/cloud_environment_paths.env')+'\nset +a\nexport PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1\nexport PATH="$GUROBI_HOME/bin:$PATH"\nexport LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"\nexport CISPO_DATA_ROOT='+shlex.quote(root+'/data_overlay')+'\nexport PYTHONPATH='+shlex.quote(root+'/repo')+'"${PYTHONPATH:+:$PYTHONPATH}"\ncd '+shlex.quote(root+'/repo')+'\n"$PYTHON" scripts/run_cispo_2030_full_year.py '+shlex.join(argv)+' > '+shlex.quote(root+'/preflight_v2.log')+' 2>&1\n'
        remote(root,'shell='+repr(shell)+'\n'+r'''
assert not (root/'preflight_v2').exists() and not (root/'submission.json').exists()
subprocess.check_call(['bash','-n',str(root/'continuation.sbatch')])
p=subprocess.run(['bash'],input=shell,universal_newlines=True)
if p.returncode:raise RuntimeError((root/'preflight_v2.log').read_text()[-7000:])
r=json.loads((root/'preflight_v2/preflight_report.json').read_text());assert r['status']=='PASS'
print(json.dumps(dict(status='PASS',report=r)))
''',dest,'preflight_v2')
    elif a.phase=='submit-release':
        remote(root,'exports='+repr('ALL,SOURCE_RELEASE='+ENV_SOURCE)+'\n'+r'''
assert not (root/'submission.json').exists()
assert json.loads((root/'preflight_v2/preflight_report.json').read_text())['status']=='PASS'
assert json.loads((root/'FINAL_GATES_PASSED.json').read_text())['batch']==2
assert json.loads((root/'launch_config.json').read_text())['framework']=='LATE_RESTRICTED_PRODUCTION'
queue=subprocess.check_output(['squeue','--me','-h','-o','%i'],universal_newlines=True).splitlines();assert len(queue)<4,'At most four queued/running jobs'
p=subprocess.run(['sbatch','--hold','--parsable','--export='+exports,'continuation.sbatch'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
if p.returncode:raise RuntimeError(p.stderr)
job=p.stdout.strip().split(';')[0];assert job.isdigit()
record=dict(job_id=job,status='HELD',stdout=p.stdout,stderr=p.stderr);(root/'submission.json').write_text(json.dumps(record,indent=2)+'\n')
control=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert str(root) in control and 'JobHeldUser' in control and 'NumCPUs=64' in control and 'TimeLimit=UNLIMITED' in control and 'Requeue=0' in control
subprocess.check_call(['scontrol','release',job]);record.update(status='RELEASED',held_control=control);(root/'release_receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
''',dest,'release')
    else:
        remote(root,r'''
r={};p=root/'submission.json'
if p.exists():
 job=json.loads(p.read_text())['job_id'];r['job_id']=job;r['accounting']=subprocess.check_output(['sacct','-j',job,'-X','-n','-P','--format=JobID,State,ExitCode,Elapsed'],universal_newlines=True)
for n in ['startup_resources.json','compute_node_smoke.json','batch_exit.json','output_8760/resource_structure_audit.json','output_8760/solve_report.json']:
 p=root/n
 if p.exists():r[n]=json.loads(p.read_text())
if (root/'stderr.log').exists():r['stderr_tail']=(root/'stderr.log').read_text()[-2000:]
r['queue']=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T|%M'],universal_newlines=True);print(json.dumps(r))
''',dest,'status')

if __name__=='__main__':main()
