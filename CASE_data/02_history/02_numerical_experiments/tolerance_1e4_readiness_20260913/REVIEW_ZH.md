# 2026-09-13 用户选定1e-4后的参数和剩余问题复核

## 当前结论

用户明确选择`BarConvTol=1e-4`，待测入口及新本地包已采用该值。
保留`Method2/Crossover0/SolutionTarget1/Threads44/NumericFocus2/ScaleFlag2/Presolve2`，
`FeasibilityTol=OptimalityTol=1e-6`、Slurm64CPU/700G、SoftMemLimit=null。
不启用自动Crossover或Stage B，不改物理模型、输入数据或QC阈值。
`1e-4`是本次选定的Barrier停止容差，不意味着每条原单位约束的绝对误差都小于1e-4。

本轮完成参数设定和诊断可靠性修复，复用上一轮同一v9、Cross0/1e-4真实冷求解作物理证据，
没有把它描述为本轮新的求解。该24h模型OPTIMAL、21.176s/74轮，但完整严格QC仍HARD_FAIL。
可运行有预算的诊断以继续暴露问题，尚不能宣称已解决全国8760 NUMERIC或直接验收生产结果。

## 剩余问题的实际量级

从已归档620库×24h的库存、入流、上游来水、发电用水和弃水独立重建：
`residual_m3 = V[t]-V[t-1]-(local_inflow+upstream_release-turbine-spill)*3600`，首小时循环。
输入/变量单位和31省/逐小时空间时间结构保持原模型，决策与年化系统成本目标均未改。
该窗口起点3960，归档NPZ里的hour_index为局部索引；本轮CSV同时给出selected_hour和weather_hour，避免时间错位。

- 水库最大残差1313.794983m3，位于高凤山`HydroCHN_01080`、库索引471、窗口小时1（气象小时3961）。
  在矩阵中的名称是`reservoir_independent_hourly_transition[345,0]`，不能把345当成站点全局索引。
- 14880站时中20站时超过1m3；全部绝对水量残差合计1619.675758m3。
  按当前各站水头和效率折算，最大单点176.025kWh，全部绝对残差折算合计310.895kWh。
  这是当前参数下的量级换算，不是实际损失电量，也不是全年误差上界，未累计梯级传播。
- 跨省双向流最大42.1258MW；24h反向重叠电量1.571604GWh，额外损耗0.037115GWh（37.115MWh）。
  城市网络对流也未通过现有严格QC。不能把未经守恒重建的流量直接在导出表里归零。
- 小幅同时充放电合计0.485553GWh、最大2.1939MW，目前是诊断项，不能仅凭次数多宣布模型错误。
- 59项小时硬检查57项PASS，失败的是reservoir_transition与unidirectional_interprovincial_flow；
  城市网络是另一个QC层。供需平衡、储能状态、碳约束等这次局部检查通过，不代表所有年份通过。
- 目标相对同MPS Cross2严格解高0.0033988%，与选择较松Barrier容差一致；目标接近不替代物理验收。

因此此前只报原行残差1.3e-3不足以判断科研影响；换算后的局部能量误差很小，
也不应把严格QC失败直接等同于先前9天的NUMERIC无解。但全年数值稳定性仍需要实际验证。

## 数据层仍有待核实项

最差残差所在高凤山的源active storage仍为3354.936947GL（约33.55亿m3），装机75MW。
该库容在已有全小时审计中属于估算模式/容量更新后水力字段待复核，带duplicate_comid标志；
全年库存界已有水量约束收紧，不能把物理源库容字段和LP实际有效上界混为一谈。
黄坛口`HydroCHN_00556`是第二大残差位置；其数据也只代表当前源表，不是新增工程认证。
本轮有限网页查找未找到足以直接替换高凤山调节库容的可靠工程值，未猜测数值或套用近名凤山水库。
官方水电坝注册中存在高凤山记录，但不能由此证明库容值正确：
[国家能源局2015年注册复函](https://zfxxgk.nea.gov.cn/auto93/201503/t20150319_1892.htm)。

当前高优先级是核实高凤山工程/库容/河段匹配，然后在固定1e-4/Cross0下验证残差改善。
不通过不断改容差、自动开Crossover或只在报表里抹掉违约量宣称修复完成。

## 已修好的诊断遗漏

`scripts/probe_full_year_numerics.py`现在：

1. 默认1e-4，plan/effective_config以及实际Gurobi回读一致。
2. 无条件调用项目已有`save_numeric_snapshot`，分块尝试保存BarX/X/BarPi/Pi等；
   即使SolCount=0仍记录哪些属性可读、哪些不可读及哈希，不把不可读向量当成能续算。
   不再用全量X数组副本保存文件；保留旧solution.npy接口，失败信息及原始MPS仍归档。
3. 城市/容量QC和小时物理QC独立执行；前者失败不会跳过水库诊断。两处继续enforce_qc=True。
4. OPTIMAL仍必须全部QC/原行与对偶误差合格才返回验收成功；保存向量和写出诊断不等于接受。

8项测试PASS，含真实小LP的无基Barrier向量保存、无解属性不可读记录、前层QC失败仍调用小时QC。
实际参数回读和dry-run通过；科学配置身份不变；Bash语法检查通过。当前模型未新增变量/行或改变目标。

## 测试预算与交付

当前保留900秒optimize、2小时Slurm作业总墙钟的早期诊断预算；未因本轮选容差自动增加预算。
历史44线程排序4155.5秒明显长于900秒，因此这个预算可能只能看到构建/预处理/排序，
不能把没有Barrier迭代的TIME_LIMIT当成数值失败，也不能据此宣布收敛资格通过。
新模型耗时尚未测出，不能机械套用历史秒数。若下一步需要评估迭代进展，须先明确覆盖排序的有限测试预算。

新本地包`cloud_gate_20260913_v9_t44_cross0_tol1e4.tar.gz`，197文件、663247bytes，SHA256
`d47f050c79a6e3c73d4216a80a3cbe0d8f168b62e630343ffdeb4905f9e2a6a2`。
旧1e-6及Cross2包保留为历史，下一次按用户选择应使用此1e-4诊断入口。
没有连接/变更服务器，没有上传或提交新作业，也没有修改正在运行的Thermal。

Git基线`0a03cc452e95d158f36923ceb5210267979b6234`，未提交。
本轮生产改动仅诊断脚本和测试；前后源快照/差异、命令、独立残差明细、参数与哈希在本目录。
详细机器可读证据：`residual_triage.json`、`worst_water_residuals.csv`、`source_storage_flags.csv`、
`parameter_readback.json`、`default_dry_run/`、`launch_tests.stderr.log`及`delivery_manifest.json`。

本地只查看当前有效计划：

```powershell
& 'C:/Users/ZZ/.conda/envs/RL/python.exe' scripts/probe_full_year_numerics.py --output-dir output/numeric_1e4_plan --dry-run
```
