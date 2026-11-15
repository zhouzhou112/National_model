"""Register observed first-batch launches without changing earlier case records."""
from pathlib import Path
import csv,hashlib,io,json
from deploy_batch1 import CASES
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
snap_path=sorted((HERE/'snapshots').glob('*/snapshot.json'))[-1]
snap=json.loads(snap_path.read_text(encoding='utf-8'))
catalog=REPO/'case_results/case_catalog.json';table=REPO/'case_results/case_catalog.csv'
old_json=catalog.read_bytes();old_csv=table.read_bytes();payload=json.loads(old_json)
for name,raw in [('catalog_before_batch1_launch.json',old_json),('catalog_before_batch1_launch.csv',old_csv)]:
 p=HERE/name;assert not p.exists();p.write_bytes(raw)
labels={'ops_open_2050':'OPS-Open','ops_conservative_2050':'OPS-Conservative','D1_2050':'C5','late_open_2050_factor5':'LATE-Open-TEST'}
added=[]
for key,meta in CASES.items():
 r=snap['cases'][key];release=json.loads((HERE/'deployment'/key/'release.json').read_text())
 assert r['compute_node_smoke.json']['status']=='PASS' and r['startup_resources.json']['available_memory_gib']>=700
 assert not any(x['release']==meta['release'] for x in payload['cases'])
 card=REPO/'case_results/by_case'/labels[key]/'2050'/meta['release']/'README.md';assert not card.exists();card.parent.mkdir(parents=True,exist_ok=True)
 text=f"# {labels[key]} 2050 — 第一批启动记录\n\nJob {release['job_id']}，截至 {snap['as_of_utc']} 为RUNNING，尚未验收/备份。44线程、64CPU/750G/UNLIMITED/no-requeue；启动可用内存 {r['startup_resources.json']['available_memory_gib']:.6f} GiB。\n\n云端：{r['release']}\n\n门禁与证据：{HERE}\n\n"
 if key=='D1_2050':text+='仅放开642个省内城市链路，其余Base冻结；C5诊断，不进入主情景比较。\n'
 if key=='late_open_2050_factor5':text+='仅构建、排序、前5轮测试，回调终止；不产科学解或规划状态，不代表已授权第二批。\n'
 text+='\n第一批全部终态后备份、验收并交批次报告，作者确认前不得提交第二批。\n'
 card.write_text(text,encoding='utf-8')
 record=dict(case=labels[key],year=2050,version='v1',kind='RUNNING_PRODUCTION' if meta['kind']=='OPS' else 'RUNNING_DIAGNOSTIC' if key=='D1_2050' else 'RUNNING_FACTOR_TEST',solver_status='RUNNING',acceptance_status='PENDING' if key!='late_open_2050_factor5' else 'NOT_APPLICABLE_TEST_ONLY',backup_status='PENDING_TERMINAL',release=meta['release'],job_id=release['job_id'],remote_directory=r['release'],local_evidence=[str(snap_path.relative_to(REPO)),str((HERE/'GATES_SUMMARY.json').relative_to(REPO))],case_card=str(card.relative_to(REPO)),batch=1,main_comparison_eligible=meta['kind']=='OPS')
 payload['cases'].append(record);added.append(record)
payload['as_of_utc']=snap['as_of_utc']
reader=csv.DictReader(io.StringIO(old_csv.decode('utf-8-sig')));rows=list(reader);fields=reader.fieldnames
buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows+added)
assert catalog.read_bytes()==old_json and table.read_bytes()==old_csv
catalog.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');table.write_text(buf.getvalue(),encoding='utf-8',newline='')
receipt=dict(as_of_utc=snap['as_of_utc'],added=added,old_catalog_sha256=hashlib.sha256(old_json).hexdigest(),new_catalog_sha256=hashlib.sha256(catalog.read_bytes()).hexdigest(),all_prior_records_unchanged=payload['cases'][:-4]==json.loads(old_json)['cases'])
(HERE/'batch1_case_registration.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(added=len(added),prior_records_unchanged=receipt['all_prior_records_unchanged'])))
