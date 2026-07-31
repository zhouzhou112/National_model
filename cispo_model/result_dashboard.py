"""Scope-aware, dependency-free result dashboard for completed CISPO runs."""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ANNUALIZED_PLANNING_SCOPE = "ANNUALIZED_PLANNING_COST"
SELECTED_HORIZON_OPERATION_SCOPE = "SELECTED_HORIZON_OPERATION_COST"
COMPOSITE_COST_SCOPE = "COMPOSITE_SEE_COMPONENT_ROWS"


def _read_json(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise FileNotFoundError(path)
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _reference_load_from_manifest(
    result_dir: Path,
    planning_year: int,
) -> tuple[float | None, str | None]:
    """Recover the immutable full-year baseline load for an older result."""
    manifest_path = result_dir / "input_manifest.csv"
    if not manifest_path.is_file():
        return None, None
    manifest = pd.read_csv(manifest_path)
    required = {"logical_path", "resolved_path"}
    if not required.issubset(manifest.columns):
        return None, None
    matches = manifest.loc[
        manifest.logical_path.astype(str).str.replace("\\", "/", regex=False).str.endswith(
            "load/hourly_load_2025_2060.csv.gz"
        )
    ]
    if matches.empty:
        return None, None
    row = matches.iloc[0]
    candidates = [Path(str(row.resolved_path))]
    data_root = os.environ.get("CISPO_DATA_ROOT")
    if data_root:
        logical_path = str(row.logical_path).replace("\\", "/")
        candidates.append(Path(data_root) / Path(logical_path))
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        return None, None
    total = 0.0
    matched_rows = 0
    for chunk in pd.read_csv(
        source,
        usecols=["year", "demand_gw"],
        chunksize=500_000,
    ):
        selected = chunk.loc[chunk.year.eq(planning_year), "demand_gw"]
        total += float(selected.sum())
        matched_rows += int(selected.notna().sum())
    if matched_rows == 0 or not np.isfinite(total) or total <= 0.0:
        return None, None
    return total, f"input_manifest:{row.logical_path}"


def _top_rows(
    frame: pd.DataFrame,
    *,
    label_column: str,
    value_column: str,
    limit: int = 8,
) -> list[dict[str, float | str]]:
    if frame.empty or label_column not in frame or value_column not in frame:
        return []
    selected = frame[[label_column, value_column]].copy()
    selected[value_column] = pd.to_numeric(selected[value_column], errors="coerce")
    selected = (
        selected.dropna()
        .loc[lambda item: item[value_column].gt(1e-12)]
        .groupby(label_column, as_index=False)[value_column]
        .sum()
        .sort_values(value_column, ascending=False)
    )
    if len(selected) > limit:
        other = float(selected.iloc[limit - 1 :][value_column].sum())
        selected = selected.iloc[: limit - 1].copy()
        selected.loc[len(selected)] = ["Other", other]
    return [
        {"label": str(row[label_column]), "value": float(row[value_column])}
        for _, row in selected.iterrows()
    ]


def _sum_columns(frame: pd.DataFrame, columns: Iterable[str]) -> float:
    total = 0.0
    for column in columns:
        if column in frame:
            total += float(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).sum())
    return total


