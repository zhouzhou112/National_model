# CISPO 完整 LP/RUC 模型复现说明

> 目的：在本地复现 `Integrated Modeling for the Transition Pathway of China’s Power System` 补充材料 S4 中的 CISPO 电力系统优化模型。
>
> 本文档供 Codex / 本地 Python + Gurobi 实现使用。请优先将其作为**数学模型规格书**，而不是普通说明文档。实现时不得随意删减约束、改变符号含义或把连续 RUC 改成整数 UC。

---

## 0. 对 Codex 的强制要求

1. **模型类型**：优先复现 CISPO 的连续线性规划 / relaxed unit commitment 版本。所有机组组合变量 `u_tot, u_on, u_su, u_sd, u_load` 默认是连续非负变量，不得改成 binary / integer，除非用户另行要求。
2. **时间分辨率**：每个规划年默认使用完整 8760 小时：`T = {0, 1, ..., 8759}`。不得擅自换成典型日、代表周或抽样小时。工程测试可显式选择连续前 744 小时（1 个月）或 4344 小时（1—6 月），但两者均采用截断区间周期边界，且年度投资成本、碳约束和生物质约束不缩放，只能用于代码与求解器测试，不能作为规划结果。
3. **空间分辨率**：风电、光伏、CSP 的基本决策单元为 0.25° × 0.25° 网格；可识别水电为坝址，清单外常规水电仅作为固定省级聚合容量；储能、火电、核电、DAC 为省级电网层面。
4. **单位与价格基准统一**：功率用 GW，电量用 GWh，CO2 用 MtCO2，成本统一为 2025 年不变人民币（2025 constant CNY），距离用 km，时间步长 `Delta_t = 1 h`，水电流量公式中 `Delta_t = 3600 s`。
5. **不得隐式引入失负荷变量**。CISPO 的负荷平衡是严格等式。如果为了调试必须加入 load shedding，只能作为 debug mode，且必须使用极高罚值并在结果中明确报告。
6. **不得删除备用、惯量、碳约束、储能 SOC 周期约束、输电容量约束**。若因为数据缺失暂时无法实现，必须在代码中显式标记 `TODO_SOURCE_DATA_REQUIRED`，不能静默跳过。
7. **目标函数中所有成本项必须按公式模块化实现**，并输出分项成本：VRE、hydro、thermal/nuclear capex、fuel、startup/shutdown、ramping、storage、inter-grid transmission、spur line、trunk line、DAC、CCS capture、CO2 transport/injection、other。
8. **所有 `max_t` 形式约束应线性化**：不要在 Gurobi 表达式中直接写 `max()`。应改为对每个小时建立一组线性不等式，或预先计算参数。
9. **RUC 索引边界必须严格检查**：涉及 `t-1`、`t+1`、最小启停时间窗口的约束，需要定义初始状态或采用周期边界。不得出现数组越界或默默跳过首尾小时。
10. **优先可复现而非“优化美化”**。第一版代码应忠实实现公式；后续再做速度优化、稀疏化、数据切片。

---

## 1. 集合与索引

### 1.1 电源技术集合

- `WE = {onshore, offshore}`：陆上风电、海上风电。
- `PV = {upv, dpv}`：集中式光伏、分布式光伏。
- `CSP = {csp}`：光热发电。
- `HP = {ror, resvor}`：径流式水电、水库式水电。
- `CP = {coal, coalccs, cchp, cchpccs}`：煤电、煤电 CCS、煤热电联产、煤热电联产 CCS。
- `GP = {gas, gasccs, gchp, gchpccs}`：气电、气电 CCS、气热电联产、气热电联产 CCS。
- `BP = {bio, bioccs}`：生物质、生物质 CCS。
- `NP = {nuclear}`：核电。
- `TP = CP ∪ GP ∪ BP`：所有火电及生物质机组。
- `PT = WE ∪ PV ∪ CSP ∪ HP ∪ TP ∪ NP`：所有电源技术。
- `ST = {BAT, PHS}`：锂电池、抽水蓄能。
- `DAC = {koh_b, mgo_am, ssor, koh_cl}`：直接空气捕集技术。

### 1.2 空间、时间与网络集合

- `g ∈ G`：31 个省级电网；内蒙古作为单一省级区域，不拆分蒙东/蒙西。
- `z ∈ Z_{g,pt}`：省级电网 `g` 内技术 `pt` 的候选空间站点。对风光/CSP 是网格；对水电是坝址。
- `sub ∈ SUB_g`：省级电网 `g` 内满足条件的变电站，通常 ≥220 kV。
- `lc ∈ LC_g`：省级电网 `g` 内负荷中心。
- `Z^{sub}_{g,pt}`：连接到变电站 `sub` 的技术 `pt` 候选站点集合。
- `L^{AC}`：省际交流输电线路集合。
- `L^{DC}`：省际直流输电线路集合。
- `l_{g,g'} ∈ L`：连接省级电网 `g` 与 `g'` 的输电线路。
- `c ∈ C`：潜在 CO2 地质封存场址。
- `r_{g,c}`：省级电网 `g` 到封存场址 `c` 的 CO2 运输路线。
- `t ∈ T = {0,1,...,8759}`：小时级时间步。
- `T_w ⊆ T`：冬季供热时段，用于 CHP 必须在线约束。

---

## 2. 决策变量

除非特别说明，所有变量均为连续非负变量。

### 2.1 风光、CSP、水电容量与出力变量

- `p_{g,z,pt}`：技术 `pt` 在站点 `z` 的优化装机容量，GW。
- `I_{g,pt,t}`：技术 `pt` 在省级电网 `g`、小时 `t` 的并网出力，GW。
- `I^{hydro,agg}_{g,t}`：缺少坝址水力属性的省级聚合常规水电出力，GW；容量外生固定。
- `stoe^{csp}_{g,t}`：省级电网 `g` 中 CSP 热储能等效电能，GWh。

### 2.2 水库水电变量

- `q^{gen}_{g,z,t}`：水库水电发电流量，m3/s。
- `q^{spill}_{g,z,t}`：水库水电弃水流量，m3/s。
- `v_{g,z,t}`：水库库容或库水位等效水量，m3。
- `I_{g,z,resvor,t}`：水库水电站点 `z` 在小时 `t` 的出力，GW。

### 2.3 火电与核电 RUC 变量

- `u^{tot}_{g,pt}`：省级电网 `g` 中技术 `pt` 的优化装机机组数量，unit。
- `u^{on}_{g,pt,t}`：在线机组数量，unit。
- `u^{su}_{g,pt,t}`：启动机组数量，unit。
- `u^{sd}_{g,pt,t}`：停机机组数量，unit。
- `u^{load}_{g,pt,t}`：承担负荷的等效机组数量，unit。

### 2.4 储能变量

- `p_{g,st}`：省级电网 `g` 储能技术 `st` 的功率容量，GW。
- `stochar_{g,st,t}`：储能充电功率，GW。
- `stodis_{g,st,t}`：储能向电网放电功率，GW。
- `stoe_{g,st,t}`：储能存储电量，GWh。
- `sr^{+,char}_{g,st,t}`：储能充电状态提供的向上备用，GW。
- `sr^{-,char}_{g,st,t}`：储能充电状态提供的向下备用，GW。
- `sr^{+,dis}_{g,st,t}`：储能放电状态提供的向上备用，GW。
- `sr^{-,dis}_{g,st,t}`：储能放电状态提供的向下备用，GW。

### 2.5 省内接入与省际输电变量

- `p^{sub}_{g,z,pt}`：站点 `z` 到对应变电站的接入线容量，GW。
- `p^{e,lc}_{g,sub}`：风光组合导致的变电站到负荷中心等效增强容量，GW。
- `p^{lc}_{g,sub}`：变电站到负荷中心主干线总增强容量，GW。
- `p^{AC}_{l}`：省际交流线路容量，GW。
- `p^{DC}_{l}`：省际直流线路容量，GW。
- `f^{AC,→}_{l,t}`：交流线路正向功率，GW。
- `f^{AC,←}_{l,t}`：交流线路反向功率，GW。
- `f^{DC,→}_{l,t}`：直流线路固定方向功率，GW。

### 2.6 DAC 与 CCS 变量

- `p_{g,dac}`：省级电网 `g` 的 DAC 年捕集能力，MtCO2/yr。
- `m_{g,dac}`：省级电网 `g` 中 DAC 技术 `dac` 年捕集 CO2 量，MtCO2。
- `m_{g,c}`：省级电网 `g` 输送到封存场址 `c` 的年 CO2 量，MtCO2。

### 2.7 中间变量

- `I^{local}_{g,t}`：本地发电中用于满足本省负荷的部分，GW。
- `ramp^{up}_{g,pt,t}`：火电/核电向上爬坡量，GW。
- `ramp^{dn}_{g,pt,t}`：火电/核电向下爬坡量，GW。
- `ele_{g,dac}`：DAC 等效小时用电负荷，GW。
- `sr^{+}_{g,pt,t}`：电源技术 `pt` 提供的向上旋转备用，GW。
- `sr^{-}_{g,pt,t}`：电源技术 `pt` 提供的向下旋转备用，GW。
- `sr^{+}_{g,st,t}`：储能技术 `st` 提供的向上旋转备用，GW。
- `sr^{-}_{g,st,t}`：储能技术 `st` 提供的向下旋转备用，GW。

---

## 3. 参数

### 3.1 资源、容量与运行参数

- `cf_{g,z,pt,t}`：风、光、CSP、径流式水电小时容量因子。
- `\underline{p}_{g,z,pt}`：优化年前已装机容量，GW。
- `\overline{p}_{g,z,pt}`：最大可开发容量潜力，GW。
- `q^{in}_{g,z,t}`：水库自然入流，m3/s。
- `\underline{V}_{g,z}`：水库安全下限库容，m3。
- `\overline{V}_{g,z}`：水库设计上限库容，m3。
- `H_{g,z}`：水头，m。
- `eta^{resvor}`：水库发电效率，CISPO 中取 0.85。
- `g_e`：重力加速度，m/s2。
- `rho_h`：水密度，kg/m3。
- `varrho_{pt}`：火电/核电单机容量，GW/unit。
- `f^{load}_{pt}`：承担负荷所需燃料消耗，GJ/GWh。
- `f^{on}_{pt}`：保持在线所需燃料消耗，GJ/GWh。
- `xi^{ccs}_{pt}`：CCS 能耗惩罚或效率损失。
- `eta^{ccs}_{pt}`：CCS 捕集率。
- `\underline{phi}_{pt}`：在线机组最小出力率。
- `\overline{phi}_{pt}`：在线机组最大出力率。
- `delta^{up}_{pt}`：最大向上爬坡率。
- `delta^{dn}_{pt}`：最大向下爬坡率。
- `tau^{up}_{pt}`：最小开机时间，h。
- `tau^{dn}_{pt}`：最小停机时间，h。
- `ef_{pt}`：碳排放因子，MtCO2/GWh。
- `thermcal_{g,bio}`：省级可用生物质燃料量，GJ/yr。
- `\underline{p}_{g,st}`：已有储能功率容量，GW。
- `\overline{p}_{g,st}`：储能容量上限，GW。
- `eta^{char}_{st}`：储能充电效率。
- `eta^{dis}_{st}`：储能放电效率。
- `stodur_{st}`：储能时长，h。
- `zeta^{self}_{st}`：储能小时自放电率。
- `d^{sub}_{g,z,pt}`：站点到最近变电站距离，km。
- `d^{lc}_{g,sub}`：变电站到最近负荷中心距离，km。
- `xi_l`：输电线路单位距离损耗率。
- `d_l`：线路距离，km。
- `eta_l = (1 - xi_l)^{d_l}`：输电效率。
- `dem_{g,t}`：省级小时负荷，GW。
- `rho^{+}_{sr}, rho^{-}_{sr}`：负荷导致的上下备用需求比例。
- `rho^{+}_{vre}, rho^{-}_{vre}`：VRE 不确定性导致的上下备用需求比例。
- `rho^{cap}`：峰值容量裕度比例。
- `lambda_{pt}, lambda_{st}`：容量信用。
- `iota_{pt}, iota_{st}`：惯量常数。
- `iota_0`：当前系统惯量水平。
- `iota^{tol}`：惯量容忍系数。
- `E`：年度净碳排放上限，MtCO2；若 `E < 0` 表示负排放要求。
- `C_c`：封存场址 `c` 年注入能力，MtCO2/yr。
- `eta_{dac}`：DAC 有效封存效率。
- `e_{dac}`：DAC 单位捕集电耗，GWh/MtCO2。
- `h_{dac}`：DAC 单位捕集热耗，GWh/MtCO2。
- `cop`：热泵 COP。

### 3.2 成本参数

生产输入遵循 `config/technoeconomic_price_basis_2025.json` 的
`technoeconomic_2025_cny_v2` 合约。CISPO 原始 2022 年不变人民币轨迹
（包括 2030、2040、2050、2060 各节点）统一乘以 `1.004004`；这只改变共同
价格基准，不改变规划年间的相对技术学习幅度。原始外币参数不对历史人民币
换算值重复使用中国 CPI：核电和省级燃料价格回到 USD 来源值后按
`7.1429 CNY/USD` 换算，波浪能的 2024 EUR 来源值按 `8.1185 CNY/EUR`
换算。效率、热耗、寿命、WACC、比例约束及作为数值破简并项的市内
`0.001 CNY/MWh` 不做价格平减。燃料表体现结构性省际价差并按实值保持至
2060 年，不能解释为 2025 年现货价格预测。

- `kappa^{cap}_{pt}`：电源投资成本，yuan/GW。
- `kappa^{cap}_{st}`：储能投资成本，yuan/GW。
- `kappa^{cap}_{l}`：输电线路投资成本，yuan/(GW·km)。
- `kappa^{cap}_{sub}`：变电站投资成本，yuan/GW。
- `kappa^{cap}_{con}`：换流站投资成本，yuan/GW。
- `kappa^{cap}_{spur}`：接入线投资成本，yuan/(GW·km)。
- `kappa^{cap}_{trunk}`：主干线投资成本，yuan/(GW·km)。
- `kappa^{cap}_{dac}`：DAC 投资成本，yuan/(MtCO2/yr)。
- `chi_{pt}, chi_{st}, chi_l, chi_{spur}, chi_{trunk}, chi_{dac}`：年化系数。
- `kappa^{fom}_{pt}, kappa^{fom}_{st}, kappa^{fom}_{l}, kappa^{fom}_{spur}, kappa^{fom}_{trunk}, kappa^{fom}_{dac}`：固定运维成本。
- `kappa^{vom}_{pt}, kappa^{vom}_{st}, kappa^{vom}_{l}, kappa^{vom}_{dac}`：可变运维成本。
- `kappa^{fuel}_{pt}`：燃料成本，yuan/GJ。
- `kappa^{su}_{pt}`：启动成本。
- `kappa^{sd}_{pt}`：停机成本。
- `kappa^{up}_{pt}`：向上爬坡成本。
- `kappa^{dn}_{pt}`：向下爬坡成本。
- `kappa^{capture}_{ccs}`：CO2 捕集成本，yuan/MtCO2。
- `kappa^{inject}_{ccs}`：CO2 注入成本，yuan/MtCO2。
- `kappa^{transport}_{ccs}`：CO2 运输成本，yuan/(km·MtCO2)。

---

## 4. 目标函数

CISPO 的目标是最小化年度系统总成本：

```math
\min f = C_{vre} + C_{hydro} + C_{thermal\_cap\_vom} + C_{fuel} + C_{su\_sd} + C_{ramp}
+ C_{storage} + C_{trans\_AC} + C_{trans\_DC}
+ C_{spur} + C_{trunk} + C_{DAC} + C_{capture} + C_{CO2\_storage} + O
```

### 4.1 风电、光伏、CSP 年化投资与固定运维成本

```math
C_{vre} =
\sum_{g}\sum_{pt\in WE\cup PV\cup CSP}\sum_{z\in Z_{g,pt}}
\left(\chi_{pt}\kappa^{cap}_{pt}+\kappa^{fom}_{pt}\right)p_{g,z,pt}
```

### 4.2 水电年化投资、固定运维与可变运维成本

