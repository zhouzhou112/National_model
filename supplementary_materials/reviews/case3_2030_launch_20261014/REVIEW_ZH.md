# case3 2030 生产部署核准（2026-10-14）

## 2026-10-14 L1–L4 完成，L5 仅获 held 提交授权

依据作者本轮指令、`TASK_case3_2030_production_launch_20261014.md` 和已更新的 `AGENTS.md` 晚节第 7 条，case3、`_nocredit` 与 C 全部年份采用 Base 生产数值设置，只改 `Aggregate=0`。这取代此前夜间实验中按温和候选顺序得到的 `AggFill=0` 建议；旧实验记录保留。F5 自然结束，仅作参考，不追加 F9。

本轮目标是两个 2030 作业的 held 部署；作者明确回复“放行”前不 release。P1–P5 按最新任务书留在作业运行期间，其中 `relative_v1` 扩展采用离线评估，不回写冻结源码。未操作 Job 5124127、T550 `cloud_backup` 或 F5；不读取凭据，不建立后台监听、回查或自动提交。

### 模型与比较范围

全国 31 省、V9 共同 2025 边界、2030 规划年，生产时间尺度为连续 8760h。既有容量与逐小时运行决策、供需/网络/备用/惯量/碳排放/水库/储能约束及年度总成本目标沿用，功率 GW、电量 GWh、成本 million 2025 CNY/year。新增入口只将筛出的 `vre_new_gw` 新建上界置零；未修改物理模型、输入数据或单位。24h 周期窗口仅作工程门禁，不作规划解释。

### L1–L4 核准结果

|门禁|结果|证据|
|---|---|---|
|L1 筛选生产化|PASS；新 profile 数值与 Base 仅 Aggregate 不同，生产 48 线程，局部门禁 8 线程|新 profile、`test_production_screen.py`、`final_gates.json`|
|完整回归|440 项，OK，跳过 1 项，163.342 秒|`unit_tests_final.stderr.log`|
|L2 参数核准|76 项 PASS；两个情景物理配置只差容量信用，ID/说明/角色另列|`parameters_05/parameter_verification_2030.json`、`PARAMETERS_ZH.md`|
|L3 Base 1h|修改前及最终代码复验均 PASS；全部 MPS 段 SHA 相同|`base_identity_final/base_identity.json`|
|L3 零签约 24h|两侧 OPTIMAL；目标相对差 1.1409671441444699e-14；柔性决策严格为 0|`zero_identity_01.json`|
|L3 筛选 1h|只有 BOUNDS_VRE_NEW 段变化；剔除 20,272 列|`screen_identity_01.json`|
|L4 case3 24h|OPTIMAL，M=1.1204230761761597e-8；信用边界最大违反 8.206036961055929e-10 GW；保全 COMPLETE|`case3_24h_01/engineering_gate.json`|
|L4 nocredit 24h|OPTIMAL，M=1.1769423379675084e-8；不创建信用变量；保全 COMPLETE|`nocredit_24h_01/engineering_gate.json`|

M 沿用夜间实验完整服务残差定义，覆盖冷热/EV 库存界、转移、控制包络等 GW/GWh 量；信用约束另审计。两份 `solution_qc.json` 均含 `acceptance_profiles.relative_v1`；QC 只作参考，原模型、BarX/BarPi、候选状态、运行日志与筛选清单完整保全。生产入口即使 QC 失败也执行独立保全，不据标签丢弃数据；是否采用由作者决定。

### 参数核准摘要

|项目|2030 核准值|
|---|---|
|基础配置/父基线|V9 / base_2024_numeric_water_dac_by_year_20260913_v9|
|参与率|heating 0.25；cooling 0.20；V1G 0.20；V2G 全车队 0.10|
|V2G 全国签约上限|10 GW|
|冷热库存|每小时保留 0.94/0.92；持续 4/5 h；舒适带 ±1°C|
|冷热成本|签约 40 CNY/kW·年；释放 40 CNY/MWh；预调节 0；legacy_bidirectional_activation=false|
|V1G|签约 40；搬移 30；功率比例 2；效率 0.94；库存 24h|
|V2G|可用性 50+设施 40；车主 150+退化 150；持续 4h|
|case3 信用|firm_flexibility_derated_v1；冷/热/V1G/V2G=0.60/0.50/0.50/0.50；基准峰值所在 4h 窗|
|nocredit 信用|baseline_peak_v1；信用变量不创建|
|求解器|Method=2，Presolve=2，Aggregate=0，Crossover=0，SolutionTarget=1，BarConvTol=1e-4，NumericFocus=2，ScaleFlag=2，48 线程；无限时，无 SoftMemLimit|

