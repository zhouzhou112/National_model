# 数值稳定性隔离实验记录

> 本文件保留2026-08-28至08-29各次实验的历史现场。完整8760h审计、后续新增候选及跨尺度
> 判定规则现统一见`NUMERICAL_STABILITY_ENGINEERING_LINE.md`；下文旧的“运行中/失败”段落不得
> 覆盖后来已经通过完整SHA和规模校验的审计终态。

日期：2026-08-28。作者授权在不干预当前GPU-PDHG的前提下同步改进数值稳定性。
本目录是从production `6065bfba34b76098e86307081323e8545a4d25ac`建立的独立worktree，
分支`codex/numerical-stability-20260828-v1`。主工作区的未提交修改没有复制、覆盖或部署。
本分支旧交接文档中的8月25日服务器状态不是当前状态；实际状态以主工作区8月28日快照及SSH核验为准。

## 当前结论

**尚无通过跨窗口验证、可以部署的大规模数值稳定性修复。**

- 已实现可逆二进制行列缩放、原单位误差还原/容差预算、只读MPS流式审计。
- 首个无容差预算缩放候选虽然改善系数范围，却增大部分原单位误差，已拒绝。
- 第二版在已有1h归档中显著改善原单位primal误差，但同起点24h回归仍出现NUMERIC，暂不推广。
- 已发现并修正一个可严格证明的零入流水库边界问题；仅此worktree修改，数学等价证明通过，
  但24h仍NUMERIC，不宣称带来数值/性能收益。
- 全尺寸8760h原矩阵的逐项流式审计已后台启动；尚未完成，不把部分扫描称为完整证据。
- 未改当前PDHG模型/参数/环境、未重启/停机、未添加服务器求解任务；未增加算法竞赛Case。

## 运行隔离与环境

服务器最近核验为**14:56+08:00**：production仍clean6065bfb，
原Python1216969自02:15:14运行，GPU1 RTX4090利用率100%、4600/24564MiB。
PDHG无时限及原3h巡检/2s采样不变。

本地测试：Windows、Python3.10.14；`.venv`为独立环境，复用RL基础包但只在本venv安装Gurobi13.0.2。
原RL环境的Gurobi12.0.1未卸载或修改；numpy1.26.4/scipy1.13.1，pip check通过，2501变量license gate通过。
新增归档A/B使用本机2线程/120s单次诊断上限，没有SoftMemLimit；它们不是2160h算法筛选，也不继承/改变PDHG时限。
不在服务器加载第二个大模型，不在云端申请计算作业。云端只执行一次只读`cat`，解压、解析和哈希均在本机。

## 数学边界与缩放

原连续最小化LP保持`min c^T x + c0`、`A x (<=,=,>=) b`、`l<=x<=u`。
采用正二进制对角因子`R,D`及坐标变换`x=D z`：

```
A_scaled = R A D
b_scaled = R b
c_scaled = D c
l_scaled = D^-1 l; u_scaled = D^-1 u
pi_original = R pi_scaled
rc_original = D^-1 rc_scaled
```

目标常数、目标方向、约束方向不变。没有另行目标缩放、系数删减、放宽物理约束或改源数据。
物理输出仍须回到GW/GWh/MtCO2/2025 constant million CNY等原单位。缩放变量不是新物理变量。
矩阵/目标/RHS/上下界逆变换及MPS导出重读逐项bit-exact；数值求解仍可能受舍入与终止条件影响。

第二版限制二进制指数在[-9,9]。按最坏放大预算将scaled FeasibilityTol/OptimalityTol设为
`1e-6/512=1.953125e-9`，不是任意强化物理QC。预算不保证Barrier所有终止指标达标，必须检查还原解。
独立数组门检采用原单位primal/bound/stationarity/dual-sign<=1e-5及相对目标差<=1e-6，
不冒充完整业务QC，也不因小试验通过而科学接受。

## 实验与负结果

