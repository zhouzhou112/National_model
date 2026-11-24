"""Record one validated batch in the handoff; no remote operations."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess
from finalize_cases import RET,HERE,finalize
ROOT=HERE.parents[2]
B1T4=['case3_2040','c2050','nocredit_2030','b2030']
B1T9=['base2030','base2040','base2060','case3_2030','b2030']
ALL=['base2030','base2040','base2050','base2060','case3_2030','case3_2040','c2050','nocredit_2030','b2030','b2040','b2050','b2060']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(batch):
 cases=sorted(set(B1T4+B1T9)) if batch==1 else ALL
 for c in cases:finalize(c)
 checks={};files={}
 for c in cases:
  s=json.loads((RET/c/'summary.json').read_text(encoding='utf-8'));needed=[]
  if batch==1:
   if c in B1T4:
    assert s['T4']=='COMPLETE' and s['T4_checks']['annual_rows']==1134
    needed+=['annual_row_duals.csv','metadata/t4_price_checks.json','metadata/row_order_verification.json']
   if c in B1T9:
    assert s['T9']=='COMPLETE';needed+=['inertia_binding_by_province.csv','inertia_binding_by_hour_month.csv','inertia_slack_dual_joint_distribution.csv','inertia_online_startup_by_technology.csv','metadata/t9_summary.json']
  elif batch==2:
   assert s['T9']=='COMPLETE'
   if c in ['b2040','b2050','b2060']:assert s['T1']=='COMPLETE' and s['T4']=='COMPLETE'
   if c not in ['base2030','base2040','base2050','base2060']:
    assert s['T6']=='COMPLETE';needed+=['credit_realization_by_province_service.csv','credit_realization_national_service.csv','metadata/metrics_summary.json']
   if c in ['b2040','b2050','b2060']:needed+=['annual_row_duals.csv','metadata/t4_price_checks.json']
  else:
   if c!='nocredit_2030':assert s['T8']=='PASS_POSTHOC_CO2_ALLOCATION';needed+=['firm_revenue_by_province_technology.csv','metadata/revenue_summary.json']
   if c in ['case3_2030','case3_2040']:
    assert s['T2'].startswith('COMPLETE') and s['T7']=='COMPLETE';needed+=['rc_screen/vre_site_reduced_costs.csv','rc_screen/capacity_column_reduced_costs.csv','typical_day_'+c+'.csv']
   if c in ['case3_2040','c2050']:assert s['T3']=='COMPLETE';needed+=['corridor_duals.csv','corridor_duals_monthly.csv']
  for n in needed:files[c+'/'+n]={'sha256':sha(RET/c/n),'bytes':(RET/c/n).stat().st_size}
  checks[c]={k:s.get(k) for k in ['T1','T2','T3','T4','T6','T7','T8','T9']}
 utc=datetime.datetime.now(datetime.timezone.utc).isoformat();commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
 result=dict(batch=batch,status='PASS',utc=utc,git_baseline=commit,return_root=str(RET),cases=checks,files=files,model_changed=False,solver_started=False)
 dest=HERE/f'batch{batch}_receipt.json';assert not dest.exists();dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 desc={1:'第一批四案例T4与五案例T9已逐案例回传；1134年度行齐全、原始行序摘要一致、31省注入/需求配对残差已披露。',2:'第二批B2040/2050/2060的T1/T4、其余T9及全部八柔性案例T6已回传；服务偏差与总负荷偏差闭合，全国同步窗按逐小时全国合计再求均值/最小值。',3:'第三批11案例T8、两案例T3/T7/T2完成（A2030既有T2重新核SHA复用）。T8按作者批准同省全部捕集来源含DAC占比分摊共同CO2费用，并保留未分摊收益及共同费用；现实可结算收入无制度证据，保留NOT_DEFINED，不把影子收入称为结算。'}[batch]
 snapshot=f'- **2026-11-05 T550主线取数第{batch}批完成。** {desc}回传根为上级 `claude_workspace/analysis/base_dual_diagnosis_20261020/02_server_returns/`；逐文件SHA及每文件30MB/每案例100MB检查通过。证据 `supplementary_materials/reviews/t550_flex_analysis_20261104/batch{batch}_receipt.json`，报告同目录 `REVIEW_ZH.md`。不改运行包、不求解、不建监听。'
 history=f'\n\n## 2026-11-05 T550主线取数第{batch}批完成\n\n{desc}\n\n- 时间：{utc}；Git基线 `{commit}`。只读备份输入，输出写独立analysis目录；原始MPS/BarPi/逐时数组未回传。\n- 命令：`dispatch.py t1|launch|collect <case>`、`collect_t4_checks.py <case>`、`t9_transfer.py`、`metrics_dispatch.py`、`finalize_cases.py`、`record_batch.py {batch}`，脚本均在本review。\n- 验证：输入SHA对result/backup manifest、MPS行序digest、派生表自检、双端传输SHA；批次收据SHA `{sha(dest)}`。完整文件/案例/任务清单见收据。\n- 输出：`{RET.as_posix()}`；本轮前summary/transfer/sha已旁置保留。\n- 边界：物理绑定率与正对偶份额分开；连续RUC启停是GW，不是机组次数；价格为模型规划指标。\n- 下一步：'+('继续后续批次与标准导出验收。' if batch<3 else '完成源码与交接Git同步；作者用精确年度行对偶重跑2040/2050价格接受者，后续新终态仍按既定备份验收规则。')+'\n'
 hp=ROOT/'CODEX_HANDOFF.md';text=hp.read_text(encoding='utf-8-sig');assert snapshot not in text;text=text.replace('## Current validated snapshot\n','## Current validated snapshot\n\n'+snapshot+'\n',1);hp.write_text(text+history,encoding='utf-8')
 records=HERE/'handoff_records.json';old=json.loads(records.read_text(encoding='utf-8')) if records.exists() else [];old.append(dict(snapshot=snapshot,history=history));records.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(batch=batch,status='PASS',files=len(files),receipt_sha256=sha(dest))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch',type=int,choices=[1,2,3]);record(p.parse_args().batch)
