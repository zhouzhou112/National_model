"""Compare required input identities before releasing the held formal job."""
import argparse
import csv
import json
from pathlib import Path


def records(path):
    result = {}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            logical = row['logical_path'].replace('\\', '/')
            if row['kind'] in {'configuration', 'solver_configuration', 'formulation_configuration'}:
                logical = logical.rsplit('/', 1)[-1]
            key = row['kind'] + ':' + logical
            if key in result:
                raise ValueError('Duplicate input identity: ' + key)
            result[key] = row
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--actual', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    expected, actual = records(a.reference), records(a.actual)
    failures, optional = [], []
    for key in sorted(set(expected) | set(actual)):
        left, right = expected.get(key), actual.get(key)
        required = any(row and row['required'] == 'True' for row in (left, right))
        if (left is None or right is None or left['sha256'] != right['sha256']
                or left['integrity_method'] != right['integrity_method']
                or (required and right['exists'] != 'True')):
            (failures if required else optional).append(key)
    report = dict(status='FAIL' if failures else 'PASS', required_failures=failures,
                  optional_sidecar_differences=optional, total_reference_records=len(expected),
                  required_records=sum(r['required']=='True' for r in expected.values()),
                  scope='File SHA256 and recorded Zarr metadata identities; not a new full chunk-data hash')
    a.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
