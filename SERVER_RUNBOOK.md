# CISPO 2030/8760 server runbook

## 2026-07-29 统一 release candidate 的固定服务器 744 h 门禁

执行状态（2026-07-29）：门禁 1--4 已在干净服务器提交 `7c56622c266e673037bd6afaa70c85aa57e6cb13` 和最终数据根 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4` 上完成；服务器完整回归 `130/130 PASS`，1 h/24 h V4 cold 均为 `OPTIMAL + QC PASS + 52/52 hard checks + valid input/result manifests`。唯一 744 h 根 `2030_744h_v0729_unified_v4_v1g_cold_v1` 已按第 5 条启动，控制目录为 `/data/zz2/National_model/run_control/2030_744h_v0729_unified_v4_v1g_cold_v1`。在它退出并完成严格验收前，任何新的 solve 都违反运行锁。

live checkpoint（2026-07-29 15:32:55+08:00）：服务器 checkout 仍为 clean `7c56622`，本地/固定服务器 bare `origin`/GitHub 文档基线为 `1f8cbaf`，模型实现仍为 `7aac739`；不要在活动进程期间仅为追平文档而切换 checkout。wrapper/Python PID `1004972/1004975` 仍存在。Barrier 已在 iteration `313`、solver runtime `9396.13 s` 完成，interior objective 约 `2,330,214.46 million CNY`；随后日志明确进入生产 `Crossover=1`。crossover basis 加入后最近为 `922,426 DPushes remaining`、`DInf=1.9217246e-6`；telemetry phase 为 `simplex`、runtime `9604.40 s`、current/max solver memory `14.06/23.13 GiB`。主机约 `101 GiB` available、swap `781 MiB/2.0 GiB`，`vmstat si/so=0`、memory PSI=0；三个终态 JSON 均尚不存在。ParaCloud 队列为空，历史 build-only/OOM/timeout 状态未变。另有一个旧 release-audit SSH/bash/grep 管道，无 Python/Gurobi 子进程且不是第二求解，本次只读记录、未终止。所有这些数值都会过期，后续必须重新读取；当前是 Crossover 阶段，不是终态接受。

任务边界：当前命令是 `scripts/run_cispo_2030_full_year.py --planning-year 2030 --horizon one_month`，仅运行一个 2030 V4 V1G cold gate；它不是、也不会自动转入 `2030→2040→2050→2060` 接续求解。服务器代码包含 `scripts/run_cispo_planning_sequence.py`，但该 runner 当前未调用。744 h 是 `TEST_ONLY_TRUNCATED_HORIZON`，不能成为正式 2040 科学状态 anchor；只有未来独立授权且逐年满足接受合同的 sequence 才能进行状态传递。

生产货币口径同样属于本 release：`technoeconomic_2025_cny_v2` 已在代码、服务器数据 sidecar、活动 input manifest 和 resolved config 中闭合，正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`。后续不得回到旧 2022-CNY/旧 FX 表或把说明性 V4 成本机械重平减。

本轮隔离部署把 `config/model_input_files.json` 升级为 v10；标准包必须包含 42 张运行表、12 个 server sidecar，归档中另含 `model_input_files.json`，合计 55 个条目。必须特别保留 `load/flexible_load_envelope_v3.{csv.gz,manifest.json}`、五张 V4 表、`flexibility/flexible_load_v4.manifest.json`、`wave/wave_sites.csv` 与 `wave/wave_input_manifest.json`。只传 V4 表而漏来源、只传 manifest 而漏 V3/wave 本体，都会在服务器回归或场景 dry-run 中失败。

当前本地匹配 Base/V4 V1G 的 2030→2040→2050→2060 168 h 序列已全部闭合，机器审计为 `outputs/planning_sequence_168h_v0729_ab_audit/planning_sequence_ab_audit.{json,csv}`。它证明递进 state、冷热/EV 输入、波浪输入、全模型 QC 和当前资源占用稳定；不证明年度价值。任何比较必须同时确认 `result_use=TEST_ONLY_TRUNCATED_HORIZON`，不得把年化 planning/enablement cost 与 168 h operation benefit 的差直接称为年度净收益。

作者已授权代码/外置数据口径统一后启动一个固定服务器 744 h 或两个月门禁。当前选择
标准 `one_month=744 h` 的 `flexible_load_comfort_v4_v1g` cold gate；它是既有支持时域，
同时覆盖新 Base 水电、wave 与 V4，且不需要新建时域接口。统一实现提交为
`1d04f07565c3039ed467ec4080f276bd0da90786`；部署时使用包含本节交接更新的最新分支 tip，
并确认相对该实现只增加文档变更。必须按以下顺序执行：

1. 本地 `scripts/audit_release_contract.py`、完整 unittest、V4 input validator、hydro input
   validator 和四个 1 h 模块根全部通过；精确暂存不得包含 `supplementary_materials/**` 或
   `.codex_tmp/**`。提交并推送后以 commit SHA 作为部署身份。
2. 实时核验固定服务器 checkout/dirty state、CISPO/Gurobi 进程、RAM/swap、`vmstat`、PSI、
   磁盘和目标输出根；同时核验 ParaCloud 队列。存在第二求解或内存持续换页时停止。
3. 从既有 model-ready 数据根复制出全新版本化根，只向新根安装 release contract 的外置
   文件；不得覆盖历史数据根。逐文件 SHA256 必须与 `release_contract_v0729.json` 相同。
4. 在精确 checkout 和新数据根运行 release audit、readiness、input-manifest、完整 tests，
   然后依次运行全新 1 h 与 24 h V4 cold；任一项不是
   `OPTIMAL + solution_qc=PASS + closed result/input manifests` 即停止，不启动 744 h。
5. 只启动一个全新命名的 2030 V4 V1G `--horizon one_month` cold root，显式使用
   `barrier_16_auto_order_v2` / `Crossover=1`，不传 `--basis-in`。持续记录 Barrier/crossover、
   raw/presolved/factor、RSS/swap/PSI、冷热/EV、wave、水电、成本 scope 和所有 hard checks。
6. 744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。不得启动 8760 h、付费云、并发第二求解、
   Base/V3/PHS/hydro-flex basis reuse 或 `Crossover=3`；MGA 仍等待完整 accepted Base anchor。
   V4 low/high 是论文参数敏感性的后续任务，不是本次工程稳定性门禁的前置条件。

下一窗口接续顺序固定为：

1. 完整读取 `AGENTS.md`、`CODEX_HANDOFF.md`、`cispo_full_lp_model_spec.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`。
2. 只读复核本地/双远端 Git，固定服务器 checkout/dirty state、唯一 PID/子进程、`solver_telemetry.jsonl`、`free -h`、`vmstat`、memory PSI、三个终态 JSON 与 ParaCloud `squeue`。
3. 若 PID 仍存在，仅监控，不改 checkout、不启动任何求解。若 PID 已退出，不以退出码或日志结尾单独验收；必须读取并交叉验证 `solve_report.json`、`solution_qc.json`、`result_manifest.json`、当前 `input_manifest.csv`、wrapper stderr/time 和全部模块输出。
4. 只有 `OPTIMAL + QC PASS + 52/52 hard checks + current input/result manifests valid` 才把该 744 h 工程门禁标为接受；随后更新三份交接文档。科学上仍保留 V4 low/high、完整 accepted Base anchor、basis/MGA 等开放项。

截断成本输出必须同时保留旧兼容列和以下解释字段：`value_million_cny_model_accounting_period`、`accounting_scope`、`optimization_hours`、`result_use`。`ANNUALIZED_PLANNING_COST` 是年化规划口径，`SELECTED_HORIZON_OPERATION_COST` 只覆盖当前求解窗口。缺少这些元数据的旧结果可以做数值/机制审计，但不能直接用于年度成本图表。

此前固定服务器 `701b9bc`、约 `70 GiB` available、swap 约 `19/21 GiB` 与空 ParaCloud
队列只是旧快照，不能作为本次启动证据；必须在部署和 744 h 启动前分别重新核验。

## 2026-07-28 常规水电 380 GW 省级聚合层的部署前门禁

当前本地未提交候选增加 `data/hydro/provincial_aggregate_capacity_2025.csv` 和 `data/hydro/provincial_aggregate_monthly_capacity_factor_2019.csv`，并将 `config/model_input_files.json` 升级为 v6。它把 297.8895 GW 站点级常规水电与 82.1105 GW 固定省级聚合容量闭合为 380 GW。省级聚合层是新的 LP topology：其发电变量进入省级平衡和 337 负荷中心年度注入，但不进入站点水文、梯级、备用、惯量、容量充裕性或 spur/trunk。不得导入任何旧 Base、duplicate-COMID-only 或跨年 `.bas`。

本节不授权服务器或云端动作。作者审阅并提交精确实现后，如单独批准部署，必须按下列顺序执行：

1. 本地工作树先分离并保留用户无关改动；提交/推送精确模型与生成脚本。核对两张新 CSV、31 省、372 省月行、全国 `297.8895 + 82.1105 = 380 GW`、PHS `65.94 GW` 以及输入 manifest v6 的 SHA256/role。
2. 远程实时核验 clean checkout、无 CISPO/Gurobi、RAM/swap/PSI 和输出根；把现有 model-ready 数据根复制到全新版本化根，只 add-only 安装两张新水电表及 v6 manifest，禁止覆盖旧根或把 82.1105 GW 写成伪站点。
3. 同时设置与新数据包匹配的 `CISPO_DATA_ROOT`、`CISPO_CF_ROOT`、`CISPO_HYDRO_ROOT` 和 `CISPO_WAVE_ROOT`，运行数据包 readiness、输入 manifest、focused hydro tests 和完整回归。注意本地原生水文索引分散在既有绝对路径时应保持 `CISPO_HYDRO_ROOT` 未设置；不要用错误的统一根覆盖索引路径。
4. 只运行全新、隔离、非并发的 1 h 和 24 h cold Base 根；要求 `OPTIMAL + solution_qc=PASS + closed manifest`，并核对 `hydro_aggregate_capacity.csv`、31×hours 的聚合发电、availability hard check、337 负荷中心聚合注入总量、成本分解、raw/presolved/factor 指标和 RSS。
5. 24 h 仍只是截断门禁。不得据此启动 168h/744h/8760h、复用 basis、覆盖旧输出或提交付费云任务；更长门禁必须由作者基于新的 topology、内存证据和科学敏感性另行授权。

## 2026-07-28 V4 冷热/EV 数据支撑型情景的运行门禁

