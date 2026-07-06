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
