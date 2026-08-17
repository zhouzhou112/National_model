# CISPO 2030 full-year server status

## 2026-08-17 15:23+08:00 second factor/throughput batch active

- 实施提交 `7551e3fcc55aa2964dd8eff2bed30e7ab47400f7` 已部署到 clean/idle fixed；`bash -n`、JSON、
  py_compile、focused `16/16` 与 full regression `197/197 PASS`（`93.710 s`，wall `1:34.83`，
  MaxRSS `1,133,084 KiB`，swaps 0）。
- baseline Fingerprint/raw/Factor/observed step metric 为
  `2120635803`、`4,454,178/3,735,087/40,395,436`、`7.334e8/4.761e12`、`12.834849 s/iter`。
  全新 v2 roots；唯一 supervisor PID `1567638`，首根 `presparsify2` 于 15:23:11 启动，stderr 0。
- 启动 available `113.951 GiB`、si/so/PSI `0/0/0`。活动期 checkout 冻结，后两根仅由同一进程
  串行启动；约 30--45 分钟/事件检查。cloud `4139552` 15:19 仍 RUNNING、iteration 338、stderr 0，
  约 2 小时低频检查且未触碰。

## 2026-08-17 15:16+08:00 second factor/throughput batch ready locally

- 第二批仅三根：`PreSparsify=2`、`BarOrder=1`、Threads 32；其余 PreDual/Aggregate/Presolve/AggFill
  已按历史结构/时间证据淘汰。共同保持 Base/744、NF1、Scale2、relaxed tolerance、Crossover 0、5 steps。
- baseline 为第一批同机 `nf1_scaleauto` 5-step；v2 结构降低门槛 `5%`，配对 step-time 降低门槛
  `10%`。summary/runner 对 case tags、profiles、identity、runtime、factor、rc/stderr fail-closed。
- 本地 JSON/compile/diff 与 focused `16/16 PASS`。尚未提交/部署/启动；fixed idle clean `4f195d4`，
  cloud `4139552` 未触碰。

## 2026-08-17 15:10+08:00 factor batch 1 complete / no shortlist / cloud round 39

- 三根 744h×5-step screens 全部 identity valid、status 7、rc 2、audit 0、stderr/swaps 0；无任何
  checkpoint/科学产物。campaign 约 `38:19`，case wall 约 `12:41--12:44`、MaxRSS
  `19.68--20.50M KiB`。
- NF0+Scale2 与 NF0+ScaleAuto 的 Factor NZ/Ops 相对 baseline 为 `1.003545/1.031506`；
  NF1+ScaleAuto 为 `1.0/1.0`。summary `NO_MATERIAL_FACTOR_IMPROVEMENT`，shortlist 空。
- fixed 无 solver，available 约 `114.0 GiB`、si/so/PSI 0、checkout clean `4f195d4`。下一轮只审计/
  短测更直接的 sparsification/fill/order 候选，不运行完整 744。
- cloud round 39：iteration 338、runtime `996,833.092 s`，wall `999,673 s`、allocated
  `26,657.947 core-hours`、actual CPU `4,169.626 h`、efficiency `15.6412%`、recent-20 `52.922 min`；
  ledger 40 records SHA256 `75c7edd5...2108`，stderr 0、无终态/Stage B。

## 2026-08-17 14:26+08:00 serial factor screens active

- exact head `4f195d4353b76ce76c710eb5c7ba3c467a4d494c` 已部署；server bash/profile/compile、focused
  `10/10`、full `194/194 PASS`。baseline Fingerprint/LP/scientific identity 与 Factor 字段全通过。
- 全新 roots `relaxed_factor_screens_v0817_v1`；supervisor PID `1494933`，第一根 `nf0_scale2`
  wrapper/Python `1495063/1495064`，14:25:49 启动。3 根只串行，每根 Base/744、5 Barrier steps、
  Crossover 0，不是 checkpoint/科学结果。
- 启动 available `113.97 GiB`、si/so/PSI 0、磁盘约 `3.96 TB` 可用、stderr 0。活动期间 checkout
  冻结 `4f195d4`；15--20 分钟或事件低频检查。cloud `4139552` 未触碰。

## 2026-08-17 14:20+08:00 factor-screen deployment preflight and data-root freeze

- fixed 已 clean/idle fast-forward `613abe8d...6723`；`bash -n`、profile JSON、`py_compile`、focused
  `10/10 PASS`。显式设置 current data/CF/hydro/raw-GRFR/wave roots 后 full regression
  `194/194 PASS`（`95.60 s`，MaxRSS `1,115,900 KiB`）。缺外部根的两次尝试 fail-fast，无 solver。
- 本地已最小修复 factor-screen runner，使其冻结五个 current 外部数据根并允许显式覆盖；静态 focused
  discovery `10/10 PASS`、diff check PASS。该补丁尚待提交、双推送与 server redeploy，screens 未启动。
- fixed 当前无 solver；cloud `4139552` 未触碰。下一步部署补丁并重跑验证，再启动唯一串行 screens。

## 2026-08-17 14:14+08:00 Base 2160 MEM_LIMIT / fixed idle / cloud round 38

- Base/2160 原始 LP `12,520,914 rows / 10,398,783 cols / 126,724,678 nnz`，build `884.643 s`；
  Presolve `2,214.94 s` 后 `9,527,353 / 8,288,888 / 106,864,030`，Ordering `565.03 s`。
- `SoftMemLimit=80 GiB` 在 Barrier 0 iterations 前触发 `MEM_LIMIT/status 17`；solver `2,800.735 s`、
  wrapper wall `1:01:40`、MaxRSS `72,659,300 KiB`、rc 2、stderr/swaps 0。`solution_count=0`、objective
  null；无 QC/result/checkpoint/BarX/BarPi，只能作为内存与 fill-in 工程证据。
- campaign 14:03:30 complete；fixed 无 CISPO/Gurobi/campaign 进程，checkout clean `902b1672...ff36`。
  available RAM 约 `114.0 GiB`、si/so/PSI 0。下一步不直接抬高 SoftMem 重跑 2160，先部署并执行
  串行 744h lower-factor screens。
- cloud `4139552` iteration 336、runtime `990,741.973 s`；round 38 wall `995,707 s`、allocated
  `26,552.187 core-hours`、actual CPU `4,153.300 h`、efficiency `15.6420%`、MaxRSS `362.913 GiB`、
  recent-20 `53.040 min`。ledger 39 records SHA256 `932b7d8a...bd534`；stderr 0、无 terminal/checkpoint，
  未取消/改参/启 Stage B。

## 2026-08-17 13:09+08:00 Base 1488 complete / Base 2160 active / cloud round 37

- Base/1488 Barrier `OPTIMAL`，143 iterations、solver `25,834.260 s`、wall `7:22:57`、MaxRSS
  `55,460,664 KiB`、rc/stderr/swaps `0/0/0`。checkpoint gate PASS；BarX/BarPi entries
  `7,236,351/8,648,849` 且 size/SHA 完整，LP Fingerprint `893131507`、input manifest 与 order digests
  齐全。身份仅 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，可 deferred crossover，不是科学结果。
- strict contract `HARD_FAIL`；engineering QC `54/58`，失败 wave `0.850 MW`、strict bidirectionality、
  reservoir `11,280 m3/3.775 m3`。power balance `2.315 kW`，storage overlap 仅 period load `0.0952%`，
  interprov opposing `0.259%`、excess loss `0.00641%`，load-center bidirectional `0.891%`。碳/CCS/DAC、
  备用、惯量、网络容量、储能状态、水文级联与成本闭合；BarPi `46,128/3,366` rows 仅工程使用。
- campaign 13:01:45 串行启动唯一 Base/2160 PID `1387308/1387309`，start hour 2880；13:08 build RSS
  `4.14 GiB`、available 约 `110 GiB`、si/so/PSI 0、stderr 0。checkout clean `902b1672...ff36`。
- cloud `4139552` iteration 335、runtime `987,914.783 s`；round 37 wall `991,984 s`、allocated
  `26,452.907 core-hours`、actual CPU `4,137.397 h`、efficiency `15.6406%`、recent-20 `53.550 min`；
  ledger 38 records SHA256 `c31d779c...e0df`，stderr 0、无 terminal/checkpoint/Stage B。

## 2026-08-17 11:57+08:00 factor shortlist audit ready locally

- 新汇总器按 LP Fingerprint/矩阵/scientific/scenario identity、rc/stderr、5 iterations、numerical trouble
  与完整 Factor 指标 fail-closed；Factor Ops/NZ 至少降低 `5%` 才进入 engineering shortlist。
- runner 在三根 screen 前先审计当前 NF1+Scale2 Base/744 baseline，末尾输出 JSON/CSV；不完整分别
  exit `98/99`。shortlist 不自动成为 winner，完整 744 exact macro A/B 仍强制。
- focused tests `11/11 PASS`、`py_compile` PASS；尚未部署，活动 fixed/cloud 未触碰。

## 2026-08-17 11:52+08:00 cloud round 36 / fixed iteration 120

- fixed Base/1488 iteration 120、runtime `21,739.318 s`，primal/dual/compl
  `0.050274/0.000789619/0.027934`；近 20/10 步 `169.03/169.75 s/step`，12 h 投影 iteration
  `247.0`。RSS `55,459,960 KiB`，available 约 `61.1 GiB`、swap used 约 `984 MiB`，si/so/PSI 0、
  stderr 0、无终态/checkpoint，唯一 solver 正常。
- cloud `4139552` RUNNING，iteration 334、runtime `984,705.405 s`，primal/dual/compl
  `1.213709/9.858e-7/0.104884`；round 36 wall `988,357 s`、allocated `26,356.187 core-hours`、
  actual CPU `4,122.200 h`、efficiency `15.6404%`、MaxRSS `362.913 GiB`、recent-20 `53.255 min`。
  ledger 37 records SHA256 `cbf0311e...33710`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- 下一次 fixed 为 iteration 130/终态，cloud 约一小时；活动 campaign 退出前不部署或并发。

## 2026-08-17 11:05+08:00 phase trajectory audit extended locally

- `collect_solver_run()` 现为每个 solver phase 自动记录 iteration/runtime span、observed seconds per
  iteration、complementarity 及末端 primal/dual objective gap；factor screen 不再依赖人工日志摘录。
- focused tests `8/8 PASS`、`py_compile` PASS、既有 1 h telemetry 实读 PASS。尚未部署，活动
  fixed/cloud 作业完全未触碰；待 campaign idle 后随 lower-factor screens 一并 fast-forward/regression。

## 2026-08-17 10:59+08:00 cloud round 35 / fixed iteration 100

- fixed Base/1488 iteration 100、runtime `18,358.690 s`，primal/dual/compl
  `0.562716/0.00180162/0.402016`；0--100/50--100/75--100/90--100 平均
  `168.69/166.88/168.82/169.06 s/step`，按近期窗口 12 h 约到 iteration `247.2`。残差量级约对应
  strict Base/744 iteration `67/96/122`；raw objective gap `5.432e6`，不跨 horizon 强行比较。
- fixed process RSS `55,452,788 KiB`，available 约 `61.1 GiB`，swap used 约 `984 MiB` 但 si/so 0、
  memory PSI 0；stderr 0、无终态/checkpoint、唯一 solver 安全运行。
- cloud `4139552` RUNNING，iteration 333、runtime `981,713.748 s`，primal/dual/compl
  `1.246258/1.002e-6/0.107341`；round 35 wall `985,280 s`、allocated `26,274.133 core-hours`、
  actual CPU `4,109.163 h`、efficiency `15.6396%`、MaxRSS `362.913 GiB`、recent-20 `53.302 min`。
  resource ledger 36 records SHA256 `64d80b8c...db6e87`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- 继续低频：fixed 每 10 iteration/15--30 min 或事件检查，cloud 约每小时且只在新 iteration 记账；
  正常中途点不再逐次写文档。活动 campaign 退出前不部署或启动 lower-factor screens。

## 2026-08-17 09:57+08:00 cloud round 34 / fixed iteration 79

- cloud `4139552` RUNNING，iteration 332、runtime `978,908.233 s`，primal/dual/compl
  `1.274926/1.023e-6/0.109716`；wall `981,492 s`、allocated `26,173.120 core-hours`、actual CPU
  `4,092.853 h`、efficiency `15.6376%`、MaxRSS `362.913 GiB`，最近 20 步 `53.291 min`。
  audit 35 records SHA256 `29960f1e...aad17`；stderr 0、无 terminal/checkpoint、未启 Stage B。
- fixed Base/1488 iteration 79、runtime `14,822.968 s`，primal/dual/compl
  `10.206400/0.00308381/7.745108`；RSS 稳定、stderr 0，继续唯一 solver 到 100/终态。

## 2026-08-17 09:44+08:00 lower-factor screens prepared locally

- 三个配对 Base/744 profiles：`NF0+Scale2`、`NF1+ScaleAuto`、`NF0+ScaleAuto`；共同
  `BarIterLimit=5`、TimeLimit 2 h、SoftMem 40 GiB，其余保持 relaxed winner 合同。
- 串行 runner 要求 clean/no-solver、available ≥64 GiB、si/so/PSI 0，记录完整 factor/resource
  证据且不导出 checkpoint。配置/配对测试 `1/1 PASS`；server bash/profile/full regression 待 idle。
- 当前 fixed/cloud 未部署或改参；活动 campaign 退出前严禁启动 screens。

## 2026-08-17 09:41+08:00 future campaign checkpoint gate fixed locally

- 旧 1488→2160 编排仅按 manifest 存在性放行；现在本地新增 fail-closed eligibility/vector-integrity
  gate，recovery-only、status 不符、向量缺失/size/SHA256 不符均停止。相关 unittest `4/4 PASS`。
- 尚未部署，活动 fixed checkout、Base/1488 和 cloud `4139552` 均未修改。必须等唯一 solver 与
  campaign 退出后才能 fast-forward，并补 server `bash -n`、focused/full regression。

## 2026-08-17 09:32+08:00 cloud round 33 / fixed iteration 70

- cloud `4139552` 仍为 `RUNNING`，iteration 331、runtime `975,911.936 s`；primal/dual/compl
  `1.336420/1.053e-6/0.113863`。wall `980,022 s`、allocated `26,133.920 core-hours`、actual CPU
  `4,086.896 h`、efficiency `15.6383%`、MaxRSS `362.913 GiB`，最近 20 步 `53.414 min`。
  resource audit 34 records SHA256 `fc88fd29...e48045c`；stderr 0、无终态/checkpoint，未启 Stage B。
- fixed Base/1488 到 iteration 70，runtime `13,316.273 s`，primal/dual/compl
  `19.574527/0.00930446/18.290173`；process RSS 约 `55,451,552 KiB`、stderr 0，仍安全。
- 当前 cloud 严格 profile 不能在运行中改参。近期衰减只支持费用预警：primal 到 relaxed-744
  终点量级约 5 天，objective gap 到 1,000 量级约 8--9 天；不是可靠完成 ETA。保持不取消，
  fixed 继续到 100/终态，下一轮转入 lower-factor 参数 screen。

## 2026-08-17 08:37+08:00 Base 1488 iteration 50

- iteration 50 runtime `10,014.836 s`；primal/dual/compl `229.055/0.172288/262.879`。
  与 Base/744 对齐分别相当于 iteration `48/58/65`，objective gap 相当于 61，综合约领先
  10--15 步；同 iteration gap 小 `157.5x`。
- 当前平均步长推算 12 h 可到 iteration `244--255`。相对 744 的 263 步仍是边界案例；继续到
  100/终态，不取消、不改参。
- RSS `55,428,232 KiB`、available 约 61.0 GiB、swap used 约 984 MiB，si/so 0、memory PSI 0、
  stderr 0；当前安全，下一任务不得并发。

## 2026-08-17 07:40+08:00 cloud round 32 / fixed iteration 30

- cloud `4139552` RUNNING，iteration 329、runtime `969,935.080 s`，primal/dual/compl
  `1.404886/1.110e-6/0.119628`；wall `973,314 s`、allocated `25,955.040 core-hours`、
  actual CPU `4,058.406 h`、efficiency `15.6363%`、MaxRSS `362.913 GiB`，最近 20 步
  `53.686 min`。resource audit 33 records SHA256 `0752c628...e467326d`；stderr 0、无终态/
  checkpoint，未启 Stage B。
- fixed Base/1488 到 iteration 30，runtime `6,588.139 s`，primal/dual/compl
  `2.223e6/702.46/5.926e5`；内存不变、stderr 0，继续到 50。

## 2026-08-17 07:35+08:00 next-candidate factor audit

- 只读历史 24 h 表明 `NumericFocus=0 + ScaleFlag=-1` 相对 NF2/Scale2 将 Factor NZ/Ops
  约降低 `8.3%/7.5%`，Barrier `18.99 s` 对 `57.95 s`；旧严格合同因
  `ConstrVio=0.04788` 拒绝，但 objective 相对差约 `1.54e-7`。
- 下一轮应在 current model / `BarConvTol=1e-2` 下拆分 NF0 与 auto scaling，并先用 744
  短迭代比较 Factor NZ/Ops；`AggFill=0` 历史收益不足 2%，`PreSparsify=2` 虽稀疏却更慢，均非
  首选完整 solve。当前 Base/1488 和 cloud job 未改，活动 campaign 退出前不启动候选。

## 2026-08-17 07:25+08:00 Base 1488 iteration 25

- iteration 25 runtime `5,731.421 s`；0--25 平均 `169.69 s/step`，primal/dual/complementarity
  `2.275e8/1.364e5/5.068e7`。相对 Base/744 同步点，primal 高 32.6% 而 dual/compl 低约
  `30x/533x`；继续到 50，不能按 263 步直接外推。
- solver current/max memory `45.07/58.29 GiB`、process RSS 约 52.8 GiB；host available 约
  61.1 GiB、si/so 0、memory PSI 0、stderr 0。当前安全；2160 仍须退出后重新满足 96 GiB 门禁。

## 2026-08-17 07:03+08:00 Base 1488 validates cloud 8760 per-step scaling

- cloud 8760 Factor NZ/Ops `3.395e10/1.931e15`，fixed 1488 为 `3.866e9/1.060e14`，比值
  `8.78x/18.22x`；dense cols `37,696/36,218`。cloud 最近实际 `3216.5 s/step` 按 Factor Ops
  折算 fixed 为 `176.6 s/step`，与 fixed 0--16 实测 `171.0 s/step` 仅差约 3.2%。
- 结论：1488 是当前 LP 的可信全年单步成本代理；fill-in 决定单步约 50--55 min。放宽容差只可能
  通过减少迭代数降总时间。继续当前 1488 到 25/50/终态实测，不改参、不并发。

## 2026-08-17 07:01+08:00 cloud round 31 / Base 1488 iteration 16

- ParaCloud `4139552` iteration 328、runtime `966,756.149 s`，primal/dual/complementarity
  `1.450925/1.129e-6/0.122696`。round 31 wall `970,967 s`、allocated `25,892.453 core-hours`、
  actual CPU `4,048.863 h`、efficiency `15.6372%`、MaxRSS `362.913 GiB`、最近 20 步
  `53.608 min`；32 records SHA256 `223757e0...e391`。stderr 0、无 terminal/checkpoint，未改任务。
- fixed Base/1488 iteration 16、runtime `4,225.346 s`；0--16 平均约 `171.00 s/step`，solver
  current/max memory `45.07/58.29 GiB`、stderr 0。继续唯一 solver 到 iteration 25 门点。

## 2026-08-17 06:21+08:00 Base 1488 factorization / Barrier start

- Base/1488 raw LP `7,236,351 vars / 8,648,849 rows / 87,364,792 nnz`；build 约 10.4 min，
  presolve `1,080.17 s` 后为 `6,564,794 / 5,761,274 / 73,637,736`，ordering `322.03 s`。
  dense cols 36,218、Factor NZ `3.866e9`（约 36 GB）、Factor Ops `1.060e14`（约 200 s/iter）。
- 相对同 Base/744 NF1 winner，presolved nnz `2.36x`，但 Factor NZ/Ops `5.27x/22.26x`；长时域
  性能瓶颈已定位为 fill-in/dense temporal coupling，不是仅靠容差能消除。
- iteration 0/1/2 runtime `1,489.26/1,595.89/1,855.80 s`；solver current/max memory
  `45.07/58.29 GiB`，stderr 0，主机无 swap I/O/PSI。继续唯一求解，至少 5--10 步后再估 12 h 终点。
- 审计发现 campaign 的 2160 gate 仅检查 checkpoint manifest 存在；若 1488 TIME_LIMIT 后只保存
  `INCOMPLETE_BARRIER_RECOVERY`，也会被误放行。活动脚本不改；本轮结束后应要求 manifest
  `deferred_crossover_eligible=true` 并加测试。

## 2026-08-17 05:47+08:00 cloud round 30 / Base 1488 building

- ParaCloud `4139552` 新落盘 Barrier iteration 326/327；最新 runtime `963,537.897 s`，
  primal/dual/complementarity `1.529887/1.166e-6/0.128042`。round 30 wall `966,523 s`、allocated
  `25,773.947 core-hours`、actual CPU `4,030.069 h`、efficiency `15.6362%`、MaxRSS
  `362.913 GiB`、最近 20 步 `53.232 min`；31 records SHA256 `5ea6005a...840c9`。stderr 0、
  无 terminal/checkpoint，未取消、未改参、未启动 Stage B。
- fixed Base/1488 PID `3899905/3899906` 仍为唯一 solver 链，05:46 尚在 build，stderr 0；继续等待
  Gurobi/presolve/Barrier，不切 checkout、不启动第二 solver。

## 2026-08-17 05:41+08:00 V5 744 terminal / Base 1488 active

- V5/744 于 05:38:39 rc 0：solver `OPTIMAL`，Barrier `305 iterations / 4,520.108 s`，wrapper
  wall `1:21:54`、stderr 0、MaxRSS `21,285,692 KiB`、swaps 0。LP 为 3,894,744 variables、
  4,636,251 constraints、41,327,437 nonzeros；完整 `BarX/BarPi`、LP Fingerprint、ordering digest、
  layered identity 与 hashes 均已保存，checkpoint 可在精确重建 LP 后延期 Crossover。
- 该解是工程检查点，不是科学结果：strict QC `HARD_FAIL`，58 个物理 hard checks 中仅
  `reservoir_transition` 失败，最大残差 `11,917.821 m3`；power balance `2.362e-7 GW`、省间双向流 0、
  storage overlap `1.745e-5 GWh`，其余网络、备用、惯量、碳/CCS 和成本账目通过；没有 scientific
  result manifest/planning state/basis。
- campaign 于 05:38:42 自动串行启动唯一 Base/1488：PID `3899905/3899906`，start hour 3624，
  output `relaxed_barrier_continuation_v0817_v5/base_1488h_bctol1e2_numeric1`，long NF1 winner profile。
  05:41 仍在 build，stderr 0、available RAM 约 111 GiB、si/so 0、memory PSI 0；固定 checkout clean
  `902b1672...ff36`。无第二 solver；仅在 1488 checkpoint 存在时才允许自动进入 Base/2160。
- ParaCloud `4139552` 未取消、未改参、未启动 Stage B；沿用 round 29 证据直到出现新 iteration。

## 2026-08-17 04:18+08:00 exact macro winner / V5 744 start / cloud round 29

- v5 exact A/B 成功：`5e-2/NF2` 与 `1e-2/NF2` 分别因宏观 operation-account L1
  `29.64%/10.04%` 等失败；`1e-2/NF1` 为唯一 `MACRO_PASS`，objective/capacity/generation/
  carbon/operation 差异为 `2.93e-9/1.33e-8/0.001056/8.41e-10/1.92e-6`。winner Barrier
  `4,275.73 s`，较 strict total `53,489.07 s` 快 `92.0%`，较 strict Barrier `7,734.65 s`
  快 `44.7%`。
- 唯一 solver 已于 04:16:42 启动 V5/744 Barrier-only：PID `3569191/3569192`，output
  `relaxed_barrier_continuation_v0817_v5/v5_744h_bctol1e2_numeric1`；profile 为 Method 2、16 threads、
  Presolve 2、Crossover 0、BarConvTol `1e-2`、Feas/Opt `1e-5`、NF1、Scale2、TimeLimit 6h、
  SoftMem 40 GiB。启动时约 113.6 GiB available、无实时 swap I/O/PSI、stderr 0。
- ParaCloud `4139552` 未触碰：iteration 325、runtime `957,363.69 s`；round 29 wall
  `961,177 s`、allocated `25,631.387 core-hours`、actual CPU `4,007.857 h`、efficiency
  `15.6365%`、最近 20 步 `53.129 min`、MaxRSS `362.913 GiB`。30 records SHA256
  `26a9903d...7a61e69`；stderr 0、无 terminal/checkpoint。

## 2026-08-17 04:16+08:00 v4 exact-macro second fail-closed / control-dir fix

- fixed server 已部署 clean `5161dd0`，`bash -n`、focused `6/6` 与完整 `187/187 PASS`
  (`94.975 s`)。v4 正确复用三候选且 import 问题已消失，但复用分支未创建候选 control 子目录，
  shell 在 stdout 重定向前即失败；故仍为 `NO_MACRO_PASS`，无 `macro_comparison.json`、无 solver。
- 最小补丁在每个候选循环入口无条件 `mkdir -p "$CONTROL_ROOT/$tag"`；本地 focused `6/6 PASS`，
  新脚本 SHA256 `21e67deb...ff79b07`。v4 保留为编排失败证据；下一步双推送、server `bash -n`
  后在全新 v5 根第三次执行 exact macro，不重算任何 744 候选。

## 2026-08-17 04:12+08:00 strict 744 accepted / exact-macro orchestration fix

- fixed strict Base/744 reference 正式 `OPTIMAL + QC PASS + 58/58 + current input manifest + valid
  68-file result manifest`。solver `53,489.07 s`：Barrier `7,734.65 s`、Crossover `45,468.01 s`，
  objective `2,361,958.416203 million CNY`；wrapper rc 0、stderr 0、wall `14:57:39`、MaxRSS
  `20,617,928 KiB`、swap 0。`ConstrVio/BoundVio/DualVio` 为
  `9.74e-8/8.50e-8/8.85e-8`，宏观电力、网络、储能、水电、备用、惯量、碳与成本检查均闭合；
  仍仅为 `TEST_ONLY_TRUNCATED_HORIZON`。
- v3 exact-macro campaign fail-closed 且未启动 solver：supervisor symlink 被重复运行逻辑误报为已有输出，
  audit 脚本又因缺少 frozen repo `PYTHONPATH` 报 `ModuleNotFoundError`，故 `NO_MACRO_PASS`。
  已最小修复 campaign：仅复用带完整 engineering contract 的 supervisor symlink，并为独立 audit
  显式注入 repo `PYTHONPATH`；本地 focused `6/6 PASS`，脚本 SHA256
  `95e177ee...5a17132`。下一步双推送、fixed server `bash -n` 后在全新 v4 control/output 根只重跑
  exact macro，再按 winner 串行进入 V5/744 与 Base/1488/2160。

