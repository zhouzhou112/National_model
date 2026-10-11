# 柔性参数落地复核（2026-10-11）

执行依据：作者已确认的 `claude_workspace/tasks/TASK_flex_parameter_implementation_20261011.md` 第 1–6 节与 `claude_workspace/reports/柔性参数定案方案_20261011.md`。本轮不重新选择参数。不访问云端、不操作 4844528、不更新生产冻结包、不读取或复制凭据。

**交付状态：落地、419 项回归、24h 构建/小解、零签约对照及两项单因素/2060 价格代理复核均完成。新中央冷热签约 5.54 GW 未达到任务书预期的 10–20 GW，作为明确差异保留，不改变作者数值。**

Git 起点：`3100bb325b691d8d398c680dcfd879b80f8f4026`，工作分支 `codex/validation-pair-20261005`。最终提交以本报告所在提交及收尾 Git 记录为准。已有 `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md` 改动及其他稿件不属于本次提交。

实现提交为 `cad25a5`，已推送 GitHub 工作分支。最终 24h 的 implementation source-bundle SHA 与该提交后的当前源码一致；三个合格新成本价格试验的模块/脚本与输入 SHA 均与最终工作区一致，见 `validation_provenance.json`。开发阶段输出中记录的旧 Git HEAD 不代表旧加载源码，必须同时使用原始文件 SHA。

## 1. 落地范围与版本身份

| 身份 | 基线 | 参数、参与率 | 容量信用 |
|---|---|---|---|
| `case3_thermal_ev_v5` | V9 | 资源成本、2030–2060 年度路径 | 作者授权的四小时峰窗折减信用 |
| `case3_thermal_ev_v5_nocredit` | V9 | 同新中央情景 | 无 |
| `case3_thermal_ev_v5_compensation_basis` | V9 | 旧补偿成本、固定参与率、旧上限 | 无 |
| `config/scenarios/legacy/case3_thermal_ev_v5.json` | 原历史基线 | 原文件字节保留 | 原历史行为 |

这里 **V5 是柔性物理模型代际，case3 是冷热+EV 资源组合，V9 是系统基线配置代际**。三者不是同一串版本号。两个新身份在目录中为 SENSITIVITY，未改变 case3 的 publication_status。

改动文件分组：

- 参数：`config/flexible_load_v5_{central_parameters,parameter_registry,source_registry,source_count_qa}.csv`；新增 12 个年份列和两行方向激活参数，标量列等于 2030。原表保存在 `config/legacy/`。
- 构建与校验：`scripts/build_flexible_load_v5_inputs.py`、`scripts/validate_flexible_load_v5_inputs.py`。确定性 CSV/GZip 重建冷热包络、EV 池、年度成本与 manifest；年度路径单调性、非负性、成本新列、源文件 SHA 检查通过。
- 模型：`cispo_model/{config,data,flexible_load,flexible_response,flexible_credit,monolithic,master,solution_export,result_summary,io_contract}.py`。只调整参数解析、成本、信用、输出及零上限消元，不改 S50–S54 的物理等式。
- 情景、目录及合同：三份 case3、`scenario_catalog.json`、`release_contract_v1005_catalog_audit.json`、`FLEXIBLE_PORTFOLIOS_V5_CONTRACT.md`。suite 支持各情景声明的基线，显式传错基线仍拒绝。
- 测试与工具：新增可选池信用测试，扩展年度参数测试；原行为测试明确使用 legacy 身份。新增版本控制内 `scripts/price_taker_enrollment.py`；工作区外同名 Claude 脚本保留为入口包装器，原稿备份在本目录 `before/`，未把外部工作区整体提交。

## 2. 输入、变量与计费

空间为 31 省，时间步长 1 h，完整输入为 8760 h/年；重建覆盖 2025、2030、2040、2050、2060。作者只给四个规划年，2025 兼容输入复用 2030 参数。功率 GW、能量 GWh，费用为 2025 年不变价，目标单位 million CNY。

冷热从既有 ±1 °C 物理包络出发，乘各年供暖/制冷参与率；EV 从不可变充电基线构造可参与池、逐时充放功率和服务库存。参与率是可进入模型的资源池上限，年度签约 K、V1G 的 alpha 与 V2G 的 beta 仍为优化决策。EV 的 `rho=f_v2g/f_v1g`，beta 受嵌套条件约束。没有将低、中、高三套潜力同时并入负荷。

