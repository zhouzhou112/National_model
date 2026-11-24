# B2040/2050/2060 最小静态闭合与门禁停止报告

2026-10-27；执行基准 Git `eb161d8cb3dd558796884683f79af1365261ed79`。本报告对应作者当日“Base 值加最小静态闭合”授权。三年未提交或 release，48 线程生产配置保留。

## 结论

三年的 1h 静态闭合及来源完整性均通过。B2060 的全部 1h/24h、年度参数、目标、双向交叉可行和成本分项门禁通过。B2040、B2050 在 24h Base 对照中仍不可行，IIS 指向短窗碳预算与 CHP/RUC/惯量等约束组合；不是允许触发 spur/trunk 窄区间重试的同类逐时网络残差。因此停止这两年的后续身份求解，也不单独提交 B2060，遵守“三年全过后同时提交”的条件。

原 Base 解、原冻结审计、旧失败模型与本轮全部输出保留。5207165、5294579 未作任何修改；只读队列核对两项仍为 RUNNING。本轮未建立监听或启动重复备份。

## 逐年调整与成本

| 年份 | 调整行数 | spur 增量 MW | trunk 增量 MW | 非 CCS bio 减量 W | 年固定成本增量 CNY/yr |
|---|---:|---:|---:|---:|---:|
| 2040 | 12 | 0.000688727 | 2.799298869 | 9.162058 | 61,596.505660 |
| 2050 | 13 | 0.001524569 | 0.179619420 | 2.293526 | 3,954.901821 |
| 2060 | 43 | 0.007008199 | 0.147646982 | 5.957564 | 3,543.065116 |

成本采用原模型目标系数折算为年度 2025 CNY，包含 bio 总容量随新建量下调而减少的固定运维成本；不是运行成本或全年最优目标变化。精确数值见 `closure_summary.csv`，逐行记录见 `<year>/derived_static/closure_audit.csv` 与 `closure.json`。原冻结 clipping 与本次授权闭合分别审计，原 clipping 门槛未变。

`derived_integrity.json` 确认三年分别仅改变 12/13/43 个授权投资列的固定上下界，原 MPS 其他分段（含目标、系数、RHS）不变；原冻结审计逐字节相同，源证据 SHA 不变。CCS、储能、省际通道及其余发电冻结值不动。

## 24h 停止证据

| 年份 | 原短窗碳上限 Mt | IIS 子模型最小排放 Mt | 网络上界各增 1 MW 后的保守排放下界 Mt |
|---|---:|---:|---:|
| 2040 | 3.561643836 | 6.234302872 | 6.234302545 |
| 2050 | -0.273972603 | 0.353699641 | 0.353698348 |

两项 IIS 均独立重放为 INFEASIBLE。诊断只在另建的 IIS 子模型中移除碳上限、最小化同一排放表达式，以得到原问题所需排放的下界；没有修改门禁模型、容差或源文件。最后一列用最小化模型的上界对偶构造保守下界，没有实际修改网络界。即使额外给予每条相关网络上界 1 MW，仍明显超过碳上限，因此网络窄区间不能解决这两项冲突。该下界是 IIS 子模型证据，不是全年排放预测或完整模型调度解。

原短窗把全年碳预算按 24/8760 缩放，冬季首日同时受 CHP/RUC/惯量等约束。IIS 支持上述约束组合冲突，不能据此断言全年不可行。2040 IIS SHA 与闭合前相同，进一步说明原静态网络修正未消除这个独立阻塞。权威诊断为 `2040/iis_diagnosis_v2/diagnosis.json` 和 `2050/iis_diagnosis_v2/diagnosis.json`；更早诊断版本保留。

**下一步需作者与决策层明确短窗年度碳预算的门禁处理规则。** 当前授权只允许静态闭合及特定网络残差回退，不能据此放宽碳约束。批准新规则后，另建目录重跑受影响门禁，再核对三年同时提交条件；本轮不提交、不 release。

## B2060 完整门禁

使用 `2060/attempt_2/`：1h 静态矛盾为零；Base 对照、零签约、开放柔性三个 24h 均 OPTIMAL、relative_v1 PASS、保全 COMPLETE，分别 72 次迭代，求解约 29.303/28.227/30.241 秒。

Base 与零签约目标相对差为 0；双向交叉约束最大违反 `4.001776687800884e-11`，最大界违反 `1.2732925824820995e-11`，均低于 `1e-8`。所有成本分项满足 `1e-7` 相对门槛。年度参数、冻结来源、原 clipping、固定投资界和仅授权改变均通过。最终依据为 `FINAL_GATES_PASSED.json` 与 `revised_identity_20261026/assessment.json`。

旧交叉检查助手输出中的 `interpretation` 固定文案仍提到已被作者废止的逐时逐变量一致性；该文案不作判据。本轮按修订身份门禁读取数值，由上述 assessment 明确判 PASS。不以退化 LP 逐变量不同否决，不将 24h 结果外推全年。

## 实现、验证和复现

- 新增 `cispo_model/frozen_closure.py`，仅显式 `--frozen-capacity-closure` 启用，验证来源 manifest、年份、行 SHA、允许列族、精确缺口和原投资界，再按行闭合；默认行为不变。
- runner 接入新开关；`frozen_capacity.py` 将原 clipping 与闭合分别计入容量来源核验。三个门禁助手保留原判据，仅增加显式闭合参数和未压缩 MPS 兼容读取。
- 新测试覆盖精确缺口、CCS/储能不动、完整成本、原审计不变，以及篡改来源/年份/行/数量和重复目标拒绝。冻结相关 19 项通过；完整串行回归 **492 项 OK，1 项平台跳过**，139.012 秒，日志 `regression_serial.log`。
- 首次并发回归和 B2060 首次构建遇到本机可用内存不足 8 GiB 的原有保护；失败保留，未降低保护。停止并发后在新 attempt_2 完成 B2060，串行完整回归通过。

运行环境为 `C:/Users/ZZ/.conda/envs/RL/python.exe`，`PYTHONPATH=.codex_tmp/gurobipy_13_recovery_validation`，Gurobi 13；`CISPO_WAVE_ROOT` 指向既有 wave_energy 数据，OMP/OPENBLAS/MKL 线程为 1。代码入口：

```text
python supplementary_materials/reviews/base_frozen_closure_20261027/prepare_closures.py
python supplementary_materials/reviews/base_frozen_closure_20261027/run_year_gates.py 2040
python supplementary_materials/reviews/base_frozen_closure_20261027/run_year_gates.py 2050
python supplementary_materials/reviews/base_frozen_closure_20261027/run_year_gates.py 2060 --attempt 2
python supplementary_materials/reviews/base_frozen_closure_20261027/audit_derived_models.py
python -m unittest discover -s tests -q
```

上述命令是本轮执行记录，复现应使用新输出目录，不能覆盖现有运行。具体每组命令/profile、参数、源 SHA 与结果见相应目录。MPS/IIS、向量和完整模型输出保留本地，Git 只同步已审查源码、命令、摘要与小文件审计；不把 Git 同步误作运行环境部署。
