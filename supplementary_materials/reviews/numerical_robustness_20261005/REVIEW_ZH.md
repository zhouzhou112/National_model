# 数值稳健性隔离验证：最终报告（2026-10-06）

**最终状态（英国22:14）：授权验证已执行完毕，A/B/C当前候选均否决；自动监听按用户要求停用。** Cfull已OPTIMAL/134轮，但目标相对参考差`7.868230489839585e-7 > 1e-7`，744h目标等价性门槛未通过，QC仍HARD_FAIL；默认及AggFill5结构门槛的独立否决保留。14份终态小文件全部SHA通过，详见5.5。以下带日期的阶段状态为历史记录，不能视为仍在运行或仍需恢复转发。

**最新状态（2026-10-06英国22:10）：外部转发中断，Cfull终态尚未取证。** 本轮一次SSH探测返回Connection refused，本机22端口无监听；最后已核验状态仍为下述17:25快照，不推断远端已完成或已停止。按用户跟进规则，自动检查`automation`已PAUSED，等待恢复原有127.0.0.1:22转发；没有停止/重提远端队列。证据`server_evidence/status_20261006T2110Z.txt`。任务1已结案，A/B/C晋级否决不变，剩余仅Cfull实际终态参数/目标/轨迹/QC核验与最终收尾。

状态：**A/B及C结构晋级均已否决；C完整744h目标等价性仍在运行，任务未完成。** 2026-10-06英国17:25：AggFill=5唯一一次双侧重试已完成，presolve结构仍完全相同，C当前分段不获2160h晋级资格。Cfull已于16:19:12 UTC由原补验队列自动启动，solver670416，本轮观测仍在presolve；实际构建配置/输入/源码身份已核验。原云端4844528未修改、停止或重提；本任务没有提交云作业，可选步骤0未做。

## 1. 当前逐项判定

连接中断历史（2026-10-05英国22:57，**已过时，保留追溯**）：当时21:55UTC SSH在banner exchange超时，最后成功证据为21:26UTC，自动跟进曾PAUSED，只暂停检查，未停止或重提远端solver/suite。**2026-10-06转发与跟进已恢复，Aon取证缺口已补齐**；当前进程及新证据以本报告开头和5.4为准，不把历史PAUSED当作当前状态。

- **A：否决当前阈值组合直接进入情景建模入口。** 24h 未清零位置的容量决策变动最大 `0.00016583682648540254 GW`，已经违反固定容量门槛；744h 157→162轮，两侧均无>=10倍残差跳升，但轮数增加3.18%，不满足固定稳健性标准。A_on完整配置/Factor日志已于10月6日补齐，身份差异仅指定A1/A2阈值及关闭的A3显式零；两侧QC均HARD_FAIL，不断言精确最优物理容量必然改变。A3仅完成独立代码/机制测试，未重跑已归档年度。
- **B：否决 `BarHomogeneous=1` 进入当前情景建模入口。** 24h物理LP相同，但744h轮数142→265（+86.62%）、总runtime增加134.63%，两侧均无>=10倍残差跳升，未满足固定稳健性标准；Factor/Dense不变，两侧QC均HARD_FAIL。
- **C：否决当前 `block_hours=730` 分段进入2160h+晋级。** 默认与AggFill=5唯一重试的off/on presolved结构分别完全相同，均未满足分段保留门槛；Factor也没有差异。24h精确消元等价性通过，完整744h目标相对差7.86823e-7未过1e-7门槛，终态证据已齐；不将该Cross0数值差解释为数学不等价。

没有将 24h、744h 或五轮日志外推为全年倍率、收敛保证或数值失败概率。

## 2. 范围、输入与可复现性

Git 基准为 `0a03cc452e95d158f36923ceb5210267979b6234` 加原有 dirty 和本轮隔离分支 `codex/validation-pair-20261005`。未删除原始数据、旧失败结果或历史交接。源文件按任务 1 冻结于 `../factor_pair_8760_20261005/frozen_local/`；固定机初始包和逐项 SHA 在 `server_code_v1.tar.gz`、`server_code_manifest.json`。

模型仍为连续 LP；决策变量是逐站/省容量、新建、改造和逐时调度，目标为原系统成本最小化。保留原电力平衡、备用、惯量、水库、SOC、输电、碳及生物质约束。窗口为连续小时、截断区间周期边界；年度流量按 `hours/8760` 缩放，年化投资/固定成本不缩放。空间分辨率及输入筛选不变。电力/容量 GW，电量 GWh，CO2 MtCO2，生物质 PJ。

