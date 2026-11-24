
import sys,json,base64,hashlib,shutil,subprocess,os,time
from pathlib import Path
p=json.load(sys.stdin)
b=Path('/home/zz2/National_model_server')
old=b/'probe_outputs/case3_flex_numerics_20261012_aef0cb7'
out=b/'probe_outputs/case3_flex_F5_direct_20261013_3e4a2fe'
new=out/('extension_source_'+p['commit'][:7])
assert not new.exists() and not (out/'extension_started.json').exists()
manifest=json.loads((old/'bundle_manifest.json').read_text())
for item in manifest['files']:
 f=(old/item['path']).resolve()
 assert f.is_relative_to(old) and hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'],item['path']
new.mkdir()
for item in manifest['files']:
 if not item['path'].startswith('repo/'): continue
 target=new/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(old/item['path'],target)
for name,item in p['files'].items():
 assert name in ('scripts/run_flex_extension_series.py','scripts/run_flex_full_diagnostic.py','scripts/flex_numerics_diagnostics.py')
 data=base64.b64decode(item['base64']);assert hashlib.sha256(data).hexdigest()==item['sha256']
 (new/'repo'/name).write_bytes(data)
files=[{'path':str(f.relative_to(new)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted((new/'repo').rglob('*')) if f.is_file()]
m={'diagnostic_commit':p['commit'],'original_commit':manifest['git_commit'],'original_verified_files':len(manifest['files']),'files':files,'overlay_files':list(p['files'])}
(new/'extension_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
python=b/'envs/cispo-2030-v1/bin/python'
check=subprocess.run([str(python),str(new/'repo/scripts/run_flex_extension_series.py'),'--help'],capture_output=True,text=True)
assert check.returncode==0,check.stderr
cmd=[str(python),str(new/'repo/scripts/run_flex_extension_series.py'),'--source',str(new),'--data-source',str(old),'--server-root',str(b),'--output',str(out)]
with (out/'extension_controller_console.log').open('x') as log:
 child=subprocess.Popen(cmd,cwd=new/'repo',stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
receipt={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'pid':child.pid,'command':cmd,'source_manifest_sha256':hashlib.sha256((new/'extension_manifest.json').read_bytes()).hexdigest(),'diagnostic_commit':p['commit'],'original_verified_files':len(manifest['files']),'overlay_files':list(p['files']),'admission_gib':60,'reserve_gib':15,'f5_not_modified':True}
(out/'extension_dispatch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
