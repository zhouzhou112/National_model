# 求解案例统一入口

这里按情景 → 年份 → 完整运行版本索引案例。研究计算和大文件保存在 T550；本机保存可核验的小结果和导航。原有路径保持不变，不删除、移动或改写历史证据。

当前索引：11个已验收生产案例、1个新完成待复评/备份案例、1个运行中案例、2个已备份失败尝试。未列入的旧诊断仍在原 reviews 目录，不表示被删除或已验收。

|情景|年份|版本|类别|验收|备份|入口|
|---|---|---|---|---|---|---|
|B|2030|v2|FAILED_ATTEMPT|NO_SOLUTION|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2030/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2/README.md>)|
|B|2030|v3|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2030/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3/README.md>)|
|B|2040|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2040/20261027_basefrozen_2040_v9a12_agg0_t48_m750_tol1e4_v1/README.md>)|
|B|2050|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2050/20261027_basefrozen_2050_v9a12_agg0_t48_m750_tol1e4_v1/README.md>)|
|B|2060|v1|FAILED_ATTEMPT|NO_SOLUTION|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2060/20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v1/README.md>)|
|B|2060|v2|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/B/2060/20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2/README.md>)|
|Base|2030|v3|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Base/2030/20260914_base_v9_t48_m750_tol1e4_v3/README.md>)|
|Base|2040|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Base/2040/20260919_base2040_v9_t44_m750_tol1e4_v1/README.md>)|
|Base|2050|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Base/2050/20260930_base2050_v9_t48_m750_tol1e4_v1/README.md>)|
|Base|2060|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Base/2060/20261012_base2060_v9a12_t48_m750_tol1e4_v1/README.md>)|
|C|2050|v2|COMPLETED_PENDING_ACCEPTANCE|待复评（旧HARD_FAIL）|T550连接阻塞|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/C/2050/20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2/README.md>)|
|Case3|2030|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Case3/2030/20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1/README.md>)|
|Case3|2040|v2|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Case3/2040/20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2/README.md>)|
|Case3|2050|v2|RUNNING_PRODUCTION|NOT_FINISHED|NOT_TERMINAL|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/Case3/2050/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2/README.md>)|
|nocredit|2030|v1|COMPLETED_PRODUCTION|PASS|COMPLETE|[打开](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/nocredit/2030/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1/README.md>)|

## 初步分析（在 T550 计算）

- [全年求解与成本汇总](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/run_summary.csv>)
- [B相对Base的工程对偶节省区间](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/B_vs_Base_cost_interval.csv>)
- [全国分技术装机](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/national_capacity.csv>)
- [全国分技术发电](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/national_generation.csv>)
- [分项成本](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/cost_components.csv>)
- [柔性签约与移峰汇总](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/analysis/flexible_contracts.csv>)

[结果解读与口径](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/PRELIMINARY_FINDINGS_ZH.md>)；[来源与SHA](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/deliveries/20261028_t550_v1/source_verification.json>)；[交付验证](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/delivery_receipt_20261028.json>)；[本机存放清单](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/local_storage_inventory.json>)。

## 存放规则

- `by_case/`：情景、年份和完整release的导航卡。v1/v2是运行包版本，不等同模型V9/v9_a12。
- `deliveries/20261028_t550_v1/`：本轮小结果，每文件≤1MiB；无逐时数组、BarX/BarPi、原MPS。
- `_packages/`：约0.61MB传输包，保留用于复核；没有把大原件复制到本机。
- 大原件和明细按 `remote_only_files.json` 定位T550。以后按需在T550汇总，再取小结果；不默认执行旧的≤32MiB全量小文件收集。
- 原 `supplementary_materials/reviews/` 含发布门禁、短窗诊断、失败保全与历史快照，是溯源档案；通过此目录查找，无需搬动。