新输入位于 `data/flexibility/participation_pathway_v2/`。原 `data/flexibility/*v5*`、Base 负荷和 ±1 °C 包络保持不变。独立生成 `data/load/flexible_load_envelope_v3_cool2c.csv.gz` 及其 manifest，未纳入中央情景 manifest。输入完整 SHA 见 `input_file_hashes.json`；新 manifest 的小文件副本为 `new_flexible_load_v5.manifest.json`。

冷热激活成本为 `1e-3 * sum(release_cost * down + precondition_cost * up)`。释放成本为 40/40/30/30 CNY/MWh，预处理为零。签约成本按年度 K 收费，V1G 按向下搬移电量计一次，V2G 保留作者指定的可用、设施、车主及退化四项费用。两个方向明细之和等于原激活汇总项，标为 `DIAGNOSTIC_DETAIL_NOT_ADDITIVE`，不重复进入目标。

新列缺失时两方向回退旧激活值，并在启用方向合同的构建审计中记录 `legacy_bidirectional_activation=true`；开关关闭则使用原目标表达式，保留旧输出结构。

预处理方向零激活费只取消这项附加服务费用；预冷/预热增加的电耗仍进入有效负荷及供给侧成本（价格接受者中为购电成本），不代表用电免费。

## 3. 信用与零签约

开启条件同时要求可选服务池、`firm_flexibility_derated_v1` 和授权值 `author_2026_10_11_derated_credit_v1`。每省取不可变全年负荷峰所在四小时窗，沿用历史窗口定位规则。对折减 d，信用分别满足：

- 冷热：`F <= d * availability_window * K`，且 `F <= d * min(down_envelope_window)`。
- V1G：`F <= d*K` 且 `F <= d*alpha*min(eligible_baseline_window)`。
- V2G：`F <= d*K`、`F <= d*beta*min(D_window)/rho`、`F <= d*beta*min(Q_window)/4`。

零 K/alpha/beta 不产生信用；QC 增加 `firm_credit_bound_violation_gw` 与 `firm_credit_zero_when_unenrolled`。没有增加备用信用。信用与负荷平衡仍由既有 monolithic 装配进入系统；master 保留供给侧充裕度记账。

## 4. 测试、短窗与兼容性

最终完整回归：`python -m unittest discover -s tests -q`，**419 tests / 215.470 s / OK (skipped=1)**。唯一跳过项为 Windows 不具备 Linux `/proc` 的测试，见 `unittest_verified.log`。输入校验为 PASS，见 `input_validation_final.json`。

24h 构建通过。新情景使用任务指定 `portfolio_local_gate_v1` 本机小解通过；最终输出为 `solve24_verified/`。它是截短时间窗诊断，年度固定成本不缩放，不作全年投资结论。中间一次 `solve24_final/` 因并行诊断占用内存，被 8 GiB 门禁在建模前拒绝；没有绕过门禁，原日志保留。

零 enrollment 上限版本在 `zero_enrollment_scenario.json`，结果 `zero24_retry/` 对照 `base24/`。两侧 QC PASS；新信用、K、alpha、beta 均严格为零。目标值为 2122268.556483912 与 2122268.556483888 million CNY，相对差约 1.1e-14；有效负荷最大差 5.68e-14 GW，为分量求和的浮点舍入，不能称数组逐字节相同。物理与经济零签约退回成立。初次零上限构建发现无控制量却创建零 UB 保留状态的边界错误，修为构建前消去由零签约已强制为零的控制，不修改物理约束。

原 case3 的 24h 合成 fixture MPS 与原解向量分别逐字节/逐值相同；原 Base、V9 与 legacy case3 有效配置相同。证据在 `compatibility_and_fingerprints.json`、`zero_base_comparison.json`。这项 MPS 比较是服务块 fixture，不能冒称全国全年矩阵比较。

| 科学配置 SHA256 | 修订前 | 修订后 |
|---|---|---|
| 原 Base | `e18a7bcb…6465b9fd22acf0` | 不变 |
| V9 Base | `937c3c6f…184315b0d4f0` | 不变 |
| legacy case3 | `731452f6…19dbe4f65` | 不变 |
| 新 case3 2030 | 原 case3 为上述 legacy SHA | `324d98cc7f4154e21fdcfcdb48768016c53ad59ffd9a7d513286e04c8a9739a1` |

完整年度指纹、两个敏感性指纹均在 JSON 中。新 case3 指纹变化来自 V9 父基线、年度路径、方向成本、独立输入位置和授权信用，不能与 legacy 混用。

## 5. 价格接受者与单因素归因

