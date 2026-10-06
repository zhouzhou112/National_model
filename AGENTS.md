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
