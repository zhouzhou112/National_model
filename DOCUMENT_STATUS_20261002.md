# 文档与代码版本使用边界（2026-10-02）

## 继续工作只需先读这些入口

1. `CODEX_HANDOFF.md` 的 `Current validated snapshot`：最新经过核验的运行状态。其后归档段只提供历史证据，不授权执行旧“下一步”。
2. `SCENARIO_EXECUTION_PLAN_20261002.md`：用户确认的联合情景完整独立路径及后续消融顺序。
3. `cispo_full_lp_model_spec.md`、`config/FLEXIBLE_PORTFOLIOS_V5_CONTRACT.md`：数学与柔性服务合同；有年代差异时以当前验证的代码、输入和追加更正共同核对，不静默改模型。
4. `SERVER_RUNBOOK.md`、`MODEL_SERVER_STATUS.md` 的最新条目：运行命令与只读状态。历史作业号和路径不能当当前进程。
5. `supplementary_materials/reviews/dual_screening_20261002/`：本轮筛选方案、测试、输入身份和清理候选。

## 保留但退出当前决策入口

| 路径/类别 | 定位 | 为什么保留 |
|---|---|---|
| `PAPER_CASE_ROADMAP_20260721.md` | 历史互补 Pareto/MGA 研究设想 | 不能覆盖 9 月 V5 合同和本轮优先级；终期条件设计与完整路径的区分仍有参考价值 |
| `SCENARIO_MODULE_ARCHITECTURE.md` 的旧 V3 正文 | 历史架构 | 其“唯一 V3 情景”指令已过时 |
| `MODEL_SYSTEM_AUDIT_20260707.md`、`MODEL_SYSTEM_AUDIT_20260718.md`、`MODEL_SOLVABILITY_AUDIT_20260719.md`、`MODEL_744_SERVER_RUN_AUDIT_20260720.md` | 历史审计证据 | 记录模型演变，不能据此宣称当前 V9/8760h 已合格 |
| `FULL_YEAR_SOLVER_DECISION_20260817.md` | 特定 LP/机器/窗口的求解器对照 | 不支持“参数永远没有优化空间”或给当前全年性能定量背书 |
| `SERVER_BASELINE_20260702.md`、`FINAL_DEPLOYMENT_WORKFLOW_20260721.md` | 历史环境/部署记录 | 当前云端 release 与固定服务器 checkout 已不同，运行须重新核验 |
| `config/optimization_2030_*v2…v8.json`、V3/V4/legacy V5 overlay、旧 solver profiles | 历史实验配置 | 有已有输出/manifest/测试引用，不作“无引用即无价值”的自动删除 |
| `supplementary_materials/reviews/*/{source_snapshot,before_change,repo}` | 冻结源码证据 | 对应历史 LP 身份，不能与活动 `cispo_model/` 混用或批量清除 |
| 失败日志、原 MPS、BarX/BarPi、`planning_state_candidate` | 科研与恢复证据 | QC 失败不等于无价值；严禁在清理中删除 |

## 可审查的物理删除候选

仅列出本轮已查看的 5 个根目录 `.tmp_*portfolio*.py` 一次性生成脚本，以及 `supplementary_materials/Anycast_Win_b31.zip`。逐文件大小、SHA 和原因在 `supplementary_materials/reviews/dual_screening_20261002/deletion_candidates.csv`，共 6 文件、12,177,853 bytes。五个脚本会写当前代码/配置，不应再次运行；成熟实现已存在。压缩包与科研模型无直接关系，但用途须由作者确认。

本轮不执行物理删除。项目 AGENTS.md 要求清理前先列出文件并请求确认；原始数据、历史成果和已有未提交改动不进入这份删除清单。代码版本整理采用入口标识和身份清单，不改写 Git 历史、不移动当前活跃文件。
