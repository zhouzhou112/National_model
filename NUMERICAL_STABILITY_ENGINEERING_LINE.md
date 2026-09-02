# CISPO数值稳定性工程线 V2

日期：2026-09-02  
分支：`codex/numerical-stability-engineering-v2`  
生产基线：`6065bfba34b76098e86307081323e8545a4d25ac`

## 1. 工程线目的与边界

本工程线统一保存8760h原始LP数值审计、已经验证过的等价缩放工具、年度能量坐标候选、
CF稀疏化误差审计及配套实验脚本。所有候选默认关闭，必须逐个、单因素启用；把代码放在同一
分支不代表允许在同一实验中叠加它们。

生产模型、活动Stage B、数据根、物理单位、时间/空间边界、目标函数和求解容差均未由本工程线
修改或热更新。固定服务器活动checkout继续停留在clean `6065bfb`，本分支只用于后续隔离测试。

## 2. 本地与服务器版本关系

- 固定服务器生产HEAD：`6065bfb`，分支`codex/cispo-2030-full-lp`，工作树clean。
- 本地主分支与固定服务器裸远端：`65c8b21`。
- `6065bfb`是`65c8b21`的祖先；本地主分支仅多`8165b20`和`65c8b21`两条活动2160h运行记录，
  没有代码分叉或双向独有提交。
- 选择`6065bfb`作为工程线基线是为了与当前服务器Stage A/Stage B的实现身份一致；后续如需部署，
  应推送本工程分支并建立新checkout/新标签，不能直接快进活动生产checkout。

## 3. 8760h完整原始矩阵审计

审计对象是历史保存的Base2030完整`original.mps.gz`，大小`4,142,909,397 bytes`，SHA256
`344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d`。下载完整性、gzip、ENDATA、
行列非零元计数全部通过；规模为`50,907,234 rows / 41,458,383 columns / 492,835,195 nonzeros`。
该审计没有调用build、presolve或optimize，因此不提供presolved range、Kappa或科学QC。

| 项目 | 最小非零绝对值 | 最大绝对值 | 跨度 |
|---|---:|---:|---:|
| Matrix | `1.000486e-6` | `6250` | `6.246964e9` |
| Objective | `1e-6` | `3853.189876` | `3.853190e9` |
| RHS | `2.522818e-7` | `1.14e6` | `4.518757e12` |
| finite bounds | `5.657608e-11` | `362808.7358` | `6.412759e15` |

首要结构风险是同一`GW`容量列同时连接约`1e-6`的小时CF和约`6000`的年度满发小时：
`hydro_capacity_gw`列跨度约`5.94e9`，`vre_capacity_gw`约`5.92e9`。VRE和hydro容量列合计占
原矩阵约43.65%的非零元。年度负荷中心网络还同时包含6250、4380与`1e-6`目标系数。

小Matrix系数`[1e-6,1e-4)`约1,411,322个，只占非零元0.2864%；它们数量少，但位于容量与小时
availability的关键连接上，既不能仅凭数量删除，也不能仅凭全局range判断条件数。

## 4. 已完成尝试及当前证据等级

### A. 通用二进制行列equilibration

- 代数映射、MPS回读、原单位primal/dual误差还原和容差预算已实现并有单测。
- 1h归档可将Matrix跨度从约`5.89e9`降至`2.36e5`，但速度约2.54→5.32s。
- 24h/start2880原LP与候选分别120/126 Barrier步，均返回NUMERIC；候选还把最差单行跨度从
  约`1.83e6`增至`6.43e6`。
- 结论：保留为诊断工具，不作为当前生产候选。全局range变小不等于presolved系统更好。

### B. 严格零入流水库上界证书

- 对原始入流严格为0且上游贡献可证明为0的水库变量，将原先人为`1e-12`余量改为精确0；
  24h中10,944个变量变更，逐项由旧MPS等式求和证书覆盖。
- Matrix/RHS/Objective/变量与约束名称均不变，仅修复数学上应为0的上界。
- 24h仍为120步/NUMERIC，没有观察到速度收益。
- 结论：这是高置信度等价边界修复，但不是已证实的加速方案；可作为独立候选继续放大验证。

### C. Annual Energy Coordinate V1（默认关闭）

- 只把年度账户和省内年度流量按`S=8192 GWh=2^13 GWh`改变内部坐标；逐小时CF、径流、容量、
  水库和科研输出仍保持物理单位。
- 24h严格解中raw Matrix上限`6250→260.417`，presolved NNZ`1,372,315→1,354,338`，Factor Ops
  `6.432e8→6.246e8`；目标binary64相同，候选`OPTIMAL + QC PASS + manifest complete`。
- 但Barrier迭代`120→131`、严格求解`174.979→178.807s`，非exact Kappa也更差。
- 结论：24h没有速度收益，但短时段不能证明更长时域必然更慢；保留为744h/2160h单因素候选。

### D. CF阈值`1e-6→1e-4`（改变可行域）

- 完整8760h误差上界：额外删除VRE 64,001项、ROR 261,060项、wave 0项；容量上界可利用能量
  最多减少约6.1015GWh，既有容量floor能量约减少0.4151GWh，资源峰值小时上界损失保守和
  约0.01303GW。它不是代数等价变换。
