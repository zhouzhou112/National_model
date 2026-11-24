"""Reuse the established immutable small-evidence collector for two solved cases.

Run from repository root. No cloud writes or model/checkpoint downloads.
Downloaded evidence is byte-verified against source SHA and result manifests.
"""
from pathlib import Path
import importlib.util
import json

HERE = Path(__file__).resolve().parent
RELEASES = {
    "base2060": "20261012_base2060_v9a12_t48_m750_tol1e4_v1",
    "case3_2030": "20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1",
}
EXTRA_NAMES = [
    "model_archive/archive_manifest.json",
    "barrier_checkpoint/barrier_checkpoint_manifest.json",
    "model_config_snapshot.json", "solver_parameters.json",
    "cost_components.csv", "annual_generation_by_technology.csv",
    "annual_storage_operation_by_technology.csv", "annual_carbon_ccs.json",
    "annual_flexible_load_by_province.csv", "dual_export_status.json",
    "candidate_selection.csv",
]


def main():
    source = HERE.parent / "base_acceptance_relative_v1_20261012/collect_evidence.py"
    spec = importlib.util.spec_from_file_location("historical_collector", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE
    module.RELEASES = RELEASES
    module.REMOTE = module.REMOTE.replace(
        "    files={}", "    names += " + repr(EXTRA_NAMES) + "\n    files={}")
    module.main()
    collection = json.loads((HERE / "collection_manifest.json").read_text())
    required = {
        "solution_qc.json", "solve_report.json", "preservation_report.json",
        "result_manifest.json", "run_identity.json", "build_report.json",
        "planning_state_candidate/state_metadata.json",
        "planning_state_candidate/capacity_cohorts.csv.gz",
        "model_archive/archive_manifest.json",
        "barrier_checkpoint/barrier_checkpoint_manifest.json",
    }
    for key, value in collection.items():
        assert required <= set(value["files"]), (key, required - set(value["files"]))
    print("Required acceptance evidence present; original source bytes verified.")


if __name__ == "__main__":
    main()
