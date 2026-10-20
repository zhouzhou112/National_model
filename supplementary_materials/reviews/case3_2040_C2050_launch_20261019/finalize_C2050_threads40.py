"""Audit the 40-thread gates against the unchanged C2050 physical LP."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from cispo_model.factor_screen import mps_section_sha256


def main():
    evidence = HERE / "deployment_C2050_t40"
    target = evidence / "gates.json"
    if target.exists():
        raise FileExistsError(target)
    checks, sections = {}, {}
    for old, new in [("C2050_screen_1h_01", "C2050_t40_1h_01"),
                     ("C2050_24h_01", "C2050_t40_24h_02")]:
        before = mps_section_sha256(HERE / old / "model_archive/original.mps")
        after = mps_section_sha256(HERE / new / "model_archive/original.mps")
        checks[new + ".unchanged_mps_all_sections"] = before == after
        sections[new] = after
        gate = json.loads((HERE / new / "continuation_gate.json").read_text())
        checks[new + ".runner"] = gate["runner_exit_code"] == 0
        checks[new + ".parameters"] = gate["parameters"] == "PASS"
        checks[new + ".tiny_capacity"] = not gate["tiny_capacity_columns"]
    gate = json.loads((HERE / "C2050_t40_24h_02/continuation_gate.json").read_text())
    checks["OPTIMAL"] = gate["status_code"] == 2
    checks["M"] = gate["M"] <= 1e-3
    preservation = gate["preservation_report.json"]
    checks["preservation"] = preservation["status"] == "COMPLETE" and not preservation["errors"]
    checks["credit"] = max(gate["credit"].values()) <= 1e-3
    for name, count in [("test_production_screen_retry.log", 6), ("formal_launch_tests.log", 7)]:
        log = (evidence / name).read_text(encoding="utf-8")
        checks[name] = f"Ran {count} tests" in log and "\nOK" in log
    baseline = json.loads((HERE / "C2050_final_gates.json").read_text())
    checks["previous_full_gates"] = baseline["status"] == "PASS"
    paths = list(baseline["tested_source_lf_sha256"])
    paths += ["config/solver_profiles/barrier_stagea_screened_agg0_2050_v1_threads40.json",
              (HERE.relative_to(ROOT) / "C2050_threads40.sbatch").as_posix(),
              "tests/test_production_screen.py",
              (HERE.relative_to(ROOT) / "run_continuation_gate.py").as_posix()]
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
              for p in paths}
    # Only the profile allowlist/validation changed in model source.
    for p, h in baseline["tested_source_lf_sha256"].items():
        if p != "cispo_model/factor_screen.py":
            checks["unchanged." + p] = hashes[p] == h
    result = dict(status="PASS" if all(checks.values()) else "FAIL", checks=checks,
                  maximum_service_residual_gw_gwh=gate["M"],
                  mps_section_sha256=sections, tested_source_lf_sha256=hashes,
                  previous_gate_sha256=hashlib.sha256((HERE / "C2050_final_gates.json").read_bytes()).hexdigest(),
                  result_use="TEST_ONLY_TRUNCATED_HORIZON",
                  retained_failed_attempt="C2050_t40_24h_01: Gurobi12 version guard, before solve")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
