# 框架 B（Base-frozen）实现与门禁记录

**当前状态：本地全部门禁和云端preflight通过；B2030作业5276670在旧许可检查失败，主模型未启动。失败记录已T550校验备份，下一步见第9节。**

日期：2026-10-26（英国 GMT）。候选实现提交：`ba7a23fdfe76a367ca72eb393daeddc334a9dc13`。源码起点：`db1a7b4498b7ed2d7b52672d379ca0e74a6cbbbb`。

**前轮停止记录（已由下方第 7 节作者修订和复核结论更新）：身份门禁 1 原逐时一致性要求未通过。** 当前为 opt-in 候选实现，未取得生产资格。没有 B 作业号，也没有全年峰值 RSS、每轮耗时或总轮数。两套已执行的 24h 结果均完整保全，不能将短窗性能外推到全年。

## 1. 授权和实现边界

依据作者任务书 `claude_workspace/tasks/TASK_base_frozen_B_20261026.md` 及本会话两次来源补充授权，摘要和任务书 SHA 见 `authorization.json`。作者口头补充优先：hydro spur 优先 X、缺失才回退 BarX；续接上游交叉恢复原 environment 路径、input manifest SHA、实际 upstream 与 metadata，Base 原件不改。2030 无上游。

新增 `cispo_model/frozen_capacity.py`、`scripts/extract_frozen_hydro_spur.py`、48 线程 Aggregate=0 profile、两组单元测试；runner 新增 `--frozen-capacity-from`、`--frozen-capacity-supplement`、`--frozen-parameters`，并将冻结来源、clip、源表 SHA 写入科学身份和 build report。保全流程新增容量身份检查阶段，失败质量标签不停止其他解数据保全。

冻结投资决策的 LB/UB；GW、GWh、MtCO2/year 分开审计。总容量由原会计等式决定。DAC 捕集量、全部逐时运行、柔性签约和信用仍自由。Base 源表用稳定键严格一对一连接，缺列、重复、非有限值、SHA 不符停止。除作者批准的 hydro spur 补表外，不推算缺失来源。2030 原配置电池/抽蓄能量由功率和时长决定，无独立 PHS 能量投资列；独立 PHS 模式另有注册入口。

显式 state、候选筛选、MGA、Stage B/热启动与冻结模式互斥。生产要求专用 profile、原模型归档与 Barrier 检查点。未来 2040–2060 恢复上游的逻辑已实现，但尚未以完整实际 release 做运行核验；不得据此提前排程。

## 2. Base 2030 冻结来源

原件位于 T550：
`/home/zz2/National_model_server/cloud_backup/20260914_base_v9_t48_m750_tol1e4_v3/output_8760`。

- 原 `result_manifest.json` SHA256：`af1e51f1c13d7bc41b997c1d4fafa8fee7efbffe40103d64b6bc5d79960dc342`。
- 原 MPS SHA256：`fa729325647ebde2d56c553397e02ef013ba09478cddc2f996f3250db14f6739`，4,048,048,342 bytes。
- 没有保全的 X 向量；采用已保全 BarX，SHA256：`c4fe9534de1b364f20d01739aed57289b8b6d7460e94fbd50ded5a494d935b90`。
- 同次 MPS 列解析核验 41,458,383 个变量的顺序；36,686 个 `vre_new_gw` 与原表逐项最大差 **0 GW**。
- 独立补表：上述 release 的 `frozen_capacity_B_20261026/hydro_spur_capacity.csv`，SHA256：`df2a242cf2f54934d3dea76acbeaa9ceaca09536d4a9a1ff47229decdc47d1be`。补表和 receipt 单独存放，原归档未改。
- 本机仅取回容量表和身份小文件，原 MPS/BarX 留 T550。源表逐项 manifest 验证见 `source_copy_receipt.json`；提取器命令、校验和结果见 `extract_2030.log`。

## 3. 已完成检查

