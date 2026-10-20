# Repository instructions for Codex

This repository implements the CISPO-style China power-system planning model. Research reproducibility, model rigor, maintainability and explainability take precedence over merely obtaining a runnable result.

## Mandatory handoff workflow

1. Before changing code, read `CODEX_HANDOFF.md`, `cispo_full_lp_model_spec.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`.
2. Treat the `Current validated snapshot` in `CODEX_HANDOFF.md` as the active handoff state. Verify drift-prone facts against Git and the server before relying on them.
3. After every material model, data, environment or server milestone:
   - update the current snapshot;
   - append a dated version entry to the handoff log;
   - record the Git commit, changed files, commands, outputs, validation evidence, unresolved issues and exact next action.
4. Never record passwords, SSH private-key contents, Gurobi activation keys or license-file contents. Paths, non-secret license metadata and SHA256 hashes are allowed.
5. Do not silently change model boundaries, units, temporal or spatial resolution, objectives, constraints, screening rules or data sources.
6. Use Chinese for research notes and handoff prose; keep file names, paths, variables, commands and formulas in English.

If chat context conflicts with committed files or verified outputs, stop and resolve the discrepancy explicitly. Do not overwrite historical handoff entries; append a correction and update the current snapshot.

## Git synchronization preference (2026-10-06)

用户要求尽量保持本地工程源码与GitHub同步。按`GIT_SYNC_POLICY_ZH.md`在任务收尾审查、测试、明确清单提交并推送安全范围；不把未审查稿件、实验大文件或凭据混入提交，不强推。`github`是GitHub，`origin`是固定服务器裸库。同步Git不授权更新正在运行的云端冻结包或启动新求解；远端工程部署独立核验。当前用户已取消自动监听，不建立后台自动提交/轮询服务。

## 作者决定：C2050 OOM 后以40线程重跑（2026-10-20）

作者明确授权C2050以40线程新建release并启动；Slurm维持64CPU/750G/billing64、UNLIMITED，Aggregate=0及其他数值/科学设置不变，复用已核验Base2040→R1状态与margin0.2清单。只对此次C2050重跑取代原48线程要求，不推广到case3其他作业。原48线程失败包、MPS与现存输出完整保留；不原地改冻结包、不建后台监听。40线程是否能通过排序峰值尚待实测，不能承诺后续内存固定400GiB。

## 作者决定：云端求解结束后的 T550 备份（2026-10-20）

每次确认云端生产求解结束，均须把结果备份到 T550，作为收尾必做项，不再逐次请求授权。沿用 T550 直连云端、单次自主拉取的流程；不建立定时监听，不更改运行中的冻结包。状态查询发现新终态时，在当次工作中核对备份并补齐缺项。

1. 先核对作业终态、导出/保全状态、已有备份 manifest 和活跃传输，避免重复启动。科学 QC 的 PASS/FAIL/HARD_FAIL 和作者是否采纳均不影响结果备份。
2. 完整备份包括全部 `output_8760`（解、BarX/BarPi、状态、QC、报告、原模型归档、日志）及明确列出的启动/身份元数据；保持相对路径。单独产生的验收/证书按来源 SHA 旁置，不改写原输出。不复制凭据或宣称这是含全部输入/环境的镜像。
3. 使用独立操作目录、互斥锁与可续传 rsync；不删除源、旧备份或部分传输。完整结果已备份且身份一致时复用；空间保持既定至少 30% 余量，空间不足或身份冲突时记录待办并报告，不静默省略原模型。
4. 目标逐文件校验 bytes/SHA256，复核源身份未变后生成 `backup_manifest.json`。只有全部层完成校验才报告“备份完成”；否则如实报告传输中、阻塞或部分保全。异常终止/导出不全时保留并整理现存文件另作部分备份，不伪称完整解备份。
5. 同步更新备份台账、交接与服务器记录，报告目标目录、规模、校验状态和剩余事项。连接恢复后先核对旧进程/状态再续传。入口和操作示例见 `SERVER_RUNBOOK.md` 的本日备份流程。

## 作者决定：验收精度与执行边界（2026-10-10）

以下规则由作者与 Claude（决策层）确定，Codex 按规则执行，不在任务中重新论证；提出异议时写入报告"差异"一节，不改变判定。