当前未提交工作树中的 `flexible_load_comfort_v4_v1g` 与 `flexible_load_comfort_v4_v2g_sensitivity` 是新的 LP topology，不是 Base 或 V3 的 resume/basis 变体。禁止在三者之间复制 `.bas`、planning state 或把某一情景的性能外推给另一情景；V1G 是工程中心情景，V2G 仅作独立敏感性。

五张数据表已由已有 `hourly_load_2025_2060.csv.gz` 和 `flexible_load_envelope_v3.csv.gz` 生成。重新构建与验收使用：

```powershell
conda run -n RL python scripts/build_flexible_load_v4_inputs.py

conda run -n RL python scripts/validate_flexible_load_v4_inputs.py `
  --source-manifest data/load/flexible_load_envelope_v3.manifest.json `
  --source-manifest config/flexible_load_v4_source_registry.csv `
  --source-manifest config/flexible_load_v4_central_parameters.csv `
  --source-manifest config/flexible_load_v4_source_count_qa.csv
```

验收必须确认四个规划年均通过 loader energy closure、五张表的 SHA256 与 source manifest 非空；`connected_vehicle_fraction` 只能为聚合服务归一化 1，`minimum_departure_energy_gwh` 必须为 0，不得把二者重标为实测车辆行为。builder 必须使用固定 gzip `mtime=0`；连续两次完整 build+validate 的输出应逐文件字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。当前本地成功根为 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v3`、`outputs/2030_24h_v0728_flexible_load_v4_data_supported_v2` 和 `outputs/2030_1h_v0728_flexible_load_v4_v2g_data_supported_v2`，均须同时通过 result manifest 与当前 input manifest；失败的 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v1` 必须保留为 export 类型 bug 证据，不得 resume 或重标。

当前停止条件是作者审阅。若作者接受公式和中心值，下一步只运行一个全新、隔离、非并发的本地 168 h V1G cold root，并记录 raw/presolved/factor、Barrier/crossover、QC、manifest 和 RSS。该门禁只证明工程可解性；论文结论前仍须执行参数登记中的 low/high。不得由此启动 basis 工程、固定服务器 744h/8760h、付费云任务或并发第二个求解；`Crossover=3` 永久拒绝。

## 2026-07-28 M2 boundary audit: local decision closure, no deployment

`379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` adds a read-only M2 decision register and scenario parameter registry. It validates the locked Base identity, cohort VRE boundary, scenario-only V3/V2G overrides, explicit BECCS evidence status, the duplicate-COMID configuration flag, and MGA-anchor stop condition without building or solving an LP. Its local output is `outputs/m2_model_boundary_audit_20260728_local_v3/` (`9 PASS, 0 OPEN, 0 hard fail`); it does not license a server operation.

The present `static_capacity_potential_share_v1` duplicate-COMID hydrology implementation remains a user-owned uncommitted candidate. Local 1h/24h candidate roots are closed, but the 24h Barrier stage reported numerical trouble before Crossover produced `OPTIMAL`. Until its owner has reviewed and committed it, do not transfer it, fast-forward a server checkout, or infer a 168h/744h/8760h permission. After an explicit accepted commit, the only possible next solver gate is a newly named, isolated **local** 168h cold Base run, one solve at a time, with `barrier_16_auto_order_v2` and `Crossover=1`; record objective, hydro generation, raw/presolved/factor diagnostics, QC, manifest, RSS and the complete solver log. It remains prohibited to use `Crossover=3`, a cross-year basis, a concurrent second solve, fixed-server 744h/8760h, or any paid-cloud task.

## 2026-07-28 swap 清理判定规则

若 swap 占用高，先只读检查 `Cached/Buffers`、`AnonPages`、主要进程 `VmSwap`、`vmstat si/so` 和 PSI；不可把 `free` 的 buff/cache 或低当前 I/O 误判为“swap 可清”。本次约 `19.1 GiB` swap 已归因于活跃 Python/MATLAB 的匿名页，`drop_caches` 不会降低它。

只有确认没有会受影响的非 CISPO 作业，或获得主机级明确授权并确认约 `70 GiB` available RAM 仍充足时，才可在维护窗口使用受监控的 `swapoff/swapon` 回迁页面；完成后必须重新核验 RAM、swap、进程与 PSI。当前不满足前一条件，故不执行清理、不部署、不启动 CISPO。

## 2026-07-28 重复 COMID 水量修复的部署前门禁

本地 `static_capacity_potential_share_v1` 修复改变水电可用流量系数但不增加 LP 行列：同一 `COMID` 的站点按 `capacity_potential_gw` 静态份额共享一次扣除环境流量后的河段径流，梯级节点汇总成员站份额。该实现和 Module 05 / S6 审查包已通过 `116/116` 本地回归、1 h/24 h `OPTIMAL + PASS + closed manifest` 与 9/9 补充材料 formal closure；这些都只是本地截断工程证据。

本节不授权部署。18:15 后只读核验的服务器仍为干净 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`、无真实 CISPO/Gurobi 进程、约 70 GiB available RAM，但 swap 约 19/21 GiB；因此继续停止。若未来单独授权部署，必须：

1. 先提交并推送精确实现，确认本地工作树中不混入补充材料或用户无关改动；服务器再次实时核验 clean checkout、进程、RAM/swap 和目标输出根。
2. fast-forward 到精确提交，并同时设置当前 `CISPO_DATA_ROOT`、`CISPO_CF_ROOT`、`CISPO_HYDRO_ROOT`、`CISPO_WAVE_ROOT`；先运行完整回归和输入 manifest 校验，确认配置项 `duplicate_comid_flow_allocation=static_capacity_potential_share_v1`。
3. 只在一个全新隔离根运行匹配 24 h，再由作者决定是否需要一个 168 h cold Base 门禁；比较水电发电量、目标、raw/presolved 结构、全部 QC、manifest 与峰值 RSS。不得复用任何旧输出根或把旧 744 h 结果重标为新口径。
4. 不得由本门禁启动固定服务器 744/8760 h、第二个并发求解或付费云任务。正式多年 P30、清单覆盖、PHS 水力配对和容量语义属于独立科学决策，不能在部署时静默修改。

## 2026-07-28 M1 168h 四根 basis gate 已闭合后的停止条件

在本地 `a5e34bf` 实现、`barrier_16_auto_order_v2` / `Crossover=1` 下，2030 和 2040 的 cold/warm 四根均已达到 `OPTIMAL + PASS + closed manifest`，同年 objective 完全一致，warm 均为 0 Barrier/0 simplex。2040 仅接收 `2030_168h_v0728_m1_statebridge_local_v1` 的显式 diagnostic state，且只导入其自身 `2040 cold` basis。它们只证明同年、同 raw CSR topology 的截断 LP 可加速，不能转化为年度科学结果或跨年 basis 许可。

当前不运行 744h basis gate。原因是 basis 需要先有同一 744h cold root；在没有第二个同构 744h 求解需求时，新增 cold root 本身不产生可回收的端到端收益。等待真实的重复同构工程需要或新的、经授权的运行目标；届时先实时核验服务器和 ParaCloud，仍禁止 `Crossover=3`、并发第二求解、固定服务器 8760h 和付费云任务。

本里程碑后的实际只读复核为：服务器干净 HEAD `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi、约 `70 GiB` available RAM，但 swap 约 `19.1/21 GiB` 且有约 `43.0 GiB RSS` 的无关 Python；ParaCloud 队列为空。这个组合仍触发暂停条件：不部署、不复制数据、不启动服务器求解。该快照会变化，任何后续动作必须再次执行同样的只读核验。

## 2026-07-28 M0/M1 basis 身份协议与当前本地门禁

`a5e34bf5357301c205b246b0aa2149db0dca9c3b` 将运行身份拆为 `scientific_case`、`solver_runtime`、`implementation_bundle`，并在 LP 构建后写入 `lp_topology`。导入 basis 时必须同时满足：source closed manifest、`OPTIMAL + solution_qc=PASS`、相同 diagnostic hours、同规划年（除非代码明确的跨年例外）、basis SHA256，以及变量/约束顺序和方向、维度、NNZ、raw CSR sparsity pattern 的精确 topology 一致。只有 `lp_topology` 是 basis 兼容硬门；scientific/implementation 差异必须留下审计记录，且 warm root 永远不能替代科学 Base 验收。

当前 Base 为 `base_2024_vre_wave_on_flex_off_v1`：VRE 2024 北京自然年、wave 2023、hydro 2019；既有 VRE 生产 mode 为 `cohort_survival_v1`，`fixed_floor_v1` 仅为可重复的对照。BECCS lifecycle low/base/high 只是目录外 post-solve screening，不加 LP 行列、不能声称重新优化的可行性；bound tightening 仅保留已证明不改变可行域的变量上界。

在任何远程动作前，先在当前本地提交上顺序完成五个根：2030 168h cold、2030 warm、2030 state bridge、2040 168h cold、2040 warm。2040 只接收显式 test-only 2030 planning state，且只导入自身 2040 cold basis；任何跨年 basis、`Crossover=3`、第二个并发求解、744h、8760h 和付费云任务均禁止。现有下节 168h 根在本协议之前生成，只能作历史性能参考。

本节不授权部署：若未来确有远程必要性，仍先重新只读核验服务器 HEAD/工作树、CISPO/Gurobi 进程、RAM/swap、数据根和 ParaCloud 队列；swap 压力、非预期 checkout 或任何活动任务都要求停止。只有随后经过 add-only data 安装、完整回归和一个新命名 168h cold 根，才可另行评估下一阶段。

## 2026-07-28 intra-grid/cohort 168h basis 结果与服务器暂停条件

本地四根 168h Base 门禁已验证同年同结构的 guarded LP basis：2030 cold/warm solver `576.593/11.406 s`，2040 cold/warm `543.965/15.517 s`；均为 `OPTIMAL + solution_qc=PASS + closed manifest`，warm 均为 0 Barrier/0 simplex，cold/warm 容量一致。2040 仅接收明确 diagnostic 的 2030 state bridge，并且只使用 2040 自身 basis；不得以此说明跨年 basis 或生产全年复用。四根均输出并校验 `intra_grid_vre_site_design.csv` / `intra_grid_substation_design.csv`，其中 2025 VRE initial trunk proxy 为 `1,069.512666 GW`，旧 nameplate proxy 为 `1,309.999999962 GW`。

本地门禁不触发服务器部署。2026-07-28 即时只读检查虽未发现 CISPO/Gurobi 进程，且显示约 70 GiB 可用内存，但 swap 已用约 `19/21 GiB`，并有约 45 GiB RSS 的无关任务。因此严禁在该状态下切换 checkout、复制 cohort 输入或启动服务器 168h。ParaCloud 队列当时为空，但这不是后续操作的实时证明。

