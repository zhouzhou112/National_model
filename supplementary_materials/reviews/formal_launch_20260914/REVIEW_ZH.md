# 2026-09-14 修复版 Base 正式启动记录

作者本轮明确授权：检查后直接启动完整 2030 Base，取消 Gurobi 求解时间上限与 Slurm 作业时限；在按 64 核计费的更宽松内存分配下尝试 48 个求解线程。本记录替代此前仅允许 900 秒/2 小时诊断的下一步，不改变现有 Thermal 作业。

## 已提交的唯一新正式作业

- Job ID：`4613045`，job name `cispo2030_base_v9_t48`。
- 2026-09-14 02:11:52 CST 提交为 held；核验后于 02:12:22 放行。
- 02:14:03 实查：`PENDING (Resources)`，`AllocTRES=(null)`；已提交且可调度，尚未构建或求解，无可信开始时间。
- Release：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v2`。
- 正式结果目录：上述 release 下 `output_8760/`；日志和启动记录位于 release 根目录。
- Thermal `4533060` 同时只读确认 `RUNNING 6-06:03:51`、64 CPU/700G；未停止、重启或修改。

## 内存与计费核验

实时 `amd_a8_768` 为 61 个节点，每节点 128 个物理核、`RealMemory=768000` MiB，即 `750GiB`。`--mem=768G` 超出调度器节点容量，`sbatch --test-only` 明确拒绝；`--mem=750G` 和 64 CPU 的组合通过。

正式 held 作业的 `ReqTRES=cpu=64,mem=750G,node=1,billing=64`，`TimeLimit=UNLIMITED`。这里确认的是 Slurm 申请/计量记录，尚无运行分配记录，也没有平台账单单价证据。启动脚本要求实际 `AllocTRES` 仍为 64 CPU/750G/billing64 才进入全国模型。内部 Gurobi Threads=48 不会把已申请的 64 核变成 48 核计量。

Slurm 记录还显示 `MinCPUsNode=125`：大内存请求对可用节点资源有额外调度要求，不能将其解读为已按 125 核计费；计费字段仍为 64。此次申请占用节点完整可配置内存，排队可能比 700G 更受限制。参考 [Slurm sbatch 内存参数](https://slurm.schedmd.com/sbatch.html) 和 [TRES 计量规则](https://slurm.schedmd.com/tres.html)。实际证据为本目录 `resource_query.json`、`memory_request_test.json`、`held_submission.json`、`release_job.json`、`startup_status_2.json`。

## 最终运行设置及本轮修改

| 设置 | 新 Base | 正在运行的 Thermal |
|---|---:|---:|
| Gurobi Threads | 48 | 44 |
| Slurm CPU / 内存 | 64 / 750GiB | 64 / 700GiB |
| Method / Crossover / SolutionTarget | 2 / 0 / 1 | 2 / 0 / 1 |
| BarConvTol | 1e-4 | 1e-4 |
| NumericFocus | 2 | 1 |
| Presolve / ScaleFlag / Aggregate | 2 / 2 / 1 | 2 / 2 / 1 |
| FeasibilityTol / OptimalityTol | 1e-6 / 1e-6 | 1e-6 / 1e-6 |
| TimeLimit / SoftMemLimit | 无限 / 无限 | 无限 / 无限 |
| Slurm TimeLimit | UNLIMITED | UNLIMITED |
| BarIterLimit | 2000000000（求解器允许的最大整数） | 1000（既有默认值） |

1. 新增 `config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json` 与 `config/cloud_resource_profiles/a8_8760_numeric_repaired_t48_m750_v1.json`。保留源 v9 中的历史本地测试预算和旧 44 线程配置，正式命令显式覆盖运行参数。
2. `scripts/run_cispo_2030_full_year.py` 增加当前修复版的独立入口资格：核验 solver profile 内容与 v9 科学配置指纹，允许当前物理年度行，不再要求旧 8192 行缩放；限制为 2030 全年、原始模型先归档、无额外预处理模型副本。保留已有结果保存与严格 QC 流程。
3. `cispo_model/diagnostics.py` 将 null TimeLimit/SoftMemLimit 显式设为无限，防止复用模型/环境继承 900 秒等旧预算。实际全国模型归档前回读参数，检查有限 TimeLimit/SoftMemLimit/MemLimit/WorkLimit 是否意外存在。没有 wrapper timeout 或自动停止/切换 Stage B。
4. 将默认 Barrier 1000 轮上限提升至最大允许整数，避免前期耗时之外再被默认轮数截断。它不是收敛保证，也不是新的接受阈值。
5. 部署脚本修复 PYTHONPATH 覆盖问题，保留既有私有 xarray 依赖目录；没有安装软件或修改共享环境。v1 在免费预检查时失败的目录、日志和包全部保留，v2 是实际提交版本。

本轮没有改变决策变量、优化目标、约束、单位、小时/空间分辨率或继续清理输入。科学配置 SHA256 仍是 `937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0`。模型仍为 2030/8760h 全国扩张与运行联合 LP，GW/GWh、MtCO2、2025 CNY，水量使用既有百万 m3 坐标并按原始 m3 验收。2030 DAC 关闭，后期年度开关保留；本次只启动 2030。

## 检查证据与可复现性

- 既有相关 69 项测试通过，新增 4 项运行配置/科学身份防漂移测试通过。第一次 unittest 包路径错误保留；随后 73 项组合运行仅因本机 Gurobi 12 与生产要求 13 的版本差异导致新增 1 项失败，修正测试作用域后新增 4 项全部通过。生产版本要求没有降低，本机测试只验证可用的参数 API，计算节点另检查 Gurobi >=13 与真实 license 小 LP。
- 本地完整输入预检查 PASS：67 PASS、3 WARN、2 INFO、0 HARD_FAIL。云端 v2 再次完整加载全年输入并预检查 PASS；66 项必需输入身份全部一致。79 个总记录中，仅两个非必需历史报告 sidecar SHA 不同，已显式记录。CF 验证使用已有 Zarr 元数据 SHA，不能冒称本轮重哈希了全部数组块。
- 本地/云端 `bash -n`、传输 archive SHA 与全部 202 个打包文件校验通过；源码 diff whitespace 检查通过。
- 包：`20260914_base_v9_t48_m750_tol1e4_v2.tar.gz`，674110 bytes，SHA256 `61c24b5283a20687e53b2b555f9cee39205bc6739252be412f37ea10662f2c2f`。
- Git 基准 `0a03cc452e95d158f36923ceb5210267979b6234`，工作树仍未提交，包含此前数值修复。本次按逐文件 SHA 冻结真实执行源，不能称为该 Git 提交的干净构建。详情 `20260914_base_v9_t48_m750_tol1e4_v2_manifest.json` 与包内 `source_identity.json`、`release_files.sha256`。
- 数据源：只读引用 `20260903_8760_stagea_final_2820fc3_v3` 的既有数据根，新建独立 `data_overlay`，复制已修复的三站库容表，不覆盖原始输入。水库表 SHA256 `f8135eaffa2de77461912cba5216106f66e0b6207c8b6c381fd725339a378e94`。

正式可复现命令（由已提交 batch 设置数据、环境和资源）：

```bash
python scripts/run_cispo_2030_full_year.py \
  --config config/optimization_numeric_dac_by_year_v9.json \
  --solver-config config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json \
  --horizon full_year --archive-original-model --allow-nonbasic-planning-state \
  --output-dir "$RELEASE_ROOT/output_8760"
