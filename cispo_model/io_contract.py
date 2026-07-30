"""Reproducible run provenance and self-describing result catalogs."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Any

import numpy as np
import pandas as pd

from .config import ModelConfig, ROOT


RUNTIME_MANAGED_FILES = {
    "result_manifest.json",
    "runner_stdout.log",
    "runner_stderr.log",
    "stdout.log",
    "stderr.log",
    "sequence_stdout.log",
    "sequence_stderr.log",
    "run.pid",
    "run.stdout",
    "run.stderr",
    "run.time",
}

OUTPUT_FILE_ROLES = {
    "base_basis.bas.gz": "Accepted full-year Base post-crossover LP basis checkpoint",
    "base_model_fingerprint.json": "Constant-memory Gurobi model identity and basis-status census",
    "base_solution.sol.gz": "Accepted full-year Base continuous solution checkpoint",
    "base_solver.prm": "Active Gurobi parameter checkpoint for the accepted full-year Base",
    "base_solver_artifact_manifest.json": "Integrity and reuse-scope contract for selective Base solver artifacts",
    "annual_adequacy_by_province.csv": "Province peak-load capacity-credit and planning-reserve-margin accounting",
    "annual_capacity_by_province_technology.csv": "Province-technology installed and new capacity",
    "annual_capacity_by_technology.csv": "National installed and new capacity by technology",
    "annual_constraint_shadow_prices.csv": "Annual policy, resource, adequacy and CCS constraint shadow prices",
    "annual_carbon_ccs.json": "National carbon, capture, DAC and storage accounting",
    "annual_generation_by_province_technology.csv": "Province-technology generation over the selected horizon",
    "annual_generation_by_technology.csv": "National generation by technology over the selected horizon",
    "annual_flexible_load_by_province.csv": "Province demand-flexibility energy, peak and V2G accounting",
    "annual_resource_accounting_by_province.csv": "Province biomass, emissions, capture and DAC accounting",
    "annual_storage_operation_by_technology.csv": "Storage energy, losses and cycling by technology",
    "annual_summary.json": "Backward-compatible compact result summary",
    "build_report.json": "Built-model size, architecture and memory report",
    "constraint_family_audit.json": "Raw LP constraint and variable family sparsity census with global solver phases",
    "co2_source_sink_flows.csv": "Positive province-to-storage-site CO2 flows",
    "cost_components.csv": "Objective and diagnostic cost decomposition",
    "dac_capacity_capture.csv": "Province-technology DAC capacity and capture",
    "dual_export_status.json": "Availability and interpretation of LP shadow-price exports",
    "flexible_load_dispatch.npz": "Province-hour baseline components, optimized flexible demand and V2G arrays",
    "hourly_marginal_prices.csv.gz": "Province-hour energy, reserve and inertia dual values",
    "hourly_national_balance.csv.gz": "Chronological national power balance",
    "hourly_province_balance.csv.gz": "Chronological provincial power balance",
    "hourly_province_security.csv.gz": "Chronological reserve and inertia accounting",
    "hydro_capacity.csv": "Station-level hydropower capacity decisions",
    "hydro_aggregate_capacity.csv": (
        "Fixed province-level conventional-hydropower residual and accounting"
    ),
    "hydro_dispatch.npz": "Province-hour run-of-river and hydropower reserve arrays",
    "hydro_cascade_reconciliation_audit.json": "Full-horizon cascade natural-flow reconciliation and routed-release adjustment audit",
    "hydro_cascade_reconciliation_by_node.csv": "Node-level cascade reconciliation counts, volumes and transfer fractions",
    "input_manifest.csv": "Resolved model input files and integrity hashes",
    "intra_grid_substation_design.csv": "CISPO-style shared wind/PV trunk design factors and capacity decisions by substation",
    "intra_grid_vre_site_design.csv": "Site-level VRE spur design factors, observed cohort floor and augmentation decisions",
    "load_center_annual_balance.csv": "Annual load-center demand and injection accounting",
    "load_center_annual_generation.csv": "Annual spatial generation assigned to load centers",
    "load_center_intra_transmission.csv": "Annual intraprovincial load-center network decisions and flows",
    "load_center_network_qc.csv": "Load-center network hard checks",
    "mga_request.json": "Validated MGA baseline, immutable inputs, cost slack and secondary-objective request",
    "mga_run.json": "Applied MGA cost-cap and secondary-objective metadata plus realized values",
    "model_config_snapshot.json": "Exact resolved year-specific model configuration",
    "monthly_energy_by_technology.csv": "Monthly energy balance by technology",
    "output_catalog.csv": "File-level result catalog",
    "output_data_dictionary.csv": "Column and array-level result data dictionary",
    "preflight_report.json": "Input, units, dimensions and boundary preflight checks",
    "province_annual_load_center_accounts.csv": "Province annual load-center closure accounts",
    "reservoir_dispatch.npz": "Station-hour reservoir operation and hydrology arrays",
    "reservoir_station_index.csv": "Row index and station metadata for reservoir arrays",
    "result_manifest.json": "SHA256 manifest of scientific result artifacts",
    "run_claim.json": "Atomic output-root ownership claim preventing overwrite or concurrent reuse",
    "run_identity.json": "Layered scientific case, LP topology, solver-runtime and implementation-bundle identity",
    "run_environment.json": "Software, host, command and data-root provenance",
    "run_scope.json": "Horizon, scientific-use boundary and scale estimate",
    "scenario_manifest.json": "Resolved optional-module scenario and demand-flexibility assumptions",
    "run_summary.json": "Scope-aware compact result summary",
    "solution_qc.json": "Hard physical and numerical solution checks",
    "solve_report.json": "Solver status, parameters, quality, runtime and memory",
    "storage_capacity.csv": "Province-technology storage capacity decisions and bounds",
    "storage_dispatch.npz": "Province-technology-hour storage operation and reserve arrays",
    "thermal_dispatch.npz": "Province-technology-hour RUC, generation and ramp arrays",
    "thermal_nuclear_capacity.csv": "Province-technology thermal/nuclear decisions and bounds",
    "time_index.csv": "Chronological hour-to-datetime mapping",
    "transmission_capacity.csv": "Interprovincial corridor capacity decisions",
    "transmission_flows.npz": "Corridor-hour directional transmission arrays",
    "vre_capacity.csv": "Site-technology VRE capacity decisions and bounds",
    "vre_dispatch.npz": "Province-technology-hour VRE availability, generation and reserve arrays",
    "wave_capacity.csv": "Wave capacity decisions on existing marine optimization grid rows",
    "wave_dispatch.npz": "Province-hour wave availability and dispatch plus grid capacity decisions",
    "warm_start_basis.bas": "Test-only post-crossover Gurobi LP basis for guarded diagnostic reuse",
    "warm_start_basis_manifest.json": "Integrity plus exact raw-LP-topology contract for a test-only LP basis",
    "warm_start_input.json": "Verified source and compatibility record for an imported test-only LP basis",
}

NPZ_DIMENSIONS = {
    "wave_dispatch.npz": {
        "generation_gw": "province,hour",
        "available_gw": "province,hour",
        "capacity_gw": "existing_marine_grid",
        "province_codes": "province",
        "grid_uids": "existing_marine_grid",
        "grid_ids": "existing_marine_grid",
        "wave_source_grid_ids": "existing_marine_grid",
        "hour_index": "hour",
    },
    "flexible_load_dispatch.npz": {
        "baseline_total_load_gw": "province,hour",
        "effective_total_load_gw": "province,hour",
        "baseline_base_residual_gw": "province,hour",
        "baseline_heating_gw": "province,hour",
        "baseline_cooling_gw": "province,hour",
        "baseline_ev_gw": "province,hour",
        "actual_base_residual_gw": "province,hour",
        "actual_heating_gw": "province,hour",
        "actual_cooling_gw": "province,hour",
        "actual_ev_gw": "province,hour",
        "heating_shift_up_gw": "province,hour",
        "heating_shift_down_gw": "province,hour",
        "cooling_shift_up_gw": "province,hour",
        "cooling_shift_down_gw": "province,hour",
        "ev_v1g_shift_up_gw": "province,hour",
        "ev_v1g_shift_down_gw": "province,hour",
        "heating_state_gwh": "province,hour",
        "cooling_state_gwh": "province,hour",
        "heating_comfort_debt_gwh": "province,hour",
        "cooling_comfort_debt_gwh": "province,hour",
        "ev_v1g_backlog_gwh": "province,hour",
        "ev_v2g_charge_gw": "province,hour",
        "ev_v2g_discharge_gw": "province,hour",
        "ev_v2g_soc_gwh": "province,hour",
        "ev_mobility_charge_gw": "province,hour",
        "ev_mobility_discharge_gw": "province,hour",
        "ev_mobility_soc_gwh": "province,hour",
        "ev_mobility_charge_deviation_gw": "province,hour",
        "ev_mobility_v1g_relocated_gw": "province,hour",
        "flexible_service_capacity_gw": "province,service",
        "flexible_service_names": "service",
        "province_codes": "province",
        "hour_index": "hour",
    },
    "thermal_dispatch.npz": {
        "gross_generation_gw": "province,technology,hour",
        "net_generation_gw": "province,technology,hour",
        "online_capacity_gw": "province,technology,hour",
        "startup_capacity_gw": "province,technology,hour",
        "shutdown_capacity_gw": "province,technology,hour",
        "ramp_magnitude_gw": "province,technology,hour",
        "reserve_up_gw": "province,hour",
        "reserve_down_gw": "province,hour",
        "province_codes": "province",
        "technologies": "technology",
        "hour_index": "hour",
    },
    "vre_dispatch.npz": {
        "generation_gw": "province,technology,hour",
        "available_gw": "province,technology,hour",
        "reserve_up_gw": "province,hour",
        "province_codes": "province",
        "technologies": "technology",
        "hour_index": "hour",
    },
    "storage_dispatch.npz": {
        "charge_gw": "province,technology,hour",
        "discharge_gw": "province,technology,hour",
        "soc_gwh": "province,technology,hour",
        "reserve_up_gw": "province,technology,hour",
        "reserve_down_gw": "province,technology,hour",
        "province_codes": "province",
        "technologies": "technology",
        "hour_index": "hour",
    },
    "hydro_dispatch.npz": {
        "ror_generation_gw": "province,hour",
        "ror_available_gw": "province,hour",
        "reservoir_generation_gw": "province,hour",
        "aggregate_generation_gw": "province,hour",
        "aggregate_available_gw": "province,hour",
        "reserve_up_gw": "province,hour",
        "province_codes": "province",
        "hour_index": "hour",
    },
    "reservoir_dispatch.npz": {
        "generation_gw": "reservoir_station,hour",
        "soc_gwh": "reservoir_station,hour",
        "spill_gwh": "reservoir_station,hour",
        "turbine_flow_m3s": "reservoir_station,hour",
        "spill_flow_m3s": "reservoir_station,hour",
        "active_storage_m3": "reservoir_station,hour",
        "local_inflow_m3s": "reservoir_station,hour",
        "upstream_release_m3s": "reservoir_station,hour",
        "inflow_gwh": "reservoir_station,hour",
        "energy_upper_gwh": "reservoir_station",
        "active_storage_upper_m3": "reservoir_station",
        "core_cascade_local_rows": "core_cascade_station",
        "core_cascade_edge_ids": "core_cascade_edge",
        "core_cascade_edge_lag_h": "core_cascade_edge",
        "hydrochn_row_id": "reservoir_station",
        "hour_index": "hour",
    },
    "transmission_flows.npz": {
        "forward_gw": "corridor,hour",
        "reverse_gw": "corridor,hour",
        "line_ids": "corridor",
        "hour_index": "hour",
    },
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_value(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def _zarr_metadata_fingerprint(path: Path) -> tuple[str, int]:
    metadata: list[Path] = []
    if path.is_dir():
        metadata.extend(item for item in path.glob(".z*") if item.is_file())
        for child in path.iterdir():
            if child.is_dir():
                metadata.extend(item for item in child.glob(".z*") if item.is_file())
    digest = hashlib.sha256()
    for item in sorted(metadata):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(item.read_bytes())
    return (digest.hexdigest() if metadata else "UNAVAILABLE", len(metadata))


def write_run_provenance(
    output_dir: str | Path,
    config: ModelConfig,
    *,
    data_root: str | Path,
    planning_state: Any,
) -> tuple[Path, Path, Path]:
    """Write the exact configuration, environment and resolved input hashes."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_root = Path(data_root).resolve()
    contract_path = ROOT / "config" / "model_input_files.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    config_snapshot = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_path": str(config.path),
        "source_sha256": sha256_file(config.path),
        "scenario_source_path": str(config.scenario_path) if config.scenario_path else None,
        "scenario_source_sha256": (
            sha256_file(config.scenario_path) if config.scenario_path else None
        ),
        "solver_source_path": (
            str(config.solver_path) if config.solver_path else None
        ),
        "solver_source_sha256": (
            sha256_file(config.solver_path) if config.solver_path else None
        ),
        "formulation_source_path": (
            str(config.formulation_path) if config.formulation_path else None
        ),
        "formulation_source_sha256": (
            sha256_file(config.formulation_path)
            if config.formulation_path
            else None
        ),
        "resolved_configuration": config.raw,
    }
    config_path = output_dir / "model_config_snapshot.json"
    config_path.write_text(
        json.dumps(config_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    environment = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "command": [sys.executable, *sys.argv],
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("branch", "--show-current"),
        "git_worktree_status": _git_value("status", "--short"),
        "packages": {
            name: _package_version(name)
            for name in (
                "numpy", "pandas", "scipy", "xarray", "netCDF4", "zarr",
                "psutil", "gurobipy",
            )
        },
        "data_roots": {
            "CISPO_DATA_ROOT": str(data_root),
            "CISPO_CF_ROOT": os.environ.get("CISPO_CF_ROOT"),
            "CISPO_HYDRO_ROOT": os.environ.get("CISPO_HYDRO_ROOT"),
            "CISPO_RAW_GRFR_ROOT": os.environ.get("CISPO_RAW_GRFR_ROOT"),
            "CISPO_WAVE_ROOT": os.environ.get("CISPO_WAVE_ROOT"),
        },
        "planning_state_in": str(planning_state.root) if planning_state.root else None,
        "planning_state_format": planning_state.metadata.get("format"),
    }
    environment_path = output_dir / "run_environment.json"
    environment_path.write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    roles = contract.get("roles", {})
    rows: list[dict[str, Any]] = []

    def add_file(kind: str, logical_path: str, resolved_path: Path, required: bool) -> None:
        exists = resolved_path.is_file()
        rows.append(
            {
                "kind": kind,
                "logical_path": logical_path,
                "resolved_path": str(resolved_path),
                "required": required,
                "exists": exists,
                "size_bytes": resolved_path.stat().st_size if exists else None,
                "sha256": sha256_file(resolved_path) if exists else None,
                "integrity_method": "sha256_file" if exists else "missing",
                "role": roles.get(logical_path, ""),
            }
        )

    add_file("configuration", str(config.path), config.path, True)
    if config.scenario_path:
        add_file(
            "scenario_configuration",
            str(config.scenario_path),
            config.scenario_path,
            True,
        )
    if config.solver_path:
        add_file(
            "solver_configuration",
            str(config.solver_path),
            config.solver_path,
            True,
        )
    if config.formulation_path:
        add_file(
            "formulation_configuration",
            str(config.formulation_path),
            config.formulation_path,
            True,
        )
    add_file("input_contract", "config/model_input_files.json", contract_path, True)
    for logical_path in contract["required_model_tables"]:
        add_file("model_table", logical_path, data_root / logical_path, True)
    if (
        bool(config.raw["features"]["flexible_load"])
        and str(
            config.raw["flexible_load"].get(
                "formulation", "daily_energy_shift_v1"
            )
        )
        == "comfort_envelope_v3"
    ):
        envelope_logical_path = str(
            config.raw["flexible_load"]["hourly_envelope_file"]
        )
        envelope_path = data_root / envelope_logical_path
        add_file(
            "scenario_model_table",
            envelope_logical_path,
            envelope_path,
            True,
        )
        envelope_manifest = envelope_path.with_suffix("").with_suffix(
            ".manifest.json"
        )
        add_file(
            "scenario_validation_sidecar",
            str(
                Path(envelope_logical_path)
                .with_suffix("")
                .with_suffix(".manifest.json")
            ),
            envelope_manifest,
            True,
        )
    if (
        bool(config.raw["features"]["flexible_load"])
        and str(
            config.raw["flexible_load"].get(
                "formulation", "daily_energy_shift_v1"
            )
        )
        == "service_constrained_v4"
    ):
        v4_files = config.raw["flexible_load"].get("v4_input_files", {})
        for key in (
            "thermal_hourly_envelope_file",
            "thermal_parameters_file",
            "ev_availability_hourly_file",
            "ev_mobility_hourly_file",
            "enablement_cost_file",
        ):
            logical_path = str(v4_files[key])
            add_file(
                "scenario_model_table",
                logical_path,
                data_root / logical_path,
                True,
            )
        manifest_logical_path = str(v4_files["input_manifest_file"])
        add_file(
            "scenario_validation_sidecar",
            manifest_logical_path,
            data_root / manifest_logical_path,
            True,
        )
    if bool(config.raw["features"].get("wave_energy", False)):
        wave_sites_logical = str(config.raw["wave_energy"]["sites_file"])
        add_file(
            "scenario_model_table",
            wave_sites_logical,
            data_root / wave_sites_logical,
            True,
        )
        wave_manifest_logical = str(
            Path(wave_sites_logical).with_name("wave_input_manifest.json")
        )
        add_file(
            "scenario_validation_sidecar",
            wave_manifest_logical,
            data_root / wave_manifest_logical,
            True,
        )
        wave_root = os.environ.get("CISPO_WAVE_ROOT")
        wave_cf = (
            Path(wave_root) / str(config.raw["wave_energy"]["cf_filename"])
            if wave_root
            else Path("__CISPO_WAVE_ROOT_NOT_SET__")
        )
        add_file(
            "capacity_factor_store",
            f"wave:{config.planning_year}",
            wave_cf,
            True,
        )
    for logical_path in contract.get("server_validation_sidecars", []):
        add_file("validation_sidecar", logical_path, data_root / logical_path, False)
    if planning_state.root:
        for name in (
            "state_metadata.json",
            "capacity_cohorts.csv.gz",
            "state_transition_summary.csv",
            "../result_manifest.json",
        ):
            add_file("planning_state", name, Path(planning_state.root) / name, True)

    cf_index_path = data_root / "vre" / "hourly_cf_index.csv"
    if cf_index_path.is_file():
        cf_index = pd.read_csv(cf_index_path)
        cf_root = os.environ.get("CISPO_CF_ROOT")
        for row in cf_index.loc[
            cf_index.year.isin(config.weather_source_years)
        ].itertuples(index=False):
            indexed = str(row.zarr_path)
            resolved = (
                Path(cf_root) / str(row.technology) / PureWindowsPath(indexed).name
                if cf_root
                else Path(indexed)
            )
            fingerprint, metadata_files = _zarr_metadata_fingerprint(resolved)
            rows.append(
                {
                    "kind": "capacity_factor_store",
                    "logical_path": f"{row.technology}:{int(row.year)}",
                    "resolved_path": str(resolved),
                    "required": True,
                    "exists": resolved.is_dir(),
                    "size_bytes": None,
                    "sha256": fingerprint,
                    "integrity_method": f"zarr_metadata_sha256:{metadata_files}_files",
                    "role": "Hourly VRE capacity-factor store; chunk payload is not duplicated in the case output",
                }
            )

    hydro_index_path = data_root / "hydro" / "timeseries_index.csv"
    if hydro_index_path.is_file():
        hydro_index = pd.read_csv(hydro_index_path)
        hydro_root = os.environ.get("CISPO_HYDRO_ROOT")
        for row in hydro_index.loc[hydro_index.dataset.ne("grfr_download_manifest")].itertuples(index=False):
            indexed = str(row.path)
            resolved = Path(hydro_root) / PureWindowsPath(indexed).name if hydro_root else Path(indexed)
            add_file("hydrology_timeseries", str(row.dataset), resolved, True)

    manifest_path = output_dir / "input_manifest.csv"
    manifest = pd.DataFrame(rows)
    manifest.to_csv(manifest_path, index=False, encoding="utf-8-sig", lineterminator="\n")
    missing = manifest.loc[manifest.required & ~manifest.exists]
    if not missing.empty:
        raise FileNotFoundError(
            "Required provenance inputs are missing: "
            + ", ".join(missing.logical_path.astype(str).tolist())
        )
    return config_path, environment_path, manifest_path


def _infer_unit(field: str) -> str:
    lower = field.lower()
    suffixes = (
        ("_million_cny_per_year", "million CNY/year"),
        ("_yuan_per_mwh", "CNY/MWh"),
        ("_mtco2_per_year", "MtCO2/year"),
        ("_mtco2", "MtCO2"),
        ("_mtpa", "MtCO2/year"),
        ("_m3s", "m3/s"),
        ("_m3", "m3"),
        ("_gwh", "GWh"),
        ("_gw_s", "GW*s"),
        ("_gw", "GW"),
        ("_pj", "PJ"),
        ("_km", "km"),
        ("_h", "hour"),
    )
    for suffix, unit in suffixes:
        if lower.endswith(suffix):
            return unit
    return "dimensionless_or_identifier"


def write_output_catalog(output_dir: str | Path) -> tuple[Path, Path]:
    """Create file- and field-level catalogs that can be read without source code."""
    output_dir = Path(output_dir)
    catalog_rows: list[dict[str, Any]] = []
    dictionary_rows: list[dict[str, Any]] = []
    excluded = RUNTIME_MANAGED_FILES | {"output_catalog.csv", "output_data_dictionary.csv"}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name in excluded:
            continue
        relative = path.relative_to(output_dir).as_posix()
        suffixes = "".join(path.suffixes).lower()
        fields = 0
        row_count: int | None = None
        file_format = path.suffix.lower().lstrip(".")
        if suffixes.endswith(".csv") or suffixes.endswith(".csv.gz"):
            file_format = "csv.gz" if suffixes.endswith(".gz") else "csv"
            try:
                header = pd.read_csv(path, nrows=0)
                columns = list(header.columns)
            except pd.errors.EmptyDataError:
                columns = []
            fields = len(columns)
            if columns:
                row_count = sum(
                    len(chunk)
                    for chunk in pd.read_csv(path, usecols=[columns[0]], chunksize=100_000)
                )
            else:
                row_count = 0
            for column in columns:
                dictionary_rows.append(
                    {
                        "file_path": relative,
                        "field": column,
                        "storage": "column",
                        "dtype": "see CSV values",
                        "shape": "rows",
                        "dimensions": "record",
                        "unit": _infer_unit(column),
                        "description": column.replace("_", " "),
                    }
                )
        elif path.suffix.lower() == ".npz":
            file_format = "npz"
            with np.load(path, allow_pickle=False) as archive:
                fields = len(archive.files)
                for name in archive.files:
                    value = archive[name]
                    dictionary_rows.append(
                        {
                            "file_path": relative,
                            "field": name,
                            "storage": "array",
                            "dtype": str(value.dtype),
                            "shape": "x".join(map(str, value.shape)) or "scalar",
                            "dimensions": NPZ_DIMENSIONS.get(path.name, {}).get(name, "see source documentation"),
                            "unit": _infer_unit(name),
                            "description": name.replace("_", " "),
                        }
                    )
        elif path.suffix.lower() == ".json":
            file_format = "json"
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                keys = list(payload) if isinstance(payload, dict) else []
            except (json.JSONDecodeError, UnicodeDecodeError):
                keys = []
            fields = len(keys)
            for key in keys:
                dictionary_rows.append(
                    {
                        "file_path": relative,
                        "field": key,
                        "storage": "json_key",
                        "dtype": "see JSON value",
                        "shape": "scalar_or_nested",
                        "dimensions": "run",
                        "unit": _infer_unit(key),
                        "description": key.replace("_", " "),
                    }
                )
        catalog_rows.append(
            {
                "file_path": relative,
                "format": file_format,
                "size_bytes": path.stat().st_size,
                "field_or_array_count": fields,
                "row_count": row_count,
                "role": OUTPUT_FILE_ROLES.get(path.name, "Supporting scientific output"),
            }
        )
    catalog_path = output_dir / "output_catalog.csv"
    dictionary_path = output_dir / "output_data_dictionary.csv"
    pd.DataFrame(catalog_rows).to_csv(
        catalog_path, index=False, encoding="utf-8-sig", lineterminator="\n"
    )
    pd.DataFrame(dictionary_rows).to_csv(
        dictionary_path, index=False, encoding="utf-8-sig", lineterminator="\n"
    )
    return catalog_path, dictionary_path


def validate_result_manifest(output_dir: str | Path) -> tuple[bool, list[str]]:
    """Verify every checksummed scientific file in an accepted result directory."""
    output_dir = Path(output_dir)
    path = output_dir / "result_manifest.json"
    if not path.is_file():
        return False, ["result_manifest.json is missing"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for row in payload.get("files", []):
        item = output_dir / row["path"]
        if not item.is_file():
            failures.append(f"missing:{row['path']}")
            continue
        if item.stat().st_size != int(row["bytes"]):
            failures.append(f"size:{row['path']}")
            continue
        if sha256_file(item) != row["sha256"]:
            failures.append(f"sha256:{row['path']}")
    return not failures, failures


def validate_input_manifest(
    manifest_path: str | Path,
) -> tuple[bool, list[str]]:
    """Verify that every recorded input still has the same on-disk identity."""
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        return False, ["input_manifest.csv is missing"]
    try:
        manifest = pd.read_csv(manifest_path)
    except (pd.errors.EmptyDataError, UnicodeDecodeError, OSError) as error:
        return False, [f"input_manifest.csv is unreadable: {error}"]
    failures: list[str] = []
    for row in manifest.itertuples(index=False):
        logical_path = str(row.logical_path)
        resolved = Path(str(row.resolved_path))
        recorded_exists = str(row.exists).strip().lower() == "true"
        required = str(row.required).strip().lower() == "true"
        method = str(row.integrity_method)
        if method.startswith("zarr_metadata_sha256:"):
            current_exists = resolved.is_dir()
        else:
            current_exists = resolved.is_file()
        if current_exists != recorded_exists:
            failures.append(f"exists:{logical_path}")
            continue
        if not current_exists:
            if required:
                failures.append(f"missing:{logical_path}")
            continue
        if method == "sha256_file":
            if pd.notna(row.size_bytes) and resolved.stat().st_size != int(
                row.size_bytes
            ):
                failures.append(f"size:{logical_path}")
                continue
            if sha256_file(resolved) != str(row.sha256):
                failures.append(f"sha256:{logical_path}")
        elif method.startswith("zarr_metadata_sha256:"):
            fingerprint, metadata_files = _zarr_metadata_fingerprint(resolved)
            expected_method = f"zarr_metadata_sha256:{metadata_files}_files"
            if method != expected_method:
                failures.append(f"zarr_metadata_count:{logical_path}")
                continue
            if fingerprint != str(row.sha256):
                failures.append(f"zarr_metadata_sha256:{logical_path}")
        else:
            failures.append(f"unsupported_integrity_method:{logical_path}")
    return not failures, failures
