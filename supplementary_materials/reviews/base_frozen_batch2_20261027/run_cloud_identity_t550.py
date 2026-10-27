"""One finite foreground validation batch in an isolated T550 checkout."""
from pathlib import Path
import subprocess
from t550_validation import SSH,REMOTE,PY,REL

HERE=Path(__file__).resolve().parent
code=f'''
from pathlib import Path
import concurrent.futures,subprocess,os,json,time
root=Path({REMOTE!r})/'repo';here=root/{REL!r}
env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(root/'data'),CISPO_CF_ROOT='/home/zz2/National_model_server/data/hourly_cf',CISPO_HYDRO_ROOT='/home/zz2/National_model_server/data/hydro_timeseries_20260719_sequential_sparse',CISPO_WAVE_ROOT='/home/zz2/National_model_server/data/wave_energy_20260727',CISPO_RAW_GRFR_ROOT='/home/zz2/National_model_server/data/grfr_raw_2019',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8',PYTHONPATH=str(root))
def work(year):
 start=time.monotonic();code=0
 with (here/('B'+str(year)+'_cloud_identity_v2.log')).open('x') as log:
  for command in [[{PY!r},str(here/'prepare_cloud_closure.py'),str(year)],
    [{PY!r},str(here/'run_year_gates.py'),str(year),'--work-tag','cloud_identity_v2','--closure',str(here/str(year)/'cloud_identity_v2/derived_static/closure.json')]]:
   p=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT);code=p.returncode
   if code:break
 result=dict(year=year,exit_code=code,runtime_seconds=time.monotonic()-start)
 (here/('B'+str(year)+'_cloud_identity_v2_execution.json')).write_text(json.dumps(result,indent=2))
 print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(work,[2040,2050,2060]))
raise SystemExit(0 if all(x['exit_code']==0 for x in results) else 1)
'''
if __name__=='__main__':
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,capture_output=True,timeout=14400)
    (HERE/'cloud_identity_v2_execution.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    print(p.stdout,p.stderr);raise SystemExit(p.returncode)
