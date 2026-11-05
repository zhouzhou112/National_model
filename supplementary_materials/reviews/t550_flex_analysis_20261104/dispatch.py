"""Finite T550 extraction and SHA-verified small returns; never calls a solver."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,io,json,subprocess,tarfile
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
RET=REPO.parent/'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
OLD=HERE  # Byte-identical archived collector dependencies are bundled here.
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
PY='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
BASE='/home/zz2/National_model_server'
OUT=BASE+'/analysis_tools_20261020'
RELEASES=dict(case3_2040='20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2',c2050='20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2',nocredit_2030='20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1',b2030='20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3',b2040='20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1',b2050='20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1',b2060='20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2')
def remote(code,binary=False,timeout=180):
 p=subprocess.run(SSH+[PY+' -'],input=code.encode(),capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')+p.stdout.decode(errors='replace')[-1500:])
 return p.stdout if binary else json.loads(p.stdout)
def load_old(name):
 spec=importlib.util.spec_from_file_location(name,OLD/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def t1(case):
 m=load_old('collect_t1');m.LOCAL=RET;m.RELEASES.update(RELEASES);m.collect(case)
def launch(case):
 scripts={n:(HERE/n).read_text(encoding='utf-8') for n in ['dual_extensions.py','run_rows_only.py','vre_reduced_cost_screen.extended.py']}
 root=BASE+'/cloud_backup/'+RELEASES[case];out=OUT+'/'+case
 code='from pathlib import Path\nimport json,subprocess,os,hashlib,datetime\nscripts='+repr(scripts)+'\nroot=Path('+repr(root)+')\nout=Path('+repr(out)+')\npy='+repr(PY)+'\ncase='+repr(case)+'\n'+'''
assert not out.exists(), 'Existing output: inspect rather than overwrite/relaunch'
out.mkdir();(out/'scripts').mkdir();(out/'logs').mkdir()
for name,content in scripts.items():(out/'scripts'/name).write_text(content)
cmd=[py,'-u',str(out/'scripts'/('vre_reduced_cost_screen.extended.py' if case=='case3_2040' else 'run_rows_only.py'))]
if case=='case3_2040':cmd+=['--mps',str(root/'output_8760/model_archive/original.mps.gz'),'--barpi',str(root/'output_8760/barrier_checkpoint/dual_barpi.npy'),'--vre-capacity-csv',str(root/'output_8760/vre_capacity.csv'),'--out',str(out/'rc_screen')]
else:cmd+=['--root',str(root),'--out',str(out)]
wrapper="import subprocess,json,datetime,time,pathlib; t=time.time(); r=subprocess.run("+repr(cmd)+"); pathlib.Path("+repr(str(out/'terminal.json'))+").write_text(json.dumps(dict(returncode=r.returncode,status='COMPLETE' if r.returncode==0 else 'FAILED',seconds=time.time()-t,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())))"
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
with (out/'logs/run.stdout.log').open('xb') as so,(out/'logs/run.stderr.log').open('xb') as se:
 p=subprocess.Popen([py,'-c',wrapper],stdout=so,stderr=se,stdin=subprocess.DEVNULL,start_new_session=True,env=env)
record=dict(case=case,command=cmd,pid=p.pid,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_release=str(root),script_sha256={n:hashlib.sha256(s.encode()).hexdigest() for n,s in scripts.items()},finite_one_case=True,solver_started=False)
(out/'run_parameters.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
'''
 result=remote(code);(HERE/(case+'_launch.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result))
def status(case):
 print(json.dumps(remote('from pathlib import Path\nimport json,os\np=Path('+repr(OUT+'/'+case)+')\nr={}\nfor name in ["terminal.json","row_order_verification.json","row_extraction_summary.json"]:\n if (p/name).exists():r[name]=json.loads((p/name).read_text())\nfor name in ["logs/run.stdout.log","logs/run.stderr.log"]:\n if (p/name).exists():r[name]=(p/name).read_text()[-2000:]\nprint(json.dumps(r))')))
def collect(case,stage):
 # Import old collector without rewriting its tested extraction or transfer logic.
 import sys
 m=load_old('collect_t1');m.LOCAL=RET;sys.modules['collect_t1']=m
 c=load_old('collect_analysis');c.LOCAL=RET;c.collect(case,stage)
 # Archive exact scripts used for this case, plus this dispatch command.
 d=RET/case/'scripts';d.mkdir(exist_ok=True)
 for n in ['dual_extensions.py','run_rows_only.py','vre_reduced_cost_screen.extended.py','dispatch.py']:
  b=(HERE/n).read_bytes();p=d/n
  if p.exists():assert p.read_bytes()==b
  else:p.write_bytes(b)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['t1','launch','status','collect']);p.add_argument('case',choices=list(RELEASES));p.add_argument('--stage',choices=['rows','final'],default='final');a=p.parse_args()
 if a.action=='collect':collect(a.case,a.stage)
 else:globals()[a.action](a.case)
