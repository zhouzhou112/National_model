"""Start one finite T550 evidence batch, or take one read-only status snapshot."""
from pathlib import Path
import argparse,datetime,json,subprocess
HERE=Path(__file__).resolve().parent
OUT=HERE/'acceptance_late_20261119'
ROOT='/home/zz2/National_model_server/acceptance_tools_resource_late_20261119'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -']

START=r'''
from pathlib import Path
import json,subprocess,os,datetime
root=Path(root);base=root.parent;op=base/'cloud_backup/_operations/20261119_resource_lateopen2050_completed';b=base/'cloud_backup/20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1'
status=json.loads((op/'transfer_status.json').read_text())
if status['status']!='COMPLETE':print(json.dumps(dict(status='WAIT_BACKUP',transfer=status)));raise SystemExit(0)
assert status['source_unchanged'] and all(x['status']=='VERIFIED' for x in status['stages'])
m=json.loads((b/'backup_manifest.json').read_text());assert m['status']=='COMPLETE' and m['source_unchanged_after_transfer'] and m['source_result_manifest_sha256']==identity['result_manifest_sha256']
assert not (root/'execution.json').exists() and not (b/'acceptance_resource_late_20261119').exists(),'Inspect prior task before any repeat'
mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))/1024**2;assert mem>=32
(root/'cloud_identity.json').write_text(json.dumps(identity)+'\n')
with (root/'worker.stdout.log').open('x') as f,(root/'worker.stderr.log').open('x') as g:p=subprocess.Popen(['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python','-u',str(root/'worker.py')],cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=g,start_new_session=True,env=dict(os.environ,PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
r=dict(status='STARTED',pid=p.pid,root=str(root),available_memory_gib=mem,backup=dict(status=status['status'],finished_at_utc=status['finished_at_utc'],files=len(m['files']),bytes=status['completed_bytes'],source_result_manifest_sha256=m['source_result_manifest_sha256']),as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());(root/'execution.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''

STATUS=r'''
from pathlib import Path
import json,datetime
root=Path(root);r={'as_of_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for n in ['execution.json','execution_results.json','audit_processes.json','COMPLETE.json']:
 if (root/n).exists():r[n]=json.loads((root/n).read_text())
for p in root.glob('*.log'):
 if p.name.endswith(('.stdout.log','.stderr.log')):r[p.name]=p.read_text()[-2500:]
side=root.parent/'cloud_backup/20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1/acceptance_resource_late_20261119'
r['evidence_files']=[str(p.relative_to(side)) for p in side.rglob('*.json')] if side.exists() else []
print(json.dumps(r))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['start','status']);a=p.parse_args()
 identity=json.loads((OUT/'cloud_identity.json').read_text(encoding='utf-8'));code='root='+repr(ROOT)+'\nidentity='+repr(identity)+'\n'+(START if a.phase=='start' else STATUS)
 result=subprocess.run(SSH,input=code,capture_output=True,text=True,encoding='utf-8',timeout=90);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');(OUT/(a.phase+'_'+stamp+'.stderr.log')).write_text(result.stderr,encoding='utf-8')
 if result.returncode:raise RuntimeError(result.stderr[-4000:]+result.stdout[-1000:])
 r=json.loads(result.stdout);(OUT/(('execution' if r.get('status')=='STARTED' else a.phase+'_'+stamp)+'.json')).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))

if __name__=='__main__':main()
