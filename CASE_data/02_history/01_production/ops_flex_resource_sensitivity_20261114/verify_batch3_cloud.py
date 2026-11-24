"""Read-only cloud input, upstream, template and job-count verification."""
from pathlib import Path
import hashlib,json,subprocess
from deploy_batch3_conservative import CASES,BASE,INPUT_STAGE
HERE=Path(__file__).resolve().parent;OUT=HERE/'batch3_conservative_20261117'
data=json.loads((OUT/'inputs.json').read_text(encoding='utf-8'))
template_release='20261115_opsopen_2030_v9_t44_m750_tol1e4_v1'
code='data='+repr(data)+'\ncases='+repr(CASES)+'\nbase='+repr(BASE)+'\nstage='+repr(INPUT_STAGE)+'\ntemplate='+repr(template_release)+'\n'+r'''
from pathlib import Path
import hashlib,json,subprocess
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
root=Path(base);bundle=Path(stage)/'inputs/conservative';assert sha(bundle/'BUILD_AUDIT.json')==data['audit_sha256']
for n,e in data['files'].items():assert (bundle/n).stat().st_size==e['bytes'] and sha(bundle/n)==e['sha256'],n
verified={}
for name,c in cases.items():
 assert not (root/c['release']).exists(),'Existing target requires inspection'
 src=root/c['source_release'];expected=data['cloud_sources'][str(c['year'])]
 for group,sub in [('data_overlay','data_overlay'),('frozen_source','frozen_source')]:
  for n,e in expected[group].items():
   p=src/sub/n;assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],n
 info=data['years'][str(c['year'])]['source_identity']
 if info['closure_sha256']:assert sha(src/'frozen_closure.json')==info['closure_sha256']
 verified[name]=dict(status='PASS',data_files=len(expected['data_overlay']),frozen_source_files=len(expected['frozen_source']))
t=root/template;startup=json.loads((t/'startup_resources.json').read_text());assert json.loads((t/'compute_node_smoke.json').read_text())['status']=='PASS';assert startup['available_memory_gib']>=700
script=(t/'continuation.sbatch').read_text();queue=subprocess.check_output(['squeue','--me','-h','-o','%i|%j|%T|%M'],universal_newlines=True)
assert len(queue.splitlines())<=1,'Unexpected active jobs: review before adding three'
print(json.dumps(dict(status='PASS',cases=verified,immutable_input_files=len(data['files']),audit_sha256=data['audit_sha256'],template_release=template,template_sha256=hashlib.sha256(script.encode()).hexdigest(),template_text=script,queue=queue,startup=startup)))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=240)
(OUT/'cloud_recheck.stderr.log').write_text(p.stderr,encoding='utf-8')
if p.returncode:raise RuntimeError(p.stderr[-3000:]+p.stdout[-1000:])
r=json.loads(p.stdout);script=r.pop('template_text');(OUT/'template.sbatch').write_bytes(script.encode());assert hashlib.sha256((OUT/'template.sbatch').read_bytes()).hexdigest()==r['template_sha256']
(OUT/'cloud_recheck.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
