"""Build navigable case/version indexes without moving or deleting originals.

Only read local metadata and file sizes. Scientific computations come from the
SHA-verified compact T550 delivery. Writes only case_results/.
"""
from pathlib import Path
import csv,hashlib,json,subprocess,os,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DEST=ROOT/'case_results'
DELIVERY=DEST/'deliveries/20261028_t550_v1'
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def link(label,p):return '['+label+'](<'+p.resolve().as_posix()+'>)'
def status(p):
 if not p.exists():return 'NOT_INDEXED'
 v=js(p);return v.get('acceptance_profiles',{}).get('relative_v1',{}).get('status',v.get('status','UNKNOWN'))
def assessment(case,year):
 review=ROOT/'supplementary_materials/reviews'
 if case=='Base':
  p=(review/f'base_acceptance_relative_v1_20261012/assessments/{year}' if year<2060 else review/'completed_acceptance_20261020/assessments/base2060')/'solution_qc_relative_v1.json'
 elif case=='B':p=(review/'completed_results_20261027/B2030/assessment' if year==2030 else HERE/f'B{year}/assessment')/'solution_qc_relative_v1.json'
 elif case=='Case3':p=(review/'completed_acceptance_20261020/assessments/case3_2030' if year==2030 else review/'completed_results_20261027/case3_2040/assessment')/'solution_qc_relative_v1.json'
 else:p=review/'case3_2030_launch_20261014/nocredit_results_20261026/assessment/solution_qc_relative_v1.json'
 return p
