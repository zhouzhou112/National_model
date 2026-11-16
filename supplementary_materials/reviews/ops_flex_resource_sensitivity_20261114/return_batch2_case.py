"""Return one accepted case with the established small-file list and derived tables."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tarfile
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
CASES={'OPS-Open-2030': ('OPS-Open', 2030, '20261115_opsopen_2030_v9_t44_m750_tol1e4_v1'), 'OPS-Open-2040': ('OPS-Open', 2040, '20261115_opsopen_2040_v9a12_t44_m750_tol1e4_v1'), 'OPS-Open-2060': ('OPS-Open', 2060, '20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1')}
REMOTE=r'''
from pathlib import Path
import hashlib,json,tarfile,sys,io
root=Path('/home/zz2/National_model_server/cloud_backup')/release;out=root/'output_8760';side=root/'acceptance_resource_batch2_20261116'
assert json.loads((side/'acceptance_record.json').read_text())['status']=='PASS'
assert json.loads((side/'analysis/analysis_summary.json').read_text())['status']=='PASS'
backup=json.loads((root/'backup_manifest.json').read_text());assert backup['status']=='COMPLETE'
index={x['path']:x for x in backup['files']};config=json.loads((out/'model_config_snapshot.json').read_text())['resolved_configuration'];files={};omitted={}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def add(name,path,source_type,expected=None):
 assert path.is_file() and not path.is_symlink() and path.stat().st_size<=32*1024**2
 digest=sha(path)
 if expected:assert expected['bytes']==path.stat().st_size and expected['sha256']==digest,name
 files[name]=dict(bytes=path.stat().st_size,sha256=digest,remote_source=str(path),source_type=source_type)
for name in standard_names:
 if not (out/name).exists():
  assert name=='candidate_selection.csv' and not config.get('candidate_screen',{}).get('enabled',False)
  omitted[name]='NOT_APPLICABLE_UNSCREENED_FROZEN_CASE';continue
 add('output_8760/'+name,out/name,'ORIGINAL_OUTPUT',index['output_8760/'+name])
extras=['frozen_capacity_audit.csv','frozen_capacity_closure_audit.csv','frozen_capacity_closure_report.json','frozen_capacity_expected.json','frozen_capacity_output_check.json','frozen_capacity_report.json','frozen_capacity_source_alignment.json','resource_structure_audit.json','resource_v2g_slack_check.json','capacity_bound_selection_audit.json']
for name in extras:
 if (out/name).exists():add('output_8760/'+name,out/name,'ORIGINAL_OUTPUT',index['output_8760/'+name])
for p in side.rglob('*'):
 if p.is_file():
  assert p.suffix in {'.json','.csv','.gz','.txt','.md'},str(p)
  add('acceptance_resource_batch2_20261116/'+str(p.relative_to(side)),p,'READ_ONLY_DERIVED_SIDECAR')
add('backup_manifest.json',root/'backup_manifest.json','VERIFIED_BACKUP_MANIFEST')
assert sum(x['bytes'] for x in files.values())<=200*1024**2
receipt=dict(case=case,release=release,files=files,standard_list_count=len(standard_names),original_standard_returned=len(standard_names)-len(omitted),omitted_not_applicable=omitted,original_source_manifest_sha256=sha(out/'result_manifest.json'),file_count=len(files),bytes=sum(x['bytes'] for x in files.values()),maximum_file_bytes=max(x['bytes'] for x in files.values()),excludes=['original.mps.gz','primal_barx.npy','dual_barpi.npy','large thermal/reservoir/flexible dispatch NPZ','hourly_province_balance.csv.gz'])
assert receipt['original_source_manifest_sha256']==backup['source_result_manifest_sha256']
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tf:
 raw=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode();ti=tarfile.TarInfo('delivery_manifest.json');ti.size=len(raw);tf.addfile(ti,io.BytesIO(raw))
 for name,record in files.items():tf.add(record['remote_source'],arcname=name,recursive=False)
'''
def main():
 ap=argparse.ArgumentParser();ap.add_argument('case',choices=CASES);a=ap.parse_args();label,year,release=CASES[a.case]
 reference=HERE.parent/'completed_results_20261027/case3_2040/collect_receipt.json';names=list(json.loads(reference.read_text())['files']);assert len(names)==73
 dest=REPO/'case_results/by_case'/label/str(year)/release;dest.mkdir(parents=True,exist_ok=True)
 receipts=HERE/'acceptance_batch2_20261116';log=receipts/(a.case+'_return.stderr.log')
 code='case='+repr(a.case)+'\nrelease='+repr(release)+'\nstandard_names='+repr(names)+'\n'+REMOTE
 ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -']
 with log.open('wb') as err:
  process=subprocess.Popen(ssh,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err);process.stdin.write(code.encode());process.stdin.close()
  manifest=None;verified=[]
  with tarfile.open(fileobj=process.stdout,mode='r|gz') as tf:
   for member in tf:
    assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
    raw=tf.extractfile(member).read()
    if member.name=='delivery_manifest.json':
     assert manifest is None;manifest=json.loads(raw)
    else:
     assert manifest and member.name in manifest['files'];r=manifest['files'][member.name];assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];verified.append(member.name)
    p=dest/member.name;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==raw,'Existing delivery differs: '+str(p)
    else:p.write_bytes(raw)
  assert process.wait()==0,log.read_text(errors='replace')
 assert set(verified)==set(manifest['files'])
 for name,r in manifest['files'].items():
  p=dest/name;assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],name
 receipt=dict(status='PASS',case=a.case,release=release,local_directory=str(dest),files=len(verified),bytes=manifest['bytes'],maximum_file_bytes=manifest['maximum_file_bytes'],all_bytes_sha_match=True,omitted_not_applicable=manifest['omitted_not_applicable'])
 (receipts/(a.case+'_return_receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
