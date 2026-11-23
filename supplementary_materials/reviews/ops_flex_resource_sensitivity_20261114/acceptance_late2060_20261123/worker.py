
from pathlib import Path
import json,subprocess,sys,os,time
root=Path(__file__).resolve().parent;b=Path('/home/zz2/National_model_server/cloud_backup/20261119_lateopen_2060_restricted_t44_m750_tol1e4_v1');side=b/'acceptance_resource_late2060_20261123';py=sys.executable;identity=json.loads((root/'cloud_identity.json').read_text());results={};env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1')
def run(label,args):
 t=time.time()
 with (root/(label+'.stdout.log')).open('x') as f,(root/(label+'.stderr.log')).open('x') as g:p=subprocess.run([py]+args,cwd=root,stdout=f,stderr=g,env=env)
 results[label]=dict(returncode=p.returncode,seconds=time.time()-t);(root/'execution_results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(dict(phase=label,**results[label])),flush=True)
 if p.returncode:raise RuntimeError(label+' failed; preserve logs and stop')
run('prepare',['prepare_acceptance.py','--cloud-sha',identity['result_manifest_sha256']])
solve=json.loads((b/'output_8760/solve_report.json').read_text());index=solve['solution_quality_locations']['maximum_constraint_violation']['index'];commands={'row_audit':['scripts/audit_archived_constraint.py','--output-dir',str(b/'output_8760'),'--row-index',str(index),'--audit-json',str(side/'row_audit_full.json')],'pricing':['scripts/price_capacity_bound_selection.py','--run-dir',str(b/'output_8760'),'--selection-json',str(b/'capacity_selection.json'),'--output',str(side/'pricing')]};active={}
for label,args in commands.items():
 f=(root/(label+'.stdout.log')).open('x');g=(root/(label+'.stderr.log')).open('x');p=subprocess.Popen([py]+args,cwd=root,stdout=f,stderr=g,env=env);active[label]=(p,time.time(),f,g)
(root/'audit_processes.json').write_text(json.dumps({k:v[0].pid for k,v in active.items()})+'\n')
for label,(p,t,f,g) in active.items():
 rc=p.wait();f.close();g.close();results[label]=dict(returncode=rc,seconds=time.time()-t);(root/'execution_results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(dict(phase=label,**results[label])),flush=True)
assert all(v['returncode']==0 for v in results.values()),'Evidence task failed; no automatic rerun'
run('finalize',['finalize_acceptance.py'])
run('analysis',['analyze_on_t550.py','LATE-Open-2060'])
(root/'COMPLETE.json').write_text(json.dumps(dict(status='PASS',results=results),indent=2)+'\n')
