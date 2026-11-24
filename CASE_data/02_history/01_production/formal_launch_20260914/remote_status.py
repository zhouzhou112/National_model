from pathlib import Path
import subprocess,json,datetime,re
root=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v2')
out=dict(queried_at_utc=datetime.datetime.utcnow().isoformat()+'Z')
for name,args in [('new_job',['scontrol','show','job','-o','4613045']),('queue',['squeue','-u','a8s001819','-h','-o','%i %j %T %M %C %m %R']),('start_estimate',['squeue','--start','-j','4613045','-h','-o','%i %T %S %R'])]:
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 out[name]=dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
for name in ['compute_node_smoke.json','batch_exit.json','runtime_slurm_job.txt']:
 p=root/name
 if p.is_file():out[name]=p.read_text()
for name in ['stdout.log','stderr.log','slurm-4613045.out','slurm-4613045.err']:
 p=root/name
 if p.is_file():
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-6000));tail=f.read().decode('utf-8','replace').splitlines()[-16:]
  out[name]=[line for line in tail if not re.search('license|wls|secret|accessid|token|password',line,re.I)]
print(json.dumps(out,indent=2))
