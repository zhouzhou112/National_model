"""Build source-bound Chinese completion reports after offline work finishes."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json

HERE=Path(__file__).resolve().parent
REVIEWS=HERE.parent
NOC=REVIEWS/'case3_2030_launch_20261014/nocredit_results_20261026'
SCREEN=REVIEWS/'base_2060_screen_20261026'

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,text):
    if p.exists():assert p.read_text(encoding='utf-8')==text,'Refuse changed report'
    else:p.write_text(text,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nocredit-only',action='store_true')
    args=parser.parse_args()
    collect=load(NOC/'collect_receipt.json');price=load(HERE/'price_receipt.json')
    assessment=load(NOC/'assess_receipt.json');qc=load(NOC/'assessment/solution_qc_relative_v1.json')['acceptance_profiles']['relative_v1']
    comparison=load(HERE/'compare_receipt.json')
    case_certificate=load(REVIEWS/'case3_2040_C2050_launch_20261019/screen_pricing_certificate_claude.json')
    assert case_certificate['objective_million_cny']==comparison['case3']['objective_value_million_cny']
    rows=[]
    for key in ['Base','nocredit','case3']:
        x=comparison[key];b=x['barrier_primal_dual_metrics'];bound=0 if key=='Base' else price['B_million_cny'] if key=='nocredit' else case_certificate['B_million_cny']
        rows.append(dict(scenario=key,primal_million_cny=x['objective_value_million_cny'],dual_million_cny=b['dual_objective'],
            primal_dual_gap_million_cny=b['absolute_primal_dual_objective_gap'],relative_gap=b['relative_primal_dual_objective_gap'],
            screen_bound_million_cny=bound,solve_report_sha256=x['source_verification']['solve_report.json']['sha256']))
    f=io.StringIO(newline='')
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    write(NOC/'objective_comparison.csv',f.getvalue())
    base=rows[0];table='\n'.join(f"|{r['scenario']}|{r['primal_million_cny']:.6f}|{r['dual_million_cny']:.6f}|{r['primal_dual_gap_million_cny']:.6f}|{r['relative_gap']:.8g}|{r['screen_bound_million_cny']:.6f}|" for r in rows)
    intervals=[]
    for r in rows[1:]:
        low=(base['dual_million_cny']-r['primal_million_cny'])/100
        high=(base['primal_million_cny']-r['dual_million_cny']+r['screen_bound_million_cny'])/100
        point=(base['primal_million_cny']-r['primal_million_cny'])/100
        intervals.append(f"- {r['scenario']} 相对 Base：点差 {point:.6f} 亿元/年；按作者公式的节省区间 [{low:.6f}, {high:.6f}] 亿元/年。")
    manifest=load(HERE/'inspect_receipt.json')['backup']
    assert collect['result_manifest_sha256']==manifest['source_result_manifest_sha256']
    write(NOC/'REVIEW_ZH.md',f'''# nocredit 2030 收尾复核（2026-10-26）

## 结论

Job 5153901 原始报告为 OPTIMAL，保全 COMPLETE。完整 T550 备份为 COMPLETE：93 文件、5,510,708,567 bytes；本轮复核 backup/result manifest 身份一致，未重复传输完整备份。扩展口径 `{qc['version']}` 为 **{qc['status']}**；原严格 HARD_FAIL 与水库暂缓项继续保留，自动验收不替代作者采纳，也不影响完整保全。

本机取回 `output_8760/` 下全部不超过 32 MiB 的文件，共 {len(collect['files'])} 个、{sum(v['bytes'] for v in collect['files'].values()):,} bytes。{sum(v['manifest_match'] for v in collect['verification'].values())} 项逐项匹配原 result manifest 的 bytes/SHA；manifest 自身与 T550 完整备份所绑定 SHA 一致。包括 annual_flexible_load_by_province、装机表、cost_components、annual_summary、状态与原模型/checkpoint身份文件。8 个超过阈值的大文件留在 T550，逐项路径和大小见 `collect_receipt.json`，没有删除或省略完整备份。

## 三方目标与原对偶差

成本单位为 **million CNY/年（2025 不变价）**，表中原对偶差来自各原始 `solve_report.json` 的最终 durable Barrier 记录。三方均为 2030 年、8760 小时、31 省系统规划；目标为模型年化投资及运行成本。容量/功率 GW、电量 GWh；本次仅后处理，不改变变量、约束、目标、时空尺度或输入。

|情景|原始目标 P|原始对偶 D|P−D|相对原对偶差|筛选上界 B|
|---|---:|---:|---:|---:|---:|
{table}

三方 solve_report 均在 T550 对原 result manifest 重新核验，路径/SHA见 `../../case3_2050_preparation_20261026/compare_receipt.json`；精确数值见 `objective_comparison.csv`。case3 的 B 复用已确认的 2026-10-19 Claude 证书（与现存归档目标一致），未重新求解。

节省区间严格使用 `[D_Base − P_X, P_Base − D_X + B_X]`。1 亿元 = 100 million CNY。

{chr(10).join(intervals)}

nocredit 与 case3 的目标点差为 {(rows[1]['primal_million_cny']-rows[2]['primal_million_cny'])/100:.6f} 亿元/年。该点差同时受各解原对偶差与筛选上界影响，不把它直接写成精确的容量信用因果贡献。工程对偶按 `BARRIER_DUAL_ENGINEERING_GRADE`、BarConvTol=1e-4 披露。

## T550 定价证书

用 `scripts/price_screened_candidates.py` 在完整备份上运行，直接读取原 MPS 和原顺序 BarPi，校验 archive/checkpoint/semantic manifest。B = {price['B_million_cny']:.9f} million CNY，B/obj = {price['B_over_objective']:.12g}，近优性 `{price['near_optimality_decision']}`，比较用途 `{price['base_comparison_decision']}`。公式为被筛掉站点原新增上界乘以负配对约化成本的正部之和，未更改筛选规则或重新求解。

完整证书与定价 CSV **仅保留在 T550**：`{price['certificate_path']}`；证书 SHA256 `{price['certificate_sha256']}`。本机只有数值/路径/SHA回执 `case3_2050_preparation_20261026/price_receipt.json`，未取回完整证书、MPS 或 BarPi。

## 扩展评估与复现

`scripts/assess_relative_v1.py` 在 T550 运行，按原逐时省平衡和水库数组计算 `archived_inputs`，源文件评估前后 SHA 一致。独立结果在 `assessment/solution_qc_relative_v1.json`，输入与核验链在同目录；原 `output_8760/solution_qc.json` 未改写。扩展项按既定 max(严格容差,1e-3 GW/GWh)，双向流按额外损耗/全年负荷≤1e-4；水库记录最差残差及库容并按作者决定暂缓，严格标签继续保留。

本轮入口为 `python supplementary_materials/reviews/case3_2050_preparation_20261026/remote_work.py collect|price|assess|compare`，每个动作单独执行；已有结果拒绝覆盖。具体远端命令、工具 SHA、源 SHA、接收字节核验见各 receipt。无随机采样，无新优化，不涉及随机种子。

## 差异与限制

旧作者决定中case3区间上界简记为64.32亿元；本轮按原归档高精度P/D/B重算为64.314766亿元（保留两位为64.31）。原记录保留，本报告明确采用表内原始高精度值，不修改公式或科学结果。

“全部小文件”以 ≤32 MiB 明确定义；完整结果仍由 T550 93文件备份覆盖。本机原始取回数据约105MB不全部发布到Git，Git保留报告、精确对照表、SHA清单与独立评估。当前报告不启动 nocredit 后继年份，不干预5201318、5207165。
''')
    if args.nocredit_only:
        print('Nocredit review and objective comparison complete.');return
    screen=load(SCREEN/'screen_identity.json');audit=load(SCREEN/'ready/audit.json')
    assert audit['status']=='PASS'
    write(SCREEN/'REVIEW_ZH.md',f'''# Base 2060 筛选清单（2026-10-26）

在 T550 完整备份上运行原 `scripts/build_vre_screen_list.py --margin 0.2`，来源 `{screen['candidate_screen']['source_release']}`。原 MPS SHA `{screen['identity']['mps_sha256']}`，BarPi SHA `{screen['identity']['barpi_sha256']}`。MPS、BarPi、checkpoint指纹和语义表身份均已核验；完整文件保留T550。

与 P4 2040/2050 使用相同的配对约化成本、费用分母、正余量与 margin0.2 判据。复用 `audit_p4_screens.py`，仅增加2060年份与显式来源参数；算术、唯一稳定键、源身份、原顺序及反序调用实际 `apply_vre_screen` 均 PASS。无模型构建或优化。

- 全部站点×技术：{audit['sites']}；有正扩展余量：{audit['expandable']}；无余量：{audit['no_headroom']}。
- 按 Base2060 原余量筛掉：{audit['excluded']}；保留可扩展：{audit['retained_expandable']}。
- 全量定价表：`source_screen.csv`，SHA `{screen['candidate_screen']['source_csv_sha256']}`。
- 生产三列清单：`ready/source_screen.csv`，SHA `{audit['published_csv_sha256']}`；生产profile片段：`ready/candidate_screen_fragment.json`。

这些计数只描述 Base2060 的原余量，不代表尚未构建的 case3/C2060 最终候选数；应用时仍须逐一按 grid_uid×technology 对齐并使用未来模型实际新增上界。清单生成不授权case3/C2060求解，也不改已完成Base2060的全候选模型。

全量CSV与来源小证据留本机/T550，Git发布生产清单、身份与审查。`source_evidence/download_identity.json` 是远端核验描述文件，明确大型原件仅在T550，不能解读为已下载本机。复现命令与返回SHA见 `screen_receipt.json`，原manifest/工具身份见 `screen_identity.json`。

生产三列清单已在本地核验并随Git交付；额外复制到T550的ready/旁置目录时连接中断，后续只读检查也在SSH banner阶段超时，目标状态未确认。原始全量清单/identity已在T550完成并核验，不受影响；恢复连接后先检查ready/，逐字节相同则复用，不盲目覆盖。
''')
    cloud=load(HERE/'cloud_preparation_receipt.json');diff=load(HERE/'profile_diff.json')
    write(HERE/'REVIEW_ZH.md',f'''# case3 2050 预置与2030收尾（2026-10-26）

## 已完成

1. nocredit2030：73个小文件逐项核验并取回；T550完整备份身份复核，定价证书留T550；扩展relative_v1为 {qc['status']}。详细三方目标/原对偶差及节省区间见 `../case3_2030_launch_20261014/nocredit_results_20261026/REVIEW_ZH.md`。
2. Base2060 margin0.2 清单：完整原MPS/BarPi在T550计算，P4同口径审核PASS；生产清单{audit['sites']}项，原Base正余量筛掉{audit['excluded']}项，SHA `{audit['published_csv_sha256']}`。
3. case3 2050：新profile逐键对照父48线程profile，**仅5个键不同**：Threads、ID、candidate_screen的3个来源字段；description及所有其他数值/验收设置不变。profile SHA `{diff['profile_sha256']}`。Base2050清单沿用既有 P4，SHA `a55a93738a37c0cf51ef84b73f1e34177cfd7f26a040df146e0c83462190d528`。

## 预置包状态

云端独立目录：`{cloud['directory']}`，状态 **{cloud['status']}**。58项数据本地与云端bytes/SHA匹配，批处理bash语法PASS；新增数据包括参与率v2与三份续接输入，其余只读链接已验证来源。11MB准备包SHA `{cloud['payload_sha256']}`，精确大小/成员见 `package_identity.json`。其中source_commit仅为准备时Git基准0cbad43，成员身份另由SHA绑定；本轮功能已提交3c11ed7，最终生产源码须从门禁通过后的已审查commit重新冻结。

正式求解资源预设40线程，OMP/OPENBLAS/MKL均40；Slurm64CPU/750G/billing64/UNLIMITED/no-requeue，启动可用内存≥700GiB。框架A `case3_thermal_ev_v5`，规划2050/边界2040。sbatch没有Late-entry标志，要求最终门禁标记和真实R1状态；当前两者均不存在，不能用于生产提交。**未生成R1、未执行1h/24h门禁、未冻结最终release、未提交或release新作业。**

准备代码补充范围：`factor_screen.py` 仅登记新profile并限制2050/case3/同情景状态/40线程；旧C2050 profile仍限定Late-entry。现有门禁助手新增显式 `--same-scenario-continuation`，默认旧行为保持兼容。没有改变物理模型、变量定义、目标、约束、单位或数据。

## 验证

定价工具5项测试PASS；扩展评估13项本地PASS，另1项本地因gurobipy缺失未执行，在T550既有环境补验PASS；T550新旧profile/身份/授权边界7项PASS，其中新profile3项也在本地通过。程序语法、profile逐键diff、58输入SHA、生产清单SHA及云端bash语法均PASS。测试不冒充尚未执行的1h/24h科学与工程门禁。

## 尚待上游结束

两个运行作业仅只读，最新快照见本目录 `live_*.json`。case3 2040终态后先全备份、T550证书、扩展评估；B/obj≤1e-2时按既定授权采纳，再R1、1h/24h、2050实际参数核准、最终冻结与云端preflight，全部通过即提交并release。C2050终态只做备份/证书/扩展评估并回报，C2060/C′等作者决定。准确入口、命令、参数与停止条件见 `NEXT_ACTIONS_ZH.md`。

没有创建后台监听或自动轮询；本轮长时任务均为有界离线处理。未读取/复制凭据，未更改运行冻结包。最终profile生效须使用本轮已审查提交的新源码，不能仅把新JSON套到旧源码。用户原有SI交接/稿件和其他改动不进入本次明确提交清单。

Base2060生产三列清单的额外T550旁置同步因连接中断未验证；本地/Git生产清单及T550原全量清单均已核验。详见base_2060_screen_20261026/ready_t550_sync_status.json。
''')
    print('Three reports and objective_comparison.csv written.')

if __name__=='__main__':main()
