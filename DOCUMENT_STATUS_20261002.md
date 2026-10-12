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


## 2026-10-12 继续工作只需先读这些入口（补充更正）

权威依据：`RESEARCH_DESIGN_CONSENSUS_20261012.md` 全文与 `AGENTS.md` 2026-10-12 两节；冲突以共识为准。下列引用逐字摘录共识，不重新计算数值。历史条目保留，仅供追溯，不构成新的执行授权。


在原入口清单前增加：

1. `RESEARCH_DESIGN_CONSENSUS_20261012.md` 全文：情景体系、价值渠道、R0/R1、证书用途、报告区间和执行顺序。
2. `AGENTS.md` 的“作者决定：relative_v1 修订、已解年份验收与 2060 数值清理（2026-10-12）”与“作者决定：情景体系与 case3 前置规则（2026-10-12 晚）”，并保留 2026-10-10 条目中未被取代的规定。
3. `CODEX_HANDOFF.md` 的 `Current validated snapshot`：运行状态必须读最新已核验证据，历史“下一步”不能重复执行。

`claude_workspace/tasks/TASK_case3_launch_contract_20261010.md` 已被部分取代，尤其涉及 relative_v1、情景范围、R1 续接、比较用证书门槛及 case3 参数待确认的内容。原第 2 项所称“后续消融顺序”不再适用；case1/case2 已移出主计划。生产代码与资格门禁仍有待实现，不把文档同步当作生产就绪。
> ## 6. 执行顺序与当前状态
>
> 1. **已完成：** Base 2030/2040/2050 正式验收（`supplementary_materials/reviews/base_acceptance_relative_v1_20261012/`）；三年结果已备份到 T550（262 文件，15.96 GB，SHA 全部核验）。
> 2. **运行中：** Base 2060，Job 5124127，release `20261012_base2060_v9a12_t48_m750_tol1e4_v1`，源码 680a5c4，不筛选。
> 3. **今晚：** case3 柔性块解质量的夜间实验（`claude_workspace/tasks/TASK_case3_flex_numerics_overnight_20261012.md`），结论决定 case3 的生产求解参数。
> 4. **下一步（Claude 写任务书，Codex 实现）：**
>    - 筛选生产化：profile、margin 参数、`--state-in` 支持；
>    - 定价证书脚本；
>    - relative_v1 扩展；
>    - R1 交接规则产品化，把 2060 的一次性脚本整理为可复用工具；
>    - 与冻结 Base 2030 release 的身份门禁、24h 门禁；
>    - held 提交。
> 5. **随后：** case3 2030 与 `_nocredit` 2030 并行提交。C 2050 在 `--state-in` 筛选就绪后提交，可与 case3 2030 并行。case3 2040 在 case3 2030 完成后提交。框架 B 任务书在 case3 2030 提交后撰写。
> 6. **云端占用：** 最多同时 4 个 64 CPU/750G 节点（Base 2060、case3 2030、`_nocredit` 2030、C 2050）。每个作业均先 held 提交，作者放行后才运行。
