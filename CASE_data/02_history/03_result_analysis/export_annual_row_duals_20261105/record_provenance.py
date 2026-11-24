"""Write existing provenance contract for a completed isolated export check."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verification", type=Path)
    args = parser.parse_args()
    result = json.loads(args.verification.read_text(encoding="utf-8"))
    from cispo_model.config import ModelConfig
    from cispo_model.io_contract import write_run_provenance
    from cispo_model.planning_state import PlanningState
    config = ModelConfig(ROOT / "config/optimization_numeric_dac_by_year_v9.json",
        result["configuration"], ROOT / "config/scenarios/case3_thermal_ev_v5.json",
        ROOT / "config/solver_profiles/barrier_stagea_screened_agg0_v1_threads48.json")
    output = args.verification.parent / "provenance"
    output.mkdir(exist_ok=False)
    write_run_provenance(output, config, data_root=ROOT / "data",
        planning_state=PlanningState.empty(config.boundary_year))
    print(output)


if __name__ == "__main__":
    main()
