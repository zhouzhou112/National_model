"""Integrate per-case receipts, preserve previous delivery metadata, validate limits."""
from pathlib import Path
import argparse,hashlib,json,datetime
HERE=Path(__file__).resolve().parent
RET=HERE.parents[2].parent/'claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finalize(case):
 d=RET/case;meta=d/'metadata';meta.mkdir(exist_ok=True)
 for name in ['summary.json','transfer_verification.json','sha256.txt']:
  p=d/name;old=meta/('before_flex_20261105_'+name)
  if p.exists() and not old.exists():old.write_bytes(p.read_bytes())
 s=json.loads((d/'summary.json').read_text(encoding='utf-8')) if (d/'summary.json').exists() else {'case':case}
 v=json.loads((d/'transfer_verification.json').read_text(encoding='utf-8')) if (d/'transfer_verification.json').exists() else {}
 for receipt in [HERE/('t9_receipt_'+case+'.json'),HERE/(case+'_t4_check_receipt.json'),HERE/('metrics_receipt_'+case+'.json'),meta/'flex_transfer_receipt.json',meta/'revenue_transfer_receipt.json',meta/'national_transfer_receipt.json']:
  if receipt.exists():
   z=json.loads(receipt.read_text(encoding='utf-8-sig'));items=z.get('files',z)
   for name,item in items.items():
    if isinstance(item,dict) and 'sha256' in item:
     assert sha(d/name)==item['sha256'],name;v[name]=item
 for task,name in [('T9','t9_summary.json'),('T4','t4_price_checks.json'),('T6','metrics_summary.json'),('T8','revenue_summary.json')]:
  p=meta/name
  if p.exists():
   z=json.loads(p.read_text(encoding='utf-8-sig'));s[task]='COMPLETE' if z.get('status')=='PASS' else z.get('status');s[task+'_checks']=z
   if task=='T8':s['T8']=z.get('T8','UNKNOWN')
   if name=='metrics_summary.json':
    s['T6']='COMPLETE' if z.get('T6')=='PASS' else z.get('T6');s['T7']='COMPLETE' if z.get('T7')=='PASS' else z.get('T7','NOT_REQUESTED')
 if case not in ['base2030','base2040','base2050','base2060','case3_2030','case3_2040']:s['T2']='NOT_REQUESTED'
 s['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['result_label']='初步结果';s['dual_grade']='BARRIER_DUAL_ENGINEERING_GRADE'
 # Verify immutable server receipts first; metadata generated here is identified as local.
 for n,i in v.items():
  if n in ['summary.json','transfer_verification.json','sha256.txt']:continue
  if (d/n).exists() and 'sha256' in i:assert sha(d/n)==i['sha256'],n
 files={}
 for p in d.rglob('*'):
  if not p.is_file() or p.name in ['summary.json','transfer_verification.json','sha256.txt']:continue
  assert p.suffix not in ['.npz','.npy','.png','.pdf'],p
  assert not p.name.endswith('.mps.gz'),p
  assert p.stat().st_size<=30000000,p
  n=p.relative_to(d).as_posix();files[n]=dict(v.get(n,{}),sha256=sha(p),bytes=p.stat().st_size,local_verified=True)
 s['files']=files;s['return_bytes_payload']=sum(x['bytes'] for x in files.values());s['transfer_limits']={'file_max_bytes':30000000,'case_max_bytes':100000000}
 (d/'summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (d/'transfer_verification.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
 allfiles={p.relative_to(d).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in d.rglob('*') if p.is_file() and p.name!='sha256.txt'}
 (d/'sha256.txt').write_text(''.join(v['sha256']+'  '+n+'\n' for n,v in sorted(allfiles.items())),encoding='utf-8')
 total=sum(p.stat().st_size for p in d.rglob('*') if p.is_file());assert total<=100000000
 out=dict(case=case,status='PASS',files=len(allfiles),total_bytes=total,summary_sha256=sha(d/'summary.json'),sha256_txt_sha256=sha(d/'sha256.txt'),tasks={k:s.get(k) for k in ['T1','T2','T3','T4','T6','T7','T8','T9']})
 (HERE/(case+'_delivery_integrity.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('cases',nargs='+');a=p.parse_args()
 for c in a.cases:finalize(c)