输入电价固定为 `claude_workspace/evidence/base2030_prices/hourly_marginal_prices.csv.gz`，31省 × 8760 h；不做归一化。优化目标为外生电价下有效负荷购电费用加服务成本。没有供给侧投资、价格反馈或容量信用收益，均为 `TEST_ONLY_PRICE_TAKER`。2060 使用 2030 价格仅检验年度池路径，不能外推 2060 收益。

完整原始报告/省级表的小文件副本在 `price_taker_reports/`，汇总为 `price_taker_comparison.csv`。alpha 上限影子价单位为 million CNY/单位 alpha，不能当作 CNY/kW；调用率使用实际搬移量除参考池电量，以及释放量除 K×8760。

数值复核中，初次新中央 Barrier 返回 OPTIMAL，但冷热原约束残差高达 7.22 GWh；只改成本试验残差 0.0649 GWh。保存状态后确认 `ConstrVio` 与重建复核一致，属于求解器返回向量的原单位不可行，不能归咎于库存重建或据 OPTIMAL 标记接受。进一步 NF2/1e-10 超时，ScaleFlag=0 数值失败，均保留报告。独立单阶段本地单纯形复核同一个服务块，不运行生产 Stage B，不修改参数或 S50–S54。

关闭该本机试验的 Presolve（保留 Barrier、Crossover=0、BarConvTol=1e-8、ScaleFlag=2、NumericFocus=1）后，同一 LP 的新中央解通过：84 轮、154.813 s，最大物理残差 8.13e-9，ConstrVio=0，BoundVio=2.58e-14。无需生产 Stage B 或物理模型变更。直接单纯形辅助诊断尚未完成时，因上述合格证据已经取得而停止；只停止本任务自己的本机进程，记录在 `simplex_cancelled.json`。**不能把初试 OPTIMAL 当作通过 QC，也不能据本轮推断所有生产模型都应关闭 Presolve。**

新中央 2030：供暖 2.652256 GW、制冷 2.886334 GW（合计 **5.538590 GW**）；V1G 21.782594 GW，31省 alpha=0.999999999975–0.999999999999958；V2G 2.95e-8 GW（数值零）。实际 V1G 搬移 28,946.922 GWh，占参考池 73,583.020 GWh 的 39.339%。31省 alpha 上限的工程对偶均为正，所选对偶解的扩张价值合计 860.495 million CNY/单位 alpha。退化 LP 的对偶分配并不唯一，初试和合格解的这个数值不同；只作为资源池约束诊断，不作稳定的扩容报价。

重建后的 2030 冷热可签约上界按各省小时包络最大值合计 13.460502 GW（供暖 3.235294、制冷 10.225208），见 `thermal_reference_pool_caps.csv`。**13.46 GW 是技术/参与池上界，不是经济最优签约**；实际供暖约签 82%、制冷约签 28%。因此任务书“冷热签约 10–20 GW”的预期未实现，不调参数凑量级。V1G 满签且上限对偶为正，支持资源池约束仍在起作用；冷热低年调用率还受季节时序、价差、年度费用和库存义务共同影响，本试验没有逐一分离这些因素。

2030 合格结果如下（所有近零量均按数值零展示，原数值保存在 JSON）：

| 对照 | 冷热签约 GW | V1G GW / alpha | V2G GW | 节省 million CNY | 最大物理残差 |
|---|---:|---:|---:|---:|---:|
| 旧补偿口径 | 0 | 0 / 0 | 0 | 0 | 1.59e-11 |
| 只改成本、旧参与率 | 5.538590 | 16.336946 / 1 | 0 | 1666.058 | 3.31e-9 |
| 只改参与率、旧成本 | 0 | 0 / 0 | 0 | 0 | 2.84e-14 |
| 新成本+新参与率 | 5.538590 | 21.782594 / 1 | 0 | 2115.141 | 8.13e-9 |

只改成本时 V1G 搬移占参考池仍为 39.339%，alpha 上限工程对偶合计 852.693 million CNY/单位 alpha。单因素结果表明：**旧口径的主要进入门槛是成本；只扩大池并不能使旧成本下的资源进入。成本门槛解除后，新参与率使 V1G 签约由 16.34 增至 21.78 GW，约增加 33.3%，节省比成本单因素多 449.082 million CNY。** 这是给定 Base 价格下的机制诊断，不能等同于内生电价的系统规划收益。冷热的2030参与率未变，所以两组新成本试验的冷热签约相同。