## 2026-08-17 03:01+08:00 cloud round 28 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 324、runtime `954,056.89 s`；round 28 为 wall
  `956,593 s`、allocated `25,509.147 core-hours`、actual CPU `3,988.565 h`、CPU efficiency
  `15.6358%`、MaxRSS `362.913 GiB`、iteration 304--324 平均 `53.113 min`。29 records SHA256
  `b9d852b3...31951f87`；stderr 0、无 terminal/checkpoint。最新单步约 `57.12 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `1,009,728`、runtime `49,698.19 s`、primal 0、dual
  `1.02e3`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 02:07+08:00 cloud round 27 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 323、runtime `950,629.60 s`；round 27 为 wall
  `953,368 s`、allocated `25,423.147 core-hours`、actual CPU `3,975.420 h`、CPU efficiency
  `15.6370%`、MaxRSS `362.913 GiB`、iteration 303--323 平均 `52.990 min`。28 records SHA256
  `1ac421f7...534f0b8`；stderr 0、无 terminal/checkpoint。最新单步约 `53.86 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `995,574`、runtime `46,496.02 s`、primal 0、dual
  `9.22e2`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 01:15+08:00 cloud round 26 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 322、runtime `947,398.04 s`；round 26 为 wall
  `950,224 s`、allocated `25,339.307 core-hours`、actual CPU `3,962.390 h`、CPU efficiency
  `15.6373%`、MaxRSS `362.913 GiB`、iteration 302--322 平均 `52.831 min`。27 records SHA256
  `ec248a3b...73ee91`；stderr 0、无 terminal/checkpoint。最新单步约 `60.04 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `980,379`、runtime `43,298.54 s`、primal 0、dual
  `3.23e2`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-17 00:14+08:00 cloud round 25 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 321、runtime `943,795.68 s`；round 25 为 wall
  `946,575 s`、allocated `25,242.000 core-hours`、actual CPU `3,947.624 h`、CPU efficiency
  `15.6391%`、MaxRSS `362.913 GiB`、iteration 301--321 平均 `52.246 min`。26 records SHA256
  `05a7a568...2f52f7`；stderr 0、无 terminal/checkpoint。最新单步约 `55.02 min`，primal 与
  complementarity 继续下降。
- fixed strict quad cleanup 为 iteration `962,785`、runtime `39,637.75 s`、primal 0、dual
  `2.55e3`；wrapper/v3 supervisor 存活、仍只有一个 solver，continuation 输出根 absent。

## 2026-08-16 23:50+08:00 cloud round 24 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 320、runtime `940,494.22 s`；round 24 为 wall
  `945,131 s`、allocated `25,203.493 core-hours`、actual CPU `3,942.270 h`、CPU efficiency
  `15.6418%`、MaxRSS `362.913 GiB`、iteration 300--320 平均 `52.071 min`。25 records SHA256
  `efb6bd58...f51a7`；stderr 0、无 terminal/checkpoint。最新单步约 `68.32 min`，但 primal 与
  complementarity 继续下降，尚无正式停滞或失败证据。
- fixed strict quad cleanup 为 iteration `955,777`、runtime `38,214.01 s`、primal 0、dual
  `1.54e4`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 23:09+08:00 cloud round 23 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 319、runtime `936,395.20 s`；round 23 为 wall
  `942,654 s`、allocated `25,137.440 core-hours`、actual CPU `3,931.546 h`、CPU efficiency
  `15.6402%`、MaxRSS `362.913 GiB`、iteration 299--319 平均 `51.167 min`。24 records SHA256
  `d203d675...fa7b`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `942,842`、runtime `35,770.00 s`、primal 0、dual
  `1.99e5`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 21:45+08:00 cloud round 22 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 318、runtime `933,326.74 s`；round 22 为 wall
  `937,651 s`、allocated `25,004.027 core-hours`、actual CPU `3,911.908 h`、CPU efficiency
  `15.6451%`、MaxRSS `362.913 GiB`、iteration 298--318 平均 `51.532 min`。23 records SHA256
  `5db4ac89...50a0`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `917,738`、runtime `30,759.68 s`、primal 0、dual
  `8.19e6`；wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 20:23+08:00 cloud round 21 / fixed cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 317、runtime `930,000.70 s`；round 21 为 wall
  `932,693 s`、allocated `24,871.813 core-hours`、actual CPU `3,890.998 h`、CPU efficiency
  `15.6442%`、MaxRSS `362.913 GiB`、iteration 297--317 平均 `51.272 min`。22 records SHA256
  `bf039d69...d7de`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `892,970`、runtime `25,778 s`、primal 0、dual `2.51e6`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 19:57+08:00 strict runtime 超过旧成功根

- 当前 strict runtime `24,224 s` 且未结束，已超过旧成功根 `24,156.53 s`；iteration `885,507`、
  primal 0、dual `2.89e5`、stderr 0。
- 本次 Barrier 比旧根快约 `3,407.9 s`，但 Barrier 后 Crossover/cleanup 已至少 `16,489.4 s`，
  相对旧完整 Crossover `12,672.69 s` 慢约 `30.1%`，端到端收益已耗尽。比较跨数据版本，仅为
  历史工程参照；继续运行并等待正式 status。云 job 不变。

## 2026-08-16 19:36+08:00 cloud round 20 / fixed low-dual cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 316、runtime `927,093.65 s`；round 20 为 wall
  `929,885 s`、allocated `24,796.933 core-hours`、actual CPU `3,879.081 h`、CPU efficiency
  `15.6434%`、MaxRSS `362.913 GiB`、iteration 296--316 平均 `51.638 min`。21 records SHA256
  `278f0396...e639`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `879,136`、runtime `22,956 s`、primal 0、dual `4.73e4`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 18:38+08:00 cloud round 19 / fixed dual recovery

- ParaCloud `4139552` 未触碰：Barrier iteration 315、runtime `923,654.91 s`；round 19 为 wall
  `926,381 s`、allocated `24,703.493 core-hours`、actual CPU `3,864.724 h`、CPU efficiency
  `15.6444%`、MaxRSS `362.913 GiB`、iteration 295--315 平均 `51.837 min`。20 records SHA256
  `19273e36...c437`；stderr 0、无 terminal/checkpoint。
- fixed strict quad 已从 `1e10--1e12` dual 段恢复；当前 iteration `859,888`、runtime `19,483 s`、
  primal 0、dual `2.05e6`、stderr 0，wrapper/v3 supervisor 存活、仍只有一个 solver。

## 2026-08-16 18:04+08:00 strict quad 轨迹偏离旧成功根

- 定量纠正：旧成功根 quad 后最大 dual `1.91e8`，仅 2 个采样 `>=1e8`、无 `>=1e9`；当前根
  quad 后最大 `6.63e12`，41/23/17/10 个采样分别 `>=1e8/1e9/1e10/1e11`。两根只有自动
  `drop basis variable + switch to quad` 动作相同，后续数值轨迹明显不同，不能沿用旧根 ETA。
- 当前 iteration `848,783`、runtime `17,444 s`、primal 0、dual `3.96e10`、objective 仍下降；
  wrapper 存活、stderr 0、无正式 failure/终态。按合同不取消、不并发，但提高数值风险等级并等待
  正式 status。云 job 不变。

## 2026-08-16 17:51+08:00 cloud round 18 / fixed quad cleanup

- ParaCloud `4139552` 未触碰：Barrier iteration 314、runtime `920,799.47 s`；round 18 为 wall
  `923,578 s`、allocated `24,628.747 core-hours`、actual CPU `3,852.752 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、iteration 294--314 平均 `51.766 min`。19 records SHA256
  `90fc64d6...0498`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `844,413`、runtime `16,683 s`、primal 0、dual `2.69e8`；
  wrapper/v3 supervisor 存活、仍只有一个 solver，终态文件 absent。

## 2026-08-16 17:06+08:00 cloud round 17 / fixed quad cleanup

- ParaCloud `4139552` 未修改：Barrier iteration 313、runtime `917,751.15 s`；round 17 为 wall
  `920,881 s`、allocated `24,556.827 core-hours`、actual CPU `3,841.487 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、最近 20 步平均 `52.099 min`。18 records SHA256
  `a7ab2c58...11ba`；stderr 0、无 terminal/checkpoint。
- fixed strict quad cleanup 为 iteration `828,761`、runtime `13,981 s`、primal 0、dual `2.73e5`；
  wrapper/v3 supervisor 存活，仍只有一个 solver，终态文件 absent。

## 2026-08-16 16:58+08:00 strict cleanup 切换 quad precision

- iteration `823,548`、runtime `13,224 s` 后，Gurobi 自动报告 `1 variables dropped from basis` 和
  `switch to quad precision`；旧成功根存在完全相同保护动作，当前不判失败或取消。
- quad 后约 `7 pivots/s`；iteration `825,303`、runtime `13,464 s` 时 primal 0、dual `1.14e5`、
  objective `2,362,020.1 million CNY`。stderr 0、wrapper 存活、终态文件 absent、只有一个 solver；
  继续等待正式 Crossover status 与强终态审计。云 job 不变。

## 2026-08-16 16:27+08:00 strict cleanup / cloud round 16

- fixed strict simplex 约从 iteration `788,784` 推进到 `792,828`，runtime `11,448→11,630 s`；
  primal infeasibility 保持 0，dual infeasibility 在 `7.47e3--9.29e8` 非单调。旧成功根同一相对
  阶段也曾摆动到 `1.09e9` 后最终 OPTIMAL，当前暂无新增 numerical failure 证据，但仍不能预测
  cleanup 完成时间。
- wrapper/Python 与 v3 supervisor 均存活，stderr 0、终态三文件 absent；fixed 仍只有一个 solver，
  available RAM 约 `100 GiB`、无实时 swap I/O、memory PSI 0。
- ParaCloud `4139552` 未触碰：Barrier iteration 312、runtime `914,959.12 s`；round 16 为 wall
  `918,306 s`、allocated `24,488.16 core-hours`、actual CPU `3,830.451 h`、CPU efficiency
  `15.6421%`、MaxRSS `362.913 GiB`、iteration 292--312 平均 `52.330 min`。17 records SHA256
  `65b3c549...a59c9`；stderr 0、无 terminal/checkpoint。

## 2026-08-16 16:20+08:00 Crossover push complete / simplex cleanup

- strict Crossover basis 约 `255 s`；DPush `841,200→0` 用 `2,565 s`，PPush `274,055→0` 用
  `602 s`。push complete runtime `11,177 s`，PInf/DInf `2.741902/1.751704e8`，已进入 simplex
  cleanup；iteration `782,690` primal infeasibility 已降至 `1.19e-3`，dual cleanup 尚未完成。
- 旧成功根 push complete runtime `13,707 s`，当前仍快 `2,530 s`；但旧 PInf/DInf 仅
  `0.576694/6.499e3`，当前 cleanup 起点更难，不能预测最终净加速。
- stderr 0、terminal files absent；RSS 约 `13.57 GiB`、available RAM 约 `100 GiB`、memory PSI
  0。仍只有一个 fixed solver，v3 supervisor 继续等待 wrapper；ParaCloud 不变。

## 2026-08-16 15:39+08:00 cloud round 15 / fixed DPush

- ParaCloud `4139552` 未触碰：Barrier iteration 311、runtime `911,815.51 s`；resource audit round
  15 为 wall `915,643 s`、allocated `24,417.15 core-hours`、actual CPU `3,819.47 h`、CPU
  efficiency `15.643%`、MaxRSS `362.913 GiB`、iteration 291--311 平均 `52.200 min`。stderr 0、
  无 terminal/checkpoint；16 records SHA256 `41c67c50...a58fe`。
- fixed strict Crossover initial basis 已完成，DPush 从 `841,200` 降至约 `237,580`；DInf 非单调但
  日志无 error。RSS 约 `12.47 GiB`、available RAM 约 `101 GiB`、memory PSI 0，仍只有一个
  solver；v3 PID `46839` 继续等待 wrapper。

## 2026-08-16 15:25+08:00 strict Barrier 完成 / Crossover basis

- strict Base/744 h Barrier 正常报告 `218 iterations / 7,734.65 s / 11,980.50 work units`、
  `Optimal objective 2,361,958.43 million CNY`，已进入 `Building initial crossover basis`。
  最后 telemetry primal/dual/complementarity `0.003445/6.761e-7/1.962e-9`；scaled Gurobi 表为
  `6.11e-4/6.58e-8/1.96e-9`，日志无 warning/error。
- 相对旧同 profile Jan/2030 Barrier `251 / 11,142.54 s`，少 33 轮、runtime 快约 `30.58%`。
  最快 `1e-2/NumericFocus=1` candidate objective 与 strict Barrier 相对差约 `3e-9`，其 runtime
  `4,275.73 s`，Barrier-only 节省约 `44.72%`；仍须 exact macro v2，尚未晋级。
- fixed 仍只有一个 solver；Crossover basis 时 RSS 约 `12.57 GiB`、available RAM 约 `101 GiB`、
  `si/so=0/0`、memory PSI 0，stderr 0、终态三文件 absent。v3 PID `46839` 仍等待 wrapper。
- ParaCloud `4139552` 未触碰，仍为 Barrier iteration 310、resource audit round 14；不取消、不改参、
  不启动 Stage B。

## 2026-08-16 14:20+08:00 strict iteration 120 / cloud audit round 14

- fixed strict Base/744 h 为唯一 solver：Barrier iteration 120、runtime `3,996.41 s`；110--120
  平均 `45.062 s/iteration`，telemetry primal/dual/complementarity 为
  `0.007359/5.61e-4/0.502643`。stderr 0、无数值 warning、终态三文件 absent。
- Python RSS 约 `17.51 GiB`，host available RAM 约 `96 GiB`，swap 实时 `si/so=0/0`、memory
  PSI 0。v3 supervisor PID `46839` 仍等待，预定输出根 absent；fixed checkout clean/frozen
  `d80f5b7`，没有第二 solver。
- 三根 relaxed candidate 的 checkpoint 预检通过：各有完整 BarX `3,735,087` 项与 BarPi
  `4,454,178` 项，只能作为 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`；copied supervisor/campaign
  `bash -n` 与 audit `py_compile` PASS。
- ParaCloud `4139552` 未触碰：iteration 310、runtime `908,489.11 s`、stderr 0、无
  terminal/checkpoint。resource audit round 14 为 wall `910,941 s`、allocated `24,291.76`
  core-hours、actual CPU `3,799.68 h`、CPU efficiency `15.642%`、MaxRSS `362.913 GiB`、最近
  290--310 平均 `51.827 min/iteration`；15 records SHA256 `12ecc84d...e21f`。

## 2026-08-16 13:54+08:00 macro accounting v2 与 supervisor v3

- `a02d4d99b1060a2552e1c1f470817f1d4dbe3ac1` 已双推送：exact macro 新增 carbon/CCS L1
  `<=2%` 与运行账目 L1 `<=5%`；成本分项存在时 L1 `<=2%`，历史缺失时仅 objective `<=1%` 作成本
  门禁并显式报告。容量/发电 `2%`、period generation `0.5%` 不变。采用 normalized L1 而非逐个
  近零项相对误差，符合全国宏观尺度且不放松科学 QC。
- `cost_components.csv` 现在在 load-center strict QC 前写出；不改表达式、数值、accounting scope 或
  QC。py_compile、macro+summary `6/6 PASS`，server isolated cost export PASS；真实旧根 parser v2
  成功但 exact identity 仍 FAIL。活动 checkout 未部署该提交。
- `5af8efe6872b569e4ca068c7c66cc2aefa9e676e` 已双推送并提供 versioned supervisor/campaign audit
  injection。旧 v2 supervisor 只等待且已精确替换，日志保留；v3 PID `46839`、PPID 1，控制/输出根
  为 `relaxed_barrier_continuation_v0816_v3`，绑定 checksummed macro v2。13:54 输出根 absent，无第二
  fixed solve。
- strict Base/744 13:54 Barrier iteration 81、runtime `2,445.64 s`、stderr 0；Python RSS 约
  `17.5 GiB`，memory PSI 0。checkout 继续 frozen `d80f5b7`。ParaCloud `4139552` 未触碰，最近权威
  审计为 round 13、iteration 309、stderr 0、无 terminal/checkpoint。

## 2026-08-16 13:42+08:00 strict reference manifest 门禁与 supervisor v2

- 实现 `f96d9e0443a40f343eaf74b6d97c7abd186e309a` 已双推送：result manifest validator 现在拒绝
  缺失/空 `files`、损坏 JSON、不安全/重复路径、非法 bytes/SHA256，并逐文件复核 size/hash；exact
  macro 审计要求 validator PASS 并记录 failures。py_compile、macro tests `5/5` 与直接 synthetic
  正/反检查通过；服务器 full regression 必须等活动 solve 退出后再做。
- 活动 fixed checkout 继续 clean/frozen `d80f5b7`。旧 supervisor v1 PID `4100799` 与唯一 sleep child
  被精确替换，未触碰 strict wrapper/time/Python `4046161/4046167/4046172` 或 sampler `4059299`；
  v1 日志全部保留。supervisor v2 PID `4179192`、PPID 1、脚本 SHA256 `90e399e9...e17c3b`，使用
  独立 `relaxed_barrier_continuation_v0816_v2` 控制/输出根。
- v2 只有在 reference 同时满足 wrapper rc 0、stderr 0、`OPTIMAL + PASS + 58/58`、非空且逐文件有效
  result manifest、current input manifest valid 后才复用 candidates 并启动串行 continuation；任一失败
  即停止。13:39 新输出根 absent，仍无第二 fixed solve。
- strict reference 13:39 Barrier iteration 51、runtime `1,579.34 s`、stderr 0；RSS 约 `17.5 GiB`、
  available RAM 约 `96.5 GiB`、实时 `si/so=0/0`、memory PSI 0。
- ParaCloud `4139552` 不变，13:42 仍 RUNNING、iteration 309、runtime `905,512.39 s`、stderr 0、无
  terminal/checkpoint。resource audit round 13：wall `908,636 s`、allocated core-hours `24,230.29`、
  actual CPU-hours `3,790.05`、MaxRSS `362.913 GiB`、iteration 289--309 平均 `52.070 min`；14 records
  SHA256 `a649998d...55a1f`。未取消、未改参、未启动 Stage B。

## 2026-08-16 13:30+08:00 Gurobi 参数边界复审

- strict Base/744 h 实际参数为 `BarConvTol=1e-8/FeasOpt=1e-7/NumericFocus=2/ScaleFlag=2/
  Crossover=2/CrossoverBasis=1`；当前矩阵、目标与 RHS 正值跨度分别约 `6.24e9/3.85e9/3.68e11`。
- Gurobi 官方说明支持当前执行边界：BarConvTol 可换取 Barrier 速度但可能转移成本到 Crossover；
  NumericFocus 越高数值保护越强且更慢；Feas/Opt 是绝对容差并非修复数值问题的首选；
  CrossoverBasis=1 更慢但更稳健。
- 因工程候选 `FeasOpt=1e-5` 比最小 `1e-6` 系数还大一个数量级，它们继续严格
  engineering-only。后续速度选择看 exact macro、V5 与长时域，不把 `1e-5` 直接升级 Stage B。
- ParaCloud `4139552` 不变；13:29 已到 iteration 309、stderr 0。fixed strict reference 13:29
  iteration 22、stderr 0、available RAM 约 96 GiB、memory PSI 0；supervisor 仍只等待。

## 2026-08-16 13:28+08:00 relaxed campaign 汇总器完成真实三根验证

- 新增纯读取 `scripts/summarize_relaxed_barrier_campaign.py`，统一输出 JSON/CSV 的 rc、wall、solver
  runtime、Barrier iterations/平均单步、GNU/进程树内存峰值、solution quality、checkpoint、工程 raw QC、
  根目录科学产物隔离、LP identity 与 macro exact A/B。py_compile 与联合测试 `5/5 PASS`。
- 活动 fixed checkout 未部署；脚本经 stdin 读取三根历史 candidate，权威输出位于 continuation 控制根
  `pre_exact_candidate_summary_v2.{json,csv}`，SHA256 为 `f1f95348...82a688`、
  `e15331e5...a6cf50`。三根均 rc 0、OPTIMAL、complete engineering checkpoint，root scientific
  QC/manifest/state/basis 均 absent。
- 观测 Barrier 单步：NumericFocus2 的 `5e-2/1e-2` 为 `31.643/32.573 s`，NumericFocus1 的
  `1e-2` 为 `14.862 s`；对应 solver runtime `4927.57/5289.26/4275.73 s`。因此最快路线的优势来自
  单步因子成本下降，尽管 iterations 为 `263`，高于另外两根的 `144/151`。
- pre-exact macro 列仍来自错误旧 reference，仅用于 parser 验证，禁止选择 winner。13:27 strict
  reference iteration 16、stderr 0；supervisor 继续等待，云端任务未修改。

## 2026-08-16 13:21+08:00 strict 744 h 已进入 Barrier；continuation supervisor 等待

- strict reference LP 为 `3,735,087` variables、`4,454,178` constraints、`40,395,436` nonzeros，
  Gurobi Fingerprint `0x7e66559b`=`2120635803`，与三条 relaxed candidates 相同。Presolve
  `226.12 s` 后为 `3,007,552 × 2,780,968`、`31,165,413` nonzeros；ordering `99.29 s`，
  Barrier iteration 0 于 runtime `363.60 s` 开始。
- 13:20 iteration 3，stderr 0；Gurobi current/max memory `12.61/21.36 GiB`。独立 5 分钟资源采样
  PID `4059299` 已记录 Python RSS `1.90/7.92/17.39 GiB`，host available RAM 当前约 96 GiB，
  swap 累计计数仅有背景级变化、memory PSI 0。
- continuation supervisor PID `4100799` 已 reparent 到 PID 1，只在 `sleep 300` 等待 reference；
  控制根为 `/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1`，预定新输出根
  尚不存在。门禁为 reference rc 0、stderr 0、`OPTIMAL + QC PASS + result manifest`；失败即停止。
- 门禁通过后仅建立指向三个旧 candidates 的 symlink，不重跑它们；在新控制根重算 exact A/B，随后
  只让最快 exact `MACRO_PASS` 严格串行进入 V5/744、Base/1488、Base/2160（最后一根还要求 1488
  checkpoint 完整）。当前服务器仍只有 strict reference 一个 solver；活动 checkout 不变。
- ParaCloud `4139552` 未修改，继续不取消、不改参、不启动 Stage B。

## 2026-08-16 13:08+08:00 current-identity strict Base/744 h reference 已启动

- local、`origin`、GitHub 与 fixed server 均为 `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`；
  fixed server clean，Gurobi 13.0.2 完整回归 `184/184 PASS`（`94.693 s`）。启动前无活动
  CISPO/Gurobi，available RAM 约 114 GiB、swap 968 MiB/2 GiB 但 `si/so=0/0`、memory PSI 0。
- strict reference wrapper PID `4046161`，输出根
  `/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2`，
  控制根为对应 `run_control/`。边界为 2030 Base、hour 0--743、
  `barrier_16_crossover2_stable_basis_long_v1`；即 `Method=2/Threads=16/Presolve=2/Crossover=2/
  CrossoverBasis=1/TimeLimit=86400 s/SoftMemLimit=80 GiB`，未导出 diagnostic state。
- 启动后 wrapper→time→Python 进程树正常，stderr 0；available RAM 约 113 GiB、`si/so=0/0`、
  memory PSI 0。fixed server 内部仍严格单求解，不在 active PID 上部署或改参数。
- ParaCloud `4139552` 未修改：13:07 `RUNNING` 10 天 11:49，iteration 308、solver runtime
  `902,426.19 s`，Gurobi primal/dual/compl `0.901/1.26e-6/0.272`；stderr 0，solve report/QC/result
  manifest/checkpoint 全部不存在。继续不取消、不改参、不启动 Stage B。
- 下一步：strict reference 退出后做完整终态与 LP 身份审计，再对三根 relaxed candidate 另写 exact-LP
  A/B 报告；不得覆盖旧的 invalid-reference 报告。只有 exact `MACRO_PASS` 最快者晋级 V5/744 与更长时域。

## 2026-08-16 13:02+08:00 relaxed 744 h campaign 已完成，但旧宏观 reference 身份无效

- fixed-server campaign `/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1`
  已严格串行完成 3 根 Base/744 h，均 rc 0、stderr 0、Gurobi `OPTIMAL`、完整工程 BarX/BarPi
  checkpoint，且根目录 scientific QC/manifest/state/basis 保护全部通过。campaign PID `3074785`
  已退出；13:02 fixed server clean `6477f42`、无求解、available RAM 约 114 GiB、swap 968 MiB/2 GiB
  且 `si/so=0/0`、memory PSI 0。
- `BarConvTol=5e-2`：wall `1:28:31`、solver `4,927.57 s`、Barrier 144、MaxRSS
  `19,959,364 KiB`；`1e-2/NumericFocus=2`：`1:34:34`、`5,289.26 s`、151、
  `19,802,092 KiB`；`1e-2/NumericFocus=1`：`1:17:32`、`4,275.73 s`、263、
  `19,486,068 KiB`。三根严格 solver/physical QC 均 HARD_FAIL，但未被误标科学结果。
- 原 `winner.json=NO_MACRO_PASS` 不能解释为参数科学失真：campaign 错用了旧 strict root
  `...744h_jan0_3f123f0_base_v1/2030`。旧根绑定 2026-07-30 数据、Git `3f123f0`、LP Fingerprint
  `-1670477391`；候选绑定 2026-08-05 Power_curve v3_qc 数据、Git `6477f42`、Fingerprint
  `2120635803`。负荷 SHA 与多个 flex/EV 文件也不同，`period_load` 因而相差 `0.2732%`。
  三根的耗时/资源证据仍有效，但既有宏观 A/B 与速度比不是 exact-LP 对照。
- 修补提交 `c53bd78` 现要求同一 baseline/scientific/scenario/formulation identity、同一非 solver
  input manifest、同一 LP variables/constraints/nnz/Fingerprint，并要求 reference
  `OPTIMAL + solution_qc PASS + result_manifest`；solver profile 允许不同。source bundle 是否相同
  单独记录但不作为 LP 门禁，以允许纯审计/导出代码更新。py_compile 与 targeted `4/4 PASS`。
- 精确下一步：双推送并部署 `c53bd78`，server 全回归后在当前 tip/当前数据新建单独 strict
  Base/744 h reference（Crossover=2，不导出 state）；完成后重算已有三根 exact A/B。只有 exact
  winner 才进入 V5/744、Base/1488 与 Base/2160，不再重复无信息的宽松候选。
- ParaCloud `4139552` 未修改：13:02 仍 RUNNING 10 天 11:44，latest Barrier iteration 308、
  runtime `902,426.19 s`、primal/dual/compl `3.376/2.02e-6/0.2725`、stderr 0，无终态/checkpoint。

## 2026-08-12 21:45+08:00 第二次 1 h smoke 定位 master-export QC；分阶段修补已提交

- 新根 `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_0d773d5_v2` 的 Python/time 终态为
  rc 0，wall `0:37.84`、MaxRSS `496,276 KiB`、stderr 0；求解结果与首次完全一致：`OPTIMAL`、
  Barrier 49、solver `2.847 s`、checkpoint 完整。外层远端审计命令仅在求解完成后因 `$rc` 转义错误
  以 shell rc 1 退出，并把 `return_code.txt` 误写为字面 `$rc`；`time.txt` 的 `Exit status: 0` 与模型
  文件证明 Python 本体成功。该 wrapper 元数据错误已保留，不重标历史文件。
- 第二次 smoke 证明 load-center 双向流拒绝实际发生在 `export_master_solution()`，早于 operational
  export；因此提交 `cc9293b` 的捕获层级仍不足，未生成 raw-QC file/annual summary/contract。新提交
  `247c3020dc7c667e161d61a331ff81d8b5f616fe` 把 master、operational、summary 拆成独立阶段：仅预期的
  `Load-center/Production solution QC failed` 可被记录并继续，磁盘错误、编程错误等非 QC 异常仍立即
  重新抛出；summary 在严格 QC 失败后继续生成。
- 本地 py_compile 与新增 targeted `3/3 PASS`。一次 Windows 完整回归因错误环境先快速失败；改用 RL
  环境后又异常长时间无终态，已终止且不计入 PASS。下一步双推送，在 clean/idle fixed server 部署，
  以权威环境执行完整 `182` 项回归和第三个全新 1 h smoke；未闭合前不启动 744 h。

## 2026-08-12 21:28+08:00 relaxed Barrier 1 h 真解暴露导出边界；保留宏观证据的修补已提交

- fixed server 的首次 Base/1 h `BarConvTol=5e-2` 烟雾根为
  `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_9f5c2ca_v1`。wrapper 正常退出，wall
  `1:44.92`、MaxRSS `497,512 KiB`、stderr 0；Gurobi `OPTIMAL`，Barrier 49 次、solver
  `2.829 s`，完整工程 checkpoint 已先保存：BarX `238,529` 项、BarPi `80,143` 项，均为 finite，
  `scientifically_accepted=false`。
- 该极宽松解没有通过严格解质量：ConstrVio `4.04e-6`、BoundVio `3.78e-9`，但 DualVio
  `0.628`、ComplVio `29.509`，最后一次 telemetry 的 primal--dual relative gap 为 `1.389%`。
  原始物理导出还检测到双向最小流最大 `3.599 GWh`、合计 `76.294 GWh`、640 条活动边，因而按既有
  load-center QC 抛错。根目录仍无 scientific `solution_qc/result_manifest`、planning state 或 basis，
  隔离边界有效；此结果明确不是科学解。
- 修补提交 `cc9293b25ef66ff4642eeb5860fb00b0a938b5ba` 让严格原始 QC 失败时写入
  `engineering_raw_qc_error.json`，同时继续导出未接受的宏观汇总与 analysis contract；宏观审计也能
  在缺少严格 `solution_qc.json` 时保留失败原因。它不改变 LP、solver profile、严格 QC 或晋级阈值。
  本地 py_compile、focused test 与完整 `181/181 PASS`。下一步为双推送、fixed server clean fast-forward、
  server 回归及全新 1 h smoke；复测闭合后立即启动唯一串行 744 h campaign。
- 21:28 fixed server 仍 clean/idle `9f5c2ca`，available RAM 约 `114 GiB`、连续 `si/so=0/0`、memory
  PSI 0、`/data` 余 `3.6 TiB`。ParaCloud job `4139552` 未触碰，仍 `RUNNING` 6 天 20:10；最新
  iteration 202、runtime `587,056.87 s`、MaxRSS `380,541,576 KiB`、stderr 0，无终态或 checkpoint。