- 基线配置：`config/optimization_numeric_dac_by_year_v9.json`；原 solver profile `barrier_stagea_numeric_repaired_v1_threads48.json`。
- A 输入：2040，起点 2880；作者指定的 `upstream_2030_bound_closed/planning_state_candidate`。完整 10 个上游文件取回并逐项校验远端 SHA，见 `upstream_remote_sha256.txt`、`upstream_transfer_verification.json`。来源仍为未接受候选，`source_qc_status=HARD_FAIL`；不能升级为科学通过状态。
- B/C 输入：2030 Base，从共同 2025 边界，起点 2880。
- 本地 24h 等价性：Gurobi 13.0.2，Seed 0，8 线程，NF2，**Cross2/1e-8**；这是较严格的等价性检查，不能冒充生产 Cross0/1e-4 稳健性结果。
- 固定机 744h：同机 Gurobi 13.0.2，Seed 0，12 线程，NF2，Cross0/1e-4，72 GB `SoftMemLimit`，无求解时间限制。内存上限是配对共同的工程保护，与无限内存生产 profile 的差异显式保留。
- 输入表复用 10 月 2 日既有传输包：SHA `c5b60a30756b46ae070fdf70f4f222c90e4aab352ccb678e040f70e1f4679a5d`；65 个数据文件与当前本地逐项相同，见 `server_data_reuse_check.json`。大时序使用固定机既有 CF、水文、波浪目录，没有复制凭据。

## 3. 实现与任务书差异

| 项目 | 实际实现与差异 |
|---|---|
| A1 | 新键 `numerics.hydro_capacity_headroom_zero_gw`，默认 0，验证范围 `[0,1e-4] GW`；仅被命中水电站 UB 收紧至 floor，其他 UB 保留原浮点值，逐站审计 |
| A2 | 新键 `numerics.retrofit_upper_zero_gw`，默认 0；仅 `0<UB<threshold` 置零并记录原值 |
| A3 | 新键 `numerics.inherited_floor_overrun_clip_gw`，默认 0；在已有 upper 的模型构建入口调用 `planning_state.py` 助手，GW 超限不超过阈值可截断，较大超限仍拒绝。`active_adjustment` 自身没有 upper，不能在那里凭空截断 |
| A3 归档保护 | 不改原 cohort；重复导入从原始 cohort 重新检查，不累积截断。VRE/wave/hydro/nuclear/storage 的有限 GW 界使用共同检查；无有限界及非 GW 变量不套用该阈值 |
| B | `config.py`/`diagnostics.py` 原本已经支持 `bar_homogeneous` 及参数回读；新增 opt-in profile，numerics 除 `bar_homogeneous:1` 外与原 48 线程 profile 逐项一致。另把 `direct_nonbasic_scientific_acceptance` 身份元数据设为 false：新诊断 ID 不在 canonical 生产白名单，复制 true 会使真实 runner 拒绝且与 TEST_ONLY 描述矛盾；没有扩展生产白名单或授予科学接受资格 |
| C 稠密行位置 | 任务书列出的 `master.py` 年度碳/生物质/CO2 source 行已经引用年度聚合变量，真正逐时稠密项在 `monolithic.py` emissions/captured/biomass accounting；在这些源求和处分块，未对稀疏终端预算增加无效层 |
| C 单位 | 电量辅助变量 `_gwh`，净排放/捕集 `_mtco2`，生物质 `_pj`；不照字面把所有物理量误命名为 GWh |
| C 常数 | 首轮逐块相加常数导致 RHS `2.2737367544323206e-13` 浮点差，严格比较拒绝。最终把常数保留在原年度行、按旧顺序求和，只分块变量项，最终 exact PASS，未放宽容差 |
| C 参数 | 实际 Gurobi `AggFill=-1`（automatic），不是任务书所述固定默认 10；若 744h 分段被 presolve 合回，按授权追加 AggFill=5 的双侧同参五轮重试 |
| 任务书 5b | 实际文件没有 5b；用户另行明确授权不可用时本地缩窗。但本轮固定机转发可达并满足初始门禁，故实际安排 744h，没有用本地短窗冒充其结论 |

新增配置全部 opt-in；A 的非零阈值进入科学指纹。默认关闭及显式零不改变 Base 指纹。C 的定义、真实单位、对偶映射和退化情形说明已追加 `MODEL_IO_CONTRACT.md`。

真实入口补证已完成，见 `real_runner_entry_audit.json`：A 与 C 分别通过 `scripts/run_cispo_2030_full_year.py` 的实际 1h 全国构建、原模型归档和 `build_report.json` 写出，两个 opt-in 审计块完整落盘，均未调用 optimize、没有 planning_state 输出。B 使用同一真实 CLI/输入加载/参数应用/写出流程，仅把 builder 替换成两行真实 Gurobi fixture，实际 `model.Params.BarHomogeneous=1`、科学接受 false，关闭的 A/C 审计字段不存在。B 第一轮入口已成功，但取证脚本误查只在 canonical 分支存在的参数文件；旧根保留，v2 改成实际 `model.Params` 回读后通过。没有把 B fixture 当全国构建或优化证据。