def collect_result_dashboard(
    result_dir: str | Path,
    *,
    reference_load_gwh: float | None = None,
) -> dict[str, Any]:
    """Read a completed result directory and derive scope-safe headline metrics."""
    result_dir = Path(result_dir)
    solve = _read_json(result_dir / "solve_report.json")
    qc = _read_json(result_dir / "solution_qc.json")
    summary = _read_json(result_dir / "run_summary.json")
    carbon = _read_json(result_dir / "annual_carbon_ccs.json", required=False)

    cost = pd.read_csv(result_dir / "cost_components.csv")
    required_cost_columns = {
        "value_million_cny_model_accounting_period",
        "accounting_scope",
    }
    if not required_cost_columns.issubset(cost.columns):
        raise ValueError(
            "cost_components.csv is missing the scope-aware cost columns"
        )
    cost_values = pd.to_numeric(
        cost["value_million_cny_model_accounting_period"], errors="raise"
    )
    planning_cost = float(
        cost_values.loc[cost.accounting_scope.eq(ANNUALIZED_PLANNING_SCOPE)].sum()
    )
    operating_cost = float(
        cost_values.loc[
            cost.accounting_scope.eq(SELECTED_HORIZON_OPERATION_SCOPE)
        ].sum()
    )
    composite_cost = float(
        cost_values.loc[cost.accounting_scope.eq(COMPOSITE_COST_SCOPE)].sum()
    )
    reconstructed_objective = planning_cost + operating_cost
    reported_objective = _finite_float(
        qc.get("objective_value_million_cny")
    )
    if reported_objective is None:
        reported_objective = _finite_float(
            solve.get("objective_value_million_cny")
        )
    objective_residual = (
        reconstructed_objective - reported_objective
        if reported_objective is not None
        else None
    )
    objective_tolerance = max(
        1e-5,
        1e-10 * max(abs(reported_objective or 0.0), 1.0),
    )
    if (
        objective_residual is not None
        and abs(objective_residual) > objective_tolerance
    ):
        raise ValueError(
            "Scope-aware detailed cost rows do not reconstruct the reported "
            f"objective: residual={objective_residual:.12g} million CNY, "
            f"tolerance={objective_tolerance:.12g}"
        )

    planning_year = int(summary.get("planning_year", solve.get("planning_year")))
    optimization_hours = int(
        summary.get("optimization_hours", solve.get("optimization_hours"))
    )
    result_use = str(
        summary.get(
            "result_use",
            "SCIENTIFIC_PRODUCTION"
            if optimization_hours == 8760
            else "TEST_ONLY_TRUNCATED_HORIZON",
        )
    )
    configured_hours = int(
        summary.get(
            "configured_hours",
            carbon.get(
                "configured_hours",
                optimization_hours
                if result_use == "SCIENTIFIC_PRODUCTION"
                else 8760,
            ),
        )
    )
    full_year = (
        result_use == "SCIENTIFIC_PRODUCTION"
        and optimization_hours == configured_hours
    )

    reference_source = "explicit_argument"
    full_year_reference_load = _finite_float(reference_load_gwh)
    if full_year_reference_load is None:
        full_year_reference_load = _finite_float(
            summary.get("full_year_reference_baseline_load_gwh")
        )
        reference_source = "run_summary:full_year_reference_baseline_load_gwh"
    if full_year_reference_load is None:
        full_year_reference_load, recovered_source = _reference_load_from_manifest(
            result_dir,
            planning_year,
        )
        reference_source = recovered_source or "unavailable"

    period_baseline_load = _finite_float(
        summary.get("period_baseline_load_gwh", summary.get("annual_load_gwh"))
    )
    period_effective_load = _finite_float(
        summary.get("period_load_gwh", summary.get("annual_load_gwh"))
    )
    planning_intensity = _ratio(planning_cost, full_year_reference_load)
    operating_intensity = _ratio(operating_cost, period_baseline_load)
    full_year_system_intensity = (
        _ratio(reconstructed_objective, full_year_reference_load)
        if full_year
        else None
    )

    hard_checks = qc.get("hard_checks", {})
    if not isinstance(hard_checks, dict):
        hard_checks = {}
    passed_hard_checks = sum(value is True for value in hard_checks.values())
    total_hard_checks = len(hard_checks)

    capacity = pd.read_csv(result_dir / "annual_capacity_by_technology.csv")
    generation = pd.read_csv(result_dir / "annual_generation_by_technology.csv")
    capacity_rows = _top_rows(
        capacity.loc[
            capacity.get("unit", pd.Series(index=capacity.index, dtype=str)).eq("GW")
        ],
        label_column="technology",
        value_column="capacity",
    )
    generation_rows = _top_rows(
        generation,
        label_column="technology",
        value_column="generation_gwh",
    )
    for row in generation_rows:
        row["value"] = float(row["value"]) / 1000.0

    flexible_path = result_dir / "annual_flexible_load_by_province.csv"
    flexible = (
        pd.read_csv(flexible_path)
        if flexible_path.is_file()
        else pd.DataFrame()
    )
    baseline_peak = _finite_float(
        summary.get("period_baseline_peak_load_gw")
    )
    effective_peak = _finite_float(
        summary.get(
            "period_effective_peak_load_gw",
            summary.get("peak_load_gw"),
        )
    )
    if baseline_peak is None:
        national_path = result_dir / "hourly_national_balance.csv.gz"
        if national_path.is_file():
            national = pd.read_csv(
                national_path,
                usecols=["baseline_load_gw", "load_gw"],
            )
            baseline_peak = float(national.baseline_load_gw.max())
            effective_peak = float(national.load_gw.max())

    carbon_limit = _finite_float(
        carbon.get(
            "selected_horizon_carbon_limit_mtco2",
            qc.get("carbon_limit_mtco2"),
        )
    )
    carbon_actual = _finite_float(
        carbon.get(
            "annual_net_emissions_mtco2",
            qc.get("annual_net_emissions_mtco2"),
        )
    )
    storage_path = result_dir / "annual_storage_operation_by_technology.csv"
    storage = pd.read_csv(storage_path) if storage_path.is_file() else pd.DataFrame()

    cost_warning = (
        "Full-year total system cost intensity is valid for this accepted "
        "full-year result."
        if full_year
        else "Truncated gate: annualized planning and selected-horizon operating "
        "intensities have different time scopes and must not be added or reported "
        "as LCOE."
    )
    payload = {
        "schema_version": "cispo_result_dashboard_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "identity": {
            "planning_year": planning_year,
            "scenario_id": str(
                summary.get("scenario_id", solve.get("scenario_id", "UNKNOWN"))
            ),
            "scenario_family": str(
                summary.get(
                    "scenario_family",
                    solve.get("scenario_family", "UNKNOWN"),
                )
            ),
            "optimization_hours": optimization_hours,
            "configured_hours": configured_hours,
            "result_use": result_use,
            "is_full_year_scientific_result": full_year,
        },
        "acceptance": {
            "solver_status": str(solve.get("status", "UNKNOWN")),
            "solution_qc_status": str(qc.get("status", "UNKNOWN")),
            "hard_checks_passed": passed_hard_checks,
            "hard_checks_total": total_hard_checks,
            "all_hard_checks_pass": (
                total_hard_checks > 0 and passed_hard_checks == total_hard_checks
            ),
            "solver_runtime_seconds": _finite_float(solve.get("runtime_seconds")),
            "barrier_iterations": int(
                solve.get("iteration_counts", {}).get("barrier", 0)
            ),
            "peak_process_tree_rss_gib": _finite_float(
                solve.get("runtime_memory", {}).get("peak_process_tree_rss_gib")
            ),
            "result_manifest_note": (
                "This dashboard is generated before result-manifest finalization "
                "and is included in the final SHA256 manifest."
            ),
        },
        "cost_accounting": {
            "annualized_planning_cost_million_cny_per_year": planning_cost,
            "selected_horizon_operating_cost_million_cny": operating_cost,
            "composite_operation_rollup_million_cny_excluded_from_sum": composite_cost,
            "reconstructed_objective_million_cny": reconstructed_objective,
            "reported_objective_million_cny": reported_objective,
            "objective_reconstruction_residual_million_cny": objective_residual,
            "objective_reconstruction_tolerance_million_cny": objective_tolerance,
            "objective_reconstruction_pass": (
                objective_residual is not None
                and abs(objective_residual) <= objective_tolerance
            ),
            "full_year_reference_baseline_load_gwh": full_year_reference_load,
            "full_year_reference_load_source": reference_source,
            "selected_horizon_reference_baseline_load_gwh": period_baseline_load,
            "annualized_planning_cost_intensity_cny_per_kwh": planning_intensity,
            "selected_horizon_operating_cost_intensity_cny_per_kwh": operating_intensity,
            "scientific_full_year_system_cost_intensity_cny_per_kwh": (
                full_year_system_intensity
            ),
            "intensity_denominator": (
                "Immutable baseline electricity demand; 1 million CNY/GWh "
                "equals 1 CNY/kWh."
            ),
            "interpretation_warning": cost_warning,
        },
        "demand_and_flexibility": {
            "selected_horizon_baseline_load_gwh": period_baseline_load,
            "selected_horizon_effective_load_gwh": period_effective_load,
            "selected_horizon_baseline_peak_load_gw": baseline_peak,
            "selected_horizon_effective_peak_load_gw": effective_peak,
            "selected_horizon_peak_change_gw": (
                effective_peak - baseline_peak
                if baseline_peak is not None and effective_peak is not None
                else None
            ),
            "contracted_thermal_flexibility_gw": _sum_columns(
                flexible,
                [
                    "contracted_heating_flexibility_gw",
                    "contracted_cooling_flexibility_gw",
                ],
            ),
            "contracted_ev_v1g_flexibility_gw": _sum_columns(
                flexible,
                ["contracted_ev_v1g_flexibility_gw"],
            ),
            "contracted_ev_v2g_flexibility_gw": _sum_columns(
                flexible,
                ["contracted_ev_v2g_flexibility_gw"],
            ),
            "firm_flexible_capacity_credit_gw": _finite_float(
                qc.get("total_v5_firm_capacity_credit_gw")
            ),
            "firm_capacity_credit_interpretation": (
                "Derived from province-specific full-year immutable baseline "
                "peak windows and configured derating; it is not the selected-"
                "horizon national peak change."
            ),
            "ev_v2g_charge_gwh": _sum_columns(
                flexible,
                ["ev_v2g_charge_gwh"],
            ),
            "ev_v2g_discharge_gwh": _sum_columns(
                flexible,
                ["ev_v2g_discharge_gwh"],
            ),
        },
        "system": {
            "selected_horizon_generation_gwh": _finite_float(
                summary.get("period_generation_gwh")
            ),
            "selected_horizon_vre_curtailment_gwh": _finite_float(
                summary.get("period_vre_curtailment_gwh")
            ),
            "selected_horizon_storage_charge_gwh": _finite_float(
                summary.get("period_storage_charge_gwh")
            ),
            "selected_horizon_storage_discharge_gwh": _finite_float(
                summary.get("period_storage_discharge_gwh")
            ),
            "installed_storage_power_gw": (
                float(
                    pd.to_numeric(
                        storage.get(
                            "power_capacity_gw",
                            pd.Series(dtype=float),
                        ),
                        errors="coerce",
                    ).fillna(0.0).sum()
                )
            ),
            "minimum_capacity_margin_gw": _finite_float(
                qc.get("minimum_capacity_margin_gw")
            ),
            "minimum_up_reserve_margin_gw": _finite_float(
                qc.get("minimum_up_reserve_margin_gw")
            ),
            "minimum_down_reserve_margin_gw": _finite_float(
                qc.get("minimum_down_reserve_margin_gw")
            ),
            "minimum_inertia_margin_gw_s": _finite_float(
                qc.get("minimum_inertia_margin_gw_s")
            ),
            "carbon_accounting_scope": str(
                carbon.get("accounting_scope", "UNKNOWN")
            ),
            "net_emissions_mtco2": carbon_actual,
            "carbon_limit_mtco2": carbon_limit,
        },
        "charts": {
            "installed_capacity_gw": capacity_rows,
            "selected_horizon_generation_twh": generation_rows,
        },
    }
    return payload