恢复服务器门禁的必要顺序是：先确认 swap 压力已解除、无求解/无冲突任务，再重新读 HEAD/内存/数据根/ParaCloud；add-only 安装 checksummed cohort CSV/sidecar；fast-forward 到精确推送提交；完整回归；最后在全新目录运行唯一的 168h cold Base 根。任何一步不符即停止。此门禁前后都不得使用 `Crossover=3`、跨年 basis、第二个并发求解、744h、8760h 或付费云任务。

## 2026-07-28 同格网风光共享并入 / 既有 VRE cohort 的部署前门禁

该本地模型变更对齐 CISPO S4-18/S4-19：site spur 使用 `max_t(cf) × capacity`，共享 wind/PV trunk 使用同一 substation 内 potential-weighted equivalent peak；它不增加逐小时 LP 行/列。既有 VRE 改用可追溯 cohort：已知 GEM 投运年按寿命退出，未知/OSM/残差与边界后投运容量只作 2025 boundary-censored cohort；退出不删除技术 site upper，因而同址再建是可选投资而非强制重建。此变更在本地 24h 通过 QC/manifest 和 `102/102` 回归，但尚未部署。

部署前必须按以下顺序执行，且一次只有一个求解：

1. 在本地从精确提交运行 `scripts/build_existing_vre_cohorts.py`，核对 `data/vre/existing_capacity_cohorts_2025.csv` 及 sidecar manifest 的 SHA256；当前已验证 CSV hash 为 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`。服务器数据根只能 add-only 安装这两个文件，不覆盖既有输入。
2. 实时读取服务器 Git HEAD、`ps`/`pgrep`、`free -h`、目标数据根和 ParaCloud 队列；若有任何活动 CISPO/Gurobi job、内存压力、非预期 checkout 或目标输出根已存在，停止，不切换 checkout。
3. 仅在空闲服务器 fast-forward 到精确已推送提交，设置全部三个数据根，并先运行完整回归和 preflight。回归、input manifest 或 cohort SHA256 任一不一致即停止，不手工绕过。
4. 仅在全新隔离目录运行一个匹配 168h Base 门禁，保持 `barrier_16_auto_order_v2` 和 `Crossover=1`。比较 `raw/presolved`、factor 指标、Barrier/crossover、objective、全部 QC、result manifest、进程树 RSS，以及 `intra_grid_vre_site_design.csv` / `intra_grid_substation_design.csv` 的容量闭合。
5. 不得把历史接受的 744h 根当作该科学边界的 anchor；不得使用已拒绝的 `Crossover=3`，不得并发第二个求解、启动固定服务器 8760h 或提交付费云任务。168h 的单次门禁只有在上述所有证据闭合后才可决定是否申请隔离 744h basis 门禁。

## 2026-07-28 Crossover=3 744h 严格 A/B 已结束：拒绝候选、保留 Crossover=1

`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 是唯一的、隔离的 solver-only A/B 根；它没有覆盖参考根或历史输出。该根在 `701b9bc`、2024 Base、wave on、flexible load off 和相同 raw/presolved/factor 结构下只把 `Crossover=1` 改为 `Crossover=3`。

Barrier 完成于 `6,981.07 s`（211 次），PPush/DPush 分别为 `1,191.93/1,214.00 s`，但 primal simplex cleanup 发生严重 infeasibility 循环。在 `10,930.99 s`、`1,724,960` simplex iterations 时向隔离候选发送一次 `SIGINT`，Gurobi 正常记录 `INTERRUPTED`；其无 solution、`solution_qc.json` 或 `result_manifest.json`，因此绝不可解释为 Base 解或“更快的 744h”。峰值进程树 RSS 为 `19.828 GiB`、无 swap，故失败原因是 crossover 数值路径而非内存。

生产决定：保持接受的参考根
`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 与
`config/solver_profiles/barrier_16_auto_order_v2.json` (`Crossover=1`)；不要把
`barrier_16_crossover_3_v1.json` 用于任何 744h/8760h/MGA anchor。保留两根和
`/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}` 作为正反对照证据。

后续任何 solver/formulation 候选必须先在新 24h、168h 根上获得
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，并记录
raw/presolved 规模、`AA' NZ`、Factor、全部阶段时间、迭代、objective、QC 与 RSS；只有唯一赢家才可运行一个新的 744h 根。当前服务器无活动求解；不得启动第二个求解、固定服务器 8760h 或新的付费云任务。

## 2026-07-28 744h 运行锁已释放

`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已达到 `OPTIMAL + PASS + manifest true`，原 wrapper/Python 进程均已退出。运行锁解除仅允许在重新核验 clean checkout、无进程和安全内存后 fast-forward 文档提交；不构成启动第二个 744h、固定服务器 8760h 或付费云任务的授权。

该根的 crossover 为 5,709.46 s，占 solver 时间约 43%。后续 8760h 方案必须单独处理 crossover 策略和 basis/MGA 需求，不能只按 Barrier 7,543.19 s 外推。

## 2026-07-28 168h 选择与 744h 唯一候选

服务器 2024 CF 与 `9a3c5e8` 已部署，完整回归及三组 168h 均闭合。省级年度排放分层不改变 presolved/factor/迭代，禁止仅因 raw dense row 消失就将其选为生产 formulation。`PreDual=1`、`PreSparsify=2` 已由 24h 淘汰。

新 744h 只允许：

```text
formulation: national_dense_v1
solver: config/solver_profiles/barrier_16_auto_order_v2.json
hours: 744
weather: Beijing natural-year aligned 2024
output: /data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2
```

选择依据是 168h 总时间 668.05 s 对 700.50 s、`AA' NZ` 低约 8%、`Factor NZ` 低约 1.8%、RSS 持平；风险是 Barrier 只到 `performed`，crossover 190.62 s 对 72.76 s、simplex 630,993 对 229,459。744h 必须监控 build/presolve/ordering/Barrier/crossover、进程树 RSS 和 solver telemetry；若达到 `MEM_LIMIT`、无进展或异常 swap 增长，应保留输出并停止，不得启动并发替代 case。

## 2026-07-28 2024 VRE 部署与 Phase A/B 放大顺序

当前本地实现提交 `1449a457` 尚未部署；服务器仍为 `4e1999d`，且 `/data/zz2/National_model/data/hourly_cf` 缺少 2024 stores。新代码需要同时读取各技术的 `cf_hourly_*_2023.zarr` 与 `cf_hourly_*_2024.zarr`，覆盖 `onshore_wind`、`offshore_wind`、`pv` 和 `mixed_wind`。

2024 数据只能在再次确认无求解进程、目标目录不存在、磁盘足够后追加传输；不得覆盖 2023 stores。传输前后记录每个目录的文件数、总字节和归档 SHA256。然后 fast-forward 到已经同时推送 `origin`/`github` 的精确提交，设置四个数据根，运行完整 discovery 回归。

服务器放大采用顺序匹配门禁，绝不并发：

1. 168h dense + `barrier_16_infeasibility_diagnostic_v1`，复现 `DualReductions=0 + InfUnbdInfo=1`；
2. 168h dense + `barrier_16_auto_order_v2`，只改变为 1/0；
3. 仅当第二步 factor/阶段证据有价值时，再运行 168h province hierarchy + 同一 profile；24h 已证明其 presolve 后矩阵与 dense 完全相同；
4. 每根必须满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，并记录 raw/presolved rows、columns、nonzeros、`AA' NZ`、`Factor NZ/Ops`、build/presolve/ordering/Barrier/crossover、迭代、objective、RSS；
5. 选择唯一胜者后，以全新名称启动一个 744h 根。启动前再次检查无第二个求解及安全可用内存；不得因 744h 压测改变 Base 目标、约束、时空尺度或技术边界。

固定服务器 8760h 继续禁止；ParaCloud 8760h 仍需用户另行确认。

## 2026-07-28 当前 Base 工程门禁与 basis 复用协议

当前部署 checkout 为 `/data/zz2/National_model/repo` 的 `4e1999d`，仅在实时确认无进程且内存安全后 fast-forward。使用附加的 wave-ready 数据根 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727`、CF 根 `/data/zz2/National_model/data/hourly_cf`、水文根 `/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse` 和波浪根 `/data/zz2/National_model/data/wave_energy_20260727`；不得替换为历史 wave-off 根。

当前 Base 已完成 1h、24h、168h 工程序列，每项均使用新根并满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。168h 根为：

```text
/data/zz2/National_model/outputs/2030_168h_v0728_server_wave_base_barrier16_v1
```

它是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。168h 求解耗时 690.86 s，其中 Barrier 584.20 s、crossover 104.23 s；后续性能比较必须同时保留两个阶段、raw/presolved 维度、`AA' NZ`、`Factor NZ`、`Factor Ops`、目标/QC 和峰值 RSS。机器可读的 1h/24h/168h 及 basis A/B 表位于 `/data/zz2/National_model/outputs/solver_audit_v0728/`。

仅限 test-only 的 LP basis 复用：先从 `OPTIMAL + PASS` 诊断根以 `--export-warm-start-basis` 导出。导入时传入 `--basis-in SOURCE_ROOT --allow-basis-reuse`；跨年还必须显式传入 `--allow-cross-year-basis`，并提供相应已验收的 diagnostic `--state-in` 与 `--allow-diagnostic-state-in`。runner 会验证源 result manifest、源终态、git commit、情景、小时数、basis hash、raw dimensions 和完整有序的带名称 LP 结构。它设置 `LPWarmStart=2` 以保留 presolve。该机制不会序列化或复用 Gurobi 模型、Barrier factorization、presolve state 或 crossover tableau。科学全年运行及 raw 非零元超过 50m 的矩阵均被显式禁止自动 basis 复用。

绝不并发运行两个 CISPO 求解。不得触碰历史输出根，尤其是 `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`。固定服务器 8760h 仍被禁止。新的云端 8760h 必须获得用户单独确认，并具备不可变代码/数据/情景 hash、新门禁、高内存 Slurm 方案、线程/SoftMemLimit、成本预估与停止规则。MGA 必须作为独立的“成本约束后二级目标”工作流实现和运行；不得覆盖或重标 Base 最小成本输出。

