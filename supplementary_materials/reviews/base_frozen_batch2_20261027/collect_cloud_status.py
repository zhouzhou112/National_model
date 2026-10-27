"""One read-only scheduler/telemetry snapshot; no polling or job mutations."""
from pathlib import Path
import subprocess,json,datetime
HERE=Path(__file__).resolve().parent
code=r'''
from pathlib import Path
import subprocess,json,datetime,re
queue=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T|%M|%Z'],universal_newlines=True)
rows=[]
for line in queue.splitlines():
 job,name,state,elapsed,wd=line.split('|');root=Path(wd)
 row=dict(job_id=job,name=name,state=state,elapsed=elapsed,release=root.name)
 p=root/'output_8760/solver_telemetry.jsonl';events=[]
 if p.exists():
  with p.open() as f:
   for line in f:
    try:e=json.loads(line)
    except ValueError:continue
    if e.get('phase')=='barrier' and e.get('iteration') is not None:events.append(e)
 row['barrier_last_11']=events[-11:]
 for name in ['compute_node_smoke.json','startup_resources.json']:
  if (root/name).exists():row[name]=json.loads((root/name).read_text())
 for name in ['stderr.log','slurm-'+job+'.err']:
  p=root/name
  if p.exists():row[name]=p.read_text()[-3000:]
 rows.append(row)
failed=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v1')
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),active_jobs=rows,failed_b2060=dict(sacct=subprocess.check_output(['sacct','-j','5295127','-X','-n','-P','--format=JobID,State,ExitCode,Elapsed'],universal_newlines=True),stderr=(failed/'stderr.log').read_text(),batch_exit=json.loads((failed/'batch_exit.json').read_text())))))
'''
if __name__=='__main__':
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=code,text=True,capture_output=True,check=True)
 result=json.loads(p.stdout);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 out=HERE/('cloud_status_'+stamp+'.json');out.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(str(out));print('active',len(result['active_jobs']))
 for r in result['active_jobs']:
  last=r['barrier_last_11'][-1] if r['barrier_last_11'] else {}
  print(r['job_id'],r['name'],r['state'],r['elapsed'],last.get('iteration'),last.get('primal_infeasibility'),last.get('dual_infeasibility'),last.get('complementarity'),r.get('compute_node_smoke.json',{}).get('status'))