def _format_number(value: Any, digits: int = 2, *, na: str = "N/A") -> str:
    number = _finite_float(value)
    if number is None:
        return na
    return f"{number:,.{digits}f}"


def _svg_text(
    x: float,
    y: float,
    text: str,
    *,
    size: int = 16,
    weight: int = 400,
    fill: str = "#1f2937",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, DejaVu Sans, '
        f'sans-serif" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{html.escape(text)}</text>'
    )


def _svg_bar_panel(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    title: str,
    rows: list[dict[str, Any]],
    unit: str,
    color: str,
) -> list[str]:
    elements = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="16" fill="#ffffff" stroke="#dbe3ec"/>',
        _svg_text(x + 24, y + 34, title, size=19, weight=700),
    ]
    if not rows:
        elements.append(_svg_text(x + 24, y + 78, "No positive values", fill="#6b7280"))
        return elements
    maximum = max(float(row["value"]) for row in rows)
    label_width = 145
    value_width = 105
    plot_x = x + 24 + label_width
    plot_width = width - 48 - label_width - value_width
    start_y = y + 65
    row_height = min(30.0, (height - 86) / max(len(rows), 1))
    for index, row in enumerate(rows):
        row_y = start_y + index * row_height
        value = float(row["value"])
        bar_width = plot_width * value / max(maximum, 1e-12)
        label = str(row["label"])
        if len(label) > 20:
            label = label[:18] + "..."
        elements.extend(
            [
                _svg_text(plot_x - 10, row_y + 15, label, size=13, anchor="end"),
                f'<rect x="{plot_x}" y="{row_y}" width="{plot_width}" height="18" rx="4" fill="#eef2f7"/>',
                f'<rect x="{plot_x}" y="{row_y}" width="{bar_width:.2f}" height="18" rx="4" fill="{color}"/>',
                _svg_text(
                    plot_x + plot_width + 10,
                    row_y + 15,
                    f"{value:,.1f} {unit}",
                    size=12,
                    fill="#4b5563",
                ),
            ]
        )
    return elements


