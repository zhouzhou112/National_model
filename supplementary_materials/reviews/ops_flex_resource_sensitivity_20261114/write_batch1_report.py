"""Format the first-batch report from SHA-verified T550 analyses and receipts."""
from pathlib import Path
import datetime,hashlib,json
import pandas as pd
HERE=Path(__file__).resolve().parent;OUT=HERE/'acceptance_batch1_20261115';ROOT=HERE.parents[2]
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
def md_table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])+'\n'
def main():
 cases=read('case_summaries.json');net=read('reference_and_network_summary.json');names=['OPS-Open','OPS-Conservative','D1-C5'];receipts={n:read(n+'_return_receipt.json') for n in names}
 wall={'OPS-Open':'15:55:05','OPS-Conservative':'17:12:19','D1-C5':'14:53:19'};jobs={'OPS-Open':'5584373','OPS-Conservative':'5584377','D1-C5':'5584390'}
 snap=json.loads((HERE/'snapshots/20261115T194003Z/snapshot.json').read_text());keys={'OPS-Open':'ops_open_2050','OPS-Conservative':'ops_conservative_2050','D1-C5':'D1_2050'}
 records=[];service_rows=[];comparisons=[];costs={};summaries=[]
 for name in names:
  a=cases[name]['acceptance'];s=cases[name]['analysis'];source=snap['cases'][keys[name]]['output_8760/solve_report.json'];assert a['status']==s['status']=='PASS' and receipts[name]['all_bytes_sha_match']
  r=dict(case=name,planning_year=2050,role='DIAGNOSTIC_ONLY' if name=='D1-C5' else 'OPS_RESOURCE_SENSITIVITY',job_id=jobs[name],acceptance='PASS',wall_time=wall[name],iterations=source['iteration_counts']['barrier'],peak_process_tree_rss_gib=source['runtime_memory']['peak_process_tree_rss_gib'],P_million_cny=a['P_million_cny'],D_million_cny=a['D_million_cny'],primal_dual_gap_million_cny=a['primal_dual_gap_million_cny'],vre_curtailment_gwh=s['annual']['vre_curtailment_gwh'],storage_charge_gwh=s['annual']['storage_charge_gwh'],storage_discharge_gwh=s['annual']['storage_discharge_gwh'],startup_capacity_sum_gw=s['startup_capacity_sum_gw'],shutdown_capacity_sum_gw=s['shutdown_capacity_sum_gw'],startup_shutdown_cost_million_cny=s['startup_shutdown_cost_million_cny'],actual_v2g_discharge_gwh=s['actual_v2g_discharge_gwh'])
  for c in s['comparisons']:
   comparisons.append(dict(planning_year=2050,**c))
   if c['reference']=='REF':r.update({k:c[k] for k in ['point_saving_yi_cny','lower_saving_yi_cny','upper_saving_yi_cny']})
  for v in s['services']:
   service_rows.append(dict(case=name,planning_year=2050,**v))
   for k in ['contract_gw','upper_gw','contract_share_of_upper','down_regulation_gwh','equivalent_down_hours']:r[v['service']+'_'+k]=v[k]
  records.append(r)
  directory=Path(receipts[name]['local_directory']);costs[name]=pd.read_csv(directory/'acceptance_resource_batch1_20261115/analysis/cost_saving_by_component.csv')
 pd.DataFrame(records).to_csv(OUT/'batch_case_summary.csv',index=False);pd.DataFrame(service_rows).to_csv(OUT/'batch_service_summary.csv',index=False);pd.DataFrame(comparisons).to_csv(OUT/'batch_cost_comparisons.csv',index=False)
 report=['# 柔性资源量敏感性：第一批验收与结果报告','',f"生成时间：{datetime.datetime.now(datetime.timezone.utc).isoformat()}（英国冬令时/UTC）。金额为2025年不变价；1亿元=100 million CNY。",'',
 '三个全年案例均完成、在T550当前评估器下验收PASS，并已取回验收包和适用结果小文件；LATE-Open五轮测试已按计划终止并完整备份。第一批交付完成。后续生产LATE-Open已获作者11-15单独授权，不是本批测试的续跑；本报告不授权其他第二/三批作业。','',
 '## 1. 终态、保全与验收','',
 md_table(['案例','Job','终态','Barrier轮数','Slurm总耗时','进程树峰GiB','验收'],[[r['case'],r['job_id'],'OPTIMAL / 0:0',r['iterations'],r['wall_time'],f"{r['peak_process_tree_rss_gib']:.3f}",'PASS'] for r in records]+[['LATE-Open五轮测试','5584392','COMPLETED / 预定回调终止',5,'04:36:18','649.791','测试符合计划；无科学解验收']]),
 '三案按relative_v1当前实现重新计算，包含逐省峰荷归一功率平衡、年度化石未减排排放量分母的Mt检查、双向流额外损耗及扩展物理检查。全部原始文件bytes/SHA复核通过，保全COMPLETE，冻结容量检查与全年资源结构审计PASS。无风光候选筛选，不要求筛选证书。水库逐站判定按作者规则暂缓，最大残差、站点与库容仍披露。验收是质量标签，不自动决定作者采用规划状态。','',
 '原严格绝对口径的HARD_FAIL没有删除：三案均含双向流和成本重构项，保守案另有水库项；这些在当前作者口径下通过或按规则暂缓。未放松现行判据，未修改任何原输出。','',
 md_table(['案例','P：亿元/年','D：亿元/年','P−D：亿元/年'],[[r['case'],f"{r['P_million_cny']/100:.6f}",f"{r['D_million_cny']/100:.6f}",f"{r['primal_dual_gap_million_cny']/100:.6f}"] for r in records]),
 '## 2. 相对REF与中央OPS的成本比较','',
 '正数表示参照案成本较高。工程区间按作者规则 `[D_ref − P_case, P_ref − D_case]`，三案均无筛选项B。它不是统计置信区间或市场结算金额。REF和中央OPS都来自原验收备份，来源SHA在各案analysis_summary.json登记。','',
 md_table(['案例','相对REF点差：亿元/年','工程区间','相对中央OPS点差：亿元/年','工程区间'],[[name,*[v for ref in ['REF','OPS-Central'] for c in cases[name]['analysis']['comparisons'] if c['reference']==ref for v in [f"{c['point_saving_yi_cny']:.2f}",f"[{c['lower_saving_yi_cny']:.2f}, {c['upper_saving_yi_cny']:.2f}]"]]] for name in names]),
 '成本排序为Open < 中央OPS < Conservative < REF。D1只作放开省内城市链路的诊断，不作为资源情景加入主排序。','',
 '## 3. 成本节省来自哪里','',
 '下表只列可相加的一级成本项；运行费用已是包含新增柔性资源费用的净额。详细子项在cost_saving_by_component.csv，不能把annual_operation与其operating_*明细再次相加。','',
 md_table(['相对REF节省：亿元/年']+names,[[label]+[f"{float(costs[n].loc[(costs[n].reference=='REF')&(costs[n].cost_component==key),'saving_million_cny'].iloc[0])/100:.2f}" for n in names] for key,label in [('annual_operation','运行费用净节省'),('ccs_capture','CO2捕集费用节省'),('co2_transport_injection','CO2运输/封存费用节省'),('load_center_intra_transmission_investment','省内链路投资费用节省（负值为新增成本）')]]),
 'Open运行费用内，燃料和启停成本分别减少413.72、281.42亿元/年，同时增加柔性接入/签约费用144.71亿元和V1G移时调用费用90.75亿元等；这些已计入514.91亿元运行净节省。发电、储能和省际通道容量固定，不能把这里的节省解释为机组投资替代。固定定义仍为原B的“Base值加最小静态闭合”，未重新调整闭合。','',
 '## 4. 服务签约、上限占比与调用','',
 md_table(['案例','服务','签约GW','上限GW','占上限','年下调TWh','等效下调小时'],[[r['case'],r['service'],f"{r['contract_gw']:.3f}",f"{r['upper_gw']:.3f}",f"{100*r['contract_share_of_upper']:.2f}%",f"{r['down_regulation_gwh']/1000:.3f}",f"{r['equivalent_down_hours']:.1f}"] for r in service_rows]),
 '调用按每个服务池相对自身基线的逐小时净负荷偏移计算，先逐省逐服务取下调正部再求和；不是全国同步净额。等效小时=下调GWh/签约GW。V1G/V2G按互斥池基线拆分，四服务偏移之和与有效负荷变化逐小时闭合≤1e-6GW。V2G实际放电另列，不再叠加到已含放电的净服务下调量；V2G是共享充电连接中的嵌套服务，四类合同GW不能直接当作独立设备总规模。','',
 md_table(['案例','实际V2G放电TWh','储能充电TWh','储能放电TWh','风光弃电TWh','启停成本亿元/年'],[[r['case'],f"{r['actual_v2g_discharge_gwh']/1000:.3f}",f"{r['storage_charge_gwh']/1000:.3f}",f"{r['storage_discharge_gwh']/1000:.3f}",f"{r['vre_curtailment_gwh']/1000:.3f}",f"{r['startup_shutdown_cost_million_cny']/100:.2f}"] for r in records]),
 '与“更多资源会让所有服务签约同时增加”的直觉不同：Open智能充电签约465.184GW，几乎用满上限；V2G仅1.313GW（上限的0.65%），低于中央OPS的19.125GW和Conservative的16.124GW。Open供暖/制冷上限利用率也仅15.27%/8.24%。这是资源组合共同变化的结果；智能充电与V2G替代是解释线索，不能据此宣称已完成单因素因果识别。开放全国V2G上限1000GW保留为约束行，其实际松弛998.687GW，满足不绑定门禁。','',
 '启停原变量是连续GW容量，本报告与小表保留启动/停机容量累加量，并给出逐省×技术的等效整容量启停次数（累加启停GW/容量GW），不伪称离散机组启动次数。启停成本用原输入参数SHA核验后重构，与原cost_components核对通过。','',
 '## 5. D1/C5省内网络诊断','',
 md_table(['指标','中央OPS','D1/C5'],[[label,f"{net['OPS-Central'][key]/scale:.3f}",f"{net['D1-C5'][key]/scale:.3f}"] for key,label,scale in [('intra_new_sum_gw','省内链路新建量GW',1),('vre_curtailment_gwh','风光弃电TWh',1000),('storage_charge_gwh','储能充电TWh',1000)]]+[['年容量约束对偶均值元/MWh',f"{net['OPS-Central']['intra_annual_capacity_value_cny_per_mwh']['mean']:.3f}",f"{net['D1-C5']['intra_annual_capacity_value_cny_per_mwh']['mean']:.3f}"]]),
 '只放开642条省内城市链路后，链路新建量增加20.633GW，弃风光减少49.411TWh（约7.87%），储能充电增加30.140TWh；成本比中央OPS再低20.75亿元/年，工程区间[2.24,23.11]。年容量约束的642行有符号容量价值均值由51.09降至2.94元/MWh。结合其他投资容量身份检查，这支持省内网络限制消纳的诊断解释；不能据此把D1推广为全源网荷储联合优化。对偶非零本身不等于物理绑定，未用对偶阈值代替原始松弛验证。','',
 'Open资源下的风光弃电仍为627.603TWh，较中央OPS仅少0.205TWh，但运行成本显著下降；增加柔性资源与放开省内网络带来的效果不同，需要分别表述。','',
 '## 6. LATE-Open排序和五轮测试','',
 'Job5584392，44线程；排序3915.91秒（65.27分钟），DenseCols=7872，FactorNZ=2.233×10^10，FactorOps=7.483×10^14；实际自由站点4481，下界固定28846、上界固定3359。5轮耗时684/511/547/510/545秒，均值559.4秒（9.32分钟）。总墙钟4:36:18，进程树峰649.791GiB，Slurm峰643.327GiB。回调第5轮确实触发，Gurobi状态11为预定中断，不是科学解收敛。','',
 '沿用C2050/Case32050历史496/551轮并考虑后期耗时增幅，完整受限求解条件估计3.57–4.03天；按求解器粗估800秒/轮则4.75–5.26天，保守端超过5天提示线。已向作者披露，作者随后单独授权生产Job5587177；仍沿用经验证的44线程。测试比较同时改变自由集、资源情景和线程数，不是纯线程消融，也不保证五天内收敛。','',
 '## 7. 备份、恢复项及本地交付','',
 '三案备份于2026-11-15 20:12:03UTC全部COMPLETE：335文件16,565,040,777bytes，T1/T2/T3逐文件bytes/SHA通过且源身份未变；LATE五轮测试另42件4,191,604,666bytes，先前已COMPLETE。按作者新规则保留至少5%磁盘余量，本批完成后实际仍约29.75%。未重启备份或求解。','',
 '本轮发现并补齐的导出缺项：三案原annual_row_duals.csv因SavedDual缺ConstrName未生成。已从各自原MPS ROWS与自身BarPi只读恢复1134个年度核算行，原始全部行的数量、顺序与sense哈希匹配；新文件位于acceptance_resource_batch1_20261115/annual_rows/，不覆盖output_8760。完整负荷侧电价按原生产公式加回年度需求、备用与惯量项，保留负值，不以“没有负价”作为正确性门槛；工程对偶不等于市场结算。该导出接口缺陷留待单独新版本修复，不改正在运行的LATE冻结包。','',
 md_table(['案例','本地文件数','总MB','单文件最大MB'],[[n,receipts[n]['files'],f"{receipts[n]['bytes']/1e6:.2f}",f"{receipts[n]['maximum_file_bytes']/1e6:.2f}"] for n in names]),
 f"合计{sum(r['files'] for r in receipts.values())}件，{sum(r['bytes'] for r in receipts.values()):,}bytes（{sum(r['bytes'] for r in receipts.values())/1e6:.2f}MB）。三案均按Case3 2040清单取回72项适用原文件；candidate_selection.csv因无筛选不适用，不伪造第73项。另含本案冻结/结构审计、验收、恢复对偶及分析表。保留原清单允许的小型NPZ；原MPS、BarX/BarPi、热电/水库/柔性大型调度NPZ和省级逐时大平衡表均留T550。每个包delivery_manifest.json及本地回读校验记录对应逐文件SHA。",'',
 '核心派生表：batch_case_summary.csv、batch_service_summary.csv、batch_cost_comparisons.csv；各案analysis目录含全国及广东/江苏/山东/四川/内蒙古8760小时调度、31省8760小时负荷侧边际电价、分省技术发电/风光弃电、启停/成本、储能操作和完整成本分项。价格与调度只返回压缩小表，分析在T550完成。','',
 '本地目录：']
 for n,r in receipts.items():report.append(f"- {n}：`{r['local_directory']}`")
 report+=['','回传期间转发曾中断：已完成的两案保持原样，重连后只补传D1，未重跑验收/备份。','',
 '## 8. 放行边界','',
 '本报告完成第一批三解一测试的收尾。除作者已单独授权的LATE-Open2050生产作业外，OPS-Open2030/2040/2060及第三批均未提交；仍等待作者/Claude审阅与明确确认。没有后台监听，没有修改旧release或在线LaTeX/SI模块。']
 path=OUT/'BATCH1_REPORT_ZH.md';assert not path.exists();path.write_text('\n'.join(report)+'\n',encoding='utf-8')
 receipt=dict(status='PASS',cases={n:r for n,r in receipts.items()},all_three_acceptance_pass=True,total_files=sum(r['files'] for r in receipts.values()),total_bytes=sum(r['bytes'] for r in receipts.values()),report_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 (OUT/'batch_delivery_summary.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(report=str(path),total_files=receipt['total_files'],total_bytes=receipt['total_bytes'])))
if __name__=='__main__':main()
