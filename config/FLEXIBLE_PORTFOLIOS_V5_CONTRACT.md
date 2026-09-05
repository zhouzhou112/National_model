# Base 与三组 V5 灵活性情景：签约、运行和验收合同

版本：`optional_service_pools_v1`，2026-09-05。作者已明确：冷热、EV、冷热+EV 是三个互相支撑的基础情景。
本文件定义新增、显式选择的研究方案；不替换旧 `flex_integrated_v5_central.json`，不热修改正在运行的 Base。

## 1. 四组共同边界

| 身份 | 冷热调节 | V1G / V2G 签约 | 原始需求 | 容量充裕度 |
|---|---|---|---|---|
| `base` | 关闭 | 关闭 | 同一分解负荷 | Base 原始全年峰值 |
| `case1_thermal_v5` | 开启 | 关闭 | 同 Base | 同 Base |
| `case2_ev_v5` | 关闭 | 开启、内生选择 | 同 Base | 同 Base |
| `case3_thermal_ev_v5` | 开启 | 开启、内生选择 | 同 Base | 同 Base |

Base 已含冷热、EV 用电，新增的是**调节和签约决策**，不再次叠加这些需求。保留 31 省、0.25°候选点、
连续 8760 h、连续 LP、原供给/水电/输电/碳/RUC/备用/惯量和年度成本合同。
负荷恒等式为 `L = residual + heating_actual + cooling_actual + EV_actual - EV_discharge`。
GW 为功率，GWh 为库存和逐小时电量，步长 1 h。目标函数以百万 2025 年不变人民币计。

主比较不使用旧 V5 静态 firm credit，`security.capacity_margin_load_basis=baseline_peak_v1`。
原因：静态峰窗功率与库存上界尚不能证明给定运行状态下的持续交付；本轮不把未经检验的容量替代收益计入主结论。
这是显式研究口径变化，不是对旧 V5 的等价重写。未来事件交付/ELCC 应作为独立验证合同。

## 2. 冷热签约及状态

沿用经过 manifest 校验的 V5 小时增减载包络、可用系数 `a_t`、效率、留存率和持续时长。
每省、每类服务有年度签约功率 `K >= 0`，小时增载 `u_t >= 0`、减载 `d_t >= 0` 和非负服务库存 `E_t`：

```
0 <= u_t <= U_t;  0 <= d_t <= D_t
u_t + d_t <= a_t K
E_t = r E_(t-1) + eta_c u_t - d_t/eta_d
0 <= E_t <= H K
heating/cooling_actual_t = immutable_component_t + u_t - d_t
```

首小时与区间最后一小时周期连接。关闭某类服务时包络、签约均为零，不创建其小时控制或库存变量。
共用 `u+d` 功率约束避免同一签约容量在两个方向各使用一遍；不同用户同时增减载仍是聚合 LP 的可能行为，
不能解释为每台空调同时制冷和制热。没有添加二进制互斥变量。

冷热库存是相对于基准用电的等效服务库存，**不是室内温度模型**。V5 的非负库存只允许先预热/预冷再释放，
不允许先欠舒适度后补偿；负库存时长字段为历史兼容输入，并未激活。存储损耗可使全年用电增加，不能额外
强加日能量守恒消除这些损耗。原 `+/-1 C` 包络与经验留存率/时长不是逐建筑 RC 参数的实证校准。

零控制时段沿用精确状态消元与衰减锚点，不删全年季节连续性、不换典型日；保留转移系数下限约 0.1 的审计。

## 3. EV：可选签约与两个不互借库存的服务群体

原始 EV 用电 `B_t` 保持不变。V5 输入的可参与参考负荷是 `b_t=f B_t`，中心 `f=0.15`。
`P_t, D_t, Q_t, W_t` 分别是原 V5 的充电功率、放电功率、服务库存和补能义务输入。
这些是由原负荷重建的服务参数；`connected_vehicle_fraction=1` 是归一化可用系数，**不是实测全天插枪率**；
`W_t=eta_c b_t` 也不是实测车辆行程链，departure 下限零不等于真实车辆可空电量出行。

新增每省两个无量纲年度决策：

```
0 <= alpha <= 1                        # 签约智能充电 / 全部可参与服务
0 <= beta <= rho alpha; rho = 0.10/0.15 # V2G / 同一个全部可参与服务
K_smart = max_full_year(P_t) alpha
K_v2g   = max_full_year(D_t) beta/rho
K_v2g <= K_smart; sum_p K_v2g <= national_cap(year)
```

31 省 V2G 上限继续使用 2030/2040/2050/2060 年的 10/20/30/40 GW。
`alpha-beta` 为仅 V1G 群体，`beta` 为 V2G 群体；使用同质比例抽样假设，最大 V2G 比例随已签约 V1G 比例缩放。
该比例是假设，不是新观测。固定全年功率归一化，避免截断窗口改变同一个签约比例的含义。

对仅 V1G 群体：

```
0 <= c1_t <= (alpha-beta) P_t
0 <= s1_t <= (alpha-beta) Q_t
s1_t = r_EV s1_(t-1) + eta_c c1_t - (alpha-beta) W_t
```

对 V2G 群体：

```
c2_t + d_t <= beta P_t; 0 <= d_t <= beta D_t/rho
0 <= s2_t <= beta Q_t
s2_t = r_EV s2_(t-1) + eta_c c2_t - d_t/eta_d - beta W_t
```

两群体各自周期连接、各自满足按份额缩放的出发库存下限。不能把 V1G 群体库存转给 V2G。
关闭 EV 时不建以上小时变量，`alpha=beta=0`。

