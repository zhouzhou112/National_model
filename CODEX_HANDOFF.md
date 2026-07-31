# CISPO model Codex handoff and version log

This is the repository's single handoff document for work continued across Codex windows. It records only verified, reproducible project state. New windows must read this file before taking action.

## Handoff update protocol

- Maintain `Current validated snapshot` as the concise active state.
- Append one entry under `Version history` after every material milestone.
- Each entry must include date, Git commit, scope, changed files, verification evidence, unresolved issues and next action.
- Link to detailed specifications rather than duplicating long derivations.
- Never include activation keys, passwords, private keys or the contents of `gurobi.lic`.

## Current validated snapshot

- 2026-07-31 12:45+08:00 当前输出语义修复与匹配 24 h/168 h
  Base--V5 门禁已在固定服务器闭合。当前本地、`origin`、GitHub 与服务器
  checkout 一致为 clean task identity
  `ae3356391ec55376b041d6a356ea2d1f26be88bc`；本地工作树仍仅保留用户拥有的
  `supplementary_materials/**`、`.codex_tmp/**` 等无关改动。该提交把
  service-constrained V4/V5 不适用的旧式
  `maximum_ev_v1g_daily_energy_residual_gwh` 显式输出为 `null`，新增
  applicability 字段，并修正 dashboard 对严格零与小于 0.001 GWh 数值的
  显示；没有改变 LP 变量、约束、目标、输入或 solver 参数。
- 本地与服务器完整回归均为 `165/165 PASS`；readiness、release contract、
  V5 input 与水电审计全部 PASS。常规水电仍精确闭合为
  `297.8895 + 82.1105 = 380.0000 GW`。本机 available RAM 约
  `7.91 GiB < 8 GiB`，故没有降低门槛或强行在 Windows 本机启动 solver。
- 当前提交的 2030/24 h Base 与 V5 production-profile 根分别为
  `/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_base_v2prod_v1`
  和
  `/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_v5_v2prod_v1`。
  两根均为 `OPTIMAL + solution_qc=PASS + 58/58 + current input +
  valid result manifest + wrapper exit 0/stderr 0`；solver runtime 为
  `407.321/420.232 s`，整轮 wall 为 `7:28.51/7:44.38`，peak
  process-tree RSS 为 `0.761/0.794 GiB`。V5 相对 Base 的 24 h solver
  增量约 3.2%，没有出现新增的数值爆炸。
- 当前 2030/168 h 匹配根为
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v2prod_v1`、
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v3stable_v1`
  与
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_v5_v3stable_v1`。
  三根全部达到 `OPTIMAL + PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0`。Base v2、Base v3、V5 v3 的 solver
  runtime 分别为 `907.672/917.121/1024.510 s`，wall 为
  `16:54.30/17:03.75/18:54.89`，peak process-tree RSS 为
  `3.336/3.328/3.508 GiB`；Barrier/simplex 分别为
  `213/211003`、`213/185333`、`232/258814`。Base v2/v3 objective
  仅差 `2.9e-7 million CNY`，证明 `CrossoverBasis=1` 没有改变科学解。
- 结构压缩 V5 的 168 h optimize() 仍由代码合同要求
  `CrossoverBasis=1`。一次显式的 V5/v2 尝试在求解前按预期被 guard
  拒绝，控制根
  `/data/zz2/National_model/run_control/2030_168h_v0731_ae33563_v5_v2prod_v1`
  记录 `exit=1`、wall `0:09.41` 与精确 RuntimeError；它不是失败求解或
  可接受结果，不得补写 result manifest。V5 的可用长时段候选仍是
  `barrier_16_auto_order_stable_basis_v3`，尚未自动晋升为全年
  production profile。
- 同 profile 的 168 h V5 相对 Base：objective 降低
  `298.097 million CNY`，bio/coal/gas 发电容量合计减少约
  `2.915 GW`，对应保守 firm-flex credit `2.891320 GW`；所选窗口全国
  effective peak 下降 `1.663365 GW`。adequacy 仍以完整 8760 h immutable
  baseline peak 为基准，只允许折减 firm credit，不直接以 effective peak
  降容。V5 的物理 EV fleet 充电 `756.192 GWh`、V1G relocated
  `193.242 GWh`、V2G export `1.178 GWh`；兼容字段
  `ev_v2g_charge_gwh=0` 在 V5 明确不适用，能量由同一 fleet SOC 与
  mobility charging 闭合，SOC transition residual 为
  `2.537e-13 GWh`。
- 冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、碳/CCS/BECCS
  与成本 accounting scope 均通过 hard QC。电池/PHS 在 168 h 内均有非零
  充放电且同充同放为零；水电 380 GW 闭合；网络对冲流与 DC 反向流为零；
  碳上限按 `168/8760` 缩放至 `76.712329 MtCO2` 并 binding；objective
  component residual 为 `-1.774e-7 million CNY`。wave 已启用但本窗口
  最优装机/发电为零，不是缺少输入。需保留两项解释边界：首周冬季没有实际
  冷热移峰，但广东 cooling 合同仍从完整全年峰窗获得 `0.3044 GW` firm
  credit；梯级水文审计虽代数闭合，raw negative-local-inflow clipping
  等价水量仍为 `974.405 million m3`、实际 routed adjustment 为
  `669.451 million m3`，属于后续科学数据敏感性而非本轮 solver bug。
- 终态实时复核：服务器 clean `ae33563`、无 CISPO/Gurobi 进程、available
  RAM 约 `114 GiB`、swap `780 MiB/2 GiB`、第二个 `vmstat` 样本
  `si/so=0/0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。
  所有 24 h/168 h 根仍严格标记 `TEST_ONLY_TRUNCATED_HORIZON`。精确下一步
  是由作者决定是否在 `stable_basis_v3` 上运行全新、串行的四年 168 h
  Base/V5 sequence，或据此批准单一更长门禁；本里程碑不自动启动
  744/1008/8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。

- 2026-07-31 10:15+08:00 固定结果查阅环节已实现并通过最终服务器门禁。
  实现提交为 `336116b493cf92eb461d1a2aab490678fd2dbac5`，最终解释修正为
  `bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`。每个正常完成的运行现在
  在 result manifest 定稿前自动生成
  `result_dashboard_summary.json`、`result_analysis_metrics.csv` 与
  `visualizations/core_result_dashboard.svg`，三项均进入
  `output_catalog.csv` 和最终 SHA256 `result_manifest.json`。独立脚本
  `scripts/build_result_dashboard.py` 可在不改动历史结果根的外部目录
  补充渲染 SVG/PNG/PDF。
- 本轮结果查阅实现不创建或修改任何 LP 变量、约束、目标系数、输入参数或
  solver 参数。此前数值稳定化仍保持冷热服务库存、V1G 充电调度、V2G
  SOC/驾驶取能、付费合同和 firm capacity credit 的既定模式；零控制状态和
  严格冗余行/列是代数等价消元。需要精确区分的是，数值稳定化里唯一新增的
  物理不等式为 `charge + discharge <= connected * K_v1g`，用于禁止
  V1G/V2G 同时重复占用同一签约连接；它不改变服务定义，但确实封闭了原来
  缺失的共享接入上限，且已有独立 hard QC。
- 成本强度分母固定为不可变 baseline electricity demand，保证 Base/V5
  可比，换算恒等式为 `1 million CNY / GWh = 1 CNY/kWh`。8760 h 才允许
  报告“年化规划成本 + 全年运行成本”的 total system cost intensity；
  截断门禁只分别报告 annualized-planning intensity 与
  selected-horizon operating intensity，二者不得相加或称为 LCOE。
  成本明细会排除 composite `annual_operation` 重复汇总项，并要求详细成本
  对 objective 的重构残差在容差内，否则 dashboard 生成失败。
- 本地完整回归在正确 `CISPO_WAVE_ROOT` 下为 `162/162 PASS`；本机当时
  available RAM `7.64 GiB < 8 GiB`，故没有降低内存门槛或强行启动新本地
  solver。既有 24 h V5 输出只读复演已在外部目录成功生成 SVG/PNG/PDF。
  固定服务器在 `bdb57b2` 上运行的最终 2030/V5 1 h 根
  `/data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`
  为 `OPTIMAL + solution_qc=PASS + 58/58`，input/result manifest
  validator 均为 `(True, [])`，wrapper exit `0`、stderr `0 bytes`、wall
  `0:39.10`、MaxRSS `597,624 KiB`、swaps `0`。solver runtime
  `7.352116 s`，Barrier/simplex 为 `96/1,716`，最大
  constraint/bound/dual violation 为
  `0/4.441e-16/0`。
- 最终 dashboard 的规划成本强度为 `0.2003156 CNY/kWh`，所选 1 h
  运行成本强度为 `0.3141334 CNY/kWh`，全年综合值为 `null`；objective
  重构残差仅 `-9.779e-9 million CNY`。所选 1 h 全国 baseline/effective
  peak 都是 `1150.7158 GW`，而 `2.8741 GW` firm credit 来自各省完整
  8760 h baseline peak windows 与折减率，dashboard 已明确说明两者不能
  直接比较。冷热状态、EV SOC、V1G/V2G nesting/共享连接、储能、网络、
  备用、惯量、碳/CCS、梯级水电和成本 hard checks 全部通过。
- 2026-07-31 10:15 实时复核服务器 checkout clean、无 CISPO/Gurobi
  进程、available RAM 约 `114 GiB`、swap `780 MiB/2 GiB` 且第二个
  `vmstat` 样本 `si/so=0/0`、memory PSI 0；ParaCloud
  `squeue -u a8s001819` 为空。该 1 h 根仍严格标记
  `TEST_ONLY_TRUNCATED_HORIZON`。结果查阅 bug 已闭合，但它不证明
  8760 h 可解性；下一次获准的 24/168/更长门禁应直接复用该固定输出环节，
  不自动启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

- 2026-07-31 05:14+08:00 固定服务器数值稳定化门禁已严格闭合。实现提交
  `fead34334153eca32bbf7ec3651f3388038ac04b` 与前一文档 tip
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8` 已双端推送，服务器 checkout
  为 clean `22e19c1`。服务器完整回归 `159/159 PASS`，readiness、release、
  V5 input、水电输入与 `297.8895 + 82.1105 = 380.0000 GW` 审计均 PASS。
  新建的 2030 Base/V5 1 h 与 24 h 四根全部达到
  `OPTIMAL + solution_qc=PASS + 58/58 + current input manifest +
  valid result manifest + wrapper exit 0`。1 h Base/V5 solver runtime 为
  `7.707/7.316 s`；24 h 为 `408.850/421.015 s`，V5 相对 Base 只增加
  5,321 variables、5,934 rows、30,045 nonzeros、约 3.0% solver time 和
  0.032 GiB RSS。24 h 两根仍在 Barrier 后报告共同的
  `Numerical trouble`，随后由 `Crossover=1` 严格恢复，故该共享数值债不能
  归因于 V5 新增结构。
- 唯一 2030/V5 168 h cold 根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  已为 `OPTIMAL + solution_qc=PASS + 58/58`；input/result manifest
  validator 均返回 `(True, [])`，wrapper exit `0`、wall `18:38.92`、
  peak process-tree RSS `3.511 GiB`、swaps `0`。服务器实际 raw 矩阵为
  `1,209,095 rows / 1,060,576 vars / 9,755,329 nz`，presolved 为
  `737,850 / 751,223 / 7,386,987`；最大矩阵系数仍为 6,250，presolve
  amplification 为 `1.0`。Barrier 运行 232 次、819.54 s 后以
  `Sub-optimal` 结束，但没有出现 `Numerical trouble encountered`；
  `CrossoverBasis=1` 在 176.79 s 内将状态改为 `Optimal`，最终
  258,814 simplex iterations、solver `1005.194 s`，无 restart。
  最大 constraint/bound/dual violation 为
  `8.339e-8 / 2.609e-8 / 6.047e-8`。
- 本轮严格 QC 未发现新增钻空子：冷热 up/down、EV charge/discharge、
  储能 charge/discharge、火电 startup/shutdown、AC 对冲流均为零；
  V1G/V2G nested、全国 V2G cap、共享连接功率、firm-credit 物理上界、
  备用、惯量、网络、水电/梯级、碳/CCS/BECCS 与成本 component 全部通过。
  2030 firm flexibility credit 为 `2.891320 GW`，诊断碳上限按
  `168/8760` 缩放至 `76.712329 MtCO2` 并 binding。输出中的
  `maximum_ev_v1g_daily_energy_residual_gwh=5.999958` 是旧式“每日充电
  量等于不受控基线”指标；V5 使用带效率、驾驶取能和周期 SOC 的车群服务
  守恒，该旧指标不适用，真正的车群 SOC transition residual 为
  `2.537e-13 GWh`。后续应清理该输出名称/适用性，避免论文审计误读，
  但不得把它误判为当前 LP 漏约束。
- 与旧 V5 168 h `TIME_LIMIT` 根相比，新根把“6 h、3,488,935 次
  simplex、无解/QC/manifest”改为约 16.8 min solver 严格最优，证明本轮
  精确冷热状态压缩修复了已复现的 V5 presolve 放大和数值循环。它仍不是
  8760 h 可解性证明：解的估计 `Kappa=1.6198e10`，共享模型最差 row
  scaling 仍来自 `load_center_ror_availability`、ROR/VRE availability
  与年度会计；直接消去 availability variables 曾增加 presolved
  nonzeros，盲目提高 CF 零阈值又会改变科学输入。因此
  `barrier_16_auto_order_stable_basis_v3` 只升级为“168 h V5 诊断通过”，
  仍不是 production profile。服务器当前无 CISPO/Gurobi 进程、约
  111 GiB available、`vmstat si/so=0`、memory PSI 0；ParaCloud 队列空。
  下一步先以相同提交/数据/profile 运行一个全新、匹配的 2030 Base 168 h
  cold gate，并在不求解的矩阵审计中量化共享小系数的可证明等价候选；
  两者闭合前不启动 744/1008/8760 h。继续禁止付费云、并发第二求解、
  basis/MGA 和 `Crossover=3`。

- 2026-07-31 04:21+08:00 已提交 V5 长时域数值稳定化实现
  `fead34334153eca32bbf7ec3651f3388038ac04b`。旧服务器根
  `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_direction_warning_v5_cf265f3_server_v1`
  已严格归类为数值 `HARD_FAIL`：2030 在 21,600 s 达到 `TIME_LIMIT`，
  Barrier 210 后出现 `Numerical trouble encountered`，Crossover/Simplex
  累计 3,488,935 次仍无可行解；无 `solution_qc.json`、无
  `result_manifest.json`，2040--2060 未启动。失败不是内存或队列导致：
  wrapper 峰值 RSS 约 3.47 GiB、swaps 0，终态服务器约 114 GiB available、
  `vmstat si/so=0`、memory PSI 0，ParaCloud 队列为空。
- 根因已由 168 h 原始/预求解矩阵复现：旧完整冷热状态链被 presolve
  反向聚合后，最大系数由 6,250 放大到 319,337.737（51.094 倍），最差
  家族为 `cooling_positive_service_bound`。新实现仅在有非零控制的小时
  保留冷热状态，并以衰减锚点限制相邻保留节点的系数不低于 0.1；被省略
  小时的控制严格为零、状态上界不随时间变化且 `0 < rho <= 1`，因此使用
  `S_t = rho^Delta S_prev + eta_c u_t - d_t/eta_d` 是精确消元，不改变可行域
  或目标。还删除 V5 未进入目标/QC 的 EV 绝对偏差 epigraph、零上界冷热
  控制变量、零 departure rows 以及可由静态正下界证明冗余的
  `effective_load >= 0` rows；全年共减少 1,227,241 个原始变量和
  2,348,964 个原始约束。新增 `charge + discharge <= connected * K_v1g`
  以禁止 V1G/V2G 同时重复占用同一签约连接，并新增对应 hard QC。
- 最终本地证据：完整回归 `159/159 PASS`，V5 input audit、release audit、
  compileall 与 `git diff --check` 均 PASS；水电仍为
  `297.8895 + 82.1105 = 380.0000 GW`。最终 2030/168 h V5 数值审计为
  raw `1,209,095 rows / 1,060,576 vars / 9,755,331 nz`，presolved
  `737,850 / 751,222 / 7,386,903`，raw/presolved 最大系数均为 6,250，
  放大比严格为 1.0。8760 h 静态 preflight 为约 42.95M variables、
  57.92M constraints、503.13M nonzeros、34.3 GiB；它不是 Barrier
  factorization 或可解性证据。本地 1 h 求解在 `optimize()` 前因 available
  RAM 约 7.9 GiB 低于 8 GiB 安全门槛而停止，不得降低门槛。
- 新的 `barrier_16_auto_order_stable_basis_v3` 只是诊断候选：
  `Method=2`、`Threads=16`、`Presolve=2`、`Crossover=1`、
  `CrossoverBasis=1`，不设置 `Aggregate=0`。下一精确步骤是推送
  `fead343`，在服务器无进程且 clean 时 fast-forward，运行完整回归、
  readiness/release/V5/hydro audits，再串行运行全新 2030 Base/V5 1 h
  与 24 h cold gates；均严格闭合后，才启动唯一 2030/168 h V5 cold
  candidate。不得自动启动 744 h、8760 h、四年 sequence、付费云、basis、
  MGA、并发第二求解或 `Crossover=3`。

- 2026-07-30 21:29+08:00 作者已决定不让系统级影响极小的 AC 对冲流阻断截断时域排错，限定 warning 实现提交为 `9b6e72a456b0dc8f0123f90b07195f94ca902c9a`。该提交不改变 LP 方程、目标、输电成本、流量数组或 `1e-6 GW` 原始检测阈值；只对 `TEST_ONLY_TRUNCATED_HORIZON` 增加七重 warning budget：每 168 h 最多 4 个 edge-hours、单小时较小方向不超过 `0.25 GW`、不超过线路容量 `15%`、累计较小方向不超过 `0.75 GWh`、额外损耗不超过 `0.025 GWh`、累计较小方向占毛输电量不超过 `5e-5`、额外损耗占系统负荷不超过 `1e-7`，其中小时/电量/损耗预算随诊断小时线性缩放。任一超限仍 hard fail；8760 h `SCIENTIFIC_PRODUCTION` 继续要求 `1e-6 GW` 以上严格零对冲。原 2050/168 h 现场在新评估器下为 `TEST_ONLY_DE_MINIMIS_WARNING`：3 edge-hours、`0.176374 GW`、线路占比 `0.107153`、`0.381006 GWh`、额外损耗 `0.011489 GWh`、毛流占比 `1.3823e-5`、负荷占比 `4.0100e-8`，所有原始值和限额均保留在 QC。
- 本地新增方向性解析测试后完整回归 `146/146 PASS`，V5 input audit 与 release audit 均 PASS；本机 available RAM 约 `7.48 GiB < 8 GiB`，因此未降低门槛或启动本地 solver。21:28 实时复核固定服务器仍为 clean `af390fa`、无 CISPO/Gurobi/sequence 进程、约 `114 GiB` available、swap `780 MiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。下一步提交文档并双端推送后，在服务器空闲现场 fast-forward 精确 tip，运行 `146/146`、release/readiness/V5/hydro audits 及全新 1 h/24 h Base/V5；随后依次运行全新四年 168 h Base 和 V5。全部闭合后，作者授权的长门禁为唯一串行四年 `1008 h` `flex_integrated_v5_central`（42 天，强于 744 h），继续使用 `barrier_16_auto_order_v2`、cold/no-basis。仍禁止 8760 h、付费云、并发第二求解、basis/MGA 和 `Crossover=3`。
- 2026-07-30 19:38+08:00 固定服务器四年 168 h Base sequence 已在 2050 年按物理 hard QC 正确停止，不能接受或续接。输出根 `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1` 的 `sequence_report.json=HARD_FAIL`：2030/2040 均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest`，2050 的 Gurobi 求解虽为 `OPTIMAL`（solver runtime `849.053 s`、Barrier `128`、Crossover/simplex `340,040`、最大 constraint/bound/dual violation `4.889e-10/1.193e-8/9.313e-8`），但 `solution_qc=HARD_FAIL`，仅 `unidirectional_interprovincial_flow` 一项失败；2050 无 `result_manifest.json`/planning state，2060 未启动，V5 sequence 也未启动。违规严格局限于 `CORRIDOR_0153`（吉林 `22`—黑龙江 `23`，AC，既有容量 `1.646 GW`）的 3 个小时：最大较小方向流量 `0.176374 GW`、累计较小方向流量 `0.381006 GWh`，不是 `1e-6 GW` 数值尾差。对应 2050 窗口净碳上限按 `168/8760` 缩放至 `-1.917808 MtCO2` 并精确 binding，碳影子价格 `3589.731 CNY/tCO2`，违规小时吉林/黑龙江边际电价约 `-1405` 至 `-3650 CNY/MWh`；模型利用 AC 正反向流的额外输电损耗吸收 BECCS 驱动的局部过剩电量。这说明现有 `1.004004 CNY/MWh` 毛流量成本在深度负价下不再足以保证无对冲流，硬 QC 拒绝是正确行为，禁止通过调大 `1e-6 GW` 阈值重标结果。
- sequence 顶层 wrapper exit `1`、wall `49:20.77`、maximum RSS `3,741,888 KiB`、swaps `0`；2030/2040 年度 stderr 为空，2050 stderr 仅为上述 QC RuntimeError。终态无 CISPO/Gurobi/Python sequence 进程；固定服务器 checkout 仍为 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，约 `114 GiB` available RAM、swap `780 MiB/2.0 GiB` 且实时 `si/so=0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地、origin、GitHub 文档 tip 均为 `134af0fcf5ccc9d631f1bf805f3104e0de5f7f7e`，用户拥有的 `supplementary_materials/**`、`.codex_tmp/**` 和历史 outputs 未改。下一步先审查并批准保持 LP/物理边界的 AC 方向性修复方案，再用全新根从 2030 重跑 Base 168 h；不得复用失败根、跳过 2050、启动 V5/744 h/8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。
- 2026-07-30 16:58+08:00 固定服务器 V5 预门禁和当前身份 24 h A/B 已闭合。跨平台构建暴露并修复两项 release 身份问题：提交 `4f717de` 将五张 V5 CSV 和 manifest 固定为 UTF-8/LF、`%.17g`、gzip level 6/空 filename/`mtime=0`，Windows Python 3.10/pandas 2.2.2/NumPy 1.26.4 与 Linux Python 3.11/pandas 2.3.3/NumPy 2.4.6 生成的六项 SHA256 逐字节一致；提交 `af390fa` 删除 V5 对本地 ignored 技术经济 manifest 的错误覆盖，继续继承 V0729 权威 SHA256 `397297ec...`。当前服务器代码为 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，最终数据根为 `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`，V5 manifest SHA256 为 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`。本地和服务器完整回归均 `141/141 PASS`；服务器 readiness、V5 输入、release 和水电审计均 PASS，水电仍为 `297.8895 + 82.1105 = 380.0000 GW`。
- 当前服务器 2030/24 h Base 根 `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_base_af390fa_server_v1` 与 V5 根 `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_central_af390fa_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest + wrapper exit 0`。solver runtime 为 `405.882/434.896 s`，wall 为 `7:26.56/7:58.18`，peak process-tree RSS 为 `0.759/0.797 GiB`，swaps 0；Barrier 均报告 numerical trouble，随后 `Crossover=1`/simplex 以 `503,365/519,659` 次迭代修复，最大 constraint violation 均为 `1.224e-8`。V5 objective 相对 Base 低 `347.394 million CNY`，显式 flexibility cost 为 `785.531 million CNY`，firm credit 为 `2.891320 GW`，总发电装机同步减少 `2.891320 GW`（主要 gas `-1.969238 GW`、coal `-0.922082 GW`），所有冷热、EV/V1G/V2G、firm credit、储能、网络、备用、惯量、碳/CCS 和成本 hard checks 均通过。
- 24 h 结果中首日全国有效峰值由 `1229.5522` 降至 `1227.3831 GW`，变化 `-2.1692 GW`；它不能与 `2.8913 GW` firm credit 直接比较。诊断运行只优化领先 24 h，而 capacity adequacy 和 firm credit 按各省不可变完整 8760 h baseline peak 的四小时窗口、合同容量、功率/能量包络与折减率计算。因而当前证据证明的是容量认证方程和发电侧容量响应已生效，不是年度 endogenous effective-peak 或中国 ELCC 结论。下一步在冻结 `af390fa` checkout 上串行运行全新四年 168 h Base sequence，严格接受后才运行 V5 sequence；两者仍为 `TEST_ONLY_TRUNCATED_HORIZON`。168 h A/B 全闭合前不得启动 744 h。
- 2026-07-30 16:05+08:00 已形成并提交集成需求侧灵活性 V5 候选 `57ad4c5`。正式主分析仍严格只有 Base 与一个中央反事实；Base 不变，中央反事实联合冷热负荷、付费 V1G、内生付费 V2G，以及只对四小时峰值窗口内可交付服务计入的折减 firm capacity credit。V1G 只对相对不受控充电基线的向下迁移计费；V2G 内嵌于有序充电合同，另付 availability、双向设施、车主参与和电池退化成本；不提供备用信用。V5 输入审计 PASS，四年/31 省/8760 h 完整，输入 manifest SHA256 为 `350fce0051d5e79494f2f71e2c28a620385f868de7596baac6dfd3e39260a108`；`release_contract_v0730_v5` 审计 PASS，完整回归 `140/140 PASS`。新的英文论文式补充章节位于 `supplementary_materials/modules/06_integrated_demand_flexibility/integrated_demand_flexibility_methods_en.tex`，仅四个紧凑 section，无内部 scenario/config/manifest 名称；对应 PDF 已经 Tectonic 编译和逐页视觉复核。中文技术合同版本同时保留。
- 2030 1 h Base/V5 门禁均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input manifest + valid result manifest`。修正 V5 单一 EV 车队 SOC 的输出解释后，当前实现 1 h 根 `outputs/2030_1h_v0730_flex_v5_central_gate_v3` 仍为 `OPTIMAL + 57/57`，solver runtime `17.330 s`；`scenario_manifest.json` 现在明确说明 `ev_mobility_charge_gwh` 是集成车队总充电，旧 `ev_v2g_charge_gwh` 在 V5 中不适用且保持兼容零值。数学实现修正前后的目标一致。24 h A/B 数学门禁根 `outputs/2030_24h_v0730_flex_v5_{base,central}_gate_v2` 均为 `OPTIMAL + PASS + 57/57 + closed manifests`，solver runtime 分别为 `404.360/727.286 s`；两者 Barrier 均数值困难后由 `Crossover=1`/simplex 修复，分别为 `507,293/546,950` 次 simplex。V5 将该 24 h 窗口全国峰值降低 `2.3211 GW`，获得 `2.8913 GW` firm credit，发电装机相对 Base 减少 `2.8913 GW`；灵活性成本约 `785.53 million CNY`，总目标净下降 `347.40 million CNY`。冷热/EV 状态、V1G/V2G 合同、全国 V2G 上限、firm-credit 物理上界、同时充放、备用、惯量、容量裕度和碳账户均无 hard-check 违反。因最后仅修改了 scenario/output 身份说明，`57ad4c5` 仍需在同一精确身份下重跑 24 h closed-manifest A/B，不能把现有 v2 根重标为当前提交结果。
- 本地四年 168 h Base sequence 首次尝试根 `outputs/planning_sequence_168h_v0730_flex_v5_base_v1` 在 2030 建模前被运行时内存门禁主动停止：available RAM `6.07 GiB < 8 GiB`，`sequence_report.json=HARD_FAIL`；无 Gurobi 求解、无 state 输出。168 h 静态估计为约 `1,019,223` variables、`1,257,802` constraints、`10,089,870` nonzeros、`0.74 GiB`，但不得降低 8 GiB 门槛或复用失败根。固定服务器实时为 clean `codex/cispo-2030-full-lp` / `c19e35b`、约 `114 GiB` available、swap `780 MiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空；没有 CISPO/Gurobi solver，但遗留部署审计 wrapper PID `976320`（子进程 `grep` PID `976713`）仍存在。按 PID 保护规则，在该遗留进程被作者确认处理前不切换服务器 checkout、不部署 `57ad4c5`、不启动 168 h/744 h。下一步是释放本地至少 2 GiB RAM 后以全新根重跑当前身份 24 h A/B 与 Base/V5 四年 168 h，或先获得处理服务器遗留 audit PID 的明确授权；仍禁止 8760 h、付费云、并发第二求解、basis/MGA 和 `Crossover=3`。
- 2026-07-30 11:26+08:00 已实现诊断时域年度流量账户缩放，模型提交为 `d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244`。定义 `f=optimization_hours/8760`，短时域的净碳上限、DAC 捕集 throughput、生物质燃料预算与 CO2 场址注入能力统一乘 `f`；DAC 小时功率由窗口捕集量除以 `f` 后的年化速率计算。年化装机/固定成本和 capacity state 不缩放，8760 h 因 `f=1` 与原科学模型完全一致。新增 2030 V4 V1G 本地 1 h/24 h 根 `outputs/2030_{1h,24h}_v0730_annual_flow_scaled_v4_v1g_v1` 均为 `OPTIMAL + solution_qc=PASS + 54/54 + current input + valid result manifest`；碳上限分别为 `0.456621/10.958904 MtCO2`，两根净排放均精确达到上限，DAC capacity violation 为 0。24 h solver runtime `270.653 s`；外层命令在结果/manifest 全部写完后达到 300 s 工具返回上限，实时复核无残留 runner。完整本地回归为 `138/139 PASS`，唯一失败仍是既有本地 ignored `technology/technoeconomic_price_basis_manifest.json` hash `f89241...` 与服务器冻结权威值 `397297...` 不同，本次未改数据或 release contract。`scenario_catalog v4` 的 `primary_analysis` 现在机器锁定为且仅为 `base` 与 `flexible_load_comfort_v4_v1g`；effective-peak、V2G、水电聚合调节、PHS low/central/high 仍是独立 sensitivity，V3 只作 legacy validation，PHS template 不可运行。固定服务器和 ParaCloud 本次均未操作；旧 744 h 结果不因新代码自动重标或复用，任何新服务器 744 h/8760 h 仍需独立授权与新输出根。
- 2026-07-30 09:18:42+08:00 串行 2030→2060 744 h V4 V1G diagnostic sequence 已严格完成，`sequence_report.json=PASS`，完成时间 `2026-07-30T09:12:33+08:00`，四年均 `ACCEPTED`、return code 0。2030/2040/2050/2060 均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + current input manifest + valid result manifest + hydro cascade reconciliation audit`，objective 分别为 `2,331,204.529 / 2,380,260.669 / 2,564,163.188 / 2,808,392.706 million CNY`，solver runtime 分别为 `12,268.312 / 10,701.027 / 12,557.989 / 14,954.122 s`；年度 `sequence_stderr.log` 全部 0 bytes。顶层 wrapper exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；活动 PID 已全部退出。53 项 hard checks 显式覆盖冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、容量充裕、碳/CCS/BECCS 与成本目标，四年 planning state 链均存在且仅标记为 test-only。终态主机 available RAM 约 114 GiB、swap 780 MiB 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。该整轮仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不能作为年度科学结果或正式 2040/2050/2060 state anchor；不得由此自动启动 8760 h、basis、MGA、付费云或第二求解。
- 2026-07-29 23:21:48+08:00 四年 744 h sequence 已完成首个逐年里程碑：2030 `ACCEPTED`，2040 正在 Barrier。2030 为 `OPTIMAL + solution_qc=PASS + 53/53 + current input manifest + valid result manifest`，solver runtime `12,268.312 s`，Crossover 后 `914,501` simplex iterations，objective `2,331,204.529 million CNY`；年度 `sequence_stderr.log` 为 0 bytes，运行监控 peak process-tree RSS `20.385 GiB`。53 项 hard checks 显式覆盖冷热服务/状态、EV V1G/V2G、wave、水电聚合与梯级水量、PHS/储能、网络方向、备用、惯量、容量充裕、碳/CCS/BECCS 与 objective components。2040 runner PID `1717598`，Barrier iteration `107`，runtime `3,572.896 s`，primal/dual infeasibility `0.008370/0.000821`、complementarity `1.8373`，current/max solver memory `13.174/22.222 GiB`；终态三文件尚不存在。主机 available RAM 约 95 GiB、swap `781 MiB/2 GiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。运行 checkout 继续冻结在 clean `5d31b51b350a581287fc8eb13e73216c11fc7543`；本地/origin/GitHub 文档 tip 为 `b0a3f3b26ff77a8b5357ccc9f423605fc3a1d2e8`，PID 存在期间不追平服务器文档。
- 2026-07-29 18:45:08+08:00 已在固定服务器 checkout `5d31b51b350a581287fc8eb13e73216c11fc7543` 启动唯一串行 2030→2060 744 h V4 V1G diagnostic sequence。输出根 `/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，控制根 `/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`；wrapper/Python PID 初始为 `1463763/1463765`，2030 runner PID `1463870`。`sequence_report.json` 已锁定 `RUNNING + TEST_ONLY_TRUNCATED_HORIZON + diagnostic_hours=744 + flexible_load_comfort_v4_v1g`，无 basis。18:45:49 首次快照仍在构建，尚无 telemetry/Gurobi/终态三文件；available RAM 约 113 GiB、swap `781 MiB/2 GiB` 且 `si/so=0`、memory PSI 0、ParaCloud 队列空。PID 存在期间只读监控，不再切换服务器 checkout；每年必须严格 accepted 后才允许 runner 串行进入下一年。
- 2026-07-29 18:42+08:00 固定服务器已 fast-forward 到干净 `codex/cispo-2030-full-lp` / `03e77ccc8d2ef3813b7cc5c0d727b068d008090d`。权威 v4 数据根下 release contract、readiness、水电 380 GW 容量审计和 V4 输入验证全部 PASS，完整回归 `135/135 PASS`；`technology/technoeconomic_price_basis_manifest.json` SHA256 为冻结值 `397297ec3980ffb38988a0463f934e310f228cbe48268d59ce38c7fa8350ec75`。服务器全新 1 h/24 h 中央 V4 V1G 根 `2030_1h_v0729_identity_hydro_v4_v1g_server_v1` 与 `2030_24h_v0729_identity_hydro_v4_v1g_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + current input manifest + valid result manifest`，且均生成 `hydro_cascade_reconciliation_audit.json`；24 h solver runtime `84.230 s`，wrapper wall `2:07.62`、peak RSS `0.813 GiB`、swaps `0`。下一步仅在再次确认无 solver、资源安全、新 sequence 输出/控制根不存在且 ParaCloud 空队列后，启动唯一串行 2030→2060 744 h V4 V1G sequence。
- 2026-07-29 18:27+08:00 新模型实现里程碑已提交为 `cea78ae1546b19754f7859982ae82dbf66820fdc`（父提交 `96e989f22a74c621ad6642a287738befa5ea6c6f`），尚未部署固定服务器。它修复 8760 h runner 在求解前无条件 `getA()` 的阻断：常规运行只记录 Gurobi `Fingerprint`、变量/约束/非零元，只有显式 diagnostic basis import/export 才物化完整 CSR。运行身份升级为 `baseline_contract + analysis_case`；Base、中央反事实、敏感性、遗留验证和模板均有显式角色，scenario overlay 只能修改白名单根。
- 容量充裕口径现有两个互斥合同：Base 与中央 V4 V1G 保持 `baseline_peak_v1`，新情景 `flexible_load_comfort_v4_v1g_effective_peak_sensitivity` 使用 `effective_peak_endogenous_v1`。后者采用每省一个 `capacity_margin_credited_capacity_gw` 辅助变量和逐小时两非零元约束，避免复制省级容量表达式。匹配 24 h 门禁均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + valid result manifest`；baseline/effective 的 raw LP 分别为 `241,523/353,587/1,799,111` 与 `242,236/353,587/1,803,544`（rows/columns/nonzeros），effective 仅增加 `713` rows、`4,433` nonzeros（约 `0.246%`），solver runtime `55.253/53.021 s`。截断窗口的全国逐省峰值和发电侧总装机分别从 `1793.402 GW/3998.172 GW` 降到 `1255.373 GW/3785.672 GW`；这只证明容量价值通道真实且工程开销很小，不能把 24 h 差值解释为年度容量价值。
- 梯级水电不再把负本地入流静默截零。`target_bounded_proportional_transfer_v1` 对每个下游节点逐时按 `min(1, target natural flow / lagged upstream natural flow)` 显式调和上游转移，并把同一系数用于优化得到的 turbine+spill release；未来任何一源多下游拓扑在缺少 branch shares 时 hard fail。当前 8760 h 输入审计为 `335,304` 个原始负本地入流 node-hours、最小 `-5701.463 m3/s`、需显式调和 `158,199.650 million m3`、94 个节点，调和后最大水量恒等式残差 `4.55e-13 m3/s`。容量口径仍严格为站点 `297.8895 GW` + 省级聚合 `82.1105 GW` = `380 GW`。
- 新增 opt-in 的 accepted full-year Base solver artifact 合同：只保存压缩 `.sol`、post-crossover `.bas`、`.prm`、轻量 fingerprint 与 hash manifest；不全量导出 RC/slack/SA 范围、不计算 `KappaExact`，也不允许自动跨年或改变矩阵后复用。MGA 仍须等待 accepted full-year Base；本里程碑不启动 MGA 或 basis gate。
- 本地验证：聚焦测试 `58/58 PASS`；完整 discovery `135` 项中 `134 PASS`，唯一失败是本地忽略数据中的 `technology/technoeconomic_price_basis_manifest.json` hash `f89241...` 与冻结服务器 v4 数据包的权威 hash `397297...` 不同，服务器文件已实时复核仍为 `397297...`，因此未篡改 release contract 或用户本地数据。全新 1 h/24 h baseline/effective 四根全部 `OPTIMAL + PASS + 53/53 + closed manifest`；全新四年 1 h V4 V1G planning sequence 为 `PASS`，四年均 `ACCEPTED`，无 basis。下一步：文档提交并推送两端；再次实时核验服务器/ParaCloud；仅在无 solver、资源安全时 fast-forward，运行服务器权威数据根下完整回归与 1 h/24 h 门禁，然后按授权启动唯一、串行的 2030→2060 744 h V4 V1G diagnostic sequence。不得启动 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`。
- 2026-07-29 固定服务器已部署并完成统一候选的隔离 744 h 门禁。当前代码身份为 `7c56622c266e673037bd6afaa70c85aa57e6cb13`，服务器 checkout 干净；外置表使用全新根 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`，标准数据归档 SHA256 为 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。`model_input_files.json` 已升级到 v10（42 张运行表、12 个 sidecar），显式覆盖 Base、wave、V3、V4 与全部来源 manifest。服务器 `release_contract/readiness/hydro/V4-loader` 全部 PASS，完整回归 `130/130 PASS`。全新 V4 V1G 1 h/24 h 根均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + current input/result manifests valid`；24 h 的 Barrier numerical trouble 由生产 `Crossover=1` 恢复为最优解，不能据此改用已拒绝的 `Crossover=3`。
- 当前唯一模型实现基线为 `codex/cispo-2030-full-lp` / `7aac739e03646edfed14bbf48ac77869ba66cbef`；本次终态审计只在其上增加交接文档，不改变模型、配置或数据合同。固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，无需为追平文档而切换；本地工作树仅保留用户拥有的 `supplementary_materials/**` 与 `.codex_tmp/**` 修改/未跟踪文件，后续必须继续选择性暂存并保护。
- `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1` 已完成并通过严格工程验收。它是单独的 `--planning-year 2030 --horizon one_month`、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2` (`Crossover=1`) cold gate，无 basis，未调用 planning-sequence runner。Gurobi 在 Barrier `313` 次后完成 Crossover，终态为 `OPTIMAL`，objective `2,330,214.449430 million CNY`，solver runtime `12,984.854 s`，simplex `832,655` 次；wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`，stderr 只有 `/usr/bin/time` 统计。`solution_qc.json=PASS`、`52/52` hard checks、current input manifest 和 result manifest 的运行时 validator 均为 `(True, [])`；最终 constraint/bound/dual violation 均低于 `1e-7`。求解 PID 已退出，未产生并发第二求解。
- 终态模块审计闭合冷热/EV 状态与边界、wave 输入和零选择、水电 380 GW 与月度/库容约束、PHS/电池容量和充放电、411 条网络 corridor 与 DC 方向、备用/惯量/容量裕度、碳/CCS 源汇平衡，以及成本 `accounting_scope`。objective 由 `2,112,470.998439 million CNY` annualized-planning scope 与截断时域 operation scope 共同构成；因此本根始终是 `TEST_ONLY_TRUNCATED_HORIZON`，不能作为年度科学结果、年度净价值或正式 2040 state anchor。
- 2026-07-29 16:32+08:00 终态刷新时，主机约 `114 GiB` available、swap `781 MiB/2.0 GiB`，实时 `vmstat si/so=0`、memory PSI=0；ParaCloud `squeue -u a8s001819` 为空。历史 `4003088/4003172/4004585` 仍分别为 `COMPLETED build-only / OUT_OF_MEMORY / TIMEOUT`。没有已验收的 8760 h 结果，也没有启动或获准启动 8760 h、付费云、basis gate、并发第二求解或 `Crossover=3`。
- 服务器隔离部署门禁发现并修复了本地同目录测试无法暴露的四类整合疏漏：hydro audit 的 `numpy.bool_` 跨环境 JSON 序列化；V4 上游 manifest 未进入部署包；V4 运行表及 wave 表/manifest 未进入标准 `model_input_files` 合同；已声明 implemented 的 V3 表未进入包且少数测试写死 `repo/data`。修复提交依次为 `a3ab9f5`、`95e1b76`、`5c749b6`、`e0b5dbd`、`7c56622`，均已推送 `origin` 与 `github`；旧的 v1--v3 数据根和失败审计目录只保留为故障证据，不得作为当前运行输入。
- 2026-07-29 对 7.28—7.29 多智能体改动完成首轮统一审计并形成实现提交 `1d04f07565c3039ed467ec4080f276bd0da90786`。发现 `3b3de57`/`b87b3b6` 的干净提交只含省级聚合水电 loader、漏掉配置/约束/输出，不能直接部署；当前提交已把常规水电 380 GW 闭合、重复 COMID 水量分配、V4 冷热/EV、PHS 功率—能量敏感性、成本会计和输出/QC 合并为一个可测试候选。`config/release_contract_v0729.json` 冻结 Base、solver profile、情景 catalog 与 11 个外置数据 SHA256；`scripts/audit_release_contract.py` 当前为 PASS。历史 `m2_model_boundary_audit_v1.json` 已显式标为 superseded，不能再代表当前模型。
- 技术经济生产口径已经进入当前代码、部署数据和活动 744 h 的实际解析配置，不是仅存在于补充材料。正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`，它是本地/GitHub `7aac739` 与服务器 `7c56622` 的共同祖先；先前交接误写的完整哈希 `29bbf904638fbfa45911bb6d801432d592302e15` 已在本次交接中纠正。`technoeconomic_2025_cny_v2` 对生产货币输入统一使用 2025 constant CNY；本地迁移审计为 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。服务器数据根的 `technology/technoeconomic_price_basis_manifest.json` 为 `APPLIED_PRODUCTION_LOCAL_DATA_PACKAGE + PASS`，活动 744 h 的 `input_manifest.csv` 与 `model_config_snapshot.json` 分别记录该 sidecar SHA256 和 `target=2025 constant CNY`。这不消除未来 CapEx 图读数、混合来源年燃料价和 V4 说明性成本的科学不确定性。
- 统一审计额外修复三项真实问题：`hydro_aggregate_flex_v1` 的向上备用 QC 曾重复计入省级聚合水电，已改为只使用模型导出的总水电备用；小时安全表的向下水电备用已包含聚合层，重新计算的 up/down closure 最大误差分别为 `1.42e-14/7.11e-15 GW`。V4 年化 enablement 成本不再误标为 selected-horizon cost，混合总项 `annual_operation` 标为 `COMPOSITE_SEE_COMPONENT_ROWS`。V4 gzip builder 固定 `mtime=0`，连续两次完整 build+validate 的六个输出逐文件字节一致，sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。
- 当前统一候选的 `py_compile` 通过，完整本地回归为 `129/129 PASS`；参数审计为 `11,727 rows / 26 PASS / 0 WARN / 0 hard fail`，保留 4 个已知科学风险；省级水电输入审计确认 `31` 省、`372` 省月行、`297.8895 + 82.1105 = 380 GW`。全新 2030 1 h Base、V4 V1G、hydro flex、PHS central 均为 `OPTIMAL + solution_qc=PASS + current input/result manifests valid`。首次 Base `_v1` 在 OPTIMAL 后因统一重命名漏改一处 export 字段失败，已保留作故障证据；修复后的 `_v2` 与 hydro flex `_v3` 闭合。
- 2026-07-29 已在本地当前工作树顺序完成匹配的 2030→2040→2050→2060 168 h Base 与 `flexible_load_comfort_v4_v1g` 两条 planning sequence；每年只接收上一年的显式 diagnostic state，不复用 basis。八个求解全部达到 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + closed result manifest + current input manifest PASS`，两条序列 resume 后四年均为 `RESUMED_ACCEPTED`。Base/V4 raw LP 分别为 `1,167,956/1,024,400/9,546,696` 与 `1,240,868/1,071,396/9,859,176`（rows/columns/nonzeros）；V4 增量为 `+6.24%/+4.59%/+3.27%`，峰值 RSS 仅增加约 `0.12--0.27 GiB`，未出现内存或可行性退化。机器审计位于 `outputs/planning_sequence_168h_v0729_ab_audit/planning_sequence_ab_audit.{json,csv}`。
- 168 h 结果只证明数据传递和机制可解性。V4 在四年分别发生 `657.86/1435.91/2025.12/2314.68 GWh` EV 充电重排，全国峰值改变 `-0.90/-1.76/-2.00/-5.78 GW`；冷热转移吞吐为零（2050 仅 `5.2e-12 GWh` 数值噪声），说明中心参数和该代表窗口下优化器不购买冷热服务，不是公式失效。波浪能在两条序列中均为 enabled，1,284 条候选与 `9,798.111 GW` 原始上限均进入输入/QC，但最优装机和发电均为零；只能表述为“已考虑但该截断窗口未选择”。
- 不能把 V4 相对 Base 的目标差直接解释为年度净价值：年化 enablement/planning cost 被完整计入，而运行收益只覆盖 168 h。诊断性的“扣除显式柔性成本前系统收益”从 2030 到 2060 为 `3.52/11.26/24.76/33.89 million CNY`，只说明机制方向。为封堵误读，当前工作树新增 `accounting_scope`，把 `ANNUALIZED_PLANNING_COST` 与 `SELECTED_HORIZON_OPERATION_COST` 分开，同时保留旧 `value_million_cny_per_year` 列兼容；独立 1 h 根 `outputs/2030_1h_v0729_cost_accounting_metadata_v4_v1g` 已验证 `OPTIMAL + PASS + closed manifests`。2026-07-29 统一审计进一步把混合的 `annual_operation` 标为 `COMPOSITE_SEE_COMPONENT_ROWS`，并把 V4 年化 enablement 成本单独归入 annualized planning scope。
- 当前主线已完成 V4 中心情景的四年 168 h 工程闭环，但尚未达到论文科学闭环。作者已在 2026-07-29 明确授权：代码/外置数据口径统一并在服务器小门禁通过后，可启动一个隔离的 744 h 或两个月长度优化。当前选择标准 744 h V4 V1G cold gate，因为它是既有支持时域且同时覆盖新 Base 水电、wave 与 V4；不复用任何 basis，不启动并发第二求解。执行前必须先提交/推送精确候选、创建版本化服务器数据根、实时核验服务器 Git/进程/RAM/swap/PSI 与 ParaCloud、运行 release/input/readiness 和服务器 1 h/24 h 门禁。low/high V4 仍是论文科学敏感性的必要后续，但不再作为本次工程 744 h 的前置条件；MGA 继续等待完整 accepted Base anchor，`Crossover=3` 永久拒绝。
- 2026-07-28 常规水电 2025 容量口径已在本地闭合：`hydro_stations.csv` 的 2,030 条记录形成 297.8895 GW 可识别站点容量，另以 `provincial_aggregate_capacity_2025.csv` 表示 82.1105 GW 固定省级聚合容量，全国严格合计 380 GW；抽水蓄能运行下限保持 65.94 GW。国家能源局约 450 GW 的水电总量是四舍五入口径，380 + 65.94 = 445.94 GW，4.06 GW 舍入差不回填到任一技术。GHT operating non-PHS 的项目容量为 302.939 GW，中国归属份额 302.133 GW；旧“未匹配 39.869 GW”中已确认至少 15.419 GW 与 HydroCHN 清单重叠，故它不是可直接追加容量。
- 省级闭合不制造虚构坝址。四川 100 GW 下限、云南 83.6036 GW、湖北 36.7763 GW 常规水电规划锚点、贵州 22.98 GW 和广西 17.8838 GW 常规水电作为校准锚点，青海 16.445 GW 仅作外部排序/量级核验；其余省份在 `max(HydroCHN station, GHT China-attributable)` 非加和下界之上按既有省级先验比例调整。82.1105 GW 聚合层只有固定容量和由同省已识别站点 2019 水文形成的逐月可弃自然可用上限；无站点、水头、库容、COMID、扩张、跨期蓄水、梯级、备用、惯量、容量信用或 spur/trunk。
- 当前未提交工作树在 `b87b3b6a76e9b6a3683087105e3251daff22cfad` 之上接入该层；聚合发电进入省级电力平衡、成本会计、337 负荷中心年度注入、结果导出和硬 QC。水电定向测试 `12/12 PASS`；与当前模型相关的回归 `117/117 PASS`，完整 discovery 的另 2 项失败来自用户拥有的 `scenario_catalog.json` 字段 `blocked_by` 与旧测试期待 `reason`，与本水电改动无关且未修改。全新 1 h/24 h 根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`；24 h 聚合发电/可用量均为 97.768506 GWh、违反量 0，最大功率平衡残差 `1.12e-12 GW`，solver 43.188 s、峰值 RSS 0.743 GiB。它们均为 `TEST_ONLY_TRUNCATED_HORIZON`。
- Module 05 / S6 包已更新为 18 张表、两张主图、源数据、风险登记、QA 与 SHA256 manifest；`formal_closure_validation.csv` 为 `12/12 PASS`。最终空间图 `Figure_M05_02_hydropower_spatial_contract_v3.{png,pdf}` 把 R1、实际存放在 `R3/R3` 的 `hyd2_4l` 和 R5 共 5,950 条全国河网线以完全相同的层级和样式绘制在两幅地图中；图 a 表示五组核心梯级且不再标注 Laxiwa 等单站名称，图 b 表示非核心既有/潜在站点与省级聚合，南海诸岛改为图间空白区的单一共享插图，下排为当前容量与未来清单技术上限双栏柱图。V3 图件 QA 全部通过，Module 05 manifest 含 63 个文件；V2 作为历史版本保留。常规水电全国总量缺口已从 P0 改为“会计闭合、分配敏感性仍开放”的 P1；仍未关闭的 P0 是 2019 单年 monthly P30 环境流量代理，以及 VRE 2024/wave 2023/hydro 2019 的混合年协方差。本里程碑没有提交、推送、部署或读取/改变固定服务器与 ParaCloud，也未启动 168h/744h/8760h；早于本条的水电门禁不能重标为新容量口径。
- 2026-07-29 在同一未提交工作树上完成 PHS 功率—能量成本标定。Base 仍为固定 8 h PHS；低、中、高候选在每个规划年严格保留现行 2025 年不变价 8 h 总 CAPEX，只把能量侧成本占比分别设为 30%、36.5% 和 45%。中央值由 DOE/PNNL 与 ANU 两组直接分项证据得到的 31.69% 和 41.35% 取中点并取整；证据矩阵共 7 个独立来源组，其中中国证据 3 组、直接分项证据 2 组。三条配置均为 `PROPOSED_NOT_APPLIED_COST_CALIBRATED`，未替换 Base；最大 8 h 重构舍入误差为 `4.0e-6 CNY/kW`。全新中央情景 1 h 根 `outputs/2030_1h_v0729_phs_power_energy_separated_central_v1/2030` 为 238,529 variables / 80,794 constraints，达到 `OPTIMAL + solution_qc=PASS + closed manifest`；完整本地回归 `125/125 PASS`。Module 05 已扩展到表 M05-19—21、独立成本 QA 和更新的 S6 方法/技术归档，formal closure `12/12 PASS`。该门禁仅验证实现和成本会计，未运行 168h/744h/8760h，未触碰固定服务器或 ParaCloud；正式年度比较仍是候选升级的必要条件。

- 2026-07-28 冷热/EV V4 已在当前未提交工作树（基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`）收敛为数据支撑型工程情景。P0 修复包括：消除多省周期状态的 `p×p` 广播、把多省成本压为标量 Gurobi 表达式、将禁用 V2G 成本保持为 `LinExpr`、让 V4 QC 使用实际 smart-charge、修正 EV 电网充电上界，并删除允许无先行预热/预冷的负舒适债。冷热改为非负、全选定时域连续的服务库存；EV 改为“75% 不可调基线 + 25% 聚合可调服务”，严格复用已有逐省逐时 EV 基线，不把 `ev_hour_weight` 伪称为接桩率，也不虚构行程链或出发 SOC。V1G 为中心情景，V2G 仅独立敏感性；Base 和 V3 未改，V4 topology 绝不与它们互用 basis。
- `scripts/build_flexible_load_v4_inputs.py` 已从现有 `hourly_load_2025_2060.csv.gz` 与已审计 BAIT `+/-1 C` 包络生成五张 V4 输入；`scripts/validate_flexible_load_v4_inputs.py` 对 2030/2040/2050/2060 全部重新走 runtime loader，并生成含源文件/输入文件 SHA256 的 `data/flexibility/flexible_load_v4.manifest.json`。2026-07-29 统一审计修复 gzip 时间戳后，连续两次完整 build+validate 的六个输出均字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。中心/低/高参数、来源和独立证据计数分别登记在 `config/flexible_load_v4_central_parameters.csv`、`config/flexible_load_v4_source_registry.csv` 与 `config/flexible_load_v4_source_count_qa.csv`。这些值可直接运行，但状态仍是 `ENGINEERING_CENTRAL_REQUIRES_LOW_HIGH_SENSITIVITY`，不能表述为已观测的中国省级校准。
- 本地 `py_compile`、V4 定向测试 `11/11 PASS` 和完整回归 `123/123 PASS`。完整回归首次发现用户现有 PHS planning-state 测试夹具缺少已实现的 `phs_energy_capacity_mode`；仅向该 stub 补入旧模式 `fixed_duration_v1` 后重跑闭合，不改变模型。与当前稳定输入身份一致的新根 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v3`、`outputs/2030_24h_v0728_flexible_load_v4_data_supported_v2`、`outputs/2030_1h_v0728_flexible_load_v4_v2g_data_supported_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h V1G raw LP 为 `241,492 rows / 353,556 columns / 1,799,247 nonzeros`，solver `43.13 s`、端到端 `81.55 s`、峰值 RSS `0.760 GiB`。相对当前 24 h Base 候选仅增加约 `4.5% rows / 2.0% columns / 2.5% nonzeros`。首个 1 h 根 `_v1` 因禁用 V2G cost 的类型错误在 OPTIMAL 后 export 失败并保留作故障证据；旧成功根使用非确定性 sidecar hash，只保留为历史数值证据。所有截断根仅是工程门禁，不是论文结果；未运行 168h/744h/8760h，未部署或启动固定服务器/ParaCloud，未暂存或修改 `supplementary_materials/**`。下一步仅在作者接受公式与中心值后运行一个隔离的本地 168 h V1G gate；此后先做低/高敏感性，再谈 basis 工程。

- 2026-07-28 M2 boundary audit Stage A is closed locally at implementation commit `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` (`feat: add m2 boundary audit`). It adds a machine-readable 11-item decision register (`config/m2_model_boundary_audit_v1.json`), actual flexible-load V3/V2G overlay registry (`config/scenario_parameter_registry.csv`), read-only auditor (`scripts/audit_m2_model_boundary.py`) and targeted tests. The audit creates no LP, changes no input, and passed with `9 PASS, 0 OPEN, 0 hard fail`; `scripts/audit_model_parameters.py` additionally reports `11,717` parameter rows, `26 PASS, 0 WARN, 0 hard fail`, and four explicitly carried open risks. `M2-PARAM-001` is therefore closed: every active V3/V2G override has an exact resolved-config path/value record and remains scenario-only, not Base.
- The current local uncommitted hydro work now contains both `duplicate_comid_flow_allocation=static_capacity_potential_share_v1` and the fixed province-aggregate conventional-hydro closure described above. It is **not deployed**. Because the aggregate layer adds variables, balance coefficients and fixed hydro cost, the earlier duplicate-COMID-only objective/topology is historical evidence and must not be used as the current gate. The current 24h raw LP is `231,076/346,736/1,754,607` (rows/columns/nonzeros), objective `2,104,433.505757702 million CNY`; it reached `OPTIMAL + PASS + closed manifest` without changing the rule that truncated annualized costs have no scientific interpretation.
- M2 remains intentionally bounded: existing VRE cohort retirement is `CLOSED_M1`; duplicate-COMID is `LOCAL_GATE_PASS_PENDING_COMMIT`; formal multi-year hydrology/PHS pairing and adequacy/capacity credit remain separate work; V4 now has reproducible engineering inputs and local 1h/24h gates but still requires low/high sensitivity before paper claims; BECCS low/base/high remains a sourced-required post-solve screen; Base stays `base_2024_vre_wave_on_flex_off_v1` (wave on, flexible load off); MGA remains blocked until a complete accepted Base anchor. No M2 finding licenses a 744h/8760h run, cloud job, server deployment, concurrent solve, cross-year basis, or rejected `Crossover=3`.

- 2026-07-28 对固定服务器 swap 的实时只读诊断否定了“只是 cache”的假设：`Cached + Buffers` 仅约 `5.6 GiB`，而 `AnonPages` 约 `49.5 GiB`、`Inactive(anon)` 约 `34.6 GiB`。约 `19.1 GiB` swap 属于仍在运行的匿名页：活跃 GPU `wind_power` Python（RSS 约 `43.0 GiB`、`VmSwap 8.18 GiB`）及两组 MATLAB（`VmSwap 6.01/2.28 GiB`）已解释约 `16.5 GiB`。`vmstat` 的 `si/so` 和 memory/IO PSI 当前为零，说明没有持续换页，但不表示这些匿名页可丢弃。`drop_caches` 无法降低 swap；`swapoff/swapon` 技术上可在约 70 GiB available RAM 下回迁页面，却会扰动这些活跃的非 CISPO 作业，未获明确主机级授权前不得执行。

- 2026-07-28 早期的重复 `COMID` 修复和 Module 05 / S6 站点下限审查已被本快照首四条的 380 GW 容量闭合层扩展；原 297.890 GW“仅为全国下限”、15 张表、9/9 QA 和三个 P0 的陈述仅保留为历史阶段，不是当前口径。
- 2026-07-28 18:15 后再次只读核验固定服务器：`/data/zz2/National_model/repo` 为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，未发现真实 CISPO/Gurobi 求解进程，约 `70 GiB` 可用 RAM；swap 仍约 `19/21 GiB`。本轮没有切换 checkout、传输输入或启动远程求解，任何未来部署仍须重新实时核验并使用新命名输出根。
- 2026-07-28 本轮结束时已重新只读核验远程易变状态：固定服务器 `/data/zz2/National_model/repo` 是干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，未发现 CISPO/Gurobi 进程，约 `70 GiB` 可用 RAM；但 swap 仍为约 `19.1/21 GiB`，并有约 `43.0 GiB RSS` 的无关 Python 进程。ParaCloud `squeue -u a8s001819` 为空。按 runbook 仍是内存压力状态，未部署 `a5e34bf`/`616acb3`、未传数据、未启动任何远程求解；任一后续远程动作前仍须重新核验。

- 2026-07-28 当前 M1 提交的 168h 四根 basis 门禁已完成，全部使用 `barrier_16_auto_order_v2` / `Crossover=1` 且仅为 `TEST_ONLY_TRUNCATED_HORIZON`。2030 cold/warm 分别为 solver `520.266/10.874 s`、RSS `2.924/2.395 GiB`；2040（仅接收明确 2030 diagnostic state bridge）cold/warm 为 `489.268/14.257 s`、RSS `3.038/2.518 GiB`。四根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`，warm 全为 0 Barrier/0 simplex，同年 objective 均完全一致；容量最大差 2030 `0`、2040 `7.11e-15 GW`，成本/发电量仅浮点量级。2040 只导入其自身 cold basis，未跨年导入。虽已证明同构重解加速，但孤立 744h basis gate 必须先额外完成同配置 cold 744h 才能产生 basis；当前没有第二次同构 744h 的端到端需求，故不申请也不启动 744h。

- 2026-07-28 本地 M0/M1 basis 前置建设已由实现提交 `a5e34bf5357301c205b246b0aa2149db0dca9c3b`（`feat: close basis preparation m0 m1`）闭合，尚未推送或部署。M0 将运行身份拆为 `scientific_case`、`lp_topology`、`solver_runtime` 与 `implementation_bundle`：只有变量/约束顺序、约束方向、维度、NNZ 以及原始 CSR sparsity pattern 的精确 `lp_topology` 相等时才允许导入 LP basis；结果 resume 仍保守审计 implementation bundle，科学 case 或实现 bundle 差异只记录审计、绝不把 warm 根提升为科学验收。24h 2030 Base cold/warm 均为 `OPTIMAL + solution_qc=PASS + closed manifest`，objective `1996289.6918468594` 完全一致；warm 为 `LPWarmStart=2`、0 Barrier/0 simplex（`65.237 s` 降至 `1.188 s`）。
- M1 已明确 Base 科学标签与 `hybrid_weather_bundle_v1`（VRE 2024、wave 2023、hydro 2019），参数 registry 26 项 PASS；VRE retirement 生产模式为 `cohort_survival_v1`，并保留 `fixed_floor_v1` 作为对照，2030/2040/2050/2060 cohort floor 均有测试闭合。BECCS lifecycle 仅为目录外、post-solve low/base/high screening，绝不改变 LP 规模或冒充有来源的生产参数；新增 bound tightening 仅加入可证明不改变可行域的显式上界。M1 24h cold 与 M0 结果 objective、容量、成本与发电量均为零差异，raw LP 仍为 `231,076/345,992/1,753,119`，本地完整回归 `114/114 PASS`。现存旧 168h 四根是 M0/M1 前快照，只可作历史性能证据；下一步必须在当前提交重新运行 2030/2040 cold/warm 四根门禁，不得复用 `Crossover=3`、跨年 basis、固定服务器/8760h 或付费云任务。

- 2026-07-28 技术经济 V2 已获作者批准并由本地实施提交 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` 写入生产模型。统一价格合约为 `technoeconomic_2025_cny_v2`：CISPO 国内 2022 年不变人民币轨迹在 2030/2040/2050/2060 各规划年统一乘 `1.004004`，只平移共同价格基准、不改变年际学习比例；核电 CapEx 回到 `2800/2650/2500/2350 USD/kW` 后乘 `7.1429 CNY/USD`；省级燃料按原始 USD/GJ 乘同一汇率；波浪能按 EUR 来源值乘 `8.1185 CNY/EUR`；CCS 捕集/运输/封存为 `261.04104 CNY/tCO2`、`0.50 CNY/tCO2/km`、`45 CNY/tCO2`。物理参数、real WACC、市内数值破简并项及独立灵活负荷情景成本不重基准。

- 本地 Git 外置 `data/` 已由幂等脚本迁移并生成 `data/technology/technoeconomic_price_basis_manifest.json`；第二次执行只校验、不重复换算。带本地原生水文路径、2024 VRE 与 wave 路径的完整回归为 `106/106 PASS`，数据包 smoke test 为 `142/142 PASS`。`config/model_input_files.json` 已升级到 v5 并要求服务器数据包携带该价格合约 sidecar。固定服务器和 ParaCloud 均未部署、未启动求解；Git 推送不等价于外置数据包部署，后续服务器同步须新建版本化数据根并重新运行 readiness/smoke/input-manifest 门禁。

- 2026-07-28 本地 168h 四根 basis 门禁已闭合，全部使用 `barrier_16_auto_order_v2` / `Crossover=1`，仅为 `TEST_ONLY_TRUNCATED_HORIZON`：2030 cold/warm 分别为 solver `576.593/11.406 s`、RSS `2.925/2.262 GiB`；2040 cold/warm 为 `543.965/15.517 s`、RSS `3.030/2.263 GiB`。四根皆为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`。warm 均为 0 Barrier/0 simplex；同年 cold/warm 的 objective 和全部容量 CSV 相同，发电量最大绝对差仅 `3.64e-11`（2030）/`2.91e-11 GWh`（2040）。2040 使用 2030 明确 test-only state bridge，但只导入 2040 自身 cold basis，未跨年 basis reuse。basis sidecar 以 Git/config/profile/命名结构 hash 约束，不能用于全年科学结果。

- 2026-07-28 本地实施已提交为 `282c393fd98e25737631493e19110e38bb49ed28`（`feat: share VRE intra-grid connection and retire cohorts`），尚未推送或部署。提交后即时只读核验固定服务器：HEAD 仍为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi 进程、约 70 GiB 可用内存，但 swap 已用约 19/21 GiB，另有约 45 GiB RSS 的无关长任务；因此按 runbook 判定为内存压力，未切换 checkout、未传输数据、未启动 168h。ParaCloud `squeue -u a8s001819` 为空。此快照只记录当时状态，任何后续部署前仍须重新实时核验。

- 2026-07-28 本地已完成“同格网风光共享并入 + 既有 VRE 可追溯退役”模型修正，尚未提交或部署。基线为 `codex/cispo-2030-full-lp` 的 `d73eb3390c970b0da6319a03ca8b1d3c30384040`；本次只修改 `cispo_model/{config,data,io_contract,master}.py`、`config/{optimization_2030.json,model_input_files.json}`、`scripts/build_existing_vre_cohorts.py`、两组测试和本交接/服务器文档，既有 `supplementary_materials/**` 用户改动未触碰。对 36,686 个 VRE technology-site 行、16,317 个 `grid_uid` 实测：12,603 个多技术格网全部连接到唯一同一 `substation`。新 spur 严格采用 CISPO S4-18 的 `max_t(cf) × capacity`；风光 trunk 改为 CISPO S4-19 的站级 potential-weighted equivalent peak，避免把风光非同期峰值相加。该设计只增加一次完整 8760 气象 CF 扫描和审计 CSV，不增加逐小时 LP 变量或约束。

- 新的 `data/vre/existing_capacity_cohorts_2025.csv` 由可复现脚本从 GEM operating projects 和已审计的 V3 0.25° 既有容量表构建：15,171 行，SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`，按技术精确闭合 2025 年 onwind/offwind/UPV/DPV `593/47/670/530 GW`。有有效 GEM 投运年的队列按技术寿命退役；未识别 OSM/残差和边界后才投运的记录显式作 2025 boundary-censored cohort，不虚构年龄。退役只解除 observed-capacity floor，不移除技术 site upper，因此同址再建是优化决策而非强制假定；既有 spur/trunk 代理按显式连接复用规则独立保留。

- 隔离本地 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 已达到 `OPTIMAL + solution_qc=PASS + closed result_manifest`；wave 开启、flexible load 关闭。raw `231,076/345,992/1,753,119`、presolved `129,500/260,190/1,295,919`（rows/columns/nonzeros），Barrier 99、crossover 53,551 simplex、solver 34.83 s、端到端 58.91 s、峰值 RSS 0.739 GiB。2025 VRE 初始 trunk proxy 从旧 nameplate `1,310.0 GW` 降至共享峰值 `1,069.513 GW`（-18.36%）；这是网络代理成本口径变化，不能由截断时域目标外推科学结论。完整本地回归 `102/102` 通过。固定服务器 checkout、进程、输出和 ParaCloud 队列均未由本里程碑写入；任何部署前必须重新实时核验。

- 2026-07-28 Module 04 的审批前深度审查 v2：15 个实质性审查单元登记 63 个独立来源、104 条证据关联，每单元 6—8 个独立证据组，`table_m04_19_source_count_qa.csv` 全部 PASS。审批前 `candidate_inputs_v2` 中的 `PROPOSED_NOT_APPLIED` 作为历史快照保留，不回写覆盖；其后已按本快照最前两条所述完成授权集成。审批后新增 `production_integration_2025cny_zh.md`、表 M04-24 和 production QA，终止标记为 `FINAL_M04_V2_PRODUCTION_INTEGRATION_PASS`。

- 2026-07-28 补充材料总控与 Module 04 的最初候选阶段保留为历史证据：候选 QA 19/19 PASS，深度 v2 QA 8/8 PASS；后续 v2 授权以核电 USD 币种链和多来源 CCS 中央值替代早期候选，并已按当前快照完成生产落库。电池功率—能量拆分、燃料长期轨迹、技术特定 WACC、既有机组寿命、CCS 有效能耗惩罚及海上风电空间成本仍保持敏感性/结构审查项。
- 2026-07-28 的当前模型实施提交为 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`，分支为 `codex/cispo-2030-full-lp`；其后提交仅闭合验证、运行状态和交接文档。744h 实际运行 checkout 为 `0dadfe9566ea69b1105161451a399e476307a4f1`；最新本地/远端/服务器 HEAD 属易变化信息，必须用 Git 实时核验。早先快照所称服务器仍为 `4e1999d` 已被实时证据纠正。
- 风电/光伏运行气象年已切换为 2024，并采用显式 `beijing_natural_year_drop_feb29_v1`：模型小时严格覆盖北京时间 2024 自然年，使用 2023 UTC 最后 8 小时衔接 2024 UTC 数据，再删除北京时间 2 月 29 日，最终保持 8760 小时。波浪能仍使用独立的 2023 reference time coordinate，水文仍为 2019；这是明确的混合数据年边界。输入 manifest 同时锁定 2023/2024 两组 VRE Zarr。服务器已追加四个 2024 stores；传输 tar 的本地/服务器 SHA256 均为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`，四个目录文件数与本地逐项一致，既有 2023 数据未覆盖。
- 求解器全局硬编码已改为 solver-profile-controlled；Base 默认仍保留已验证的 `DualReductions=0 + InfUnbdInfo=1`。新增显式生产候选 `barrier_16_auto_order_v2`（1/0）、`PreSparsify=2`、`PreDual=1/2` 与旧诊断参数 profile。新增可选且严格等价的 `annual_emissions_province_hierarchy_v1`：用 31 条省级年度排放会计替换一条全国全小时行，再由 31 个省级变量进入全国碳上限；它是 formulation A/B，不是新科学情景。
- 本地完整回归 `89/89` 通过。2024 气象 Base 的两个 1h 根均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，全国式与省级分层式目标完全一致。六个 24h 匹配根也全部 `OPTIMAL + PASS + manifest closed`，目标仅有浮点级差异。省级分层把原始 6,697-NZ 全国排放行拆开，但在 `DualReductions=1` 下 dense/hierarchy 的 presolved 矩阵、`AA' NZ=1.925e6`、`Factor NZ=5.602e6`、`Factor Ops=5.883e8` 完全相同，因此尚无性能收益证据。
- 服务器完整回归 `89/89`。三组新 168h 根均 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。旧 0/1 参数为 presolved `731,124/820,537/7,212,238`、`AA' NZ=2.160e7`、`Factor NZ=1.042e8`、`Factor Ops=8.440e10`、163 Barrier/626.10 s、crossover 72.76 s、229,459 simplex、700.50 s、3.407 GiB RSS。dense v2 为 `704,597/719,155/7,133,417`、`1.987e7`、`1.023e8`、`8.480e10`、124 Barrier/475.02 s、crossover 190.62 s、630,993 simplex、668.05 s、3.411 GiB。省级分层 v2 的 presolved/factor/迭代/work units/目标与 dense v2 完全一致，仅墙钟受调度波动，故不采用分层。唯一 744h 候选为 dense + `barrier_16_auto_order_v2`；必须显式保留 crossover 放大风险。
- 新 744h 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已在运行 checkout `0dadfe9` 上完成并严格验收：`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=(True, [])`，49 项 hard checks 全部通过；Base 波浪能开启、灵活负荷关闭，VRE 为 2024 北京时间自然年对齐。raw/presolved 为 `4,915,427/3,711,992/40,836,493` 与 `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros），`AA' NZ=6.388e7`、`Factor NZ=7.481e8`、`Factor Ops=4.721e12`。Barrier 211 次/7,543.19 s，crossover 5,709.46 s，simplex 1,437,196 次，总 solver 13,268.90 s，端到端 3:47:18，峰值进程树 RSS 20.049 GiB，无 swap。最大功率平衡残差 `3.43e-12 GW`；最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。它仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。
- 当前 Base 为含陆上/海上风电、光伏和严格映射到既有 marine `grid_uid` 的波浪能，`flexible_load=false`；唯一可运行覆盖情景为 `flexible_load_comfort_v3_v2g_5pct`，仍是待校准敏感性。历史 wave-off 744h 仅作历史数学/QC/性能证据，绝不能伪称为当前 Base 门禁。
- 固定服务器在 `9a3c5e8` 阶段完成波浪数据和运行环境部署，随后以 `0dadfe9` 运行 168h/744h 门禁；运行根使用新增且不覆盖历史的 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727` 与 `/data/zz2/National_model/data/wave_energy_20260727`。`wave_sites.csv`、`wave_input_manifest.json`、`wave_grid.nc` 的 SHA256 分别为 `9b318630e4783a9453492ae6403ae9f3d108a9cec09499dd6f0acd961fdd79d3`、`540d601070b093f0d991193ce606c861ab5b310b7a892ca9787a455b95405af9`、`b2e259862c8bad9a34addf24534a8d1e1c8f66c4e351bdfe13fe9cfca1eb4831`。服务器专用 CISPO 环境补齐了与本地一致的 `xarray==2025.1.2`，并通过 `wave_grid.nc` 打开 smoke test；未记录任何密钥或 license 内容。
- 先前 2023 气象的固定服务器 Base 输出 `/data/zz2/National_model/outputs/2030_{1h,24h,168h}_v0728_server_wave_base_*` 与 `2030_1h_v0728_server_mga_runner_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，且都是 `TEST_ONLY_TRUNCATED_HORIZON`。其 168h raw/presolved 为 `1,167,958/1,019,192/9,486,177` 与 `730,782/820,208/7,174,545`（rows/columns/nonzeros），`AA' NZ=2.150e7`、`Factor NZ=1.045e8`、`Factor Ops=8.532e10`、138 Barrier、411,056 simplex/crossover、690.86 s solver、3.359 GiB process-tree RSS；该证据保留为历史年份对照，不能替代上面的 2024 门禁。
- `solver_audit.py` 现在解析 Barrier 的 `solved` 与 `performed` 分支、crossover 时间、presolve 缩减、factor/AA' 比和 post-Barrier 时间；同机 `1h/24h/168h` 审计表在 `/data/zz2/National_model/outputs/solver_audit_v0728/base_time_expansion_1h_24h_168h.{json,csv}`。24h 的 Barrier 虽为 `performed`，但 crossover 将终态恢复为 `OPTIMAL`，因此终态必须以 `solve_report.json`/QC/manifest 为准。
- `warm_start_basis.bas` 是仅限 diagnostic 的 crossover 后 LP basis，不是可序列化的 Gurobi 模型、presolve 状态、Barrier factorization 或 crossover tableau。导入前强制验证源 manifest、`OPTIMAL+PASS`、git、情景、小时数、raw dimensions 与全体变量/约束名-方向哈希，跨年还须显式 `--allow-cross-year-basis`；科学全年自动 basis 复用被代码阻止。固定服务器 1h 证据：2030 同年从 9.43 s/80 Barrier 降至 0.25 s/0 Barrier；2030→2040（携带严格 cohort state）从 9.29 s/77 Barrier 降至 0.52 s/0 Barrier，2040 目标一致至浮点误差。它们仅说明工程可行性，不构成全年性能或科学结论。
- 已保留既有 744h 根且未原地重建 manifest；固定服务器未启动 8760h，ParaCloud 未提交新任务。当前 checkout 的 MGA 只能接受闭合的 `SCIENTIFIC_PRODUCTION + BASE_MINIMUM_COST + OPTIMAL + PASS` 年度 Base 根，并逐项匹配 resolved config 和 required-input hash；它将原年度成本作为硬上限、以点/省/全国筛选的风光/波浪/水电/储能新增容量为二级目标，并拒绝导出递进 planning state。当前没有 accepted Base 全年结果，故未运行 MGA。任何云端 8760h 仍需用户单独确认。

- 当前生产工程实施提交为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，已推送 `origin` 与 `github` 并部署到固定服务器。该提交不改变 Base 数学模型、数据口径或情景边界；新增单运行根原子 claim、`run_identity.json`、源码/config/profile/scenario/formulation/data-root 身份、运行前当前输入复验、递进序列身份锁与 stale-lock 恢复协议。runner 只有在 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True` 时返回成功。本地与服务器完整回归均为 `98/98`；本地新 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0728_production_contract_v1` 均闭合，使用 2024 VRE、wave on、flexible load off，24h objective 为 `1,982,265.6076383933 million CNY`。
- 固定服务器 wave-ready 数据根以 add-only 方式补齐唯一灵活性覆盖层所需的 `load/flexible_load_envelope_v3.csv.gz` 及 manifest，未覆盖任何既有文件；SHA256 分别为 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03` 与 `0298256b2c1394f8e5a9e36780d2be279f06b27b291a9eca57daae91dba9a745`。这只闭合数据契约，不表示柔性参数已完成科学校准。
- 严格同结构 168h Crossover A/B 已闭合。`Crossover=1` 参考根 solver `649.17 s`、Barrier `124/455.86 s`、crossover `190.92 s`；`Crossover=3` 候选 solver `594.63 s`、Barrier `124/474.61 s`、crossover `117.67 s`。两根 raw/presolved、`AA' NZ=1.987e7`、`Factor NZ=1.023e8`、`Factor Ops=8.480e10`、目标、49 项 hard checks、manifest 与约 `3.41 GiB` RSS 一致；Crossover=3 的总 solver 快 `8.4%`、crossover 快 `38.4%`。`CrossoverBasis=0` 为 `661.25 s`，无收益，已淘汰。
- 744h 放大结果否决将 `Crossover=3` 作为生产候选。隔离根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 与接受的参考根具有相同 raw/presolved/factor 结构、相同 211 次 Barrier 和 2024 Base 身份；其 Barrier `6,981.07 s`、PPush `1,191.93 s`、DPush `1,214.00 s`，但 primal cleanup 出现量级 `1e8--1e38` 的 infeasibility 循环。按数值稳定性停止准则优雅中断后，`solve_report=INTERRUPTED`、runtime `10,930.99 s`、crossover `3,947.89 s`、simplex `1,724,960`、peak RSS `19.828 GiB`，没有解、QC 或 result manifest；它不是科学结果，也不能被宣称为“更快”。机器可读比较为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}`。接受的 744h 工程参考仍是 `2030_744h_v0728_2024_dense_dualred_v2` / `barrier_16_auto_order_v2` (`Crossover=1`)。
- 当前固定服务器无活动 CISPO/Gurobi 求解，历史与候选输出均保留。下一步生产路线：保留 `Crossover=1` 作为唯一接受的 744h profile；任何新 solver/formulation 改动先经过匹配 24h/168h 的 `OPTIMAL+PASS+manifest` 门禁，再由唯一赢家获得一个新 744h 根。固定服务器 8760h 与新付费云任务继续禁止；8760h 前仍需用户单独确认、高内存节点、不可变身份、线程/SoftMemLimit、预算与优雅停止规则。

## Superseded snapshot detail (preserved historical notes)

- 原始 LP 约束族稀疏审计已在本地闭合（2026-07-27，实施提交 `6114157`）：新增只读 `--constraint-family-audit`，在 `model.update()` 后以显式 50,000,000 非零元安全上限读取原始矩阵；它不改变变量、目标、约束、求解器参数或任何科学情景。输出 `constraint_family_audit.json` 纳入 `output_catalog.csv` 与 result manifest，记录稳定命名前缀的约束/变量族、每族矩阵非零元、最稠密的 25 个具体行/列，以及仅能从日志获得的全局 presolve/ordering/Barrier/crossover 指标。Gurobi 不暴露稳定的预处理后来源归属，审计明确禁止将全局 presolve 删除量归因于任一约束族。
- 新的含波浪、无灵活负荷 Base 根 `outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真。24h 原始/预处理矩阵为 `231,074/345,992/1,729,035` 与 `129,335/260,116/1,269,506`（rows/columns/nonzeros）；`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、`Factor Ops=7.399e8`、89 Barrier、57,741 simplex/crossover、29.107 s solver runtime 和 0.712 GiB 峰值进程树 RSS。精确最稠密行依次是 `annual_emissions_accounting`（6,697 个非零元）、`capacity_margin_p65`（6,491）、`capacity_margin_p15`（5,736）以及 31 个 `co2_source_balance_p*`（各 3,246）；最稠密列为省级 `storage_capacity_gw[province,1]`（各 194）。水电逐站库容/泄流/水量平衡并非这次矩阵密集度的首要来源。
- 审计只确定候选，不允许删除容量裕度、CO2 源汇守恒、年度碳约束或储能物理。下一步仅为 `annual_emissions_accounting` 的省级会计分解准备代数等价证明与匹配 24h A/B；只有目标、全部 QC、manifest、presolved/factor 结构、阶段时间和 RSS 均通过，才可考虑 168h。当前未部署固定服务器或 ParaCloud、未启动任何长任务；既有 744h、所有其他输出和 `supplementary_materials/**` 保持未改。

- 孤立梯级节点的等价构建瘦身（2026-07-27，实施提交 `9787ba7`）：保留 `data/hydro/cascade_topology_nodes.csv` 的 142 个节点和 `cascade_topology_edges.csv` 的 124 条边，不删除水电站、GRFR 入流、库容、泄流变量或水量平衡。8 个经核验为“零度、单站”的孤立拓扑节点仅从逐小时核心梯级装配转入既有向量化独立水库平衡；因其无上游到达流且本地入流就是站点 GRFR 可用流量，S4-17 逐项代数等价。有效核心行由 146 降至 138，结果 QC 记录该数量、124 条有效边及 8 个转入独立平衡的节点；未来多站孤立节点会硬失败而不会静默转换。
- 本地完整回归为 `71/71` 通过。全新且隔离的含波浪 Base 根 `outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真，灵活负荷关闭、波浪能开启。24h 与 RUC 瘦身后对照的原始/预处理矩阵均为 `345,992/231,074/1,729,035` 与 `260,116/129,335/1,269,506`（columns/rows/nonzeros）；最优目标差仅 `9.78e-09 million CNY`。添加顺序改变使 factor/crossover 路径有数值差异（`Factor NZ` `6.111e6→6.284e6`、67,614→61,108 simplex），故这只是极小的 Python 约束构建清理，未证明 Barrier 加速或 8760h 内存改善。截断 LP 的退化可导致逐小时调度取不同等价最优基，不能据此解释为物理边界改变。
- 此次仅本地操作：未连接或改动固定服务器 checkout/进程/内存/输出，也未查询或改动 ParaCloud 队列；未启动 744h、8760h、第二个求解或付费云任务。既有输出（含 744h）和 `supplementary_materials/**` 均未触碰。任何未来服务器部署仍需实时复核状态、部署精确已推送提交并先运行单一新命名的匹配 168h 门禁。

- 连续 RUC 的可证明等价瘦身（2026-07-27，实施提交 `3f2255a`）：在不改变任何变量、目标函数、科学情景、容量/备用/惯量/爬坡/最小出力/启停时序或水电约束的前提下，移除了四组已被保留时序行严格蕴含的逐小时上界：`online<=capacity`、`startup<=capacity`、`shutdown<=capacity` 和通用 `gross<=pmax*online`。建模前新硬校验要求完整 RUC 参数、`min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction`；S4-24、S4-25 和 S4-29 仍全部保留，因此这是可行域完全等价的行缩减而非放松。详见 `cispo_full_lp_model_spec.md` §5.5.3。
- 新建且隔离的 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷关闭、波浪能开启。相对于对应的 wave-integrated Base 对照，变量数和最优目标不变（1h 仅有 `-2.33e-10 million CNY` 浮点舍入差，24h 完全一致）；1h/24h 原始行数精确减少 `1,364/32,736`，非零元减少 `2,728/65,472`。24h 原始矩阵由 `345,992/263,810/1,794,507` 降至 `345,992/231,074/1,729,035`（variables/rows/nonzeros），但 presolve 后均为 `129,335/260,116/1,269,506`，且 `AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier、67,614 simplex/crossover 完全相同。该缩减降低的是原始建模/矩阵负担，并未在此尺度改变 Barrier 因子分解瓶颈。
- 更新后的 8760h 静态 preflight 是 `41,186,792` variables、`55,928,636` estimated constraints、`497,144,388` estimated nonzeros、`33.40 GiB`；较原估算少 `11,948,640` 行和 `35,845,920` 估计非零元。它只是结构性预估，绝不能作为全年 Barrier factorization 可行性或 8760h 授权证据。本轮未接触固定服务器 checkout/进程/输出或 ParaCloud 队列，未启动任何服务器、云端、744h 或 8760h 作业；既有 744h 根保持未改。

- 情景边界已按用户指令重置（2026-07-27，实施提交 `c992550`）：唯一可运行的基准为 `base`，其默认包含陆上/海上风电、光伏与已严格映射到既有 marine `grid_uid` 的波浪能；`flexible_load=false`。唯一可运行的柔性覆盖层是 `flexible_load_comfort_v3_v2g_5pct`，它继承同一含波浪 Base，并启用 `comfort_envelope_v3` 冷热状态、EV V1G 与日内因果 5% V2G。其灵活性参数仍为待校准敏感性，不得作为已校准 Base 结论。旧 `flexible_load_v1`、`flexible_load_state_v2`、`flexible_load_v2g_v1`、单独 comfort/wave 及各组合情景 JSON 已删除；历史代码、Git 记录和既有输出均保留且只能按其原情景身份解释。`CISPO_WAVE_ROOT` 因而是两个当前可运行情景的必需运行时数据根。
- 本地验证（`c992550`）：设置 `CISPO_WAVE_ROOT` 后，完整 `unittest discover` 回归为 `66/66` 通过。四个全新截断根 `outputs/2030_{1h,24h}_v0727_wave_integrated_base` 与 `outputs/2030_{1h,24h}_v0727_wave_integrated_flexible_v3_v2g_5pct` 都独立达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，所有 hard checks 为真且 scenario identity/开关复核正确。24h Base 为 raw `345,992/263,810/1,794,507`、presolved `129,335/260,116/1,269,506`（rows/columns/nonzeros）、`AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier、67,614 simplex/crossover、34.074 s、0.735 GiB 峰值 RSS；24h 柔性覆盖层为 `354,920/268,398/1,844,355`、`132,254/266,492/1,299,953`、`2.221e6`、`6.179e6`、`5.905e8`、101、56,990、33.984 s、0.731 GiB。它们均为 `TEST_ONLY_TRUNCATED_HORIZON`，不能解释为年度科学结果或已校准技术经济性。
- 全年静态 preflight（未构建、未求解）现为：wave-integrated Base `41,186,792` variables、`67,877,276` constraints、`532,990,308` nonzeros、36.47 GiB；唯一柔性覆盖层 `44,445,512`、`69,551,896`、`538,014,168`、37.63 GiB。本机可用内存约 15 GiB，低于 96 GiB preflight 门槛；这些静态数值绝不证明 Barrier factorization 可行。此次只做本地工作，未触碰固定服务器 checkout/进程/输出、ParaCloud 队列或历史 744h 根；固定服务器 8760h 和新的付费云端任务仍未授权。

- 本地全模块联合敏感性与求解结构审计（2026-07-27，提交 `31dc265`）：新增显式、独立的 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct` 情景；它同时启用既有 marine `grid_uid` 波浪能、`comfort_envelope_v3` 冷热状态、EV V1G 和 5% 日内因果 V2G，但 `evidence_status=EVIDENCE_ANCHORED_PARAMETERS_REQUIRE_SENSITIVITY`，绝非 Base。完整本地回归 `67/67` 通过。新根 1h、24h、168h 分别达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，全部 hard checks 为真；168h 为 raw `1,081,688/1,429,226/10,293,428`、presolved `751,365/865,314/7,363,654`（rows/columns/nonzeros），`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`、180 Barrier、239,930 simplex/crossover、602.265 s 和 3.296 GiB 峰值 RSS。截断窗口只出现 V1G（上/下移各 190.173 GWh）；冷热、V2G、波浪容量/发电均为零，不能作技术经济性结论。全年静态 preflight 为 44,445,512 variables、69,551,896 constraints、538,014,168 nonzeros 和 37.63 GiB，较 Base 多 8.64% variables/2.88% constraints/3.28% nonzeros/1.63 GiB；它不证明 Barrier factorization 可行。本轮未改变 Base、既有 744h、固定服务器 checkout/进程或 ParaCloud；固定服务器 8760h 和新付费云端任务仍禁止。细节见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`；下一步仅在同机同 profile 的匹配 168h A/B 和资源复核后评估结构优化，不直接放大到全年。

- 固定服务器 Base 168h manifest 闭合门禁（2026-07-27）：在空闲、干净且已 fast-forward 到 `67482ab` 的 `/data/zz2/National_model/repo` 上，以 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48` 运行新根 `/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`。服务器完整回归通过 `67` 项（其中 2 项为可选 xarray 测试而跳过）。门禁为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`；灵活负荷与波浪能关闭，所有 hard checks 为真。LP 原始规模为 1,393,915 行、1,011,079 列、9,797,949 非零元；presolve 后为 729,559/817,723/7,001,232，ordering 26.08 s，`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、`Factor Ops=8.436e10`。Gurobi 为 161 次 Barrier、226,659 次 simplex/crossover、614.894 s；端到端墙钟 12:24.94，进程树峰值 RSS 3.453 GiB（`/usr/bin/time` 3,641,828 KiB），无 swap。QC 最大功率平衡残差 `3.91e-12 GW`、最大约束/边界/对偶违例 `4.17e-8/4.11e-12/1.75e-10`。最终 `stdout.log` 为 18,072 bytes、`stderr.log` 为 1,006 bytes，二者与 `run.pid` 均明确出现在 manifest 的 `excluded_runtime_files`，科学文件验证零失败；这直接验证了 finalize 后 wrapper 继续输出的 P0 修复。该根仍为 `TEST_ONLY_TRUNCATED_HORIZON`，不是全年科学结果。既有 744h 根未写入或重跑；固定服务器未启动 8760h，ParaCloud 未启动新任务。确切下一步：P2 仅设计目录外只读 post-run audit 方案（若协议需要）；P3 在匹配 24h/168h A/B 上记录完整稀疏/Barrier/crossover/RSS 指标后，才评估是否申请新的 744h。
- Manifest 契约 P0 与本地 P1 闭合（2026-07-27，实施提交 `7499062`）：已将通用 `stdout.log`、`stderr.log` 明确加入 `RUNTIME_MANAGED_FILES`，与既有 runner/sequence 日志一样排除在科学输出目录和 result manifest 之外。`tests/test_result_manifest.py` 会创建这两个文件、生成 manifest、随后追加 wrapper 文本，并验证 `validate_result_manifest()` 仍为真。完整本地测试通过 `67/67`。新的独立 2030 Base 根 `outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷和波浪能均关闭。24h 诊断为 342,343 个变量、262,201 条约束、1,771,702 个非零元，求解时间 41.296 s、进程树峰值 RSS 为 0.725 GiB。它们仍是 `TEST_ONLY_TRUNCATED_HORIZON`；未改变固定服务器/云端 checkout、进程或既有 744h 输出。确切下一步：推送审查后的提交，再复核空闲固定服务器后决定是否部署到新的 168h Base 根。
- Solvability A/B decision (2026-07-26, comparison commit `9e82cc5`): explicit nonnegative spill and equality water balances remain the default. Both 168h Base formulations are `OPTIMAL + solution_qc=PASS` with objectives agreeing within `6.2e-8 million CNY`. Projection is 1.84% faster (641.996 versus 654.026 s), but explicit spill reduces presolved rows/nonzeros by 2.03%/0.74%, `AA' NZ` by 0.88%, `Factor NZ/Factor Ops` by 0.67%/0.80%, and telemetry peak solver memory from 3.957 to 3.876 GB. It is also 24.0% faster in the paired 24h flexibility case. Because the 8760h bottleneck is factorization memory, not a 12 s 168h runtime difference, lower factor structure and cross-scenario robustness take priority over removing raw columns. The projected outputs remain preserved as exact-formulation evidence. `scripts/compare_solver_runs.py` writes the paired JSON/CSV audit.
- Solver engineering milestone (2026-07-26, commits `6d84209` and `44f7fef`): a numerics-only `--solver-config` contract, six versioned Barrier/dual-simplex/CPU-PDHG profiles, flushed `solver_telemetry.jsonl` and SIGTERM/SIGINT-to-`Model.terminate()` handling are validated locally. Solver-profile paths/hashes are recorded and cannot modify scientific settings. CPU-PDHG requires the fixed server's Gurobi 13 environment and is not run under local Gurobi 12.
- Dual-simplex 168h rejection (2026-07-26): the fixed-server 16-thread run was gracefully terminated after 905.073 solver seconds and 421,470 pivots, with no feasible solution and repeated primal-infeasibility spikes. This is already 38.4% slower than the complete Barrier-32 reference. Peak process-tree RSS falls from 3.614 to 2.594 GiB, but the convergence loss disqualifies dual simplex from the first 744h gate. The SIGTERM handler wrote a normal `INTERRUPTED` report with `termination_signal=SIGTERM`; logs and telemetry are preserved.
- Barrier-16+AMD 168h result (2026-07-26): `OPTIMAL + solution_qc=PASS` in 644.636 s, 1.44% faster than Barrier-32, with peak process-tree RSS reduced from 3.614 to 3.187 GiB. However, forced AMD ordering reduces ordering time from 25.70 to 9.83 s while increasing `Factor NZ` from `1.036e8` to `1.090e8` and `Factor Ops` from `8.436e10` to `1.059e11`. It is not yet the 744h selection. A new `barrier_16_auto_order_v1` profile isolates the thread/memory effect without the adverse factor-order change.
- Barrier-16 automatic-order 168h result (2026-07-26): current best Barrier profile, `OPTIMAL + solution_qc=PASS` in 637.344 s. It retains the reference `Factor NZ=1.036e8` and `Factor Ops=8.436e10`, reduces telemetry solver memory from 3.876 to 3.538 GB and peak process-tree RSS from 3.614 to 3.459 GiB, and is 2.55% faster than Barrier-32. A first CPU-PDHG launch failed before model loading because `pdhg_gpu` was missing from the solver-profile whitelist; the whitelist and direct profile-loading test are corrected locally, with no model process or scientific output from the failed root.
- CPU-PDHG 168h decision and active 744h gate (2026-07-26): the corrected fixed-server PDHG run was gracefully terminated after 3,074.134 solver seconds and 496,035 recorded telemetry iterations. It used only 1.990 GB peak solver memory and 2.503 GiB peak process-tree RSS, but produced no feasible solution; near termination the log still showed primal residual about `49.5`, a roughly `0.6%` primal-dual objective gap and a rising dual residual. PDHG is retained only as a low-memory research option, not the first scale-up profile. The five-profile comparison is saved under `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}`. With 69 GiB available RAM and no other CISPO solve, a single 744h Base gate using `barrier_16_auto_order_v1`, `Threads=16` and `SoftMemLimit=48` was launched at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`; Python PID was `663050`. This is an active engineering gate, not yet an accepted result. Do not start another fixed-server solve concurrently.
- Active 744h structure checkpoint (2026-07-26): model construction completed in 341.673 s with 3,686,023 variables, 5,920,701 constraints and 42,360,391 nonzeros; build peak process-tree RSS was 4.977 GiB. Presolve took 223.80 s and reduced the LP to 3,088,821 rows, 3,017,979 columns and 30,884,732 nonzeros. Automatic ordering took 115.48 s and produced `AA' NZ=6.449e7`, `Factor NZ=8.062e8` (Gurobi estimate about 9.0 GB) and `Factor Ops=6.197e12`. Barrier iteration 4 completed at solver time 493 s with decreasing primal residual and complementarity; telemetry peak solver memory was 25.087 GB and observed process RSS was about 19.1 GiB. Available host memory remained about 50 GiB. The gate is healthy but not solved; continue monitoring without changing checkout or parameters.
- Active 744h crossover checkpoint (2026-07-27): Barrier completed normally in 244 iterations and 8,917.48 solver seconds with interior objective `2,196,881.94 million CNY`, then entered crossover. At the live checkpoint, dual pushes fell from 1,044,784 to 464,775 remaining and telemetry reached 358,606 simplex iterations at solver time 9,996.25 s. Solver memory was 13.948 GB with the unchanged 25.087 GB peak; process RSS fell to about 13.8 GiB and host available memory rose to about 55 GiB. No `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists yet, so this is a phase milestone, not acceptance.
- Terminal 744h result and manifest rejection (2026-07-27): the run completed `OPTIMAL + solution_qc=PASS` with objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations, 1,451,182 simplex iterations, 3:52:03 wall time, 23.121 GiB peak process-tree RSS and zero swaps. All QC hard checks pass; maximum constraint/bound/dual violations are `9.30e-8/5.50e-8/9.22e-8`, maximum power-balance residual is `2.40e-10 GW`, bidirectional interprovincial edge-hours and maximum DC reverse flow are zero, and nested `scenario.id` is `base` with flexibility/wave disabled. Strict acceptance nevertheless fails: `validate_result_manifest()` reports only `size:stdout.log`, because the manifest hashes 63,631 bytes before the final printed solve report while the wrapper-managed file finishes at 66,236 bytes. The result is mathematically/QC valid but not a closed reproducibility gate. Preserve the output unchanged; fix the wrapper/runtime-managed filename contract and obtain an independently closed manifest before formal acceptance.
- 本轮对话收束与下一阶段（2026-07-27）：实时复核确认固定服务器无 CISPO/Gurobi 进程、约 69 GiB 可用内存，checkout 干净停留在实现 `c879c99`；ParaCloud `squeue` 为空，`4003088/4003172/4004585` 分别保持 `COMPLETED build-only`、`OUT_OF_MEMORY`、`TIMEOUT`，没有已验收 8760h 结果。当前能力边界是“`city_337` Base 月尺度连续 LP 可稳定完成 Barrier+Crossover 并通过全部物理 QC”，不是“全年科学结果已完成”。下一阶段按优先级执行：P0 修复通用 `stdout.log`/`stderr.log` 与 `RUNTIME_MANAGED_FILES` 的 manifest 契约并增加 append-after-finalize 回归；P1 用 1h/24h 和固定服务器 168h 新根验证闭合，不因本缺陷立即重跑 744h；P2 决定既有 744h 采用独立只读 post-run audit 还是在严格协议要求下重跑；P3 基于 744h 与云端 Factor NZ/Factor Ops/MaxRSS 证据开展不改变科学边界的稀疏结构、presolve、Barrier/Crossover 求解性优化；P4 仅在新 24h/168h/744h 门禁、资源方案和付费授权齐备后再申请 8760h。Base 默认继续禁用灵活负荷与波浪能；V3 灵活性校准、贴现路径成本/总转型成本账本以及 MGA 均为后续独立研究工作。
- Cloud Barrier-32 terminal state (read-only audit 2026-07-26): ParaCloud job `4004585` ended `TIMEOUT` after `1-00:00:25`, with the batch step `CANCELLED` at `1-00:00:32`. It retained the sampled 499,919,116 KiB = 476.76 GiB MaxRSS and reached Barrier iteration 35 at solver time 82,521 s. Primal residual/complementarity improved to `1.05e8/6.03e6`, but the primal/dual objectives remained `2.0166e11/-1.4513e13`; no accepted iterate, `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists. This is preserved as scale/convergence evidence, not a scientific result. No ParaCloud job is active.
- Local optional wave-energy integration corrected to the existing optimization grid (2026-07-25, uncommitted worktree based on `796a6fc`): raw wave cells are coordinate-intersected with `optimization_points.csv` and restricted to `is_land=0`, yielding 1,285 unique existing marine `grid_uid` rows, 1,284 positive-potential expansion options, 9,798.111 GW retained raw potential and 57 imputed-CF rows. Province/substation/`city_337` routes are exact reuse of the matched existing rows; the prior nearest-offshore-wind proxy and out-of-bound matches up to roughly 1,524 km are removed. `wave_energy_medium_v1` remains optional and creates no wave variables in Base. Two explicit combined cases enable wave with flexible-load V1 or comfort V3 in the same LP, while Base and all single-module cases remain isolated. Base/wave/wave+flex V1/wave+comfort V3 24h build-only gates succeed at 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. Wave and combined preflight reports have overall `PASS` status with 72 records (67 `PASS`/2 `INFO`/3 unrelated existing `WARN`); full local regression passes 62/62. Full-year static estimates are 41,186,792 variables/67,877,276 constraints/532,990,308 nonzeros/36.47 GB for wave and 42,816,152/68,182,781/533,906,823/36.91 GB for wave+flex V1. No optimization, fixed-server checkout, cloud release, process or output was changed.
- Local comfort-aware flexibility V3 (2026-07-24, uncommitted worktree based on `796a6fc`): the independent `comfort_envelope_v3` formulation preserves Base and every accepted V1/V2 path. `scripts/build_flexible_load_envelope_v3.py` perturbs the original `Power_curve_V2` 2024 BAIT/balance-point equations by `+/-1 C`, carries the original future `thermal_multiplier`, and writes a 1,357,800-row envelope for 31 provinces, 2025/2030/2040/2050/2060 and 8760 h/year. Source-formula reconstruction, National_model load alignment, reduction bounds and finite/nonnegative QC pass; the generated ignored-data SHA256 is `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`. Thermal flexibility uses a causal daily-reset equivalent state, V1G uses a rolling 12h cumulative service deadline, and optional V2G is capped at 5% of province-day baseline EV peak with a causal daily-zero state and a shared V1G+V2G grid-charging power limit. Activation costs are component/direction specific and V1G/V2G moved energy is charged once. Local regression is 58/58. Both 2030 24h gates are `OPTIMAL + solution_qc=PASS`: no-V2G has 349,039 variables/265,270 constraints/1,807,414 nonzeros and 33.63 s solver runtime; final 5%-V2G has 351,271/266,789/1,821,550 and 38.60 s. All state/backlog/V2G/combined-charging residual and terminal checks pass, with zero simultaneous operations. The V3 scenario input and sidecar are included in `input_manifest.csv`. No fixed-server/cloud checkout, process or output was changed; no 168h/744h/8760h V3 run is authorized by this milestone.
- Local state-based flexible-load enhancement (2026-07-24, implementation `271c6dc`): `flexible_load_state_v2` adds daily-reset equivalent heating/cooling inventories and a causal EV V1G charging backlog while preserving Base and the accepted legacy V1/V2G formulations. `Power_curve_V2` `ev_hour_weight` is explicitly treated as the uncontrolled charging baseline rather than plug availability; V2G is rejected in the new state formulation until calibrated availability/battery/departure inputs exist. The final local 2030 24h gate is `OPTIMAL + solution_qc=PASS`, with state/backlog transition residuals at most `8.88e-16 GWh`, zero terminal states/backlog, zero simultaneous up/down and a valid result manifest. A four-year 1h diagnostic chain passes all solve/QC/manifests and immediate `--resume`. Full regression is 56/56. Base and existing scenario JSON files are unchanged, so accepted V1/V2G scenario identities remain reproducible. This implementation is not deployed to the fixed server or active cloud release.
- Local correctness hardening (2026-07-24, based on `4b5bd98`): runtime VRE CF resolution now forbids wind-to-PV fallback and permits missing wind only to the same-grid `mixed_wind` store; nearest-province PV fallback candidates must be land-centroid PV grids. The active data audit finds 35 onwind and 10 offwind rows using valid same-grid mixed-wind, zero wind-to-PV mappings, and 141 PV-family nearest-grid fallbacks. Excluding water-centroid PV donors changes zero current donor assignments, so this closes a latent future-data bug without changing the current Base feasible set or cloud run. Four focused tests and the complete 54-test regression suite pass. `MODEL_IO_CONTRACT.md` and `SCENARIO_MODULE_ARCHITECTURE.md` now consistently identify `city_337` as an annual load-center/transmission proxy, not a city-hourly dispatch network; 278 Natural Earth remains replication/sensitivity only.
- Cloud execution update (2026-07-24): the staged `city_337` release passed both mandatory single-year 2030 Base engineering gates. Job `4003035` (24h, 32 CPU/64G) is `OPTIMAL + solution_qc=PASS`, with 342,343 variables, 262,201 constraints, 1,771,703 nonzeros, 26.978 s solver time and 0.834 GiB peak process-tree RSS. Job `4003045` (168h, 32 CPU/64G, `m4ci1805`) is `OPTIMAL + solution_qc=PASS`, with 1,011,079 variables, 1,393,915 constraints, 9,797,949 nonzeros, 377.057 s solver time and 3.661 GiB peak process-tree RSS. Both pass all 50 regression tests and independent `solve_report`/`solution_qc`/result-manifest validation.
- Full-year cloud terminal state (live read-only audit at 2026-07-25 02:14 CST): structural job `4003088` remains accepted as build-only, but the authorized real 2030 job `4003172` ended `OUT_OF_MEMORY`, exit `0:125`, after 5:44:03 on `m4cg1702`. The 40,912,327-variable/68,189,325-constraint/515,040,080-nonzero model completed Gurobi presolve in 17,932.25 s and reduced to 35,423,761 variables, 37,982,903 constraints and 400,861,556 nonzeros. It then reached ordering for barrier factorization but was OOM-killed before barrier iteration 0. Slurm recorded 526.99 GiB MaxRSS/527.03 GiB MaxVMSize against a 700G request; the node rebooted shortly after the failure, so sampled MaxRSS may not capture the terminal spike and the exact kernel/cgroup cause requires cluster-admin evidence. No `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists. The output is a failed scale/memory diagnostic, not a scientific result. No cloud job remains active; do not resubmit the same configuration or start 2040.

- User-authorized Barrier-32 retry (live audit at 2026-07-25 02:35 CST): ParaCloud job `4004585` is `RUNNING` on `m4cg1702` from the immutable `22fb493` Base/`city_337` release. The only solver-resource change from failed job `4003172` is `Threads=128 -> 32`; `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, the 700G request, 24h limit and all scientific settings are unchanged. The new script SHA256 is `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`, and the isolated output root is `outputs/full_year_2030_base_22fb493_barrier32_700g_v0725`. The 50-test gate passed in 11.845 s and the generated config records `threads=32`. Because the 700G memory request forced Slurm to allocate 96 CPU billing units despite `CPUs/Task=32`, scheduler billing for this run accrues at 96 core-hours per wall-clock hour. The prior failed job consumed 2,642,304 allocated CPU-seconds = 733.973 core-hours, while its actual `TotalCPU` was only 7:03:11. No solve/QC/manifest is expected until optimization completes; do not start 2040 or another retry while `4004585` is active.

- Barrier-32 live progress (read-only audit at 2026-07-25 20:30 CST): job `4004585` remains `RUNNING` on `m4cg1702` after 17:55:54. It completed ordering in 3,180.53 s and, unlike failed job `4003172`, entered Barrier iterations. The presolved system has `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, an estimated 340.0 GB factor footprint and `Factor Ops=2.448e15`; iteration 23 completed at solver time 60,528 s. Primal residual and complementarity decreased from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7` at iteration 23, so the process is advancing but is not close to an accepted solution. Current sampled `MaxRSS` is 499,919,116 KiB = 476.76 GiB, below the failed 128-thread sample. Slurm has 6:04:06 remaining and will end the job at `2026-07-26 02:34:26 CST`; recent iterations take roughly 30-32 minutes, so completion within the current wall limit is uncertain and no solve/QC/result manifest exists. No scheduler setting was changed during this audit.

### Version identity

- Latest cloud audit (2026-07-24): the user-authorized city_337 release is staged at `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`. Code archive SHA256 is `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`; all 11,350 runtime-input files (model-ready, hourly CF and hydrology) match the fixed-server SHA256 manifest (`662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`). Compute-node job `4001137` completed the 2030/8760h preflight: 175.17 GiB available memory, 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB static model-memory estimate. It did not construct or solve a Gurobi model.
- Cloud proxy/WLS was revalidated on 2026-07-24 after repairing the three malformed `.bashrc` exports (the pre-fix file is retained as `.bashrc.codex_backup_20260724_proxy_export`). Compute-node job `4002980` inherited the proxy from `.bashrc` and reached `token.gurobi.com` through `172.16.110.3:8888` with HTTP 302. WLS job `4002981` then completed `Env.start()` and a tiny LP with `GUROBI_SMOKE_PASS`/`OPTIMAL` on `m4ci1905.para.bscc`. A short standalone curl probe in that smoke still timed out, so treat Gurobi's successful authenticated solve—not curl alone—as the license gate. Cloud 24h/168h gates are now eligible; full-year build-only remains downstream of those gates.

- Handoff version: `v0.9.66`
- Snapshot date: `2026-07-28`
- Local repository: `D:\codeenv\pycharmproject\National_RL\National_model`
- Git branch: `codex/cispo-2030-full-lp`
- Live identity after P1 deployment: local/server shared HEAD was `67482ab` before this documentation closeout; the fixed-server checkout is clean and has no CISPO/Gurobi process. It contains the P0 implementation `7499062` plus prior documentation; relative to the prior server implementation `c879c99`, the only model-adjacent code change is the runtime-log manifest exclusion, not LP/data/scenario logic. `9e82cc5` retains explicit reservoir spill, `84a277c` adds the automatic-order Barrier control, and `c879c99` completes the traceable CPU-PDHG profile contract. The matched spill and five-profile 168h outputs are preserved. The fully rebuilt `city_337` package is the production configuration; 278 Natural Earth remains separate. The fixed server uses the additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- A separate ParaCloud/BSCC-A8 endpoint was authenticated on 2026-07-20 through both configured IPv4 routes using the existing local public key. The remote host is `ln301.para.bscc`, account `a8s001819`; port 22 is primary and 2222 is fallback. The official Gurobi 13.0.2 Linux package is staged privately on the cloud. Following transient refusal in `4000608`, `4000762` and `4001248`, the user-authorized `.bashrc` repair and fresh compute-node WLS solve `4002981` restore the cloud license gate. The proxy is now inherited by batch shells from `.bashrc`; retain explicit lower-/upper-case exports in production scripts as defensive reproducibility, and do not regard the short curl timeout in `4002981` as a replacement for the authenticated Gurobi smoke result.
- SSH access was restored on 2026-07-19 by using the configured `national-model-server` alias, which binds the approved workstation source address. The obsolete PID `863603` was not active and no CISPO solve process remained.
- Server readiness, raw-GRFR SHA256 verification and 24/24 regression tests passed on the new versioned data roots. The server 24h gate is `OPTIMAL` in 60.53 s with `solution_qc=PASS`.
- After commit `1b6da28`, server regression tests passed 26/26 and the corrected 24h transmission gate reached `OPTIMAL` in 43.88 s with all directionality/QC/manifest checks passing.
- PID `3778049` completed mathematically `OPTIMAL`, but its result is rejected as a physical model gate because the prior QC omitted 3,358 material AC bidirectional edge-hours.
- Initial handoff-document commit: `1ac58dd`
- Server repository: `/data/zz2/National_model/repo`
- Server Git remote: `/home/zz2/git/National_model.git`
- At handoff version `v0.2.0`, local code was committed and pushed as `8e49a87`, and the server checkout under `/data/zz2/National_model/repo` was fast-forwarded to that commit before data/readiness validation. Always confirm the live HEAD with `git rev-parse --short HEAD` rather than treating a documentation commit as immutable current state.

### Fixed model boundary and architecture

- 2025 is an input boundary condition, not an optimization year.
- 2030 is the first planning year and represents capacity changes during 2025-2030; accepted capacity cohorts then pass sequentially to 2040, 2050 and 2060.
- The scientific production model is one continuous national LP with 8760 chronological hours.
- No Benders decomposition, representative periods, sampled hours or temporal weights are used.
- Test horizons are `one_month=744h` and `six_months=4344h`; their annual costs and policy constraints are not rescaled, so their solutions are engineering tests rather than planning results.
- Per-year entry is `scripts/run_cispo_2030_full_year.py`; the isolated multi-year entry is `scripts/run_cispo_planning_sequence.py`.

### Implemented model scope

- 31 provincial load regions; Inner Mongolia is not split.
- 36,686 VRE technology-site rows with 2023 hourly capacity-factor linkage.
- Continuous capacity-based thermal RUC, ramping, reserve and inertia.
- Battery and PHS state of charge; station-level hydropower, reservoir balance and committed core-cascade hydropower coupling for the Stage2 recommended mainstem groups.
- 411 interprovincial transmission corridors and strict hourly provincial power balance.
- Nuclear upper bounds, a shared `bio+bioccs` capacity upper, the CISPO Table S17 2030 battery floor and AC-only reverse-flow active indexing are committed and deployed. V0720 changes only provenance, exports, diagnostics and state acceptance; it does not change the feasible set.
- DAC, annual carbon and biomass accounting, CCS capture and point-level injection.
- Spur line, trunk line and substation augmentation.
- The production load-center scenario is `city_337`; the 278-node Natural Earth paper replication is retained as a separate reproducibility/sensitivity input.
- Annual load-center energy allocation, provincial export closure and a 642-edge intraprovincial AC500 proxy expansion layer are implemented. The 2025 city network initializes 203 positive-capacity edges.
- Wind, solar and hydropower use spatial spur/trunk routing. Thermal, nuclear and biomass generation are allocated within each province by load-center demand shares.
- Optional `flexible_load_v1` and `flexible_load_v2g_v1` modules are implemented behind explicit scenario files. Base creates no flexibility variables. The current values are illustrative sensitivity assumptions, not calibrated transport/building parameters and not CISPO source values.
- Optional `wave_energy_medium_v1` is implemented only on existing marine optimization `grid_uid` rows behind an explicit scenario file. Base creates no wave variables. Wave capacity is grid resolved and hourly generation is province aggregated after applying site CF; costs, potential scaling and the explicit 2060 hold remain sensitivity assumptions. Explicit wave+flexibility V1 and wave+comfort-V3 combined cases are also available.

Detailed definitions are in `cispo_full_lp_model_spec.md` and `LOAD_CENTER_NETWORK_278_年度输电层说明.md`.

### Server runtime

- Host login: `zz2@210.77.85.166`; SSH identity path on the workstation is `%USERPROFILE%\.ssh\server_ed25519`. Never read or copy the private-key contents.
- Server hardware observed: 96 logical CPUs and about 125 GiB RAM.
- Python environment: `/home/zz2/.local/envs/cispo-2030`, Python 3.11.15.
- Gurobi Optimizer: 13.0.2 at `/home/zz2/opt/gurobi1302/linux64`.
- `gurobipy`: 13.0.2 in the `cispo-2030` environment.
- GPU test environment: `/home/zz2/.local/envs/cispo-gurobi-gpu` with `gurobipy 13.0.2+cu129`; it is isolated from the production CPU environment and should be used only for PDHG tests with `Method=6`, `PDHGGPU=1`.
- Gurobi 12.0.1 remains installed as rollback software.
- License file: `/home/zz2/gurobi.lic`, mode `0600`, issued license ID `2840423`, valid through `2027-07-02`.
- The activation key and license-file contents must not be committed or copied into documentation.

### Server data paths

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260723_v0722_city337
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

### Latest verification evidence

- Fixed-server 168h `city_337` Base sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337` and immediate `--resume` pass. Solver runtimes are 733.00/811.58/892.10/1397.12 s; wall time 1:13:47; peak RSS 4,085,152 KiB; zero swaps. Every year is `OPTIMAL + solution_qc=PASS`, has zero false hard checks, 337 center rows, 642 intra-edge rows, 31 province-account rows and 59 manifest entries. Maximum center/province/intra-capacity/power residuals are `7.09e-11 GWh`, `2.73e-12 GWh`, `8.24e-12 GWh` and `1.78e-10 GW`; BECCS net-carbon residual is numerical zero. Compared with the prior 278 Base gate, the 337 layer adds only 1,031 variables, 924 constraints and 2,749 nonzeros at 168h; total solver time increases 4.68%, dominated by a 706.6 s 2060 Crossover.
- Fixed-server `city_337` `flexible_load_v1` 24h and 168h sequences both pass four years and immediate `--resume`. The 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1` has runtimes 714.39/816.08/1007.71/980.09 s, wall 1:08:59, peak RSS 4,030,672 KiB and zero swaps. Every year is `OPTIMAL + solution_qc=PASS`, has 59 validated manifest entries, 337 center rows, 642 intra-edge rows and 31 province/flexibility accounts. Maximum heating/cooling/EV V1G residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; simultaneous up/down is zero, V2G is disabled and BECCS/network/security checks pass. Versus city_337 Base, V1 adds 3.09% variables and 2.23% nonzeros but total solver time is 8.23% lower; 2050/2060 crossover remains the main variability source.
- The independent V2G 24h and 168h roots both pass four years, manifests and immediate `--resume`. The accepted 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` has runtimes 792.55/806.12/953.60/1033.25 s, wall 1:09:57, peak RSS 4,087,888 KiB and zero swaps. All years are `OPTIMAL + solution_qc=PASS`, have 59 validated manifest entries, V2G transition residual at most `1.90e-13 GWh`, zero simultaneous charge/discharge and exact period loss closure (`charge-discharge = net_load_energy_change`). The fixed server is now idle; do not launch 744h/8760h without a new explicit authorization.
- Fixed-server 24h `city_337` Base sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337` passes four years and `--resume`. Solver runtimes are 43.29/48.82/41.17/46.90 s; wall time 7:21; peak RSS 930,204 KiB. Every year is `OPTIMAL + solution_qc=PASS`, Base flexibility is disabled, security is 5%/3.5 s, 337 center rows and all 59 manifest entries are present, and maximum center/province/intra-capacity residuals are `3.01e-12/4.55e-13/4.61e-10 GWh`. BECCS net-carbon closure is zero.
- The first server smoke attempt exposed a stale row-count contract (1,240 expected versus the correct 31 provinces × 5 years × 10 thermal/biomass technologies = 1,550). Commit `cf39e0a` fixes only that test and adds uniqueness/year/technology checks. Local and server smoke then pass 142/142; server tests pass 50/50, readiness/full-license gate passes, and preflight passes.
- Local implementation `8e76753`: the new additive `data/load_center_network/city_337/` package contains 337 city centers, 16,609 VRE routes, 2,030 hydropower routes and 642 same-province edges. All 31 provincial graphs are connected; province demand shares close within `1.11e-15`; 2025 initialization includes 1,310.0 GW connected wind/utility PV, 530.0 GW local DPV, 297.8895 GW existing hydro and 647.8401 GW summed intra-edge capacity, with maximum balance residual `7.28e-14 GW`. Exact joint routing improves spur+trunk distance by 20.21 km on average versus the former nearest-substation-first logic. Regression tests pass 50/50 and preflight passes 61 checks with zero hard failures. The local four-year 1h Base sequence `outputs/planning_sequence_1h_v0722_city337` is `PASS`; every year is `OPTIMAL + solution_qc=PASS`, exports 337 load-center balance rows and a 59-file manifest, and a fresh `--resume` returns four `RESUMED_ACCEPTED` records. This is engineering evidence only.
- Live fixed-server audit before deployment: clean checkout `6ed943a`, no active CISPO/Gurobi solve, approximately 35 GiB available RAM and swap nearly full. The accepted V1 168h root remains `PASS` with four resumed years. This resource state allows only the new 24h/168h gates; fixed-server 744h/8760h remain prohibited.
- Local uncommitted reliability update at Git HEAD `e28f315`: 49/49 regression tests PASS. The real 1h engineering gate `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS`; effective inertia is recorded as `3.5 s`, capacity-margin and inertia hard checks pass, and the result manifest validates with zero mismatches. No server checkout, process, data root or output was changed. User-owned `supplementary_materials/**` changes remain untouched.
- Local `c62b769` validation: 47/47 regression tests pass. Real Base 1h gate `outputs/2030_1h_v0722_beccs_mass_balance` is `OPTIMAL + solution_qc=PASS`; all four new BECCS/captured-CO2 hard residuals are exactly zero, all six explicit BECCS accounting fields are present, and the 59-file result manifest validates with zero mismatches. The parameter audit under `outputs/parameter_audit_20260722_beccs_mass_balance` reports 11,681 rows, 22 PASS, 0 WARN, 0 HARD_FAIL and six remaining open/scenario-required risks; the former P0 BECCS mass-balance risk is closed for the zero-lifecycle CISPO baseline.
- Local implementation `c91828a` adds `scripts/run_cispo_sensitivity_suite.py` and identity-safe tests without changing the model formulation. All 45 regression tests pass. A real 1h suite under `outputs/sensitivity_suite_1h_v0722_interface` ran Base, `flexible_load_v1` and `flexible_load_v2g_v1` as three isolated 2030→2040→2050→2060 state chains: all 12 year-scenario cases are `OPTIMAL + solution_qc=PASS`, all hard checks and 59-file result manifests pass, Base reports flexibility disabled, V1 reports V2G disabled and V2G is enabled only in its independent scenario. A suite-level `--resume` audit returned all three scenarios and all four years as accepted without re-solving. The original suite report was preserved in `sensitivity_suite_history` with SHA256 `2140efc5ac4cbb4e9dedbaf4e1d8f43593c05132d638e08dccc1526b5da63766`.
- Local `6ed943a` validation: 42/42 regression tests pass; Base 1h, `flexible_load_v1` 24h and `flexible_load_v2g_v1` 24h all reach `OPTIMAL + solution_qc=PASS`; all three result manifests validate with zero mismatches. The V1 24h run has daily heating/cooling/EV closure errors below `2e-13 GWh`, no simultaneous up/down and reduces the test-period national peak from 1229.55 to 1215.78 GW. The V2G run has maximum SOC-transition residual `5.55e-17 GWh`, zero simultaneous charge/discharge and records 0.0231 GWh of charging-loss energy. These are truncated engineering gates, not planning results.
- The active load table contains 1,357,800 rows for 31 provinces, five model years and 8,760 h per province-year. `demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw` closes to `8.53e-14 GW` on the loaded arrays and all components are nonnegative. The refreshed parameter audit expands 11,681 runtime rows with 22 PASS, 0 WARN and 0 HARD_FAIL; seven scientific risks remain open.
- Full-year static estimates are Base 40.91M variables/67.60M constraints/36.00 GiB, flexibility V1 42.54M/67.91M/36.44 GiB and V2G 43.36M/68.18M/36.70 GiB. These are construction estimates and do not reduce the 96 GiB availability gate or bound barrier factor memory.
- V0721 implementation `0c1eaf2` is pushed and deployed to the fixed server. Local and server regression tests pass 37/37. The local real 1h 2030→2040→2050→2060 diagnostic chain and a subsequent `--resume` audit both report `PASS`; all four years are `OPTIMAL + solution_qc=PASS + accepted state`.
- New server data root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state` was copied additively from the V0719 root and receives only the rebuilt fuel tables. SHA256 matches the local files: `province_fuel_prices.csv` = `b6867259317b419bc8b35aedf6b614fd930cf0eed9620fdddeca6fc6434c50a1`; `province_fuel_generation_cost_by_year.csv` = `e1133fbfc798a15524e3ee920a0c6e3e771206874427abcef7db399227df94cd`.
- Local and server parameter audits each expand 11,658 active runtime parameter rows and report 22 PASS, 0 WARN, 0 HARD_FAIL, with seven scientific risks retained separately. Province-level biomass/BECCS fuel costs now cover every model province and are no longer zeroed in the objective.
- Fixed-server 24h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state` and a subsequent `--resume` chain-identity audit both report `PASS`. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 49.42/46.49/45.98/45.74 s, wall time is 6:03 and peak RSS is 0.879 GiB. States are explicitly `TEST_ONLY_TRUNCATED_HORIZON`.
- Fixed-server Base 168h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS` for 2030/2040/2050/2060 and passed an immediate `--resume` identity audit. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 708.80/708.69/1107.69/1137.22 s, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero. Each result manifest validates with zero mismatches. It ran from checkout `b6ca42d` containing implementation `0c1eaf2` and is retained as the uncontaminated pre-flexibility Base gate.
- After deployment to `6ed943a`, the fixed server passes 42/42 regression tests with all three external data roots explicit. Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` and its immediate resume audit both report `PASS`: all years are `OPTIMAL + solution_qc=PASS`, wall time is 6:32, peak RSS is 946,804 KiB and swap is zero. Daily heating/cooling/EV residuals are at most `6.44e-13 GWh`, simultaneous up/down counts are zero, all manifests validate, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- Fixed-server four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, every hard QC check passes, and each 59-file result manifest validates with zero size/SHA256 mismatches. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Heating/cooling/EV V1G daily-energy residuals are at most `8.17e-13 GWh`, all simultaneous up/down counts are zero, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`. A fresh `--resume` identity audit reports four `RESUMED_ACCEPTED` years and sequence `PASS`; diagnostic states remain `TEST_ONLY_TRUNCATED_HORIZON`.
- The pre-fix V0720 2030 168h comparison gate completed `OPTIMAL + solution_qc=PASS` under `/data/zz2/National_model/outputs/2030_168h_v0720_io_contract_server`: solver runtime 799.07 s, wall time 16:06, peak process-tree RSS 3.762 GiB. It omits biomass fuel cost and is retained only as a comparison baseline.
- V0720 implementation `b40900a` is pushed and deployed to the clean fixed-server checkout. Local and server unit tests pass 34/34; the V0719 server data package passes 139/139 smoke checks.
- Server 24h I/O-contract gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, Gurobi runtime 43.65 s and peak process-tree RSS 0.838 GiB. All 27 hard checks pass; result-manifest validation has zero mismatches; all NPZ files load with `allow_pickle=False`; dual export contains 744 hourly and 3,366 annual rows.
- The output contract now includes immutable configuration/environment/input manifests, a 50-file output catalog, a 493-row data dictionary, province-technology capacity and generation tables, security/adequacy/resource diagnostics, hourly marginal prices, annual shadow prices and verified capacity-cohort state transfer. Detailed definitions are in `MODEL_IO_CONTRACT.md`.
- The pre-V0719 744h run at old commit `5a9f4ab` is an accepted engineering gate only. Its solver/QC passed, but the old result manifest is not closed: `run.stdout` and `run.time` were modified by the wrapper after hashing. See `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.
- V0719 local capacity-bound/DC-sparse correction: 32/32 unit tests PASS; 139/139 data-package smoke checks PASS; strict 24h output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, 39.79 s solver time and 0.702 GiB peak RSS.
- New bound QC is zero for nuclear floor/upper, shared biomass+BECCS upper and battery/PHS floor. DC reverse maximum and AC bidirectional edge-hours are zero; maximum power-balance residual is `7.43e-12 GW`.
- Full-year V0719 estimator: 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and about 36.0 GiB static model memory. Exact DC variable removal is `363×8760=3,179,880`; no runtime or factor-memory speedup is inferred from this structural reduction.
- Server V0719 deployment root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was copied additively from the completed sparse root, then supplemented with the three generated V0719 bound tables, `sets/model_years.csv` and 28 canonical smoke/QC/source files that were absent from the old sparse root. The old root and completed 744h output were not overwritten.
- Server V0719 gates on 2026-07-19: checkout HEAD `bc83663`; readiness PASS; 32/32 unit tests PASS; 139/139 smoke checks PASS; 24h solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s, peak RSS 0.841 GiB and zero nuclear/biomass/storage/DC/AC hard-check violations.
- Requested 8760 direct trial was not launched because the live memory gate failed: `scripts/run_cispo_2030_full_year.py --horizon full_year --preflight-only --output-dir /data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` versus required `96.0 GiB`. It produced a V0719 full-year estimate of 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and 36.0 GiB static model memory; no full-year model was built or solved.
- Server 744h strict gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed on 2026-07-19 19:44 Asia/Shanghai under deployed HEAD `5a9f4ab`. It reached `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, solver runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Hard QC passed with zero bidirectional interprovincial edge-hours, zero DC reverse flow, maximum power-balance residual `3.64e-10 GW`, and maximum constraint/bound/dual violations `9.73e-8`/`6.59e-8`/`8.81e-8`.

- Commit `5a9f4ab` is pushed and deployed. Local tests passed 29/29; the strict local 24h solve reached `OPTIMAL` in 32.00 s with peak RSS 0.694 GiB and every QC hard check passed.
- The corrected server 168h gate under `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict` contains 1,071,032 variables, 1,392,960 constraints and 10,100,058 nonzeros. It reached strict `OPTIMAL` in 666.45 s with peak RSS 3.910 GiB, maximum constraint violation `4.17e-8`, zero AC bidirectional edge-hours, zero DC reverse flow and `solution_qc=PASS`.
- The equivalent annual-network rewrite reduced 168h nonzeros by 380,581 (`3.63%`) without changing decision-variable count. Directly eliminating the VRE/ROR availability auxiliaries was tested and rejected because it duplicated CF coefficients in availability and reserve rows.
- The full-year runtime memory gate is now 96 GiB. The scale estimator covers all current variable blocks exactly (44,091,176 projected variables), estimates about 520.9 million nonzeros and 36.71 GiB static model memory, and explicitly does not treat this as a barrier-factorization guarantee.
- Corrected 744h CPU barrier gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has passed for deployed HEAD `5a9f4ab`. This preserves the sparse transmission/load-center formulation gate, but it does not include the uncommitted V0719 capacity-bound/DC active-index corrections.
- Solvability audit commit `ab9dfe8` records the revised 8760h projection: 44,091,176 variables, 68,188,384 constraints and about 515-524 million nonzeros. The existing 853.5 million preflight nonzero count is a conservative structural upper estimate, while its 46.62 GiB memory number is not a barrier peak-memory estimate.
- Current 24h and 168h build-only numerical audits were written under `outputs/audit_24h_20260719_system_solvability` and `outputs/audit_168h_20260719_system_solvability`. They contain 350,024/261,280/1,867,008 and 1,071,032/1,392,991/10,480,639 variables/constraints/nonzeros respectively.
- Rejected 744h solver evidence identifies the scaling bottleneck: presolved 3,274,450 rows and 3,353,208 columns; `Factor NZ=8.289e8` (about 10 GB); barrier 10,969.01 s and crossover 9,123.64 s. Linear factor-memory extrapolation alone is about 118 GB at 8760h, so a direct solve on the 125 GiB host is high risk even if build-only succeeds.
- A current-model 24h `Crossover=0` re-audit returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. A candidate `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7`, `Crossover=1` run reached `OPTIMAL/QC PASS` in 37.38 s versus the approximately 40.02 s local strict baseline; this candidate is not approved for production until a corrected 168h/744h comparison passes.
- Live server HEAD remained `f22b9cf`; available RAM was about 30 GiB and all 21 GiB swap was occupied. No large server process was launched.

- Local implementation commit `2a0ee99` plus planning-state export test commit `ecfc7ed`; AST 38 files PASS; unit tests 24/24 PASS; data-package smoke 124/124 PASS.
- Final local 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; Gurobi `OPTIMAL` in 58.79 s; peak RSS 0.698 GiB; `solution_qc=PASS`; maximum power-balance residual `3.90e-11 GW`.
- Local full-year preflight: PASS, zero hard failures; 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory. The workstation does not meet the 64 GiB full-year construction gate.
- Nonempty 2040 state-transfer diagnostic: `OPTIMAL/QC PASS`; inherited 2.5 GW battery and 1.0 GW PHS cohorts entered the intended province-technology lower bounds exactly.
- PHS source/QC: GHT 2026 province-level 8h storage; national operating floor 65.94 GW; 2030 project upper 249.191 GW; 2040+ upper 514.755 GW.
- Outputs: compact capacity/generation/storage/monthly/hourly summaries, SVG quicklooks and SHA256 result manifest are implemented and validated. Detailed audit: `MODEL_SYSTEM_AUDIT_20260718.md`.
- Minimal server bundle prepared from HEAD `dafeb24` with `--skip-cf` and locally rehashed: `national_model_code.tar.gz` 283,416 bytes SHA256 `1311f3ccfd53b26248e37c13370016a6b5e6165f717d1bde0e79c21d3cd73a4d`; `model_ready_data.tar.gz` 49,131,551 bytes SHA256 `502a60e58da959bfa6e5c3ba2ea83a8d39c3aade212231e5c6ecc42db6a9eb17`; `hydro_timeseries.tar.gz` 24,777,505 bytes SHA256 `573d1285eb4787a3058bff8c25b382a5df6630441de2c5e5b8d58095fbfd70f5`. The data archive contains the PHS bounds and no untracked `supplementary_materials/` files.
- On 2026-07-19 those two data archives were uploaded, verified with the same SHA256 values and extracted additively to the current server roots. Readiness passed with 28/28 required tables, 2,030 hydro stations, 124 cascade edges, full-license confirmation and both raw-GRFR hashes valid; server `unittest` passed 24/24 in 19.62 s.
- Server 24h output `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_sequential_sparse_cpu`: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; Gurobi `OPTIMAL` in 60.53 s; maximum constraint violation `1.32e-08`; peak process-tree RSS 0.851 GiB; `solution_qc=PASS`.
- Replacement 744h preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated memory. PID `3778049` was alive after 55 s with empty `stderr` under `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`.
- At launch, another user's four training jobs occupied about 67 GiB RAM; server available RAM was about 49 GiB and swap was full. This is adequate for the 744h estimate but below the configured 64 GiB full-year gate, so 8760h was not started.

- Local implementation commit: `8e49a87` (`fix: harden CCS and station-level hydropower model`) pushed to `origin/codex/cispo-2030-full-lp`.
- Raw GRFR transfer to `/data/zz2/National_model/data/grfr_raw_2019` completed and was verified by server-side file size and SHA256:
  - `output_pfaf_03_2019.nc`: `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures; hydropower station rows `2030`, reservoir rows `620`, run-of-river rows `1410`, potential paper-rule mismatches `0`.
- Server regression tests: `15 passed in 20.75s` with pytest.
- One-month server preflight: 4,300,620 variables, 6,004,434 constraints, 74,591,808 nonzeros; estimated memory 4.19 GiB; memory gate passed with about 110.24 GiB available.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros; estimated memory 47.98 GiB; memory gate passed with about 110.22 GiB available.
- Local verification before server sync: AST parse passed for 14 changed Python files; `unittest discover -s tests -q` passed 15 tests; data-package smoke test passed 113/113 checks; 24h station-hydro solve reached Gurobi `OPTIMAL` and `solution_qc.json` reported `PASS`.
- Verification scripts: `scripts/check_gurobi_full_license.py` and `scripts/check_server_readiness.py`; the latter now enforces raw GRFR presence and optional SHA256 verification.
- Local cascade implementation verification on 2026-07-06:
  - Stage2 source path `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630` is readable.
  - Generated cascade topology contains 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations across 5 recommended core groups.
  - All 146 Stage2 station IDs map into current `data/hydro/hydro_stations.csv`; all are `reservoir_storage`; capacity alignment residual is 0.0 GW; the directed topology is acyclic.
  - GRFR cross-correlation lag estimation produced non-negative 3h-multiple lags with range 0-168 h; 4 edges have low lag correlation and 18 edges select the 168 h search bound, so these are WARN-level topology/lag QA items.
  - `scripts/build_cispo_data_package.py` with ArcGIS Pro Python regenerated the local data package with 90 QC checks and zero failures.
  - `python scripts/smoke_test_data_package.py` passed 118/118 checks.
  - `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 16/16 tests.
  - `scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only` passed and estimated 4,761,900 variables, 6,465,714 constraints and 78,282,048 nonzeros.
  - A custom 24h monolithic build with `compute_max_cf=False` succeeded with 422,596 variables, 342,510 constraints and 2,037,793 nonzeros; reservoir variables now include `reservoir_turbine_flow`, `reservoir_spill_flow` and `reservoir_volume`; core cascade rows = 146 and edges = 124.
- Cascade server deployment and verification on 2026-07-06:
  - Server checkout HEAD `7a2ca27` contains implementation commit `b3e6298`.
  - Versioned data roots are `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade` and `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`.
  - Server readiness with raw-GRFR SHA256 verification passed; it reported 2,030 hydropower stations, 620 reservoirs, 1,410 run-of-river stations, 142 cascade nodes, 124 edges, 4 low-correlation edges, 18 max-lag-bound edges and maximum lag 168 h.
  - Server regression tests passed 16/16 in 20.12 s.
  - Server `one_month` preflight passed with estimated 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros and 4.48 GiB model memory.
  - The actual 744h model build completed with 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
  - The optimization output directory is `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade`; PID `244035` remained active at 2026-07-06 22:37 Asia/Shanghai after about 5 h 59 min.
  - Gurobi reported large matrix-coefficient and RHS ranges, barrier restarted near iteration 111, dual crossover pushes completed, and primal cleanup was still active at about 1,919,682 remaining pushes with `PInf=3.1246436e+02`. No `solve_report.json` or `solution_qc.json` existed at that checkpoint, so the 744h gate is not yet passed.
- Numerical-stability implementation and validation on 2026-07-07:
  - Commit `281f9c7` scales reservoir flow variables to `10^3 m3/s` and reservoir volume variables to `10^6 m3`, preserving physical `m3/s` and `m3` at all inputs, exports and QC checks.
  - `coefficient_zero_tolerance=1e-6`, `hydrology_flow_zero_tolerance_m3s=1e-4`, `BarConvTol=1e-8`, `Crossover=1` and `Threads=-1` are explicit configuration values.
  - Local numerical audit at 24h improved matrix coefficients from approximately `1e-10–3600` to `1e-6–24`, RHS from approximately `2e-13–4.48e10` to `4.32e-7–1.17e5`, and removed all coefficients/RHS below `1e-8` in the audited model.
  - Local 24h full solve: 422,596 variables, 342,508 constraints and 2,037,549 nonzeros; Gurobi `59.66 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.865 GiB`.
  - Server checkout was fast-forwarded to `281f9c7`; 18/18 tests passed in `19.46 s`.
  - Server 168h full solve under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled`: 1,299,844 variables, 1,581,351 constraints and 10,733,898 nonzeros; build `90.54 s`; Gurobi `675.56 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `4.061 GiB`.
  - Server CPU is 48 physical cores / 96 logical processors. `Threads=-1` exposed all 96 logical processors; barrier factorization used 48 physical threads. Two RTX 4090 GPUs are present, but current `gurobipy 13.0.2` is the standard non-`+cu` build and therefore did not use GPU acceleration.
  - Detailed module and numerical audit: `MODEL_SYSTEM_AUDIT_20260707.md`.
- P30-cleanup and GPU validation on 2026-07-07:
  - Commit `a8cd150` removes the obsolete early block-boundary variables from `master.py`, switches conventional hydropower environmental flow to the configured `monthly_environmental_flow_2019_p30` dataset and keeps run-of-river hydropower as station-CF-weighted provincial hourly output variables.
  - Local checks: AST parse for changed Python files PASS; `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 19/19; `scripts/smoke_test_data_package.py` passed 118/118.
  - New server data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 proxy NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
  - Server readiness with the P30 roots passed, including raw-GRFR SHA256 verification; server regression tests passed 19/19 in `18.06 s`.
  - Server 24h CPU P30 gate under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu`: 375,910 variables, 278,737 constraints, 1,879,966 nonzeros; Gurobi `45.06 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.879 GiB`.
  - GPU-enabled Gurobi was installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu` from verified wheel `gurobipy-13.0.2+cu129-cp311-cp311-manylinux_2_24_x86_64.whl` (SHA256 `10f0a10fed0c0f959d11bc4f60d36d4ef04a13c48ecf649cd557e8b952de0680`; server SHA256 matched after upload).
  - GPU probe confirmed `linux64gpu[cuda12]`, `GPU model: NVIDIA GeForce RTX 4090` and `Start PDHG on GPU`.
  - The same 24h model with GPU-PDHG was interrupted after about 600 s because it was still iterating and had no `solve_report.json`; CPU barrier is therefore the accepted default for this model at this stage.
  - The P30-cleanup 744h CPU gate under `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu` completed model build in `339.56 s` with peak RSS `5.336 GiB`; model statistics are 4,762,150 variables, 6,472,914 constraints and 45,718,011 nonzeros. Gurobi optimization is still running under PID `863603`; no `solve_report.json` or `solution_qc.json` exists yet.

### Known limitations and unresolved inputs

- CSP site potential and hourly profiles are missing; CSP is disabled.
- PHS open-loop/closed-loop hydraulic pairing is unavailable. PHS is represented as province-level 8h storage with a GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on` is not implemented; fuel is charged on gross generation only.
- Hydropower type labels are assigned from the available GHT/proxy rules because source data do not provide reliable type labels for every plant; low-confidence labels are retained for now and should be validated later against external station evidence.
- Core hydropower cascade coupling, the scaled 168h solve and the corrected 744h sparse transmission gate have passed server regression, optimization and QC gates. PID `3778049` reached mathematical optimality but is preserved as a rejected transmission-formulation baseline. Current implementation covers conventional reservoir cascade operation, not open-loop or closed-loop PHS water-pair coupling.
- Core cascade environmental flow now uses a 2019 single-year monthly P30 proxy. This follows the requested P30 direction but is still not the formal 1980-2019 climatological P30; manual review of the 4 low-correlation / 18 max-bound lag edges also remains unresolved input work.
- Capacity-credit values and spur/trunk proxy costs still require parameter-source review. The Base capacity margin and inertia threshold are now reviewed at `5%` and `3.5 s` respectively; alternatives require explicit scenario overrides.
- The intraprovincial load-center network uses a 50% design-utilization assumption.
- Two western AC500 proxy edges exceed the 1000 km range of the cited source cost.
- Intraprovincial load-center transmission losses remain zero.
- Demand-flexibility calibration remains open: building thermal inertia/comfort data and province-hour EV connection availability, driving energy, accessible battery capacity and departure SOC are not yet available. The current daily envelopes must be sensitivity-tested before paper interpretation.
- Direct server access to PyPI fails TLS certificate-chain validation. The user chose to defer this issue. Do not disable TLS verification; use verified offline wheels when a new package is required.
- Temporary uploaded installers and wheel directories remain on the server; do not delete them without explicit user confirmation.

### Exact next action

1. 保留既有 744h 原目录不变；如研究协议需要处理其 manifest，只能设计目录外、名称明确、只读的 post-run audit。原目录 manifest 只有在明确批准后才可由全新根重跑取代。
2. 这项连续 RUC 行缩减已完成本地 1h/24h 闭合门禁；若用户单独授权服务器部署，先实时复核固定服务器 checkout、进程、内存和数据根，再部署精确提交，在新的、隔离的含波浪 Base 根上运行一个匹配 168h A/B。不得并发求解、不得覆盖历史根，也不得直接放大到 744h/8760h。
3. 后续 P3 优先寻找会同时改善 presolved 矩阵和 `Factor NZ/Factor Ops` 的等价结构修改；每个候选须记录 raw/presolved rows、columns、nonzeros、ordering/Barrier/crossover 时间、迭代数、目标、全部 QC 与 RSS。仅减少会被 presolve 消去的原始行不足以证明全年收益。
4. 新的付费云端 8760h 必须单独获得授权，并满足不可变代码/数据/场景 hash、新 24h/168h 门禁、高内存节点与线程/SoftMemLimit、Slurm 优雅终止规则、预计核时费用和明确停止条件；固定服务器继续禁止 8760h。
5. 科学建模的并行后续：Base 保持波浪能开启、灵活负荷关闭；以 `Power_curve_V2`/建筑热工与车辆可用性数据校准唯一的 V3-V2G 覆盖层后再做 low/base/high；先定义目标年年度成本与 2025-2060 贴现路径总成本的关系，再开展 MGA 成本松弛和点/省/全国互补性分析。

## Version history

### 2026-07-31 — 输出语义修复与 24 h/168 h Base--V5 匹配门禁

- Git/changed files: `ae3356391ec55376b041d6a356ea2d1f26be88bc`
  更新 `cispo_model/solution_export.py`、`cispo_model/result_dashboard.py`、
  `tests/test_solution_qc_semantics.py`、`tests/test_result_dashboard.py`、
  `MODEL_IO_CONTRACT.md` 与 `cispo_full_lp_model_spec.md`。修改仅涉及
  QC/展示语义：V4/V5 的旧 V1G daily-energy residual 标为不适用，
  dashboard 区分精确零和小于 0.001 GWh 的非零量；LP 与 solver 配置不变。
- Commands/verification: 本地和服务器均运行
  `python -m unittest discover -s tests -p 'test_*.py' -v`，结果
  `165/165 PASS`；服务器另运行 readiness、release、V5 input 与 hydro
  audits，全部 PASS。服务器按串行、cold、no-basis 运行当前快照中的两根
  24 h 与三根 168 h；每个有效根均为
  `OPTIMAL + PASS + 58/58 + current input + valid result manifest +
  wrapper exit 0/stderr 0`。V5/v2 的 168 h 尝试由预期 guard 在 optimize
  前拒绝，作为合同证据保留，不重标为 solver result。
- Evidence: 24 h Base/V5 solver 为 `407.321/420.232 s`；168 h
  Base-v2/Base-v3/V5-v3 为 `907.672/917.121/1024.510 s`。V5-v3 最大
  constraint/bound/dual violation 为
  `8.339e-8/2.609e-8/6.047e-8`，peak process-tree RSS `3.508 GiB`，
  swaps 0。Base-v2/v3 objective 在 `2.9e-7 million CNY` 内一致。
- Scientific audit: 168 h V5 的容量变化、firm credit、EV fleet SOC、
  PHS/储能、水电 380 GW、网络方向、可靠性、碳/CCS/BECCS 与成本闭合均
  通过。未发现凭空 V2G 能量或以 selected-horizon effective peak 直接
  降容。首周冷热未实际调度却存在全年峰窗 cooling credit，以及非零梯级
  negative-inflow clipping 水量，均已登记为截断解释/后续科学敏感性。
- Unresolved/exact next action: `stable_basis_v3` 已有匹配 2030 Base/V5
  168 h 工程证据，但 V5 `Kappa≈1.62e10`，不能据此宣称 8760 h 可解或把
  168 h 价值外推全年。保持服务器空闲；下一步由作者选择全新四年 168 h
  Base/V5 sequence 或一个明确命名的更长测试。继续禁止自动启动
  8760 h、付费云、basis/MGA、并发第二求解与 `Crossover=3`。

### 2026-07-31 — 固定、scope-aware 的结果数据与图表环节

- Git commits: `336116b493cf92eb461d1a2aab490678fd2dbac5`
  实现固定结果 dashboard；`bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`
  将 firm flexibility credit 明确标为“full-year provincial peak-window
  accreditation”，避免与截断时域全国峰值变化混读。
- Scope/changed files: 新增 `cispo_model/result_dashboard.py`、
  `scripts/build_result_dashboard.py` 与 `tests/test_result_dashboard.py`；
  更新 `cispo_model/result_summary.py`、`cispo_model/io_contract.py`、
  `scripts/run_cispo_2030_full_year.py`、`MODEL_IO_CONTRACT.md` 和
  `cispo_full_lp_model_spec.md`。自动产物为 JSON、tidy CSV 和无外部依赖
  SVG；外部重渲染支持 SVG/PNG/PDF。dashboard 在最终 solve report 与 QC
  已存在后、output catalog/result manifest 之前生成，因此自身也被严格
  checksummed。
- Model boundary: dashboard-only 提交对 LP 变量、约束、目标、输入和 solver
  参数的改动均为零。前一数值稳定化的冷热/EV 服务模式保持不变；其代数
  等价消元与唯一新增的 V1G/V2G 共享接入功率约束必须分别解释，不能笼统
  写成“全程没有约束变化”。
- Verification: 本地完整回归 `162/162 PASS`；既有 24 h V5 输出只读复演
  的成本重构通过并成功渲染三种格式。本机新求解由未修改的 8 GiB 内存门槛
  安全阻止。服务器 `336116b` 完整回归同为 `162/162 PASS`，readiness、
  release、V5 input、hydro audits 均 PASS；最终 `bdb57b2` 聚焦 dashboard
  回归 `3/3 PASS`。
- Server command/output:
  `/home/zz2/.local/envs/cispo-2030/bin/python
  scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-hours 1 --scenario-config
  config/scenarios/flex_integrated_v5_central.json --solver-config
  config/solver_profiles/barrier_16_auto_order_v2.json --output-dir
  /data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`。
  对应控制根为
  `/data/zz2/National_model/run_control/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`。
  终态为 `OPTIMAL + PASS + 58/58 + current input + valid result manifest`，
  wrapper `exit=0/stderr=0/wall=0:39.10/MaxRSS=597624 KiB/swaps=0`。
- Interpretation/unresolved: 1 h 的 `0.2003156 CNY/kWh` 是用全年 baseline
  demand 作分母的年化规划成本强度；`0.3141334 CNY/kWh` 是用所选 1 h
  baseline demand 作分母的运行成本强度。它们时域不同，不能相加，全年
  total 字段因此强制为 `null`。只有 8760 h accepted scientific run 才会
  输出可比较的 total system cost intensity；即便如此也不自动等同于文献
  中边界各异的 LCOE。
- Exact next action: 保持服务器空闲。下一次经作者选择的 Base/V5
  24 h、168 h 或更长工程门禁直接使用这一输出合同，并以图表作为固定查阅
  入口；仍需逐根严格验收 QC/manifest/wrapper，而不是以图片替代审计。
  不自动启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

### 2026-07-31 — V5 数值修复的固定服务器 1 h/24 h/168 h 严格验收

- Git/identity: 模型实现为
  `fead34334153eca32bbf7ec3651f3388038ac04b`，部署文档 tip 为
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8`；本地、origin、GitHub 与
  clean 固定服务器 checkout 已核对一致。数据根为
  `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`，
  solver 候选为
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。
- Commands/outputs: 服务器依次执行 `159/159` regression、readiness、
  release/V5/hydro validators、Base/V5 1 h、Base/V5 24 h，最后只运行
  `scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-hours 168 --scenario-config
  config/scenarios/flex_integrated_v5_central.json --solver-config
  config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。全部
  输出根隔离，无 basis、无并发第二求解。
- 168 h evidence: 输出根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  为 `OPTIMAL + PASS + 58/58 + current input + valid result manifest`。
  raw/presolved 为 `1,209,095/1,060,576/9,755,329` 与
  `737,850/751,223/7,386,987`；Barrier 232/819.54 s，
  Crossover 176.79 s，solver 1005.194 s，258,814 simplex，peak RSS
  3.511 GiB，swaps 0。Crossover 将 `Sub-optimal` interior status 改为
  `Optimal`，日志无 `Numerical trouble`，所有物理、服务、网络、安全、
  碳/CCS 与成本 QC 均通过。
- Interpretation/unresolved: 该证据接受本轮“V5 精确稀疏化 +
  `CrossoverBasis=1`”作为 168 h 诊断路径，但不接受为 8760 h production
  solver。`Kappa≈1.62e10` 与 24 h Base/V5 的共同 Barrier recovery 表明
  ROR/VRE availability 和年度会计仍有共享 conditioning debt。旧式
  `maximum_ev_v1g_daily_energy_residual_gwh` 对 V5 车群 SOC 服务模型不
  适用，需在下一代码里显式标记 N/A/替换为服务账户指标，避免误读。
- Exact next action: 先运行同身份、同 profile 的单一 2030 Base 168 h
  匹配根；同时只做共享小系数的 build/presolve 数值审计，任何稀疏化必须
  证明不改变科学可行域且同时改善 presolved/factor 证据。未闭合前不得
  启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

### 2026-07-31 — V5 长时域精确稀疏化与数值兼容门禁

- Git commit:
  `fead34334153eca32bbf7ec3651f3388038ac04b`。
- Scope/changed files: `cispo_model/flexible_load.py` 与新增
  `cispo_model/flexible_load_numerics.py` 实施零控制冷热状态的精确消元、
  稀疏控制变量和 EV 共享连接约束；`preflight.py`、runner、diagnostics、
  solver/model-structure audits 与 `solution_export.py` 增加规模、数值风险、
  硬验收和 QC 证据；新增
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`；同步更新
  V5 合同、模型规范及对应测试。
- Commands/evidence:
  `CISPO_WAVE_ROOT=...\wave_energy conda run -n RL python -m unittest discover
  -s tests -p 'test_*.py' -v` 为 `159/159 PASS`；V5 input/release audits PASS；
  `scripts/audit_model_numerics.py --hours 168 --presolve` 得到 raw
  `1,209,095/1,060,576/9,755,331` 与 presolved
  `737,850/751,222/7,386,903`（rows/vars/nonzeros），最大矩阵系数放大比
  `1.0`。全年 preflight 估计 `42,946,990` variables、
  `57,924,850` constraints、`503,133,030` nonzeros、`34.3 GiB`。
- Unresolved/next action: 当前提交尚未经过固定服务器 1 h/24 h 或 168 h
  求解验证；`CrossoverBasis=1` 尚不能标为 production。推送后只允许在
  clean/idle 固定服务器依次执行回归、readiness/release/V5/hydro、
  Base/V5 1 h、Base/V5 24 h 和单个 2030/V5 168 h。禁止把静态规模或
  truncated gates 外推为 8760 h 可解性或年度科学结果。

### 2026-07-30 — bounded test-only AC counterflow warning contract

- Implementation commit: `9b6e72a456b0dc8f0123f90b07195f94ca902c9a`.
- Scope: preserve all model equations, objective coefficients, raw directional flows and the `1e-6 GW` detector; add a bounded `TEST_ONLY_TRUNCATED_HORIZON` warning classification using seven simultaneous prevalence/power/capacity/energy/loss/system-share limits. Full-year scientific outputs remain strict-zero.
- Verification: analytic tests cover strict pass, bounded warning, every-budget failure and full-year rejection; full local discovery is `146/146 PASS`; V5 input and release audits PASS. The observed failed 2050 case is transparently reclassified as a warning with `0.011489 GWh` induced extra loss, only `4.0100e-8` of system load.
- Local execution boundary: available RAM was `7.48 GiB`, below the immutable 8 GiB runtime gate, so no local solve was forced.
- Authorized server sequence: deploy the exact pushed tip only while idle; repeat server regressions/audits and fresh 1 h/24 h Base/V5, then fresh four-year 168 h Base and V5. If all close, start one serial four-year `1008 h` V5 sequence with `barrier_16_auto_order_v2`, cold/no-basis. Keep 8760 h, paid cloud, MGA/basis, Crossover=3 and concurrent solves forbidden.

### 2026-07-30 — 168 h Base sequence stopped by material AC counterflow

- Server/model identity: clean `af390fad22dc4e3ec4636edadfb56295e4907234`; output root `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1`; data root `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`.
- Terminal state: sequence `HARD_FAIL`; 2030/2040 accepted with valid current input/result manifests, while 2050 is mathematically `OPTIMAL` but physical QC fails only `unidirectional_interprovincial_flow`; no 2050 result manifest/state and no 2060 or V5 run.
- Exact evidence: three simultaneous AC direction edge-hours on `CORRIDOR_0153` (Jilin--Heilongjiang), maximum opposing minimum `0.176374 GW`, total opposing minimum `0.381006 GWh`; the line's forward plus reverse flow equals its `1.646 GW` capacity in all three hours.
- Mechanism: the scaled 2050 net-carbon cap is binding at `-1.917808 MtCO2`; carbon scarcity is `3589.731 CNY/tCO2` and affected nodal prices are deeply negative. The current `1.004004 CNY/MWh` gross-flow term is therefore outweighed by the value of dissipating BECCS-driven surplus through directional transmission losses. This is a real formulation loophole, not solver tolerance.
- Runtime/closure: wrapper exit 1, wall `49:20.77`, MaxRSS `3,741,888 KiB`, swaps 0; server idle and memory-safe afterward; ParaCloud empty. Existing output remains immutable failure evidence.
- Exact next action: design and review a directionality treatment that does not weaken QC, hide spillage, convert the national LP to a large MILP, or materially distort ordinary transmission economics. Only after focused regression plus new 1 h/24 h and four-year 168 h Base closure may V5 or 744 h start.

### 2026-07-30 — V5 cross-platform release identity and fixed-server 24 h A/B

- Model/release commits: `4f717de` (canonical cross-platform CSV/gzip/manifest serialization) and `af390fa` (retain the inherited authoritative techno-economic manifest).
- Server identity: clean `af390fa`; data root `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`; V5 manifest SHA256 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`.
- Verification: local and server `141/141 PASS`; server readiness, V5 input, release and 380 GW hydropower audits PASS; Base/V5 24 h roots both `OPTIMAL + PASS + 57/57 + closed manifests + wrapper exit 0`.
- Finding: parsed V5 values were already identical across hosts, but pandas/Python platform serialization changed every release hash. Canonical serialization now produces identical bytes. A second pre-solve failure showed that V5 had frozen a local timestamp-only techno-economic manifest rather than inheriting the existing server authority; no parameter table differed.
- 24 h evidence: Base/V5 runtime `405.882/434.896 s`, simplex `503,365/519,659`, objective delta `-347.394 million CNY`, explicit flexibility cost `785.531 million CNY`, firm credit and generation-capacity delta `+2.891320/-2.891320 GW`. Both Barrier stages report numerical trouble before successful crossover repair.
- Interpretation/next action: truncated leading hours cannot validate annual effective-peak value because adequacy accreditation references immutable full-year provincial peak windows. Run isolated serial four-year 168 h Base then V5 under frozen `af390fa`; audit every year, state transfer, manifests, flexibility/accounting and an immediate resume before considering 744 h.

### 2026-07-30 — integrated demand flexibility V5 and paper-style supplement

- Git implementation commit: `57ad4c5`.
- Scope: keep Base unchanged; add one integrated central flexibility counterfactual with thermal-load service envelopes, paid V1G, nested endogenous paid V2G and derated peak-deliverable firm capacity credit; add evidence/source registries, deterministic input builder/validator, release contract, expanded QC/output accounting and an English supplementary-information chapter.
- Principal changed files: `cispo_model/{config,data,flexible_load,master,monolithic,solution_export}.py`, `config/scenarios/flex_integrated_v5_central.json`, V5 parameter/source registries, `scripts/{build,validate}_flexible_load_v5_inputs.py`, V5 release/audit contracts, tests, and `supplementary_materials/modules/06_integrated_demand_flexibility/*`.
- Verification: V5 input audit PASS; release audit PASS; full unittest `140/140 PASS`; English TeX has four sections, no internal scenario/config names, compiles to a visually checked 9-page PDF; 1 h current-output-contract V5 gate `OPTIMAL + PASS + 57/57 + current input + valid result manifest`; 24 h Base/V5 mathematical A/B both `OPTIMAL + PASS + 57/57 + closed manifests`.
- Material findings: the 24 h V5 gate pays all contracted/activated service costs, reduces the selected-window national peak by `2.3211 GW`, receives `2.8913 GW` bounded firm credit and reduces generation capacity by the same `2.8913 GW`; no simultaneous charge/discharge or state/reliability/accounting loophole was detected. Both Base and V5 encounter Barrier numerical trouble and require large simplex repair, so numerical efficiency remains an explicit 744 h risk.
- Unresolved: after the final output-contract-only patch, the exact commit still needs fresh 24 h A/B closure. Local 168 h was blocked before build by `6.07 GiB < 8 GiB` available RAM. Fixed-server deployment is blocked by stale non-solver audit PID `976320`; do not terminate it or switch checkout without explicit authorization.
- Exact next action: obtain at least 8 GiB local available RAM and use fresh roots for current-commit 24 h Base/V5 and serial four-year 168 h Base/V5; alternatively obtain explicit permission to clear the stale fixed-server audit wrapper, then deploy the pushed commit and repeat the same staged gates. Do not start 744 h until those gates close.

### 2026-07-30 — 诊断时域年度碳与资源流量缩放

- 实现提交：`d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244`。
- 变更范围：`cispo_model/{master,monolithic,solution_export}.py`、full-year/sensitivity runners、`scenario_catalog v4`、配置/数学说明和年度缩放/情景目录测试。
- 公式：`f=optimization_hours/8760`；窗口净碳上限、DAC throughput、生物质燃料、CO2 sink 注入均乘 `f`，DAC 电力负荷使用窗口质量除以 `f` 的年化速率；annualized capacity/fixed cost 不缩放。
- 验证证据：新增 1 h/24 h V4 V1G 根均 `OPTIMAL + PASS + 54/54 + current input + valid result manifest`，碳约束在两根中均 binding；聚焦测试通过，完整本地 `138/139 PASS`，唯一失败为已知本地 ignored technoeconomic manifest 与冻结服务器数据 hash 差异。
- 情景边界：主分析只有 `base` 和 `flexible_load_comfort_v4_v1g`；其余 implemented 文件是独立敏感性或历史回归，不会在一次 run 中自动叠加。
- 未决问题与精确下一步：先提交并推送三份交接文档；如需新的四年 744 h 验证，必须在实时核验固定服务器/ParaCloud 后用新输出根、无 basis、串行执行。旧 744 h 不可重标；8760 h、付费云、MGA、basis 与并发求解仍禁止自动启动。

### 2026-07-30 — 四年 744 h sequence 严格终态接受

- 运行身份：clean `5d31b51b350a581287fc8eb13e73216c11fc7543`，中央 V4 V1G、`barrier_16_auto_order_v2` / `Crossover=1`、cold/no-basis、每年 744 h。
- 终态：sequence `PASS`，四年全部 `ACCEPTED`；每年均 `OPTIMAL + PASS + 53/53 + current input + valid result manifest`，完整 test-only planning-state 链闭合。
- wrapper/资源：exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；终态无活动 PID、无内存压力、ParaCloud 空。
- 未决问题：V4 low/high、完整 accepted Base anchor、年度 effective-peak sensitivity、basis/MGA 与 8760 h 均未闭合。本结果始终 `TEST_ONLY_TRUNCATED_HORIZON`。
- 精确下一步：提交并双端推送本终态文档；服务器空闲时仅 fast-forward 文档 tip；停止 744 h heartbeat。不得自动启动任何求解。

### 2026-07-29 — 四年 744 h：2030 accepted，2040 Barrier

- 2030 终态：`OPTIMAL + PASS + 53/53 + current input + valid result manifest`，sequence 记录 `ACCEPTED` 并只传递显式 test-only planning state。
- 完整 scope：冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、容量充裕、碳/CCS/BECCS、成本目标均由 hard checks 通过；年度 stderr 为空。
- 2040 实时状态：Barrier iteration 107，尚无终态报告；资源与队列安全。
- 精确下一步：继续只读监控 2040，只有 runner 自身严格接受后才允许串行进入 2050。

### 2026-07-29 — 启动唯一串行四年 744 h diagnostic sequence

- 运行 Git 身份：`5d31b51b350a581287fc8eb13e73216c11fc7543`；命令、PID 与 wrapper 日志记录在 `/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`。
- 边界：2030→2060、每年 744 h、中央 V4 V1G、`barrier_16_auto_order_v2` / `Crossover=1`、cold/no-basis、严格串行。
- 初始证据：唯一进程树正常，sequence identity 为 `TEST_ONLY_TRUNCATED_HORIZON`，资源无压力，ParaCloud 为空。
- 精确下一步：PID 存在时只读监控 2030 build/Barrier/Crossover；不得启动第二求解或修改服务器 checkout。任一年退出后按 OPTIMAL、QC、53/53、input/result manifests、wrapper 与完整 accounting scope 审计。

### 2026-07-29 — 固定服务器部署与 1 h/24 h 新实现门禁

- 部署身份：`03e77ccc8d2ef3813b7cc5c0d727b068d008090d`，固定服务器 checkout clean。
- 命令/输出：权威四数据根环境下运行 release/readiness/hydro/V4 validators、完整 unittest，并依次执行中央 V4 V1G 1 h/24 h cold gates；部署证据根为 `/data/zz2/National_model/run_control/deployment_03e77cc_v1`，求解根见 current snapshot。
- 验证证据：validators 全 PASS，`135/135` tests；两根均 `OPTIMAL + PASS + 53/53 + current input + valid result manifest + hydro reconciliation audit`。
- 未决问题与下一步：再次实时核验后启动唯一串行 2030→2060 744 h；该 sequence 仍是 `TEST_ONLY_TRUNCATED_HORIZON`，任一年失败必须停止。

### 2026-07-29 — effective-peak、梯级水量调和与 8760 runner 阻断修复

- 实现提交：`cea78ae1546b19754f7859982ae82dbf66820fdc`。
- 变更范围：`cispo_model/{basis_reuse,config,hydro,io_contract,master,monolithic,preflight,run_contract,solution_export,solver_artifacts}.py`，`config/optimization_2030.json`、release/scenario contracts，full-year/sensitivity runners 与相关测试。
- 验证证据：本地 1 h/24 h matched baseline/effective gates、四年 1 h sequence、8760 h hydro input-only audit、聚焦 `58/58 PASS`、完整 `134/135`（唯一差异为本地 ignored technoeconomic manifest 与服务器权威数据包 hash）。
- 未决问题：V4 low/high、accepted full-year Base、full-year solver artifact 实际生成、MGA batch、年度 effective-peak 容量价值均未闭合；24 h 结果始终 `TEST_ONLY_TRUNCATED_HORIZON`。
- 精确下一步：推送文档 tip；实时核验并部署固定服务器；服务器权威数据根完整回归和 1 h/24 h 后，启动唯一 2030→2060 744 h V4 V1G sequence。

### v0.9.75 - 2026-07-29 - 统一候选 744 h 工程门禁终态接受

- Git/运行身份：终态审计前本地、固定服务器 bare `origin` 与 GitHub 分支 tip 均为文档提交 `5ffee8a79b090dd8493e9b38da78464f3312ec6f`；固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，唯一模型实现基线仍为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本里程碑只改 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，不切换服务器 checkout，不改模型/配置/数据，不暂存用户拥有的 supplementary 或临时文件。
- Solver/wrapper：原 wrapper/Python PID `1004972/1004975` 已退出，Gurobi 终态 `OPTIMAL`、objective `2,330,214.449430 million CNY`、runtime `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover `3,573.87 s`。wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`；stderr 无 Traceback 或错误，仅含 `/usr/bin/time` 统计。
- 严格接受证据：`solution_qc.json=PASS` 且 `52/52` hard checks 全真；`validate_input_manifest(input_manifest.csv)` 与 `validate_result_manifest(output_root)` 均返回 `(True, [])`。运行身份为 2030/744 h、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2`、`Crossover=1`、cold/no-basis，数据根和 `technoeconomic_2025_cny_v2 / 2025 constant CNY` sidecar/config snapshot 匹配。
- 模块/会计：冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 scope 全部通过硬 QC 和逐表审计；最大电力平衡残差 `1.63e-10 GW`，objective component residual `1.79e-6 million CNY`。wave 1,284 个候选已加载但装机/发电为零；常规水电 `297.8895 + 82.1105 = 380 GW`；电池/PHS 为 `66.881775/65.94 GW`；411 条 corridor 无 AC 同时双向、DC 反向为零。成本混合 annualized planning 与 744 h operation，不能解释为年度净价值。
- 资源/队列/下一步：终态刷新约 `114 GiB` available、swap `781 MiB/2.0 GiB`、实时 `si/so=0`、memory PSI=0；ParaCloud 队列为空。744 h 仅为 `TEST_ONLY_TRUNCATED_HORIZON`，不作为正式 2040 state anchor。V4 low/high、完整 accepted Base anchor、basis 工程与 MGA 仍未闭合；本次不启动固定服务器 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`，完成交接推送后暂停 heartbeat。

### v0.9.74 - 2026-07-29 - 统一候选 744 h 完成 Barrier 并进入生产 Crossover

- Git/运行身份：2026-07-29 15:25--15:33+08:00 实时复核确认本地、固定服务器 bare `origin` 与 GitHub 分支 tip 均为文档提交 `1f8cbaf9fd6ad778084ee97405beb99150fe9551`；固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，唯一模型实现仍为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本里程碑只更新三份交接文档，不切换服务器 checkout，不改模型/配置/数据，也不暂存 `supplementary_materials/**` 或 `.codex_tmp/**`。
- Phase evidence：wrapper/Python PID `1004972/1004975` 持续存在。Barrier 在 iteration `313`、solver runtime `9396.13 s` 完成，interior objective 约为 `2,330,214.46 million CNY`；随后日志明确出现 `Crossover log...`。crossover basis 加入后进入 dual push，最近 Gurobi 进度为 `922,426 DPushes remaining`、`DInf=1.9217246e-6`；15:32:53 telemetry phase 为 `simplex`、runtime `9604.40 s`、current/max solver memory `14.06/23.13 GiB`。
- Resource/queue：主机约 `101 GiB` available、swap `781 MiB/2.0 GiB`；连续 `vmstat` 实时 `si/so=0`，memory PSI avg10/60/300 均为 0。ParaCloud `squeue -u a8s001819` 为空。另有一个 12:28 起遗留的旧 release-audit SSH/bash/grep 管道，占用约 3 MiB RSS、无 Python/Gurobi 子进程；它不是第二求解，本次只读记录且未终止。
- Acceptance/next action：`solve_report.json`、`solution_qc.json`、`result_manifest.json` 仍不存在，因此这只是阶段里程碑，不是终态接受。继续只读监控 Crossover；PID 退出后必须交叉验证 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + current input/result manifests valid`、wrapper stderr/time，以及冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 `accounting_scope`。744 h 始终为 `TEST_ONLY_TRUNCATED_HORIZON`；不得启动固定服务器 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`。

### v0.9.73 - 2026-07-29 - 最终窗口 live refresh：744 h 仍在 Barrier，primal residual 未闭合

- Git/文档基线：上一轮完整交接已提交并同步为 `a92a5c7e50bf8774fe1db75ae21c4c425f80b5ed`；本条仅把其后的易变服务器状态追加到三份交接文档，不改变模型实现 `7aac739`、服务器 checkout `7c56622` 或外置数据根。
- Live evidence：2026-07-29 15:18:36+08:00，唯一 wrapper/Python PID `1004972/1004975` 已运行约 `2:31 h`，Barrier 到 iteration `280`、runtime `8746.80 s`。telemetry primal/dual infeasibility 为 `0.014279/6.29e-7`、complementarity `1.31e-9`；Gurobi log 最近的 primal residual 约 `4.6e-3--4.9e-3`。这说明求解仍在推进但 primal feasibility 尚未闭合，不能因 dual/complementarity 较小而提前接受。
- Resource/queue：solver current/max memory `13.56/23.13 GiB`，主机约 `95 GiB` available、swap `781 MiB/2.0 GiB`，`vmstat` 无新增 swap-in/out、memory PSI=0；ParaCloud 队列为空。没有启动、终止或修改任何进程/队列。
- Acceptance/next action：三个终态 JSON 仍不存在。下一窗口先实时读取 PID、最新 telemetry/log 和终态文件；若仍运行只监控，若退出则严格验证 solve/QC/input+result manifests 和模块输出。不得启动第二求解、`Crossover=3`、basis gate、固定服务器 8760 h 或付费云。

### v0.9.72 - 2026-07-29 - 对话窗口收束、技术经济实装复核与活动 744 h 边界冻结

- Git/范围：本次只读审计开始时，本地、固定服务器 bare `origin` 与 GitHub tip 同步于模型实现基线 `7aac739e03646edfed14bbf48ac77869ba66cbef`；固定服务器保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，不切换活动 checkout。仅更新 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；后续文档提交不改变模型，用户拥有的 `supplementary_materials/**` 与 `.codex_tmp/**` 不暂存。
- 口径闭合：重新验证 `technoeconomic_2025_cny_v2` 已被当前代码、服务器数据根和活动 run config 实际消费；本地迁移审计 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`，并修正历史交接中不可解析的错误完整哈希。
- 运行边界：当前服务器任务是单独的 `--planning-year 2030 --horizon one_month` V4 V1G cold gate，不是 `2030→2040→2050→2060` sequence。13:43:13+08:00 时 Barrier iteration `87`、runtime `2994.35 s`，current/max solver memory `13.56/23.13 GiB`；约 `95 GiB` available、swap `781 MiB`、`si/so=0`、memory PSI=0。终态三件套均不存在。ParaCloud 队列为空，三个历史全年度作业状态未变。
- 已闭合与未闭合：`7aac739` 是后续修改的唯一统一工程基线；代码/数据/参数身份、release contract、服务器 130 项回归、小门禁和本地四年 168 h Base/V4 sequence 已闭合。活动 744 h 终态、V4 low/high、完整 accepted Base anchor、后续 basis/MGA 仍未闭合。
- 下一窗口精确动作：先完整读取五份交接/规范文件，再实时读取固定服务器 Git、唯一 PID、`solver_telemetry.jsonl`、RAM/swap/PSI、三个终态 JSON 和 ParaCloud 队列。若仍运行，只监控；若退出，先验证 `solve_report`、全部 hard QC、当前 input/result manifests 与模块输出，再更新三份交接文档。无论状态如何，不启动第二求解、8760 h、付费云、basis gate 或 `Crossover=3`。

### v0.9.71 - 2026-07-29 - 隔离服务器数据合同闭合、130 项回归与 V4 744 h 启动

- Git/部署：统一实现 `1d04f07565c3039ed467ec4080f276bd0da90786` 之后的服务器专用闭合提交为 `a3ab9f5`、`95e1b76`、`5c749b6`、`e0b5dbd`、`7c56622`，当前本地/服务器/双远端 tip 为 `7c56622c266e673037bd6afaa70c85aa57e6cb13`。提交范围仅为模型输入合同、release contract、两个审计脚本相关测试与跨数据根测试修复；`supplementary_materials/**` 和 `.codex_tmp/**` 未暂存。
- 根因与修复：服务器先后暴露 `numpy.bool_` 无法 JSON 序列化、V4 来源 manifest 漏包、V4 五张运行表与 wave 两文件漏出标准打包合同、V3 implemented 场景本体漏包，以及三个测试写死 `repo/data`。`config/model_input_files.json` 现为 v10，42 张 required tables + 12 sidecars 完整覆盖 Base/wave/V3/V4；release contract 同时冻结新增来源和 wave/V3 SHA256。测试新增场景文件必须是部署合同子集的门禁。
- 数据/审计：最终标准归档 `transfer_bundle/model_ready_data.tar.gz` 为 68,238,922 bytes、SHA256 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`、55 个归档条目；add-only 安装到 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`。服务器审计根 `/data/zz2/National_model/outputs/release_contract_v0729_server_7c56622_v5` 中 readiness、release、hydro、V4 loader 均 PASS，完整 unittest 为 `130/130 PASS`。
- 小门禁：`2030_1h_v0729_unified_v4_v1g_server_v1` 为 `81,166 rows / 238,901 columns / 455,569 nnz`、65 Barrier、1,877 simplex、4.136 s solver、0.485 GiB peak RSS；`2030_24h_v0729_unified_v4_v1g_server_v1` 为 `241,492/353,556/1,799,247`、107 Barrier、135,724 simplex、82.272 s solver、0.819 GiB peak RSS。两根均为 `OPTIMAL + QC PASS + 52/52 hard checks + valid input/result manifests`；24 h Barrier numerical trouble 后由 `Crossover=1` 恢复最优。24 h 聚合水电为 82.1105 GW、V4 EV mobility charge deviation 为 93.91 GWh、冷热吞吐为 0、wave 最优容量为 0；这些仍是 truncated engineering evidence。
- 744 h：启动前实时核验 checkout 干净、目标根不存在、约 114 GiB available、`vmstat si/so=0`、memory PSI=0、ParaCloud 队列为空。唯一 cold 根使用 `--horizon one_month`、V4 V1G、`barrier_16_auto_order_v2`/`Crossover=1`，不使用 basis。raw/presolved 和 factor 指标为 `5,238,323/3,942,756/42,266,264`、`3,234,057/2,812,319/31,818,664`、`AA' NZ=6.236e7`、`Factor NZ=8.124e8`、`Factor Ops=5.567e12`；本条提交时仍在 Barrier。
- 未决/下一步：持续监控该唯一求解直至进程退出；仅以 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + valid current input/result manifests` 接受，并审计冷热/EV、wave、水电、储能/网络/备用/惯量/碳 CCS、成本 scope、RSS/swap/PSI。无论终态如何均不得并发替代 case、使用 `Crossover=3`、运行固定服务器 8760 h 或付费云；744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。

### v0.9.70 - 2026-07-29 - 多智能体改动统一、release contract 与干净提交复验

- Git：模型/配置/测试实现提交为 `1d04f07565c3039ed467ec4080f276bd0da90786`（`feat: unify 0729 model release candidate`）。选择性暂存 52 个模型、配置、脚本、测试和交接文件；`supplementary_materials/**`、`.codex_tmp/**` 与全部历史 outputs 均未进入提交。
- 统一内容：闭合常规水电 `297.8895 + 82.1105 = 380 GW`、重复 COMID 一次水量分配、V4 冷热/EV 数据合同、PHS 功率/能量分离 sensitivities、scenario catalog、成本 accounting scope 与完整输出/QC；新增 `release_contract_v0729.json`、release/hydro input auditors 和确定性 V4 builder。
- 修复：聚合水电 up-reserve QC 不再重复计数，down-reserve 安全表不再漏项；V4 年化 enablement 与 selected-horizon 运行成本分列；gzip `mtime=0`；M2 v1 标为历史 superseded。精确提交第一次 detached 复验还发现 M2 历史 audit 依赖受保护未跟踪 review 文件，已改为校验外部证据引用登记，避免主工作树假阳性。
- 验证：V4 连续两次完整 build+validate 六文件字节一致；release audit PASS；参数 audit `11,727 rows / 26 PASS / 0 WARN / 0 hard fail`；hydro input audit `31 provinces / 372 province-month rows / 380 GW closure`；本地四个全新 1 h Base/V4/hydro-flex/PHS-central 均 `OPTIMAL + solution_qc=PASS + current input/result manifests valid`；detached 精确提交在外置数据 junction 下 `129/129 PASS`。
- 未决/下一步：外置 `data/` 未由 Git 携带，服务器必须按 release contract 新建版本化根并逐文件核对 SHA256。实现提交尚未部署，固定服务器与 ParaCloud 的旧状态不得沿用。下一步先 push，再实时核验服务器和队列、部署新数据根、运行服务器 release/readiness/1 h/24 h 门禁；全部通过后只启动一个 2030 V4 V1G 744 h cold gate。禁止 8760 h、付费云、并发第二求解、basis reuse 和 `Crossover=3`。

### v0.9.69 - 2026-07-29 - V4/Base 四年 168 h 配对序列、机制审计与成本口径修复（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`；仍是包含水电、PHS、V4 与其他用户改动的未提交工作树，未暂存、提交、推送、部署或修改 `supplementary_materials/**`。
- Scope: 顺序运行 2030/2040/2050/2060 的 V4 V1G 与匹配 Base，每年使用上一年 diagnostic state，禁止跨年/跨情景 basis；新增只读 `scripts/audit_planning_sequence_ab.py`，并修复截断时域 `cost_components.csv` 把运行成本误标成每年值的语义风险。主要改动为 `scripts/audit_planning_sequence_ab.py`、`cispo_model/{master,monolithic,flexible_load}.py`、`tests/test_cost_accounting_metadata.py` 及四份交接/规范文档；LP 目标与约束未改。
- Evidence: 两条序列均 `PASS`，八个根均 `OPTIMAL + QC PASS + 52/52 hard checks + result/input manifests valid`，resume 后均 `RESUMED_ACCEPTED`。V4 solver 时间为 `542.60/535.68/534.58/624.49 s`，Base 为 `524.30/528.61/502.95/616.01 s`；V4 峰值 RSS `3.205--3.309 GiB`，Base `2.939--3.165 GiB`。完整回归 `127/127 PASS`，V4 输入验证 PASS。
- Mechanism audit: EV 四年均有 `657.86--2314.68 GWh` 重排并降低选定窗口全国峰值；冷热服务合同容量/吞吐为零；波浪能已加载并通过 availability QC，但装机和发电为零。全模型其他电力平衡、水电、储能、输电、备用、惯量、容量裕度、碳/CCS/BECCS/DAC 与递进状态检查均通过。
- Interpretation and bug boundary: 所有根均为 `TEST_ONLY_TRUNCATED_HORIZON`。年化规划/enablement 成本与 168 h 运行收益口径不对称，因此目标差不是年度净收益。后修复的 1 h 根证明新增 `accounting_scope` 和 `optimization_hours/result_use` 输出闭合；四年 A/B 根生成于该输出修复之前，但其 LP topology、数值解和 manifests 保持有效。
- Unresolved and exact next action: 未发现需要继续扩写模型的硬公式 bug；主要开放项是 V4 low/high 参数敏感性、冷热零采用的经济含义、波浪零采用的长时域稳健性，以及两条序列共同存在的 late-Barrier/crossover 数值恢复。下一步仅落地独立 low/high overlays 并先运行 2030/2060 168 h 配对门禁，同时只读定位近零 RHS/约束族；不得修改 `barrier_16_auto_order_v2`、使用 `Crossover=3`、启动服务器/云端/并发第二求解、744h/8760h 或 MGA。

### v0.9.68 - 2026-07-29 - PHS 功率—能量成本标定与中央情景 1 h 闭合（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`；本里程碑仍位于包含水电、V4 和其他用户改动的未提交工作树中，没有暂存、提交、推送或部署。
- Scope: 保持 Base 固定 8 h 和现行 PHS 总 CAPEX 轨迹不变，只为已实现的 `independent_power_energy_v1` 建立低/中/高 \(c_P/c_E\) 候选。8 h 能量侧占比为 30%、36.5%、45%，其中中央值由 DOE/PNNL 31.69% 与 ANU 41.35% 两组直接分项结果取中点并取整；所有配置均标记 `PROPOSED_NOT_APPLIED_COST_CALIBRATED`。
- Main changed files: `config/scenarios/phs_power_energy_separated_{low_energy_cost,central,high_energy_cost}_v1.json`；`tests/test_sensitivity_suite.py`；`cispo_full_lp_model_spec.md`；Module 05 的 `source_data/phs_cost_calibration_evidence.csv`、生成脚本、表 M05-19—21、`supplementary_methods_zh.md`、`technical_archive_zh.md`、`source_references.md`、QA 和 manifest。
- Evidence and accounting: 登记 7 条记录/7 个独立来源组，其中中国证据 3 组、直接功率—能量分项证据 2 组。CISPO 轨迹是总成本锚点；NREL 用于分项结构和场址不确定性；中国官方项目披露与 IRENA 只作总量级核验；中国站点级抽蓄研究只说明固定 8 h 的结构风险。中央 2030 \(c_P=3353.473760\) CNY/kW、\(c_E=240.948410\) CNY/kWh，低/中/高所有年份的最大 8 h 重构误差为 `4.0e-6 CNY/kW`。
- Verification: 成本标定 QA `10/10 PASS`，Module 05 formal closure `12/12 PASS`；配置加载和模板拒绝测试 PASS；完整本地 discovery `125/125 PASS`。全新 2030 中央情景 1 h 根为 `OPTIMAL + solution_qc=PASS + closed manifest`，raw 模型 238,529 variables / 80,794 constraints / 453,957 nonzeros，solver 12.074 s、峰值 RSS 0.425 GiB。该根为 `TEST_ONLY_TRUNCATED_HORIZON`，目标值和最优时长不得解释为年度经济结果。
- Unresolved: 直接分项证据仍只有两个国际独立组，中国项目披露没有可比的 power/energy component breakdown；4—48 h 时长范围、闭式/开式差异、场址成本异质性和既有机组时长仍需敏感性。当前没有 168 h、744 h 或 8,760 h 证据支持把中央候选升级为 Base。
- Exact next action: 由作者审阅 30%/36.5%/45% 包络和 `PROPOSED_NOT_APPLIED` 边界；如接受，只在另行授权后按 Base、low、central、high 的同配置长时域阶梯门禁评估成本分摊与时长选择，先本地 168 h，再决定是否需要更长门禁。不得直接覆盖 Base、复用不匹配 basis 或启动固定服务器/ParaCloud/744h/8760h。

### v0.9.67 - 2026-07-28 - PHS 功率—能量候选结构与省级聚合水电灵活性情景（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`; 本里程碑仍为未提交工作树，保留用户已有 Module 05、V4 与其他未提交内容。
- Scope: 保持 Base 科学边界不变，增加可切换的 31 省 PHS 年度能量容量结构、跨规划年 GWh cohort、参考 8 h CAPEX 闭合门禁，以及不增加小时变量的聚合常规水电月度电量预算/备用/惯量敏感性。
- Main changed files: `config/optimization_2030.json`; `config/scenarios/{hydro_aggregate_flex_v1,phs_power_energy_separated_template_v1,scenario_catalog}.json`; `cispo_model/{config,master,monolithic,planning_state,solution_export}.py`; `tests/{test_bound_tightening,test_sensitivity_suite}.py`; `cispo_full_lp_model_spec.md`; Module 05 的 `supplementary_methods_zh.md`、`technical_archive_zh.md`、`source_references.md`、生成脚本、QA 与 manifest。
- Verification: `py_compile` PASS；水电定向 `12/12 PASS`；PHS/边界定向 `3/3 PASS`；完整本地 discovery `123/123 PASS`。`outputs/2030_1h_v0728_phs_hydro_refinement_base_control_v1`、`outputs/2030_1h_v0728_hydro_aggregate_flex_v1`、`outputs/2030_24h_v0728_hydro_aggregate_flex_v1` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`。1 h 配对根均 238,498 variables，情景 constraints 为 80,763、Base 为 80,732；24 h 情景为 346,736 variables / 231,107 constraints / 1,756,839 nonzeros，月度预算最大违反 \(3.55\times10^{-15}\) GWh。
- Evidence boundary: 2026 EES 研究的约 30% 闭式抽蓄容量高估和约 360 亿元/年成本差来自站点—库盆—水头—成本联合模型，不能直接校准本省级 4–48 h 结构。当前 PHS 总 CAPEX 仅有聚合 CNY/kW 路径，生产 \(c_P/c_E\) 未确定，故模板拒绝运行；聚合水电备用系数 1 与 3 s 惯量也只是与现有站点级公式对齐的敏感性。
- Unresolved: 正式 PHS 功率/能量成本证据矩阵与中央值；聚合水电低/中灵活性系数；年度 Base 对照；原有 2019 单年 P30、混合天气—水文年、备用持续时间与同步机在线状态风险。
- Exact next action: 先对 PHS power/energy CAPEX、闭式/开式定义和时长范围做来源审查并形成 `PROPOSED_NOT_APPLIED` 候选表；获得作者批准后再激活 PHS 情景。聚合水电先做本地 168 h Base/情景对照或年度求解授权评估，不得将本轮 1 h/24 h 结果解释为科学结果。

### v0.9.66 - 2026-07-28 - 冷热/EV V4 数据支撑型闭环与 P0 修复（本地）

- Git/范围：当前工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。模型修改集中于 `cispo_model/{data,flexible_load,preflight,solution_export}.py`、两个 V4 scenario、V4 参数/来源登记、输入生成与验证脚本、测试和模型规范；保留用户现有水电改动，未修改或暂存 `supplementary_materials/**`。
- 数学与数据：修复多省周期转移错误广播、多省目标向量、禁用 V2G cost 类型、V4 charge/QC 上界等 P0；冷热采用有前置库存约束的非负连续服务状态，EV 采用既有基线的 75% 固定负荷与 25% 可调服务库存。五张逐省/小时输入由已有 load/V3 envelope 可复现生成；中心值与 low/high、来源映射和证据计数全部机器登记。V1G 为中心情景，V2G 只作敏感性；没有车辆会话数据时不声称物理车队 SOC。
- 验证/输出：输入构建与五年份 runtime-loader 审计 PASS；确定性 sidecar 连续两次 SHA256 相同（`49cefa…c3108`）；`py_compile`、V4 定向 `11/11`、完整 `123/123` 回归 PASS。完整回归所需的唯一额外修正是为既有 PHS planning-state 测试 stub 明确 `fixed_duration_v1`，不改变模型。当前身份的新 V1G 1 h/24 h 与 V2G 1 h 根分别为 `_data_supported_v3`、`_data_supported_v2`、`_v2g_data_supported_v2`，均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h raw `241,492/353,556/1,799,247`（rows/columns/nonzeros），solver `43.13 s`、端到端 `81.55 s`、峰值 RSS `0.760 GiB`。失败根 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v1` 因 export cost 类型错误保留，不得重标为成功结果。
- 未决/下一步：中心值是可直接运行的工程假设，不是已观测省级校准。作者接受当前边界后，只运行一个隔离、本地、顺序的 168 h V1G gate；论文结论前必须执行已登记的参与率、时长/保留率和成本 low/high，V2G 不替代 V1G。不得复用 Base/V3 basis、`Crossover=3`、启动 744h/8760h、固定服务器或付费云任务。
- 里程碑结束只读复核：本地仍为 `codex/cispo-2030-full-lp` / `b87b3b6a76e9b6a3683087105e3251daff22cfad` 加未提交候选；固定服务器仍是 clean `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，没有真实 CISPO/Gurobi 求解进程，约 `70.9 GiB` available RAM、swap 使用约 `19.1/21.5 GiB`；ParaCloud `squeue -u a8s001819` 为空。本轮没有远程写操作。

### v0.9.65 - 2026-07-28 - 水电空间图 V3 河网与插图版式统一（本地）

- Git/范围：工作树仍基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。本次只修改 `plot_hydro_capacity_spatial_contract.py` 的制图布局与 `generate_module_outputs.py` 的图注，并增量生成 V3 PNG/PDF、五份 V3 source-data sidecar 和 `figure_m05_02_v3_qa.json`；V2 文件未覆盖或删除，模型变量、约束、容量口径、输入数据和求解结果均未改变。
- 图形契约：图 a 与图 b 均调用同一个底图函数，固定按 R5、hyd2/R2、R1 顺序绘制相同的 5,950 条分级河网；删除按梯级组自动选择并显示 Laxiwa 等代表站名的文字循环。原先两幅地图各自覆盖右下角内容的南海小图，改为整张 figure 仅创建一次、放置于两图之间空白区的共享插图，不覆盖河网、站点、梯级线或省级聚合标记。
- 验证：两份脚本 `py_compile` 通过；V3 为 `7.2 × 6.6 in`、`450 dpi`、`3240 × 2970 px`，PNG/PDF 均存在。`figure_m05_02_v3_qa.json` 全部检查为真，记录两图河网层级同为 `R5/R2/R1`、单一共享南海插图和无站名；计数仍为 31 省、2,030 个站点记录、142 个核心节点、2,211 条核心路径河段及 5,950 条全国河网。生成器重建后 formal closure 保持 `12/12 PASS`，SHA256 manifest 为 63 个文件。
- 未决/下一步：该修改仅关闭当前图件的遮挡、冗余文字和跨面板底图不一致问题，不改变省级聚合分配、2019 单年月曲线或混合资源年份等科学风险。下一步由作者审阅 V3 的地图密度和柱图范围后决定是否定稿；不得据此重解释既有 1h/24h 门禁或启动任何远程求解。

### v0.9.64 - 2026-07-28 - 常规水电 380 GW 省级闭合与聚合运行层（本地）

- Git/范围：工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。模型改动覆盖 `cispo_model/{config,hydro,io_contract,load_center,master,monolithic,result_summary,solution_export}.py`、`config/{optimization_2030,model_input_files}.json`、`tests/test_hydro_station_model.py` 和 `cispo_full_lp_model_spec.md`；新增外置水电容量/月曲线输入以及 Module 05 重建脚本、表、图和 QA。用户拥有的 `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md` 等无关改动未覆盖。
- 容量与来源：2025 常规水电按“297.8895 GW 可识别站点 + 82.1105 GW 固定省级聚合”闭合到国家能源局 380 GW；PHS 下限 65.94 GW。GHT operating non-PHS 项目总量 302.939 GW、中国归属 302.133 GW；旧未匹配 39.869 GW 中至少 15.419 GW 为清单重叠，不直接加和。重点省份锚点、时间、是否规划值和抽蓄扣除均记录在表 M05-18；非锚点在站点/GHT 非加和下界之上按省级先验比例调整。
- 模型契约：省级聚合容量固定不扩张，逐小时出力上界为容量乘 2019 逐月代理 CF，可弃发；无站点、水头、额定流量、库容、COMID、跨期蓄水、梯级、备用、惯量、容量信用或 spur/trunk。其发电进入省级平衡，并按需求份额进入 337 负荷中心；结果、QC、NPZ 和 manifest 均显式导出。成本沿用 CISPO 对总装机计收 annualized CapEx/FOM 的口径，因此固定聚合容量的该成本是情景常数。
- 验证：`tests/test_hydro_station_model.py` 为 `12/12 PASS`；水电改动相关回归 `117/117 PASS`。完整 discovery 另有 2 项与本改动无关的 scenario catalog 字段失败，未修改用户文件。新根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`；24h raw/presolved 为 `231,076/346,736/1,754,607` 与 `129,500/260,862/1,295,832`（rows/columns/nonzeros），120 Barrier、52,592 simplex、43.188 s、0.743 GiB RSS，最大平衡残差 `1.12e-12 GW`，聚合可用量违反为 0。
- 补充材料：`reconcile_provincial_hydro_2025.py`、表 M05-16—18和容量闭合 QA记录去重与分配；`Figure_M05_02_hydropower_spatial_contract_v2.{png,pdf}` 以上排双地图分别表示 5,950 条真实分级河网/五组核心梯级与非核心既有/潜在站点/省级聚合，下排双栏表示31省当前容量和未来站点清单技术上限，图件 QA 通过。生成器重建后 Module 05 formal closure 为 `12/12 PASS`，输出 manifest 含 55 个文件。
- 未决/下一步：全国容量会计已闭合，但聚合省间分配与月曲线仍为 P1 敏感性；2019 单年 monthly P30 和混合资源年份仍为 P0。下一步是作者审阅这些边界后再决定是否提交；不得用省级聚合层声称获得了清单外电站的水库调度，也不得据此启动服务器/云端 168h、744h 或 8760h。任何未来部署须新建版本化数据根并重新执行完整输入、测试、1h/24h 和 manifest 门禁。

### v0.9.63 - 2026-07-28 - 冷热/EV V4 服务约束情景与校准拒绝门禁（本地）

- Git/范围：实现提交为 `3b3de57f41a8208b4e6bd0265270a91c77b1c8df` (`feat: add v4 flexible service contract`)。变更限于 `cispo_model/{config,data,flexible_load,io_contract,preflight,solution_export}.py`、两个 V4 scenario JSON、V4 校准契约/参数登记、输入验证脚本、配置说明和 `tests/test_flexible_load.py`；未修改 Base JSON 或 V3 JSON，未暂存 `supplementary_materials/**`。
- 数学与数据契约：`service_constrained_v4` 对冷热使用连续的 signed state、`-S_under <= S <= S_bar`、舒适债与服务签约容量；EV 仅使用一个车群 SOC，按外生连接率/可用功率限制充放电，并扣除出行能耗、满足最低出发 SOC。V1G 为主情景，V2G 仅敏感性。五张输入表、来源 manifest 和 SHA256 验证为强制条件；没有已验证输入时 loader/preflight/provenance 都拒绝继续，故 V4 不会以默认数值或代理数据伪装为已校准情景。
- 验证：`conda run -n RL python -m py_compile cispo_model/data.py cispo_model/flexible_load.py cispo_model/preflight.py cispo_model/io_contract.py cispo_model/solution_export.py scripts/validate_flexible_load_v4_inputs.py` 通过；`conda run -n RL --no-capture-output python -m unittest discover -s tests -p test_flexible_load.py -v` 为 `11/11 PASS`，包括 1 省×4 小时 Gurobi 线性门禁；设置 `CISPO_WAVE_ROOT` 后，`conda run -n RL --no-capture-output python -m unittest discover -s tests -p 'test_*.py' -v` 为 `122/122 PASS`。
- 未决/下一步：V4 的热惯性、舒适边界、连接可用率、车队电池/功率、出行/出发 SOC 以及启用/激活/补偿/退化成本仍需由有来源的四规划年输入校准。输入交付后先运行 `scripts/validate_flexible_load_v4_inputs.py`，再仅在本地顺序运行新命名的 1h、24h、168h V4 gate；不得使用 Base/V3 basis，不得启动固定服务器 744h/8760h、付费云任务或并发第二个求解。

### v0.9.62 - 2026-07-28 - M2 boundary audit Stage A and current-worktree hydro gate record

- Git implementation: `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` (`feat: add m2 boundary audit`).
- Scope/changed files: added `config/m2_model_boundary_audit_v1.json`, `config/scenario_parameter_registry.csv`, `scripts/audit_m2_model_boundary.py`, `tests/test_m2_model_boundary_audit.py`; added one scope record to `config/critical_parameter_registry.csv`; updated this handoff, `MODEL_SERVER_STATUS.md`, and `SERVER_RUNBOOK.md`. No `supplementary_materials/**` content is staged by this milestone.
- Verification: audit output `outputs/m2_model_boundary_audit_20260728_local_v3/` has 11 findings and `9 PASS, 0 OPEN, 0 hard fail`; targeted audit tests pass; parameter audit output `outputs/parameter_audit_20260728_m2_local_v2/` has `11,717` rows, `26 PASS, 0 WARN, 0 hard fail`, and four explicit open risks. The independent review was triaged rather than implemented wholesale: Base-changing suggestions, unsourced parameters, and new LP formulations remain separated from basis work.
- Hydrology evidence/status: the user's uncommitted duplicate-COMID candidate passed `117/117` regression and local 1h/24h `OPTIMAL + PASS + closed manifest` gates in `outputs/2030_{1h,24h}_v0728_m2_hydro_duplicate_comid_local_v1`. The 24h root is a candidate only: it retains the raw `231,076/345,992/1,753,119` topology, has objective delta `+12.883815481793135 million CNY`, and its Barrier stage reported numerical trouble before terminal Crossover optimality. Do not stage, deploy, or call it an accepted scientific Base until the owner separately reviews and commits the scientific change.
- Unresolved/next action: first review/commit (or revise) the duplicate-COMID implementation independently; only after that decision, use a new isolated local 168h cold Base gate if a further model gate is warranted. Continue BECCS evidence/provenance work without inserting unsourced LP parameters. No server/cloud/744h/8760h action is authorized; preserve `Crossover=1` and never reuse `Crossover=3`.

### v0.9.61 — 2026-07-28 — 固定服务器 swap 归因与清理停止条件

- Read-only evidence: `free` 显示约 `70 GiB` available RAM、swap `19.1/21 GiB`；`Cached+Buffers` 仅约 `5.6 GiB`，并非 cache 累积。`/proc` 显示活跃 `wind_power` Python 的 `VmSwap=8.18 GiB`，两组 MATLAB 为 `6.01/2.28 GiB`；`vmstat` 5 秒采样 `si/so=0`，memory/IO PSI 均为 0。
- Decision: 当前 swap 是未被访问但仍归属于活跃匿名内存的页面。不得使用 `drop_caches`（不能释放 swap）或在未获主机级授权下运行 `swapoff/swapon`（会将约 19 GiB 页面回迁并扰动活动 GPU/MATLAB 作业）。未停止、重启、修改或清理任何非 CISPO 进程；服务器继续不满足 CISPO 部署/求解门槛。

### v0.9.61 — 2026-07-28 — 重复 COMID 水量守恒修复与 Module 05 / S6 审查包

- Git/scope: 本地基线 `ed72ba08ff52025cb372fc5c16583c3e05bd38b5`；本里程碑尚未创建提交。模型改动限于 `cispo_model/{hydro,config}.py`、`config/optimization_2030.json`、`tests/test_hydro_station_model.py` 与 `cispo_full_lp_model_spec.md`；补充材料新增 `supplementary_materials/modules/05_hydropower_and_pumped_storage/**`。既有用户文档和其他模块未覆盖。
- Root cause/fix: 2,030 条站点记录中有 146 个重复 `COMID`，涉及 319 条站点记录，其中 44 个河段同时映射径流式和水库式站点；旧实现会在非梯级或混合类型映射中重复使用同一 GRFR 河段序列。新配置锁定 `static_capacity_potential_share_v1`，先扣除 2019 monthly P30 环境流，再按技术容量上限分配；逐河段份额和硬校验为 1，梯级节点改为汇总成员站分配流量。该静态规则保持 LP 线性，但候选站未建时不会动态转移份额，已登记为敏感性边界。
- Commands/evidence: focused hydro tests `10/10 PASS`；`CISPO_WAVE_ROOT` 指向当前 wave 输入后执行完整 `unittest` 为 `116/116 PASS`。隔离根 `outputs/2030_1h_v0728_hydro_comid_flow_share_base_v1` 与 `outputs/2030_24h_v0728_hydro_comid_flow_share_base_v1` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`。24 h 新根 raw/presolved 为 `231,076/345,992/1,753,119` 与 `129,500/260,190/1,295,919`，solver `41.70 s`、峰值 RSS `0.742 GiB`；相对修复前参考根，水电发电量 `380.062 → 348.553 GWh`，目标 `+0.714%`。两根均为 `TEST_ONLY_TRUNCATED_HORIZON`。
- Supplement evidence: Module 05 / S6 生成器只读当前输入和已闭合诊断根，不运行优化器；产出中文方法、15 张表、四联图及 PNG/PDF/SVG、6 份 figure-data CSV、技术档案、来源登记、图注、风险表、QA 与 SHA256 manifest。formal closure `9/9 PASS`，包括 142 节点/124 边的 Kahn 有向无环检验。
- Unresolved/next action: P0 保持为常规水电清单覆盖不足、正式多年环境流量缺失、混合气象年协方差边界；另需对 115/750 MW 分类代理、22 条非 PASS 梯级时滞、PHS 8 h/效率/省级聚合及水电备用持续时间做敏感性。先由作者审阅风险处置口径并决定是否补建多年 P30 与清单覆盖层；未经批准不恢复旧省级残差、不改变 PHS 功率语义、不部署服务器或放大到 168/744/8760 h。

### v0.9.59 — 2026-07-28 — M1 168h 四根 basis 工程门禁闭合（本地）

- Git/runtime: implementation `a5e34bf5357301c205b246b0aa2149db0dca9c3b`，documentation baseline `7b5c2d66f7826d13635a403f0da012ce4f8631fe`；Base 为 `base_2024_vre_wave_on_flex_off_v1`，profile `barrier_16_auto_order_v2`、`Crossover=1`。仅生成新的本地 outputs，未改模型代码、服务器 checkout、服务器进程、ParaCloud 队列或 `supplementary_materials/**`。
- Commands/roots: 顺序运行 `outputs/2030_168h_v0728_m1_basis_{cold_local_v1,warm_local_v1}`、`outputs/2030_168h_v0728_m1_statebridge_local_v1`，以及携带该 test-only state 的 `outputs/2040_168h_v0728_m1_basis_{cold_local_v1,warm_local_v1}`。2030/2040 cold 各自导出 `cispo_lp_basis_reuse_v2` basis；2040 warm 仅导入 2040 cold basis，未使用 `--allow-cross-year-basis`。
- Acceptance evidence: 四根均 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`。2030 cold/warm objective `2043256.6580149832`，solver `520.266/10.874 s`，warm 0 Barrier/0 simplex；2040 `2025434.603188973`，solver `489.268/14.257 s`，warm 0/0。cold/warm objective 均 zero-diff；2030 容量 zero-diff、成本/发电最大差 `1.82e-12/2.73e-12`，2040 为 `7.11e-15 GW`、`2.91e-11/4.09e-11`。raw topology 保持 `1,167,956/1,019,192/9,536,286`，CSR pattern SHA256 为 `50220850416e219fb1f3f5130c4c20cb6419cbf6b56d5d22d231491ab383f998`。
- Decision/next action: 这证明同年、同拓扑的 truncated-horizon warm restart 工程可用，不构成全年科学结果。孤立 744h basis gate 无法在没有先行同构 cold 744h 的情况下产生净端到端收益，故不申请、不运行。下一阶段保持模型边界冻结，等待实际重复同构求解或明确的、获授权的工程需求；远程动作仍须实时核验服务器和 ParaCloud，`Crossover=3` 永久拒绝。

### v0.9.60 — 2026-07-28 — M1 门禁后服务器与 ParaCloud 实时只读复核

- Git/server: 只读核验固定服务器为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；`ps` 未发现 CISPO/Gurobi，RAM available 约 `70 GiB`。无需、也没有切换 checkout、传输输入或运行回归。
- Safety decision: host swap 约 `19.1/21 GiB`，RSS 最大的无关 Python 约 `43.0 GiB`；即使 ParaCloud `squeue -u a8s001819` 为空，也不满足服务器运行门槛。未启动第二个求解、固定服务器 744h/8760h 或任何付费云任务；下一步仍为等待状态变化后重新读取，而非复用本条快照。

### v0.9.58 — 2026-07-28 — M0 分层身份与 M1 科学前置闭合（本地）

- Git implementation: `a5e34bf5357301c205b246b0aa2149db0dca9c3b` (`feat: close basis preparation m0 m1`)。范围为 `cispo_model/{run_contract,basis_reuse,config,data,master,carbon_accounting,io_contract}.py`、Base/registry/BECCS screening 配置、两份审计脚本和对应测试；`supplementary_materials/**`、固定服务器和 ParaCloud 均未写入。
- M0 contract: `run_identity.json` 现在显式保存 `scientific_case`、`solver_runtime`、`implementation_bundle`，建模后附加 `lp_topology`。basis 导入严格要求同 test-only horizon、closed source manifest、`OPTIMAL + PASS`、basis hash 和完整 raw CSR pattern；科学/实现层身份不相同只写入 `audit_layer_matches`，不作为 source basis 的结构兼容性替代，也不授予科学验收。
- M1 scope: Base 标签和混合气象 bundle 已登记；`cohort_survival_v1` 的 2030--2060 floor 以及 `fixed_floor_v1` 对照均已测试；BECCS lifecycle 是固定结果的 post-solve screening；新增的 wave/nuclear/hydro/PHS/CO2-ship/DAC 上界均有可行域不变论证。参数审计输出 `outputs/parameter_audit_20260728_m1_local_v1`：11,717 行、26 PASS、0 WARN、0 hard fail（4 项待来源研究风险保持显式）。
- Verification: M0 24h cold/warm 根为 `outputs/2030_24h_v0728_m0_identity_{cold_local_v2,warm_local_v1}`，同一 objective 且 warm 为 0 Barrier/0 simplex；M1 24h cold `outputs/2030_24h_v0728_m1_equivalence_cold_local_v1` 与 M0 zero-diff，跨 implementation-bundle 的 warm 审计根也 closed；`conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 为 `114/114 PASS`。
- Unresolved/next action: 现存 168h basis 根形成于 M0/M1 前，不能充当新分层契约的 gate。只在本地、一次一个求解地运行当前提交的 2030 cold/warm 与携带明确 2030 diagnostic state bridge 的 2040 cold/warm；四根闭合且端到端收益明确前，不申请隔离 744h basis gate。固定服务器的 swap 压力仍须在任何远程动作前实时复核；`Crossover=3` 永久拒绝。

### v0.9.57 — 2026-07-28 — 技术经济 V2 批准落库与 2025 年不变人民币生产合约

- Git implementation: `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` (`feat: normalize technoeconomic inputs to 2025 CNY`). A later handoff audit corrected the previously mistyped full hash while preserving the valid short prefix `29bbf90`.
- Scope: 将经 CISPO 原作者逻辑与多来源审查后的 V2 货币参数正式写入运行配置、数据构建器和本地外置数据包；统一 2025 constant CNY，保留审批前 candidate 快照；未改变物理参数、约束边界、目标结构或时间/空间尺度。
- Main changed files: `config/technoeconomic_price_basis_2025.json`, `config/optimization_2030.json`, `config/technology_parameters.json`, `config/fuel_prices_supplementary_table2.json`, `config/model_input_files.json`, `cispo_model/price_basis.py`, `scripts/apply_technoeconomic_price_basis_v2.py`, `scripts/build_cispo_data_package.py`, `scripts/build_natural_earth_278_network.py`, smoke/unit tests, `cispo_full_lp_model_spec.md` and Module 04.
- Production rules: domestic 2022 CNY × `1.004004` across the complete planning trajectory; nuclear/source fuel USD × `7.1429`; wave EUR × `8.1185`; CCS central values `261.04104/0.50/45`; numerical and physical exceptions explicitly registered.
- Verification: migration representative checks 9/9 PASS; idempotent second execution PASS; full local unit tests 106/106 PASS; model-ready data smoke 142/142 PASS. The earlier hydrology failure was an incorrect local `CISPO_HYDRO_ROOT` override forcing two native files into one directory; native indexed paths passed.
- Data/deployment boundary: repository `data/` is Git-ignored. Local model-ready tables and `technoeconomic_price_basis_manifest.json` are updated, while the pushed commit carries the reproducible config/builder/migration contract. No fixed-server checkout, external data root, output or cloud job was changed.
- Unresolved: fuel time trajectories, storage duration decomposition, technology-specific WACC, plant age/retirement, CCS energy penalty and offshore spatial cost remain sensitivity priorities. Exact next action is to create a new server data root, apply the migration there, and pass readiness/smoke/1h or 24h gates before any longer solve; this deployment requires a separate explicit request.

### v0.9.56 — 2026-07-28 — intra-grid/cohort 的 168h 同年 basis 四根门禁（本地闭合）

- 范围：实施提交 `282c393fd98e25737631493e19110e38bb49ed28` 的模型/配置/数据契约在本地运行四根新命名的隔离 168h Base 根；另以 2030 warm 根导出一个明确 `TEST_ONLY` diagnostic state bridge，供 2040 cold/warm 的既有容量递进状态输入。未连接、写入或部署固定服务器，未传输 cohort 数据，未修改 ParaCloud，未启动 744h、8760h 或并发第二个求解。
- 2030：`outputs/2030_168h_v0728_intra_grid_cohort_basis_cold_local_v1` 为 `OPTIMAL + QC PASS + manifest true`，raw/presolved `1,167,956/1,019,192/9,536,286` 与 `697,875/712,434/7,103,801`（rows/columns/nonzeros），180 Barrier、219,076 simplex、solver `576.593 s`、RSS `2.925 GiB`。同身份 warm 根以其 checksummed post-crossover basis 输入，solver `11.406 s`、0 Barrier/0 simplex、RSS `2.262 GiB`；objective 都为 `2,027,739.8896732337 million CNY`，容量 CSV 完全一致，发电 CSV 最大绝对差 `3.64e-11 GWh`。
- 2040：2030 state bridge 使用 `--allow-diagnostic-state-in`，不构成生产递进 state。`outputs/2040_168h_v0728_intra_grid_cohort_basis_cold_local_v1` 为 `OPTIMAL + QC PASS + manifest true`，raw/presolved `1,167,956/1,019,192/9,536,286` 与 `699,024/715,445/7,173,198`，168 Barrier、221,342 simplex、solver `543.965 s`、RSS `3.030 GiB`；2040 自身 basis 的 warm 根为 `15.517 s`、0 Barrier/0 simplex、RSS `2.263 GiB`。目标都为 `2,008,165.4183561637 million CNY`，容量完全一致、发电最大差 `2.91e-11 GWh`。未使用 `--allow-cross-year-basis`。
- 共享并网审计：四根均含 manifest/catalog 覆盖的 `intra_grid_vre_site_design.csv` 和 `intra_grid_substation_design.csv`；2025 初始 VRE trunk 均为 `1,069.512666 GW`，旧 nameplate proxy 为 `1,309.999999962 GW`。四根 result manifest 的验证错误列表皆为空。
- 决策/下一步：同年同结构 basis 工程复用具有明确收益，但不证明跨年或全年 reuse，也不授权 744h。固定服务器即时检查存在 19/21 GiB swap 使用和无关 45 GiB RSS 长任务，故部署和服务器 168h 均暂停。待主机压力解除且用户仍授权时，重新实时核验 HEAD/进程/内存/队列，add-only 安装 cohort CSV/sidecar，部署精确推送提交并完成服务器回归后，才可运行一个新的服务器 168h cold gate；不得复用 `Crossover=3` 或启动 744h/8760h/付费云任务。

### v0.9.55 — 2026-07-28 — 同格网风光共享并入与既有 VRE cohort retirement（本地闭合，未部署）

- Git/范围：起始分支/HEAD 为 `codex/cispo-2030-full-lp` / `d73eb3390c970b0da6319a03ca8b1d3c30384040`。工作树原有 `supplementary_materials/**` 与本交接文档用户改动保留；本次模型工作尚未提交。新增 `scripts/build_existing_vre_cohorts.py`、`tests/test_intra_grid_vre_design.py`，并修改 `cispo_model/config.py`、`cispo_model/data.py`、`cispo_model/io_contract.py`、`cispo_model/master.py`、`config/optimization_2030.json`、`config/model_input_files.json`、`tests/test_model_foundation.py` 及交接文档。没有连接、写入或部署固定服务器，未修改 ParaCloud，未启动 168h/744h/8760h 或第二个求解。
- 模型边界：逐格网 VRE 仍沿既有 `grid_uid -> substation -> load center` 路由；现场 spur 保留 CISPO S4-18 的 `p_spur >= max_t(cf_site,t) * capacity_site`。共享 wind/PV trunk 由原先的逐 site `max(cf)` 相加，改为 CISPO S4-19 的 `p_trunk >= sum(capacity_site) * max_t[sum(potential_site*cf_site,t)/sum(potential_site)]`，DPV 不引入此输电代理，水电仍按其原有项另加。36,686 行中 12,603 个多技术 `grid_uid` 全部映射同一 substation，零违规。完整 8760 CF 扫描为设计系数，不是 8760 LP 求解，且不增加 LP 变量或逐小时约束。
- 既有 VRE：新增受 `model_input_files.json` 和 manifest 追踪的 cohort 输入。GEM project 使用可用 `start_year`；unknown/OSM/residual 与 `start_year>2025` 容量以显式 `boundary_censored_2025_v1` 处理。2025 容量按每个 grid-technology 严格闭合，cohort 为 15,171 行、SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`；退出的 observed cohort 不再构成容量下界，但保留 site technical upper 和独立连接代理，故模型允许而不强迫同址再建。
- 验证：`CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 为 `102/102 OK`。本地 preflight `outputs/2030_24h_v0728_intra_grid_cohort_preflight_local_v1` PASS；隔离 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 为 `OPTIMAL + solution_qc=PASS + closed result_manifest`，raw/presolved `231,076/345,992/1,753,119` 与 `129,500/260,190/1,295,919`，objective `1,982,153.352438188 million CNY`，solver `34.83 s`、端到端 `58.91 s`、peak RSS `0.739 GiB`。输出新增 `intra_grid_vre_site_design.csv` 与 `intra_grid_substation_design.csv`，并被 output catalog 和 manifest 覆盖。
- 下一步：先审查并选择性提交这组非补充材料变更；若获准部署，先重新实时核验服务器 HEAD/空闲进程/内存与 ParaCloud 队列，以 add-only 方式传输 checksummed cohort 输入，fast-forward 到精确提交并完成服务器完整回归。只有上述条件满足，才在新隔离根顺序运行单一匹配 168h Base 门禁（`barrier_16_auto_order_v2`、`Crossover=1`）；不得复用已拒绝的 `Crossover=3`，不得启动 744h/8760h 或付费云任务。

### v0.9.53 — 2026-07-28 — CISPO 驱动的技术经济参数深度综合审查 v2

- Git/授权边界：沿用本轮只读核验的本地基线 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有补充材料改动全部保留。本里程碑只新增/修改 Module 04 补充材料、`supplementary-materials` skill 和本交接记录，未修改 `National_model/data`、`config`、模型方程、服务器 checkout、历史输出或求解状态。
- CISPO 原作者逻辑：逐节恢复 S3.3.4、S3.5.1—3、S3.6.2、S3.7—10 和 S6 的当前成本锚点、相对学习率来源、插值/外推、运行参数、CCS/DAC、WACC 和 1.25× CapEx 不确定性设计。关键结论是原作者对风光采用“中国绝对成本锚点 + 多来源相对下降率”，并未直接导入 NREL 的美国绝对成本。
- 深度证据：建立 15 个审查单元、63 条唯一来源、104 条参数族—来源关联；主文/SI/代码/数据按一个 `independence_group` 计数，同一机构同版报告不同格式不重复计数。每单元 6—8 个独立来源，最低为 6；`table_m04_19_source_count_qa.csv` 15/15 PASS，并报告中国证据数和最新证据年。
- 2025 CNY 口径：国内 2022 CNY 值继续乘 `1.004004`；原始外币值必须回到可复现来源币种后按 2025 FX 转换，不再对旧 CNY 折算值机械乘中国 CPI。完整来源年、币种、指数/汇率、公式和解释见 `table_m04_21_2025_price_conversion_ledger.csv`。
- v2 中央值：核电回到 Bowen/CISPO 原始 USD 路径，2030/2040/2050/2060 为 `2800/2650/2500/2350 USD/kW × 7.1429`，即 `20000.12/18928.69/17857.25/16785.82 CNY/kW`。CCS 运输和封存不再采用 An 等单篇中央值，而按中国多来源综合取 `0.50 CNY/tCO2/km` 与 `45 CNY/tCO2`，敏感性范围约 `0.18—0.80` 与 `25—116`。其余 v1 候选值在五来源以上审查后保留。
- 产物：新增 `deep_integrated_technoeconomic_review_2025cny_zh.md`、`scripts/generate_deep_integrated_review.py`、`candidate_inputs_v2/` 四张候选表、表 M04-16—23、`qa/deep_integrated_review_validation.csv` 和运行摘要。候选行数为 CapEx 76、燃料 31、派生燃料成本 1550、其他参数 166；全部为 `PROPOSED_NOT_APPLIED`。
- Skill：`supplementary-materials` 新增强制原作者逻辑恢复、每审查单元至少 5 个独立证据组、中国证据优先、source registry/evidence matrix/source-count QA、外币来源链和 v1→v2 变更表规则。Windows 默认 GBK 首次读取 UTF-8 skill 失败；设置 `PYTHONUTF8=1` 后 `quick_validate.py` 返回 `Skill is valid!`。
- 验证/下一步：生成脚本成功，8/8 QA PASS，正式标记 `FINAL_M04_DEEP_REVIEW_2025CNY_PASS`。作者下一步校对 v2 三项数值修正及波浪能参考情景边界；批准前不落库。电池功率—能量成本拆分、CCS 有效能耗、既有容量 CapEx 计费、既有机组退役队列等仍为独立 `MODEL_CODE_REVIEW_REQUIRED`，本轮未运行敏感性或优化。

### v0.9.52 — 2026-07-28 — Module 04 最终候选输入、逐参数文献审查与图件重构

- Git/授权边界：只读核验时本地分支 `codex/cispo-2030-full-lp` 的 HEAD 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有用户补充材料改动全部保留。本里程碑只修改补充材料、`supplementary-materials` skill 和本交接记录，未改 `National_model/data`、`config`、优化方程、服务器 checkout 或任何求解输出。
- 文献与来源纠正：查明 `province_fuel_prices.csv` 来自 An 等（2025）*Nature Communications* 16, 2311，DOI `10.1038/s41467-025-57559-2`，公开数据/代码 DOI `10.5281/zenodo.14836760`。煤价由 2014—2020 省级指数回归到 2023 全国水平，气价由 2018 省级门站基准加 `0.8 CNY/m3` 构造，生物质价来自其引用的 2022 出厂价研究；先前“燃料价格年未解决”结论被纠正。候选表按 2025 官方平均 `7.1429 CNY/USD` 换算文献所报 USD/GJ，但明确不是统一的 2025 现货观测。
- 中央候选值：19 技术×4 年 CapEx、绝对 O&M/启停/核燃料/DAC/CCS 捕集/输电等 2022 语境货币量按 CPI `1.004004`转为 2025 CNY；效率、时长、寿命、热耗、排放和容量边界不做价格换算。统一实际 WACC `7.4%`、4 h 电池 `RTE=90.25%`、8 h 抽蓄 `RTE=77.44%`在最新证据对照后保留。CCS 运输和封存建议采用 An 等中央值按 2025 FX 换算的 `0.185715 CNY/tCO2/km` 与 `35.7145 CNY/tCO2`，须作者批准后落库；捕集成本保留 CISPO 并按 CPI 得到 `261.041 CNY/tCO2`。
- 结构边界：电池不同时长严谨比较需要 `CAPEX=c_P K_P+c_E K_E`；当前 CCS 能耗同时通过热耗率和 5% 净出力损失实现，不能直接抄入单一文献惩罚百分比；目标函数按 CapEx×CRF 对全部在役容量计费。三项均标记 `MODEL_CODE_REVIEW_REQUIRED`，本轮未改代码。实时配置核验确认当前 Base 的 `features.wave_energy=true`；本轮建议最终论文 reference 改为 wave-disabled，把 2025 EUR/CNY 换算与强制敏感性留给独立波浪能情景，该 Base 情景改动同样须作者批准。
- 产物：新增 `final_candidate_input_review_zh.md`；`candidate_inputs/{technology_capex_by_year_2025_candidate,province_fuel_prices_2025_candidate,province_fuel_generation_cost_by_year_2025_candidate,other_parameter_values_2025_candidate}.csv`；表 M04-11—15（含候选输入 SHA256 清单）；Figure M04-03—06 及机器绘图数据；`scripts/generate_final_candidate_review.py`；`qa/final_candidate_validation.csv` 与运行摘要。原两张四面板审计图保留作历史证据，但已在图注中标记为非优先投稿图。
- 图件：新图按单一科学问题拆分为风光成本、可调度技术成本、储能外部对照和参数处置决定；每图最多 1—2 面板，不再把全部 CapEx 曲线堆在同一图。所有新图为精确 177.8 mm 宽 PDF + 450 dpi PNG，并有 `figure_data`。
- Skill：`C:\Users\ZZ\.codex\skills\supplementary-materials\SKILL.md` 新增强制技术经济审查流程，并新增 `references/techno-economic-parameter-review.md`；要求先产出精确中央候选值，再做敏感性；强制来源年/货币/换算/可比性/可靠性/授权状态；区分数据更新与模型结构问题；技术经济图默认 1—2 面板且禁止无证据区间。`python -X utf8 ...\quick_validate.py` 返回 `Skill is valid!`。
- 验证：两套生成脚本均成功；初始模块 QA 19/19 PASS，候选 QA 19/19 PASS；候选 CapEx 76 行、燃料价 31 行、派生燃料成本 1,550 行；燃料成本逐行满足价格×热耗率；4 张新 PNG 均为 3150 px 宽且 PDF 非空；完成逐图视觉检查并修复裁切、图例遮挡和无来源区间。正式标记 `FINAL_M04_CANDIDATE_INPUT_REVIEW_PASS`。
- 未决/下一步：作者先校对 `final_candidate_input_review_zh.md` 和表 M04-12/M04-14，并明确批准或拒绝三类数据更新（2025 CNY 重基准、燃料 FX/来源纠正、CCS 运输/封存替换）。只有批准后才更新生产输入和 manifest；任何电池成本拆分、CCS 能耗公式或既有容量投资计费修改都需单独模型代码审查与小样本门禁。敏感性注册已完成，但本轮未运行任何敏感性或优化。

### v0.9.51 — 2026-07-28 — Module 04 技术经济参数与 2025 年价格口径定稿

- Git 基线：本轮只读核验时本地分支 `codex/cispo-2030-full-lp` 的 HEAD 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有用户补充材料改动，均予保留。本里程碑没有提交、推送、切换服务器 checkout、启动求解或修改生产数据包。
- 范围：新增 `supplementary_materials/modules/04_thermal_nuclear_storage_technoeconomics/`。以 `cispo_model/data.py`、`master.py`、`monolithic.py`、`config/optimization_2030.json` 和当前实际输入为权威，核对 18 类有效输入、19 技术×4 年 CapEx、11 类火电/核电 RUC 与 O&M、2 类储能、31 省燃料、DAC/CCS/输电、容量上下界和寿命/WACC；并识别 partly stale 的 278 中心 sidecar 及历史审查/计划文档。
- 价格定稿：补充材料采用 2025 年不变人民币作为共同报告口径。明确或可靠归入 2022 年的货币参数以 2023/2024/2025 CPI `0.2%/0.2%/0.0%` 换算，系数 `1.004004`；生产模型值未覆盖。燃料来源价格年仍未解决，因此保留 `6.9 CNY/USD` 活动值，只以 2025 年平均 `7.1429 CNY/USD` 给出 `1.035203` 汇率对照。波浪能保留 `7.8 CNY/EUR` 说明性基线，`8.1185 CNY/EUR` 只作敏感性。
- 关键方法边界：核电 pipeline 下界与 110/205/300/300 GW 上界分列；2030 年电池下界 65.85 GW、抽蓄下界/上界 65.94/249.191 GW，最新 160 GW 抽蓄和 300 GW 新型储能只作政策比较。当前目标函数按 `CapEx × CRF × 全部在役容量` 年化，既有容量也计费；四个规划年目标不会自动折现汇总为 2025—2060 NPV。
- 产物：`technical_archive_zh.md`、`supplementary_methods_zh.md`、`supplementary_tables_zh.md`、`source_references.md`、`figure_legends_zh.md`、10 张 CSV 表、6 个绘图数据文件、`Figure_M04_01_capacity_boundaries_and_capex.{pdf,png}`、`Figure_M04_02_price_basis_and_uncertainty.{pdf,png}`、生成脚本和 QA/运行摘要。顶层 `SUPPLEMENT_WORKFLOW_GUIDE_ZH.md` 与 `SUPPLEMENT_EVIDENCE_REGISTER_ZH.md` 已同步。
- 验证：`conda run -n RL python modules\04_thermal_nuclear_storage_technoeconomics\scripts\generate_module_outputs.py` 成功；`python -m py_compile` 通过；`qa/formal_closure_validation.csv` 19/19 PASS；两张 PNG 均为 `3150×2497`，两张 PDF 均存在且非空；正式终止标记 `FINAL_M04_TECHNOECONOMIC_CLOSURE_PASS`。两张图已完成人工视觉检查。
- 未决/下一步：燃料原始美元价格的价格年和正式出处、GEM tracker 精确版本/下载日期/许可、CapEx 图表数字化误差仍需投稿前补齐；海上风电空间成本、技术特定 WACC、电池时长、既有机组寿命和 CCS/DAC 为高优先级敏感性。下一模块固定为 Module 05 水电、水文、环境流量与梯级拓扑。

### v0.9.50 — 2026-07-28 — 补充材料总控刷新与 Module 02 定稿

- Git/范围：实时本地 HEAD `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作树原有用户补充材料改动保持未提交。本里程碑只新增/修改 `supplementary_materials/**` 和本交接记录，未改模型、配置、数据包、服务器或运行结果。
- 输入与口径：直接核对 `optimization_2030.json`、`CapacityFactorStore`、`hourly_cf_index.csv`、`optimization_points.csv` 和 `03_compute_hourly_cf_from_era5V2.py`。生产口径为 2024 北京自然年、删除 2 月 29 日后 8760 h，前 8 h 读取 2023 UTC 年末；波浪能仍为独立 2023 参考年。`city_337`/642 边为生产网络，278/517 只作复现对照。
- 交付：新增 `modules/02_hourly_vre_capacity_factors/` 的技术档案、正式中文方法、来源表、6 张机器表、图注、5 份绘图数据、可复现 Python 脚本及六面板 PDF/PNG；更新 `SUPPLEMENT_WORKFLOW_GUIDE_ZH.md` 和 `SUPPLEMENT_EVIDENCE_REGISTER_ZH.md` 的剩余路线与易漂移计数。
- 命令/证据：`conda run -n RL python modules\02_hourly_vre_capacity_factors\scripts\generate_module_outputs.py` 返回 `FINAL_M02_HOURLY_VRE_CLOSURE_PASS`；正式 QA 12/12 PASS，PNG 3150×2497 px，配对 PDF 非空；人工视觉检查后修复曲线截断和色标遮挡并重跑。当前 manifest/source/QA/smoke 为 240/33/90/142 项，构建 QA 74 PASS + 16 WARN + 0 FAIL，smoke 142/142 PASS。
- 未决/下一步：Module 02 的 2024 单年结果不是长期气候均值，少量格点使用已审计回退；Module 01/03 仍有外部许可与引用缺口。补充材料下一步固定为 Module 04，需把核电 pipeline 下界与 110/205/300/300 GW 上界分列，并完成火电退役、储能和 19 类技术经济参数的来源—表格—图件—QA 闭合。

### v0.9.49 — 2026-07-28 — 2024 Base 744h 严格验收

- 终态：唯一 744h 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 在 `0dadfe9` 上以 `barrier_16_auto_order_v2` 完成。`solve_report=OPTIMAL`、`solution_qc=PASS`、Base identity 正确、49 项 hard checks 全真、result manifest 验证 `(True, [])`；进程已退出，服务器恢复空闲。
- 规模/求解：raw `4,915,427/3,711,992/40,836,493`，presolved `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros），presolve 173.12 s，ordering 114.19 s，`AA' NZ=6.388e7`，`Factor NZ=7.481e8`，`Factor Ops=4.721e12`。Barrier 211 次/7,543.19 s；crossover 5,709.46 s；simplex 1,437,196；solver 13,268.90 s；墙钟 3:47:18；峰值 RSS 20.049 GiB；无 swap。
- 科学身份：`base`、wave on、flexible load off、`national_dense_v1`、2024 Beijing natural-year VRE。最大功率平衡残差 `3.43e-12 GW`，最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。结果是 744h 工程门禁，不能解释为 8760h 科学结果。
- 解释：相对历史 wave-off/旧气象 744h，本根墙钟、RSS 和 factor ops 均较低，但模型边界与气象数据不同，不能把差异单独归因于 solver profile。crossover 占约 43% solver 时间，仍是后续 8760h 的核心工程风险。未启动固定服务器 8760h、第二个求解或付费云任务。

### v0.9.54 — 2026-07-28 — 生产运行契约闭合与 Crossover=3 744h 否决

- Git/范围：工程提交 `701b9bc225013a5009dcce3f4e97ee2063dcd00f` 已双端推送并部署。修改只涉及运行身份、原子锁、严格 resume/input 校验、solver 阶段审计和数值 profile；未改变 Base 的目标、约束、技术、时空尺度或数据来源。已有 `supplementary_materials/**` 用户改动保持未提交。
- 工程与短门禁：新增 `run_identity.json`、源码 bundle、Git/config/profile/scenario/formulation/data-root 身份，且运行根与 planning sequence 均采用原子 claim。运行中输入变化、混合身份 resume、或非 `OPTIMAL+PASS+manifest` 终态均硬失败。本地/服务器完整回归均 `98/98`；本地 1h/24h 新 Base 根均 `OPTIMAL + PASS + manifest true`。服务器仅以 add-only 方式补齐 flexible envelope 与 manifest，SHA256 已在当前快照记录。
- 168h 严格 A/B：`Crossover=3` 在完全相同矩阵、目标、QC、manifest 与 RSS 下，将 crossover 从 `190.92 s` 降至 `117.67 s`，总 solver 从 `649.17 s` 降至 `594.63 s`；`CrossoverBasis=0` 为 `661.25 s`，淘汰。比较文件为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_168h.{json,csv}`。
- 744h 放大反例：唯一新根 `2030_744h_v0728_2024_dense_dualred_crossover3_v1` 与接受的 Crossover=1 根 raw/presolved、`AA' NZ=6.388e7`、`Factor NZ=7.481e8`、`Factor Ops=4.721e12` 和 211 次 Barrier 完全一致。候选完成 Barrier (`6,981.07 s`) 和两类 push (`PPush=1,191.93 s`、`DPush=1,214.00 s`)，但 primal cleanup 发生极端 infeasibility 循环；在 `10,930.99 s` 时优雅中断，终态 `INTERRUPTED`、无解、无 QC、无 manifest，simplex `1,724,960`，peak RSS `19.828 GiB`。因此不能用中断时的较低累计时间声称更快，`Crossover=3` 明确不进入生产候选。
- 决策/下一步：继续以 `barrier_16_auto_order_v2` / `Crossover=1` 作为唯一接受的 744h profile；保留中断根和 `solver_ab_v0728_crossover_744h.{json,csv}` 作为负面工程证据，绝不重写为科学结果。未来候选先完成匹配 24h/168h 的最终门禁，再由唯一胜者运行一个新 744h 根；固定服务器 8760h、新付费云任务和 MGA solve 均未启动且仍需相应授权。

### v0.9.48 — 2026-07-28 — 单一 2024 Base 744h 已启动

- Git/运行身份：168h 证据提交 `0dadfe9` 已双端推送并部署。服务器在无其他求解、约 70 GiB 可用内存时，于 `03:12:23+08:00` 启动唯一根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2`；命令显式使用 `--diagnostic-hours 744` 与 `barrier_16_auto_order_v2`，未使用省级碳分层。
- 当前状态：PID `2708836`/Python child `2708837` 正常存在，尚处于模型构建且没有 Gurobi 日志。此条仅记录启动，不是求解验收。终态必须同时满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。
- 安全边界：保持单一求解；不改变运行 checkout，不启动固定服务器 8760h、第二个 744h 或付费云任务。结束后再记录 raw/presolved/factor/Barrier/crossover/RSS 与 manifest 终态。

### v0.9.47 — 2026-07-28 — 固定服务器 2024 数据与 168h Phase A/B

- Git/部署：`9a3c5e8` 已同时推送 `origin`/`github` 并部署到空闲固定服务器；部署前实际服务器 HEAD 为 `78a605d`，不是旧快照中的 `4e1999d`。服务器完整回归 `89/89`。
- 数据：以新增归档传输四个 2024 CF Zarr，本地/服务器 SHA256 均为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`；四目录文件数 3,489/465/3,489/3,825，与本地一致。目标目录原先不存在，未覆盖 2023 stores，归档未删除。
- 168h A/B：三个隔离根均 `OPTIMAL + PASS + manifest true`。0/1 参数 700.50 s；dense 1/0 参数 668.05 s，`AA' NZ`/`Factor NZ` 更低但 crossover 从 72.76 s 增至 190.62 s。省级碳会计与 dense 1/0 的 presolved/factor/迭代/work units/目标完全一致，证明该 raw 稀疏化已由 Gurobi presolve 自动完成，不选为默认。
- 决策/下一步：保留 Base 默认 0/1，不修改科学边界；本轮 744h 工程候选显式使用 dense + `barrier_16_auto_order_v2`，因为 168h 总时间、AA' NZ 与 Factor NZ 占优，同时以 crossover 放大作为停止/复核风险。再次核验空闲和内存后只启动一个新 744h 根；固定服务器 8760h 与付费云任务继续禁止。

### v0.9.46 — 2026-07-28 — 2024 VRE 自然年契约与本地 Phase A/B

- Git/范围：模型实施提交 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`；本条文档闭合提交待生成。本里程碑仅在本地完成，固定服务器 checkout 仍为 `4e1999d`。修改 `cispo_model/{config,data,diagnostics,io_contract,master,monolithic,wave_energy}.py`、runner、主配置、参数注册表、新 solver/formulation profiles 与聚焦测试；未暂存或修改本任务范围外的 `supplementary_materials/**`。
- 数据契约：风电/光伏使用严格的北京时间 2024 自然年，拼接 2023 UTC 尾部与 2024 UTC 主体并删除北京时间闰日；wave 使用独立的 2023 reference coordinate。provenance 同时哈希两年 VRE stores 及可选 formulation profile。
- 本地验证：完整 discovery `89/89`；两个新 1h 和六个新 24h 根均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。机器可读比较为 `outputs/solver_ab_v0728_2024_24h.{json,csv}`。
- 结论：省级碳会计在代数、目标和 QC 上等价，但 Gurobi presolve 重建出与全国式相同的矩阵，故保留为实验 formulation 而不选为默认。开启 dual reductions 虽降低 factor 结构，却因 crossover 增长在 24h 变慢；`PreDual=1` 和 `PreSparsify=2` 已在短门禁淘汰。未启动 744h、8760h 或付费云任务。
- 下一步：推送两个远端；再次复核服务器空闲后追加并校验四个 2024 CF stores，部署精确推送提交，运行服务器完整回归和顺序匹配 168h A/B。只有唯一胜者通过全部阶段/RSS/QC/manifest 门禁后，才启动一个新命名的 744h 根；固定服务器 8760h 继续禁止。

### v0.9.45 — 2026-07-28 — 受限 Base MGA 契约及双端回归门禁

- Git/模型范围：实施提交 `4e1999d`（`cispo_model/mga.py`、`scripts/run_cispo_2030_full_year.py`、`cispo_model/solution_export.py`、`cispo_model/result_summary.py`、`cispo_model/master.py`、`cispo_model/io_contract.py`、`config/mga/base_min_onwind_new_national_epsilon_1pct.json` 与 `tests/test_mga.py`）。MGA 不改写 Base 最小成本模型：先按闭合年度 Base manifest、`OPTIMAL+PASS`、`SCIENTIFIC_PRODUCTION`、`BASE_MINIMUM_COST`、相同年度/边界/已解析配置及 required-input SHA256 验证基线，再添加 `Base_cost <= Base_cost* (1+epsilon)`，最后才设置一个显式二级容量目标。
- 输出/QC：MGA 根记录 `mga_request.json`、`mga_run.json`、基线 manifest SHA256、成本松弛、选择器、候选资产哈希、主成本和二级目标。`solution_qc.json` 按原成本表达式而非求解器的 GW 二级目标检查 cost-component closure，并新增成本上限 hard check；`run_summary.json`/`solve_report.json` 分别保留主成本和二级目标。MGA 输出不导出 `planning_state`，也不能成为后续 MGA 基线。
- 支持范围：当前仅接受 `base` 年度基线；二级目标可按全国、省或显式点位选择 `vre_new_capacity_gw`（onwind/offwind/pv）、`wave_new_capacity_gw`、`hydro_new_capacity_gw` 或 `storage_new_power_gw`，方向为最小化或最大化。示例 JSON 是在 1% 松弛内最小化全国新增 onwind；它不是已授权的 MGA 求解。
- 验证/部署：MGA 的小 LP 成本上限测试、闭合基线接受测试、截断基线拒绝测试均通过。本地及固定服务器完整回归均为 `82/82`。在固定服务器空闲、checkout 干净、约 70 GiB 可用内存时，已由 `56d166d` fast-forward 至 `4e1999d`；新根 `/data/zz2/National_model/outputs/2030_1h_v0728_server_mga_runner_base` 为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，波浪开启、灵活负荷关闭、`analysis_mode=BASE_MINIMUM_COST`。本地同类根为 `outputs/2030_1h_v0728_local_mga_runner_base`。两者都只是截断工程门禁。
- 未决/下一步：当前没有已验收的 2030 Base 8760h，因此不得运行 MGA 或把 1h/24h/168h 诊断根作为其基线。后续先在已授权的全年度 Base 后进行 MGA preflight（不求解）以核验全部身份和成本松弛，再为每个独立的二级目标建立新根和完整 QC；不得启动固定服务器 8760h 或新付费云端任务。

### v0.9.44 — 2026-07-28 — 固定服务器当前 Base 门禁、阶段审计与受限 LP basis 复用

- Git/模型范围：已提交并推送 `56d166d`（`cispo_model/basis_reuse.py`、`cispo_model/diagnostics.py`、`cispo_model/io_contract.py`、`cispo_model/solver_audit.py`、`scripts/run_cispo_2030_full_year.py` 及聚焦测试）。本轮未改变 Base 代数、输入数据契约、情景边界、目标函数或约束；唯一新增的数学模型输出均在隔离的新 test-only 根目录。
- 部署/环境：fast-forward 前已实时复核服务器 checkout、进程和内存。服务器在无活动 CISPO 进程时由 `01ec6f9` fast-forward 至 `56d166d`。新增的 wave-ready 数据根和 wave 数据根均为附加目录，未覆盖或删除既有根、输出或临时文件。仅以本地 wheel 和 `--no-deps` 补齐缺失的 `xarray==2025.1.2`，随后通过 NetCDF smoke test。
- 验证：本地及服务器完整 `unittest discover` 均为 `78/78` 通过。服务器新建的 Base 1h、24h、168h 根均闭合科学 result manifest 并通过 QC。阶段比较 JSON/CSV 记录 raw/presolved 维度、ordering、factor 结构、Barrier、crossover、总运行时间和 RSS；不将全局 presolve 缩减归因于任一源约束族。
- Basis 证据：新的 test-only `.bas` 导出/导入契约会对源 basis 和带名称的 LP 结构哈希。2030 同年及 2030→2040 跨年 1h A/B 都复现了冷启动目标和 QC，并消除了 Barrier；但端到端墙钟仍须完整重建模型和导出结果。全年自动 basis 导出/导入仍受显式 `50m` 非零元带名称身份安全上限及科学运行保护所阻止。
- 未决/下一步：不得由 168h 推断 8760h 可行性。仅在获得已验收的 Base 科学结果后，以独立 runner 实现 MGA，并保留显式成本上限和基线身份。保持历史 744h 根完全不变；未授权固定服务器 8760h 或新的付费云端运行。

### v0.9.43 - 2026-07-27 - raw LP constraint-family sparsity audit

- Implementation commit: `6114157` (`feat: audit raw LP constraint sparsity`). Changed `cispo_model/model_structure_audit.py`, `cispo_model/io_contract.py`, `cispo_model/solver_audit.py`, `scripts/run_cispo_2030_full_year.py`, `tests/test_model_structure_audit.py`, `tests/test_solver_audit.py` and `cispo_full_lp_model_spec.md`. The feature is diagnostic only: it neither adds/removes mathematical variables or constraints nor changes objective, scenario, input data, temporal/spatial boundary or solver numerics.
- Contract: `--constraint-family-audit` explicitly materializes only the raw Gurobi sparse matrix after `model.update()` and hard-fails above the configured 50,000,000-nonzero safety limit. Its JSON records raw family totals, exact densest rows/columns and global log phases after solve; it is catalogued and hashed. Presolve family attribution is deliberately recorded as unavailable because Gurobi does not publish a stable source mapping.
- Verification: targeted audit tests and the full local discovery suite pass `75/75` with `CISPO_WAVE_ROOT` set. Fresh isolated Base roots `outputs/2030_1h_v0727_constraint_family_audit_base_v3` and `outputs/2030_24h_v0727_constraint_family_audit_base_v3` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; wave is enabled, flexibility is disabled and every hard check is true. The 24h root has raw `231,074/345,992/1,729,035`, presolved `129,335/260,116/1,269,506` (rows/columns/nonzeros), 0.73 s presolve, 0.41 s ordering, `AA' NZ=2.200e6`, `Factor NZ=6.284e6`, `Factor Ops=7.399e8`, 89 Barrier, 57,741 simplex/crossover, 29.107 s solver runtime and 0.712 GiB peak RSS.
- Finding/next action: `annual_emissions_accounting` (6,697 raw coefficients), the two largest provincial capacity-margin rows (6,491/5,736) and the 31 `co2_source_balance_p*` rows (3,246 each) are the first dense-row candidates. These are binding scientific/accounting structures, not proven redundancy; do not remove them. First prepare an algebraic equivalence proof for a province-disaggregated annual-emissions accounting form and test one new 24h Base A/B before any 168h/744h decision. No server/cloud checkout, process, queue, historical output or `supplementary_materials/**` file was changed.

### v0.9.42 - 2026-07-27 - isolated cascade nodes use the equivalent independent balance

- Implementation commit: `9787ba7` (`Optimize isolated cascade node construction`). Changed `cispo_model/hydro.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `tests/test_hydro_station_model.py` and `cispo_full_lp_model_spec.md`; no source topology, hydrology input, station, objective, capacity, spill, storage or scientific scenario file was changed.
- Scope/equivalence: source topology remains 142 nodes/124 edges. The 8 nodes with no incident edge and exactly one station are excluded only from per-hour core-cascade assembly and receive the existing independent S4-17 vectorized balance. Their core equation has an empty upstream term and a local GRFR inflow identical to the independent form, so the effective core station rows change 146→138 while all 124 topology edges remain. The new guard rejects any multi-station isolated node, preventing a future data refresh from silently changing hydraulic aggregation.
- Validation: targeted hydrology tests pass 8/8; full local discovery passes 71/71 with `CISPO_WAVE_ROOT` set. Fresh Base roots `outputs/2030_1h_v0727_cascade_isolated_nodes_independent_base` and `outputs/2030_24h_v0727_cascade_isolated_nodes_independent_base` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; all hard checks pass, wave is enabled and flexibility is disabled. The 24h objective differs from the paired RUC-thinned reference by `9.78e-09 million CNY`, with identical raw/presolved dimensions. LP degeneracy changes some equivalent dispatch/basis values, so solver path differences are not evidence of a model-boundary change.
- Solvability finding/preservation: 24h `Factor NZ`/`Factor Ops` move from `6.111e6/6.039e8` to `6.284e6/7.399e8`; runtime is 34.636 versus 33.766 s and peak RSS remains 0.724 GiB. This avoids 8×hours Python scalar cascade-row constructions but does not improve the presolved structure, so do not promote it as a Barrier or 8760h optimization. Existing outputs, user-owned `supplementary_materials/**`, fixed-server checkout/outputs and ParaCloud state remain untouched. Exact next action is to seek another mathematically safe, presolve-relevant thinning target locally; no server/cloud run follows from this change.

### v0.9.41 - 2026-07-27 - exact continuous-RUC row reduction

- Implementation commit: `3f2255a` (`Optimize redundant continuous RUC bounds`); this is local only and has not changed the fixed-server or ParaCloud checkout.
- Changed `cispo_model/monolithic.py`, `cispo_model/preflight.py`, `tests/test_ruc_redundancy.py` and `cispo_full_lp_model_spec.md`. It removes only the four generic continuous-RUC upper-bound row families proven by S4-24/S4-25/S4-29 and the nonnegative variable bounds. A build-time domain guard rejects missing RUC parameters, `min_up_h<1`, `min_down_h<1` or `pmin_fraction>pmax_fraction`.
- Validation: the targeted proof/regression tests pass 3/3 and the full local discovery suite passes 69/69 with `CISPO_WAVE_ROOT` set. Fresh Base roots `outputs/2030_1h_v0727_ruc_dominated_bounds_removed_base` and `outputs/2030_24h_v0727_ruc_dominated_bounds_removed_base` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; wave is enabled and flexibility is disabled. Objectives match the paired wave-integrated Base reference within floating-point tolerance, all hard checks pass and manifests close.
- 24h raw rows/nonzeros fall by exactly 32,736/65,472 (12.41%/3.65%) with no variable change. Presolved matrix, factor structure and iterations are identical, so retain this as safe construction/matrix thinning—not as evidence of a Barrier-factorization speedup. The revised static 8760h estimate is 41,186,792 variables/55,928,636 constraints/497,144,388 nonzeros/33.40 GiB and remains non-evidence for an 8760h solve.
- Existing outputs and user-owned `supplementary_materials/**` remain untouched. No server/cloud process, checkout, queue, output root, 744h run or 8760h run was changed. Next action is a separately authorized, fresh 168h A/B only after live server readiness revalidation.

### v0.9.40 - 2026-07-27 - wave-integrated Base and single flexibility overlay

- Git/scenario scope: `c992550` (`refactor: make wave energy part of base`) makes wave energy a normal Base technology and retains exactly two runnable JSON identities: `base` and `flexible_load_comfort_v3_v2g_5pct`. The latter is the sole permitted future flexibility path and inherits the wave-integrated Base. Eight earlier experimental scenario JSONs and planned-suite metadata are removed. Historical outputs, implementations and Git history are deliberately not deleted; they cannot be relabelled as results of the redefined Base.
- Scientific boundary: Base now means wind (including offshore wind), PV and correctly routed existing-grid wave potential, with flexibility disabled. The overlay adds only V3 comfort-envelope heating/cooling, causal V1G and 5% V2G; it retains its calibration-sensitive evidence status. Both runnable cases require `CISPO_WAVE_ROOT`; wave is no longer an optional Base-off switch. This is a stated Base-boundary change, not a solver-only optimization, so earlier wave-off Base gates remain historical engineering evidence only.
- Verification: with the wave data root set, `conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` passed `66/66`. New 1h and 24h roots for both identities are `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`; every hard check is true. 24h Base: raw `345,992/263,810/1,794,507`, presolved `129,335/260,116/1,269,506`, `AA' NZ=2.200e6`, `Factor NZ=6.111e6`, `Factor Ops=6.039e8`, 95 Barrier, 67,614 simplex/crossover, 34.074 s, 0.735 GiB peak RSS. 24h overlay: `354,920/268,398/1,844,355`, `132,254/266,492/1,299,953`, `2.221e6`, `6.179e6`, `5.905e8`, 101, 56,990, 33.984 s, 0.731 GiB. These roots are explicitly truncated tests.
- Full-year preflight/preservation: Base estimates `41,186,792` variables, `67,877,276` constraints, `532,990,308` nonzeros and 36.47 GiB; the overlay estimates `44,445,512`, `69,551,896`, `538,014,168` and 37.63 GiB. Local available memory is below the 96 GiB gate, so no build/solve followed. No server/cloud checkout, process, queue, old output or 744h evidence was modified; no 8760h or paid cloud task was launched.
- Exact next action: retain only these two identities in future gates. Before any authorized server deployment, re-check live server checkout/process/memory and run at most one new, separately named 168h root; do not reuse old wave-off Base roots as an A/B baseline for this new Base.

### v0.9.39 - 2026-07-27 - 本地全模块联合敏感性门禁与求解结构审计

- Git commit: `31dc265` (`feat: add combined flexibility and wave sensitivity`)。新增 `config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct.json` 并登记 catalog；仅扩展独立情景和契约测试，未改动 Base JSON、LP 目标函数、约束、空间/时间尺度或既有模块接口。情景同时使用 medium 波浪能、`comfort_envelope_v3` 冷热、V1G 和日内因果 5% V2G；参数状态仍为敏感性，不能提升为 Base 或论文基准。
- Verification: `conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 通过 `67/67`。新建本地 1h、24h、168h 根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，且 scenario identity、冷热/V1G/V2G/wave 开关和所有 hard checks 已单独复核。168h raw/presolved 矩阵为 `1,081,688/1,429,226/10,293,428` 与 `751,365/865,314/7,363,654`，`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`，180 Barrier、239,930 crossover/simplex、602.265 s 和 3.296 GiB 峰值 RSS。科学 manifest 为零失败。
- Solvability evidence: 全年 preflight 静态估计为 44,445,512 variables、69,551,896 constraints、538,014,168 nonzeros 和 37.63 GiB；相对于 Base 的增量为 +3,533,185 variables、+1,947,832 constraints、+17,091,336 nonzeros、+1.63 GiB。它只描述构建规模，不能替代 Barrier factor/workspace 证据，也不授权 8760h。168h 仅 V1G 激活；冷热/V2G/wave 为零不是技术无效结论，因为该根是 `TEST_ONLY_TRUNCATED_HORIZON` 且混合全年化容量成本与截断运行项。
- Preservation/next action: 未写入既有 744h 输出，未改变固定服务器或 ParaCloud 的 checkout、进程、队列或任务；未启动服务器 8760h 或新付费云任务。详细指标、阻碍及下一步见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。如需量化模块的 168h 因果增量，先在同机/同线程/同 profile 下做单一匹配 Base A/B，完整记录 raw/presolved/factor/phase/RSS/QC 后再决定是否评估更长根。

### v0.9.38 - 2026-07-27 - fixed-server Base 168h manifest closure gate passed

- Git/deployment: P0 implementation is `7499062` (`fix: exclude generic wrapper logs from result manifest`); reviewed branch was pushed and the idle fixed-server checkout was fast-forwarded cleanly to `67482ab`. Only `cispo_model/io_contract.py`, `tests/test_result_manifest.py` and handoff documents are in scope; `supplementary_materials/**` user changes remain untouched and uncommitted.
- Command/output: after exporting the three versioned data roots, the server complete discovery suite passed `67` tests (`2` optional xarray tests skipped). The one-at-a-time command used `scripts/run_cispo_2030_full_year.py --diagnostic-hours 168 --solver-config config/solver_profiles/barrier_16_auto_order_v1.json --output-dir /data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`, with generic `stdout.log`/`stderr.log` redirection and `/usr/bin/time -v`.
- Acceptance evidence: `solve_report.json` is `OPTIMAL`, `solution_qc.json` is `PASS`, `scenario_id=base`, flexibility/wave are false, every hard check is true and `validate_result_manifest()` returns `(True, [])`. The scientific manifest excludes exactly `run.pid`, `stderr.log` and `stdout.log`; their completed sizes may therefore change after finalize without affecting the scientific hash contract. The root is `TEST_ONLY_TRUNCATED_HORIZON`, not a 8760h planning result.
- Scale/performance: raw 1,393,915 rows / 1,011,079 columns / 9,797,949 nonzeros; presolved 729,559 / 817,723 / 7,001,232; presolve 22.89 s; ordering 26.08 s; `AA' NZ=2.131e7`, `Factor NZ=1.036e8`, `Factor Ops=8.436e10`. The solve used 161 Barrier and 226,659 simplex/crossover iterations, 614.894 s solver runtime, objective `2,028,598.8440447072 million CNY`, 3.453 GiB process-tree peak RSS and 12:24.94 wall clock. This is a revalidation of the same Base engineering boundary, not an A/B speed claim against a different scientific case.
- Preservation/next action: existing 744h output was neither modified nor re-manifested; no fixed-server 8760h and no cloud job was started. First design a clearly named, directory-external, read-only post-run audit if P2 needs it. For P3, require matched 24h/168h A/B records of raw/presolved matrix, factor structure, phase times, iterations, objective/QC equivalence and RSS before considering any replacement 744h run.

### v0.9.37 - 2026-07-27 - manifest runtime 日志契约闭合；本地 Base 短门禁通过

- Git 实施：`7499062`（`fix: exclude generic wrapper logs from result manifest`）。仅修改 `cispo_model/io_contract.py` 与 `tests/test_result_manifest.py`；未暂存或提交 `supplementary_materials/**`。
- 契约修正：`stdout.log`、`stderr.log` 与 `runner_stdout.log`、`runner_stderr.log`、`sequence_stdout.log`、`sequence_stderr.log`、`run.stdout`、`run.stderr`、`run.time` 和 PID 文件同属 runtime-managed artifacts。它们从科学目录和 SHA256 result manifest 中排除；`gurobi.log` 继续作为带哈希的科学诊断文件。
- 回归证据：修订后的 manifest 测试先 finalize、再向通用 stdout/stderr 追加，随后通过 `validate_result_manifest()`。聚焦 manifest/I-O 测试通过；`conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 在 17.821 s 内通过 `67/67`。直接以模块路径调用 unittest 的失败仅因 `tests/` 不是 Python package；discovery 是认可的调用方式。
- 新本地 Base 诊断：`outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均为新根，均有 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base`、灵活负荷/波浪能关闭且 result manifest 零失败。24h 为 342,343 个变量、262,201 条约束、1,771,702 个非零元、41.296 s 求解时间和 0.725 GiB 进程树峰值 RSS；它们仅是截断工程门禁。
- 保全/下一步：已完成的固定服务器 744h 根未被写入、重建或重做 manifest；未改变服务器/云端 checkout、进程、调度任务或付费运行。推送审查后的提交后，再次实时核验固定服务器空闲状态、checkout 与内存，才单独决定是否部署并运行新的 168h Base 门禁。固定服务器 8760h 仍禁止；新云端 8760h 仍须单独授权。

### v0.9.36 - 2026-07-27 - 对话收束、实时状态复核与下一阶段目标冻结

- 实时状态：本地分支起始 HEAD `3664177`；固定服务器 checkout 干净停留在 `c879c99`，无 CISPO/Gurobi 进程，约 69 GiB 可用内存。ParaCloud `squeue -u a8s001819` 为空；`sacct` 复核 `4003088=COMPLETED`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`。
- 核验命令：本地执行 `git status --short`、`git branch --show-current`、`git rev-parse --short HEAD`；固定服务器只读执行 `ps -eo pid,comm,args`、`free -h`、`git -C /data/zz2/National_model/repo status/branch/rev-parse` 及终态 JSON/log 列表；ParaCloud 只读执行 `squeue -u a8s001819` 与 `sacct -j 4003088,4003172,4004585`。
- 本轮结论：`city_337` Base 744h 工程门禁已经证明当前连续 LP 能在固定服务器完成构建、presolve、Barrier、crossover 并满足全部物理/数值 QC；但它是 `TEST_ONLY_TRUNCATED_HORIZON`，且原 `result_manifest.json` 因 wrapper `stdout.log` 在 finalize 后继续写入而未闭合，因此不是 8760h 科学结果或严格可复现 acceptance。
- 对话累计工作：完成 337 市级负荷中心及省内年度网络、2025 初始化、风光水接入路由、5%容量裕度/3.5 s惯量、BECCS 显式碳质量守恒、Base/V1/V2G/V3 模块边界、逐年状态传递与 resume、开放式输入输出/QC/manifest、云端数据/WLS/24h/168h门禁、两次 8760h 失败诊断，以及固定服务器求解器/显式弃水/744h优化。
- 本次变更文件仅为 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；`supplementary_materials/**` 用户改动和 `.codex_tmp/` 均保持未修改、未暂存。
- 约束边界：Base 默认不启用灵活负荷和波浪能；不把 744h 目标值解释为年度/路径成本；不把 build-only、静态内存或 Barrier 中间迭代解释为求解成功；不触碰或提交 `supplementary_materials/**` 用户改动。
- 下一阶段：先闭合 manifest 契约和短门禁，再做匹配 A/B 的稀疏结构及 Barrier/Crossover 优化；随后决定744h证据闭合方式。只有通过门禁、资源/费用方案审查并取得显式授权后，才可再次尝试单年 2030/8760h。灵活负荷校准、贴现路径成本账本和 MGA 在 accepted Base 科学结果基础上分别推进。

### v0.9.35 - 2026-07-27 - 744h optimal/QC pass; strict manifest gate rejected

- Terminal solve: fixed-server checkout remained clean at `c879c99`; the sole 744h process exited normally with Gurobi `OPTIMAL`, objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations and 1,451,182 simplex iterations.
- Runtime evidence: `/usr/bin/time` records 3:52:03 wall time, 24,244,196 KiB maximum RSS, 1,086% average CPU, zero swaps and exit status 0. The internal process-tree monitor records 23.121 GiB peak RSS.
- Scientific QC: `solution_qc=PASS` and every hard check is true. Maximum constraint/bound/dual violations are `9.2955e-8/5.4955e-8/9.2151e-8`; maximum power-balance residual is `2.3961e-10 GW`; reservoir transition residual is `1.8798e-5 m3`; AC bidirectional edge-hours and DC reverse flow are zero. `solve_report.scenario_id=base`, `scenario_manifest.scenario.id=base`, and optional flexibility/wave are disabled.
- Manifest audit: 58 entries were checked and every item except `stdout.log` matches. The manifest records 63,631 bytes, while the completed wrapper log is 66,236 bytes; `validate_result_manifest()` returns `False` with only `size:stdout.log`.
- Root cause: `finalize_result_manifest()` correctly excludes names in `RUNTIME_MANAGED_FILES`, but the launch wrapper used `stdout.log`; the current contract recognizes `runner_stdout.log`, `run.stdout` and sequence variants, not the generic name. The script prints the final solve report after manifest finalization, making this particular log stale by construction.
- Decision and exact next action: preserve the terminal output unchanged and do not call it an accepted reproducibility gate. Review a minimal wrapper/contract correction with regression coverage, then either produce a separately identified post-run audit manifest without overwriting evidence or rerun the corrected 744h gate. Do not infer authorization for fixed-server 8760h or another cloud job.

### v0.9.34 - 2026-07-27 - active 744h Barrier completed; crossover in progress

- Runtime identity remains the clean fixed-server checkout `c879c99`, output `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`, sole Python PID `663050`; no checkout, parameter or process was changed.
- Barrier milestone: Gurobi completed Barrier normally in 244 iterations and 8,917.48 s, reporting interior objective `2,196,881.94 million CNY`, then entered crossover.
- Crossover progress: 1,044,784 initial dual pushes fell to 464,775 by solver time 9,860 s. Telemetry subsequently reached 358,606 simplex iterations at 9,996.25 s with dual infeasibility about `3.515e-3`.
- Memory remains safe: solver memory is 13.948 GB, peak solver memory remains 25.087 GB, process RSS is about 13.8 GiB and host available memory about 55 GiB.
- Acceptance remains pending: `solve_report.json`, `solution_qc.json`, `result_manifest.json` and final `/usr/bin/time` output are absent. Exact next action is continue the sole crossover process and validate all terminal reports before accepting the 744h engineering gate.

### v0.9.33 - 2026-07-26 - active 744h build, presolve and factorization gates passed

- Git/runtime identity: the active solve remains on clean fixed-server HEAD `c879c99`; documentation milestone `b7b6e80` is pushed to both remotes but is intentionally not pulled into the active checkout.
- Build evidence: `build_report.json` records 341.673 s, 3,686,023 variables, 5,920,701 constraints, 42,360,391 nonzeros and 4.977 GiB build peak process-tree RSS.
- Solver structure: presolve completed in 223.80 s at 3,088,821 rows/3,017,979 columns/30,884,732 nonzeros. Automatic ordering completed in 115.48 s with `AA' NZ=6.449e7`, `Factor NZ=8.062e8`, about 9.0 GB estimated factor memory and `Factor Ops=6.197e12`.
- Runtime safety: telemetry peak solver memory reached 25.087 GB during ordering/factor setup; process RSS at early Barrier was about 19.1 GiB and host available memory about 50 GiB. These remain below the 48 GiB solver soft limit and do not justify interruption.
- Progress: Barrier iteration 4 completed at solver time 492.91 s. Primal residual and complementarity fell from `4.97e9/3.55e10` at iteration 0 to `3.89e9/2.83e10`; no acceptance result exists yet.
- Exact next action: keep the sole PID `663050` running, monitor residual trajectory, peak memory and crossover. On completion validate `solve_report.json`, `solution_qc.json`, `result_manifest.json` and scenario identity before accepting the 744h engineering gate.

### v0.9.32 - 2026-07-26 - CPU-PDHG rejected for first scale-up; Barrier-16-auto 744h launched

- Server deployment and validation: local, fixed-server and both pushed remotes are aligned at `c879c99`. The server-focused solver-profile tests pass after adding `pdhg_gpu` to the numerics-only whitelist; Base scientific settings remain unchanged.
- PDHG output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2` was gracefully stopped with `status=INTERRUPTED`, `termination_signal=SIGTERM`, `solution_count=0`, 3,074.134 solver seconds and 496,035 last recorded telemetry iterations. Peak solver/process-tree memory was 1.990 GB/2.503 GiB.
- Convergence decision: at about 49万 iterations the log retained a primal residual around `49.5`; the primal/dual objectives were about `2.0117e6/1.9993e6`, and the dual residual was rising. The run was about 4.82 times slower than the complete 637.344 s Barrier-16-auto gate and still had no accepted solution. Keep PDHG as low-memory diagnostic evidence, but exclude it from the first 744h run.
- Five-profile audit: `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}` records Barrier-32, Barrier-16+AMD, Barrier-16-auto, interrupted dual simplex and interrupted CPU-PDHG.
- Active gate: after verifying no other CISPO process and about 69 GiB available RAM, the fixed server launched one 2030 Base 744h run at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order` using `barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and `SoftMemLimit=48`. Python PID at launch was `663050`.
- Exact next action: monitor build, presolve, ordering, factor structure, Barrier/crossover and process-tree memory. Accept only `OPTIMAL + solution_qc=PASS + closed result_manifest`; otherwise preserve diagnostics and stop cleanly. Do not start a concurrent fixed-server solve, fixed-server 8760h or another paid cloud job.

### v0.9.31 - 2026-07-26 - 16-thread automatic-order Barrier leads; PDHG profile contract fixed

- Accepted output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier16_auto_order` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.8440447072 million CNY`, 637.344 s solver time and 3.459 GiB process-tree peak.
- Against Barrier-32: same presolved matrix and factor structure, 16 rather than 32 threads, 2.55% faster solve, 8.72% lower telemetry solver memory and 4.29% lower process-tree peak. Against Barrier-16+AMD: 7.292 s faster and avoids the AMD factor-operation inflation.
- Comparison output: `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}` records Barrier-32, Barrier-16+AMD, Barrier-16-auto and interrupted dual simplex.
- PDHG contract defect: the first root `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32` exited before data/model loading with `Unsupported solver-profile numerics keys: pdhg_gpu`. No solve was started. `cispo_model/config.py` now permits the diagnostics-supported key and `tests/test_solver_profiles.py` directly loads/asserts the CPU-PDHG profile.
- Validation: 67/67 local tests pass. Exact next action is deploy the whitelist fix, pass the focused server test, rerun CPU-PDHG under a new output identity, then select and launch one 744h profile.

### v0.9.30 - 2026-07-26 - Barrier-16 accepted at 168h; automatic-order control added

- Accepted output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier16_sparse_amd` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.8440447145 million CNY`, solver runtime 644.636 s and peak process-tree RSS 3.187 GiB.
- Relative to Barrier-32: runtime improves 9.390 s (1.44%), process-tree peak falls 0.427 GiB (11.81%), Barrier iterations fall from 185 to 175 and crossover/simplex iterations fall from 228,190 to 226,296.
- Ordering caveat: AMD ordering takes 9.83 rather than 25.70 s, but produces 5.21% more factor nonzeros and 25.54% more factor operations. This could scale adversely at 8760h even though the 168h total is slightly faster.
- Added `config/solver_profiles/barrier_16_auto_order_v1.json` and regression coverage so the next 168h run changes only `Threads=32 -> 16`; automatic ordering and sparsification remain at Gurobi defaults. Scientific settings are unchanged.
- Exact next action: pass local/server tests, run the automatic-order 16-thread 168h gate, then run CPU-PDHG. Select the first 744h profile only after comparing solve/QC, factor structure and memory.

### v0.9.29 - 2026-07-26 - dual simplex rejected at 168h; graceful termination proven

- Output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_dual_simplex16`.
- Evidence: after 905.073 solver seconds and 421,470 simplex iterations, the run still had no feasible solution and no objective; recent primal infeasibility repeatedly ranged from roughly `1.5e7` to `1.1e8`. Complete Barrier-32 took 654.026 s on the identical LP.
- Memory tradeoff: dual simplex peak process-tree RSS is 2.594 GiB and telemetry solver memory is about 2.70 GB, versus 3.614 GiB/3.88 GB for Barrier-32. The lower memory does not compensate for the observed degeneracy and convergence risk at larger horizons.
- Termination validation: SIGTERM reached `GracefulSolverTermination`, Gurobi returned status 11, and `solve_report.json` records `status=INTERRUPTED`, `solution_count=0`, `termination_signal=SIGTERM`; `/usr/bin/time` exited normally with status 0. No QC or scientific result is claimed.
- Decision: exclude dual simplex from the first 744h gate. Continue with sequential 168h Barrier-16 and CPU-PDHG gates on explicit spill.

### v0.9.28 - 2026-07-26 - matched 168h spill A/B closed; explicit formulation retained

- Server deployment: idle fixed-server checkout was fast-forwarded from `ed8e91a` to documentation HEAD `94d1f1d`; the complete suite passes 67 tests with two optional wave-I/O tests skipped because xarray is absent. No Base dependency is missing.
- Matched solve: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier32` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.844044710 million CNY`, solver runtime 654.026 s and peak process-tree RSS 3.614 GiB.
- A/B result: projected spill is 12.030 s faster at 168h but has 15,114 more presolved rows, 51,936 more presolved nonzeros, `0.7e6` more factor nonzeros, `6.8e8` more factor operations and 0.081 GB higher telemetry peak solver memory. Explicit spill also wins the paired 24h flexibility runtime 34.358 versus 45.168 s. Objectives and QC agree.
- Decision: retain explicit spill because full-year feasibility is constrained by presolved/factor memory and the explicit formulation is more robust across Base and flexibility. Do not infer solve benefit from a raw-column estimate. Preserve the projected 24h/168h roots as rejected-performance evidence.
- Audit output: `/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.{json,csv}` contains both paired runs.
- Local profile pre-screen: Base 24h reference Barrier-32, Barrier-16+AMD+PreSparsify, and dual simplex solve in 33.889, 29.181 and 25.796 s, respectively, all with identical objectives within tolerance and QC PASS. Limited-presolve and forced-dual profiles are slower and produce the same 24h presolved structure as reference.
- Exact next action: on the retained explicit formulation, run sequential fixed-server 168h dual-simplex, Barrier-16 and CPU-PDHG gates. Use their solve/QC/memory evidence to select one 744h profile; do not run fixed-server 8760h.

### v0.9.27 - 2026-07-26 - spill formulation A/B reopened after presolved-matrix evidence

- Git state: `44f7fef` adds limited-presolve/fast-crossover, forced-dual and CPU-PDHG profiles; `9e82cc5` restores explicit full-reservoir spill as the provisional default and adds `cispo_model/solver_audit.py`, `scripts/compare_solver_runs.py` and parser regression coverage. User-owned `supplementary_materials/**` changes remain unstaged and unmodified.
- Local paired evidence: explicit spill repeated at 349,039 variables/265,270 constraints/1,807,414 nonzeros, `OPTIMAL + solution_qc=PASS`, objective `1,982,474.939703926 million CNY` and 34.358 s solver time. The exact projected variant has the same objective within `1.4e-9` and passes QC, but takes 45.168 s; its presolved rows/nonzeros and factor operations are higher by 2.03%, 0.68% and 9.62%, respectively.
- Fixed-server projected evidence: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_projection_barrier32` is `OPTIMAL + solution_qc=PASS`. It has 931,447 original columns, presolves to 744,673 rows/757,209 columns/7,053,168 nonzeros, reports `Factor NZ=1.043e8`, `Factor Ops=8.504e10`, solves Barrier in 182 iterations/585.33 s and finishes after 219,718 crossover iterations/641.996 s. Peak process-tree RSS is 3.512 GiB.
- Interpretation: exact feasible-set equivalence does not imply a faster sparse factorization. The projected 168h result is faster than an older fixed-server reference but is not a matched current-code A/B, whereas the local paired 24h result favors explicit spill. Do not select by raw column count.
- Validation: 67/67 local regression tests pass after removing two projection-specific tests. The comparison parser test is included, and the repeated explicit-spill 24h gate passes all manifests and QC.
- Exact next action: push the comparison commits and this documentation, fast-forward the idle fixed server, pass regression, then run the same 2030 Base 168h Barrier-32 command with explicit spill. Select the formulation from presolved matrix/factor/runtime/QC evidence, then test solver profiles sequentially before the first 744h gate.

### v0.9.26 - 2026-07-26 - exact reservoir spill projection and persistent solver diagnostics

- Git state: implementation committed as `6d84209` on `codex/cispo-2030-full-lp`. No `supplementary_materials/**` file was staged or committed; the remaining user worktree changes are preserved.
- Exact reformulation: only 146 cascade-reservoir spill arrays remain explicit. For 474 independent reservoirs, the equality plus nonnegative spill is projected to a water-volume inequality and spill is reconstructed from its slack. This preserves the projected feasible set, generation, costs, downstream physics and the existing full reservoir-output contract.
- Scale evidence: Base estimates are now 330,967 variables at 24h and 36,760,087 at 8760h. Full-year reduction is 4,152,240 columns = 10.15% of the previous Base estimate; constraints are unchanged.
- Numerical equivalence: the previous 24h `flexible_load_comfort_v3` reference objective `1,982,474.939703926` and the projected result `1,982,474.9397039246 million CNY` differ by only `1.4e-9`. The new run is `OPTIMAL + solution_qc=PASS`; maximum reservoir balance residual is `4.68e-6 m3` and minimum reconstructed spill is `-2.12e-9 m3/s`.
- Solver engineering: `--solver-config` accepts only validated `numerics`, is separately hashed in provenance and cannot change scenario/model assumptions. Added reference Barrier-32, memory-conscious Barrier-16+PreSparsify+AMD and dual-simplex profiles. `solver_telemetry.jsonl` flushes Barrier/PDHG/simplex progress, residuals, work and solver memory during the solve, and graceful signal handling asks Gurobi to terminate so normal reports can be written when the scheduler provides a signal grace period.
- Validation: 68/68 regression tests pass. A real 1h Barrier-16 profile run is `OPTIMAL + solution_qc=PASS`, records the solver profile and telemetry, and reports about 0.17 s callback cost in a 9.31 s solve.
- Cloud terminal evidence: job `4004585` ended `TIMEOUT`, not OOM or infeasible, after reaching Barrier iteration 35. MaxRSS remained 476.76 GiB and no principal acceptance reports exist.
- Exact next action: push `6d84209` plus this documentation follow-up, fast-forward the idle fixed server, pass server regression plus 24h/168h gates, then run one 744h profile at a time under the 48 GiB solver soft limit and compare build, presolve, ordering, factorization, iterations, crossover, memory, objective and QC.

### v0.9.25 - 2026-07-25 - Barrier-32 passed factorization and reached iteration 23

- Scope: read-only live audit of ParaCloud job `4004585`; no checkout, model, data, output, scheduler limit or process was changed.
- Solver evidence: ordering completed in 3,180.53 s and produced `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, an estimated 340.0 GB factor footprint and `Factor Ops=2.448e15`. Barrier iteration 23 completed at solver time 60,528 s.
- Convergence evidence: primal residual/complementarity declined from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7` at iteration 23. This is real progress but not convergence; primal/dual objectives remain widely separated.
- Resource evidence: after 17:55:54 wall time, `sstat` reports 499,919,116 KiB MaxRSS = 476.76 GiB and `AveCPU=15-07:23:51`, corresponding to about 367.40 actual CPU-hours and roughly 20.5 cores used on average. Slurm allocation remains 96 CPU billing units/700G.
- Time-limit risk: only 6:04:06 remained at the audit. The Slurm 24h end time precedes the configured 86,400-second Gurobi optimize limit because approximately 41 minutes were spent building the model; without an authorized extension, Slurm may terminate the process before Gurobi can return a graceful `TIME_LIMIT` result.
- Acceptance: only `build_report.json` exists among the principal reports. `solve_report.json`, `solution_qc.json` and `result_manifest.json` remain absent; do not classify the run as solved or start 2040.

### v0.9.24 - 2026-07-25 - authorized Barrier-32 full-year retry submitted

- Git/model identity: local worktree remains dirty at `796a6fc6d0e37db1156c56d9fcbe2468db8cceef`; concurrent local wave/flexibility changes were preserved. The cloud release remains immutable at `22fb493`; no model code, data root or scientific configuration was changed.
- Remote change: created additive script `cloud_cispo_8760_2030_base_barrier32.sbatch` with SHA256 `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`. Relative to job `4003172`, it changes only `--cpus-per-task=128 -> 32`, job/log identity and the isolated output root; it retains `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, 700G and 24h.
- Scheduler evidence: job `4004585` started at `2026-07-25 02:34:26 CST` on `m4cg1702`. Slurm shows `CPUs/Task=32` and the runtime config records `threads=32`, but the 700G request caused an allocation/billing TRES of 96 CPUs. The embedded 50-test gate passed in 11.845 s.
- Prior-use accounting: job `4003172` has `CPUTimeRAW=2,642,304` allocated CPU-seconds = 733.973 core-hours and `TotalCPU=07:03:11` actual CPU time. The account-level `sreport` total for 2026-07-24 through 2026-07-26 was 48,355 CPU-minutes = 805.917 core-hours across all jobs; Slurm exposes no remaining paid quota or currency balance.
- Changed handoff files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`. No supplementary-material file was modified.
- Exact next action: monitor `4004585` through construction, presolve and ordering. Acceptance requires a terminal status plus `solve_report.json`, `solution_qc.json` and `result_manifest.json`; if it again fails before `Barrier statistics`, preserve the root and do not start another full-year retry without a new solver/memory decision.

### v0.9.23 - 2026-07-25 - authorized 2030 cloud solve OOM before barrier

- Git/server scope: documentation-only live audit of ParaCloud job `4003172`; concurrent local wave/flexibility work was preserved and no checkout, code, input, output or scheduler state was changed.
- Terminal evidence: `sacct` reports `OUT_OF_MEMORY`, exit `0:125`, start `2026-07-24 20:24:47`, end `2026-07-25 02:08:50`, elapsed 5:44:03, 128 CPUs and 700G requested memory. `seff` reports 526.99 GiB MaxRSS and 0.96% CPU efficiency.
- Solver stage: model construction had already passed. Gurobi presolve consumed 17,932.25 s and produced 37,982,903 rows, 35,423,761 columns and 400,861,556 nonzeros. Ordering logged through 140 s; no barrier statistics or iteration 0 appeared before the process was killed.
- Acceptance: `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent. The cloud root `outputs/full_year_2030_base_22fb493_128cpu_700g` is rejected as an incomplete OOM diagnostic and must be preserved.
- Resource caveat: recorded MaxRSS is below the 700G request, but the step reported an OOM kill and the 750G-configured node rebooted approximately two minutes later. Do not infer a safe 527 GiB requirement; a transient spike, cgroup/kernel accounting or node failure remains possible without administrator logs.
- Exact next action: do not repeat `Method=2`, `Presolve=2`, `Threads=128`, `SoftMemLimit=640` on the same 750G-class node. First audit lower-memory algorithms/orderings on bounded gates or obtain a genuinely larger-memory node, and require fresh explicit authorization before any new full-year submission. Crossover changes alone cannot address this failure because crossover was never reached.

### v0.9.22 - 2026-07-25 - existing-grid wave correction and combined wave/flexibility cases

- Git state: uncommitted local worktree on `codex/cispo-2030-full-lp`, based on `796a6fc`; all pre-existing flexibility and `supplementary_materials/**` changes were preserved. No server/cloud state changed.
- Scope: supersedes v0.9.21 spatial routing. `scripts/build_wave_energy_inputs.py` now retains only raw wave cells matching existing `optimization_points.csv` coordinates within `0.02` degrees and `is_land=0`; `wave_source_grid_id` is CF provenance only, while model identity/cohorts/routes use existing `grid_uid`/`grid_id`.
- Data evidence: 1,285 unique existing marine rows, 1,284 positive-potential options, 9,798.111 GW retained raw potential, 57 imputed-CF rows, maximum actual coordinate difference `4.96e-5` degrees, and exact reuse of every matched `city_337` route. The previous nearest-offwind proxy could misroute external South China Sea rows by up to about 1,524 km and has been removed.
- Combined cases: added `wave_energy_medium_v1_flexible_load_v1.json` and `wave_energy_medium_v1_flexible_load_comfort_v3.json`. Each jointly optimizes both modules in one LP; Base and the single-module scenarios remain separate catalog cases and outputs.
- Changed files: `scripts/build_wave_energy_inputs.py`, `cispo_model/{wave_energy,config,master,monolithic,load_center,preflight,solution_export,io_contract}.py`, wave and combined scenario JSON, scenario catalog, critical parameter registry, wave/sensitivity tests, `WAVE_ENERGY_INTEGRATION.md`, model spec, status, runbook and this handoff.
- Verification: wave and combined 24h preflight reports have overall `PASS` status with 72 records each (67 `PASS`, 2 `INFO`, 3 unrelated existing `WARN`); full local regression passes 62/62; scenario JSON parsing, `py_compile` and `git diff --check` pass. Base/wave/wave+flex-V1/wave+comfort-V3 24h build-only gates contain 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. A four-case sensitivity-suite dry run preserves independent output/state roots and accepts both combined IDs. Full-year static wave and wave+flex-V1 estimates are 36.47/36.91 GB. No optimization was started.
- Unresolved: retained potential is still a very large technical upper bound; scenario-specific potential is absent; 2060 holds 2050; China cost, exchange rate, depth/distance, imputation and `potential_fraction` sensitivities remain mandatory. Comfort V3 combined runs additionally require its generated envelope.
- Exact next action: finish local regression/diff checks, then review the spatial/cost sensitivity matrix before any separately authorized 24h optimization and QC gate.

### v0.9.21 - 2026-07-25 - grid-resolved optional wave-energy expansion

- Git state: uncommitted local worktree on branch `codex/cispo-2030-full-lp`, based on `796a6fc`; pre-existing flexibility and supplementary-material changes were preserved and no server/cloud checkout was modified.
- Scope: audited `wave_grid.nc` and the Excel summary; added an opt-in wave data contract, grid capacity/new-build cohorts, exact hourly CF availability, provincial dispatch/balance/reserve coupling, annual load-center allocation, cost/QC/provenance/summary exports, and a scenario catalog entry while leaving `VRE_TECHS` and Base unchanged.
- Main changed files: `cispo_model/wave_energy.py`, `data.py`, `config.py`, `master.py`, `monolithic.py`, `load_center.py`, `planning_state.py`, `preflight.py`, `solution_export.py`, `result_summary.py`, `io_contract.py`; `config/optimization_2030.json`, `config/scenarios/wave_energy_medium_v1.json`, `config/scenarios/scenario_catalog.json`, `config/critical_parameter_registry.csv`; `scripts/build_wave_energy_inputs.py`, `data/wave/*`, `tests/test_wave_energy.py`, `tests/test_sensitivity_suite.py`, `WAVE_ENERGY_INTEGRATION.md`, `cispo_full_lp_model_spec.md`.
- Commands/evidence: `scripts/build_wave_energy_inputs.py` produced 4,194 unique routes and SHA256 manifests; wave preflight is `PASS` with 68 checks; Base and wave 24h build-only gates succeed; `python -m unittest discover -s tests` passes 61/61; `py_compile` and `git diff --check` pass.
- Data/cost boundary: raw potential is identical in all ten CF scenarios, 241 CF grids are imputed, maximum source distance/depth is 1,654.768 km/5,847.782 m, route-proxy distance reaches 1,530.837 km, and 2060 holds 2050 medium. CAPEX/FOM/lifetime and depth/distance adders follow DOI `10.1016/j.apenergy.2024.123119` with explicit `7.8 CNY/EUR`.
- Unresolved: replace the nearest-offwind route proxy with maritime/landing/cable data; obtain real scenario-specific potential and 2060 data; calibrate China cost year/exchange rate; run potential/depth/distance/imputation/cost sensitivities. No 24h solve, 168h/744h/8760h run or deployment is authorized by this milestone.
- Exact next action: review and freeze the wave spatial-screen and cost sensitivity matrix; only then run a local 24h optimization/QC gate, followed by separately authorized staged gates.

### v0.9.20 - 2026-07-24 - Power_curve_V2 comfort envelopes, deadline V1G and causal optional V2G

- Git state: uncommitted local worktree based on `796a6fc`; no fixed-server or cloud deployment.
- Scope: adds an independent `comfort_envelope_v3` without changing Base or accepted legacy scenario semantics. Thermal power limits come from `Power_curve_V2` BAIT/balance-point perturbations rather than uniform 15% fractions; V1G receives a rolling cumulative 12h service deadline; optional V2G is a causal daily-zero 5%-of-EV-peak sensitivity. Response costs are split by thermal direction, V1G relocated energy and V2G discharged energy.
- Changed files: `cispo_model/{config,data,flexible_load,io_contract,preflight,solution_export}.py`, `scripts/build_flexible_load_envelope_v3.py`, `config/scenarios/{flexible_load_comfort_v3,flexible_load_comfort_v3_v2g_5pct,scenario_catalog}.json`, `tests/{test_flexible_load,test_sensitivity_suite}.py`, `supplementary_materials/灵活性负荷V3建模与参数依据.md`, and this handoff/status/runbook set. Existing user-owned supplementary files were not edited.
- Data evidence: generated ignored input `data/load/flexible_load_envelope_v3.csv.gz` has 1,357,800 rows and SHA256 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`; its provenance sidecar records all upstream hashes and four passing QC families. A 24h preflight confirms both files are required/hash-recorded scenario inputs.
- Validation: 58/58 local regression tests pass. `outputs/diagnostic_24h_flexible_load_comfort_v3` and final V2G root `outputs/diagnostic_24h_flexible_load_comfort_v3_v2g_5pct_final` are both `OPTIMAL + solution_qc=PASS`; solver runtimes are 33.63/38.60 s, peak process-tree RSS 0.739/0.718 GiB, and all state, terminal, service, combined-charging, simultaneity and objective-component checks pass.
- Unresolved: the +/-1 C band, equivalent thermal duration/retention, V1G participation/deadline and activation prices remain sensitivity parameters rather than province-specific building/vehicle calibrations. Vehicle connection/SOC/departure data and building RC/COP/occupancy data are absent. The 5% V2G number is explicitly not a policy mandate.
- Next action: retain the no-V2G V3 scenario as the main flexibility sensitivity and the 5% V2G case as separate. Run low/base/high parameter sweeps on small horizons, then request explicit authorization before any fixed-server 168h or larger V3 gate. Do not alter the active cloud release.

### v0.9.19 - 2026-07-24 - cloud full-year build accepted; 2030 solve in presolve

- Git/model identity: cloud release remains immutable at `22fb493`; this is a read-only operational audit and documentation update. Local state-flex code `271c6dc` is not deployed to the active cloud release.
- Build-only evidence: Slurm job `4003088` completed in `00:40:20`, exit `0:0`, on `m4cm1904`. `build_report.json` records `SCIENTIFIC_PRODUCTION`, 8,760 h, 40,912,327 variables, 68,189,325 constraints, 515,040,080 nonzeros and 53.633 GiB peak process-tree RSS. No solve/QC is expected from this no-optimize gate.
- Solve evidence at 2026-07-24 21:17 CST: dependent job `4003172` is `RUNNING` on `m4cg1702`, 128 CPU, 700G, 24h limit. Its model build completed in about 40m32s with identical structure and 53.686 GiB build peak. Gurobi 13.0.2 accepted `Threads=128`, `SoftMemLimit=640`, the WLS license and the full LP, then entered `Optimize`.
- Current stage/resource: the latest log ends after coefficient statistics, before `Presolve removed` or barrier iteration 0. Treat it as Gurobi presolve/matrix preprocessing, not barrier or crossover. `sstat` batch MaxRSS is 101,085,156 KiB = 96.402 GiB; no `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists yet.
- Action: continue read-only monitoring. Do not cancel, resubmit, change checkout/config, start 2040 or classify the result until terminal Slurm state plus solve report, QC and manifest are all available.

### v0.9.18 - 2026-07-24 - state-based thermal flexibility and causal EV V1G

- Git implementation: `271c6dc` (`feat: add state-based flexible load scenario`), based on `72bd078`.
- Scope: added independent `flexible_load_state_v2` without changing Base, `flexible_load_v1` or `flexible_load_v2g_v1`; implemented daily-reset equivalent heating/cooling state equations, thermal loss accounting and a nonnegative EV charging backlog that prevents recovery charging before baseline energy is deferred. The new formulation rejects V2G until hourly vehicle availability, battery energy and departure-service inputs exist.
- Power_curve_V2 alignment: verified the current 1,357,800-row National_model table is an exact five-year/name-code/MW-to-GW transformation of the eight-year future projection, with maximum numerical error `5.68e-14 GW`. The final input SHA256 is `8c2cb3b6b233625af2e6f9aef635a1fcabfe746010c2a11464579f8b77a369cd`; the upstream projection SHA256 is `67a0a79ed94f5ffa1f5935519044e09e8878f6429fbe79ed605d16e4d067af5a`. `ev_hour_weight` remains an uncontrolled charging shape, not availability.
- Main files: `cispo_model/flexible_load.py`, `cispo_model/config.py`, `cispo_model/preflight.py`, `cispo_model/solution_export.py`, `cispo_model/io_contract.py`, `config/scenarios/flexible_load_state_v2.json`, `config/scenarios/scenario_catalog.json`, tests and the tracked model/I/O/provenance documents. No `supplementary_materials/**` file was modified or committed.
- Verification: 56/56 regression tests and `compileall` pass. Final 2030 24h output `outputs/2030_24h_v0724_flexible_load_state_v2_final` is `OPTIMAL + solution_qc=PASS`; it has 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 32.84 s solve time and 0.705 GiB peak process-tree RSS. Maximum heating/cooling/EV backlog transition residuals are `8.88e-16/1.73e-18/4.44e-16 GWh`, all daily terminal states/backlog are zero, simultaneous up/down counts are zero and the result manifest validates.
- Sequential interface: `outputs/planning_sequence_1h_v0724_flexible_load_state_v2` passes 2030/2040/2050/2060 with four `OPTIMAL + QC PASS` cases, four valid manifests and immediate four-year `RESUMED_ACCEPTED`. This is test-only evidence.
- Scale: full-year static estimate is 43,356,367 variables, 68,724,249 constraints, 524,283,387 nonzeros and 36.84 GiB model memory. Barrier factorization remains a separate larger risk; no 8760h authorization is inferred.
- Unresolved: V2 parameters remain illustrative (`15%` thermal power envelope, `4/5 h` duration, `0.94/0.92` retention, `50%` EV movable share, `12 h` queue envelope, `10 CNY/MWh` per throughput direction). The upstream `Power_curve_V2/scripts/08_generate_future_8760_loads.py` is still untracked in its own dirty repository, so its file SHA256 is recorded but Git-only upstream reproduction is incomplete. No hourly EV plug availability, battery energy, driving withdrawal, departure SOC or province-calibrated building RC/COP data exist.
- Server/cloud: not deployed and not started. Existing fixed-server and cloud output identities must not be reused with `271c6dc`.
- Next action: review/calibrate the new sensitivity parameters and obtain EV availability/building thermal evidence; only after explicit authorization and a live idle-check may a new versioned fixed-server 24h then 168h state-V2 gate be deployed. Do not launch fixed-server 744h/8760h or another paid-cloud 8760h case.

### v0.9.17 - 2026-07-24 - VRE CF fallback hard-fail and city_337 contract clarification

- Git baseline: `4b5bd98`. Changed owned files are `cispo_model/data.py`, `cispo_model/preflight.py`, `tests/test_vre_cf_fallback.py`, `MODEL_IO_CONTRACT.md`, `SCENARIO_MODULE_ARCHITECTURE.md` and the three continuity documents. The user-authored `supplementary_materials/deep-research-report.md`, `supplementary_materials/National_model_Codex_implementation_plan.md` and all other `supplementary_materials/**` changes remain untouched and unstaged.
- Scope and decision: fixed only a latent cross-technology CF fallback path. Wind sites may use their primary technology store or same-grid `mixed_wind`; if neither exists the loader now hard-fails instead of selecting a PV donor. UPV/DPV may still use the nearest same-province valid PV donor, now explicitly restricted to land-centroid donor grids. Added hard preflight checks for cross-technology mappings and non-land PV donors. Corrected two current contract descriptions from 278 to the production `city_337` annual proxy without rewriting historical 278 replication records.
- Evidence: the active 2030 Base input has 35 onwind and 10 offwind primary-store gaps, all resolved at the same grid through `mixed_wind`; there are zero unresolved wind rows and zero wind-to-PV mappings. There are 29 UPV and 112 DPV nearest-PV fallback rows. A before/after donor comparison shows that the new land-donor restriction changes zero of the 141 current assignments. Focused tests pass 4/4 and full local regression passes 54/54 in the `RL` environment.
- Scientific interpretation: `is_land` is the 0.25-degree cell-centroid mask, not a technology label. The 35 onwind-on-water and 10 offwind-on-land active rows are existing-capacity boundary allocations, have no expandable scenario-B capacity, and use the documented same-grid mixed-wind fallback. They must not be silently reclassified or deleted. Existing-VRE retirement, coincident trunk sizing and enhanced flexibility remain separate scientific choices, not part of this no-regression fix.
- Exact next action: do not alter the active cloud release or jobs. Before deploying this local hardening to any server, wait for the current cloud case to be preserved, use a new code/data/output identity and rerun regression/preflight plus 24h/168h gates. Decide the existing-VRE survival dataset and optional coincident-trunk scenario separately; do not insert unsourced retirement fractions into Base.

### v0.9.16 - 2026-07-24 - cloud 24h/168h gates accepted; authorized 2030 full-year execution queued

- Git baseline: `1d72a8a`; new tracked cloud wrappers are `cloud_runs/scripts/cloud_cispo_diagnostic_gate.sbatch`, `cloud_runs/scripts/cloud_cispo_8760_build_only.sbatch` and `cloud_runs/scripts/cloud_cispo_8760_2030_base.sbatch`, alongside the three handoff/runbook status documents. No `supplementary_materials/**` content was modified or staged.
- Scope: the user-authorized release passed ordered 24h and 168h 2030 Base cloud gates, each with explicit `Threads=32`, 50/50 tests, `OPTIMAL`, `solution_qc=PASS` and closed result-manifest validation. Structural full-year job `4003088` then began on the 768G partition with 128 CPU and 700G; it performs model construction only. After the user explicitly authorized a single-year full solve, `4003172` was submitted with `afterok:4003088`, 128 CPU, 700G, 24h scheduler limit and a 640G Gurobi soft-memory limit. The resource overrides do not change the CISPO physics, objective, constraints, data or horizon.
- Evidence: `4003035` has 342,343 variables/262,201 constraints/1,771,703 nonzeros and 26.978 s solve time; `4003045` has 1,011,079/1,393,915/9,797,949 and 377.057 s. Their cloud roots are respectively `outputs/cloud_gate_24h_base_2030_22fb493` and `outputs/cloud_gate_168h_base_2030_22fb493`; both retain full solver, QC and manifest evidence. At update time `4003088` is running on `m4cm1904`, while `4003172` is correctly `PENDING` on the success dependency.
- Exact next action: let `4003088` finish and validate its `build_report.json`, run scope and Slurm `MaxRSS`. If it succeeds, monitor `4003172` through model construction, Gurobi presolve/barrier/crossover and terminal output QC. Do not start a 2040 successor or reinterpret an incomplete/limit-stopped 2030 run as a scientific production sequence.

### v0.9.15 - 2026-07-24 - cloud proxy export repaired; WLS smoke restored

- Git baseline: `90a0785`; changed tracked files are `cloud_runs/scripts/cloud_proxy_export_probe.sbatch`, `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. No `supplementary_materials/**` content was touched or staged.
- Scope: at user direction, repaired only the three malformed lower-case proxy export lines in cloud account `.bashrc` and retained `/publicfs01/fs1-a8/home/a8s001819/.bashrc.codex_backup_20260724_proxy_export` before the change. No license-file content, credential or fixed-server checkout was modified.
- Verification: fresh login shell reports all three expected proxy variables. Compute-node job `4002980` explicitly cleared its proxy environment, sourced `.bashrc`, passed `PROXY_EXPORT_COMPUTE_PASS`, and reached `token.gurobi.com` through `172.16.110.3:8888` with HTTP 302. WLS job `4002981` on `m4ci1905.para.bscc` completed `Env.start()` and a two-variable LP with `SMOKE_STATUS 2`, objective `1.0` and `GUROBI_SMOKE_PASS`. Its separate 10-second curl probe timed out, but Gurobi authenticated and optimized successfully.
- Next action: cloud license gate is restored. Before any full-year build-only, run fresh versioned 24h and 168h cloud gates with `Threads <= --cpus-per-task`, full QC and manifests. Do not start fixed-server 744h/8760h or cloud full-year optimization.

### v0.9.14 - 2026-07-24 - fresh cloud network probe reconfirms WLS block

- Git state: local HEAD remains `22fb493`; no model code, input data or production output was changed.
- Scope: submitted only user-authorized Slurm job `4001248` to `amd_a8_384` with 1 node, 1 CPU, 2 GiB and a 5-minute limit. It was the staged `cloud_wls_network_probe.sbatch`; no Gurobi model, CISPO model build or optimization was submitted.
- Evidence: node `m4cl1305.para.bscc` reported direct DNS timeout for `token.gurobi.com` and `curl` status `000`; the explicitly supplied historical proxy `172.16.110.3:8888` returned connection refused and status `000`. `sacct` reports `COMPLETED`, exit code `0`, because the diagnostic intentionally records connectivity failures without failing the shell job.
- Decision: the 8760h user request was reduced safely to its required network gate. No full-year build-only or solve can start until the administrator supplies a currently reachable compute-node proxy or egress route and a new WLS LP reports `GUROBI_SMOKE_PASS`.
- Exact next action: obtain the current proxy hostname/port or an approved direct allowlist from the administrator; run one 1-CPU/2-GiB WLS LP smoke, then re-establish the ordered 24h and 168h cloud gates with explicit Gurobi thread limits before the separately controlled 8760h build-only gate.

### v0.9.13 - 2026-07-24 - cloud city_337 staging and 8760h preflight

- Git baseline: local `22fb493`; fixed-server source baseline `cf39e0a`. Changed tracked files: `cloud_runs/scripts/cloud_wls_network_probe.sbatch`, `cloud_runs/scripts/cloud_cispo_8760_preflight.sbatch`, this handoff, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. User-owned `supplementary_materials/**` changes were not modified or staged.
- Scope: staged a new cloud release `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493` without touching the fixed-server checkout. It contains the `22fb493` code archive, `model_ready_20260723_v0722_city337`, `hourly_cf` and `hydro_timeseries_20260719_sequential_sparse`; raw GRFR is intentionally not replicated because it is a provenance/readiness input, not a runtime dependency of this LP.
- Verification: code archive SHA256 is `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`; 11,350 staged input hashes match source manifest SHA256 `662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`. A missing cloud numerical stack was installed offline into the user-private `gurobipy310` environment from a 14-wheel Linux/Python 3.10 bundle (archive SHA256 `63141e6059580f7a94cbdeafbbc60fe98b69f6e5eca971d9b342ac5d4529228e`); `pip check` passes and Gurobi 13.0.2 was not replaced. Slurm job `4001137` completed the full-year preflight on `m4ci1905.para.bscc` in 4 s, reporting 175.17 GiB available memory, 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB estimated model memory.
- Blocker: WLS smoke `4000608` on `amd_a8_384` and independent network probe `4000762` on `amd_m8_768-a` both show direct DNS/egress failure and `172.16.110.3:8888` connection refused. Therefore no Gurobi model build, no 24h/168h cloud gate and no 8760h build-only/solve was submitted. The `.bashrc` proxy whitespace defect remains untouched; batch scripts export proxy variables explicitly.
- Exact next action: obtain a working compute-node proxy/egress route from the cloud administrator, rerun one 1-CPU/2-GiB WLS smoke and require `GUROBI_SMOKE_PASS`; then run fresh cloud 24h and 168h gates with `Threads <= --cpus-per-task` before the separately controlled full-year build-only gate. Do not infer solve time from the static 36.0 GiB estimate.

### v0.9.12 - 2026-07-23 - city_337 fixed-server 168h V2G accepted

- Identity: server checkout `cf39e0a`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; output `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1`.
- Solve/state evidence: all four years are `OPTIMAL + solution_qc=PASS`; immediate `--resume` returns four `RESUMED_ACCEPTED` records. Runtimes are 792.55/806.12/953.60/1033.25 s; wall time 1:09:57; peak RSS 4,087,888 KiB; swaps zero; wrapper exit zero.
- Output/QC evidence: each 59-entry SHA256 manifest validates with no mismatch. The V2G matrix has 1,057,951 variables, 1,404,982 constraints and 10,100,013 nonzeros. All hard checks pass; maximum center/province/intra/power residuals are `5.12e-12 GWh`, `3.64e-12 GWh`, `3.11e-08 GWh` and `1.60e-10 GW`; BECCS closure is zero.
- V2G evidence: V2G is enabled only in this independent scenario; maximum transition residual is `1.90e-13 GWh`; simultaneous charge/discharge is zero. Period losses in 2030/2040/2050/2060 are 7.747/4.509/13.909/42.092 GWh and agree with both `charge-discharge` and net-load energy change to numerical precision.
- Solvability assessment: barrier/crossover times are 729.00/61.68, 720.15/82.77, 665.47/283.90 and 770.22/259.12 s. Memory remains below 3.9 GiB and no output or state-chain regression is found; late-year crossover remains the measurable runtime variability.
- Next action: server is deliberately idle after completing the approved Base/V1/V2G 24h/168h matrix. Use `city_337` for all future work. Do not start 744h/8760h locally or paid-cloud 8760h without a separately authorized gate.

### v0.9.11 - 2026-07-23 - city_337 fixed-server 24h V2G accepted; 168h V2G active

- Accepted output: `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1`, server checkout `cf39e0a`, data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- Solve/evidence: all four years and immediate `--resume` pass; runtimes are 44.81/43.45/48.35/45.23 s, wall time 9:10, peak RSS 934,340 KiB, swaps zero and wrapper exit zero. Every year is `OPTIMAL + solution_qc=PASS`, has zero false hard checks and a valid 59-entry SHA256 manifest.
- V2G/output evidence: V2G is enabled only in this independent scenario. Maximum transition residual is `1.83e-12 GWh`; simultaneous charge/discharge is zero. Period charging losses in 2040/2050/2060 are 0.1563/2.3423/3.4673 GWh and equal both `charge-discharge` and `net_load_energy_change` to numerical precision. Network, Base flexibility, security and BECCS closures remain valid.
- Active/next action: PID `4032297` runs `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1`. Keep checkout/data immutable; after exit validate all four years, output layers, loss accounting, state transfer and an immediate `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.10 - 2026-07-23 - city_337 fixed-server 168h V1 accepted; 24h V2G active

- Accepted output: `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1`, server checkout `cf39e0a`, data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- Solve evidence: all four years and immediate `--resume` pass; runtimes are 714.39/816.08/1007.71/980.09 s, wall time 1:08:59, peak RSS 4,030,672 KiB, swaps zero and wrapper exit zero. Barrier/crossover times are 665.74/45.79, 738.71/74.38, 738.10/265.69 and 688.26/288.77 s.
- Output/QC evidence: four SHA256 manifests validate with no mismatches; every year has 337 center balances, 2,022 center-technology rows, 642 intra edges, 31 province accounts, 31 flexibility accounts and 57 output-catalog data rows. All hard checks pass; maximum center/province/intra/power residuals are `5.06e-12 GWh`, `3.64e-12 GWh`, `4.69e-11 GWh` and `1.75e-10 GW`. BECCS closure is zero.
- Flexibility/state evidence: maximum heating/cooling/EV V1G daily-energy residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; no simultaneous up/down occurs; V2G is disabled; the scenario SHA256 is identical in all four years. `capacity_cohorts_v2` and the final four `RESUMED_ACCEPTED` records revalidate strict state transfer.
- Solvability assessment: versus city_337 Base, V1 adds 31,248 variables, 5,859 constraints and 218,736 nonzeros (3.09%, 0.42%, 2.23%) but total solver time decreases 8.23%. Runtime variability remains concentrated in crossover, especially 2050/2060; no memory, swap, manifest or output-layer regression is detected.
- Active/next action: PID `3984748` runs the independent 24h `flexible_load_v2g_v1` chain at `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1`. Keep checkout/data immutable; require V2G transition closure, zero simultaneous charge/discharge, energy-loss accounting, four manifests and `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.9 - 2026-07-23 - city_337 fixed-server 24h V1 accepted; 168h V1 active

- Identity: server checkout `cf39e0a`; data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; accepted output `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1`.
- Solve/output evidence: four years and immediate `--resume` are `PASS`; all years are `OPTIMAL + solution_qc=PASS`, have zero false hard checks, 337-node network closure and 59 manifest entries. Runtimes are 40.84/44.23/43.39/41.95 s; wall time is 9:35, peak RSS 929,096 KiB and swaps zero.
- Flexibility evidence: scenario ID is `flexible_load_v1`, flexibility is enabled, V2G is disabled, maximum heating/cooling/EV V1G daily-energy residual is `1.14e-13 GWh`, and simultaneous up/down counts are zero. Capacity margin remains 5%, effective inertia remains 3.5 s and BECCS closure remains numerical zero.
- Active/next action: PID `3687503` runs `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1`. Do not change the server checkout/data root. After exit, audit all four solve/QC/manifests/network/flexibility/state outputs and run an immediate identity-safe `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.8 - 2026-07-23 - city_337 fixed-server 168h Base gate accepted

- Identity: model/server checkout `cf39e0a`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; Base output `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`.
- Solve evidence: sequence and immediate resume are `PASS`; all four years are `OPTIMAL + solution_qc=PASS` with runtimes 733.00/811.58/892.10/1397.12 s. Wall time is 1:13:47, peak RSS 4,085,152 KiB and swaps zero.
- Output/state evidence: no false hard checks; every result manifest has 59 entries and validates; output layers contain 337 centers, 2,022 center-technology rows, 642 edges and 31 province accounts; strict `capacity_cohorts_v2` transition is reverified by four `RESUMED_ACCEPTED` records.
- Solvability assessment: versus the prior 278 Base 168h model, city_337 adds 1,031 variables, 924 constraints and 2,749 nonzeros. Total solver time is 4.68% higher; 2030/2040/2050 remain comparable or faster, while 2060 Crossover takes 706.6 s and is the principal remaining numerical-performance risk.
- Active/next action: PID `3632117` runs a separate 24h `flexible_load_v1` city_337 chain in `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1`. Keep checkout/data immutable; validate daily conservation, simultaneous shifting, manifests and resume. V2G remains separate; no 744h/8760h.

### v0.9.7 - 2026-07-23 - city_337 fixed-server 24h gate accepted

- Git/server identity: model and fixed-server checkout `cf39e0a`; city-network implementation `8e76753`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; transferred archive SHA256 `c1451d95c3303f98e53434cd29abc4288f486cba04c99a2c591380b010d470bb`.
- Gate repair: the first server smoke correctly stopped before any solve because its legacy expectation omitted two fuel-cost technologies. The table itself is complete and unique at 1,550 rows (31×5×10). `cf39e0a` updates the smoke contract and adds year/technology/uniqueness checks; local and server smoke pass 142/142.
- Verification: server 50/50 tests, full-license/readiness and preflight pass. The 24h Base four-year sequence and immediate resume audit pass; runtimes 43.29/48.82/41.17/46.90 s, wall 7:21, peak RSS 930,204 KiB, 337 centers and 59 manifest entries per year. All hard checks, network residuals, capacity margin, inertia and BECCS closure pass.
- Active/next action: PID `3321747` runs the new 168h Base chain in `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`. Keep server checkout/data immutable, monitor each year, then validate all outputs and `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.6 - 2026-07-23 - 337-city production network and 2025 initialization

- Git implementation: `8e76753` (`feat: promote 337-city load-center network`). Before deployment the fixed server was reverified clean and idle at `6ed943a`; existing output roots were not altered.
- Scope: promoted one-center-per-prefecture `city_337` to production; retained the 278 Natural Earth package as a separate CISPO replication input; rebuilt every VRE/hydropower route by exact same-province joint minimization of great-circle spur+trunk distance; rebuilt the 642-edge MST+3NN network and 2025 spur/trunk/intra capacities.
- Data/figure evidence: 337 centers/31 provinces, 296 observed and 41 imputed 2022 city electricity weights, 16,609 VRE routes, 2,030 hydro routes, 642 edges, 203 initialized edges, and maximum initialization balance residual `7.28e-14 GW`. Module 03 Figure M09 and the new two-panel Figure M09c plus PDF/450-dpi PNG/source CSV/QA were regenerated locally; pre-existing user files outside the requested module scope were not staged or committed.
- Verification: package manifest `PASS`; 50/50 regression tests; 61-check preflight `PASS`; local four-year 1h Base sequence `PASS` with four `OPTIMAL + solution_qc=PASS` cases, 337 center rows and 59 manifest entries per year; `--resume` returned four `RESUMED_ACCEPTED` records. Base flexibility remains disabled, capacity margin is 5%, and effective inertia is 3.5 s.
- Unresolved/next action: transfer the ignored model-data package by SHA256 to a new additive server data root, deploy the exact pushed commit only while the checkout remains idle, run server tests/readiness, then validate a new 24h four-year Base chain before a 168h chain. Inspect every output layer and compare scale/runtime; do not start fixed-server 744h/8760h or paid cloud 8760h.

### v0.9.5 - 2026-07-22 - reviewed capacity margin and inertia baseline

- Git state: local HEAD `e28f315`; reliability changes are uncommitted and not deployed. The fixed server remains at accepted checkout `6ed943a`, with no new process or output.
- Scope: changed Base provincial capacity margin from `15%` to the reviewed CISPO-aligned `5%`; represented minimum inertia as `3.5 s reference × 1.0 tolerance`; added one resolver shared by model construction and solution QC; retained backward compatibility for v1 scenarios that supply the former single effective threshold.
- Changed files: `config/optimization_2030.json`, `config/critical_parameter_registry.csv`, `cispo_model/config.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `scripts/audit_model_parameters.py`, `tests/test_model_foundation.py`, `cispo_full_lp_model_spec.md`, and the three handoff/runbook files. User-owned `supplementary_materials/**` changes were not modified.
- Verification: `conda run -n RL python -m unittest discover -s tests -p "test_*.py" -v` passed 49/49 tests. Local 1h output `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` reached `OPTIMAL` in 12.84 s with `solution_qc=PASS`; effective inertia is `3.5 s`, both reliability hard checks pass, minimum inertia margin is `12.4173 GW·s`, the capacity-margin residual is numerical zero (`-5.68e-14 GW`), and manifest validation returns `(True, [])`. This is a truncated engineering gate, not a scientific result.
- Unresolved/next action: freeze the 2025-2060 total transformation-cost formulation before changing the objective. Keep the current annual snapshot objective until an explicit discounted multi-period NPV or clearly separated ex-post pathway ledger is approved; do not mix lump-sum CapEx with CRF annualization.

### v0.9.4 - 2026-07-22 - CISPO-equivalent BECCS carbon mass balance closed

- Git implementation: `c62b769` (`fix: close beccs carbon mass balance`), based on `231c3d9`. The fixed server remains at `6ed943a`; no checkout, process or accepted output was changed.
- Scope: introduced a single BECCS factor resolver and replaced the ambiguous dual use of the negative factor with explicit gross/captured/stored/uncaptured biogenic CO2, lifecycle emissions and net removal. The CISPO replication baseline retains zero lifecycle emissions, 90% capture and the published year-specific net factors, so objective coefficients, source-sink quantities and feasible set are unchanged.
- Outputs/QC: `annual_resource_accounting_by_province.csv` gains six BECCS fields; `solution_qc.json` hard-checks capture, storage, net-carbon and total-captured reconstruction closure. The I/O contract, formula specification, parameter registry and risk audit were updated.
- Verification: 47/47 tests PASS. `outputs/2030_1h_v0722_beccs_mass_balance` is `OPTIMAL + solution_qc=PASS`; all four new residuals are zero and the result manifest passes. Parameter audit has 22 PASS / 0 WARN / 0 HARD_FAIL and six remaining open/scenario risks.
- Unresolved/next action: make CISPO/adapted parameter scenarios explicit for 40/60-year nuclear lifetime, 5/15% capacity margin and the 3.5 s reference inertia with tolerance; then address CapEx/fuel trajectories and separate line/substation annualization. Do not infer a nonzero BECCS lifecycle factor without new evidence.

### v0.9.3 - 2026-07-22 - diagnostic sensitivity suite interface validated

- Git implementation: `c91828a` (`feat: add diagnostic sensitivity suite runner`), based on accepted fixed-server handoff commit `0d44616`. The fixed server remains clean and idle at `6ed943a`; this runner has not been deployed and no server checkout/output was changed.
- Scope: added a diagnostic-only catalog runner with explicit `--diagnostic-hours`, isolated per-scenario state roots, catalog/config SHA256 identity, refusal of planned-not-runnable scenarios, non-empty-root protection, identity-safe `--resume`, immutable prior-report history and timestamped wrapper logs. Full-year execution is intentionally unsupported by this wrapper.
- Changed files: `scripts/run_cispo_sensitivity_suite.py`, `tests/test_sensitivity_suite.py` and `config/README.md`; this handoff milestone additionally updates `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. User-owned `supplementary_materials/**` changes were not modified, staged or committed.
- Verification: 45/45 local regression tests PASS. Real 1h output `outputs/sensitivity_suite_1h_v0722_interface` contains three independent Base/V1/V2G four-year chains; all 12 cases are `OPTIMAL + solution_qc=PASS`, all hard checks and result manifests pass, and scenario boundaries are correct. Suite `--resume` returns all cases as accepted without re-solving and preserves the prior report with SHA256 `2140efc5ac4cbb4e9dedbaf4e1d8f43593c05132d638e08dccc1526b5da63766`.
- Scientific boundary: no flexibility parameters, costs, objectives, constraints, units, spatial/temporal resolution or state-transition rules changed. The 1h suite is interface/identity engineering evidence only, not a sensitivity result.
- Unresolved/next action: calibrate evidence-backed building and EV parameter envelopes before adding runnable low/base/high cases. Keep complementarity/cost-relaxation cases planned-not-runnable until their formulation is frozen. Any server deployment must use a new small-gate root; fixed-server 744h/8760h and paid cloud 8760h remain prohibited without the required gates and authorization.

### v0.9.2 - 2026-07-22 - fixed-server 168h flexibility chain accepted

- Git/server identity: before this documentation update, local and pushed HEAD was `d00d1fb`; fixed-server checkout was clean at model commit `6ed943a`. No server checkout change occurred during the run or audit, and PID `1708266` is no longer active.
- Output: `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`; original sequence `PASS`, four years `ACCEPTED`, wall time 1:06:54, peak RSS 4,040,256 KiB, swap zero and wrapper exit status 0.
- Solve/QC evidence: 2030/2040/2050/2060 are all `OPTIMAL + solution_qc=PASS`; runtimes 705.49/672.16/994.41/1181.26 s; all hard checks pass. Maximum heating/cooling/EV V1G daily-energy residual over all years is `8.17e-13 GWh`, with zero simultaneous up/down province-hours.
- Integrity/state evidence: each year has a closed 59-file result manifest; scenario IDs agree across solve/scope/scenario manifests; all input manifests record SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`; `capacity_cohorts_v2` state inputs follow 2030 -> 2040 -> 2050 -> 2060 and remain `TEST_ONLY_TRUNCATED_HORIZON`.
- Resume evidence: a fresh `--resume` audit at 2026-07-22 16:05 CST returned sequence `PASS` with four `RESUMED_ACCEPTED` records and no re-solve.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; user-owned `supplementary_materials/**` changes were not modified or staged.
- Unresolved/next action: formalize the sensitivity-case registry/runner and calibrate building/EV flexibility envelopes before scientific interpretation. Keep Base disabled, keep V2G separate, and do not start fixed-server 744h/8760h or paid cloud 8760h without the required gates and explicit authorization.

### v0.9.1 - 2026-07-22 - fixed-server flexibility deployment and gates

- Deployment: fixed-server checkout fast-forwarded cleanly from `b6ca42d` to `6ed943a`; no model process was active during deployment, and existing data/results were not modified. The previous handoff shorthand is corrected: `b6ca42d` was the actual checkout for the Base 168h gate, while `0c1eaf2` was its model implementation baseline.
- Base acceptance: the four-year 168h Base chain completed in 1:08:40 with peak RSS 4,116,892 KiB and zero swap. Every year is `OPTIMAL + solution_qc=PASS + accepted state`; all four result manifests and the immediate resume audit pass.
- Flexibility acceptance: server regression tests pass 42/42. The four-year 24h `flexible_load_v1` chain completed in 6:32 with peak RSS 946,804 KiB and zero swap; all years and the immediate resume audit pass, scenario hashes are identical, daily load-shift conservation closes below `6.44e-13 GWh`, and simultaneous up/down counts are zero.
- Active task: four-year 168h `flexible_load_v1` chain is running under PID `1708266` in `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`.
- Exact next action: monitor the active 168h flexibility chain, validate its four solve/QC/result manifests and resume identity, then calibrate the illustrative flexibility envelopes before any cloud 8760h flexibility case. Do not launch fixed-server 744h/8760h.

### v0.9.0 - 2026-07-22 - modular load flexibility and scenario contract

- Git implementation: commit `6ed943a` (`feat: add modular demand flexibility scenarios`) is pushed to `origin/codex/cispo-2030-full-lp` but not yet deployed, so the fixed-server 168h Base sequence remains an uncontaminated `0c1eaf2` gate.
- Scope: retained the four existing load components in `ModelData`; hard-failed component nonclosure; added recursive, checksummed v1 scenario overrides; implemented daily-conserving heating/cooling and EV V1G shifting plus optional daily-cyclic V2G; routed effective load into hourly balance/reserve/inertia and annual load-center closure while retaining Base peak for capacity margin; added throughput/degradation costs, outputs, QC, scenario-safe resume and sequence aggregation.
- Changed files: `cispo_model/{config,data,flexible_load,io_contract,load_center,monolithic,preflight,result_summary,solution_export}.py`, `config/{optimization_2030,model_input_files}.json`, `config/scenarios/*`, run entrypoints, tests, the model/I/O specifications and new parameter/scenario documentation.
- Verification: 42/42 tests PASS; parameter audit 11,681 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; Base 1h, V1 24h and V2G 24h all `OPTIMAL + solution_qc=PASS`; all three manifests validate. V1/V2G detailed closure and scale evidence is in the current snapshot.
- Unresolved: the current flexibility values are illustrative and need physical calibration; complementarity point/province/national and integrated-realistic entries are explicitly catalogued as planned-not-runnable; no 168h flexibility chain or cloud deployment has been performed.
- Exact next action: finish and audit the active server Base 168h chain; then push/deploy `6ed943a`, run fixed-server 24h/168h flexibility gates, and only after those pass stage the same commit/data hashes on the cloud. Do not launch a paid flexibility 8760h case before calibration and gates.

### v0.8.1 - 2026-07-22 - fixed-server four-year 24h chain passed

- Git/model/data baseline: implementation `0c1eaf2`, documentation/encoding HEAD `b6ca42d`, V0721 additive data root.
- Output: `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state`; initial sequence `PASS`, immediate `--resume` sequence `PASS`, four `RESUMED_ACCEPTED` records.
- Per-year result: 2030/2040/2050/2060 all `OPTIMAL + solution_qc=PASS`; solver runtimes 49.424/46.489/45.976/45.735 s; objective values 2,024,956.703 / 2,073,142.226 / 2,232,353.866 / 2,470,806.369 million CNY. These are truncated-horizon engineering values and have no scientific cost interpretation.
- Resource evidence: sequence wall time 6:03.31, maximum RSS 921,792 KiB, exit status 0 and no swap by the sequence process tree.
- Next gate: launched the 168h four-year diagnostic chain as PID `1348292` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state`. Audit all four years and resume identity after completion; do not start cloud 8760h meanwhile.

### v0.8.0 - 2026-07-22 - fuel accounting and safe sequential diagnostic chain

- Git implementation: `0c1eaf2` (`fix: harden sequential planning and fuel accounting`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the fixed server.
- Scope: connected existing province-level biomass prices to `bio/bioccs` fuel costs and the objective; added strict fuel-table coverage/range checks; upgraded state to `capacity_cohorts_v2`; validated source QC/solve/summary/result-manifest hashes and source year/use; isolated test-only diagnostic states from 8760h production; prevented nonempty-directory overwrite, nonzero-return acceptance and stale/mixed resume chains; bounded thermal retrofits by future surviving source capacity; cached Gurobi solution arrays during cohort export; added a parameter audit and deployment/paper case roadmaps.
- Changed files: `cispo_model/{config,data,io_contract,master,monolithic,planning_state}.py`, `config/optimization_2030.json`, `scripts/{build_cispo_data_package,rebuild_fuel_price_tables,audit_model_parameters,run_cispo_2030_full_year,run_cispo_planning_sequence}.py`, three regression tests, `FINAL_DEPLOYMENT_WORKFLOW_20260721.md` and `PAPER_CASE_ROADMAP_20260721.md`.
- Data: new additive fixed-server root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`; rebuilt fuel-table SHA256 values are recorded in the current snapshot. The previous V0719 root was not overwritten.
- Local verification: 37/37 tests PASS; parameter audit 11,658 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; real four-year 1h diagnostic sequence PASS; all years `OPTIMAL + solution_qc=PASS`; immediate `--resume` revalidation PASS. Caching `vre_new.X` reduced a 1h result/state export from an interrupted >5 min path to about 40 s total wall time.
- Server verification: HEAD `0c1eaf2`; parameter audit matches local counts; 37/37 tests PASS; V0721 24h four-year diagnostic sequence launched as PID `1314704`.
- Unresolved: BECCS gross/captured/stored/lifecycle/net carbon separation; 40/60-year nuclear lifetime, 5/15% capacity margin and 3.0/3.5 s inertia scenarios; CapEx and fuel-price low/base/high trajectories; decision-dependent versus fixed cost decomposition before complementarity epsilon constraints; formal multi-weather-year hydrology/robustness.
- Exact next action: audit the server 24h chain; if four years and resume identity pass, launch a new 168h four-year chain. Only after both pass should the cloud receive the new code/data package and run a single 2030 8760h production case.

### v0.7.4 - 2026-07-21 - second proxy/WLS smoke passed; thread limit flagged

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975741` to `amd_a8_384`, 1 node, 1 CPU, 2 GB and 5 minutes; no CISPO command and no exclusive-node request.
- Proxy/license evidence: node `m4cl2501.para.bscc` used the engineer-provided proxy `172.16.110.3:8888`; the connectivity check returned HTTP 302, WLS authentication succeeded, and the two-variable LP returned `OPTIMAL` with `GUROBI_SMOKE_PASS`. `sacct` reports `COMPLETED`, exit code `0`.
- Resource caveat: despite the one-CPU request, the smoke log reported Gurobi could use up to 32 threads. Production scripts must set Gurobi `Threads` no higher than `--cpus-per-task` and verify the effective thread count before paid runs.
- Unresolved/next action: stage only the validated input package, verify SHA256 and output permissions, run cloud 24h/168h gates with explicit resources, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.3 - 2026-07-21 - compute-node proxy/WLS smoke passed

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975724` to partition `amd_m8_768-a`, 1 node, 2 CPUs, 8 GiB, 5 minutes; no CISPO command and no exclusive-node request.
- Compute evidence: node `m4cl0208.para.bscc`, Python 3.10.20, `gurobipy`/Gurobi 13.0.2. Partition inventory reports 192 CPUs and 768,000 MB per node; this resource class is adequate for the current 8760 build/factor-memory estimate, subject to an explicit per-job memory request.
- Proxy evidence: correctly encoded lower- and upper-case proxy variables made `token.gurobi.com` return HTTP 405 through remote IP `172.16.110.3`; WLS authentication then solved the tiny LP with `GUROBI_STATUS=2` and objective `1.0`. A PyPI request transferred data but did not finish within 30 seconds, so proxy throughput remains unbenchmarked for multi-GB data transfer.
- Configuration defect: the account `.bashrc` lines contain non-breaking spaces after `export`, producing `No such file or directory` on login and job startup. No configuration was modified automatically; correct proxy exports are now required inside every Slurm script.
- Unresolved/next action: transfer the tracked code and versioned model-ready/CF/hydrology data to a new cloud directory, verify SHA256 and shared-file permissions, run cloud 24h and 168h CISPO gates, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.2 - 2026-07-21 - WLS recognized; compute-node DNS/egress gate failed

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: after the engineer's WLS reinstallation, submitted only job `3975474` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute/license evidence: node `m4cl1306.para.bscc` loaded `gurobipy310`/Gurobi 13.0.2 and recognized WLS parameters from the new private license path. `Env.start()` then failed with `Could not resolve host: token.gurobi.com`; `sacct` reports `FAILED`, exit code `1`.
- Unresolved/next action: the WLS credentials are being parsed, but the compute node cannot resolve/reach the WLS endpoint. Ask the cluster engineer to fix compute-node DNS/egress or provide the required proxy/allowlist, and protect the WLS file with mode `600`. Do not resubmit paid jobs or launch CISPO until one smoke test returns `GUROBI_SMOKE_PASS`/`OPTIMAL`.

### v0.7.1 - 2026-07-21 - Compute-node Gurobi call reached license gate

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: submitted only job `3974169` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute evidence: node `m4cm2307.para.bscc` loaded `/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310`, imported `gurobipy` 13.0.2 and saw `GRB_LICENSE_FILE`.
- License evidence: the two-variable LP failed at `Env.start()` with `HostID mismatch`; `sacct` reports `FAILED`, exit code `1`. The Python/Gurobi installation path is therefore reachable, but the current license is not valid for the allocated compute node.
- Unresolved/next action: do not launch CISPO or repeatedly resubmit paid smoke jobs. Obtain a compute-node-compatible academic named-user reactivation or Academic WLS/site license, then rerun one equivalent smoke test requiring `GUROBI_SMOKE_PASS`/`OPTIMAL` before any data staging or 8760h preflight.

### v0.7.0 - 2026-07-20 - open-source I/O contract, diagnostics and verified server gate

- Git implementation: `b40900a` (`feat: formalize model I/O and diagnostics`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the clean fixed-server checkout.
- Scope: added an open-source project `README.md`; formal input/output contract and data dictionary; immutable configuration, environment and input provenance; scope-aware summaries; complete dispatch, reserve, adequacy, resource, marginal-price and shadow-price exports; pickle-free NPZ identifiers; stronger model/state acceptance checks; and sequence-wide aggregation. Constraint handles and diagnostics were added without changing the LP feasible set.
- Main changed files: `README.md`, `MODEL_IO_CONTRACT.md`, `MODEL_744_SERVER_RUN_AUDIT_20260720.md`, `cispo_model/io_contract.py`, `solution_export.py`, `result_summary.py`, `planning_state.py`, `master.py`, `monolithic.py`, run/sequence scripts, input contract and tests.
- Local evidence: 34/34 unit tests PASS; 139/139 data-package checks PASS; local 24h output `outputs/2030_24h_v0720_io_contract_rerun3` is `OPTIMAL/QC PASS`, all 27 hard checks pass, manifest validation is clean, dual export is available and complementarity diagnostics are zero.
- Server evidence: 34/34 unit tests and 139/139 smoke checks PASS. `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL/QC PASS` with 43.65 s solver time and 0.838 GiB peak RSS; manifest `(True, [])`; output catalog 50 rows; data dictionary 493 rows; hourly prices 744 rows; annual shadow prices 3,366 rows; all NPZ files are safe under `allow_pickle=False`.
- 744h audit: the old `5a9f4ab` engineering gate remains solver-valid, but its wrapper-owned `run.stdout` and `run.time` invalidate two old manifest entries. V0720 excludes runtime-managed wrapper files from the scientific manifest and validates the manifest before accepting sequence output.
- Architecture decision: retain sequential 2030/2040/2050/2060 full-year optimization as the production default. It requires four solves and is myopic, but keeps only one 8760h LP resident at a time; a joint four-year perfect-foresight model would multiply time-dependent matrix blocks and peak memory and is reserved for reduced-scale research experiments.
- Unresolved/next action: do not repeat 744h on the fixed server. Complete cloud compute-node/license/data staging, run 24h/168h gates there, then use the 8760h output contract for a single production case. Existing VRE retirement, formal climatological hydrology, cascade lag warnings, PHS hydraulic pairing and long-term sensitivity assumptions remain explicit research items.

### v0.6.4 - 2026-07-20 - Gurobi Linux package staged; license transfer held

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, solver environment or remote job state was changed.
- Scope: downloaded the official Gurobi 13.0.2 Linux x86-64 package, verified the official MD5 and uploaded only the installation archive to the user-private cloud staging directory. No license file was transferred.
- Artifact evidence: `/publicfs01/fs1-a8/home/a8s001819/staging/gurobi1302/gurobi13.0.2_linux64.tar.gz`, 64,798,273 bytes, MD5 `f12dcad337ae1d8f9b8c2b3f51b92bb5`, SHA256 `cffd4ee3c1990294e80446626bd1772045e420d7c34c379839b6acca16f0a23b`; local and remote hashes match.
- License decision: the user-provided email identifies an academic named-user license. Because Gurobi named-user licenses are machine-scoped and Slurm may dispatch jobs across multiple compute nodes, copying a license generated on another server was not assumed valid and was deliberately not performed. The cloud document records `grbgetkey`/WLS decision rules without storing key codes or license contents.
- Unresolved/next action: after explicit approval, use a small scheduler allocation to determine the compute-node target and Gurobi installation path, then choose a compliant named-user reactivation or Academic WLS/site license. Do not install or start 8760h before this check.

### v0.6.3 - 2026-07-20 - BSCC-A8 manual reconciliation and cloud usage document

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: interpreted the user-provided official BSCC-A8 manual screenshot and created `supplementary_materials/云服务器使用规范_BSCC-A8.md` with the documented Modules/Slurm/compiler workflow, current SSH aliases, login-node boundary, storage layout, cost gate and CISPO-specific 8760h stop rules.
- Reconciliation evidence: the manual is dated 2024-08-26 and refers to the older `amd_a8_768` queue; live Slurm audit on `ln301.para.bscc` reports `amd_m8_768-a` as the default partition and `amd_a8_384` as the second active partition. The document marks live values as authoritative instead of copying stale queue names.
- Safety evidence: no remote file was written, no module or package was installed, no Slurm allocation was requested and no job was submitted. The verified module initializer `/public1/soft/modules/module.sh` is documented, while current compute-node Gurobi availability remains explicitly unverified.
- Unresolved/next action: only after user approval, run a small scheduler allocation to inventory compute-node Python/Gurobi/license and perform a smoke test; do not launch 8760h production directly from the login node.

### v0.6.2 - 2026-07-20 - ParaCloud Slurm login-node audit

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: performed a read-only audit after public-key login to identify the safe cloud execution path. No `sbatch`, `srun`, package installation, environment activation persisted, file transfer or model execution was performed.
- Verified cluster: Rocky Linux 8.10 login host `ln301.para.bscc`; Slurm 23.11.9, cluster `bscc-m8`, `select/cons_tres` with `CR_CORE_MEMORY`; account `bscc-a8`, QoS `normal`, association output showing a 10-job submission limit.
- Verified partitions: default `amd_m8_768-a` has 194 nodes, 192 CPUs/node and 768000 MB/node with 4000 MB/CPU default; `amd_a8_384` has 103 nodes, 128 CPUs/node and 384000+ MB/node with 3000 MB/CPU default. Both partitions are `UP` and allow all accounts/QoS at the partition level.
- Environment evidence: login host has 64 logical CPUs and about 376 GiB RAM; `/publicfs01` has about 3.1 PB free. System Python is legacy; shared Miniforge `/public1/soft/miniforge/24.11` exposes `base`, `py-moose` and `toga2`, but none of the checked environments imports `gurobipy` or `torch`. This does not prove compute-node software absence.
- Safety conclusion/next action: treat `ln301` as login-only. Before any paid 8760h work, create an explicit Slurm script, request a small approved allocation to inventory compute-node Python/Gurobi/license and run a smoke check, then require the full-year preflight, memory gate and cost confirmation. Do not install packages or run the long solve from the login node.

### v0.6.1 - 2026-07-20 - ParaCloud public-key authentication verified

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: corrected the ParaCloud SSH aliases to use the normal public-key-first OpenSSH authentication order, then verified both port 22 and port 2222 end to end with a read-only remote command.
- Verification evidence: `paracloud-bscc-a8` and `paracloud-bscc-a8-backup` authenticated with the existing local public key and returned `CODEX_CLOUD_SSH_OK`, remote host `ln301.para.bscc`, account `a8s001819` and home `/publicfs01/fs1-a8/home/a8s001819`; both commands exited with status 0.
- Security evidence: no password was entered, stored or logged; no private-key content was read or copied. The earlier password prompt was caused by the temporary alias preference and has been removed.
- Unresolved/next action: inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi, data paths and job accounting on the cloud login node. Do not launch a paid 8760h solve until the cost gate and full-year preflight requirements in the selection policy pass.

### v0.6.0 - 2026-07-20 - ParaCloud route selection and cost-gated SSH configuration

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: classified the two server targets and configured local SSH aliases for the separate ParaCloud BSCC-A8 endpoint. Existing `national-model-server` configuration was preserved unchanged.
- Changed files/state: repository handoff updated; user SSH config `C:\Users\ZZ\.ssh\config` gained `paracloud-bscc-a8` on port 22 and `paracloud-bscc-a8-backup` on port 2222; memory note `20260720-paracloud-server-routing.md` records non-secret routing and cost-gate metadata.
- Verification evidence: DNS resolved both IPv4 backends; TCP checks passed on ports 22, 2222 and 8443 via Ethernet source `124.16.2.171`. SSH banner/auth checks succeeded on ports 22 and 2222 (`ParaCloud`, `password,publickey`); 8443 and IPv6 port 22 reset before the banner. `ssh -G` confirmed both aliases resolve to the intended compound user and ports.
- Selection rule: use `national-model-server` for local work and the 744h engineering gate; use ParaCloud only for explicitly authorized, scheduler-backed 8760h production after full-year preflight, memory/resource/license validation and cost confirmation. No cloud authentication or paid job was started.
- Unresolved/next action: authenticate through `paracloud-bscc-a8`; inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi and data paths; only then prepare a checksum-verified production transfer and launch decision.

### v0.5.9 - 2026-07-20 - ParaCloud candidate SSH pre-authentication check

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or server process was changed.
- Scope: performed a read-only connectivity check for the separate ParaCloud/BSCC-A8 candidate endpoint intended for possible future 8760h computation. The existing validated `national-model-server` target and its SSH configuration were not modified.
- Changed file: `CODEX_HANDOFF.md` only, to preserve this verified server milestone without credentials.
- Verification evidence: the hostname resolved to two IPv4 backends; `Test-NetConnection` passed on TCP port `8443` for both via the workstation Ethernet source address. OpenSSH parsed the compound login user correctly, but `ssh -vv`, `ssh-keyscan` and raw banner checks received no SSH banner and both backends reset or timed out before key exchange.
- Security evidence: no password, private-key content, activation key or license content was read, logged or written. Password validity was not tested because the connection never reached authentication.
- Unresolved/next action: verify in ParaCloud that the BSCC-A8 direct-connection mapping is active and that the workstation source IP is permitted, then rerun the SSH banner/authentication check. After successful login, inventory scheduler, CPU/RAM/storage, quotas, environment and Gurobi license before transferring data or launching any 744h/8760h job.

### v0.5.8 - 2026-07-19 - V0719 deployed, 24h gate passed, 8760 memory gate blocked

- Git/server state: local commits `451b1c0`, `c8db9be` and `bc83663` were pushed to `origin/codex/cispo-2030-full-lp`; server checkout `/data/zz2/National_model/repo` was fast-forwarded to `bc83663`.
- Scope: deployed V0719 code and data contract to a new additive data root, fixed server smoke-test path resolution for CF and hydrology files, and ran server validation. No old data root or old 744h output was overwritten.
- Data root: `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`; generated `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`; added missing smoke/QC support files from canonical `model_ready`.
- Validation evidence: server smoke `139/139 PASS`, server unit tests `32/32 PASS`, readiness `PASS` with full Gurobi license and raw-GRFR SHA256 verification.
- Solve evidence: server 24h V0719 output `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL/QC PASS`; model size 341,312 variables / 261,280 constraints / 1,768,957 nonzeros; Gurobi runtime 48.96 s; peak RSS 0.841 GiB; zero nuclear, biomass+BECCS, storage and transmission-direction hard-check violations.
- 8760 evidence: direct full-year solve was not launched. Full-year preflight `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported `memory_gate_pass=false`, available memory `73.15 GiB` versus required `96.0 GiB`; estimated full-year scale 40,911,296 variables / 67,603,283 constraints / 520,920,489 nonzeros.
- Unresolved/next action: wait for memory pressure to clear or use a high-memory node. On this host, run V0719 168h and 744h gates before any full-year production solve. If overriding for an exploratory full-year build, require at least 96 GiB available RAM and start with build-only/preflight evidence, not optimize.

### v0.5.7 - 2026-07-19 - corrected 744h sparse gate completed

- Git/server state: server checkout HEAD `5a9f4ab`; local V0719 capacity-bound/DC active-index corrections remain an uncommitted working tree on local HEAD `f84143a` and were not used by this server run.
- Scope: verified completion of `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`; no model code, data root or server process was changed.
- Verification evidence: `solve_report.json` reports `OPTIMAL`, `solution_count=1`, objective `2,196,413.3453 million CNY`, runtime `16,245.79 s`, barrier iterations `214`, simplex/crossover iterations `1,468,988`, peak process-tree RSS `21.979 GiB`, and model size 3,955,064 variables / 5,919,746 constraints / 43,707,940 nonzeros. `/usr/bin/time` reports wall time 4:37:02, maximum RSS 23,469,440 kB and exit status 0.
- QC evidence: `solution_qc.json` reports `PASS`, maximum power-balance residual `3.64e-10 GW`, zero line-capacity violation, zero bidirectional interprovincial edge-hours, zero DC reverse flow across 363 DC corridors, zero biomass/carbon/CO2 sink violations and all hard checks true.
- Unresolved/next action: preserve this as the completed pre-V0719 sparse gate. Do not start 8760 production on this older scientific boundary. Commit/push V0719, build a new versioned data root with the three new capacity-bound tables, then rerun readiness, tests, smoke, 24h, 168h and corrected 744h before any 8760 build-only or solve.

### v0.5.6 - 2026-07-19 - V0719 capacity bounds and DC active-index correction

- Git state: branch `codex/cispo-2030-full-lp`, local HEAD `f84143a`, implementation base `5a9f4ab`; V0719 changes are intentionally left uncommitted pending user review. Server HEAD remains `5a9f4ab`.
- Scope: implemented the four issues identified in `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md`: nuclear capacity upper, shared biomass+BECCS capacity upper, 2030 battery exogenous floor and removal of DC reverse fixed-zero variables.
- Main changed files: `config/capacity_bounds_v0719.json`, `scripts/build_v0719_capacity_bounds.py`, data/config loaders, `cispo_model/master.py`, `monolithic.py`, `load_center.py`, `solution_export.py`, `result_summary.py`, `preflight.py`, model-input contract/config, data-package builder/smoke tests, unit tests, model specification and V0719 report.
- Generated inputs: `thermal/nuclear_capacity_upper_by_year.csv` (124 rows), `biomass/capacity_upper_by_province_year.csv` (124 rows), `storage/battery_capacity_floor_by_province_year.csv` (124 rows). These are generated under the configured data root and remain outside Git with the rest of `data/`.
- Scientific boundaries: nuclear national upper `110/205/300/300 GW`; shared `bio+bioccs` upper uses `thermcal×0.35/(3600×6132)` with an inherited-floor safeguard that triggers only in Shanghai; 2030 battery floor totals 65.85 GW after Mengdong/Mengxi merge and is zero as an exogenous boundary from 2040 onward.
- Exact sparsification: reverse variables now exist only for 48 AC corridors; all 411 corridors retain forward variables. Dense 411-row reverse output is reconstructed with DC rows zero, preserving file/API compatibility. Full-year variable reduction is 3,179,880.
- Commands/evidence: `C:\Users\ZZ\.conda\envs\RL\python.exe scripts\build_v0719_capacity_bounds.py`; `... -m unittest discover -s tests -q` passed 32/32 in 17.62 s; `... scripts\smoke_test_data_package.py` passed 139/139; strict 24h solve at `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL/QC PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, solver 39.79 s and peak RSS 0.702 GiB.
- Validation details: all new capacity-bound violations are zero; DC reverse flow and AC simultaneous bidirectionality are zero; maximum power-balance residual `7.43e-12 GW`. The first too-short timeout output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse` is retained as an interrupted trace.
- Server evidence: at 2026-07-19 16:42 Asia/Shanghai, `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remained active under PID `3344086`, elapsed 01:35:08 at barrier iteration 107, with no solve/QC reports. It uses the old versioned data root and was not modified.
- Unresolved/next action: commit/push only after review; after the old 744h is preserved, create a new versioned data root, generate the three bound tables and pass server readiness, 32 tests, 139 smoke checks, 24h, 168h and corrected 744h. Do not run 8760 yet. Long-term nuclear, updated biomass, separated battery GW/GWh, formal multi-year hydrology and CSP remain scenario/data work, not hidden hard constraints.

### v0.5.5 - 2026-07-19 - annual-network sparse cleanup and corrected 168h gate

- Git implementation: `5a9f4ab` (`Reduce annual network matrix duplication`).
- Scope/changed files: `cispo_model/load_center.py` reuses province sent/received accounts in net-import closure, removes the implied province reservoir-generation closure and adds unique route checks; `cispo_model/preflight.py` corrects variable-block accounting and recalibrates nonzeros; `config/optimization_2030.json` raises the full-year RAM gate to 96 GiB and removes unused LP-inapplicable settings; `tests/test_model_foundation.py` adds scale/sparsity/gate regressions.
- Verification: local 29/29 tests; local strict 24h `OPTIMAL/QC PASS`; server readiness/raw-GRFR/full-license PASS; server 29/29 tests; server strict 168h `OPTIMAL/QC PASS` in 666.45 s with 3.910 GiB peak RSS.
- Scale evidence: 168h nonzeros decreased from 10,480,639 to 10,100,058 while variables remained 1,071,032. Direct availability-variable removal was rejected after a 24h build increased nonzeros from about 1.87m to 2.23m.
- Server command/output: `scripts/run_cispo_2030_full_year.py --diagnostic-hours 168 --output-dir /data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`.
- Unresolved/next action: PID `3344086`/child `3344087` is running the strict corrected 744h gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`. Only after `OPTIMAL/QC PASS` and a fresh >=96 GiB memory check may 8760h build-only start; build success still does not authorize solve.

### v0.5.4 - 2026-07-19 - full-year solvability and cross-year completeness audit

- Git audit commit: `ab9dfe8` (`docs: audit full-year solvability and state transfer`); implementation remains `1b6da28`, documentation baseline before this entry was `f22b9cf`.
- Scope: decomposed current 24h/168h model size by VRE, thermal RUC, storage, hydropower, transmission, balance/security, annual load-center and carbon blocks; recalibrated 8760 nonzeros/static build memory; audited 744h factorization/crossover; reviewed Gurobi parameters and every cross-year capacity cohort class.
- Changed files: `MODEL_SOLVABILITY_AUDIT_20260719.md`, followed by continuity updates in `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`.
- Commands/evidence: current 24h/168h `scripts/audit_model_numerics.py --skip-full-max-cf`; live `ssh national-model-server` HEAD/resource check; rejected 744h `solve_report.json` and `gurobi.log`; two current-model 24h parameter diagnostics.
- Findings: revised 8760 scale is about 44.09m variables, 68.19m constraints and 515-524m nonzeros; calibrated build peak is about 58 GiB, but linearly extrapolated barrier factor memory alone is about 118 GB. Direct 8760 solve on 125 GiB is high risk.
- Parameter result: `Crossover=0` failed current hard QC; a default feasibility/optimality tolerance plus `BarConvTol=1e-7` candidate saved about 7% at 24h and remains diagnostic-only.
- Cross-year result: all current capacity decision classes are transferred through checksummed active cohorts, including VRE, thermal/nuclear, hydro, battery/PHS, inter-/intra-provincial transmission, DAC, spur and trunk. Remaining physical limitations are myopic foresight, missing existing-VRE age retirement, plant-level thermal retrofit remaining life, additive nuclear pipeline interpretation and province-level fixed-duration PHS.
- Unresolved/next action: implement exact availability/load-center sparse reformulations, correct scale reporting, pass local gates, then rerun corrected 744h when shared memory pressure clears. Require at least 96 GiB available RAM for 8760 build-only; do not optimize until its true memory evidence is reviewed.

### v0.5.3 - 2026-07-19 - corrected server 24h transmission gate

- Git implementation: `1b6da28`; synchronized server documentation HEAD includes `c4cfddd` or later.
- Server tests: 26/26 PASS in 22.24 s under `/home/zz2/.local/envs/cispo-2030`.
- Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Solver: 350,024 variables, 261,280 constraints and 1,867,007 nonzeros; Gurobi 13.0.2 `OPTIMAL` in 43.88 s; peak process-tree RSS 0.845 GiB.
- QC: power-balance residual `1.46e-11 GW`; reservoir-transition residual `7.63e-06 m3`; zero AC bidirectional edge-hours; zero DC reverse flow on 363 DC edges; all hard checks PASS.
- Output integrity: every scientific manifest file matched size and SHA256; runtime-owned stdout/stderr/PID files are explicitly excluded.
- Resource stop: only about 32 GiB RAM was available and all 21 GiB swap was occupied by shared workloads. No corrected 744h or 8760h process was started.
- Next action: wait for shared memory pressure to clear, require at least 64 GiB available RAM, then launch a new versioned corrected 744h CPU barrier gate.

### v0.5.2 - 2026-07-19 - CISPO transmission alignment after 744h result audit

- Git implementation: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- Rejected baseline: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu` reached `OPTIMAL` in 20,118.58 s with 22.141 GiB peak RSS, but contained 3,358 material bidirectional edge-hours, 3,909.04 GWh summed opposing minimum flow and a 4.393 GW maximum opposing minimum flow.
- Root causes: the model configured `0.001 yuan/MWh` instead of CISPO's `0.001 yuan/kWh = 1 yuan/MWh`; DC reverse flow was not fixed to zero; the added annual load-center layer closed gross sent/received energy and rewarded artificial loops.
- Fix: AC keeps `f_forward + f_reverse <= capacity`; DC reverse UB is zero; flow cost is 1 yuan/MWh; the annual load-center layer closes province net exchange; AC bidirectionality and DC reverse flow are hard QC failures; shell-managed files are excluded from the scientific SHA256 manifest.
- Local verification: tests 26/26 PASS; corrected 24h model 350,024 variables, 261,280 constraints and 1,867,006 nonzeros; `OPTIMAL` in 40.02 s; peak RSS 0.700 GiB; power-balance residual `5.35e-12 GW`; zero AC bidirectionality; zero DC reverse flow across 363 DC edges; manifest mismatches zero.
- Detailed evidence: `TRANSMISSION_FLOW_AUDIT_20260719.md`.
- Next action: deploy `1b6da28`, run server tests and corrected 24h gate, then defer the corrected 744h until shared-server available RAM is safe.

### v0.5.1 - 2026-07-19 - server synchronization and replacement 744h launch

- Git baseline: branch `codex/cispo-2030-full-lp`, server checkout HEAD `827b37f`, containing implementation commit `2a0ee99`.
- Scope: restored live SSH through the configured bound-source alias; fast-forwarded the clean server checkout; uploaded and SHA256-verified versioned model/hydrology bundles; ran readiness, regression and 24h solve gates; launched the replacement 744h CPU barrier gate.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; model source files were not changed in this milestone.
- Verification: readiness PASS with zero hard failures; raw GRFR 2/2 hashes PASS; tests 24/24 PASS; 24h `OPTIMAL/QC PASS` in 60.53 s with 0.851 GiB peak RSS.
- Server output: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`, PID `3778049`; initial process check passed and `stderr` was empty.
- Unresolved: the 744h result is still pending; formal climatological P30 and 4 low-correlation/18 max-bound cascade-lag edges remain input limitations. Shared server load leaves only about 49 GiB available, below the 8760h gate.
- Next action: inspect the 744h reports after process exit; if and only if `OPTIMAL/QC PASS` and RAM is at least 64 GiB, run the 8760h build-only gate.

### v0.5.0 - 2026-07-18 - sequential planning, exact sparse reformulation and complete outputs

- Git implementation baseline: `2a0ee99` (`feat: add sequential planning and stabilize full-year LP`).
- Scope: implemented checksummed 2030/2040/2050/2060 capacity-cohort transfer; added GHT 2026 province-level PHS floor/project upper; removed redundant ramp, storage reserve, reservoir generation, hydro inertia and operating-cost-account variables/equalities using exact linear reformulations; completed compact outputs/SVG/manifest; reduced model input tables to an explicit 28-table contract.
- Main changed files: `cispo_model/config.py`, `data.py`, `master.py`, `monolithic.py`, `planning_state.py`, `preflight.py`, `result_summary.py`; `config/model_data_config.json`, `optimization_2030.json`, `model_input_files.json`; run/build/readiness/smoke scripts and sequence/tests.
- Local validation: AST 38 PASS; unit tests 24/24 PASS including real solution-to-cohort mapping; data-package smoke 124/124 PASS; 2030 and 2040 full-year preflight PASS; four-year sequence dry-run PASS; final 24h solve `OPTIMAL/QC PASS` in 58.79 s with 0.698 GiB peak RSS; nonempty 2040 state diagnostic `OPTIMAL/QC PASS`.
- Scale: full-year preflight estimates 44,090,772 variables, 67,603,314 constraints, 853,505,952 nonzeros and 46.62 GiB model memory. Local build is correctly blocked by the 64 GiB runtime gate.
- Server status: not deployed. SSH connected to TCP/22 but closed during key exchange on 2026-07-18, so server HEAD and old 744h status could not be verified.
- Transfer status: minimal code/data/hydrology archives and SHA256 manifest were prepared locally; Git push and server upload are blocked by the same SSH key-exchange closure.
- Unresolved: replacement 744h and 8760 build-only gates; formal multi-year P30; 4 low-correlation and 18 max-bound lag edges; plant-level thermal retrofit/retirement identity; CSP, thermal `f_on`, PHS hydraulic pairing and proxy network assumptions.
- Next action: restore SSH, verify old artifacts, deploy commit/data, pass readiness/tests/744h, then 8760 build-only before any production sequence.

### v0.4.1 - 2026-07-07 - P30 hydropower cleanup and GPU-PDHG isolation test

- Git implementation baseline and live server HEAD: `a8cd150` (`fix: switch hydropower to p30 proxy`).
- Scope: removed obsolete early block-boundary variables from `master.py`; switched conventional hydropower environmental flow from the single-year P10 proxy to the configured single-year P30 proxy; retained run-of-river as station-CF-weighted provincial hourly output variables; kept PHS as province-level storage; installed GPU-enabled Gurobi only in an isolated venv and tested PDHG.
- Main changed files: `.gitignore`, `config/model_data_config.json`, `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/hydro.py`, `cispo_model/master.py`, `scripts/build_cispo_data_package.py`, `scripts/check_server_readiness.py`, `scripts/prepare_server_bundle.py`, `tests/test_hydro_station_model.py`.
- Data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
- Validation: local AST PASS, local 19/19 unit tests PASS, data smoke test 118/118 PASS; server readiness PASS with raw-GRFR SHA256 verification; server 19/19 tests PASS; server 24h CPU P30 solve `OPTIMAL`, `solution_qc=PASS`, Gurobi `45.06 s`, peak RSS `0.879 GiB`.
- GPU result: isolated `gurobipy 13.0.2+cu129` environment successfully used `Start PDHG on GPU`, but the 24h P30 model was still iterating after about 600 s and was interrupted with no `solve_report.json`; standard CPU barrier remains the accepted solver route.
- Current run: P30-cleanup 744h CPU gate is running at `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu`, PID `863603`; build completed in `339.56 s` with peak RSS `5.336 GiB`, and Gurobi optimization is in progress.
- Unresolved: 744h gate final status not yet known; formal 1980-2019 climatological P30 remains future data work; low-correlation/max-bound cascade lag edges still need manual data review.
- Next action: monitor PID `863603`, then audit solve/QC outputs before any 8760h build or production solve.

### v0.4.0 - 2026-07-07 - LP numerical scaling repair and 168h server gate

- Git baseline and live server HEAD: `281f9c7` (`fix: stabilize hydropower LP numerics`).
- Scope: preserved and interrupted the failed old 744h run; audited every model block; applied mathematically equivalent reservoir flow/volume scaling; added numerical-audit and arbitrary diagnostic-hour tooling; exposed all server CPUs; expanded solver-quality reporting.
- Main changed files: `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/diagnostics.py`, `cispo_model/hydro.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `scripts/audit_model_numerics.py`, `scripts/run_cispo_2030_full_year.py`, `tests/test_hydro_station_model.py`.
- Validation: local 18/18 tests PASS; local 24h `OPTIMAL` and QC PASS in `59.66 s`; server 18/18 tests PASS; server 168h `OPTIMAL` and QC PASS in `675.56 s` with `4.061 GiB` peak RSS.
- CPU/GPU: `Threads=-1` exposes 96 logical processors; barrier uses 48 physical threads. Two RTX 4090 GPUs are compatible candidates for Gurobi GPU PDHG, but current installed build is CPU-only; any GPU test must use a separate `+cu` environment and `Method=6`, `PDHGGPU=1`.
- Unresolved: replacement scaled 744h run not yet started; no 8760h run is authorized before it passes. Full details are in `MODEL_SYSTEM_AUDIT_20260707.md`.
- Next action: run and audit `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade_numerics_scaled`.

### v0.3.1 - 2026-07-06 - cascade server deployment and 744h numerical gate in progress

- Git implementation baseline: `b3e6298`; server checkout HEAD verified as `7a2ca27`.
- Scope: transferred and verified versioned cascade model-ready/hydrology data, passed server readiness and 16 regression tests, passed the 744h preflight and completed the full 744h model build.
- Server data roots:
  - `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`
- Verification: readiness PASS with raw-GRFR SHA256 verification; cascade counts 142 nodes and 124 edges; 16/16 tests PASS; one-month preflight PASS; actual model build 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Numerical status: Gurobi emitted coefficient/RHS scale warnings, barrier restarted once and the solve entered a long crossover cleanup. At the recorded checkpoint the process was still active after about 5 h 59 min, with no final solve/QC report. This is not a passed optimization gate.
- Changed files in this handoff-only milestone: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`.
- Next action: preserve and audit the current run when it exits; if crossover does not finish acceptably, compare a separate `Crossover=0` diagnostic configuration without modifying model physics.

### v0.3.0 - 2026-07-06 - core mainstem hydropower cascade implementation

- Git baseline: `b3e6298` (`fix: add core hydropower cascade coupling`), based on prior server-validated commit `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: read and validated the Stage2 core-mainstem hydropower classification/cascade scaffold; generated model-ready cascade nodes/edges; estimated MERIT downstream travel lags by 2019 GRFR cross-correlation; replaced independent core-reservoir operation with local-inflow plus upstream turbine/spill delayed arrival; retained independent operation for non-core reservoirs.
- Main changed files in the implementation commit:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/smoke_test_data_package.py`
  - `cispo_model/data.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/preflight.py`
  - `cispo_model/solution_export.py`
  - `tests/test_hydro_station_model.py`
  - `cispo_full_lp_model_spec.md`
- Local generated data files:
  - `data/hydro/cascade_topology_nodes.csv`
  - `data/hydro/cascade_topology_edges.csv`
- Verification: Stage2-to-model mapping passed with 146/146 reservoir stations; cascade topology is acyclic; local data package QC has zero failures; smoke test passed 118/118 checks; local unit tests passed 16/16; one-month preflight passed; custom 24h monolithic build succeeded.
- Modeling note: the local implementation follows the user's requested core-mainstem cascade mode for conventional reservoir hydropower. It does not yet implement open-loop/closed-loop PHS hydraulic coupling because required pairing/source data are not present in the current data package.
- Unresolved items: 4 low-correlation lag edges and 18 max-bound lag edges require manual hydrological/topological review; formal multi-year environmental flow remains unavailable.
- Next action: synchronize the branch and transfer a new versioned data package to the server, then rerun server readiness plus 744h `one_month` optimization.

### v0.2.0 - 2026-07-06 - station-level hydropower, CCS retrofit accounting and raw GRFR server readiness

- Git baseline: `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: implemented assigned-label hydropower rules, paper-consistent potential hydropower classification, independent station-level reservoir balance using GRFR inflow, CCS retrofit/capture-cost accounting, production solution export/QC, and raw GRFR server readiness gates.
- Main changed files:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/prepare_server_bundle.py`
  - `scripts/run_cispo_2030_full_year.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/load_center.py`
  - `cispo_model/master.py`
  - `cispo_model/solution_export.py`
  - `cispo_model/runtime_monitor.py`
  - `tests/test_hydro_station_model.py`
  - `tests/test_ccs_model_structure.py`
- Data packages transferred to the server:
  - `/data/zz2/National_model/data/model_ready_20260706_station_hydro`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_station_hydro`
  - `/data/zz2/National_model/data/grfr_raw_2019`
- Verification: raw GRFR SHA256 matched source files; server readiness passed with raw-GRFR SHA verification; 15/15 tests passed on the server; one-month and full-year preflights passed memory gates with the scale estimates recorded in the current snapshot.
- Modeling note: according to the EES hydropower supplement, installed labels are retained from assigned labels, potential dam sites with design capacity greater than 750 MW are modeled as reservoir hydropower, remaining potential sites as run-of-river hydropower, and no hydraulic cascade propagation delay is added because the cited equations use independent station-level natural inflow rather than upstream/downstream travel-time coupling.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization using the versioned station-hydropower data paths.

### v0.1.0 - 2026-07-06 - Gurobi 13.0.2 server readiness

- Git baseline: `805a1fa` (`chore: configure Gurobi 13.0.2 server runtime`).
- Scope: completed server Gurobi installation, license retrieval, full-license verification, dependency documentation and synchronized server checkout.
- Main changed files:
  - `requirements-server.txt`
  - `requirements-test.txt`
  - `env/cispo-server.yml`
  - `scripts/check_gurobi_full_license.py`
  - `scripts/check_server_readiness.py`
  - `SERVER_RUNBOOK.md`
  - `MODEL_SERVER_STATUS.md`
- Verification: full-license 2,501-variable gate passed; server readiness passed; 10/10 tests passed; 8760h preflight memory gate passed.
- Environment note: pytest 9.1.1 was installed from locally verified offline wheels because server PyPI TLS validation remains unresolved.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization.
