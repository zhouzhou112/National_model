"""One-case finite metrics deployment/execution/return. No watcher."""
from pathlib import Path
import argparse,subprocess,json,hashlib,io,tarfile,time
HERE=Path(__file__).resolve().parent
LOCAL=HERE.parents[3]/'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
BASE='/home/zz2/National_model_server';PY=BASE+'/envs/cispo-2030-v1/bin/python'
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
RELEASES={'case3_2030':'20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1','case3_2040':'20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2','c2050':'20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2','nocredit_2030':'20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1','b2030':'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3','b2040':'20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1','b2050':'20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1','b2060':'20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2','base2030':'20260914_base_v9_t48_m750_tol1e4_v3','base2040':'20260919_base2040_v9_t44_m750_tol1e4_v1','base2050':'20260930_base2050_v9_t48_m750_tol1e4_v1','base2060':'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}
def remote(code,timeout=1800):
 r=subprocess.run(SSH+[PY+' -'],input=code.encode(),capture_output=True,timeout=timeout)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')+r.stdout.decode(errors='replace')[-5000:])
 return r.stdout

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case',choices=RELEASES);ap.add_argument('--revenue',action='store_true');ap.add_argument('--national',action='store_true');ap.add_argument('--attempt',type=int,default=1);a=ap.parse_args();case=a.case;tag='revenue' if a.revenue else ('national' if a.national else 'flex');out=BASE+'/analysis_tools_20261105_metrics/'+case+'/'+tag+f'_v{a.attempt}'
 scripts={n:(HERE/n).read_text(encoding='utf-8-sig') for n in ['metrics_flex.py','metrics_revenue.py','metrics_national.py']}
 version='scripts_'+hashlib.sha256(''.join(scripts.values()).encode()).hexdigest()[:12]
 code='from pathlib import Path\nimport json,hashlib,subprocess,os,time\n'+f'scripts={scripts!r}\nbase=Path({BASE!r})\nout=Path({out!r})\ncase={case!r}\nrelease={RELEASES[case]!r}\n'
 code+=f'version={version!r}\n'
 code+='''tools=base/'analysis_tools_20261105_metrics'/version
tools.mkdir(parents=True,exist_ok=True)
for n,content in scripts.items():
 p=tools/n
 if p.exists():assert p.read_text()==content,'script differs from deployed version'
 else:p.write_text(content)
annual=base/'analysis_tools_20261020'/case/'annual_row_duals.csv'
identity=json.loads((annual.parent/'input_identity.json').read_text());order=json.loads((annual.parent/'row_order_verification.json').read_text())
assert identity['status']=='PASS' and order['status']=='PASS'
assert Path(identity['release']).name==release
assert annual.is_file()
annual_sha=hashlib.sha256(annual.read_bytes()).hexdigest()
'''
 cmd=[PY,BASE+'/analysis_tools_20261105_metrics/'+version+'/'+('metrics_revenue.py' if a.revenue else ('metrics_national.py' if a.national else 'metrics_flex.py')),'--case',case,'--release',RELEASES[case],'--out',out]
 if a.revenue:cmd+=['--data-root',BASE+'/base_frozen_B_validation_20261026/data']
 elif not a.national and case in ('case3_2030','case3_2040'):cmd+=['--typical-days']
 code+=f'command={cmd!r}\n'
 code+='''command+=['--annual-duals',str(annual),'--annual-sha',annual_sha]
out.parent.mkdir(parents=True,exist_ok=True)
log=out.parent/(out.name+'.stdout.log');err=out.parent/(out.name+'.stderr.log')
assert not out.exists(),'Existing output: inspect before retry'
with log.open('xb') as f,err.open('xb') as e:r=subprocess.run(command,stdout=f,stderr=e,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
print(json.dumps({'returncode':r.returncode,'stdout':log.read_text(),'stderr':err.read_text(),'output':str(out)}))
'''
 result=json.loads(remote(code));(HERE/f'metrics_{case}_{tag}_v{a.attempt}_execution.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False),flush=True)
 if result['returncode']:return
 code='from pathlib import Path\nimport json,tarfile,sys,hashlib\n'+f'out=Path({out!r})\ntag={tag!r}\n'
 code+='''manifest=json.loads((out/(('revenue' if tag=='revenue' else 'metrics')+'_manifest.json')).read_text())
files={}
for name,m in manifest.items():
 p=out/name;assert p.stat().st_size<=30_000_000 and hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256']
 target=('metadata/'+name) if name.endswith('.json') else ('scripts/'+tag+'/'+name.split('/',1)[1] if name.startswith('scripts/') else name)
 files[target]=dict(m,remote_source=str(p))
for suffix in ['stdout','stderr']:
 p=out.parent/(out.name+'.'+suffix+'.log');files['logs/'+tag+'.'+suffix+'.log']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'remote_source':str(p)}
assert sum(v['bytes'] for v in files.values())<=100_000_000
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tf:
 for target,v in files.items():tf.add(v['remote_source'],arcname=target,recursive=False)
 raw=json.dumps(files,indent=2).encode();ti=tarfile.TarInfo('metadata/'+tag+'_transfer_receipt.json');ti.size=len(raw);tf.addfile(ti,__import__('io').BytesIO(raw))
'''
 raw=remote(code);dest=LOCAL/case
 with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
  receipt=json.load(tf.extractfile('metadata/'+tag+'_transfer_receipt.json'))
  for member in tf:
   assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
   data=tf.extractfile(member).read();p=dest/member.name;p.parent.mkdir(parents=True,exist_ok=True)
   if member.name in receipt:assert hashlib.sha256(data).hexdigest()==receipt[member.name]['sha256']
   if p.exists():assert p.read_bytes()==data, 'Local conflict: '+str(p)
   else:p.write_bytes(data)
 print(json.dumps({'returned':case,'kind':tag,'files':len(receipt),'bytes':sum(v['bytes'] for v in receipt.values()),'destination':str(dest)}),flush=True)
if __name__=='__main__':main()