def main():
 delivery=js(DELIVERY/'delivery_manifest.json')
 for x in delivery['files']:
  p=DELIVERY/x['path'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
 evidence=js(DELIVERY/'source_verification.json');inventory=js(HERE/'T550_inventory_20261028.json');summaries=js(DELIVERY/'analysis/run_summaries.json')
 snapshots=sorted(HERE.glob('cloud_status_*.json'));snapshot=js(snapshots[-1]);active={r['release']:r for r in snapshot['active_jobs']}
 # Match existing production evidence by content SHA; short-window solves do not match.
 tracked_paths=subprocess.check_output(['rg','--files','supplementary_materials/reviews','-g','solve_report.json','-g','*__solve_report.json'],cwd=ROOT,text=True).splitlines()
 local_by_hash={}
 for name in tracked_paths:
  p=ROOT/name;local_by_hash.setdefault(sha(p),[]).append(p)
 catalog=[];locations=[]
 for s in summaries:
  case,year,release=s['case'],s['year'],s['release'];version=release.split('_')[-1]
  sources=local_by_hash.get(evidence[release]['files']['solve_report.json']['sha256'],[])
  compact=DELIVERY/'cases'/case/str(year)/release
  if compact.exists():sources.insert(0,compact/'small_results/solve_report.json')
  ap=assessment(case,year)
  rec=dict(case=case,year=year,version=version,release=release,kind='COMPLETED_PRODUCTION',solver_status=s['solver_status'],acceptance_status=status(ap),acceptance_path=str(ap.relative_to(ROOT)) if ap.exists() else None,backup_status=inventory['backups'][release]['status'],remote_directory='/home/zz2/National_model_server/cloud_backup/'+release,source_result_manifest_sha256=evidence[release]['source_result_manifest_sha256'],local_evidence=[str(p.relative_to(ROOT)) for p in sources],iterations=s['iterations'])
  catalog.append(rec)
 for release,r in active.items():
  case='C' if 'lateentry' in release else 'Case3';catalog.append(dict(case=case,year=2050,version=release.split('_')[-1],release=release,kind='RUNNING_PRODUCTION',solver_status=r['state'],acceptance_status='NOT_FINISHED',backup_status='NOT_TERMINAL',job_id=r['job_id'],remote_directory='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+release,local_evidence=[str(snapshots[-1].relative_to(ROOT))]))
 for release,b in inventory['backups'].items():
  if b.get('result_manifest_sha256'):continue
  year=2030 if '_2030_' in release else 2060
  catalog.append(dict(case='B',year=year,version=release.split('_')[-1],release=release,kind='FAILED_ATTEMPT',solver_status='FAILED',acceptance_status='NO_SOLUTION',backup_status=b['status'],remote_directory='/home/zz2/National_model_server/cloud_backup/'+release,local_evidence=[str((HERE/'B2060_v1_failure_backup.json' if year==2060 else HERE.parent/'base_frozen_B_20261026/startup_failure_backup.json').relative_to(ROOT))]))
 catalog.sort(key=lambda x:(x['case'],x['year'],x['release']))
 for rec in catalog:
  card=DEST/'by_case'/rec['case']/str(rec['year'])/rec['release']/'README.md';card.parent.mkdir(parents=True,exist_ok=True);rec['case_card']=str(card.relative_to(ROOT))
  text=f"# {rec['case']} {rec['year']} · {rec['version']}\n\n类型：{rec['kind']}；求解：{rec['solver_status']}；验收：{rec['acceptance_status']}；备份：{rec['backup_status']}。\n\n完整运行身份：`{rec['release']}`。\n\n远端目录：`{rec['remote_directory']}`。\n\n## 本机入口\n\n"
  for n in rec['local_evidence']:text+='- '+link(n,ROOT/n)+'\n'
  if rec.get('acceptance_path'):text+='- '+link('独立验收 JSON',ROOT/rec['acceptance_path'])+'\n'
  text+='\n'+link('统一目录',DEST/'README.md')+'。正式解、候选筛选解和失败记录的身份保持原样；不要把调试短窗当成全年结果。\n'
  card.write_text(text,encoding='utf-8')
  for n in rec['local_evidence']:
   parent=(ROOT/n).parent;files=[p for p in parent.rglob('*') if p.is_file() and not p.is_symlink()]
   large=sorted(files,key=lambda p:p.stat().st_size,reverse=True)[:5]
   locations.append(dict(case=rec['case'],year=rec['year'],release=rec['release'],directory=str(parent.relative_to(ROOT)),files=len(files),bytes=sum(p.stat().st_size for p in files),largest_files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size) for p in large],basis='Matching original solve-report SHA, or explicit launch/failure receipt; directory may contain additional historical evidence'))
 dump(DEST/'case_catalog.json',dict(as_of_utc=snapshot['utc'],cases=catalog,organization='Index only: originals were not moved, renamed, overwritten or deleted',scientific_analysis_location='/home/zz2/National_model_server/cloud_backup/_analysis/20261028_compact_case_results_v1'))
 dump(DEST/'local_storage_inventory.json',locations)
 with (DEST/'case_catalog.csv').open('w',newline='',encoding='utf-8-sig') as f:
  fields=['case','year','version','kind','solver_status','acceptance_status','backup_status','release','remote_directory','case_card'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(catalog)
 readme='# 求解案例统一入口\n\n这里按情景 → 年份 → 完整运行版本索引案例。研究计算和大文件保存在 T550；本机保存可核验的小结果和导航。原有路径保持不变，不删除、移动或改写历史证据。\n\n'
 readme+='当前索引：11个已解生产案例、2个运行中案例、2个已备份失败尝试。未列入的旧诊断仍在原 reviews 目录，不表示被删除或已验收。\n\n|情景|年份|版本|类别|验收|备份|入口|\n|---|---|---|---|---|---|---|\n'
 for x in catalog:readme+='|'+ '|'.join([x['case'],str(x['year']),x['version'],x['kind'],x['acceptance_status'],x['backup_status'],link('打开',ROOT/x['case_card'])])+'|\n'
 readme+='\n## 初步分析（在 T550 计算）\n\n'
 for n,label in [('run_summary.csv','全年求解与成本汇总'),('B_vs_Base_cost_interval.csv','B相对Base的工程对偶节省区间'),('national_capacity.csv','全国分技术装机'),('national_generation.csv','全国分技术发电'),('cost_components.csv','分项成本'),('flexible_contracts.csv','柔性签约与移峰汇总')]:readme+='- '+link(label,DELIVERY/'analysis'/n)+'\n'
 readme+='\n'+link('结果解读与口径',DEST/'PRELIMINARY_FINDINGS_ZH.md')+'；'+link('来源与SHA',DELIVERY/'source_verification.json')+'；'+link('交付验证',DEST/'delivery_receipt_20261028.json')+'；'+link('本机存放清单',DEST/'local_storage_inventory.json')+'。\n\n## 存放规则\n\n- `by_case/`：情景、年份和完整release的导航卡。v1/v2是运行包版本，不等同模型V9/v9_a12。\n- `deliveries/20261028_t550_v1/`：本轮小结果，每文件≤1MiB；无逐时数组、BarX/BarPi、原MPS。\n- `_packages/`：约0.61MB传输包，保留用于复核；没有把大原件复制到本机。\n- 大原件和明细按 `remote_only_files.json` 定位T550。以后按需在T550汇总，再取小结果；不默认执行旧的≤32MiB全量小文件收集。\n- 原 `supplementary_materials/reviews/` 含发布门禁、短窗诊断、失败保全与历史快照，是溯源档案；通过此目录查找，无需搬动。\n'
 (DEST/'README.md').write_text(readme,encoding='utf-8')
 (DEST/'.gitignore').write_text('/_packages/\n/deliveries/\n',encoding='utf-8')
 print(json.dumps(dict(cases=len(catalog),cards=len(list((DEST/'by_case').rglob('README.md'))),originals_moved=0,originals_deleted=0),ensure_ascii=False))
if __name__=='__main__':main()
