"""Compact scientific summaries, deterministic SVG figures, and output manifest."""
from __future__ import annotations

import hashlib
import html
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import ModelConfig
from .data import STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .master import MasterArtifacts


def _value(expression: Any) -> np.ndarray:
    if hasattr(expression, "X"):
        return np.asarray(expression.X, dtype=float)
    if hasattr(expression, "getValue"):
        return np.asarray(expression.getValue(), dtype=float)
    return np.asarray(expression, dtype=float)


def _write_json(payload: dict, path: Path) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _svg_bar(
    labels: list[str],
    values: np.ndarray,
    *,
    title: str,
    unit: str,
    path: Path,
) -> None:
    width, height = 1100, 620
    left, right, top, bottom = 90, 30, 70, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    maximum = max(float(np.max(values)) if len(values) else 0.0, 1e-12)
    count = max(len(labels), 1)
    slot = plot_w / count
    bar_w = slot * 0.68
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="34" text-anchor="middle" font-size="24" font-family="Arial, sans-serif">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#333"/>',
    ]
    for tick in range(6):
        value = maximum * tick / 5
        y = top + plot_h * (1 - tick / 5)
        elements.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{left+plot_w}" y2="{y:.2f}" stroke="#e5e7eb"/>',
                f'<text x="{left-10}" y="{y+5:.2f}" text-anchor="end" font-size="13" font-family="Arial, sans-serif">{value:,.1f}</text>',
            ]
        )
    palette = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#dc2626", "#0891b2"]
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * slot + (slot - bar_w) / 2
        bar_h = plot_h * float(value) / maximum
        y = top + plot_h - bar_h
        elements.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="{palette[index % len(palette)]}"/>'
        )
        elements.append(
            f'<text x="{x+bar_w/2:.2f}" y="{top+plot_h+18}" text-anchor="end" transform="rotate(-45 {x+bar_w/2:.2f} {top+plot_h+18})" font-size="12" font-family="Arial, sans-serif">{html.escape(label)}</text>'
        )
    elements.append(
        f'<text x="18" y="{top+plot_h/2}" text-anchor="middle" transform="rotate(-90 18 {top+plot_h/2})" font-size="15" font-family="Arial, sans-serif">{html.escape(unit)}</text>'
    )
    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def _svg_lines(frame: pd.DataFrame, columns: list[str], *, title: str, path: Path) -> None:
    width, height = 1200, 620
    left, right, top, bottom = 80, 30, 70, 70
    plot_w, plot_h = width - left - right, height - top - bottom
    values = frame[columns].to_numpy(dtype=float)
    maximum = max(float(np.max(values)) if values.size else 0.0, 1e-12)
    colors = ["#111827", "#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed"]
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="34" text-anchor="middle" font-size="24" font-family="Arial, sans-serif">{html.escape(title)}</text>',
    ]
    for tick in range(6):
        y = top + plot_h * (1 - tick / 5)
        value = maximum * tick / 5
        elements.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left+plot_w}" y2="{y:.2f}" stroke="#e5e7eb"/>'
        )
        elements.append(
            f'<text x="{left-8}" y="{y+5:.2f}" text-anchor="end" font-size="12" font-family="Arial, sans-serif">{value:,.0f}</text>'
        )
    n = max(len(frame) - 1, 1)
    for index, column in enumerate(columns):
        points = []
        for position, value in enumerate(frame[column].to_numpy(dtype=float)):
            x = left + plot_w * position / n
            y = top + plot_h * (1.0 - value / maximum)
            points.append(f"{x:.2f},{y:.2f}")
        elements.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[index % len(colors)]}" stroke-width="2"/>'
        )
        legend_x = left + index * 175
        elements.append(
            f'<line x1="{legend_x}" y1="{height-25}" x2="{legend_x+24}" y2="{height-25}" stroke="{colors[index % len(colors)]}" stroke-width="3"/>'
        )
        elements.append(
            f'<text x="{legend_x+30}" y="{height-20}" font-size="13" font-family="Arial, sans-serif">{html.escape(column)}</text>'
        )
    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def export_result_summary(
    artifacts: MasterArtifacts,
    data: ModelData,
    config: ModelConfig,
    output_dir: str | Path,
) -> dict:
    output_dir = Path(output_dir)
    figure_dir = output_dir / "visualizations"
    figure_dir.mkdir(parents=True, exist_ok=True)
    variables = artifacts.variables
    hours = int(artifacts.index["optimization_hours"])

    capacity_rows: list[dict] = []
    vre_capacity = _value(variables["vre_capacity"])
    vre_new = _value(variables["vre_new"])
    for technology in VRE_TECHS:
        rows = data.vre_sites.technology.eq(technology).to_numpy()
        capacity_rows.append(
            {"asset_group": "generation", "technology": technology, "unit": "GW", "capacity": vre_capacity[rows].sum(), "new_capacity": vre_new[rows].sum()}
        )
    thermal_capacity = _value(variables["thermal_capacity"])
    thermal_new = _value(variables["thermal_new"])
    for technology, k in artifacts.index["thermal_index"].items():
        capacity_rows.append(
            {"asset_group": "generation", "technology": technology, "unit": "GW", "capacity": thermal_capacity[:, k].sum(), "new_capacity": thermal_new[:, k].sum()}
        )
    hydro_capacity = _value(variables["hydro_capacity"])
    hydro_new = _value(variables["hydro_new"])
    for label, operation_type in (("ror", "run_of_river"), ("reservoir", "reservoir_storage")):
        rows = data.hydro_stations.operation_type_model.eq(operation_type).to_numpy()
        capacity_rows.append(
            {"asset_group": "generation", "technology": label, "unit": "GW", "capacity": hydro_capacity[rows].sum(), "new_capacity": hydro_new[rows].sum()}
        )
    storage_capacity = _value(variables["storage_capacity"])
    storage_new = _value(variables["storage_new"])
    for technology, s in artifacts.index["storage_index"].items():
        capacity_rows.append(
            {"asset_group": "storage_power", "technology": technology, "unit": "GW", "capacity": storage_capacity[:, s].sum(), "new_capacity": storage_new[:, s].sum()}
        )
    capacity = pd.DataFrame(capacity_rows)
    capacity.to_csv(
        output_dir / "annual_capacity_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )

    vre_generation = _value(variables["vre_generation"])
    thermal_generation = _value(variables["actual_thermal_generation"])
    ror_generation = _value(variables["ror_generation"])
    reservoir_generation = _value(variables["reservoir_generation"])
    generation_series: dict[str, np.ndarray] = {}
    for technology, position in zip(VRE_TECHS, range(len(VRE_TECHS))):
        generation_series[technology] = vre_generation[:, position, :].sum(axis=0)
    for technology, k in artifacts.index["thermal_index"].items():
        generation_series[technology] = thermal_generation[:, k, :].sum(axis=0)
    generation_series["ror"] = ror_generation.sum(axis=0)
    generation_series["reservoir"] = reservoir_generation.sum(axis=0)
    generation = pd.DataFrame(
        [
            {"technology": technology, "generation_gwh": float(values.sum())}
            for technology, values in generation_series.items()
        ]
    )
    generation.to_csv(
        output_dir / "annual_generation_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )

    storage_charge_by_technology = _value(variables["storage_charge"]).sum(axis=0)
    storage_discharge_by_technology = _value(variables["storage_discharge"]).sum(axis=0)
    storage_charge = storage_charge_by_technology.sum(axis=0)
    storage_discharge = storage_discharge_by_technology.sum(axis=0)
    storage_parameters = data.storage.set_index("technology")
    storage_rows = []
    for technology, s in artifacts.index["storage_index"].items():
        installed_energy_gwh = float(
            storage_capacity[:, s].sum()
            * storage_parameters.loc[technology, "duration_h"]
        )
        discharged_gwh = float(storage_discharge_by_technology[s].sum())
        storage_rows.append(
            {
                "technology": technology,
                "power_capacity_gw": float(storage_capacity[:, s].sum()),
                "energy_capacity_gwh": installed_energy_gwh,
                "charge_gwh": float(storage_charge_by_technology[s].sum()),
                "discharge_gwh": discharged_gwh,
                "conversion_and_self_discharge_loss_gwh": float(
                    storage_charge_by_technology[s].sum()
                    - storage_discharge_by_technology[s].sum()
                ),
                "equivalent_full_discharge_cycles": (
                    discharged_gwh / installed_energy_gwh
                    if installed_energy_gwh > 1e-12
                    else 0.0
                ),
            }
        )
    pd.DataFrame(storage_rows).to_csv(
        output_dir / "annual_storage_operation_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )
    load = np.asarray(artifacts.index["selected_load_gw"], dtype=float).sum(axis=0)
    dac_load = _value(variables["dac_load"]).sum()
    network_injection = _value(variables["network_injection"]).sum(axis=0)
    national = pd.DataFrame(
        {
            "hour_index": np.arange(hours),
            "load_gw": load,
            "vre_generation_gw": sum(generation_series[t] for t in VRE_TECHS),
            "thermal_nuclear_generation_gw": sum(
                generation_series[t] for t in THERMAL_TECHS
            ),
            "ror_generation_gw": generation_series["ror"],
            "reservoir_generation_gw": generation_series["reservoir"],
            "storage_charge_gw": storage_charge,
            "storage_discharge_gw": storage_discharge,
            "net_interprovincial_injection_gw": network_injection,
            "dac_load_gw": np.full(hours, dac_load),
        }
    )
    national.to_csv(
        output_dir / "hourly_national_balance.csv.gz",
        index=False,
        compression="gzip",
        encoding="utf-8-sig",
    )

    dates = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
        .iloc[:hours]
    )
    months = pd.to_datetime(dates.datetime_bj).dt.month.to_numpy(dtype=int)
    monthly_rows = []
    for month in sorted(np.unique(months)):
        selected = months == month
        row = {
            "month": int(month),
            "load_gwh": float(load[selected].sum()),
            "storage_charge_gwh": float(storage_charge[selected].sum()),
            "storage_discharge_gwh": float(storage_discharge[selected].sum()),
        }
        row.update(
            {
                f"{technology}_generation_gwh": float(values[selected].sum())
                for technology, values in generation_series.items()
            }
        )
        monthly_rows.append(row)
    pd.DataFrame(monthly_rows).to_csv(
        output_dir / "monthly_energy_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )

    vre_available = _value(variables["vre_available"])
    ror_available = _value(variables["ror_available"])
    flow_forward = _value(variables["flow_forward"])
    flow_reverse = _value(variables["flow_reverse"])
    efficiency = np.asarray(artifacts.index["line_efficiency"], dtype=float)
    transmission_losses = float(
        ((1.0 - efficiency)[:, None] * (flow_forward + flow_reverse)).sum()
    )
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "optimization_hours": hours,
        "objective_million_cny_per_year": float(artifacts.model.ObjVal),
        "annual_load_gwh": float(load.sum()),
        "peak_load_gw": float(load.max()),
        "annual_generation_gwh": float(generation.generation_gwh.sum()),
        "vre_curtailment_gwh": float((vre_available - vre_generation).sum()),
        "ror_curtailment_gwh": float((ror_available - ror_generation).sum()),
        "storage_charge_gwh": float(storage_charge.sum()),
        "storage_discharge_gwh": float(storage_discharge.sum()),
        "interprovincial_transmission_losses_gwh": transmission_losses,
    }
    _write_json(summary, output_dir / "annual_summary.json")

    plotted_capacity = capacity.loc[
        capacity.unit.eq("GW") & capacity.capacity.gt(1e-9)
    ].sort_values("capacity", ascending=False)
    _svg_bar(
        plotted_capacity.technology.astype(str).tolist(),
        plotted_capacity.capacity.to_numpy(float),
        title=f"CISPO {config.planning_year} installed capacity",
        unit="GW",
        path=figure_dir / "capacity_by_technology.svg",
    )
    plotted_generation = generation.loc[generation.generation_gwh.gt(1e-6)].sort_values(
        "generation_gwh", ascending=False
    )
    _svg_bar(
        plotted_generation.technology.astype(str).tolist(),
        plotted_generation.generation_gwh.to_numpy(float) / 1000.0,
        title=f"CISPO {config.planning_year} generation",
        unit="TWh",
        path=figure_dir / "generation_by_technology.svg",
    )
    first_week = national.iloc[: min(168, hours)].copy()
    _svg_lines(
        first_week,
        [
            "load_gw", "vre_generation_gw", "thermal_nuclear_generation_gw",
            "ror_generation_gw", "reservoir_generation_gw",
        ],
        title=f"CISPO {config.planning_year} national dispatch (first {len(first_week)} h)",
        path=figure_dir / "national_dispatch_first_week.svg",
    )
    return summary


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finalize_result_manifest(output_dir: str | Path, config: ModelConfig) -> Path:
    output_dir = Path(output_dir)
    # These files are owned by the outer shell/nohup wrapper. In particular,
    # stdout receives the final printed solve report after this function
    # returns, so hashing it here would create a manifest that is stale by
    # construction. Scientific result files and the Gurobi log remain hashed.
    runtime_managed_files = {
        "result_manifest.json",
        "runner_stdout.log",
        "runner_stderr.log",
        "run.pid",
    }
    try:
        git_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        git_commit = "UNAVAILABLE"
    files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name not in runtime_managed_files:
            files.append(
                {
                    "path": path.relative_to(output_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "git_commit": git_commit,
        "configuration": str(config.path),
        "excluded_runtime_files": sorted(runtime_managed_files - {"result_manifest.json"}),
        "files": files,
    }
    path = output_dir / "result_manifest.json"
    _write_json(manifest, path)
    return path
