"""Read-only diagnosis of the post-Shanghai 2060 build and state integrity.

Run in the project Python/data environment after prepare_state_6b.py and
build_gate.py. Reads revision_6d; writes small audit evidence only. Never solves
or changes state/model bounds. The revision name labels a conversation decision,
not an additional section of the author task document.
"""
from pathlib import Path
import csv, gzip, hashlib, json, sys
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from cispo_model.config import load_model_config
from cispo_model.data import load_model_data, STORAGE_TECHS
from cispo_model.planning_state import PlanningState, stable_asset_id


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    out = HERE / 'revision_6d'
    candidate = HERE / 'upstream_2050_prepared_6d/planning_state_candidate'
    old = HERE / 'upstream_2050_prepared_6c_v2/planning_state_candidate/capacity_cohorts.csv.gz'
    new = candidate / 'capacity_cohorts.csv.gz'
    before, after = records(old), records(new)
    assert len(before) == len(after)
    changed = []
    for a, b in zip(before, after):
        if a == b:
            continue
        assert {k for k in a if a[k] != b[k]} == {'capacity_delta'}
        assert a['asset_id'] == '31::bio' and a['technology'] == 'bio'
        assert a['action'] == 'new_build' and a['unit'] == 'GW'
        assert 0 <= float(b['capacity_delta']) < float(a['capacity_delta'])
        changed.append(dict(before=a, after=b))
    assert len(changed) == 2
    cfg = load_model_config(ROOT / 'config/optimization_numeric_dac_by_year_v9_a12.json').for_planning_year(2060)
    state = PlanningState.load(candidate, expected_boundary_year=2050,
        expected_scenario_id='base', allow_unaccepted_candidate=True)
    data = load_model_data(cfg, planning_state=state)
    provinces = data.province_codes.tolist()
    ids = [stable_asset_id(p, t) for p in provinces for t in STORAGE_TECHS]
    inherited = state.active_adjustment('storage', ids, planning_year=2060, unit='GW').reshape(len(provinces), len(STORAGE_TECHS))
    tiny = pd.read_csv(out / 'build_2060_a12/tiny_intervals.csv')
    tiny = tiny[tiny.gw_capacity]
    details = []
    for r in tiny.to_dict('records'):
        p, t = map(int, r['variable'].split('[')[1].rstrip(']').split(','))
        province, tech = provinces[p], STORAGE_TECHS[t]
        bounds = data.storage_bounds.set_index('province_code').loc[province]
        r.update(province_code=province, technology=tech,
            exogenous_floor_gw=float(bounds.capacity_floor_gw),
            inherited_gw=float(inherited[p, t]), input_upper_gw=float(bounds.capacity_upper_gw),
            interval_kw=r['width'] * 1e6)
        details.append(r)
    pd.DataFrame(details).to_csv(out / 'storage_tiny_capacity_stop.csv', index=False)
    affected = {stable_asset_id(r['province_code'], r['technology']) for r in details}
    c = state.cohorts
    c[c.asset_class.eq('storage') & c.asset_id.isin(affected)].to_csv(out / 'storage_tiny_capacity_cohorts.csv', index=False)
    original = records(HERE / 'upstream_2050_source_capsule/planning_state_candidate/capacity_cohorts.csv.gz')
    original_storage = [r for r in original if r['asset_class']=='storage' and r['asset_id'] in affected]
    prepared_storage = [r for r in after if r['asset_class']=='storage' and r['asset_id'] in affected]
    assert original_storage == prepared_storage
    report = dict(status='STOP_AUTHOR_REVIEW_REQUIRED',
        trigger='D2: unauthorized GW capacity intervals with 0 < UB-LB < 1e-5',
        capacity_intervals=details, affected_storage_cohorts_unchanged_from_original=True,
        shanghai_changed_rows=changed, all_other_6c_v2_fields_text_exact=True,
        retrofit_and_ccs_unchanged_from_6c_v2=True,
        original_sha256=sha(HERE / 'upstream_2050_source_capsule/planning_state_candidate/capacity_cohorts.csv.gz'),
        previous_6c_v2_sha256=sha(old), prepared_sha256=sha(new),
        no_optimization=True, no_submission=True,
        proposed_not_applied='Explicit opt-in PHS headroom closure: for 0 < upper-floor < 1e-5 GW set effective upper=floor and new-build upper=0; retain inherited state; audit paired bounds and extend D4 whitelist only with author approval')
    (out / 'storage_capacity_stop.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
