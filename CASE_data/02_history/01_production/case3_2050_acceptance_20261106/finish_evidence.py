"""Finalize the completed evidence once, return only small SHA-verified sidecars."""
import pathlib,json,base64,hashlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
PY='/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
REMOTE=r"""
from pathlib import Path
import json,hashlib,subprocess,base64,sys
b=Path('/home/zz2/National_model_server/cloud_backup/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2')
side=b/'acceptance_20261106';out=b/'author_review_20261106';price=b/'postprocess_20261106/pricing'
assert (price/'screen_pricing_certificate.json').exists(),'Pricing still running'
receipt=json.loads((b/'postprocess_20261106/pricing_receipt.json').read_text())
for n in ['vre_site_reduced_costs.csv','screen_pricing_certificate.json','negative_screened_columns.csv','screen_sign_flip_sites.csv']:
 raw=(price/n).read_bytes();e=receipt['files'][n];assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'],n
assert hashlib.sha256((side/'finalize_acceptance.py').read_bytes()).hexdigest()==tool_sha
assert not out.exists(),'Review existing operation; do not repeat'
cmd=[sys.executable,str(side/'finalize_acceptance.py'),'--release-root',str(b),'--output',str(out),'--frozen-source',str(side/'frozen_row_formulation_verified.json')]
r=subprocess.run(cmd,capture_output=True,text=True)
(side/'finalize.stdout.log').write_text(r.stdout);(side/'finalize.stderr.log').write_text(r.stderr)
assert r.returncode==0,r.stderr
payload={}
for p in list(out.iterdir())+[price/n for n in ['screen_pricing_certificate.json','negative_screened_columns.csv','screen_sign_flip_sites.csv']]:
 assert p.is_file() and p.stat().st_size<30*2**20
 raw=p.read_bytes();name=('pricing/' if p.parent==price else 'author_review/')+p.name
 payload[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
print(json.dumps({'files':payload,'summary':json.loads(r.stdout),'command':cmd}))
"""
def main():
 target=HERE/'finalize_receipt.json';assert not target.exists()
 code='tool_sha='+repr(hashlib.sha256((HERE/'finalize_acceptance.py').read_bytes()).hexdigest())+'\n'+REMOTE
 r=subprocess.run(SSH+[PY+' -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=180)
 (HERE/'finalize_transport.stderr.log').write_text(r.stderr,encoding='utf-8');r.check_returncode();data=json.loads(r.stdout)
 for n,e in data['files'].items():
  raw=base64.b64decode(e.pop('base64'));assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
  p=HERE/n;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==raw
  else:p.write_bytes(raw)
 target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(data['summary'],ensure_ascii=False))
if __name__=='__main__':main()
