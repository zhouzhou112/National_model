"""Read-only code SHA/Git comparison of deployed engineering trees.

Uses existing SSH aliases. Does not read credentials or modify remote files.
Run from the repository root; writes comparison evidence beside this script.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import hashlib,json,subprocess,sys
roots=json.loads(sys.argv[1]);out={}
for label,name in roots.items():
 p=Path(name); files={}
 for folder in ('cispo_model','config','scripts','tests'):
  for f in (p/folder).rglob('*'):
   if f.is_file() and f.suffix in {'.py','.json','.csv','.sh','.sbatch'}:
    files[f.relative_to(p).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
 def git(*args):
  r=subprocess.run(['git','-C',str(p),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
  return r.stdout.strip() if r.returncode==0 else None
 out[label]=dict(root=str(p),exists=p.is_dir(),git_head=git('rev-parse','HEAD'),git_status=git('status','--porcelain','-uno'),files=files)
print(json.dumps(out))
'''

def main():
 cloud='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
 sets=[('cloud',['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','paracloud-bscc-a8'],'python3',dict(production2050=f'{cloud}/20260930_base2050_v9_t48_m750_tol1e4_v1/repo',factor_F=f'{cloud}/claude_workspace/factor_pair_8760_20261005/member_F/repo',factor_S=f'{cloud}/claude_workspace/factor_pair_8760_20261005/member_S/repo')),
 ('fixed',['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','-p','22','national-model-server'],'/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python',dict(primary='/home/zz2/National_model_server/repo',numerical='/home/zz2/National_model_server/probe_outputs/numerical_robustness_20261005/repo'))]
 for name,cmd,python,roots in sets:
  arg=json.dumps(roots)
  run=subprocess.run(cmd+[python+" - '"+arg.replace("'","'\"'\"'")+"'"],input=REMOTE,encoding='utf-8',capture_output=True,timeout=60)
  if run.returncode:
   (HERE/(name+'_error.txt')).write_text(run.stderr,encoding='utf-8');print(name,'ERROR',run.returncode);continue
  data=json.loads(run.stdout)
  for v in data.values():
   v['local_differences']=[f for f,h in v['files'].items() if not (ROOT/f).is_file() or hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h]
  (HERE/(name+'_versions.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({k:{key:v[key] for key in ['root','exists','git_head','git_status','local_differences']}|{'file_count':len(v['files'])} for k,v in data.items()},indent=2))

if __name__=='__main__':main()
