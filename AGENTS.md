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

