# CISPO 8760 h 求解参数与分阶段执行决策（2026-08-17）

## 1. 文档状态

```text
decision_status=APPROVED_AFTER_DEFERRED_CROSSOVER_744_STRICT_PASS
parameter_route_goal_status=COMPLETE_WITH_CLOUD_STAGE_A_STILL_RUNNING
current_cloud_job=4139552
current_cloud_action=KEEP_RUNNING_UNCHANGED
fixed_validation=deferred_crossover2_744_validation_v0817_v3_PASS
approved_stage_a_profile=barrier_checkpoint_full_year_cloud_v3
approved_stage_b_profile=deferred_crossover2_full_year_cloud_v3
formal_profile_validation=FIXED_GUROBI_FOCUSED_14_OF_14_FULL_212_OF_212_PASS
scientific_result_available=false
```

本文件汇总当前模型 identity 下已经完成的 strict/relaxed 744 h、V5/744 h、Base/1488 h、
Base/2160 h、两批 5-iteration factor screens 和正在运行的 cloud/8760 h Stage A 证据。它用于冻结
下一次全年运行的工程方案，不把任何截断时域结果解释为年度科学结果。固定服务器 744 h deferred
Stage B 已通过严格终态和宏观配对审计，第 6 节的未来 A/B 参数路线现升级为 approved；实际提交仍须
单独授权、独立 roots 与云资源门禁。

当前云端 `4139552` 已运行多日，继续按原 profile 求解；本文不授权取消、改参、缩容、重排队或启动
Stage B。Gurobi 参数不能在一次活动 optimize 中途安全替换，当前费用已经成为 sunk cost，不应为了采用
尚未完成续接验证的新参数而丢弃已有 Barrier 轨迹。

## 2. 当前模型与实验边界

- branch：`codex/cispo-2030-full-lp`。
- 唯一模型实现基线仍由已验证统一实现及其后续兼容性修复组成；Stage A/B resume 需要在 optimize 前
  验证 source/target manifests、Gurobi version、scientific/data identity、Fingerprint、raw LP dimensions
  和完整变量/约束顺序 digests。
- Base：2024 VRE、wave on、flexible load off；本地所有证据均为 `TEST_ONLY_TRUNCATED_HORIZON`。
- 744 h current LP：Fingerprint `2120635803`，`3,735,087` variables、`4,454,178` constraints、
  `40,395,436` nonzeros。
- 8760 h 单体 LP 必须在大内存云节点运行；固定服务器只用于 744/1488 与受内存门禁约束的工程验证。
- 科学结果必须来自最终 basic solution，而不是 raw Barrier checkpoint；工程 BarPi 可保存和诊断，但不得
  当作论文影子价格。

## 3. 已完成证据矩阵

