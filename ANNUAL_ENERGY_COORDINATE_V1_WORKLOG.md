# Annual Energy Coordinate V1 隔离候选记录

> 本文件记录该单一候选。跨候选状态、744h结果的外推边界和后续2160h/8760h工程门禁统一见
> `NUMERICAL_STABILITY_ENGINEERING_LINE.md`；代码整合到同一工程分支不表示允许叠加候选。

## 目的与边界

本候选从生产提交 `6065bfba34b76098e86307081323e8545a4d25ac` 建立在独立
worktree/分支 `codex/annual-energy-coordinate-v1`。默认配置仍为物理GWh；只有显式传入
`config/formulation_profiles/annual_energy_coordinate_8192_v1.json` 才启用候选。当前生产
Stage B、服务器数据、求解参数和主工作区均未被修改。

`S = 8192 GWh` 是内部坐标的单位，不是容量上限、需求假设或取整规则。若某年度账户的
物理值为 `9000 GWh`，solver内部保存 `9000 / 8192 = 1.0986328125`；导出和QC前再乘回
8192。因为8192是2的13次方，在当前有限binary64数值范围内，除以/乘以8192本身只是
二进制指数移动，不引入十进制缩放舍入。

## 第二版（当前候选）

第一版曾把VRE、波浪、径流和水库的年度资源发电变量一并缩放。24h/start2880矩阵门禁
立即发现其会把某些极小CF汇总系数从约 `1e-6` 压到 `5.64e-10`，故该版已否决，不能
部署或进入2160h。

当前第二版只缩放以下年度账户和省内年度流量：

- load-center injection/demand/external net import；
- province non-spatial injection/effective demand/sent/received/net import；
- intra-load-center forward/reverse annual flow。

VRE、波浪、径流式和水库年度发电变量、资源可用量行、逐小时CF、逐小时径流/水库入流
全部保持物理坐标，不删小值、不设阈值、不改变数据。省内流量的 `1e-6 million CNY/GWh`
破简并成本在内部变量上乘8192为 `0.008192`，但物理目标完全相同。公开CSV、QC残差均在
物理GWh中计算；checkpoint及原始solver向量显式记录内部坐标合同，禁止与物理坐标
checkpoint混用。

## 已完成验证

输入：Base2030，wave on/flexible load off，24h，start_hour=2880；本地Gurobi 13.0.2。
原版和候选变量/约束/非零元均为 `346767 / 213253 / 1834406`。

| 指标 | 原物理坐标 | 当前8192候选 |
|---|---:|---:|
| raw Matrix | `1.0262457e-6 .. 6250` | `1.0262457e-6 .. 260.4167` |
| raw Objective | `1e-6 .. 3853.1899` | `0.001004004 .. 3853.1899` |
| raw RHS | `4.3444242e-7 .. 2873.3179` | `4.3444242e-7 .. 517.0825` |
| presolved nonzeros（严格Barrier+Crossover） | 1,372,315 | 1,354,338 |
| Factor NZ / Ops | `6.165e6 / 6.432e8` | `6.104e6 / 6.246e8` |
| 严格求解秒 | 174.979 | 178.807 |
| Barrier / simplex迭代 | 120 / 366,065 | 131 / 370,107 |
| objective（million CNY） | 2,112,716.6766244858 | 2,112,716.6766244858 |
| 最大solution violation | `6.06846e-8` | `6.06846e-8` |
| Kappa（非exact） | `1.2696e6` | `6.5890e6` |

候选严格求解为 `OPTIMAL + solution_qc PASS + manifest complete`，目标与原版binary64数值
相同。原版求解也达到OPTIMAL并写出solve_report，但第一次运行在新增导出辅助函数处触发
NameError，因此原版该根不是完整结果；问题已修复，不能把该根当完整QC证据。

与2160h V3 Stage A相同的宽松参数做24h工程checkpoint时，原版/候选分别为
124/132 Barrier步、10.861/11.503秒；最大原始约束违反4.039/2.573，最大互补违反
6.597e6/1.901e6。两者按设计都不是科学结果。候选改善部分残差，但短时段没有速度收益，
且严格解的非exact Kappa更差；因此不得宣称已改善条件数或收敛。

单元证据：新增6项坐标/代数/微型LP测试通过；设置当前外部data/CF/wave根后，完整
`unittest discover` 为 `223/223 PASS`（75.259秒）。

## 唯一下一阶段A/B

先让当前未改坐标的2160h/start2880 Barrier16 Stage A+B基线完整结束。随后只运行一个候选：

1. 同一Base2030、2160h/start2880、同一Stage A profile、同一线程和容差，唯一增加上述
   formulation profile，生成候选自己的Barrier checkpoint；
2. 候选Stage B必须从候选checkpoint启动，保持同一Stage B profile；禁止复用原版checkpoint；
3. 不同时改算法、容差、线程、数据或内存规则；solver SoftMemLimit仍为空，外部整机95%保护保留；
4. 比较端到端Stage A+B总时间、峰值RSS、raw/presolved结构、Factor NZ/Ops、迭代数、原单位
   objective、全部QC/hard checks和manifest；
5. 只有原单位结果闭合且候选在2160h端到端确有收益才考虑推广。24h结果不支持速度改善，
   所以2160h测试是证伪/验证，不是预设候选必胜；绝不直接启动8760h。
