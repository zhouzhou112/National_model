"""Read-only server gate for the CISPO 2030/8760 model."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-raw-grfr",
        action="store_true",
        help="Require the two source 2019 GRFR NetCDF files on the server.",
    )
    parser.add_argument(
        "--verify-raw-grfr-sha256",
        action="store_true",
        help="Hash the raw files against raw_grfr_transfer_manifest.json.",
    )
    args = parser.parse_args()
    if args.verify_raw_grfr_sha256 and not args.require_raw_grfr:
        raise SystemExit("--verify-raw-grfr-sha256 requires --require-raw-grfr")
    project = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("CISPO_DATA_ROOT", str(project / "data")))
    cf_root = Path(os.environ.get("CISPO_CF_ROOT", ""))
    hydro_root = Path(os.environ.get("CISPO_HYDRO_ROOT", ""))
    raw_grfr_root = Path(os.environ.get("CISPO_RAW_GRFR_ROOT", ""))
    required_cf = [
        cf_root / technology / f"cf_hourly_{technology}_2023.zarr"
        for technology in ("mixed_wind", "offshore_wind", "onshore_wind", "pv")
    ]
    required_hydro = [
        hydro_root / "grfr_target_comids_hourly_2019.nc",
        hydro_root / "grfr_monthly_p10_single_year_proxy_2019.nc",
        hydro_root / "ror_hourly_profiles_2019_provisional.nc",
    ]
    required_raw_grfr = [
        raw_grfr_root / "output_pfaf_03_2019.nc",
        raw_grfr_root / "output_pfaf_04_2019.nc",
    ]
    disk = shutil.disk_usage(project)
    report = {
        "status": "PASS",
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "project_root": str(project),
        "project_disk_free_gib": round(disk.free / 1024**3, 2),
        "environment": {
            "CISPO_CF_ROOT": str(cf_root),
            "CISPO_HYDRO_ROOT": str(hydro_root),
            "CISPO_DATA_ROOT": str(data_root),
            "CISPO_RAW_GRFR_ROOT": str(raw_grfr_root),
        },
        "packages": {
            name: importlib.util.find_spec(name) is not None
            for name in ("numpy", "pandas", "scipy", "netCDF4", "zarr", "psutil", "gurobipy")
        },
        "capacity_factor_stores": [
            {"path": str(path), "exists": path.exists(), "bytes": directory_size(path) if path.exists() else None}
            for path in required_cf
        ],
        "hydrology_files": [
            {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else None}
            for path in required_hydro
        ],
        "raw_grfr_files": [
            {"path": str(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else None}
            for path in required_raw_grfr
        ],
        "model_ready_data": {
            "path": str(data_root),
            "exists": data_root.exists(),
            "bytes": directory_size(data_root) if data_root.exists() else None,
        },
    }
    hard_fail = []
    if not all(report["packages"][name] for name in ("numpy", "pandas", "scipy", "netCDF4", "zarr", "psutil")):
        hard_fail.append("scientific Python environment incomplete")
    if not all(row["exists"] for row in report["capacity_factor_stores"]):
        hard_fail.append("capacity-factor stores incomplete")
    if not all(row["exists"] for row in report["hydrology_files"]):
        hard_fail.append("hydrology inputs incomplete")
    if not report["model_ready_data"]["exists"]:
        hard_fail.append("model-ready data root missing")
    hydro_stations_path = data_root / "hydro" / "hydro_stations.csv"
    classification_path = data_root / "hydro" / "classification_summary.csv"
    cascade_nodes_path = data_root / "hydro" / "cascade_topology_nodes.csv"
    cascade_edges_path = data_root / "hydro" / "cascade_topology_edges.csv"
    report["hydro_station_model"] = {
        "hydro_stations_path": str(hydro_stations_path),
        "classification_summary_path": str(classification_path),
        "cascade_nodes_path": str(cascade_nodes_path),
        "cascade_edges_path": str(cascade_edges_path),
    }
    if hydro_stations_path.is_file():
        import pandas as pd

        stations = pd.read_csv(hydro_stations_path, low_memory=False)
        required_columns = {
            "operation_type_model", "operation_type_scope",
            "installed_operation_type_assigned", "potential_operation_type_paper",
        }
        missing_columns = sorted(required_columns.difference(stations.columns))
        counts = (
            stations["operation_type_model"].value_counts().to_dict()
            if "operation_type_model" in stations
            else {}
        )
        if missing_columns:
            potential_mismatch = None
        else:
            potential = stations["operation_type_scope"].eq("potential_or_nonoperating")
            potential_mismatch = int((
                potential
                & stations["operation_type_model"].ne(
                    stations["potential_operation_type_paper"]
                )
            ).sum())
        report["hydro_station_model"].update(
            station_rows=int(len(stations)),
            reservoir_rows=int(counts.get("reservoir_storage", 0)),
            run_of_river_rows=int(counts.get("run_of_river", 0)),
            potential_paper_rule_mismatches=potential_mismatch,
            missing_required_columns=missing_columns,
        )
        if len(stations) != 2030 or missing_columns or potential_mismatch not in (0, None):
            hard_fail.append("station-level hydropower classification is inconsistent")
    else:
        hard_fail.append("hydro_stations.csv missing")
    if not classification_path.is_file():
        hard_fail.append("hydropower classification summary missing")
    if cascade_nodes_path.is_file() and cascade_edges_path.is_file():
        import pandas as pd

        nodes = pd.read_csv(cascade_nodes_path)
        edges = pd.read_csv(cascade_edges_path)
        cascade_required = {
            "edge_id", "source_node_id", "target_node_id",
            "source_hydrochn_row_ids", "target_hydrochn_row_ids",
            "travel_lag_h", "lag_quality_flag",
        }
        missing_edge_columns = sorted(cascade_required.difference(edges.columns))
        report["hydro_cascade_model"] = {
            "node_rows": int(len(nodes)),
            "edge_rows": int(len(edges)),
            "missing_edge_columns": missing_edge_columns,
            "low_correlation_edges": int(edges.lag_quality_flag.eq("LOW_CORRELATION").sum())
            if "lag_quality_flag" in edges else None,
            "max_lag_bound_edges": int(edges.lag_quality_flag.eq("MAX_LAG_BOUND_SELECTED").sum())
            if "lag_quality_flag" in edges else None,
            "maximum_travel_lag_h": float(edges.travel_lag_h.max())
            if "travel_lag_h" in edges and len(edges) else None,
        }
        if len(nodes) != 142 or len(edges) != 124 or missing_edge_columns:
            hard_fail.append("core hydropower cascade topology is inconsistent")
    else:
        hard_fail.append("core hydropower cascade topology files missing")
    if args.require_raw_grfr:
        if not all(row["exists"] for row in report["raw_grfr_files"]):
            hard_fail.append("raw GRFR source files incomplete")
        manifest_path = raw_grfr_root / "raw_grfr_transfer_manifest.json"
        report["raw_grfr_manifest"] = {"path": str(manifest_path), "exists": manifest_path.is_file()}
        if not manifest_path.is_file():
            hard_fail.append("raw GRFR transfer manifest missing")
        elif args.verify_raw_grfr_sha256:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = {
                row["name"]: row
                for row in manifest["raw_grfr_direct_transfer"]["files"]
            }
            verified = []
            for path in required_raw_grfr:
                actual_hash = sha256(path) if path.is_file() else None
                row = expected.get(path.name, {})
                ok = bool(
                    actual_hash
                    and actual_hash == row.get("sha256")
                    and path.stat().st_size == row.get("bytes")
                )
                verified.append({"name": path.name, "sha256": actual_hash, "pass": ok})
                if not ok:
                    hard_fail.append(f"raw GRFR checksum mismatch: {path.name}")
            report["raw_grfr_sha256_verification"] = verified
    if report["packages"]["gurobipy"]:
        try:
            from check_gurobi_full_license import check_full_license

            report["gurobi_license_gate"] = check_full_license()
        except Exception as exc:  # preserve the exact solver/license diagnostic
            report["gurobi_license_gate"] = {
                "status": "HARD_FAIL",
                "error": f"{type(exc).__name__}: {exc}",
            }
            hard_fail.append("Gurobi full-license gate failed")
    else:
        report["gurobi_license_gate"] = {"status": "HARD_FAIL", "error": "PACKAGE_MISSING"}
        hard_fail.append("gurobipy package missing")
    report["hard_failures"] = hard_fail
    report["status"] = "HARD_FAIL" if hard_fail else "PASS"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(2 if hard_fail else 0)


if __name__ == "__main__":
    main()
