"""Versioned capacity-cohort state for sequential CISPO planning years."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import ModelConfig


STATE_METADATA = "state_metadata.json"
STATE_COHORTS = "capacity_cohorts.csv.gz"
STATE_SUMMARY = "state_transition_summary.csv"
STATE_FORMAT = "capacity_cohorts_v2"
PRODUCTION_STATE_USE = "SCIENTIFIC_PRODUCTION"
DIAGNOSTIC_STATE_USE = "TEST_ONLY_TRUNCATED_HORIZON"
STATE_COLUMNS = (
    "asset_class",
    "asset_id",
    "province_code",
    "technology",
    "build_year",
    "retire_year",
    "capacity_delta",
    "unit",
    "action",
)


def stable_asset_id(*parts: object) -> str:
    return "::".join(str(part) for part in parts)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class PlanningState:
    root: Path | None
    metadata: dict
    cohorts: pd.DataFrame

    @classmethod
    def empty(cls, boundary_year: int) -> "PlanningState":
        return cls(
            root=None,
            metadata={
                "format": STATE_FORMAT,
                "state_use": "INITIAL_DATA_BOUNDARY",
                "planning_year": int(boundary_year),
                "empty_initial_boundary": True,
            },
            cohorts=pd.DataFrame(columns=STATE_COLUMNS),
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        expected_boundary_year: int,
        allow_test_only: bool = False,
    ) -> "PlanningState":
        root = Path(path).resolve()
        metadata_path = root / STATE_METADATA
        cohorts_path = root / STATE_COHORTS
        if not metadata_path.is_file() or not cohorts_path.is_file():
            raise FileNotFoundError(
                f"Planning state requires {metadata_path} and {cohorts_path}"
            )
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("format") != STATE_FORMAT:
            raise ValueError("Unsupported planning-state format")
        if int(metadata.get("planning_year", -1)) != int(expected_boundary_year):
            raise ValueError(
                f"Planning state year {metadata.get('planning_year')} does not match "
                f"required boundary year {expected_boundary_year}"
            )
        required_metadata = {
            "state_use",
            "capacity_cohorts_sha256",
            "state_transition_summary_sha256",
            "source_solution_qc",
            "source_solution_qc_sha256",
            "source_solve_report_sha256",
        }
        missing_metadata = sorted(
            key for key in required_metadata if not metadata.get(key)
        )
        if missing_metadata:
            raise ValueError(
                "Planning-state metadata missing required integrity fields: "
                + ", ".join(missing_metadata)
            )
        state_use = str(metadata["state_use"])
        if state_use not in {PRODUCTION_STATE_USE, DIAGNOSTIC_STATE_USE}:
            raise ValueError(f"Unsupported planning-state use: {state_use}")
        if state_use == DIAGNOSTIC_STATE_USE and not allow_test_only:
            raise ValueError(
                "Diagnostic planning state requires explicit allow_test_only=True"
            )
        expected_hash = str(metadata["capacity_cohorts_sha256"])
        actual_hash = sha256_file(cohorts_path)
        if expected_hash != actual_hash:
            raise ValueError("Planning-state cohort SHA256 mismatch")
        summary_path = root / STATE_SUMMARY
        if not summary_path.is_file():
            raise FileNotFoundError(f"Planning-state summary is missing: {summary_path}")
        if sha256_file(summary_path) != metadata["state_transition_summary_sha256"]:
            raise ValueError("Planning-state transition-summary SHA256 mismatch")
        source_qc_path = root.parent / str(metadata["source_solution_qc"])
        if not source_qc_path.is_file():
            raise FileNotFoundError(
                f"Planning-state source QC is missing: {source_qc_path}"
            )
        if sha256_file(source_qc_path) != metadata["source_solution_qc_sha256"]:
            raise ValueError("Planning-state source solution QC SHA256 mismatch")
        source_qc_payload = json.loads(source_qc_path.read_text(encoding="utf-8"))
        if source_qc_payload.get("status") != "PASS":
            raise ValueError("Planning-state source solution QC is not PASS")
        source_solve_path = root.parent / "solve_report.json"
        if not source_solve_path.is_file():
            raise FileNotFoundError(
                f"Planning-state source solve report is missing: {source_solve_path}"
            )
        if sha256_file(source_solve_path) != metadata["source_solve_report_sha256"]:
            raise ValueError("Planning-state source solve-report SHA256 mismatch")
        source_solve = json.loads(source_solve_path.read_text(encoding="utf-8"))
        if source_solve.get("status") != "OPTIMAL":
            raise ValueError("Planning-state source solve is not OPTIMAL")
        if source_solve.get("result_use") != state_use:
            raise ValueError("Planning-state use does not match source solve result_use")
        if int(source_solve.get("planning_year", -1)) != int(expected_boundary_year):
            raise ValueError("Planning-state source solve planning_year mismatch")
        from .io_contract import validate_result_manifest

        manifest_ok, manifest_failures = validate_result_manifest(root.parent)
        if not manifest_ok:
            raise ValueError(
                "Planning-state source result manifest is invalid: "
                + ", ".join(manifest_failures[:10])
            )
        cohorts = pd.read_csv(cohorts_path)
        missing = sorted(set(STATE_COLUMNS).difference(cohorts.columns))
        if missing:
            raise ValueError(f"Planning-state cohorts missing columns: {', '.join(missing)}")
        cohorts = cohorts.loc[:, STATE_COLUMNS].copy()
        if cohorts.duplicated(
            ["asset_class", "asset_id", "technology", "build_year", "action"]
        ).any():
            raise ValueError("Duplicate planning-state cohort keys")
        numeric = cohorts[["build_year", "retire_year", "capacity_delta"]].apply(
            pd.to_numeric, errors="coerce"
        )
        if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy(float)).all():
            raise ValueError("Planning-state cohort numeric fields are invalid")
        if (numeric.retire_year <= numeric.build_year).any():
            raise ValueError("Planning-state retire_year must be later than build_year")
        cohorts[["build_year", "retire_year", "capacity_delta"]] = numeric
        return cls(root=root, metadata=metadata, cohorts=cohorts)

    def active_adjustment(
        self,
        asset_class: str,
        asset_ids: Iterable[str],
        *,
        planning_year: int,
        unit: str,
    ) -> np.ndarray:
        ids = pd.Index([str(value) for value in asset_ids], dtype="object")
        if self.cohorts.empty:
            return np.zeros(len(ids), dtype=float)
        selected = self.cohorts.loc[
            self.cohorts.asset_class.eq(asset_class)
            & self.cohorts.unit.eq(unit)
            & self.cohorts.build_year.le(int(planning_year))
            & self.cohorts.retire_year.gt(int(planning_year))
        ]
        unknown_units = set(
            self.cohorts.loc[
                self.cohorts.asset_class.eq(asset_class), "unit"
            ].astype(str)
        ).difference({unit})
        if unknown_units:
            raise ValueError(
                f"Planning-state unit mismatch for {asset_class}: {sorted(unknown_units)}"
            )
        unknown_ids = set(selected.asset_id.astype(str)).difference(ids)
        if unknown_ids:
            raise ValueError(
                f"Planning state references unknown {asset_class} assets: "
                f"{sorted(unknown_ids)[:10]}"
            )
        grouped = selected.groupby(selected.asset_id.astype(str)).capacity_delta.sum()
        return grouped.reindex(ids, fill_value=0.0).to_numpy(dtype=float)


def write_planning_state(
    output_dir: str | Path,
    *,
    config: ModelConfig,
    previous_state: PlanningState,
    new_cohorts: pd.DataFrame,
    source_solution_qc: str,
    state_use: str,
) -> Path:
    """Write an additive, checksummed state bundle for the next planning year."""
    output_dir = Path(output_dir)
    state_dir = output_dir / "planning_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    missing = sorted(set(STATE_COLUMNS).difference(new_cohorts.columns))
    if missing:
        raise ValueError(f"New cohorts missing columns: {', '.join(missing)}")
    tolerance = float(config.raw["planning_sequence"]["cohort_zero_tolerance"])
    retained = previous_state.cohorts.loc[
        previous_state.cohorts.retire_year.gt(config.planning_year)
    ].copy()
    additions = new_cohorts.loc[
        new_cohorts.capacity_delta.abs().gt(tolerance), STATE_COLUMNS
    ].copy()
    numeric_additions = additions[
        ["build_year", "retire_year", "capacity_delta"]
    ].apply(pd.to_numeric, errors="coerce")
    if (
        numeric_additions.isna().any().any()
        or not np.isfinite(numeric_additions.to_numpy(dtype=float)).all()
        or (numeric_additions.retire_year <= numeric_additions.build_year).any()
    ):
        raise ValueError("New planning-state cohorts contain invalid numeric values")
    frames = [frame for frame in (retained, additions) if not frame.empty]
    cohorts = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=STATE_COLUMNS)
    )
    cohorts = cohorts.sort_values(
        ["asset_class", "asset_id", "technology", "build_year", "action"]
    ).reset_index(drop=True)
    cohorts_path = state_dir / STATE_COHORTS
    cohorts.to_csv(
        cohorts_path,
        index=False,
        compression="gzip",
        encoding="utf-8",
        lineterminator="\n",
    )
    next_planning_year = next(
        (year for year in config.planning_years if year > config.planning_year),
        None,
    )
    active_next = (
        cohorts.loc[
            cohorts.build_year.le(next_planning_year)
            & cohorts.retire_year.gt(next_planning_year)
        ]
        if next_planning_year is not None
        else cohorts.iloc[0:0]
    )
    summary = (
        active_next.groupby(
            ["asset_class", "technology", "unit", "action"], dropna=False
        )
        .agg(cohort_rows=("asset_id", "size"), capacity_delta=("capacity_delta", "sum"))
        .reset_index()
    )
    summary.insert(0, "active_planning_year", next_planning_year)
    summary.to_csv(
        state_dir / STATE_SUMMARY,
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
    )
    if state_use not in {PRODUCTION_STATE_USE, DIAGNOSTIC_STATE_USE}:
        raise ValueError(f"Unsupported planning-state use: {state_use}")
    source_qc_path = output_dir / source_solution_qc
    source_solve_path = output_dir / "solve_report.json"
    if not source_qc_path.is_file() or not source_solve_path.is_file():
        raise FileNotFoundError(
            "Planning state requires source solution_qc.json and solve_report.json"
        )
    metadata = {
        "format": STATE_FORMAT,
        "state_use": state_use,
        "generated_at": datetime.now().astimezone().isoformat(),
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "next_planning_year": next_planning_year,
        "retirement_rule": config.raw["planning_sequence"]["retirement_rule"],
        "source_solution_qc": source_solution_qc,
        "source_solution_qc_sha256": sha256_file(source_qc_path),
        "source_solve_report_sha256": sha256_file(source_solve_path),
        "cohort_rows": int(len(cohorts)),
        "new_cohort_rows": int(len(additions)),
        "active_next_planning_year_rows": int(len(active_next)),
        "capacity_cohorts_sha256": sha256_file(cohorts_path),
        "state_transition_summary_sha256": sha256_file(state_dir / STATE_SUMMARY),
    }
    (state_dir / STATE_METADATA).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return state_dir


def export_solution_planning_state(
    artifacts,
    data,
    config: ModelConfig,
    output_dir: str | Path,
    *,
    state_use: str,
) -> Path:
    """Convert one accepted full-year solution into transferable cohorts."""
    variables = artifacts.variables
    year = config.planning_year
    lifetimes = config.raw["finance"]["default_lifetime_years"]
    rows: list[dict] = []

    def append(
        asset_class: str,
        asset_id: str,
        province_code: int | float | None,
        technology: str,
        capacity_delta: float,
        unit: str,
        lifetime_years: float,
        action: str,
    ) -> None:
        rows.append(
            {
                "asset_class": asset_class,
                "asset_id": str(asset_id),
                "province_code": (
                    "" if province_code is None or pd.isna(province_code)
                    else int(province_code)
                ),
                "technology": str(technology),
                "build_year": year,
                "retire_year": year + int(round(float(lifetime_years))),
                "capacity_delta": float(capacity_delta),
                "unit": unit,
                "action": action,
            }
        )

    # Read each Gurobi solution array once.  Accessing ``MVar.X`` inside the
    # 36,686-site loop repeatedly materializes the full vector and turns state
    # export into an accidental O(n^2) post-processing step.
    vre_new = np.asarray(variables["vre_new"].X, dtype=float)
    for position, site in data.vre_sites.iterrows():
        append(
            "vre",
            artifacts.index["vre_asset_ids"][position],
            site.province_code,
            site.technology,
            vre_new[position],
            "GW",
            lifetimes[site.technology],
            "new_build",
        )
    if getattr(data, "wave", None) is not None and "wave_new" in variables:
        wave_new = np.asarray(variables["wave_new"].X, dtype=float)
        wave_cost_year = str(
            config.raw["wave_energy"]["cost_year_by_planning_year"][str(year)]
        )
        wave_lifetime = float(
            config.raw["wave_energy"]["lifetime_years_by_year"][wave_cost_year]
        )
        for position, site in data.wave.sites.iterrows():
            append(
                "wave",
                artifacts.index["wave_asset_ids"][position],
                site.province_code,
                "wave",
                wave_new[position],
                "GW",
                wave_lifetime,
                "new_build",
            )

    provinces = artifacts.index["province_codes"]
    thermal_index = artifacts.index["thermal_index"]
    thermal_new = variables["thermal_new"].X
    for p, province_code in enumerate(provinces):
        for technology, k in thermal_index.items():
            append(
                "thermal",
                stable_asset_id(province_code, technology),
                province_code,
                technology,
                thermal_new[p, k],
                "GW",
                lifetimes[technology],
                "new_build",
            )
    retrofit = variables["thermal_retrofit_to_ccs"].X
    for pair_position, (non_ccs, ccs) in enumerate(artifacts.index["ccs_pairs"]):
        for p, province_code in enumerate(provinces):
            value = float(retrofit[p, pair_position])
            append(
                "thermal",
                stable_asset_id(province_code, non_ccs),
                province_code,
                non_ccs,
                -value,
                "GW",
                lifetimes[non_ccs],
                "retrofit_out",
            )
            append(
                "thermal",
                stable_asset_id(province_code, ccs),
                province_code,
                ccs,
                value,
                "GW",
                lifetimes[non_ccs],
                "retrofit_in",
            )

    hydro_new = variables["hydro_new"].X
    for position, station in data.hydro_stations.iterrows():
        append(
            "hydro",
            station.hydrochn_row_id,
            station.province_code,
            "hydro",
            hydro_new[position],
            "GW",
            lifetimes["hydro"],
            "new_build",
        )

    storage_new = variables["storage_new"].X
    for p, province_code in enumerate(provinces):
        for technology, s in artifacts.index["storage_index"].items():
            append(
                "storage",
                stable_asset_id(province_code, technology),
                province_code,
                technology,
                storage_new[p, s],
                "GW",
                lifetimes[technology],
                "new_build",
            )

    line_new = np.asarray(variables["line_new"].X, dtype=float)
    for position, line in data.lines.iterrows():
        append(
            "interprovincial_transmission",
            line.line_id,
            None,
            line.preset_technology,
            line_new[position],
            "GW",
            lifetimes["transmission"],
            "new_build",
        )

    if "intra_load_center_new" in variables:
        for position, edge in data.intra_load_center_edges.iterrows():
            append(
                "intra_load_center_transmission",
                edge.intra_edge_id,
                edge.province_code,
                str(getattr(edge, "technology", "AC_500kV")),
                variables["intra_load_center_new"].X[position],
                "GW",
                lifetimes["transmission"],
                "new_build",
            )

    dac_lifetime = data.dac.set_index("technology").lifetime_years.to_dict()
    dac_new = variables["dac_new"].X
    for p, province_code in enumerate(provinces):
        for technology, d in artifacts.index["dac_index"].items():
            append(
                "dac",
                stable_asset_id(province_code, technology),
                province_code,
                technology,
                dac_new[p, d],
                "MtCO2_per_year",
                dac_lifetime[technology],
                "new_build",
            )

    if "spur_augmentation" in variables:
        spur = variables["spur_augmentation"].X
        for position, site in data.vre_sites.iterrows():
            append(
                "vre_spur",
                artifacts.index["vre_asset_ids"][position],
                site.province_code,
                site.technology,
                spur[position],
                "GW",
                lifetimes["spur"],
                "new_build",
            )
        hydro_spur = variables["hydro_spur_augmentation"].X
        for position, station in data.hydro_stations.iterrows():
            append(
                "hydro_spur",
                station.hydrochn_row_id,
                station.province_code,
                "hydro",
                hydro_spur[position],
                "GW",
                lifetimes["spur"],
                "new_build",
            )
        trunk = variables["trunk_augmentation"].X
        for position, substation in data.substations.iterrows():
            append(
                "trunk",
                substation.substation_id,
                getattr(substation, "province_code", None),
                "AC_trunk",
                trunk[position],
                "GW",
                lifetimes["trunk"],
                "new_build",
            )

    new_cohorts = pd.DataFrame(rows, columns=STATE_COLUMNS)
    return write_planning_state(
        output_dir,
        config=config,
        previous_state=data.planning_state,
        new_cohorts=new_cohorts,
        source_solution_qc="solution_qc.json",
        state_use=state_use,
    )
