"""One read-only cloud snapshot; no watcher, retries, releases or solver actions."""
from pathlib import Path
import datetime,json,subprocess
from deploy_batch1 import BASE,CASES
from deploy_late_production import CASES as AUTHORIZED_LATE_CASES
from deploy_batch2 import CASES as AUTHORIZED_BATCH2_CASES
from deploy_batch3_conservative import CASES as AUTHORIZED_CONSERVATIVE_CASES
CASES={**CASES,**AUTHORIZED_LATE_CASES,**AUTHORIZED_BATCH2_CASES,**AUTHORIZED_CONSERVATIVE_CASES}
CASES['late_open_2060']=dict(resource='open',kind='LATE_RESTRICTED_PRODUCTION',release='20261119_lateopen_2060_restricted_t44_m750_tol1e4_v1')
HERE=Path(__file__).resolve().parent
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=HERE/'snapshots'/stamp;out.mkdir(parents=True,exist_ok=False)
code='base='+repr(BASE)+'\ncases='+repr(CASES)+'\n'+r'''
from pathlib import Path
import datetime,json,subprocess
def cmd(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 return dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
def tail(path,limit=5000):
 if not path.exists():return None
 with path.open('rb') as f:
  f.seek(max(0,path.stat().st_size-limit));return f.read().decode('utf-8',errors='replace')
result=dict(as_of_utc=datetime.datetime.utcnow().isoformat()+'Z',queue=cmd(['squeue','--me','-h','-o','%i|%j|%T|%M|%N']),cases={})
for case,meta in cases.items():
 root=Path(base)/meta['release'];r=dict(release=str(root),kind=meta['kind']);result['cases'][case]=r
 for name in ['submission.json','release_receipt.json','startup_resources.json','compute_node_smoke.json','batch_exit.json','output_8760/resource_structure_audit.json','output_8760/solve_report.json','output_8760/preservation_report.json','output_8760/unlimited_stage_a_parameters.json']:
  path=root/name
  if path.exists():r[name]=json.loads(path.read_text())
 if 'submission.json' in r:
  job=r['submission.json']['job_id'];r['accounting']=cmd(['sacct','-j',job,'-X','-n','-P','--format=JobID,State,ExitCode,Elapsed,Start,End,NodeList']);r['allocation']=cmd(['scontrol','show','job','-o',job]);r['rss']=cmd(['sstat','-j',job+'.batch','-n','-P','--format=JobID,MaxRSS,AveRSS'])
 for name in ['stdout.log','stderr.log','output_8760/gurobi.log','output_8760/solver_telemetry.jsonl']:
  text=tail(root/name)
  if text is not None:r[name+'_tail']=text
print(json.dumps(result))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=120)
(out/'transport.stderr.log').write_text(p.stderr,encoding='utf-8')
if p.returncode:raise RuntimeError(p.stderr)
result=json.loads(p.stdout);(out/'snapshot.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(path=str(out),as_of_utc=result['as_of_utc'],queue=result['queue'],cases={k:dict(accounting=v.get('accounting'),startup=v.get('startup_resources.json'),smoke=v.get('compute_node_smoke.json',{}).get('status'),structure=v.get('output_8760/resource_structure_audit.json',{}).get('status'),batch_exit=v.get('batch_exit.json'),stderr=v.get('stderr.log_tail')) for k,v in result['cases'].items()}),ensure_ascii=False))
