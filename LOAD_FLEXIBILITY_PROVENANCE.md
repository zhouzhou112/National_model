# 负荷分解与灵活性输入来源

## 1. 当前运行时负荷

`data/load/hourly_load_2025_2060.csv.gz` 是当前模型唯一逐时负荷输入。2026-07-24
整表复核结果为：

- 31 省 × 5 个模型年份（2025、2030、2040、2050、2060）× 8,760 h；
- 共 1,357,800 行；
- `demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw`；
- SHA256：
  `8c2cb3b6b233625af2e6f9aef635a1fcabfe746010c2a11464579f8b77a369cd`。

该表由本机 `Power_curve_V2` 输出
`outputs/future_8760_projection/tables/future_hourly_load_2025_2060_8760.csv.gz`
转换而来。上游表包含 2025、2030、2035、2040、2045、2050、2055、2060 八个年份，
SHA256 为
`67a0a79ed94f5ffa1f5935519044e09e8878f6429fbe79ed605d16e4d067af5a`。
转换只执行三项操作：

1. 选择 National_model 使用的五个模型年份；
2. 依据 `data/sets/provinces.csv` 将中文省名映射为 `province_code`；
3. 将 `future_total_load_mw`、`base_residual_load_mw`、`heating_load_mw`、
   `cooling_load_mw`、`ev_load_mw` 除以 1,000 转为 GW。

整表逐行核验表明，省名、年份、`hour_index`、北京时间和省码完全一致，MW→GW
最大绝对数值误差为 `5.68e-14 GW`。

## 2. Power_curve_V2 的四分量构建

经本地已验收的 Power_curve_V2 过程，历史分解的规范运行目录为
`outputs/run_20260617_122125`。

### 冷热负荷

`scripts/02_reconstruct_weather_and_thermal_load.py` 先以城市月度用电权重聚合 ERA5
网格天气，构建 BAIT，再计算：

\[
HDD_h=\max(T_{heat}-BAIT_h,0)/24,
\qquad
CDD_h=\max(BAIT_h-T_{cool},0)/24.
\]

\[
Heating_h=P_{heat}\times HDD_h\times1000,
\qquad
Cooling_h=P_{cool}\times CDD_h\times1000.
\]

未来投影由 `scripts/08_generate_future_8760_loads.py` 读取 2024 非闰年的省级逐时冷热
形状，并乘省年 `thermal_multiplier`。因此当前 2025–2060 冷热分量不是逐年未来天气
模拟，而是 2024 天气形状与未来空调/热需求倍率的组合。

### EV 负荷

`scripts/03_reconstruct_ev_load.py` 将 96 点行为概率聚合为北京时间
`hour_bj -> ev_hour_weight`，并校验 24 h 权重和为 1。未来逐时 EV 基线为：

\[
EV_{p,t}=
Stock_{p,y}\times kWhPerVehicleDay_m/1000\times evHourWeight_t.
\]

`ev_hour_weight` 表示无序充电基线的日内分配权重，不是车辆在桩率、离家率或 V2G
可用率。任何灵活性情景不得把它直接重命名为 `availability`。

### 基础残差与总量闭合

历史 Module 04 使用：

\[
BaseResidual=TotalLoad-Heating-Cooling-EV.
\]

未来 Module 08 先给定省年总用电目标，再扣除冷热和 EV 年电量，将剩余电量按
`base_template_share` 分配到 8,760 h，最后重新求和形成总负荷。National_model
加载时再次逐行验证四分量闭合。

## 3. 灵活性模块如何使用这些分量

- Base：直接使用四分量总和，不创建灵活性变量。
- `flexible_load_v1`：保留已验收的逐日能量守恒上下调。
- `flexible_load_state_v2`：
  - `heating_gw/cooling_gw` 是不可变服务基线，增加日内因果、日末归零的等效热库存；
  - `ev_gw` 是不可变无序充电基线，可搬运部分先进入待充队列，只有已有延期电量后
    才能在后续小时补充充电；
  - V2G 强制关闭，因为当前数据不含逐时车辆接入率、可用电池能量、驾驶取能与出发
    SOC。
- `flexible_load_v2g_v1`：继续作为独立虚拟储能敏感性情景，不应称为已校准车辆模型。

所有冷热保留率、库存时长、可搬运比例、队列时长和吞吐成本仍标记为
`ILLUSTRATIVE_ASSUMPTIONS_REQUIRE_SENSITIVITY`。状态形式比纯日守恒更严格，但不能
代替省级建筑 RC 标定或车辆出行调查。

## 4. 当前可复现性缺口

2026-07-24 审计时，`Power_curve_V2` Git HEAD 为 `abbb330`，但其
`scripts/08_generate_future_8760_loads.py` 仍是用户工作树中的未跟踪文件，当前文件
SHA256 为
`defe6261df63e3c5b1864cfa43dc94e7de8a1ee98fa4543ec39283248222a6aa`。
因此不能只用 `abbb330` 宣称未来负荷生成链已经由 Git 完整冻结。当前
National_model 通过固定最终输入 SHA256、上游输出 SHA256、生成脚本 SHA256 和整表
变换核验保证结果可追溯；后续应由用户确认后在 Power_curve_V2 仓库单独版本化
Module 08 及其输入清单。本仓库不得代替用户提交该上游工作树。