### A. 既有1h归档（只做工具和等价性回归）

输入为主工作区`outputs/stage_a_recovery_validation_20260827_v2_gurobi13/source/model_archive/original.mps`，
SHA256 `a52f8aabfa204c0025fad981499cd4b7e68960640e51a619d70308802bb6f4f7`。
80143行、238529列、453269非零；不是新选取的性能基准，不代表全年难度。

| 指标 | 原LP | 无预算候选v1 | 容差预算候选v2 |
|---|---:|---:|---:|
| 原始Matrix极值比 | 5.8875e9 | 5.8875e4 | 2.3550e5 |
| 原单位最大约束违反 | 9.4161e-7 | 4.4746e-6 | 7.0887e-11 |
| 原单位最大边界违反 | 2.6156e-7 | 2.6146e-7 | 1.7299e-12 |
| 原单位dual-sign违反 | 3.1375e-7 | 6.2795e-6 | 1.0132e-6 |
| solver秒（单次，无重复统计） | 约2.54 | 约5.08 | 约5.32 |

第二版与基线目标相对差4.6053e-11；两者均OPTIMAL，数组级门检通过。
但第二版并非所有dual指标都变好，也没有速度收益；行尺度分布、RHS与边界跨度并非全部改善。
因此不能将Matrix极值比下降称为条件数下降或全尺寸加速。
证据：`outputs/archived_1h_binary_scaling_v1/`、`outputs/archived_1h_binary_scaling_v2/`。
v1复现须显式`--exponent-limit 20 --legacy-unbudgeted-diagnostic`，仅保留反例，不允许推广。

### B. 新建24h、start2880的结构回归

仅本地从生产基线代码构建Base2030，wave on/flexible_load off，小时2880～2903；
不改变连续小时、周期边界、年度流量H/8760与年度投资成本规则。
构建无optimize/presolve（方法已用mock禁止），约32.55s，346767列/213253行/1834406非零。
源MPS SHA256 `7b341915dcab9a819414b9c4171993051ebdbff6962ae81606def80cfe767e20`。

- 原LP Barrier：120步，约14.29s，status12 NUMERIC、SolCount0。
- 二进制缩放v2：126步，约14.70s，status12 NUMERIC、SolCount0。
- 原LP与缩放LP代数逆变换/导出重读仍通过，但求解验证失败；两者都不接受、不部署。
- 预求解Matrix极值比约6.09e9→7.80e7，但最差单行比约1.83e6→6.43e6，反而变差。
  这再次说明只优化全局range不充分。

唯一额外检查是同一失败原LP的homogeneous-Barrier可行性诊断，不是新增性能算法组合。
未放松模型，返回status13 SUBOPTIMAL，而非INFEASIBLE；所以没有有效IIS、不能认定模型不可行。
原LP最大约束违反3.38192395e-4、DualVio0.0011880，仍不接受。
重复同一诊断仅为保存向量/最差行，参数相同。最差行主要是水库水量状态转移，行内系数仅1～3.6，
并非只有DAC的6250行有问题。该定位不证明这些行独立导致全部问题。
证据：`outputs/source_24h_start2880_v1/`、`paired_24h_start2880_v2/`、
`diagnose_24h_start2880_v1/`及`diagnose_24h_start2880_vectors_v1/`。

### C. 严格零入流水库上界修正（未部署）

旧`_reservoir_release_upper_scaled`对包括严格零上界在内的结果统一加`1e-12`余量。
新实现只从原始入流全为0、上游零入流证书、零传输系数/权重推导严格零；不以求和浮点为0、
不以阈值或“很小”代替零。所有正入流保留原来的向外舍入，包括1e-320这样的正数测试。

证明：将周期水量平衡逐小时相加，库容项抵消。全周期总入流为零且发电/弃水流量非负，
因此每小时释放量都必须为零；沿有向无环上游图传播同一结论，不依赖初始库容为零。

