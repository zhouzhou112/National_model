"""One-shot T550 pull of terminal B2060 v1 evidence; not a solved-result backup."""
from pathlib import Path
import subprocess,sys
from t550_validation import SSH
HERE=Path(__file__).resolve().parent
RELEASE='20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v1'
SOURCE='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+RELEASE
INVENTORY=r'''
from pathlib import Path
import hashlib,json,subprocess
root=Path(SOURCE)
state=subprocess.check_output(['sacct','-j','5295127','-X','-n','-P','--format=JobID,State,ExitCode'],universal_newlines=True).strip()
assert state.startswith('5295127|FAILED|'),state
assert (root/'batch_exit.json').exists()
paths=list((root/'output_8760').rglob('*'))
paths += [p for p in root.iterdir() if p.is_file() and (p.suffix in {'.json','.log','.txt','.sbatch','.out','.err'} or p.name=='release_files.sha256')]
paths+=list((root/'preflight').rglob('*'))
files=[]
for p in sorted(set(paths)):
 if p.is_file():
  assert not p.is_symlink()
  files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
print(json.dumps(dict(state=state,files=files)))
'''
code=f'''
from pathlib import Path
import json,subprocess,hashlib,shutil,fcntl,datetime
base=Path('/home/zz2/National_model_server/cloud_backup');dest=base/{RELEASE!r}
op=base/'_operations/20261027_B2060_v1_failed';op.mkdir(exist_ok=True)
ssh=['ssh','-F','/home/zz2/.ssh/paracloud_backup_20261012/ssh_config','paracloud-backup']
inventory='SOURCE='+repr({SOURCE!r})+'\\n'+{INVENTORY!r}
def scan():return json.loads(subprocess.check_output(ssh+['python3 -'],input=inventory,text=True))
with (base/'_operations/transfer_global.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=scan();total=sum(x['bytes'] for x in before['files']);usage=shutil.disk_usage(base)
 assert (usage.free-total)/usage.total>=.30
 manifest=dest/'backup_manifest.json'
 if manifest.exists():
  old=json.loads(manifest.read_text());assert old['files']==before['files'];print(json.dumps(old));raise SystemExit(0)
 plan=op/'plan.json'
 if plan.exists():assert json.loads(plan.read_text())==before
 else:plan.write_text(json.dumps(before,indent=2))
 dest.mkdir(exist_ok=True);fl=op/'files.txt';fl.write_text(''.join(x['path']+'\\n' for x in before['files']))
 subprocess.check_call(['rsync','-rt','--partial','--files-from='+str(fl),'-e','ssh -F /home/zz2/.ssh/paracloud_backup_20261012/ssh_config','paracloud-backup:'+{SOURCE!r}+'/',str(dest)+'/'])
 for x in before['files']:
  p=dest/x['path'];assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],x['path']
 assert scan()==before
 result=dict(status='COMPLETE',backup_scope='PARTIAL_BUILD_FAILURE_NO_SOLUTION',job_id='5295127',source={SOURCE!r},destination=str(dest),files=before['files'],bytes=total,source_unchanged=True,all_files_sha256_verified=True,free_fraction=shutil.disk_usage(base).free/usage.total,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 manifest.write_text(json.dumps(result,indent=2));(op/'receipt.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''
if __name__=='__main__':
 p=subprocess.run(SSH+['python3 -'],input=code,text=True,capture_output=True,timeout=1800)
 (HERE/'B2060_v1_failure_backup.stdout.log').write_text(p.stdout,encoding='utf-8')
 (HERE/'B2060_v1_failure_backup.stderr.log').write_text(p.stderr,encoding='utf-8')
 if p.returncode==0:
  import json
  result=json.loads(p.stdout.strip().splitlines()[-1]);(HERE/'B2060_v1_failure_backup.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
  print({k:v for k,v in result.items() if k!='files'})
 else:print(p.stdout[-2000:],p.stderr[-3000:])
 sys.exit(p.returncode)