## 4. 关闭回归及等价性证据

### 4.1 关闭时 Base 不变

冻结旧 V9 与新代码 `explicit_off24`：原始 MPS **全字节相同**，完整原始解向量 `solution.npy` **全字节相同**，科学 SHA 均为 `937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0`。两者 77 Barrier 轮，目标均 `2112723.3677720963 million CNY`，QC PASS。

`disabled_regression.json` 列出逐文件检查。科学 CSV/NPZ 字节相同；三个 `.csv.gz` 仅容器时间头不同，解压内容字节相同；`solution_qc.json`/`dual_export_status.json` 含运行元数据差异，未把这些文件或日志/运行时间/绝对路径宣称为整目录字节相同。生产导出逻辑未因本轮改变。

### 4.2 24h 隔离配对

| 配对 | 目标相对差 | 物理 LP 比较 | Barrier 轮数 | 最终 QC | 严格门槛 |
|---|---:|---|---|---|---|
| A2040 off / A1+A2 on | `1.6290758e-12` | 仅 67 个审计界变化；A/RHS/LB/目标/sense exact | 131 / 135 | PASS / PASS | 容量决策一致性 FAIL |
| B2030 off / homogeneous | `1.5428565e-15` | A/RHS/LB/UB/目标/sense exact | 77 / 84 | PASS / PASS | 24h 等价性 PASS；744h 待判 |
| C2030 off / split v2 | `4.4081615e-16` | 消去 2148 个定义变量后全部 exact | 77 / 77 | PASS / PASS | 24h 等价性 PASS；744h 待判 |

C24 用 `block_hours=6`，专门覆盖四块与分段机制；生产候选/744h 使用 730。独立消元检查同时要求辅助定义块矩阵为单位阵、目标系数为零、UB 无限；LB 必须自由，或能从原变量界证明该块和非负。不能通过直接删除一个额外物理界伪造等价。

本地局部运行与项目测试共享主机，表中运行时间和每轮时间仅作为原始记录，**不据此作受控提速结论**。完整数值见 `paired_evidence.csv`；各根有 `gurobi.log`、`barrier.jsonl`、`barrier_trajectory.csv`、`result.json`、`build_report.json`、MPS/矩阵/解及物理导出。

### 4.3 A 的界与容量审核

A1/A2 测试值各 `1e-6 GW`。33 个水电站清除总 headroom `4.6925323645991696e-6 GW`（4.692532 kW），水电容量/新建成对 66 列，另 1 个改造尾差列；没有把这项近似写成严格可行域等价。

原 `tiny_bound_audit_20261004/audit_bounds.py` 对新 MPS 实算：

| 窗口 | `0<UB−LB<1e-6` 全变量 | 同阈值 GW 变量 | 解释 |
|---|---:|---:|---|
| 2040 / 1h / A on | 465 | 0 | 465 个均 `co2_ship_mt`，是小时窗口年度预算缩放产生的 MtCO2 界；不能套 GW 阈值，更不能为了零计数删物理流量 |
| 2040 / 24h / A on | 0 | 0 | 原审计脚本确认，全变量零命中 |

原审计结果在 `A2040_on1_capacity_v2/audit_bounds/` 与 `A2040_on24_capacity_v2/audit_bounds/`。1h/24h 物理比较为 `A_1h_capacity_physical_lp_diff.json`、`A_24h_capacity_physical_lp_diff.json`。

分析器已进一步加固，保留上述旧 JSON，正式复核引用 `A_1h_physical_lp_diff_audit_verified.json`、`A_24h_physical_lp_diff_audit_verified.json`、`B_24h_physical_lp_diff_audit_verified.json`、`C_24h_v2_physical_lp_diff_audit_verified.json`。A 白名单从 candidate `build_report.numerical_robustness_audit` 的逐站 `site_rows/removed_gw` 独立导出，水电 cap/new 双列及按列表顺序定位的 retrofit pair 逐值核对原/新界，禁止从观察到的界差反推豁免。B/C 无 A 审计时白名单为空。新增机制负例确认未审计的小界变化被拒绝。四项重分析均 PASS，没有重求解、没有改变 LP 或解。

但正式 24h 输出中出现：

| 未被清零的决策 | off GW | on GW | 差 GW |
|---|---:|---:|---:|
| `thermal_new_gw[13,8]` | 10.213267085370660 | 10.213101248544175 | −0.000165836826485 |
| `thermal_new_gw[13,9]` | 0 | 0.000165836826485 | +0.000165836826485 |
| `thermal_retrofit_to_ccs_gw[13,4]` | 0.000165836826485 | 0 | −0.000165836826485 |

