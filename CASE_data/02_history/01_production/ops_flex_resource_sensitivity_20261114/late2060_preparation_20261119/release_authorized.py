"""Release only the already frozen LATE-Open2060 package under 2026-11-19 approval."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
from prepare_cloud import ROOT,ENV_SOURCE,LICENSE,HERE,sha,load

OUT=HERE/'release_20261119'
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

SUBMIT=r'''
from pathlib import Path
import json,hashlib,subprocess,datetime,re
root=Path(root)
assert not (root/'submission.json').exists(),'Existing job requires read-only inspection; never duplicate'
assert not (root/'output_8760').exists() and not (root/'batch_exit.json').exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(root/'release_files.sha256')==expected['release_manifest_sha256']
subprocess.check_call(['sha256sum','--status','-c','release_files.sha256'],cwd=root)
assert sha(root/'capacity_selection.json')==expected['selection_sha256']
assert sha(root/'continuation.sbatch')==expected['script_sha256']
launch=json.loads((root/'launch_config.json').read_text());gates=json.loads((root/'FINAL_GATES_PASSED.json').read_text());pre=json.loads((root/'preflight/preflight_report.json').read_text())
assert gates['status']==pre['status']=='PASS' and launch['planning_year']==2060 and launch['boundary_year']==2050
assert launch['license_path']==license_path and ('export GRB_LICENSE_FILE="'+license_path+'"') in (root/'continuation.sbatch').read_text()
profile=json.loads((root/'repo'/launch['solver_profile']).read_text())['numerics']
for k,v in dict(threads=44,method=2,crossover=0,aggregate=0,numeric_focus=2,barrier_convergence_tolerance=1e-4).items():assert profile[k]==v,(k,profile[k])
assert profile['time_limit_seconds'] is None
selection=json.loads((root/'capacity_selection.json').read_text());assert sum(r['state']=='free' for r in selection['columns'])==4879
queue=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T'],universal_newlines=True);assert len(queue.splitlines())<4
record=dict(status='PRE_RELEASE_RECHECK_PASS',as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_files_verified=True,expected=expected,queue_before=queue,license_path_only=True,credential_contents_read=False)
(root/'release_recheck_20261119.json').write_text(json.dumps(record,indent=2)+'\n')
auth.update(as_of_utc=record['as_of_utc'],frozen_preparation_records_retained=True)
assert not (root/'author_release_20261119.json').exists();(root/'author_release_20261119.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n')
p=subprocess.run(['sbatch','--hold','--parsable','--export=ALL,SOURCE_RELEASE='+env_source,'continuation.sbatch'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
if p.returncode:raise RuntimeError(p.stderr)
job=p.stdout.strip().split(';')[0];assert job.isdigit();submission=dict(job_id=job,status='HELD',stdout=p.stdout,stderr=p.stderr,author_authorization='author_release_20261119.json');(root/'submission.json').write_text(json.dumps(submission,indent=2)+'\n')
control=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
assert str(root) in control and 'JobHeldUser' in control and 'NumCPUs=64' in control and 'TimeLimit=UNLIMITED' in control and 'Requeue=0' in control
tres=re.search(r'\bReqTRES=(\S+)',control).group(1);assert 'cpu=64' in tres and 'mem=750G' in tres and 'billing=64' in tres
subprocess.check_call(['scontrol','release',job]);result=dict(job_id=job,status='RELEASED',held_control=control,pre_release_recheck=record,author_authorization=auth)
(root/'release_receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
'''

STATUS=r'''
from pathlib import Path
import json,subprocess,datetime
root=Path(root);r={'as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for n in ['submission.json','release_receipt.json','startup_resources.json','compute_node_smoke.json','batch_exit.json','output_8760/resource_structure_audit.json','output_8760/solve_report.json','output_8760/preservation_report.json']:
 if (root/n).exists():r[n]=json.loads((root/n).read_text())
if 'submission.json' in r:
 job=r['submission.json']['job_id'];r['accounting']=subprocess.check_output(['sacct','-j',job,'-X','-n','-P','--format=JobID,State,ExitCode,Elapsed,Start,End,NodeList'],universal_newlines=True)
 control=subprocess.run(['scontrol','show','job','-o',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 r['control']=control.stdout;r['control_returncode']=control.returncode;r['control_stderr']=control.stderr
for n in ['stderr.log','stdout.log','output_8760/gurobi.log']:
 p=root/n
 if p.exists():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-2500));r[n]=f.read().decode(errors='replace')
r['queue']=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T|%M|%R'],universal_newlines=True);print(json.dumps(r))
'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['submit-release','status']);a=ap.parse_args();OUT.mkdir(exist_ok=True)
 receipt=load(HERE/'PREPARATION_RECEIPT.json');assert receipt['status']=='READY_NOT_SUBMITTED'
 expected=dict(release_manifest_sha256=receipt['release_manifest_sha256'],selection_sha256=receipt['selection_sha256'],script_sha256=sha(HERE/'deployment/job.sbatch'))
 auth=dict(date='2026-11-19',authorization='User explicitly requested continuing the solve after reviewing preparation; engineering readiness explained without promising convergence or unrestricted optimality',user_instruction='也就是说是高度靠谱的对吗，如果是就继续求解吧',release=receipt['release'],submission_authorized=True,automatic_resolve=False,resources=dict(threads=44,cpus=64,memory='750G',time_limit='UNLIMITED',requeue=False,minimum_available_memory_gib=700))
 if a.phase=='submit-release':
  assert not (OUT/'release.json').exists();save(OUT/'AUTHORIZATION.json',auth)
 code='root='+repr(ROOT)+'\nexpected='+repr(expected)+'\nlicense_path='+repr(LICENSE)+'\nenv_source='+repr(ENV_SOURCE)+'\nauth='+repr(auth)+'\n'+(SUBMIT if a.phase=='submit-release' else STATUS)
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=180)
 label='release' if a.phase=='submit-release' else 'status_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 (OUT/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
 if p.returncode:raise RuntimeError(p.stderr[-4000:]+p.stdout[-2000:])
 r=json.loads(p.stdout);save(OUT/(label+'.json'),r)
 if a.phase=='submit-release':print(json.dumps(dict(job_id=r['job_id'],status=r['status'],frozen_recheck=r['pre_release_recheck']['status'])))
 else:print(json.dumps({k:v for k,v in r.items() if k not in ['release_receipt.json','control','output_8760/solve_report.json','output_8760/resource_structure_audit.json']}))

if __name__=='__main__':main()