验证环境为 T550 独立目录 `/home/zz2/National_model_server/base_frozen_B_validation_20261026`；使用现有 Gurobi 13.0.2 Python。复制后的源码清单、私有数据覆盖层与补丁 SHA 见 `t550_validation_payload_identity.json`、`t550_data_inventory.json`、`t550_validation_patch_0*.json`。未部署或修改任何生产 release。

| 检查 | 结果 |
|---|---|
| 默认关闭，旧/新 runner 的 1h MPS 解压后逐字节一致 | PASS，SHA `1cee854614792bb6bbe1c94192508cc578b60adacb5e40795e64ac598cd32f92` |
| 冻结 1h，12 类投资变量固定 | PASS，86,745 列，MPS `FX` 数量和值与审计完全一致 |
| 总容量与 Base 原表加 clip 修正 | PASS，最大差 2.84e-14 |
| GW clip | 110 列，合计 2.6415681231e-10 GW，单列最大 2.6414467271e-10 GW，均未触发阈值 |
| DAC MtCO2/year clip | 124 列、零 clip；未与 GW 相加 |
| 新增定向单元测试 | 13 tests，OK |
| 全套回归（最终候选源码） | 477 tests，159.655 秒，OK，无跳过；源码与本机逐文件 SHA 一致，见 `final_validation.json` |

默认关闭证据在 `evidence/default_off_identity.json`；冻结审计证据在 `evidence/frozen_1h_v2/`。原逐列审计及 MPS 均保留在 T550 同名完整运行目录。

## 4. 身份门禁 1：目标通过，逐时量不通过

两侧同一 Base 2030 冻结来源、同一 clip 后容量、同一 24h 窗，V9、Aggregate=0、Cross2、BarConvTol=1e-8、FeasibilityTol/OptimalityTol=1e-9、8 线程。8 线程仅为工程门禁；生产候选仍为作者要求的 48 线程。

| 项目 | 固定容量 Base | 零签约 B |
|---|---:|---:|
| 求解状态 | OPTIMAL | OPTIMAL |
| 目标值（模型单位 million CNY，短窗诊断口径） | 2684955.8057521186 | 2684955.805752121 |
| Barrier 轮数（仅短窗） | 62 | 62 |
| 求解器 Runtime（秒，仅短窗） | 14.0387 | 15.0759 |
| 保全状态 | COMPLETE | COMPLETE |
| 容量输出最大绝对差 | 2.84e-14 | 2.84e-14 |

目标相对差 **8.6716750851e-16 ≤ 1e-7**。但是共同变量中，风光出力最大差 **8.5702132881 GW**、省际正向潮流 **2.8086927514 GW**、储能放电 **0.0674837760 GW**、储能 SOC **0.0750482373 GWh**。水库有效蓄水最大差 8.7303916878 million m³，不能与 GW 混合比较。完整逐族差异在 `evidence/identity_gate_comparison.json`。

任务未给逐时容差具体数值，报告同时列出 1e-9、1e-6、1e-3 的超差计数；上述差异远超数值误差量级，未以自选容差将其放行。

**未重新优化的交叉检查：** 读取两套原 MPS，把另一解的共同变量代入，B 独有辅助变量保留零签约解值。两方向约束最大违反均 3.7169e-11、界最大违反 4.8743e-12，交叉目标分别等于原目标。证据见 `evidence/saved_solution_crosscheck.json`。这支持相同成本的退化多解解释；并不能代替任务书明定的逐时一致门禁。未加扰动目标、未选择性删变量、未放宽门禁。

**第二个待解决问题：** 两套 `solution_qc.json` 的严格 QC 均 PASS，但 `acceptance_profiles.relative_v1` 均为 ERROR，缺少 `barrier_primal_dual_metrics`。这是 Cross2/basic 结果进入现有 Barrier 专用评价分支的兼容性问题，不能称扩展验收正常生成。保留原 QC，不修改历史输出；后续须修复并重新验证。

## 5. 停止点和未完成项