- 744h五步筛选曾显示Factor NZ -2.24%、Factor Ops -6.14%、早期solver约-7.10%。
- 但完整744h Stage A中，候选相对基线Barrier`120→134`、solver`2995.079→3070.307s`
  （+2.51%）、work units +5.75%、端到端 +2.91%、process-tree RSS +1.76%。
- 结论边界：`1e-4`不凭744h结果晋级744h Stage B或生产默认值；但744h负结果不能证明2160h/
  8760h一定更慢，因为presolve消元、稀疏填充、排序与长时序块结构均非线性随时域扩展。
  因此候选保留为“长时域研究候选”，只能按第6节门禁继续，而不能直接启动8760h生产求解。

## 5. 为什么小规模结果不能直接外推

以下量会随时域和活跃约束组合非线性变化：presolved rows/columns/NNZ、nested dissection排序、
Factor NZ/Factor Ops、dense columns、Barrier corrector数以及Crossover push长尾。删掉0.05% raw NNZ
可能在某一规模减少fill-in，也可能破坏另一规模的有利消元顺序。因此：

- 24h负结果只否决“直接推广”，不否决744h/2160h验证；
- 744h负结果只否决“凭744h晋级生产”，不构成8760h性能定理；
- 任何长时域复测必须保留物理误差预算、相同窗口、相同线程/算法/容差和独立checkpoint。

## 6. 后续实验序列（单因素、逐级放大）

### E1：2160h CF稀疏化结构/早期Barrier筛选

在当前Case1 Stage B和Case2结束、服务器重新满足内存门禁后，使用相同Base2030、
2160h/start2880、Method2/Threads16/Presolve2/Crossover0、相同容差和CPU绑定，仅比较CF阈值。
先限制相同Barrier步数，比较raw/presolved结构、ordering、Factor NZ/Ops、dense columns、work units、
残差轨迹和RSS。只有候选在结构与轨迹上均不劣、且有明确收益，才运行完整Stage A；仍不得自动Stage B。

### E2：744h/2160h Annual Energy Coordinate单因素A/B

先用744h完整Stage A检查24h的迭代劣势是否持续；若Factor Ops、迭代和时间没有综合改善则停止。
若744h出现稳定收益，再做2160h Stage A，候选必须自产checkpoint。只有Stage A有端到端潜力，
才执行候选Stage B并在原物理单位完成全部QC。

### E3：严格零边界候选放大

先生成完整744h/2160h证书，确认所有置零项均由精确零入流和拓扑闭合推导，不使用经验阈值。
随后按相同Barrier配置比较presolve、退化性、迭代和Crossover长尾。此候选可与科研结果保持等价，
但必须独立测试，不能与E1/E2叠加后再归因。

### 进入8760h前的统一门槛

至少一个候选必须在2160h满足：

1. 等价候选原单位objective及所有hard QC闭合；非等价CF候选则误差预算和目标差单独报告；
2. Stage A与Stage B端到端总时间均可追溯，且相对基线有实质收益；
3. 峰值RSS、Factor NZ/Ops、work units和长尾push数量没有不可接受退化；
4. 不靠放宽FeasibilityTol、OptimalityTol或QC阈值获得“加速”；
5. 使用新输出根和独立checkpoint，不覆盖历史结果。

满足这些门槛后，才准备8760h build/presolve/有限Barrier步结构门禁；完整8760h生产求解仍需单独
资源和运行授权。若744h与2160h的方向相反，应以2160h及8760h结构门禁作为规模趋势证据，不能
选择性只报告有利窗口。

## 7. 工程判定

当前没有可直接部署的数值加速修复，但也没有证据支持永久停止所有候选。最有价值的后续工作是：

1. 保留生产`1e-6`作为科学基线；
2. 在独立资源窗口复测2160h CF稀疏化的规模效应；
3. 并行准备但不叠加Annual Energy Coordinate与严格零边界候选；
4. 用原单位QC和端到端Stage A+B，而非单一Matrix range或前5步时间，决定是否进入8760h。

本文件是当前工程线的权威状态。三个原始worklog保留各次实验当时的事实和命令；若旧worklog的
“否决”措辞与本文件冲突，应解释为“不在该已测规模直接晋级”，不是对所有更大规模的数学外推。

## 8. 整合验证

- `test_lp_equilibration.py`：11/11 PASS；
- `test_exact_zero_reservoir_bounds.py`：9/9 PASS；
- `test_annual_energy_coordinate.py`：6/6 PASS；
- `test_solver_profiles.py`：10/10 PASS；
- 设置现有本地`CISPO_DATA_ROOT`和`CISPO_WAVE_ROOT`后，完整`unittest discover`：
  `243/243 PASS`，76.866秒；
- 关键新增Python脚本`py_compile` PASS，`git diff --check` PASS。

首次不带外部数据根的完整回归出现缺表错误，属于短路径worktree没有复制大型数据包；设置已验证的
只读外部数据根后全量通过。该失败没有被记作代码通过，也没有通过复制或修改原始数据来规避。
