"""Read the existing 2030 exception gate once, without restarting it."""
from pathlib import Path
import datetime,json,subprocess
HERE=Path(__file__).resolve().parent;OUT=HERE/'batch2/2030/author_window_v2'
CODE=r'''
from pathlib import Path
import json,datetime
r=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/runtime_batch2_2030_author_window_20261115');w=r/'gates/2030';result={'as_of_utc':datetime.datetime.utcnow().isoformat()+'Z'}
for n in ['execution_results.json','YEAR_GATES_PASSED.json','YEAR_GATES_STOP.json']:
 p=w/n
 if p.exists():result[n]=json.loads(p.read_text())
for name in ['2030.stdout.log','2030.stderr.log']:
 p=r/name
 if p.exists():result[name]=p.read_text()[-5000:]
result['started']=[p.name for p in w.iterdir() if p.is_dir()] if w.exists() else []
print(json.dumps(result))
'''
if __name__=='__main__':
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr)
 r=json.loads(p.stdout);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');(OUT/('progress_'+stamp+'.json')).write_text(json.dumps(r,indent=2)+'\n')
 for name in ['YEAR_GATES_PASSED.json','YEAR_GATES_STOP.json']:
  if name in r:(OUT/name).write_text(json.dumps(r[name],indent=2)+'\n')
 print(json.dumps(dict(status='PASS' if 'YEAR_GATES_PASSED.json' in r else 'STOP' if 'YEAR_GATES_STOP.json' in r else 'RUNNING',completed=list(r.get('execution_results.json',{})),started=r['started'],stdout=r.get('2030.stdout.log','')[-1600:],stderr=r.get('2030.stderr.log',''))))
