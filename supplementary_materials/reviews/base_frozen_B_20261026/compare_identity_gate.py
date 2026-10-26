"""Read-only comparison of the preserved, same-window fixed-capacity solves.

Run in the T550 validation copy; writes a separate comparison JSON. It never
changes a solve or relaxes a gate. Detailed operation differences are reported
in their native variable units, separately by family.
"""
import argparse
import json
from pathlib import Path


def compare(root):
    folders = [root / 'base_control_24h', root / 'zero_24h']
    probes = [json.loads((p / 'identity_gate_probe.json').read_text()) for p in folders]
    solutions = []
    for p in folders:
        with (p / 'gate_values.jsonl').open() as f:
            solutions.append(dict(json.loads(line) for line in f))
    base, zero = solutions
    shared = base.keys() & zero.keys()
    families = {}
    for name in sorted(shared):
        family = name.split('[')[0]
        item = families.setdefault(family, dict(entries=0, max_abs_difference=0.,
                                               worst_variable=None, above_1e_9=0,
                                               above_1e_6=0, above_1e_3=0))
        delta = abs(base[name] - zero[name])
        item['entries'] += 1
        for key, tolerance in [('above_1e_9', 1e-9), ('above_1e_6', 1e-6), ('above_1e_3', 1e-3)]:
            item[key] += delta > tolerance
        if delta > item['max_abs_difference']:
            item.update(max_abs_difference=delta, worst_variable=name,
                        base_value=base[name], zero_value=zero[name])
    objective = [p['objective'] for p in probes]
    relative = abs(objective[0] - objective[1]) / max(abs(objective[0]), 1.)
    return dict(base_objective=objective[0], zero_contract_objective=objective[1],
                objective_relative_difference=relative, objective_tolerance=1e-7,
                objective_pass=relative <= 1e-7,
                both_optimal=all(p['status'] == 2 for p in probes),
                shared_variables=len(shared), base_only_variables=len(base.keys()-zero.keys()),
                zero_only_variables=len(zero.keys()-base.keys()), families=families,
                operation_gate='REQUIRES_REVIEW_OF_NATIVE_UNIT_DIFFERENCES',
                note='No unapproved aggregate or degeneracy exception is applied.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    result = compare(args.root)
    with (args.root / 'identity_gate_comparison.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='families'}, indent=2))
    print(json.dumps(sorted(result['families'].items(), key=lambda kv:kv[1]['max_abs_difference'], reverse=True)[:12], indent=2))
