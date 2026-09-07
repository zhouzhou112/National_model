"""Final parameter/prebuild audit for the frozen three portfolios; never solve.

Run from the repository: python scripts/audit_final_portfolio_no_solve.py
  --base-snapshot PATH --output-dir NEW_DIRECTORY
Reads local V5 data and a previously copied running-Base configuration.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gurobipy as gp
import numpy as np
import pandas as pd
from scripts.validate_flexible_portfolios import read_service_inputs, CASES
from cispo_model.config import load_model_config
from cispo_model.data import DATA_ROOT
from cispo_model.flexible_load_numerics import prebuild_flexible_load_solver_compatibility
from cispo_model.io_contract import sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-snapshot", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with ExitStack() as stack:
        for method in ("optimize", "optimizeAsync", "presolve", "feasRelax", "feasRelaxS"):
            if hasattr(gp.Model, method):
                stack.enter_context(patch.object(gp.Model, method, side_effect=AssertionError(method + " forbidden")))
        data = read_service_inputs(2030)  # Loader enforces V5 input manifest and scientific closure.
        base = json.loads(args.base_snapshot.read_text(encoding="utf-8"))["resolved_configuration"]
        report = dict(generated_at=datetime.now().astimezone().isoformat(), optimize_called=False,
                      presolve_called=False, remote_mutation=False, planning_year=2030,
                      provinces=len(data.provinces), hours=8760, cases={}, data_file_checks=[],
                      git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
        manifest_path = DATA_ROOT / "flexibility/flexible_load_v5.manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, row in manifest["generated_files"].items():
            path = DATA_ROOT / relative
            digest = sha256_file(path)
            report["data_file_checks"].append(dict(path=relative, sha256=digest,
                pass_hash=digest == row["sha256"], pass_size=path.stat().st_size == row["size_bytes"]))
        report["manifest_coverage"] = manifest["coverage"]
        report["baseline_component_closure_max_gw"] = float(np.abs(data.load_gw - sum(data.load_components_gw.values())).max())
        service = data.flexible_load_v4
        report["ev_reference_energy_max_gwh"] = float(np.abs(service.ev_mobility["driving_energy_withdrawal_gwh"]
            - .94 * .15 * data.load_components_gw["ev"]).max())
        for case in CASES:
            path = ROOT / f"config/scenarios/{case}.json"
            config = load_model_config(scenario_path=path,
                solver_path=ROOT / "config/solver_profiles/barrier_stagea_portfolio_v1_threads44.json",
                formulation_path=ROOT / "config/formulation_profiles/annual_capacity_link_rows_8192_v1.json")
            strict = prebuild_flexible_load_solver_compatibility(config, data, hours=8760)
            current = dict(config.raw["numerics"])
            config.raw["numerics"] = dict(base["numerics"])
            loose = prebuild_flexible_load_solver_compatibility(config, data, hours=8760)
            config.raw["numerics"] = current
            recorded = subprocess.check_output(["git", "show", f"HEAD:config/scenarios/{case}.json"])
            report["cases"][case] = dict(scenario_sha256=sha256_file(path),
                unchanged_from_head=path.read_bytes().replace(b"\r\n", b"\n") == recorded.replace(b"\r\n", b"\n"),
                solver_differences={k: {"running_base": base["numerics"].get(k), "portfolio": current.get(k)}
                    for k in base["numerics"].keys() | current.keys() if base["numerics"].get(k) != current.get(k)},
                existing_profile_prebuild=strict, running_base_numerics_prebuild=loose,
                parameters=config.raw["flexible_load"])
        for name in ("thermal_parameters_by_province_v5.csv", "flex_enablement_cost_v5.csv"):
            frame = pd.read_csv(DATA_ROOT / "flexibility" / name)
            group = "component" if "component" in frame else "service"
            report[name] = {str(key): {column: sorted(rows[column].unique().tolist())
                for column in frame.columns if column not in ("province_code", group)}
                for key, rows in frame.groupby(group)}
        report["status"] = "PASS" if all(row["pass_hash"] and row["pass_size"] for row in report["data_file_checks"]) \
            and all(row["unchanged_from_head"] for row in report["cases"].values()) else "FAIL"
        report["formal_launch_authorized"] = False
        report["full_year_solver_qualification"] = "NOT_ESTABLISHED_BY_NO_SOLVE_AUDIT"
        (args.output_dir / "parameter_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: report[key] for key in ("status", "provinces", "hours", "baseline_component_closure_max_gw",
                                                       "ev_reference_energy_max_gwh", "formal_launch_authorized")}, indent=2))


if __name__ == "__main__":
    main()