## 2026-08-12 12:05+08:00 fixed-server relaxed Barrier campaign 已实现、尚未部署

- 作者授权保持 ParaCloud `4139552` 运行，同时在 fixed server 严格串行测试显著宽松的 744 h
  和更长时域。实时 fixed server 为 clean `3f739fd`，无 CISPO/Gurobi solver，Gurobi 13.0.2，
  available RAM 约 114 GiB、swap 976 MiB/2 GiB 且连续 `si/so=0/0`、memory PSI 0、磁盘余
  3.6 TiB。两个 8 月 5 日遗留 bash/grep 只读审计管道无 Python/Gurobi 子进程，不是第二求解。
- 云 job 未修改：iteration 191 于 12:04:31 落盘，runtime 554,846.21 s；Slurm MaxRSS
  362.913 GiB、stderr 0，`solve_report.json`、`solution_qc.json`、`result_manifest.json` 与
  checkpoint 均不存在。继续禁止人工取消、Stage B 或第二个云任务。
- 实现提交 `9308ac002161a0b7971c28db8e46b5f42e8b91a8` 的新路线只在显式
  `--engineering-barrier-checkpoint-only
  --engineering-relaxed-barrier-analysis` 下工作。3 个 744 h profiles 扫描
  `BarConvTol=5e-2/1e-2` 和 matched `NumericFocus=1`；`FeasibilityTol/OptimalityTol=1e-5`，
  无 Crossover。宽松解的完整 `BarX/BarPi` 与宏观 outputs 分层保存，后者永不生成科学 manifest/
  state/basis。自动 campaign 在 3 个 744 h Base 之后只允许最快 `MACRO_PASS` 进入 V5/744 h、
  Base/1488 h 和最多 Base/2160 h，全程单实例。
- 本地验证为 focused `31/31`、完整 `180/180 PASS`、py_compile/JSON/diff PASS。尚未提交、部署或
  启动任何 fixed-server solve；Linux `bash -n`、server full regression 和 1 h 真解烟雾门禁仍是
  744 h 启动前置条件。

## 2026-08-12 11:50+08:00 Barrier iteration 190，资源审计 round 12

- job `4139552` `RUNNING` 6 天 10:32:11；iteration 190 于 11:18:12 落盘，solver runtime
  552,067.53 s。iteration 158--190 平均 47.571 分钟/步，速度稳定。
- 最新 Gurobi primal/dual residual/complementarity 为 `4.00e1/9.35e-7/2.37e1`；objective 相对
  间距由 iteration 158 的 `3.69` 缓慢降至 `3.21`。仍在推进，但长尾明显且尚未收敛。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  14,835.493 core-hours、actual CPU 2,300.554 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 12 共 13 records，SHA256
  `e299d4c7821a0e6e372b44182c3dc239179b58bea5ccfa784a4cc841a77b776d`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-11 10:16+08:00 Barrier iteration 158，资源审计 round 11

- job `4139552` `RUNNING` 5 天 08:58:07；iteration 158 于 09:55:55 落盘，solver runtime
  460,730.61 s。iteration 145--158 平均 47.263 分钟/步，速度稳定。
- 最新 Gurobi primal/dual residual/complementarity 为 `6.97e1/1.92e-6/4.63e1`；objective 相对
  间距由 iteration 145 的 `3.90` 缓慢降至 `3.69`。仍在推进，但已是明显数值长尾，尚未收敛。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  12,380.987 core-hours、actual CPU 1,906.975 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 11 共 12 records，SHA256
  `467e4f1bba55a0fac1c9947d444e8f45d3e32fc247b043c0e0dfa76d9c8dc6b4`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-10 23:43+08:00 Barrier iteration 145，资源审计 round 10

- job `4139552` `RUNNING` 4 天 22:25:36；iteration 145 于 23:41:30 刚落盘，solver runtime
  423,865.48 s。iteration 116--145 平均 47.530 分钟/步，计算节奏稳定。
- 相对 iteration 116，telemetry primal/dual infeasibility 与 complementarity 再缩小
  `6.61/4.71/4.81` 倍；最新 Gurobi 三项为 `8.16e1/3.23e-6/5.61e1`。objective 相对间距由
  `8.56` 降至 `3.90`，说明仍有推进，但依然是长尾而非已收敛状态。
- Slurm MaxRSS 362.913 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  11,368.96 core-hours、actual CPU 1,744.324 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 10 共 11 records，SHA256
  `581e3c52d5a087f38368cf35f9396a67c7561e612d91b2059b9f19537db3bba0`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-10 00:47+08:00 Barrier iteration 116，资源审计 round 9

- job `4139552` `RUNNING` 3 天 23:29:30；iteration 116 于 00:43:08 落盘，solver runtime
  341,163.39 s。iteration 77--116 平均 47.499 分钟/步，未发生持续性能退化。
- 相对 iteration 77，telemetry primal/dual infeasibility 与 complementarity 又缩小
  `82.48/36.26/42.62` 倍；最新 Gurobi 三项为 `5.40e2/1.52e-5/2.70e2`。近期收敛已转入较缓长尾，
  primal/dual objective `2.28e9/-1.72e10` 相对间距约 `8.56`，尚不能声明临近完成。
- Slurm MaxRSS 362.909 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  9,167.2 core-hours、actual CPU 1,391.305 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 9 共 10 records，SHA256
  `9aa1f051e406b4bdfd5056f0dec90303e4d5ad3b18a0faf360cd18580bf9052b`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-08 17:51+08:00 Barrier iteration 77，资源审计 round 8

- job `4139552` `RUNNING` 2 天 16:33:41；iteration 77 于 17:50:39 刚落盘，solver runtime
  230,014.78 s。iteration 48--77 平均 46.061 分钟/步，整体节奏稳定。
- 相对 iteration 48，telemetry primal/dual infeasibility 与 complementarity 已分别缩小约
  `82,964/832,887/57,100` 倍；Gurobi 表内最新三项为 `4.45e4/5.22e-5/1.15e4`。这是明显推进，
  但 primal/dual objective `4.98e10/-5.30e11` 尚未闭合，不能声明收敛或给完成百分比。
- Slurm MaxRSS 362.765 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  6,197.893 core-hours、actual CPU 915.299 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 8 共 9 records，SHA256
  `f0c7fdfa03c0ab39c5a1ace6739ea5a337b7dd0b22de7e83d37c4f5bde09ede0`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-07 19:45+08:00 Barrier iteration 48，资源审计 round 7

- job `4139552` `RUNNING` 1 天 18:27:23；iteration 48 于 19:34:53 落盘，solver runtime
  149,868.82 s。iteration 35--48 平均 46.951 分钟/步，计算节奏稳定。
- 相对 iteration 35，telemetry primal/dual infeasibility 与 complementarity 分别下降
  `77.27%/84.52%/77.95%`；目标和残差继续改善，但绝对量级仍不能声明收敛或完成比例。
- Slurm MaxRSS 362.649 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  4,075.813 core-hours、actual CPU 572.464 h。stderr 0，无 warning/numerical trouble/error。
- 终态报告、QC、result manifest 和 checkpoint 均不存在。资源账本 round 7 共 8 records，SHA256
  `d691d087fec95263c77e62530befa58cac9b0aed6a986a55a9b992535305badc`。继续不取消、不改参，
  不启动 Stage B/第二求解。

## 2026-08-07 09:59+08:00 Barrier iteration 35，资源审计 round 6

- job `4139552` 仍为 `RUNNING`，wall 1 天 08:41:08、96 CPU/700G、`TimeLimit=UNLIMITED`；
  iteration 35 于 09:24:32 落盘，solver runtime 113,247.02 s，正在计算下一轮。
- iteration 23--35 平均 47.032 分钟/步（8--35 平均 47.112）；同期 telemetry primal/dual
  infeasibility 与 complementarity 分别下降 `78.29%/76.82%/77.52%`，dual objective 继续向
  primal 方向回转。绝对残差和目标间距仍很大，不能据 iteration 序号外推完成百分比。
- Slurm MaxRSS 362.540 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  3,137.813 core-hours、actual CPU 421.861 h。stderr 0，日志无 warning/numerical trouble/error。
- `solve_report.json`、`solution_qc.json`、`result_manifest.json` 与 checkpoint 均不存在。
  resource audit round 6 已追加，共 7 records，SHA256
  `13e567bd1743c5b0079ebb7445123bb18f6cba05a5e7be208f9619592c2c6175`。继续不取消、不改参、
  不启动 Stage B/第二求解。

## 2026-08-07 00:00+08:00 Barrier iteration 23，资源审计 round 5

- job `4139552` `RUNNING` 22:42:29，iteration 23 于 00:00:09 刚完成；solver runtime
  79,383.98 s。iteration 18--23 平均 47.105 分钟/步，iteration 8--23 平均 47.175 分钟/步，
  长时速度稳定。
- 相对 iteration 18，telemetry primal/dual infeasibility 与 complementarity 分别下降
  `42.9%/54.9%/45.6%`；dual objective 持续向 primal 方向回转。仍未接近验收容差，不给完成百分比。
- Slurm MaxRSS 362.344 GiB、Gurobi current/max 351.054/354.498 GiB；累计 allocation
  2,179.973 core-hours、actual CPU 267.629 h。stderr 0、无数值警告，无终态/checkpoint文件。
- resource audit round 5 已追加，共 6 records，SHA256
  `73f3df3998f4313051231658dd35dc8ccaeb1f8c3c23ccec5efa7a0e4c30d967`。继续不取消、不改参、
  不启动 Stage B/第二求解。

## 2026-08-06 20:27+08:00 Barrier iteration 18，资源审计 round 4

- job `4139552` 仍为唯一活动 cloud task：`RUNNING` 19:08:54、96 CPU/700G、无限时长。
  iteration 18 于 20:04:37 落盘，solver runtime 65,252.49 s；iteration 8--18 平均
  47.210 分钟/步，未出现持续变慢。
- 相对 iteration 8，Gurobi 表内 primal residual/dual residual/complementarity 分别下降约
  `74.4%/78.0%/75.1%`；dual objective 在 iteration 14 后开始回转，但仍是早期 Barrier，不能
  换算完成比例或声称接近收敛。日志无 warning/numerical trouble/error，stderr 0。
- 当前 Slurm MaxRSS 362.188 GiB，Gurobi current/max memory 仍为 351.054/354.498 GiB；累计
  allocation 1,838.24 core-hours，实际 CPU 212.941 h。终态三文件和 checkpoint 均不存在。
- `resource_audit_snapshots.jsonl` 已追加 round 4，共 5 records，当前 SHA256
  `fb390f551ef190720673a341037e2bcd8b6ce006905b549268a27c4f0f418c7f`。继续禁止人工取消、
  Stage B、第二求解或重提；资源账本仅在审计时旁路更新，不修改 solver/output。

## 2026-08-06 12:16+08:00 iteration 8 与全程资源审计已固化

- job `4139552` 仍为 `RUNNING`；iteration 8 于 12:12:31 落盘，solver runtime 36,926.33 s，
  该步耗时 2,724.09 s（45.40 分钟）。12:16 Slurm MaxRSS 361.648 GiB、累计实际 CPU
  86.877 h、累计 allocation 约 1,054.24 core-hours，stderr 0。除非作者明确授权，禁止人工取消；
  作业自身终态仍按报告/checkpoint合同审计。
- 当前 control root 新增只读审计产物：`resource_audit_snapshots.jsonl`（4 records，SHA256
  `7ecb6006...5dae10`）记录 launch/iteration 7/iteration 8 的 Slurm 快照与禁止取消策略；
  `historical_8760_comparison.json`（SHA256 `2e77c8ef...fc7f6`）冻结与旧 job `4004585` 的同口径比较。
  每个 Barrier iteration 继续由 `solver_telemetry.jsonl` 自动记录 runtime/work units/residual/memory；
  人工审计追加 Slurm elapsed/CPU/RSS，终态再以 `sacct` 汇总总资源。
- 旧 `4004585` 同样是完整 8760 h LP，只是墙钟限制 24 h，并非 24 h 时域；它最终 `TIMEOUT` 于
  iteration 35、无 accepted result。当前相对旧模型：raw rows/cols/nnz 为 `-25.344%/+1.335%/-4.311%`；
  presolved 为 `-0.734%/-9.194%/+0.848%`；Factor NZ/Ops 为 `-11.772%/-21.119%`，当前 sampled
  MaxRSS 低 `24.145%`。但当前 16 threads 对旧 32 threads，近期单步约慢 50%，且科学模型/数据已变，
  不能直接比较目标与残差大小。

## 2026-08-06 12:06+08:00 2030 Base 8760 h Stage A 已进入 Barrier iteration 7

- ParaCloud job `4139552` 仍为唯一活动任务，`RUNNING` 10:48 于 `m4cm1901`；96 CPU/700G、
  billing 96、`TimeLimit=UNLIMITED`。Slurm stderr 仍为 0 bytes，日志未出现 warning、numerical
  trouble 或 error；58 秒采样中累计 CPU 增加约 15.5 分钟，证明 16 个 Gurobi threads 正在工作。
- model build 于 01:57 完成，耗时 2,336.984 s、build peak RSS 48.574 GiB。实际原始 LP 为
  `41,458,383 vars / 50,907,234 rows / 492,835,195 nnz`，fingerprint `0xd16b4c7e`；presolve
  17,414.51 s 后为 `32,166,850 vars / 37,703,954 rows / 404,259,819 nnz`，ordering 2,912.17 s。
- Barrier 当前最新落盘 iteration 为 7（11:27:07，solver runtime 34,202.25 s）。iteration 3--7
  间隔约 44.6/47.0/48.1/47.7 分钟；12:06 正在计算 iteration 8。表内 primal residual 从
  `6.77e11` 降至 `5.32e11`、complementarity 从 `1.28e11` 降至 `1.02e11`，仍属极早期，不能据此
  判定收敛或失败。Factor NZ `3.395e10`，Gurobi 估算 factor memory 约 300 GB。
- Slurm MaxRSS `379,125,920 KiB`（约 361.6 GiB），Gurobi current/max memory 约
  `351.1/354.5 GiB`；尚未触及 600 GiB soft limit 或 700 GiB allocation。当前无 solve report、
  QC、result manifest 或 checkpoint，继续只读监控，禁止 Stage B/第二求解。

## 2026-08-06 01:19+08:00 2030 Base 8760 h Stage A v2 已稳定进入 model build

- 当前唯一活动 cloud job 为 `4139552`，`RUNNING` 于 `m4cm1901`，开始时间 01:17:53；
  `Req/AllocTRES=cpu=96,mem=700G,billing=96`、`TimeLimit=UNLIMITED`，无依赖任务。Gurobi profile
  仍为 16 threads、Crossover=0、SoftMemLimit=600 GiB；不会自动 Stage B/2040/V5。
- 有效 release：
  `$HOME/National_model_cloud/20260806_8760_stagea_3f739fd_v5`，Git `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`，
  Linux archive SHA256 `c49d48da070834b969b13b7a4ea50d0b45c5383276820db0e314d324822ec40e`；
  私有 xarray wheel SHA256 `a7ad6a36...a7f8d6`，共享 conda env 未修改。
- compute data-load gate `4139550` 为 `COMPLETED 0:0`：41.69 s、321,264 KiB、0 swap；31×8760、
  36,686 VRE sites、2,030 hydro stations 与 wave 全载入。主 job 已通过 profile、provenance、input
  manifest、67 PASS/3 WARN/2 INFO/0 HARD_FAIL preflight；full-year scale estimate 为
  `41,186,823 vars / 55,928,698 rows / 497,144,574 nnz`，available 732.26 GiB。
- 01:19 主 job 已越过前三次 fail-fast 点，处于 LP model build；MaxRSS 3,986,620 KiB，Slurm stderr
  0 bytes，尚无 `gurobi.log`/telemetry/build report。继续只读监控，不提交任何第二任务。

## 2026-08-06 01:13+08:00 第三次提交在 wave 数据加载前 fail-fast；补齐私有 xarray overlay

- v4 的低成本 job `4139494` 已证明 profile、代理/WLS 与 Gurobi 13.0.2 小 LP `PASS`。主 job
  `4139496` 完成 provenance/input manifest 后，因 cloud Python 缺 `xarray` 在 wave store 初始化
  前退出；Slurm elapsed 7 秒，无 LP build、`gurobi.log` 或 telemetry。
- cloud 现有环境已含 `netCDF4=1.7.2/cftime=1.6.5/numpy=2.2.6/pandas=2.3.2`，仅缺 xarray。
  fixed server 已有纯 Python wheel `xarray-2025.1.2-py3-none-any.whl`，SHA256
  `a7ad6a36c6e0becd67f8aff6a7808d20e4bdcd344debb5205f0a34b1a4a7f8d6`。
- 不修改共享 cloud conda env；下一 release 使用私有 `python_overlay` + `PYTHONPATH`。先以低资源
  compute job 完整执行 `load_model_data(Base/8760)`，通过依赖/数据加载后才可再提交 96/700G。
  job `4139496` 与 v4 release 不复用。

## 2026-08-06 01:10+08:00 第二次提交在 provenance 前 fail-fast；环境导出已修复

- job `4139479` 先通过 `STAGE_A_PROFILE_PREFLIGHT_PASS`，随后因四个 `CISPO_*_ROOT` 仅被
  shell `source`、未 export 给子 Python 而在 `write_run_provenance` 前退出。Slurm elapsed 5 秒，
  runner wall `1.09 s`、peak RSS `83,900 KiB`、swap 0；没有 LP build、Gurobi log/telemetry 或求解。
- 修复提交 `b5cad0dee02f0f2ac7c8368b778f68dde0796826` 使用 `set -a/source/set +a`，并把该导出
  合同加入 wrapper 静态测试；profile suite 继续 `9/9 PASS`。
- job `4139419/4139479` 与 cloud `_v1/_v2/_v3` 均为只读失败证据，不得重提或补写结果。
  下一步是双推送/deploy `b5cad0d`，以 Linux archive 创建 `_v4`，重复语法/调度预检后只提交
  一个全新 Stage A。

## 2026-08-06 01:06+08:00 首次提交 0 秒失败；未求解，wrapper 已修复

- cloud 无计费 `sbatch --test-only` 接受 `96 CPU/700G`。首次实际 job `4139419` 的
  `ReqTRES/AllocTRES=cpu=96,mem=700G,billing=96`、`TimeLimit=UNLIMITED`，但在 0 秒、
  `TotalCPU=0.007 s/MaxRSS=0` 时 `FAILED 1:0`；Slurm stdout/stderr 均为 0 bytes，未进入 Python、
  模型 build 或 Gurobi，不是数值/模型失败，也没有持续计费。
- 原因是 Slurm 执行 spool copy，旧 wrapper 从 `$0` 推导 release 根会落到 spool 路径。
  修复提交 `d857f8d2a0724bc7d89856aea70042977b2f9b0a` 改用提交时固定的
  `SLURM_SUBMIT_DIR`，并新增静态回归，profile tests `9/9 PASS`。
- Windows tar 导出的 CRLF `_v1` 与上述 job 所在 `_v2` release 均保留为失败证据；二者不复用。
  精确下一步是双推送/deploy `d857f8d`，用 fixed-server Linux archive 建立全新 `_v3` release，
  再次 `bash -n + sbatch --test-only` 后仅重提一个 Stage A。

## 2026-08-06 00:57+08:00 2030 Base 8760 h Stage A v2 已实现，待部署提交

- 实现提交 `6f0b1f7286a5ba479eabff3df2b14c2f8cf6bbb6` 新增
  `barrier_checkpoint_full_year_cloud_v2`：`Method=2/Threads=16/Presolve=2/Crossover=0/
  SolutionTarget=1/BarConvTol=1e-8/FeasibilityTol=OptimalityTol=1e-6/MarkowitzTol=0.01/
  NumericFocus=2/ScaleFlag=2/Aggregate=1/SoftMemLimit=600 GiB`，Gurobi `TimeLimit` 显式为
  `null`，因此保持 solver 默认无限；Slurm wrapper 也不设置 wall time。
- 新 runner 路径保持 Stage A 工程身份：完整 `BarStatus=OPTIMAL` 后先保存 finite `BarX/BarPi`；
  如果外部中断且未完成 Barrier，只在属性仍可读时尽力保存 `RECOVERY_ONLY`，其
  `deferred_crossover_eligible=false`。Stage A 不写 scientific manifest/planning state，也不会
  自动启动 Stage B、2040 或任何情景。
- 本地 py_compile PASS；solver profile `8/8`、checkpoint `5/5`，完整回归 `179/179 PASS`。
  00:49 实时核验 local/origin/GitHub/fixed server 均为前一 clean tip `ad662c8`，fixed server
  idle、available 约 113 GiB、无 swap I/O/PSI；ParaCloud 队列为空。云分区
  `amd_a8_768` 为 `DefaultTime=NONE/MaxTime=UNLIMITED`。
- 已准备单任务 wrapper，申请 `96 CPU/700G` 但 Gurobi 只用 16 threads；相对 128 CPU 请求可将
  计费 TRES 降低 25%（以调度器 `--test-only` 和实际 `sacct` 为准）。此状态点尚未提交付费 job；
  下一步是双推送、clean 部署、建立不可变 cloud release、无计费调度预检后只提交一个 Stage A。

## 2026-08-05 20:35+08:00 Power_curve v3_qc 已部署 fixed server 并同步 ParaCloud

- fixed server clean implementation HEAD `3cb3939197c3915a5a679a15c9a42e651c320534`；新数据根
  `/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1` 为 78 files、
  127 MiB，tree SHA256 `4e5ba9c5057ff18a2c7267395d69ce292b8f5347453dc57f9dcd892af45886e0`。
  旧生产根与历史 outputs 未改。
- data smoke `142/142 PASS`，完整 unittest `178/178 PASS`，release/readiness/V4/V5 全 PASS。
  首次 v1 smoke 暴露旧精简根缺 16 个当前 QA/support tables，失败记录保留；v2 全闭合。
- 全新四年 Base/V5 1 h 与 24 h 共 16 roots 全部 `ACCEPTED`；两份 A/B audit PASS，无 basis、
  无并发、无 swap，且全部为 `TEST_ONLY_TRUNCATED_HORIZON`。
- ParaCloud 有效 file release 为
  `$HOME/National_model_cloud/20260805_power_curve_v3_qc_3cb3939_v2`，5.5 GiB；code、model-ready、
  CF、hydro、wave 的 archive/tree hashes 全闭合。队列为空、未提交 cloud job。raw GRFR 8.3 GiB
  未复制，故 cloud `--require-raw-grfr` readiness 未执行；无 `_v2` 的 sibling 为无效 clone 尝试。
- 当前无 fixed-server CISPO/Gurobi process；本任务不授权 168/744/8760 h 或付费云求解。

## 2026-08-05 16:05+08:00 本地负荷已切换到 Power_curve_V2 v3_qc；服务器未变

- 本地权威上游现为 `Power_curve_V2/outputs/future_8760_projection_ev_calibrated_v3_qc/tables/
  future_hourly_load_2025_2060_8760.csv.gz`，SHA256
  `8ed727745afda68b7114b08ea65660392cb374b68f203a6633bbbc9a13af791a`。
- 本地 `data/load/hourly_load_2025_2060.csv.gz` 已替换为五模型年转换，SHA256
  `bd94df0fd192c31e553ec9df7e486c90cc51ce2f9cd063cc660e499dce0c9903`；31省×5年×8760 h、
  key/datetime/单位/组件闭合全部通过。EV 年电量较旧本地输入提高 4.219004%，base residual 回算，
  全国总负荷年电量和冷热分量不变。
- `hourly_load_2030_2060.csv.gz`、`annual_load_summary.csv`、V3 envelope、V4/V5 EV 派生输入及
  manifests 已同步重建；V4/V5 sidecar 均直接绑定新负荷主表 SHA256。data smoke `142/142 PASS`，
  相关 unittest `23/23 PASS`。
- 这是 **local-only data milestone**。截至该里程碑时点，固定服务器 checkout、当前版本化数据根、输出和
  ParaCloud 均未改变；此前 accepted roots 继续绑定旧 input manifest，不能
  重标为新负荷结果。部署需另建数据根并重新完成 release/readiness/短门禁。

## 2026-08-05 14:50+08:00 两阶段 8760 h 合同已实现，尚未启动

- implementation `369506010b5bc876676941e456d9574187e0f293` 已双推送并部署到 fixed
  server；server checkout clean/idle，targeted Gurobi 13.0.2 tests `12/12 PASS`。本次只做
  Git fast-forward、py_compile 和 tests，没有 model build/solve。
- Stage A `barrier_checkpoint_full_year_cloud_v1` 强制工程身份：`BarStatus=OPTIMAL` 后优先
  保存 finite raw-order `BarX/BarPi`、完整 LP/order/config/input/Gurobi 身份；即使 solver
  最终为 `OPTIMAL`，该 root 仍是 `scientifically_accepted=false`，无 scientific result
  manifest/planning state。`BarPi` 只可作工程 shadow-price 原始向量。
- Stage B `deferred_crossover2_full_year_cloud_v1` 只接受 exact-LP matched checkpoint；工程源
  需双重显式授权，使用 `PStart/DStart + LPWarmStart=2 + Crossover=2/CrossoverBasis=1`，
  不重复 Barrier。只有 Stage B 的 `OPTIMAL/QC/all checks/input/result manifest/Pi` 全闭合
  才能成为科学结果；planning state 还需单独显式授权。
- 14:50 fixed server available 约 `113 GiB`，Stage A/B profile 内建最低 available
  `640 GiB`，因此 fixed server 会在 build 前 hard-fail。ParaCloud 队列为空；
  `amd_a8_768` 为 128 CPU/750 GiB，`DefMemPerCPU=6000 MB`、`MaxMemPerCPU=6144 MB`。
  建议 job 申请整节点 `128 CPU/700G`，Gurobi 仍为 16 threads；尚未提交作业。

## 2026-08-05 14:09+08:00 744 h 耗时/profile 汇总；无 Barrier-only 744 记录

- 11 个已执行 Phase 2 744 h Base 根全部为 Crossover=2 同一 profile；9 accepted runtime
  `5.20--18.37 h`、平均 `8.89 h`、中位 `7.24 h`，Barrier/Crossover 平均约
  `2.60/6.08 h`；另两根 24 h TIME_LIMIT。峰值 RSS `18.632--21.158 GiB`。
- 服务器全部现存 solve reports 中，744 h 且 Crossover=0 的数量为 0。当前从未真正运行
  744 h Barrier-only；recovery BarX/BarPi 不改变这一事实。

## 2026-08-05 13:52+08:00 当前无已验证 8760 h solver route

- Barrier-only 当前模型 24 h 的 20 个组合均未同时通过严格 primal/dual；它只是历史设计
  目标，不是已验证 production profile。`Crossover=2` 是截断时域已冻结路线，但本轮 744 h
  只完成 9/12 Base，另有两个 Crossover TIME_LIMIT。
- 因此不能把任一路线直接外推到 8760 h，也不能把 recovery-only `BarX/BarPi` 当作
  Barrier-only 可用性证明。正式年度求解继续禁止，先做 recovery 离线审计和新 profile A/B。

## 2026-08-05 13:47+08:00 两个 timeout 根已保存 recovery-only BarX/BarPi

- Jan/2050 与 Jun/2060 均为 Gurobi 13 `BarStatus=OPTIMAL`，wrapper 因而自动保存了完整
  `BarX/BarPi` 向量；两份 checkpoint 均标记
  `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`、`scientifically_accepted=false`、
  `deferred_crossover_eligible=false`。
- 这些文件只证明 Barrier 内点向量仍可读取，不等于 accepted solution：源 solve
  `TIME_LIMIT + SolCount=0`，无 QC/result manifest/planning state，亦不含 presolve、
  factorization 或 basis。不得 resume、续接或用于科学影子价格。
- 大于 744 h 的 inline Crossover 当前默认被 runner 拒绝；8760 h 必须先用严格 accepted
  `Crossover=0` Barrier 主阶段闭合并生成 accepted checkpoint。当前模型尚未通过该门禁。

## 2026-08-05 13:42+08:00 Phase 2 停止：Base 9/12 accepted、2 timeout

- Jan/2050 与 Jun/2060 均在约 `86,400 s` 触发 `TIME_LIMIT`；Crossover 分别耗时
  `79,706.97/78,531.93 s`，日志为 `Crossover changed status from Optimal to Time Limit`。
  两根无 QC/result manifest/planning state；Jan/Jun sequence `HARD_FAIL`，Jan/2060 未运行。
- Oct/2060 严格接受：objective `2,644,370.958385 million CNY`、runtime `18,714.463 s`、
  Barrier/simplex `207/1,846,030`、peak `20.118 GiB`，contract/QC/58 checks/input/result
  manifests/Pi 全部 PASS，counterflow 与 storage/V2G overlap 0。Oct 四年 Base sequence PASS。
