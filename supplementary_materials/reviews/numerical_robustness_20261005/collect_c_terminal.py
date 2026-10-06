"""Read-only terminal evidence collection; no model build or solver launch.

Usage: python collect_c_terminal.py OUTPUT_DIRECTORY
Copies only named probe evidence and records SHA256 of exact transferred bytes.
Uses the existing SSH alias and forwarding; never reads credential files.
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REMOTE = r'''
from pathlib import Path
import base64, hashlib, json, subprocess, datetime
r=Path('/home/zz2/National_model_server/probe_outputs/numerical_robustness_20261005')
names=['result.json','scope.json','effective_config.json','scientific_identity.json','input_manifest.csv','run_environment.json','build_report.json','gurobi.log','barrier_trajectory.csv','barrier.jsonl','physical_export/solution_qc.json']
paths=[r/'C_on744_full'/n for n in names]
paths += [r/n for n in ['C_on744_full.gate.json','C_on744_full.console.log','C_followup_status.json']]
files=[]
for p in paths:
    if not p.is_file():
        files.append(dict(path=str(p.relative_to(r)),missing=True)); continue
    b=p.read_bytes()
    files.append(dict(path=str(p.relative_to(r)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode()))
source={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'repo').rglob('*') if p.is_file() and p.suffix in {'.py','.json'}}
ps=subprocess.run(['ps','-p','639732,639733,670415,670416','-o','pid,etime,rss,comm'],capture_output=True,text=True)
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files,source_sha256=source,process_snapshot=ps.stdout,process_exit=ps.returncode)))
'''

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','-p','22','national-model-server','/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -']
    run=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=60,encoding='utf-8')
    (out/'ssh_stderr.txt').write_text(run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError(f'SSH failed {run.returncode}: {run.stderr}')
    data=json.loads(run.stdout)
    for entry in data['files']:
        if entry.get('missing'):continue
        b=base64.b64decode(entry.pop('base64'))
        assert hashlib.sha256(b).hexdigest()==entry['sha256'] and len(b)==entry['bytes']
        p=out/entry['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        entry['verified']=True
    (out/'transfer_verification.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(data['files']),'missing':[e['path'] for e in data['files'] if e.get('missing')],'process_snapshot':data['process_snapshot']}))

if __name__=='__main__':main()