def _write_svg_dashboard(payload: dict[str, Any], path: Path) -> None:
    identity = payload["identity"]
    acceptance = payload["acceptance"]
    costs = payload["cost_accounting"]
    flex = payload["demand_and_flexibility"]
    system = payload["system"]
    charts = payload["charts"]
    width, height = 1600, 1120
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f5f7fa"/>',
        '<rect x="0" y="0" width="1600" height="126" fill="#10233f"/>',
        _svg_text(
            42,
            48,
            f"CISPO {identity['planning_year']} core result dashboard",
            size=28,
            weight=700,
            fill="#ffffff",
        ),
        _svg_text(
            42,
            82,
            (
                f"{identity['scenario_id']}  |  {identity['optimization_hours']} h / "
                f"{identity['configured_hours']} h  |  {identity['result_use']}"
            ),
            size=16,
            fill="#c8d7ea",
        ),
    ]
    badges = [
        ("Solver", acceptance["solver_status"]),
        ("QC", acceptance["solution_qc_status"]),
        (
            "Hard checks",
            f"{acceptance['hard_checks_passed']}/{acceptance['hard_checks_total']}",
        ),
        (
            "Runtime",
            f"{_format_number(acceptance['solver_runtime_seconds'], 0)} s",
        ),
    ]
    for index, (label, value) in enumerate(badges):
        badge_x = 900 + index * 165
        ok = value in {"OPTIMAL", "PASS"} or (
            label == "Hard checks"
            and acceptance["all_hard_checks_pass"]
        )
        fill = "#147d64" if ok else "#8a5a12"
        elements.extend(
            [
                f'<rect x="{badge_x}" y="28" width="150" height="66" rx="12" fill="{fill}"/>',
                _svg_text(badge_x + 12, 51, label, size=12, fill="#dff6ef"),
                _svg_text(badge_x + 12, 78, str(value), size=16, weight=700, fill="#ffffff"),
            ]
        )
    elements.extend(
        _svg_bar_panel(
            36,
            150,
            750,
            345,
            title="Installed capacity",
            rows=charts["installed_capacity_gw"],
            unit="GW",
            color="#2878b5",
        )
    )
    elements.extend(
        _svg_bar_panel(
            814,
            150,
            750,
            345,
            title="Generation over modeled horizon",
            rows=charts["selected_horizon_generation_twh"],
            unit="TWh",
            color="#2b9b6f",
        )
    )

    elements.extend(
        [
            '<rect x="36" y="520" width="750" height="475" rx="16" fill="#ffffff" stroke="#dbe3ec"/>',
            _svg_text(60, 557, "Scope-aware cost view", size=20, weight=700),
            _svg_text(60, 596, "Annualized planning cost", size=14, fill="#526071"),
            _svg_text(
                60,
                629,
                f"{_format_number(costs['annualized_planning_cost_million_cny_per_year'], 0)} million CNY/year",
                size=22,
                weight=700,
                fill="#1f5a91",
            ),
            _svg_text(60, 674, "Selected-horizon operating cost", size=14, fill="#526071"),
            _svg_text(
                60,
                707,
                f"{_format_number(costs['selected_horizon_operating_cost_million_cny'], 0)} million CNY",
                size=22,
                weight=700,
                fill="#167456",
            ),
            _svg_text(60, 758, "Planning cost intensity", size=14, fill="#526071"),
            _svg_text(
                60,
                793,
                f"{_format_number(costs['annualized_planning_cost_intensity_cny_per_kwh'], 3)} CNY/kWh",
                size=24,
                weight=700,
            ),
            _svg_text(395, 758, "Horizon operating intensity", size=14, fill="#526071"),
            _svg_text(
                395,
                793,
                f"{_format_number(costs['selected_horizon_operating_cost_intensity_cny_per_kwh'], 3)} CNY/kWh",
                size=24,
                weight=700,
            ),
            _svg_text(60, 845, "Full-year total system cost intensity", size=14, fill="#526071"),
            _svg_text(
                60,
                882,
                (
                    f"{_format_number(costs['scientific_full_year_system_cost_intensity_cny_per_kwh'], 3)} CNY/kWh"
                    if costs["scientific_full_year_system_cost_intensity_cny_per_kwh"]
                    is not None
                    else "N/A for a truncated engineering gate"
                ),
                size=23,
                weight=700,
                fill=(
                    "#111827"
                    if costs["scientific_full_year_system_cost_intensity_cny_per_kwh"]
                    is not None
                    else "#a4491f"
                ),
            ),
            _svg_text(
                60,
                932,
                (
                    "Detailed scope rows reconstruct objective: "
                    f"{_format_number(costs['objective_reconstruction_residual_million_cny'], 6)} "
                    "million CNY residual"
                ),
                size=13,
                fill="#526071",
            ),
        ]
    )

    elements.extend(
        [
            '<rect x="814" y="520" width="750" height="475" rx="16" fill="#ffffff" stroke="#dbe3ec"/>',
            _svg_text(838, 557, "Demand flexibility and system checks", size=20, weight=700),
        ]
    )
    diagnostic_rows = [
        (
            "Baseline -> effective peak",
            f"{_format_number(flex['selected_horizon_baseline_peak_load_gw'], 1)} -> "
            f"{_format_number(flex['selected_horizon_effective_peak_load_gw'], 1)} GW",
        ),
        (
            "Firm flex credit (annual peak windows)",
            f"{_format_number(flex['firm_flexible_capacity_credit_gw'], 2)} GW",
        ),
        (
            "Contracted thermal / V1G / V2G",
            f"{_format_number(flex['contracted_thermal_flexibility_gw'], 1)} / "
            f"{_format_number(flex['contracted_ev_v1g_flexibility_gw'], 1)} / "
            f"{_format_number(flex['contracted_ev_v2g_flexibility_gw'], 1)} GW",
        ),
        (
            "Storage charge / discharge",
            f"{_format_number(system['selected_horizon_storage_charge_gwh'], 1)} / "
            f"{_format_number(system['selected_horizon_storage_discharge_gwh'], 1)} GWh",
        ),
        (
            "VRE curtailment",
            f"{_format_number(system['selected_horizon_vre_curtailment_gwh'], 1)} GWh",
        ),
        (
            "Net CO2 / applicable cap",
            f"{_format_number(system['net_emissions_mtco2'], 2)} / "
            f"{_format_number(system['carbon_limit_mtco2'], 2)} MtCO2",
        ),
        (
            "Min capacity / up / down margin",
            f"{_format_number(system['minimum_capacity_margin_gw'], 3)} / "
            f"{_format_number(system['minimum_up_reserve_margin_gw'], 3)} / "
            f"{_format_number(system['minimum_down_reserve_margin_gw'], 3)} GW",
        ),
        (
            "Min inertia margin",
            f"{_format_number(system['minimum_inertia_margin_gw_s'], 3)} GW*s",
        ),
    ]
    for index, (label, value) in enumerate(diagnostic_rows):
        row_y = 604 + index * 46
        elements.extend(
            [
                _svg_text(838, row_y, label, size=14, fill="#526071"),
                _svg_text(1538, row_y, value, size=15, weight=700, anchor="end"),
                f'<line x1="838" y1="{row_y+13}" x2="1538" y2="{row_y+13}" stroke="#edf0f4"/>',
            ]
        )

    warning_fill = "#fff2e8" if not identity["is_full_year_scientific_result"] else "#eaf7f1"
    warning_text = "#9a431b" if not identity["is_full_year_scientific_result"] else "#12654c"
    elements.extend(
        [
            f'<rect x="36" y="1018" width="1528" height="70" rx="14" fill="{warning_fill}"/>',
            _svg_text(58, 1047, "Interpretation boundary", size=14, weight=700, fill=warning_text),
            _svg_text(
                58,
                1072,
                str(costs["interpretation_warning"]),
                size=14,
                fill=warning_text,
            ),
            "</svg>",
        ]
    )
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def _write_metrics_csv(payload: dict[str, Any], path: Path) -> None:
    identity = payload["identity"]
    acceptance = payload["acceptance"]
    costs = payload["cost_accounting"]
    flex = payload["demand_and_flexibility"]
    system = payload["system"]
    rows = [
        ("identity", "planning_year", identity["planning_year"], "year", "run", ""),
        ("identity", "scenario_id", identity["scenario_id"], "identifier", "run", ""),
        (
            "identity",
            "optimization_hours",
            identity["optimization_hours"],
            "hour",
            "modeled_horizon",
            "",
        ),
        ("acceptance", "solver_status", acceptance["solver_status"], "status", "run", ""),
        (
            "acceptance",
            "solution_qc_status",
            acceptance["solution_qc_status"],
            "status",
            "run",
            "",
        ),
        (
            "acceptance",
            "hard_checks_passed",
            acceptance["hard_checks_passed"],
            "count",
            "run",
            f"out of {acceptance['hard_checks_total']}",
        ),
        (
            "cost",
            "annualized_planning_cost_million_cny_per_year",
            costs["annualized_planning_cost_million_cny_per_year"],
            "million_CNY/year",
            ANNUALIZED_PLANNING_SCOPE,
            "",
        ),
        (
            "cost",
            "selected_horizon_operating_cost_million_cny",
            costs["selected_horizon_operating_cost_million_cny"],
            "million_CNY",
            SELECTED_HORIZON_OPERATION_SCOPE,
            "",
        ),
        (
            "cost_intensity",
            "annualized_planning_cost_intensity_cny_per_kwh",
            costs["annualized_planning_cost_intensity_cny_per_kwh"],
            "CNY/kWh",
            "full_year_reference_baseline_load",
            "",
        ),
        (
            "cost_intensity",
            "selected_horizon_operating_cost_intensity_cny_per_kwh",
            costs["selected_horizon_operating_cost_intensity_cny_per_kwh"],
            "CNY/kWh",
            "selected_horizon_reference_baseline_load",
            "",
        ),
        (
            "cost_intensity",
            "scientific_full_year_system_cost_intensity_cny_per_kwh",
            costs["scientific_full_year_system_cost_intensity_cny_per_kwh"],
            "CNY/kWh",
            "full_year_reference_baseline_load",
            costs["interpretation_warning"],
        ),
        (
            "demand",
            "selected_horizon_baseline_peak_load_gw",
            flex["selected_horizon_baseline_peak_load_gw"],
            "GW",
            "selected_horizon",
            "",
        ),
        (
            "demand",
            "selected_horizon_effective_peak_load_gw",
            flex["selected_horizon_effective_peak_load_gw"],
            "GW",
            "selected_horizon",
            "",
        ),
        (
            "flexibility",
            "firm_flexible_capacity_credit_gw",
            flex["firm_flexible_capacity_credit_gw"],
            "GW",
            "planning_adequacy",
            flex["firm_capacity_credit_interpretation"],
        ),
        (
            "system",
            "selected_horizon_vre_curtailment_gwh",
            system["selected_horizon_vre_curtailment_gwh"],
            "GWh",
            "selected_horizon",
            "",
        ),
        (
            "carbon",
            "net_emissions_mtco2",
            system["net_emissions_mtco2"],
            "MtCO2",
            system["carbon_accounting_scope"],
            "",
        ),
        (
            "carbon",
            "carbon_limit_mtco2",
            system["carbon_limit_mtco2"],
            "MtCO2",
            system["carbon_accounting_scope"],
            "",
        ),
    ]
    pd.DataFrame(
        rows,
        columns=[
            "section",
            "metric_id",
            "value",
            "unit",
            "accounting_scope",
            "interpretation",
        ],
    ).to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def _write_matplotlib_dashboard(
    payload: dict[str, Any],
    path: Path,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "PNG/PDF rendering is optional and requires matplotlib; the "
            "dependency-free SVG dashboard remains available."
        ) from exc

    charts = payload["charts"]
    costs = payload["cost_accounting"]
    flex = payload["demand_and_flexibility"]
    system = payload["system"]
    identity = payload["identity"]
    acceptance = payload["acceptance"]
    figure, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    figure.suptitle(
        f"CISPO {identity['planning_year']} | {identity['scenario_id']} | "
        f"{identity['optimization_hours']} h | {identity['result_use']}\n"
        f"Solver {acceptance['solver_status']} | QC "
        f"{acceptance['solution_qc_status']} | hard checks "
        f"{acceptance['hard_checks_passed']}/{acceptance['hard_checks_total']}",
        fontsize=16,
        fontweight="bold",
    )
    for axis, rows, title, unit, color in [
        (
            axes[0, 0],
            charts["installed_capacity_gw"],
            "Installed capacity",
            "GW",
            "#2878b5",
        ),
        (
            axes[0, 1],
            charts["selected_horizon_generation_twh"],
            "Generation over modeled horizon",
            "TWh",
            "#2b9b6f",
        ),
    ]:
        labels = [str(row["label"]) for row in rows][::-1]
        values = [float(row["value"]) for row in rows][::-1]
        axis.barh(labels, values, color=color)
        axis.set_xlabel(unit)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.grid(axis="x", alpha=0.2)
    axes[1, 0].axis("off")
    axes[1, 0].set_title("Scope-aware cost view", loc="left", fontweight="bold")
    cost_lines = [
        (
            "Annualized planning cost",
            f"{_format_number(costs['annualized_planning_cost_million_cny_per_year'], 0)} "
            "million CNY/year",
        ),
        (
            "Selected-horizon operating cost",
            f"{_format_number(costs['selected_horizon_operating_cost_million_cny'], 0)} "
            "million CNY",
        ),
        (
            "Planning cost intensity",
            f"{_format_number(costs['annualized_planning_cost_intensity_cny_per_kwh'], 3)} "
            "CNY/kWh",
        ),
        (
            "Horizon operating intensity",
            f"{_format_number(costs['selected_horizon_operating_cost_intensity_cny_per_kwh'], 3)} "
            "CNY/kWh",
        ),
        (
            "Full-year total system cost intensity",
            (
                f"{_format_number(costs['scientific_full_year_system_cost_intensity_cny_per_kwh'], 3)} "
                "CNY/kWh"
                if costs["scientific_full_year_system_cost_intensity_cny_per_kwh"]
                is not None
                else "N/A for a truncated engineering gate"
            ),
        ),
    ]
    for index, (label, value) in enumerate(cost_lines):
        axes[1, 0].text(0.02, 0.88 - index * 0.17, label, fontsize=10, color="#526071")
        axes[1, 0].text(
            0.02,
            0.82 - index * 0.17,
            value,
            fontsize=13,
            fontweight="bold",
        )
    axes[1, 1].axis("off")
    axes[1, 1].set_title(
        "Demand flexibility and system checks",
        loc="left",
        fontweight="bold",
    )
    diagnostic_lines = [
        (
            "Baseline -> effective peak",
            f"{_format_number(flex['selected_horizon_baseline_peak_load_gw'], 1)} -> "
            f"{_format_number(flex['selected_horizon_effective_peak_load_gw'], 1)} GW",
        ),
        (
            "Firm flex credit (annual peak windows)",
            f"{_format_number(flex['firm_flexible_capacity_credit_gw'], 2)} GW",
        ),
        (
            "Storage charge / discharge",
            f"{_format_number(system['selected_horizon_storage_charge_gwh'], 1)} / "
            f"{_format_number(system['selected_horizon_storage_discharge_gwh'], 1)} GWh",
        ),
        (
            "VRE curtailment",
            f"{_format_number(system['selected_horizon_vre_curtailment_gwh'], 1)} GWh",
        ),
        (
            "Net CO2 / cap",
            f"{_format_number(system['net_emissions_mtco2'], 2)} / "
            f"{_format_number(system['carbon_limit_mtco2'], 2)} MtCO2",
        ),
        (
            "Min capacity / up / down margin",
            f"{_format_number(system['minimum_capacity_margin_gw'], 3)} / "
            f"{_format_number(system['minimum_up_reserve_margin_gw'], 3)} / "
            f"{_format_number(system['minimum_down_reserve_margin_gw'], 3)} GW",
        ),
    ]
    for index, (label, value) in enumerate(diagnostic_lines):
        axes[1, 1].text(0.02, 0.9 - index * 0.145, label, fontsize=10, color="#526071")
        axes[1, 1].text(
            0.98,
            0.9 - index * 0.145,
            value,
            fontsize=11,
            fontweight="bold",
            ha="right",
        )
    figure.text(
        0.5,
        0.004,
        costs["interpretation_warning"],
        ha="center",
        fontsize=9,
        color="#9a431b" if not identity["is_full_year_scientific_result"] else "#12654c",
    )
    figure.savefig(path, dpi=200 if path.suffix.lower() == ".png" else None)
    plt.close(figure)


