"""Render a local report from completed T550 evidence and SHA receipts."""
from pathlib import Path
import json,csv
W=Path(__file__).resolve().parent
def read(n):return json.loads((W/n).read_text(encoding='utf-8'))

def main():
 a=read('author_review/acceptance_author_20261114.json');assert a['status']=='PASS'
 row=a['row'];cert=a['certificate'];comp=a['comparison'];dist=a['rc_ratio_distribution'];flips=a['shaanxi_comparison']
 receipt=read('finalize_receipt.json');v=read('section2_verification.json');cost=read('cost_comparison/comparison_summary.json')
 audit=read('row_audit_receipt.json')['audit'];count=audit['counts']
 text=f'''# Case3 2060（A）验收与成本区间（2026-11-14）

**PASS：三项独立证据满足作者条件，按任务书验收。** 第2节完成后已先回报，再执行第3节。原结果、严格QC及基础评估器HARD_FAIL保留；新relative_v1记录仅对solver作条件披露。水库仍为作者暂缓，不写成已通过；未重解、不建监听。

## 前置备份

旧PID1081649已退出，15:46:56UTC传输COMPLETE，T1/T2/T3全部VERIFIED，106文件5,506,884,504bytes。开始行审计前已重读全部目标bytes/SHA并复核当前云端result_manifest一致，源身份未变；详见`backup_precheck.json`。作者本次磁盘余量例外保留在原备份操作记录，不放松验收门槛。

## 原MPS与本解BarX独立行定位

索引53400865从本案原MPS的完整行序定位为 `{row['name']}`。变量数{count['variable']:,}、约束数{count['constraint']:,}，两类顺序摘要均匹配本解checkpoint。行名不由C2060或2050同索引推定；冻结运行源码逐文件SHA已核对。

变量族与原系数：

|变量族|项数|系数|贡献|
|---|---:|---|---:|
'''
 for name,r in row['term_families'].items():text+=f"|{name}|{r['count']}|{r['coefficient_values']}|{r['contribution']:.12f}|\n"
 text+=f'''
该行为河北省年度外送汇总等式：年度外送GWh等于全年8760个1h步的正向/反向外送GW之和。单位 **GWh**。

- 重构残差 **{row['residual_gwh']:.12f} GWh**，年度量级 **{row['row_magnitude_gwh']:.9f} GWh**。
- 相对比例 **{row['relative_residual']:.12g}**；适用容差 `max(1e-3 GWh,1e-6×年度电量)` = **{row['tolerance_gwh']:.12f} GWh**。
- 残差为容差的 **{row['ratio_to_tolerance']:.6%}**，通过。与原solve_report最大违反的差 **{a['reconstruction_difference']:.6g} GWh**（求和舍入）。完整逐项审计留T550，摘要及完整文件SHA见`row_audit_receipt.json`。

## 本解自身BarPi证书与终态P/D

B = **{cert['B_million_cny']:.9f} million CNY = {cert['B_million_cny']/100:.9f}亿元/年**；B/obj = **{cert['B_over_objective']:.12g}**，低于1e-2门槛。证书原MPS、checkpoint和本解BarPi身份全部核验。

|终态指标|million CNY|
|---|---:|
|P|{comp['P_million_cny']:.9f}|
|D|{comp['D_million_cny']:.9f}|
|P−D|{comp['original_P_minus_D_million_cny']:.9f}|

P−D = **{comp['original_gap_yi_cny']:.9f}亿元**；B/(P−D) = **{comp['B_to_original_gap']:.6%}**。B{'超过' if cert['B_over_objective']>1e-4 else '未超过'}1e-4×P；本任务链终点按作者规则只披露，**不重解**。

|8025被剔除列统计|值|
|---|---:|
|当前最小rc_ratio|{dist['minimum_rc_ratio']:.12g}|
|负价列 / 翻转站点|{dist['negative_count']} / {flips['current_flip_count']}|
|rc_ratio <0.1|{dist['below_0p1_count']}（{dist['below_0p1_fraction']:.6%}）|
|当前rc_ratio中位数|{dist['current_quantiles']['0.5']:.12g}|
|当前rc_ratio的5%分位|{dist['current_quantiles']['0.05']:.12g}|
|相对Base2060清单变化中位数|{dist['delta_median']:.12g}|
|相对Base2060清单变化5%分位|{dist['delta_p05']:.12g}|

变化为“本解rc_ratio − Base2060原清单rc_ratio”，列等权，numpy线性分位数，不是GW加权。8025列全表见`author_review/excluded_rc_ratio_columns.csv`；Base清单SHA与候选逐列比对见`base_screen_ratio_identity.json`。

负约化成本列（不等同负电价）：

|grid_uid|技术|省代码|rc_ratio|B贡献 million CNY|
|---|---|---:|---:|---:|
'''
 for r in csv.DictReader((W/'pricing/negative_screened_columns.csv').open(encoding='utf-8-sig')):text+=f"|{r['grid_uid']}|{r['technology']}|{r['province_code']}|{float(r['rc_ratio']):.9f}|{float(r['improvement_bound_million_cny']):.9f}|\n"
 text+='\n## C2060及陕西11站比对\n\nC2060原翻转集合独立核对为G000041198/onwind、G000041199/onwind、G000031280/upv。历史定价文件均核对receipt SHA及各自BarPi身份；按grid_uid+technology集合比对。\n\n'
 for label,c in flips['comparisons'].items():
  def sites(key):return '、'.join(r['grid_uid']+'/'+r['technology'] for r in c[key]) or '无'
  text+=f"- 相对{label}：交集{len(c['intersection'])}站（{sites('intersection')}）；新增{len(c['new_in_case3_2060'])}站（{sites('new_in_case3_2060')}）；本案不再翻转{len(c['no_longer_flipped'])}站（{sites('no_longer_flipped')}）。\n"
 text+='\n|陕西grid_uid|本解rc_ratio|B贡献 million CNY|本案翻转|C2060翻转|Case3 2050翻转|C2050翻转|\n|---|---:|---:|---|---|---|---|\n'
 for r in csv.DictReader((W/'author_review/shaanxi_11_sites.csv').open(encoding='utf-8-sig')):
  text+=f"|{r['grid_uid']}|{float(r['current_rc_ratio']):.9f}|{float(r['improvement_bound_million_cny']):.9f}|{r['currently_flipped']}|{r['flipped_in_C2060']}|{r['flipped_in_case3_2050']}|{r['flipped_in_C2050']}|\n"
 text+=f"\n陕西11站本案翻转{flips['shaanxi_current_flip_count']}站，B贡献合计{flips['shaanxi_B_million_cny']:.9f} million CNY。\n"
 text+=f'''
## 重评、交付与同步

当前评估器六组已执行物理相对检查通过；水库`DEFERRED_BY_AUTHOR_20261012`。PInf={a['barrier_primal_infeasibility']:.12g}在授权区间，行定位与证书均满足，因此独立作者记录PASS，solver作条件披露；原评估记录保留。

与C2060完全相同的73文件清单已取回`case3_2060/output_8760/`，共{v['collected_small_bytes']:,}bytes（{v['collected_small_bytes']/2**20:.2f}MiB），最大单文件{v['maximum_collected_file_bytes']:,}bytes。包含gurobi.log、两份指定逐时小CSV、年度表和状态；大原模型/BarX/BarPi/省级调度留T550。所有回传文件bytes/SHA通过，收尾重读原备份{v['original_backup_file_count']}文件全部匹配；未修改源输出。

验收JSON双端SHA：`{receipt['files']['author_review/acceptance_author_20261114.json']['sha256']}`。详见`finalize_receipt.json`、`case3_2060/collect_receipt.json`、`section2_verification.json`。37项相关测试通过，模型与求解配置未改。

## A2060相对Base/B/C的成本点差与工程对偶区间

下表均为“参考情景成本 − A成本”，正值表示A节省，单位亿元/年。计算在T550完成，四案原solve_report及两案自身BarPi证书均按SHA核对。

|参考情景|节省点差|区间下界|区间上界|包含零|
|---|---:|---:|---:|---|
'''
 for r in cost['comparisons']:text+=f"|{r['reference']}|{r['point_saving']:.9f}|{r['lower_saving']:.9f}|{r['upper_saving']:.9f}|{r['interval_contains_zero']}|\n"
 text+='\nBase/B为未筛选参考，区间`[D_ref−P_A, P_ref−D_A+B_A]`；C为筛选参考，区间`[D_C−B_C−P_A, P_C−D_A+B_A]`，不能遗漏下界的B_C。完整P/D/B与来源见`cost_comparison/comparison_summary.json`、`A2060_cost_intervals.csv`。标记`BARRIER_DUAL_ENGINEERING_GRADE`；这是作者指定的工程区间，不是统计置信区间或市场结算。若A/C区间包含零，点差本身不足以判定成本优势；正式2050/2060机制比较由Claude另开目录。\n'
 (W/'REVIEW_ZH.md').write_text(text,encoding='utf-8')

if __name__=='__main__':main()
