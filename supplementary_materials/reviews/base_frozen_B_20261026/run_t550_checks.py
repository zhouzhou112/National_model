"""One foreground, finite T550 check; no daemon, listener or scheduler."""
import argparse
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REMOTE='/home/zz2/National_model_server/base_frozen_B_validation_20261026'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1',
     '-o','BindAddress=127.0.0.1','national-model-server']
CODE=r'''
from pathlib import Path
import os,subprocess,json,time,gzip,hashlib
root=Path(REMOTE);repo=root/'repo'
here=repo/'supplementary_materials/reviews/base_frozen_B_20261026'
env=os.environ.copy();env.update(CISPO_DATA_ROOT=str(root/'data'),CISPO_CF_ROOT='/home/zz2/National_model_server/data/hourly_cf',CISPO_HYDRO_ROOT='/home/zz2/National_model_server/data/hydro_timeseries_20260719_sequential_sparse',CISPO_WAVE_ROOT='/home/zz2/National_model_server/data/wave_energy_20260727',CISPO_RAW_GRFR_ROOT='/home/zz2/National_model_server/data/grfr_raw_2019',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8',PYTHONPATH=str(repo))
py='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
def run(name,command):
 name+=SUFFIX
 log=here/(name+'.log');start=time.monotonic()
 with log.open('x') as f:p=subprocess.run(command,cwd=repo,env=env,stdout=f,stderr=subprocess.STDOUT)
 result={'name':name,'exit_code':p.returncode,'runtime_seconds':time.monotonic()-start,'command':command,'log':str(log)}
 (here/(name+'_execution.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result),flush=True);print('\n'.join(log.read_text().splitlines()[-22:]),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
def gate(mode,hours,name):
 run(name,[py,str(here/'run_gate.py'),'--mode',mode,'--hours',str(hours),'--output',str(here/(name+SUFFIX)),'--baseline-runner',str(here/'baseline_runner_reference.py')])
if STAGE=='regression':
 run('full_regression_t550_v2',[py,'-m','unittest','discover','-s','tests','-q'])
elif STAGE=='build':
 gate('old-default',1,'old_default_1h')
 gate('default',1,'default_1h')
 def mps_hash(folder):
  paths=list((here/(folder+SUFFIX)/'model_archive').glob('original.mps*'));assert len(paths)==1
  p=paths[0];h=hashlib.sha256();opener=gzip.open if p.suffix=='.gz' else open
  with opener(p,'rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  return h.hexdigest()
 a,b=mps_hash('old_default_1h'),mps_hash('default_1h')
 result={'status':'PASS' if a==b else 'FAIL','old_uncompressed_mps_sha256':a,'new_uncompressed_mps_sha256':b}
 (here/('default_off_identity'+SUFFIX+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 if a!=b:raise SystemExit('Default-off MPS byte identity gate failed')
 gate('frozen',1,'frozen_1h')
elif STAGE in {'zero','base-control','frozen'}:
 gate(STAGE,24,STAGE.replace('-','_')+'_24h')
elif STAGE=='frozen-build':
 gate('frozen',1,'frozen_1h')
'''

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['regression','build','zero','base-control','frozen','frozen-build'])
    parser.add_argument('--suffix',default='')
    args=parser.parse_args()
    code='REMOTE='+repr(REMOTE)+'\nSTAGE='+repr(args.stage)+'\nSUFFIX='+repr(args.suffix)+'\n'+CODE
    p=subprocess.run(SSH+['python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=14400)
    with (HERE/(args.stage+args.suffix+'_t550_receipt.log')).open('x',encoding='utf-8') as f:f.write(p.stdout+p.stderr)
    print(p.stdout);print(p.stderr)
    raise SystemExit(p.returncode)