def build_result_dashboard(
    result_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    formats: Iterable[str] = ("svg",),
    reference_load_gwh: float | None = None,
) -> dict[str, Any]:
    """Generate fixed machine-readable metrics and a human-readable dashboard."""
    result_dir = Path(result_dir)
    target_dir = result_dir if output_dir is None else Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = (
        result_dir / "visualizations"
        if target_dir.resolve() == result_dir.resolve()
        else target_dir
    )
    figure_dir.mkdir(parents=True, exist_ok=True)
    payload = collect_result_dashboard(
        result_dir,
        reference_load_gwh=reference_load_gwh,
    )
    _write_json(payload, target_dir / "result_dashboard_summary.json")
    _write_metrics_csv(payload, target_dir / "result_analysis_metrics.csv")

    requested = {str(item).strip().lower() for item in formats}
    unsupported = requested - {"svg", "png", "pdf"}
    if unsupported:
        raise ValueError(f"Unsupported dashboard formats: {sorted(unsupported)}")
    if "svg" in requested:
        _write_svg_dashboard(
            payload,
            figure_dir / "core_result_dashboard.svg",
        )
    for suffix in ("png", "pdf"):
        if suffix in requested:
            _write_matplotlib_dashboard(
                payload,
                figure_dir / f"core_result_dashboard.{suffix}",
            )
    return payload