| 实验 | 关键参数/阶段 | 结果 | Solver / wall | Peak RSS | 可用于什么 |
|---|---|---|---:|---:|---|
| strict Base/744 | BCTol `1e-8`，Feas/Opt `1e-7`，NF2，Crossover2 | `OPTIMAL + PASS + 58/58` | `53,489.07 s` / `14:57:39` | 约 `20 GiB` | strict reference；仅截断时域 |
| relaxed Base/744 winner | BCTol `1e-2`，Feas/Opt `1e-5`，NF1，Crossover0 | Barrier `OPTIMAL`，263 iter，exact macro A/B PASS | `4,275.732 s` / `1:17:32` | 约 `20 GiB` | Stage A 工程 checkpoint 候选 |
| deferred Stage B/744 v3 | Feas/Opt `1e-6`，NF2，Crossover2，LPWarmStart2 | `OPTIMAL + PASS + 58/58 + manifests + macro PASS`，Barrier 0 | `2,662.606 s` / `50:52.08` | `9,644,004 KiB` | exact deferred route 严格证明；仍仅截断时域 |
| relaxed V5/744 | 同 winner，V5 | Barrier `OPTIMAL`，305 iter | `4,520.108 s` / `1:21:54` | 约 `20 GiB` | 稳健性工程证据；reservoir QC 未 strict PASS |
| relaxed Base/1488 | 同 winner long | Barrier `OPTIMAL`，143 iter，checkpoint eligible | `25,834.260 s` / `7:22:57` | `55,460,664 KiB` | 较长时域资源/检查点证据 |
| relaxed Base/2160 | 同 winner long，SoftMem80 | Presolve/ordering 后、Barrier iter 0 前 `MEM_LIMIT` | `2,800.735 s` / `1:01:40` | `72,659,300 KiB` | 固定服务器内存边界；无解/无 checkpoint |
| factor screens batch 1 | NF0/Scale auto 组合，均 5 iter | 三根均无改善，shortlist 空 | batch 约 `38:19` | `19.7--20.5 GiB` | 否决 NF0/auto-scale 盲扫 |
| factor screens batch 2 | PreSparsify2/BarOrder1/Threads32，均 5 iter | 无 material cost improvement，shortlist 空 | batch 约 `43:00` | `19.8--20.4 GiB` | 否决继续短参数盲扫 |
| cloud Base/8760 Stage A | BCTol `1e-8`，Feas/Opt `1e-6`，NF2，Crossover0，16 solver threads | 仍 RUNNING；最后已落账 iter 343 | runtime `1,012,057.571 s` | MaxRSS `362.913 GiB` | 当前唯一全年 Stage A 工程任务 |

strict Base/744 的分时为 Barrier `7,734.65 s`、Crossover/simplex cleanup `45,468.01 s`。因此当前
全年架构的主要风险不是“Barrier-only 一定不能结束”，而是：

1. 单体全年 factorization 的内存与每步成本；
2. 若直接 inline Crossover，退化 cleanup 可能远长于 Barrier；
3. 若不先保存完整内点，Crossover 失败会同时丢失昂贵的 Stage A 工程资产。

## 4. 参数筛选结论

### 4.1 保留

- `Method=2`：当前大型连续 LP 的主路径仍是 Barrier。
- `Threads=16`：current 744 配对 screen 中 Threads32 不改变 Factor 结构，observed step time 反而为
  baseline 的 `1.256668` 倍。没有证据支持为求解速度扩大到 32 threads。
- `Presolve=2`、`Aggregate=1`：当前 best known equivalent LP reduction 组合。
- `NumericFocus=1 + ScaleFlag=2`：在 relaxed Stage A 中的唯一实测总耗时 winner；它通过 current
  identity exact macro A/B，并完成 V5/744 与 Base/1488 checkpoint。该结论只适用于工程 Stage A。
- `Crossover=2 + CrossoverBasis=1 + LPWarmStart=2`：严格 Stage B 已由 fixed v3 独立续接证明；Barrier 0、
  58/58、manifests、Pi 与宏观 A/B 全通过。

### 4.2 否决或不再盲扫

- `Crossover=3`：已有 744 h 数值失稳证据，永久拒绝。
- NF0、ScaleFlag auto：Factor NZ/Ops 未改善，部分指标恶化。
- `PreSparsify=2`：Factor NZ 降 `2.40%`，但 Factor Ops 升 `7.35%`、步时升 `10.79%`。
- `BarOrder=1`：Factor NZ/Ops 不变，步时升 `10.78%`。
- `Threads=32`：结构不变，步时升 `25.67%`。
- `PreDual=1/2`、`Aggregate=0`、`Presolve=1`、`AggFill=0`：历史/current screens 没有足够结构或吞吐
  收益，不能用低价值重复运行消耗服务器时间。
- 仅继续放宽 `BarConvTol` 到 `5e-2`：在 current Base/744 没有比 `1e-2/NF1` 更快，raw quality 更弱。