这些表现为新增生物质、BECCS 新增与改造之间的路径重分配，接近相同目标/总容量并不能自动豁免固定门槛。因此记录为当前晋级否决，保留代码关闭。见 `A_capacity_decision_gate.json`、`A_capacity_decision_differences_gt1e8.csv`；检查显示阈值 `1e-8 GW` 仅用于报告过滤，实际最大差远大于 `1e-6 GW`，没有用过滤掩盖失败。

A3 首轮与 A1/A2 一起启用时，另截断 84 个 VRE 浮点越界，总 `4.376707329889484e-15 GW`，造成 RHS/LB/UB 微小差，完整失败证据保留于 `A2040_on1`、`A2040_on24`、`A_1h_physical_lp_diff.json`，未进入正式 A1/A2 配对表。按任务书“A3 仅代码与测试”，随后隔离了该开关；A3 开关关闭/重复导入/超过阈值拒绝由独立测试覆盖。

## 5. 固定服务器 744h 当前状态

SSH 别名原默认 BindAddress 不通；使用已配置转发 `HostName=127.0.0.1`、`BindAddress=127.0.0.1`、22 端口、BatchMode 可达 `t550`。初始门禁可用 `105669423104 bytes`（约 98.4 GiB），无其他可见 solver；每个新 case 前重新检查至少 90 GiB 和单求解器，使用 `flock` 避免本套件重入。

隔离根：`/home/zz2/National_model_server/probe_outputs/numerical_robustness_20261005`。原suite PID `185795/185796` 已自然结束，六项均rc0，未重启。2026-10-06 15:51:12 UTC新建C有限补验队列通过门禁（可用 `107037192192 bytes`、其他solver为空），flock PID `639732`、协调器 `639733`、首个solver `639735`；每项再次核验至少90GiB/独占求解器，并记录实际源码SHA。新协调器不改原repo或旧suite。

| 744h 项目 | 当前状态 | 还需证据 |
|---|---|---|
| A off / on（2040） | 两侧OPTIMAL、QC HARD_FAIL；157→162轮，否决 | 证据已齐；保留24h容量门槛独立否决 |
| B off / on（2030） | 两侧OPTIMAL、QC HARD_FAIL；142→265轮，否决 | 证据已齐 |
| C off / on 五轮（2030） | 默认及AggFill=5唯一重试均完成；结构无存续，否决晋级 | 结构/Factor/逐轮成本证据已齐 |
| C full solve（2030） | solver670416运行中，构建身份已验 | C on默认AggFill−1跑至终态，与B off同参作目标等价性参考 |

### 5.1 A_off744 单侧终态证据（英国 20:28 追加）

新快照 `server_evidence/20261005T1926Z/` 保存完整 A_off 原始目录、console `/usr/bin/time -v`、两侧 gate，以及本轮进程/suite/log 摘录。**56 个原始文件、61506064 字节逐文件远端 SHA256 与本地一致**，见 `remote_sha256.txt`、`transfer_verification.json`。包括参数/配置、科学与输入身份、逐轮 JSONL/CSV、原始 solver log 和完整物理导出；没有大型原模型或解向量传输。派生分析单独写入 `A_off744_statistics.json`、`paired_evidence.csv`、`A_off744_qc_failures.json`、`A_off744_resource_usage.json`，原始文件保持不变。

| A_off744 指标 | 原始证据/值 |
|---|---|
| 终态 / 解数 / 科学用途 | OPTIMAL / 1 / TEST_ONLY，production_result=false |
| 目标 | `2874720.3002322502 million CNY` |
| Barrier 轮数 / solver runtime | 157 / `6448.669574975967 s` |
| 迭代 2 起平均相邻回调耗时 | `38.82588423062594 s/轮` |
| 残差单步回升 >=10 倍 | **0 次**；逐项检查 PInf、DInf、Compl，见 `A_off744/trajectory_diagnostics.json` |
| 轨迹完整性 | CSV/JSONL 各158条，iteration 0..157 连续且无重复，Runtime/Work 均不倒退；PInf/DInf/Compl 的“0 后转正”事件为0，见 `A_off744_trajectory_integrity.json` |
| Presolved rows / cols / nnz | 3254362 / 3067759 / 36429985 |
| Dense cols / Factor NZ / Factor Ops | 6444 / `8.601e8` / `5.588e12` |
| 参数实际回读 | Method2、Threads12、Cross0、SolutionTarget1、BarConvTol1e-4、NF2、BarHomogeneous−1、AggFill−1、Seed0 |
| 原生约束 / 界最大违反 | `7.134770794436918e-5` / `5.136509106939968e-6`（原模型混合单位，不能统一当 GW） |
| 整进程 wall / MaxRSS / swaps / rc | 1:54:04 / 21232208 KiB（约20.25 GiB）/ 0 / 0 |
| 物理 QC | **HARD_FAIL**，三个 hard check 失败 |

