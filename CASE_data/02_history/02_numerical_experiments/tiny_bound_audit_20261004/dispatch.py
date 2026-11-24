"""Upload to a NEW audit directory and submit exactly three authorized audit jobs.

Run once: python dispatch.py. Refuses to overwrite/re-submit existing work.
Only writes the independent audit workspace; no model or production job commands.
"""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
cfg=json.loads((HERE/'inputs.json').read_text())
remote=cfg['remote_base']+'/'+cfg['remote_work_subdir']
names=['audit_bounds.py','inputs.json']+['audit_{}.sbatch'.format(y) for y in [2030,2040,2050]]
files={name:(HERE/name).read_text(encoding='utf-8') for name in names}
hashes={name:hashlib.sha256(text.encode()).hexdigest() for name,text in files.items()}
if (HERE/'submission_attempt.json').exists():
    raise RuntimeError('A submission attempt exists; inspect it, never blindly retry')
code='from pathlib import Path\nimport json,subprocess,hashlib,datetime\n'
code+='root=Path('+repr(remote)+')\nfiles='+repr(files)+'\nhashes='+repr(hashes)+'\n'
code+='''
assert not root.exists(), 'Refuse to replace an existing audit workspace'
root.mkdir()
for name,content in files.items():
    p=root/name
    p.write_bytes(content.encode('utf-8'))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[name]
compile(files['audit_bounds.py'],'audit_bounds.py','exec')
for year in [2030,2040,2050]:
    subprocess.check_call(['bash','-n','audit_{}.sbatch'.format(year)],cwd=str(root))
(root/'uploaded_sha256.json').write_text(json.dumps(hashes,indent=2))
jobs={}
for year in [2030,2040,2050]:
    attempt=root/'submission_attempt_{}.json'.format(year)
    with attempt.open('x') as f: json.dump({'timestamp':datetime.datetime.now().astimezone().isoformat()},f)
    p=subprocess.run(['sbatch','--parsable','audit_{}.sbatch'.format(year)],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
    record={'year':year,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    (root/'submission_{}.json'.format(year)).write_text(json.dumps(record,indent=2))
    if p.returncode: raise RuntimeError('Submission failed: '+json.dumps(record))
    job=p.stdout.strip().split(';')[0]
    assert job.isdigit(),record
    jobs[str(year)]=job
    print(json.dumps(record),flush=True)
receipt={'jobs':jobs,'root':str(root),'submitted_at':datetime.datetime.now().astimezone().isoformat(),'sha256':hashes}
(root/'submission_receipt.json').write_text(json.dumps(receipt,indent=2))
print('RECEIPT '+json.dumps(receipt),flush=True)
'''
(HERE/'submission_attempt.json').write_text(json.dumps(dict(timestamp=datetime.datetime.now().astimezone().isoformat(),remote=remote)),encoding='utf-8')
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=180)
(HERE/'dispatch.stdout.log').write_text(p.stdout,encoding='utf-8')
(HERE/'dispatch.stderr.log').write_text(p.stderr,encoding='utf-8')
print(p.stdout);print(p.stderr);p.check_returncode()
receipt=json.loads(next(line[8:] for line in p.stdout.splitlines() if line.startswith('RECEIPT ')))
(HERE/'submission_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