结论：当前瓶颈由 LP 稀疏结构和 factorization 决定，常见 Gurobi 参数组合没有产生可重复的 material
factor-cost 降幅。后续若提出新候选，必须先给出数学机制，并在同机同 identity 5-step 配对中达到
Factor Ops/NZ 至少 `5%` 或 observed step time 至少 `10%` 的改善；否则不进入完整 744。

## 5. 资源与成本边界

### 5.1 固定服务器

- Base/1488 已使用约 `52.9 GiB` RSS 并成功；Base/2160 在 Barrier 前已达到约 `69.3 GiB` RSS，受
  `SoftMemLimit=80 GiB` 正常停止。
- 2160 的 raw LP 为 `10,398,783` variables、`12,520,914` constraints、`126,724,678` nonzeros；
  presolved 后仍为 `8,288,888 / 9,527,353 / 106,864,030`，说明固定服务器不能用作全年单体求解器。
- 不通过提高 SoftMemLimit 在 128 GiB 主机上盲目重跑 Base/2160；固定服务器后续只运行一个 solver，
  并优先完成 deferred Crossover 架构验证。

### 5.2 云端

- 当前 job 申请资源不能中途改变；保持原样直到 Stage A 自行结束或出现明确 fatal terminal。
- 最后已落账的 allocated core-hours 为 `27,076.827`，actual CPU hours 为 `4,235.784`，CPU efficiency
  `15.6436%`，说明 96 allocated cores 并未被 16-thread solver 充分使用。该事实不等于当前任务可以
  安全缩容；节点内存是主要申请约束。
- 下一次提交应先核对 ParaCloud 的“每核对应可申请内存”与计费规则，在满足 `>=600 GiB` 可用内存的
  最小合法核数上申请。若队列允许独立大内存且 16/32 cores，则优先 16 solver threads；不要只为使用
  已分配 CPU 把 solver 提到 96 threads。
- Stage A/B 均不设置 Gurobi `TimeLimit`；费用控制依赖低频轨迹审计、资源异常门禁和独立阶段授权，
  而不是让昂贵全年解在固定时限处无条件丢失。

## 6. 下一次 8760 h 推荐架构（参数已批准，实际运行须单独授权）

### 6.1 Stage A：save-first relaxed Barrier checkpoint

已正式冻结为 `barrier_checkpoint_full_year_cloud_v3`，不覆盖当前正在运行的
`barrier_checkpoint_full_year_cloud_v2`：

```json
{
  "method": 2,
  "threads": 16,
  "presolve": 2,
  "crossover": 0,
  "solution_target": 1,
  "barrier_convergence_tolerance": 0.01,
  "feasibility_tolerance": 0.00001,
  "optimality_tolerance": 0.00001,
  "markowitz_tolerance": 0.01,
  "numeric_focus": 1,
  "scale_flag": 2,
  "aggregate": 1,
  "dual_reductions": 1,
  "inf_unbd_info": 0,
  "time_limit_seconds": null,
  "soft_mem_limit_gb": 600
}
```

适用身份仅为：

```text
ENGINEERING_BARRIER_CHECKPOINT_ONLY
scientifically_accepted=false
planning_state_allowed=false
publication_shadow_prices_allowed=false
```

Stage A 返回后必须优先保存有限、完整、raw-order 的 BarX/BarPi，并记录 solver status、BarStatus、
primal/dual objectives、residuals、complementarity、Fingerprint、Gurobi version、完整 order digests、
input manifest、scenario/planning identity 和资源/时间。若没有完整有限向量或 exact identity，不能进入
Stage B。Gurobi 没有为当前 Python solve 提供可移植的任意 Barrier iteration 中途 checkpoint；因此
“save-first”指 optimize 返回后立即落盘，不应宣称能抵御节点硬故障或进程被强杀。

### 6.2 Stage B：独立 exact-LP deferred Crossover

正式 profile 为 `deferred_crossover2_full_year_cloud_v3`：