- 身份门禁 1 未通过，因此没有执行开放柔性 B 的 24h 门禁 2。对照两侧容量 PASS 不能冒充门禁 2 已完成。
- 没有完成 2030 最终参数核准、生产 release 冻结、云端 preflight、sbatch 提交或 release。
- 没有生产峰值 RSS、迭代耗时、总轮数、终态、全年扩展验收或全年备份。两个短窗实验直接在 T550 执行并完整保全。
- 后续 2040/2050/2060 仍须作者确认线程数；既有 5201318、5207165 和 case3 2050 包均未触碰。

**待作者决定：** 是否将零签约门禁中的“逐时变量逐项相等”修订为“目标差 ≤1e-7、两侧可行，并对保存解做双向交叉可行性验证”，逐时差异作为退化披露。该建议有本次交叉证据支持，但尚未获得授权。即使修改该判据，也须先解决 Cross2 的 relative_v1 兼容性问题，再继续开放柔性 24h 门禁 2、参数核准和生产 preflight。

## 6. 敏感性入口与复现

`--frozen-parameters <JSON>` 只允许 `flexible_load`、`service_costs`、`contract_upper_fraction`、`weather` 四类根键。通过已有 V5 输入表切换参与率/舒适带，覆盖已有服务成本字段、折减系数、V2G 上限；关闭某项贡献用签约上限比例 0。气象入口支持 `weather_year`、`weather_source_years`、水文/月型、波浪来源及明确的 CF/HYDRO/WAVE/RAW_GRFR 数据目录，并进入覆盖 SHA/身份记录。新气象数据须另行生成并验收；不假造数据。负荷总量、投资成本、碳约束覆盖拒绝。除了零签约覆盖，其他敏感性入口未运行真实敏感性门禁或作业。

本次使用 `run_gate.py --mode old-default|default|frozen --hours 1` 和 `--mode base-control|zero --hours 24`；每次输出新目录，完整 argv/profile 与运行产物旁置。`run_t550_checks.py` 为前台有限命令，无定时器或后台监听。比较用 `compare_identity_gate.py`，交叉检查用 `crosscheck_saved_solutions.py`（不调用 optimize）。再次执行须使用新输出名，禁止覆盖本轮证据。

提交范围：本次源码/profile/tests、本文、少量门禁 JSON/来源 SHA/执行回执、交接与服务器记录。源表缓存、MPS、解向量、tar 包、原始大日志及其他作者稿件留原位置，不进入 Git。

## 7. 作者修订后的通过记录（2026-10-26 GMT）

作者明确修订门禁 1：目标相对差 ≤1e-7、双向交叉可行（约束/界 ≤1e-8）、交叉目标相等、成本分项相对差 ≤1e-7；逐时差异按退化披露。授权 SHA 见 `authorization_revision_2.json`。

旧成本 CSV 来自 BarX，而门禁保存基解为 X。此次在原模型同指纹/同列序检查通过后，仅重新构建表达式，按已保存 X 离线评价成本，不重新求解、不改原件；旁置于 `evidence/*_24h_Xcost/cost_from_X/`。全部成本项通过，最大相对差 **1.6352960585e-13**。Base 无柔性成本项，在 B 侧逐项核实为零并明确记录结构性缺项。变化列的 reduced cost 最大 **2.2898349883e-15**（Base）/ **1.4571677198e-15**（零签约 B）。这说明变化在零边际成本替代调度方向上；不把潮流正则化等直接目标系数误写为零。风光弃电分配、潮流路径、水电/储能与备用分配均逐族记录，见 `evidence/revised_identity_20261026/assessment.json`。身份门禁 1 **PASS**。

`relative_v1` 新增明确 basic contract 分支：无 Barrier 指标且合同要求基解，按 OPTIMAL 和原始约束违反、约束残差、界违反 ≤1e-8 评价，标注 `solver.mode=BASIC_CROSSOVER`。缺失/非有限指标失败，不允许缺指标的 Cross0 冒充基解；其余物理检查不变，原 Cross0 分支和输出保持原口径。基解 dual 元数据标为 BASIC_CROSSOVER_DUAL。另修复保全时基解的语义向量选择：basic 合同选 X/Pi，但仍保全 BarX/BarPi；默认及 Cross0 顺序不变。新增阈值、缺值、非最优、Cross0 防误判和向量选择测试。