- Oct runner 在自动启动 V5 前因 memory PSI avg10 `0.54/0.54` fail-closed 为
  `RESOURCE_GATE_BLOCKED`；三个窗口 V5 均未启动，也不存在 V5 root。当前所有 runner/
  solver 已退出，Base 总计 `9 accepted / 2 TIME_LIMIT / 1 not run`。
- 13:42 available `116,236 MiB`、swap `596/2047 MiB`、实时 `si/so=0/0`、memory/IO PSI 0；
  ParaCloud 空，server clean `3f123f0`。不 resume 或重标失败根；下一步先做新 profile A/B。

## 2026-08-05 00:26+08:00 Base 8/12 accepted；两根 Crossover 数值风险

- Oct Base/2050 新增严格接受：`OPTIMAL + contract/QC PASS + 58/58 + Pi + current input +
  valid result manifest`，objective `2,570,488.097027 million CNY`、runtime `66,128.573 s`、
  Barrier/simplex `238/1,113,083`、peak `19.916 GiB`；counterflow、storage/V2G overlap 0。
- Jan Base/2050 与 Jun Base/2060 仍在 Crossover/simplex，runtime 约 `81,826/64,975 s`；
  中间 primal/dual infeasibility 分别约 `3.79e39/1.18e6` 与 `5.91e40/4.91e7`。Jan 距
  `86,400 s` TimeLimit 约 1.27 h。它们尚无终态，不提前判失败，但风险显著。
- Oct Base/2060 已进入 model build，尚无 Gurobi log；V5 未启动。host available
  `74,239 MiB`、swap `623/2047 MiB`、最新 `si/so=0/0`、memory PSI avg10/60
  `0.02/0.08`、IO PSI `4.70/1.93`、`/data` 余 `3.7 TiB`；control stderr 0，ParaCloud 空。
- server repo 保持 clean `3f123f0`。继续只读监控，不改活动参数、不启动第四条或部署 docs。

## 2026-08-04 13:57+08:00 Base 累计 7/12 accepted；三个下一年度活动

- 新增 Jan/2040、Jun/2050、Oct/2040 三根严格接受，均为 `OPTIMAL + contract/QC PASS +
  58/58 + Pi + current input + valid result manifest`，manifest commit `3f123f0`、72 files，
  counterflow、storage overlap、EV V2G overlap 均为零。
- Jan/2040 objective/runtime/Barrier/simplex/peak 为
  `2,695,375.706199 million CNY / 35,113.316 s / 295 / 775,050 / 19.266 GiB`；Jun/2050 为
  `2,653,537.909967 / 23,990.239 / 208 / 1,065,097 / 19.859 GiB`；Oct/2040 为
  `2,624,367.338789 / 33,408.641 / 204 / 960,431 / 20.706 GiB`。
- 当前 Jan Base/2050、Jun Base/2060、Oct Base/2050 均在 Crossover/simplex；V5 roots 均
  尚不存在。13:57 available `74,374 MiB`、swap `507/2047 MiB`、最新 `si/so=0/0`、
  memory/IO PSI 0、`/data` 余 `3.7 TiB`；全部 control stderr 0，ParaCloud 队列为空。
- server repo 保持 clean `3f123f0`。继续只读监控，不启动第四条/独立 V5，不改参数或部署
  后续 docs tip；活动 Crossover 中间 infeasibility 不作为终态判断。

## 2026-08-04 00:50+08:00 Jun/2040 与 Oct/2030 严格接受；三条 Base 继续

- Jun Base/2040 与 Oct Base/2030 均为 `OPTIMAL + contract/QC PASS + 58/58 + Pi +
  current input + valid result manifest`，manifest commit `3f123f0`、72 files，输入/结果
  validators 均 `(true, [])`；counterflow、storage overlap、EV V2G overlap 均为零。
- Jun/2040 objective `2,678,562.527479 million CNY`、runtime `26,056.710 s`、
  Barrier/simplex `227/850,993`、peak `18.632 GiB`；Oct/2030 objective
  `2,316,701.874843 million CNY`、runtime `34,852.144 s`、`223/1,071,575`、peak
  `21.158 GiB`。年度与控制 stderr 均 0 bytes。
- 当前活动：Jan Base/2040 PID `1152769` 与 Oct Base/2040 PID `2270187` 均在
  Crossover/simplex；Jun Base/2050 PID `2949044` 在 Barrier。三个 runner/sequence 均活动，
  尚无 V5 solve。00:48 available `70,941 MiB`、swap `507/2047 MiB`、实时 `si/so=0/0`、
  memory/IO PSI 0、CPU 约 `65--66% idle`、`/data` 余 `3.7 TiB`；ParaCloud 为空。
- server repo 保持 clean `3f123f0`。继续只读监控，不启动第四条/独立 V5，不改参数或部署
  后续 docs tip；新年度必须重复完整终态审计后才能记为 accepted。

## 2026-08-03 17:25+08:00 Jan/Jun Base 2030 严格接受；2040 活动中

- Jan/Jun Base 2030 均为 `OPTIMAL + contract/QC PASS + 58/58 + Pi + current input + valid
  result manifest`，且 storage/V2G overlap 0、counterflow strict zero。Jan runtime
  `24,157.126 s`、Barrier/simplex `251/751,916`、peak `19.022 GiB`；Jun runtime
  `25,642.054 s`、`218/914,644`、peak `19.366 GiB`。
- 两条已用 accepted planning state 自动进入 Base/2040；17:25 Jan Barrier 128、Jun 107。
  Oct Base/2030 仍在 Crossover，约 1.008m simplex iterations，尚无 solve/QC/result manifests。
- host available 约 `73.2 GiB`，实时 `si/so=0/0`、memory/IO PSI 0、磁盘余 `3.7 TiB`；
  所有 stderr 0，ParaCloud 为空。server checkout 固定 `3f123f0`，不启动第四条、不部署 docs tip。

## 2026-08-03 10:45+08:00 Phase 2 三个季节窗口均已启动

- Jan/Jun 两实例 max solver memory 为 `20.91/21.42 GiB`，历史峰值约 `23.13 GiB`；作者授权
  将第三实例按 24 GiB 规划，并以启动 available `>=56 GiB`、预计后备 `>=32 GiB` 替代此前
  48 GiB 保守 reserve。该变更只影响资源调度，不改 LP、profile 或 strict acceptance。
- Oct PID `4173801`，Base 根 `planning_sequence_2030_2060_744h_oct6552_3f123f0_base_v1`，
  scope `[6552,7296)`；启动 available `62,007,656 KiB`、`si/so=0/0`、PSI 0，stderr 0。
  专用 runner SHA256 `e22f1696445b88458b1927fc1e803ca8ae7ec8c2f00ccf34f2c8feb6111c6be1`。
- 当前 Jan/Jun/Oct 三条均先运行 Base 四年，再由各自 runner 自动接续 V5 四年。不得提前独立
  启动 V5，不得启动第四条；server checkout 固定 `3f123f0`，活动期间只读监控。

## 2026-08-03 08:56+08:00 Phase 2 Jan/Jun-15 两条窗口活动中

- server clean checkout 冻结在 `3f123f0`；模型实现仍为 `b2206d9`。control root
  `/data/zz2/National_model/run_control/phase2_3f123f0_v1`，runner SHA256
  `db8adbfa18821d5dd09875cf8eee7301b557172c9189c9c140e5b93c95fafa1c`。
- Jan PID `3742233`：Base 四年根 `planning_sequence_2030_2060_744h_jan0_3f123f0_base_v1`，
  2030 scope `[0,744)`；Jun-15 PID `3746869`：Base 四年根
  `planning_sequence_2030_2060_744h_jun15_3960_3f123f0_base_v1`，scope `[3960,4704)`。
  两者均为 correct Base/test-only/Crossover=2/no-basis，当前处于 2030 build。
- 08:56 available `117,797,340 KiB`、`si/so=0/0`、memory PSI 0；两个 window stderr 和
  两个 Base stderr 均为 0。当前恰有两个授权槽位，禁止第三条；Oct 等任一窗口完整 Base→V5
  结束并复核资源后才启动。PID 存在时只读监控，不部署后续文档 tip、不切参数。

## 2026-08-03 08:51+08:00 Phase 2 门槛下调；准备立即启动 Jan Base

- 作者已明确撤销 Phase 2 新 sequence 的 `available>=96 GiB` 门槛，并允许资源证据支持时最多
  并发两条。历史实测为 process-tree peak `21.484--21.92 GiB`、solver max memory 约
  `23.13 GiB`，故单实例审计上界按 `24 GiB`，不把“20 GiB”写成硬上界。
- 新单序列启动合同：available `>=64 GiB`、`vmstat si/so=0/0`、memory PSI 0、checkout
  clean/current、目标根不存在、ParaCloud 已核验；运行中 available `<48 GiB` 时不启动下一条。
  第二并发序列还要求首实例实时内存 `<=24 GiB`、预计启动后 available `>=32 GiB`、无 swap
  I/O/PSI；最多两条。
- 08:51 server clean/idle checkout `b2206d9`，available `91,889,284 KiB`（约 `87.63 GiB`）、
  `si/so=0/0`、PSI 0、磁盘余 `3.7 TiB`，ParaCloud 空队列，全部 Phase 2 候选根不存在。
  local/origin/GitHub 为 `2ddf432`；下一步提交本合同、双推送并 fast-forward server，随后立即
  启动 `start-hour=0` Jan Base 四年 744 h sequence。
- 本次只改资源调度合同；`barrier_16_crossover2_stable_basis_long_v1.json`、严格终态验收、
  `TEST_ONLY_TRUNCATED_HORIZON` 标签均不变，仍禁止 Crossover=3、basis/MGA、8760 h 与付费云。

## 2026-08-03 03:17+08:00 Phase 1 完整闭合；Phase 2 等待资源

- `/data/zz2/National_model/run_control/phase1_b2206d9_v1` 已写出 `PHASE1_DONE`；总 stderr
  为 0。1/24/168 h Base/V5 六条四年 sequences 均 rc 0，六个 time wrapper 均 exit 0。
- 三组 A/B audits 全部 `PASS`；`phase1_strict_audit.json` 复核 24/24 年度根均为
  `OPTIMAL + contract/QC PASS + 58/58 + current input/valid result manifests + Pi`，零 failures。
  24 根 storage/V2G overlap 均为零。仅 168 h Base/V5 的 2050 各有 7 个预算内 de-minimis
  counterflow edge-hours；其余 counterflow 为 strict zero。
- 当前无 CISPO/Gurobi/sequence PID。固定服务器 clean checkout
  `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；available RAM 约 `87 GiB`、swap
  `449 MiB/2 GiB`、`vmstat si/so=0/0`、memory PSI 0、磁盘余 `3.7 TiB`；ParaCloud 队列为空。
- Phase 2 仍要求新任务前 available `>=96 GiB`。当前只等待外部资源恢复，不降低门槛、不终止
  外部任务。满足后才部署双推送文档 tip，并严格串行执行 `744 h @ start 0/3960/6552`，每个窗口
  Base 四年后 V5 四年；继续禁止并发、basis、Crossover=3、8760 h、付费云和 MGA。

## 2026-08-02 23:16+08:00 Phase 1 已进入 168 h Base

- 1 h Base/V5 与 24 h Base/V5 四条四年 sequences 均 `rc=0`；逐根
  `OPTIMAL/PASS`，result manifests 完整，storage/V2G overlap 与 24 h counterflow 为零。
- 24 h 部分 Barrier 根以 sub-optimal 结束，但 Crossover=2 成功恢复 primal/dual feasible
  optimal；当前不关闭 crossover。
- wrapper PID `1314144` 仍活动，23:16:52 开始 168 h Base。启动 available
  `91,891,228 KiB`、`si/so=0/0`、PSI=0；无第二 CISPO solve，ParaCloud 为空。
- PID 存在期间只读监控。168 h Base/V5 均 accepted 后才执行 Phase 1 总审计；Phase 2
  仍须重新满足 available `>=96 GiB`。

## 2026-08-02 22:55+08:00 全新 Phase 1 活动中

- fixed server clean deployed `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；生产环境
  `177/177`、readiness、release、V5 input 和 hydro 380 GW audits 全部 PASS。
- wrapper PID `1314144`，control root
  `/data/zz2/National_model/run_control/phase1_b2206d9_v1`；22:55 正在 1 h Base，后续按
  1 h V5、24 h Base/V5、168 h Base/V5 严格串行。
- 启动 available `91,919,056 KiB`、`si/so=0/0`、memory PSI 0；无第二 CISPO solve，
  ParaCloud 队列为空。PID 存在期间不 fast-forward、不改 checkout、不启动 Phase 2。

## 2026-08-02 22:49+08:00 轻微对冲流 warning 合同已在本地闭合

- 作者决定保持 current full-LP 网络结构，不为截断时域极小系统影响的 AC 对冲流增加
  MILP/方向锁复杂度。2050/168 h storage 与 EV V2G overlap 均为零，唯一异常仍是
  7 个 AC counterflow edge-hours；其 excess-loss/load 与 opposing/gross-flow 分别仅
  `9.7667e-8`、`3.4079e-5`。
- 仅将 test-only 每 168 h 的绝对 warning budgets 调整为
  `8 edge-hours / 1.25 GWh opposing / 0.04 GWh excess loss`；单小时功率、线路占比和两个
  相对系统影响门禁不变，full-year 继续 strict zero。模型与 solver 参数不变。
- 本地方向性 `7/7`、完整回归 `177/177 PASS`。服务器尚未部署本修订，也没有从旧失败根
  resume；部署与新 Phase1 roots 必须等待提交、双推送及实时 server 门禁。

## 2026-08-02 22:19+08:00 Phase 1 在 168 h Base 2050 fail closed

- Phase1 wrapper 与本项目 Python/Gurobi 均已退出。1 h Base/V5、24 h Base/V5 四条四年
  sequence 全部 PASS；逐年复验共 16 个输出均满足 `OPTIMAL + QC PASS + 58/58 + current
  input/result manifests PASS`。
- 168 h Base：2030、2040 strict PASS；2050 的 Gurobi solve/solver acceptance 均 PASS，
  但 `solution_qc=HARD_FAIL`、hard checks `57/58`。因此 runner 未生成 result manifest 或
  accepted state，并正确停止在 2050；2060、168 h V5、Phase 2 都未启动。
- 唯一失败项为 `unidirectional_interprovincial_flow`。吉林—黑龙江
  `CORRIDOR_0153`（AC，`1.646 GW`）在一周内每天 04:00 共 7 次同时双向流，opposing
  energy `1.029728 GWh`、excess loss `0.031052 GWh`，超过 168 h test-only budgets
  `4/0.75/0.025`；最大 opposing flow `0.177690 GW`，远高于 `1e-6 GW` 数值容差。
  对应边际价最低约 `-3412.05 CNY/MWh`，与负价下 lossy-sink 机制一致，不能按数值尾差放行。
- 实时 server checkout clean `fc2c5002d774e80853f4059c506a55d2befc08f0`；available RAM
  约 `87 GiB`、swap `449 MiB/2 GiB`、`si/so=0/0`、memory PSI 0；ParaCloud 队列为空。
  当前状态是“审计阻塞”，不是资源阻塞。保持现场，不 resume、不启动 Phase 2。

## 2026-08-02 19:58+08:00 Phase 1 分级内存门禁生效

- 当前 available RAM 约 `85 GiB`、`si/so=0/0`、PSI=0；外部 wind-power workers 仍在。
- current-tip 168 h 实测 process-tree peak `<=3.651 GiB`，因此仅 Phase 1 的 1/24/168 h
  允许在 `available>=64 GiB` 时启动；运行中低于 48 GiB 或出现 swap I/O/PSI 即停止后续根。
  Phase 2 仍要求 `>=96 GiB`，未放松。

## 2026-08-02 19:53+08:00 168 h V5 调优闭合；等待共享 RAM 恢复

- `d190c23` 在正确生产数据环境下专项 `30/30`、完整回归 `175/175 PASS`。一次漏设 data
  env 的完整回归调用产生 missing-file failures，显式修正五个 roots 后通过。
- 168 h V5 Crossover=2/4 均 strict PASS；solver 分别 `2021.046/2122.079 s`，simplex
  `382,382/383,134`，峰值约 `3.65 GiB`。production winner 为 Crossover=2；4 为 fallback，
  direct dual simplex 为无 Crossover fallback，3 禁止。
- 新 long production profile 为
  `barrier_16_crossover2_stable_basis_long_v1`：16 threads、Presolve=2、Crossover=2、
  CrossoverBasis=1、TimeLimit=86400 s、SoftMemLimit=80 GiB。
- 当前无 CISPO/Gurobi 进程，但 available RAM 约 `93 GiB < 96 GiB`。外部用户多条 wind-power
  worker 正在占用 RAM；swap `449 MiB/2 GiB`、`si/so=0/0`、PSI=0。不得终止外部任务；
  Phase 1 等资源恢复后才启动。

## 2026-08-02 18:35+08:00 24 h 配对通过；168 h Base 通过、V5 被旧 guard 拦截

- 服务器 clean/idle `eb4d5591723d5ed528c8326898731591937ec645`，available RAM
  `113 GiB`、swap `447 MiB/2 GiB`、`si/so=0/0`、memory PSI 0。现行数据根为
  `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。
- Crossover 1/2/4 的 24 h Base/V5 六根全部 strict PASS。168 h Base 的 Crossover 2/4
  也 strict PASS，solver runtime 分别 `2044.630/1822.354 s`，Crossover=4 当前总耗时更短。
- 168 h V5 两个候选没有进入 Gurobi optimize：旧代码只把 Crossover=1 识别为 stable
  basic route，均在 prebuild 后约 9.5 s fail closed。正在把允许集合最小扩展为已经 matched
  24 h 验证的 `{1,2,4}`，保留 `CrossoverBasis=1` 并永久拒绝 3。部署后用全新输出根重跑，
  不 resume 两个 prebuild-failed 根。
- Phase 1/2 尚未启动；没有 8760 h、付费云、并发第二求解、basis reuse 或 MGA。

## 2026-08-01 16:53+08:00 Phase 0 完成；Barrier-only 路线被严格门禁拒绝

- 固定服务器已部署 clean `5e7db6835db60170fad7a1a13283e2a4d16792f4`；Phase 0 的
  `175/175` 回归、readiness、显式 data-root release、Base/V5 input、hydropower 380 GW
  和 Base/V5 1 h build audit 全部 PASS。1 h build 的 Base/V5 规模分别为
  `238,529 vars/79,979 rows/452,433 nnz` 和
  `238,978 vars/80,363 rows/453,968 nnz`，process-tree peak 分别约
  `0.429/0.462 GiB`。
- 24 h Base 两轮串行参数诊断已结束，当前无活动 CISPO/Gurobi process。20 个 Barrier-only
  配置均无法同时满足严格 primal/dual contract，故无 accepted `BarPi`、QC 或 result
  manifest。`ScaleFlag=0/1/3`、`NumericFocus=3`、`Aggregate=0`、`Presolve=0/1`、
  `PreDual=1/2`、`PreSparsify=2`、threads `8/32` 和 `BarOrder=1` 均未解除 blocker。
- 同一 24 h Base LP 的 `tuning2_dual_simplex16_v1` 严格通过：solver
  `795.205647945404 s`，`524,890` simplex iterations，process-tree peak
  `0.692 GiB`，`OPTIMAL_BASIC_OR_DEFAULT/PASS`、QC `58/58`、input/result manifest
  validators 均 PASS，dual attribute 为 `Pi`。这证明模型可行，问题局限于当前 Barrier
  数值路径。
- 下一步只串行测试 current-tip matched `Crossover=1/2/4 + CrossoverBasis=1`；不会运行
  `Crossover=3`、8760 h、付费云、并发第二求解、`.bas` reuse 或 MGA。通过 24 h 和 168 h
  配对门禁后才开始 Phase 1/2。

## 2026-08-01 14:18+08:00 0729 统一候选 744 h 历史根复核通过；服务器仍 idle

- 历史根
  `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1`
  的 PID 已退出；终态再次确认是 `OPTIMAL + solution_qc=PASS + 52/52 + valid
  result manifest + wrapper exit 0`，不是仍在 Barrier/Crossover、数值失败或异常退出。
  solver `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover
  `3,573.87 s`、wall `3:42:57`、process-tree peak `21.484 GiB`、swaps 0。
- 运行提交/情景/数据身份仍为 clean `7c56622`、
  `flexible_load_comfort_v4_v1g`、744 h January cyclic window、
  `barrier_16_auto_order_v2`、no-basis，以及
  `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`。
  数据归档 SHA256 复算为
  `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。
- `validate_result_manifest=(True, [])`。当前 server checkout 已前进，因此直接运行
  `validate_input_manifest` 对 3 个 repo 配置文件报告 size drift；其余 75/78 输入仍
  通过，且运行提交 `7c56622` 的 3 个 Git blob size/SHA256 与 manifest 完全一致。
  该差异是历史 run identity 与当前 checkout 的正常分离，不是结果损坏；历史验收不变，
  但不得把当前 runtime validator 误报为全绿。
- 实时 local/origin/GitHub tip 均为 `fb7cec37b552f31dcf365b859c93f2734241bb53`；
  固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean `7a1520e`，无真实
  CISPO/Gurobi/planning-sequence 进程。available RAM 约 114 GiB、swap
  447 MiB/2 GiB、连续实时 `si/so=0/0`、memory PSI 0、`/data` available
  3.7 TiB；ParaCloud 队列为空。本轮没有部署或启动任何任务。
- 0729 根仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为年度科学结果或 2040
  state anchor。下一步继续按 `SERVER_RUNBOOK.md` 顶节执行 Barrier-primary Phase 0；
  不自动启动 8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。

## 2026-08-01 13:58+08:00 Barrier 主线续接实现完成；服务器仍 idle、未部署

- 新实现提交为 `53a5873156bfe4e81abfaa258d02b3f3ff664bbd`，父提交
  `19b5754bb0db12818975344e5365777674698c47`。主线现在严格接受并保存
  `Crossover=0` 的 Barrier 最优内点解；planning sequence 在 accepted checkpoint
  闭合后显式导出 nonbasic cohort state 并继续 2030→2060，不再等待 Crossover。
- 后置 Crossover 仅由作者在全部主线完成后选择年份执行。它重建 exact LP，以
  `PStart/DStart + LPWarmStart=2` 构造 basic derivative，不写 `planning_state`、
  不回溯替换序列路径。容量、调度、成本、碳和 `BarPi` dual 不以 Crossover 为门禁；
  `VBasis/CBasis`、`.bas` 和 SA sensitivity 才需要它；连续 LP 的 RC 可从非基解
  读取，但与 dual 一样在退化问题中可能不唯一。
- sequence runner 新增并锁定 `--diagnostic-start-hour`，nonbasic sequence 自动显式
  传递 checkpoint/state flags；state load 会复核 solve/QC/input/result manifests、
  checkpoint 两条向量与 identity，并记录微小 cohort 截断统计。模型方程、数据、
  Base/V5 参数和 58 项（或当前实际总数）科学 QC 均未放松。
- 本地正确 wave root 下完整回归 `175/175 PASS`，真实 Gurobi checkpoint round-trip、
  `py_compile` 和 `git diff --check` 均 PASS。
- 13:58 固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，无 CISPO/Gurobi/planning-sequence
  进程；host available 约 `114 GiB`、swap `447 MiB/2 GiB`、连续采样
  `si/so=0/0`、memory PSI 0，`/data` available `3.7 TiB`。ParaCloud 队列为空。
- 本窗口没有部署或启动任何求解。下一窗口先完成四端/资源/数据实时核验和服务器
  regression/readiness/release/input/hydro audits，再按 `SERVER_RUNBOOK.md` 顶节
  严格串行运行小门禁、三季节 Base/V5 四年 744 h sequences 与长时段阶梯；主线
  禁止自动 Crossover、MGA、basis、8760 h、付费云或并发第二求解。

## 2026-08-01 12:20+08:00 Barrier-first 实现已提交；服务器仍 idle、尚未部署

- 新实现提交为 `19b5754bb0db12818975344e5365777674698c47`。它把 `>744 h`
  默认工作流改为先接受严格 `Crossover=0/SolutionTarget=1` 内点解并保存完整
  `BarX/BarPi`，可选 Crossover 在全新根以 `PStart/DStart + LPWarmStart=2`
  独立执行；科学/物理 QC 没有放松，模型约束没有改变。
- 本地正确设置 wave root 后完整回归 `174/174 PASS`，真实 Gurobi checkpoint
  round-trip PASS，`py_compile`/`git diff --check` PASS。新的 long profile 为
  `TimeLimit=86400 s/SoftMemLimit=80 GiB`；diagnostic memory gate 按
  8/32/96 GiB 阶梯向上匹配，避免长 diagnostic 被错误的 8 GiB 门禁放行。
- 12:20 实时固定服务器仍为 branch `codex/cispo-2030-full-lp`、clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，尚未部署 `19b5754`；只读进程复核
  仅看到审计命令自身，无 CISPO/Gurobi/planning-sequence solver。host 总内存
  `125 GiB`、available 约 `113 GiB`、swap `447 MiB/2 GiB`，最新
  `vmstat si/so=0/0`、memory PSI avg10/60/300 均为 0。ParaCloud 队列为空。
- 本窗口没有启动 Base/V5、744 h、长时域、8760 h 或付费云任务。下一窗口必须先
  等 local/origin/GitHub 文档 tip 一致，再实时核验并 fast-forward 服务器、运行完整
  audits；详细五季节 744 h 配对和长度阶梯见 `SERVER_RUNBOOK.md` 顶节。任何 PID
  存在时只读监控，仍禁止并发第二求解、`Crossover=3`、MGA/basis 和自动 8760 h。

## 2026-08-01 05:52+08:00 reservoir-native Base 744 h 已 TIME_LIMIT；V5 未启动

- 当前 local/origin/GitHub/server 均为
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`；固定服务器 branch
  `codex/cispo-2030-full-lp`、worktree clean、无 CISPO/Gurobi 进程。
- Base 输出根
  `/data/zz2/National_model/outputs/2030_744h_v0731_reservoir_native_ub_7a1520e_base_stablebasis_v1`
  已结束。`solve_report.json` 为 `TIME_LIMIT/status_code=9`、`SolCount=0`、
  solver `21,601.01 s`；wrapper exit 2、wall `6:05:29`、stderr 0、MaxRSS
  `19,702,352 KiB`、process swaps 0。
- Barrier 为 218 iterations/`6,900.02 s`/objective `2,352,092.16 million CNY`；
  Crossover 重启后 push phase 仍有 `PInf=6.459046`、`DInf=1.0102534e5`，
  cleanup 报告 basis variable drop 与 quad precision，最终 crossover
  `14,528.04 s`、746,438 simplex iterations，并把 Barrier `Optimal` 改为
  `TIME_LIMIT`。
- `input_manifest.csv` 当前且 validator 为 `(True, [])`，SHA256
  `99842464c22371d15e757bcc6db76490060a74bbb944961ed1be6cbdef40d6e4`；无
  `solution_qc.json`，故 58 项 solution hard checks 未执行；无
  `result_manifest.json`，validator 返回 missing。所有解后 physics/accounting
  输出均未形成，不能审计或解释。
- 候选 V5 输出/控制根均不存在，不得启动。Base 自身已复现同类 crossover
  blocker，说明它不是 V5 独有问题。available RAM 约 `114 GiB`、系统 swap
  `447 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0，ParaCloud 队列为空。
- 下一步只允许保留失败根并做 shared-core 数值诊断；重新通过匹配
  1 h/24 h/168 h Base/V5 门禁前，不运行新的 744 h。继续禁止 8760 h、付费云、
  并发、basis/MGA 与 `Crossover=3`。

## 2026-07-31 20:41+08:00 summer 744 h 已 TIME_LIMIT；nonbasic 修复待部署

- 旧活动根
  `/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1`
  已终止：`TIME_LIMIT`、`SolCount=0`、solver `21,600.80 s`、Barrier
  `233/7,414.52 s`、Crossover `13,917.15 s`、simplex 1,069,484。
  无 `solution_qc.json`、无 `result_manifest.json`；wrapper exit 2、wall
  `6:05:39`、MaxRSS `22,364,408 KiB`、swaps 0、stderr 0。结论是
  Crossover cleanup 工程失败，不是 Barrier、RAM 或 swap 失败。
- 本地实现提交 `8de7a8e5bf4712bac30472fc4a564f47462fd9cd` 新增 Gurobi 13+
  strict optimal primal-dual nonbasic 诊断路线、`BarPi` dual、未接受解的
  fail-closed 导出合同，以及 annual load-center 每边 0.1 MWh 的显式数值尘埃
  阈值；没有改变冷热/EV/可靠性/成本模型。完整回归 `169/169 PASS`。
- 本地 Gurobi 12 的 1 h Base/V5 可严格闭合，但 24 h Base 返回
  `SUBOPTIMAL/HARD_FAIL`；该 profile 因已知版本风险明确要求 Gurobi 13。
  因而尚未声称该路线适用于 744/8760 h。
- 20:41 服务器仍为 clean `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`，
  无 CISPO/Gurobi/National_model 进程；available RAM `114 GiB`、swap
  `447 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0；ParaCloud 队列空。
