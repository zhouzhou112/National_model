# Base 2030/2040/2050 验收证据收集（未正式签发）

2026-10-12，Git 基准 `ba3424ba2544e9eaced7e26ace2d6140cb1ce0d4`。

**本轮仅完成源证据读取与 SHA 核对。2060 小容量删除检查触发任务书 D2 停止条件，relative_v1 实现与正式验收尚未完成；没有创建 acceptance_relative_v1.json。**

每年 17 个小文件保存于本地 `evidence/<year>/`；16 个是原 `result_manifest.json` 成员，bytes/SHA 一致，manifest 自身由源端 SHA 与下载字节复核。云端文件没有改写。完整源 release、文件 SHA、输出目录逐文件大小见 `collection_manifest.json`。本地原始副本未全部纳入 Git，可用 `python supplementary_materials/reviews/base_acceptance_relative_v1_20261012/collect_evidence.py` 重取；现存副本不同会拒绝覆盖。

|指标|2030|2040|2050|
|---|---:|---:|---:|
|最大功率残差 GW|1.855408100e-4|2.059834154e-6|2.653842488e-7|
|成本分项相对闭合残差|1.760943342e-11|2.224817162e-11|1.680873654e-11|
|双向流额外损耗/系统负荷|9.188963622e-7|1.312362370e-5|1.253011093e-5|
|原严格 QC|HARD_FAIL|HARD_FAIL|HARD_FAIL|
|relative_v1 正式验收|未签发|未签发|未签发|

三项数值与任务书预期相符，分别低于最低功率阈值 1e-3 GW、成本阈值 1e-7、额外损耗阈值 1e-4。水库应按作者决定标记 `DEFERRED_BY_AUTHOR_20261012`，但本轮尚未补齐其站点/活动库容披露。其余原 hard checks 无失败；2030 原失败为 power_balance、unidirectional_interprovincial_flow、reservoir_transition、objective_components；2040/2050 是后三项。正式求解器、全部披露及派生验收 SHA 合同仍待独立评估器完成，不用三项初查替代验收记录。

输出盘点：2030 为 5,314,638,348 bytes，2040 为 5,319,922,492 bytes，2050 为 5,321,841,011 bytes。用户要求重试后固定服务器已连接到 t550，目标盘总量 4,029,616,283,648 bytes、可用 1,481,126,653,952 bytes，备份这三个目录后估算剩余 36.36%，满足 30% 空间门槛。因 D2 停止，未备份 T1/T2/T3。固定机的云端别名无法解析，若续办备份可采用本机流式中转。

停止证据及精确下一步见 `../base_2060_launch_20261012/REVIEW_ZH.md`。


## 2026-10-12 续办：三年正式验收

# Base 2030/2040/2050 正式验收（2026-10-12）

作者决定 `ACCEPTED_RELATIVE_V1_20261012`：三年均通过修订后的 relative_v1。冻结归档和原 candidate 标记不变，验收 JSON 作为旁置证据保存。固定服务器每个 release 的 `acceptance_relative_v1_20261012/` 已有离线 assessment；正式验收 JSON 的同步结果以 `acceptance_sync_status.json` 为准。

| 年份 | 原严格失败项（保留） | relative_v1 | 最大功率残差 GW | 成本闭合相对残差 | 双向流额外损耗/系统负荷 | 最大水量残差 m³（暂缓） |
|---|---|---|---:|---:|---:|---:|
| 2030 | power_balance, unidirectional_interprovincial_flow, reservoir_transition, objective_components | PASS | 0.00018554081 | 1.76094334e-11 | 9.18896362e-07 | 1.60177381 |
| 2040 | unidirectional_interprovincial_flow, reservoir_transition, objective_components | PASS | 2.05983415e-06 | 2.22481716e-11 | 1.31236237e-05 | 232.508416 |
| 2050 | unidirectional_interprovincial_flow, reservoir_transition, objective_components | PASS | 2.65384249e-07 | 1.68087365e-11 | 1.25301109e-05 | 29.2747617 |

水量项按作者决定暂缓逐站判定；站点、小时及活动库容见每年的 `assessments/<year>/acceptance_relative_v1.json`。小于 1 MW 新建量、储能充放电、火电启停与双向流重叠、历史 bound-close 和数值清理披露均保存在对应 assessment 中。省际结果报告净流。工程对偶等级为 `BARRIER_DUAL_ENGINEERING_GRADE`，BarConvTol=1e-4。

执行：`collect_evidence.py` 核对云端小文件；`assess_on_t550.py` 在已核验 T1 备份上运行独立离线评估，不重启备份；`finalize_acceptance.py` 在三年全部 PASS 后写正式记录。各证据 SHA 见 `evidence_manifest.json`、`collection_manifest.json` 与 `acceptance_server_sha256.json`，可追溯回各冻结 `result_manifest.json`。没有原 manifest 条目的文件（包括 manifest 本身）通过两端 SHA 核对。水库逐时残差从原 npz 重算并与原 QC 最大值一致。

差异：无新增科学判据；严格口径仍为 HARD_FAIL，作者验收为独立旁置记录，不伪装成历史严格 QC 已通过。
