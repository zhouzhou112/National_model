"""Verify the existing autonomous backup before any acceptance computation."""
from pathlib import Path
import json, subprocess

REMOTE=r'''
from pathlib import Path
import json,subprocess,hashlib,datetime,shutil,socket
base=Path('/home/zz2/National_model_server/cloud_backup');rel='20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1';b=base/rel;op=base/'_operations/20261114_case3_2060_completed'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(8*1024**2),b''):h.update(x)
 return h.hexdigest()
status=json.loads((op/'transfer_status.json').read_text());launch=json.loads((op/'launch.json').read_text())
assert launch['pid']==1081649 and status['status']=='COMPLETE' and status['source_unchanged'],status
manifest=json.loads((b/'backup_manifest.json').read_text());plan=json.loads((op/'backup_plan.json').read_text())
assert {s['tier'] for s in status['stages']}=={'T1','T2','T3'} and all(s['status']=='VERIFIED' for s in status['stages'])
assert manifest['status']=='COMPLETE' and manifest['source_unchanged_after_transfer'] and not manifest.get('deferred_files')
assert manifest['files']==plan['releases'][rel]['files'] and manifest['source_result_manifest_sha256']==plan['releases'][rel]['result_manifest_sha256']
for e in manifest['files']:
 p=b/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
assert sha(b/'output_8760/result_manifest.json')==manifest['source_result_manifest_sha256']
source='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+rel+'/output_8760/result_manifest.json'
x=subprocess.run(['ssh','-F','/home/zz2/.ssh/paracloud_backup_20261012/ssh_config','paracloud-backup','sha256sum',source],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30);assert x.returncode==0,x.stderr;assert x.stdout.split()[0]==manifest['source_result_manifest_sha256']
proc=subprocess.run(['ps','-p','1081649','-o','pid,ppid,stat,args'],stdout=subprocess.PIPE,text=True).stdout
sidecars={n:(b/n).exists() for n in ['acceptance_20261114','postprocess_20261114','author_review_20261114']};assert not any(sidecars.values())
r=dict(status='COMPLETE_VERIFIED_BEFORE_ACCEPTANCE',verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host=socket.gethostname(),pid_process=proc,transfer_status=status,backup_manifest=manifest,backup_manifest_sha256=sha(b/'backup_manifest.json'),source_result_manifest_sha256=manifest['source_result_manifest_sha256'],current_cloud_source_manifest_matches=True,all_original_target_bytes_sha_match=True,sidecars=sidecars,disk_free=shutil.disk_usage(base).free,launch_config=json.loads((b/'launch_config.json').read_text()),frozen_source_hashes=json.loads((b/'cloud_source_repo_sha256.json').read_text()))
print(json.dumps(r))
'''

if __name__=='__main__':
 w=Path(__file__).resolve().parent;target=w/'backup_precheck.json';assert not target.exists()
 ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
 p=subprocess.run(ssh+['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -'],input=REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=180)
 (w/'verified_precheck.stderr.log').write_text(p.stderr);p.check_returncode();r=json.loads(p.stdout)
 target.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in r.items() if k not in ['backup_manifest','frozen_source_hashes','launch_config']},ensure_ascii=False))
