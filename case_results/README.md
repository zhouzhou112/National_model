# 求解案例资料入口

打开 [00_案例总览.html](00_案例总览.html)，按情景、年份和版本查找全部 29 条登记记录。

- `core_library_20261123/by_case/`：T550 预处理并逐文件 SHA 核验的统一轻量包；25 个生产案例和 1 个诊断案例各 21 个核心文件，字段一致。
- `core_case_summary.csv`：26 个完整解的年度汇总；用 kind 区分诊断与生产。
- `case_catalog.json/csv`：本地入口、原备份和 T550 整理入口的对应表。
- 每案 `90_remote_files.csv`：全量原件路径、大小和 SHA；`91_remote_directories.json`：已有分析目录和文件位置。
- 失败尝试与排序测试仅保留身份和保全索引，明确无完整生产结果。Base 柔性关闭时同表保留条目，数值留空并标 DISABLED_BY_SCENARIO。

本轮统一核心文件约 19.99 MiB，压缩回传 4.83 MiB。未取回逐时数组、原 MPS、BarX/BarPi。

T550 统一入口：`/home/zz2/National_model_server/case_library_v2_20261123`；每案含 `core/`、`full_backup/` 原件导航及 `analysis_links/` 分析导航。所有原备份和分析原位保留。

原 `by_case/`、`deliveries/` 和审查目录作为历史交付保留，旧脚本引用不失效；旧入口说明见 `history/README_before_20261123.md`。后续新案例应沿用本次核心模式，补齐全部适用条目再登记，原始大文件继续仅存 T550。

口径：年度约束影子值不等于完整负荷价格或结算价；启停表是连续容量等效次数；V2G 净调节不重复叠加放电量；本目录保留既有验收标签，不替作者采纳结果。
