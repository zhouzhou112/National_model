"""Read-only server gate for the CISPO 2030/8760 model."""
from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
import sys
from pathlib import Path


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("CISPO_DATA_ROOT", str(project / "data")))
    cf_root = Path(os.environ.get("CISPO_CF_ROOT", ""))
    hydro_root = Path(os.environ.get("CISPO_HYDRO_ROOT", ""))
    required_cf = [
        cf_root / technology / f"cf_hourly_{technology}_2023.zarr"
        for technology in ("mixed_wind", "offshore_wind", "onshore_wind", "pv")
    ]
    required_hydro = [
        hydro_root / "grfr_target_comids_hourly_2019.nc",
        hydro_root / "grfr_monthly_p10_single_year_proxy_2019.nc",
        hydro_root / "ror_hourly_profiles_2019_provisional.nc",
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
