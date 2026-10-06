# 2026-10-05 两项隔离验证的共同证据

Git 基准为 `0a03cc452e95d158f36923ceb5210267979b6234`，开始时已有大量 dirty 内容；本轮创建分支 `codex/validation-pair-20261005`，未回退或清理原文件。两项实验证据分别由相邻 `factor_pair_8760_20261005` 和 `numerical_robustness_20261005` 目录保存。本文件仅记录共用环境、回归与协调，不替代两份实验判定报告。

## 已核验差异

- 用户提到数值任务书第 5b 节，但收到的完整文件没有该节；固定机不可用时按用户本轮明确授权本地缩窗，不能将短窗标为 744h 通过。
- Slurm held 时没有 AllocTRES。先核 ReqTRES=64CPU/750G/billing64 后放行；计算节点核实际 AllocTRES 通过才允许建模及求解。
- V9 的既有 headroom 清理会使源清单 14,170 个有空间候选在实际模型中变为 14,167；不修改原有清理规则凑齐数量。
- `BarHomogeneous` 已有配置支持；C 中碳/生物质真正的跨小时稠密求和位于 `monolithic.py`，不能只拆 `master.py` 中引用年度聚合变量的短行。

## 环境与既有回归问题

最新补证（英国19:55）：正式runner审计和独立清零白名单加固后，`unittest_verified_20261005T185140Z.log`确认412项/112.906秒、`OK (skipped=1)`、exit0、源码前后SHA相同。日志SHA=`bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79`；RSS采样峰1031180288bytes（约0.96GiB）、系统可用最低15548526592bytes（约14.48GiB），保护未触发。启动前`_started.json`记录源SHA和非敏感环境白名单，完成JSON与memory.jsonl保留。中间`184739Z`因该shell漏设CISPO_WAVE_ROOT出现8项环境错误，保留失败记录；补齐环境后才得到上述最新通过，不把环境失败当模型数值失败。

最终验证：作者在蓝屏后重新授权本机串行测试，`unittest_verified_20261005T183454Z.log`确认411项/110.818秒、`OK (skipped=1)`、exit0，唯一skip为Windows不适用的Linux /proc集成。对应JSON记录受测源码前后SHA完全一致，日志SHA为`f2335935e2e62579f0bcbded12c3e5efbb2898bf0cfed4c59fe78133f517ea1b`。`_memory.jsonl`每2秒采样测试树RSS峰约0.95GiB、系统可用最低约14.65GiB，3GiB保护未触发；不代表上一轮崩溃前峰值。旧`unittest_verified_20261005T172230Z.log`因蓝屏中断、无完成JSON，不计通过。原始失败及中断证据均保留。

1. 默认 `D:/anaconda/python.exe` 缺少 Gurobi 与 Zarr。`unittest_baseline.log` 保存 181 项测试、8 failures、34 errors、1 skip 的原始失败；没有为此安装或修改全局环境。
2. 复用 `C:/Users/ZZ/.conda/envs/RL/python.exe`，通过 `PYTHONPATH=<repo>/output/portfolio_runtime_gurobi13` 选择既有 Gurobi 13，`CISPO_WAVE_ROOT=<repo-parent>/wave_energy`、`OPENBLAS_NUM_THREADS=1`。`unittest_rl_baseline.log` 是整合过程中的 402 项测试记录，2 failures/1 skip；该次不是最终回归。
3. 原 `audit_release_contract.py` 默认审计继承 2026-07-30 的旧情景成员，与已建立的可选组合 V5 目录冲突。本轮新增只覆盖目录的 `config/release_contract_v1005_catalog_audit.json`，其余历史输入哈希、Base/solver 检查继续继承；默认审计切到该合同。它不构成 V9 科学或求解器接受资格。`release_contract_test.log` 的 2 项测试通过，历史合同不变。
4. `test_flexible_portfolio.py` 仍断言 `1e-9`，与该 profile 自 2026-09-07 已明确授权的 `1e-4` 不符。本轮只纠正测试断言，不改 profile。
5. suite dry-run 全套中一度失败，单独真实 dry-run 与 4 项 suite 单测通过，原始输出保留于 `suite_baseline/` 与 `suite_unit.log`。测试现附上子进程 stderr，避免临时目录删除后只剩失效路径。
6. `unittest_integrated_1.log`：410项、151.848秒，`OK (skipped=1)`，进程退出0。跳过的是Windows不适用的Linux `/proc` 专用集成测试。日志含一条非致命子进程UTF-8读取线程异常，未导致测试失败；后续代码修正后仍需最终回归，不删除此原始记录。

完整回归复现（PowerShell，在仓库根目录）：

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'output/portfolio_runtime_gurobi13'
$env:CISPO_WAVE_ROOT = Join-Path (Split-Path (Get-Location)) 'wave_energy'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = 'C:\Users\ZZ\.conda\envs\RL;C:\Users\ZZ\.conda\envs\RL\Scripts;' + $env:PATH
python -m unittest discover -s tests -q
```

路径仅为这台机器既有环境的复现记录，不是模型代码内的硬编码依赖。Linux `/proc` 专用测试在 Windows 跳过须单列，不能冒充已执行。

## 原作业与候选续接输入

本轮用 `squeue` / `sacct` 只读确认 4844528 为 RUNNING、m4cm1802、64CPU/750G，未对它发出控制命令。任务2所需 `20260919_base2040_v9_t44_m750_tol1e4_v1/upstream_2030_bound_closed` 共10个文件通过 SSH/SCP 只读取回；远端与本地逐文件 SHA 一致，证据见数值目录 `upstream_transfer_verification.json`。其未接受的科学身份保留；不读取或复制任何凭据文件。