- 下一步：待文档 tip 推送后重新核验，fast-forward 并运行服务器完整回归/
  readiness/release/input audits；随后串行执行 hour 3960 起点的 1 h 与 24 h
  Base/V5 nonbasic 配对。任一失败即淘汰候选并停止；成功后才执行配对 168 h，
  再依次执行 same-window Base/V5 744 h。禁止 8760 h、付费云、并发、basis/
  MGA 与 `Crossover=3`。

## 2026-07-31 16:49+08:00 summer 744 h 正在 Crossover/simplex cleanup（已由上节终态取代）

- Barrier 已在 iteration `233`、runtime `7,414.52 s` 报告 optimal objective
  `2,351,134.66 million CNY`；末行 primal/dual infeasibility 与
  complementarity 为 `2.26e-4/2.27e-8/1.82e-9`，日志无
  `Numerical trouble`。
- crossover basis 构建后 DPush/PPush 于 `9,652 s` 完成；16:48 最新
  simplex iteration `912,630`、runtime `11,752.76 s`、objective
  `2,351,203.328 million CNY`、primal infeasibility 0、dual
  infeasibility `2.014e6`。近期 dual 指标显著振荡，当前未收敛，也尚无正式
  失败状态。
- 唯一 PID 链仍存活；server clean `aaf16cc`，stderr 0。solver current/max
  memory `16.36/23.50 GiB`，host available RAM 约 `100 GiB`，swap
  实时 `si/so=0/0`，memory PSI 0；ParaCloud 空。
- `solve_report.json`、`solution_qc.json`、`result_manifest.json` 均不存在。
  `TimeLimit=21,600 s`；继续只读监控，禁止改 checkout 或启动第二任务。

## 2026-07-31 13:29+08:00 summer 744 h V5 cold gate 正在构建

- 唯一活动输出/控制根均为
  `2030_744h_v0731_summer_offset_a7c6715_v5_v1`；启动提交为 clean
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`，wrapper/Python PID 初始
  `674143/674145`，启动于 `2026-07-31T13:27:06+08:00`。
- 实时 scope 为 model hour `[3960,4704)`，北京时间 2030-06-15 00:00 至
  07-15 23:00，V5 central、744 h carbon/resource scaling、no-basis、
  `Crossover=1/CrossoverBasis=1` 均正确。
- 13:29 仍处于 build，Python RSS 约 `1.68 GiB`；尚无
  `build_report/solver_telemetry/gurobi.log`，stderr 0。available RAM
  约 `112 GiB`、swap `780 MiB/2 GiB`、实时 `si/so=0/0`、memory PSI 0，
  ParaCloud 队列为空。
- PID 存在时仅监控，不修改服务器 checkout、不启动第二任务。该根仍为
  `TEST_ONLY_TRUNCATED_HORIZON`；终态必须执行完整严格审计。

## 2026-07-31 13:27+08:00 summer 1 h/24 h 小门禁已严格接受

- 固定服务器部署 `11c682076869e30e0ed24db038bf3c12ecdbb1ae` 后完整回归
  `167/167 PASS`。全新 summer 1 h Base v2 与 24 h V5 v2 均达到
  `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0`，失败 v1 未复用。
- 1 h Base v2 solver runtime `4.966 s`、Barrier/simplex `92/1,134`、
  wall `0:34.02`、MaxRSS `498,444 KiB`、swaps 0；`time_index.csv`
  从 model hour 3960、`2030-06-15 00:00` 开始。
- 24 h V5 v2 solver runtime `115.226 s`、Barrier/simplex `243/29,002`、
  wall `2:38.15`、MaxRSS `962,928 KiB`、swaps 0。Barrier 的
  sub-optimal warning 由 crossover 恢复为 `Optimal`，无
  `Numerical trouble`；最大 constraint/bound/dual violation
  `3.242e-8/2.980e-11/2.025e-13`。
- 24 h V5 cooling up/down `2.1335/1.6170 GWh`，storage
  charge/discharge `187.9103/162.4830 GWh` 且无同充同放；EV mobility
  charge `152.998 GWh`、V1G relocated `43.3376 GWh`、本日 V2G export
  为 0。缩放碳上限 `10.958904 MtCO2` binding。全部 58 项 hard QC
  覆盖冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS/BECCS
  和成本 accounting scope。
- 下一步只允许部署包含本记录的文档 tip 后启动一个
  `/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1`
  cold gate；窗口 `[3960,4704)`，profile
  `barrier_16_auto_order_stable_basis_v3.json`，no-basis、
  no-concurrency。仍禁止 8760 h、付费云、basis/MGA 与 `Crossover=3`。

## 2026-07-31 13:18+08:00 首个 summer 1 h build failure 已最小修复

- `985983b` 已部署且 server `166/166` regression、readiness、release、
  V5 input 与 hydro audits 全 PASS；但首次 summer hour 3960 Base 1 h
  在 build 阶段因空 CHP winter 索引触发 Gurobi `AssertionError`。无
  `build_report/solve_report/solution_qc/result_manifest`，不是 solver
  失败或可接受根。
- 失败输出/控制根以 `...summer_offset_985983b_base_v1` 原样保留，wrapper
  exit 1、wall `0:23.75`、MaxRSS `493,580 KiB`、swaps 0。
- 修复提交 `a7c67153d9b90055b60ed2704ef6bba702086ae4` 仅跳过空 winter
  constraint set，并把完整模型测试固定到 hour 3960；本地
  `167/167 PASS`。部署后必须用全新 `v2` 根重跑，禁止复用 v1。

## 2026-07-31 13:10+08:00 summer-offset 744 h 候选待部署

- 实现提交 `077bce0eca16b1025130143122aee0a05559c3e0` 为诊断 runner
  增加一致的非年初连续窗口合同；不改变冷热、V1G、V2G、firm credit、
  年度流量缩放或 solver 科学边界。夏季 744 h 定义为 model hour
  `[3960,4704)`，对应 2030-06-15 00:00 至 2030-07-15 23:00。
- 本地完整回归在正确 wave 根下为 `166/166 PASS`；窗口数据核验 cooling
  为 `147,056.322 GWh`，显著高于年初 744 h 的 `68.469 GWh`。该证据只
  说明测试覆盖更强，不构成结果接受。
- 当前服务器尚未部署该提交，也尚未启动新任务。部署前必须重新核验
  本地/origin/GitHub/server HEAD、server clean/idle、RAM/swap/vmstat/PSI、
  目标根不存在与 ParaCloud 空队列。部署后先串行运行 1 h Base 和 24 h V5
  offset gates；两根严格接受后才允许一个 2030/V5 744 h cold gate。
  长时段 V5 固定使用
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`，
  no-basis、no-concurrency。744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`；
  禁止 8760 h、付费云、basis/MGA 和 `Crossover=3`。

## 2026-07-31 12:45+08:00 当前提交的 24 h/168 h 匹配门禁闭合

- 当前本地、`origin`、GitHub 与固定服务器任务身份均为
  `ae3356391ec55376b041d6a356ea2d1f26be88bc`；服务器 checkout clean。
  本地/服务器完整回归均 `165/165 PASS`，服务器 readiness、release、
  V5 input 与 hydro audits 全部 PASS，水电容量为
  `297.8895 + 82.1105 = 380.0000 GW`。本机 `7.91 GiB < 8 GiB`，未绕过
  内存门槛启动 Windows solver。
- 当前提交的 24 h Base/V5 production-profile 根均为
  `OPTIMAL + PASS + 58/58 + current input + valid result manifest +
  wrapper exit 0/stderr 0`。solver runtime `407.321/420.232 s`，
  wall `7:28.51/7:44.38`，RSS `0.761/0.794 GiB`。
- 168 h Base-v2、Base-v3、V5-v3 三根也全部严格接受。solver runtime
  `907.672/917.121/1024.510 s`，wall
  `16:54.30/17:03.75/18:54.89`，RSS `3.336/3.328/3.508 GiB`，
  Barrier/simplex `213/211003`、`213/185333`、`232/258814`。
  Base 两 profile 的 objective 仅差 `2.9e-7 million CNY`。
- V5 168 h 使用
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。
  production-v2 尝试在 optimize 前被既有 guard 正确拒绝，控制根
  `/data/zz2/National_model/run_control/2030_168h_v0731_ae33563_v5_v2prod_v1`
  记录 `exit=1` 与 RuntimeError；无 solve/QC/manifest，不是求解失败根。
- 同 profile V5 相对 Base objective `-298.097 million CNY`，发电容量
  `-2.915 GW`，firm credit `2.891320 GW`，所选窗口 effective peak
  `-1.663365 GW`。adequacy 仍使用完整 8760 h immutable baseline peak，
  未直接使用 effective peak 降容。V5 EV fleet charge/V1G relocated/V2G
  export 为 `756.192/193.242/1.178 GWh`；周期 SOC 与驾驶取能闭合。
- 全部 58 项 hard QC 覆盖冷热/EV、wave、水电/梯级、PHS/储能、网络、
  备用、惯量、碳/CCS/BECCS 与成本。碳限额 `76.712329 MtCO2` binding；
  objective residual `-1.774e-7 million CNY`。截断解释边界仍包括：
  冬季首周无冷热实际移峰却存在全年峰窗 cooling credit；水文 raw clip
  等价量 `974.405 million m3`，需后续科学敏感性。
- 终态服务器无 CISPO/Gurobi，available RAM 约 `114 GiB`，swap
  `780 MiB/2 GiB`、`si/so=0`、memory PSI 0；ParaCloud 队列为空。
  全部结果仍为 `TEST_ONLY_TRUNCATED_HORIZON`。下一步由作者决定四年
  168 h Base/V5 sequence 或单一更长门禁；不自动启动 744/1008/8760 h、
  付费云、basis/MGA、并发第二求解或 `Crossover=3`。

## 2026-07-31 10:15+08:00 固定结果 dashboard 已部署并闭合

- 结果查阅实现提交为 `336116b493cf92eb461d1a2aab490678fd2dbac5`，
  最终解释修正为 `bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`。
  dashboard 本身不改变 LP、数据、目标或 solver；冷热、V1G、V2G 与 firm
  credit 的服务模式保持不变。前一数值稳定化中唯一新增的物理约束仍是
  V1G/V2G 共享签约连接功率上限，不应与本轮图表改造混为一谈。
- 本地完整回归 `162/162 PASS`；可用内存 `7.64 GiB < 8 GiB`，没有绕过
  门槛启动本地 solver。服务器在 `336116b` 上完整回归 `162/162 PASS`，
  readiness、release、V5 input、hydro audits 均 PASS，常规水电仍为
  `297.8895 + 82.1105 = 380.0000 GW`；最终 `bdb57b2` 的 dashboard
  聚焦测试 `3/3 PASS`。
- 最终服务器根
  `/data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`
  为 `OPTIMAL + solution_qc=PASS + 58/58`，current input/result manifest
  均 `(True, [])`，result manifest 的 Git identity 精确为 `bdb57b2`。
  wrapper exit 0、stderr 0 bytes、wall `0:39.10`、MaxRSS
  `597,624 KiB`、swaps 0；solver runtime `7.352116 s`，Barrier
  96、simplex 1,716，最大 constraint/bound/dual violation
  `0/4.441e-16/0`。
- `result_dashboard_summary.json`、`result_analysis_metrics.csv` 和
  `visualizations/core_result_dashboard.svg` 均存在、进入 output catalog，
  并由最终 result manifest 校验。1 h 的规划/运行成本强度分别为
  `0.2003156/0.3141334 CNY/kWh`；由于时域不同，全年 total 强制为
  `null`，不得相加或表述为 LCOE。objective 重构残差为
  `-9.779e-9 million CNY`。
- 当前服务器 checkout clean，无 CISPO/Gurobi 进程，available RAM 约
  114 GiB、swap 780 MiB/2 GiB、实时 `si/so=0`、memory PSI 0；
  ParaCloud 队列为空。该输出仍是 `TEST_ONLY_TRUNCATED_HORIZON`。
  下一次获准的门禁直接复用固定 dashboard 合同；不自动启动
  744/1008/8760 h、付费云、basis/MGA、并发求解或 `Crossover=3`。

## 2026-07-31 05:14+08:00 V5 168 h 数值稳定化门禁严格通过

- 当前本地/origin/GitHub/固定服务器部署基线均为
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8`，服务器 checkout clean；
  模型实现提交为 `fead34334153eca32bbf7ec3651f3388038ac04b`。服务器
  `159/159` regression、readiness、release、V5 input、hydro 与 380 GW
  容量审计全部 PASS。
- 新建 Base/V5 1 h 与 24 h 四根均为
  `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0`。24 h Base/V5 solver runtime 为
  `408.850/421.015 s`，两者均有 Barrier `Numerical trouble` 后的严格
  crossover 恢复；V5 的规模/时间增量仅为
  `+5,321 vars / +5,934 rows / +30,045 nz / +3.0% solver time`。
- 唯一 168 h V5 根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  已严格接受：`OPTIMAL + PASS + 58/58`，current input/result manifest
  均 `(True, [])`，wrapper exit 0、wall `18:38.92`、RSS `3.511 GiB`、
  swaps 0。raw/presolved 矩阵为
  `1,209,095/1,060,576/9,755,329` 与
  `737,850/751,223/7,386,987`。Barrier 232 次/819.54 s 后
  `Sub-optimal`，但无 `Numerical trouble`；`CrossoverBasis=1` 用
  176.79 s 改为 `Optimal`，最终 solver 1005.194 s、258,814 simplex，
  最大 constraint/bound/dual violation 为
  `8.339e-8/2.609e-8/6.047e-8`。
- 冷热、EV 共享连接、V1G/V2G nesting/全国上限、firm credit、网络方向、
  水电/梯级、储能、备用、惯量、碳/CCS/BECCS、成本 scope 均无 hard
  failure；诊断碳限额 `76.712329 MtCO2` binding。旧式 V1G daily-energy
  residual 对 V5 的 SOC/驾驶取能服务账户不适用，实际 SOC transition
  residual 为 `2.537e-13 GWh`；需后续修正输出语义，不是本次解的漏约束。
- 当前无 CISPO/Gurobi 进程，约 111 GiB available，swap 约 780 MiB
  但 `vmstat si/so=0`、memory PSI 0；ParaCloud `squeue` 为空。该根仍是
  `TEST_ONLY_TRUNCATED_HORIZON`，`Kappa≈1.62e10`，候选 profile 还不是
  production。下一步只允许同身份匹配 Base 168 h 与只读矩阵缩放审计；
  不自动启动 744/1008/8760 h、付费云、basis/MGA、第二求解或
  `Crossover=3`。

## 2026-07-31 04:21+08:00 V5 数值根因已结构修复，待部署服务器短门禁

- 本地实现提交为 `fead34334153eca32bbf7ec3651f3388038ac04b`；当前
  origin/GitHub 与固定服务器仍为 clean
  `cf265f365c85f8bb9aa8c18880cba04f095fc982`，尚未部署新提交。
- 旧 V5 2030/168 h 终态是 `TIME_LIMIT + Numerical trouble`，不是可接受
  结果：Barrier 210、solver 21,600.187 s、simplex 3,488,935、无解、
  无 QC、无 result manifest；wrapper 峰值 RSS 约 3.47 GiB、swaps 0。
  2040--2060 未启动。
- 最终本地 168 h 矩阵审计：raw
  `1,209,095 rows / 1,060,576 vars / 9,755,331 nz`，presolved
  `737,850 / 751,222 / 7,386,903`；raw/presolved 最大系数同为 6,250，
  presolve amplification `1.0`。旧模型对应放大比为 `51.094`。
  完整回归 `159/159 PASS`，V5 input/release/hydro audits PASS。
- 04:12 实时服务器为 clean `cf265f3`、无真实 CISPO/Gurobi 进程、约
  114 GiB available、swap 780 MiB/2 GiB 且 `vmstat si/so=0`、memory
  PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地 Windows 只有约
  7.9 GiB available，1 h gate 在 `optimize()` 前由 8 GiB 门槛拒绝。
- 下一步：推送后再次实时核验，再 fast-forward 到精确提交；先跑服务器
  `159/159`、readiness/release/V5/hydro，再串行运行全新 Base/V5
  1 h 与 24 h，全部达到 `OPTIMAL + QC PASS + 58/58 + current input +
  valid result manifest` 后，才允许单独启动 2030/V5 168 h。仍禁止
  744 h、8760 h、四年 sequence、付费云、basis/MGA、并发第二求解和
  `Crossover=3`。

## 2026-07-30 21:29+08:00 test-only 对冲流 warning 已实现，待部署

- 实现提交 `9b6e72a` 保持模型与 `1e-6 GW` 检测不变，只把同时满足七项上限的截断时域微小 AC 对冲流标为 `TEST_ONLY_DE_MINIMIS_WARNING`；任一上限超限仍 hard fail，8760 h 始终 strict zero。原 2050 事件对应额外损耗仅 `0.011489 GWh`、占系统负荷 `4.0100e-8`，在新合同内，但不会被写成“严格单向”。
- 本地 `146/146 PASS`，V5 input/release audits PASS。本机约 `7.48 GiB` available，低于 8 GiB solver gate，故没有强行本地求解。
- 服务器尚未部署，仍为 clean `af390fa`；21:28 实时无 CISPO/Gurobi/sequence，约 `114 GiB` available、swap 无进出、PSI 0，ParaCloud 空。代码/文档双端推送后才允许 fast-forward。
- 部署后顺序固定为 server regression/audits → 新 1 h/24 h Base/V5 → 新四年 168 h Base → 新四年 168 h V5。全部接受后启动一个四年 `1008 h` V5 串行门禁；不得跳过短门禁或复用失败 state。仍禁止 8760 h、付费云、basis/MGA、第二求解和 `Crossover=3`。

## 2026-07-30 19:38+08:00 168 h Base 在 2050 网络方向 hard QC 停止

- 当前无 CISPO/Gurobi/planning-sequence 进程。固定服务器保持 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，约 `114 GiB` available RAM，swap `780 MiB/2.0 GiB` 且 `vmstat si/so=0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地/origin/GitHub 文档 tip 均为 `134af0f`。
- Base 输出根 `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1` 为 `sequence_report=HARD_FAIL`。2030/2040 已 accepted，input/result manifests 均由当前 runtime validator 返回 `(True, [])`；2050 Gurobi 为 `OPTIMAL`，但 `solution_qc=HARD_FAIL`，缺少 `result_manifest.json` 和 planning state，2060 未启动。V5 尚未启动。
- 2050 唯一失败 hard check 为 `unidirectional_interprovincial_flow`。`CORRIDOR_0153`（吉林—黑龙江、AC、`1.646 GW`）在 hour 28/94/95 同时有正反向流：较小方向分别为 `0.083989/0.176374/0.120643 GW`，累计 `0.381006 GWh`。这远高于 `1e-6 GW` QC 容差，不能放宽阈值。
- 机制证据：2050 `168/8760` 缩放后的净碳上限 `-1.917808 MtCO2` 精确 binding，碳 scarcity `3589.731 CNY/tCO2`；违规小时吉林/黑龙江电价约 `-1405/-2338/-3650 CNY/MWh`。少量对冲流通过额外线路损耗消纳 BECCS 驱动的过剩电量，现有 `1.004004 CNY/MWh` 毛流量成本不足以阻止该行为。
- wrapper exit 1、wall `49:20.77`、MaxRSS `3,741,888 KiB`、swaps 0；2030/2040 stderr 为 0 bytes，2050 stderr 明确为 production QC RuntimeError。保留失败根，不续跑、不补写 manifest、不重标。下一步必须先评审 AC 方向性修复；严禁自动启动 V5、744 h、8760 h、付费云、basis/MGA、第二求解或 `Crossover=3`。

## 2026-07-30 16:58+08:00 V5 服务器预门禁与 24 h A/B 已闭合

- 固定服务器 clean checkout 为 `af390fad22dc4e3ec4636edadfb56295e4907234`，数据根为 `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。跨 Windows/Linux 的 V5 五表和 manifest 已由 `4f717de` 固定为逐字节一致；`af390fa` 恢复继承权威技术经济 manifest。V5 manifest SHA256 为 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`。
- 本地/服务器完整回归均 `141/141 PASS`；服务器 readiness、V5 input、release、水电审计均 PASS。水电容量闭合为 `297.8895 + 82.1105 = 380.0000 GW`。
- 2030/24 h Base/V5 根均为 `OPTIMAL + PASS + 57/57 + current input + valid result manifest + wrapper exit 0`。solver runtime `405.882/434.896 s`，peak RSS `0.759/0.797 GiB`，swaps 0。两者 Barrier 均 numerical trouble 后由 `Crossover=1` 修复，simplex `503,365/519,659`。
- V5 相对 Base 的 objective、firm credit、发电装机变化分别为 `-347.394 million CNY`、`+2.891320 GW`、`-2.891320 GW`；显式 flexibility cost `785.531 million CNY`。领先 24 h 的全国 effective peak 只下降 `2.1692 GW`，不可解释为年度峰值价值，因为 capacity adequacy 使用完整 8760 h 各省 baseline-peak 服务窗口。
- 下一步：服务器 checkout 保持 `af390fa` 冻结，先运行唯一串行四年 168 h Base；严格闭合后再运行 V5。168 h A/B 未全部接受前不启动 744 h；继续禁止 8760 h、付费云、basis/MGA、并发第二求解和 `Crossover=3`。

## 2026-07-30 16:05+08:00 V5 已提交；本地 168 h 被内存门禁阻止，服务器暂不部署

- 集成需求侧灵活性 V5 实现与中英文补充材料提交为 `57ad4c5`。Base 不变；唯一中央反事实联合冷热、付费 V1G、内生付费 V2G 和四小时峰值可交付的折减 firm capacity credit。完整本地回归 `140/140 PASS`，V5 输入/release 审计均 PASS。
- 1 h 当前输出合同 V5 根 `outputs/2030_1h_v0730_flex_v5_central_gate_v3` 为 `OPTIMAL + PASS + 57/57 + current input + valid result manifest`。24 h Base/V5 数学根均 `OPTIMAL + PASS + 57/57 + closed manifests`；V5 的 selected-window peak/firm credit/generation-capacity changes 分别为 `-2.3211/+2.8913/-2.8913 GW`。两根均在 Barrier 数值困难后由 `Crossover=1` 修复，V5 耗时 `727.286 s`。
- 本地 `outputs/planning_sequence_168h_v0730_flex_v5_base_v1` 在求解前因 available RAM `6.07 GiB < 8 GiB` hard fail；没有建模、求解或 state 传递。禁止降低门槛或复用失败根。
- 固定服务器实时 checkout 为 clean `c19e35b87fb5295101d918b29815ea79424e50a5`，无 CISPO/Gurobi solver，available RAM 约 `114 GiB`、swap `780 MiB` 且 `si/so=0`、memory PSI 0；ParaCloud `squeue` 为空。但 2026-07-29 遗留的非 solver release-audit wrapper PID `976320` 与 `grep` 子进程 `976713` 仍存在。按 PID 保护合同，不切换 checkout、不部署 V5、不启动新服务器任务，等待作者明确授权处理该遗留进程。
- 下一步：本地释放至少 2 GiB 后，以全新根重跑当前提交的 24 h Base/V5 和四年 168 h Base/V5；全部闭合后才允许新的服务器 744 h。8760 h、付费云、basis/MGA、并发第二求解和 `Crossover=3` 继续禁止。

## 2026-07-30 11:26+08:00 年度流量缩放已本地闭合，服务器未部署

- 新模型提交 `d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244` 将诊断时域碳上限、DAC throughput、生物质年度燃料和 CO2 年注入能力统一按 `optimization_hours/8760` 缩放；DAC 功率按年化捕集速率计算。8760 h 的比例为 1，不改变全年方程；annualized capacity/fixed cost 不缩放。
- 本地 1 h/24 h 中央 V4 V1G 根 `outputs/2030_{1h,24h}_v0730_annual_flow_scaled_v4_v1g_v1` 均 `OPTIMAL + PASS + 54/54 + current input + valid result manifest`。2030 窗口碳上限分别为 `0.456621/10.958904 MtCO2`，均 binding，DAC capacity violation 为 0；24 h solver runtime `270.653 s`。
- 完整本地回归 `138/139 PASS`；唯一失败是已知的本地 ignored technoeconomic manifest hash 与冻结服务器数据包不一致，本次未改动外置数据或 release contract。
- `scenario_catalog v4` 显式把主分析限制为 `base` 与 `flexible_load_comfort_v4_v1g`。其他 runnable overlay 仍是独立 sensitivity/legacy validation，并未进入本次 1 h/24 h 求解。
- 固定服务器与 ParaCloud 本次未操作。服务器上的旧 744 h 根属于旧的未缩放实现，必须保留原身份；不得原地覆盖或重标。若作者授权新 744 h，须先实时核验 checkout、进程、资源、目标根和队列，再部署新提交并运行全新串行根。

## 2026-07-30 09:18+08:00 四年 744 h sequence 已 PASS，服务器空闲

- `/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1` 于 `09:12:33+08:00` 完成，sequence `PASS`；2030/2040/2050/2060 全部 `ACCEPTED`。
- 四年均 `OPTIMAL + solution_qc=PASS + 53/53 + current input manifest + valid result manifest + hydro reconciliation audit`。objective 依次为 `2,331,204.529 / 2,380,260.669 / 2,564,163.188 / 2,808,392.706 million CNY`；solver runtime 依次为 `12,268.312 / 10,701.027 / 12,557.989 / 14,954.122 s`。
- 顶层 wrapper exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；年度 stderr 全空。当前无 CISPO/Gurobi/planning-sequence PID，available RAM 约 114 GiB，swap 无实时进出，memory PSI 0；ParaCloud 队列空。
- 744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。服务器不得自动启动 8760 h、basis、MGA、付费云或第二求解。

## 2026-07-29 23:21+08:00 2030 已接受，2040 Barrier iteration 107

- sequence 仍为唯一活动任务。2030 已 `ACCEPTED`：`OPTIMAL + PASS + 53/53 + current input + valid result manifest`，solver runtime `12,268.312 s`，objective `2,331,204.529 million CNY`，peak process-tree RSS `20.385 GiB`，年度 stderr 为空。
- 当前 2040 runner PID `1717598`；Barrier iteration `107`、runtime `3,572.896 s`，primal/dual infeasibility `0.008370/0.000821`、complementarity `1.8373`，solver current/max memory `13.174/22.222 GiB`。`solve_report.json`、`solution_qc.json`、`result_manifest.json` 尚不存在，故当前只能判定为 Barrier 进行中。
- 主机 available RAM 约 95 GiB，swap 781 MiB 且无实时进出，memory PSI 0；ParaCloud 队列空。运行 checkout clean `5d31b51`，不追平活动运行期间新增的文档提交。

## 2026-07-29 18:45+08:00 四年 744 h sequence 已启动，当前 2030 构建中

- 唯一任务：`/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，控制根同名位于 `run_control`；运行 checkout `5d31b51b350a581287fc8eb13e73216c11fc7543`。
- wrapper/Python/2030 runner 初始 PID `1463763/1463765/1463870`。身份为 `RUNNING + TEST_ONLY_TRUNCATED_HORIZON + 744 h + flexible_load_comfort_v4_v1g`，无 basis；首次快照尚在 build，故 telemetry、Gurobi log 和终态报告均未出现。
- 初始资源为约 113 GiB available RAM、781 MiB/2 GiB swap、`si/so=0`、memory PSI 0；ParaCloud 队列空。PID 存在时只读监控，不切 checkout、不启动任何其他任务。

## 2026-07-29 18:42+08:00 新实现已部署，权威回归与 1 h/24 h 门禁通过

- 固定服务器为 clean `codex/cispo-2030-full-lp` / `03e77ccc8d2ef3813b7cc5c0d727b068d008090d`。部署证据根 `/data/zz2/National_model/run_control/deployment_03e77cc_v1` 中 release contract、readiness、380 GW hydro audit、V4 input validation 全部 PASS；完整回归 `135/135 PASS`。
- 全新中央 V4 V1G 1 h/24 h 根分别为 `/data/zz2/National_model/outputs/2030_1h_v0729_identity_hydro_v4_v1g_server_v1` 和 `/data/zz2/National_model/outputs/2030_24h_v0729_identity_hydro_v4_v1g_server_v1`；均 `OPTIMAL + PASS + 53/53 + current input manifest + valid result manifest + hydro reconciliation audit`。24 h solver runtime `84.230 s`，wrapper wall `2:07.62`，peak RSS `852,644 KiB`，swaps `0`。
- 尚未启动四年 744 h sequence。启动前仍须重新核验唯一进程、RAM/swap/vmstat/PSI、服务器 checkout、目标根不存在和 ParaCloud 队列；禁止项不变。

