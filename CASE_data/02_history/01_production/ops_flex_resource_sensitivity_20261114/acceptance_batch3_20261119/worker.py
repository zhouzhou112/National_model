
from pathlib import Path
import subprocess,json,sys,time,os
root=Path(__file__).resolve().parent;result={}
for year in (2030,2040,2060):
 case='OPS-Conservative-'+str(year);result[case]={}
 for phase,script,args in [('acceptance','accept_batch3_on_t550.py',['--cloud-identities',str(root/'cloud_identities.json')]),('analysis','analyze_batch3_on_t550.py',[])]:
  before=time.time()
  with (root/(case+'_'+phase+'.stdout.log')).open('x') as f,(root/(case+'_'+phase+'.stderr.log')).open('x') as g:
   p=subprocess.run([sys.executable,str(root/script),case]+args,cwd=root,stdout=f,stderr=g,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1'))
  result[case][phase]=dict(exit_code=p.returncode,seconds=time.time()-before)
  (root/'execution_results.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps(dict(case=case,phase=phase,**result[case][phase])),flush=True)
  if p.returncode:break
(root/'COMPLETE.json').write_text(json.dumps(dict(status='PASS' if all(len(v)==2 and all(t['exit_code']==0 for t in v.values()) for v in result.values()) else 'STOP',results=result),indent=2)+'\n')