2060 输入、2030 价格代理：供暖 **9.772982 GW**、制冷 **9.231947 GW**、V1G **191.142105 GW**、V2G **9.67e-8 GW**（数值零）；alpha 约为 1，V1G 搬移占参考池 **41.148%**。求解 160.791 s，最大物理残差 1.78e-8，ConstrVio=0，local_diagnostic_passed=true；所选 alpha 上限对偶合计 13,727.099 million CNY/单位 alpha。年度路径生效，但不能把 21,824.563 million CNY 的代理价格节省作为 2060 系统预测。

原口径与参与率单因素使用原数值设置并通过物理 QC；新中央、成本单因素、2060 最终采用显式 `--presolve 0`。差别是求解数值设置，实际比较的数学模型仍严格按上述单因素定义。初试失败、超时和中止记录均保留，没有挑掉失败日志。

## 6. 差异与未闭合项

原注册表实际为 31 行而非任务书所述 32 行；新增两行后为 33 行、20 列，没有为凑行数制造参数。

1. 任务指向 master 中的四条上界，但当前代码实际在 flexible_load 创建服务信用，由 monolithic 装配。新增 `flexible_credit.py` 复用此实际接口，未在 master 重复创建信用。
2. 定案表使用 `derated_peak_service_v1` 字样；代码合法枚举是任务明确指定的 `firm_flexibility_derated_v1`，因此采用后者。
3. 为满足旧数据字节不变，新 manifest 放在独立年度路径目录，未覆盖任务示例中的原 manifest。无新参数行的构建调用仍默认原目录；新情景明确引用新目录。
4. full_year CLI 有显式旧默认基线，因此实际本机命令增加 `--config config/optimization_numeric_dac_by_year_v9.json`。配置 API 与 sensitivity suite 在调用者未指定基线时支持 scenario 的 `base_config`；显式基线不会被偷偷替换。
5. 三类 evidence_status 单列无法表达 V1G“2030 政策锚、远期文献”的混合性质，保留 POLICY_ANCHOR 并在模型用途/来源说明年度差别。17 个来源 ID 已补录；作者 bibliography 的 VERIFY 项继续标记待核，不声称本轮重新核验政策网页。source_count QA 沿用按注册 ID 的计数方法，不等于重新去重的独立文献系统综述。
6. `ev.v2g_owner_compensation_cost` 名称和数值严格保留作者决定；“资源成本、无转移支付”的经济解释仍需论文明确区分用户不便与补偿支付，未据此改值。
7. 只开容量信用的单因素收益必须留给 Base-frozen，价格接受者不能回答；本轮未启动该任务。低/高参数列和独立 +2 °C 包络已可复现，但未把它们冒称已跑完的全国情景。
8. 旧输出不变的证据范围为原输入 SHA、有效科学配置与 24h 服务 fixture；含运行时间/路径的所有结果文件不可能跨运行逐字节相同。零签约全国 24h 对照的浮点舍入差已明确披露。

## 7. 复现入口

在 National_model 根目录使用既有 RL Python 和本地 Gurobi 13 runtime。PowerShell 环境：

```powershell
$env:PYTHONPATH='output/portfolio_runtime_gurobi13;tests'
$env:CISPO_WAVE_ROOT='../wave_energy'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PYTHONIOENCODING='utf-8'
# python 指向已有 RL 环境；不读取或复制其许可证。
python scripts/build_flexible_load_v5_inputs.py
python scripts/validate_flexible_load_v5_inputs.py --scenario-config config/scenarios/case3_thermal_ev_v5.json --output <new-review-dir>/input_validation.json
python -m unittest discover -s tests -q
python scripts/run_cispo_2030_full_year.py --config config/optimization_numeric_dac_by_year_v9.json --scenario-config config/scenarios/case3_thermal_ev_v5.json --solver-config config/solver_profiles/portfolio_local_gate_v1.json --planning-year 2030 --diagnostic-hours 24 --output-dir <new-24h-dir>
python ../claude_workspace/scripts/price_taker_enrollment.py --prices ../claude_workspace/evidence/base2030_prices/hourly_marginal_prices.csv.gz --year 2030 --cost-set current --presolve 0 --time-limit 600 --output <new-price-dir>
```

构建专用门禁追加 `--build-only`；单因素追加 `--single-factor cost_only` 或 `participation_only`；旧口径用 `--case case3_thermal_ev_v5_compensation_basis`；2060 用 `--year 2060 --price-year 2030`。诊断数值设置逐次记录在报告或命令日志；不覆盖已有输出目录。大数组、MPS 和输入数据留本地，Git 只保存源码、参数、合同、报告和小型判定证据。
