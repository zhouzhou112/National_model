# Module 04 数据与参考来源

> 检索与核对日期：2026-07-28。正式投稿时应按全文参考文献编号统一格式。

## 一、当前模型输入来源

| 参数族 | 当前来源与状态 | 本模块处理 |
|---|---|---|
| 技术 CapEx | CISPO 技术经济体系及其补充图表数字化；当前输入含 19 类技术、4 个规划年 | 保留模型值；记录图号、数字化方法和映射；另给 2025 年不变价对照 |
| 火电/核电运行参数 | CISPO 补充信息中的 RUC、热耗、启停和 O&M 参数 | 按当前表逐项核对，不由历史综述反推 |
| 既有火电、核电和 pipeline | Global Energy Monitor 项目级数据形成的 2025 状态、退役和容量下界 | 分开报告既有容量、退役队列、pipeline 下界和政策上界 |
| 储能 | CISPO 省级电池最低目标、GHT 抽蓄运行/项目数据及当前储能技术表 | 政策目标只作比较，不静默替换模型约束 |
| 省级燃料价格 | An 等（2025）Supplementary Note 3 与 Supplementary Table 2；煤为 2023 推算水平，气为 2018 门站基准构造，生物质来自 2022 出厂价研究 | 保留省级 USD GJ⁻¹结构；最终候选值按 2025 官方平均汇率换算，并设置燃料轨迹敏感性 |
| DAC、CCS、输电 | CISPO 补充参数及当前生产输入 | 2022 语境项给出 CPI 对照；来源不完整项标为 provisional |
| 波浪能 | Applied Energy 2024 研究及当前 wave-enabled Base 配置 | 建议最终 reference 改为关闭；2025 汇率换算只用于独立敏感性 |

各生产输入的相对路径、模型消费者、行数与 SHA256 见 `tables/table_m04_1_active_input_register.csv`。

## 二、模型基线与方法

1. Integrated modeling for the transition pathway of China’s power system. *Energy & Environmental Science* (2025). DOI: https://doi.org/10.1039/D5EE00355E
2. Global Energy Monitor. Global Coal Plant Tracker, Global Gas Plant Tracker, Global Bioenergy Power Tracker and Global Nuclear Power Tracker. 项目级版本与下载信息由当前数据构建链记录。
3. An, K. et al. Repositioning coal power to accelerate net-zero transition of China’s power system. *Nature Communications* 16, 2311 (2025). DOI: https://doi.org/10.1038/s41467-025-57559-2；数据与代码：https://doi.org/10.5281/zenodo.14836760

## 三、最新政策

1. 国家能源局，《新型能源体系建设“十五五”规划》，2026-06-25。https://www.nea.gov.cn/20260625/0ccfdc1674e84868b49480edf584eb5f/202606250ccfdc1674e84868b49480edf584eb5f_27b526ec29479c4fd4bbb6f42d3ce5bbca.pdf
2. 国家发展改革委、国家能源局，《新型储能规模化建设专项行动方案（2025—2027年）》，2025。https://www.gov.cn/zhengce/zhengceku/202509/P020250912411822546143.pdf
3. 国家发展改革委、国家能源局，《关于深化新能源上网电价市场化改革 促进新能源高质量发展的通知》，2025-01-27。https://zfxxgk.ndrc.gov.cn/web/iteminfo.jsp?id=20482

政策数字用于容量边界比较和情景审计，不直接作为技术成本观测值。

## 四、价格水平与汇率

1. 国家统计局，《中华人民共和国2025年国民经济和社会发展统计公报》，2026-02-28。2025 年 CPI 为 0.0%，人民币兑美元年平均汇率为 7.1429。https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html
2. 国家统计局，《中华人民共和国2024年国民经济和社会发展统计公报》，2025-02-28。2024 年 CPI 为 0.2%。https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html
3. 国家统计局，《中华人民共和国2023年国民经济和社会发展统计公报》，2024-02-28。2023 年 CPI 为 0.2%。https://www.stats.gov.cn/sj/zxfb/202402/t20240228_1947915.html
4. Oesterreichische Nationalbank / ECB reference-rate statistics. 2025 年人民币兑欧元年平均汇率 8.1185。https://www.oenb.at/isawebstat/stabfrage/createReport?lang=EN&report=2.14.5

## 五、近期参数更新与敏感性文献

1. High-resolution gridded dataset of China’s offshore wind potential and costs under technical change. *Scientific Data* (2025). DOI: https://doi.org/10.1038/s41597-025-04428-8
2. Substantially lower estimates in China’s offshore wind potential using farm-scale spatial modeling and wake effects. *Nature Communications* (2026). DOI: https://doi.org/10.1038/s41467-026-68655-2
3. Historical and future projected costs of capital for ten energy technologies across 176 countries. *Scientific Data* (2025). DOI: https://doi.org/10.1038/s41597-025-06177-0
4. Heterogeneous effects of battery storage deployment strategies on provincial power-system decarbonization. *Nature Communications* (2023). DOI: https://doi.org/10.1038/s41467-023-40337-3
5. 波浪能成本来源：*Applied Energy* (2024). DOI: https://doi.org/10.1016/j.apenergy.2024.123119
6. IRENA. *Renewable Power Generation Costs in 2024* (2025). https://www.irena.org/Publications/2025/Jul/Renewable-power-generation-costs-in-2024
7. NREL. *Cost Projections for Utility-Scale Battery Storage: 2025 Update*. https://research-hub.nrel.gov/en/publications/cost-projections-for-utility-scale-battery-storage-2025-update/
8. NREL. *2024 Annual Technology Baseline: Pumped Storage Hydropower*. https://atb.nrel.gov/electricity/2024/pumped_storage_hydropower
9. 国家能源局，《中国新型储能发展报告（2025）》。https://www.nea.gov.cn/20250731/1d40d09f75714280a9218d5bea178fbd/c.html
10. Hatton, L. et al. Historical and future projected costs of capital for ten energy technologies across 176 countries. *Scientific Data* (2025). DOI: https://doi.org/10.1038/s41597-025-06177-0；数据：https://doi.org/10.5281/zenodo.17076925

这些研究用于识别空间成本、融资成本和储能时长的不确定性，不被用来无条件替换当前成套模型参数。

## 六、引用缺口与投稿前动作

- 省级燃料价格来源已经闭合到 An 等（2025）Supplementary Note 3 和 Supplementary Table 2；最终表注仍须区分煤、气、生物质的不同构造年份，并明确其不是统一的 2025 年现货观测价。
- GEM 各 tracker 的精确版本、下载日期和许可应从构建 manifest 统一写入最终参考文献表。
- CISPO 图表数字化值需在最终英文表注中保留“visual estimate/digitized”标签，并报告读取误差或范围。
- 当前模块已给出政策和论文 URL/DOI，但最终需与全文参考文献编号及数据可用性声明统一。