## 2026-07-29 18:27+08:00 新实现已本地闭合，待推送/部署；服务器仍保持旧 checkout

- 新实现提交 `cea78ae1546b19754f7859982ae82dbf66820fdc` 已完成：8760 runner 常规路径不再调用 `getA()`；双层身份 `baseline_contract + analysis_case`；Base/中央 V4 保持 baseline peak，独立 sensitivity 使用 effective peak；梯级水电使用显式比例转移调和；accepted full-year Base 可 opt-in 输出精选 `.sol/.bas/.prm/fingerprint`。
- 当前固定服务器尚未部署该提交，仍须在部署前实时复核 `/data/zz2/National_model/repo` 的 checkout/dirty state、唯一 CISPO/Gurobi 进程、RAM/swap/vmstat/PSI、旧/新目标根与 ParaCloud。权威数据根仍为 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`；其 technoeconomic manifest SHA256 已实时复核为 `397297ec3980ffb38988a0463f934e310f228cbe48268d59ce38c7fa8350ec75`。
- 本地优化后的 24 h baseline/effective A/B：raw nonzeros `1,799,111/1,803,544`（effective 仅 `+0.246%`），runtime `55.253/53.021 s`，发电侧总容量 `3998.172/3785.672 GW`，两根均 `OPTIMAL + PASS + 53/53 + valid manifest`。容量差只能作为截断工程证据，不能作为年度结论。
- 水电全年输入审计保持 `297.8895 + 82.1105 = 380 GW`，并显式记录原始负本地入流 `335,304` node-hours、`158,199.650 million m3` 调和量和 `4.55e-13 m3/s` 最大闭合残差。全新四年 1 h V4 sequence 已 `PASS`。
- 下一步只允许：推送文档 tip后重新只读核验；服务器 fast-forward；权威数据根完整回归 + 1 h/24 h；随后启动唯一串行 2030→2060 744 h V4 V1G diagnostic sequence。禁止 8760 h、付费云、并发第二求解、basis/MGA gate 和 `Crossover=3`。

## 2026-07-29 统一候选已部署；唯一 2030 V4 V1G 744 h cold gate 已严格接受

- 当前固定服务器 checkout 为干净 `codex/cispo-2030-full-lp` / `7c56622c266e673037bd6afaa70c85aa57e6cb13`；终态审计前，本地、固定服务器 bare `origin` 与 GitHub 文档 tip 均为 `5ffee8a79b090dd8493e9b38da78464f3312ec6f`，唯一模型实现基线为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本次只增加交接文档；无需切换服务器 checkout。最终外置输入根为 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`，标准归档 SHA256 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。`model_input_files.json` v10 包含 42 张运行表和 12 个 sidecar，显式覆盖 wave、V3、V4 和其来源 manifest。
- 服务器审计根 `/data/zz2/National_model/outputs/release_contract_v0729_server_7c56622_v5`：readiness PASS、release contract PASS、聚合水电 `297.8895 + 82.1105 = 380 GW` PASS、V4 四规划年 loader PASS、完整 unittest `130/130 PASS`。隔离部署过程中发现并修复 hydro audit NumPy 标量序列化、V4 source/运行表漏包、wave 表漏包、V3 implemented 表漏包与测试写死 `repo/data`；失败的 v1--v3 数据根/审计目录保留作证据，不是当前输入。
- 服务器 V4 小门禁 `2030_{1h,24h}_v0729_unified_v4_v1g_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + valid input/result manifests`。1 h solver 4.136 s、peak RSS 0.485 GiB；24 h solver 82.272 s、peak RSS 0.819 GiB。24 h Barrier 报 numerical trouble，`Crossover=1` 恢复 Optimal；这强化而不是削弱对 `Crossover=3` 的拒绝。
- 技术经济实装已再次复核：正确实施提交 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` 是两端 checkout 的祖先；服务器 `technology/technoeconomic_price_basis_manifest.json` 为 `technoeconomic_2025_cny_v2 / 2025 constant CNY / PASS`，活动 run 的 input/config snapshot 实际记录该 contract。本地迁移审计为 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。
- 根 `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1` 使用 `--planning-year 2030 --horizon one_month`、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2`，没有 basis。它是单独的 2030 cold gate，未调用 `scripts/run_cispo_planning_sequence.py`。raw 为 `5,238,323/3,942,756/42,266,264`，presolved 为 `3,234,057/2,812,319/31,818,664`，presolve/ordering `177.00/108.70 s`，`AA' NZ=6.236e7`、`Factor NZ=8.124e8`、`Factor Ops=5.567e12`。
- 2026-07-29 16:32+08:00 终态审计：wrapper/Python PID `1004972/1004975` 已退出。Gurobi 为 `OPTIMAL`，objective `2,330,214.449430 million CNY`、solver runtime `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover `3,573.87 s`；最终 primal/dual infeasibility 为零。wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`，stderr 只有 `/usr/bin/time` 统计。
- 严格验收为 `solution_qc=PASS + 52/52 hard checks + validate_input_manifest=(True, []) + validate_result_manifest=(True, [])`。冷热/EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 accounting scope 已逐表核对；最大 power-balance residual `1.63e-10 GW`、objective component residual `1.79e-6 million CNY`。成本同时含 annualized planning 与截断 operation scope，因此本根仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果、年度净价值或正式 2040 state anchor。
- 终态刷新时主机约 `114 GiB` available、swap `781 MiB/2.0 GiB`，实时 `vmstat si/so=0`、memory PSI=0；ParaCloud `squeue -u a8s001819` 为空。历史 `4003088=COMPLETED build-only`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`。另有旧 release-audit SSH/bash/grep 管道，无 Python/Gurobi solver 子进程且不是第二求解，本次未终止。不得启动第二个 CISPO/Gurobi、固定服务器 8760 h、付费云、basis gate 或 `Crossover=3`。

## 2026-07-29 多智能体改动已统一为本地 release candidate；等待精确提交和实时服务器复核

- `b87b3b6` 的干净提交不是可部署版本：它已有省级聚合水电 loader，但漏掉同一功能的配置、LP、导出和测试。统一实现已提交为 `1d04f07565c3039ed467ec4080f276bd0da90786`，并由 `config/release_contract_v0729.json` 把 Base、水电 380 GW、V4、PHS sensitivities、scenario catalog、production solver profile 与 11 个外置数据 SHA256 锁定；detached 精确提交的 release audit PASS、完整回归 `129/129 PASS`。
- 本地当前工作树顺序完成 `outputs/planning_sequence_168h_v0729_{base_current,flexible_load_v4_v1g_current}_local_v1`。2030→2040→2050→2060 八个根均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + closed result manifest + current input manifest PASS`，两条序列 resume 后均为四年 `RESUMED_ACCEPTED`；没有 basis 复用、并发求解或远程计算。
- V4 相对 Base 增加 `4.59%` variables、`6.24%` constraints、`3.27%` nonzeros，峰值 RSS 增量不超过约 `0.27 GiB`，未显示工程性能失控。EV 在四年均有实质重排；冷热吞吐为零；波浪能 enabled、候选和上限已加载，但装机/发电为零。上述均是 168 h 机制证据，不是年度价值或年度技术淘汰结论。
- 统一审计修复 aggregate-hydro 备用 QC 重复计数/安全表遗漏、V4 年化成本分类和 gzip 非确定性。完整本地回归 `129/129 PASS`；参数 audit `11,727/26/0/0`（rows/pass/warn/hard-fail）；四个全新 2030 1 h Base/V4/hydro-flex/PHS-central 根均为 `OPTIMAL + QC PASS + manifests valid`。省级水电 up/down 安全表 closure 最大误差为 `1.42e-14/7.11e-15 GW`。
- 作者现已授权代码/数据统一后启动一个固定服务器 744 h 或两个月门禁；当前计划选择标准 744 h V4 V1G cold。它仍须等待精确 commit/push、版本化数据根、服务器实时 Git/进程/RAM/swap/PSI 与 ParaCloud 复核，以及服务器 release/input/readiness + 1 h/24 h 门禁。不得运行 8760 h、付费云、并发第二求解、basis reuse 或 `Crossover=3`。下文 `701b9bc`/RAM/swap 是旧快照，不能直接沿用。

## 2026-07-28 常规水电 380 GW 省级闭合仅在本地；服务器未部署

- 当前本地未提交水电候选已从重复 `COMID` 修复扩展为“297.8895 GW 站点 + 82.1105 GW 固定省级聚合”常规水电表示，并严格闭合国家能源局 2025 年末 380 GW 分项；PHS 下限保持 65.94 GW。聚合层增加 LP 变量和输入文件，旧 duplicate-COMID-only 门禁的矩阵、目标和 basis 均不再代表当前 topology。
- 新的本地 1 h/24 h 根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`。24 h raw 为 `231,076 rows / 346,736 columns / 1,754,607 nonzeros`，聚合水电 97.768506 GWh 严格等于该窗口可用量、违反量为 0，最大功率平衡残差 `1.12e-12 GW`。这些是 `TEST_ONLY_TRUNCATED_HORIZON`，不能解释为年度发电量或系统成本。
- 本里程碑没有读取、切换或修改固定服务器 checkout，没有传输 `provincial_aggregate_capacity_2025.csv` 或月曲线，没有启动 CISPO/Gurobi，也没有查询或提交 ParaCloud 作业。下文服务器 RAM/swap/进程数值均是旧时间戳快照，未来任何远程动作前必须重新实时核验并取得授权。

## 2026-07-28 冷热/EV V4 数据支撑型本地门禁闭合；没有服务器动作

当前未提交工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，已把 `flexible_load_comfort_v4_v1g` 收敛为数据支撑型工程中心情景，并保留独立的 V2G sensitivity。P0 修复覆盖多省周期状态广播、多省目标标量化、禁用 V2G cost 导出类型、V4 smart-charge QC/上界，以及不具物理支撑的负舒适债。冷热现在是非负连续服务库存；EV 是既有 EV 基线的 75% 固定负荷与 25% 可调服务库存，不声称车辆接桩率、行程链、出发 SOC 或物理车队 SOC。Base（wave on、flexible load off）和 V3 均未改动；V4 改变 LP topology，不能与 Base/V3 导入或导出 basis。

五张省-小时输入已由现有负荷/V3 BAIT envelope 生成，中心/低/高参数、来源登记和独立证据计数齐全；四规划年 runtime-loader 审计 PASS。2026-07-29 修复 gzip 时间戳后，连续两次完整 build+validate 的六个输出字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。当前输入身份下的 V1G 1 h/24 h 与 V2G 1 h 新根均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h raw 为 `241,492/353,556/1,799,247`（rows/columns/nonzeros），solver `43.13 s`、峰值 RSS `0.760 GiB`。它们只证明本地截断工程可解性；中心参数仍是 `ENGINEERING_CENTRAL_REQUIRES_LOW_HIGH_SENSITIVITY`，不是论文校准结果。

本里程碑结束时只读复核：固定服务器仍为 clean `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，没有真实 CISPO/Gurobi 求解进程，约 `70.9 GiB` available RAM，swap 仍使用约 `19.1/21.5 GiB`；ParaCloud `squeue -u a8s001819` 为空。本轮没有更改固定服务器 checkout、数据、进程或队列。下一步必须先由作者接受当前边界，之后至多运行一个隔离的本地 168 h V1G gate；不得自动进入 basis、744h/8760h 或远程阶段。任何未来远程动作之前仍须重新实时核验 Git、CISPO/Gurobi、RAM/swap/PSI 和 ParaCloud，并取得单独授权。

## 2026-07-28 M2 boundary audit closed locally; no server action

Local implementation commit `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` closes M2 Stage A as a read-only decision/parameter audit, not as a solver or deployment milestone. `outputs/m2_model_boundary_audit_20260728_local_v3/` has 11 findings with `9 PASS, 0 OPEN, 0 hard fail`; the parameter audit has `11,717` rows, `26 PASS, 0 WARN, 0 hard fail`, and four retained open risks. It closes scenario-overlay traceability (`M2-PARAM-001`) while leaving Base wave on/flexible load off and leaving all new scientific formulations out of the production LP.

The duplicate-COMID hydrology work currently present in the local worktree is owner-uncommitted and must not be deployed. Its local 1h/24h Base candidate gates are closed (`OPTIMAL + solution_qc=PASS + closed manifest`) and the 24h raw topology remains `231,076/345,992/1,753,119`, but its Barrier log reported numerical trouble before a successful Crossover. This is a review gate, not a server authorization. The last live server check remains the separately time-stamped `701b9bc` / no-CISPO / occupied-swap snapshot below; recheck it live before any future remote action.

## 2026-07-28 swap 不是 cache；保持暂停

- 实时 `/proc` 诊断：`Cached+Buffers` 仅约 `5.6 GiB`，但匿名页约 `49.5 GiB`、inactive anonymous 页约 `34.6 GiB`。swap `19.1/21 GiB` 主要归属仍在运行的 GPU `wind_power` Python（`VmSwap 8.18 GiB`）和两组 MATLAB（`6.01/2.28 GiB`），不是可由 `drop_caches` 清除的文件缓存。
- 5 秒 `vmstat` 的 `si/so=0` 且 memory/IO PSI 均为 0，表明此刻没有持续换页；但这些 swapped pages 仍属于活跃作业。虽有约 `70 GiB` available RAM，`swapoff/swapon` 会进行约 19 GiB 主机级页面回迁并干扰其工作负荷，未取得明确授权前不执行。无 CISPO/Gurobi，但服务器仍暂停部署和求解。

## 2026-07-28 重复 COMID 水量守恒修复仅在本地闭合；服务器未部署

- 本地工作树基于 `ed72ba08ff52025cb372fc5c16583c3e05bd38b5`，将同一 GRFR `COMID` 映射的全部水电站改为按 `capacity_potential_gw` 静态份额共享一次扣除环境流量后的河段径流；梯级节点使用成员站分配流量之和。146 个重复河段、319 条共映射站点记录逐组份额和均为 1。实现尚未提交、推送或部署。
- 完整本地回归 `116/116 PASS`。隔离 1 h/24 h Base 根 `outputs/2030_{1h,24h}_v0728_hydro_comid_flow_share_base_v1` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`；24 h 根为 test-only，不能作为年度水电量或系统成本结论。
- 18:15 后只读服务器核验：checkout 为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；未发现真实 CISPO/Gurobi 进程，约 `70 GiB` available RAM，swap 仍约 `19/21 GiB`。本里程碑没有传输代码/数据、切换 checkout 或启动求解；既有服务器结果全部早于该水量口径修复。

## 2026-07-28 当前 M1 168h 四根 basis 门禁闭合；不申请 744h

- 本地当前提交顺序完成 2030 cold/warm、2030 diagnostic-state bridge、2040 cold/warm。四根都是 `OPTIMAL + solution_qc=PASS + closed manifest`，同年 objective 完全相同；2030 solver `520.266 → 10.874 s`，2040 `489.268 → 14.257 s`，warm 均为 0 Barrier/0 simplex。2040 只接受标注为 test-only 的 2030 state，basis 只来自 2040 cold；没有跨年 basis。
- 这给出同构 168h 重解的明确加速证据，但不能授权 744h：孤立 744h warm 必须先额外运行同配置 cold 744h 才会有 source basis，当前没有第二个同构 744h 目标，因而无净端到端收益。结论是“不申请、不启动”，而不是将 168h 优势外推为全年表现。
- 本里程碑只写入本地 outputs 和交接记录；随后已实时只读复核固定服务器：干净 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`、无 CISPO/Gurobi、约 `70 GiB` available RAM，但 swap 仍约 `19.1/21 GiB` 且有约 `43.0 GiB RSS` 的无关 Python。ParaCloud `squeue -u a8s001819` 为空。按 runbook 继续暂停；任何未来需求仍须重新读取，不能复用本条快照。

## 2026-07-28 M0/M1 仅本地闭合；现有 168h roots 降为历史证据

- 本地实现提交 `a5e34bf5357301c205b246b0aa2149db0dca9c3b` 完成 M0/M1，未推送、未部署。M0 的 `run_identity` 已拆成 `scientific_case`、`lp_topology`、`solver_runtime`、`implementation_bundle`；basis 的唯一硬兼容条件是完整 raw LP topology（变量/约束顺序与方向、维度、NNZ、raw CSR pattern），其余层只作审计。故纯文档提交不会废弃 basis，但活动模型结构变化必定拒绝。
- M1 已闭合 Base 标签/混合气象、VRE `cohort_survival_v1` 与 `fixed_floor_v1` 对照、BECCS 固定结果 lifecycle screening 和仅限可行域不变的 bound tightening。`outputs/2030_24h_v0728_m1_equivalence_cold_local_v1` 为 `OPTIMAL + PASS + closed manifest`，与 M0 cold objective/容量/成本/发电量 zero-diff；完整本地回归为 `114/114 PASS`。
- 因此下节所述 M0/M1 前 168h 根不再是当前 basis 门禁，只保留为历史性能记录。下一步只允许本地当前提交的 2030 cold/warm、2030 diagnostic-state bridge、2040 cold/warm；不跨年导入 basis、不使用 `Crossover=3`，也不启动 744h/8760h 或付费云任务。
- 本条没有重新读取服务器或 ParaCloud。此前 `701b9bc`、swap 压力及空队列只是旧快照；若后续申请远程动作，必须先重新实时核验 Git、CISPO/Gurobi 进程、RAM/swap 与队列。

## 2026-07-28 intra-grid/cohort 本地 168h basis 四根门禁通过；服务器仍因 swap 压力暂停

- 提交 `282c393fd98e25737631493e19110e38bb49ed28` 的本地 168h Base 冷/暖四根已闭合。2030 cold/warm 为 `576.593/11.406 s`，2040 cold/warm 为 `543.965/15.517 s`；四根全部 `OPTIMAL + solution_qc=PASS + manifest true`。warm 均为 0 Barrier/0 simplex，且同年 cold/warm objective、容量 CSV 一致，发电差仅浮点量级。2040 仅用明确 test-only 2030 diagnostic state bridge；每一年只导入本年自身 cold basis，未跨年复用。
- 四根均含新的 site/substation intra-grid CSV，且 2025 VRE 初始共享 trunk proxy 为 `1,069.512666 GW`，相对旧 nameplate `1,309.999999962 GW` 为 -18.36%。这验证 CISPO S4-18 spur 与 S4-19 potential-weighted wind/PV trunk 的本地工程/数值可解性，不是截断时域科学结论，也不证明全年 basis reuse。
- 即时只读服务器核验：checkout 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi 进程，约 70 GiB available RAM；但 swap 已用约 `19/21 GiB`，并有约 45 GiB RSS 的无关长任务。按 runbook 这是内存压力，故没有切换 checkout、安装 cohort 输入或启动服务器 168h。ParaCloud 队列为空。以后服务器状态必须重新读取，不能复用本条快照。
- 下一步只有在该压力消除后才允许：重新核验服务器/队列，add-only 安装 checksummed cohort CSV/manifest，部署精确提交、跑完整回归，再在全新目录运行一个 168h cold Base 根。`Crossover=3`、744h、8760h 和付费云任务均继续禁止。

## 2026-07-28 同格网风光共享并入与既有 VRE cohort：仅本地闭合，禁止据此直接放大

- 本地工作树以 `d73eb3390c970b0da6319a03ca8b1d3c30384040` 为基线完成 CISPO S4-18/S4-19 对齐：spur 继续按 site `max_t(cf) × capacity`，而 wind/PV trunk 在共同 substation 按 potential-weighted equivalent peak 建模。36,686 个 VRE site 行中的 12,603 个多技术 `grid_uid` 全部共享唯一的现有 substation；设计系数使用完整 8760 CF 扫描，但不新增 LP 变量或逐小时约束。
- 新的既有容量 cohort 输入有 15,171 行，2025 年按技术严格闭合为 onwind/offwind/UPV/DPV `593/47/670/530 GW`，SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`。GEM 可用投运年进入寿命队列；未知/OSM/残差和边界后投运容量显式作为 2025 boundary-censored cohort。退役解除 observed floor，但不删除 technical upper，连接代理独立复用；这允许、但不强迫同址再建。
- 本地隔离 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 为 `OPTIMAL + solution_qc=PASS + closed result_manifest`，完整回归 `102/102`。站级 VRE 初始 trunk proxy `1,069.513 GW`，相对旧 nameplate `1,310.0 GW` 为 -18.36%；这不是年度科学结果，也不是 744h/8760h 性能外推。
- 本条不写入固定服务器 checkout、数据根、进程、输出或 ParaCloud 队列；本文件先前记录的服务器状态不可作为部署时的实时证明。后续必须先实时核验 `701b9bc` 是否仍为预期 checkout、主机无 CISPO/Gurobi 进程且内存安全、ParaCloud 队列为空，再以 add-only 方式安装 cohort CSV/manifest、fast-forward 至精确已推送提交、运行完整回归。仅通过后才可运行一个新命名的 168h Base 门禁；`Crossover=3`、744h、8760h 和付费云任务均不在本条授权内。

## 2026-07-28 生产运行契约闭合与 Crossover=3 744h 反例

- 固定服务器模型 checkout 已部署 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；本地与服务器完整回归均为 `98/98`。本次工程改动增加运行根/递进序列原子 claim、不可混用的运行身份、当前输入复验和严格成功终态，不改变 Base 数学边界。
- 服务器数据根以 add-only 方式补齐 `load/flexible_load_envelope_v3.csv.gz` 与 manifest，SHA256 分别为 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03` 和 `0298256b2c1394f8e5a9e36780d2be279f06b27b291a9eca57daae91dba9a745`；既有文件未覆盖。服务器回归由此从缺少覆盖层输入恢复为 `98/98`。
- 168h 同结构 A/B 中，`Crossover=3` 的 solver/crossover 为 `594.63/117.67 s`，参考 `Crossover=1` 为 `649.17/190.92 s`；`CrossoverBasis=0` 无收益。这个短时域结论没有直接推广到 744h。
- 744h `Crossover=3` 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 的 raw/presolved/factor 与参考根完全一致，Barrier 从 `7,543.19 s` 降到 `6,981.07 s`，两个 push 阶段也较短；但 primal cleanup 出现 `1e8--1e38` infeasibility 循环。该隔离候选按数值稳定性停止准则优雅中断，终态 `INTERRUPTED`、runtime `10,930.99 s`、crossover `3,947.89 s`、peak RSS `19.828 GiB`、无解/QC/manifest，故明确拒绝为生产 profile。
- 当前无活动 CISPO/Gurobi 进程；接受的 744h 参考仍为 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` (`OPTIMAL + PASS + manifest true`，`barrier_16_auto_order_v2`/`Crossover=1`)。比较记录为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}`。固定服务器 8760h 与新的付费云任务仍禁止。

## 2026-07-28 2024 Base 744h 已完成并验收

- 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已完成：`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=(True, [])`；49 项 hard checks 全真。wave 开启、flexible load 关闭、全国碳会计、2024 Beijing-aligned VRE；结果用途为 `TEST_ONLY_TRUNCATED_HORIZON`。
- raw/presolved：`4,915,427/3,711,992/40,836,493` 与 `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros）。presolve 173.12 s；ordering 114.19 s；`AA' NZ=6.388e7`；`Factor NZ=7.481e8`；`Factor Ops=4.721e12`。
- Barrier 211 次/7,543.19 s；crossover 5,709.46 s；simplex 1,437,196；solver 13,268.90 s；端到端 3:47:18；峰值进程树 RSS 20.049 GiB；无 swap。最大功率平衡残差 `3.43e-12 GW`，最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。
- 进程已退出，服务器约 70 GiB 可用内存且无活动 CISPO solve。crossover 约占 solver 时间 43%，仍是 8760h 的主要风险。未启动第二个求解、固定服务器 8760h 或付费云任务。

## 2026-07-28 2024 数据已部署；服务器 168h Phase A/B 完成

- 固定服务器实际从干净、空闲的 `78a605d` fast-forward 到双端已推送的 `9a3c5e8`。四个 2024 CF stores 以新增归档安装，归档 SHA256 为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`，文件数与本地一致；既有数据和归档均未删除/覆盖。服务器完整回归 `89/89`。
- `/data/zz2/National_model/outputs/2030_168h_v0728_2024_dense_reductions_off`：`OPTIMAL + PASS + manifest true`；raw `1,167,956/1,019,192/9,536,283`、presolved `731,124/820,537/7,212,238`，`AA' NZ=2.160e7`、`Factor NZ=1.042e8`、`Factor Ops=8.440e10`，163 Barrier/626.10 s，crossover 72.76 s，229,459 simplex，总 700.50 s，RSS 3.407 GiB。
- `/data/zz2/National_model/outputs/2030_168h_v0728_2024_dense_dualred_v2`：`OPTIMAL + PASS + manifest true`；presolved `704,597/719,155/7,133,417`，`AA' NZ=1.987e7`、`Factor NZ=1.023e8`、`Factor Ops=8.480e10`，Barrier `performed` 124/475.02 s，crossover 190.62 s 后恢复 Optimal，630,993 simplex，总 668.05 s，RSS 3.411 GiB。
- 省级碳分层根也闭合，但其 presolved/factor/迭代/work units/目标与 dense v2 完全一致，故不采用。机器可读比较位于 `/data/zz2/National_model/outputs/solver_audit_v0728_2024_phase_ab/phase_ab_168h.{json,csv}`。
- 当前唯一 744h 候选为 dense + `barrier_16_auto_order_v2`。启动前必须再次确认无进程、可用内存安全和输出根不存在；不得并发或启动 8760h。

## 2026-07-28 2024 气象与 Phase A/B 仅本地闭合；等待服务器放大

- 本地实现提交为 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`，尚未部署。固定服务器在本轮写入前实时核验为干净 `4e1999d`、无 CISPO/Gurobi 进程、约 70 GiB 可用内存；CF 根有 2023 stores 但缺少全部四个 2024 stores。因此服务器不得直接运行新配置，必须先以追加方式传输 `onshore_wind/offshore_wind/pv/mixed_wind` 的 2024 Zarr 并校验目录、大小和 hash，不覆盖已有数据。
- 新配置的风电/光伏按北京时间 2024 自然年取 8760 小时：2023 UTC 尾部 8 小时 + 2024 UTC 数据，并删除北京时间 2 月 29 日。波浪 reference year 仍为 2023，水文仍为 2019。完整本地回归 `89/89` 通过。
- 新 1h 两根和 24h 六根全部达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。全国排放式与 31 省分层式目标一致；分层式消除了 raw 6,697-NZ 行，但 presolve 后矩阵/factor 完全相同。`DualReductions=1` 降低 24h factor 结构却显著增加 crossover，旧 0/1 参数总时间 39.706 s，而生产候选为 56--62 s；`PreDual=1` 和 `PreSparsify=2` 已在短门禁淘汰。
- 下一步只能顺序执行：推送两远端 → 再次实时核验空闲服务器 → 追加 2024 CF → fast-forward 到精确推送提交 → 完整服务器回归 → 新根 168h 匹配 A/B。全部通过后只选择一个 case 启动新 744h。不得并发、不得覆盖历史根、不得启动固定服务器 8760h 或付费云任务。

## 2026-07-28 当前 Base/MGA 工程代码已部署；1h/24h/168h 与 basis/MGA 诊断通过门禁

- 写入前已实时复核服务器：无 CISPO/Gurobi 进程，可用内存约 69--70 GiB。干净 checkout 在未替换任何活动 checkout 或任务的前提下由 `01ec6f9` fast-forward 至 `56d166d`，并在本轮新代码通过本地完整回归后 fast-forward 至已推送的 `4e1999d`；服务器不再是旧 `c879c99` 模型实现。
- 含波浪 Base 使用附加数据根 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727` 与 `/data/zz2/National_model/data/wave_energy_20260727`，并沿用既有 CF/水文根。服务器 CISPO 环境缺少 `xarray`；仅从本地下载的 wheel 以 `--no-deps` 加入 `xarray==2025.1.2`，`wave_grid.nc` 已 smoke-open 通过。未读取或记录任何密钥。
- 本地和服务器完整回归均为 `82/82` 通过。服务器新根 `2030_1h_v0728_server_wave_base_basis_source_v1`、`2030_24h_v0728_server_wave_base_phase_audit_v1`、`2030_168h_v0728_server_wave_base_barrier16_v1`、`2030_1h_v0728_server_mga_runner_base` 均为波浪开启、灵活负荷关闭的 Base，且满足 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base` 和有效科学 result manifest；它们仅是截断时域工程门禁。最后一个 1h 根为 81,061 行、238,467 列、463,697 非零元、83 Barrier、2,674 simplex、10.33 s solver、0.463 GiB RSS，`analysis_mode=BASE_MINIMUM_COST`。
- 168h 终态证据：raw `1,167,958/1,019,192/9,486,177`；presolved `730,782/820,208/7,174,545`；`AA' NZ=2.150e7`；`Factor NZ=1.045e8`；`Factor Ops=8.532e10`；138 次 Barrier/584.20 s；crossover 104.23 s；411,056 次 simplex；总 solver 时间 690.86 s；进程树峰值 RSS 3.359 GiB。168h 的 crossover 具有实质影响，后续审计必须保留。
- 受限 crossover-basis 证据保存在新的隔离 1h 根。完全相同的 2030 LP 从 9.43 s/80 次 Barrier 降至 0.25 s/0 次 Barrier；使用源 2030 diagnostic cohort state 时，2040 冷启动为 9.29 s/77 次 Barrier，而跨年 basis 为 0.52 s/0 次 Barrier 加 1,714 次 simplex，目标和全部 QC 一致。此证据只验证受限的 test-only 路径，不验证全年复用或科学结果。
- 未启动固定服务器 8760h，未触碰历史 744h 文件，未提交或修改 ParaCloud 任务。168h/1h 门禁后服务器空闲。`4e1999d` 的 MGA 只接受闭合的年度 Base 最小成本基线、相同配置/required-input hash，并以硬成本上限加二级目标运行；其输出不得导出递进 state。当前无 accepted 年度 Base，故未运行 MGA。未来 8760h 仍需用户单独确认并满足完整云端协议。