QC 失败明细：波浪可用出力违反 `3.4682468357708334e-5 GW > 1e-5 GW`；水库续接水量残差 `63.25561703722042 m³ > 1 m³`；省际双向流检查不通过（35712 edge-hours，反向电量 `63.92706374225972 GWh`，额外网损 `1.5544075522517158 GWh`，最大反向占线路容量比 `0.31844734393630575`，完整观察值/门槛见 QC JSON）。没有放宽门槛或把 OPTIMAL 等同科学通过。上述为20:28时的单侧记录；22:26终态配对补充如下。

### 5.2 A 终态配对与部分传输记录（英国 22:26 追加）

`server_evidence/20261005T2126Z/` 已保存远端 A_on 全部原文件 SHA 清单和 B_off 启动门禁/进程摘录。取回期间转发失联，后续小文件重试也在 SSH banner exchange 超时；只结束本机停滞的 scp，没有对服务器/suite/solver 发信号。`transfer_verification.json` 明确区分 **31 个已取文件 SHA 一致、1 个 partial（reservoir_dispatch.npz 为0字节）、24 个未取文件**，不把本快照标为完整。result、完整轨迹 CSV、build_report、物理 QC 已核验；`gurobi.log`、`effective_config.json`、`scientific_identity.json`、`model_config_snapshot.json`、`input_manifest.csv`、JSONL及time console尚待补取。远端原件保留。

| A 的744h配对指标 | off | on |
|---|---:|---:|
| Gurobi终态 / QC | OPTIMAL / HARD_FAIL | OPTIMAL / HARD_FAIL |
| 轮数 | 157 | 162（+3.1847%） |
| solver runtime (s) | 6448.669574975967 | 6531.959604978561 |
| iteration2起平均相邻回调耗时 (s/轮) | 38.82588423062594 | 38.135633794417295 |
| PInf/DInf/Compl >=10倍跳升 | 0 | 0 |
| 连续轨迹 / 重复 / 时间和work倒退 / 0后转正 | 0..157 / 0 / 0 / 0 | 0..162 / 0 / 0 / 0 |
| 目标 (million CNY) | 2874720.3002322502 | 2874696.1442373097 |
| Dense cols / Factor NZ / Factor Ops | 6444 / 8.601e8 / 5.588e12 | 原日志补取后填写 |

两侧 result 中10项参数实际回读逐项相同（Method、Threads、Crossover、SolutionTarget、BarConvTol、NumericFocus、BarHomogeneous、AggFill、BarIterLimit、Seed）；ScaleFlag、Aggregate等尚需原log/全config补证。输入清单文件远端SHA均为 `da36913d542ace44d55a2876828920d2e9a4af6c3e8aeaa890f2ad8f7704d73a`，与已验证的off文件一致。完整effective_config和科学身份文件SHA按预期不同，但本轮尚未取得on内容，不能仅凭SHA差就宣称变化严格只有A开关；须在连接恢复后补逐键白名单核验。另有已记录的C禁用模块修复源码时间差，继续保留5节说明，不能把整体源包称为字节一致。

目标相对差 `8.402902688862481e-6` 作为 Cross0/1e-4 终态数值差报告；两侧 QC 未通过，不能把它直接解释为物理 LP 不等价或精确最优解改变。on的三个QC失败与off同类：波浪违反 `3.368803976540414e-5 GW`、水库残差 `75.79915969024432 m³`、省际双向流35712 edge-hours/反向电量 `50.808687822772626 GWh`/额外损耗 `1.231540498021815 GWh`。

固定规则下，观测轮数增加且没有满足至少10%减少，**A当前阈值组合不晋级**；24h容量门槛否决仍是独立成立的理由。较短的单轮时间不能推翻以稳健性为主的判据，且本轮Factor/完整身份取证未齐，不提前给成本晋级判断。全部派生值见 `A_pair_partial_analysis.json`、`A_on744_trajectory_integrity.json`；后续只补证，不覆盖此次部分传输和先前失败记录。

17:19:45 UTC，在 A_off744 已加载代码、C 尚未启用时，仅更换了 C 常数处理模块，前版保留在初始包，后版 `annual_dense_split.py` SHA 为 `0623b45eb962579e140b07239377ee2916293b43426003df09d42448662b66e4`，见 `server_C_constant_fix.log`。A off/on 的整体源包因此不能宣称逐字相同；该模块关闭分支仍原样立即返回 `sum_block(slice(None))`，A 不启用 C。C 两侧必须使用同一最终版本。没有对运行中求解器发信号或更改参数。

本机在英国约 18:23 蓝屏重启，最后一次全套测试被中断。固定机 suite 为独立进程，之后仍存活且迭代连续；**未因本机重启而重复提交或启动第二个 suite**。本地计算曾暂停；用户后续明确授权继续串行测试，真实入口补证与最终回归均在独占本机计算窗口执行。

