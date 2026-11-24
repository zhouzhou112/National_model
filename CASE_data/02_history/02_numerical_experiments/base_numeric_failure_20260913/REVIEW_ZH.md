# 2030 Base 8760h 数值失败复核（2026-09-13）

本轮为只读取证与日志复算，不执行 optimize/presolve/IIS/松弛，不修改科学模型或任何作业。
本地 Git HEAD `0a03cc452e95d158f36923ceb5210267979b6234`；原有未提交文件保留。
输入为云端冻结 Base job `4479238` 的日志、报告、参数及 Slurm 记录，精确路径见 `source.json`。
部署 release 为 `20260903_8760_stagea_final_2820fc3_v3`，case 为
`2030_base_8760_rows8192_stagea_final_t32_mem550_slurm32_no_softmem_2820fc3_v4`。

## 1. 已核实的损失与终态

- Slurm：2026-09-03 17:24:04 开始，2026-09-13 07:16:40 结束，历时 9天13小时52分36秒，FAILED 2:0。
- Gurobi 13.0.2：654轮，Barrier 824483.46秒，status 12 NUMERIC；不是 OPTIMAL 或已证明 INFEASIBLE。
- `solution_count=0`，`X/BarX` 无法读取；QC NOT_EVALUATED，preservation PARTIAL，terminal INCOMPLETE_NO_USABLE_STAGEA。
- preservation 的导出异常在数值失败之后发生，不能把后续 Unable to retrieve attribute 'x' 当作失败起点。
- MaxRSS 503822896K，约480.48 GiB，申请550G；已核实终态不支持 OOM/超时/节点故障归因。
  wrapper 的 `STAGE_A_INFRASTRUCTURE_FAILED` 是分类标签，不是硬件故障证据。
- 原 MPS 文件保留，可重建问题；没有可恢复的本轮解向量。不能从第654轮原地续算。
  原 MPS 不包含 Barrier 私有分解状态；本轮未重新下载或校验整个约3.86 GiB MPS。

以获得可用于论文的规划解衡量，本次计算未达成目标。保存的模型与日志有诊断价值，不能抵消求解时间损失。

## 2. 实际轨迹与此前进度判断的纠正

本轮解析全部655条日志（iter0至654）。沿用 `cispo_model/diagnostics.py` 的诊断式：
`abs(P-D)/max(1,abs(P),abs(D))`。日志数值经过打印舍入；此量不是已认证最优性误差，亦不是 Gurobi 内部全部停止条件。

| iter | Primal objective | Dual objective | Primal residual | Dual residual | Compl | 相对目标差 |
|---|---:|---:|---:|---:|---:|---:|
| 481 | 1.03421997e10 | 4.12402855e6 | 0.104 | 0.0102 | 0.00988 | 99.9601% |
| 600 | 3.11696489e9 | 4.18767044e6 | 6.77e-4 | 5.52e-4 | 5.61e-5 | 99.8656% |
| 633 | 1.06285268e9 | 4.18792928e6 | 8.40e-5 | 1.52e-4 | 6.75e-6 | 99.6060% |
| 634 | 1.16211747e9 | 4.18793173e6 | 8.20e-5 | 1.46e-4 | 0.0631 | 99.6396% |
| 654 | 1.15843259e9 | 4.18790162e6 | 8.19e-5 | 1.46e-4 | 0.0633 | 99.6385% |

整个过程相对目标差最小99.6060%，远高于项目接受门槛1%。iter633至634的Compl恶化约9348倍，随后约20轮停滞。
因此“仅差最后一点”“Compl低于0.01便接近完成”“按近期衰减还需1–2天”的说法没有充分依据。
原链接线程9月9日至10日的ETA应撤回；这属于监测解释遗漏目标差，不能归咎于作者。
此前文字“目标上下界”亦不够严谨：在可行性未认证时应称原始/对偶迭代目标，不应视为有效上下界。

## 3. 原因：已知事实、合理推断与未决问题

1. **直接原因已确定**：Barrier 数值失败，无法提供可读取解；错误不是输出CSV造成的。
2. **尺度风险已确定，具体病态位置未确定**：41,458,383变量、50,907,234行、492,835,195非零；矩阵非零系数
   1.000486e-6至6250，跨度约6.247e9；目标系数1e-6至3853；日志边界6e-11至4e5、RHS约3e-7至1e6。
   这些范围与失败轨迹支持数值条件不良的怀疑，但不能单凭范围证明条件数或锁定某条约束。
3. **结构与历史证据**：37,696 dense columns、26 free variables，Factor NZ约3.375e10，每轮约20分钟。
   9月5–6日全国24h的无Crossover测试已发现水库原单位残差超限，大自由周期库存/小小时通量是已定位风险。
   该证据来自历史24h样本，不证明本轮全年一定由该水库块触发；预处理聚合、近零边界、退化/近相关约束也待检查。
4. **当前求解路线未解决上述风险**：Method2、Crossover0、NumericFocus1、ScaleFlag2、Presolve2、Aggregate1、BarConvTol0.01。
   无Crossover不会自动构成错误，且Crossover也可能失败或昂贵；但历史依赖Crossover通过的结果不能证明当前路线可靠。
   短时段测试、build/presolve与模型身份通过，同样不等于全年数值收敛通过。
5. **不能据此判定科学模型不可行**：日志的 may be infeasible or unbounded 是建议诊断的提示，status12没有给出不可行证明。
6. **保全边界**：当前机制在solver返回后尝试导出BarX，NUMERIC终态不保证属性可读。
   “有保全机制”不能表述成“无论如何都能接着算”。普通日志只记录标量，不能反推出四千多万维解向量。

历史证据：`../portfolio_prelaunch_20260905/REVIEW_CN.md` 中水库残差定位。
官方依据：[数值问题识别](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/modelissues.html)、
[数值参数与算法选择](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/numeric_parameters.html)、
[Barrier日志含义](https://docs.gurobi.com/projects/optimizer/en/current/concepts/logging/barrier.html)。

## 4. 当前处理与精确下一步

已保留小体积原始证据并复算轨迹；没有重启Base、启动Stage B、停止或改参Thermal。
Thermal4533060在本轮Slurm查询时仍RUNNING；其原线程日志iter366→367的Compl实际为0.257→8.24e11，
应纠正旧总结误引的0.292。当前继续运行不等于数值健康，最终是否可用仍未知。

下一步先对冻结模型的系数来源、近零边界、水库周期库存与年度容量耦合做离线定位，提出数学等价变换与验证计划；
不能仅增线程、放宽容差或直接重跑相同全年配置。若需要新的solver实验，先形成可审查候选与有限预算的配对测试，
保留小时/空间尺度、原单位QC与原科学约束；不能自动启动新的付费求解。
今后监测同时报告两目标及差距、三种残差、突变/停滞、解可读性；停止发布仅按残差曲线外推的ETA。

## 5. 复现与验证

运行 `python supplementary_materials/reviews/base_numeric_failure_20260913/analyze_log.py`，不导入Gurobi、不求解。
输出 `barrier_iterations.csv`、`analysis.json`（含证据SHA256）；验证655轮连续、NUMERIC、solution_count0，通过。
输入完整小文件来自只读SSH/SCP，调度命令为 `sacct -j 4479238,4533060 --format=JobID,State,ExitCode,Elapsed,Start,End,AllocCPUS,ReqMem,MaxRSS -P`。
本轮无随机实验，随机种子不适用。修改范围为本报告目录及三份交接文档，未提交，未修改运行源码/配置/数据。
