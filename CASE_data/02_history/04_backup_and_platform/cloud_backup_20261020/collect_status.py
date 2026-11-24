"""One-shot read of the T550 backup; writes only local evidence, no polling."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess

HERE=Path(__file__).resolve().parent
CODE=r'''
from pathlib import Path
import json, os
root=Path('/home/zz2/National_model_server/cloud_backup')
op=root/'_operations/20261020_base2060_case3_2030'
result={}
for name in ['backup_plan.json','transfer_launch.json','transfer_status.json']:
    p=op/name
    if p.exists(): result[name]=json.loads(p.read_text())
status=result.get('transfer_status.json',{})
stages=status.get('stages',[])
if stages:
    current=stages[-1]
    logfile=op/(current['release']+'_'+current['tier']+'.log')
    if logfile.exists():
        with logfile.open('rb') as stream:
            stream.seek(max(0,logfile.stat().st_size-2000))
            result['current_transfer_tail']=stream.read().decode('utf-8',errors='replace')
for release in result.get('backup_plan.json',{}).get('releases',{}):
    p=root/release/'backup_manifest.json'
    if p.exists(): result.setdefault('backup_manifests',{})[release]=json.loads(p.read_text())
if 'transfer_launch.json' in result:
    pid=result['transfer_launch.json']['pid']
    result['runner_proc_exists']=Path('/proc')/str(pid)
    result['runner_proc_exists']=result['runner_proc_exists'].exists()
print(json.dumps(result))
'''

def main():
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20',
        '-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1',
        'national-model-server','python3 -'],input=CODE,text=True,
        encoding='utf-8',capture_output=True,timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr)
    result=json.loads(p.stdout)
    tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (HERE/('status_'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (HERE/'latest_status.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for release,manifest in result.get('backup_manifests',{}).items():
        (HERE/(release+'_backup_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    status=result.get('transfer_status.json',{})
    stages=status.get('stages',[])
    tail=result.get('current_transfer_tail','').replace('\r','\n').splitlines()
    print(json.dumps({'status':status.get('status'),'error':status.get('error'),
                     'completed_bytes':status.get('completed_bytes'),
                     'verified_stages':sum(s['status']=='VERIFIED' for s in stages),
                     'current_stage':stages[-1] if stages else None,
                     'runner_proc_exists':result.get('runner_proc_exists'),
                     'tail':tail[-2:]},indent=2))

if __name__=='__main__': main()