## 2026-07-27 原始 LP 稀疏审计已本地闭合；未部署

- 本地实施提交 `6114157` 新增 `--constraint-family-audit`。它只在 `model.update()` 后读取原始 Gurobi 稀疏矩阵，默认超过 50,000,000 非零元即硬失败；不改变 LP 变量、约束、目标、Base 身份、数据或 solver profile。`constraint_family_audit.json` 记录原始约束/变量族、具体最稠密 25 行/列，并在求解后追加全局 presolve、ordering、factor、Barrier/crossover 指标；该文件被 output catalog 和 SHA256 manifest 正式纳入。Gurobi 不提供 presolved 行到源族的稳定映射，故不得将全局 presolve 缩减归因于某一族。
- 完整本地回归 `75/75` 通过。新的波浪开启、灵活负荷关闭 Base 根 `outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真。24h raw/presolved 为 `231,074/345,992/1,729,035` 与 `129,335/260,116/1,269,506`（rows/columns/nonzeros）；0.73 s presolve、0.41 s ordering、`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、`Factor Ops=7.399e8`、89 Barrier、57,741 simplex/crossover、29.107 s solver runtime、0.712 GiB 峰值进程树 RSS。
- 精确高连接行是 `annual_emissions_accounting`（6,697）、`capacity_margin_p65/p15`（6,491/5,736）和 31 个 `co2_source_balance_p*`（各 3,246）；最大列为省级 `storage_capacity_gw`（各 194）。这排除了“水电逐站平衡是当前首要矩阵密集源”的假设，但不构成删除任一物理/碳/可靠性约束的授权。下一步仅准备年度排放会计的代数等价候选并做新的匹配 24h A/B；通过后才可考虑 168h。未连接、写入或部署固定服务器，未查询/修改 ParaCloud，也未启动 744h、8760h、第二个求解或付费云任务。

## 2026-07-27 孤立梯级节点等价清理已在本地闭合；未部署

- 本地提交 `9787ba7` 保留 142 个源拓扑节点、124 条源边和全部水电站/GRFR 入流/库容/泄流物理，仅将 8 个“无入边、无出边、单站”的节点从逐小时核心梯级行转入已有的向量化独立水库平衡。该节点的上游项为空、局部入流等于站点 GRFR 可用流量，故约束代数等价；有效核心站点行由 146 降至 138。多站孤立节点触发硬失败，避免未来数据刷新静默改变水文聚合。
- 本地完整回归 `71/71` 通过；含波浪、无灵活负荷的全新 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，全部 hard checks 为真。24h 与清理前的目标仅差 `9.78e-09 million CNY`，raw/presolved 维度不变；`Factor NZ/Factor Ops` 增至 `6.284e6/7.399e8`，所以它是构建路径清理，不是 Barrier 提速证据。
- 本轮没有连接、写入或部署固定服务器，也没有查询/修改 ParaCloud；不得据此启动 168h、744h、8760h 或云端任务。若以后另行授权部署，先实时复核服务器 checkout、进程、可用内存和数据根，部署精确推送提交后才可在新根运行单一匹配 168h 门禁。

## 2026-07-27 连续 RUC 等价瘦身已在本地闭合；未部署

- 本地实施提交 `3f2255a` 仅删除连续 RUC 中由保留 S4-24、S4-25、S4-29 严格蕴含的四组逐小时上界；容量、备用、惯量、爬坡、最小出力、启停时序、目标函数、Base 技术边界与变量数均未改变。建模前会拒绝不满足 `min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction` 或参数缺失的 RUC 表，防止未来参数修改破坏等价性。
- 新的本地含波浪 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷关闭。24h 原始矩阵由 `345,992/263,810/1,794,507` 变为 `345,992/231,074/1,729,035`（variables/rows/nonzeros），目标完全相同；presolved `129,335/260,116/1,269,506`、`AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier 和 67,614 simplex/crossover 均不变。因此它是安全的构建瘦身，并非已证实的 Barrier 加速。
- 8760h 静态预估更新为 `41,186,792` variables、`55,928,636` estimated constraints、`497,144,388` estimated nonzeros、`33.40 GiB`。这不证明 factorization 可行，不能触发固定服务器 8760h 或新付费云端任务。本轮未连接或修改固定服务器/ParaCloud；服务器 checkout、进程、输出和队列状态必须在任何后续部署前重新实时核验。

## 2026-07-27 Base 定义重置为含波浪能；仅本地验证，未部署

- 用户已将 Base 定义为风电（含海风）、光伏和波浪能共同参与的连续 LP。提交 `c992550` 将 `base` 的 `wave_energy=true` 固化，并仅保留一个柔性覆盖层 `flexible_load_comfort_v3_v2g_5pct`：它继承含波浪 Base，再启用 `comfort_envelope_v3`、V1G 和因果日内 5% V2G。旧的 V1、state-v2、单独 wave/comfort 及组合情景 JSON 已删除；历史根和记录保持原样，不能改名为新 Base。
- 本地设置 `CISPO_WAVE_ROOT` 后回归 `66/66` 通过；两个身份的 1h/24h 新根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，所有 hard checks 为真。24h Base/柔性覆盖层的峰值 RSS 分别为 0.735/0.731 GiB；全年静态 preflight 分别为 36.47/37.63 GiB，均只是模型规模估计。
- 此边界变化尚未部署到固定服务器；先前服务器上的 wave-off Base 168h/744h 结果保留为历史数学、物理 QC 与性能证据，但不是新 Base 的可比求解门禁。此次未写入服务器 checkout、进程、输出，也未修改 ParaCloud 队列或启动新任务。固定服务器 8760h 和新付费云端任务继续禁止。

## 2026-07-27 本地全模块联合敏感性门禁；未部署到服务器或云端

- 新增本地独立情景 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct`，在同一连续 LP 中启用既有 marine `grid_uid` 波浪能、`comfort_envelope_v3` 冷热状态、EV V1G 和日内因果 5% V2G。它保持 `EVIDENCE_ANCHORED_PARAMETERS_REQUIRE_SENSITIVITY`，不是 Base；Base 默认开关与任何科学边界均未改变。
- 本地 1h、24h、168h 新根均达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，完整回归 `67/67` 通过。联合 168h raw/presolved 为 `1,081,688/1,429,226/10,293,428` 和 `751,365/865,314/7,363,654`，`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`，180 Barrier、239,930 simplex/crossover、602.265 s、3.296 GiB 峰值 RSS。详情和局限见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。
- 全年 preflight 的 37.63 GiB 是静态构建估计，不能证明 Barrier factorization；因此本工作不授权固定服务器 8760h 或新付费云任务。未对服务器 checkout、运行进程、现有输出或 ParaCloud 队列作任何写入。若以后要上服务器，只能在空闲复核后以新输出根做单一匹配 168h A/B；不得与其他求解并发。

## 2026-07-27 固定服务器 Base 168h manifest 闭合门禁

- 先实时确认固定服务器无 CISPO/Gurobi 进程、约 69 GiB 可用内存、checkout 干净于 `c879c99`，随后仅 fast-forward 到已经推送的 `67482ab`；P0 实施提交为 `7499062`。相对于原服务器模型实现，部署代码的唯一模型邻接差异是通用 runtime 日志排除，不改变 LP、数据、情景、目标函数、约束或时空边界。
- 服务器以三个版本化数据根运行完整 discovery 回归，结果 `67` 项通过、`2` 项可选 xarray 测试跳过。随后单独启动一个 Base 168h 根 `/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`，使用 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48`、`Crossover=1` 和 generic `stdout.log`/`stderr.log` wrapper 重定向；无并行求解。
- 终态为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷/波浪能均关闭，所有 hard checks 为真。原始矩阵 1,393,915 行、1,011,079 列、9,797,949 非零元；presolved 为 729,559/817,723/7,001,232，presolve 22.89 s、ordering 26.08 s，`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、`Factor Ops=8.436e10`。Gurobi 为 161 次 Barrier、226,659 次 simplex/crossover、614.894 s；端到端为 12:24.94、进程树峰值 RSS 3.453 GiB（`/usr/bin/time` 3,641,828 KiB），zero swaps。
- 物理/数值关键值：目标 `2,028,598.8440447072 million CNY`，最大功率平衡残差 `3.91e-12 GW`，最大约束/边界/对偶违例 `4.17e-8/4.11e-12/1.75e-10`。该根标记为 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为全年科学结论。
- P0 直接复核：`result_manifest.json` 的 `excluded_runtime_files` 恰为 `run.pid`、`stderr.log`、`stdout.log`；完成后 stdout/stderr 分别为 18,072/1,006 bytes，科学 manifest 仍零失败。这验证了 finalize 后 wrapper 继续打印的实际运行路径。既有 744h 根完全未写入；没有固定服务器 8760h 或新的 ParaCloud 任务。后续仅按 P2 设计目录外只读审计或按 P3 做匹配 A/B，不得因本日志缺陷立即重跑 744h。

## 2026-07-27 本地 manifest 契约与 Base 短门禁闭合

- 本地实施提交 `7499062` 将通用 `stdout.log`、`stderr.log` 加入 runtime-managed manifest 排除集合。在不改变 LP、数据、场景、目标函数、约束、时空边界或 solver profile 的前提下，修复了已知的通用重定向日志契约缺陷。
- 回归先 finalize 科学 manifest、随后向两类 wrapper 日志追加内容，再确认 `validate_result_manifest()` 仍通过。聚焦测试及完整本地 `unittest discover` 套件通过 `67/67`。
- 新的独立 2030 Base 诊断 `outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均为 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base`、灵活负荷/波浪能关闭和 result manifest 闭合。24h 根记录 342,343 个变量、262,201 条约束、1,771,702 个非零元、41.296 s 求解时间与 0.725 GiB 进程树峰值 RSS；它们是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。
- 未改变固定服务器/云端 checkout、进程、输出或调度状态，既有 744h 输出按字节保全。在任何新的服务器 168h 门禁之前，须推送精确审查提交并重复实时核验服务器空闲、checkout 和内存。固定服务器 8760h 仍禁止。

## 2026-07-27 744h optimal/QC pass; strict manifest closure failed

- 2026-07-27 对话收束时再次实时复核：固定服务器无 CISPO/Gurobi 进程，约 69 GiB 可用内存，checkout 干净停留在实现 `c879c99`；本地文档分支起始 HEAD 为 `3664177`。ParaCloud `squeue -u a8s001819` 为空，历史作业状态仍为 `4003088=COMPLETED build-only`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`，没有已验收的 8760h 结果。
- ParaCloud job `4004585` is terminal `TIMEOUT` after `1-00:00:25`; its batch step is `CANCELLED` after `1-00:00:32`. It reached Barrier iteration 35 at solver time 82,521 s, with primal residual `1.05e8`, dual residual `2.68`, complementarity `6.03e6`, primal objective `2.0166e11` and dual objective `-1.4513e13`. It was still far from acceptance.
- Sampled MaxRSS remains 499,919,116 KiB = 476.76 GiB. The run did not produce `solve_report.json`, `solution_qc.json` or `result_manifest.json`; it is neither solved nor evidence of infeasibility. Preserve the cloud root unchanged. No cloud job is active.
- The fixed-server implementation remains at `c879c99`; local commits after it are documentation continuity updates and must not be mistaken for a different deployed model. The complete local suite at the implementation milestone passes 67/67 and the server solver-profile tests pass. Both 168h spill formulations are `OPTIMAL + solution_qc=PASS`. Projection takes 641.996 s and explicit spill 654.026 s, but explicit spill has lower presolved rows/nonzeros, `Factor NZ`, `Factor Ops` and telemetry solver memory; it is also materially faster in the paired 24h flexibility case. Explicit spill is therefore retained for the memory-bound full-year target.
- Machine-readable evidence is saved at `/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.{json,csv}`. The two original output roots are preserved.
- Persistent solver telemetry, graceful termination and seven traceable numerics-only solver profiles are validated. The user has authorized one-at-a-time 744h or longer stress tests subject to the memory gate. Do not run concurrent CISPO solves and do not start fixed-server 8760h.
- The 168h dual-simplex result overturns its 24h ranking: after 905.073 s/421,470 pivots it remained infeasible and was gracefully terminated, producing a traceable `INTERRUPTED` report. Peak process-tree RSS was only 2.594 GiB, but runtime already exceeded complete Barrier-32 by 38.4%. Dual simplex is excluded from 744h; Barrier-16 and CPU-PDHG remain pending.
- Barrier-16+AMD is `OPTIMAL + solution_qc=PASS` in 644.636 s with 3.187 GiB peak RSS, modestly better than Barrier-32. Forced AMD nevertheless raises Factor NZ/ops by 5.21%/25.54%. A clean `barrier_16_auto_order_v1` control is added before choosing a 744h profile; CPU-PDHG remains pending.
- Barrier-16 automatic order is the accepted scale-up profile: `OPTIMAL + solution_qc=PASS` in 637.344 s, unchanged reference factor structure, 3.538 GB telemetry solver memory and 3.459 GiB process-tree peak.
- The corrected CPU-PDHG root `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2` was gracefully stopped after 3,074.134 solver seconds and 496,035 last recorded telemetry iterations. It used only 1.990 GB peak solver memory and 2.503 GiB peak process-tree RSS, but had no feasible solution; the terminal region retained primal residual around `49.5`, about `0.6%` primal-dual objective gap and rising dual residual. PDHG is excluded from the first 744h gate but retained as low-memory research evidence.
- The five-profile machine-readable comparison is `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}`.
- The fixed-server 744h Base gate was launched at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order` from clean HEAD `c879c99` with about 69 GiB available RAM, `barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and `SoftMemLimit=48`; Python PID at launch was `663050`.
- Its build phase passed in 341.673 s: 3,686,023 variables, 5,920,701 constraints, 42,360,391 nonzeros and 4.977 GiB build peak RSS. Presolve took 223.80 s and reduced the matrix to 3,088,821 rows, 3,017,979 columns and 30,884,732 nonzeros. Ordering took 115.48 s; `AA' NZ=6.449e7`, `Factor NZ=8.062e8` (about 9.0 GB) and `Factor Ops=6.197e12`. An early Barrier checkpoint at iteration 4 recorded 492.91 solver seconds, 25.087 GB peak solver memory, about 19.1 GiB process RSS and about 50 GiB host-available memory.
- Barrier subsequently completed normally in 244 iterations and 8,917.48 solver seconds with interior objective `2,196,881.94 million CNY`. During crossover, dual pushes fell from 1,044,784 to 464,775 remaining, and telemetry reached 358,606 simplex iterations at 9,996.25 s; solver memory was 13.948 GB, process RSS about 13.8 GiB and host-available memory about 55 GiB. These are retained as intermediate checkpoints; the terminal result is recorded below.
- Terminal state: no CISPO process remains. The 744h run is `OPTIMAL + solution_qc=PASS`, objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations, 1,451,182 simplex iterations, 3:52:03 wall time and 23.121 GiB peak process-tree RSS. All hard QC checks pass; maximum constraint/bound/dual violations are below `1e-7`, maximum power-balance residual is `2.40e-10 GW`, AC bidirectional edge-hours and DC reverse flow are zero, scenario is Base, and flexibility/wave are disabled.
- Strict manifest acceptance fails only on `size:stdout.log`: the result manifest records 63,631 bytes while the completed redirected log is 66,236 bytes. All other 57 manifest entries validate. This is caused by using the generic wrapper name `stdout.log`, which is not in `RUNTIME_MANAGED_FILES`, followed by the program's final report print after manifest generation. Preserve the output unchanged and classify it as mathematical/QC evidence, not a closed reproducibility gate.
- Fixed-server checkout remains clean at `c879c99`; the host has about 69 GiB available memory and no active CISPO solve. Do not start 8760h or another cloud task. Exact next action is a reviewed minimal wrapper/manifest-contract fix with tests and a separately identified closure path.
- 下一阶段门禁顺序：本地修复通用 wrapper log 排除/终结契约并增加 append-after-finalize 回归 → Base 1h/24h `OPTIMAL+QC+manifest` → 空闲服务器新根 168h → 决定既有744h采用独立只读审计还是严格重跑 → 匹配24h/168h/744h求解性A/B。新的云端8760h需要单独付费授权、不可变hash、高内存/线程/时限方案和停止规则；固定服务器仍禁止8760h。

## 2026-07-25 20:30 CST Barrier-32 reached iteration 23

- Job `4004585` remains `RUNNING` on `m4cg1702` after 17:55:54 and has passed the exact stage where the 128-thread run failed.
- Ordering completed in 3,180.53 s. Gurobi reports `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, approximately 340.0 GB factor memory, `Factor Ops=2.448e15` and `Threads=32`.
- Barrier iteration 23 completed at solver time 60,528 s. Primal residual/complementarity improved from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7`; the run is progressing but is not converged and its primal/dual objectives remain far apart.
- `sstat` reports 499,919,116 KiB MaxRSS = 476.76 GiB and 499,955,580 KiB MaxVMSize. This is below the prior sampled 526.99 GiB peak, but it does not establish a safe lower bound for future runs.
- Slurm has 6:04:06 remaining and ends at `2026-07-26 02:34:26 CST`. Recent iterations require about 30-32 minutes, so completion within the current 24h wall limit is uncertain. The Slurm limit will arrive before Gurobi's configured 86,400-second optimize limit because model construction consumed about 41 minutes.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent; only `build_report.json` is present. No scheduler parameter was changed during this read-only audit. Do not start 2040 or another job.

## 2026-07-25 02:35 CST authorized Barrier-32 cloud retry running

- ParaCloud job `4004585` started at `2026-07-25 02:34:26 CST` on `m4cg1702`. It uses the unchanged `22fb493` Base/`city_337` release, 700G and 24h, with only Gurobi `Threads` reduced from 128 to 32 relative to failed job `4003172`; `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640` and all scientific settings remain unchanged.
- The additive script is `cloud_cispo_8760_2030_base_barrier32.sbatch`, SHA256 `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`. Output is isolated under `outputs/full_year_2030_base_22fb493_barrier32_700g_v0725`.
- The 50-test gate passed in 11.845 s. Runtime stdout reports `FULL_SOLVE_CPUS 32`, and `optimization_2030_cloud_32threads_640gsoft.json` confirms `threads=32`, `presolve=2`, `method=2`, `crossover=1` and `soft_mem_limit_gb=640`.
- Although the script requests 32 CPUs per task, Slurm allocated 96 CPU/billing units because the 700G request exceeds the partition's per-CPU memory ratio. Cost accounting therefore accrues at 96 allocated core-hours per wall-clock hour, while Gurobi remains capped at 32 threads.
- Failed job `4003172` consumed 2,642,304 allocated CPU-seconds = 733.973 core-hours. Its actual `TotalCPU` was 7:03:11. The scheduler's account report shows 48,355 CPU-minutes = 805.917 core-hours for user `a8s001819` across all jobs in the 2026-07-24 to 2026-07-26 window, but it exposes no paid-credit or remaining-quota balance.
- This is active engineering evidence, not an accepted scientific result. Do not change the release, start 2040 or submit another retry while `4004585` is active.

## 2026-07-25 02:14 CST cloud 2030/8760h solve failed OOM before barrier

- ParaCloud job `4003172` is terminal `OUT_OF_MEMORY` with exit `0:125`; it ran from `2026-07-24 20:24:47` to `2026-07-25 02:08:50` for 5:44:03 on `m4cg1702`, using 128 CPUs and a 700G request.
- The full model build succeeded earlier. Gurobi then spent 17,932.25 s in presolve, reducing 68,189,325 rows/40,912,327 columns/515,040,080 nonzeros to 37,982,903/35,423,761/400,861,556.
- Ordering for barrier factorization ran for at least 140 s, but no barrier statistics or iteration 0 appeared. The Python process was killed by Slurm before an optimization iterate existed.
- Accounting records 526.99 GiB MaxRSS and 527.03 GiB MaxVMSize; CPU efficiency was 0.96%. The node is configured with 750G and rebooted shortly after the OOM event, so the sampled peak does not establish the true instantaneous memory requirement.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent. Preserve `outputs/full_year_2030_base_22fb493_128cpu_700g` as failed engineering evidence; it is not accepted.
- No ParaCloud CISPO job is now active. Do not rerun the identical barrier configuration, do not start 2040, and do not treat the successful 53.633 GiB build-only result as evidence that barrier factorization fits.

## 2026-07-25 wave module corrected to existing marine grid; combined cases added; not deployed

- This local correction supersedes the spatial mapping and scale figures in the wave note immediately below; no accepted server/cloud release, checkout, data root, process or output changed.
- Raw wave rows are intersected with existing `optimization_points.csv` coordinates within `0.02` degrees and then restricted to `is_land=0`. The resulting contract contains 1,285 unique existing marine `grid_uid` rows (1,284 positive-potential options), 9,798.111 GW retained raw potential and 57 imputed-CF rows. The actual maximum coordinate difference is `4.96e-5` degrees.
- Province, substation and `city_337` load-center identifiers now reuse the exact existing `grid_uid` route. The prior nearest-offshore-wind proxy, including erroneous model-boundary-external matches up to roughly 1,524 km, is removed.
- Explicit combined cases `wave_energy_medium_v1_flexible_load_v1` and `wave_energy_medium_v1_flexible_load_comfort_v3` enable both modules in one LP while Base and single-module cases remain isolated.
- Wave and wave+flex preflight reports have overall `PASS` status with 72 records each (67 `PASS`, 2 `INFO`, 3 pre-existing unrelated `WARN`); the complete local regression passes 62/62. Base/wave/wave+flex-V1/wave+comfort-V3 24h build-only gates are respectively 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. No optimization was started.
- Full-year static estimates are 41,186,792 variables/67,877,276 constraints/532,990,308 nonzeros/36.47 GB for wave, and 42,816,152/68,182,781/533,906,823/36.91 GB for wave+flex V1. These are not solve-memory guarantees.

## 2026-07-25 optional wave-energy module passed local build gates; not deployed

- Local worktree based on `796a6fc` adds `wave_energy_medium_v1` without changing Base `VRE_TECHS`, accepted server/cloud releases, data roots, processes or outputs.
- The source audit finds 4,194 unique grids, 4,187 positive-potential grids, 35,898.123 GW raw potential, ten CF scenarios, 241 imputed-CF grids and no 2060 profile. Capacity potential is identical in every source scenario.
- `data/wave/wave_sites.csv` and `wave_input_manifest.json` are reproducible from `scripts/build_wave_energy_inputs.py`; hourly data stay external and require `CISPO_WAVE_ROOT`.
- Wave preflight passes 68 checks and the complete local regression passes 61/61. Base 24h build-only remains 342,343 variables/262,201 constraints/1,771,704 nonzeros; wave 24h build-only is 351,798/266,712/1,867,703. No optimization was started.
- Full-year static estimate with wave is 41,192,598 variables, 67,880,179 constraints, 558,429,297 nonzeros and 37.23 GB. This is not a solve-memory guarantee.
- Deployment remains blocked pending review of maritime routing, scenario-specific potential, 2060 treatment and China cost sensitivities. Do not stage `wave_grid.nc`, change a live checkout or start any wave solve without a new versioned release and explicit authorization.

## 2026-07-24 local comfort-aware flexibility V3 accepted at 24h; not deployed

- Local worktree based on `796a6fc` adds independent `flexible_load_comfort_v3` and `flexible_load_comfort_v3_v2g_5pct` scenarios. Base, accepted V1/V2 and server/cloud releases are unchanged.
- The generated ignored-data table `data/load/flexible_load_envelope_v3.csv.gz` contains 1,357,800 province-year-hour rows. It reconstructs the `Power_curve_V2` BAIT/balance-point formula with a +/-1 C setpoint envelope, retains the upstream future `thermal_multiplier`, matches the National_model load components, and has SHA256 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
- Thermal flexibility is a causal daily-reset equivalent state. EV V1G uses a rolling 12h cumulative latest-service constraint. Optional V2G is limited to 5% of province-day baseline EV peak, has a four-hour energy envelope and requires charge before discharge through a daily-zero causal state.
- Costs are explicit objective components: thermal reduction/increase are separate, V1G relocated energy is paid once, and V2G discharged energy is paid once while charging energy/losses remain in normal system operating costs.
- Local regression passes 58/58. The no-V2G 2030 24h gate `outputs/diagnostic_24h_flexible_load_comfort_v3` is `OPTIMAL + solution_qc=PASS` with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 33.63 s solver time and 0.739 GiB peak process-tree RSS.
- The final independent 5% V2G gate `outputs/diagnostic_24h_flexible_load_comfort_v3_v2g_5pct_final` is also `OPTIMAL + solution_qc=PASS`, with 351,271 variables, 266,789 constraints, 1,821,550 nonzeros, 38.60 s solver time and 0.718 GiB peak RSS. V1G and V2G share one aggregate grid-charging power ceiling; its violation is zero. All transition/terminal checks pass and simultaneous operations are zero.
- This is local truncated-horizon engineering evidence only. No server/cloud state was changed or refreshed during this milestone. Do not launch fixed-server 168h/744h/8760h or another cloud job without explicit authorization and a new versioned release.

## 2026-07-24 21:17 CST prior cloud checkpoint (superseded by OOM terminal state)

