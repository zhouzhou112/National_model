"""Author 2026-10-27: opt-in Base plus minimal static closure, in GW.

Only diagnosed spur/trunk additions and non-CCS bio new-build reductions are
permitted. Source tables, original clipping audit and constraint RHS stay intact.
"""
import hashlib
import json
import math
from pathlib import Path
import re

import pandas as pd

SCHEMA = 'base_frozen_static_closure_20261027_v1'


def fixed_accounting_values(model, overrides=None):
    """Evaluate capacity equalities from fixed investment bounds, without solve."""
    model.update()
    values = {v.VarName: v.LB for v in model.getVars() if v.LB == v.UB}
    values.update(overrides or {})
    for row in model.getConstrs():
        if row.Sense != '=' or 'capacity_accounting' not in row.ConstrName:
            continue
        expression = model.getRow(row)
        terms = [(expression.getVar(i).VarName, expression.getCoeff(i)) for i in range(expression.size())]
        free = [(n, c) for n, c in terms if n not in values]
        if len(free) == 1:
            name, coefficient = free[0]
            values[name] = (row.RHS - math.fsum(c*values[n] for n, c in terms if n in values))/coefficient
    return values


def row_evidence(model, row, values):
    expression = model.getRow(row)
    terms = [(expression.getVar(i).VarName, expression.getCoeff(i)) for i in range(expression.size())]
    identity = dict(name=row.ConstrName, sense=row.Sense, rhs=row.RHS, terms=sorted(terms))
    sha = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    lhs = math.fsum(c*values[n] for n, c in terms)
    gap = lhs-row.RHS if row.Sense == '<' else row.RHS-lhs
    return dict(row_sha256=sha, lhs=lhs, rhs=row.RHS, gap_gw=gap), dict(terms)


def permitted_target(row_name, audit):
    match = re.fullmatch(r'spur_capacity_non_dpv\[(\d+)\]', row_name)
    if match:
        return 'spur_augmentation_gw['+match[1]+']', 1
    match = re.fullmatch(r'trunk_capacity_(\d+)', row_name)
    if match:
        return 'trunk_augmentation_gw['+match[1]+']', 1
    match = re.fullmatch(r'biomass_beccs_shared_capacity_upper_s4_34\[(\d+)\]', row_name)
    if match:
        selected = audit[(audit.family == 'thermal_new') &
            audit.variable.str.startswith('thermal_new_gw['+match[1]+',')]
        selected = selected[selected.stable_key.map(lambda x: json.loads(x)[1] == 'bio')]
        if len(selected) == 1:
            return selected.iloc[0].variable, -1
    raise ValueError('Closure row outside author whitelist: '+row_name)


def build_payload(model, audit, conflicts, source_manifest, year):
    before = fixed_accounting_values(model)
    rows, overrides = [], {}
    by_name = {v.VarName: v for v in model.getVars()}
    for conflict in conflicts:
        name = conflict['row']
        target, direction = permitted_target(name, audit)
        if target in overrides:
            raise ValueError('Duplicate closure target')
        constraint = model.getConstrByName(name)
        evidence, terms = row_evidence(model, constraint, before)
        if evidence['gap_gw'] <= 0 or not math.isfinite(evidence['gap_gw']):
            raise ValueError('Diagnosed row is not a positive finite gap')
        if direction == 1:
            if constraint.Sense != '>' or terms.get(target) != 1:
                raise ValueError('Network closure coefficient/sense changed')
        else:
            capacity = target.replace('thermal_new_gw', 'thermal_capacity_gw')
            if constraint.Sense != '<' or terms.get(capacity) != 1:
                raise ValueError('Bio closure coefficient/sense changed')
        variable = by_name[target]
        if variable.LB != variable.UB:
            raise ValueError('Closure source must be fixed')
        original = audit.set_index('variable').loc[target]
        delta = direction*evidence['gap_gw']
        after = variable.LB+delta
        if after < original.original_lb or after > original.original_ub:
            raise ValueError('Static closure exceeds original investment bounds')
        overrides[target] = after
        rows.append(dict(row=name, variable=target, family=original.family,
            stable_key=original.stable_key, base_value=float(original.base_value),
            before_gw=variable.LB, after_gw=after, delta_gw=delta,
            objective_coefficient=variable.Obj, **evidence))
    after_values = fixed_accounting_values(model, overrides)
    cost_terms = {name: (value-before[name])*by_name[name].Obj
                  for name, value in after_values.items() if name in before and value != before[name]}
    for item in rows:
        item['direct_annual_cost_delta_million_cny'] = item['delta_gw']*item['objective_coefficient']
        if item['family'] == 'thermal_new':
            name = item['variable'].replace('thermal_new_gw', 'thermal_capacity_gw')
            item['derived_annual_cost_delta_million_cny'] = cost_terms.get(name, 0.)
        else:
            item['derived_annual_cost_delta_million_cny'] = 0.
    return dict(schema_version=SCHEMA, planning_year=year,
        source_result_manifest_sha256=source_manifest, mode='STATIC_EXACT', rows=rows,
        annual_cost_delta_million_cny=math.fsum(cost_terms.values()),
        annual_cost_terms_million_cny=cost_terms,
        definition='Base clipped values plus author-approved minimal static closure')


def apply_static_closure(artifacts, output, path, source_manifest, year):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema_version') != SCHEMA or payload.get('mode') != 'STATIC_EXACT':
        raise ValueError('Unsupported frozen closure policy')
    if payload['source_result_manifest_sha256'] != source_manifest or payload['planning_year'] != year:
        raise ValueError('Frozen closure source/year mismatch')
    root = Path(output)
    audit_path = root/'frozen_capacity_audit.csv'
    audit_bytes = audit_path.read_bytes()
    audit = pd.read_csv(audit_path)
    expected = build_payload(artifacts.model, audit, payload['rows'], source_manifest, year)
    if len(expected['rows']) != len(payload['rows']):
        raise ValueError('Frozen closure row mismatch')
    for requested, actual in zip(payload['rows'], expected['rows']):
        for key in ['row', 'variable', 'family', 'stable_key', 'row_sha256']:
            if requested[key] != actual[key]:
                raise ValueError('Frozen closure row identity mismatch: '+key)
        for key in ['before_gw', 'after_gw', 'delta_gw', 'gap_gw', 'objective_coefficient']:
            if not math.isfinite(requested[key]) or not math.isclose(requested[key], actual[key], rel_tol=0, abs_tol=1e-12):
                raise ValueError('Frozen closure numeric mismatch: '+key)
    model = artifacts.model
    for item in expected['rows']:
        variable = model.getVarByName(item['variable'])
        variable.LB = variable.UB = item['after_gw']
    model.update()
    values = fixed_accounting_values(model)
    for item in expected['rows']:
        after, _ = row_evidence(model, model.getConstrByName(item['row']), values)
        item['post_closure_gap_gw'] = after['gap_gw']
        if after['gap_gw'] > 1e-12:
            raise ValueError('Static closure did not close its row')
    assert audit_path.read_bytes() == audit_bytes
    expected.update(status='PASS', payload_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        original_frozen_audit_sha256=hashlib.sha256(audit_bytes).hexdigest(),
        original_audit_unchanged=True, constraint_rhs_unchanged=True)
    pd.DataFrame(expected['rows']).to_csv(root/'frozen_capacity_closure_audit.csv', index=False)
    (root/'frozen_capacity_closure_report.json').write_text(json.dumps(expected, indent=2)+'\n', encoding='utf-8')
    artifacts.index['frozen_capacity_closure'] = expected
    return expected
