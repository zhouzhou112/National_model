# 三个 V5 情景正式启动前审查：不求解验证

记录日期：2026-09-06；验证主要发生于 2026-09-05 23:39–23:51 +08:00。
实现提交：`b225ab522a3bd7a38ea5ef1318beb4c161cdd8db`，父提交 `a09aee7`。

**结论：本轮修复了保全、续接和启动门禁，但正式全年无 Crossover 数值资格仍未闭合。不得启动优化。**
没有修改冷热/EV 物理方程、签约上限、参与比例上限、效率、成本、时间尺度或 Base 供给侧。
case1=Base+冷热，case2=Base+EV，case3=Base+冷热+EV；原始需求已经包含这些负荷，不能重复添加。

## 1. Base 一致性证据

只读核验 T32 job `4479238` 的冻结 release：
`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260903_8760_stagea_final_2820fc3_v3`。
23:44 的作业状态仍为 RUNNING，elapsed `2-06:20:27`，节点 `m4cg1605`。这是当时快照，不是未来状态保证。

- 11 个供给建模/数据/水电/年度连接缩放等核心文件与运行 release 的 SHA256 一致，包括
  `monolithic.py`、`master.py`、`data.py`、`hydro.py`、`load_center.py`。
- 使用与运行作业相同的默认 Base 入口解析配置，科学设置差异为零；保留 `coefficient_zero_tolerance`
  的比较，不把它当作可忽略的求解器参数。三个情景相对 Base 的差异仅限情景说明与柔性模块及其开关。
- 显式 `base.json` 与默认入口有一处描述文字差异。第一次审查如实标为 REVIEW_REQUIRED，确认该来源后
  改用运行作业实际使用的默认入口比较；没有改配置来掩盖差异。
- 云端已有原 LP 身份 PASS：50,907,234 行、41,458,383 变量、492,835,195 非零元，指纹 `0x94cf2e50`，
  原 MPS 解压 SHA256 `8216816027025ffc16eb7fb80ce55d6beb822242f03f1a24433102248603713a`。
- 共同输入清单 76 项中 74 项字节哈希相同。不同项仅为 `output_manifest.csv` 与 `smoke_test_report.json`。
  后者解析后的 JSON 完全相同；前者是整个数据包清单，本地多 186 项、云端独有 1 项；两清单的共同
  76 项中 75 项哈希相同，剩下一项正是上述格式不同的 smoke report。未发现共同运行数值输入变更。
- 三份既有全国 24h basic 结果的原始总负荷数组逐元素相同，原结果 manifest 全部有效。

边界：这不是新构建的全国 8760h 矩阵逐系数比较；CF Zarr 清单仅覆盖元数据，没有重新扫描全量 chunk。
完整的来源/差异记录见 `evidence/base_identity_audit.json`、`recorded_input_comparison.csv` 和
`evidence_summary.json`。审查脚本内 PASS 表示模型源码/配置比较，不是正式求解资格。

## 2. 实际修复

| 问题 | 最小修复 | 对模型的影响 |
|---|---|---|
| 压缩冷热状态离线导出仍可能读取活跃模型的 `X` | `offline_solution.py` 为 `SparseThermalStateView` 递归绑定保存向量 | 不改 LP；中断后可独立重建小时状态 |
| 无限变量边界使原单位残差报告无法写严格 JSON | 无界端点写 null，同时写 unbounded 标志 | 不改边界或残差阈值 |
| 单年 `--state-in` 可缺少跨情景检查 | 单年和 sequence 入口要求源情景 ID、配置 SHA256；生产入口同时复用严格科学接受条件 | 拒绝串用 Base/冷热/EV/联合容量路径及未接受结果 |
| 候选全年 profile 未通过资格但存在可调用入口 | profile 和其他 profile 下的 portfolio 8760h 启动均拦截，云端 wrapper 同步加拦截 | 保留 preflight/build-only/离线恢复；不改 Base 启动合同 |
| 新 EV 数组缺少物理单位与维度字典 | 六个字段补齐 province/province,hour 和 GW/GWh/资格池份额 | 不改值、不改既有字段名 |
| V2G 对流统计可能混入 V1G-only 池充电 | V2G 同池对流使用 `ev_v2g_pool_charge` | 修正诊断口径，不增加/删除物理约束 |

`PlanningState.load` 新参数均有默认值，保留旧诊断 API；生产 runner 明确传入检查条件。
源结果的 manifest、年份、QC、Barrier checkpoint 校验继续保留。`candidate_unaccepted` 的显式诊断通道
仍存在，但不能用于自动科学接受。年度柔性签约目前属于每年重选的服务，不是跨年充电桩/车队资产队列；
V2G 基础设施成本仍按原有年化服务代理计费。本轮没有擅自引入资产继承或免收后续年成本。

## 3. 本轮验证及真实残差

24 项不求解测试 PASS。新增测试显式封锁 `optimize`、`optimizeAsync`、`presolve`、`feasRelax`、
`feasRelaxS`；其余回归为配置、结果完整性和 sequence dry-run 测试。Python 编译、Git whitespace、
通过 SSH 执行的 `bash -n` 纯语法检查均 PASS；没有运行云端作业或任何优化调用。

使用既有 `output/portfolio_20260905/system24_case3_nonbasic` 保存的 Barrier 向量，以新代码重新构建
全国 24h LP，仅比较指纹/顺序并代入向量：353,514 变量、225,811 行，精确 LP/向量身份通过。
容量、成本、运行结果和输出字典完成离线导出，路径：
`output/portfolio_prelaunch_20260905/offline_case3_final/`。