`4e1999d` 已提供 MGA runner 选项：`--mga-spec SPEC.json --mga-baseline BASE_ROOT`。它只接受闭合的 `SCIENTIFIC_PRODUCTION + BASE_MINIMUM_COST + OPTIMAL + PASS` 年度 Base 根，且要求同一计划年/边界年、已解析配置和 required-input SHA256；诊断时域、basis 复用、diagnostic state 和既有 MGA 输出均被拒绝。通过后模型保留原年度成本表达式并添加成本上限，再最小化或最大化一个明确筛选的新增容量目标；结果写入 `mga_request.json`/`mga_run.json`，不导出 `planning_state`。当前没有 accepted 年度 Base，故只允许 MGA preflight/契约测试，不得执行 MGA 求解。

## 2026-07-27 原始 LP 稀疏审计：仅本地闭合，不得据此扩大求解

本地提交 `6114157` 增加可选的 `--constraint-family-audit`。该开关仅在
`model.update()` 后读取原始稀疏矩阵，默认 `50,000,000` 个非零元是硬安全上限；
超过即停止审计，禁止为完整 744h/8760h 提高上限。它不改动任何变量、约束、
目标、场景、数据或 Gurobi 数值参数。`constraint_family_audit.json` 与结果目录
一起被 catalog 和 SHA256 manifest 记录，包含原始约束/变量族、最稠密 25 行/列，
以及求解日志的全局 presolve、ordering、`AA' NZ`、`Factor NZ`、`Factor Ops`、
Barrier/crossover 指标。不得把 Gurobi 的全局 presolve 删除量虚假归因给某个族。

本地 1h/24h 新根
`outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，
波浪能开启、灵活负荷关闭，完整回归 `75/75`。24h 根为 raw
`231,074/345,992/1,729,035`、presolved `129,335/260,116/1,269,506`
（rows/columns/nonzeros），`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、
`Factor Ops=7.399e8`、89 Barrier、57,741 crossover/simplex、29.107 s 和
0.712 GiB RSS。最稠密原始行是 `annual_emissions_accounting`（6,697）、
`capacity_margin_p65/p15`（6,491/5,736）和 `co2_source_balance_p*`（各 3,246）；
水电逐站平衡不是当前首要密集行来源。

这只是候选筛选，不是删约束许可。下一步仅为年度排放会计分解建立代数等价证明，
并在新的隔离 Base 24h 根上同机、同 profile 做一次 A/B。只有目标、全部 QC、
manifest、raw/presolved 尺度、factor、阶段时间、迭代和 RSS 都通过后，才可决定是否
运行 168h。未部署固定服务器、未查询或修改 ParaCloud；不得据此启动服务器 168h、
744h、8760h 或新的付费云任务。

## 2026-07-27 孤立梯级节点等价清理：仅本地已验收，禁止直接扩大求解

本地提交 `9787ba7` 不删除拓扑源数据或水电站：142 个节点、124 条边保持不变。只有 8 个已经核验为零度、单站的节点从逐小时核心梯级装配转入向量化独立水库平衡。它们没有上游到达流，其局部 GRFR 入流就是独立平衡的入流，因此物理方程、库容、弃水和可行域均不变；有效核心梯级站点行从 146 变为 138。任何多站孤立节点均会使建模硬失败，不能静默转换。

设置 `CISPO_WAVE_ROOT` 的本地完整回归通过 `71/71`；新的 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，波浪能开启、灵活负荷关闭。24h 目标相对清理前只差 `9.78e-09 million CNY`，raw/presolved 规模不变；但 `Factor NZ/Factor Ops` 从 `6.111e6/6.039e8` 变为 `6.284e6/7.399e8`，且 34.636 s 不优于 33.766 s。因此将其视为局部 Python 约束构建清理，不得宣传为 Barrier、内存或 8760h 优化。

本轮没有服务器或云端操作。后续如获单独授权，必须先实时复核固定服务器 checkout、CISPO/Gurobi 进程、`free -h` 和数据根，部署精确的已推送提交，再以全新隔离根运行一个单一的匹配 168h Base 门禁。不得并发、覆盖历史输出、启动固定服务器 8760h 或提交新的付费云任务。

## 2026-07-27 连续 RUC 等价瘦身：仅本地已验收，服务器操作需另行授权

本地实施提交 `3f2255a` 移除了连续 RUC 中四组严格冗余的逐小时上界行：
`online<=capacity`、`startup<=capacity`、`shutdown<=capacity`、`gross<=pmax*online`。
它们分别由保留的 S4-24、S4-25、S4-29 和变量非负下界蕴含；建模前硬校验
`min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction` 及参数完整性。不得在
未保留这些行或未通过硬校验的分支上套用此说明。

本地完整回归 `69/69`，以及新建 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均为
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`；Base 波浪能开启、
灵活负荷关闭。24h 原始行数/非零元减少 `32,736/65,472`，变量和目标值不变；但 presolved
矩阵、`AA' NZ`、`Factor NZ`、`Factor Ops`、Barrier/crossover 迭代都完全相同。因此把它记录为
原始构建负担的等价缩减，不能以此声称 8760h Factorization 已加速或可行。

本轮没有服务器部署或远程写操作。只有用户另行授权后，才可按顺序：实时读取服务器
checkout/进程/内存/数据根 → 部署精确的已推送提交 → 用新的、隔离的含波浪 Base 输出根运行一个
匹配 168h A/B。不得并发求解、覆盖任何历史输出、启动固定服务器 8760h，或提交新的付费云端任务。

## 2026-07-27 新 Base：波浪能已整合；服务器尚未部署

当前仅允许两个可运行身份：

1. `base`：风电（含海风）、光伏、严格映射至既有 marine `grid_uid` 的波浪能；`flexible_load=false`。
2. `flexible_load_comfort_v3_v2g_5pct`：继承上述 Base，并启用 `comfort_envelope_v3` 冷热状态、EV V1G 和因果日内 5% V2G；它仍是参数待校准的敏感性。

提交 `c992550` 删除其余实验性 scenario JSON；不删除历史输出、数据或 Git 证据。两个当前身份都必须先设置 `CISPO_WAVE_ROOT`。本地 1h/24h 均已通过 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，完整回归为 `66/66`；但这不构成服务器部署、更不构成 8760h 授权。新 Base 的全年静态预估为 36.47 GiB，柔性覆盖层为 37.63 GiB，不能用来判断 Barrier factorization。

旧服务器 wave-off Base 根一律保留且只作历史证据，不能作为重定义后 Base 的新门禁结果。若用户另行授权服务器测试，先实时复核空闲 checkout/进程/内存，部署精确推送提交，并且仅运行一个全新的、明确命名的 168h 根；固定服务器 8760h 和新付费云端任务仍禁止。

## 2026-07-27 全模块联合敏感性：本地门禁完成，服务器运行尚未授权

本地新增的 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct` 同时启用波浪能、
`comfort_envelope_v3` 冷热、V1G 和 5% 日内因果 V2G。它是参数待校准的独立敏感性，
不是 Base；不得通过覆盖 Base JSON、环境变量或默认开关把它伪装为 Base。

本地 1h/24h/168h 已各自形成新根并通过
`OPTIMAL + solution_qc=PASS + validate_result_manifest=True`；168h 的 factor 结构为
`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`。其全年静态 preflight
估计 37.63 GiB，但这不是 Barrier factor/workspace 的内存保证，更不是 8760h 授权。
详细输出、短窗口解释限制与结构优化次序见
`MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。

禁止仅因该本地结果启动固定服务器 8760h、新付费云端任务或并发第二个求解。若用户另行
授权服务器比较，先实时核验空闲 checkout/进程/内存，并且只运行一个新的、明确命名的
168h 根；同机、同线程、同 solver profile 的 Base 对照是记录模块求解性增量的前置条件。

## 2026-07-27 Base 168h generic-wrapper manifest 门禁已通过

固定服务器在空闲且 clean 的 `c879c99` 上复核后，fast-forward 到已推送的
`67482ab`（其中 P0 实施为 `7499062`），并完成服务器 discovery 回归 `67` 项
通过、`2` 项可选 xarray 测试跳过。相对于原固定服务器模型实现，新增的唯一
模型邻接代码为 runtime-log manifest 排除；不得将它表述为 LP 或科学边界变化。

已完成且必须保留的新门禁根：

```text
/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base
```

命令使用 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48`、
`Crossover=1`，将 wrapper 输出重定向到通用 `stdout.log`/`stderr.log`，并由
`/usr/bin/time -v` 记录端到端资源。终态为 `OPTIMAL + solution_qc=PASS +
scenario_id=base + validate_result_manifest=True`，Base 灵活负荷和波浪能均关闭；
所有 hard checks 通过。原始/预处理矩阵为
`1,393,915/1,011,079/9,797,949` 和 `729,559/817,723/7,001,232`
（rows/columns/nonzeros）；`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、
`Factor Ops=8.436e10`。Gurobi 运行 614.894 s（161 Barrier、226,659
simplex/crossover），端到端 12:24.94，峰值进程树 RSS 3.453 GiB，未发生 swap。

`result_manifest.json` 明确排除 `run.pid`、`stdout.log`、`stderr.log`；最终
`validate_result_manifest()` 为真且无失败项，证明最终报告打印发生在 manifest
finalize 后时，wrapper 日志不会再污染科学哈希契约。这个 168h 根仅为
`TEST_ONLY_TRUNCATED_HORIZON`。不得写入、重建或原地修复旧
`2030_744h_v0726_spill_explicit_barrier16_auto_order`；不得启动固定服务器
8760h 或新的付费云端 8760h。

接下来 P2 若需要处理旧 744h，只能先设计名称明确、目录外且只读的
post-run audit manifest；只有研究协议明确要求原目录 result manifest 闭合时，
才可申请全新根的修正版 744h。P3 候选必须先在匹配 24h/168h 记录 raw/presolved
rows、columns、nonzeros、`AA' NZ`、`Factor NZ`、`Factor Ops`、phase time、
Barrier/crossover、objective/QC 与 RSS；不得以改变 Base 科学边界换取加速。

## 2026-07-27 manifest 契约 P0 在本地闭合

提交 `7499062` 修复通用 shell 重定向文件名缺口：`stdout.log` 和
`stderr.log` 均为 runtime-managed artifacts，已从科学输出目录及
`result_manifest.json` 排除；不改变任何科学模型设定。回归先 finalize
manifest，再向两类通用 wrapper 日志追加，并验证所有科学文件哈希仍可
验证。完整本地回归通过 `67/67`。

新的 Base 诊断根为：

```text
outputs/2030_1h_v0727_manifest_runtime_contract
outputs/2030_24h_v0727_manifest_runtime_contract
```

