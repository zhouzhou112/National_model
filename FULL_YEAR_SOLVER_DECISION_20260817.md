# CISPO 8760 h 求解参数与分阶段执行决策（2026-08-17）

## 1. 文档状态

```text
decision_status=PROVISIONAL_PENDING_DEFERRED_CROSSOVER_744_TERMINAL
current_cloud_job=4139552
current_cloud_action=KEEP_RUNNING_UNCHANGED
fixed_validation=deferred_crossover2_744_validation_v0817_v3_ACTIVE
scientific_result_available=false
```

本文件汇总当前模型 identity 下已经完成的 strict/relaxed 744 h、V5/744 h、Base/1488 h、
Base/2160 h、两批 5-iteration factor screens 和正在运行的 cloud/8760 h Stage A 证据。它用于冻结
下一次全年运行的工程方案，不把任何截断时域结果解释为年度科学结果。只有固定服务器 744 h deferred
Stage B 通过严格终态和宏观配对审计后，第 6 节的未来 A/B 路线才能由 provisional 升级为 approved。

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
| relaxed V5/744 | 同 winner，V5 | Barrier `OPTIMAL`，305 iter | `4,520.108 s` / `1:21:54` | 约 `20 GiB` | 稳健性工程证据；reservoir QC 未 strict PASS |
| relaxed Base/1488 | 同 winner long | Barrier `OPTIMAL`，143 iter，checkpoint eligible | `25,834.260 s` / `7:22:57` | `55,460,664 KiB` | 较长时域资源/检查点证据 |
| relaxed Base/2160 | 同 winner long，SoftMem80 | Presolve/ordering 后、Barrier iter 0 前 `MEM_LIMIT` | `2,800.735 s` / `1:01:40` | `72,659,300 KiB` | 固定服务器内存边界；无解/无 checkpoint |
| factor screens batch 1 | NF0/Scale auto 组合，均 5 iter | 三根均无改善，shortlist 空 | batch 约 `38:19` | `19.7--20.5 GiB` | 否决 NF0/auto-scale 盲扫 |
| factor screens batch 2 | PreSparsify2/BarOrder1/Threads32，均 5 iter | 无 material cost improvement，shortlist 空 | batch 约 `43:00` | `19.8--20.4 GiB` | 否决继续短参数盲扫 |
| cloud Base/8760 Stage A | BCTol `1e-8`，Feas/Opt `1e-6`，NF2，Crossover0，16 solver threads | 仍 RUNNING；最后已落账 iter 340 | runtime `1,002,807.627 s` | MaxRSS `362.913 GiB` | 当前唯一全年 Stage A 工程任务 |

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
- `Crossover=2 + CrossoverBasis=1 + LPWarmStart=2`：严格 Stage B 候选，需由当前 fixed 独立续接验证
  最终证明。

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
- 最后已落账的 allocated core-hours 为 `26,657.947`，actual CPU hours 为 `4,169.626`，CPU efficiency
  `15.6412%`，说明 96 allocated cores 并未被 16-thread solver 充分使用。该事实不等于当前任务可以
  安全缩容；节点内存是主要申请约束。
- 下一次提交应先核对 ParaCloud 的“每核对应可申请内存”与计费规则，在满足 `>=600 GiB` 可用内存的
  最小合法核数上申请。若队列允许独立大内存且 16/32 cores，则优先 16 solver threads；不要只为使用
  已分配 CPU 把 solver 提到 96 threads。
- Stage A/B 均不设置 Gurobi `TimeLimit`；费用控制依赖低频轨迹审计、资源异常门禁和独立阶段授权，
  而不是让昂贵全年解在固定时限处无条件丢失。

## 6. 下一次 8760 h 推荐架构（条件性）

### 6.1 Stage A：save-first relaxed Barrier checkpoint

建议新增/冻结为一个新的 profile 版本，不覆盖当前正在运行的
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
| fixed 并发第二 solver | NO-GO | v3 已启动，checkout 冻结且只允许此唯一验证 |
| 继续盲扫常规 Gurobi 参数 | NO-GO | 两批 paired screens 均无 material improvement |
| fixed 重跑 Base/2160 | NO-GO | 已在 Barrier 前触发明确内存边界 |
| future relaxed Stage A profile | CONDITIONAL GO | 744 macro、V5/744、Base/1488 已支持；待 deferred Stage B terminal |
| future Stage B profile | CONDITIONAL GO | v3 已证明 direct primal/dual Crossover；待 fixed 744 strict terminal + macro pair |

## 9. 尚待闭合

1. fixed v1 已在 optimize 前因未消费 RAW_GRFR root 的环境登记差异 fail-closed；窄修复仅允许两端
   manifest usage 都为 0 的该可选根不同。v2 随后又在 build 前因 memory gate 遗留的已删除常量引用
   异常退出；没有 LP/Gurobi/数值结果。`018607c` 已修复并覆盖所有 cloud profile versions。v1/v2 roots
   永久保留。server regression `212/212 PASS` 后，全新 v3 已于 17:53:13 启动；仍须证明
   `LPWarmStart=2` 已于 Gurobi 日志证明生效且未重跑 Barrier；当前处于 simplex cleanup，仍待完成严格
   `OPTIMAL + PASS + 58/58 + manifests + macro pair`。
2. cloud `4139552` Stage A 需要最终 Barrier/checkpoint/resource terminal 审计；在此之前不能给出实际全年
   Stage A 总耗时或终态质量。
3. 仅在第 1 项通过后，新增 future relaxed Stage A 的正式 profile/runner tests；不覆盖当前 v2。
4. 结合 ParaCloud 最新资源计费/核内存绑定规则，冻结下一次申请的最小合法 CPU 与 `>=600 GiB` 内存。
5. 将最终批准状态同步到 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，记录精确
   Git、commands、outputs、SHA256、验证和下一步。