未筛选 case3 科学指纹仍为 `324d98cc7f4154e21fdcfcdb48768016c53ad59ffd9a7d513286e04c8a9739a1`。筛选后科学身份额外包含源 CSV/BarPi/release、margin 与实际保留/剔除规模，指纹因此有意变化。`participation_pathway_v2` manifest SHA 为 `156cd5e972af5688ed94c25bf55ee13687c2fb6db3fce8995cdc86375200d492`。

源 Base BarPi SHA：`f2aa7651125202126e3c20ae8b60e03ac721d7e3d82c295b6cbcee1f80800b5e`；筛选 CSV SHA：`fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368`。margin=0.2；当前可扩展 34,439 列，保留 14,167 列，剔除 20,272 列、39,341.39949215136 GW 余量。逐列原上界和筛选标志保存在每个输出的 `candidate_selection.csv`，不将原模型或大向量提交 Git。

残留配置成本 300/400 不进入 V5 目标：对实际 1h MPS 检查了冷热预调节 0、释放 0.04、V1G 搬移 0.03、V2G 放电 0.30 million CNY/GWh 系数；输入表中的冷热 legacy activation=300 同样未进入 directional 公式。

### 差异、修复和保全记录

- `base_identity_01` 因旧生产 profile 禁止短窗而在构建前停止；后续两侧使用同一 V9 原配置做 build-only，不求解、不改旧 profile，`base_identity_02` 和最终复验均通过。
- 参数脚本初版误用不存在的解析键，后改为实际 by-year 上限和 SHA 链接的上游舒适带 manifest。`parameters_03/04` 的目标检查误找未压缩变量名，后使用实际 `_active` 名称并核对选窗零控制支撑；保留原记录。`parameters_05` 复用原始构建并核对解析配置相同，不重复改模型或计算解。
- `zero24_01` 初版最大值误包括两组常量上界；`zero_identity_01.json` 明确排除常量、列出全部决策键并复核严格为零，不覆盖旧报告。
- 新生产保全分支最初不兼容异常测试的空 config，已修复；`unit_tests_02` 439 项通过。附加回归 `unit_tests_03` 因同时本机构建令可用内存 7.9 GiB 低于原 8 GiB 门槛而失败；未降门槛，构建完成后最终 440 项串行回归通过。
- 修复输入溯源遗漏：`io_contract.py` 原先只登记 V4 的覆盖路径，现同时登记实际 V5 的 5 表及 manifest；数据与物理矩阵未变。早期门禁的旧清单保留，新生产 preflight 使用完整清单，L2 已独立核验实际载入的 V5 数据。
- Windows 文本管道给远端 Bash 引入 CRLF 的语法检查失败记录保留；按原文件 LF 字节传输后 `bash -n` PASS。冻结包使用 Git 的 LF 字节。

### 可复现入口与后续

`check_base_identity.py --output NEW` 执行源码 SHA 和 Base 1h 对照；`scripts/verify_case3_parameters.py --output NEW` 核准实际输入与两份 1h 构建；`run_engineering_gate.py --case base|zero|case3|nocredit --output NEW` 运行单个有限 24h 门禁。完整命令及原始输出留在本目录，所有目录均新建、从不覆盖或删除。

`deploy_held.py prepare|preflight|submit --case case3|nocredit` 在 L1–L4 全通过且源码提交后才允许执行；只包含 held 提交，没有 release 操作。两个 release 均使用同一源码提交，完整 SHA 将在部署条目追加。

每个作业申请 64 CPU / 750G / UNLIMITED / no-requeue，求解 48 线程，启动可用内存须 ≥700 GiB。历史筛选后 Aggregate=1 峰值 RSS 680.804 GiB；744h Aggregate=0 的 Factor NZ +3.8%、RSS 近似不变，余量有限，不能视为全年峰值上界或 OOM 保证。

P1–P5 尚未执行，待作者放行、作业运行期间继续；C2050 完成其前置门禁后也仅 held 提交并汇报。