两者均为 `OPTIMAL + solution_qc=PASS + scenario_id=base`，manifest 闭合且
灵活负荷/波浪能关闭；24h 门禁有 342,343 个变量、262,201 条约束、1,771,702
个非零元、41.296 s 求解时间和 0.725 GiB 峰值 RSS。它们仅为 test-only
门禁。不得向旧 744h 目录写入。提交推送后，先重新核验固定服务器 checkout、
CISPO/Gurobi 进程和可用内存，再决定是否部署并启动一个新的 168h Base 根。
固定服务器 8760h 与所有新的付费云端 8760h 工作仍禁止。

## 2026-07-26 solvability-optimization campaign

The user has explicitly authorized sequential 744h or longer fixed-server stress
tests for the latest model, provided the host does not exceed safe memory. This
authorization supersedes earlier fixed-server 744h prohibitions in older entries,
but it does not authorize a fixed-server 8760h solve or another paid cloud run.

Required sequence:

1. preserve `supplementary_materials/**` user changes and commit only reviewed
   non-supplementary code/config/test/handoff files;
2. verify the fixed server has no CISPO/Gurobi process, then fast-forward the
   checkout to the exact pushed commit;
3. export the four versioned runtime roots and pass the complete server regression;
4. retain explicit spill: its matched 168h factor structure and telemetry memory
   are lower, and its 24h flexibility runtime is materially faster;
5. compare dual simplex, Barrier-16 and CPU-PDHG sequentially at 168h;
6. run only one 744h profile at a time, requiring at least 56 GiB available RAM
   before launch and using `SoftMemLimit=48`;
7. compare `build_report.json`, `solver_telemetry.jsonl`, `gurobi.log`,
   `solve_report.json`, `solution_qc.json`, process-tree peak RSS and `/usr/bin/time`;
8. stop further profiles after any memory hard failure or when available RAM falls
   below the gate. Never run multiple profiles concurrently.

The independent-reservoir spill projection in `6d84209` is mathematically exact,
but raw-column reduction alone is not an acceptance criterion. The matched 168h
projection is 1.84% faster, yet explicit spill has lower presolved rows/nonzeros,
lower `AA' NZ`, `Factor NZ`, `Factor Ops` and telemetry solver memory. Explicit
spill is also 24.0% faster in the paired flexibility case. Commit `9e82cc5`
therefore remains the default because 8760h is factor-memory bound. Preserve both
output roots and the audit at:

```text
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.json
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.csv
```

Solver profiles are numerics-only JSON files and are separately hashed in
provenance:

```text
config/solver_profiles/barrier_32_reference_v1.json
config/solver_profiles/barrier_16_sparse_amd_v1.json
config/solver_profiles/barrier_16_auto_order_v1.json
config/solver_profiles/dual_simplex_16_v1.json
config/solver_profiles/barrier_32_limited_presolve_fast_basis_v1.json
config/solver_profiles/barrier_32_force_dual_v1.json
config/solver_profiles/pdhg_cpu_32_v1.json
```

Run CPU PDHG only with Gurobi 13.0+ (the fixed server qualifies); local Gurobi
12 must not be used for that profile. Use `scripts/compare_solver_runs.py` to
write one JSON and CSV row per isolated output root.

Dual simplex is not a 744h candidate. The 168h run was stopped gracefully after
905.073 solver seconds and 421,470 pivots without a feasible basis, compared with
654.026 s for a complete Barrier-32 solution. Preserve its diagnostic root:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_dual_simplex16
```

Barrier-16+AMD completes 168h in 644.636 s with lower RSS, but AMD increases
factor nonzeros and operations. Do not promote it directly to 744h. First run
`barrier_16_auto_order_v1.json`, which changes only the thread limit relative to
the Barrier-32 reference.

The automatic-order control completes in 637.344 s and is the current Barrier
leader while preserving the reference factor structure. The first PDHG launch
root named `2030_168h_v0726_spill_explicit_pdhg_cpu32` is a pre-build config
failure, not a solve. Use a new output root only after the `pdhg_gpu` solver-key
whitelist regression passes on the server.

The corrected CPU-PDHG root is:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2
```

It was gracefully terminated after 3,074.134 solver seconds with no feasible
solution. The last telemetry record is near iteration 496,035; peak solver and
process-tree memory are only 1.990 GB and 2.503 GiB, but the terminal primal
residual is still about 49.5 and the dual residual is rising. Retain it as a
low-memory diagnostic, not as the first 744h profile.

The active one-at-a-time 744h gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order
PID=663050
ps -p "$PID" -o pid,etime,%cpu,%mem,rss,vsz,stat,cmd
tail -n 100 "$OUT/stdout.log"
tail -n 20 "$OUT/solver_telemetry.jsonl" 2>/dev/null
ls -lh "$OUT"/{build_report,solve_report,solution_qc,result_manifest}.json 2>/dev/null
```

It uses clean server HEAD `c879c99`, the `city_337` data root,
`barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and
`SoftMemLimit=48`. Available RAM was about 69 GiB at launch. Do not start a
second fixed-server solve. PID exit is not acceptance: require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest and inspection of process-tree
peak RSS, presolve/factor structure and crossover behavior.

The verified active-run structure checkpoint is:

```text
build: 341.673 s; 3,686,023 columns; 5,920,701 rows; 42,360,391 nonzeros
build peak process-tree RSS: 4.977 GiB
presolve: 223.80 s; 3,017,979 columns; 3,088,821 rows; 30,884,732 nonzeros
ordering: 115.48 s
AA' NZ: 6.449e7
Factor NZ: 8.062e8 (about 9.0 GB)
Factor Ops: 6.197e12
early telemetry peak solver memory: 25.087 GB
```

This passes the build/factor memory gate but is not solve acceptance. Continue
monitoring the Barrier residual trajectory and subsequent crossover; do not
infer success from factorization alone.

Barrier subsequently completed normally in 244 iterations and 8,917.48 solver
seconds with interior objective `2,196,881.94 million CNY`. The active run is
now in crossover:

```text
initial dual pushes remaining: 1,044,784
dual pushes remaining at solver time 9,860 s: 464,775
latest telemetry checkpoint: 358,606 simplex iterations at 9,996.25 s
current / peak solver memory: 13.948 / 25.087 GB
```

Do not treat the Barrier objective as the accepted LP result. Continue until
crossover and any primal cleanup finish, then require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest, `scenario_id=base` and final
process-tree memory/time evidence.

The run subsequently completed:

```text
status: OPTIMAL
objective: 2,196,881.920967378 million CNY
solver runtime: 13,541.717 s
Barrier / simplex iterations: 244 / 1,451,182
wall time: 3:52:03
peak process-tree RSS: 23.121 GiB
swaps: 0
solution_qc: PASS
scenario: base
```

Scientific checks pass, but strict manifest validation returns only
`size:stdout.log`. The manifest records 63,631 bytes and the completed file has
66,236 bytes. The launch wrapper used `stdout.log`, while
`RUNTIME_MANAGED_FILES` recognizes `runner_stdout.log`, `run.stdout` and the
sequence variants. Because the entrypoint prints the final solve report after
manifest finalization, hashing the generic redirected log creates a stale
manifest.

Preserve this output unchanged. Treat it as valid mathematical/QC and
performance evidence, but not as a closed reproducibility gate. Before any
replacement run, align the wrapper filename with the runtime-managed contract
or make a reviewed additive contract fix with regression coverage. Do not
silently regenerate the existing manifest or overwrite the terminal output.

## 2026-07-27 next-phase closure and scale-up gate

Live closeout state:

```text
fixed-server implementation HEAD: c879c99 (clean)
fixed-server CISPO/Gurobi process: none
fixed-server available RAM: about 69 GiB
ParaCloud active jobs: none
8760h accepted scientific result: none
```

Follow this order:

1. Make a minimal local manifest-contract fix. Generic wrapper files
   `stdout.log` and `stderr.log` must be runtime-managed/excluded, or the
   alternative design must prove they cannot change after manifest
   finalization. Add a regression that appends to a wrapper log after finalize
   and still validates every scientific file.
2. Preserve
   `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`
   byte-for-byte. Never regenerate its `result_manifest.json` in place.
3. Pass the complete local regression and new Base 1h/24h roots with
   `OPTIMAL`, `solution_qc=PASS`, `scenario_id=base` and a closed result
   manifest. Then, only on an idle clean fixed server, deploy the exact commit
   and run one new 168h Base root.
4. Do not rerun 744h solely because the wrapper log changed. Default to an
   explicitly named, directory-external, read-only post-run audit for the old
   result. Request a corrected 744h rerun only if the research acceptance
   protocol requires the original in-directory manifest to close.
5. For solvability work, compare candidate formulations/settings on matched
   24h and 168h cases before any 744h. Record raw/presolved rows, columns and
   nonzeros, `AA' NZ`, `Factor NZ`, `Factor Ops`, Barrier/crossover iterations,
   objective/QC equivalence and process-tree peak RSS. Do not change Base
   physics, temporal resolution, objective or constraints to obtain speed.
6. A new ParaCloud 2030/8760h solve requires separate explicit authorization,
   immutable code/data/scenario hashes, fresh 24h/168h gates, a reviewed
   high-memory node/thread/time-limit plan, estimated billed core-hours and
   termination rules. Never launch fixed-server 8760h.

Scientific work may proceed independently only behind scenario/accounting
boundaries: Base keeps flexibility and wave disabled; flexibility V3 requires
building/EV calibration and low/base/high tests; total 2025-2060 transformation
cost requires a discounted pathway ledger or an explicitly approved
multi-period objective; MGA cost-relaxation and point/province/national
complementarity follow an accepted Base scientific solution.

For Slurm deployments, request a termination warning such as
`--signal=B:TERM@300` and set the Slurm wall limit at least five minutes longer
than Gurobi `TimeLimit`. This lets the signal handler call `Model.terminate()` and
write a normal interrupted report. `solver_telemetry.jsonl` is flushed during
optimization and remains useful even if a later hard kill prevents final export.

Cloud job `4004585` is terminal `TIMEOUT`. It reached Barrier iteration 35 with
476.76 GiB sampled MaxRSS but remained far from convergence, and it produced no
acceptance reports. Preserve its output unchanged.

## 2026-07-25 Barrier-32 live factorization evidence

At `2026-07-25 20:30 CST`, job `4004585` has passed ordering and reached Barrier
iteration 23:

```text
Ordering time: 3180.53 s
AA' NZ: 7.425e8
Factor NZ: 3.848e10
estimated factor memory: 340.0 GB
Factor Ops: 2.448e15
Threads: 32
MaxRSS: 499,919,116 KiB = 476.76 GiB
```