### 5.3 转发恢复后补证、B正式判定和C追加验证（2026-10-06）

新快照 `server_evidence/20261006T1549Z/` 包含原六项case的97个必要小文件：原始solver日志、console/time、gate、参数/配置/身份、输入manifest、CSV/JSONL轨迹、QC及原suite终态。归档337403字节，SHA `85a63afdb8633c4a9f8a295de913f729350192be05a0348f8627c60f297fd178`，归档及97个文件逐项校验全通过；没有再次下载大型dispatch表。旧partial快照和网络失败记录保留，**A的日志/全配置/Factor/time证据缺口现已补齐**。

`pair_identity.json` 证明每项off/on输入manifest字节相同：A effective_config仅新增水电/改造阈值各1e-6和关闭A3的显式0；B仅 `bar_homogeneous=1`，实参仅BarHomogeneous−1→1；C仅启用annual_dense_row_split、block730，数值参数相同。当前远端源码相对初始包只存在前述C常数修复，修复发生在B与C运行之前；没有因后续本地B身份元数据纠正而改变正在运行的远端包。

A成本补证：Dense6444→6411，FactorNZ `8.601e8→8.259e8`，Ops `5.588e12→5.140e12`；每轮耗时仅下降1.78%，不推翻轮数增加和24h容量门槛否决。A所有缺失原件已补取并验证，5.2仍保留为当时部分传输历史。

| B / 2030 / start2880 / 744h | 默认 | BarHomogeneous=1 |
|---|---:|---:|
| 状态 / QC | OPTIMAL / HARD_FAIL | OPTIMAL / HARD_FAIL |
| Barrier轮数 | 142 | 265（+86.62%） |
| solver runtime (s) | 5105.366325139999 | 11978.510196208954（+134.63%） |
| 第2轮起平均相邻回调耗时 (s/轮) | 33.416009062570886 | 43.88992733756701（+31.34%） |
| >=10倍残差跳升 / 0后转正 | 0 / 0 | 0 / 0 |
| 轨迹连续性 | 0..142，无重复/Runtime或Work倒退 | 0..265，无重复/Runtime或Work倒退 |
| 目标 (million CNY) | 2313582.8385150842 | 2313490.91155216 |
| Presolved rows / cols / nnz | 3235681 / 3061348 / 35969902 | 相同 |
| Dense / Factor NZ / Factor Ops | 6627 / 8.416e8 / 5.354e12 | 相同 |
| 进程wall / MaxRSS | 1:31:13 / 23522576 KiB | 3:25:44 / 23055064 KiB |

B目标相对差 `3.9733594749168745e-5`，是Cross0/1e-4终态数值差，不直接称物理LP不等价。off的QC失败为省际双向流和水库续接残差（23.6581m³）；on另有power_balance、reservoir_energy、reservoir_active_storage、carbon失败，水库续接残差1332.6796m³。原JSON保留每项值和阈值。按预定规则，齐次轮数明显增加、原基线零跳升没有改善为更低跳升数，**否决当前BarHomogeneous=1候选**；不作全年倍率或NUMERIC风险概率外推。

C首轮五轮off/on均status7（ITERATION_LIMIT）、无解，不能作为744h目标等价性证据。两侧presolved行/列/nnz、Dense、Factor均与B表结构数完全相同，说明分段被合回；第2–5轮平均耗时29.13366848/28.19115877秒，单次短测不赋予晋级。按任务书只追加一次AggFill=5双侧重试，两个case保持其余参数相同。

新有限协调器 `server_c_followup_20261006.py` 于15:51:12 UTC通过门禁启动（flock639732、协调器639733，第一solver639735），顺序为 `C_off744_factor_aggfill5` → `C_on744_factor_aggfill5` → `C_on744_full`。每次启动再次核验90GiB与独占solver并记源码SHA，原模型源码/旧运行包不改。Cfull采用默认AggFill−1与B_off744数值同参；AggFill5两侧仅用于presolve结构重试，不把不同AggFill的解当目标配对。

`C_full_reference_preflight.json` 已证明，现有Cfactor配置去除C formulation、把BarIterLimit从5改回原full默认后，与B_off744配置逐键完全一致，输入manifest字节相同。实际Cfull构建/终态后仍须再次核对其effective_config、input_manifest、实参数与源码SHA，再比较目标相对差<=1e-7。Boff仅复用为工程求解目标参考，HARD_FAIL身份不会因此升级为科学接受。统计/轨迹完整性/身份/资源与QC派生证据见同快照 `statistics.json`、`paired_evidence.csv`、`pair_identity.json`、`qc_and_resource_summary.json`。

### 5.4 AggFill=5重试终态与Cfull运行身份（2026-10-06英国17:25）

