"""One finite read of existing gate/regression results; never starts work."""
from pathlib import Path
import datetime,json,subprocess
HERE=Path(__file__).resolve().parent
CODE=r'''
from pathlib import Path
import json,datetime,subprocess
r=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/runtime_batch2_20261115');result=dict(as_of_utc=datetime.datetime.utcnow().isoformat()+'Z',years={})
for name in ['installation_receipt.json','full_tests.json','validation_execution.json']:
 p=r/name
 if p.exists():
  try:result[name]=json.loads(p.read_text())
  except json.JSONDecodeError:result[name]={'state':'WRITE_IN_PROGRESS'}
for y in [2030,2040,2060]:
 w=r/'gates'/str(y);item={};result['years'][y]=item
 for name in ['YEAR_GATES_PASSED.json','YEAR_GATES_STOP.json','execution_results.json']:
  p=w/name
  if p.exists():
   try:item[name]=json.loads(p.read_text())
   except json.JSONDecodeError:item[name]={'state':'WRITE_IN_PROGRESS'}
 for suffix in ['stdout','stderr']:
  p=r/(str(y)+'.'+suffix+'.log')
  if p.exists():item[suffix+'_tail']=p.read_text()[-3500:]
 if w.exists():item['started_gate_directories']=sorted(p.name for p in w.iterdir() if p.is_dir())
p=r/'unittest.stderr.log'
if p.exists():result['regression_tail']=p.read_text()[-1500:]
print(json.dumps(result))
'''
if __name__=='__main__':
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr)
 result=json.loads(p.stdout);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');path=HERE/'batch2'/('progress_'+stamp+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
 if result.get('full_tests.json',{}).get('status')=='PASS':(HERE/'batch2/full_tests.json').write_text(json.dumps(result['full_tests.json'],indent=2)+'\n')
 for year,item in result['years'].items():
  if 'YEAR_GATES_PASSED.json' in item:
   out=HERE/'batch2'/year;out.mkdir(exist_ok=True);(out/'YEAR_GATES_PASSED.json').write_text(json.dumps(item['YEAR_GATES_PASSED.json'],indent=2)+'\n')
 print(json.dumps(dict(snapshot=str(path),tests={k:v for k,v in result.get('full_tests.json',{}).items() if k in ['status','tests','skips','seconds']},regression_tail=result.get('regression_tail','')[-450:],years={y:dict(status='PASS' if 'YEAR_GATES_PASSED.json' in x else 'STOP' if 'YEAR_GATES_STOP.json' in x else 'RUNNING',gates=list(x.get('execution_results.json',{})),started=x.get('started_gate_directories'),stdout=x.get('stdout_tail','')[-800:],stderr=x.get('stderr_tail','')) for y,x in result['years'].items()}),ensure_ascii=False))
