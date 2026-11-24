# CASE_data：求解案例数据与历史档案

日常查看请打开 [00_案例总览.html](00_案例总览.html)。这是本项目求解数据的正式本地入口，与 `supplementary_materials` 平级。

| 目录 | 用途 |
|---|---|
| `01_cases/<REF、OPS、LATE、PLAN等>/<year>/<release>/` | T550预处理后的统一核心数据：八模块、完整案例各22文件 |
| `02_history/01_production/` | 历史启动、状态、验收、筛选、续接与敏感性记录 |
| `02_history/02_numerical_experiments/` | 数值方案、诊断、失败与未晋级实验；保留科学决策依据 |
| `02_history/03_result_analysis/` | 既有结果分析、对偶提取和比较 |
| `02_history/04_backup_and_platform/` | 备份、传输、平台和测试记录 |
| `03_legacy_deliveries/` | 过去交付包与原manifest，保持原始字节 |
| `00_registry/` | 案例台账、模块完整性、迁移映射、校验与筛查清单 |
| `workflow/` | 标准提取、导入、验证和导航生成入口 |

本地标准核心是约20MiB的小表与验收证据，不包含原MPS、BarX/BarPi或逐时大数组。历史目录中既有的大副本本轮只迁移、没有删除；它们不是今后本地标准交付的要求。

T550保留完整结果和详细分析。来源：`/home/zz2/National_model_server/cloud_backup/<release>/`；有序全量入口：`case_library_v2_20261123/INDEX_ZH.md`；本轮模块化核心：`paper_core_modules_v1_20261124/`。每案溯源模块保留远端路径及校验信息。

工作流见 [WORKFLOW_ZH.md](workflow/WORKFLOW_ZH.md)：完整备份及验收 → T550只读核心提取 → 模块化打包 → 本地SHA导入 → 更新总览。后续案例不得再将求解数据堆入补充材料目录。

迁移报告见 [迁移与筛查报告](00_registry/migration_20261124/REPORT_ZH.md)。旧路径仍有兼容联接，防止已有论文脚本断链；它们不占第二份大数据，也不构成备份。统计空间时不能跟随联接重复计数。所有历史记录中的RUNNING/STOP仅表示当时状态，当前结论以案例台账与验收模块为准。

Git保留工作流、清单、报告及原先已经跟踪的历史文件（只变路径）；科学大数据和未跟踪档案不随Git发布。新克隆可按 `workflow/restore_legacy_paths.ps1` 重建需要的旧路径联接；未下载的数据仍需从T550按清单取回。
