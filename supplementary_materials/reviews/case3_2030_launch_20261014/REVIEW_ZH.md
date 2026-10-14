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

## 2026-10-14 英国21:46：case3 held 提交

源码提交 `62bba5928f9db3c6d947e33350d5e08bd9bec01d` 已推送 GitHub 工作分支和 main。case3 release 为 `20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1`，385 个源码文件、55 个数据文件 SHA 核验通过，云端 preflight_v2 PASS。作业 `5153878` 为 PENDING / JobHeldUser，ReqTRES cpu64/mem750G/node1/billing64，TimeLimit=UNLIMITED、Requeue=0、AllocTRES=null、released=false。nocredit 包尚在传输，此条不代表两作业已齐备。

首次 preflight 误把 --archive-original-model 与 --preflight-only 同用，被入口在构建前拒绝；仅修正本地部署工具的调用参数，改用独立 preflight_v2 目录和日志，冻结源码及原失败日志均保留。生产 batch 的归档选项保留。工具修复将随最终部署记录提交，不改变 release 的源码提交。

## 2026-10-14 英国21:52（20:52 UTC）：L5 两作业 held 完成，等待作者放行

L1–L4 PASS，两个 release 都冻结自已推送源码 `62bba5928f9db3c6d947e33350d5e08bd9bec01d`。每份 385 个源码文件、55 个必需数据文件 SHA 通过，云端 preflight_v2 均 PASS。远端小证据按原字节 SHA 下载核验；与本地核准输入比较，9 项 capacity_factor_store 身份、3 项 hydrology_timeseries 身份完全一致，并登记实际 V5 六个覆盖路径。

|情景|release（云端 National_model_cloud 下）|Job ID|状态|
|---|---|---|---|
|case3_thermal_ev_v5|20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1|5153878|PENDING / JobHeldUser|
|case3_thermal_ev_v5_nocredit|20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1|5153901|PENDING / JobHeldUser|

共享 source manifest SHA256：`ec8fa5906eff941c60cee0b9cb905adb18500641a24e493d39e00c2003d09e7c`。

- case3 release manifest SHA256：`90e4f9f89cc798d1c4eebc576ea24de97dc70481eb9ed838f503e49ceae0166c`。
- nocredit release manifest SHA256：`d7bfbe0db90fc48de9086a029cff24ee0b991711ab3d2334c5d22669c4dade1c`。

两个作业均已再次只读核验：`ReqTRES=cpu=64,mem=750G,node=1,billing=64`，`TimeLimit=UNLIMITED`，`Requeue=0`，`AllocTRES=(null)`；没有执行 release。生产 48 线程、Aggregate=0、筛选 margin=0.2，共同 V9/2025 边界；其余数值设置逐键等于 Base。每作业启动可用内存门槛为 700 GiB；实际分配待作者放行并启动后核对，不能用 ReqTRES 冒充 AllocTRES。历史筛选 Aggregate=1 峰值 680.804 GiB，744h Aggregate=0 Factor NZ +3.8%，全年内存余量有限，短窗证据不构成峰值上界。

操作证据为 `deployment_case3/`、`deployment_nocredit/` 中 `launch_config.json`、`frozen_release.json`、`cloud_preflight.json`、`held_submission.json`、`remote_evidence_sha256.json`、`local_cloud_input_check.json`，以及 `both_held_verified.json`。命令为 `deploy_held.py prepare|preflight|submit --case case3|nocredit`，其中 submit 使用 `sbatch --hold`；仅修复本地 preflight 调用参数，未修改已冻结源码。此轮不重新求解，引用源码 SHA 不变的 440 项回归与既有门禁证据。原模型、解、BarX/BarPi、大包及全部运行日志保留在原目录，小证据随 Git 提交。

下一动作仅在作者回复“放行”后 release 这两个确切 Job ID，再核验 AllocTRES 与启动内存。作业运行期间继续 P1–P5；C2050 通过独立门禁后同样 held 汇报。F5 自然结束后只留参考记录，不追加 F9；取消的定时回查不恢复。本轮未操作 Job5124127、旧冻结源码、T550 cloud_backup 或凭据。
