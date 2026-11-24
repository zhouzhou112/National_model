"""Format the accepted T550 results and latest live LATE snapshot; no raw-array analysis."""
from pathlib import Path
import datetime,hashlib,json
import pandas as pd
HERE=Path(__file__).resolve().parent;OUT=HERE/'acceptance_batch2_20261116'
def load(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def tab(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
def main():
 summaries=load('case_summaries.json');four=load('four_year_summary.json');late=load('late_progress_final.json');terminal=json.loads((HERE/'batch2_completed_backup_20261116/terminal_summary.json').read_text());names=['OPS-Open-2030','OPS-Open-2040','OPS-Open-2060'];receipts={n:load(n+'_return_receipt.json') for n in names};rows=[]
 for name in names:
  r=summaries[name];a=r['acceptance'];s=r['analysis'];y=a['planning_year'];t=terminal[f'ops_open_{y}'];assert a['status']==s['status']=='PASS' and receipts[name]['all_bytes_sha_match'];rows.append(dict(year=y,case=name,job=t['job_id'],iterations=t['barrier_iterations'],wall=t['accounting'].split('|')[3],peak=t['memory']['peak_process_tree_rss_gib'],P=a['P_million_cny'],D=a['D_million_cny'],gap=a['primal_dual_gap_million_cny'],files=receipts[name]['files'],bytes=receipts[name]['bytes']))
 pd.DataFrame(rows).to_csv(OUT/'accepted_OPS_cases.csv',index=False)
 service=[x for x in four['services'] if x['planning_year'] in [2030,2040,2060]]
 report=['# OPS-Open 2030、2040、2060：验收与结果交付','',f"生成：{datetime.datetime.now(datetime.timezone.utc).isoformat()}。时间采用英国冬令时/UTC；金额为2025年不变价，1亿元=100 million CNY。",'',
 '三案已在T550备份上完成当前relative_v1重评，均PASS；各自年度核算行对偶已恢复，验收包和适用结果小文件已回本机并校验。LATE-Open2050仍运行，因此这是第二批三个OPS案例的阶段交付，不是整个第二批终态报告；不触发第三批提交。','',
 '## 1. 备份、终态与验收','',
 '合并备份20261116_resource_batch2_ops_completed于2026-11-16 21:19:45UTC COMPLETE，333文件16,567,230,513bytes，T1/T2/T3全部VERIFIED，源身份未变，原PID2385473已退出。验收前在T550重新逐文件读取全部备份bytes/SHA。5%余量规则沿用，原始输出/失败记录不修改。','',
 tab(['年份','Job','终态','轮数','总耗时','进程树峰GiB','当前relative_v1'],[[r['year'],r['job'],'OPTIMAL / 0:0',r['iterations'],r['wall'],f"{r['peak']:.3f}",'PASS'] for r in rows]),
 '三案保全COMPLETE、固定容量身份和全年资源结构检查PASS。原严格HARD_FAIL仍保留，失败项均为双向流/成本重构；按作者相对口径通过，水库逐站判定按原决定暂缓并披露最大残差和活动库容。三案均无候选筛选，不需要筛选证书。验收是质量标签，不自动把某案状态作为另一OPS年份的上游。','',
 tab(['年份','P：亿元/年','D：亿元/年','P−D：亿元/年'],[[r['year'],f"{r['P']/100:.6f}",f"{r['D']/100:.6f}",f"{r['gap']/100:.6f}"] for r in rows]),
 '2030的10.95890410958904 Mt额度例外仅用于24h工程门禁和全部对照；本次8760h生产年度上限仍为4000 Mt，未放松冻结容量或求解容差。2040/2060继续使用对应B原冻结源、上游和原静态闭合。','',
 '## 2. 成本点差与工程区间','',
 '各年均与同年已验收REF、中央OPS比较。正数为节省，区间按作者规则 `[D_ref−P_case, P_ref−D_case]`，无筛选B项；这是工程对偶区间，不是统计置信区间或市场结算。2050沿用第一批已验收且SHA匹配的结果，未重新计算或求解。','',
 tab(['年份','相对REF点差：亿元/年','工程区间','相对中央OPS再节省：亿元/年','工程区间'],[[r['planning_year'],f"{r['ref_point_saving_yi_cny']:.2f}",f"[{r['ref_lower_saving_yi_cny']:.2f}, {r['ref_upper_saving_yi_cny']:.2f}]",f"{r['central_ops_point_saving_yi_cny']:.2f}",f"[{r['central_ops_lower_saving_yi_cny']:.2f}, {r['central_ops_upper_saving_yi_cny']:.2f}]"] for r in four['rows']]),
 '开放资源在三个新增年份均降低固定机组体系内的运行成本，工程区间均为正。2050点差略高于2060，但二者区间重叠，不能仅凭点差判定年度价值排序稳健。发电、储能和省际通道固定；这些结果不能解释为机组投资替代收益，也不能直接与资源量不同的PLAN/LATE比较框架份额。','',
 '## 3. 服务签约与调用','',
 tab(['年份','服务','签约GW','上限GW','上限利用率','下调TWh','等效下调小时'],[[r['planning_year'],r['service'],f"{r['contract_gw']:.3f}",f"{r['upper_gw']:.3f}",f"{100*r['contract_share_of_upper']:.2f}%",f"{r['down_regulation_gwh']/1000:.3f}",f"{r['equivalent_down_hours']:.1f}"] for r in service]),
 '智能充电签约占上限分别为99.54%、100.00%、97.78%；V2G仅约0.556、0.638、1.199GW，上限利用率均不足1%。这与第一批Open2050的1.313GW低V2G签约相呼应，但资源组合多参数一起变化，不能据此宣称完成单因素替代因果识别。V2G全国1000GW约束保留且不绑定。','',
 '调用采用各服务池相对自身基线的逐小时净负荷偏移，先逐省逐服务取下调正部再加总，非全国同步净额；等效小时=下调GWh/签约GW。V1G/V2G用互斥池基线拆分，四服务偏移与有效负荷变化逐小时闭合≤1e-6GW。V2G合同嵌套在共享充电连接中，合同GW不能直接当作独立设备总规模；实际V2G放电另列，不能与已含放电的净服务下调重复相加。','',
 tab(['年份','实际V2G放电TWh','风光弃电TWh','储能充电TWh','储能放电TWh','启停成本亿元/年'],[[r['planning_year'],f"{r['v2g_discharge_gwh']/1000:.3f}",f"{r['vre_curtailment_gwh']/1000:.3f}",f"{r['storage_charge_gwh']/1000:.3f}",f"{r['storage_discharge_gwh']/1000:.3f}",f"{r['startup_shutdown_cost_million_cny']/100:.2f}"] for r in four['rows']]),
 '启停变量是连续GW容量，输出包含容量累加量、逐省×技术的等效整容量启停次数及成本，不伪称离散机组次数。启停成本用原参数SHA核验后重构；成本分项相加、储能总量、服务合同CSV/NPZ及调度分解均已核对。','',
 '## 4. 年度核算行对偶及完整负荷侧价格','',
 '原生产导出均记录SavedDual缺少ConstrName，原annual_row_duals.csv未生成。本轮对每案独立读取原MPS ROWS与自身BarPi，完整行数、名称、sense顺序摘要匹配后恢复1134条年度核算行；没有因不同案例索引相近而套用行定位。结果旁置于acceptance_resource_batch2_20261116/annual_rows/，原输出与原错误记录不改。','',
 '完整负荷侧边际价格按原生产公式：1000×(逐时平衡Pi + 年度有效需求Pi + 备用负荷系数×备用Pi + 惯量秒数×惯量Pi)。年度注入/需求对偶配对残差在analysis_summary.json披露。保留负价，不以“无负价”判正确；标为BARRIER_DUAL_ENGINEERING_GRADE，不能直接当成市场结算价格。','',
 '## 5. 本地交付','',
 tab(['案例','有效载荷文件数','总MB','最大单件MB'],[[n,receipts[n]['files'],f"{receipts[n]['bytes']/1e6:.2f}",f"{receipts[n]['maximum_file_bytes']/1e6:.2f}"] for n in names]),
 f"三案有效载荷合计{sum(r['files'] for r in receipts.values())}件、{sum(r['bytes'] for r in receipts.values()):,}bytes（{sum(r['bytes'] for r in receipts.values())/1e6:.2f}MB），另附传输清单和本报告。均沿用Case3 2040清单的72项适用原文件，candidate_selection.csv因无筛选不适用；再加冻结审计、验收、恢复对偶和分析。原MPS、BarX/BarPi、热电/水库/柔性大型调度NPZ留T550。保留原清单允许的小型NPZ，单件均≤32MiB。",'',
 '每案analysis目录含签约/占比/调用/等效小时、全国及广东/江苏/山东/四川/内蒙古8760调度、31省逐时价格、分省技术发电/风光弃电、启停/成本、储能操作和成本分项。四年概览CSV使用T550既有计算结果，仅2050引用第一批已验收件。', '']
 for n,r in receipts.items():report.append(f"- {n}：`{r['local_directory']}`")
 l=late['last'];d=late['drop_last10'];report+=['','回传2040时SSH握手曾中断，用户重连后以一次连接补传2040/2060，2030没有重复传输，未重跑备份或科学计算。','',
 '## 6. LATE-Open2050进展与后续边界','',
 f"截至{late['as_of_utc']}，云端仅Job5587177 RUNNING，已运行35小时23分，最新第{l['iteration']}轮。日志打印PInf={l['pinf']:.6g}、DInf={l['dinf']:.6g}、Compl={l['compl']:.6g}；近10轮PInf/Compl分别下降{100*d['pinf']:.1f}%/{100*d['compl']:.1f}%，DInf反弹{100*(-d['dinf']):.1f}%，仍在1e-7量级。平均{late['minutes_per_round']:.2f}分钟/轮，Slurm峰RSS约643.93GiB，stderr空、无终态。不能把低DInf或降幅当作已接近最优，也不把不同尺度callback残差混入表述。",'',
 'LATE仍需完成求解、全量备份、当前验收与本解自身双向定价证书，并按同法恢复年度行对偶。本次三个OPS阶段交付不代表整个第二批已结束。第三批仍等待作者明确确认；未启动新求解或后台监听，未修改运行中冻结包或SI/在线LaTeX。']
 path=OUT/'OPS_OPEN_2030_2040_2060_REPORT_ZH.md';assert not path.exists();path.write_text('\n'.join(report)+'\n',encoding='utf-8')
 receipt=dict(status='PASS',cases=receipts,all_three_acceptance_pass=True,total_files=sum(r['files'] for r in receipts.values()),total_bytes=sum(r['bytes'] for r in receipts.values()),report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),late_snapshot=late['as_of_utc'],whole_second_batch_complete=False)
 (OUT/'delivery_summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report=str(path),files=receipt['total_files'],bytes=receipt['total_bytes'])))
if __name__=='__main__':main()
