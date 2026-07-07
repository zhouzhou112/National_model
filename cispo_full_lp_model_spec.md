# CISPO 完整 LP/RUC 模型复现说明

> 目的：在本地复现 `Integrated Modeling for the Transition Pathway of China’s Power System` 补充材料 S4 中的 CISPO 电力系统优化模型。
>
> 本文档供 Codex / 本地 Python + Gurobi 实现使用。请优先将其作为**数学模型规格书**，而不是普通说明文档。实现时不得随意删减约束、改变符号含义或把连续 RUC 改成整数 UC。

---

## 0. 对 Codex 的强制要求

1. **模型类型**：优先复现 CISPO 的连续线性规划 / relaxed unit commitment 版本。所有机组组合变量 `u_tot, u_on, u_su, u_sd, u_load` 默认是连续非负变量，不得改成 binary / integer，除非用户另行要求。
2. **时间分辨率**：每个规划年默认使用完整 8760 小时：`T = {0, 1, ..., 8759}`。不得擅自换成典型日、代表周或抽样小时。工程测试可显式选择连续前 744 小时（1 个月）或 4344 小时（1—6 月），但两者均采用截断区间周期边界，且年度投资成本、碳约束和生物质约束不缩放，只能用于代码与求解器测试，不能作为规划结果。
3. **空间分辨率**：风电、光伏、CSP 的基本决策单元为 0.25° × 0.25° 网格；水电为坝址；储能、火电、核电、DAC 为省级电网层面。
4. **单位统一**：功率用 GW，电量用 GWh，CO2 用 MtCO2，成本用 yuan 或 CNY，距离用 km，时间步长 `Delta_t = 1 h`，水电流量公式中 `Delta_t = 3600 s`。
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
\sum_g\sum_{pt\in HP}\sum_{t\in T}\kappa^{vom}_{pt}I_{g,pt,t}
```

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

> CISPO 中 `kappa_vom_l` 取一个很小的值，用于避免交流线路同小时双向流动，并避免 AC/DC 人工偏好。

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

1. 非核心干流水库站仍按站点级独立水量平衡建模，`q^{in}_{g,z,t}` 来自该站 GRFR 可用流量。
2. Stage2 推荐核心干流梯级站进入梯级水量平衡。核心范围来自 `hydro_model_2019_stage2_classification_cascade_20260630` 的 5 个推荐梯级组，生成到 `data/hydro/cascade_topology_nodes.csv` 和 `data/hydro/cascade_topology_edges.csv`。边的河道传播时滞 `\tau_{u,z}` 由 2019 GRFR 小时 `qout_model_m3s` 按 3 h 倍数做上下游互相关估计，搜索窗上限为 168 h。

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

重复 COMID 节点中的多个电站按 `capacity_potential_gw` 权重分摊本地增量入流和上游到达流量。当前环境流量为 2019 单年 monthly P30 代理；正式 1980-2019 多年 P30 环境流和开环/闭环抽水蓄能水库配对尚未接入。

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

正式方案采用 278 个 Natural Earth 城市斑块几何中心复现论文方法。1 km 电力消费栅格只用于在省内分配年度需求份额，不移动中心坐标，也不生成中心小时负荷曲线。每个优化格点选择使“格点到变电站 spur 距离 + 变电站到同省 Natural Earth 中心 trunk 距离”最小的 ≥220 kV OSM 变电站。水电站使用同一目标函数补齐路线。DPV 位于负荷侧，spur/trunk 容量与成本保持为0。

## 5.4.4 负荷中心年度能量分配与省内500 kV扩容

本层不增加 `lc × hour` 变量。对完整年度，所有量均为 GWh；截短时段只用于代码测试。

风光与水电的实际省级发电量通过年度归属变量分配到空间连接的负荷中心，并受相应点位/电站在选定时段内的可发电量上界约束。火电、核电、生物质、储能充放电、DAC及省际受入电量按固定年度需求份额分配。

```math
J_{lc}+\sum_{e\in IN(lc)}F_e
=D^{eff}_{lc}+\sum_{e\in OUT(lc)}F_e+X_{lc}
```

其中 `J` 为年度注入量，`D^{eff}` 为用户负荷、储能充电和 DAC 用电构成的年度有效需求，`X` 为分配给该中心的省际送端电量。省级外送严格闭合：

```math
\sum_{lc\in LC_g}X_{lc}
=\sum_{t}\sum_{l\in OUT(g)}f^{send}_{l,t}
```

省内边只连接同省中心。候选拓扑为每省最小生成树加每节点3个最近邻，共517条无向边。线路容量约束为：

```math
F^{\to}_e+F^{\leftarrow}_e
\le H\rho^{design}\left(\underline K^{2025}_e+K^{new}_e\right)
```

默认 `rho_design=0.5`。该值是显式软假设，必须做敏感性分析。初始容量使用2025同时铭牌压力下的空间平衡代理，不得解释为观测额定容量。

成本采用 EES Table S20 和 Figure S44 的 `AC_500kV` 参数，而非单独的550 kV线路类型：变电站159 yuan/kW、架空线2640 thousand yuan/km，线路参考传输能力随距离变化。中心间直线距离是工程走廊代理。为保持省级小时平衡与年度中心平衡严格闭合，第一版省内损耗设为0；非零损耗必须先作为附加用电反馈到小时平衡。

---

## 5.5 火电与核电 RUC 约束

## 5.5.1 机组状态转移

### S4-22 状态变量上下界

```math
0\le u^{on}_{g,pt,t},u^{su}_{g,pt,t},u^{sd}_{g,pt,t}\le u^{tot}_{g,pt},
\quad \forall g,\; pt\in TP\cup NP,\; t\in T
```

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

> 该约束配合极小输电可变成本，用于避免同小时无意义的双向流动。

---

## 5.8 电力负荷平衡

CISPO 负荷平衡在省级电网 `g` 与小时 `t` 层面闭合。

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

> 实现注意：生物质与 BECCS 的碳核算取决于 `ef_pt` 与 `eta_ccs_pt` 的参数化。若要表达 BECCS 负排放，需要明确生物质碳排放因子与捕集量如何进入净排放核算，不能仅凭技术名称假设。

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

### S4-75 DAC 等效小时用电

```math
ele_{g,dac}
=
\frac{1}{|T|}\left(e_{dac}+\frac{h_{dac}}{cop}\right)m_{g,dac},
\quad \forall g,\; dac\in DAC
```

DAC 年捕集量被平均分配到所有小时，因此形成恒定附加负荷。

---

## 5.13 碳源—碳汇匹配约束

### S4-76 封存场址年注入能力约束

```math
\sum_{g\in G}m_{g,c}\le C_c,
\quad \forall c\in C
```

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

### 7.3 当前 31 省模型输入数据包（2026-07-01）

可直接读取的数据位于 `data/`，由 `scripts/build_cispo_data_package.py` 统一生成，独立完整性检查由 `scripts/smoke_test_data_package.py` 执行。所有容量和功率字段已统一为 GW；大型小时容量因子和水文 NetCDF 不复制，在索引表中记录绝对原始路径、数组维度和时间口径。

| 模块 | 直接输入或索引 | 当前口径 |
|---|---|---|
| 集合 | `data/sets/provinces.csv` | 31 省，内蒙古不拆分 |
| 风光/CCS | `data/vre/optimization_points.csv` | 16,609 个模型点；61 个山东海上点由 46 修正为 37；130 个 `province=71` 点保留审计但不进入 31 省模型 |
| UPV/DPV | 同上 | 继续分开。二者共享 PV 容量因子，但保留不同的既有容量、资源上限、成本和接入距离口径；DPV 接入距离可设为 0 |
| 模型年份 | `data/sets/model_years.csv` | 2025 为固定校准年；2030/2040/2050/2060 为容量扩张决策年 |
| 小时容量因子 | `data/vre/hourly_cf_index.csv` | 索引 `D:\National_model\Data\Gis\Hourly_cf` 下 2020–2025 Zarr；默认气象年为 2023 |
| 负荷 | `data/load/hourly_load_2025_2060.csv.gz` | 31 省 × 5 模型年 × 8,760 h，北京时间，GW |
| 火电 | `data/thermal/capacity_floor_by_year.csv` | GEM 2025 运行机组扣除逐期退役后的外生容量下界；新增容量由模型决定 |
| 核电 | `data/thermal/nuclear_capacity_floor_by_year.csv` | GEM committed/pipeline 下界；不强制 2050 年 300 GW，2060 暂保持 2050 管线下界 |
| 水电 | `data/hydro/hydro_stations.csv`、`data/hydro/timeseries_index.csv`、`data/hydro/cascade_topology_nodes.csv`、`data/hydro/cascade_topology_edges.csv` | 现有站使用当前分配标签，不按置信度剔除；潜在坝址按论文 `>750 MW` 为水库式、其余为径流式；Stage2 推荐核心干流梯级站使用本地 GRFR 增量入流 + 上游发电/弃水时滞到达，其余水库站保持独立水量平衡；环境流量为 2019 单年 monthly P30 代理，正式多年 P30 尚未接入 |
| 生物质 | `data/biomass/fuel_potential_by_province_year.csv` | 省级农业残余、林业残余、能源作物热值约束；2030/2040 线性插值，2060 保持 2050 |
| 输电 | `data/transmission/existing_lines.csv`、`data/transmission/candidate_corridors.csv` | 2025 既有通道和 31 省全组合候选走廊 |
| 碳约束 | `data/carbon/emissions_limits_by_scenario.csv` | 2025 不启用上限；默认 Base 路径为 2030/2040/2050/2060 = 4000/1300/-100/-550 MtCO2/yr |
| DAC | `data/technology/dac_parameters_by_year.csv` | 四类技术，包含年度成本、CRF、直接电耗、热耗、COP换算后总电耗 |
| CapEx | `data/technology/technology_capex_by_year.csv` | 19 类技术 × 2030/2040/2050/2060；来自用户提取的 CISPO 图表目测值，yuan/kW；CHP 使用对应燃料与 CCS 曲线，水电锚点保持不变 |
| 煤气价格 | `data/technology/province_fuel_prices.csv` | Supplementary Table 2 截图的 31 省煤炭/天然气价格；6.9 yuan/USD 转换；蒙东/蒙西算术平均；截图未注明价格年，暂保持 2025–2060 不变 |
| 发电燃料成本 | `data/technology/province_fuel_generation_cost_by_year.csv` | 由省级 yuan/GJ 与 RUC fuel load 计算为 yuan/MWh；北京、西藏煤价缺失，煤类技术不允许调度或新增 |
| 技术参数 | `data/technology/` | VRE/水电成本锚点、thermal/nuclear RUC、储能、输电、CCS与排放因子 |
| 278中心正式输入 | `data/load_center_network/natural_earth_278/load_centers.csv` | Natural Earth论文复现中心及1 km栅格年度需求份额；31省份额分别闭合到1 |
| 风光省内接入 | `data/load_center_network/natural_earth_278/vre_routes.csv` | 16,609个优化格点的最小spur+trunk路线；DPV接入距离为0 |
| 水电省内接入 | `data/load_center_network/natural_earth_278/hydro_routes.csv` | 2,030个水电站到同省变电站和Natural Earth中心的路线 |
| Spur 初始容量 | `data/load_center_network/natural_earth_278/initial_spur_capacity_2025.csv` | 论文路线下的2025逐点逐技术初值与2023 CF峰值对照 |
| Trunk/变电站初值 | `data/load_center_network/natural_earth_278/substation_initial_capacity_2025.csv` | 6,294个OSM变电站的VRE接口容量代理；水电既有容量在模型中另行加入初始trunk |
| 省内中心网络 | `data/load_center_network/natural_earth_278/intra_edges.csv` | 517条省内MST+3NN无向边、AC500成本、2025容量代理 |
| 省级接入汇总 | `data/grid/province_initial_intra_grid_capacity_2025.csv` | 31 省容量闭合、变电站峰值合计和省级同时峰值对照 |

数据层面的默认选项记录在 `data/model_defaults.json`，来源与输出校验分别记录在 `data/source_manifest.csv`、`data/output_manifest.csv`、`data/qc_summary.csv` 和 `data/smoke_test_report.json`。现有未标注水电站的 115 MW 代理分类在 GHT 已标注样本上的平衡准确率约为 0.677，故该标签是当前模型分配值而不是经核验的电站事实属性；本轮按用户决策直接使用，不开展 60/115/200 MW 分类敏感性。

重建与检查命令：

```powershell
& "D:\Program Files\ArcGISPro\bin\Python\envs\arcgispro-py3\python.exe" scripts\build_cispo_data_package.py
& "D:\Program Files\ArcGISPro\bin\Python\envs\arcgispro-py3\python.exe" scripts\smoke_test_data_package.py
python scripts\build_natural_earth_278_network.py
```

当前正式负荷中心情景为278中心Natural Earth论文复现方案。模型已包含风光、水电空间归属、其他电源按需求份额分配、省际送端电量闭合、省内年度流动和AC500扩容成本。当前主要限制是中心间线路仍为直线候选走廊、2条西部边超过EES AC500的1000 km来源范围、年度容量换算使用50%利用率软假设，以及省内损耗尚未反馈到小时平衡。

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
