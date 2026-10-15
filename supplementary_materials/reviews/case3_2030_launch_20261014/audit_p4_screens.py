"""Audit completed P4 tables without building or solving any planning model.

Usage: --screen DIR --archive DIR --year 2040|2050 --output NEW_DIR.
Verifies identities, arithmetic and real apply_vre_screen stable-key behavior
using an in-memory bounds stub, including deliberately reversed site order.
Counts apply to the source Base headroom, not an unbuilt future case3 state.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from cispo_model.factor_screen import apply_vre_screen
from cispo_model.vre_pricing import sha256
from fetch_pricing_archive import RELEASES


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--screen', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--year', type=int, choices=(2040, 2050), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    identity = json.loads((a.screen/'screen_identity.json').read_text())
    download = json.loads((a.archive/'download_identity.json').read_text())
    table = pd.read_csv(a.screen/'source_screen.csv')
    config = json.loads((a.archive/'model_config_snapshot.json').read_text())['resolved_configuration']
    source = identity['identity']['source']
    contract = identity['candidate_screen']
    assert source['planning_year'] == a.year == config['planning_year']
    assert source['scenario_id'] == 'base' and source['optimization_hours'] == 8760
    assert identity['scope'] == 'FULL_YEAR'
    assert contract['source_release'] == download['source_release'] == RELEASES[a.year]
    assert contract['margin'] == .2
    assert contract['source_csv_sha256'] == sha256(a.screen/'source_screen.csv')
    assert contract['source_dual_sha256'] == download['files']['barrier_checkpoint/dual_barpi.npy']['sha256']
    assert identity['identity']['mps_sha256'] == download['files']['model_archive/original.mps.gz']['sha256']
    for name in ('vre_capacity.csv', 'model_config_snapshot.json'):
        assert sha256(a.archive/name) == download['files'][name]['sha256']
    keys = ['grid_uid', 'technology']
    assert not table.duplicated(keys).any() and not table[keys].isna().any().any()
    original = pd.read_csv(a.archive/'vre_capacity.csv')
    assert set(map(tuple, table[keys].to_numpy())) == set(map(tuple, original[keys].to_numpy()))
    assert len(table) == identity['sites']
    values = table[['rc_build','rc_cap','rc_new','rc_ratio','obj_total','headroom_gw',
                    'archived_new_lb_gw','archived_new_ub_gw']].to_numpy()
    assert np.isfinite(values).all()
    assert (table.obj_total > 0).all() and (table.archived_new_lb_gw == 0).all()
    assert np.allclose(table.rc_cap + table.rc_new, table.rc_build, rtol=1e-12, atol=1e-8)
    assert np.allclose(table.rc_build / table.obj_total, table.rc_ratio, rtol=1e-12, atol=1e-12)
    expected = (table.rc_ratio >= .2) & (table.headroom_gw > 0)
    assert np.array_equal(table.screened_out_at_margin, expected)
    assert int(expected.sum()) == identity['excluded_sites']
    # Publish only the three columns consumed by the production entry point.
    # Preserve their original strings; use LF so Git does not change SHA bytes.
    compact = a.output/'source_screen.csv'
    with (a.screen/'source_screen.csv').open(encoding='utf-8',newline='') as source_file, compact.open('w',encoding='utf-8',newline='') as target_file:
        fields = keys + ['rc_ratio']
        writer = csv.DictWriter(target_file,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for row in csv.DictReader(source_file):
            writer.writerow({key:row[key] for key in fields})
    compact_table = pd.read_csv(compact)
    assert table[fields].equals(compact_table[fields])
    compact_contract = dict(contract,source_csv_sha256=sha256(compact))
    (a.output/'candidate_screen_fragment.json').write_text(json.dumps(dict(candidate_screen=compact_contract),indent=2)+'\n',encoding='utf-8')
    tests = []
    for reversed_order in (False, True):
        current = table.iloc[::-1] if reversed_order else table
        ub = current.archived_new_ub_gw.to_numpy().copy()
        new = SimpleNamespace(UB=ub.copy())
        artifacts = SimpleNamespace(model=SimpleNamespace(update=lambda: None), variables={'vre_new':new})
        folder = a.output/('reversed' if reversed_order else 'original')
        folder.mkdir()
        result = apply_vre_screen(artifacts,current[keys],compact,folder,margin=.2)
        expected_bounds = np.where((current.rc_ratio.to_numpy() >= .2) & (ub > 0),0.,ub)
        assert np.array_equal(new.UB,expected_bounds)
        assert np.array_equal(ub,current.archived_new_ub_gw.to_numpy())
        tests.append(dict(reversed_site_order=reversed_order,passed=True,counts=result))
    by_technology = []
    for technology, group in table.groupby('technology'):
        expandable = group.headroom_gw > 0
        excluded = (group.rc_ratio >= .2) & expandable
        by_technology.append(dict(technology=technology,sites=len(group),
            expandable=int(expandable.sum()),excluded=int(excluded.sum()),
            retained_expandable=int((expandable & ~excluded).sum())))
    result = dict(status='PASS',year=a.year,checked_utc=datetime.now(timezone.utc).isoformat(),
                  source_release=RELEASES[a.year],scope='BASE_SOURCE_HEADROOM_ONLY_NOT_FUTURE_MODEL_GATE',
                  source_csv_sha256=sha256(a.screen/'source_screen.csv'),
                  published_csv_sha256=sha256(compact),
                  published_csv_columns=fields,
                  screen_identity_sha256=sha256(a.screen/'screen_identity.json'),
                  download_identity_sha256=sha256(a.archive/'download_identity.json'),
                  sites=len(table),expandable=int((table.headroom_gw>0).sum()),
                  excluded=int(expected.sum()),retained_expandable=int(((table.headroom_gw>0)&~expected).sum()),
                  no_headroom=int((table.headroom_gw<=0).sum()),by_technology=by_technology,
                  apply_screen_stub_tests=tests,no_optimization_performed=True)
    (a.output/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','year','sites','expandable','excluded','retained_expandable')}))


if __name__ == '__main__':
    main()
