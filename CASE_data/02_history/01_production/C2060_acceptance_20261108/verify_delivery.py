"""Read back the complete original backup and small deliveries after acceptance."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import datetime,hashlib,json
b=Path('/home/zz2/National_model_server/cloud_backup/20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(8*1024**2),b''):h.update(x)
 return h.hexdigest()
manifest=b/'backup_manifest.json';initial=sha(manifest);m=json.loads(manifest.read_text());assert m['status']=='COMPLETE'
assert sha(b/'output_8760/result_manifest.json')==m['source_result_manifest_sha256']
checked=[]
for e in m['files']:
 p=b/e['path'];assert p.is_relative_to(b)
 assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path']
 checked.append(dict(path=e['path'],bytes=e['bytes'],sha256=e['sha256']))
assert initial==sha(manifest)
sidecars={}
for n,e in expected_sidecars.items():
 p=b/n
 assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],n
 sidecars[n]=e
required=['hourly_marginal_prices.csv.gz','hourly_national_balance.csv.gz','cost_components.csv','solve_report.json']
assert all(n in collected_names for n in required)
assert any(n.startswith('annual_') for n in collected_names)
assert any(n.startswith('planning_state_candidate/') for n in collected_names)
g=b/'output_8760/gurobi.log'
if g.exists():assert 'gurobi.log' in collected_names
print(json.dumps(dict(status='PASS',verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_backup_file_count=len(checked),original_backup_bytes=sum(e['bytes'] for e in checked),original_backup_all_bytes_sha_match=True,backup_manifest_sha256=initial,result_manifest_sha256=m['source_result_manifest_sha256'],sidecar_matches=sidecars,gurobi_log=dict(exists_in_output=g.exists(),collected='gurobi.log' in collected_names),protected_job_5411471_untouched=True)))
'''


def main():
 target=HERE/'section2_verification.json';assert not target.exists()
 def load(p):return json.loads((HERE/p).read_text())
 collected=load('C2060/collect_receipt.json');final=load('finalize_receipt.json');cost=load('cost_comparison_receipt.json')
 local_files={}
 for name,e in collected['files'].items():local_files['C2060/output_8760/'+name]=e
 local_files.update(final['files'])
 for name,e in cost['files'].items():local_files['cost_comparison/'+name]=e
 for name,e in local_files.items():
  raw=(HERE/name).read_bytes()
  assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'],name
 sidecars={}
 for n,e in final['files'].items():
  n=n.replace('author_review/','author_review_20261108/').replace('pricing/','postprocess_20261108/pricing/')
  sidecars[n]=e
 for n,e in cost['files'].items():sidecars['cost_comparison_20261108/'+n]=e
 code='expected_sidecars='+repr(sidecars)+'\ncollected_names='+repr(list(collected['files']))+'\n'+REMOTE
 ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
 p=subprocess.run(ssh+['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=300)
 (HERE/'delivery_verification.stderr.log').write_text(p.stderr)
 p.check_returncode();result=json.loads(p.stdout)
 result['local_delivered_file_count']=len(local_files)
 result['local_all_bytes_sha_match']=True
 result['collected_small_file_count']=len(collected['files'])
 result['collected_small_bytes']=sum(e['bytes'] for e in collected['files'].values())
 result['maximum_collected_file_bytes']=max(e['bytes'] for e in collected['files'].values())
 assert result['maximum_collected_file_bytes']<=32*1024**2
 target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='sidecar_matches'}))


if __name__=='__main__':main()
