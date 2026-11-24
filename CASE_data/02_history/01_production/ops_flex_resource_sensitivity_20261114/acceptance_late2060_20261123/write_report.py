"""Format the verified T550 acceptance and delivery; no hourly-array analysis."""
from pathlib import Path
import json,csv,datetime,hashlib,os
HERE=Path(__file__).resolve().parent
WORK=HERE.parent
REPO=WORK.parents[2]

def lp(p):
 p=Path(p)
 return Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' and not str(p).startswith('\\\\?\\') else p
def load(p):return json.loads(lp(p).read_text(encoding='utf-8'))
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
def interval(a,b):return f'[{a:.3f}, {b:.3f}]'

def main():
 receipt=load(HERE/'LATE-Open-2060_return_receipt.json');root=Path(receipt['local_directory']);side=root/'acceptance_resource_late2060_20261123';a=load(side/'acceptance_record.json');analysis=load(side/'analysis/analysis_summary.json');row=load(side/'row_audit_summary.json');direction=load(side/'comparisons/directional_B_summary.json');central=load(side/'comparisons/LATE_Open_vs_central.json');annual=load(side/'annual_rows/row_extraction_summary.json');order=load(side/'annual_rows/row_order_verification.json');term=load(WORK/'late2060_completed_20261123/terminal_summary.json')
 assert a['status']==analysis['status']==central['status']==annual['status']==order['status']=='PASS' and receipt['all_bytes_sha_match']
 province_path=REPO/'data/sets/provinces.csv';expected=load(WORK/'batch2/cloud_source_file_sha256.json')['2060']['data_overlay']['sets/provinces.csv'];assert hashlib.sha256(province_path.read_bytes()).hexdigest()==expected['sha256']
 with province_path.open(encoding='utf-8-sig',newline='') as f:names={int(r['province_code']):r['province_name_zh'] for r in csv.DictReader(f)}
 provinces='、'.join(names[p] for p in direction['province_codes'])
 comparisons=[[r['reference'],f"{r['point_saving_yi_cny']:.3f}",interval(r['lower_saving_yi_cny'],r['upper_saving_yi_cny'])] for r in analysis['comparisons']]
 comparisons.append(['中央LATE2060',f"{central['point_saving_yi_cny']:.3f}",interval(central['lower_saving_yi_cny'],central['upper_saving_yi_cny'])])
 report=['# LATE-Open2060条件验收报告','',f'生成：{datetime.datetime.now(datetime.timezone.utc).isoformat()}。结论：**PASS，接受并披露**。本次只读重评、原行重构、自身双向定价、年度对偶恢复和初步分析均在T550完成；原始输出、严格HARD_FAIL及基线relative_v1记录保持不变，未重解。验收为质量标签，作者采纳仍由作者决定。','',
 '## 1. 终态与完整备份','',
 'Job5658666于2026-11-22 22:34:36UTC（北京时间23日06:34:36）COMPLETED/0:0，477轮OPTIMAL，总3天08:34:07。进程树峰637.027908GiB，原保全COMPLETE/errors=[]、stderr空。',
 '完整备份于11月23日16:03:07UTC完成：108文件5,546,730,397bytes，T1/T2/T3全部VERIFIED，源身份不变。验收前再次逐文件核全部原件bytes/SHA并匹配当前云端manifest，未重复传输或计算已完成案例。','',
 '## 2. 条件验收的三项独立证据','',
 f"最大违反索引 **{row['index']}** 在本案原MPS中独立定位为`{row['name']}`，河北年度外送汇总等式。变量族为年度外送GWh、8760小时正向及交流反向GW流；系数分别+1和−1。完整{row['counts']['variable']:,}变量与{row['counts']['constraint']:,}约束的原始名称/sense顺序摘要匹配本解checkpoint，没有由2050或中央2060索引推定。",'',
 table(['项目','核验值'],[['重构绝对残差',f"{a['row']['residual_gwh']:.12g} GWh"],['年度量级',f"{a['row']['row_magnitude_gwh']:.9f} GWh"],['相对残差',f"{a['row']['relative_residual']:.12g}"],['适用容差',f"max(1e-3 GWh, 1e-6×年度电量) = {a['row']['tolerance_gwh']:.9f} GWh"],['与归档最大违反值的重构差',f"{a['maximum_violation_reconstruction_difference']:.12g} GWh"]]),'',
 f"本解自身BarPi双向证书 **B={a['screening_B_million_cny']:.9f} million CNY，即{a['screening_B_million_cny']/100:.6f}亿元/年；B/P={a['B_over_objective']:.12g}（{100*a['B_over_objective']:.6f}%）**，处于1e-3至1e-2接受并披露档。固定在下界和上界分别计算增加/减少方向，cap/new及对应接入线关系保留；清单SHA与原运行audit一致，不以参考C2060对偶冒充本解证书。",'',
 f"共{a['certificate']['fixed_sites']}个固定站点×技术组。负方向约化成本组{direction['negative_direction_groups']}个，其中{direction['negative_direction_zero_original_range']}组原始可动区间为零；真正对B有正贡献的是{direction['positive_improvement_groups']}组，覆盖{direction['province_count']}省：{provinces}。完整方向价格CSV、负方向组及上下界rc_ratio分布均在验收包；B贡献省码×技术表在comparisons目录。",'',
 f"当前评估器全部已执行相对检查通过，水库按作者暂缓。验收用回调PInf={a['barrier_primal_infeasibility']:.12g}在[1e-2,1e-1]内；独立最大行在族容差内，自身B/P≤1e-2，三项合取满足后，仅在旁置当前评估中将solver改为条件披露。日志打印尺度与回调尺度不同，不混作收敛反弹。",'',
 '## 3. P、D、证书与成本区间','',
 table(['量','million CNY','亿元/年'],[['P',f"{a['P_million_cny']:.9f}",f"{a['P_million_cny']/100:.6f}"],['D',f"{a['D_million_cny']:.9f}",f"{a['D_million_cny']/100:.6f}"],['P−D',f"{a['primal_dual_gap_million_cny']:.9f}",f"{a['primal_dual_gap_million_cny']/100:.6f}"],['B',f"{a['screening_B_million_cny']:.9f}",f"{a['screening_B_million_cny']/100:.6f}"]]),'',
 f"B为原对偶差的 **{a['B_to_original_gap']:.6f}倍（{100*a['B_to_original_gap']:.3f}%）**。B>1e-4×P，比较精度问题提交作者判断，不自动放回列、重解或改变验收门槛。B是此2060模型在给定继承状态下放开固定点位的工程上界，不覆盖2050上游误差的跨期传播，不是整个多阶段路径的全局最优证书。",'',
 '正数为本案较参考案节省，金额为2025年不变价。无筛选参考使用`[D_ref−P, P_ref−D+B]`；中央LATE自身也有筛选证书，使用`[D_ref−B_ref−P, P_ref−D+B]`。均为工程对偶区间，不是统计置信区间或市场结算。','',
 table(['同年参考','节省点差：亿元/年','工程区间'],comparisons),'',
 '各2060路径继承状态不同，不能将所有点差归因于单一资源参数。当前结论不等同于所有路径的完美预见联合最优。','',
 '## 4. 年度对偶及初步分析','',
 f"原MPS ROWS与自身BarPi恢复{annual['T4_rows']}条年度核算行，完整原始行序摘要通过。旁置annual_rows/annual_row_duals.csv补齐原导出缺项，不改原输出；工程影子价格标BARRIER_DUAL_ENGINEERING_GRADE，不裁负价。",'',
 table(['服务','签约GW','上限GW','上限利用率','下调TWh','等效下调小时'],[[r['service'],f"{r['contract_gw']:.3f}",f"{r['upper_gw']:.3f}",f"{100*r['contract_share_of_upper']:.2f}%",f"{r['down_regulation_gwh']/1000:.3f}",f"{r['equivalent_down_hours']:.1f}" if r['equivalent_down_hours'] is not None else 'NA'] for r in analysis['services']]),'',
 'T550还完成成本分项、全国及五省小时汇总、31省完整负荷侧价格、分技术发电与弃电、连续启停容量/等效次数、储能充放电。服务调用按各自签约基线池重构，V1G/V2G不重叠；V2G实际放电另报，不重复累加。连续RUC启停不是离散机组台次。','',
 '## 5. 本地交付和边界','',
 f"本轮回传{receipt['files']}个有效载荷文件，{receipt['bytes']:,}bytes（{receipt['bytes']/1e6:.2f}MB），单件最大{receipt['maximum_file_bytes']:,}bytes，逐件SHA匹配，验收JSON同步。完整固定列审计如超过32MiB则无损gzip并验证解压SHA。原MPS、BarX/BarPi、大型调度数组、完整行系数及解析缓存留T550。",'',
 f"本地案例目录：`{root}`。原73项清单中candidate_selection.csv因边界状态固定方式不适用，72项适用原文件加固定清单/验收/定价/分析；delivery_manifest逐项记录。准备与求解失败历史、原严格标签全部保留。",'',
 '状态：条件验收完成；没有新增求解、自动重解或后台监听。是否采纳及是否为更精确的成本比较重解，由作者决定。']
 (HERE/'ACCEPTANCE_REPORT_ZH.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
 summary=dict(status='PASS',case='LATE-Open-2060',classification='ACCEPT_DISCLOSE',P_million_cny=a['P_million_cny'],D_million_cny=a['D_million_cny'],B_million_cny=a['screening_B_million_cny'],B_over_P=a['B_over_objective'],B_over_gap=a['B_to_original_gap'],row=a['row'],negative_direction_groups=direction['negative_direction_groups'],positive_improvement_groups=direction['positive_improvement_groups'],province_count=direction['province_count'],delivery=receipt,automatic_resolve=False,author_adoption='PENDING_AUTHOR_REVIEW')
 (HERE/'acceptance_delivery_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
