"""Verify every immutable backup file and recover own annual row duals on T550."""
from pathlib import Path
import argparse,datetime,gzip,hashlib,json,socket,time
import numpy as np
from cispo_model.relative_acceptance import archived_inputs,add_relative_profile,VERSION
from dual_extensions import RowsObserver

BASE=Path('/home/zz2/National_model_server/cloud_backup')
RELEASE='20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1'
SIDE='acceptance_resource_late_20261119'
CASES={'LATE-Open-2050':RELEASE}

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def save(p,x):
 assert not Path(p).exists(),str(p)
 Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cloud-sha',required=True);a=ap.parse_args()
 assert socket.gethostname().split('.')[0]=='t550'
 b=BASE/RELEASE;root=b/'output_8760';out=b/SIDE
 status=json.loads((BASE/'_operations/20261119_resource_lateopen2050_completed/transfer_status.json').read_text())
 assert status['status']=='COMPLETE' and status['source_unchanged'] and all(x['status']=='VERIFIED' for x in status['stages'])
 backup=json.loads((b/'backup_manifest.json').read_text());assert backup['status']=='COMPLETE' and backup['source_unchanged_after_transfer']
 assert a.cloud_sha==backup['source_result_manifest_sha256']==sha(root/'result_manifest.json')
 assert not out.exists();out.mkdir();checked={};stats={};start=time.time()
 for record in backup['files']:
  p=b/record['path'];assert p.is_relative_to(b) and not p.is_symlink()
  assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],record['path']
  checked[record['path']]=dict(bytes=record['bytes'],sha256=record['sha256']);stats[record['path']]=[p.stat().st_size,p.stat().st_mtime_ns]
 save(out/'backup_verification.json',dict(status='PASS',checked=checked,source_file_stats=stats,files=len(checked),bytes=sum(r['bytes'] for r in checked.values()),source_result_manifest_sha256=a.cloud_sha))
 qc=json.loads((root/'solution_qc.json').read_text());solve=json.loads((root/'solve_report.json').read_text());inputs=archived_inputs(root)
 save(out/'assessment_inputs.json',inputs);profile=add_relative_profile(qc,solve,inputs=inputs)
 save(out/'solution_qc_relative_v1_baseline.json',dict(evaluator_version=VERSION,source_sha256={n:sha(root/n) for n in ['solution_qc.json','solve_report.json','model_config_snapshot.json','result_manifest.json']},acceptance_profiles={'relative_v1':profile}))
 rows=out/'annual_rows';rows.mkdir();cp=json.loads((root/'barrier_checkpoint/barrier_checkpoint_manifest.json').read_text());pi=np.load(root/'barrier_checkpoint/dual_barpi.npy',mmap_mode='r',allow_pickle=False)
 observer=RowsObserver(b,rows,pi,dict(ordering=cp['lp_ordering']));inside=False
 with gzip.open(root/'model_archive/original.mps.gz','rt',encoding='ascii') as f:
  for line in f:
   if line.startswith('ROWS'):inside=True
   elif line.startswith('COLUMNS'):observer.finish();break
   elif inside:
    parts=line.split()
    if parts and parts[0]!='N':observer.consume(parts[0],parts[1])
  else:raise RuntimeError('MPS has no COLUMNS boundary')
 assert all([(b/n).stat().st_size,(b/n).stat().st_mtime_ns]==v for n,v in stats.items())
 save(out/'PREPARATION_COMPLETE.json',dict(status='PASS',seconds=time.time()-start,source_unchanged=True,row_index=solve['solution_quality_locations']['maximum_constraint_violation']['index'],baseline_relative_status=profile['status']))
 print(json.dumps(dict(status='PASS',seconds=time.time()-start)),flush=True)

if __name__=='__main__':main()