`server_evidence/20261006T1626Z/` 保存41个必要小文件，归档93503字节、SHA `e800c89ef6b6a95c3648056c1816518882c6250f8e2240c4d359d4191fa4e4e4`，归档及全部文件SHA一致。包含两侧AggFill5终态和Cfull运行中快照；manifest明确标识Cfull文件为在跑快照，不把日志截断当终态。原输出不改写。

| C / AggFill=5 / 744h五轮 | off | on |
|---|---:|---:|
| status / BarIterCount / 解数 | 7 / 5 / 0 | 7 / 5 / 0 |
| Presolved rows / cols / nnz | 3243048 / 3064635 / 35878945 | 完全相同 |
| Dense / Factor NZ / Factor Ops | 6675 / 8.385e8 / 5.495e12 | 完全相同 |
| solver runtime (s) | 505.9852180480957 | 503.2991750240326 |
| 第2–5轮平均相邻回调耗时 (s/轮) | 29.232561290264115 | 28.577638745307922 |

两侧输入manifest字节相同、数值配置/实参相同，仅C formulation启用不同。AggFill5下分段仍未形成预期presolved增量，**不满足任务书结构存续晋级门槛，否决当前C进入2160h+**；约2.24%的短测单轮时间差不改变判定。没有再次更改参数或追加第二次重试。

Cfull由同一协调器自动启动：16:19:12 UTC门禁可用 `107711418368 bytes`，其他solver为空；solver670416，16:25:34 UTC进程6m21s，RSS8711012 KiB，处于presolve。其实际 `effective_config.json` 与B_off744逐键对比仅C formulation不同，`input_manifest.csv`字节完全相同，三个新case gate的全部源码SHA与15:49已核快照一致；详见 `identity_verification.json`。这一结果将预核验推进到真实构建身份核验。终态仍需检查实际回读参数、QC和目标相对差<=1e-7；不因结构否决而伪造目标等价性已通过，也不停止已授权在跑求解。

### 5.5 C完整744h终态与最终判定（2026-10-06英国22:14）

用户恢复22端口后，本次只读取原队列，无启动/停止/重提。`C_followup_status.json`三项均rc0；原flock/coordinator/solver进程已消失。`server_evidence/20261006T2114Z/`保存14份终态原件，全部按远端同一次读取的bytes/SHA核验；原始log、CSV/JSONL、QC、配置、输入、环境、gate和time记录齐全。

| 2030/start2880/744h，Cross0/1e-4/NF2/12线程 | B_off744复用参考 | C_on744_full |
|---|---:|---:|
| solver状态 / QC | OPTIMAL / HARD_FAIL | OPTIMAL / HARD_FAIL |
| Barrier轮数 | 142 | 134 |
| Runtime(s) / Work | 5105.36632514 / 8152.73287161 | 4848.09546709 / 7694.50628128 |
| 第2轮起平均相邻回调秒数 | 33.41600906 | 33.52334139 |
| 目标(million CNY) | 2313582.8385150842 | 2313584.6588953873 |
| >=10倍残差跳升 / 零后转正 | 0 / 0 | 0 / 0 |
| 连续轨迹条数 | 143（0..142） | 135（0..134） |
| Presolved行/列/nnz | 3235681 / 3061348 / 35969902 | 完全相同 |
| Dense / Factor NZ / Factor Ops | 6627 / 8.416e8 / 5.354e12 | 完全相同 |
| 进程wall / MaxRSS(KiB) | 1:31:13 / 23522576 | 1:27:02 / 22921876 |

两侧10项终态参数回读完全一致，effective_config仅`formulation.annual_dense_row_split`不同，input_manifest逐字节相同。C首次补验gate、Cfull gate与本次终态源码SHA完全一致。**源码身份局限**：原Boff gate未记录源SHA；其源码依据为初始冻结包、唯一C常数修复早于Boff启动的日志及后续manifest，不能称为Boff已加载模块的同期逐SHA证明。复用参考的输入/配置/实际参数核验严格成立，源身份按上述可得证据和局限披露，不掩盖历史缺项。本次分析脚本初版读取不存在的Boff gate源SHA字段报KeyError；已改为显式报告缺项，没有补造该字段或重跑参考。

目标差为1.8203803030773997 million CNY，按参考绝对目标归一化得`7.868230489839585e-7`，超过固定`1e-7`。因此目标门槛未过；两侧Cross0/1e-4、QC均HARD_FAIL，不据此断言精确LP或最优物理解改变。两侧QC失败均为水库续接与省际双向流；C原约束违反9.60861253e-5、界违反3.90639357e-6。轮数虽减少5.63%且无跳升，不能覆盖结构存续和目标等价性门槛失败，亦不作全年时间/风险外推。

**一句话最终判定：否决当前C年度分段方案晋级，因默认与唯一AggFill5重试均未保留分段结构，且完整744h目标比较未过预定门槛。** 复算入口`python finalize_c_terminal.py server_evidence/20261006T2114Z`仅分析已存小文件，输出`final_comparison.json`；取证脚本`collect_c_terminal.py`只读远端，禁止将其误当求解入口。没有继续调参、2160h试验或生产情景。