The residuals are decreasing, but no accepted solution exists. Slurm ends the job
at `2026-07-26 02:34:26 CST`, about 6:04 after this checkpoint. Because the
Gurobi 86,400-second limit begins after model construction, the Slurm wall limit
will arrive first. Do not interpret a later scheduler kill as mathematical
infeasibility, and do not extend the paid allocation or start another job without
explicit authorization.

## 2026-07-25 active Barrier-32 full-year diagnostic

User-authorized ParaCloud job `4004585` is the only active full-year retry. It uses
the immutable `22fb493` Base/`city_337` release and the additive script:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/cloud_cispo_8760_2030_base_barrier32.sbatch
SHA256 fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2
```

Relative to failed job `4003172`, change only:

```text
Gurobi Threads: 128 -> 32
Slurm CPUs/Task: 128 -> 32
job/log/output identity: new and isolated
```

Retain `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, 700G,
24h and every scientific setting. The output root is:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_barrier32_700g_v0725
```

Initial evidence at `2026-07-25 02:35 CST`: job `4004585` is `RUNNING` on
`m4cg1702`; 50/50 tests pass; the generated config records `threads=32`.
Because 700G forced an allocation of 96 CPU/billing units, do not estimate this
run at only 32 billed core-hours per wall-clock hour. Monitor with:

```bash
squeue -j 4004585 -o '%i|%j|%T|%M|%D|%C|%m|%R'
sstat -j 4004585.batch --format=JobID,AveCPU,MaxRSS,MaxVMSize
tail -n 80 cloud_cispo_8760_base_b32-4004585.out
tail -n 80 outputs/full_year_2030_base_22fb493_barrier32_700g_v0725/gurobi.log
```

The failed 128-thread job consumed `CPUTimeRAW=2,642,304` allocated CPU-seconds,
or 733.973 core-hours; actual `TotalCPU` was only 7:03:11. Slurm exposes this
usage but not the ParaCloud paid-credit or remaining currency balance.

Do not start 2040 or another retry. Accept only after terminal Slurm state plus
`solve_report.json`, `solution_qc.json` and `result_manifest.json`; reaching
`Barrier statistics`/iteration 0 is diagnostic progress but not scientific
acceptance.

## 2026-07-25 cloud full-year OOM boundary

Job `4003172` is terminal `OUT_OF_MEMORY`; do not resubmit its batch script unchanged.
The build-only gate is still valid, but the real solve proved that build memory is not a
barrier-factorization memory estimate.

Terminal facts:

```text
state: OUT_OF_MEMORY
exit: 0:125
elapsed: 05:44:03
request: 128 CPU / 700G
recorded MaxRSS: 526.99 GiB
presolve time: 17,932.25 s
presolved model: 37,982,903 rows / 35,423,761 columns / 400,861,556 nonzeros
terminal stage: ordering before barrier iteration 0
```

The absence of `solve_report.json`, `solution_qc.json` and `result_manifest.json` is
decisive. Preserve the failed root:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_128cpu_700g
```

`Crossover=0` is not a remedy because crossover was never reached. Raising only
`SoftMemLimit` is also unsupported: Slurm killed the step before the configured 640G
soft limit was reported. The 750G-class node rebooted shortly after the event, while
accounting captured only 526.99 GiB; require administrator evidence before interpreting
that value as the true peak.

Before another paid full-year attempt, first choose and validate a lower-memory solver
route on bounded gates or secure a genuinely larger-memory node. Any new 8760h submission
requires a new output identity, explicit user authorization and monitoring through
presolve, ordering, factorization, barrier and QC. Do not start 2040 from this failed
2030 root.

## 2026-07-25 existing-grid correction and combined wave/flexibility cases

This section supersedes the nearest-offshore-wind routing language in the older
wave section below. `scripts/build_wave_energy_inputs.py` must produce contract
`wave_existing_grid_v2`: only coordinate-matched rows already present in
`optimization_points.csv` with `is_land=0` are eligible. Require 1,285 unique
`grid_uid` rows, exact route equality with `city_337/vre_routes.csv`, maximum
coordinate difference no larger than `0.02` degrees, and the recorded source/table
SHA256 values. Never map source rows outside the optimization grid to a distant
in-model anchor.

Two reproducible combined cases are available:

```text
config/scenarios/wave_energy_medium_v1_flexible_load_v1.json
config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3.json
```

Each combined file enables wave and flexible load in one LP. Comparative Base,
single-module and combined cases remain separate sensitivity-suite runs with
separate output roots. Deployment still requires an explicitly authorized,
versioned release and fresh tests/preflight/24h build and solve-QC gates.

## 2026-07-25 `wave_energy_medium_v1` local-only deployment boundary

The optional wave module is not present in any accepted fixed-server or cloud release.
Base must keep `features.wave_energy=false`. Enabling the scenario requires three
separately verified artifacts:

```text
config/scenarios/wave_energy_medium_v1.json
data/wave/wave_sites.csv
data/wave/wave_input_manifest.json
```

and the external hourly source:

```bash
export CISPO_WAVE_ROOT=/versioned/path/to/wave_energy
test -f "$CISPO_WAVE_ROOT/wave_grid.nc"
```

Rebuild the small site contract locally before transfer:

```bash
$PYTHON scripts/build_wave_energy_inputs.py \
  --wave-netcdf /source/path/wave_grid.nc \
  --output-directory data/wave
```

Require the source and site-table SHA256 values in `wave_input_manifest.json`.
Do not interpret the nearest offshore-wind routing anchor as a maritime boundary or
engineering cable route. Do not claim scenario-specific potential: the current source
potential is identical across all ten CF scenarios. The configured 2060 profile/cost is
an explicit 2050 hold.

After separate deployment authorization, use a new release and output root. First run
tests, wave preflight and a 24h build-only gate. A later 24h optimization must additionally
pass wave availability, power balance, reserve, load-center closure, cost, cohort and
manifest checks. Do not share offshore-wind spur/trunk in this scenario. A successful
local build is not permission for server/cloud 24h, 168h, 744h or 8760h execution.

## 2026-07-24 `comfort_envelope_v3` local-only deployment boundary

The V3 implementation is an independent sensitivity and is not present in the fixed-server
checkout or active cloud release. It requires both code and the ignored generated input:

```text
data/load/flexible_load_envelope_v3.csv.gz
data/load/flexible_load_envelope_v3.manifest.json
```

Rebuild locally from the recorded `Power_curve_V2` products with:

```bash
$PYTHON scripts/build_flexible_load_envelope_v3.py
```

The accepted local table has 1,357,800 rows and SHA256
`b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
The input manifest must record both the scenario table and its sidecar. Never stage only the
scenario JSON: a missing or mismatched envelope must hard-fail.

Main and optional V2G scenario files are:

```text
config/scenarios/flexible_load_comfort_v3.json
config/scenarios/flexible_load_comfort_v3_v2g_5pct.json
```

The 5% value means 5% of each province-day baseline EV peak power, not 5% vehicle
participation and not a policy mandate. Main V3 keeps V2G disabled. The V2G sensitivity uses
`daily_zero_causal`, so it cannot borrow energy from the end of a day.

After explicit deployment authorization, create a new versioned code/data/output identity and
first require:

```bash
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_comfort_v3.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_comfort_v3
```

Acceptance additionally requires four valid input/result manifests, four
`OPTIMAL + solution_qc=PASS` years, `flexible_load_formulation=comfort_envelope_v3`,
closed thermal state and V1G backlog transitions, zero daily terminal state/backlog, zero
simultaneous up/down, correct cost components and four `RESUMED_ACCEPTED` records. Validate the
no-V2G main scenario before separately testing the 5% V2G case. A successful 24h local gate is
not permission for server 168h/744h/8760h or cloud execution.

## 2026-07-24 `flexible_load_state_v2` deployment boundary

Implementation `271c6dc` is local-only. It adds
`config/scenarios/flexible_load_state_v2.json` and does not change the accepted Base,
`flexible_load_v1` or `flexible_load_v2g_v1` configurations. Never update an active
server/cloud checkout or reuse an accepted output root for this code.

The new module uses `Power_curve_V2` load components already present in
`hourly_load_2025_2060.csv.gz`. Heating/cooling have causal daily-reset equivalent
inventories; EV V1G has a causal daily-reset charging backlog. Do not relabel
`ev_hour_weight` as vehicle availability. Configuration validation intentionally rejects
V2G in this formulation until hourly availability, usable battery energy and departure
service are provided.

After explicit deployment authorization, first verify an idle clean server and use a new
checkout/data/output identity. Minimum gates are:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_state_v2.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_state_v2
```

Require four `OPTIMAL + solution_qc=PASS` years, four valid result manifests,
`scenario_id=flexible_load_state_v2`, `flexible_load_formulation=state_envelope_v2`,
closed thermal/EV transitions, zero daily terminal state/backlog, no simultaneous
up/down, valid capacity-cohort hashes and four `RESUMED_ACCEPTED` records. Only then may
an explicitly authorized new 168h root start. The current full-year estimate is
43,356,367 variables/68,724,249 constraints/524,283,387 nonzeros; do not infer
fixed-server 744h/8760h or paid-cloud 8760h authorization from this estimate.

## 2026-07-24 local CF-fallback hardening deployment boundary

The local post-release change forbids cross-technology wind-to-PV CF fallback and adds hard preflight checks. It does not alter the currently staged cloud release and must not be copied into an active checkout or output root. Current production inputs already resolve all 45 wind primary-store gaps through same-grid `mixed_wind`; the patch therefore changes no current wind CF mapping or model scale. When deploying later, require a new versioned code/output identity, 54/54 local-equivalent tests, preflight checks `vre_cf_cross_technology_fallback=PASS` and `vre_cf_pv_fallback_uses_land_grid=PASS`, followed by new 24h and 168h gates.

## 2026-07-24 cloud execution state: accepted small gates and one authorized 2030 Base full-year job

The staged city_337 release now has accepted cloud gates `outputs/cloud_gate_24h_base_2030_22fb493` (`4003035`) and `outputs/cloud_gate_168h_base_2030_22fb493` (`4003045`). Both use the released code/data roots, `Threads=32`, pass 50/50 tests, reach `OPTIMAL`, pass QC and close their result manifests. Do not rerun into either root.

`4003088` completed the non-solving 8760h construction gate in 40m20s with exit `0:0`; its build report records 40,912,327 variables, 68,189,325 constraints, 515,040,080 nonzeros and 53.633 GiB peak process-tree RSS. The dependent real 2030 job `4003172` started normally on `m4cg1702`, using 128 CPU/700G/24h and root `outputs/full_year_2030_base_22fb493_128cpu_700g`. Its runtime configuration changes only `numerics.threads=128` and `numerics.soft_mem_limit_gb=640`; do not change any scientific model setting.

