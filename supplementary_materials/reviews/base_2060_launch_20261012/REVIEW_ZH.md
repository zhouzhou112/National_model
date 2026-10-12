# Base 2060 启动前检查：D2 停止条件触发

2026-10-12（英国日期）。Git 基准 `ba3424ba2544e9eaced7e26ace2d6140cb1ce0d4`。

**状态：STOP_AUTHOR_REVIEW_REQUIRED。未删除 cohort、未准备派生状态、未构建或求解、未创建 release、未提交任何 Slurm 作业（包括 --hold）。**

任务授权来自 `../claude_workspace/tasks/TASK_base_acceptance_and_2060_launch_20261012.md`（相对仓库根目录），用户要求全部前置条件满足后先 held 提交，回复“放行”才释放。本轮发现任务书 D2 明确停止条件，故先停止并保全证据，不能用提交 held 绕过前置门禁。

## 停止证据

读取 2050 冻结输出的 `planning_state_candidate/capacity_cohorts.csv.gz`。只选择 `unit=GW`、`action=new_build`、`build_year>2025`，按 `asset_class × technology × asset_id` 跨 2030/2040/2050 cohort 求和，再选择 `0<sum<1e-3 GW`。这些 cohort 在 2050 均未退役；原状态不含 2025 外生既有装机 cohort。零值、非 GW、改造动作未作为新建量删除；负值保留原值参与所属组求和，无静默截零。

|门禁|观测|阈值|判定|
|---|---:|---:|---|
|全部 GW 资产拟删除合计|1.136306309440 GW|≤1 GW|STOP|
|燃气 CCS：删除 / 2050 装机|0.002534384242 / 0.351110918971 GW = 0.7218187%|≤0.1%|STOP|
|波浪能：删除 / 2050 装机|0.011349181817 / 0.011349181817 GW = 100%|≤0.1%|STOP|

共有 50,523 个正小量资产组、151,569 条对应 cohort（含同组选中的零值年份）。合计中发电与储能 0.638135708256 GW、接入与输电 0.498170601184 GW；二者的资产单位同为 GW，但总和**不是去重后的发电装机**。即使后续作者把总量门槛改为仅统计发电与储能，两个单技术门禁仍然失败，不能因此自行通过。

燃气 CCS 的分母为结果表中的全部已装容量，包含改造贡献；分子仅为满足删除规则的 `new_build`，没有将改造扣减。水电分母按站点型 `ror+reservoir` 统计，省级固定聚合容量没有对应可删 cohort。网络各技术比例门禁在已确认停止后未继续补齐。

另有 521 条负 `new_build` 浮点/数值尾差，合计 -0.000064421872 GW（约 -64.42 kW），单条最小值与负聚合组数见 JSON；本轮只披露，未判定其成因或擅自清零。

## 已执行范围与剩余工作

- A：已定位 `solution_export.py` / `solution_preservation.py`，未修改模型或 QC 源码；`relative_v1` 正式实现、离线评估器与完整回归尚未执行。
- B：三年各取回 17 个小文件并核对 SHA，16 个/年与 `result_manifest.json` 一致；manifest 自身无自引用，记录源端传输 SHA。共 48 个清单成员通过，3 个 manifest 通过传输 SHA。原 QC 初查符合任务书预期，但**尚未签发 acceptance_relative_v1.json，不宣称正式验收完成**。见相邻验收目录报告。
- C：云端输出每年约 5.3 GB，总计 15,956,401,851 bytes。固定机首次连接失败；用户要求重试后，127.0.0.1:22 转发已恢复并核实主机名 t550。目标盘总量 4,029,616,283,648 bytes、可用 1,481,126,653,952 bytes；即使三个 output 目录全部备份，按总容量估算可用比例仍约 36.36%，高于 30%。固定机的 paracloud-bscc-a8 别名无法解析，后续可采用本机流式中转。因 D2 停止，未传输备份或创建 backup_manifest。
- D：提前执行只读小量停止检查，已触发 D2。D1 的其余 headroom/超界/水力界、D2 派生状态、D3 1h 数值审计、D4 身份/白名单/24h 工程门禁均未执行。
- E：无新配置、profile、release、作业或 held Job ID；原云端 release 和已完成作业不变。无 Stage B、case3、后台监听，未访问凭据；未修改 SI modules 或在线 LaTeX。

## 输入、输出与复现