```

提交/放行的原样参数分别见 `remote_submit_held.py`、`remote_release_job.py`；它们已执行，**不得再次执行以启动重复作业**。只读状态查询脚本为 `remote_status.py`，运行方式：将文件内容通过 SSH 标准输入交给云端 `python3 -`。

## 仍未验证的结论及下一步

此次已完成正式提交，尚未获得计算节点，因此不能宣称实际 48 线程进入 Barrier、全国数值错误已经消失或 9–10 天必然完成。之前完整 620×8760 水力子模型通过，与全国电力 LP 通过仍有区别。此前 24h Cross0/1e-4 解的严格 QC 失败和约 0.311MWh 水量残差折算记录继续保留，未用它们触发无条件收紧容差，也没有篡改严格验收状态。

下一次只读检查：先看 `squeue -j 4613045`、实际 AllocTRES、`compute_node_smoke.json`；随后看 `output_8760/build_report.json`、`solver_parameters_before_optimize.json`、`model_archive/archive_manifest.json`、`gurobi.log` 与 `solver_telemetry.jsonl`，确认原始/预处理矩阵、内存和 Barrier 长尾走势。没有自动监控任务，没有自动停止时刻，没有自动 Stage B 或后续年份提交。终态时必须核对保存的 X/BarX/BarPi/Pi、求解状态、原单位 QC 和可用性，不能将保存成功当成科学验收。
