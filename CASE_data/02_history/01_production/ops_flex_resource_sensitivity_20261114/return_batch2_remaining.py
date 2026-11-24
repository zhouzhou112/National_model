"""Return 2040/2060 in one SSH stream; reuse completed server calculations."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
import return_batch2_case as standard
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];OUT=HERE/'acceptance_batch2_20261116'
SELECTED={k:standard.CASES[k] for k in ['OPS-Open-2040','OPS-Open-2060']}
PREPARE=standard.REMOTE.split("with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tf:")[0]
REMOTE=r'''
from pathlib import Path
import tarfile,sys,json,io,hashlib
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tf:
 for case,(_,year,release) in selected.items():
  scope=dict(case=case,release=release,standard_names=standard_names)
  exec(compile(prepare,'<verified-single-case-collection>','exec'),scope)
  receipt=scope['receipt'];raw=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode();ti=tarfile.TarInfo(case+'/delivery_manifest.json');ti.size=len(raw);tf.addfile(ti,io.BytesIO(raw))
  for name,record in receipt['files'].items():tf.add(record['remote_source'],arcname=case+'/'+name,recursive=False)
 base=Path('/home/zz2/National_model_server/cloud_backup');reportdir=Path('/home/zz2/National_model_server/analysis_tools_resource_batch2_20261116/combined_report')
 if not (reportdir/'four_year_summary.json').exists():
  import pandas as pd
  refs={2030:('20261115_opsopen_2030_v9_t44_m750_tol1e4_v1','acceptance_resource_batch2_20261116'),2040:('20261115_opsopen_2040_v9a12_t44_m750_tol1e4_v1','acceptance_resource_batch2_20261116'),2050:('20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1','acceptance_resource_batch1_20261115'),2060:('20261115_opsopen_2060_v9a12_t44_m750_tol1e4_v1','acceptance_resource_batch2_20261116')}
  rows=[];services=[];sources={}
  for year,(release,sidecar) in refs.items():
   p=base/release/sidecar/'analysis/analysis_summary.json';raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();s=json.loads(raw);assert s['status']=='PASS' and s['annual']['planning_year']==year
   if year==2050:assert h==previous_sha
   sources[year]=dict(path=str(p),sha256=h)
   row=dict(planning_year=year,P_million_cny=s['P_million_cny'],D_million_cny=s['D_million_cny'],vre_curtailment_gwh=s['annual']['vre_curtailment_gwh'],storage_charge_gwh=s['annual']['storage_charge_gwh'],storage_discharge_gwh=s['annual']['storage_discharge_gwh'],v2g_discharge_gwh=s['actual_v2g_discharge_gwh'],startup_shutdown_cost_million_cny=s['startup_shutdown_cost_million_cny'])
   for c in s['comparisons']:
    prefix='ref' if c['reference']=='REF' else 'central_ops'
    for name in ['point_saving_yi_cny','lower_saving_yi_cny','upper_saving_yi_cny']:row[prefix+'_'+name]=c[name]
   rows.append(row)
   for service in s['services']:services.append(dict(planning_year=year,**service))
  reportdir.mkdir(exist_ok=False);pd.DataFrame(rows).to_csv(reportdir/'OPS_Open_four_year_summary.csv',index=False);pd.DataFrame(services).to_csv(reportdir/'OPS_Open_four_year_services.csv',index=False)
  result=dict(status='PASS',computed_on='T550',rows=rows,services=services,sources=sources,previous_2050_reused_without_recalculation=True);(reportdir/'four_year_summary.json').write_text(json.dumps(result,indent=2)+'\n')
 batchfiles={}
 for name in ['four_year_summary.json','OPS_Open_four_year_summary.csv','OPS_Open_four_year_services.csv']:
  p=reportdir/name;raw=p.read_bytes();batchfiles[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());tf.add(p,arcname='_batch/'+name,recursive=False)
 raw=(json.dumps(batchfiles,indent=2)+'\n').encode();ti=tarfile.TarInfo('_batch/transfer_receipt.json');ti.size=len(raw);tf.addfile(ti,io.BytesIO(raw))
'''
def main():
 ref=HERE.parent/'completed_results_20261027/case3_2040/collect_receipt.json';names=list(json.loads(ref.read_text())['files']);assert len(names)==73
 old=ROOT/'case_results/by_case/OPS-Open/2050/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1/delivery_manifest.json';m=json.loads(old.read_text());previous=m['files']['acceptance_resource_batch1_20261115/analysis/analysis_summary.json']['sha256']
 code='selected='+repr(SELECTED)+'\nstandard_names='+repr(names)+'\nprepare='+repr(PREPARE)+'\nprevious_sha='+repr(previous)+'\n'+REMOTE
 manifests={};seen={k:[] for k in SELECTED};batch={};log=OUT/'remaining_single_connection.stderr.log'
 with log.open('wb') as err:
  p=subprocess.Popen(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server','/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err)
  p.stdin.write(code.encode());p.stdin.close()
  with tarfile.open(fileobj=p.stdout,mode='r|gz') as tf:
   for member in tf:
    assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
    case,name=member.name.split('/',1);raw=tf.extractfile(member).read()
    if case=='_batch':batch[name]=raw;continue
    assert case in SELECTED;label,year,release=SELECTED[case];dest=ROOT/'case_results/by_case'/label/str(year)/release
    if name=='delivery_manifest.json':manifests[case]=json.loads(raw)
    else:
     e=manifests[case]['files'][name];assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'];seen[case].append(name)
    target=dest/name;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert target.read_bytes()==raw,target
    else:target.write_bytes(raw)
  assert p.wait()==0,log.read_text(errors='replace')
 for case,m in manifests.items():
  assert set(seen[case])==set(m['files']);label,year,release=SELECTED[case];dest=ROOT/'case_results/by_case'/label/str(year)/release
  for name,e in m['files'].items():
   f=dest/name;assert f.stat().st_size==e['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==e['sha256']
  receipt=dict(status='PASS',case=case,release=release,local_directory=str(dest),files=len(m['files']),bytes=m['bytes'],maximum_file_bytes=m['maximum_file_bytes'],all_bytes_sha_match=True,omitted_not_applicable=m['omitted_not_applicable']);(OUT/(case+'_return_receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
 proof=json.loads(batch['transfer_receipt.json'])
 for name,e in proof.items():
  raw=batch[name];assert len(raw)==e['bytes'] and hashlib.sha256(raw).hexdigest()==e['sha256'];target=OUT/name
  if target.exists():assert target.read_bytes()==raw
  else:target.write_bytes(raw)
 (OUT/'four_year_transfer_receipt.json').write_bytes(batch['transfer_receipt.json'])
if __name__=='__main__':main()
