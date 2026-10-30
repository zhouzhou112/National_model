"""Deploy and run one finite, immutable T550 archived-row audit; no polling."""
from pathlib import Path
import base64
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RELEASE = '20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20',
       '-o', 'HostName=127.0.0.1', '-o', 'BindAddress=127.0.0.1', 'national-model-server']
PYTHON = '/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'


def main():
    raw = (ROOT/'scripts/audit_archived_constraint.py').read_bytes()
    code = '''from pathlib import Path
import base64, hashlib, json, subprocess, sys, math
base=Path('/home/zz2/National_model_server/cloud_backup')/RELEASE
side=base/'acceptance_20261029'
side.mkdir(exist_ok=True)
target=side/'archived_constraint_audit.json'
script=side/'audit_archived_constraint.py'
raw=base64.b64decode(ENCODED)
if script.exists(): assert script.read_bytes()==raw, 'tool identity conflict'
else: script.write_bytes(raw)
assert json.loads((base/'backup_manifest.json').read_text())['status']=='COMPLETE'
if not target.exists():
    with (side/'row_audit.stdout.log').open('x') as out, (side/'row_audit.stderr.log').open('x') as err:
        r=subprocess.run([sys.executable,str(script),'--output-dir',str(base/'output_8760'),
            '--row-index','53400865','--audit-json',str(target)],stdout=out,stderr=err)
    if r.returncode: raise RuntimeError((side/'row_audit.stderr.log').read_text()[-4000:])
data=target.read_bytes()
audit=json.loads(data)
terms=audit.pop('terms')
groups={}
for term in terms: groups.setdefault(term['variable'].split('[')[0],[]).append(term)
audit['term_families']={k:dict(count=len(v),coefficient_values=sorted(set(t['coefficient'] for t in v)),
    contribution=math.fsum(t['contribution'] for t in v)) for k,v in groups.items()}
audit['term_count']=len(terms)
audit['full_row_audit_remote_path']=str(target)
print(json.dumps(dict(audit=audit,audit_sha256=hashlib.sha256(data).hexdigest(),
    backup_manifest=json.loads((base/'backup_manifest.json').read_text()),tool_sha256=hashlib.sha256(raw).hexdigest())))
'''
    code = 'RELEASE='+repr(RELEASE)+'\nENCODED='+repr(base64.b64encode(raw).decode())+'\n'+code
    receipt = HERE/'row_audit_receipt.json'
    if receipt.exists():
        raise FileExistsError(receipt)
    r = subprocess.run(SSH+[PYTHON+' -'], input=code, capture_output=True, text=True, encoding='utf-8', timeout=14400)
    (HERE/'row_audit_transport.stderr.log').write_text(r.stderr, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(r.stderr[-4000:])
    result = json.loads(r.stdout)
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result['audit'][k] for k in ['status','name','violation','row_magnitude','relative_violation']}))


if __name__ == '__main__':
    main()
