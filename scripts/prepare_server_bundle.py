"""Create auditable transfer archives for the CISPO 2030 server workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "transfer_bundle"
MODEL_DATA_DIRS = (
    "sets", "vre", "load", "thermal", "hydro", "biomass",
    "transmission", "carbon", "technology", "grid", "load_center_network",
)
CF_ROOT = Path(r"D:\National_model\Data\Gis\Hourly_cf")
HYDRO_ROOT = Path(
    r"D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro"
    r"\hydro_model_2019_stage1_20260629\model_inputs"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_tree(archive: tarfile.TarFile, source: Path, arcname: str) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    archive.add(source, arcname=arcname, recursive=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-only", action="store_true")
    args = parser.parse_args()
    BUNDLE.mkdir(parents=True, exist_ok=True)
    archives: list[Path] = []

    code_archive = BUNDLE / "national_model_code.tar.gz"
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    with tarfile.open(code_archive, "w:gz") as archive:
        for relative in sorted(set(listed)):
            path = ROOT / relative
            excluded_code = {
                "MODEL_IMPLEMENTATION_STATUS.md",
                "cispo_model/subproblem.py",
                "scripts/build_cispo_2030_master.py",
                "scripts/solve_cispo_2030_block.py",
            }
            if (
                path.is_file()
                and relative not in excluded_code
                and not relative.startswith(("data/", "outputs/", "transfer_bundle/"))
            ):
                archive.add(path, arcname=relative)
    archives.append(code_archive)

    if args.code_only:
        manifest = {
            "generated_at": datetime.now().astimezone().isoformat(),
            "purpose": "CISPO 2030 full-year monolithic LP code refresh",
            "archives": [{
                "name": code_archive.name,
                "bytes": code_archive.stat().st_size,
                "sha256": sha256(code_archive),
            }],
            "excluded": sorted(excluded_code),
        }
        (BUNDLE / "code_transfer_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return

    data_archive = BUNDLE / "model_ready_data.tar.gz"
    with tarfile.open(data_archive, "w:gz") as archive:
        for directory in MODEL_DATA_DIRS:
            add_tree(archive, ROOT / "data" / directory, directory)
        for name in (
            "README.md", "model_defaults.json", "output_manifest.csv",
            "qc_summary.csv", "smoke_test_report.json", "source_manifest.csv",
        ):
            path = ROOT / "data" / name
            if path.exists():
                archive.add(path, arcname=name)
    archives.append(data_archive)

    cf_archive = BUNDLE / "hourly_cf_2023.tar"
    with tarfile.open(cf_archive, "w") as archive:
        for technology in ("mixed_wind", "offshore_wind", "onshore_wind", "pv"):
            name = f"cf_hourly_{technology}_2023.zarr"
            add_tree(archive, CF_ROOT / technology / name, f"{technology}/{name}")
    archives.append(cf_archive)

    hydro_archive = BUNDLE / "hydro_timeseries.tar.gz"
    with tarfile.open(hydro_archive, "w:gz") as archive:
        for name in (
            "grfr_target_comids_hourly_2019.nc",
            "grfr_monthly_p10_single_year_proxy_2019.nc",
            "ror_hourly_profiles_2019_provisional.nc",
        ):
            archive.add(HYDRO_ROOT / name, arcname=name)
    archives.append(hydro_archive)

    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "purpose": "CISPO 2030 full-year monolithic LP server transfer",
        "archives": [
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in archives
        ],
        "excluded": [
            "data/raw (source and rebuild inputs)",
            "data/load_centers_1km (validation-only rasters)",
            "all non-2023 capacity-factor years",
            "outputs and local Gurobi artifacts",
            "SSH keys and Gurobi license files",
        ],
    }
    (BUNDLE / "transfer_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
