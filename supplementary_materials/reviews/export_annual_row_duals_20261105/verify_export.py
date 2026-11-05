"""Finite local 1h/24h identity and same-iterate export checks; no production runs.

Run with the repository's RL Python, CISPO_WAVE_ROOT set as documented.
Baseline source is read from Git (default HEAD); no checkout is modified.
Only the new 24h diagnostic is optimized, with an isolated eight-thread profile.
"""
import argparse
from datetime import datetime, timezone
import gc
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def baseline_module(name, path):
    spec = importlib.util.spec_from_file_location("cispo_model._baseline_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(model):
    model.update()
    return {key: int(getattr(model, key)) for key in ("NumVars", "NumConstrs", "NumNZs", "Fingerprint")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", default="HEAD")
    parser.add_argument("--reuse-fingerprints", type=Path,
        help="Reuse verified same-source 1h/24h build evidence, then build only 24h")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = output / "source_before"
    before.mkdir()
    commit = subprocess.check_output(["git", "rev-parse", args.baseline], cwd=ROOT, text=True).strip()
    for name in ("load_center", "solution_export"):
        (before / (name + ".py")).write_bytes(subprocess.check_output(["git", "show", f"{commit}:cispo_model/{name}.py"], cwd=ROOT))
    baseline_load_center = baseline_module("load_center", before / "load_center.py")
    baseline_export = baseline_module("solution_export", before / "solution_export.py")
    import numpy as np
    import gurobipy as gp
    from cispo_model.config import load_model_config
    from cispo_model.data import load_model_data
    from cispo_model import monolithic, solution_export
    config = load_model_config(ROOT / "config/optimization_numeric_dac_by_year_v9.json",
        scenario_path=ROOT / "config/scenarios/case3_thermal_ev_v5.json",
        solver_path=ROOT / "config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json")
    config.raw["numerics"]["threads"] = 8
    data = load_model_data(config)
    result = {"baseline_commit": commit, "gurobi_version": gp.gurobi.version(),
        "scope": "TEST_ONLY_TRUNCATED_HORIZON", "configuration": config.raw,
        "source_after_sha256": {name: sha(ROOT / name) for name in ["cispo_model/load_center.py", "cispo_model/solution_export.py", "cispo_model/io_contract.py"]},
        "gates": {}}
    if args.reuse_fingerprints:
        previous = json.loads(args.reuse_fingerprints.read_text(encoding="utf-8"))
        assert previous["baseline_commit"] == commit
        # Only handle registration changes construction. Export-only metadata
        # may advance while reusing the already matched raw LP fingerprints.
        assert previous["source_after_sha256"]["cispo_model/load_center.py"] == result["source_after_sha256"]["cispo_model/load_center.py"]
        assert not subprocess.check_output(["git", "diff", commit, "--", "cispo_model/master.py", "cispo_model/monolithic.py", "config"], cwd=ROOT)
        assert previous["configuration"] == config.raw
        assert previous["gurobi_version"] == list(gp.gurobi.version())
        assert all(previous["gates"][str(h)]["equal"] for h in (1, 24))
        result["gates"] = previous["gates"]
        result["reused_build_evidence"] = {"path": str(args.reuse_fingerprints), "sha256": sha(args.reuse_fingerprints)}
        current = monolithic.build_full_year_monolithic(config, data, optimization_hours=24)
        assert identity(current.model) == result["gates"]["24"]["after"]
    for hours in (() if args.reuse_fingerprints else (1, 24)):
        with patch.object(monolithic, "attach_annual_load_center_network", baseline_load_center.attach_annual_load_center_network):
            baseline = monolithic.build_full_year_monolithic(config, data, optimization_hours=hours)
        old_identity = identity(baseline.model)
        baseline.model.dispose()
        del baseline
        gc.collect()
        current = monolithic.build_full_year_monolithic(config, data, optimization_hours=hours)
        new_identity = identity(current.model)
        result["gates"][str(hours)] = {"before": old_identity, "after": new_identity, "equal": old_identity == new_identity}
        save(output / "verification.json", result)
        assert old_identity == new_identity
        if hours == 1:
            current.model.dispose()
            del current
            gc.collect()
    model = current.model
    from cispo_model.diagnostics import configure_gurobi
    configure_gurobi(model, config, output / "solve_24h.log")
    model.Params.LogFile = str(output / "solve_24h.log")
    model.optimize()
    result["diagnostic_solve"] = {"status": model.Status, "runtime_seconds": model.Runtime,
        "objective_million_cny": model.ObjVal if model.SolCount else None,
        "parameters": {k: getattr(model.Params, k) for k in ("Threads", "Method", "Crossover", "BarConvTol", "Aggregate", "NumericFocus")}}
    save(output / "verification.json", result)
    assert model.Status == gp.GRB.OPTIMAL
    assert model.Params.Method == 2 and model.Params.Crossover == 0 and model.Params.SolutionTarget == 1
    assert model.Params.Threads == 8 and model.Params.Aggregate == 0
    # Same exact primal/dual vector: timestamp freezing is for byte comparison only.
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 5, 0, 0, tzinfo=timezone.utc)
    for label, module in (("before", baseline_export), ("after", solution_export)):
        with patch.object(module, "datetime", FrozenDatetime), patch("gzip.time.time", return_value=1793836800):
            module.export_operational_solution(current, data, config, output / label, enforce_qc=False)
    old_files = {p.name: p for p in (output / "before").iterdir() if p.is_file()}
    new_files = {p.name: p for p in (output / "after").iterdir() if p.is_file()}
    assert set(new_files) - set(old_files) == {"annual_row_duals.csv"}
    differences = [name for name in old_files if sha(old_files[name]) != sha(new_files[name])]
    result["existing_export_byte_differences"] = differences
    old_status = json.loads(old_files["dual_export_status.json"].read_text())
    new_status = json.loads(new_files["dual_export_status.json"].read_text())
    assert old_status["available"] and new_status["annual_row_duals_exported"]
    assert all(new_status[k] == v for k, v in old_status.items())
    assert differences == ["dual_export_status.json"]
    import pandas as pd
    table = pd.read_csv(output / "after/annual_row_duals.csv", keep_default_na=False)
    constraints = model.getConstrs()
    offline = []
    # T4's MPS row-name matching against the exact original-index BarPi.
    import re
    for index, constraint in enumerate(constraints):
        name = constraint.ConstrName
        if (name.startswith("load_center_annual_energy_balance_") or
            name.startswith("intra_load_center_annual_capacity[") or
            (name.startswith("province_annual_") and re.search(r"_p\d+$", name))):
            offline.append((index, name, constraint.BarPi))
    assert table.original_row_index.tolist() == [r[0] for r in offline]
    assert table.row_name.tolist() == [r[1] for r in offline]
    delta = float(np.max(np.abs(table.pi_million_cny_per_gwh - np.asarray([r[2] for r in offline]))))
    paired = table[table.row_family.isin(["province_annual_non_spatial_injection", "province_annual_effective_demand"])].groupby("province_code").pi_million_cny_per_gwh.sum()
    result["annual_row_validation"] = {"rows": len(table), "family_counts": table.row_family.value_counts().to_dict(),
        "offline_t4_max_absolute_difference": delta, "paired_provinces": len(paired),
        "injection_demand_max_absolute_residual_cny_per_mwh": float(paired.abs().max() * 1000),
        "same_barpi_original_order": True}
    result["existing_export_byte_identical_count"] = len(old_files) - 1
    assert delta <= 1e-12
    assert len(paired) == 31
    result["status"] = "PASS"
    save(output / "verification.json", result)
    model.dispose()
    print(json.dumps({k: v for k, v in result.items() if k != "configuration"}, indent=2))


if __name__ == "__main__":
    main()
