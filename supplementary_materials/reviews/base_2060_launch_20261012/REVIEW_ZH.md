# Base 2060 启动前检查：D2 停止条件触发

2026-10-12（英国日期）。Git 基准 `ba3424ba2544e9eaced7e26ace2d6140cb1ce0d4`。

**状态：STOP_AUTHOR_REVIEW_REQUIRED。未删除 cohort、未准备派生状态、未构建或求解、未创建 release、未提交任何 Slurm 作业（包括 --hold）。**

任务授权来自 `../claude_workspace/tasks/TASK_base_acceptance_and_2060_launch_20261012.md`（相对仓库根目录），用户要求全部前置条件满足后先 held 提交，回复“放行”才释放。本轮发现任务书 D2 明确停止条件，故先停止并保全证据，不能用提交 held 绕过前置门禁。

## 停止证据

读取 2050 冻结输出的 `planning_state_candidate/capacity_cohorts.csv.gz`。只选择 `unit=GW`、`action=new_build`、`build_year>2025`，按 `asset_class × technology × asset_id` 跨 2030/2040/2050 cohort 求和，再选择 `0<sum<1e-3 GW`。这些 cohort 在 2050 均未退役；原状态不含 2025 外生既有装机 cohort。零值、非 GW、改造动作未作为新建量删除；负值保留原值参与所属组求和，无静默截零。

|门禁|观测|阈值|判定|
|---|---:|---:|---|
|全部 GW 资产拟删除合计|1.136306309440 GW|≤1 GW|STOP|
|燃气 CCS：删除 / 2050 装机|0.002534384242 / 0.351110918971 GW = 0.7218187%|≤0.1%|STOP|
|波浪能：删除 / 2050 装机|0.011349181817 / 0.011349181817 GW = 100%|≤0.1%|STOP|

共有 50,523 个正小量资产组、151,569 条对应 cohort（含同组选中的零值年份）。合计中发电与储能 0.638135708256 GW、接入与输电 0.498170601184 GW；二者的资产单位同为 GW，但总和**不是去重后的发电装机**。即使后续作者把总量门槛改为仅统计发电与储能，两个单技术门禁仍然失败，不能因此自行通过。

燃气 CCS 的分母为结果表中的全部已装容量，包含改造贡献；分子仅为满足删除规则的 `new_build`，没有将改造扣减。水电分母按站点型 `ror+reservoir` 统计，省级固定聚合容量没有对应可删 cohort。网络各技术比例门禁在已确认停止后未继续补齐。

另有 521 条负 `new_build` 浮点/数值尾差，合计 -0.000064421872 GW（约 -64.42 kW），单条最小值与负聚合组数见 JSON；本轮只披露，未判定其成因或擅自清零。

## 已执行范围与剩余工作

- A：已定位 `solution_export.py` / `solution_preservation.py`，未修改模型或 QC 源码；`relative_v1` 正式实现、离线评估器与完整回归尚未执行。
- B：三年各取回 17 个小文件并核对 SHA，16 个/年与 `result_manifest.json` 一致；manifest 自身无自引用，记录源端传输 SHA。共 48 个清单成员通过，3 个 manifest 通过传输 SHA。原 QC 初查符合任务书预期，但**尚未签发 acceptance_relative_v1.json，不宣称正式验收完成**。见相邻验收目录报告。
- C：云端输出每年约 5.3 GB，总计 15,956,401,851 bytes。固定机首次连接失败；用户要求重试后，127.0.0.1:22 转发已恢复并核实主机名 t550。目标盘总量 4,029,616,283,648 bytes、可用 1,481,126,653,952 bytes；即使三个 output 目录全部备份，按总容量估算可用比例仍约 36.36%，高于 30%。固定机的 paracloud-bscc-a8 别名无法解析，后续可采用本机流式中转。因 D2 停止，未传输备份或创建 backup_manifest。
- D：提前执行只读小量停止检查，已触发 D2。D1 的其余 headroom/超界/水力界、D2 派生状态、D3 1h 数值审计、D4 身份/白名单/24h 工程门禁均未执行。
- E：无新配置、profile、release、作业或 held Job ID；原云端 release 和已完成作业不变。无 Stage B、case3、后台监听，未访问凭据；未修改 SI modules 或在线 LaTeX。

## 输入、输出与复现

云端源：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260930_base2050_v9_t48_m750_tol1e4_v1/output_8760/`。完整三年清单与大小在相邻目录 `base_acceptance_relative_v1_20261012/collection_manifest.json`。原件的本地只读副本位于该目录 `evidence/<year>/`，保留本地，不全部混入 Git。源 cohort/metadata/manifest/容量表 SHA 写入 `state_structure_audit.json`。

```powershell
python supplementary_materials/reviews/base_acceptance_relative_v1_20261012/collect_evidence.py
python supplementary_materials/reviews/base_2060_launch_20261012/audit_cohort_cleanup.py
```

第二条命令完全离线。只写审计 JSON/CSV，不写 planning state；可用 `--source` 和 `--output-dir` 指定目录。`deletion_by_technology.csv` 是完整逐技术拟删量，`cohort_bins.csv` 是逐年份新建正 cohort 分箱；`deletion_candidates.csv` 保存全部 50,523 资产，保留本地。JSON 的 `by_technology` 可直接复查报告表。

验证：CSV 标准库逐组 `math.fsum` 与独立 pandas 分组计算资产个数一致，总量差 <1e-12 GW。未修改生产源码，未因只读审计运行全套模型求解测试；全套测试属于尚未完成的 A 阶段。

## 差异与精确下一步

为及早发现不允许继续的情况，在代码实现及备份前进行了只读 D2 预检查；没有将 A–E 未完成部分描述为通过。历史 handoff 的双向流重叠比例否决口径已被 10 月 12 日额外损耗判据取代，原归档与历史记录不改写。

建议作者/决策层明确：波浪能、燃气 CCS 的小技术容量是否保留（作为具名清理豁免），以及 1 GW 合计是否包含接入/输电资产。也可指定新的、更低 cohort 清理阈值并要求重新审计；当前授权下不能自行降低阈值、增加豁免或忽略超限。收到明确修订后先重新执行停止检查，随后完成 A/B/C 与 D/E 全部门禁，才可 held 提交。单独“放行”不对应任何现存 held 作业。
