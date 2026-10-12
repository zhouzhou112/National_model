"""Freeze explicit diagnostic code/config/input files and data-selected windows.

Usage: python scripts/prepare_flex_diagnostic_bundle.py --output NEW_DIRECTORY
No raw datasets, manuscript modules, external weather stores or credentials copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=False)
    from cispo_model.config import load_model_config
    from cispo_model.data import DATA_ROOT
    from validate_flexible_portfolios import read_service_inputs
    cfg = load_model_config(scenario_path=ROOT / "config/scenarios/case3_thermal_ev_v5.json").for_planning_year(2030)
    data = read_service_inputs(2030, cfg)
    months = pd.date_range("2030-01-01", periods=8760, freq="h").month.to_numpy()
    windows = {}
    for component in ("cooling", "heating"):
        envelope = data.flexible_load_v4.thermal_envelopes_gw[component+"_down"]
        energy = {int(m): float(envelope[:, months==m].sum()) for m in range(1,13)}
        month = max(energy, key=energy.get)
        windows[component] = dict(month=month, start=int(np.flatnonzero(months==month)[0]), monthly_envelope_gwh=energy,
            selection_basis="national sum of contract-eligible downward thermal envelope; unweighted original hourly data")
    (a.output / "windows.json").write_text(json.dumps(windows, indent=2), encoding="utf-8")
    paths = {}
    for folder in ("cispo_model", "config"):
        for file in (ROOT / folder).rglob("*"):
            if file.is_file() and file.suffix in (".py", ".json", ".csv", ".yaml", ".yml"):
                paths["repo/"+file.relative_to(ROOT).as_posix()] = file
    for name in ("run_flex_full_diagnostic.py", "run_flex_server_series.py", "flex_numerics_diagnostics.py", "validate_flexible_portfolios.py"):
        paths["repo/scripts/"+name] = ROOT / "scripts" / name
    contract = json.loads((ROOT / "config/model_input_files.json").read_text())
    for rel in contract["required_model_tables"] + contract["server_validation_sidecars"]:
        file = DATA_ROOT / rel
        if file.is_file(): paths["data/"+rel] = file
    for folder in ("flexibility/participation_pathway_v2", "hydro/repaired_storage_audit_20260913_v2"):
        for file in (DATA_ROOT / folder).rglob("*"):
            if file.is_file(): paths["data/"+file.relative_to(DATA_ROOT).as_posix()] = file
    paths["windows.json"] = a.output / "windows.json"
    manifest = dict(git_commit=subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT,text=True).strip(),
        files=[dict(path=rel, bytes=f.stat().st_size, sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for rel,f in sorted(paths.items())])
    mf = a.output / "bundle_manifest.json"; mf.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    with tarfile.open(a.output / "diagnostic_bundle.tar.gz", "x:gz") as tar:
        for rel, file in paths.items(): tar.add(file, arcname=rel, recursive=False)
        tar.add(mf,arcname="bundle_manifest.json",recursive=False)
    print(json.dumps(dict(windows=windows, files=len(paths), bytes=(a.output / "diagnostic_bundle.tar.gz").stat().st_size)))


if __name__ == "__main__":
    main()
