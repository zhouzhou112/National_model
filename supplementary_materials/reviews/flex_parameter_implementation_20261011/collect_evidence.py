"""Collect small, read-only local evidence for the 2026-10-11 parameter task.

Run from any directory after the documented local checks. Large solver arrays
remain in their original directories; this exports summaries and SHA256 only.
"""
from pathlib import Path
import hashlib
import json
import shutil
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT.parent / "claude_workspace/evidence"


def main():
    rows = []
    out = HERE / "price_taker_reports"
    out.mkdir(exist_ok=True)
    names = ["price_taker_2030_v2central", "price_taker_2030_compensation_20261011",
             "price_taker_2030_cost_only_20261011", "price_taker_2030_participation_only_20261011",
             "price_taker_2060_v2central_prices2030", "price_taker_2030_v2central_qc",
             "price_taker_2030_v2central_scale0", "price_taker_2030_v2central_simplex",
             "price_taker_2030_v2central_presolve0", "price_taker_2030_cost_only_presolve0",
             "price_taker_2060_presolve0_prices2030",
             "price_taker_2030_cost_only_simplex", "price_taker_2060_simplex_prices2030"]
    for name in names:
        folder = EVIDENCE / name
        if not (folder / "report.json").is_file():
            continue
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        shutil.copyfile(folder / "report.json", out / (name + ".json"))
        row = dict(run=name, status=report["status"], max_qc=report.get("max_qc_residual"),
                   physical_qc_pass=report["status"]==2 and report.get("max_qc_residual",float("inf"))<=1e-5,
                   saving_million_cny=report.get("net_saving_million_cny"),
                   scope=report["scope"], alpha_min=report.get("alpha_min"), alpha_max=report.get("alpha_max"),
                   relocated_pool_fraction=report.get("v1g_relocation_fraction_of_reference_pool"),
                   alpha_upper_value_million_cny=report.get("alpha_upper_expansion_value_sum_million_cny"))
        row.update({key+"_gw": value for key,value in report.get("national_contract_gw",{}).items()})
        if (folder / "province_enrollment.csv").is_file():
            table = pd.read_csv(folder / "province_enrollment.csv")
            shutil.copyfile(folder / "province_enrollment.csv", out / (name + ".csv"))
            row.update(beta_min=float(table.beta.min()), beta_max=float(table.beta.max()))
            for service in ("heating", "cooling"):
                capacity = table[service+"_contract_gw"].sum()
                row[service+"_release_utilization"] = float(table[service+"_shift_down_gwh"].sum() / (8760*capacity)) if capacity>1e-3 else 0
        rows.append(row)
    pd.DataFrame(rows).to_csv(HERE / "price_taker_comparison.csv", index=False)
    paths = list((ROOT / "cispo_model").glob("*.py")) + [ROOT / "scripts/price_taker_enrollment.py"]
    (HERE / "final_source_sha256.json").write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+"\n",encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
