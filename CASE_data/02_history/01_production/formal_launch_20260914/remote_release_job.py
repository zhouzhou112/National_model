from pathlib import Path
import subprocess,json,re,datetime
root=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v2')
held=json.loads((root/'held_submission.json').read_text());job=held['job_id']
assert job=='4613045'
record=subprocess.check_output(['scontrol','show','job','-o',job],universal_newlines=True)
def field(key):
 m=re.search(r'\b'+key+r'=(\S+)',record)
 assert m,key
 return m.group(1)
assert field('Reason')=='JobHeldUser'
assert field('TimeLimit')=='UNLIMITED'
req=dict(x.split('=',1) for x in field('ReqTRES').split(','))
assert req['cpu']=='64' and req['mem']=='750G' and req['billing']=='64'
assert field('WorkDir')==str(root)
p=subprocess.run(['scontrol','release',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
r=dict(job_id=job,released_at_utc=datetime.datetime.utcnow().isoformat()+'Z',verified_requested_resources=req,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
(root/'release_job.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
raise SystemExit(p.returncode)
