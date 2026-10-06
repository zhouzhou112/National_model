"""Read-only overview of a preserved 8760 h result, including unaccepted data.

Outputs: PNG/SVG/PDF overviews, exact grouped CSVs, and inline-viz data JSON.
No solver, presolve, clipping, threshold filtering, or acceptance changes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from verify_preserved_backup import verify

GROUPS = {
    "陆上风电": ["onwind"], "海上风电": ["offwind"],
    "集中式光伏": ["upv"], "分布式光伏": ["dpv"],
    "煤电及煤热电": ["coal", "coalccs", "cchp", "cchpccs"],
    "气电及气热电": ["gas", "gasccs", "gchp", "gchpccs"],
    "生物质": ["bio", "bioccs"], "核电": ["nuclear"],
    "常规水电": ["ror", "reservoir", "hydro_aggregate"], "波浪能": ["wave"],
}
MONTHLY = {
    "风电": ["onwind", "offwind"], "光伏": ["upv", "dpv"],
    "化石燃料": GROUPS["煤电及煤热电"] + GROUPS["气电及气热电"],
    "生物质及波浪能": GROUPS["生物质"] + ["wave"],
    "核电": ["nuclear"], "常规水电": GROUPS["常规水电"],
}


def write_json(data, path):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root, out = args.result_dir.resolve(), args.output_dir.resolve()
    if root == out or root in out.parents:
        parser.error("Use an external output directory; preserve source manifest")
    out.mkdir(parents=True, exist_ok=True)
    check = verify(root, subset=True)
    if check["errors"]:
        raise ValueError("Analysis input hash mismatch")
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    summary, carbon, qc = read("run_summary.json"), read("annual_carbon_ccs.json"), read("solution_qc.json")
    if summary["optimization_hours"] != 8760:
        raise ValueError("This overview requires an actual full-year result")
    capacity = pd.read_csv(root / "annual_capacity_by_technology.csv")
    generation = pd.read_csv(root / "annual_generation_by_technology.csv")
    cost = pd.read_csv(root / "cost_components.csv")
    hourly = pd.read_csv(root / "hourly_national_balance.csv.gz")
    monthly = pd.read_csv(root / "monthly_energy_by_technology.csv")
    if len(hourly) != 8760 or not np.array_equal(hourly.hour_index, np.arange(8760)):
        raise ValueError("Hourly index is not a complete ordered 8760 h year")
    time = pd.DatetimeIndex(pd.to_datetime(hourly.datetime_bj))
    if time.has_duplicates or not (time[1:] - time[:-1] == pd.Timedelta(hours=1)).all():
        raise ValueError("Hourly timestamps are not consecutive")
    if set(generation.technology) != {t for g in GROUPS.values() for t in g}:
        raise ValueError("Technology group map does not cover source exactly")
    tech_rows = []
    for label, technologies in GROUPS.items():
        cap = capacity.loc[capacity.technology.isin(technologies)]
        gen = generation.loc[generation.technology.isin(technologies), "generation_gwh"].sum()
        tech_rows.append(dict(label=label, technologies="|".join(technologies),
                             capacity_gw=float(cap.capacity.sum()), new_capacity_gw=float(cap.new_capacity.sum()),
                             generation_twh=float(gen / 1000)))
    grouped = pd.DataFrame(tech_rows)
    grouped.to_csv(out / "grouped_generation_capacity.csv", index=False, encoding="utf-8-sig")
    cap_rows = [[r["label"], r["capacity_gw"]] for r in tech_rows]
    cap_rows += [["电池储能", float(capacity.loc[capacity.technology.eq("battery"), "capacity"].sum())],
                 ["抽水蓄能", float(capacity.loc[capacity.technology.eq("phs"), "capacity"].sum())]]
    gen_rows = [[r["label"], r["generation_twh"]] for r in tech_rows]
    value = "value_million_cny_model_accounting_period"
    planning = float(cost.loc[cost.accounting_scope.eq("ANNUALIZED_PLANNING_COST"), value].sum())
    operation = float(cost.loc[cost.cost_component.eq("annual_operation"), value].sum())
    op_details = float(cost.loc[cost.accounting_scope.eq("SELECTED_HORIZON_OPERATION_COST"), value].sum())
    cost_map = {
        "燃料": ["operating_fuel"], "风光投资及固定运维": ["vre_investment", "vre_fixed_om"],
        "火电核电投资及固定运维": ["thermal_nuclear_investment", "thermal_nuclear_fixed_om"],
        "水电投资及固定运维": ["hydro_investment", "hydro_fixed_om"],
        "储能投资及固定运维": ["storage_investment", "storage_fixed_om"],
        "输电及接网投资": ["transmission_investment", "load_center_intra_transmission_investment", "spur", "hydro_spur", "trunk"],
        "其他运行费用": [str(v) for v in cost.cost_component if str(v).startswith("operating_") and v != "operating_fuel"],
        "CCS、DAC及波浪能固定费用": ["dac", "ccs_capture", "co2_transport_injection", "wave_investment", "wave_fixed_om"],
    }
    covered = [t for group in cost_map.values() for t in group]
    if len(set(covered)) != len(covered) or set(covered) != set(cost.cost_component) - {"annual_operation"}:
        raise ValueError("Cost grouping duplicates or omits a non-composite row")
    costs = [[k, float(cost.loc[cost.cost_component.isin(v), value].sum()) / 1e6] for k, v in cost_map.items()]
    pd.DataFrame(costs, columns=["cost_group", "trillion_2025_cny"]).to_csv(out / "grouped_cost.csv", index=False, encoding="utf-8-sig")
    monthly_rows = []
    for _, row in monthly.iterrows():
        item = {"month": int(row.month)}
        for label, technologies in MONTHLY.items():
            item[label] = float(sum(row[t + "_generation_gwh"] for t in technologies) / 1000)
        item["负荷"] = float(row.load_gwh / 1000)
        monthly_rows.append(item)
    month_frame = pd.DataFrame(monthly_rows)
    month_frame.to_csv(out / "monthly_generation_twh.csv", index=False, encoding="utf-8-sig")
    daily = hourly.assign(day=hourly.hour_index // 24 + 1).groupby("day").agg(
        load_mean_gw=("load_gw", "mean"), load_min_gw=("load_gw", "min"), load_max_gw=("load_gw", "max"),
        vre_mean_gw=("vre_generation_gw", "mean"), thermal_nuclear_mean_gw=("thermal_nuclear_generation_gw", "mean"))
    daily.to_csv(out / "daily_operation_gw.csv", encoding="utf-8-sig")
    gen_total = float(generation.generation_gwh.sum())
    accounting_residual = (gen_total + summary["period_storage_discharge_gwh"] - summary["period_load_gwh"]
                           - summary["period_storage_charge_gwh"] - summary["period_interprovincial_transmission_losses_gwh"]
                           - float(hourly.dac_load_gw.sum()))
    vre_total = float(generation.loc[generation.technology.isin(["onwind", "offwind", "upv", "dpv"]), "generation_gwh"].sum())
    monthly_residual = float(month_frame[list(MONTHLY)].to_numpy().sum() * 1000 - gen_total)
    # Sanity evidence is descriptive, not a replacement acceptance gate.
    derived = {"year": 2030, "hours": 8760, "qc_status": qc["status"],
               "hard_pass": sum(v is True for v in qc["hard_checks"].values()), "hard_total": len(qc["hard_checks"]),
               "failed_checks": [k for k, v in qc["hard_checks"].items() if v is not True],
               "scientifically_accepted": False, "author_decision": "PENDING",
               "generation_twh": gen_total / 1000, "load_twh": summary["period_load_gwh"] / 1000,
               "generation_capacity_gw": float(grouped.capacity_gw.sum()),
               "wind_solar_generation_share": vre_total / gen_total,
               "wind_solar_curtailment_ratio_available": summary["period_vre_curtailment_gwh"] / (vre_total + summary["period_vre_curtailment_gwh"]),
               "net_emissions_mtco2": carbon["annual_net_emissions_mtco2"],
               "carbon_limit_mtco2": carbon["carbon_limit_mtco2"],
               "primary_objective_million_cny": summary["objective_million_cny_per_year"],
               "planning_cost_million_cny": planning, "annual_operation_million_cny": operation,
               "operation_detail_minus_rollup_million_cny": op_details - operation,
               "primary_components_minus_objective_million_cny": planning + operation - summary["objective_million_cny_per_year"],
               "raw_cost_intensity_cny_per_kwh": summary["objective_million_cny_per_year"] / summary["period_baseline_load_gwh"],
               "monthly_annual_generation_residual_gwh": monthly_residual,
               "national_energy_closure_residual_gwh": accounting_residual,
               "input_manifest_sha256": check["manifest_sha256"], "verified_input_files": check["checked_count"],
               "aggregation": "Technology sums without threshold filters; costs exclude composite annual_operation to avoid double counting; daily plot uses explicit 24-hour means; full hourly values retained in source.",
               "technology_mapping": GROUPS, "monthly_mapping": MONTHLY, "cost_mapping": cost_map}
    write_json(derived, out / "analysis_summary.json")
    inline = {"capacity": cap_rows, "generation": gen_rows, "cost": costs,
              "carbon": [["净排放", carbon["annual_net_emissions_mtco2"]], ["模型上限", carbon["carbon_limit_mtco2"]]],
              "monthly": monthly_rows, "month_series": list(MONTHLY),
              "daily": [[int(i), *[round(float(row[k]), 4) for k in ["load_mean_gw", "vre_mean_gw", "thermal_nuclear_mean_gw"]]] for i, row in daily.iterrows()]}
    write_json(inline, out / "inline_data.json")
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                         "font.size": 10, "axes.unicode_minus": False, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 220})
    fig, axes = plt.subplots(2, 2, figsize=(15, 11), constrained_layout=True)
    fig.suptitle("2030 年首次完整 Stage A 结果 | 8760 h\nQC FAIL：56/58 项通过 · 科学采用待作者判断", fontsize=17)
    for ax, rows, title, unit, color in [
        (axes[0, 0], cap_rows, "a  年末容量（含两类储能功率）", "容量 (GW)", "#3976a8"),
        (axes[0, 1], gen_rows, "b  年度发电量（不重复计入储能放电）", "发电量 (TWh)", "#269b87"),
        (axes[1, 0], costs, "c  年化投资、固定运维与全年运行费用", "万亿元（2025 年不变价）", "#bc8840"),
        (axes[1, 1], inline["carbon"], "d  净碳排放与约束上限", r"排放量 (MtCO$_2$)", "#8672a5"),
    ]:
        labels, values = zip(*rows)
        ax.barh(np.arange(len(rows)), values, color=color, height=.64)
        ax.set_yticks(np.arange(len(rows)), labels)
        ax.invert_yaxis()
        ax.set_xlabel(unit)
        ax.set_title(title, loc="left", pad=14)
        lo, hi = min(0, min(values)), max(values)
        ax.set_xlim(lo, hi * 1.2)
        ax.grid(axis="x", color="#dddddd", linewidth=.5)
        ax.set_axisbelow(True)
        for i, val in enumerate(values):
            label = f"{val:.2e}" if abs(val) < .005 and val != 0 else (f"{val:,.3f}" if hi < 10 else f"{val:,.1f}")
            ax.text(val + hi * .018, i, label, va="center", fontsize=9)
    fig.supxlabel("原始值未筛除；微小值以科学计数法标注。成本分项存在原始 QC 记录的约 354 元闭合差；未修改容差。", fontsize=9)
    for extension in ["png", "pdf", "svg"]:
        fig.savefig(out / f"2030_stage_a_overview.{extension}")
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(15, 11), constrained_layout=True)
    fig.suptitle("2030 年运行结构 | QC FAIL · 原始恢复结果", fontsize=16)
    colors = ["#3976a8", "#e6ad45", "#775b53", "#a56893", "#6f75af", "#269b87"]
    bottom = np.zeros(12)
    for label, color in zip(MONTHLY, colors):
        axes[0].bar(month_frame.month, month_frame[label], bottom=bottom, label=label, color=color, width=.76)
        bottom += month_frame[label].to_numpy()
    axes[0].plot(month_frame.month, month_frame["负荷"], "k.-", label="负荷")
    axes[0].set(xlabel="月份（北京时间）", ylabel="电量 (TWh)", title="a  月度一次发电构成与负荷（差额含储能净耗电和输电损耗）", xticks=range(1, 13))
    axes[0].legend(ncol=7, loc="upper left", frameon=False)
    axes[0].set_ylim(0, max(bottom.max(), month_frame["负荷"].max()) * 1.22)
    for ax, column, title in [(axes[1], "load_gw", "b  逐小时负荷"), (axes[2], "vre_generation_gw", "c  逐小时风光及波浪能出力")]:
        matrix = hourly[column].to_numpy().reshape(365, 24).T
        image = ax.imshow(matrix, aspect="auto", origin="lower", extent=[.5, 365.5, -.5, 23.5], cmap="cividis")
        ax.set(xlabel="年内日序（无抽样、无平滑）", ylabel="小时（北京时间）", title=title, yticks=[0, 6, 12, 18, 23])
        fig.colorbar(image, ax=ax, label="功率 (GW)", pad=.01)
    for extension in ["png", "pdf", "svg"]:
        fig.savefig(out / f"2030_stage_a_operation.{extension}")
    plt.close(fig)
    print(json.dumps({k: v for k, v in derived.items() if not k.endswith("mapping")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
