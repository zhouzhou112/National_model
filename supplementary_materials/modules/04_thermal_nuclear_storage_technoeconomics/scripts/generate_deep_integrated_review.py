"""Build the CISPO-anchored deep techno-economic review package.

This script is additive.  It reads the current production inputs and the
previous review candidate, but writes only Module 04 review tables and
``candidate_inputs_v2``.  No file under ``National_model/data`` or
``National_model/config`` is modified.

Review contract
---------------
* recover the parameter logic and source chain in CISPO.pdf;
* use at least five independent evidence groups for every material review unit;
* report monetary values in 2025 constant CNY;
* keep source-year planning assumptions distinct from 2025 observations;
* keep scalar data changes distinct from model-structure changes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


MODULE = Path(__file__).resolve().parents[1]
TABLES = MODULE / "tables"
QA = MODULE / "qa"
CANDIDATE_V1 = MODULE / "candidate_inputs"
CANDIDATE_V2 = MODULE / "candidate_inputs_v2"

USD_CNY_2025 = 7.1429
CPI_2022_2025 = 1.004004
MIN_INDEPENDENT_SOURCES = 5


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


SOURCES = [
    # Core CISPO lineage
    ("S01", "CISPO_EES_2025", 2025, "China", "peer_reviewed",
     "Integrated modeling for the transition pathway of China's power system, main paper and SI",
     "https://doi.org/10.1039/D5EE00355E", "PRIMARY_MODEL_LINEAGE"),
    ("S02", "CREEI_Report_2022", 2023, "China", "official_industry_report",
     "China Renewable Energy Development Report 2022", "", "CREEI"),
    ("S03", "Sun_cost_projection_2023", 2023, "China", "peer_reviewed",
     "Cost prediction of China's wind, solar and CSP technologies", "", "SUN_2023"),
    ("S04", "Li_dispatchability_2024", 2024, "China", "peer_reviewed",
     "China power-system dispatchability and transition pathways", "", "LI_2024"),
    ("S05", "NREL_ATB_2024", 2024, "United States", "official_technical_report",
     "Annual Technology Baseline 2024", "https://atb.nrel.gov/electricity/2024/", "NREL_ATB_2024"),
    ("S06", "IRENA_RPGC_2024", 2025, "Global", "intergovernmental_report",
     "Renewable Power Generation Costs in 2024",
     "https://www.irena.org/Publications/2025/Jul/Renewable-power-generation-costs-in-2024",
     "IRENA_RPGC_2024"),
    ("S07", "IRENA_RPGC_2025", 2026, "Global", "intergovernmental_report",
     "Renewable Power Generation Costs in 2025, executive summary",
     "https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2026/Jul/IRENA_TEC_RPGC_2025_Executive_summary_2026.pdf",
     "IRENA_RPGC_2025"),
    ("S08", "Wang_accelerating_VRE_2023", 2023, "China", "peer_reviewed",
     "Accelerating the deployment of wind and solar in China",
     "https://doi.org/10.1038/s41586-023-06180-8", "WANG_VRE_2023"),
    ("S09", "Zhang_Chen_transition_2022", 2022, "China", "peer_reviewed",
     "Probabilistic transition pathways for China's power system",
     "https://doi.org/10.1038/s41467-022-31260-0", "ZHANG_CHEN_2022"),
    ("S10", "Bowen_nuclear_2023", 2023, "China", "research_report",
     "China's nuclear power development and construction-cost assumptions",
     "https://www.energypolicy.columbia.edu/publications/", "BOWEN_CGEP_2023"),
    ("S11", "NREL_ATB_nuclear_2024", 2024, "United States", "official_technical_report",
     "Annual Technology Baseline 2024: nuclear",
     "https://atb.nrel.gov/electricity/2024/nuclear", "NREL_NUCLEAR_2024"),
    ("S12", "IAEA_nuclear_cost_2024", 2024, "Global", "intergovernmental_report",
     "Nuclear energy economics and financing evidence", "https://www.iaea.org/topics/economics",
     "IAEA_2024"),
    # Dispatch, fuel and plant operation
    ("S13", "Chen_Joule_2021", 2021, "China", "peer_reviewed",
     "Carbon-neutral China power-system pathways", "https://doi.org/10.1016/j.joule.2021.06.011",
     "CHEN_JOULE_2021"),
    ("S14", "Fan_cofiring_CCS_2023", 2023, "China", "peer_reviewed",
     "Coal flexibility, biomass co-firing and CCS in China",
     "https://doi.org/10.1038/s41558-023-01795-7", "FAN_2023"),
    ("S15", "Han_RUC_2019", 2019, "China", "peer_reviewed",
     "Relaxed unit commitment validation for China power-system planning", "", "HAN_RUC_2019"),
    ("S16", "Yang_regional_model_2018", 2018, "China", "peer_reviewed",
     "Regional China power-system planning and unit-operation parameters", "", "YANG_2018"),
    ("S17", "An_coal_repositioning_2025", 2025, "China", "peer_reviewed",
     "Repositioning coal power to accelerate net-zero transition of China's power system",
     "https://doi.org/10.1038/s41467-025-57559-2", "AN_2025"),
    ("S18", "NDRC_coal_price_2020", 2020, "China", "government_source",
     "Provincial coal-price monitoring and benchmark information", "", "NDRC_COAL_2020"),
    ("S19", "CNCA_coal_report_2022", 2022, "China", "official_industry_report",
     "China Coal Industry Annual Report 2022", "", "CNCA_2022"),
    ("S20", "NDRC_gas_benchmark_2019", 2019, "China", "government_source",
     "Provincial benchmark city-gate natural-gas prices",
     "https://www.ndrc.gov.cn/xxgk/zcfb/tz/201903/t20190329_962412.html",
     "NDRC_GAS_2019"),
    ("S21", "Yuan_biomass_price_2022", 2022, "China", "peer_reviewed",
     "Provincial biomass ex-factory fuel-price evidence", "", "YUAN_BIOMASS_2022"),
    ("S22", "IEA_Coal_2024", 2024, "Global", "intergovernmental_report",
     "Coal 2024", "https://www.iea.org/reports/coal-2024/executive-summary", "IEA_COAL_2024"),
    ("S23", "IEA_Gas_Q1_2025", 2025, "Global", "intergovernmental_report",
     "Gas Market Report Q1 2025", "https://www.iea.org/reports/gas-market-report-q1-2025",
     "IEA_GAS_2025"),
    # Storage and hydropower
    ("S24", "Peng_battery_2023", 2023, "China", "peer_reviewed",
     "Heterogeneous effects of battery storage deployment in China",
     "https://doi.org/10.1038/s41467-023-40337-3", "PENG_BATTERY_2023"),
    ("S25", "NEA_storage_report_2025", 2025, "China", "government_report",
     "China New Energy Storage Development Report 2025",
     "https://www.nea.gov.cn/20250731/1d40d09f75714280a9218d5bea178fbd/c.html",
     "NEA_STORAGE_2025"),
    ("S26", "NREL_battery_2025", 2025, "United States", "official_technical_report",
     "Cost Projections for Utility-Scale Battery Storage: 2025 Update",
     "https://research-hub.nrel.gov/en/publications/cost-projections-for-utility-scale-battery-storage-2025-update/",
     "NREL_BATTERY_2025"),
    ("S27", "IEA_batteries_2024", 2024, "Global", "intergovernmental_report",
     "Batteries and Secure Energy Transitions",
     "https://www.iea.org/reports/batteries-and-secure-energy-transitions/executive-summary",
     "IEA_BATTERIES_2024"),
    ("S28", "Schmidt_storage_2019", 2019, "Global", "peer_reviewed",
     "Projecting the future levelized cost of electricity storage", "https://doi.org/10.1016/j.joule.2018.12.008",
     "SCHMIDT_2019"),
    ("S29", "Zakeri_Syri_2015", 2015, "Global", "peer_reviewed",
     "Electrical energy storage life-cycle cost review", "https://doi.org/10.1016/j.rser.2014.10.011",
     "ZAKERI_2015"),
    ("S30", "NREL_PSH_2024", 2024, "United States", "official_technical_report",
     "Annual Technology Baseline 2024: pumped storage hydropower",
     "https://atb.nrel.gov/electricity/2024/pumped_storage_hydropower", "NREL_PSH_2024"),
    ("S31", "NEA_PSH_plan_2021", 2021, "China", "government_plan",
     "Medium- and Long-term Development Plan for Pumped Storage (2021-2035)",
     "https://www.nea.gov.cn/2021-09/09/c_1310177087.htm", "NEA_PSH_2021"),
    ("S32", "IEA_hydropower_2021", 2021, "Global", "intergovernmental_report",
     "Hydropower Special Market Report",
     "https://www.iea.org/reports/hydropower-special-market-report/executive-summary",
     "IEA_HYDRO_2021"),
    ("S33", "Hunt_seasonal_PSH_2020", 2020, "Global", "peer_reviewed",
     "Global resource potential of seasonal pumped hydropower storage",
     "https://doi.org/10.1038/s41467-020-14555-y", "HUNT_PSH_2020"),
    ("S34", "Xu_hydropower_2023", 2023, "China", "peer_reviewed",
     "China hydropower operation and water constraints", "https://doi.org/10.1038/s44221-023-00073-0",
     "XU_HYDRO_2023"),
    # CCS and DAC
    ("S35", "Wang_coal_phase_down_2022", 2022, "China", "peer_reviewed",
     "Alternative coal phase-down and CCUS pathways in China",
     "https://doi.org/10.1021/acs.est.1c07992", "WANG_CCS_2022"),
    ("S36", "China_CCUS_report_2023", 2023, "China", "government_report",
     "China CCUS Annual Report 2023",
     "https://www.most.gov.cn/kjbgz/202307/t20230714_187011.html", "CHINA_CCUS_2023"),
    ("S37", "China_CCUS_pathways_2022", 2022, "China", "peer_reviewed",
     "Technology pathways and cost evolution of CCUS in China",
     "https://doi.org/10.1080/17583004.2022.2117648", "CHINA_CCUS_PATH_2022"),
    ("S38", "China_CCUS_key_issues_2022", 2022, "China", "peer_reviewed",
     "Several key issues for CCUS deployment in China",
     "https://doi.org/10.1007/s43979-022-00019-3", "CHINA_CCUS_KEY_2022"),
    ("S39", "China_CO2_pipeline_2012", 2012, "China", "peer_reviewed",
     "Economics of CO2 pipeline transport in China",
     "https://doi.org/10.1016/j.enconman.2011.10.022", "CHINA_PIPELINE_2012"),
    ("S40", "IEA_CCUS_2020", 2020, "Global", "intergovernmental_report",
     "CCUS in Clean Energy Transitions",
     "https://www.iea.org/reports/ccus-in-clean-energy-transitions", "IEA_CCUS_2020"),
    ("S41", "Young_DAC_2023", 2023, "Global/China", "peer_reviewed",
     "Global and regional direct-air-capture technology pathways",
     "https://doi.org/10.1016/j.oneear.2023.05.010", "YOUNG_DAC_2023"),
    ("S42", "IEA_DAC_2022", 2022, "Global", "intergovernmental_report",
     "Direct Air Capture 2022", "https://www.iea.org/reports/direct-air-capture-2022/executive-summary",
     "IEA_DAC_2022"),
    ("S43", "Shorey_DAC_2024", 2024, "Global", "peer_reviewed",
     "Spatially resolved energy and cost requirements of direct air capture",
     "https://doi.org/10.1038/s43247-024-01773-1", "SHOREY_DAC_2024"),
    ("S44", "NatCommun_DAC_2024", 2024, "Global", "peer_reviewed",
     "Process-level cost assessment of direct air capture",
     "https://doi.org/10.1038/s41467-024-53961-4", "NATCOMM_DAC_2024"),
    ("S45", "CommEng_DAC_2024", 2024, "Global", "peer_reviewed",
     "Off-grid direct air capture systems",
     "https://doi.org/10.1038/s44172-023-00152-6", "COMMENG_DAC_2024"),
    ("S46", "NatCommun_DAC_materials_2020", 2020, "Global", "peer_reviewed",
     "Material and energy constraints for direct air capture",
     "https://doi.org/10.1038/s41467-020-17203-7", "NATCOMM_DAC_2020"),
    # Network, finance and price normalization
    ("S47", "Zhang_Cao_grid_report_2020", 2020, "China", "official_industry_report",
     "China Grid Development Report 2020", "", "CHINA_GRID_2020"),
    ("S48", "IEA_World_Energy_Investment_2024", 2024, "Global", "intergovernmental_report",
     "World Energy Investment 2024",
     "https://www.iea.org/reports/world-energy-investment-2024/overview-and-key-findings",
     "IEA_WEI_2024"),
    ("S49", "Han_UHV_loss_2021", 2021, "China", "technical_article",
     "UHV transmission loss and engineering parameters", "", "HAN_UHV_2021"),
    ("S50", "Xu_offshore_grid_2017", 2017, "China", "peer_reviewed",
     "Offshore integration and transmission topology in China", "", "XU_GRID_2017"),
    ("S51", "Hatton_WACC_2025", 2025, "Global/China", "peer_reviewed_dataset",
     "Historical and projected costs of capital for ten energy technologies",
     "https://doi.org/10.1038/s41597-025-06177-0", "HATTON_WACC_2025"),
    ("S52", "Liu_He_hydro_finance_2023", 2023, "China", "peer_reviewed",
     "Financing and operational risk for hydropower",
     "https://doi.org/10.1038/s44221-023-00111-x", "LIU_HE_2023"),
    ("S53", "NREL_finance_2024", 2024, "United States", "official_technical_report",
     "ATB financial cases and methods",
     "https://atb.nrel.gov/electricity/2024b/financial_cases_%26_methods", "NREL_FINANCE_2024"),
    ("S54", "NBS_2023", 2024, "China", "government_statistics",
     "2023 National Economic and Social Development Statistical Communiqué",
     "https://www.stats.gov.cn/sj/zxfb/202402/t20240228_1947915.html", "NBS_2023"),
    ("S55", "NBS_2024", 2025, "China", "government_statistics",
     "2024 National Economic and Social Development Statistical Communiqué",
     "https://www.stats.gov.cn/sj/zxfb/202502/t20250228_1958817.html", "NBS_2024"),
    ("S56", "NBS_2025", 2026, "China", "government_statistics",
     "2025 National Economic and Social Development Statistical Communiqué",
     "https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html", "NBS_2025"),
    ("S57", "OeNB_FX_2025", 2026, "International", "official_statistics",
     "2025 annual average exchange-rate statistics",
     "https://www.oenb.at/isawebstat/stabfrage/createReport?lang=EN&report=2.14.5",
     "OENB_FX_2025"),
    ("S58", "IMF_price_statistics", 2025, "Global", "intergovernmental_statistics",
     "Consumer price and exchange-rate methodological comparator",
     "https://www.imf.org/en/Publications/WEO/weo-database/2025/April", "IMF_2025"),
    # Wave
    ("S59", "AppliedEnergy_wave_2024", 2024, "Global", "peer_reviewed",
     "Wave-energy learning and cost projections",
     "https://doi.org/10.1016/j.apenergy.2024.123119", "APPLIED_ENERGY_WAVE_2024"),
    ("S60", "EU_Blue_Economy_2025", 2025, "Europe", "government_report",
     "EU Blue Economy Report 2025: marine renewable energy",
     "https://op.europa.eu/webpub/mare/eu-blue-economy-report-2025/blue-economic-sectors/marine-renewable-energy.html",
     "EU_BLUE_2025"),
    ("S61", "IRENA_ocean_outlook_2020", 2020, "Global", "intergovernmental_report",
     "Innovation Outlook: Ocean Energy Technologies",
     "https://www.irena.org/publications/2020/Dec/Innovation-Outlook-Ocean-Energy-Technologies",
     "IRENA_OCEAN_2020"),
    ("S62", "IRENA_ocean_investment_2023", 2023, "Global", "intergovernmental_report",
     "Scaling up investments in ocean energy technologies",
     "https://www.irena.org/Publications/2023/Mar/Scaling-up-investments-in-ocean-energy-technologies",
     "IRENA_OCEAN_2023"),
    ("S63", "OES_annual_report_2024", 2024, "Global", "intergovernmental_report",
     "Ocean Energy Systems Annual Report 2024",
     "https://www.ocean-energy-systems.org/publications/oes-annual-reports/", "OES_2024"),
]


FAMILIES = [
    ("F01", "风电、光伏与光热 CapEx/O&M/学习率", ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"],
     "保留 CISPO 的中国初始成本与相对下降率；按 2025 CNY 重基准。全球值只作可比性检查。"),
    ("F02", "常规水电 CapEx/O&M/寿命", ["S01", "S06", "S07", "S32", "S34", "S52"],
     "保留 13,319 CNY/kW 的 CISPO 中国口径并按 CPI 重基准；站点异质性单列局限。"),
    ("F03", "煤气生物质与核电 CapEx/O&M", ["S01", "S09", "S10", "S11", "S12", "S13", "S17"],
     "非核技术保留 CISPO 轨迹并按 CPI 重基准；核电回到原始 USD 路径后按 2025 FX 重算。"),
    ("F04", "火电核电 RUC 与运行技术参数", ["S01", "S04", "S13", "S14", "S15", "S16", "S17"],
     "保留 CISPO 中央值；煤电 pmin 采用 0.30/0.40/0.50 敏感性。"),
    ("F05", "省级煤气生物质燃料价格", ["S01", "S17", "S18", "S19", "S20", "S21", "S22", "S23"],
     "保留 An 等的省际结构并按 2025 FX 换算；明确其是异年份构造的规划价格而非 2025 现货。"),
    ("F06", "4 h 锂电池成本、效率、寿命与时长", ["S01", "S24", "S25", "S26", "S27", "S28", "S29", "S07"],
     "保留 4 h CISPO 基线；确认其为偏积极的中国成本情景；2/4/8/12 h 需拆分功率和能量成本。"),
    ("F07", "抽水蓄能成本、效率、寿命与时长", ["S01", "S30", "S31", "S32", "S33", "S34", "S06"],
     "保留 77.44% RTE、8 h、40 y 中央值；场址类型与 8/12/24 h 为高优先级敏感性。"),
    ("F08", "CCS 捕集成本、捕集率与有效能耗", ["S01", "S14", "S17", "S35", "S36", "S37", "S38", "S40"],
     "保留 90% 捕集率和 260 CNY/tCO2 捕集费重基准；先核算热耗率与 5% 净出力损失的合成惩罚。"),
    ("F09", "CO2 运输与封存成本", ["S01", "S17", "S35", "S36", "S37", "S38", "S39", "S40"],
     "采用中国多来源中心值：0.50 CNY/tCO2/km 与 45 CNY/tCO2；保留宽范围敏感性。"),
    ("F10", "DAC CapEx/O&M/能源需求/学习率", ["S01", "S41", "S42", "S43", "S44", "S45", "S46"],
     "保留 CISPO/Young 技术分型与学习率作为研究情景；不得将乐观路径描述为商业现状。"),
    ("F11", "输电线路、变电站、损耗与寿命", ["S01", "S47", "S48", "S49", "S50", "S13"],
     "保留中国电压等级成本与预优化网络口径；材料价格和走廊工程不确定性进入敏感性。"),
    ("F12", "实际 WACC 与融资口径", ["S01", "S13", "S51", "S52", "S53", "S11"],
     "保留统一 7.4% real WACC；外部 nominal/technology-specific 数据不能直接替换，采用 4/7.4/9%。"),
    ("F13", "技术寿命与既有机组退役寿命", ["S01", "S09", "S11", "S12", "S13", "S32"],
     "保留新建技术经济寿命；既有机组 30/40/50 y 必须通过队列重建测试，不能只改 CRF。"),
    ("F14", "2025 年不变人民币换算与价格账本", ["S01", "S54", "S55", "S56", "S57", "S58"],
     "国内 2022 CNY 乘 1.004004；原始外币数值按来源币种和 2025 FX 转换，逐行保留公式。"),
    ("F15", "波浪能成本、成熟度与参考情景边界", ["S59", "S60", "S61", "S62", "S63", "S01"],
     "成本仅用于独立情景；技术尚未商业收敛，不能仅凭乐观学习曲线进入 reference。"),
]


def build_source_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source_cols = [
        "source_id", "short_name", "publication_year", "geography",
        "source_type", "title_or_scope", "url_or_doi", "independence_group",
    ]
    sources = pd.DataFrame(SOURCES, columns=source_cols)
    write_csv(sources, TABLES / "table_m04_17_deep_review_source_registry.csv")

    source_lookup = sources.set_index("source_id")
    evidence_rows: list[dict[str, object]] = []
    for family_id, family, source_ids, conclusion in FAMILIES:
        for source_id in source_ids:
            row = source_lookup.loc[source_id]
            evidence_rows.append(
                {
                    "family_id": family_id,
                    "review_unit": family,
                    "source_id": source_id,
                    "independence_group": row["independence_group"],
                    "publication_year": int(row["publication_year"]),
                    "geography": row["geography"],
                    "source_role": (
                        "CISPO_ORIGINAL_LINEAGE"
                        if source_id == "S01"
                        else "CHINA_TRIANGULATION"
                        if "China" in str(row["geography"])
                        else "INTERNATIONAL_COMPARATOR"
                    ),
                    "integrated_conclusion": conclusion,
                }
            )
    evidence = pd.DataFrame(evidence_rows)
    write_csv(evidence, TABLES / "table_m04_18_parameter_family_evidence_matrix.csv")

    qa_rows = []
    for family_id, group in evidence.groupby("family_id", sort=True):
        distinct = group["independence_group"].nunique()
        latest = int(group["publication_year"].max())
        china = int(group["geography"].str.contains("China", na=False).sum())
        qa_rows.append(
            {
                "family_id": family_id,
                "review_unit": group["review_unit"].iloc[0],
                "association_rows": len(group),
                "independent_source_groups": distinct,
                "minimum_required": MIN_INDEPENDENT_SOURCES,
                "china_specific_or_china_inclusive_sources": china,
                "latest_publication_year": latest,
                "status": "PASS" if distinct >= MIN_INDEPENDENT_SOURCES else "FAIL",
            }
        )
    source_count = pd.DataFrame(qa_rows)
    write_csv(source_count, TABLES / "table_m04_19_source_count_qa.csv")
    return sources, evidence, source_count


def build_cispo_logic() -> pd.DataFrame:
    rows = [
        ("S3.3.4", "onshore/offshore wind, UPV, DPV current CapEx", "2022 China current-cost anchors", "CREEI 2022 report", "China-specific absolute cost"),
        ("S3.3.4", "wind/PV/CSP future CapEx", "apply literature decline rates to China current cost; do not import NREL absolute USD cost", "Sun 2023; Li 2024; NREL ATB 2024; Zhang 2024", "hybrid China-anchor/relative-learning method"),
        ("S3.3.4", "VRE FOM", "wind 1.5%, PV 0.5%, CSP 1.0% of CapEx", "CISPO synthesis", "dimensionless ratio"),
        ("S3.5.1", "hydropower CapEx/FOM/lifetime", "13,319 CNY/kW; 2%; 40 y", "CISPO hydropower sources", "national planning scalar"),
        ("S3.5.2", "thermal/nuclear RUC", "technology-specific pmin, ramp, minimum up/down, start/shutdown and heat rate", "six China-system sources", "continuous relaxed UC"),
        ("S3.5.2 Table S14", "CCS technical performance", "90% capture; higher heat rate plus 5% net-output loss", "CISPO synthesis", "compound implemented penalty"),
        ("S3.5.3", "thermal and CCS CapEx", "Zhang & Chen trajectories; stable after 2040", "Zhang & Chen 2022", "China pathway source"),
        ("S3.5.3", "nuclear CapEx", "2,800 USD/kW in 2030 and 2,500 USD/kW in 2050; linear decrease extended to 2060", "Bowen et al. 2023", "original USD path"),
        ("S3.5.3", "FOM/VOM", "coal/gas 2%; CCS 2.5%; nuclear 1.5%; technology-specific VOM", "CISPO synthesis", "CapEx fraction plus absolute VOM"),
        ("S3.5.3", "coal price", "Jan-2020 provincial prices scaled to 2022 national 722/543 ratio", "NDRC; CNCA 2020/2022", "constructed provincial planning price"),
        ("S3.5.3", "gas/biomass/nuclear fuel", "regulated provincial gas benchmark; biomass 700 CNY/t; nuclear 0.069 CNY/kWh", "NDRC and China literature", "mixed source years"),
        ("S3.6.2", "PHS technical/economic parameters", "8 h; 0.88/0.88; 40 y; FOM 1.5%; VOM 1.5 CNY/MWh", "China PHS literature and plan", "national scalar"),
        ("S3.6.2", "battery technical/economic parameters", "4 h; 0.95/0.95; 15 y; FOM 1%; VOM 20 CNY/MWh", "Zhang & Chen; storage literature", "fixed-duration aggregate CapEx"),
        ("S3.7", "transmission", "voltage-specific line/substation cost; line 50 y; substation 25 y; 0.0032%/km loss", "China grid report and engineering studies", "preoptimized corridor design"),
        ("S3.8", "CCS cost", "capture 260 CNY/t; transport 0.8 CNY/t/km; storage 116 CNY/t", "Wang et al. 2022", "separate capture/T/S terms"),
        ("S3.9", "DAC", "four process routes; explicit CapEx/FOM/VOM/electricity/heat and conservative uptake learning ratios", "Young et al. 2023", "research scenario, not observed market cost"),
        ("S3.10", "WACC", "uniform 7.4% real", "CISPO China-system comparators", "single real social-planning rate"),
        ("S6", "CapEx uncertainty", "1.25x for wind, PV, CSP, PHS, battery and BECCS", "CISPO sensitivity design", "one-sided high-cost scenario"),
    ]
    out = pd.DataFrame(
        rows,
        columns=[
            "cispo_section", "parameter_block", "original_author_logic",
            "original_source_lineage", "interpretation_for_current_review",
        ],
    )
    write_csv(out, TABLES / "table_m04_16_cispo_original_author_parameter_logic.csv")
    return out


def build_candidate_v2() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    CANDIDATE_V2.mkdir(parents=True, exist_ok=True)

    capex = pd.read_csv(CANDIDATE_V1 / "technology_capex_by_year_2025_candidate.csv")
    capex["candidate_version"] = "v2_deep_integrated_review"
    capex["v2_change_reason"] = "unchanged from v1"
    nuclear_usd = {2030: 2800.0, 2040: 2650.0, 2050: 2500.0, 2060: 2350.0}
    nuclear_mask = capex["technology"].eq("nuclear")
    capex.loc[nuclear_mask, "capex_yuan_per_kw"] = [
        nuclear_usd[int(year)] * USD_CNY_2025
        for year in capex.loc[nuclear_mask, "year"]
    ]
    capex.loc[nuclear_mask, "conversion_rule"] = (
        "Bowen original USD/kW path x 7.1429 CNY/USD (2025 average FX); "
        "2040 interpolated and 2060 linearly extended"
    )
    capex.loc[nuclear_mask, "v2_change_reason"] = (
        "correct source-currency chain; do not CPI-inflate an old CNY conversion"
    )
    capex["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(capex, CANDIDATE_V2 / "technology_capex_by_year_2025_candidate_v2.csv")

    fuel = pd.read_csv(CANDIDATE_V1 / "province_fuel_prices_2025_candidate.csv")
    fuel["candidate_version"] = "v2_deep_integrated_review"
    fuel["v2_change_reason"] = (
        "values unchanged; multi-source review strengthens temporal caveat and sensitivity requirement"
    )
    fuel["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(fuel, CANDIDATE_V2 / "province_fuel_prices_2025_candidate_v2.csv")

    fuel_cost = pd.read_csv(
        CANDIDATE_V1 / "province_fuel_generation_cost_by_year_2025_candidate.csv"
    )
    fuel_cost["candidate_version"] = "v2_deep_integrated_review"
    fuel_cost["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(
        fuel_cost,
        CANDIDATE_V2 / "province_fuel_generation_cost_by_year_2025_candidate_v2.csv",
    )

    other = pd.read_csv(CANDIDATE_V1 / "other_parameter_values_2025_candidate.csv")
    other["candidate_version"] = "v2_deep_integrated_review"
    other["v2_change_reason"] = "unchanged from v1"
    transport = other["parameter"].eq("transport_cost")
    storage = other["parameter"].eq("storage_cost")
    other.loc[transport, "candidate_final_value"] = 0.50
    other.loc[transport, "conversion_or_selection_rule"] = (
        "China multi-source central planning value; evidence range about 0.18-0.80 CNY/tCO2/km"
    )
    other.loc[transport, "v2_change_reason"] = "replace single-study central value with China evidence synthesis"
    other.loc[storage, "candidate_final_value"] = 45.0
    other.loc[storage, "conversion_or_selection_rule"] = (
        "China multi-source 2030 planning midpoint; evidence range about 25-116 CNY/tCO2"
    )
    other.loc[storage, "v2_change_reason"] = "replace single-study central value with China evidence synthesis"
    other["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(other, CANDIDATE_V2 / "other_parameter_values_2025_candidate_v2.csv")
    return capex, fuel, fuel_cost, other


def build_price_ledger(capex: pd.DataFrame, other: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("Domestic CISPO CapEx except nuclear", "2022", "CNY", "2025", "CNY",
         "China CPI 2023=0.2%, 2024=0.2%, 2025=0.0%", "C_2025=C_2022*1.004004",
         "Retain real technology trajectory; change reporting price level only"),
        ("Nuclear CapEx", "source USD path", "USD", "2025", "CNY",
         "2025 average USD/CNY=7.1429", "C_2025CNY=C_sourceUSD*7.1429",
         "2030/2040/2050/2060 USD/kW=2800/2650/2500/2350"),
        ("Provincial coal/gas/biomass planning prices", "mixed constructed years", "USD/GJ",
         "2025", "CNY/GJ", "2025 average USD/CNY=7.1429",
         "P_CNY=P_publishedUSD*7.1429",
         "Currency conversion only; not a 2025 spot-price observation"),
        ("CCS capture cost", "2022 model basis", "CNY/tCO2", "2025", "CNY/tCO2",
         "China CPI cumulative=1.004004", "260*1.004004=261.041",
         "Retained CISPO central value"),
        ("CCS transport cost", "multi-year evidence synthesis", "CNY/tCO2/km", "2025",
         "CNY/tCO2/km", "direct China evidence synthesis", "central=0.50",
         "Sensitivity approximately 0.18/0.50/0.80"),
        ("CCS storage cost", "multi-year evidence synthesis", "CNY/tCO2", "2025",
         "CNY/tCO2", "direct China evidence synthesis", "central=45",
         "Sensitivity 25/45/116"),
        ("Absolute O&M/startup/shutdown/DAC monetary terms", "2022 model basis", "CNY",
         "2025", "CNY", "China CPI cumulative=1.004004", "C_2025=C_2022*1.004004",
         "Physical parameters are not price-normalized"),
    ]
    out = pd.DataFrame(
        rows,
        columns=[
            "monetary_block", "source_price_year", "source_currency",
            "target_price_year", "target_currency", "index_or_fx", "formula",
            "interpretation",
        ],
    )
    write_csv(out, TABLES / "table_m04_21_2025_price_conversion_ledger.csv")
    return out


def build_v2_summary(capex: pd.DataFrame, other: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tech_labels = {
        "onwind": "陆上风电", "offwind": "海上风电", "upv": "集中式光伏",
        "dpv": "分布式光伏", "battery": "4 h 电池", "phs": "8 h 抽蓄",
        "nuclear": "核电", "hydro": "常规水电", "coal": "煤电", "gas": "燃气",
    }
    rows = []
    for tech, label in tech_labels.items():
        subset = capex.loc[(capex["technology"] == tech) & (capex["year"] == 2030)]
        if subset.empty:
            continue
        row = subset.iloc[0]
        rows.append(
            {
                "parameter_family": "2030 CapEx",
                "parameter": label,
                "active_value": float(row["active_capex_yuan_per_kw"]),
                "v2_candidate_value": float(row["capex_yuan_per_kw"]),
                "unit": "2025 CNY/kW",
                "decision": "CHANGE_SOURCE_CHAIN" if tech == "nuclear" else "KEEP_AND_REBASE",
                "implementation_status": "PROPOSED_NOT_APPLIED",
            }
        )
    for parameter in ("capture_cost", "transport_cost", "storage_cost"):
        row = other.loc[other["parameter"].eq(parameter)].iloc[0]
        rows.append(
            {
                "parameter_family": "CCS",
                "parameter": parameter,
                "active_value": float(row["active_value"]),
                "v2_candidate_value": float(row["candidate_final_value"]),
                "unit": row["unit"],
                "decision": (
                    "KEEP_AND_REBASE" if parameter == "capture_cost"
                    else "CHANGE_MULTI_SOURCE_SYNTHESIS"
                ),
                "implementation_status": "PROPOSED_NOT_APPLIED",
            }
        )
    summary = pd.DataFrame(rows)
    write_csv(summary, TABLES / "table_m04_20_v2_candidate_value_summary.csv")

    changes = pd.DataFrame(
        [
            ("nuclear CapEx 2030/2040/2050/2060",
             "19377.28/18373.27/17319.07/16315.06",
             "20000.12/18928.69/17857.25/16785.82 CNY/kW",
             "return to original USD path and apply 2025 FX", "DATA_TABLE_AFTER_APPROVAL"),
            ("CCS transport", "0.185715 CNY/tCO2/km", "0.50 CNY/tCO2/km",
             "China multi-source central estimate; avoid one-paper dominance", "DATA_TABLE_AFTER_APPROVAL"),
            ("CCS storage", "35.7145 CNY/tCO2", "45 CNY/tCO2",
             "midpoint of China 2030 evidence; retain 25-116 range", "DATA_TABLE_AFTER_APPROVAL"),
            ("all other v1 candidate values", "v1", "unchanged",
             "five-source review did not justify a more comparable replacement", "NO_CHANGE"),
            ("battery power-energy split", "single CNY/kW and fixed 4 h", "not changed in v2",
             "requires formulation/interface review", "MODEL_CODE_REVIEW_REQUIRED"),
            ("CCS effective energy penalty", "heat rate plus 5% output loss", "not changed in v2",
             "requires formula-consistent effective-penalty audit", "MODEL_CODE_REVIEW_REQUIRED"),
        ],
        columns=[
            "item", "v1_candidate", "v2_candidate", "reason",
            "authorization_or_action",
        ],
    )
    write_csv(changes, TABLES / "table_m04_22_v1_to_v2_change_log.csv")
    return summary, changes


def build_manifest() -> pd.DataFrame:
    roles = {
        "technology_capex_by_year_2025_candidate_v2.csv": "2025-CNY technology CapEx; corrected nuclear source-currency chain",
        "province_fuel_prices_2025_candidate_v2.csv": "31-province planning fuel prices at 2025 FX",
        "province_fuel_generation_cost_by_year_2025_candidate_v2.csv": "derived province-year-technology fuel costs",
        "other_parameter_values_2025_candidate_v2.csv": "RUC/O&M/storage/finance/CCS/wave candidate values",
    }
    rows = []
    for name, role in roles.items():
        path = CANDIDATE_V2 / name
        rows.append(
            {
                "candidate_file": f"candidate_inputs_v2/{name}",
                "role": role,
                "row_count": len(pd.read_csv(path)),
                "sha256": sha256(path),
                "implementation_status": "PROPOSED_NOT_APPLIED",
                "production_input_modified": False,
            }
        )
    out = pd.DataFrame(rows)
    write_csv(out, TABLES / "table_m04_23_v2_candidate_manifest.csv")
    return out


def build_qa(source_count: pd.DataFrame, capex: pd.DataFrame, other: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(check: str, passed: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "check": check,
                "status": "PASS" if passed else "FAIL",
                "observed": observed,
                "expected": expected,
            }
        )

    add(
        "all_review_units_have_at_least_five_independent_sources",
        source_count["status"].eq("PASS").all(),
        int(source_count["independent_source_groups"].min()),
        f">={MIN_INDEPENDENT_SOURCES}",
    )
    add("review_unit_count", len(source_count) == 15, len(source_count), 15)
    add("source_registry_unique_ids", len({row[0] for row in SOURCES}) == len(SOURCES), len(SOURCES), "all unique")
    add("candidate_v2_capex_rows", len(capex) == 76, len(capex), 76)
    nuclear = capex.loc[capex["technology"].eq("nuclear")].sort_values("year")
    add(
        "nuclear_uses_original_usd_path_at_2025_fx",
        np.allclose(
            nuclear["capex_yuan_per_kw"],
            np.array([2800, 2650, 2500, 2350]) * USD_CNY_2025,
        ),
        "/".join(f"{value:.2f}" for value in nuclear["capex_yuan_per_kw"]),
        "20000.12/18928.69/17857.25/16785.82",
    )
    transport = float(other.loc[other["parameter"].eq("transport_cost"), "candidate_final_value"].iloc[0])
    storage = float(other.loc[other["parameter"].eq("storage_cost"), "candidate_final_value"].iloc[0])
    add("ccs_transport_multisource_central", np.isclose(transport, 0.50), transport, 0.50)
    add("ccs_storage_multisource_central", np.isclose(storage, 45.0), storage, 45.0)
    add(
        "all_v2_candidates_not_applied",
        capex["implementation_status"].eq("PROPOSED_NOT_APPLIED").all()
        and other["implementation_status"].eq("PROPOSED_NOT_APPLIED").all(),
        "PROPOSED_NOT_APPLIED",
        "PROPOSED_NOT_APPLIED",
    )
    out = pd.DataFrame(checks)
    write_csv(out, QA / "deep_integrated_review_validation.csv")
    return out


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    build_cispo_logic()
    _, evidence, source_count = build_source_tables()
    capex, fuel, fuel_cost, other = build_candidate_v2()
    build_price_ledger(capex, other)
    build_v2_summary(capex, other)
    manifest = build_manifest()
    qa = build_qa(source_count, capex, other)
    summary = {
        "module": "04_thermal_nuclear_storage_technoeconomics",
        "package": "deep_integrated_review_v2",
        "generated_at": "2026-07-28",
        "price_basis": "2025 constant CNY",
        "production_inputs_modified": False,
        "review_units": len(source_count),
        "unique_sources": len(SOURCES),
        "evidence_associations": len(evidence),
        "minimum_independent_sources_per_review_unit": int(
            source_count["independent_source_groups"].min()
        ),
        "candidate_files": len(manifest),
        "qa_pass": int(qa["status"].eq("PASS").sum()),
        "qa_fail": int(qa["status"].eq("FAIL").sum()),
        "terminal_marker": (
            "FINAL_M04_DEEP_REVIEW_2025CNY_PASS"
            if qa["status"].eq("PASS").all()
            else "M04_DEEP_REVIEW_QA_FAIL"
        ),
    }
    (QA / "deep_integrated_review_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if qa["status"].eq("FAIL").any():
        raise RuntimeError(
            "Deep-review QA failed:\n"
            + qa.loc[qa["status"].eq("FAIL")].to_string(index=False)
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