1. **Stage B 不执行。** 科学结果采用 Stage A（Barrier、Crossover=0、BarConvTol=1e-4）内点解。`FULL_YEAR_SOLVER_DECISION_20260817.md` 第 2 节"科学结果必须来自最终 basic solution"自本日起作废，见该文件 2026-10-10 条目。
2. **验收精度按科学精度而非机器精度定。** 物理 QC 采用相对口径（`acceptance_profile=relative_v1`，定义见 `claude_workspace/tasks/TASK_case3_launch_contract_20261010.md` 第 6 节）；严格绝对口径并行记录、不删除，但不再作为 HARD_FAIL 的依据。两口径同时写入 `solution_qc.json`。
3. **等价性门槛分档。** Cross2/1e-8 的对照用相对目标差 1e-7；Cross0/1e-4 的对照用 1e-5。退化 LP 不设逐变量一致性门槛，判据是目标相等且两侧可行。
4. **对偶筛选证书规则。** Lagrangian 上界相对目标 ≤1e-3 接受；≤1e-2 接受并披露；>1e-2 加回 `rc<0` 列重解一次，第二次无条件接受并披露。不以"存在负价列"本身作为否决或重解理由。
5. **影子价格发表口径。** 工程对偶（Barrier 级）可用于分析和发表，图注标明 `BARRIER_DUAL_ENGINEERING_GRADE` 与 BarConvTol；不再要求 DualVio/ComplVio ≤1e-5 的发布门槛。
6. **保留不变的部分。** 输入/源码/参数 SHA 溯源、release 冻结、不触碰在跑作业、不读取凭据、不外推短窗结果、历史记录只追加不改写。
7. **小量近似的披露规则。** 续接年水电/改造余量清零（A1/A2，阈值 1e-6 GW）和新建量 <1 MW 按零计，均为文档化近似，写入方法说明和结果披露，不作为 QC 失败项。

## 作者决定：relative_v1 修订、已解年份验收与 2060 数值清理（2026-10-12）

由作者与 Claude（决策层）确定，补充并在冲突处取代上节第 2、7 条；Codex 按此执行，异议写入报告"差异"一节。

1. **省际双向流判据。** relative_v1 中该项改为：同时双向流造成的额外损耗不超过全年系统负荷的 1e-4 即通过；重叠电量、重叠占 gross 交换比例、最大反向流照常记录并披露，结果表一律报告净流。原"重叠电量 ≤ 全年交换电量 1e-4"不再作为判据。理由：重叠是 Crossover=0 内点解在退化面上的固有特征，其物理后果只有额外损耗；2030/2040/2050 的额外损耗分别为全年负荷的 9.2e-7/1.3e-5/1.3e-5。
2. **水库水量平衡暂缓逐站判定。** 记录最大残差及所在站点、该站活动库容，状态标 `DEFERRED_BY_AUTHOR_20261012`，不作为 HARD_FAIL 依据，待后续单独复核。
3. **已解年份正式验收。** Base 2030/2040/2050 按 relative_v1（含本节第 1、2 条）出具验收记录，冻结归档不改写，验收记录与归档并列存放并以 SHA 互相引用。
4. **2060 起续接年的小数值清理。** A1/A2 阈值由 1e-6 改为 1e-5 GW，与 V9 已用的风光余量/下界清零阈值统一；A3 仍关闭。其余容量列族（储能功率/能量、火电新建、核电、波浪、接入与输电）采用同一个 10 kW（或 10 kWh）数值零：0 < 上界 − 继承下界 < 1e-5 时关闭余量。构建中 \|RHS\| < 1e-12 的浮点残差置零。所有调整逐列审计并披露。上一年状态中模型新建量（按站点或省 × 技术合计）<1 MW 的 cohort 在交接时删除，与第 7 条"新建量 <1 MW 按零计"的结果口径一致；删除量逐技术披露。
5. **Base 2060 不做候选筛选**，求解参数与 2050 生产 profile 相同（48 线程、Barrier、Crossover=0、BarConvTol=1e-4、NumericFocus=2）。
6. **验收结论只是参考标签。** 任何口径的自动验收（严格、relative_v1 或今后新增）都只用来记录解的质量；无论结论是 PASS、FAIL 还是 HARD_FAIL，都必须完整保全全部解数据（solution、BarX/BarPi、原始模型归档、状态、日志），不得因验收未通过而删除、覆盖、放弃或停止导出。是否采用某个解，由作者与决策层人工决定。

## 作者决定：情景体系与 case3 前置规则（2026-10-12 晚）

依据与理由见 `RESEARCH_DESIGN_CONSENSUS_20261012.md`；与旧文档冲突时以该文件为准。

1. **情景体系：** Base / Flex-coopt（`case3_thermal_ev_v5`，框架 A）/ Base-frozen（框架 B）/ Late-entry（框架 C：Base 2040 状态 → case3 配置 2050→2060）。框架 C 自本日纳入主计划。
2. **敏感性：** `case3_thermal_ev_v5_nocredit` 只跑 2030 一年，与 case3 2030 并行；`compensation_basis` 不排程。
3. **交接规则：** case3 与 C 的全部续接年使用 R1（与 Base 2060 相同的交接与数值清理规则）；case3 2030 与 `_nocredit` 2030 使用 V9，与 Base 2030 完全一致。
4. **relative_v1 扩展：** 除已实现的四项外，其余以 GW/GWh 计的物理残差检查一律采用 max(严格容差, 1e-3 GW 或 GWh)，在 case3 启动前实现。
5. **定价证书的比较用途：** 2026-10-10 第 4 条的门槛继续用于判断方案是否近优；与 Base 比较成本差时，证书上界 B 计入节省区间，B > 1e-4 × 目标值即加回负价列重解一次，两次求解数据均保全。
6. **报告口径：** 情景相对 Base 的节省按区间 [D_Base − P_X, P_Base − D_X + B_X] 报告；2040 年以后以物理量差为主。
7. **case3 求解参数（2026-10-14 作者确认）：** case3、`_nocredit` 与 C 的全部年份，在 Base 生产数值设置上只改 `Aggregate=0`，其余不变。依据为夜间数值实验第 5b、5c 节：冷热库存是每小时衰减 6–8% 的长链，预求解聚合沿链代入后，还原出的库存出现下界违反，规模越大越严重；关闭聚合后，隔离块与全模型中该机制均消失，744h 耗时 +28%，内存不变。LP 与 Base 相同，只是求解路径不同，结果可直接比较。F9 不做；F5 运行完后作为参考记录。