```json
{
  "method": 2,
  "threads": 16,
  "presolve": 2,
  "crossover": 2,
  "crossover_basis": 1,
  "lp_warm_start": 2,
  "solution_target": 0,
  "barrier_convergence_tolerance": 1e-8,
  "feasibility_tolerance": 1e-6,
  "optimality_tolerance": 1e-6,
  "markowitz_tolerance": 0.01,
  "numeric_focus": 2,
  "scale_flag": 2,
  "aggregate": 1,
  "dual_reductions": 1,
  "inf_unbd_info": 0,
  "time_limit_seconds": null,
  "soft_mem_limit_gb": 600
}
```

Stage B 必须重建相同科学 LP，把 source `BarX -> PStart`、`BarPi -> DStart`，并用
`LPWarmStart=2` 映射到 presolved model。solver profile 本身允许不同，但不能排除任何科学、数据、
scenario、formulation 或 planning-state manifest 行。跨 implementation bundle 只在显式授权后继续 exact
Fingerprint/dimension/order checks；不是宽松跳过 identity。

## 7. 验收与保留数据合同

### 7.1 Stage A 工程接受

Stage A 只要求证明存在可恢复的内点工程资产，而不要求 58/58 strict scientific QC：

- solver 未报告 infeasible/unbounded/numerical fatal；
- BarX/BarPi 完整、有限、size/SHA256 与 raw order 一致；
- current input manifest 和 checkpoint/recovery manifest 有效；
- objective、residual、complementarity、resource/time、stderr 全记录；
- 不生成 accepted planning state、scientific result manifest 或 publication shadow prices。

低量级方向性流、storage overlap 或水库 residual 可以保留为工程质量证据，不单独阻断 Stage B 尝试；
但它们不能被删除、隐藏或重标为 PASS。

### 7.2 Stage B 科学接受

只有同时满足以下条件，8760 h 才成为科学结果：

```text
Status=OPTIMAL
solver_solution_contract=PASS
solution_qc=PASS
hard_checks=58/58
input_manifest=current_and_valid
result_manifest=valid
Pi=complete_and_finite
planning_state=valid
wrapper_stderr_and_time=audited
```

还必须逐项覆盖冷热服务/状态、EV、wave、水电/级联水库、PHS/储能、网络、备用、惯量、容量充裕、
碳/CCS/BECCS/DAC、成本与 objective accounting scope。不得仅凭 Gurobi `OPTIMAL`、PID 退出或日志尾部
接受结果。

## 8. 当前 go/no-go

| 动作 | 当前决定 | 依据 |
|---|---|---|
| 继续 cloud job `4139552` | GO | 已投入多日计算；仍正常 RUNNING，无 fatal evidence |
| 修改/取消当前 cloud 参数 | NO-GO | 活动 solve 不可安全热替换；会丢失轨迹 |
| 当前 cloud 自动启动 Stage B | NO-GO | Stage A 尚未终态；需独立授权和 exact resume gate |
| fixed 新增 solver | NO-GO | v3 已完成且固定服务器内存边界明确，不再追加盲测 |
| 继续盲扫常规 Gurobi 参数 | NO-GO | 两批 paired screens 均无 material improvement |
| fixed 重跑 Base/2160 | NO-GO | 已在 Barrier 前触发明确内存边界 |
| `barrier_checkpoint_full_year_cloud_v3` | APPROVED / NOT LAUNCH AUTHORIZED | 744 macro、V5/744、Base/1488 与 deferred v3 已闭合；正式文件已建立 |
| `deferred_crossover2_full_year_cloud_v3` | APPROVED / NOT LAUNCH AUTHORIZED | v3 已完成 strict terminal、Pi、manifests 与 macro pair；正式文件已建立 |

## 9. 参数筛选目标之外仍待发生的外部事件

1. deferred v1/v2 的 pre-optimize 失败根永久保留；v3 已以 Barrier 0、strict `OPTIMAL + PASS + 58/58 +
   manifests + Pi + macro pair` 完成架构闭合。该项不再未决，但 744 h 仍不得重标为年度结果。