云端源：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260930_base2050_v9_t48_m750_tol1e4_v1/output_8760/`。完整三年清单与大小在相邻目录 `base_acceptance_relative_v1_20261012/collection_manifest.json`。原件的本地只读副本位于该目录 `evidence/<year>/`，保留本地，不全部混入 Git。源 cohort/metadata/manifest/容量表 SHA 写入 `state_structure_audit.json`。

```powershell
python supplementary_materials/reviews/base_acceptance_relative_v1_20261012/collect_evidence.py
python supplementary_materials/reviews/base_2060_launch_20261012/audit_cohort_cleanup.py
```

第二条命令完全离线。只写审计 JSON/CSV，不写 planning state；可用 `--source` 和 `--output-dir` 指定目录。`deletion_by_technology.csv` 是完整逐技术拟删量，`cohort_bins.csv` 是逐年份新建正 cohort 分箱；`deletion_candidates.csv` 保存全部 50,523 资产，保留本地。JSON 的 `by_technology` 可直接复查报告表。

验证：CSV 标准库逐组 `math.fsum` 与独立 pandas 分组计算资产个数一致，总量差 <1e-12 GW。未修改生产源码，未因只读审计运行全套模型求解测试；全套测试属于尚未完成的 A 阶段。

## 差异与精确下一步

为及早发现不允许继续的情况，在代码实现及备份前进行了只读 D2 预检查；没有将 A–E 未完成部分描述为通过。历史 handoff 的双向流重叠比例否决口径已被 10 月 12 日额外损耗判据取代，原归档与历史记录不改写。

建议作者/决策层明确：波浪能、燃气 CCS 的小技术容量是否保留（作为具名清理豁免），以及 1 GW 合计是否包含接入/输电资产。也可指定新的、更低 cohort 清理阈值并要求重新审计；当前授权下不能自行降低阈值、增加豁免或忽略超限。收到明确修订后先重新执行停止检查，随后完成 A/B/C 与 D/E 全部门禁，才可 held 提交。单独“放行”不对应任何现存 held 作业。

## 2026-10-12 16:54 英国：按第 6b 节复审通过，2060 构建出现新停止条件

本节追加纠正上文旧停止状态；上文及 `b4a3bfb` 原始证据不改写。当前 **STOP_AUTHOR_REVIEW_REQUIRED**，没有创建云端 release、没有 2060 held Job，没有调用 optimize。原 2050 状态保持字节不变；本地派生状态仅用于本次失败门禁，不可作为生产就绪包。

### 第 6b 节清理门禁

- 发电与储能正删除量 **0.638135708256 GW**；接入与输电 **0.498170601184 GW**，分别小于 1 GW。储能删除为零，保守计入第一组。
- 已补齐网络各技术的 2050 装机分母。装机 ≥1 GW 的全部比例检查通过；最大比例为 coalccs 的 **0.093959868795%**。波浪与 gasccs 按绝对量披露，不设比例否决。
- 整组删除 72,566 个资产组、217,698 条 cohort；其中正合计组 50,523 个、非正组 22,043 个。保留组 34 条负 new_build 置零，增加量 **6.640521466e-15 GW**。
- 删除后 bound-close 94 条风光 cohort，合计减少 **0.000181119526 GW（0.181120 MW）**。逐行原值、新值和原因记录在派生 metadata / `bound_closure_audit.json`。没有修改 retrofit_in/out 或非 GW cohort。
- 证据：`revision_6b/cleanup_gate.json`、`revision_6b/deletion_by_technology.csv`、`revision_6b/state_structure_audit.json`。旧版 `state_structure_audit.json` 保留原样。原始源状态 capsule 和派生状态的完整文件位于本地 `upstream_2050_source_capsule/`、`upstream_2050_prepared/`；不将其大文件混入 Git。

### 新停止：删除新建 cohort 与历史改造扣减存在关联

使用真实 2060 输入、v9_a12、准备好的继承状态进行 1h build-only，在 `master.py` 原有负容量下界检查处停止：`Inherited thermal retrofit/build cohorts make a capacity floor negative`。这不是求解器 INFEASIBLE 结果，尚未生成完整 LP，因此无 IIS；未放松约束或执行修复性求解。

| 省份 | 技术 | 原继承下界 MW | 删除后下界 MW | 被删、仍在 2060 存续的新建量 MW |
|---|---|---:|---:|---:|
| 内蒙古（15） | bio | 0.076722754 | -0.245349727 | 0.322072481 |
| 黑龙江（23） | coal | 0.093171872 | -0.054065539 | 0.147237412 |
| 海南（46） | coal | 0.069473465 | -0.092907754 | 0.162381219 |
| 西藏（54） | gas | 0.121839627 | -0.047471271 | 0.169310898 |
| 合计 | | | **-0.439794291** | **0.801002010** |

原状态这四组下界均为非负，负下界由本次删除产生。例如内蒙古 bio 的 2060 外生容量 192 MW，而存续 retrofit_out 为 -192.245349727 MW；原来另有 0.322072481 MW 新建量支撑扣减，整组删除后剩余 -0.245349727 MW。其余三组 2060 外生容量为零，删除新建量后只剩负改造扣减。

证据：`revision_6b/thermal_floor_stop.json` 和 `thermal_floor_stop_cohorts.csv`。源 cohort SHA `976f18bebdf93fd974f1d29eadd880f0ebc20571002131fadf5714de0ab9b5af`；派生 cohort SHA `d7f2f7120c470d3b01d9d23999a8f9e99dbefe4e31217aa56e56ed1eaa598e3e`。

### A–E 交付与边界

- A：新增 `cispo_model/relative_acceptance.py`、只读离线 CLI，导出和保全路径异常隔离。严格 QC 原字段/status/hard_checks 不改，candidate 写出不因相对口径异常中断。边界、异常、历史 2050 对照与配置身份测试见 `tests/test_relative_acceptance.py`。首轮完整回归 427 项通过、跳过 1；补充 BarConvTol 记录与新配置身份测试后的最终回归 **429 项通过、跳过 1，157.837 秒**，日志为本地 `revision_6b/unittest_final.log`，摘要与 SHA 随 Git 保存。2060 的实际解导出联调仍待构建问题解决后的 24h 门禁。
- B：三年 relative_v1 全 PASS，补齐逐省峰荷、水库最大残差站点/活动库容、各重叠量、微小新建和历史 bound-close 披露。正式作者验收 JSON 已在本地生成；固定服务器已完成三年离线 assessment。正式验收 JSON 同步遇本机→T550 SSH banner 超时，状态见相邻目录 `acceptance_sync_status.json`，不能宣称此最后一步已完成。归档不改写。
- C：没有重复启动传输。最后成功快照为 **2026-10-12 15:34 UTC（英国16:34）**：三年 T1/T2 均 SHA VERIFIED，已核验 3,806,534,257 bytes；当时正在传输 2030 T3，约 54%。此后本机→T550 握手超时，最新进度和最终 backup_manifest 暂未核验；不能据此认定 T550→云端传输失败，也不能宣称全部备份完成。
- D1/D2：分组分箱、风光/水电 headroom 及 bound-close 已记录；v9_a12 只增加 A1/A2=1e-5 GW，A3=0。原有科学指纹随配置如实变化。D1 的改造上界/水力系数完整构建审计尚未完成。
- D3/D4：1h 构建在上述下界检查处失败；矩阵范围、与 2050 行列非零元对照、MPS 身份、A1/A2 白名单、24h 工程门禁均尚未完成，不能填 PASS。
- E：2060 profile 已准备，除 profile_id/description 外与 2050 逐键相同；尚未部署、冻结 release 或提交。继续保持仅授权 held 提交、作者“放行”前不可释放的边界。

### 复现、差异与作者需定案事项

使用项目 RL Python、Gurobi 13 overlay、`CISPO_DATA_ROOT` 与 `CISPO_WAVE_ROOT` 环境，按序运行 `audit_cleanup_6b.py`、`prepare_state_6b.py`、`build_gate.py --year 2060 --a12 --state-in .../upstream_2050_prepared/planning_state_candidate --output NEW_DIRECTORY`、`diagnose_thermal_floor.py`。准备脚本拒绝覆盖已有派生状态；诊断脚本只读。

第 6b 节没有授权删除/重配 retrofit_out，bound-close 只减少超上界，不解决负下界。直接将负下界裁零会掩盖容量账不闭合，因此不执行。建议最小具名例外：保留上述四组全部 new_build cohort（本次被删存续量合计 0.801002 MW），保留原 retrofit 配对与寿命结构，再重新执行所有清理及工程门禁。若作者坚持所有 <1 MW 新建组均删除，需另定 retrofit_out/retrofit_in 的成对回退规则；这会改变继承 CCS 容量，不在现有授权内。

下一步是作者/决策层明确这一改造关联规则后重新生成新版本派生状态，不能只凭“放行”跳过当前构建失败。Git 基准 `a4f039762392afdf55acb8476b412ec339100238`；本节及配套代码按安全明确清单提交，不带 SI 会话改动。