## 作者决定：case3 链接续与证书的两种用途分开（2026-10-19）

1. **2040 准备不等证书。** 以 case3 2030 筛选解的 `planning_state_candidate` 为上游，立即按 R1 生成 2040 派生状态，完成 1h/24h 门禁、冻结 release 并 held 提交。这些步骤与定价证书并行进行。
2. **链的接续只看近优性门槛。** 证书算出后，若 B/obj ≤ 1e-2（2026-10-10 第 4 条的接受范围），作者即采纳 2030 筛选解作为链的上游状态，放行 2040；若 B/obj > 1e-2，先按第 4 条加回负价列重解 2030，2040 改从重解状态出发。
3. **比较用途的重解不阻塞链。** 若 1e-4 × obj < B ≤ 1e-2 × obj，按 2026-10-12 晚第 5 条另起一个节点重解 2030，只用于与 Base 的成本比较。重解完成后，对比重解解与筛选解的分技术全国容量；任一技术相差超过 max(1 GW, 1%) 时报告作者，决定是否需要从重解状态重启后续年份，否则在方法中披露"续接年继承筛选解状态"。两次求解完整保全。
4. 2040 筛选清单使用已完成的 Base 2040 清单（margin 0.2）；求解设置同 2030（Aggregate=0），交接用 R1。R1 审计中"current deleted storage is zero"的固定文案须改为按实际逐技术数值输出。

## 作者决定：采纳 case3 2030 筛选解并授权放行（2026-10-19 晚）

1. **证书结果：** Claude 调用已提交的 `cispo_model/vre_pricing.py`，在本机独立算出 B = 347.782 million CNY，B/obj = 8.30e-5，近优性 ACCEPT，比较用途 INTERVAL_WITH_B（无需重解）；仅 3 个被剔除的陆上风电列转为负价。证据见 `claude_workspace/evidence/case3_2030_certificate_claude_20261019/`。节省区间更新为 [44.46, 64.32] 亿元/年，点差 47.52 亿元/年。
2. **作者采纳** case3 2030 筛选解的 `planning_state_candidate`，作为 case3 2040 的上游状态。
3. **放行授权，本条取代逐个作业"held 后等作者回复放行"的要求，仅限下列三个作业，各自门禁全部通过后由 Codex 直接 release：**
   - `_nocredit` 2030（Job 5153901）：立即 release；
   - case3 2040：R1 状态、1h 构建与 MPS 分段检查、24h 工程门禁、冻结 release 全部通过后，提交并 release；
   - C 2050：同类门禁全部通过后，提交并 release。
   任一门禁不通过或出现任务书未覆盖的异常，即停止该作业的放行并回报作者；其他作业不受影响。
4. 云端最多同时运行 4 个作业：Base 2060、`_nocredit` 2030、case3 2040、C 2050。

## 作者决定：恢复大型求解排程（2026-10-19，取代下节 2026-10-15 的暂停安排）

1. **`_nocredit` 2030（Job 5153901）立即放行。** 全年反事实只做 2030 一年；其余年份的能量/容量渠道拆分用 case3 自身对偶计算（容量裕度对偶 × 信用 GW 与逐时电价 × 移动负荷）。是否加 2050 单年反事实，待 2030 结果后另定。
2. **case3 2040** 按 2026-10-19 前一节准备并 held 提交，证书满足 B/obj ≤ 1e-2 后放行。它在关键路径上，优先于 C 2050。
3. **恢复 P5，准备 C 2050**（Base 2040 状态 → R1 → Base 2050 清单 margin 0.2 → Aggregate=0），门禁通过后 held 提交并汇报，作者放行后运行。
4. **框架 C 采用分步设计：** 先跑 C（2050 进入）。A 与 C 的 2050 结果出来后，若差异显著，再加 C′（2040 进入：Base 2030 状态 → case3 配置 2040→2060）；不显著则不跑 C′。

## 作者决定：继续 P4，暂停 C2050 与 nocredit 排程（2026-10-15）

作者要求继续 P4（Base2040/Base2050 筛选清单），P5 暂时不执行。C2050 和 `_nocredit`2030 都先等 case32030 这一系列成功收敛，再按作者后续确认安排；Job5153901 保持 held，不自动 release，C2050 暂不执行新增准备、门禁、打包或 held 提交。此条在执行顺序上取代此前二者与 case32030 并行推进的安排，不改变情景身份、数值参数、科学规则或既有结果。任何运行与部分传输继续完整保全；不建立后台监听或自动提交服务。