```math
C_{hydro} =
\sum_g\sum_{pt\in HP}\sum_{z\in Z_{g,pt}}
\left(\chi_{pt}\kappa^{cap}_{pt}+\kappa^{fom}_{pt}\right)p_{g,z,pt}
+
\sum_g
\left(\chi_{hydro}\kappa^{cap}_{hydro}+\kappa^{fom}_{hydro}\right)
\overline p^{hydro,agg}_g
+
\sum_g\sum_{pt\in HP}\sum_{t\in T}\kappa^{vom}_{pt}I_{g,pt,t}
```

其中 \(\overline p^{hydro,agg}_g\) 为固定的 2025 年省级聚合常规水电容量。当前实现沿用 CISPO 对总装机计收年化 CapEx 与固定运维的会计口径；该项在同一规划年和容量口径下是常数，不表示对既有聚合机组的新增建设投资。

### 4.3 火电与核电投资、固定运维、可变运维成本

```math
C_{thermal\_cap\_vom} =
\sum_g\sum_{pt\in TP\cup NP}
\left(\chi_{pt}\kappa^{cap}_{pt}+\kappa^{fom}_{pt}\right)u^{tot}_{g,pt}\varrho_{pt}
+
\sum_g\sum_{pt\in TP\cup NP}\sum_{t\in T}
\kappa^{vom}_{pt}u^{load}_{g,pt,t}\varrho_{pt}
```

### 4.4 燃料成本

```math
C_{fuel} =
\sum_g\sum_{pt\in TP\cup NP}\sum_{t\in T}
\kappa^{fuel}_{pt}
\left(f^{load}_{pt}u^{load}_{g,pt,t}+f^{on}_{pt}u^{on}_{g,pt,t}\right)
\varrho_{pt}\Delta t
```

### 4.5 启停成本

```math
C_{su\_sd} =
\sum_g\sum_{pt\in TP\cup NP}\sum_{t\in T}
\left(\kappa^{su}_{pt}u^{su}_{g,pt,t}+\kappa^{sd}_{pt}u^{sd}_{g,pt,t}\right)
```

> 实现注意：若输入成本单位为 yuan/GW-start 或 yuan/GW-stop，则需乘以 `varrho_pt`。CISPO 公式中未显式乘 `varrho_pt`，实现时必须根据数据单位判断并记录。

### 4.6 爬坡成本

```math
C_{ramp} =
\sum_g\sum_{pt\in TP\cup NP}\sum_{t\in T}
\left(\kappa^{up}_{pt}ramp^{up}_{g,pt,t}+\kappa^{dn}_{pt}ramp^{dn}_{g,pt,t}\right)
```

### 4.7 储能成本

```math
C_{storage} =
\sum_g\sum_{st\in ST}
\left(\chi_{st}\kappa^{cap}_{st}+\kappa^{fom}_{st}\right)p_{g,st}
+
\sum_g\sum_{st\in ST}\sum_{t\in T}
\kappa^{vom}_{st}\left(stochar_{g,st,t}+stodis_{g,st,t}\right)
```

### 4.8 省际交流输电成本

```math
C_{trans\_AC} =
\sum_{l\in L^{AC}}
\left[\left(\chi_l\left(\kappa^{cap}_l d_l + \kappa^{cap}_{sub}\right)+\kappa^{fom}_l\right)p^{AC}_{l}
+
\sum_{t\in T}\kappa^{vom}_l\left(f^{AC,\to}_{l,t}+f^{AC,\leftarrow}_{l,t}\right)\right]
```

### 4.9 省际直流输电成本

```math
C_{trans\_DC} =
\sum_{l\in L^{DC}}
\left[\left(\chi_l\left(\kappa^{cap}_l d_l + \kappa^{cap}_{con}\right)+\kappa^{fom}_l\right)p^{DC}_{l}
+
\sum_{t\in T}\kappa^{vom}_l f^{DC,\to}_{l,t}\right]
```

> CISPO 原始 `kappa_vom_l` 取 `0.001 yuan/kWh = 1 yuan/MWh`。生产输入按统一价格基准换算为 `1.004004`（2025 CNY/MWh），用于抑制交流线路同小时双向流动，并避免 AC/DC 人工偏好；不能误写为 `0.001 yuan/MWh`。该正成本在常规边际价格下可破除对冲流，但在严格负碳约束导致的深度负节点价格下不构成无条件数学保证。负荷中心网络另设的 `0.001 CNY/MWh` 是纯数值破简并项，不属于 CISPO 经济成本，故不平减。

### 4.10 风光/CSP/水电接入线 spur line 成本

```math
C_{spur} =
\sum_g\sum_{pt\in WE\cup PV\cup CSP\cup HP}\sum_{z\in Z_{g,pt}}
\left[\chi_{spur}\left(\kappa^{cap}_{spur,pt}d^{sub}_{g,z,pt}+\kappa^{cap}_{sub}\right)+\kappa^{fom}_{spur,pt}\right]
p^{sub}_{g,z,pt}
```

### 4.11 变电站到负荷中心 trunk line 成本

```math
C_{trunk} =
\sum_g\sum_{sub\in SUB_g}
\left[\chi_{trunk}\left(\kappa^{cap}_{trunk}d^{lc}_{g,sub}+\kappa^{cap}_{sub}\right)+\kappa^{fom}_{trunk}\right]
p^{lc}_{g,sub}
```

### 4.12 DAC 成本

```math
C_{DAC} =
\sum_g\sum_{dac\in DAC}
\left[\left(\chi_{dac}\kappa^{cap}_{dac}+\kappa^{fom}_{dac}\right)p_{g,dac}+\kappa^{vom}_{dac}m_{g,dac}\right]
```

### 4.13 CO2 捕集成本

```math
C_{capture} =
\sum_g\sum_{pt\in CCS}\sum_{t\in T}
\kappa^{capture}_{ccs}\eta^{ccs}_{pt}ef_{pt}u^{load}_{g,pt,t}\varrho_{pt}\Delta t
```

### 4.14 CO2 运输与注入成本

```math
C_{CO2\_storage} =
\sum_g\sum_{c\in C}
\left(\kappa^{inject}_{ccs}+\kappa^{transport}_{ccs}d_{g,c}\right)m_{g,c}
```

### 4.15 其他技术成本

```math
O = \text{scenario-specific additional annual cost}
```

第一版复现中可以令 `O=0`，但必须保留接口。

---

## 5. 约束条件

## 5.1 风电与光伏出力约束

### S4-2 装机上下界

```math
\underline{p}_{g,z,pt} \le p_{g,z,pt}\le \overline{p}_{g,z,pt},
\quad \forall g,\; pt\in WE\cup PV,\; z\in Z_{g,pt}
```

### S4-3 风光实际并网出力不超过可用出力

```math
I_{g,pt,t}\le \sum_{z\in Z_{g,pt}}cf_{g,z,pt,t}p_{g,z,pt},
\quad \forall g,\; pt\in WE\cup PV,\; t\in T
```

> 弃风弃光可后处理为：
>
> ```math
> Curt_{g,pt,t}=\sum_z cf_{g,z,pt,t}p_{g,z,pt}-I_{g,pt,t}
> ```

---

## 5.2 CSP 出力与储热约束

### S4-4 CSP 装机上下界

```math
\underline{p}_{g,z,csp}\le p_{g,z,csp}\le \overline{p}_{g,z,csp},
\quad \forall g,\; z\in Z_{g,csp}
```

### S4-5 CSP 太阳热收集、储能与发电平衡

```math
\left(stoe^{csp}_{g,t}-stoe^{csp}_{g,t-1}\right)+I_{g,csp,t}
\le
\sum_{z\in Z_{g,csp}}cf_{g,z,csp,t}p_{g,z,csp},
\quad \forall g,\; t\in T
```

### S4-6 CSP 期初期末储能一致

```math
stoe^{csp}_{g,t_0}=stoe^{csp}_{g,t_T},
\quad \forall g
```

### S4-7 CSP 储能容量上限

```math
stoe^{csp}_{g,t}\le stodur_{csp}\sum_{z\in Z_{g,csp}}p_{g,z,csp},
\quad \forall g,\; t\in T
```

---

## 5.3 水电约束

## 5.3.1 径流式水电

### S4-8 径流式水电装机上下界

```math
\underline{p}_{g,z,ror}\le p_{g,z,ror}\le \overline{p}_{g,z,ror},
\quad \forall g,\; z\in Z_{g,ror}
```

### S4-9 径流式水电出力约束

```math
I_{g,ror,t}\le \sum_{z\in Z_{g,ror}}cf_{g,z,ror,t}p_{g,z,ror},
\quad \forall g,\; t\in T
```

### S4-9a 重复河段水量的站间分配

`hydro_stations.csv` 允许多个站点记录映射到同一 `COMID`。GRFR 提供的是河段流量而不是逐站独立来水，因此同一河段扣除环境流量后的可用流量只能计入一次。当前生产规则
`static_capacity_potential_share_v1` 按站点技术容量上限给出静态份额：

```math
s_i=
\frac{\overline p_i}
{\sum_{j:\;COMID_j=COMID_i}\overline p_j},
\qquad
q^{avail}_{i,t}
=
s_i\max\left(q^{out}_{r,t}-q^{env}_{r,m(t)},0\right),
\qquad
\sum_{i:\;COMID_i=r}s_i=1.
```

该分配同时适用于径流式、水库式及两类混合映射，避免同一河段序列被重复用于多个站点。它是保持 LP 线性的保守静态规则：若共享河段中的候选站点未建设，其份额不会自动转移给其他站点，因此需要作为容量权重敏感性而不是实测分水关系解释。

## 5.3.2 水库式水电

### S4-10 水库水电装机上下界

```math
\underline{p}_{g,z,resvor}\le p_{g,z,resvor}\le \overline{p}_{g,z,resvor},
\quad \forall g,\; z\in Z_{g,resvor}
```

对于已建水库水电，容量下界为现有装机；候选坝址允许扩建到数据给定的潜力上界。潜在坝址按论文口径分类：设计容量严格大于 750 MW 作为水库式，其余作为径流式。现有电站因源数据无法提供完整可靠类型，直接采用当前分配标签（GHT 明确标签或 115 MW 代理标签），不因置信度较低而从模型剔除。

```math
\underline{p}_{g,z,resvor}=p^{exist}_{g,z,resvor},
\quad p_{g,z,resvor}\le \overline{p}_{g,z,resvor}
```

### S4-11 水库期初期末库容一致

```math
v_{g,z,t_0}=v_{g,z,t_T},
\quad \forall g,\; z\in Z_{g,resvor}
```

### S4-12 水库库容上下限

```math
\underline{V}_{g,z}\le v_{g,z,t}\le \overline{V}_{g,z},
\quad \forall g,\; z\in Z_{g,resvor},\; t\in T
```

> 数值实现（2026-07-31）：`v_model` 的上限直接写入 Gurobi 变量
> `UB=active_storage_m3/10^6`，不再另建逐站逐小时的单变量
> `v_model <= UB` 行。两种写法的可行域和最优解严格相同；对当前 620 座
> 水库可精确省去 `620|T|` 条原始约束（168 h、744 h、8,760 h 分别为
> 104,160、461,280、5,431,200 条），物理单位导出与 QC 不变。

### S4-13 水库流量转化为发电功率

```math
I_{g,z,resvor,t}
=
q^{gen}_{g,z,t}H_{g,z}\eta^{resvor}g_e\rho_h,
\quad \forall g,\; z\in Z_{g,resvor},\; t\in T
```

> 实现注意：上式需处理单位换算。若 `q` 为 m3/s，`H` 为 m，`g_e` 为 m/s2，`rho_h` 为 kg/m3，则得到 W，需要转为 GW。

> 数值实现（2026-07-07，commit `281f9c7`）：输入、公式说明、结果导出和 QC 继续使用物理单位 `m3/s`、`m3`；LP 内部采用严格等价的缩放变量 `q_model=q_m3s/1000` 和 `v_model=v_m3/1e6`。因此小时水量平衡系数由 `3600` 变为 `3.6`，发电系数同步乘以 `1000`，不改变任何物理流量、库容、发电量或梯级传播关系。

### S4-14 水库水电出力不超过装机容量

```math
I_{g,z,resvor,t}\le p_{g,z,resvor},
\quad \forall g,\; z\in Z_{g,resvor},\; t\in T
```

### S4-15 发电流量与弃水流量不超过可用水量

```math
\left(q^{gen}_{g,z,t}+q^{spill}_{g,z,t}\right)\Delta t
\le
q^{in}_{g,z,t}\Delta t+v_{g,z,t-1}-\underline{V}_{g,z},
\quad \forall g,\; z\in Z_{g,resvor},\; t\in T
```

此处水文 `Delta_t` 应取 3600 s。

> 数值实现（2026-07-31）：周期水量平衡、非负库容、逐小时本地来水、
> 梯级时滞传递和活动库容共同给出每站每小时总泄流的有限数学蕴含上界；
> 发电流量上界还与装机潜力除以流量—功率转换系数取最小值。这些上界作为
> `q^{gen}`、`q^{spill}` 的变量 `UB` 写入，只缩紧原先无穷的搜索域，不删除
> 水量平衡、梯级路由、装机上限或 S4-15 的任何物理含义。实现审计必须记录
> 上界方法、有限性和缩放后的最小/最大值。

### S4-16 省级水库水电出力聚合

```math
I_{g,resvor,t}=\sum_{z\in Z_{g,resvor}}I_{g,z,resvor,t},
\quad \forall g,\; t\in T
```

### S4-17 水库水量平衡

```math
v_{g,z,t}=v_{g,z,t-1}+\left(q^{in}_{g,z,t}-q^{gen}_{g,z,t}-q^{spill}_{g,z,t}\right)\Delta t,
\quad \forall g,\; z\in Z_{g,resvor},\; t\in T
```

当前实现分为两类：

1. 非核心干流水库站仍按站点级独立水量平衡建模，`q^{in}_{g,z,t}` 来自 S4-9a 分配后的站点 GRFR 可用流量。
2. Stage2 推荐核心干流梯级站进入梯级水量平衡。核心范围来自 `hydro_model_2019_stage2_classification_cascade_20260630` 的 5 个推荐梯级组，生成到 `data/hydro/cascade_topology_nodes.csv` 和 `data/hydro/cascade_topology_edges.csv`。每个拓扑节点的自然流量等于该节点全部成员站点经 S4-9a 分配后的流量之和；边的河道传播时滞 `\tau_{u,z}` 由 2019 GRFR 小时 `qout_model_m3s` 按 3 h 倍数做上下游互相关估计，搜索窗上限为 168 h。

2026-07-27 的构建瘦身不删除任何水电站、拓扑源记录、来水、库容、泄流变量或水量平衡：源拓扑仍为 142 个节点、124 条边。仅对已核验为“无入边、无出边且 `model_station_count=1`”的 8 个孤立节点，实施时不再逐小时构造核心梯级行，而是送入上述站点级独立 S4-17 向量化平衡；有效核心梯级站点行因此由 146 变为 138。对这些节点 `U_z=\varnothing` 且本地增量入流等于该站 GRFR 可用流量，故两种写法代数完全相同。若未来源数据出现多站孤立节点，建模会硬失败，禁止静默套用该等价转换。结果 QC 输出保留有效核心行数、124 条边和 8 个转入独立平衡的节点数。

对核心梯级站，模型先从下游节点 GRFR 可用流量中扣除上游节点可用流量的时滞项，得到本地增量入流 `q^{local}_{g,z,t}`，再在优化约束中显式加入上游机组发电流量和弃水流量：

```math
q^{in}_{g,z,t}
=
q^{local}_{g,z,t}
+
\sum_{u\in U_z}
\left(q^{gen}_{g,u,t-\tau_{u,z}}+q^{spill}_{g,u,t-\tau_{u,z}}\right),
\quad \forall z\in Z^{core}_{g,resvor},\; t\in T
```

因此核心梯级水量平衡为：

```math
v_{g,z,t}=v_{g,z,t-1}
+
\left[
q^{local}_{g,z,t}
+
\sum_{u\in U_z}
\left(q^{gen}_{g,u,t-\tau_{u,z}}+q^{spill}_{g,u,t-\tau_{u,z}}\right)
-q^{gen}_{g,z,t}
-q^{spill}_{g,z,t}
\right]\Delta t
```

重复 COMID 的站点先在读取水文序列时统一执行 S4-9a；梯级节点随后汇总其成员站份额并计算本地增量入流和上游到达流量，不再复制河段流量。当前环境流量为 2019 单年 monthly P30 代理；正式 1980-2019 多年 P30 环境流和开环/闭环抽水蓄能水库配对尚未接入。

## 5.3.3 省级聚合常规水电