## 6. 测试、运行方式与收尾

**收尾：下列“待运行/待连接”条目保留为阶段历史，已由5.5终态核验关闭。** 两报告、否决清单与handoff完成；本次351受测源SHA仍与412全套回归一致（`../validation_coordination_20261005/final_source_integrity_20261006.json`），只新增取证/分析脚本和文档，未重新求解或无理由重测。用户要求取消自动监听，`automation`保持PAUSED，不自动恢复。后续科学情景、2160h、修订阈值/容差均不在本轮执行范围。

- 2026-10-06英国22:10外部阻塞追加：恢复既有转发后，先只读检查原Cfull进程670416及`C_followup_status.json`，如已完成则取回终态小文件逐SHA核验、对照Boff目标和身份后收尾；不得重复启动原suite或C补验。自动检查已按指令暂停；此前运行状态段是历史快照。
- `tests/test_numerical_robustness_optin.py` 最新 7 项 PASS，日志 `unit_optin_entry_final.log`；包括关闭历史指纹、界审计、重复导入、超阈值拒绝、B 实际参数、C 有符号/常数顺序回归及未审计小界变化必须拒绝。
- 整合全套曾 410 项 PASS，但启动早于最终 C 常数修复；其后一次最终 411 项执行被蓝屏中断，此失败过程保留。用户明确授权恢复后，根代理独占本机单进程串行重跑：**最终 411 项 / 110.818 秒 / OK / rc0**，仅跳过 1 项 Windows 不适用的 Linux `/proc` 测试。`source_unchanged=true`，内存采样 RSS 峰 `1018630144 bytes`、系统可用最低 `15725244416 bytes`，保护未触发。日志/JSON/内存轨迹为 `../validation_coordination_20261005/unittest_verified_20261005T183454Z.log`、同名 `.json` 和 `_memory.jsonl`，日志 SHA `f2335935e2e62579f0bcbded12c3e5efbb2898bf0cfed4c59fe78133f517ea1b`。本次通过不覆盖或解释前次蓝屏成因。
- B profile 身份元数据纠正、真实入口补证和白名单机制负例后，重新串行运行最终全套：**412 项 / 112.906 秒 / OK / rc0 / skipped=1**，Gurobi 13.0.2，`source_unchanged_during_test=true`。日志为 `../validation_coordination_20261005/unittest_verified_20261005T185140Z.log`（SHA `bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79`），同名 JSON、`_started.json`、`_memory.jsonl` 保存环境白名单、前后源码 SHA 和内存轨迹；RSS 峰 `1031180288 bytes`、系统可用最低 `15548526592 bytes`，保护未触发。此前 `184739Z` 一次调用漏设 `CISPO_WAVE_ROOT` 导致 352 项中 8 项导入/数据定位错误，完整失败日志保留；纠正环境后才取得本次通过，未修改测试以掩盖环境错误。
- 重现短窗入口为 `run_probe.py`，对比为 `compare_probes.py`，汇总为 `summarize_results.py`。原测试目录禁止覆盖；复现必须选择新输出路径，并使用 Gurobi 13 运行时。完整回归从仓库根执行，显式设置 `PYTHONPATH=output/portfolio_runtime_gurobi13` 的绝对路径、`CISPO_DATA_ROOT=data` 的绝对路径、`CISPO_WAVE_ROOT=../wave_energy` 的绝对路径、`OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`、`PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`，再用 RL Python 执行 `python -m unittest discover -s tests -q`；内存留痕包装器为 `../validation_coordination_20261005/run_final_regression.py`。当前本地验证完成，不再启动额外计算。
- 固定机现有 `server_suite.py` 已串行排 A off/on → B off/on → C 五轮 off/on。仅观察它完成，不重复启动。每 case 原始日志/环境/输入/参数/轨迹保留在对应目录。
- 原suite自然完成，A/B终态证据已取齐并按固定规则否决；C默认与**off/on 都 AggFill=5**的唯一一次重试均已终态取证，结构门槛未通过，不再重复factor或重提旧suite。
- 继续观察已运行Cfull（670416）完成，核对相对目标差 `<=1e-7`、实际参数和QC，补齐工程等价性证据。C结构门槛已经否决，即使目标等价也不自动进入2160h；不得为观察进度重复启动。
- 最终冻结代码的完整回归已由根代理在本机串行完成；除非后续修复源代码，不无理由重跑。固定机所有求解完成后更新本报告、否决清单与主 `CODEX_HANDOFF.md`，追加而不覆盖历史；如必须新开本机测试，先协调串行执行。

可选旧 Thermal 极小区间云小作业未执行；没有以此项缺失推断跳升根因。

