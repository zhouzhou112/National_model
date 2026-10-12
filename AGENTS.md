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
4. **2060 起续接年的小数值清理。** A1/A2 阈值由 1e-6 改为 1e-5 GW，与 V9 已用的风光余量/下界清零阈值统一；A3 仍关闭。上一年状态中模型新建量（按站点或省 × 技术合计）<1 MW 的 cohort 在交接时删除，与第 7 条"新建量 <1 MW 按零计"的结果口径一致；删除量逐技术披露。
5. **Base 2060 不做候选筛选**，求解参数与 2050 生产 profile 相同（48 线程、Barrier、Crossover=0、BarConvTol=1e-4、NumericFocus=2）。

