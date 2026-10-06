# 2026-09-13 资源默认纠正与Barrier容差对照

## 结论

用户指出的44线程默认是正确的。当前Thermal job4533060以及
`config/cloud_resource_profiles/a8_8760_stagea_default_v1.json`一致采用：
**Slurm 64 CPU / 700G / billing64，Gurobi Threads44，不设SoftMemLimit。**
前轮限时测试包的32线程/550GB软限偏离已选定资源默认，现已纠正。
诊断入口直接读取已有资源配置的线程、内存和CPU字段，防止再次引入不同默认。

下一阶段数值诊断建议采用`BarConvTol=1e-6`，保留NF2、Crossover2/Basis1、
FeasibilityTol=OptimalityTol=1e-6及原单位QC。这是本地对照通过后的折中测试设置，
**没有证据证明它比1e-8在全国模型中更快，更不是新的全年数值验收。**
900秒优化、2小时任务墙钟仍为本次诊断预算；用户本次要求匹配线程和内存，没有要求取消诊断时限。

## Thermal实际设置已只读核对

服务器release：`20260907_thermal_stagea_1e4_t44_ffd651a_v2`。
实际Slurm为64CPU/700G/billing64；源release中对应solver profile为Threads44、
BarConvTol=1e-4、NumericFocus1、Crossover0、SolutionTarget1，TimeLimit/SoftMemLimit均null。
原作业仍RUNNING，本轮未修改它，也未提交新全国作业。

本次只恢复同样的资源，不能把Thermal整套算法参数直接覆盖到修复模型：
新模型此前通过的是NF2和Crossover2，且已经取消8192年度行缩放。
`config/optimization_numeric_dac_by_year_v9.json`的科学模型不变，本轮只改变诊断运行参数。
科学配置哈希前后一致：`937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0`。

历史44线程记录的峰值RSS约628.16GiB；550GB软限仅约512.23GiB，可能在已知内存范围内提前停止。
恢复无SoftMemLimit仍受Slurm700G硬上限约束，不意味着可无限使用物理内存。
历史峰值不等于已经测出修复版44线程的实际峰值，后者仍需全年诊断。

## 容差对照：更松不必更快

`BarConvTol`越小越严格，1e-8是Gurobi默认值。放宽可减少Barrier工作，但可能增加Crossover工作；
容差不是修复病态模型的替代方法。语义依据为
[Gurobi BarConvTol文档](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameterbarconvtol)。

同一v9夏季24h模型，起始小时3960，采用全年水库界和全年CF送出设计；本地8线程，均为冷启动。
1e-8基准取前轮最终冷测试，1e-6和1e-4本轮顺序执行。三份原始MPS逐字节一致：
`c8b0c338f86b550e59d42f48e6a5271f1c8b64fb0e6de3b1d78eef393c8e75c3`。

| BarConvTol | Barrier轮数 | Barrier秒数 | 总秒数 | 总Work | 最终QC |
|---|---:|---:|---:|---:|---|
| 1e-8 | 88 | 23.43 | 25.740 | 48.02 | PASS |
| 1e-6 | 83 | 23.02 | 26.347 | 47.22 | PASS |
| 1e-4 | 74 | 20.48 | 31.189 | 60.56 | PASS |

1e-6最终原行违反1.973532e-11、对偶违反1.748822e-9；
1e-4分别1.291056e-11、7.105427e-14，目标值与基准仅浮点级差异。
三组都没有最终质量损失，但1e-4的Crossover工作明显增加，总Work反而上升。
因此不支持“照Thermal设1e-4就会提速”。1e-6作为初筛折中，其实际运行效果仍须看真正全国LP。
本对照不测44线程吞吐量，不把本地8线程秒数推算为云端全年速度。

## 实现与验证

- `scripts/probe_full_year_numerics.py`从现有云资源配置读取默认Threads44/SoftMemLimit=null，
  完整模型要求Slurm CPU分配不低于该配置的64。实际参数回读会拒绝意外残留的有限SoftMemLimit。
- 新增`--bar-conv-tol`，可取1e-8、1e-6、1e-4，诊断默认1e-6；有效参数写入输出。
  v9源配置保留已归档的1e-8，差异明确属于诊断运行参数，不覆盖历史配置/解。
- 新包Slurm申请64CPU/700G，OMP/MKL/BLAS及Gurobi使用44线程，无额外软内存限制。
  求解前模型/参数归档、原子终态、严格QC、失败退出码及不覆盖旧目录均保留。
- 更新后的5项启动入口测试PASS；44线程、无限软内存、1e-6实际回读通过；
  默认dry-run确认资源字段。两次新增真实24h求解及完整物理QC通过。
- `sbatch --test-only`接受64CPU/700G/2h；4609802是模拟编号，非已提交作业；远期调度预测不作ETA。
  Slurm脚本通过`bash -n`。只读核对与全部日志保留。

新包：`cloud_gate_20260913_v9_t44_tol1e6.tar.gz`，197文件，662855 bytes，SHA256
`d743fa82f33f5b8b5f3427ceff1513bed8a13f55570f6dacc3b85e2d1ef624fd`。
该包替代前轮32线程/550GB软限包作为待启动候选，旧包保留；本轮未上传、未正式提交。

Git基线`0a03cc452e95d158f36923ceb5210267979b6234`，未提交。
证据：`thermal_verified.*`、`tolerance_comparison.json/csv`、`parameter_readback.json`、
`launch_tests.json`、`default_dry_run/`、两组`probes/`及`delivery_manifest.json`。
最新修改和下一步已同步四份交接文档。当前下一步是这一个固定参数的8760限时诊断，
不是重启或修改正在运行的Thermal，也不自动提交后续年份。

检查新的默认计划（新输出目录）：

```powershell
python scripts/probe_full_year_numerics.py --output-dir output/numeric_t44_plan --dry-run
```


## 2026-09-13 用户提醒后的追加更正

> 2026-09-13 Crossover更正：原定Stage A/Thermal为0/1，入口已恢复Crossover0/SolutionTarget1；44线程/64CPU/700G/无软限不变。新24h无Cross、BarConvTol1e-6及1e-4均OPTIMAL但完整QC HARD_FAIL（水库平衡等），先前Cross2通过不能冒充原定方案资格。撤回上轮可启动结论；1e-6仅为未验收测试值，新包仅归档诊断用途，未上传/提交。下一步本地定位失败行，详见crossover_contract_20260913/REVIEW_ZH.md。

三组Cross2容差比较仍为真实历史证据，但不再用于直接推荐原定Cross0方案的容差。旧包保留，新的复测和当前下一步以上述后续报告为准。