- 保存向量逐行重算检出 415 条超过 1e-5 的约束，全部属于水库约束。
- 最大残差 `0.04265177930528807`，位于 `reservoir_independent_hourly_transition[348,15]`，为模型
  水量单位 million m3，**不是 GW**。其中独立水库小时行 338 条、独立周期首小时行 12 条，其余为级联行。
- 原始边界最大违规 `6.64e-12`，没有超过边界容差的变量。
- 冷热/EV optional portfolio 检查最大值 `8.88e-16`；这是该保存向量的结果，不证明所有非零服务工况。
- 重放柔性数组与历史导出最大差值 `2.84e-14`，保持同一物理结果；新元数据明确 GW/GWh。
- 整体 QC 仍 HARD_FAIL、科学接受仍 false，没有把“成功保全”误当成“成功优化”。

以前完成的非零签约服务块测试和三组 basic 求解证据保留在相邻 `portfolio_20260905` 目录，本轮没有重跑。
尤其不能把独立服务块全年通过等同全国供给系统全年通过。

### 水库残差的进一步离线定位

从保存的物理调度数组独立重算 482 个独立水库，复现 350 个超限小时，恰好对应原 LP 的 338 条普通小时行
和 12 条周期首小时行。最大残差行中的 `[348,15]` 是“独立子集第 348 行、去掉首小时后的第 15 列”，
正确映射为全体水库 `reservoir_local_index=475`、模型 hour index=16，`HydroCHN_01147` 耿达水电站。
不能直接把它解读为全表第 348 座水库或模型小时 15。

该站 24h 来水总量 `9,776.165 m3`，最大残差小时库存 `1.482789663e9 m3`、库存上限 `2.965618074e9 m3`；
当小时来水为零、排水近零，但库存仍变化约 `42,651.779 m3`。该误差是整个所选时段来水的 4.36 倍。
这是“大自由周期库存、小小时通量”的直接数值诊断，尚不能证明它是唯一求解失败原因，也不能把误差视为
无害的浮点舍入而接受结果。逐站表和摘要见 `evidence/independent_reservoir_residual_scales.csv` 与
`water_scale_diagnostic.json`，由不导入 Gurobi 的 `scripts/analyze_portfolio_water_residuals.py` 生成。

可进一步审查固定仿射坐标变换 `x=z+c`：必须同步变换全部上下界、RHS、目标常数和导出映射，才能保持
同一物理 LP。此法不需要新增二进制变量；是否改善 Barrier 要另行验证。本轮未实施变换，没有固定初始
库存为零，也没有放宽容差。未来任何候选仍须保持与运行 Base 的可比性，不能只给三个新情景更宽的模型。

## 4. 正式启动前仍需完成的事项

1. **水库数值问题，当前首要阻塞。** 先在保存模型/向量中检查零来水、近零库存边界、周期行和单位尺度的
   关联，再提出数学等价的行/列处理候选。必须证明不扩大可行域、原单位残差阈值不变。当前 Base 同样有
   非 basic 短时段失败证据，不能靠改柔性假设解决，不能热改正在运行的 Base。
2. **四情景配对验收。** 后续获得重新求解授权后，先固定输入、小时、资源和验收规则，在本地完成 Base、
   冷热、EV、联合的非 basic 配对测试，包含冬季、夏季和非零签约见证。现有短时段 basic 通过是参考，
   不是正式 nonbasic 资格。若需要修改 Base 数学表达，必须新建共同 benchmark 并重新审查四情景可比性。
3. **跨年与服务边界。** 2030/2040/2050/2060 逐年校验输入和签约上限，使用各自同情景的已接受状态；
   不能用 Base 2030 的投资路径无说明地衔接灵活性情景 2040。签约服务年费与持久资产的区别必须写清。
4. **正式规模与完整保全。** 通过前述数值资格后，新不可变 release 必须归档实际原 MPS、代码/输入/参数
   和输出 manifest；再验证受控中断保存与正常终态导出。原始向量不能替代求解器内部 Barrier 因子状态，
   不承诺从中断迭代原地热续算。硬杀/OOM 前未写出的向量也无法保证恢复。
5. **云预算。** 现有 Base 的构建、Presolve、Ordering 已很昂贵，4h 云端测试上限不能被理解为足以完成
   全国全年。当前不启动任何优化；后续即使数值资格通过，也不能自行扩大云端预算或自动启动 Stage B。

本轮新增拦截只存在于本地新提交；旧云端 `20260905_v5_portfolios_87b534f_v1` 未覆盖、未重提作业。
它仍未取得正式资格，不应继续作为启动入口。正在运行的 T32 Base 未改文件、参数、信号或控制目录。

## 5. 不求解复现入口

PowerShell 本地运行，使用现有独立 Gurobi 13.0.2 Python 包；不需要调用优化：

```powershell
$env:PYTHONPATH=(Join-Path (Get-Location) 'output/portfolio_runtime_gurobi13')+';'+(Join-Path (Get-Location) 'tests')
& 'C:/Users/ZZ/.conda/envs/RL/python.exe' -m unittest test_portfolio_no_solve test_planning_sequence test_run_contract -v
$env:CISPO_WAVE_ROOT=(Resolve-Path '../wave_energy').Path
& 'C:/Users/ZZ/.conda/envs/RL/python.exe' scripts/audit_portfolio_saved_result.py --source output/portfolio_20260905/system24_case3_nonbasic --output-dir output/NEW_OFFLINE_REPLAY
```

`NEW_OFFLINE_REPLAY` 必须是不存在的新目录。该脚本拒绝超过 168h 的来源，不允许指纹不匹配降级。
只读 Base 比较使用 `scripts/audit_portfolio_base_readonly.py --help` 中的参数；远端仅读取文件和 `squeue`。
所有失败历史和原始结果保持原状；本轮未删除原始数据，未运行 IIS/修复性松弛或优化器实验。