- Job `4003088` completed normally in 40m20s (`COMPLETED`, exit `0:0`). The full Base model has 40,912,327 variables, 68,189,325 constraints and 515,040,080 nonzeros. Build-only peak process-tree RSS is 53.633 GiB.
- The success dependency released job `4003172`, now running on `m4cg1702` with 128 CPU, 700G and a 24h limit. Its full model build completed in about 40m32s with identical statistics and 53.686 GiB build peak.
- Gurobi 13.0.2 accepted the WLS license, `Threads=128` and `SoftMemLimit=640`, and entered `Optimize`. At the audit checkpoint the log had not yet emitted presolve completion or barrier iterations; current stage is presolve/matrix preprocessing.
- Current `sstat` batch MaxRSS is 101,085,156 KiB (96.402 GiB). This remains far below both the 700G allocation and 640G solver soft limit, but presolve/barrier factorization may increase it further.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` do not yet exist. The task is healthy but not accepted. Continue monitoring without changing the release or starting 2040.

## 2026-07-24 local `flexible_load_state_v2` accepted; not deployed

- Local implementation `271c6dc` adds an independent state-based flexibility scenario. Base and the accepted legacy V1/V2G scenario JSON files are unchanged.
- Heating/cooling use daily-reset equivalent inventories with explicit retention/efficiency and loss accounting. EV V1G uses a causal charging backlog derived from the immutable `Power_curve_V2` uncontrolled charging baseline; `ev_hour_weight` is not treated as plug availability. The new formulation refuses V2G until calibrated availability, battery-energy and departure-service inputs exist.
- Full local regression passes 56/56. Final 2030 24h gate `outputs/2030_24h_v0724_flexible_load_state_v2_final` is `OPTIMAL + solution_qc=PASS`, with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 32.84 s solver time, 0.705 GiB peak process-tree RSS, transition residuals at most `8.88e-16 GWh`, zero terminal state/backlog, zero simultaneous up/down and a valid result manifest.
- Four-year 1h diagnostic chain `outputs/planning_sequence_1h_v0724_flexible_load_state_v2` passes all four solve/QC/manifests and immediate `--resume`. It is engineering evidence only.
- Full-year static estimate is 43,356,367 variables, 68,724,249 constraints, 524,283,387 nonzeros and 36.84 GiB model memory. This is not a barrier-memory guarantee and no 8760h job was started.
- No fixed-server or cloud checkout, process, input or output was changed. Retain the existing active cloud release and output roots unchanged. Any deployment of `271c6dc` requires a new versioned identity and fresh authorized 24h/168h gates.

## 2026-07-24 local post-release hardening; not deployed to active cloud run

- Local code based on `4b5bd98` now forbids wind-to-PV CF fallback, hard-fails unresolved wind after same-grid mixed-wind, and requires land-centroid donors for nearest-province PV fallback. Current data have 35 onwind and 10 offwind same-grid mixed-wind rows, zero wind-to-PV mappings, and 141 PV-family nearest-grid fallbacks; the land-donor restriction changes zero current donor assignments.
- Focused tests pass 4/4 and the full local suite passes 54/54. Two live contract documents now describe production `city_337` as a 337-city annual allocation/transmission proxy, not a 337-city hourly nodal dispatch network.
- This hardening is local only. Do not change the staged cloud release, its checkout, inputs or output roots while its authorized jobs are active. Any later deployment requires a new identity and fresh small gates.

## 2026-07-24 ParaCloud 24h/168h accepted; full-year build and authorized single-year solve active

- Cloud 2030 Base 24h job `4003035` (32 CPU, 64G) and 168h job `4003045` (32 CPU, 64G, `m4ci1805`) each pass 50/50 tests, `OPTIMAL`, `solution_qc=PASS` and independent result-manifest validation. Their solver statistics are respectively 342,343 variables/262,201 constraints/1,771,703 nonzeros/26.978 s/0.834 GiB and 1,011,079/1,393,915/9,797,949/377.057 s/3.661 GiB.
- Full-year build-only job `4003088` is running on `m4cm1904` in `amd_a8_768` with 128 CPU and 700G. It constructs but does not optimize the 2030 Base 8760h LP, writing `outputs/full_year_build_only_2030_22fb493_128cpu_700g`.
- The user explicitly authorized one real 2030/8760h Base solve. Job `4003172` is submitted as `afterok:4003088`, requests 128 CPU, 700G and 24h, writes the separate root `outputs/full_year_2030_base_22fb493_128cpu_700g`, and raises only Gurobi `soft_mem_limit_gb` from the fixed-server 80 to 640. Do not start a successor year or a second full-year run while this evidence is pending.

## 2026-07-24 ParaCloud city_337 release staged; 8760h preflight and repaired WLS smoke passed

- New cloud release: `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`. It carries code archive `22fb493` (SHA256 `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`) and exactly 11,350 runtime data files whose cloud SHA256 check matches the fixed-server manifest (`662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`). The release is additive and does not modify the fixed server.
- Cloud preflight job `4001137` completed on `m4ci1905.para.bscc`: 175.17 GiB available memory exceeds the full-year 96 GiB gate. For 2030 Base/city_337 it estimates 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB static model memory. This is a data/scale gate only, not a Gurobi build or solve.
- Cloud environment was completed offline with the project numerical stack and `pip check` passes. The user-authorized repair of the three `.bashrc` proxy exports was verified on compute node `m4ci1905` by job `4002980` (`PROXY_EXPORT_COMPUTE_PASS`, HTTP 302 through `172.16.110.3`). WLS job `4002981` then reached `Env.start()` and solved its LP to `OPTIMAL` with `GUROBI_SMOKE_PASS`. Its standalone 10-second curl check timed out, but the authenticated Gurobi solve is the decisive license evidence.
- No cloud 24h/168h, full-year build-only or full-year solve is active. Next cloud action is a new versioned 24h gate, then a 168h gate, with explicit Gurobi thread limits; the full-year build-only gate remains later. Fixed server remains idle and restricted to its accepted 24h/168h roots; do not start fixed-server 744h/8760h.

## 2026-07-23 city_337 fixed-server 168h V2G accepted; server idle

- Four-year 168h V2G root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 792.55/806.12/953.60/1033.25 s, wall time is 1:09:57, peak RSS is 4,087,888 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. The V2G model has 1,057,951 variables, 1,404,982 constraints and 10,100,013 nonzeros. All hard checks pass; maximum center/province/intra/power residuals are `5.12e-12/3.64e-12/3.11e-08 GWh` and `1.60e-10 GW`; BECCS closure is zero.
- V2G transition residual is at most `1.90e-13 GWh`, simultaneous charge/discharge is zero, and period charging losses of 7.747/4.509/13.909/42.092 GWh equal both `charge-discharge` and net-load energy change to numerical precision.
- No CISPO/Gurobi process remains. Base, V1 and V2G have all passed 24h/168h city_337 gates. Do not start fixed-server 744h/8760h without separate authorization.

## 2026-07-23 city_337 fixed-server 24h V2G accepted

- Four-year 24h V2G root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 44.81/43.45/48.35/45.23 s, wall time is 9:10, peak RSS is 934,340 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. V2G is enabled only in this separate scenario; maximum transition residual is `1.83e-12 GWh`, simultaneous charge/discharge is zero, and 2040/2050/2060 charging losses of 0.1563/2.3423/3.4673 GWh close exactly against net-load energy change within floating-point precision.
- Maximum center/province/intra/power residuals are `6.37e-12/5.24e-13/4.61e-10 GWh` and `2.46e-12 GW`; heating/cooling/EV V1G daily conservation, security and BECCS checks also pass.
- The follow-on 168h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h V1 accepted

- Four-year 168h V1 root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`; runtimes are 714.39/816.08/1007.71/980.09 s, wall is 1:08:59, peak RSS is 4,030,672 KiB and swaps are zero.
- All four 59-entry SHA256 manifests validate. Each year exports 337 center balances, 2,022 center-technology rows, 642 intra edges, 31 province accounts, 31 flexibility accounts and 57 output-catalog data rows. Maximum center/province/intra/power residuals are `5.06e-12/3.64e-12/4.69e-11 GWh` and `1.75e-10 GW`; BECCS closure is zero.
- Maximum heating/cooling/EV V1G daily-energy residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; simultaneous up/down counts are zero and V2G is disabled. Four `RESUMED_ACCEPTED` records revalidate scenario and strict state-chain identity.
- The V1 matrix has 1,042,327 variables, 1,399,774 constraints and 10,016,685 nonzeros: +3.09%, +0.42% and +2.23% versus Base. Total solver time is nevertheless 8.23% lower; 2050/2060 crossover (265.69/288.77 s) is the remaining performance variability.
- The follow-on 24h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h V1 accepted

- Four-year 24h V1 root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`, has 59 manifest entries and closes the 337-center network; runtimes are 40.84/44.23/43.39/41.95 s.
- The wrapper completed in 9:35 with peak RSS 929,096 KiB, zero swaps and exit status zero. Maximum daily heating/cooling/EV V1G residual is `1.14e-13 GWh`, all simultaneous up/down counts are zero, and V2G is explicitly disabled.
- Capacity margin remains 5%, effective inertia remains 3.5 s, all hard checks pass and BECCS net-carbon closure is zero. These are truncated engineering diagnostics, not scientific planning results.
- The follow-on 168h V1 chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h Base accepted

- Four-year 168h Base root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337` is accepted: sequence and `--resume` pass, all years are `OPTIMAL + solution_qc=PASS`, runtimes 733.00/811.58/892.10/1397.12 s, wall 1:13:47, peak RSS 4,085,152 KiB and zero swaps.
- Every year has zero false hard checks, 59 valid manifest entries, 337 center balances, 642 intra-edge outputs and 31 province accounts. Maximum network/power residuals are below `1.78e-10` in their reported units; BECCS closure is numerical zero.
- Relative to the prior 278 Base gate, the 168h city model adds 1,031 variables, 924 constraints and 2,749 nonzeros. Total solver time rises 4.68%; the measurable risk is 2060 Crossover (706.6 s), not model construction or memory.
- The follow-on 24h `flexible_load_v1` chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h accepted; 168h active

- Fixed-server checkout is clean at `cf39e0a`; active data root is `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. The city archive SHA256 matches local: `c1451d95c3303f98e53434cd29abc4288f486cba04c99a2c591380b010d470bb`.
- Server regression is 50/50, smoke is 142/142, readiness/full-license and preflight pass. The initial 139-check smoke failure was an obsolete 8-technology row expectation; the production table is correctly 31×5×10=1,550 unique rows and the corrected smoke now validates this explicitly.
- Four-year 24h Base root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337` and immediate `--resume` are `PASS`. Runtimes are 43.29/48.82/41.17/46.90 s, wall time 7:21, peak RSS 930,204 KiB, and all four 59-file manifests validate. Base flexibility is disabled; 5% capacity margin, 3.5 s inertia, power/network/BECCS checks all pass.
- The new four-year 168h Base chain is active as PID `3321747` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`. Do not change checkout or data root until it exits and is audited. Do not start 744h/8760h.

## 2026-07-23 city_337 local gate and pre-deployment server audit

- Local implementation commit `8e76753` promotes `city_337` to production while retaining `natural_earth_278` as a separate CISPO replication/sensitivity package. The package has 337 centers, 16,609 VRE routes, 2,030 hydropower routes, 642 intra-provincial edges and 203 positive 2025 initial edges.
- Data QA is `PASS`: 31 connected provincial graphs, province demand-share error at most `1.11e-15`, initial network-balance residual at most `7.28e-14 GW`, and exact joint routing is never materially worse than the old nearest-substation-first rule (mean distance reduction 20.21 km).
- Local validation passes 50/50 tests and 61 preflight checks. `outputs/planning_sequence_1h_v0722_city337` passes all four years and `--resume`; each year is `OPTIMAL + solution_qc=PASS`, has 337 load-center rows, a closed 59-file result manifest, Base flexibility disabled, 5% capacity margin and 3.5 s effective inertia.
- Live fixed-server audit before deployment: branch `codex/cispo-2030-full-lp`, clean HEAD `6ed943a`, no active CISPO/Gurobi process, about 35 GiB available memory, 21 GiB swap occupied and 3.8 TiB free on `/data`. The accepted V1 168h root remains `PASS` after its prior four-year resume audit.
- Exact next gate: push/deploy the code plus a SHA256-verified additive `city_337` data root, pass server tests/readiness, then use new 24h and 168h Base output roots. Do not reuse accepted roots and do not launch fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 reviewed reliability parameters (local only)

- Local Git HEAD remains `e28f315`; the working tree now sets Base provincial capacity margin to `5%` and minimum inertia to `3.5 s reference × 1.0 tolerance = 3.5 s effective`.
- Model construction and solution QC use the same effective-threshold resolver. Legacy scenario overrides containing `minimum_system_inertia_seconds` remain accepted and take precedence within that scenario.
- Local regression tests pass 49/49. Local 1h output `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS`; effective inertia is `3.5 s`, capacity-margin/inertia checks pass and the result manifest validates. No fixed-server checkout change, server process or server output was created.
- Fixed-server checkout and all accepted Base/V1 gates remain at their previously recorded versions and therefore still reflect the old committed security configuration. Do not compare new local results against those outputs without identifying this feasible-set change.
- The next server action, if authorized, is a new versioned 24h gate after committing/pushing/deploying the exact reliability update. Do not reuse accepted output roots and do not start fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 V0722 flexibility deployment and server gates (authoritative)

- Local commit `c62b769` closes the CISPO-equivalent BECCS carbon mass balance without changing the published net factors, objective or feasible set. Local validation is 47/47 tests plus an `OPTIMAL/QC PASS` 1h gate with zero new closure residuals and a valid manifest. This commit is not deployed; the fixed server remains unchanged at `6ed943a`, and no new server job was started.
- Local commit `c91828a` adds a diagnostic sensitivity-suite runner and passes 45/45 tests plus a real 1h Base/V1/V2G suite (12/12 year-scenario cases `OPTIMAL + solution_qc=PASS`, closed manifests, identity-safe `--resume`). This is local interface evidence only: the runner is not deployed, no server job was started, and the fixed-server checkout remains clean and idle at `6ed943a`.
- Commit `6ed943a` implements the optional flexibility/scenario interface and is now the clean fixed-server checkout. It passes 42/42 local and server tests plus local Base 1h, V1 24h and V2G 24h `OPTIMAL/QC PASS` gates.
- The fixed-server Base 168h gate ran from checkout `b6ca42d`, whose model implementation baseline is `0c1eaf2`; this corrects the earlier shorthand that described the checkout itself as `0c1eaf2`. The active data root remains `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`.
- The server four-year 24h sequence and immediate resume audit pass for 2030/2040/2050/2060.
- Four-year 168h Base sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS`: all years are `OPTIMAL + solution_qc=PASS`, every result manifest validates, the resume identity audit passes, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero.
- Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` completed `PASS` and passed resume identity validation. Wall time is 6:32, peak RSS is 946,804 KiB and all daily flexibility residuals are below `6.44e-13 GWh` with no simultaneous up/down.
- Four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, all hard checks pass, and every 59-file result manifest validates. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Maximum heating/cooling/EV V1G daily-energy residual is `8.17e-13 GWh`, simultaneous up/down counts are zero, and scenario SHA256 is consistently `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- A fresh 168h `--resume` identity audit at 2026-07-22 16:05 CST completed `PASS` with four `RESUMED_ACCEPTED` years. The accepted capacity-cohort chain remains explicitly `TEST_ONLY_TRUNCATED_HORIZON` and cannot enter production.
- Flexibility is disabled in Base. Local full-year static estimates are 40.91M variables for Base, 42.54M for V1 and 43.36M for V2G; the 96 GiB availability gate remains unchanged.
- No fixed-server 744h/8760h and no cloud 8760h task is running. The V1 168h gate is now accepted, but cloud production remains gated on calibrated sensitivity assumptions, exact code/data/scenario deployment, cloud 24h/168h gates, explicit Slurm thread limits and explicit cost authorization.

## 2026-07-20 V0720 I/O-contract deployment (authoritative)

- Fixed-server checkout is clean at `b40900a`; active model data are `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds` with the existing versioned hydrology and CF stores.
- Server unit tests pass 34/34 and data-package smoke checks pass 139/139.
- New 24h gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, solve time 43.65 s and peak RSS 0.838 GiB.
- All 27 hard checks pass. The SHA256 result manifest is closed with zero mismatches; all NPZ files are pickle-free; the output catalog has 50 files, the field dictionary has 493 rows, and LP dual export contains 744 hourly price rows plus 3,366 annual constraint-shadow rows.
- At launch, about 88 GiB RAM was available. Another user's four Python training processes occupied about 29 GiB RSS and were not changed. This was safe for 24h only and remains below the 96 GiB full-year build gate.
- No 744h or 8760h process is running. The next full-year solve belongs on the cloud platform after compute-node Gurobi licensing, data staging and small gates are verified.
- The old `5a9f4ab` 744h result remains an engineering solvability gate, not a V0720 or scientific-horizon result. Its old manifest has two wrapper-after-hash mismatches (`run.stdout`, `run.time`); see `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.

## 2026-07-19 V0719 deployed server status (authoritative)

- Current server checkout is `bc83663`, including V0719 capacity-bound/DC active-index commit `451b1c0` plus server smoke-test path fixes `c8db9be` and `bc83663`.
- Active V0719 data root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was created additively; the old `model_ready_20260719_sequential_sparse` root and the completed 744h output were not overwritten.
- Generated V0719 tables are present: `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`. The root also includes `sets/model_years.csv` and canonical smoke/QC support files that were absent from the old sparse root.
- Server smoke checks passed 139/139, server unit tests passed 32/32 and readiness passed with full Gurobi license plus raw-GRFR SHA256 verification.
- Server 24h V0719 solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s and peak process-tree RSS 0.841 GiB. Nuclear floor/upper, biomass+BECCS capacity upper, storage floor, AC bidirectionality and DC reverse-flow hard checks are all zero.
- Requested direct 8760 trial was not launched because the live full-year preflight failed the checked memory gate: `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` against required `96.0 GiB`. The V0719 full-year estimate is 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros.
- The completed pre-V0719 sparse 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remains valid solver evidence for deployed HEAD `5a9f4ab`, but it is not the V0719 scientific boundary.
- Sections below this heading include older handoff snapshots; use this authoritative section for current deployment and launch decisions.

## 2026-07-19 V0719 local capacity-bound correction

- Local working tree based on Git HEAD `f84143a` / implementation base `5a9f4ab` now implements four reviewed corrections: provincial nuclear upper bounds, shared `bio+bioccs` capacity upper bounds, the CISPO Table S17 2030 battery floor, and active-index AC-only reverse-flow variables.
- New reproducible inputs are generated by `scripts/build_v0719_capacity_bounds.py` from `config/capacity_bounds_v0719.json`; `config/model_input_files.json` contract v2 requires all three new tables.
- Local unit tests passed 32/32; data-package smoke checks passed 139/139. The corrected 24h solve under `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints and 1,768,956 nonzeros. Every nuclear/biomass/storage bound residual and every transmission-direction hard check passed.
- Full-year active-index estimate is now 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros; exact variable reduction is `363×8760=3,179,880`. This is a structural estimate, not barrier-memory proof.
- This local V0719 correction is **not yet committed, deployed or used by the server**. The server remains at `5a9f4ab` and its current versioned data root remains unchanged.
- Server check at 2026-07-19 20:14 Asia/Shanghai: corrected old-code 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has completed. `solve_report.json` reports `OPTIMAL`; `solution_qc.json` reports `PASS`. It used the old versioned data root and did not include the uncommitted V0719 capacity-bound/DC active-index corrections.

## 2026-07-19 synchronized server validation

- Current deployed implementation `5a9f4ab`; readiness/raw-GRFR/full-license gates and 29/29 server tests pass.
- Strict corrected 168h output `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`: 1,071,032 variables, 1,392,960 constraints, 10,100,058 nonzeros, `OPTIMAL` in 666.45 s, peak RSS 3.910 GiB and `solution_qc=PASS`. AC bidirectional edge-hours and DC reverse flow are both zero.
- Corrected 744h CPU gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed with `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, Gurobi runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Directionality QC passed with zero AC bidirectional edge-hours and zero DC reverse flow.
- Full-year available-memory gate is now checked in as 96 GiB; the unused `NodefileStart`-style config was removed because this is a continuous LP, not branch-and-bound.
- Solvability audit `ab9dfe8` revises the current-code 8760 projection to approximately 44,091,176 variables, 68,188,384 constraints and 515-524 million nonzeros. The prior 853.5 million nonzero preflight is conservative for the raw matrix, but the reported 46.62 GiB is not a barrier peak-memory estimate.
- The rejected 744h barrier formed `8.289e8` factor nonzeros (about 10 GB), then spent 10,969.01 s in barrier and 9,123.64 s in crossover. Linear factor-memory extrapolation is already about 118 GB at 8760h before the model and workspaces are counted; a direct solve on this 125 GiB host is therefore high risk.
- Earlier pre-launch resource snapshot: server HEAD was `f22b9cf`, about 30 GiB available RAM and 21 GiB/21 GiB swap occupied. This snapshot is superseded by the active corrected 744h status recorded above; 8760 was not launched.
- Full-year build-only requires at least 96 GiB available RAM after V0719 server gates, not merely after this old-code 744h. A successful build-only does not authorize solve; inspect peak RSS and factor-risk estimates first.

- Current implementation commit: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- The production sequence is now 2030/2040/2050/2060, with checksummed capacity-cohort transfer between successive full-year solves.
- Local final 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; `OPTIMAL` in 58.79 s; `solution_qc=PASS`; peak RSS 0.698 GiB.
- Local full-year preflight: 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory; local available RAM does not meet the 64 GiB build gate.
- PHS now uses the GHT 2026 province-level 8h-storage floor/project-pipeline upper: 2030 national floor 65.94 GW and upper 249.191 GW; 2040+ upper 514.755 GW.
- Server readiness and raw-GRFR SHA256 verification passed on the 2026-07-19 versioned data roots; server regression tests passed 24/24.
- Server 24h gate: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; `OPTIMAL` in 60.53 s; `solution_qc=PASS`; peak RSS 0.851 GiB.
- PID `3778049` completed `OPTIMAL`, but the result is rejected: 3,358 material simultaneous AC-direction edge-hours were omitted from the former hard QC. The corrected formulation still needs new server gates.
- Do not start 8760 on the old scientific boundary. The sparse cleanup and corrected 744h gate have passed for deployed HEAD `5a9f4ab`, but V0719 capacity-bound/DC active-index corrections still need commit, deployment to a new versioned data root and fresh 24h/168h/744h gates. Require at least 96 GiB available RAM for build-only; a direct solve remains blocked pending true build/factor-memory review.

## Boundary and architecture

- 2025 is an input boundary only; it is not an optimization year.
- 2030 is the first planning year and represents changes over 2025-2030.
- Production is one continuous LP containing all 8760 chronological hours.
- No Benders decomposition, representative days, sampled hours, or temporal weights are used.
- Optional 744h and 4344h leading-hour horizons are explicitly test-only; 8760h remains the only scientific horizon.

## Implemented

- 31 provinces and 36,686 VRE technology-site rows at 0.25-degree resolution.
- Exact 2023 hourly CF linkage with sparse coefficient construction.
- Continuous capacity-based RUC and cyclic annual commitment/ramp state.
- Battery/PHS SOC and reserve; station-level hydropower and reservoir balance. Commit `b3e6298` adds Stage2 core-mainstem conventional hydropower cascade coupling and is deployed on the server.
- 411 interprovincial corridors, strict hourly power balance, reserve and inertia.
- DAC, annual carbon and biomass accounts, CCS capture and point-level injection.
- Spur/trunk/substation augmentation, memory gate, numerical diagnostics and IIS.
- Production load centers are the 278-node Natural Earth paper replication.
- Annual center energy allocation, provincial export closure and 517-edge intra-province AC500 expansion layer.
- Hydropower station-to-substation/load-center routing and hydro spur/trunk augmentation.

## Verification snapshot

- Current deployed implementation baseline: `827b37f` on 2026-07-19; it contains implementation commit `2a0ee99`. Verify the live HEAD directly because documentation-only synchronization commits follow this baseline.
- Current validated server data paths:
  - `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse`
  - `CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse`
  - `CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019`
- Raw GRFR transfer completed on 2026-07-06 and was verified on the server:
  - `output_pfaf_03_2019.nc`: 3,380,260,808 bytes, SHA256 `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: 5,445,519,752 bytes, SHA256 `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures.
- Hydropower station input: 2,030 rows, 620 reservoir rows, 1,410 run-of-river rows, 0 potential paper-rule mismatches, no missing required columns. Cascade readiness reported 142 nodes, 124 edges, 4 low-correlation edges, 18 max-bound edges and maximum lag 168 h.
- Server regression test on the synchronized checkout/data: 24/24 tests passed with `unittest` in 19.62 seconds.
- Current one-month preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated model memory.
- One-month cascade server preflight: 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros; estimated model memory 4.48 GiB; memory gate passed with about 106.65 GiB available.
- Actual one-month cascade model build: 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros.
- Conservative full-year model-memory estimate: 47.98 GiB; configured `SoftMemLimit`: 80 GiB.
- Local 744h build-only test: 3,032,784 variables, 4,760,844 constraints, 39,084,173 nonzeros; completed in about 134 seconds without optimization.
- Local 24h smoke solve: 365,184 variables, 285,309 constraints and 1,812,785 nonzeros; continuous LP solved to optimality in about 8 seconds after presolve. Maximum center-balance and province-export residuals were `1.16e-13` and `1.14e-13` GWh; no edge flowed in both directions, DPV spur augmentation was exactly zero, and no intra-capacity constraint was violated.
- Six-month/full-year local preflight correctly reported that the 32/64 GiB memory gates were not met; no construction was attempted.
- Server: 96 logical CPUs, 125 GiB RAM, 4.3 TiB free under `/data`.
- Server Gurobi Optimizer and `gurobipy`: 13.0.2 installed under `/home/zz2/opt/gurobi1302/linux64` and `/home/zz2/.local/envs/cispo-2030` respectively; 12.0.1 remains available as rollback software.
- Server license: retrieved successfully with Gurobi 13.0.2 on 2026-07-03, stored at `/home/zz2/gurobi.lic`, and valid through 2027-07-02. The server-issued license ID is 2840423.
- Production-license gate passed on 2026-07-06: Gurobi 13.0.2 solved the deterministic 2,501-variable LP to optimality with objective `1.0`, confirming that the bundled size-limited fallback is not active. This gate is also enforced by `scripts/check_server_readiness.py`.

## Cascade server validation status

- Implementation commit `b3e6298` reads Stage2 core cascade files from `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630`.
- Generated cascade inputs contain 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations. All mapped stations exist in `data/hydro/hydro_stations.csv`, all are `reservoir_storage`, capacity alignment residual is 0.0 GW and the topology is acyclic.
- Travel lags are estimated from 2019 GRFR hourly discharge by 3h-multiple cross-correlation, range 0-168 h. QA warnings remain for 4 low-correlation edges and 18 edges selecting the 168 h maximum search bound.
- Local checks passed: data-package rebuild with 90 QC checks and zero failures, smoke test 118/118 PASS, unit tests 16/16 PASS, one-month preflight PASS, and custom 24h monolithic build PASS with 146 cascade reservoir rows and 124 cascade edges.
- Server readiness, regression, preflight and full 744h model-build gates passed using the versioned cascade data roots.
- The old 744h solve under `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade` was normally interrupted after `37,576.53 s`. Final status is `INTERRUPTED`, `solution_count=0`, and peak RSS is `22.161 GiB`; the output is preserved as the failed numerical baseline.
- Commit `281f9c7` scales water flow/volume variables without changing physical equations. Server 168h validation under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled` reached `OPTIMAL` in `675.56 s`, used `4.061 GiB` peak RSS and passed every `solution_qc.json` hard check.
- Commit `a8cd150` switches hydropower environmental flow to the 2019 single-year monthly P30 proxy and removes obsolete master boundary variables. Server 24h P30 CPU validation under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu` reached `OPTIMAL` in `45.06 s`, used `0.879 GiB` peak RSS and passed `solution_qc.json`.
- GPU-enabled Gurobi is available only in `/home/zz2/.local/envs/cispo-gurobi-gpu` (`gurobipy 13.0.2+cu129`). It confirmed `Start PDHG on GPU`, but the same 24h model with GPU-PDHG was still iterating after about 600 s and was interrupted without `solve_report.json`; CPU barrier remains the default route.
- PID `3778049` completed with 3,955,002 variables, 5,919,470 constraints and 44,169,131 nonzeros; build 348.74 s, solve 20,118.58 s and peak RSS 22.141 GiB. Although the old report says `solution_qc=PASS`, post-audit found 3,358 material bidirectional edge-hours, so the output is explicitly rejected and 8760h remains blocked.
- Commit `1b6da28` aligns with CISPO S4-55/S4-56: AC shared bidirectional capacity, DC fixed direction, `0.001 yuan/kWh = 1 yuan/MWh` flow cost, net-exchange load-center closure and hard directionality QC. Local 26/26 tests and corrected 24h `OPTIMAL/QC PASS` succeeded with zero AC bidirectionality and zero DC reverse flow.
- Corrected server validation also passed: 26/26 tests; 24h Gurobi 13.0.2 `OPTIMAL` in 43.88 s; 0 AC bidirectional edge-hours; 0 DC reverse flow across 363 DC edges; all hard QC and scientific manifest hashes PASS. Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Corrected 744h was initially deferred when available RAM was only about 32 GiB and swap was full; it was launched later after memory pressure cleared and completed `OPTIMAL/QC PASS`. Current authoritative status is recorded at the top of this file.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Open-loop and closed-loop PHS hydraulic pairing data remain unavailable; current PHS is province-level 8h storage with GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Hydropower type labels include low-confidence assigned labels because source data do not provide reliable type labels for all stations; retain them for now and validate later against external station evidence.
- Formal multi-year environmental flow for hydropower; the current cleanup uses the requested 2019 single-year monthly P30 proxy, not a formal 1980-2019 climatological P30. Four low-correlation and eighteen max-bound cascade-lag edges need manual hydrological/topological review.
- Capacity-credit values and spur/trunk proxy costs still need parameter-source review. Base capacity margin and inertia threshold are reviewed locally at `5%` and `3.5 s` but are not yet deployed on the fixed server.
- Intra-center annual capacity uses a 50% design utilization assumption; two western AC500 proxy edges exceed the 1000 km source range.
- Intra-center losses remain zero until their annual energy can be fed back into the provincial hourly balance.

Per-year production entry: `scripts/run_cispo_2030_full_year.py`.
Sequential production entry: `scripts/run_cispo_planning_sequence.py`.
