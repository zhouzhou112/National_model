# 2026-09-14 启动失败定位与修复

失败原因已定位为上轮正式入口改动的遗漏：配置读取阶段已允许修复版 `physical_v1`，但 `build_full_year_monolithic()` 返回之后的第二处校验仍对所有 direct nonbasic 运行强制要求 `binary_power2_safe_8192_v1`、exponent=13。因此当前正确的物理行被错误拒绝。此前“解除旧8192绑定”的说明不完整，本条作明确更正。

## 失败事实

- 旧作业 `4613045`：2026-09-14 04:26:18–05:05:59 CST，`FAILED 1:0`，39分41秒，节点 `m4cg1602`。
- 异常：`RuntimeError: Direct nonbasic scientific acceptance requires exact VRE/ROR annual capacity-link exponent 13 runtime evidence`，旧 runner 第1546行。
- 异常发生在模型构建返回后、原始模型归档与 `optimize()` 之前。没有 `gurobi.log`、`model_archive`、`build_report.json`，不是 Barrier 的 NUMERIC 终态；无法从该失败根恢复已退出进程的内存模型，需要重建。
- 实际 `AllocTRES=billing=64,cpu=64,mem=750G,node=1`，`TimeLimit=UNLIMITED`。Gurobi13.0.2计算节点许可小LP PASS，初始可用内存732.42GiB。`/usr/bin/time`峰值RSS约57.04GiB、Swaps=0；sacct采样MaxRSS=56.00G。现有证据排除了本次因申请计费不符、许可失败、内存耗尽或时间预算触发退出的解释。
- 原release、输入、失败输出及Slurm记录全部保留；只读证据为 `failure_status.json`、`failed_phase_evidence.json`。

## 最小修复及验证

`scripts/run_cispo_2030_full_year.py` 将配置检查和构建后检查统一使用 `direct_nonbasic_row_scaling_contract()`：当前修复版必须 `physical_v1/exponent=0`；旧版保持8192/exponent13。新增 `require_direct_nonbasic_runtime_row_scaling()` 仍校验实际矩阵的行名、系数、符号、非零数及元数据；没有直接跳过校验。运行时行元数据先写盘再执行资格判断，便于失败定位。

没有改变科学配置、数学变量/约束/单位、物理模型、输入数据或Gurobi参数。v3相对v2的文件SHA差异仅3项：runner、batch脚本、新增到部署包的测试文件，见 `release_delta.json`。所有 `cispo_model` 模块、科学/solver配置和修复水库数据逐字节一致。

本轮45项测试通过：7项正式入口测试（含3项新增运行时回归）+38项既有云端profile和年度行缩放测试。新增测试覆盖：

1. 真实Gurobi矩阵分别接受正确的物理行/8192配置，拒绝二者错配。
2. 拒绝缺失registry以及元数据与真实矩阵系数不一致。
3. 调用真正的全年runner `main()`，仅将大LP构建器替换为两条真实年度行，以 `--build-only --archive-original-model` 走过本次失败分支、参数回读和实际MPS归档。测试使用临时目录且不求解、不写规划状态；这证明入口路径修复，不是全国全年数值资格。

本机Gurobi12测试API；生产最低13要求保持。新batch在计算节点、实际Gurobi13与部署依赖下先重跑7项入口测试，PASS后才构建全国8760LP，避免相同的启动校验缺陷再耗费全年构建时间。此前numpy导入warning在本地日志原样保留，测试通过，不擅自更新共享环境。

云端v3完整输入预检查PASS，66项必需输入身份一致；两个非必需历史sidecar差异同前次并保留。传输SHA、203个文件校验、本地/云端Bash语法与源码diff whitespace检查通过。

## 重新提交

- 新作业 `4614693`，08:49:52提交为held，08:50:27核验申请后放行。08:51:11查询仍PENDING，实际分配尚未产生；后续回读见本目录 `restart_status_*.json`。
- 新release：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3`。
- 新结果根：release下 `output_8760/`。运行前检查日志为 `compute_node_smoke.json`、`startup_regression.log`；正式日志为 `stdout.log`、`stderr.log`、`output_8760/gurobi.log`。
- 继续使用64 CPU/750GiB/billing64、Gurobi48线程、Method2/Crossover0/SolutionTarget1/BarConvTol1e-4/NF2；无TimeLimit/SoftMemLimit/Slurm时限、无自动Stage B、无自动后续年份。未修改正在运行的Thermal `4533060`。
- 包：`20260914_base_v9_t48_m750_tol1e4_v3.tar.gz`，676910 bytes，SHA256 `987a351effdfca79d4020568aea0957a04a0d20b7fe1a5a238911610fb8c9547`，203文件。
- 科学配置指纹仍为 `937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0`。Git基准 `0a03cc452e95d158f36923ceb5210267979b6234` 加未提交工作树，真实执行源按逐文件SHA冻结，不能称为干净Git提交。

可复现命令：本目录 `stage_release.py`（已执行，拒绝覆盖）、`remote_setup_v3.py`、`remote_submit_held.py`、`remote_release_job.py`。已有作业不得重复提交。正式运行参数与上一版本相同，仅batch新增计算节点入口回归步骤。

下一步只读核对新作业分配、计算节点7项测试、正式输入加载、`annual_capacity_link_row_scaling.json`、`build_report.json`、`solver_parameters_before_optimize.json`、`model_archive`以及`solver_telemetry.jsonl`。本次已确认并修复启动代码错误，尚不等于验证全国LP长尾数值稳定性；不承诺9–10天收敛。
