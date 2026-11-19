"""Format verified T550 summaries and transfer receipts; no raw-array analysis."""
from pathlib import Path
import datetime,json
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OUT=HERE/'completion_20261119'

def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
def interval(lo,hi):return f'[{lo:.3f}, {hi:.3f}]'

def main():
 cons=load(HERE/'acceptance_batch3_20261119/case_summaries.json');perf=load(HERE/'acceptance_batch3_20261119/terminal_performance.json');four=load(OUT/'OPS_resources_four_year_summary.json');comparison=load(OUT/'LATE_Open_vs_central.json')
 late_receipt=load(HERE/'acceptance_late_20261119/LATE-Open-2050_return_receipt.json');late=Path(late_receipt['local_directory'])/'acceptance_resource_late_20261119';a=load(late/'acceptance_record.json');analysis=load(late/'analysis/analysis_summary.json');row=a['row'];cert=a['certificate'];assert a['status']==analysis['status']=='PASS'
 receipts=[load(HERE/'acceptance_batch3_20261119'/f'OPS-Conservative-{y}_return_receipt.json') for y in (2030,2040,2060)]+[late_receipt];assert all(r['all_bytes_sha_match'] for r in receipts)
 rows=[]
 for y in (2030,2040,2060):
  t=perf[f'ops_conservative_{y}'];rows.append([f'OPS-Conservative {y}',t['iterations'],{2030:'11:16:20',2040:'16:32:15',2060:'16:11:04'}[y],f"{t['peak_process_tree_rss_gib']:.3f}",'PASS'])
 rows.append(['LATE-Open 2050',451,'3天17:50:42',f"{perf['late_open_2050']['peak_process_tree_rss_gib']:.3f}",'PASS（solver条件披露）'])
 total=sum(r['bytes'] for r in receipts);count=sum(r['files'] for r in receipts)
 report=['# 柔性资源量敏感性：四案验收、证书与结果交付','',f'生成时间：{datetime.datetime.now(datetime.timezone.utc).isoformat()}。金额均为2025年不变价；亿元=100 million CNY。','',
 '本轮四案均已完整备份、在T550完成只读验收与分析，年度核算行对偶恢复并通过原始完整行序核验，小文件已回本机且SHA匹配。云端本批作业全部结束。本报告完成第二批LATE-Open2050收尾和第三批三个OPS-Conservative的阶段交付；LATE-Open2060仍待作者明确确认，未提交。','',
 '## 1. 终态与备份','',table(['案例','轮数','总耗时','进程树峰GiB','当前relative_v1'],rows),'',
 '三项Conservative备份333件16,551,979,130bytes，11月18日19:03UTC COMPLETE；LATE备份104件5,550,464,171bytes，11月19日10:28UTC COMPLETE。均含全部原MPS、BarX/BarPi、状态、QC、日志及明确启动元数据，逐文件bytes/SHA和源身份闭合；不是包含全部输入环境的镜像。原严格标签和原输出完整保留。水库逐站检查按作者决定暂缓，残差照常披露。','',
 '## 2. LATE-Open2050独立行定位与双向定价','',
 f"最大违反索引53471702独立定位为`{row['name']}`，河北年度外送汇总等式；变量族为年度外送GWh与8760小时省际正向/交流反向GW流量。原MPS变量、约束名称和sense完整顺序摘要均与本解checkpoint一致。残差{row['residual_gwh']:.12g} GWh，年度量级{row['row_magnitude_gwh']:.9f} GWh，相对比例{row['relative_residual']:.9g}，容差`max(1e-3,1e-6×年度电量)`={row['tolerance_gwh']:.9f} GWh；在容差内。完整245281项行系数/BarX重构留T550，回传摘要含SHA与路径。",'',
 f"本解自身BarPi双向证书：**B={a['screening_B_million_cny']:.9f} million CNY（{a['screening_B_million_cny']/100:.6f}亿元），B/P={a['B_over_objective']:.9g}**；固定站点×技术组{cert['fixed_sites']}个，其中{cert['negative_fixed_sites']}组有正的潜在改进上界。上下界固定分别计算增加/减少方向，并保留相应接入线约束的解析关系；没有把参考解价格当作本解证书。逐组价格、负价组与上下界rc_ratio分布已回传。",'',
 f"P={a['P_million_cny']:.9f}、D={a['D_million_cny']:.9f}、P−D={a['primal_dual_gap_million_cny']:.9f} million CNY；B为原对偶差的{100*a['B_to_original_gap']:.4f}%。B/P≤1e-2，满足近优性条件。比较用途是否需要作者考虑重解：{'B/P>1e-4，须报告作者决定，不自动重解' if a['comparison_resolve_requires_author'] else 'B/P≤1e-4，不触发比较用途重解报告阈值'}。",'',
 f"验收使用的终态回调PInf={a['barrier_primal_infeasibility']:.12g}；日志打印PInf=0.00394，尺度不同，不能混作残差反弹。全部已执行物理相对检查、独立最大行容差、自身证书及终态范围满足作者11月6日规则，solver转为条件披露，新旁置记录PASS；原HARD_FAIL记录未改。原模型未求解第二次，固定集未放回。",'',
 '## 3. LATE成本比较','',
 '工程对偶区间不是统计置信区间或市场结算。对无筛选参考案用`[D_ref−P_target, P_ref−D_target+B_target]`；中央LATE也有筛选误差，比较时使用`[D_ref−B_ref−P_target, P_ref−D_target+B_target]`，不能漏掉参考案B。','',
 table(['参考案例','点差：亿元/年','工程区间'],[[r['reference'],f"{r['point_saving_yi_cny']:.3f}",interval(r['lower_saving_yi_cny'],r['upper_saving_yi_cny'])] for r in analysis['comparisons']]+[['LATE-Central2050',f"{comparison['point_saving_yi_cny']:.3f}",interval(comparison['lower_saving_yi_cny'],comparison['upper_saving_yi_cny'])]]),'',
 '与中央LATE的比较共享REF2040上游，但资源输入和受限集合不同，双方证书均保留；与OPS比较同时改变投资自由度，不能将差额全部归因于某一项柔性资源。','',
 '## 4. 四年OPS资源量对比','',
 '2050与全部Open结果复用此前已验收归档，逐项核身份；本轮只新增Conservative2030/2040/2060。各OPS年复用同年B冻结来源，不把某个OPS年份作为另一年的上游。','',
 table(['年份','资源情景','相对REF点差：亿元/年','工程区间','相对中央OPS点差'],[[r['year'],r['case'],f"{r['ref_point_saving_yi_cny']:.3f}",interval(r['ref_lower_saving_yi_cny'],r['ref_upper_saving_yi_cny']),f"{r['central_point_saving_yi_cny']:.3f}"] for r in four['rows']]),'',
 '保守情景相对REF仍有运行价值。2030保守与中央OPS的差异区间跨零；不因点差排序宣称严格优劣。机组、储能、省际网络固定，OPS结果不代表投资替代。成本分项、合同/上限利用率、等效调用小时、弃电、连续启停容量和储能充放电均见逐案analysis及四年CSV。','',
 '## 5. LATE服务签约与调用','',table(['服务','签约GW','上限GW','上限利用率','下调TWh','等效下调小时'],[[r['service'],f"{r['contract_gw']:.3f}",f"{r['upper_gw']:.3f}",f"{100*r['contract_share_of_upper']:.2f}%",f"{r['down_regulation_gwh']/1000:.3f}",f"{r['equivalent_down_hours']:.1f}" if r['equivalent_down_hours'] is not None else 'NA'] for r in analysis['services']]),'',
 'V1G/V2G基线池分开，实际V2G放电另报，不重复累加到服务下调；供暖/制冷存在预热预冷损耗，净用电变化保留。四年OPS全部服务签约、上限和调用见OPS_resources_four_year_services.csv。连续RUC启停按GW及等效次数披露，不解释为离散机组台次。','',
 '## 6. 本地交付与后续边界','',
 f"本轮共回传{count}个有效载荷小文件、{total:,}bytes（{total/1e6:.2f}MB），单件最大{max(r['maximum_file_bytes'] for r in receipts):,}bytes；每案≤200MiB。原MPS、BarX/BarPi、大型热电/水库/柔性数组、定价解析缓存和完整行系数留T550。验收JSON、摘要、完整方向价格CSV及分析小表双端SHA匹配。",'',
 '各案目录：`case_results/by_case/OPS-Conservative/{2030,2040,2060}/<release>/`与`case_results/by_case/LATE-Open/2050/<release>/`。每个包的delivery_manifest列出来源、大小和SHA。原73清单的candidate_selection.csv因本组无该筛选方式不适用，固定状态选择另以capacity_selection及audit披露。','',
 '原年度行导出缺项由每案独立MPS+BarPi旁置恢复1134行，不改冻结包，不裁负价。工程影子价标BARRIER_DUAL_ENGINEERING_GRADE。Conservative工具首次导入缺依赖、未读数据即退出；v2隔离初始化修正，失败日志保留，未改模型。','',
 '下一检查点：作者/Claude审阅本轮验收与区间，明确是否采纳LATE-Open2050、是否放行LATE-Open2060；后者尚未提交。本轮没有自动重解、完整联合优化替代求解、后台监听或运行包修改。']
 (OUT/'RESOURCE_SENSITIVITY_ACCEPTANCE_REPORT_ZH.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
 (OUT/'delivery_summary.json').write_text(json.dumps(dict(status='PASS',files=count,bytes=total,cases=receipts,late_B_million_cny=a['screening_B_million_cny'],late_B_over_objective=a['B_over_objective'],late_2060_submitted=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(status='PASS',report=str(OUT/'RESOURCE_SENSITIVITY_ACCEPTANCE_REPORT_ZH.md'),files=count,bytes=total)),flush=True)

if __name__=='__main__':main()
