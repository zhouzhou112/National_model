"""Run the unchanged production full-year entry point with read-only logging.

Adds actual-parameter evidence before optimize and a raw .sol.gz after the
production solve report, even if its QC fails. Does not relax acceptance or
alter model building, optimize calls, tolerances, or the production checkout.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import runpy
import sys
import time


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    args, forwarded = parser.parse_known_args()
    started = time.monotonic()
    # Bias an actual OOM toward this newly authorized speculative trial only.
    Path("/proc/self/oom_score_adj").write_text("500\n")
    sys.path.insert(0, str(args.repo_root))
    import cispo_model.diagnostics as diagnostics
    original_configure = diagnostics.configure_gurobi
    original_solve = diagnostics.solve_and_report

    def configure(model, config, log_path):
        result = original_configure(model, config, log_path)
        names = ["Method", "Threads", "Crossover", "PDHGGPU", "PDHGConvTol", "PDHGAbsTol",
                 "PDHGRelTol", "TimeLimit", "SoftMemLimit", "Presolve", "NumericFocus", "ScaleFlag"]
        actual = {name: getattr(model.Params, name) for name in names}
        assert actual["Method"] == 6 and actual["Threads"] == 32
        assert actual["Crossover"] == 0 and actual["PDHGGPU"] == 1
        assert actual["PDHGConvTol"] == 1e-2 and actual["PDHGAbsTol"] == 1e-5 and actual["PDHGRelTol"] == 1e-2
        assert math.isinf(actual["TimeLimit"]) and math.isinf(actual["SoftMemLimit"])
        evidence = {"actual_params": {k: ("Infinity" if isinstance(v, float) and math.isinf(v) else v) for k, v in actual.items()},
                    "seconds_since_process_start": time.monotonic() - started,
                    "model_statistics": diagnostics.model_statistics(model),
                    "scope": "read back from actual model immediately before production optimize"}
        (args.control_root / "actual_solver_params.json").write_text(json.dumps(evidence, indent=2) + "\n")
        print("ACTUAL_GPU_PDHG_PARAMS " + json.dumps(evidence["actual_params"]), flush=True)
        return result

    def solve(model, config, output_dir, **kwargs):
        report = original_solve(model, config, output_dir, **kwargs)
        evidence = {"scientific_accepted": False, "note": "raw solver values only; see production QC separately",
                    "sol_count": int(model.SolCount), "status": int(model.Status)}
        if model.SolCount:
            raw_path = Path(output_dir) / "raw_pdhg_solution.sol.gz"
            try:
                model.write(str(raw_path))
                evidence.update(path=str(raw_path), bytes=raw_path.stat().st_size, preservation_status="COMPLETE")
            except Exception as exc:
                evidence.update(preservation_status="FAILED", error=f"{type(exc).__name__}: {exc}")
        else:
            evidence["preservation_status"] = "NO_SOLUTION_AVAILABLE"
        (args.control_root / "raw_solution_preservation.json").write_text(json.dumps(evidence, indent=2) + "\n")
        return report

    diagnostics.configure_gurobi = configure
    diagnostics.solve_and_report = solve
    sys.argv = [str(args.repo_root / "scripts/run_cispo_2030_full_year.py"), *forwarded]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