2025 年末常规水电容量以国家能源局 380 GW 分项为约束。当前可追溯站点容量为 297.8895 GW；其余 82.1105 GW 不具备可核验的坝址、水头、额定流量、库容或 COMID，因此不得伪装成站点，也不得进入 S4-9a 或 S4-17。省级聚合容量只作为固定既有容量：

```math
p^{hydro,agg}_g=\overline p^{hydro,agg}_g,
\qquad
\sum_g\left(
\sum_{z\in Z_{g,HP}}p^{exist}_{g,z}
+\overline p^{hydro,agg}_g
\right)=380\ \mathrm{GW}.
```

Base 中的小时出力受逐月天然可用上限约束：

```math
0\le I^{hydro,agg}_{g,t}
\le
\overline p^{hydro,agg}_g\,cf^{hydro,agg}_{g,m(t)}.
```

`cf^{hydro,agg}_{g,m}` 由同省已识别既有站点的 2019 自然可用出力按容量加权形成，只是逐月代理。Base 中该变量可弃发，但没有跨时段蓄水、梯级耦合、扩张、站点 spur/trunk、向上/向下备用、惯量或容量充裕性信用。省内年度发电按负荷中心年度需求份额分配。

独立情景 `hydro_aggregate_flex_v1` 将同一逐月代理解释为月度电量预算，而不是每个小时均相同的功率上限：

```math
0\le I^{hydro,agg}_{g,t}\le \overline p^{hydro,agg}_g,
\qquad
\sum_{t\in T_m}I^{hydro,agg}_{g,t}
\le
\sum_{t\in T_m}\overline p^{hydro,agg}_g
cf^{hydro,agg}_{g,m(t)}.
```

该表达不增加小时运行变量，只对每个省—月增加一条电量预算约束；截断门禁按所选时段内的同月小时构造预算。情景中的向上和向下备用分别为未利用功率和当前出力，系数均为 1；惯量代理沿用站点级水电的 3 s 装机口径。容量充裕性信用仍为 0，且不增加启停、最小出力、爬坡、库容或跨月水量状态。因此它是“聚合可调水电”敏感性，不是对清单外坝址和水库调度的重建。

---

## 5.4 省内接入线路与变电站到负荷中心增强

## 5.4.1 Spur line：站点到变电站

### S4-18 风光站点接入线容量

```math
p^{sub}_{g,z,pt}\ge p_{g,z,pt}\cdot \max_t\left(cf_{g,z,pt,t}\right),
\quad \forall g,\; pt\in WE\cup PV,\; z\in Z_{g,pt}
```

实现时将 `max_t(cf)` 预计算为参数：

```math
cf^{max}_{g,z,pt}=\max_t(cf_{g,z,pt,t})
```

然后写成线性约束：

```math
p^{sub}_{g,z,pt}\ge cf^{max}_{g,z,pt}p_{g,z,pt}
```

对 CSP 和水电，接入线容量不小于装机容量：

```math
p^{sub}_{g,z,pt}\ge p_{g,z,pt},
\quad \forall g,\; pt\in CSP\cup HP,\; z\in Z_{g,pt}
```

## 5.4.2 Trunk line：变电站到负荷中心

CISPO 原式使用同一变电站下风光聚合后的历史最大等效容量因子：

```math
p^{e,lc}_{g,sub}\ge
\left(\sum_{pt\in WE\cup PV}\sum_{z\in Z^{sub}_{g,pt}}p_{g,z,pt}\right)
\max_t
\left[
\frac{\sum_{pt\in WE\cup PV}\sum_{z\in Z^{sub}_{g,pt}}cf_{g,z,pt,t}p_{g,z,pt}}
{\sum_{pt\in WE\cup PV}\sum_{z\in Z^{sub}_{g,pt}}p_{g,z,pt}}
\right]
```

该式可等价线性化为对每个历史小时 `t` 建立：

```math
p^{e,lc}_{g,sub}\ge
\sum_{pt\in WE\cup PV}\sum_{z\in Z^{sub}_{g,pt}}cf_{g,z,pt,t}p_{g,z,pt},
\quad \forall g,\; sub\in SUB_g,\; t\in T^{hist}
```

> 实现注意：CISPO 文中用于该最大值的历史时段为 1980–2019。若本地只拥有模型年容量因子，可先用模型年 `T` 替代，但必须在代码和结果中标注。

### S4-21 加上 CSP 和水电后的主干线总增强容量

```math
p^{lc}_{g,sub}\ge
p^{e,lc}_{g,sub}
+
\sum_{pt\in CSP\cup HP}\sum_{z\in Z^{sub}_{g,pt}}p_{g,z,pt},
\quad \forall g,\; sub\in SUB_g
```

## 5.4.3 2025 初始 spur/trunk/变电站接口容量

EES 补充材料没有提供 OSM 变电站的额定容量、可接入容量或可用间隔。论文中的 `p^{sub}` 和 `p^{lc}` 是由接入发电容量推导的所需线路/增强容量，不是变电站铭牌数据。因此本项目同时保留以下两套 2025 初值：

论文公式对照值（当前以可用的 2023 小时 CF 代替原文 1980–2019 历史序列）：

```math
\underline{p}^{sub,paper}_{g,z,pt}=p^{exist}_{g,z,pt}\max_t(cf_{g,z,pt,t})
```

```math
\underline{p}^{lc,paper}_{g,sub}=
\max_t\left[
\sum_{pt\in\{onwind,offwind,upv\}}
\sum_{z\in Z^{sub}_{g,pt}}
p^{exist}_{g,z,pt}cf_{g,z,pt,t}
\right]
```

用户指定的保守压力初值（默认）：

```math
\underline{p}^{sub,stress}_{g,z,pt}=p^{exist}_{g,z,pt}
```

```math
\underline{p}^{lc,stress}_{g,sub}=
\sum_{pt\in\{onwind,offwind,upv\}}
\sum_{z\in Z^{sub}_{g,pt}}p^{exist}_{g,z,pt}
```

初始变电站 VRE 接口容量代理取 `\underline{p}^{station,proxy}_{g,sub}=\underline{p}^{lc,stress}_{g,sub}`。该值仅表示“若 2025 已有 onwind/offwind/UPV 同时按铭牌送出时所需的最低接口容量”，不得解释为实测或额定变电站容量。DPV 按论文零接入距离口径视为负荷侧资源，不占用 spur/trunk 容量。

沿海中心点存在技术掩膜与装机类型错配。逐点回退规则为：onwind/offwind 缺少专用小时 CF 时使用同格 `mixed_wind`；UPV 缺少 PV CF 时使用同省最近陆地 PV 格点。所有回退均写入审计字段，不得静默处理。

正式方案采用 337 个市级行政单元代理中心；节点坐标为县级城镇人口加权中心，需求权重为 2022 城市用电省内份额（296 个观测、41 个按省内用电/城镇人口强度插补）。每个风光优化格点或水电站在同省全部 ≥220 kV OSM 变电站中精确选择使“大圆 spur 距离 + 该变电站到最近市级中心 trunk 距离”最小的联合路线。DPV 位于负荷侧，spur/trunk 容量与成本保持为0。原 278 个 Natural Earth 建成区质心及 2019 年 1 km 栅格权重完整保留为 CISPO 复现/敏感性方案。

## 5.4.4 负荷中心年度能量分配与省内500 kV扩容

本层不增加 `lc × hour` 变量。对完整年度，所有量均为 GWh；截短时段只用于代码测试。

风光与站点级水电的实际省级发电量通过年度归属变量分配到空间连接的负荷中心，并受相应点位/电站在选定时段内的可发电量上界约束。省级聚合常规水电因不存在可审计的站点路线，按固定年度需求份额分配，不增加 spur/trunk。火电、核电、生物质、储能充放电、DAC及省际受入电量同样按固定年度需求份额分配。

```math
J_{lc}+\sum_{e\in IN(lc)}F_e
=D^{eff}_{lc}+\sum_{e\in OUT(lc)}F_e+X_{lc}
```

其中 `J` 为年度注入量，`D^{eff}` 为用户负荷、储能充电和 DAC 用电构成的年度有效需求，`X` 为分配给该中心的省际送端电量。省级外送严格闭合：

```math
\sum_{lc\in LC_g}X_{lc}
=\sum_{t}\sum_{l\in OUT(g)}f^{send}_{l,t}
```

省内边只连接同省中心。候选拓扑为每省最小生成树加每节点3个最近邻，共642条无向边。线路容量约束为：

```math
F^{\to}_e+F^{\leftarrow}_e
\le H\rho^{design}\left(\underline K^{2025}_e+K^{new}_e\right)
```

默认 `rho_design=0.5`。该值是显式软假设，必须做敏感性分析。初始容量使用2025同时铭牌压力下的空间平衡代理，不得解释为观测额定容量。

成本采用 EES Table S20 和 Figure S44 的 `AC_500kV` 参数，而非单独的550 kV线路类型：原始 2022 年价为变电站159 yuan/kW、架空线2640 thousand yuan/km；生产输入分别换算为159.636636 yuan/kW和2650.57056 thousand 2025 yuan/km。线路参考传输能力随距离变化。中心间直线距离是工程走廊代理。为保持省级小时平衡与年度中心平衡严格闭合，第一版省内损耗设为0；非零损耗必须先作为附加用电反馈到小时平衡。

省内年度流量采用正、反两个非负变量。内点解可能在已由正流量破简并成本压制的方向上保留极小的互逆数值尘埃；QC 因此显式记录每条边的 opposing minimum flow、全国总量和阈值。当前阈值为 `0.0001 GWh`（每条边 0.1 MWh），仅用于年度负荷中心代理；任一边超过阈值仍为硬失败。该阈值不改变 LP、成本、容量或省际逐小时方向性门禁，也不得用于隐藏具有系统意义的循环流。

---

## 5.5 火电与核电 RUC 约束

## 5.5.1 机组状态转移

### S4-22 状态变量上下界

```math
0\le u^{on}_{g,pt,t},u^{su}_{g,pt,t},u^{sd}_{g,pt,t}\le u^{tot}_{g,pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

> 实现等价化说明（v0.9.41）：保留变量非负下界，但不单独实例化这三组上界行。对周期边界下的每个小时，S4-24 直接蕴含 `u_on,t <= u_tot`，并在前一小时蕴含 `u_su,t <= u_tot`；S4-25 与前述 S4-24 则蕴含 `u_sd,t <= u_tot`。该等价缩减仅在所有技术满足 `min_up_h >= 1`、`min_down_h >= 1` 时有效；实现会在建模前硬校验这些前提。

### S4-23 在线机组动态平衡

```math
u^{on}_{g,pt,t}=u^{on}_{g,pt,t-1}+u^{su}_{g,pt,t}-u^{sd}_{g,pt,t},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

> 实现注意：`t=0` 需要初始在线状态 `u_on_init`，或采用周期条件 `u_on_{t=-1}=u_on_{t_T}`。第一版建议显式输入初始状态；若缺失，则使用周期边界并记录。

## 5.5.2 最小开停机时间

### S4-24 最小开机/停机相关约束之一

```math
u^{on}_{g,pt,t}
\le
u^{tot}_{g,pt}
-u^{su}_{g,pt,t+1}
-
\sum_{k=\max(t-\tau^{up}_{pt}+2,1)}^{t}u^{sd}_{g,pt,k},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

### S4-25 最小开机/停机相关约束之二

```math
u^{on}_{g,pt,t}
\ge
u^{sd}_{g,pt,t+1}
+
\sum_{k=\max(t-\tau^{dn}_{pt}+2,1)}^{t}u^{su}_{g,pt,k},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

> 实现注意：原文公式采用 `t+1`，最后一个小时必须定义边界。不得直接跳过 `t=T_end`。建议封装函数 `next_t(t)` 支持周期边界或终端边界。

## 5.5.3 出力上下限

### S4-26 在线机组最小/最大出力

```math
\underline{\phi}_{pt}u^{on}_{g,pt,t}
\le
u^{load}_{g,pt,t}
\le
\overline{\phi}_{pt}u^{on}_{g,pt,t},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

> 实现等价化说明（v0.9.41）：最小出力行保持显式。最大出力通用行不单独实例化，因为已保留的 S4-29 右端等于 `pmax*u_on - (pmax-pmin)*(u_su+u_sd,next)`，在 `pmin <= pmax` 和启停变量非负时逐行不大于 `pmax*u_on`。实现会硬校验 `pmin <= pmax`，因此此缩减不改变可行域或目标函数。

## 5.5.4 爬坡约束

### S4-27 向上爬坡约束

```math
u^{load}_{g,pt,t}-u^{load}_{g,pt,t-1}
\le
\delta^{up}_{pt}\left(u^{on}_{g,pt,t}-u^{su}_{g,pt,t}-u^{sd}_{g,pt,t+1}\right)
+
\overline{\phi}_{pt}\left(u^{su}_{g,pt,t}-u^{sd}_{g,pt,t}\right),
\quad \forall g,\; pt\in TP\cup NP,\; t\ge 1
```

### S4-28 向下爬坡约束

```math
u^{load}_{g,pt,t-1}-u^{load}_{g,pt,t}
\le
\delta^{dn}_{pt}\left(u^{on}_{g,pt,t}-u^{su}_{g,pt,t}-u^{su}_{g,pt,t-1}\right)
-
\underline{\phi}_{pt}\left(u^{su}_{g,pt,t}-u^{sd}_{g,pt,t}\right),
\quad \forall g,\; pt\in TP\cup NP,\; t\ge 1
```

> 重要：S4-27/S4-28 在原文中存在易混淆符号，尤其是 `u_sd_{t+1}`、`u_su_{t-1}` 项。第一版应按原文实现，并提供 `ruc_formula_variant = "CISPO_original"`。如果出现不可行，需要另设 `ruc_formula_variant = "standard_clustered_RUC"` 进行诊断，但不能替代主复现结果。

### S4-29 考虑启动/停机的最大出力附加约束

```math
u^{load}_{g,pt,t}
\le
\overline{\phi}_{pt}\left(u^{on}_{g,pt,t}-u^{su}_{g,pt,t}-u^{sd}_{g,pt,t+1}\right)
+
\underline{\phi}_{pt}\left(u^{su}_{g,pt,t}+u^{sd}_{g,pt,t+1}\right),
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

## 5.5.5 爬坡成本变量

### S4-30 向上爬坡量

