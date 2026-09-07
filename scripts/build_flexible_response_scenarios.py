"""Write explicit literature-informed V5 candidate overlays, never solve.

Original scenarios and input tables are retained. Existing output files are
refused. Subsidy levels affect sensitivity enrollment bounds; incentive
payments remain outside the social-cost objective. See the response contract.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cispo_model.flexible_response import RESPONSE_CONTRACT, normal_participation_fraction

PARENTS = ("case1_thermal_v5", "case2_ev_v5", "case3_thermal_ev_v5")
PAPER_DOI = "10.1038/s41467-026-76799-4"


def build(output: Path) -> dict:
    payloads = {}
    for parent in PARENTS:
        source = ROOT / "config/scenarios" / f"{parent}.json"
        raw = json.loads(source.read_text(encoding="utf-8"))
        identifier = parent + "_response_v1"
        raw.update(scenario_id=identifier, description="Explicit proportional thermal enrollment and separate EV willingness/infrastructure caps; unchanged central real costs.",
                   evidence_status="NO_SOLVE_CANDIDATE_REQUIRES_QUALIFICATION", analysis_role="SENSITIVITY",
                   publication_status="NOT_QUALIFIED_FOR_FORMAL_RESULTS", supersedes=None)
        raw["response_evidence"] = dict(parent_scenario_id=parent,
            parent_scenario_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), doi=PAPER_DOI,
            transfer_status="Mechanism-informed aggregate extension, not a reproduction or nationally calibrated parameter set.")
        settings = raw["overrides"]["flexible_load"]
        settings["response_contract"] = dict(version=RESPONSE_CONTRACT,
            maximum_enrollment_fraction=dict(heating=1., cooling=1., ev_v1g=1., ev_v2g=1.),
            v2g_infrastructure_fraction=1., cost_multipliers={})
        settings["parameter_status"]["response_revision"] = "Thermal hourly bounds scale with the same annual contracted population; old thermal retention/comfort/durations and EV efficiency/obligations are preserved. No observed session SOC is claimed."
        payloads[identifier] = raw
    combined = payloads[PARENTS[2] + "_response_v1"]
    levels = []
    for number, gamma in enumerate((.5, 1., 1.5, 2.), 1):
        raw = deepcopy(combined)
        identifier = PARENTS[2] + f"_response_sub{number}_v1"
        raw["scenario_id"] = identifier
        raw["description"] = "Exogenous willingness sensitivity within existing eligible cooling/V2G pools; no heating or V1G willingness extrapolation."
        fraction = normal_participation_fraction(gamma)
        raw["overrides"]["flexible_load"]["response_contract"]["maximum_enrollment_fraction"].update(cooling=fraction, ev_v2g=fraction)
        # Eq.47 offer thresholds are recorded as an explicit ledger convention,
        # not an asserted reconstruction of ambiguous paper Eq.9 multipliers.
        ledger = dict(subsidy_level=number, gamma=gamma, expected_acceptance_fraction=fraction,
            cooling_offer_yuan_per_kwh=gamma*.022, v2g_offer_yuan_per_kwh=gamma*.15,
            price_basis="Paper-reported RMB; real price year unspecified; no 2025 deflator assumed.",
            objective_includes_incentive_payments=False,
            interpretation="Eq.47 threshold as offer-price convention only. Paper Eq.9 multiplier remains unresolved; these are not national social costs.")
        raw["response_evidence"]["incentive_ledger"] = ledger
        levels.append(ledger)
        payloads[identifier] = raw
    for fraction in (.25, .5):
        raw = deepcopy(combined)
        identifier = PARENTS[2] + f"_response_infra{int(fraction*100)}_v1"
        raw["scenario_id"] = identifier
        raw["description"] = "Independent bidirectional infrastructure ceiling sensitivity; willingness and the baseline demand remain fixed."
        raw["overrides"]["flexible_load"]["response_contract"]["v2g_infrastructure_fraction"] = fraction
        payloads[identifier] = raw
    registry = {}
    with (ROOT / "config/flexible_load_v5_central_parameters.csv").open(encoding="utf-8-sig", newline="") as f:
        registry = {r["parameter_id"]: r for r in csv.DictReader(f)}
    mapping = {
        "heating": {"enablement_cost_yuan_per_kw_year": "thermal.enablement_cost", "activation_cost_yuan_per_mwh": "thermal.activation_cost"},
        "cooling": {"enablement_cost_yuan_per_kw_year": "thermal.enablement_cost", "activation_cost_yuan_per_mwh": "thermal.activation_cost"},
        "ev_v1g": {"enablement_cost_yuan_per_kw_year": "ev.v1g_enablement_cost", "activation_cost_yuan_per_mwh": "ev.v1g_activation_cost"},
        "ev_v2g": {"enablement_cost_yuan_per_kw_year": "ev.v2g_availability_cost", "infrastructure_cost_yuan_per_kw_year": "ev.v2g_infrastructure_cost",
                   "activation_cost_yuan_per_mwh": "ev.v2g_owner_compensation_cost", "degradation_cost_yuan_per_mwh": "ev.v2g_degradation_cost"},
    }
    for level in ("low", "high"):
        raw = deepcopy(combined)
        identifier = PARENTS[2] + f"_response_cost_{level}_v1"
        raw["scenario_id"] = identifier
        raw["description"] = "Bundled real-cost sensitivity using existing V5 registry bounds; not paper subsidy costs or a single-factor experiment."
        raw["response_evidence"]["cost_registry"] = dict(
            path="config/flexible_load_v5_central_parameters.csv",
            sha256=hashlib.sha256((ROOT/"config/flexible_load_v5_central_parameters.csv").read_bytes()).hexdigest(),
            selected_bound=level,
        )
        raw["overrides"]["flexible_load"]["response_contract"]["cost_multipliers"] = {
            service: {field: float(registry[key][level+"_value"])/float(registry[key]["central_value"])
                      for field, key in fields.items()} for service, fields in mapping.items()}
        payloads[identifier] = raw
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "flexible_response_candidates_v1.manifest.json"
    targets = [output / f"{key}.json" for key in payloads] + [manifest_path]
    if any(p.exists() for p in targets):
        raise FileExistsError("Refusing to overwrite response candidate files")
    for key, raw in payloads.items():
        (output/f"{key}.json").write_bytes((json.dumps(raw, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    manifest = dict(version="response_candidates_v1", optimize_called=False, presolve_called=False,
        objective_includes_incentive_payments=False, paper_doi=PAPER_DOI, subsidy_levels=levels,
        candidates={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in targets[:-1]},
        implementation_boundary="No new hourly states, binaries, fixed SOC or observed plug-session data. Existing Base/inputs/central cases remain immutable.")
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for new candidate overlays; existing files are refused")
    args = parser.parse_args()
    manifest = build(args.output_dir)
    print(json.dumps(dict(output_dir=str(args.output_dir), candidates=len(manifest["candidates"]), optimize_called=False)))


if __name__ == "__main__":
    main()
