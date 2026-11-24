"""Read-only acceptance and row-dual recovery on fully verified T550 backups."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,socket,sys,time
import numpy as np
from cispo_model.relative_acceptance import add_relative_profile,archived_inputs,VERSION
from dual_extensions import RowsObserver

BASE=Path('/home/zz2/National_model_server/cloud_backup')
OP=BASE/'_operations/20261116_resource_batch2_ops_completed'
CASES={'OPS-Open-2030': '20261115_opsopen_2030_v9_t44_m750_tol1e4_v1', 'OPS-Open-2040': '20261115_opsopen_2040_v9a12_t44_m750_tol1e4_v1', 'OPS-Open-2060': '20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('case',choices=CASES);p.add_argument('--cloud-identities',required=True,type=Path);a=p.parse_args()
 assert socket.gethostname().split('.')[0]=='t550'
 b=BASE/CASES[a.case];root=b/'output_8760';out=b/'acceptance_resource_batch2_20261116';assert not out.exists();out.mkdir()
 started=time.time();status=json.loads((OP/'transfer_status.json').read_text());assert status['status']=='COMPLETE' and status['source_unchanged']
 assert all(any(x['release']==b.name and x['tier']==tier and x['status']=='VERIFIED' for x in status['stages']) for tier in ['T1','T2','T3'])
 backup=json.loads((b/'backup_manifest.json').read_text());assert backup['status']=='COMPLETE' and backup['source_unchanged_after_transfer']
 cloud=json.loads(a.cloud_identities.read_text());assert cloud[b.name]==backup['source_result_manifest_sha256']==sha(root/'result_manifest.json')
 checked={};stats={}
 for record in backup['files']:
  f=b/record['path'];assert f.is_relative_to(b) and not f.is_symlink()
  assert f.stat().st_size==record['bytes'] and sha(f)==record['sha256'],record['path']
  checked[record['path']]=dict(bytes=record['bytes'],sha256=record['sha256']);stats[record['path']]=[f.stat().st_size,f.stat().st_mtime_ns]
 save(out/'backup_verification.json',dict(status='PASS',files=len(checked),bytes=sum(x['bytes'] for x in checked.values()),all_tiers_verified=True,source_result_manifest_sha256=cloud[b.name],checked=checked,source_file_stats=stats))
 print(a.case,'FULL_BACKUP_SHA_PASS',len(checked),flush=True)
 qc=json.loads((root/'solution_qc.json').read_text());solve=json.loads((root/'solve_report.json').read_text())
 inputs=archived_inputs(root);save(out/'assessment_inputs.json',inputs);profile=add_relative_profile(qc,solve,inputs=inputs)
 source={n:sha(root/n) for n in ['result_manifest.json','solution_qc.json','solve_report.json','model_config_snapshot.json','frozen_capacity_output_check.json','resource_structure_audit.json','preservation_report.json']}
 save(out/'solution_qc_relative_v1.json',dict(source_sha256=source,acceptance_profiles={'relative_v1':profile}))
 frozen=json.loads((root/'frozen_capacity_output_check.json').read_text());struct=json.loads((root/'resource_structure_audit.json').read_text());pres=json.loads((root/'preservation_report.json').read_text())
 config=json.loads((root/'model_config_snapshot.json').read_text())['resolved_configuration'];assert config['planning_year']==int(a.case.rsplit('-',1)[-1]);assert not config.get('candidate_screen',{}).get('enabled',False)
 checks=dict(current_relative_v1=profile['status']=='PASS',frozen_capacity_identity=frozen['status']=='PASS',annual_resource_structure=struct['status']=='PASS',original_preservation=pres['status']=='COMPLETE',optimal=solve['status']=='OPTIMAL')
 metrics=solve['solution_contract']['barrier_primal_dual_metrics'];P=float(metrics['primal_objective']);D=float(metrics['dual_objective'])
 result=dict(status='PASS' if all(checks.values()) else 'FAIL',case=a.case,planning_year=config['planning_year'],release=b.name,checks=checks,P_million_cny=P,D_million_cny=D,primal_dual_gap_million_cny=P-D,screening_certificate='NOT_APPLICABLE_UNSCREENED',screening_B_million_cny=0.,strict_source_status=qc['status'],strict_failed_checks=[k for k,v in qc['hard_checks'].items() if v is False],evaluator_version=VERSION,source_sha256=source,scope='Quality label under author relative_v1 rules; no change to archived QC or automatic state adoption',assessed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 save(out/'acceptance_record.json',result);print(a.case,'ACCEPTANCE',result['status'],flush=True)
 rows=out/'annual_rows';rows.mkdir();cp=json.loads((root/'barrier_checkpoint/barrier_checkpoint_manifest.json').read_text());identity=dict(ordering=cp['lp_ordering'])
 pi=np.load(root/'barrier_checkpoint/dual_barpi.npy',mmap_mode='r',allow_pickle=False);observer=RowsObserver(b,rows,pi,identity)
 in_rows=False
 with gzip.open(root/'model_archive/original.mps.gz','rt',encoding='ascii') as f:
  for line in f:
   if line.startswith('ROWS'):in_rows=True
   elif line.startswith('COLUMNS'):observer.finish();break
   elif in_rows:
    parts=line.split()
    if parts and parts[0]!='N':observer.consume(parts[0],parts[1])
  else:raise RuntimeError('No original MPS COLUMNS boundary')
 assert source=={n:sha(root/n) for n in source}
 assert all([(b/n).stat().st_size,(b/n).stat().st_mtime_ns]==s for n,s in stats.items())
 tools={str(f.relative_to(Path(__file__).parent)):sha(f) for f in Path(__file__).parent.rglob('*.py') if '__pycache__' not in f.parts}
 save(out/'evidence_manifest.json',dict(status='PASS',original_backup_all_bytes_sha_match=True,source_unchanged=True,source_sha256=source,tool_sha256=tools,evaluator_version=VERSION,seconds=time.time()-started,annual_row_duals_recovered_from='Original MPS ROWS plus own BarPi, complete row-order digest checked',original_export_error=json.loads((root/'dual_export_status.json').read_text()).get('annual_row_duals_reason')))
 save(out/'ACCEPTANCE_AND_ROWS_COMPLETE.json',dict(status=result['status'],case=a.case,seconds=time.time()-started));print(a.case,'COMPLETE',time.time()-started,flush=True)
if __name__=='__main__':main()
