# Module 04 V2 生产集成记录：2025 年不变人民币

> 授权日期：2026-07-28  
> 合约：`technoeconomic_2025_cny_v2`  
> 状态：`APPROVED_AND_APPLIED_LOCAL_PRODUCTION_PACKAGE`  
> 终止标记：`FINAL_M04_V2_PRODUCTION_INTEGRATION_PASS`

## 1. 最终规则

模型目标函数中的经济成本统一采用 2025 年不变人民币。

1. CISPO 以 2022 年不变人民币给出的国内成本，包括其 2030、2040、
   2050 和 2060 规划年轨迹，均乘同一系数 `1.004004`。
2. 核电 CapEx 回到原始 USD 路径
   `2800/2650/2500/2350 USD/kW`，再乘 `7.1429 CNY/USD`。
3. 省级燃料价格使用文献所报 USD/GJ 值乘 `7.1429 CNY/USD`。
   这些数值表示结构性省际规划价差，并非 2025 年现货观测。
4. 波浪能以 2024 EUR 来源值乘 `8.1185 CNY/EUR`。
5. 效率、热耗、寿命、WACC、容量约束和比例参数不换算。市内
   `0.001 CNY/MWh` 是数值破简并项；灵活负荷成本为独立研究情景，
   两者不执行 CISPO 价格重基准。

共同价格因子不会改变规划年间的相对学习幅度。例如

\[
\frac{C_{2060}^{2025CNY}}{C_{2030}^{2025CNY}}
=
\frac{1.004004 C_{2060}^{2022CNY}}
{1.004004 C_{2030}^{2022CNY}}
=
\frac{C_{2060}^{2022CNY}}{C_{2030}^{2022CNY}}.
\]

因此 2050、2060 等远期价格需要调整到 2025 年价，但只进行一次共同
价格基准转换，不能再按“距 2025 年的年数”追加通胀。

## 2. 写入位置

- 价格规则：`config/technoeconomic_price_basis_2025.json`
- 运行时配置：`config/optimization_2030.json`
- 原始参数与转换元数据：`config/technology_parameters.json`
- 燃料来源币种配置：`config/fuel_prices_supplementary_table2.json`
- 可复现构建：`scripts/build_cispo_data_package.py`
- 现有数据包迁移：`scripts/apply_technoeconomic_price_basis_v2.py`
- 生产数据包审计标记：
  `data/technology/technoeconomic_price_basis_manifest.json`

`data/` 为 Git 外置数据包。Git 推送交付代码、配置和迁移合约；向固定
服务器或云端部署时仍须显式同步经过迁移的数据包，并在目标环境重新运行
readiness、smoke test 和输入 manifest 校验。本轮不启动长期求解。

## 3. 核心定稿值

- onshore wind 2030 CapEx：`5522.022 CNY/kW`
- battery 2060 CapEx：`2409.6096 CNY/kW`
- nuclear CapEx 2030/2040/2050/2060：
  `20000.12/18928.685/17857.25/16785.815 CNY/kW`
- CCS capture/transport/storage：
  `261.04104 CNY/tCO2`、`0.50 CNY/tCO2/km`、`45 CNY/tCO2`
- wave FX：`8.1185 CNY/EUR`
- fuel FX：`7.1429 CNY/USD`

完整运行时权威文件映射见
`tables/table_m04_24_production_integration.csv`，验证结果见
`qa/production_integration_validation.csv`。