开放柔性 **24h 门禁 2 PASS**：容量最大差 **2.8421709430e-14**，relative_v1 PASS/BASIC_CROSSOVER，原始约束违反 3.7169e-11、界违反 4.8946e-12；保全 COMPLETE，语义向量 X。短窗因年度签约成本权衡，目标与零签约解相等，不据此推断全年柔性价值。

2030 中央参数已复用 `scripts/verify_case3_parameters.py` 对真实加载数据核准 PASS；另比较 B 与已核准 case3 的 1h 原 MPS：变量/约束名、矩阵、RHS、目标、全部非投资列界完全相同，只改变投资界。证据 `evidence/parameters_2030/`。

最终全套回归 **480 tests / 161.365 秒 / OK / 无跳过**，368 个模型、配置、脚本与测试文件的本机/T550 LF SHA 对齐。门禁清单见 `FINAL_GATES_PASSED.json`。本节为本地门禁通过，云端冻结/preflight/提交与资源状态另行记录；后续三个年份仍等待作者线程确认。

## 8. 云端 preflight 参数冲突修复与 v2（2026-10-26 GMT）

v1 源码 `e2bb4fd` 已冻结，405源码/58输入与源容量 SHA 校验完成，但首次云端 preflight 被 CLI 拒绝：preflight-only 不允许 archive/export 写出参数，而冻结模式原验证器又要求二者。未提交任何 v1 作业；v1目录、包与失败日志完整保留，见 `deployment/`。

最小修复：仅 preflight-only 豁免写出参数；生产 solve 仍强制原MPS归档和 Barrier 检查点。补充单元测试确认只读 preflight 可以通过、缺保全参数的生产 solve 仍拒绝。T550真实全年配置 preflight PASS；最终全回归 **481 tests / 159.093秒 / OK / 无跳过**，368源码 LF SHA 对齐。模型构建/目标/约束/数值求解参数未改，不复用失败v1目录；新release后缀 **v2**，实际冻结/preflight/提交记录在 `deployment_v2/`。

## 9. B2030 实际提交、启动失败与保全（2026-10-26 19:39 GMT）

最终源码 `9f0a042`；release `20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2`。405源码/58输入冻结校验 PASS；release manifest SHA `153d78c95caff43b72ea2a164e7068ca81565c8c4be12d54e4c2420640b7e1b0`。云端真实 preflight PASS，sbatch test-only PASS。Job **5276670** held 后核验资源并按作者授权 release。

实际节点 **m4cg1603**，AllocTRES=cpu64/mem750G/node1/billing64、UNLIMITED、Requeue0/Restarts0，符合要求。英国时间19:39:55启动，19:39:59以FAILED/ExitCode1:0结束。runtime hash 全部通过；执行已越过 ≥700GiB 可用内存检查，但未到写出 smoke JSON 的位置，故没有精确启动内存数值。

计算节点 `gp.Env.start()` 报 **License 2847107 has expired**。部署沿用旧默认许可路径，是本次执行疏漏；既有记录明确已有10-20独立WLS路径，不应推断所有许可失效或要求作者重新提供凭据。已登记路径为 `/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic`，本轮没有读取其内容或重新验证有效性。

遵循失败停止规则，本轮没有再次提交。主模型未构建、output_8760不存在、没有Barrier迭代；因此**不能提供全年峰值RSS、每轮耗时或总轮数**。sacct 的 batch MaxRSS=0 不能当作真实模型峰值。启动失败日志、冻结包和全部身份元数据留存，见 `deployment_v2/startup_failure_summary.json`；T550启动失败备份另见 `startup_failure_backup.json`（不称完整解备份）。

下一动作：复用已登记WLS路径（仅引用路径，不读凭据），先做许可门禁；新建v3，不修改v1/v2，不重启5276670。新发布包须明确绑定该路径，并让启动资源检查在许可检查前先落盘。生产内核和科学门禁保持已验证版本；后续2040/2050/2060继续等待作者线程决定。5201318/5207165及case3 2050未干预，无后台监听。
