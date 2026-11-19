"""Return only completed preparation evidence and the compact R1 capsule."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,os
HERE=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import hashlib,json,tarfile,sys,io
root=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114/late2060_preparation_20261119')
assert json.loads((root/'PREPARATION_GATES_COMPLETE_v2.json').read_text())['status']=='PASS'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
names=['installation_receipt.json','author_preparation_acceptance.json','initial_selection_audit.json','initial_state_and_2050_change_audit.csv','final_selection.json','selection_receipt.json','identity_reference_source.json','identity_v2_result.json','PREPARATION_GATES_COMPLETE_v2.json','execution_results.json','execution_results_v2.json','STOP.json']
paths=[root/n for n in names if (root/n).is_file()]
for directory in ['R1_v1/prepared_state','R1_v1/evidence']:
 for p in (root/directory).rglob('*'):
  if not p.is_file() or any(n in p.parts for n in ['model_archive','solution_snapshot','barrier_checkpoint']):continue
  if p.suffix in {'.json','.csv','.log'} or p.name=='capacity_cohorts.csv.gz':paths.append(p)
for directory in ['identity_24h_central_v2','selected_1h','restricted_24h','t550_preflight']:
 for p in (root/directory).rglob('*'):
  if p.is_file() and p.name in {'identity_gate.json','selection_build_gate.json','solve_report.json','solution_qc.json','preservation_report.json','run_identity.json','build_report.json','model_config_snapshot.json','preflight_report.json'}:paths.append(p)
for n in ['directional_pricing_report.json','parse_cache_manifest.json']:
 p=root/'reference_pricing_2060'/n
 if p.exists():paths.append(p)
files={};omitted={}
for p in sorted(set(paths)):
 assert p.is_relative_to(root) and not p.is_symlink()
 name=p.relative_to(root).as_posix();record=dict(bytes=p.stat().st_size,sha256=sha(p))
 if p.stat().st_size>32*1024**2:omitted[name]=dict(**record,reason='Large original preparation audit retained on T550');continue
 files[name]=record
assert sum(r['bytes'] for r in files.values())<=100*1024**2
reused=[n for n,r in files.items() if known.get(n)==r['sha256']]
manifest=dict(status='PASS',remote_root=str(root),files=files,omitted_large=omitted,reused_local_sha_match=reused,scope='Completed engineering summaries and compact R1 state only; diagnostic dispatch tables, reference price CSV, original MPS and raw solver arrays stay on T550',submitted=False)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tf:
 raw=(json.dumps(manifest,indent=2)+'\n').encode();e=tarfile.TarInfo('preparation_transfer_manifest_v2.json');e.size=len(raw);tf.addfile(e,io.BytesIO(raw))
 for n in files:
  if n not in reused:tf.add(root/n,arcname=n,recursive=False)
'''

def main():
 dest=HERE/'t550_evidence'
 if os.name=='nt':dest=Path('\\\\?\\'+str(dest.resolve()))
 dest.mkdir(exist_ok=True);manifest=None;seen=[]
 known={p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}
 with (HERE/'collect.stderr.log').open('wb') as err:
  p=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','python3 -'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err);p.stdin.write(('known='+repr(known)+'\n'+REMOTE).encode());p.stdin.close()
  with tarfile.open(fileobj=p.stdout,mode='r|gz') as tf:
   for m in tf:
    assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
    raw=tf.extractfile(m).read()
    if m.name=='preparation_transfer_manifest_v2.json':
     manifest=json.loads(raw)
     for n in manifest['reused_local_sha_match']:
      q=dest/n;r=manifest['files'][n];assert q.stat().st_size==r['bytes'] and hashlib.sha256(q.read_bytes()).hexdigest()==r['sha256'];seen.append(n)
    else:
     r=manifest['files'][m.name];assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];seen.append(m.name)
    target=dest/m.name;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
     old=target.read_bytes()
     if m.name=='preparation_transfer_manifest_v2.json' and old!=raw:
      history=dest/'transfer_history';history.mkdir(exist_ok=True);(history/('manifest_'+hashlib.sha256(old).hexdigest()[:16]+'.json')).write_bytes(old);target.write_bytes(raw)
     else:assert old==raw,'Existing evidence differs: '+m.name
    else:target.write_bytes(raw)
  assert p.wait()==0,(HERE/'collect.stderr.log').read_text(errors='replace')
 assert set(seen)==set(manifest['files'])
 receipt=dict(status='PASS',files=len(seen),bytes=sum(r['bytes'] for r in manifest['files'].values()),all_bytes_sha_match=True,omitted_large=manifest['omitted_large'],submitted=False)
 (HERE/'collect_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
