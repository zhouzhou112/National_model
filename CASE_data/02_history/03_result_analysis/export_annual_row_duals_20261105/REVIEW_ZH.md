# 年度核算行对偶标准导出验证（2026-11-05）

## 范围与改动

依据作者 2026-11-05 决定和 `../claude_workspace/tasks/TASK_export_annual_row_duals_20261105.md` 执行。基线 Git 为 `9bbff99`；改动仅供今后新冻结 release 使用，未访问或修改任何云端运行包，未对已解生产案例重解或重导出。

- `cispo_model/load_center.py`：只保存原有 `addConstr` 返回句柄，表达式、创建顺序、变量、目标及求解参数均不变。
- `cispo_model/solution_export.py`：新增 `export_annual_row_duals`，复用当前生产选择的 `BarPi`/`Pi`；新增 `annual_row_duals.csv`，十列与 T4 完全一致，按原模型行索引排序。覆盖五类省级年度行各 31 行、城市年度能量平衡 337 行、省内年度容量 642 行，共 1134 行。保留原始 RHS 导数的符号，`row_sense` 使用 MPS 的 E/L/G，单位为 million CNY/GWh。
- `dual_export_status.json`：新增成功标记和完整负荷侧价格公式；实际系数为 0.05、0.05、3.5，来源为 `model_config_snapshot.json:resolved_configuration.security`，并记录惯量 legacy 参数优先、否则 reference × tolerance 的实际键名和规则。
- `cispo_model/io_contract.py`：登记新文件用途及 `pi_million_cny_per_gwh` 单位；只给新文件增加字典记录，不改变旧字段的推断结果。`cispo_full_lp_model_spec.md` 增补导出说明。
- `tests/test_annual_row_duals.py`：新增 31 省小型 LP 测试，覆盖 217 行、列序、单位、原始 BarPi 索引、负号保留、配对残差 <1e-8、完整性拒绝与字典单位。

所选七类行在当前代码中均采用物理 GWh 坐标。年度二进制行缩放只作用于另行登记的 VRE/ROR 容量链接行；`annual_dense_split` 增加块定义行，但不缩放这里的外层年度账户 RHS，因此这里的原始 BarPi 无需再乘除缩放因子。未使用“无负价”作为验收判据。

## 验证证据

最终证据在 `verification_v3_final/verification.json`；同版 Gurobi 的完整前后构建在 `verification_v2_gurobi13/verification.json`，最终版复用同一建模源码的构建证据并重新构建 24h 模型验证一致。运行版本为本机 Python 3.10.14 / Gurobi 13.0.2；求解器安装到独立 `.codex_tmp/annual_export_gurobi13_20261105`，未更改原 RL 环境。

| 工程窗口 | 列数 | 行数 | 非零数 | 前后 Fingerprint | 结果 |
|---|---:|---:|---:|---:|---|
| 1h | 239109 | 80896 | 455184 | 692580241 | 完全一致 |
| 24h | 353638 | 226051 | 1766991 | -1060391456 | 完全一致 |

验证使用 case3 2030 的真实输入和全部候选点，不改变科学配置；全年 CF 仍用于既有接入设计，没有使用 max-CF=1 的快捷构建。只对新 24h 工程窗求解：Barrier、Crossover=0、SolutionTarget=1、BarConvTol=1e-4、NumericFocus=2、Aggregate=0、8 线程；71 轮 OPTIMAL，61.433 s。该窗口不产生全国全年科学结论，不作为生产采纳。

1. 同一精确求解向量分别调用旧、新导出器，固定时间戳仅用于消除文件字节比较中的时间差。除 `dual_export_status.json` 新字段外，23 个既有运行导出逐字节一致，包含 `hourly_marginal_prices.csv.gz`。只新增 `annual_row_duals.csv`。
2. 使用 T4 的原始行名匹配逻辑独立遍历同一原模型的行序与 BarPi，对照全部 1134 行，索引及行名完全相同；CSV 浮点往返后的最大绝对差为 **3.552713678800501e-15 million CNY/GWh**。
3. 31 省年度注入行与需求行对偶之和的最大绝对残差为 **0.1596239653776953 CNY/MWh**。这是 24h / BarConvTol=1e-4 的实测量，不能与 case3 2030 全年 0.00064 CNY/MWh 混称，也没有据此另设生产价格接受门槛。
4. `verification_v3_final/provenance/input_manifest.csv` 记录 86 项输入及各自完整性方式、SHA、大小、路径；与前一次 Gurobi 13 验证的输入清单完全一致。配置、情景、求解 profile 的原文件 SHA 及实际派生 8 线程配置另见同目录 `model_config_snapshot.json`。随机种子沿用 Gurobi 默认 0。
5. 最终 Gurobi 13 全套回归 **505 项，504 通过、1 项按既定 Windows 平台跳过**，206.473 s，零失败/错误；跳过项为 Linux `/proc` 进程集成测试。日志 `regression_gurobi13.log`；新增测试包含在本次全套中。源码 AST 编译与 `git diff --check` 通过。小型可提交证据见 `verification_receipt.json`，含最终源码、验证 JSON、输入清单、年度 CSV、公式状态及回归日志的 SHA256。

## 运行方式

在工程根目录，以已配置的 RL Python 执行；`CISPO_WAVE_ROOT` 指向已有 `../wave_energy`，`PYTHONPATH` 在本轮隔离验证时加入上述 Gurobi 13 目录。生产部署仍使用其已冻结的环境。

```powershell
python supplementary_materials/reviews/export_annual_row_duals_20261105/verify_export.py --output <NEW_DIRECTORY>
python supplementary_materials/reviews/export_annual_row_duals_20261105/record_provenance.py <NEW_DIRECTORY>/verification.json
python -m unittest discover -s tests -v
```

`verify_export.py` 拒绝覆盖已存在目录，只构建 1h/24h，保留基线源码、解日志、前后导出与逐项核验；可用 `--reuse-fingerprints` 引用已验证同建模源码、同版本、同配置的指纹证据，再重新构建 24h 检查导出元数据改动。未使用后台监听。

## 保留的失败与限制

- `verification_v1`：首次诊断脚本未调用求解参数配置器，实际为默认求解路径，导致新导出 Pi 与独立读取 BarPi 不同；该次只保留其原始证据，不用于同 BarPi 验收。已修正脚本，v2/v3 明确读取并核验 Method=2、Crossover=0、SolutionTarget=1、Aggregate=0、8 线程。
- `regression.log`：首次本机 Gurobi 12 回归 505 项，有两项环境错误（并行构建期间可用内存低于既有 8 GiB 门禁、测试要求 Gurobi≥13），另有一项既定 Windows 平台跳过。未放宽门禁或修改既有测试；释放构建进程后改用隔离 Gurobi 13 串行重跑。
- 本轮完成的是导出与工程身份验证，不改变任何既有全年结果的严格 QC、relative_v1 或作者采纳状态。运行中的 5294579、5318408 仍应走离线 T4。

源码和小证据可按明确清单提交；`verification_*` 下的逐时数组、基线源码副本、完整环境转储及本地 Gurobi 包留在本机，不加入 Git。
