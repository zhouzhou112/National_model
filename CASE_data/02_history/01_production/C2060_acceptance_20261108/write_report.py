"""Render the local handoff from verified receipts; no scientific computation."""
import json
import csv
from pathlib import Path

W = Path(__file__).resolve().parent


def read(name):
    return json.loads((W/name).read_text(encoding='utf-8'))


def main():
    a=read('author_review/acceptance_author_20261108.json')
    assert a['status']=='PASS'
    row=a['row'];cert=a['certificate'];comp=a['comparison'];dist=a['rc_ratio_distribution'];flips=a['shaanxi_comparison']
    collection=read('C2060/collect_receipt.json');receipt=read('finalize_receipt.json')
    verification=read('section2_verification.json')
    cost=read('cost_comparison/comparison_summary.json')
    site=list(csv.DictReader((W/'author_review/shaanxi_11_sites.csv').open(encoding='utf-8-sig')))
    sha=receipt['files']['author_review/acceptance_author_20261108.json']['sha256']
    n=len(collection['files']);size=sum(v['bytes'] for v in collection['files'].values())
    text=f'''# C2060 验收与初步成本对照（2026-11-08）

**PASS：本案证据满足作者条件，按任务书验收。** 原输出、原始严格 QC 和基础评估器 HARD_FAIL 记录均保留；通过的是三项证据支持的独立 relative_v1 条件验收。水库逐站水量检查仍按作者规定暂缓。未重解，未触碰 Case3 2060/5411471，未建立监听。

## 原 MPS + BarX 独立行定位

索引 53400865 在本案原 MPS 中为 `{row['name']}`，河北年度外送汇总等式。43,761,732 个变量与 54,217,741 个约束的顺序摘要均与本解 checkpoint 一致；不是由 Case3 2050 的索引推定。

- 变量族：`province_annual_external_sent_gwh` 1项（+1）、`flow_forward_gw` 227760项（−1）、`flow_reverse_ac_gw` 17520项（−1）。全年8760个1h步的GW相加，行单位GWh；冻结源码SHA已核对。
- 残差 **{row['residual_gwh']:.12f} GWh**；年度量级 **{row['row_magnitude_gwh']:.9f} GWh**；相对比例 **{row['relative_residual']:.12g}**。
- 适用容差 `max(1e-3 GWh, 1e-6 × 年度电量)` = **{row['tolerance_gwh']:.12f} GWh**；残差为容差的 **{row['ratio_to_tolerance']:.6%}**，通过。
- 与原 solve_report 最大违反量的差为 {a['reconstruction_difference']:.6g} GWh（求和舍入）。完整245281项行审计留在T550，摘要和SHA见 `row_audit_receipt.json`。

## 本解自身 BarPi 筛选证书

B = **{cert['B_million_cny']:.9f} million CNY = {cert['B_million_cny']/100:.9f} 亿元/年**；B/obj = **{cert['B_over_objective']:.12g}**，小于1e-2采纳门槛。证书MPS、BarPi、checkpoint与本案源结果身份一致。

P = **{comp['P_million_cny']:.9f} million CNY**；D = **{comp['D_million_cny']:.9f} million CNY**；P−D = **{comp['original_P_minus_D_million_cny']:.9f} million CNY（{comp['original_gap_yi_cny']:.9f}亿元）**。

B/(P−D) = **{comp['B_to_original_gap']:.6%}**；B {'超过' if cert['B_over_objective']>1e-4 else '未超过'} 1e-4×P。按本任务规则只披露，不重解。旧定价工具的比较标签原样保留，不执行其旧版自动重解含义。

|8025个被剔除列的统计|数值|
|---|---:|
|当前最小rc_ratio|{dist['minimum_rc_ratio']:.12g}|
|负价列 / 翻转站点|{dist['negative_count']} / {flips['current_flip_count']}|
|rc_ratio <0.1|{dist['below_0p1_count']}（{dist['below_0p1_fraction']:.6%}）|
|当前中位数|{dist['current_quantiles']['0.5']:.12g}|
|当前5%分位|{dist['current_quantiles']['0.05']:.12g}|
|相对Base2060变化中位数|{dist['delta_median']:.12g}|
|相对Base2060变化5%分位|{dist['delta_p05']:.12g}|

变化定义为“本解rc_ratio − Base2060原筛选清单rc_ratio”，列等权，numpy线性分位数。全部被剔除列见 `author_review/excluded_rc_ratio_columns.csv`，负价列与翻转站点见 `pricing/`。原Base筛选清单SHA与本案配置逐一核验。

## 陕西11站点与历史翻转集合

|grid_uid|本解rc_ratio|B贡献 million CNY|本案翻转|Case3 2050翻转|C2050翻转|
|---|---:|---:|---|---|---|
'''
    for r in site:
        text+=f"|{r['grid_uid']}|{float(r['current_rc_ratio']):.9f}|{float(r['improvement_bound_million_cny']):.9f}|{r['currently_flipped']}|{r['flipped_in_case3_2050']}|{r['flipped_in_C2050']}|\n"
    text+=f"\n上述11站点均为陕西陆风；本案翻转{flips['shaanxi_current_flip_count']}站，合计B贡献{flips['shaanxi_B_million_cny']:.9f} million CNY。\n\n"
    text+='当前3个负价列为广东两列陆上风电与西藏一列地面光伏：\n\n|grid_uid|技术|省代码|rc_ratio|B贡献 million CNY|\n|---|---|---:|---:|---:|\n'
    for r in csv.DictReader((W/'pricing/negative_screened_columns.csv').open(encoding='utf-8-sig')):
        text+=f"|{r['grid_uid']}|{r['technology']}|{r['province_code']}|{float(r['rc_ratio']):.9f}|{float(r['improvement_bound_million_cny']):.9f}|\n"
    text+='\n'
    for label,c in flips['comparisons'].items():
        def sites(key):
            return '、'.join(r['grid_uid']+'('+r['technology']+')' for r in c[key]) or '无'
        text+=f"- 相对{label}（历史{c['historical_count']}站）：交集{len(c['intersection'])}站：{sites('intersection')}；新增{len(c['new_in_C2060'])}站：{sites('new_in_C2060')}；本案不再翻转{len(c['no_longer_flipped'])}站：{sites('no_longer_flipped')}。\n"
    text+=f'''
历史翻转集合从T550原证书旁置包读取，逐文件核对receipt SHA，并核对历史证书自身BarPi身份；按grid_uid+technology比对。详见 `shaanxi_flip_comparison.json`。

## 重评、保全与取回

- 当前评估器已在T550重评，所有已执行物理相对检查通过；水库为 `DEFERRED_BY_AUTHOR_20261012`。PInf={a['barrier_primal_infeasibility']:.12g}，满足三项证据后在新作者记录中转为条件披露，原档不改写。
- 全备份106文件，5,506,707,098bytes，COMPLETE；本任务未重复传输云端备份。新增验收/证书均为T550独立旁置目录。
- 按Case3 2050同一≤32MiB/文件清单回传 **{n}文件、{size:,}bytes（{size/2**20:.2f}MiB）**，逐项bytes/SHA通过。目录 `C2060/output_8760/`；大型MPS、BarX/BarPi、完整逐时省级调度留在T550。
- `gurobi.log`：{'源文件存在且已回传。' if verification['gurobi_log']['collected'] else '原output_8760中不存在该文件；不伪造同名日志，原始求解日志按备份清单保全。'}
- 收尾重新读取T550原备份全部{verification['original_backup_file_count']}文件，bytes/SHA全部与原backup_manifest一致；新增验收、证书及成本表双端字节一致。
- 验收JSON双端SHA：`{sha}`。完整回传证据见 `finalize_receipt.json`、`C2060/collect_receipt.json`；另见 `section2_verification.json`。
- 34项相关测试通过。所有工具只读原结果，独立审计旁置；未更改模型、阈值、筛选或求解设置。

## Base2060 / B2060 / C2060 初步成本对照

计算在T550完成，原 `cost_components.csv` 与 `solve_report.json` 均核验源manifest。主成本分量加总与目标一致，运营细分与 `annual_operation` 一致，差异与检查见 `cost_comparison/comparison_summary.json`。运营表不可再次加到主表；Base没有柔性项，只在冻结配置明确 `flexible_load=false` 的已知八项内补零。

|情景|P（亿元/年）|D（亿元/年）|
|---|---:|---:|
'''
    for c,m in cost['metrics'].items():text+=f"|{c}|{m['P']/100:.6f}|{m['D']/100:.6f}|\n"
    text+=f"\nC相对Base成本点差节省 **{cost['Base_minus_C_point_yi_cny']:.6f}亿元/年**，相对B节省 **{cost['B_minus_C_point_yi_cny']:.6f}亿元/年**。按作者`[D_Base−P_C, P_Base−D_C+B_C]`口径，Base−C工程对偶节省区间 **[{cost['Base_minus_C_engineering_interval_yi_cny'][0]:.6f}, {cost['Base_minus_C_engineering_interval_yi_cny'][1]:.6f}]亿元/年**。\n\n"
    text+='分量表：`cost_comparison/primary_cost_comparison.csv`；运营细分：`cost_comparison/operating_cost_comparison.csv`。此为初步会计分解，不把成本差直接解释为单一资源的因果贡献；标记 `BARRIER_DUAL_ENGINEERING_GRADE`，不是市场结算。正式分析由Claude另开目录；A与C的2060对照等待Case3 2060终态。\n'
    text+='\n相对Base，主要减项为火电/核电投资371.62亿元、其固定运维87.63亿元、运营合计446.14亿元；主要增项为风光投资106.37亿元、储能投资69.70亿元。运营合计内部燃料减少390.36亿元、启停减少202.51亿元，同时新增柔性费用，不能将这些细项再与运营合计相加。\n'
    (W/'REVIEW_ZH.md').write_text(text,encoding='utf-8')


if __name__=='__main__':main()
