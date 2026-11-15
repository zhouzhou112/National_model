"""Install the immutable supplied input package only; no jobs or data generation."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/_staging/ops_resource_sensitivity_20261114'
ARCHIVE=HERE/'baseline_install_payload.tar.gz'
SHA='1d004681780684247dda48f198cce339718abd2d43b62c3e7500d0d67e1e571e'
assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==SHA
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','paracloud-bscc-a8','python3 -']
code='from pathlib import Path\np=Path('+repr(ROOT)+')\nassert not p.exists()\np.mkdir(parents=True)\n'
resume=sys.argv[1:]==['--resume-uploaded']
assert not sys.argv[1:] or resume
if not resume:
 subprocess.run(ssh,input=code,text=True,check=True)
 subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',str(ARCHIVE),'paracloud-bscc-a8:'+ROOT+'/input_payload.tar.gz'],check=True)
code='root='+repr(ROOT)+'\nexpected='+repr(SHA)+'\n'+r'''
from pathlib import Path
import hashlib,json,tarfile
root=Path(root);p=root/'input_payload.tar.gz'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
assert not (root/'inputs').exists()
with tarfile.open(p) as tf:
 selected=[e for e in tf.getmembers() if e.name.startswith('inputs/')]
 for e in selected:assert e.isfile() and root.resolve() in (root/e.name).resolve().parents
 tf.extractall(root,members=selected)
report={}
for name in ['conservative','open']:
 bundle=root/'inputs'/name;a=json.loads((bundle/'BUILD_AUDIT.json').read_text())
 for n,e in a['files'].items():
  p=bundle/n;assert p.stat().st_size==e['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'],n
 report[name]=dict(status='PASS',files=len(a['files']),audit_sha256=hashlib.sha256((bundle/'BUILD_AUDIT.json').read_bytes()).hexdigest())
result=dict(status='PASS',root=str(root),source_payload_sha256=expected,inputs=report,generated_or_repaired=False,baseline_repo_extracted=False)
(root/'installation_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
p=subprocess.run(ssh,input=code,text=True,encoding='utf-8',capture_output=True)
label='cloud_input_install_resume' if resume else 'cloud_input_install'
(HERE/(label+'.stdout.log')).write_text(p.stdout,encoding='utf-8');(HERE/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
if p.returncode:raise RuntimeError(p.stderr)
result=json.loads(p.stdout);(HERE/'cloud_input_installation_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
