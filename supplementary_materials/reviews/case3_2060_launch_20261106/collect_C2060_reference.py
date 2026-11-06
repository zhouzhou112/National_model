"""Read only three explicit C2060 template/screen files; no scheduler actions."""
import pathlib,subprocess,base64,json,hashlib,csv,io
HERE=pathlib.Path(__file__).resolve().parent
REMOTE=r"""
from pathlib import Path
import base64,json,hashlib,csv,io
b=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1')
names=['source_screen.csv','output_8760/candidate_selection.csv','continuation.sbatch','launch_config.json']
r={}
for n in names:
 raw=(b/n).read_bytes();r[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
print(json.dumps({'release':str(b),'files':r}))
"""
def main():
 target=HERE/'C2060_reference_receipt.json';assert not target.exists()
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],input=REMOTE,text=True,encoding='utf-8',capture_output=True,timeout=90);p.check_returncode();r=json.loads(p.stdout)
 for n,e in r['files'].items():
  raw=base64.b64decode(e.pop('base64'));assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256']
  dest=HERE/'C2060_reference'/n;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():assert dest.read_bytes()==raw
  else:dest.write_bytes(raw)
 local=HERE.parent/'base_2060_screen_20261026/ready/source_screen.csv'
 assert hashlib.sha256(local.read_bytes()).hexdigest()==r['files']['source_screen.csv']['sha256']
 rows=list(csv.DictReader(io.StringIO((HERE/'C2060_reference/output_8760/candidate_selection.csv').read_text())))
 excluded=sorted((x['grid_uid'],x['technology']) for x in rows if x['screened_out'].lower()=='true')
 raw=json.dumps(excluded,separators=(',',':')).encode();r.update(screen_sha_matches_local=True,excluded_columns=len(excluded),excluded_identity_sha256=hashlib.sha256(raw).hexdigest())
 target.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='files'}))
if __name__=='__main__':main()