2. cloud `4139552` Stage A 需要最终 Barrier/checkpoint/resource terminal 审计；在此之前不能给出实际全年
   Stage A 总耗时或终态质量。该任务继续运行，不阻断“为下一次全年求解形成可靠参数决策”目标闭合。
3. 正式 v3 profiles 已完成 fixed Gurobi focused `14/14` 与 full `212/212`；该工程项已闭合，但不覆盖
   当前 v2，也不授权启动任务。
4. 任何下一次付费提交前，仍须结合 ParaCloud 当时有效的资源计费/核内存绑定规则，冻结最小合法 CPU
   与 `>=600 GiB` 内存；当前没有新任务授权，故不得把易变计费规则猜测写入 profile。
5. 服务器验证后的最终状态已同步到 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；
   implementation `0363b7b`、documentation `5fc60ef` 已双推送，该项已闭合。

## 10. 原目标逐项完成审计

| 原目标要求 | 权威证据 | 判定 |
|---|---|---|
| 不停止当前 cloud/8760 Stage A | round 41：job `4139552` RUNNING/Barrier 343；无 cancel/reparameterize/Stage B，ledger 42 records | 已满足 |
| 固定服务器设计并运行多轮宽松 744 h | relaxed Base/744、V5/744、两批 paired factor screens；每根均记录 identity、参数、wall/RSS/rc | 已满足 |
| 执行更长时域并确定资源边界 | Base/1488 Barrier OPTIMAL/checkpoint eligible；Base/2160 在 iter 0 前 MEM_LIMIT，形成 128 GiB 主机边界 | 已满足 |
| 筛出显著提速且宏观稳定路线 | relaxed Stage A + exact deferred Stage B：solver/wall `6,938.338 s/2:08:24.08`，相对 strict `7.71×/6.99×`；strict/macro pair PASS | 已满足 |
| 记录解质量和全国宏观账目 | Stage B `OPTIMAL + PASS + 58/58 + manifests + finite Pi`；objective/capacity/carbon/cost/generation/operation A/B 全闭合 | 已满足 |
| 冻结后续全年工程方案 | Stage A/B v3 正式 profiles、模型规范与 go/no-go 表；明确工程 checkpoint 与科学 basic result 边界 | 已满足 |
| 验证代码并保存 Git/运行证据 | fixed Gurobi focused `14/14`、full `212/212`；implementation `0363b7b`、docs `5fc60ef` 同步 origin/GitHub | 已满足 |

因此本参数筛选与全年决策目标完成；这不把任何 744/1488 截断根重标为年度科学结果，也不声称当前
cloud 已终态。后续只剩外部 job 的低频终态审计及任何新付费提交前的实时资源规则复核。

## 2026-10-05 数值稳健性 A：24h 容量门槛未通过（不代表 744h 已否决）

隔离验证 `numerics.hydro_capacity_headroom_zero_gw=1e-6`、`retrofit_upper_zero_gw=1e-6`，A3 续接截断独立只做代码/测试、实际配对关闭。2040/start2880/24h 的 A1/A2 on/off 均 OPTIMAL/QC PASS，目标相对差 1.6290758e-12；物理 LP 仅 67 个审计容量界变化，A/RHS/LB/目标/行方向精确一致；24h MPS 的 0<range<1e-6 全变量数为 0。

但输出 `thermal_new_gw[13,8]`、`thermal_new_gw[13,9]`、`thermal_retrofit_to_ccs_gw[13,4]` 在未清零位置发生路径重分配，最大 0.00016583682648540254 GW，大于 1e-6 GW。按任务书“容量输出差异仅限被清零站点且不超过阈值”的固定门槛，**否决这一当前阈值组合直接进入情景建模入口**，全部开关保持默认关闭。该判断限于规定的 24h 容量门槛；不能表述为 744h 稳健性已否决、全年最优容量必然改变，或永久否定该技术。