```math
ramp^{up}_{g,pt,t}\ge \left(u^{load}_{g,pt,t}-u^{load}_{g,pt,t-1}\right)\varrho_{pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

### S4-31 向下爬坡量

```math
ramp^{dn}_{g,pt,t}\ge \left(u^{load}_{g,pt,t-1}-u^{load}_{g,pt,t}\right)\varrho_{pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

## 5.5.6 CHP 冬季供热在线约束

### S4-32 CHP 冬季全部在线

```math
u^{on}_{g,pt,t}=u^{tot}_{g,pt},
\quad \forall g,\; pt\in CCHP\cup GCHP,\; t\in T_w
```

## 5.5.7 生物质约束

### S4-33 生物质机组最低在线比例

```math
u^{on}_{g,pt,t}\ge \sigma^{on}_{pt}u^{tot}_{g,pt},
\quad \forall g,\; pt\in BP,\; t\in T
```

CISPO 中 `sigma_on = 0.5`。

### S4-34 生物质装机上限

```math
\sum_{pt\in BP}u^{tot}_{g,pt}\le \overline{u}^{tot}_{g,bio},
\quad \forall g
```

V0719 实现以 `data/biomass/capacity_upper_by_province_year.csv` 为直接输入，对 `bio + bioccs` 施加共享省级上界。表中公式为

```math
\overline{u}^{tot}_{g,bio}
=\max\left(
\frac{thermcal_{g,bio}\eta_{bio}}{3600\,h^{eq}_{bio}},
\underline u^{existing}_{g,bio}+\underline u^{existing}_{g,bioccs}
\right),
```

其中 `eta_bio=0.35`、`h_eq_bio=6132 h`。第二项是既有容量可行性保护；当前只在上海触发。S4-34 与 S4-35 同时保留，分别约束装机规模和年度燃料消耗。

### S4-35 生物质燃料年消耗上限

```math
\sum_{t\in T}\sum_{pt\in BP}
\left(f^{load}_{pt}u^{load}_{g,pt,t}+f^{on}_{pt}u^{on}_{g,pt,t}\right)
\varrho_{pt}\Delta t
\le
thermcal_{g,bio},
\quad \forall g
```

## 5.5.8 核电装机上下界

### S4-36 核电容量约束

```math
\underline{u}^{tot}_{g,pt}\le u^{tot}_{g,pt}\le \overline{u}^{tot}_{g,pt},
\quad \forall g,\; pt\in NP
```

V0719 下界继续使用 GEM committed/pipeline；上界由 `data/thermal/nuclear_capacity_upper_by_year.csv` 读取。全国 2030/2040/2050/2060 上界为 `110/205/300/300 GW`，省级分配先保证不低于管线下界，再按 2050 管线权重分配剩余包络。2030 的 110 GW 是官方规划锚点，2040-2060 是显式研究情景，不应解释为官方目标。

## 5.5.9 CCS 改造配对约束

定义 CCS 与非 CCS 技术配对集合：

```text
CCSpair = {
  (coal, coalccs),
  (cchp, cchpccs),
  (gas, gasccs),
  (gchp, gchpccs),
  (bio, bioccs)
}
```

### S4-37 已有 CCS 容量下界

```math
u^{tot}_{g,pt}\ge \underline{u}^{tot}_{g,pt},
\quad \forall g,\; pt\in CCS
```

### S4-38 CCS/非 CCS 配对组总容量不低于既有容量

```math
\sum_{pt\in Gen}u^{tot}_{g,pt}\ge \sum_{pt\in Gen}\underline{u}^{tot}_{g,pt},
\quad \forall g,\; Gen\in CCSpair
```

其中 `Gen` 是一个二元技术组，例如 `{coal, coalccs}`。

### S4-39 CHP 配对组总容量固定

```math
\sum_{pt\in Gen}u^{tot}_{g,pt}=\sum_{pt\in Gen}\underline{u}^{tot}_{g,pt},
\quad \forall g,\; Gen\in CHP\;\text{pairs}
```

---

## 5.6 储能约束

## 5.6.1 储能容量上下界

### S4-40 储能装机容量

```math
\underline{p}_{g,st}\le p_{g,st}\le \overline{p}_{g,st},
\quad \forall g,\; st\in ST
```

## 5.6.2 充电侧功率与备用约束

### S4-41 充电功率与向下备用不超过功率容量

```math
stochar_{g,st,t}+sr^{-,char}_{g,st,t}\le p_{g,st},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-42 充电后不能超过剩余能量容量

```math
\left(stochar_{g,st,t}+sr^{-,char}_{g,st,t}\right)\Delta t\eta^{char}_{st}
\le
p_{g,st}stodur_{st}-stoe_{g,st,t-1},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-43 充电状态提供的向上备用不超过当前充电功率

```math
sr^{+,char}_{g,st,t}\le stochar_{g,st,t},
\quad \forall g,\; st\in ST,\; t\in T
```

## 5.6.3 放电侧功率与备用约束

### S4-44 放电功率与向上备用不超过功率容量

```math
stodis_{g,st,t}+sr^{+,dis}_{g,st,t}\le \eta^{dis}_{st}p_{g,st},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-45 放电与备用不超过可用 SOC

```math
\left(stodis_{g,st,t}+sr^{+,dis}_{g,st,t}\right)\Delta t
\le
\eta^{dis}_{st}stoe_{g,st,t-1},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-46 放电状态提供的向下备用不超过当前放电功率

```math
sr^{-,dis}_{g,st,t}\le stodis_{g,st,t},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-47 总向上备用不超过储能等效放电容量

```math
sr^{+,char}_{g,st,t}+sr^{+,dis}_{g,st,t}\le \eta^{dis}_{st}p_{g,st},
\quad \forall g,\; st\in ST,\; t\in T
```

## 5.6.4 储能能量约束

### S4-48 SOC 上限

```math
stoe_{g,st,t}\le p_{g,st}stodur_{st},
\quad \forall g,\; st\in ST,\; t\in T
```

### S4-49 期初期末 SOC 一致

```math
stoe_{g,st,t_0}=stoe_{g,st,t_T},
\quad \forall g,\; st\in ST
```

### S4-50 SOC 动态平衡

```math
stoe_{g,st,t}
=
\left(1-\zeta^{self}_{st}\right)stoe_{g,st,t-1}
+\eta^{char}_{st}stochar_{g,st,t}\Delta t
-\frac{stodis_{g,st,t}\Delta t}{\eta^{dis}_{st}},
\quad \forall g,\; st\in ST,\; t\in T
```

---

## 5.7 省际输电约束

## 5.7.1 省际输电容量下界

### S4-51 交流线路容量不低于既有容量

```math
\underline{p}^{AC}_{l}\le p^{AC}_{l},
\quad \forall l\in L^{AC}
```

### S4-52 直流线路容量不低于既有容量

```math
\underline{p}^{DC}_{l}\le p^{DC}_{l},
\quad \forall l\in L^{DC}
```

## 5.7.2 小时输电功率不超过容量

### S4-53 交流正向输电容量

```math
f^{AC,\to}_{l,t}\le p^{AC}_{l},
\quad \forall l\in L^{AC},\; t\in T
```

### S4-54 交流反向输电容量

```math
f^{AC,\leftarrow}_{l,t}\le p^{AC}_{l},
\quad \forall l\in L^{AC},\; t\in T
```

### S4-55 直流固定方向输电容量

```math
f^{DC,\to}_{l,t}\le p^{DC}_{l},
\quad \forall l\in L^{DC},\; t\in T
```

### S4-56 交流线路正反向合计不超过容量

```math
f^{AC,\to}_{l,t}+f^{AC,\leftarrow}_{l,t}\le p^{AC}_{l},
\quad \forall l\in L^{AC},\; t\in T
```

> 当前实现对 AC 保留正反向非负流量并施加上述共享容量约束；对 DC 按 S4-55 **不创建反向变量**。内部变量为 `flow_forward_gw[411,H]` 和 `flow_reverse_ac_gw[48,H]`；结果导出时重建 411 行反向数组并将 DC 行填 0，以保持输出兼容。年度负荷中心代理层只接收省级净外部交换，避免额外的毛进口/毛出口闭合重新诱导小时级对冲潮流。

> 方向性 QC 分为两个不可混淆的范围。`SCIENTIFIC_PRODUCTION` 全年结果继续要求所有 AC edge-hour 在 `1e-6 GW` 容差以上严格零对冲，DC 反向流也严格为零。`TEST_ONLY_TRUNCATED_HORIZON` 工程门禁允许把极小系统影响的 AC 对冲流降为显式 warning，但必须同时满足配置中的七重预算。当前每 168 h 参考预算为：最多 8 个 edge-hours、单小时较小方向不超过 `0.25 GW`、不超过线路容量 `15%`、累计较小方向电量不超过 `1.25 GWh`、额外损耗不超过 `0.04 GWh`、累计较小方向占毛输电量不超过 `5e-5`、额外损耗占系统负荷不超过 `1e-7`；前三项中的小时计数以及两个绝对电量预算随诊断时长线性缩放。任一预算超限仍为 hard fail；warning 的原始流量、额外损耗、限额和适用范围全部写入 `solution_qc.json`，不能重标为严格单向，也不能用于年度科学结论。

---

## 5.8 电力负荷平衡

CISPO 负荷平衡在省级电网 `g` 与小时 `t` 层面闭合。

### 5.8.0 Base 与独立需求柔性情景

运行时负荷表同时保存 `base_residual_gw`、`heating_gw`、`cooling_gw` 和 `ev_gw`，并硬校验四分量逐省逐时之和等于 `dem_{g,t}`。Base 直接使用 `dem_{g,t}`，不创建任何柔性变量。历史 V3 覆盖 `flexible_load_comfort_v3_v2g_5pct.json` 在 Base 上使 `features.flexible_load=true`；供暖、制冷和 EV 充电分别引入非负上调、下调变量：

\[
d^{x,act}_{g,t}=d^{x,base}_{g,t}+d^{x,+}_{g,t}-d^{x,-}_{g,t},
\qquad x\in\{heat,cool,EV\}.
\]

V3 冷热功率包络由 `Power_curve_V2` BAIT/balance-point 公式的 `+/-1 C` 舒适区间生成；
冷热等效库存采用逐日因果转移、日首/日末为零，分别使用 4/5 h 时长和 0.94/0.92 小时
保留率。EV V1G 以无序充电基线为服务需求，加入非负因果待充队列和 12 h 聚合服务期限；
`ev_hour_weight` 不能解释为接桩可用率。

可选 V2G 不是重复计算驾驶用能，而是在上述 EV 服务上叠加日内循环虚拟储能：

\[
e^{EV}_{g,t}=\lambda e^{EV}_{g,t-1}+\eta_c p^{V2G,c}_{g,t}
-p^{V2G,d}_{g,t}/\eta_d,
\]

日首与前一日末在各自然日内部循环；V2G 功率上限为各省每日基线 EV 峰值的 5%，并与
V1G 共用电网充电功率上限。有效负荷为：

\[
d^{eff}_{g,t}=d^{base}_{g,t}+d^{heat,act}_{g,t}+d^{cool,act}_{g,t}
+d^{EV,act}_{g,t}+p^{V2G,c}_{g,t}-p^{V2G,d}_{g,t}\ge0.
\]

移峰吞吐与 V2G 充放电吞吐均进入目标函数。小时功率平衡、备用、惯量和年度负荷中心闭合使用 `d^{eff}`；规划容量裕度仍使用 Base 峰值，且需求柔性不提供备用或容量信用。该处理故意保守，并防止未校准的需求侧参数削弱可靠性边界。V3 的热工、车辆连接率、可用电池、出发 SOC 和响应成本仍属历史敏感性假设，不得作为 CISPO 原始参数引用。

### 5.8.0a V4 数据支撑型冷热与 EV 服务库存

`flexible_load_comfort_v4_v1g` 是独立的工程中心情景，`flexible_load_comfort_v4_v2g_sensitivity` 仅作 V2G 敏感性；二者都不是 Base，也不能与 Base/V3 互用 basis。V4 最大限度复用既有 `Power_curve_V2` 结果：不可变负荷表给出逐省逐时冷热/EV 基线，已审计的 BAIT `+/-1 C` 表给出冷热功率包络。中心情景把该包络分别乘以供暖 25%、制冷 20% 的明确参与率。

冷热服务库存为非负连续状态：

\[
S^{c}_{g,t}=\rho^c_g S^{c}_{g,t-1}
 +\eta^{c,+}_g P^{c,+}_{g,t}
 -P^{c,-}_{g,t}/\eta^{c,-}_g,
\qquad c\in\{heat,cool\},
\]
\[
0\le S^{c}_{g,t}\le H^c_g K^c_g,\qquad
0\le P^{c,+}_{g,t},P^{c,-}_{g,t}
\le \min(\bar P^c_{g,t},K^c_g).
\]

状态首尾在所选时域上周期连接，不再使用逐日 reset，也不允许负值“舒适债”；因而削减负荷必须由更早的预热或预冷支撑。只有 8,760 h 求解才可解释为年度科学结果，1 h/24 h/168 h 仅是工程门禁。

EV 基线按 `f^{smart}=0.25` 拆为不可调部分和可调服务：

\[
L^{EV,fixed}_{g,t}=(1-f^{smart})L^{EV,base}_{g,t},\qquad
E^{service}_{g,t}=\eta_c f^{smart}L^{EV,base}_{g,t},
\]
\[
S^{EV}_{g,t}=S^{EV}_{g,t-1}
+\eta_cP^{smart}_{g,t}
-P^{V2G}_{g,t}/\eta_d
-E^{service}_{g,t},
\]
\[
L^{EV,act}_{g,t}=L^{EV,fixed}_{g,t}+P^{smart}_{g,t}.
\]

中心服务库存上限为一天的可调服务量，充电功率上限取可调基线与其逐日平均值两倍中的较大者。`P^{smart}=f^{smart}L^{EV,base}`、`P^{V2G}=0`、`S^{EV}=0` 时严格复现原 EV 基线。现有数据不含车辆接桩会话、行程链或出发 SOC，因此 V4 不虚构这些观测量；`connected_vehicle_fraction=1` 仅为服务归一化，`minimum_departure_energy_gwh=0` 为兼容旧 schema，EV 状态应解释为聚合可调服务库存而不是物理车队 SOC。

所有参与率、状态时长/保留率和响应成本均有中心/低/高登记；它们是可直接运行的工程情景假设，不是已观测的中国省级校准值。V1G 是中心情景，V2G 仅独立敏感性；二者均不提供容量、备用或惯量信用。完整公式、来源映射与输入生成/校验合同见 `config/FLEXIBLE_LOAD_V4_CALIBRATION_CONTRACT.md`。

### 5.8.0b V5 集成需求柔性与数值等价稀疏化

正式比较集只保留不可变 Base 与一个集成中央反事实。Base 不创建需求柔性变量；`flex_integrated_v5_central` 同时启用数据支撑的冷热服务包络、付费 V1G、内生付费 V2G 合同及折减后的 firm-flexibility capacity credit。中央 V1G 仅把不可变 EV 充电基线的 15% 作为可调服务，其余 85% 固定；V2G 合同满足

\[
0\le K^{V2G}_g\le K^{V1G}_g,\qquad
\sum_g K^{V2G}_g\le \overline K^{V2G}_y,
\]

且共享同一批签约充电接口：

\[
P^{charge}_{g,t}+P^{discharge}_{g,t}
\le a^{EV}_{g,t}K^{V1G}_g,\qquad
P^{discharge}_{g,t}\le a^{EV}_{g,t}K^{V2G}_g.
\]

该聚合车队包络允许不同车辆同时充、放电，但禁止充电与放电分别占满两套嵌套合同而重复使用双向接口；实现上以该行替换原充电单向合同，不增加逐小时约束数量。V2G 分别支付年度可用性、双向基础设施、车主参与及放电退化成本。V1G 也不是免费资源：合同容量支付年度控制/聚合成本，原无序充电基线被向下移走的电量支付激活成本。额外用于补偿 V2G 放电损耗的充电不重复计入 V1G relocation。

V5 不使用可由模型自由压低的内生 effective peak 替换容量裕度峰值。容量充裕性仍以完整 8,760 h 不可变 Base 各省峰值为右端，仅允许合同容量、峰值四小时窗口可交付功率/能量包络及透明 derating 共同限定的 firm credit：

\[
C^{supply}_g+\sum_{s\in FLEX}F^{firm}_{g,s}
\ge (1+m)\max_{t\in T_{8760}}L^0_{g,t}.
\]

冷热、V1G 与 V2G 的中央 derating 分别为 0.60、0.60、0.50 和 0.50；这些是需做范围敏感性的工程假设，不是中国省级 ELCC 估计。需求柔性不获得备用或惯量信用。完整参数、来源和确定性输入合同见 `config/FLEXIBLE_LOAD_V5_CONTRACT.md`。

生产构模只允许数学等价的结构稀疏化。逐省逐时控制变量仅在经校验的物理上界严格大于零时创建。冷热状态只在上调或下调具有正物理上界的小时及少量纯衰减锚点创建。若相邻保留节点为 \(t_{i-1}\) 和 \(t_i\)，两者间控制严格固定为零，则原逐小时递推被精确消元为

\[
S_{g,t_i}=\rho_g^{\Delta_i}S_{g,t_{i-1}}
+\eta^{in}_gP^{up}_{g,t_i}
-P^{down}_{g,t_i}/\eta^{out}_g,\qquad
\Delta_i=(t_i-t_{i-1})\bmod |T|.
\]

纯衰减锚点保证所有保留转移系数不低于 0.1；未显式创建的小时按 \(S_{g,t_i+k}=\rho_g^kS_{g,t_i}\) 解后重建。由于 \(0<\rho_g\le1\) 且状态上界在所选时域内不随小时变化，中间状态的非负下界和上界均由前一保留节点蕴含，因此该消元不改变可行域。上下调上界在完整时域恒为零的省份不创建任何对应状态节点。

`minimum_departure_energy_gwh=0` 的兼容行不进入 LP。V5 目标函数使用单边 V1G relocation，因此不参与目标或任何约束的双边 charge-deviation epigraph 从 LP 删除，其绝对偏差仅在解后重建。仅当所有控制变量的保守界共同证明

\[
\underline L^{eff}_{g,t}>10^{-6}\ {\rm GW}
\]

时，才省略该单元的 \(L^{eff}_{g,t}\ge0\) 行；否则保留显式约束。上述删减不改变可行域、目标函数、输出单位或 QC 重建。

未压缩的周期冷热状态在长时间零控制区间内会被自动 presolve 逆向消去并累积大系数。runner 因此在建模前和建模后分别审计原链风险、稀疏状态表示和 solver contract，二者不一致即拒绝 `optimize()`。状态精确消元后允许继续使用自动 aggregation。Gurobi 13+ 的主生产路线 `barrier_16_nonbasic_primal_dual_v1` 使用 `Method=2`、`Crossover=0`、`SolutionTarget=1`、`BarConvTol=1e-10`，只接受同时满足 `OPTIMAL` 与严格 primal/dual violation 门禁的非基内点解，影子价格读取 `BarPi`。该 profile 本身不生成/复用 basis，禁止 scientific `.bas`、直接 MGA 和 basis warm start；但严格接受且 checkpoint 闭合的容量解可由 planning sequence 显式登记为下一规划年的 cohort state。任何非 `OPTIMAL` 或质量门禁失败的解都不得进入科学输出、dashboard、planning state 或 result manifest。Gurobi 12 的同参数路径存在已知 suboptimal unscaling 风险，profile 因而显式拒绝 13 以下版本。`Aggregate=0` 保留为未来矩阵审计再次发现系数放大时的保守回退，而不是默认生产设置。任一路线只有通过匹配 1 h、24 h、168 h 和授权长时域门禁后才能升级，不能仅凭 Barrier 日志或 presolve 结果称为 production。

自 2026-08-01 起，默认求解合同改为 **Barrier-first**，但不放松科学验收：主阶段必须使用 `Method=2`、`Crossover=0`、`SolutionTarget=1`，只有最终 `Status=OPTIMAL`、严格 primal/dual quality contract、完整 `solution_qc=PASS`、全部 hard checks、当前 input manifest 与有效 result manifest 同时闭合，才接受内点解。通过后，runner 正常导出容量、逐小时运行、成本、碳/CCS 和 `BarPi` 影子价格，并保存按原 LP 顺序排列的 `BarX`/`BarPi` 检查点；744 h 及以下用 `--export-barrier-checkpoint` 显式启用，长于 744 h 自动启用。检查点不含 presolve 消元或 Barrier factorization，约 8760 h 原始向量本体的 float64 规模约为变量数与约束数之和乘以 8 bytes，导入时仍可能额外物化 Python Gurobi 对象列表。

跨年主线不等待 Crossover。`run_cispo_planning_sequence.py` 对 nonbasic profile 显式传入 `--export-barrier-checkpoint --allow-nonbasic-planning-state`；只有 accepted checkpoint 存在时才写出 `planning_state`。`state_metadata.json` 记录 `source_solution_contract_mode`、checkpoint SHA256、`ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE` 策略、cohort 截断阈值及被忽略的微小容量统计。这里继承的是一个满足全部约束且达到最小成本的容量解；它在多重最优空间中可能比极点解更弥散，因此论文应把 sequential cohort policy 作为方法定义，而不能暗示该容量分布唯一。截断时域导出的 state 仍为 `TEST_ONLY_TRUNCATED_HORIZON`，绝不能冒充正式年度 anchor。

Crossover 是全部主线 case/year 完成后由作者选择的独立派生任务，而不是年度门禁。它必须重建完全相同的 LP，逐层核对 baseline/analysis case、implementation bundle、data roots、input manifest、规划年、窗口、Gurobi `Fingerprint`、变量/约束/非零元数及检查点 SHA256，再把全量 `BarX/BarPi` 分别作为 `PStart/DStart` 注入，使用 `LPWarmStart=2` 将 start 映射到 presolved model 后执行 `Crossover=1/CrossoverBasis=1`。该阶段用于生成 `VBasis/CBasis`、`.bas`、basis sensitivity range 和可供 MGA 工程复用的 basic solution；容量、调度、成本、碳核算、`BarPi` 影子价格和连续 LP 的 reduced cost 本身不以 Crossover 为前提，但退化问题中的 dual/reduced-cost 可能不唯一。后置 Crossover 不写新的 `planning_state`，不得回溯改写已完成的跨年路径，其失败也不得撤销主阶段已经接受的科学结果。旧式同进程 Crossover 在超过 744 h 时默认被 runner 拒绝，只有显式 `--allow-inline-crossover` 才可作为诊断运行；若 Gurobi 13 已记录 `BarStatus=OPTIMAL` 后整体超时，runner 尝试保存 `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT` 原始检查点，但它没有完整 QC，不能被重标为科学接受结果。

#### 2026-08-05 solver-route 实证更正

上文 Barrier-first 是 2026-08-01 提出的**设计目标**，不是当前已验证生产路线。随后在当前模型 24 h Base 上完成的 20 个 `Method=2/Crossover=0/SolutionTarget=1` 参数组合均未同时通过严格原始 primal/dual 门禁：典型最大 constraint violation 为 `4.26e-2`；即使 `PreDual=1` 将 constraint violation 降至约 `7.60e-8`，dual violation 仍为 `1.29e-5`。因此当前可运行的截断时域 profile 是经 24 h/168 h 配对后冻结的 `barrier_16_crossover2_stable_basis_long_v1`，不是 Barrier-only profile。

2026-08-05 三季节 744 h Base 的终态又为 `9/12 accepted + 2 Crossover TIME_LIMIT + 1 not run`。这既证明 `Crossover=2` 能接受多数 744 h 根，也证明它不能未经更长门禁直接外推到 8760 h。两个超时根虽为 `BarStatus=OPTIMAL` 并保存 recovery-only `BarX/BarPi`，但没有 QC、result manifest 或 accepted planning state，不能反向证明 Barrier-only 已可用。**当前没有任何已验证的 8760 h production solver route，正式年度求解不得启动。**

恢复年度路线前，必须先对 recovery `BarX/BarPi` 做 exact-LP 原始 primal/physical/dual 离线审计，再以最小容差候选完成 24 h→168 h→单根 744 h A/B。只有最终 `OPTIMAL`、宏观结果稳定、全部 QC/hard checks/manifests 闭合且端到端效率可接受的路线，才能升级到 8760 h preflight。大于 744 h 的 inline Crossover 继续默认禁止；recovery-only checkpoint 不得重标、续年或解释为科学影子价格。

#### 2026-08-05 作者批准的 8760 h 两阶段覆盖合同

作者随后明确选择“先保全昂贵 Barrier 内点、再按需独立 Crossover”的年度工程架构。本节覆盖
上文“Stage A 必须先成为科学 accepted 主结果”以及“后置 Crossover 只能是无 state 派生物”
的旧设计，但不覆盖物理、成本、数据、QC、manifest 或科学解释边界。

Stage A `barrier_checkpoint_full_year_cloud_v1` 使用
`Method=2/Threads=16/Presolve=2/Crossover=0/SolutionTarget=1/BarConvTol=1e-9/
FeasibilityTol=OptimalityTol=1e-7/NumericFocus=2/ScaleFlag=2/Aggregate=1/
DualReductions=1/InfUnbdInfo=0/TimeLimit=604800/SoftMemLimit=600`。它是明确的工程检查点任务，
不因 Gurobi 最终 `Status=OPTIMAL` 而自动升级为科学结果。runner 必须在任何大规模科学导出和
物理 QC 前优先读取并保存原始 LP index order 的 `BarX/BarPi`；可复用检查点至少要求 Gurobi 13
`BarStatus=OPTIMAL`、两个向量长度正确且全为 finite、input manifest 当前有效、运行身份完整。
manifest 记录完整 baseline/analysis/implementation/data/lp identity、scenario/solver config SHA256、
predecessor planning-state path、Gurobi version、Fingerprint、变量/约束/非零元数，并对完整
`VarName` 顺序与 `ConstrName+Sense` 顺序分块计算 SHA256。检查点身份固定为
`ENGINEERING_BARRIER_CHECKPOINT_ONLY`、`scientifically_accepted=false`；raw `BarPi` 可以保留
为工程 shadow-price 向量并用于后续 DStart，但不得进入论文价格、planning state、MGA、dashboard
或 scientific result manifest。若 `BarStatus` 不为 OPTIMAL 但至少完成一次 Barrier iteration，runner
应尽力把当前可读取的完整有限 `BarX/BarPi` 保存为 `INCOMPLETE_BARRIER_RECOVERY_ONLY`；它只用于
故障取证，`deferred_crossover_eligible=false`，不能续接 Stage B。若向量不可读、不完整/不有限或写出
失败，仍记录显式 export error。上述情况均表示 Stage A 未完成；recovery 或中间日志不能替代可复用
检查点。

Stage B `deferred_crossover2_full_year_cloud_v1` 必须从头重建完全相同 LP。Stage A 与 Stage B
必然使用不同 solver profile，因此 resume identity 只从 `input_manifest.csv` 排除恰好一行
`solver_configuration`；configuration、scenario、formulation、planning state、全部数据文件及其
size/SHA256 仍逐行一致。继续核对 baseline/analysis/scientific/data/lp identity、Fingerprint、LP
dimensions、完整变量/约束顺序 SHA256 及 checkpoint 文件 SHA256。若 Git/source bundle 改变，默认
仍 fail-closed；只有显式 `--allow-compatible-primal-dual-implementation` 才能进入后续 exact-LP
Fingerprint/order 复核，且该授权及 source/target bundle 必须写入 `primal_dual_start_input.json`。
工程源还需显式授权；随后设置全量 `variable.PStart=saved_bar_x`、
`constraint.DStart=saved_bar_pi`、`LPWarmStart=2`，使用
`Method=2/Crossover=2/CrossoverBasis=1/SolutionTarget=0` 直接在 presolved crushed starts 上
执行 Crossover，不重复 Barrier。只有 Stage B 达到 `Status=OPTIMAL`、strict ConstrVio/BoundVio/
DualVio、`solution_qc=PASS`、全部 hard checks（当前 Base 合同为 58/58）、current input manifest、
valid result manifest、标准 `Pi` 导出和 wrapper/time 闭合，才是年度科学结果。此时它是 canonical
basic result，而不只是附属分析；经单独显式许可可导出下一规划年的 planning state。Stage B
失败不损坏 Stage A，但不得重标失败解或手工补 manifest。

`data_roots` 默认逐键精确一致。唯一已审计例外是 `CISPO_RAW_GRFR_ROOT`：它在 current solve package
中是 readiness/provenance 环境根，旧 checkpoint 创建 shell 可能未设置。只有 source/target 已分别通过
manifest validation、排除 solver 行后的 77 行科学 manifest 逐字段/SHA 完全相同，并且两端 manifest
在各自声明的 RAW_GRFR root 下消费文件数均为 0 时，才允许该可选根的 `null`/路径差异；差异、两端
使用计数和 allowlist 必须写入 `primal_dual_start_input.json`。任何被消费根不同，或任何非 allowlist
根即使暂未消费也不同，仍在 optimize 前 fail-closed。

所有 `barrier_checkpoint_full_year_cloud_*` 与 `deferred_crossover2_full_year_cloud_*` profile 版本均由
runner 按前缀分别识别为 Stage A/Stage B，而不是只硬编码 v1。前者强制
`--engineering-barrier-checkpoint-only`，后者强制 `--primal-dual-checkpoint-in`，二者都禁止用于截断
时域。新增 v3/v4 等版本不能因遗漏 allowlist 而绕过全年与阶段边界。

两阶段均保留严格物理 QC，不以 `BarConvTol` 代替原模型可行性/dual 验收。`BarConvTol=1e-9`
相对默认 `1e-8` 的意义是提高内点精度并可能缩短 Crossover，而不是保证任意超大 LP 必然得到
`BarStatus=OPTIMAL`。`FeasibilityTol/OptimalityTol` 主要约束 simplex/crossover 的最终可行性；
`CrossoverBasis=1` 以更高初始 basis 构造成本换取数值稳定性；`Crossover=2` 表示 dual push、
primal push、dual-simplex cleanup。该架构的代码/小模型契约已经 Gurobi 13.0.2 验证，但尚未执行
8760 h，因此仍不能把它描述为已有年度科学结果或已实测年度性能。

#### 2026-08-17 大尺度参数实证与正式 v3 profile 覆盖

2026-08-17 的 current-model 配对实验覆盖 strict Base/744、relaxed Base/744、V5/744、Base/1488、
Base/2160 memory boundary、两批同 identity 5-iteration factor screens，以及 exact deferred
Crossover/744。证据表明 Stage A 不宜继续沿用上节未经大尺度实证的 `BarConvTol=1e-9`：当前
`barrier_checkpoint_full_year_cloud_v3` 冻结为 `Method=2/Threads=16/Presolve=2/Crossover=0/
SolutionTarget=1/BarConvTol=1e-2/FeasibilityTol=OptimalityTol=1e-5/MarkowitzTol=0.01/
NumericFocus=1/ScaleFlag=2/Aggregate=1/DualReductions=1/InfUnbdInfo=0/no TimeLimit/
SoftMemLimit=600 GiB`。它只产生 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，必须保存完整 finite raw-order
`BarX/BarPi`、identity、残差、资源和时间；不得产生 scientific result manifest、accepted planning state
或论文影子价格。

配套 `deferred_crossover2_full_year_cloud_v3` 冻结为 `Method=2/Threads=16/Presolve=2/
Crossover=2/CrossoverBasis=1/LPWarmStart=2/SolutionTarget=0/FeasibilityTol=OptimalityTol=1e-6/
MarkowitzTol=0.01/NumericFocus=2/ScaleFlag=2/Aggregate=1/DualReductions=1/InfUnbdInfo=0/
no TimeLimit/SoftMemLimit=600 GiB`。其 `BarConvTol=1e-8` 仅为完整 numerics 记录；exact PStart/DStart
路线不得重跑 Barrier。Base/744 已实证 Barrier 0、`OPTIMAL + solution contract PASS + QC PASS 58/58 +
valid manifests + finite Pi + macro pair PASS`，Stage A+B 合计 solver/wall 为 `6,938.338 s/2:08:24.08`，
相对 strict inline 路线约加速 `7.71×/6.99×`。该结果仍是 `TEST_ONLY_TRUNCATED_HORIZON`，只批准未来
全年工程架构与参数文件；不授权自动提交 8760 h、当前 cloud Stage B、下一规划年或第二并发任务。

#### 2026-08-27 作者要求：Stage A 完整保存与结果采用解耦（待实现）

本节覆盖上文将工程 Stage A、QC FAIL 或非 accepted checkpoint 排除在结果文件、结果清单及容量
状态**保存**之外的限制；不修改模型、输入、单位、目标、约束、数值阈值或历史求解身份，也不授权
自动科学接受、自动 Stage B 或自动跨年。状态为 `AUTHOR_REQUIRED_EXPORT_POLICY_PENDING_IMPLEMENTATION`。

1. **先保全**：优先写出可读取的原始 primal/dual checkpoint，再保存完整容量、逐时运行、成本分项、
   碳/CCS 核算、原始对偶及其变量/约束语义映射。不得因某个 QC 失败而中断其他可导出模块。
   必须产生 `solution_qc.json`、`result_manifest.json` 和候选跨年容量状态，明确每类数据的覆盖范围、
   单位、源 checkpoint/模型/数据身份及 SHA256。文件清单验证通过只表示完整性/一致性，不代表结果可用。
2. **如实评价**：保存每个检查的状态、阈值、实测违反量、可定位的行/变量及物理单位；无法检查的项
   标为未完成并说明原因。QC FAIL 不是丢弃文件的条件，未知状态不能写成 PASS。若无可读取解、部分
   数据缺失、写盘失败或进程被强杀，只能尽力保全已有内容并标记 partial/error，不能宣称完整。
3. **候选 state 与采用分离**：候选状态必须保存原始容量变化、资产类别/标识、建造与退役年份、单位、
   前序状态和转换规则；完整保留微小或负值及其诊断，不静默裁剪/省略。既有 accepted state 的 cohort
   tolerance 不得导致候选原值丢失；如提供兼容的筛选视图，须另存并记录差异。作者以后可选择该候选
   继续实验，读取接口必须显式记录选择及上游未通过项；该选择不改变原始 QC，也不自动升级论文证据。
4. **结果身份分轴记录**：产物完整性、solver/physical QC、科学验收及作者采用决定是不同字段。新 schema
   必须可表达“导出完整、QC FAIL、科学未接受、作者待决定”；不能借生成 `result_manifest.json` 冒用
   accepted 标记。老的 accepted state 读取接口保持兼容，未经作者选择不自动消费候选状态。
5. **Stage B 可选**：Stage A 保存和候选容量状态恢复不等待 Stage B。Stage B 是同年 exact-LP starts
   的独立后处理/求解任务；跨年则是资产 cohort 继承，两者不是同一个续接接口。

对历史 job `4139552`，完整 `BarX/BarPi` 已备份但未持久化完整 name catalog。恢复需依原源码、配置、
输入和原 LP identity/order 重建语义，再直接从保存向量计算各类输出。默认恢复设计不调用
`optimize/presolve/crossover`；此前“PStart/DStart + 零迭代暴露 `.X`”只能视为未验证试验，不作保证。
恢复结果写入独立根，保持原始 checkpoint 和 `solve_report.json` 不变；完整 QC 与对偶解释可信度待
恢复后评价。当前 runner 和 `PlanningState.load` 尚未实现上述解耦，不得宣称原 `.npy` 已能直接续年。

#### 2026-08-27 14:18 实现状态覆盖

2026-08-28作者授权补充：历史恢复可显式`--allow-fingerprint-mismatch`，在原源码/输入/依赖可追溯、
维度/非零元及完整变量/约束名称与sense顺序核对、向量hash/finite有效的情况下，指纹差异记录为
诊断信息而不阻断候选结果导出。先保存重建模型和映射，原LP残差/QC如实报告，任何不匹配不伪称
exact LP一致或科学接受；普通审计异常也尽量保留语义结果并标PARTIAL。这只调整恢复保全决策，
不修改模型方程/输入/科学阈值，不授权自动Stage B或跨年优化。

上节策略已本地实现，状态为 `LOCAL_VALIDATED_NOT_DEPLOYED`。所有nonbasic Stage A均保存完整可读
结果与候选state，默认原始MPS/参数/名称归档；QC FAIL只记录，模块错误标PARTIAL并继续其他模块。
`--allow-candidate-state-in`使作者可显式选择未验收候选进行后续实验，严格保留哈希、年份、资产/单位
和原始QC来源，不自动升级科学结果。旧accepted-only sequence不隐式消费候选；基本解生产路径仍保留。

`--recover-stage-a-from`支持新snapshot及legacy Barrier向量；先核验原输入、Gurobi版本及实现身份，
再核对exact LP指纹/规模/顺序/向量哈希，直接代入原式导出，不做presolve或optimize。原LP全部行与边界
检查另存具名违反清单。presolved诊断副本为可选额外调用，既不是内部uncrush映射，也不是Barrier状态。

Gurobi13.0.2下222项回归及1h在线/离线对照通过；45个结果表/数组、碳和原LP残差一致，候选状态可加载
并构建2040/1h LP。全部为截断测试，不证明历史8760h已恢复、内存峰值已验证或论文结论已接受。
该历史保全机制的运行边界已在本节自包含：必须绑定原模型/输入/顺序/hash、保留raw-order向量和逐项QC，
候选state只能显式选择且不自动升级为accepted；服务器当时尚未部署，活动旧进程行为不变。本规范不依赖
当时未提交的独立说明文档。

#### 2026-09-02 current override：VRE/ROR年度容量连接行的精确左缩放

为尽快获得可在云端实际运行的8760h模型，同时不改变科学可行域，当前唯一允许继续的数值变换为
`annual_capacity_link_rows_8192_v1`。它不是变量换元、CF截断、目标重标度或约束放松，而是对经过
显式登记的VRE与径流式水电（ROR）年度可用量零右端行做正数整行左乘。

对目标族 $f\in\{\mathrm{VRE},\mathrm{ROR}\}$ 的任一登记行 $r$，以物理单位书写为

\[
g_r(x)=E_r-\sum_j H_{rj}K_j\le 0,\qquad
H_{rj}=\sum_{t\in T}cf_{rjt}\,\Delta t .
\]

其中 $E_r$ 是该行汇总的年度发电/交付电量（GWh），$K_j$ 是物理装机（GW），
$H_{rj}$ 是所选时域内由容量因子汇总得到的等效满负荷小时（h）。求解器接收

\[
\tilde g_r(x)=s_f g_r(x)
=s_fE_r-\sum_j s_fH_{rj}K_j\le0,\qquad s_f=2^{-k_f}>0 .
\]

因为右端为零且 $s_f>0$，$g_r(x)\le0\iff\tilde g_r(x)\le0$。因此决策变量、变量边界、
目标函数、行列支撑、约束sense和可行域逐项不变；只改变登记行的数值坐标。Wave容量行经审计没有同类
病态列跨度，省内负荷中心容量行也没有小时极小系数耦合，二者明确排除，不能因名称相似而自动缩放。

族指数由模型实值fail-closed计算：

\[
k_f=\max\left\{k\in\mathbb Z:0\le k\le13,
2^{-k}\min_{a\in A_f,\,a\ne0}|a|\ge10^{-6}\right\}.
\]

登记表必须保存profile、族、constraint prefix、全部constraint names、行数、缩放非零元数、原始/缩放
系数范围和SHA256，并与已建模型的名称、sense、RHS、符号、anchor、nnz及range做深绑定。正式
2160h/8760h合同额外要求VRE与ROR都得到`k=13`（`s=2^-13=1/8192`）；任何缺行、重复行、未登记行
变化、指数不是13、缩放后系数低于`1e-6`或注册表/模型不一致均直接失败，不得回退到部分缩放。

科学解释必须回到原行坐标。设求解器对 $\tilde g_r$ 给出的对偶和松弛分别为
$\pi_r^{solver}$、$slack_r^{solver}$，则

\[
\pi_r^{physical}=s_f\pi_r^{solver},\qquad
slack_r^{physical}=\frac{slack_r^{solver}}{s_f}.
\]

变量仍是物理单位，目标值不缩放；在上述对偶映射下reduced cost不变。所有约束残差、年度可用量、
容量、成本和输出QC必须用原单位计算，不能把solver坐标直接写入论文或跨年状态。

求解合同只保留一条路线：

1. 固定服务器2160h/start2880工程资格运行使用
   `barrier_checkpoint_fixed_server_host_memory_95_v2`与本formulation profile，参数为
   `Method=2/Threads=32/Presolve=2/Crossover=0/SolutionTarget=1/BarConvTol=1e-2/
   FeasibilityTol=OptimalityTol=1e-5/MarkowitzTol=0.01/NumericFocus=1/ScaleFlag=2/Aggregate=1/
   DualReductions=1/InfUnbdInfo=0`，无`TimeLimit`，并设置`host_memory_soft_limit_fraction=0.95`及整机95%
   保护。profile中的`soft_mem_limit_gb=80`只作fallback/provenance；runner将有效Gurobi
   `SoftMemLimit`覆盖为`physical_memory_bytes*0.95/1e9`十进制GB。
2. 8760h Stage A使用`barrier_checkpoint_full_year_cloud_v4`，固定`Threads=32`、`Method=2`、
   `Presolve=2`、`Crossover=0`、`SolutionTarget=1`、`BarConvTol=1e-9`、`FeasibilityTol=1e-9`、
   `OptimalityTol=1e-8`、`MarkowitzTol=0.01`、`NumericFocus=1`、`ScaleFlag=2`、`Aggregate=1`、
   `DualReductions=1`、`InfUnbdInfo=0`、`soft_mem_limit_gb=600`，无`TimeLimit`。32线程是作者
   根据既有全年证据作出的资源选择，短时域线程吞吐不构成否决依据。
3. Stage A checkpoint必须按raw order校验变量/约束数量、名称顺序、dtype、shape、finite、bytes与SHA；
   promotion前`BarX==X`、`BarPi==Pi`须逐项binary64精确成立。accepted结果还必须满足OPTIMAL、完整
   solution contract、原单位QC、result manifest及原始身份门禁；文件保全不等于科学接受。
4. Stage B是**非必需、非自动**的独立后续。任何Stage A launcher、guard、watcher、planning sequence或
   promotion路径都不得自动启动Stage B；只有作者以后另行明确授权，且Stage A耗时已证明值得继续时，
   才建立新任务与独立验收合同。

本地正确性证据为完整回归`290 passed, 1 skipped`，以及24h/start2880物理原式/缩放式双
Gurobi status2 `OPTIMAL`：目标均为`2112716.676624984 million CNY`，两者原单位QC均`PASS`，15项结构
等价检查全真。该短时域结果只验证代数、注册表、导出和QC接口，不证明2160h或8760h性能。

2160h候选尚未运行，资格门槛为：raw结构精确`12,520,914 rows / 10,398,783 vars /
126,724,678 nnz`；presolved nnz`<=107,398,350`、DenseCols`<=38,982`、`AA' NZ<=2.17035e8`、
Factor NZ`<=6.28845e9`、Factor Ops`<=2.19345e14`、日志factor memory`<=63 GB`且无数值警告。
首个`iteration>=30`记录须同时满足累计runtime`<=12,000 s`、Work`<=18,961.075`和进程组RSS
`<=75 GiB`；runtime/Work通过后即锁定，后续内存或警告仍可使候选失败。只有该门禁形成真实长时域
证据后才能决定是否放大8760h，不能把预期收益写成已证实加速。

### 5.8.0c 截断时域的价值核算与当前验证边界

对于 `hours < 8760` 的工程门禁，目标函数同时含全年年化规划/enablement 成本与所选小时的运行成本，二者不能在未加代表时段权重时直接相减为年度净收益。`cost_components.csv` 因此保留兼容列 `value_million_cny_per_year`，并新增：

- `value_million_cny_model_accounting_period`：该行在当前模型核算期内实际进入的数值；
- `accounting_scope=ANNUALIZED_PLANNING_COST`：全年年化投资、固定运维或年度服务开通成本；
- `accounting_scope=SELECTED_HORIZON_OPERATION_COST`：只覆盖当前所选小时的燃料、可变运维、移峰等运行成本；
- `optimization_hours` 与 `result_use`：强制携带时域和结果用途。

匹配 Base/V4 的历史 2030→2040→2050→2060 168 h 本地序列曾验证递进 planning state、硬 QC、输入/结果 manifest 和 resume；它只保留为旧 formulation 的复现证据，不能替代 V5 门禁。四年截断结果中出现的 EV 重排、未购买冷热服务或零波浪装机都只能说明对应窗口内的机制响应，不能证明这些技术在全年无价值，也不能把目标差写成年度净成本。

当前科学闭环必须重新对 Base 与唯一 V5 中央反事实做匹配门禁。只有 V5 在相同代码、数据、参数和数值 profile 下获得完整 8,760 h 的 `OPTIMAL`、全部 hard checks、当前 input manifest、有效 result manifest 及完整成本核算，才可解释年度容量与系统价值。V5 参数登记中的 low/high 只在中央反事实工程闭合后执行；完整 accepted Base anchor 之前不得运行 MGA。

## 5.8.1 本省负荷满足方程

### S4-57 负荷由本地供电、储能放电和外省输入满足

```math
I^{local}_{g,t}
+
\sum_{st\in ST}stodis_{g,st,t}
+
\sum_{g'}\eta^{AC}_{g',g}f^{AC}_{g',g,t}
+
\sum_{g'}\eta^{DC}_{g',g}f^{DC}_{g',g,t}
=
 dem_{g,t}+\sum_{dac\in DAC}ele_{g,dac},
\quad \forall g,\; t\in T
```

> 实现注意：需要根据线路方向把 `f^{AC,←}` / `f^{AC,→}` 映射到具体省份。推荐建立统一函数 `incoming_flows(g,t)`。

## 5.8.2 本地发电去向方程

### S4-58 本地发电用于本地消纳、储能充电和外送

```math
I^{local}_{g,t}
+
\sum_{st\in ST}stochar_{g,st,t}
+
\sum_{g'}f_{g,g',t}^{AC\cup DC}
=
\sum_{pt\in WE\cup PV\cup CSP\cup HP}I_{g,pt,t}
+
\sum_{pt\in TP\cup NP}\left(1-\xi^{ccs}_{pt}\right)u^{load}_{g,pt,t}\varrho_{pt},
\quad \forall g,\; t\in T
```

> 对没有 CCS 的技术，`xi_ccs_pt=0`。

---

## 5.9 备用约束

CISPO 包含向上旋转备用、向下旋转备用以及容量裕度。

## 5.9.1 向上备用需求

### S4-59 向上备用需求约束

```math
\sum_{pt\in PT}sr^{+}_{g,pt,t}+\sum_{st\in ST}sr^{+}_{g,st,t}
\ge
\rho^{+}_{sr}dem_{g,t}
+
\rho^{+}_{vre}\sum_{pt\in WE\cup PV}I_{g,pt,t},
\quad \forall g,\; t\in T
```

CISPO 中备用需求比例通常取 5%。

### S4-60 火电/核电提供向上备用

```math
sr^{+}_{g,pt,t}
\le
\left(1-\xi^{ccs}_{pt}\right)
\left(\overline{\phi}_{pt}u^{on}_{g,pt,t}-u^{load}_{g,pt,t}\right)\varrho_{pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

### S4-61 风光提供向上备用：来自可弃出力

```math
sr^{+}_{g,pt,t}
\le
\sum_{z\in Z_{g,pt}}cf_{g,z,pt,t}p_{g,z,pt}-I_{g,pt,t},
\quad \forall g,\; pt\in WE\cup PV,\; t\in T
```

### S4-62 CSP 提供向上备用

```math
sr^{+}_{g,csp,t}
\le
\sum_{z\in Z_{g,csp}}cf_{g,z,csp,t}p_{g,z,csp}
-I_{g,csp,t}
-\left(stoe^{csp}_{g,t}-stoe^{csp}_{g,t-1}\right),
\quad \forall g,\; t\in T
```

### S4-63 径流式水电提供向上备用

```math
sr^{+}_{g,ror,t}
\le
\sum_{z\in Z_{g,ror}}cf_{g,z,ror,t}p_{g,z,ror}-I_{g,ror,t},
\quad \forall g,\; t\in T
```

> 注：原文 S4-63 疑似存在 `ror/resvor` 符号排版错误。实现时按径流式水电可用出力减实际出力处理。

### S4-64 水库水电提供向上备用

```math
sr^{+}_{g,resvor,t}
\le
\sum_{z\in Z_{g,resvor}}p_{g,z,resvor}-I_{g,resvor,t},
\quad \forall g,\; t\in T
```

### S4-65 储能向上备用聚合

```math
sr^{+}_{g,st,t}=sr^{+,char}_{g,st,t}+sr^{+,dis}_{g,st,t},
\quad \forall g,\; st\in ST,\; t\in T
```

## 5.9.2 向下备用需求

### S4-66 向下备用需求约束

```math
\sum_{pt\in PT}sr^{-}_{g,pt,t}+\sum_{st\in ST}sr^{-}_{g,st,t}
\ge
\rho^{-}_{sr}dem_{g,t}
+
\rho^{-}_{vre}\sum_{pt\in WE\cup PV}I_{g,pt,t},
\quad \forall g,\; t\in T
```

### S4-67 火电/核电提供向下备用

```math
sr^{-}_{g,pt,t}
\le
\left(1-\xi^{ccs}_{pt}\right)
\left(u^{load}_{g,pt,t}-\underline{\phi}_{pt}u^{on}_{g,pt,t}\right)\varrho_{pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

### S4-68 水电提供向下备用

```math
sr^{-}_{g,pt,t}\le I_{g,pt,t},
\quad \forall g,\; pt\in HP,\; t\in T
```

### S4-69 储能向下备用聚合

```math
sr^{-}_{g,st,t}=sr^{-,char}_{g,st,t}+sr^{-,dis}_{g,st,t},
\quad \forall g,\; st\in ST,\; t\in T
```

## 5.9.3 容量裕度约束

### S4-70 峰值容量裕度

```math
\sum_{pt\in TP\cup NP}\lambda_{pt}u^{tot}_{g,pt}\varrho_{pt}
+
\sum_{pt\in WE\cup PV\cup CSP\cup HP}\sum_{z\in Z_{g,pt}}\lambda_{pt}p_{g,z,pt}
+
\sum_{st\in ST}\lambda_{st}p_{g,st}
\ge
\left(1+\rho^{cap}\right)dem^{peak}_{g},
\quad \forall g
```

当前 reviewed Base 取 `rho^{cap}=0.05`，并继续逐省使用 Base 负荷峰值；需求柔性不获得容量信用。其他裕度必须通过显式 scenario override 给出。

其中：

```math
dem^{peak}_{g}=\max_{t\in T}dem_{g,t}
```

---

## 5.10 惯量约束

### S4-71 最小惯量需求

```math
\sum_{pt\in TP\cup NP}\iota_{pt}u^{on}_{g,pt,t}\varrho_{pt}
+
\sum_{pt\in HP\cup CSP}\sum_{z\in Z_{g,pt}}\iota_{pt}p_{g,z,pt}
+
\sum_{st\in ST}\iota_{st}p_{g,st}
\ge
\iota^{tol}\iota_0dem_{g,t},
\quad \forall g,\; t\in T
```

> 实现注意：原文将火电/核电按在线容量提供惯量，水电、CSP、储能按装机容量提供惯量。储能是否具有等效惯量能力取决于参数假设。
>
> 当前 reviewed Base 将 `iota_0=3.5 s` 与 `iota^{tol}=1.0` 分开记录，有效最低惯量为 `3.5 s`。各发电技术的 `iota_pt` 保持技术参数值，不应统一替换为 3.5 s。旧版 scenario 若仍提供单一 `minimum_system_inertia_seconds`，由兼容解析器将其作为该 scenario 的有效阈值。

---

## 5.11 年度碳排放约束

### S4-72 年度净 CO2 排放上限

```math
\sum_{g\in G}\sum_{pt\in TP}
\left(1-\eta^{ccs}_{pt}\right)ef_{pt}
\sum_{t\in T}u^{load}_{g,pt,t}\varrho_{pt}\Delta t
-
\sum_{g\in G}\sum_{dac\in DAC}\eta_{dac}m_{g,dac}
\le
E
```

对于完整 8760 h 科学运行，比例 \(f_T=1\)。对于 24/168/744/4344 h 等连续
leading-hour 工程门禁，定义：

```math
f_T=\frac{|T|}{8760}.
```

诊断时域中的净排放质量与 \(f_TE\) 比较。所有同属年度流量的资源账户使用同一比例：
DAC 窗口捕集量不超过 \(f_Tp_{g,dac}\)，生物质燃料预算和 CO2 场址注入能力也分别
乘以 \(f_T\)。DAC 小时功率由 \(m_{g,dac}/f_T\) 的年化捕集速率计算。年化装机成本、
固定成本和容量状态不缩放。该处理使短时域能够检查碳约束与碳流闭合，但 leading-hour
窗口仍不代表全年气象、负荷或运行价值，因此不能作为科学规划结果。

> 实现注意：生物质与 BECCS 的碳核算取决于 `ef_pt` 与 `eta_ccs_pt` 的参数化。若要表达 BECCS 负排放，需要明确生物质碳排放因子与捕集量如何进入净排放核算，不能仅凭技术名称假设。

V0722 将 CISPO replication baseline 的隐含碳流显式拆分。CISPO 假定 biomass carbon-neutral、CCS 捕集率为 `eta_ccs=0.9`、捕集量全部封存，并给出逐年的 BECCS 净负排放因子 `ef_net<0`。在暂不加入生命周期排放的基线中：

```math
CO2^{stored}=-ef^{net}G,\qquad
CO2^{gross}_{bio}=CO2^{stored}/\eta^{ccs},
```

```math
CO2^{uncaptured}_{bio}=CO2^{gross}_{bio}-CO2^{stored},\qquad
E^{BECCS}=CO2^{lifecycle}+CO2^{uncaptured}_{bio}-CO2^{gross}_{bio}=-CO2^{stored}.
```

该拆分不改变原有负排放系数、捕集/运输/封存成本或可行域，只消除同一负因子同时承担“净排放”和“物理捕集量”语义的歧义。若以后采用非零 `CO2_lifecycle`，必须作为有独立来源的 adapted scenario，并满足 `net removal = stored - lifecycle emissions`。

---

## 5.12 DAC 约束

### S4-73 DAC 装机不低于已有能力

```math
\underline{p}_{g,dac}\le p_{g,dac},
\quad \forall g,\; dac\in DAC
```

### S4-74 DAC 年捕集量不超过装机能力

```math
m_{g,dac}\le p_{g,dac},
\quad \forall g,\; dac\in DAC
```

截断诊断时域使用 \(m_{g,dac}^{T}\le f_Tp_{g,dac}\)；8760 h 时退化为上述原式。

### S4-75 DAC 等效小时用电

```math
ele_{g,dac}
=
\frac{1}{|T|}\left(e_{dac}+\frac{h_{dac}}{cop}\right)m_{g,dac},
\quad \forall g,\; dac\in DAC
```

DAC 年化捕集速率被平均分配到所有小时，因此形成恒定附加负荷。截断诊断中窗口捕集
质量先除以 \(f_T\) 还原成年化速率，避免以部分年度电耗完成全年捕集量。

---

## 5.13 碳源—碳汇匹配约束

### S4-76 封存场址年注入能力约束

```math
\sum_{g\in G}m_{g,c}\le C_c,
\quad \forall c\in C
```

截断诊断时域使用 \(\sum_gm^T_{g,c}\le f_TC_c\)。

### S4-77 省级捕集 CO2 必须全部封存

```math
\sum_{c\in C}m_{g,c}
\ge
\sum_{dac\in DAC}m_{g,dac}
+
\sum_{pt\in TP}\eta^{ccs}_{pt}ef_{pt}
\sum_{t\in T}u^{load}_{g,pt,t}\varrho_{pt}\Delta t,
\quad \forall g
```

> 实现注意：CISPO 使用省级电网中心点到封存场址的最短地理距离近似 CO2 运输距离。因此第一版需要预先构造 `D_CO2[g,c]` 距离矩阵。

---

## 6. 动态规划年份设置

CISPO 不是一次性把所有年份联合求解，而是按规划年序贯求解。本地复现把模型边界前移至 2025：2025 仅作为存量、退役和初始网络状态的边界输入，不单独运行优化；第一个完整 8760 小时规划问题为 2030，表示 2025—2030 的容量变化和年度成本；随后沿用原文扩张决策年：

```text
2025 [boundary state only] -> 2030 -> 2040 -> 2050 -> 2060
```

2030/2040/2050/2060 各自运行一个完整 8760 小时模型。2030 下界由 2025 边界存量扣除截至 2030 的退役得到；此后上一期优化装机扣除退役后作为下一规划年的已有装机下界。2025 现有火电容量不得再扣除 `2025` 退役桶，否则会把基准存量重复减少。

### 6.1 容量继承公式

对任意技术 `k` 和站点/省级单元 `i`：

```math
\underline{K}_{i,k,y}
=
K^{opt}_{i,k,y-\Delta y}-K^{retired}_{i,k,y}
```

然后进入该规划年的容量约束：

```math
\underline{K}_{i,k,y}\le K_{i,k,y}\le \overline{K}_{i,k,y}
```

### 6.2 2025 基准状态与 2030 初始下界

本地实现以 2025 年已运行装机作为边界状态，不建立2025调度优化实例。2030 年下界由 2025 存量扣除截至 2030 的退役容量得到；核电采用 GEM 2030 committed/pipeline 下界。若已建容量退役后允许替换，必须把 replacement capacity 与真正新增容量分开记录。

### 6.3 寿命退役

每类技术需要寿命参数：

```text
lifetime[onshore wind], lifetime[offshore wind], lifetime[PV], lifetime[coal], ...
```

到达寿命的上一期新增容量应从下一期既有容量中扣除。若采用“退役后替换”假设，则该部分仍保留下界，但应记录为 replacement capacity。

---

## 7. 本地实现建议：数据结构

### 7.1 输入表建议

至少需要以下表：

1. `sets/provinces.csv`
   - `g, province_name`
2. `sets/technologies.csv`
   - `pt, category, varrho, lifetime, capex, fom, vom, fuel_cost, ...`
3. `vre/sites.csv`
   - `site_id, g, pt, lon, lat, p_existing, p_max, d_sub, sub_id, d_export_optional`
4. `vre/cf.zarr` 或 `vre/cf.parquet`
   - index: `site_id, t`
   - value: `cf`
5. `hydro/sites.csv`
   - `site_id, g, type, p_existing, p_max, H, V_min, V_max, ...`
6. `hydro/inflow.zarr`
   - `site_id, t, q_in`
7. `thermal/existing_capacity.csv`
   - `g, pt, u_existing or p_existing`
8. `storage/potential.csv`
   - `g, st, p_existing, p_max`
9. `transmission/lines.csv`
   - `line_id, from_g, to_g, type, p_existing, distance, loss_rate, capex, fixed_direction`
10. `grid/substations.csv`
    - `sub_id, g, lon, lat, lc_id, d_lc`
11. `load/hourly_load.csv`
    - `g, t, dem`
12. `ccs/storage_sites.csv`
    - `c, lon, lat, C_c`
13. `ccs/distance_matrix.csv`
    - `g, c, d_gc`
14. `scenario/year_params.csv`
    - `year, E, costs_multiplier, demand_multiplier, ...`

### 7.2 输出表建议

1. `outputs/capacity_vre.csv`
   - `year, g, site_id, pt, p_opt`
2. `outputs/dispatch_generation.csv`
   - `year, g, pt, t, I`
3. `outputs/thermal_ruc.csv`
   - `year, g, pt, t, u_on, u_su, u_sd, u_load`
4. `outputs/storage_dispatch.csv`
   - `year, g, st, t, charge, discharge, soc`
5. `outputs/transmission_flows.csv`
   - `year, line_id, t, flow_forward, flow_reverse`
6. `outputs/reserves.csv`
   - `year, g, t, sr_up_required, sr_up_available, sr_dn_required, sr_dn_available`
7. `outputs/carbon.csv`
   - `year, emissions_gross, emissions_residual, dac_removed, net_emissions, E`
8. `outputs/cost_breakdown.csv`
   - all objective components.
9. `outputs/model_diagnostics.json`
   - constraints count, variables count, nonzeros, solve status, gap, runtime, infeasibility diagnostics.

### 7.3 当前 31 省模型输入数据包（V0719）

可直接读取的数据位于 `data/`，由 `scripts/build_cispo_data_package.py` 统一生成，独立完整性检查由 `scripts/smoke_test_data_package.py` 执行。所有容量和功率字段已统一为 GW；大型小时容量因子和水文 NetCDF 不复制，在索引表中记录绝对原始路径、数组维度和时间口径。

| 模块 | 直接输入或索引 | 当前口径 |
|---|---|---|
| 集合 | `data/sets/provinces.csv` | 31 省，内蒙古不拆分 |
| 风光/CCS | `data/vre/optimization_points.csv` | 16,609 个模型点；61 个山东海上点由 46 修正为 37；130 个 `province=71` 点保留审计但不进入 31 省模型 |
| UPV/DPV | 同上 | 继续分开。二者共享 PV 容量因子，但保留不同的既有容量、资源上限、成本和接入距离口径；DPV 接入距离可设为 0 |
| 模型年份 | `data/sets/model_years.csv` | 2025 为固定校准年；2030/2040/2050/2060 为容量扩张决策年 |
| 小时容量因子 | `data/vre/hourly_cf_index.csv` | 索引 `D:\National_model\Data\Gis\Hourly_cf` 下 2020–2025 Zarr；默认气象年为 2023 |
| 负荷 | `data/load/hourly_load_2025_2060.csv.gz` | 31 省 × 5 模型年 × 8,760 h，北京时间，GW；当前本地版本由 `Power_curve_V2/future_8760_projection_ev_calibrated_v3_qc` 的 8 年上游筛选既有五模型年，采用广州逐日 QC 后的 EV 形状与显式月度单车电量参数；总负荷与 base residual/heating/cooling/EV 四分量逐时闭合，2035/2045/2055 不进入当前模型年集合 |
| V4 需求柔性 | `data/flexibility/{thermal_hourly_envelope_v4.csv.gz,thermal_parameters_by_province_v4.csv,ev_availability_hourly_v4.csv.gz,ev_mobility_hourly_v4.csv.gz,flex_enablement_cost_v4.csv,flexible_load_v4.manifest.json}` | 独立工程情景输入；由既有冷热/EV 基线和 BAIT `+/-1 C` 包络生成，四规划年 loader/SHA256 闭合；中心/低/高参数是需敏感性的工程假设，不进入 Base |
| 火电 | `data/thermal/capacity_floor_by_year.csv` | GEM 2025 运行机组扣除逐期退役后的外生容量下界；新增容量由模型决定 |
| 核电 | `data/thermal/nuclear_capacity_floor_by_year.csv`、`data/thermal/nuclear_capacity_upper_by_year.csv` | GEM committed/pipeline 下界；V0719 全国上界 2030/2040/2050/2060 = 110/205/300/300 GW，省级按管线权重分配 |
| 水电 | `data/hydro/hydro_stations.csv`、`data/hydro/timeseries_index.csv`、`data/hydro/cascade_topology_nodes.csv`、`data/hydro/cascade_topology_edges.csv`、`data/hydro/provincial_aggregate_capacity_2025.csv`、`data/hydro/provincial_aggregate_monthly_capacity_factor_2019.csv` | 297.8895 GW 可识别站点与 82.1105 GW 固定省级聚合容量闭合至 2025 年常规水电 380 GW；站点层使用当前分类、重复 `COMID` 静态份额、GRFR 2019 与核心梯级水量平衡；聚合层只有可弃的逐月自然可用上限，不具有站点水力属性、扩张、备用、惯量、容量信用或 spur/trunk；环境流量仍为 2019 单年 monthly P30 代理 |
| 生物质 | `data/biomass/fuel_potential_by_province_year.csv`、`data/biomass/capacity_upper_by_province_year.csv` | 省级热值同时进入年度燃料约束和 bio+bioccs 共享容量上界；2030/2040 线性插值，2060 保持 2050 |
| 电池 | `data/storage/battery_capacity_floor_by_province_year.csv` | CISPO Table S17 的 2025 省级目标作为 2030 功率下界；Mengdong/Mengxi 合并后全国 65.85 GW；2040+ 不重复锁定该 15 年寿命 cohort |
| 输电 | `data/transmission/existing_lines.csv`、`data/transmission/candidate_corridors.csv` | 2025 既有通道和 31 省全组合候选走廊 |
| 碳约束 | `data/carbon/emissions_limits_by_scenario.csv` | 2025 不启用上限；默认 Base 路径为 2030/2040/2050/2060 = 4000/1300/-100/-550 MtCO2/yr |
| DAC | `data/technology/dac_parameters_by_year.csv` | 四类技术，包含年度成本、CRF、直接电耗、热耗、COP换算后总电耗 |
| CapEx | `data/technology/technology_capex_by_year.csv` | 19 类技术 × 2030/2040/2050/2060；来自用户提取的 CISPO 图表目测值，yuan/kW；CHP 使用对应燃料与 CCS 曲线，水电锚点保持不变 |
| 煤气价格 | `data/technology/province_fuel_prices.csv` | Supplementary Table 2 的 31 省煤炭/天然气 USD/GJ 值；按 7.1429 CNY/USD 转为 2025 年不变人民币；蒙东/蒙西算术平均；作为结构性省际价差保持 2025–2060 实值不变，不解释为 2025 现货预测 |
| 发电燃料成本 | `data/technology/province_fuel_generation_cost_by_year.csv` | 由省级 yuan/GJ 与 RUC fuel load 计算为 yuan/MWh；北京、西藏煤价缺失，煤类技术不允许调度或新增 |
| 技术参数 | `data/technology/` | VRE/水电成本锚点、thermal/nuclear RUC、储能、输电、CCS与排放因子 |
| 337中心正式输入 | `data/load_center_network/city_337/load_centers.csv` | 一市一点、2022 城市用电省内份额；31省份额分别闭合到1 |
| 风光省内接入 | `data/load_center_network/city_337/vre_routes.csv` | 16,609个优化格点的联合最小spur+trunk路线；DPV接入距离为0 |
| 水电省内接入 | `data/load_center_network/city_337/hydro_routes.csv` | 2,030个站点级水电经同省联合最优变电站连接到最近市级中心；省级聚合水电无站点路线，按需求份额分配且不增加 spur/trunk |
| Spur 初始容量 | `data/load_center_network/city_337/initial_spur_capacity_2025.csv` | 337路线下的2025逐点逐技术名义装机压力初值 |
| Trunk/变电站初值 | `data/load_center_network/city_337/substation_initial_capacity_2025.csv` | 6,294个OSM变电站的VRE接口需求代理；水电既有容量在模型中另行加入初始trunk |
| 省内中心网络 | `data/load_center_network/city_337/intra_edges.csv` | 642条省内MST+3NN无向边、AC500成本，203条边具有2025正初始容量 |
| 278中心复现输入 | `data/load_center_network/natural_earth_278/` | CISPO Natural Earth定义、2019年1 km栅格权重及完整旧路线；保留用于敏感性，不覆盖 |
| 省级接入汇总 | `data/grid/province_initial_intra_grid_capacity_2025.csv` | 31 省容量闭合、变电站峰值合计和省级同时峰值对照 |

数据层面的默认选项记录在 `data/model_defaults.json`，来源与输出校验分别记录在 `data/source_manifest.csv`、`data/output_manifest.csv`、`data/qc_summary.csv` 和 `data/smoke_test_report.json`。现有未标注水电站的 115 MW 代理分类在 GHT 已标注样本上的平衡准确率约为 0.677，故该标签是当前模型分配值而不是经核验的电站事实属性；本轮按用户决策直接使用，不开展 60/115/200 MW 分类敏感性。

重建与检查命令：

```powershell
& "D:\Program Files\ArcGISPro\bin\Python\envs\arcgispro-py3\python.exe" scripts\build_cispo_data_package.py
& "D:\Program Files\ArcGISPro\bin\Python\envs\arcgispro-py3\python.exe" scripts\smoke_test_data_package.py
python scripts\build_city_337_network.py
python scripts\build_natural_earth_278_network.py  # 仅在需要重建 CISPO 复现情景时运行
```

当前正式负荷中心情景为337市级方案；278中心Natural Earth论文复现方案仍完整保留。模型已包含风光、水电空间归属、其他电源按需求份额分配、省际送端电量闭合、省内累计能量流动和AC500扩容成本。当前主要限制是中心间线路仍为大圆距离候选走廊、年度容量换算使用50%利用率软假设、省际交换按城市需求份额分摊，以及省内损耗尚未反馈到小时平衡。

---

## 8. 本地实现顺序建议

### Step 1：最小可行系统

先只实现：风光 + 负荷 + 弃电 + 储能 + 省际输电 + 严格负荷平衡。

目的：验证网格容量因子、负荷、输电和储能数据单位正确。

### Step 2：加入火电/核电 RUC

加入 S4-22 至 S4-31。先禁用最小启停时间，验证燃料成本、出力上下限和爬坡约束；再启用最小启停时间。

### Step 3：加入水电

先加入径流式水电，再加入水库水电。水库水电最容易产生单位错误，必须单独测试。

### Step 4：加入备用与惯量

加入 S4-59 至 S4-71。调试时输出每小时 reserve slack。

### Step 5：加入 CCS、DAC、碳源汇匹配

加入 S4-72 至 S4-77。先用宽松 `E` 测试，再使用情景碳约束。

### Step 6：加入省内 spur/trunk line 成本与约束

加入 S4-18 至 S4-21。尤其注意 S4-19 的线性化。

### Step 7：多年份序贯求解

将单年模型封装为：

```python
def solve_year(year, existing_capacity, scenario_params):
    ...
    return optimized_capacity, dispatch_results, diagnostics
```

然后外层循环：

```python
existing_capacity = load_boundary_state(2025)
for year in [2030, 2040, 2050, 2060]:
    result = solve_year(year, existing_capacity, scenario[year])
    existing_capacity = update_existing_capacity(result.capacity, retirements, lifetime)
```

---

## 9. 必须进行的自检

### 9.1 单位自检

- 所有功率变量是否为 GW。
- 所有小时发电量是否通过 `GW × h = GWh`。
- 水电 `qHηgρ` 是否从 W 转换为 GW。
- CO2 排放是否为 `MtCO2/GWh × GWh = MtCO2`。
- 输电损耗是否只在受端计入。

### 9.2 物理自检

- 任意小时任意省负荷平衡误差应小于 `1e-6` 或求解器容差。
- 储能 SOC 不得超过 `p * duration`。
- 储能期初期末 SOC 必须一致。
- 风光并网出力不得超过可用出力。
- 输电流不得超过线路容量。
- 年度净排放不得超过 `E`。
- 捕集 CO2 必须全部分配到封存场址。

### 9.3 经济自检

- 成本分项不得出现异常负数，除非明确设置负成本。
- 若无碳约束，系统应偏向低成本电源；若收紧碳约束，低碳电源、CCS、DAC、储能或输电应增加。
- 若输电成本设为极高，跨省流量应下降。
- 若储能成本设为极高，储能容量应下降，弃电或火电调节应上升。

### 9.4 规模自检

输出：

```text
number_of_variables
number_of_constraints
number_of_nonzeros
solve_status
objective_value
runtime_seconds
```

当模型不可行时，必须调用 Gurobi IIS 并输出 `iis.ilp` 或 `iis.json`。

---

## 10. 与 CISPO 复现相关的已知简化和注意事项

1. CISPO 的省际输电是 transportation / pipeline model，不是 AC 潮流模型。
2. CISPO 的 RUC 是连续松弛，不是严格整数 UC。
3. CISPO 的负荷平衡是省级小时平衡，不是节点级潮流平衡。
4. CISPO 的风光出力可弃，实际并网出力由 `I_{g,pt,t}` 表示。
5. CISPO 的 CO2 运输距离采用省级电网中心到封存场址的最短地理距离近似。
6. CSP、储能、水库均有期初期末状态一致约束。
7. 若某些公式在原文中存在排版疑似错误，必须在代码注释中记录，并保留原公式版本与修正版诊断版本。

---

## 11. 第一版代码模块建议

```text
cispo_rebuild/
  README.md
  config.yaml
  data_schema.md
  src/
    build_sets.py
    load_data.py
    parameters.py
    model_core.py
    constraints_vre.py
    constraints_csp.py
    constraints_hydro.py
    constraints_thermal_ruc.py
    constraints_storage.py
    constraints_transmission.py
    constraints_balance.py
    constraints_reserve_inertia.py
    constraints_carbon.py
    objective.py
    solve_year.py
    dynamic_loop.py
    diagnostics.py
    export_results.py
  tests/
    test_units.py
    test_small_system.py
    test_storage_soc.py
    test_power_balance.py
    test_carbon_balance.py
  outputs/
```

---

## 12. 复现优先级说明

若数据尚未齐全，第一阶段不建议试图一次性跑全国 8760 小时 × 60000 网格。建议先构造小系统：

```text
2 provinces
2 wind sites per province
2 PV sites per province
1 thermal technology
1 storage technology
1 AC line
24 or 168 hours
```

确认全部约束可行后，再扩展到：

```text
31 provinces
full VRE sites
8760 hours
all technologies
all transmission lines
carbon system
```

---

## 13. 关键词定位

该模型可称为：

```text
CISPO-inspired high-resolution capacity expansion and dispatch LP with relaxed unit commitment
```

不要称为：

```text
AC power flow model
strict unit commitment model
mixed-integer UC model
nodal dispatch model
```

除非后续另行扩展。

---

## 14A. 2026-07-27 波浪能纳入 Base

波浪能是 Base 的默认资产类，但不加入 `VRE_TECHS`。原始波浪格点不作为第二套优化
网格；构建输入时只保留与 `optimization_points.csv` 坐标一致且 `is_land == 0` 的既有
`grid_uid`。对每个被波浪数据覆盖的既有海洋格点 \(i\) 增加连续容量变量：

\[
K_i^{wave}=K_{i,inherited}^{wave}+K_{i,new}^{wave},\qquad
0\le K_i^{wave}\le f_{potential}K_{i,raw}^{wave}.
\]

省份 \(p\) 的波浪能小时出力满足：

\[
0\le g_{p,t}^{wave}\le\sum_{i\in p}CF_{i,t}^{wave}K_i^{wave},
\]

并直接进入严格省级小时电力平衡。首版不给予波浪能向上/向下备用、容量
充裕度或惯量贡献，但按实际波浪能出力增加 5% 上下备用需求。这样既保持
保守可靠性边界，也无需增加波浪能 availability 或备用分配辅助变量。

成本使用 `base CAPEX + depth adder × water_depth_m + distance adder ×
distance_to_shore_km`，其中参数来自 DOI
`10.1016/j.apenergy.2024.123119`。该成本已代表独立海上项目的位置差异，
因此本情景不占用或共享海上风电 spur/trunk。省份、变电站和负荷中心
标识直接复用同一个既有 `grid_uid` 的 `city_337` 路由，不使用最近海上
风电格点代理，也不代表新增工程海缆路线。

原始数据只有 2030/2040/2050 的 conservative/medium/aggressive CF，容量潜力在全部
情景中相同且没有 2060 数据。当前 2060 明确保持 2050 medium CF 和成本；
`potential_fraction`、水深/离岸距离筛选、插补 CF、汇率和成本必须作为敏感性参数。
运行 Base 或唯一 V3+V2G 柔性覆盖均须设置 `CISPO_WAVE_ROOT`。完整数据审计、规模门检
和运行说明见 `WAVE_ENERGY_INTEGRATION.md`；历史波浪单模块和组合 JSON 已删除。

## 14. 2026-07-18 production implementation addendum

本节记录当前 production code 相对基础公式文档的实现合同，代码基线为 `2a0ee99`。详细审计证据见 `MODEL_SYSTEM_AUDIT_20260718.md`。

### 14.1 规划年份和状态传递

模型按 `2030 -> 2040 -> 2050 -> 2060` 顺序逐期求解。2025 仅是 2030 的输入边界。第 `y` 年容量下界由外生存量与仍在寿命期内的历史模型 cohort 组成：

```math
\underline P_{a,y}^{effective}
=
\underline P_{a,y}^{exogenous}
+
\sum_{c:\; build_c\le y<retire_c}\Delta P_{a,c}.
```

每个 full-year 解只有在 `OPTIMAL` 且 `solution_qc=PASS` 后才写出带 SHA256 的下一期状态。该路径是 myopic sequential planning，不是四期 perfect foresight。

### 14.2 Battery/PHS 边界

Battery 的 2030 省级 exogenous capacity floor 来自 `data/storage/battery_capacity_floor_by_province_year.csv`，全国合计 65.85 GW。当前 battery 为固定 4h 功率-能量比，因此不能直接把异质时长的新型储能统计功率全部写成下界；后续应将 GW 与 GWh 分开建模。

Base 中 PHS 维持省级 8h storage 形式。省级 capacity floor 来自 GHT 2026 operating projects，capacity upper 来自 `available_from_year <= planning_year` 的项目池。当前不表示 open-loop/closed-loop reservoir pairing。

代码另提供 `independent_power_energy_v1` 结构：保留现有省—小时充电、放电、SOC 和备用数组，只增加每省一个年度能量容量变量 \(K^{PHS,E}_g\)，并以

```math
D^{min}K^{PHS,P}_g\le K^{PHS,E}_g\le D^{max}K^{PHS,P}_g
```

替代固定 \(K^{PHS,E}_g=8K^{PHS,P}_g\)。投资成本写为 \(c_PK^{PHS,P}+c_EK^{PHS,E}\)，且配置必须使 \(c_P+8c_E\) 在每个规划年严格闭合当前 8h 总 CAPEX；否则模型硬失败。来源审查后提供低、中、高三条候选路径，8 h 能量侧成本占比分别为 30%、36.5% 和 45%；中央值由 DOE/PNNL 与 ANU 两组直接分项证据的 31.69% 和 41.35% 取中点并取整得到。三条配置均为 `PROPOSED_NOT_APPLIED_COST_CALIBRATED`，只用于敏感性门禁；Base 在取得年度与长时域证据前继续固定 8 h。

### 14.3 储能备用的精确投影

代码将四类 charge/discharge reserve component 投影为 `R_up`、`R_down`，但保留相同聚合可行域。上备用同时受功率容量、当前充电可削减量和前一时刻 SOC 约束；下备用同时受充电余量和剩余 SOC 空间约束。不得删除 SOC reserve headroom 约束。

### 14.4 稀疏等价表达

- `ramp_magnitude >= +/- (P_t-P_{t-1})` 替代独立 `ramp_up/ramp_down`；
- reservoir generation 由 turbine flow 线性表达，不再设置重复 generation variable/equality；
- hydro inertia 为容量表达式；
- annual operating cost 直接进入 objective，不再设置大尺度会计等式；
- VRE/ROR availability 辅助变量继续保留，因为直接代入会把 site CF 系数复制到多个约束并增加 nonzeros。
- DC 走廊不创建反向逐时变量；仅 48 条 AC 走廊创建 `flow_reverse_ac_gw`，全年精确减少 `363×8760=3,179,880` 个固定零变量。

### 14.5 成本口径

与本文件 CISPO 目标函数保持一致，VRE、thermal/nuclear、hydro、storage 和 transmission 的 annualized CapEx 均按当期 total installed capacity 计算。对固定的既有容量（包括 82.1105 GW 省级聚合常规水电），这部分是当期常数；对新增/继承 cohort，边际系数与技术 CapEx/CRF 一致。

### 14.6 生产输出和停止规则

生产输出必须包含容量、逐小时运行、碳/CCS、成本分解、`solution_qc.json`、SHA256 manifest 和简要 SVG。每个成功求解还必须在 manifest 封存前生成固定结果查阅合同：`result_dashboard_summary.json`、`result_analysis_metrics.csv` 与 `visualizations/core_result_dashboard.svg`，统一显示 solver/QC/hard checks、容量、所选时域发电、灵活性、碳约束和安全裕度。

对于采用物理车群 SOC、驾驶取能、充放电效率和周期边界的 V4/V5，
“逐日网侧充电量等于不受控 EV 充电基线”不再是守恒恒等式。因此
`maximum_ev_v1g_daily_energy_residual_gwh` 必须输出为 `null`，并由
`ev_v1g_daily_energy_residual_applicability` 明确标记不适用；真正的 hard
evidence 是车群 SOC transition、departure SOC、SOC 上界、充放电功率与
周期边界。固定 dashboard 对绝对值小于 `0.001 GWh` 但非零的储能电量显示
`<0.001`，不得将自放电补偿等微量流误画为严格零。

成本强度的分母统一采用柔性调度前的不可变基准用电量，以保证 Base 与 V5 可比；因 \(1\ \mathrm{million\ CNY}/\mathrm{GWh}=1\ \mathrm{CNY}/\mathrm{kWh}\)，无需额外换算因子。只有 `SCIENTIFIC_PRODUCTION` 的 8760 h 结果可以把年化规划成本与全年运行成本相加并报告“总系统成本强度”。1 h/24 h/168 h/744 h 的 `TEST_ONLY_TRUNCATED_HORIZON` 必须分别报告“年化规划成本/全年基准负荷”和“所选时域运行成本/同期基准负荷”，不得相加、不得标记为 LCOE，也不得当作年度科学结果。`annual_operation` 仅为 composite roll-up；详细成本求和时必须排除该行，并硬校验 scope-aware 明细能够重构目标值。

744h 只作为求解门槛；8760 是唯一可用于论文结果的时段。若 infeasible，应输出 IIS；若 memory gate、solver status、solution contract 或 QC 不通过，不得导出看似完整的科学结果、封存 result manifest、自动放松约束或写出下一期 planning state。

### 14.7 原始 LP 结构审计合同

求解性优化候选必须先用 `--constraint-family-audit` 在新的、隔离的短时
Base 根进行结构测量。审计在 `model.update()` 后仅读取 Gurobi 的原始系数
矩阵，不调用 `optimize()`、不修改参数、变量、目标函数或约束。它输出
`constraint_family_audit.json`，并作为科学诊断文件进入 `output_catalog.csv`
和 `result_manifest.json`。

审计至少记录原始 rows/columns/nonzeros、按稳定名称前缀归类的约束/变量
族、每族的最大/平均行或列非零元，以及最稠密的 25 个具体行和列。求解完成
后同一文件追加 Gurobi 日志中的全局 presolve、ordering、`AA' NZ`、`Factor NZ`、
`Factor Ops`、Barrier 和 crossover 指标。Gurobi 不提供稳定的“预处理后行到
源约束族”映射，因此不得把全局 presolve 删除量归因给某一族。

`Model.getA()` 会显式物化稀疏矩阵；默认安全上限是 50,000,000 个原始非零元，
超过上限必须硬失败而不是占用全年求解内存。故该审计自身不构成 744h/8760h
运行许可；任何等价改写仍须在匹配 24h/168h 上验证目标、全部 QC、manifest、
raw/presolved 规模、因子结构、阶段时间、迭代数和峰值 RSS 后，才可评价是否有
全年收益。
