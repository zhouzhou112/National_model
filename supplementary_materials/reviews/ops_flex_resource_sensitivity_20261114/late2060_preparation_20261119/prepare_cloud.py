"""Freeze a reviewable LATE-Open2060 package and preflight it; cannot submit jobs."""
from pathlib import Path
import argparse,hashlib,io,json,shlex,subprocess,tarfile,re

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
REPO=WORK.parents[2]
BASE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
RELEASE='20261119_lateopen_2060_restricted_t44_m750_tol1e4_v1'
ROOT=BASE+'/'+RELEASE
ENV_SOURCE=BASE+'/20260903_8760_stagea_final_2820fc3_v3'
DATA_SOURCE=BASE+'/20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2'
INPUT_STAGE=BASE+'/_staging/ops_resource_sensitivity_20261114/inputs/open'
TEMPLATE_SOURCE='20261117_opsconservative_2060_v9a12_t44_m750_tol1e4_v1'
LICENSE='/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic'
DEST=HERE/'deployment'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def remote(code,label):
 header='from pathlib import Path\nimport json,hashlib,subprocess,os,tarfile,shutil\nroot=Path('+repr(ROOT)+')\n'
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=header+code,capture_output=True,text=True,encoding='utf-8',timeout=900)
 (DEST/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(DEST/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
 if p.returncode:raise RuntimeError(p.stderr[-4000:]+p.stdout[-2000:])
 result=json.loads(p.stdout);save(DEST/(label+'.json'),result);return result

def args(preflight=False):
 result=['--config','config/optimization_numeric_dac_by_year_v9_a12.json','--scenario-config','config/scenarios/ops_open_resource_v1.json','--solver-config','config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json','--planning-year','2060','--horizon','full_year','--state-in',ROOT+'/upstream_state/planning_state_candidate','--allow-candidate-state-in','--capacity-bound-selection',ROOT+'/capacity_selection.json']
 result+=['--preflight-only'] if preflight else ['--archive-original-model','--export-barrier-checkpoint','--allow-nonbasic-planning-state']
 return result+['--output-dir',ROOT+('/preflight' if preflight else '/output_8760')]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('phase',choices=['prepare','preflight','status']);a=ap.parse_args();DEST.mkdir(exist_ok=True)
 authorization=load(HERE/'AUTHORIZATION.json');assert authorization['submission_authorized'] is False and authorization['held_submission_authorized'] is False
 if a.phase=='prepare':
  gates=load(HERE/'FINAL_PREPARATION_GATES.json');assert gates['status']=='PASS' and gates['submitted'] is False
  for n,h in gates['local_evidence_sha256'].items():assert sha(HERE/n)==h,n
  assert not subprocess.check_output(['git','diff','HEAD','--','cispo_model','scripts','config','tests'],cwd=REPO).strip()
  source=load(HERE/'source_manifest.json');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
  codearchive=subprocess.check_output(['git','archive',commit,'cispo_model','scripts','config','tests','AGENTS.md'],cwd=REPO)
  template=(WORK/'batch3_conservative_20261117/deployment/ops_conservative_2060/job.sbatch').read_bytes().replace(b'\r\n',b'\n').decode();assert hashlib.sha256(template.encode()).hexdigest()==gates['template_sha256']
  marker='/usr/bin/time -v -o "$RELEASE_ROOT/resource_usage.txt"';assert template.count(marker)==1
  prefix,count=re.subn(r'#SBATCH --job-name=\S+','#SBATCH --job-name=late_open_2060_t44',template[:template.index(marker)]);assert count==1
  command=['scripts/run_resource_sensitivity_case.py','--resource','open','--reference',ROOT+'/resource_contract_reference.csv','--']+args()
  batch=prefix+marker+' \\\n  "$PYTHON" '+shlex.join(command)+' \\\n  > "$RELEASE_ROOT/stdout.log" 2> "$RELEASE_ROOT/stderr.log"\n'
  (DEST/'job.sbatch').write_bytes(batch.encode())
  launch=dict(release=RELEASE,source_commit=commit,framework='LATE_RESTRICTED_PRODUCTION',resource_scenario='open',scenario='case3_thermal_ev_v5',scenario_config='config/scenarios/ops_open_resource_v1.json',solver_profile='config/solver_profiles/barrier_stagea_resource_restricted_agg0_v1_threads44.json',planning_year=2060,boundary_year=2050,batch=3,automatic_successor=False,license_path=LICENSE,template_release=TEMPLATE_SOURCE,author_authorization='2026-11-19 PREPARATION ONLY; no submission including held jobs. Separate author release instruction required.',submission_authorized=False,resources=dict(cpus=64,memory='750G',billing=64,solver_threads=44,time_limit='UNLIMITED',requeue=False,minimum_available_memory_gib=700))
  save(DEST/'launch_config.json',launch);save(DEST/'FINAL_GATES_PASSED.json',dict(status='PASS',framework='LATE_RESTRICTED_PRODUCTION',planning_year=2060,submission_authorized=False,evidence_sha256=sha(HERE/'FINAL_PREPARATION_GATES.json')))
  payload=DEST/'release_payload.tar.gz';assert not payload.exists();expected={};sources={}
  with tarfile.open(fileobj=io.BytesIO(codearchive)) as src,tarfile.open(payload,'w:gz') as tf:
   def add(name,raw):
    ti=tarfile.TarInfo(name);ti.size=len(raw);ti.mode=0o640;tf.addfile(ti,io.BytesIO(raw));expected[name]=hashlib.sha256(raw).hexdigest()
   for member in src.getmembers():
    if not member.isfile():continue
    raw=src.extractfile(member).read()
    if member.name!='AGENTS.md':assert hashlib.sha256(raw).hexdigest()==source['files'][member.name]['sha256'],member.name
    add('repo/'+member.name,raw);sources[member.name]=hashlib.sha256(raw).hexdigest()
   upstream=HERE/'t550_evidence/R1_v1/prepared_state';state_manifest=load(upstream/'result_manifest.json')
   for e in state_manifest['files']:
    p=upstream/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];add('upstream_state/'+e['path'],p.read_bytes())
   add('upstream_state/result_manifest.json',(upstream/'result_manifest.json').read_bytes())
   selection=HERE/'t550_evidence/final_selection.json';assert sha(selection)==gates['selection_sha256'];add('capacity_selection.json',selection.read_bytes())
   for n in ['launch_config.json','FINAL_GATES_PASSED.json']:add(n,(DEST/n).read_bytes())
   add('continuation.sbatch',batch.encode());add('resource_contract_reference.csv',(WORK/'contractable_total_national_source.csv').read_bytes());add('source_code_sha256.json',json.dumps(sources,indent=2).encode());add('preparation_authorization.json',(HERE/'AUTHORIZATION.json').read_bytes());add('preparation_gate_evidence.json',(HERE/'FINAL_PREPARATION_GATES.json').read_bytes())
  remote("assert not root.exists()\nroot.mkdir()\nprint(json.dumps({'status':'CREATED','root':str(root)}))",'create')
  subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=15',str(payload),'paracloud-bscc-a8:'+ROOT+'/release_payload.tar.gz'],check=True)
  data_expected=load(WORK/'batch2/cloud_source_file_sha256.json')['2060']['data_overlay']
  remote('expected='+repr(expected)+'\nbase_data='+repr(DATA_SOURCE)+'\ninput_stage='+repr(INPUT_STAGE)+'\ndata_expected='+repr(data_expected)+'\npayload_sha='+repr(sha(payload))+'\ninput_sha='+repr(gates['open_BUILD_AUDIT_sha256'])+'\n'+r'''
assert hashlib.sha256((root/'release_payload.tar.gz').read_bytes()).hexdigest()==payload_sha
with tarfile.open(root/'release_payload.tar.gz') as tf:
 for e in tf.getmembers():assert e.isfile() and not Path(e.name).is_absolute() and '..' not in Path(e.name).parts
 tf.extractall(root)
for n,h in expected.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
source=Path(base_data)/'data_overlay';data=root/'data_overlay';shutil.copytree(source,data,symlinks=False)
for n,e in data_expected.items():assert (data/n).stat().st_size==e['bytes'] and hashlib.sha256((data/n).read_bytes()).hexdigest()==e['sha256'],n
bundle=Path(input_stage);assert hashlib.sha256((bundle/'BUILD_AUDIT.json').read_bytes()).hexdigest()==input_sha;a=json.loads((bundle/'BUILD_AUDIT.json').read_text())
for n,e in a['files'].items():
 p=bundle/n;assert p.stat().st_size==e['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],n
 if n.startswith(('load/','flexibility/')):
  q=data/n;q.parent.mkdir(parents=True,exist_ok=True);assert not q.is_symlink();shutil.copy2(p,q);assert hashlib.sha256(q.read_bytes()).hexdigest()==e['sha256']
shutil.copy2(bundle/'BUILD_AUDIT.json',root/'input_BUILD_AUDIT.json')
import csv,gzip,itertools
with gzip.open(source/'load/hourly_load_2025_2060.csv.gz','rt') as f,gzip.open(data/'load/hourly_load_2025_2060.csv.gz','rt') as g:
 count=0
 for x,y in itertools.zip_longest(csv.DictReader(f),csv.DictReader(g)):assert x and y and x['demand_gw']==y['demand_gw'];count+=1
launch=json.loads((root/'launch_config.json').read_text());assert launch['submission_authorized'] is False
assert ('export GRB_LICENSE_FILE="'+launch['license_path']+'"') in (root/'continuation.sbatch').read_text()
(root/'license_path_preflight.json').write_text(json.dumps(dict(status='PASS',path_only_checked=True,contents_read=False))+'\n')
(root/'data_copy_verification.json').write_text(json.dumps(dict(status='PASS',inputs_regenerated=False,scenario_files=len(a['files']),demand_gw_rows=count,demand_gw_text_identical=True))+'\n')
files=[p for p in root.rglob('*') if p.is_file() and p.name not in ['release_files.sha256','release_payload.tar.gz']]
(root/'release_files.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(files)))
print(json.dumps(dict(status='FROZEN_NOT_SUBMITTED',files=len(files),manifest_sha256=hashlib.sha256((root/'release_files.sha256').read_bytes()).hexdigest(),submission_authorized=False)))
''','freeze')
 elif a.phase=='preflight':
  shell='set -euo pipefail\nset -a\nsource '+shlex.quote(ENV_SOURCE+'/manifests/cloud_environment_paths.env')+'\nset +a\nexport PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1\nexport PATH="$GUROBI_HOME/bin:$PATH"\nexport LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"\nexport CISPO_DATA_ROOT='+shlex.quote(ROOT+'/data_overlay')+'\nexport PYTHONPATH='+shlex.quote(ROOT+'/repo')+'"${PYTHONPATH:+:$PYTHONPATH}"\ncd '+shlex.quote(ROOT+'/repo')+'\n"$PYTHON" scripts/run_cispo_2030_full_year.py '+shlex.join(args(True))+' > '+shlex.quote(ROOT+'/preflight.log')+' 2>&1\n'
  remote('shell='+repr(shell)+'\n'+r'''
assert not (root/'preflight').exists() and not (root/'submission.json').exists()
assert json.loads((root/'launch_config.json').read_text())['submission_authorized'] is False
subprocess.check_call(['sha256sum','--status','-c','release_files.sha256'],cwd=root)
subprocess.check_call(['bash','-n',str(root/'continuation.sbatch')])
p=subprocess.run(['bash'],input=shell,universal_newlines=True)
if p.returncode:raise RuntimeError((root/'preflight.log').read_text()[-7000:])
r=json.loads((root/'preflight/preflight_report.json').read_text());assert r['status']=='PASS'
print(json.dumps(dict(status='PASS_NOT_SUBMITTED',report=r,submission_authorized=False)))
''','preflight')
 else:
  remote("assert not (root/'submission.json').exists()\nprint(json.dumps(dict(submitted=False,queue=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T'],universal_newlines=True))))",'status')

if __name__=='__main__':main()