```
EV_actual_t = B_t - alpha b_t + c1_t + c2_t   # 放电前的表计充电需求
R_t >= alpha b_t - c1_t - c2_t; R_t >= 0    # 付费单次下移电量
```

零签约使所有运行决策/服务成本为零且严格退回 Base。对原中心 `r_EV=1`，全年两池合计满足：
`net_EV_energy_change = (1/(eta_c eta_d)-1) * discharged_energy`。
V2G 自耗损失非零或截断输入不满足逐小时参考闭合时，必须使用完整状态式核验，不能沿用简化恒等式。

目前重建 `W_t` 与参考充电曲线同形，因此本模型不能研究实测早晚出行高峰或临时拔枪；这应列为数据边界，
不能凭空补造 departure SOC。可后续用有数据支持的 availability/withdrawal 情景替换，并重新校验 manifest。

## 4. 成本与输出

继续读取同一个 V5 成本文件，没有改成本数值。年度签约成本：冷热 40 CNY/kW-year；智能充电 60；
V2G 增量可用性 60，加基础设施 40。小时成本：冷热每方向 300 CNY/MWh，即增减载都计激活；
V1G 下移 300；V2G 放电计参与成本 150 和损耗外的电池退化 400。电能损失由电源侧成本内生支付。
同一 V2G 服务承担其所属智能充电的共同控制成本，以及 V2G 增量成本；不能再额外重复统计“独立 V2G 充电量”。

价格转换：`CNY/kW-year * GW = million CNY/year`；`CNY/MWh * GWh * 1e-3 = million CNY`。
激励/补贴本身是转移支付；现有数值仅可解释为真实实施成本/不便效用损失的工程代理，
不能凭地方补偿标准即认定为社会资源成本。成本、参与率、时长是必须报告的敏感性维度。

输出新增 `alpha/beta`、两池充电/库存至 `flexible_load_dispatch.npz` 及省级签约摘要；
`solution_qc.json.optional_portfolio_qc` 独立重算两池状态、份额、连接、库存、基线重建和冷热共用签约功率。
所有新增检查进入 hard checks。旧总车队字段保留为两池之和，不能据此再优化跨池能量转移。

## 5. 求解、部署与证据界限

`portfolio_local_gate_v1.json`：本地短时段 Barrier + Crossover 稳定基准，4 线程、600 秒求解时限。
`portfolio_local_nonbasic_gate_v1.json`：本地无 Crossover 诊断，保留未通过向量，不可当正式结果。
`barrier_stagea_portfolio_v1_threads44.json`：独立的全年无 Crossover 配置，沿用 Base Stage A 结构、
二进制年度连接行缩放与原单位验收，不冒用 Base LP fingerprint；配置的数值资格以本轮审查报告为准。

本地真实输入服务块显示原 `BarConvTol=1e-2` 可返回 OPTIMAL 而未通过原单位 QC，因此保留旧长链 guard，
新增配置采用 `1e-9`，不把 OPTIMAL 状态等同物理正确。全国模型还需检查供给侧水库等约束的数值行为。
24 h、168 h 及抽省全年均不代表全国全年规划结果；短时段年度成本不缩放，不能据其零签约推断全年服务无价值。

云端只允许新不可变 release；必须归档原 MPS/输入/代码/参数、保全 BarX/BarPi 并经过全部原单位 QC。
新增 `run_cloud_portfolio_job.sh` 实查 Slurm wall limit，缺失、无限时或超过 04:00:00 均拒绝；
4 h 包括构建、归档和求解。部署不启动作业。当前 Base 全年构建/Presolve/Ordering 成本已经很高，
不能期待这个 4 h 上限足以完成全国全年验证；后续是否放开预算须由作者另行决定。

## 6. 2026-09-05 正式启动前覆盖

作者最新指令为暂不启动优化。本轮只做静态/构建/保存向量回放，不执行 `optimize`、`presolve` 或松弛。
本地代码现在拒绝未通过资格验收的 portfolio Stage A profile；其他 profile 也不能绕过三个组合情景的
8760h 启动拦截。preflight、build-only 和离线恢复保留。拦截没有环境变量或命令行开关可直接解除，
后续必须以数值验收证据修订；不能因仅有模型归档指纹而将其视为已获求解资格。

后续年份直接 `--state-in` 和 sequence 入口均核验源情景 ID、情景配置 SHA256；正式接受还要求
原有结果 manifest、OPTIMAL、严格布尔 hard checks、有限 QC、科学接受状态。历史候选状态显式诊断
路径保留，但绝不自动转为生产结果。年度冷热/EV 签约是每规划年重新决策的服务量，并非可跨年传递的
车辆/充电桩资产；现有 V2G 基础设施费用是年化服务代理成本，没有新增基础设施存量队列。

冷热压缩状态的离线视图现在从归档向量读取保留节点；无限边界在残差报告中用 null + unbounded 标志
表达，避免严格 JSON 写入失败。六个新 EV 数组补齐单位/维度字典；同池双向充放统计只用 V2G 池充电，
不把 V1G-only 池的正常充电归入 V2G 池内部对流。以上均不改变原 LP 系数、边界、目标或物理可行域。

完整证据与未闭合项见 `supplementary_materials/reviews/portfolio_prelaunch_20260905/REVIEW_CN.md`。
既有云端 `87b534f` release 仍是旧冻结代码；不能将本地新增拦截误称已覆盖该 release 或正在运行的 Base。