At 2026-07-24 21:17 CST, the solve job had completed the full model build in about 40m32s, entered Gurobi `Optimize`, and used 96.402 GiB batch MaxRSS. The log had not yet reached a presolve-complete line or barrier iteration. Continue monitoring Slurm accounting, Gurobi log and memory; `solve_report.json`, `solution_qc.json` and `result_manifest.json` were not yet present. Do not launch a successor planning year until the 2030 root is accepted.

## 2026-07-24 ParaCloud city_337 staged preflight (current cloud state)

The additive release is `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`; do not overwrite it. It contains code archive `National_model_22fb493.tar.gz`, the checksummed runtime roots `data/model_ready_20260723_v0722_city337`, `data/hourly_cf` and `data/hydro_timeseries_20260719_sequential_sparse`, and the source-to-cloud SHA256 manifest. The 2030 Base 8760h `--preflight-only` job `4001137` passed on a compute node with 175.17 GiB available memory; its scale is 40,912,327 variables, 67,604,064 constraints and 520,922,832 nonzeros. This proves neither model construction nor optimization.

Do not submit the staged `cloud_cispo_8760_preflight.sbatch` as a Gurobi build substitute. On 2026-07-24 the user-authorized `.bashrc` repair replaced malformed whitespace in its three proxy exports; its backup is `.bashrc.codex_backup_20260724_proxy_export`. Job `4002980` confirmed the proxy is inherited on `m4ci1905` and returns HTTP 302 through `172.16.110.3`; job `4002981` then completed the authenticated Gurobi WLS LP (`GUROBI_SMOKE_PASS`). Its short curl health probe timed out despite the successful solver authentication, so accept Gurobi's `Env.start()` plus `OPTIMAL` as the WLS gate. Retain explicit lower- and upper-case proxy exports in production batch scripts as defensive reproducibility.

Only after that smoke succeeds, use a new versioned 24h cloud root, then a new 168h root, both with `Threads <= --cpus-per-task`, full manifests and QC. A full-year `--build-only` is still a distinct later gate; it requires at least 96 GiB available memory and must not be treated as evidence that barrier factorization or a production solve fits. The raw GRFR source is deliberately not in this runtime release; add it only when running the separate raw-hydrology provenance readiness check.

## Accepted V0722 city_337 V2G gate

The Base, V1 and independent V2G 24h/168h gates are accepted for `city_337`. The accepted V2G 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` has four `OPTIMAL + solution_qc=PASS` years, four valid 59-entry manifests and four `RESUMED_ACCEPTED` records. The server is idle at checkout `cf39e0a` with data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. Revalidate without changing checkout:

```bash
OUT=/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1
pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py' || true
cat "$OUT/sequence_report.json"
```

The accepted chain has closed network/BECCS/security checks, V2G transition closure, zero simultaneous charge/discharge, explicit charging-loss accounting and an immediate four-year `--resume`. Keep `run.stdout`, `run.stderr` and `run.pid` as wrapper evidence. Do not launch fixed-server 744h/8760h.

## V0722 city_337 deployment and small-gate contract

Implementation `8e76753` changes the production spatial input contract from `natural_earth_278` to `city_337` and includes the reviewed 5% capacity-margin/3.5 s inertia baseline. Because `data/` is intentionally outside Git, deploy code and data as two independently verified artifacts. Never copy over the active V0721 data root.

Required new data files are `load_center_network/city_337/{load_centers,vre_routes,hydro_routes,intra_edges,initial_spur_capacity_2025,substation_initial_capacity_2025}.csv`; retain the package README, manifest, initialization audit and route comparison as sidecars. Verify the transferred archive SHA256 before extraction, copy the current data root to a new additive root, and extract only the `city_337` subdirectory there.

Before changing checkout, require `git status --short` empty and no `run_cispo`/Gurobi process. Then run, with the new data root and existing CF/hydrology roots:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_v0722_city337.json
$PYTHON scripts/run_cispo_planning_sequence.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337
```

Accept only if all four years are `OPTIMAL + solution_qc=PASS`, scenario ID is `base`, flexibility is disabled, every result manifest closes, load-center outputs contain 337 unique nodes, center/province/capacity residuals pass, security manifests record 5% and 3.5 s, and `--resume` returns four `RESUMED_ACCEPTED` years. Only then launch the corresponding new 168h Base root. Current live memory (about 35 GiB available with swap occupied) is sufficient only for these small gates; do not launch 744h/8760h on the fixed server.

## V0722 reviewed reliability update — not deployed

The local working tree at Git HEAD `e28f315` changes the feasible set: Base provincial capacity margin is `5%`, and minimum system inertia is recorded as `3.5 s reference × 1.0 tolerance = 3.5 s effective`. Model construction and QC share one resolver; legacy scenario overrides may still provide `minimum_system_inertia_seconds`.

Local regression validation is 49/49 PASS. The local 1h engineering gate `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS` and its result manifest validates. The fixed server remains at accepted checkout `6ed943a`, so every existing server output predates this reliability update. Never reuse an accepted output directory with the new configuration. After an explicit commit/push/deployment decision, first verify an idle clean server checkout, then use a new versioned 24h root and require:

- `model_config_snapshot.json` contains capacity margin `0.05` and the two inertia fields;
- `scenario_manifest.json.security_parameters.minimum_system_inertia_seconds_effective = 3.5`;
- `solution_qc.json.minimum_system_inertia_seconds = 3.5`;
- capacity-margin and inertia hard checks both pass;
- the result manifest closes with no size/SHA256 mismatch.

Do not start fixed-server 744h/8760h or paid cloud 8760h from this local-only state.

## V0722 BECCS carbon-accounting gate

Local commit `c62b769` explicitly closes the CISPO-equivalent BECCS carbon mass balance while retaining the published negative factors, 90% capture assumption and all capture/transport/storage costs. It is not deployed on the fixed server. Before deployment, verify an idle clean checkout and use a new versioned 1h/24h output root; do not reuse any accepted Base/V1 directory.

Acceptance requires the four `solution_qc.json` fields `maximum_beccs_capture_balance_residual_mtco2`, `maximum_beccs_storage_balance_residual_mtco2`, `maximum_beccs_net_carbon_balance_residual_mtco2` and `maximum_captured_co2_reconstruction_residual_mtco2` to pass, plus all six explicit BECCS columns in `annual_resource_accounting_by_province.csv` and a closed result manifest. Baseline lifecycle emissions are zero. A nonzero lifecycle factor is a separate sourced scenario and must not be inserted into Base silently.

## V0722 diagnostic sensitivity suite interface

Local commit `c91828a` adds `scripts/run_cispo_sensitivity_suite.py` as a diagnostic-only wrapper around the existing four-year planning sequence. It does not authorize 8760h and is not deployed on the fixed server; live checkout `6ed943a` remains the accepted Base/V1 model gate. The wrapper gives every scenario an independent state chain, records catalog/config SHA256 values, rejects planned-not-runnable entries and refuses a non-empty root unless `--resume` passes exact suite identity checks.

List or dry-run the implemented scenarios before any solve:

```bash
$PYTHON scripts/run_cispo_sensitivity_suite.py --list-scenarios
$PYTHON scripts/run_cispo_sensitivity_suite.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/sensitivity_suite_24h_<version> \
  --dry-run
```

An actual small gate uses the same command without `--dry-run`; an audit of an accepted root adds `--resume`. Resume must match the mode, diagnostic hours, scenario order, catalog/base-config hashes and each scenario-config hash. The prior suite report is preserved under `sensitivity_suite_history/`, and new timestamped stdout/stderr logs are created rather than overwriting operational evidence. Base must report flexibility disabled, V1 must report V2G disabled, and V2G must remain a separate scenario/root. Do not deploy or start even this small gate until the server is idle and its exact checkout is verified; do not use this wrapper for fixed-server 744h/8760h or paid cloud 8760h.

## V0722 deployed scenario interface

Commit `6ed943a` adds optional, checksummed scenario overrides without changing Base by default and is deployed on the fixed server. The pre-deployment Base 168h gate ran from checkout `b6ca42d`, containing model implementation `0c1eaf2`. Do not mix code versions inside an existing output root.

After deployment, a flexibility gate is selected explicitly:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 24 \
  --output-dir /data/zz2/National_model/outputs/flexible_load_v1_24h_gate
```

Require `scenario_manifest.json`, `flexible_load_dispatch.npz`, `annual_flexible_load_by_province.csv`, `solution_qc=PASS` and a closed result manifest. Full-year Base/V1/V2G estimates are 40.91M/42.54M/43.36M variables respectively; retain the 96 GiB pre-build gate because the static estimate does not bound barrier factor memory.

The fixed-server four-year 168h V1 gate is accepted at `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`. It completed in 1:06:54 with peak RSS 4,040,256 KiB and zero swap; every year is `OPTIMAL + solution_qc=PASS`, every 59-file result manifest validates, maximum daily heating/cooling/EV V1G residual is `8.17e-13 GWh`, and simultaneous up/down counts are zero. Revalidate the immutable chain only with:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 168 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1 \
  --resume
```

Acceptance of `--resume` requires four `RESUMED_ACCEPTED` records, the same `flexible_load_v1` scenario ID/SHA256, closed result manifests and matching `capacity_cohorts_v2` state hashes. Never rerun without `--resume` into these accepted directories. The fixed server remains restricted to small gates; do not launch 744h/8760h there. V2G is an independent optional scenario and must use a new output root.

## V0721 production I/O and acceptance contract

Implementation `0c1eaf2` remains the production I/O/state-acceptance baseline contained by the current fixed-server checkout `6ed943a`. Read `README.md` and `MODEL_IO_CONTRACT.md` before scheduling an expensive case. A case is accepted only when all of the following hold:

- `solve_report.json`: `status=OPTIMAL` and `result_use=SCIENTIFIC_PRODUCTION`;
- `solution_qc.json`: `status=PASS` and every hard check is true;
- `result_manifest.json` validates every scientific output by byte size and SHA256;
- `output_catalog.csv`, `output_data_dictionary.csv`, `model_config_snapshot.json`, `run_environment.json` and `input_manifest.csv` are present;
- the next planning year loads `planning_state/state_metadata.json` and verifies the source solve, source QC, cohort table and transition summary hashes.

Wrapper-owned files such as `run.stdout`, `run.time`, PID and scheduler logs must not be included in the scientific manifest because wrappers can append after model finalization. Preserve them next to the case as operational evidence.