固定机 744h A/B/C 验证仍在运行，英国19:24 A off 尚无终态；B/C 暂无通过/否决结论。最终全套测试因本机蓝屏中断，不伪记已通过。完整证据与剩余行动：`supplementary_materials/reviews/numerical_robustness_20261005/REVIEW_ZH.md`、`A_24h_capacity_physical_lp_diff.json`、`A_capacity_decision_gate.json`。

2026-10-05 英国19:37追加测试更正：前述蓝屏中断记录保留。作者授权恢复后，最终冻结源码已由根代理在本机独占串行完成 `python -m unittest discover -s tests -q`：411 tests / 110.818s / OK (skipped=1，Windows不适用Linux /proc) / rc0，source_unchanged=true。日志SHA `f2335935e2e62579f0bcbded12c3e5efbb2898bf0cfed4c59fe78133f517ea1b`。这仅补齐代码回归，不改变A的24h容量门槛否决，也不提前判定尚未完成的744h配对。

2026-10-05 英国19:54追加入口及最终回归证据：B诊断profile的 `direct_nonbasic_scientific_acceptance` 改为false，数值参数仍仅增加BarHomogeneous=1；实际runner A/C 1h build-only审计与B参数入口fixture通过。A的物理白名单改由逐站清理审计独立导出，B/C没有A审计不能豁免界差；四组既有LP重新分析通过，原LP/解未改动。最终源码完整回归 **412 tests / 112.906s / OK (skipped=1) / rc0**，source_unchanged=true；日志 `supplementary_materials/reviews/validation_coordination_20261005/unittest_verified_20261005T185140Z.log`，SHA `bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79`。之前184739Z调用漏设CISPO_WAVE_ROOT的环境失败保留。A当前阈值晋级否决不变；B/C仍等待固定机744h终态，不能把这次代码回归写成稳健性通过。

2026-10-05 英国22:26追加 A 的744h终态观察：off/on均OPTIMAL但物理QC均HARD_FAIL，轮数157→162（+3.1847%），PInf/DInf/Compl两侧均无单步>=10倍回升。on的163条轨迹0..162连续无重复，Runtime/Work不倒退，无残差0后转正。观测结果不满足“轮数不增加且无跳升，或轮数至少减少10%”的固定稳健性晋级规则，故**当前A1/A2阈值组合不晋级**，先前24h容量门槛否决独立保留。目标相对差8.402902688862481e-6仅报告为Cross0/1e-4终态数值差，不能直接解释成物理LP不等价或精确最优解改变。两侧10项参数回读相同、input_manifest远端SHA相同；但取证期间SSH转发握手失联，on的完整config/Factor原log/time console尚未取齐，不能宣称身份和成本证据全部闭合。部分快照 `supplementary_materials/reviews/numerical_robustness_20261005/server_evidence/20261005T2126Z/` 明列31文件已验SHA、1个0字节partial、24个未取，原件与SHA保留远端；后续补证不覆盖本记录。最后确认B_off744由原suite正常运行，不因网络失联推断远端终止，不重启或重提。

## 2026-10-06 BarHomogeneous=1：744h隔离配对否决

固定机2030/start2880/744h、12线程、Cross0/1e-4/NF2/Seed0，同输入manifest（字节相同）和有效配置，唯一数值差为BarHomogeneous默认−1→1。两侧OPTIMAL，但均物理QC HARD_FAIL；Barrier轮数142→265（+86.62%），runtime5105.36632514→11978.51019621秒（+134.63%），第2轮起平均相邻回调耗时33.41600906→43.88992734秒。Presolved rows/cols/nnz、Dense6627、Factor NZ8.416e8/Ops5.354e12完全相同。两侧完整轨迹均无>=10倍PInf/DInf/Compl跳升、无残差0后转正、无重复或Runtime/Work倒退。因此未满足“轮数不增且无跳升，或轮数减少至少10%”固定晋级规则，**否决当前BarHomogeneous=1候选**，默认配置保持不变。