24h重新构建后，10944个水库泄流变量UB由正微量变为精确0；
Matrix/RHS/Objective/LB/变量名称/约束名称/方向/目标常数全部逐项保持不变。
独立证书直接从**旧MPS等式行求和**验证了全部10944个变更，无未覆盖变量，不仅依赖代码注释。
源MPS SHA256 `c8c91a9a3be558e40c359d6a3eeaa3f99e56d362ead655db558de049e92c998d`。
求解仍是120步/NUMERIC，与原基线几乎相同；没有验证到实际数值改善。
这项改动只消除数学冗余余量，不能作为已解决收敛的证据。
证据：`outputs/source_24h_start2880_exact_zero_v1/`、`outputs/zero_bound_fix_24h_start2880_v1/zero_bound_certificate.json`。

## 8760h全尺寸流式审计：运行中

14:49:54+08:00启动，Python实际PID34684，venv启动器37332，SSH客户端40220；
必须每次操作前核验命令行/创建时间，不凭本文旧PID操作。
本地进程BelowNormal、单解析进程，15:02约39MB RSS；不占GPU，不在固定服务器计算。
15:02已读完50,907,234条约束名，进入矩阵系数段；约15,089,834/492,835,195非零已扫描，
这不是完整矩阵检查完成，亦未获得完整文件SHA复核。预计需较长时间，勿换标签重复启动。

- 云端只读源：`paracloud-bscc-a8:/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1/recovered_8760/model_archive/original.mps.gz`。
- 预期大小4142909397bytes；SHA256 `344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d`，来自既有完整release清单。
- 预期约束/列/非零50907234/41458383/492835195；gzip CRC、ENDATA、SHA256、大小和维度全部通过才COMPLETE。
- 状态：`outputs/stream_8760_original_v1/status.json`；完成后`audit.json`。
- 启动stdout/stderr：`outputs/stream_8760_launch_v1/`；SSH stderr在运行目录。
- 输入是云端完整源文件，不是仍在传输的固定服务器副本；未干预原备份流程。
- 统计为全局/行族/列族范围、对数分箱、逐列跨度；**不提供逐行全量跨度或条件数**。
  不保存全部LP，内存受族数量/缓存限制；输出目标常数与约束RHS分开。
- 工具从不调用Gurobi；本机需保持联网开机。异常写FAILED并退出，不自动重启或缩模型。

## 验证、运行方式与下一步

已通过：缩放/流式解析11项、零边界及独立证书9项、原有bound_tightening7项；
归档流式统计与原build_report的维度/系数极值/哈希一致；pip check通过。
完整项目回归237/237通过（80.494s），含上述20项新增单测；不能将这些测试等同全尺寸科学QC。
现有solver-profile单测会在微型测试模型上验证历史配置，包括其TimeLimit/SoftMemLimit，
不表示给本轮PDHG或新增A/B设置这些历史参数。早期诊断脚本的rc0只表示执行结束；
当前版本已让求解/原单位质量失败返回rc2，历史NUMERIC输出不重写、不伪装成成功。

```
.venv/Scripts/python.exe -m unittest discover -s tests -p test_lp_equilibration.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -p test_exact_zero_reservoir_bounds.py -v
.venv/Scripts/python.exe scripts/audit_saved_mps_stream.py --help
.venv/Scripts/python.exe scripts/validate_lp_equilibration.py --help
```

下一步先读取全尺寸流式审计终态和SHA/规模校验，聚焦真实极值来源与水库状态链相关族；
仍需独立资源窗口的全尺寸presolved系数/条件诊断，不能从1h或24h外推。
此后设计有证据支持的等价结构改进；不要继续无依据扩展参数组合。
本轮所有候选均保持未部署，当前无时限PDHG继续，绝不把NUMERIC/子最优结果标为达标。

参考：[Gurobi用户缩放说明](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/tolerances_scaling.html)、
[原单位质量与数值诊断](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/modelissues.html)。