The fixed server is limited to small regression gates for this phase. Use a new versioned output directory for 24h/168h, and do not launch 744h/8760h there. Production 8760h is reserved for the cloud compute node after Gurobi license, data hashes, current regression/smoke checks and 24h/168h solves have passed.

## V0719 capacity-bound/DC-sparse deployment gate

V0719 adds three required data tables and changes the in-memory reverse-flow index. It must be deployed only after the local working tree is committed and the currently active `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` task has completed or been explicitly preserved. Never rebuild the active `model_ready_20260719_sequential_sparse` directory in place.

After the implementation commit is pushed and the server checkout is fast-forwarded, create an additive data version and generate only the three new bound tables:

```bash
OLD_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse
NEW_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
test -d "$OLD_DATA_ROOT"
test ! -e "$NEW_DATA_ROOT"
cp -a "$OLD_DATA_ROOT" "$NEW_DATA_ROOT"

cd /data/zz2/National_model/repo
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/build_v0719_capacity_bounds.py --data-root "$NEW_DATA_ROOT"
export CISPO_DATA_ROOT="$NEW_DATA_ROOT"
$PYTHON scripts/smoke_test_data_package.py
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
```

Acceptance requires 32/32 unit tests, 139/139 data smoke checks and readiness PASS. Confirm the generated national totals before solving:

- nuclear upper 2030/2040/2050/2060 = `110/205/300/300 GW`;
- battery floor 2030 = `65.85 GW`, later exogenous floors = 0;
- `bio+bioccs` shared capacity upper is never below inherited pair capacity; the current expected safeguard is Shanghai in four planning years.

Then run new output directories in order: 24h, 168h and corrected 744h. Each must report zero nuclear floor/upper violation, zero biomass/BECCS shared-capacity violation, zero storage-floor violation, zero AC simultaneous bidirectionality and zero DC reverse flow. Do not launch 8760 before corrected 744h acceptance and the 96 GiB available-memory gate.

## 2026-07-19 deployment note

Implementation commit `1b6da28` supersedes the previously deployed formulation. PID `3778049` completed mathematically `OPTIMAL`, but post-audit rejected it because the former QC did not fail 3,358 material AC bidirectional edge-hours. Do not reuse that result as a solver/model gate.

The corrected server gate `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu` is `OPTIMAL/QC PASS`: zero AC bidirectional edge-hours, zero DC reverse flow on 363 DC edges and a closed scientific manifest. Server tests passed 26/26. A corrected 744h run is still required.

The updated data root must include `storage/phs_capacity_bounds_by_province_year.csv`. Use `config/model_input_files.json` as the minimal table contract. The code transfer archive must be created from tracked files after the implementation commit; do not package untracked workspace directories.

Production architecture is one continuous LP containing 2030 capacity decisions and all 8760 chronological hours. The 2025 data are boundary conditions only. No Benders decomposition, representative periods, or temporal weights are used.

## Server layout

- Repository: `/data/zz2/National_model/repo`
- Model-ready tables: `/data/zz2/National_model/data/model_ready`
- Capacity factors: `/data/zz2/National_model/data/hourly_cf`
- Hydrology: `/data/zz2/National_model/data/hydro_timeseries`
- Raw 2019 GRFR source: `/data/zz2/National_model/data/grfr_raw_2019`
- Python environment: `/home/zz2/.local/envs/cispo-2030`
- Gurobi Optimizer: `/home/zz2/opt/gurobi1302/linux64`
- Gurobi license: `/home/zz2/gurobi.lic` (mode `600`)
- Environment definition: `/data/zz2/National_model/repo/env/cispo-server.yml`
- Outputs: `/data/zz2/National_model/outputs`
- Logs and manifests: `/data/zz2/National_model/logs`, `/data/zz2/National_model/manifests`

The `/data` filesystem is NTFS/fuseblk and does not enforce normal Unix ownership or mode bits. Do not store SSH keys or `gurobi.lic` there.

Current versioned model and hydropower data:

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
```

The versioned data roots remain current. Fixed-server HEAD `b40900a` passes 34 regression tests, 139 smoke checks and the V0720 24h I/O-contract gate. Do not schedule another 744h run on this host.

## Long-term Git synchronization

- Bare remote: `/home/zz2/git/National_model.git`
- Local `origin`: `ssh://zz2@210.77.85.166/home/zz2/git/National_model.git`
- Active branch: `codex/cispo-2030-full-lp`

Normal local-to-server workflow:

```bash
# Local workstation
git pull --ff-only
git push origin codex/cispo-2030-full-lp

# Server working copy
cd /data/zz2/National_model/repo
git pull --ff-only
```

If code is edited on the server, commit and push it before pulling locally. Model data, capacity-factor Zarr stores, hydrology, outputs, licenses and environments remain outside Git.

## Environment and data gates

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_2030.json
```

For the pending cascade version, the model-ready data root must include:

- `hydro/cascade_topology_nodes.csv`
- `hydro/cascade_topology_edges.csv`

The readiness gate now reports cascade node/edge counts, low-correlation lag edges, max-bound lag edges and maximum travel lag. A valid cascade server bundle should report 142 nodes, 124 edges, 4 low-correlation lag warnings, 18 max-bound lag warnings and no missing required cascade columns.

The server uses Gurobi Optimizer and `gurobipy` 13.0.2. Store the license file under the protected home directory, not `/data`. Do not commit the license file or activation key.

```bash
export GUROBI_HOME=/home/zz2/opt/gurobi1302/linux64
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
chmod 600 /home/zz2/gurobi.lic
$PYTHON scripts/check_gurobi_full_license.py
```

The license gate deliberately solves an LP with 2,501 variables. A size-limited fallback license must fail this check; package import or a two-variable solve is not sufficient evidence for production readiness.

Install test-only dependencies with `$PYTHON -m pip install -r requirements-test.txt`, then run `$PYTHON -m pytest -q`. The production dependency file intentionally excludes `pytest`.

As verified on 2026-07-06, direct server access to PyPI fails certificate-chain validation. Do not bypass TLS with `--trusted-host` or disabled verification. Download Linux/Python 3.11 wheels on a trusted workstation, record SHA256 hashes, upload them, and install with `--no-index --find-links=<wheel-directory>` until the institutional CA chain is repaired.

## Selectable optimization horizons

| Horizon | Hours | Intended use | Minimum available RAM |
|---|---:|---|---:|
| `one_month` | 744 | Local code/solver test only | 8 GiB |
| `six_months` | 4344 | Large integration test only | 32 GiB |
| `full_year` | 8760 | Production scientific run/build gate | 96 GiB |

The truncated horizons use the leading hours and a cyclic boundary over the selected interval. Annual investment costs, carbon limits and biomass limits are not rescaled. Their solutions therefore must not be interpreted as planning results.

Preflight without requiring Gurobi:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only
```

## Current 744h cascade gate

The active corrected gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
pgrep -P "$PID" -a
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/build_report.json" "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

It was launched from implementation `5a9f4ab` after the strict 168h gate reached `OPTIMAL/QC PASS`. At launch `/usr/bin/time` PID was `3344086`, Python child PID was `3344087`, and about 116 GiB RAM was available. Do not infer completion from PID exit alone; require both reports and inspect QC.

The old output below is a preserved failed numerical baseline and must not be reused:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_hydro_cascade
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

PID `244035` was normally interrupted on 2026-07-07 after `37,576.53 s`; it produced no solution. Do not delete this directory.

The following completed output is a preserved rejected baseline:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

Its former `solution_qc=PASS` is insufficient. Acceptance now additionally requires zero AC bidirectional edge-hours above `1e-6 GW`, zero DC reverse flow, closed load-center net exchange and a closed result manifest. CISPO's `0.001 yuan/kWh` flow penalty is configured as `1 yuan/MWh`; DC corridors have reverse UB zero, while AC corridors retain the S4-56 shared-capacity constraint.

Before launching the corrected 744h gate, require at least 64 GiB available RAM and verify that swap/shared jobs no longer leave the host under pressure. The rejected 744h reached 22.141 GiB peak process-tree RSS despite a lower preflight estimate.

Do not set `Crossover=0` for acceptance: the option was retested on the current corrected model and returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. `Threads=-1` exposes all 96 logical processors; Gurobi barrier uses the 48 physical cores. GPU-enabled Gurobi is installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu`; it confirmed `Start PDHG on GPU`, but the same 24h P30 model was still iterating after about 600 s and was interrupted. CPU barrier remains the default route.

A diagnostic candidate using `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7` and `Crossover=1` passed the current 24h QC in 37.38 s, about 7% faster than the strict local baseline. Do not promote it from 24h evidence: Gurobi warns that looser barrier termination can prolong crossover. Compare it at corrected 168h/744h and retain only if objective, capacity decisions and every hard QC remain acceptable.

`NodefileStart` does not solve this model's memory problem because this is an LP without branch-and-bound nodes. For normal production solves, benchmark default `DualReductions`/`InfUnbdInfo` behavior; use `DualReductions=0`, `InfUnbdInfo=1` and homogeneous-barrier diagnostics only after an infeasible-or-unbounded status. See `MODEL_SOLVABILITY_AUDIT_20260719.md` for the parameter matrix.

## Full model

The revised current-code projection is about 44.09 million variables, 68.19 million constraints and 515-524 million nonzeros. The old 744h factorization already used about 10 GB for factor nonzeros; linear extrapolation is about 118 GB for this component alone. Require at least 96 GiB available RAM for build-only, and do not optimize immediately after a successful build.

Build without optimizing:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --build-only --output-dir /data/zz2/National_model/outputs/2030_full_year_build
```

Solve:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --output-dir /data/zz2/National_model/outputs/2030_full_year
```

The runtime gate refuses to build when available memory is below the checked-in 96 GiB threshold. This is a build scheduling gate, not proof that barrier factorization fits. For infeasibility, the solve path writes `iis.ilp`; production constraints are not silently relaxed.

Successful solves additionally write `solution_qc.json`, compressed hourly province balances, technology dispatch arrays, station-indexed reservoir dispatch, transmission flows, annual carbon/CCS accounts and objective cost decomposition. A solution is not accepted as production output unless `solution_qc.json` reports `PASS`.

## Sequential 2030-2060 production path

After the revised 744h gate and 8760 build-only gate pass, run a single year as:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir /data/zz2/National_model/outputs/planning_sequence/2030
```

Only `OPTIMAL + solution_qc PASS` full-year runs write `planning_state/`. The isolated sequential driver releases each year's process memory before the next year:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence
```

Resume only already accepted years:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence \
  --resume
```

The driver stops at the first non-optimal/QC-failed year. Do not manually copy an unchecked state directory or bypass its SHA256/year-boundary validation.
