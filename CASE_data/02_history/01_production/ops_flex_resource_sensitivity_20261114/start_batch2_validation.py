"""Start finite regression and three independent year gates after verified installation."""
from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import json,subprocess,os,hashlib
runtime=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/runtime_batch2_20261115');repo=runtime/'repo';work=repo/'supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114'
receipt=json.loads((runtime/'installation_receipt.json').read_text());assert receipt['status']=='PASS' and set(receipt['years'])=={'2030','2040','2060'}
assert not (runtime/'validation_execution.json').exists(),'Inspect existing processes/results before any repeat'
for name,expected in helpers.items():assert hashlib.sha256((work/name).read_bytes()).hexdigest()==expected,name
env=dict(os.environ,PYTHONPATH=str(repo),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',CISPO_DATA_ROOT=str(repo/'data'),CISPO_CF_ROOT='/data/zz2/National_model/data/hourly_cf',CISPO_HYDRO_ROOT='/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse',CISPO_RAW_GRFR_ROOT='/data/zz2/National_model/data/grfr_raw_2019',CISPO_WAVE_ROOT='/data/zz2/National_model/data/wave_energy_20260727')
worker=runtime/'batch2/full_regression.py';assert not worker.exists();worker.write_text(regression)
py='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python';commands={'regression':[py,str(worker),str(runtime)]}
for year in [2030,2040,2060]:commands[str(year)]=[py,str(work/'run_batch2_year_gates.py'),str(year),'--runtime',str(runtime)]
result={}
for name,command in commands.items():
 with (runtime/(name+'.stdout.log')).open('x') as f,(runtime/(name+'.stderr.log')).open('x') as g:
  p=subprocess.Popen(command,cwd=repo,stdin=subprocess.DEVNULL,stdout=f,stderr=g,start_new_session=True,env=env)
 result[name]=dict(pid=p.pid,command=command)
(runtime/'validation_execution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
REGRESSION=r'''
from pathlib import Path
import json,subprocess,sys,time,hashlib,re
runtime=Path(sys.argv[1]);repo=runtime/'repo';before=json.loads((runtime/'installation_receipt.json').read_text())['tested_source_lf_sha256'];start=time.time()
with (runtime/'unittest.stdout.log').open('x') as f,(runtime/'unittest.stderr.log').open('x') as g:p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=repo,stdout=f,stderr=g)
after={n:hashlib.sha256((repo/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in before};assert before==after
log=(runtime/'unittest.stderr.log').read_text();count=re.search(r'Ran (\d+) tests',log);skips=[s for s in log.splitlines() if s.startswith('test_') and '... skipped ' in s]
report=dict(status='PASS' if p.returncode==0 else 'FAIL',exit_code=p.returncode,tests=int(count.group(1)) if count else None,skips=skips,seconds=time.time()-start,tested_source_lf_sha256=after,stderr_tail=log[-5500:])
(runtime/'full_tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='tested_source_lf_sha256'}))
'''
if __name__=='__main__':
 import hashlib
 names=['resource_gate_batch2.py','resource_audit_batch2.py','run_batch2_year_gates.py','window_gate.py','contractable_total_national_source.csv']
 helpers={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}
 code='helpers='+repr(helpers)+'\nregression='+repr(REGRESSION)+'\n'+REMOTE
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],input=code,text=True,encoding='utf-8',capture_output=True)
 (HERE/'batch2/validation_start.stderr.log').write_text(p.stderr,encoding='utf-8')
 if p.returncode:raise RuntimeError(p.stderr[-3000:]+p.stdout[-1000:])
 result=json.loads(p.stdout);(HERE/'batch2/validation_execution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