目标相对差3.9733594749168745e-5只作为Cross0/1e-4终态数值差，不直接解释为物理LP或精确最优解改变。off的QC失败为双向流与水库续接；on另外出现功率平衡、水库能量/库容、碳检查失败。不得把本次744h时间差外推全年倍率。原日志、参数、配置、输入身份、逐轮CSV/JSONL、QC/time均在 `supplementary_materials/reviews/numerical_robustness_20261005/server_evidence/20261006T1549Z/`，97个必要文件逐SHA全通过，归档SHA `85a63afdb8633c4a9f8a295de913f729350192be05a0348f8627c60f297fd178`。

同次补证关闭了前述A的partial缺口：A完整配置仅指定A阈值差、全部输入manifest相同、Factor NZ8.601e8→8.259e8/Ops5.588e12→5.140e12，每轮仅改善1.78%，不改变157→162轮及24h容量门槛否决。C尚未最终判定：默认presolve将分段合回，已按原授权启动唯一AggFill5双侧五轮重试及随后默认AggFill−1的Cfull744工程等价性求解；不提前授予2160h资格，不增加云作业。

## 2026-10-06 C年度分段：AggFill=5后仍未保留，否决当前2160h晋级

默认AggFill−1的744h五轮配对中分段被presolve合回；按任务书唯一一次双侧AggFill=5重试也已自然完成（两侧status7/BarIterCount5/无解）。off/on同为Presolved3243048行、3064635列、35878945非零，Dense6675、Factor NZ8.385e8、Factor Ops5.495e12，均完全相同。两侧输入manifest字节相同、实参相同、配置仅C formulation不同；第2–5轮平均回调间隔29.23256129/28.57763875秒，约2.24%时间差不补足结构存续门槛。因此**否决当前block_hours=730的C分段进入2160h+晋级**；不追加第二次参数重试、不外推全年。

41个必要证据文件SHA全通过，目录 `supplementary_materials/reviews/numerical_robustness_20261005/server_evidence/20261006T1626Z/`，归档SHA `e800c89ef6b6a95c3648056c1816518882c6250f8e2240c4d359d4191fa4e4e4`。此判定限于结构晋级，**不表示744h完整目标等价性已完成**。已授权的C_on744_full由原补验队列在16:19:12UTC正常启动（solver670416），gate可用107711418368字节、其他solver为空，仍继续运行。实际构建配置与B_off744仅C formulation不同、输入manifest字节同、gate源码SHA无变化；终态还需比对实际参数、QC和目标差<=1e-7。已恢复转发/跟进，前日PAUSED仅为中断历史；不重启旧suite，不停止在跑solver。

2026-10-06英国22:14追加C终态：Cfull已OPTIMAL/134轮/Runtime4848.09546709s/Work7694.50628128/目标2313584.6588953873，QC HARD_FAIL；参考Boff为142轮/目标2313582.8385150842，相对差7.868230489839585e-7 > 1e-7，目标门槛亦未通过。终态配置仅C formulation差、输入manifest字节同、10项实参数相同，C启动至终态源SHA一致；Boff原gate没有同期源SHA，源身份仅有冻结包/修复早于B启动日志/后验manifest链，明确保留此局限，不造同期证明。两侧无>=10倍跳升/零后转正，结构/Dense/Factor同，QC失败均水库续接和省际双向流。该Cross0数值目标差不是数学不等价证明，也不能用轮数减少覆盖结构与等价性门槛；当前C否决不变。14份终态原件逐SHA通过，详见`numerical_robustness_20261005/server_evidence/20261006T2114Z/final_comparison.json`及REVIEW5.5。授权验证收尾，用户取消自动监听，保持PAUSED；不启动2160h或科学情景。
