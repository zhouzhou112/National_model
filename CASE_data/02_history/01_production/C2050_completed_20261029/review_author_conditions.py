"""Evaluate the C2050 author conditions without inventing a row-family tolerance.

This case-specific review retains the baseline relative_v1 assessment and
source archives. It adds an evidence-linked acceptance/stop record only.
"""
from pathlib import Path
import hashlib
import json
import math
import argparse

HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def row_family_check(row, *, annual_account_relative=False):
    if row['name'] != 'province_annual_external_sent_p13':
        raise ValueError('Unreviewed row family; report before applying a tolerance')
    if row['status'] != 'ORDER_AND_ROW_VERIFIED' or row['sense'] != '=':
        raise ValueError('Row identity/sense not verified')
    residual = float(row['violation'])
    scale = float(row['row_magnitude'])
    if not math.isfinite(residual) or residual < 0 or not math.isfinite(scale) or scale <= 0:
        raise ValueError('Invalid row residual or magnitude')
    # AGENTS 2026-10-12 evening, item 4: general GW/GWh residuals use
    # max(strict tolerance, 1e-3). No annual-account proportional rule exists.
    limit = max(1e-3, 1e-6*scale) if annual_account_relative else max(1e-5, 1e-3)
    return dict(passed=residual <= limit, name=row['name'], province_code=13,
                province_name='河北', family='province_annual_external_sent', unit='GWh',
                variable_families=['province_annual_external_sent_gwh',
                                   'flow_forward_gw', 'flow_reverse_ac_gw'],
                residual_gwh=residual, row_magnitude_gwh=scale,
                relative_residual=residual/scale,
                tolerance_gwh=limit, equivalent_relative_tolerance=limit/scale,
                ratio_to_authorized_tolerance=residual/limit,
                rule=('AGENTS.md 2026-10-30 item 5: max(1e-3 GWh, 1e-6 * annual row energy)' if annual_account_relative
                      else 'AGENTS.md 2026-10-12 evening item 4: max(strict, 1e-3 GW/GWh)'),
                proportional_annual_account_tolerance_authorized=annual_account_relative,
                equation='annual external sent GWh = sum of outgoing forward and AC reverse GW over 8760 one-hour periods',
                row_scaling='Physical GWh; coefficient of annual account is 1; no capacity-link scaling',
                source_code='cispo_model/load_center.py:394-398, frozen source SHA in frozen_row_formulation.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-version', choices=['20261029','20261030'], default='20261029')
    args = parser.parse_args()
    target = HERE/f'acceptance_author_{args.review_version}.json'
    if target.exists():
        raise FileExistsError(target)
    output = HERE/'C2050/output_8760'
    solve = json.loads((output/'solve_report.json').read_text())
    assessed = json.loads((HERE/'C2050/assessment/solution_qc_relative_v1.json').read_text())
    profile = assessed['acceptance_profiles']['relative_v1']
    row_receipt = json.loads((HERE/'row_audit_receipt.json').read_text())
    row = row_receipt['audit']
    price = json.loads((HERE/'C2050/price_receipt.json').read_text())
    collection = json.loads((HERE/'C2050/collect_receipt.json').read_text())
    backup = json.loads((HERE/'backup_complete_20261029.json').read_text())
    result_sha = sha(output/'result_manifest.json')
    assert result_sha == backup['source_result_manifest_sha256'] == row['source_result_manifest_sha256']
    for name, record in row['source_files'].items():
        if name in collection['files']:
            assert collection['files'][name] == record
    assert sha(output/'solve_report.json') == row['source_files']['solve_report.json']['sha256']
    assert row['index'] == solve['solution_quality_locations']['maximum_constraint_violation']['index']
    reported = solve['solution_quality']['maximum_constraint_violation']
    # Disclosure of summation-rounding agreement only; never a scientific relaxation.
    agreement = abs(row['violation']-reported)
    if agreement > 1e-7:
        raise ValueError('Original quality and recomputed row differ; inspect before acceptance')
    family = row_family_check(row, annual_account_relative=args.review_version=='20261030')
    physical = {k:v for k,v in profile['checks'].items() if k != 'solver'}
    conditions = dict(physical_relative_checks=all(v.get('passed') is not False for v in physical.values()),
                      maximum_constraint_row_within_family_tolerance=family['passed'],
                      own_BarPi_certificate=price['scope']=='FULL_YEAR' and 0 <= price['B_over_objective'] <= 1e-2)
    metrics = solve['solution_contract']['barrier_primal_dual_metrics']
    pinf = float(metrics['primal_infeasibility'])
    gap = float(metrics['relative_primal_dual_objective_gap'])
    conditions['barrier_terminal_range_and_gap'] = solve['status']=='OPTIMAL' and 1e-2 < pinf <= 1e-1 and 0 <= gap <= 1e-2
    # Cross-link own-dual identity from the independently SHA-verified pricing receipt.
    identity = price['source_identity']
    identity_text = json.dumps(identity, sort_keys=True)
    for name in ['model_archive/original.mps.gz', 'barrier_checkpoint/barrier_checkpoint_manifest.json']:
        assert row['source_files'][name]['sha256'] in identity_text, name
    checkpoint = json.loads((output/'barrier_checkpoint/barrier_checkpoint_manifest.json').read_text())
    assert checkpoint['vectors']['dual']['sha256'] in identity_text
    accepted = all(conditions.values())
    result = dict(status='PASS' if accepted else 'STOP_AUTHOR_CONDITION_NOT_MET',
                  author_decision='ACCEPTED_RELATIVE_V1_'+args.review_version if accepted else 'NOT_ADOPTED_CONDITIONS_UNMET',
                  conditions=conditions, row=family,
                  archived_violation_gwh=reported, recomputation_difference_gwh=agreement,
                  barrier_primal_infeasibility=pinf, relative_primal_dual_gap=gap,
                  barrier_primal_infeasibility_disclosure_only=accepted,
                  physical_deferred=[k for k,v in physical.items() if v.get('passed') is None],
                  certificate={k:price[k] for k in ['B_million_cny','B_over_objective','near_optimality_decision','base_comparison_decision','certificate_sha256','certificate_path']},
                  source_evidence=dict(source_sha256={'result_manifest.json':result_sha,
                      **{name:row['source_files'][name]['sha256'] for name in row['source_files']}}),
                  evidence_sha256={name:sha(HERE/name) for name in [
                      'row_audit_receipt.json','frozen_row_formulation.json','backup_complete_20261029.json',
                      'C2050/price_receipt.json','C2050/collect_receipt.json',
                      'C2050/assessment/solution_qc_relative_v1.json']},
                  C2060=dict(R1_executed=False,engineering_gates_executed=False,submitted=False,released=False),
                  source_archives_modified=False)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],conditions=conditions,row=family),ensure_ascii=False))


if __name__ == '__main__':
    main()
