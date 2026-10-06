# 当前 Base 修复应用与矩阵指数复核

核验时刻：2026-09-15 23:25:50 CST。Git 基准：`0a03cc452e95d158f36923ceb5210267979b6234`，保留既有 dirty 工作区。本轮仅只读服务器、保存核验证据及更新交接文档；未修改模型、输入、求解参数或作业。

## 结论

当前 Base `4614693` 已应用最终保留的数值修复，未发现漏部署。截图中的 `1.607e8` 是正指数的最大/最小非零系数之比，不是 `1e-8` 的系数。当前原始矩阵最小非零系数为 `3.7e-5`；日志中的 `4.12e-08` 是第 98 轮对偶残差。

运行目录：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3`，输出目录为其下 `output_8760`。核验时队列为 `RUNNING 1-13:04:55 64CPU 750G m4cm1708`。

## 部署与运行证据

- `verification.json`：冻结发布清单的 203 个云端文件全部 SHA256 匹配，本地对应的 198 个文件也全部匹配。
- `evidence/input_manifest.csv`：实际读取的是 `data_overlay/hydro/repaired_storage_audit_20260913_v2/hydro_stations.csv`，重新计算的文件 SHA 与运行时记录一致，完整 SHA 为 `f8135eaffa2de77461912cba5216106f66e0b6207c8b6c381fd725339a378e94`。
- 三站有效库容修正：锦屏二级 `4.96 GL`、白竹洲 `3.84 GL`、克孜尔 `339.9 GL`；原始字段与历史数据保留。修正表 SHA 为 `5244572958c2c357b7f09e81a50858d2be484e977b85bafdf85091a390538341`。
- `evidence/model_config_snapshot.json` 的 `resolved_configuration` 与 `evidence/build_report.json`、实际参数回读共同确认下表。配置文件存在、发布成功和实际加载分别核对，未仅凭文件名判断。

| 最终保留的修改 | 实际运行值/证据 |
|---|---|
| 水库库存界收紧 | `reduce_cyclic_inventory_range=true` |
| 独立水库弃水界收紧及正上界下限 | `limit_independent_spill_to_inflow=true`，`independent_spill_positive_bound_floor_m3s=1.0` |
| 风光容量因子毛刺 | `coefficient_zero_tolerance=0.01`，这是适用输入的筛选阈值，不是全部矩阵系数的删除阈值 |
| 小容量/扩建余量毛刺 | `capacity_floor_zero_gw=capacity_headroom_zero_gw=1e-5`，即 10 kW |
| 小入流/梯级传输毛刺 | `local_inflow_cleanup_m3s=0.01`，`cascade_transfer_cleanup_fraction=1e-4` |
| 省内负荷中心输电正则 | `load_center_network.flow_regularization_yuan_per_mwh=1.0` |
| 2030 DAC 关闭，后续年份可用 | 当前 `features.dac=false`；年份表 2030 为 false，2040/2050/2060 为 true |
| 撤销年度行除以 8192 的缩放 | 实际 VRE/ROR 行均 `physical_v1 / exponent=0 / row_scale=1` |
| 最终求解参数 | `Threads=48, NumericFocus=2, BarConvTol=1e-4, Crossover=0, SolutionTarget=1` |
| 其他实际参数/限制 | `Method=2, ScaleFlag=2, Presolve=2, Aggregate=1`；Time/Mem/SoftMem/Work 均无有限上限 |

“全部应用”指最终保留版本；历史中撤回的 CO₂ 单位试验、Crossover=2 和更紧容差并非当前生产设置。此前局部 Cross2 的 QC 通过不能代替当前 Cross0 的全年验收。

## 极值、跨度及极小数来源

`build_report.json` 的原始矩阵统计与 Gurobi 日志的四舍五入值一致：

| 指标 | 实际值 |
|---|---:|
| 最小非零矩阵系数 | `3.699999999999999e-5` |
| 最大非零矩阵系数 | `5945.8478236198425` |
| 最大/最小比值 | `160698589.82756335 = 1.606985898e8` |
| 原始 Gurobi Matrix range | `[4e-05, 6e+03]` |
| 目标系数范围 | `[0.001, 3853.189875762917]` |
| RHS 非零绝对值范围 | `[1.0186e-5, 1139999.9999996377]` |

最小值可由实际加载的排放表和代码直接复算：2030 燃气排放因子 `0.00037 MtCO₂/GWh`，CCS 捕集比例 `0.9`，剩余排放系数 `0.00037*(1-0.9)=3.699999999999999e-5 MtCO₂/GWh`，与原始矩阵最小值完全一致。它对应 `0.037 tCO₂/MWh` 的物理排放，不能作为无意义小数值毛刺删除。来源为 `data/technology/emission_factors_by_year.csv` 与 `cispo_model/monolithic.py` 的 `annual_emissions_accounting` 构造；排放表本地 SHA 与实际输入清单一致：`6c1002b18c623901483397e2ef405eb51cb61577c6e92b62d206ed7fa943dec9`。

最大值与实际 ROR 年度电量—容量关系的行注册表最大值完全一致，约为 `5945.85 h` 的全年等效利用小时数。这个全年系数不能与 168 h 短窗中的年度行系数上限混为一谈。

日志最后一行：

```text
                  Objective                Residual
Iter       Primal          Dual         Primal    Dual     Compl     Time
  98   3.97983246e+08 -4.17162235e+09  4.70e+02 4.12e-08  6.14e+01 130133s
```

其中 `4.12e-08` 位于 Dual residual 列，是求解误差指标。它小不代表其他指标也达标：原始残差仍为 470，互补性指标 61.4，原对偶目标差仍很大，尚未收敛。

本次日志仅有一组原始 `Coefficient statistics`，没有单独报告预处理后矩阵系数范围。本次没有额外构建完整 presolved 模型，因此结论不扩展为所有内部变换矩阵中均不存在 `1e-8`。

## 改善幅度与未解决项

相对旧 Base 约 `6.247e9`，当前极值比缩小约 38.9 倍，即对数跨度减少约 1.59 个数量级，仍有约 8.21 个数量级。不是 38.9 倍加速，也不是问题已经消除的证明。Gurobi 官方将小于 `1e9` 作为粗略范围参考，理想上低于 `1e6`；范围本身不能取代实际收敛与质量检验。[官方说明](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/modelissues.html)

下一步若继续诊断，应区分具体约束族、单位与真正的输入毛刺，结合长程残差和最终 QC 判断；不要为降低展示的极值比而盲删排放系数或恢复未经验证的行缩放。此核验不触发作业重启、改参、自动监控或新的全年构建，也不承诺 9–10 天收敛。

## 复现与文件

- 远程只读检查脚本：`remote_verify.py`，通过 `ssh paracloud-bscc-a8 python3 -` 接收脚本，读取文件并调用队列查询；不启动 Gurobi。它嵌入冻结清单，输出核验 JSON 和运行证据，重新执行应另存新目录，保留当前快照。
- 完整逐文件比较、库容输入实际路径和散列、日志摘录：`verification.json`。
- 原始证据：`evidence/build_report.json`、`model_config_snapshot.json`、`solver_parameters_before_optimize.json`、`input_manifest.csv`、`run_identity.json`、`gurobi.log`。
- 本轮日志快照 SHA256：`b781293c31ac9c6edde341209194b5356d70fee177adf084c90a0dedac97d6ca`。
- 检查方式：203/198 文件散列比较、实际输入清单与库容文件复核、配置与参数回读、范围算术及日志列核对。未修改可执行代码，未新增求解测试。
