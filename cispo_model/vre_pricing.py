"""Solver-free VRE pair pricing from original MPS and raw ordered BarPi.

Adapted from claude_workspace/scripts/vre_reduced_cost_screen.py. The pair
direction d(vre_capacity)=d(vre_new)=1 cancels the capacity-accounting row.
Only VRE columns are accumulated; no per-column arrays for the entire LP.
The row-name index still scales with original constraint count (~8 GiB for
51M rows). Use a suitably provisioned local/compute machine, never login nodes.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

SITE_COLUMN = re.compile(r'^(vre_capacity_gw|vre_new_gw)\[(\d+)\]$')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_table(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    keys = [(r['grid_uid'], r['technology']) for r in rows]
    if not rows or len(keys) != len(set(keys)) or any(not all(k) for k in keys):
        raise ValueError('Empty, missing or duplicate grid_uid x technology identities')
    return rows


def finite(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('Nonfinite pricing input')
    return x


def parse_vre_mps(mps, barpi):
    """Read the original Gurobi continuous, minimization MPS. Fail on drift."""
    pi = np.load(barpi, mmap_mode='r', allow_pickle=False)
    if pi.ndim != 1:
        raise ValueError('BarPi must be one-dimensional in original ROWS order')
    for start in range(0, len(pi), 1000000):
        if not np.isfinite(pi[start:start+1000000]).all():
            raise ValueError('Nonfinite BarPi')
    rows = {}; columns = {}; objective = None; section = None
    ended = False; row_hash = hashlib.sha256(); column_count = 0; previous = None
    opener = gzip.open if str(mps).endswith('.gz') else open
    with opener(mps, 'rt', encoding='ascii', errors='strict') as stream:
        for line in stream:
            if not line.strip() or line.lstrip().startswith('*'):
                continue
            tokens = line.split()
            if line[0] not in ' \t':
                section = tokens[0]
                if section == 'COLUMNS' and len(rows) != len(pi):
                    raise ValueError('MPS constraint count differs from BarPi length')
                if section == 'OBJSENSE' and len(tokens) > 1 and tokens[1] != 'MIN':
                    raise ValueError('Only minimization is supported')
                if section not in {'NAME', 'OBJSENSE', 'ROWS', 'COLUMNS', 'RHS', 'BOUNDS', 'ENDATA'}:
                    raise ValueError('Unsupported MPS section: ' + section)
                if section == 'ENDATA':
                    ended = True
                    break
                continue
            if section == 'OBJSENSE':
                if tokens != ['MIN']:
                    raise ValueError('Only minimization is supported')
            elif section == 'ROWS':
                sense, name = tokens
                if sense == 'N':
                    if objective is not None:
                        raise ValueError('Multiple objective/free rows unsupported')
                    objective = name
                else:
                    if sense not in {'E', 'L', 'G'} or name in rows:
                        raise ValueError('Invalid or duplicate MPS row')
                    rows[name] = len(rows)
                    row_hash.update((name+'\n').encode('ascii'))
            elif section == 'COLUMNS':
                if "'MARKER'" in tokens:
                    raise ValueError('Integer MPS is not a continuous pricing LP')
                name = tokens[0]
                if name != previous:
                    column_count += 1
                    previous = name
                match = SITE_COLUMN.fullmatch(name)
                if not match:
                    continue
                if len(tokens) not in {3, 5}:
                    raise ValueError('Unexpected MPS column record')
                d = columns.setdefault(name, dict(obj=0., atpi=0., nnz=0, lb=0., ub=math.inf))
                for k in range(1, len(tokens), 2):
                    row, value = tokens[k], finite(tokens[k+1].replace('D', 'E'))
                    if row == objective:
                        d['obj'] += value
                    else:
                        if row not in rows:
                            raise ValueError('Unknown MPS row ' + row)
                        d['atpi'] += value * float(pi[rows[row]])
                        d['nnz'] += 1
            elif section == 'BOUNDS':
                kind, _, name = tokens[:3]
                if not SITE_COLUMN.fullmatch(name):
                    continue
                d = columns[name]
                value = finite(tokens[3]) if len(tokens) == 4 else None
                if kind == 'UP': d['ub'] = value
                elif kind == 'LO': d['lb'] = value
                elif kind == 'FX': d['lb'] = d['ub'] = value
                elif kind == 'FR': d['lb'], d['ub'] = -math.inf, math.inf
                elif kind == 'MI': d['lb'] = -math.inf
                elif kind == 'PL': d['ub'] = math.inf
                else: raise ValueError('Unsupported VRE bound ' + kind)
    if not ended or not objective or len(rows) != len(pi) or not columns:
        raise ValueError('Incomplete MPS/BarPi or missing VRE columns')
    for d in columns.values():
        d['rc'] = finite(d['obj'] - d['atpi'])
    return columns, dict(constraint_rows=len(rows), columns=column_count,
        constraint_name_order_sha256=row_hash.hexdigest(),
        method='c-A_transpose_BarPi; original MPS row order; raw solver-unit BarPi')


def site_prices(columns, capacity_rows, *, headroom_zero_gw=0.):
    """CSV is the archived model-index export, NOT a positional screen join."""
    result = []
    if len(columns) != 2 * len(capacity_rows):
        raise ValueError('VRE column count and archived capacity export disagree')
    for i, row in enumerate(capacity_rows):
        cap, new = columns[f'vre_capacity_gw[{i}]'], columns[f'vre_new_gw[{i}]']
        c = finite(cap['obj'] + new['obj']); rc = finite(cap['rc'] + new['rc'])
        if c <= 0:
            raise ValueError('Nonpositive annualized VRE pair cost')
        # Validate that this CSV belongs to the same original model ordering.
        floor = finite(row['capacity_floor_gw'])
        upper = finite(row['capacity_upper_gw'])
        expected_upper = floor if abs(upper-floor) <= finite(headroom_zero_gw) else upper
        if not math.isclose(cap['lb'], floor, abs_tol=1e-9, rel_tol=1e-10):
            raise ValueError('VRE capacity CSV floor differs from archived column')
        if not math.isclose(cap['ub'], expected_upper, abs_tol=1e-9, rel_tol=1e-10):
            raise ValueError('VRE capacity CSV upper bound differs from archived column')
        result.append(dict(site_index=i, grid_uid=row['grid_uid'], technology=row['technology'],
            province_code=row.get('province_code',''), obj_total=c,
            rc_cap=cap['rc'], rc_new=new['rc'], rc_build=rc, rc_ratio=rc/c,
            capacity_floor_gw=floor, capacity_upper_gw=upper,
            archived_capacity_upper_gw=cap['ub'],
            new_capacity_gw=finite(row['new_capacity_gw']),
            archived_new_lb_gw=new['lb'], archived_new_ub_gw=new['ub']))
    return result


def certificate(prices, selection, objective, *, re_solve_count=0):
    objective = finite(objective)
    if objective <= 0 or re_solve_count not in {0, 1}:
        raise ValueError('Positive objective and re_solve_count 0 or 1 required')
    lookup = {(r['grid_uid'], r['technology']): r for r in prices}
    if len(lookup) != len(prices) or set(lookup) != {(r['grid_uid'], r['technology']) for r in selection}:
        raise ValueError('Selection must match archived site identities one-to-one')
    if len(selection) != len(prices):
        raise ValueError('Duplicate candidate selection')
    terms = []; negative = []; flips = []
    for row in selection:
        p = lookup[(row['grid_uid'], row['technology'])]
        if str(row['screened_out']).lower() not in {'true', 'false'}:
            raise ValueError('screened_out must be an explicit boolean')
        excluded = str(row['screened_out']).lower() == 'true'
        head = finite(row['original_new_ub_gw'])
        base_ratio = finite(row['rc_ratio'])
        if head < 0 or p['archived_new_lb_gw'] != 0:
            raise ValueError('Invalid new-build interval')
        expected = 0. if excluded else head
        if not math.isclose(p['archived_new_ub_gw'], expected, abs_tol=1e-10, rel_tol=1e-10):
            raise ValueError('Screen bound in original MPS differs from candidate_selection')
        term = head * max(-p['rc_build'], 0.) if excluded else 0.
        terms.append(term)
        if excluded and p['rc_build'] < 0:
            item = dict(p, original_new_ub_gw=head, improvement_bound_million_cny=term,
                        base_rc_ratio=base_ratio)
            negative.append(item)
            if base_ratio > 0: flips.append(item)
    bound = math.fsum(terms); ratio = bound / objective
    near = ('ACCEPT_SECOND_SOLVE_DISCLOSE' if re_solve_count else
            'ACCEPT' if ratio <= 1e-3 else
            'ACCEPT_DISCLOSE' if ratio <= 1e-2 else 'RESOLVE_NEGATIVE_COLUMNS_ONCE')
    comparison = ('SECOND_SOLVE_INTERVAL_DISCLOSE' if re_solve_count else
                  'RESOLVE_NEGATIVE_COLUMNS_ONCE' if ratio > 1e-4 else 'INTERVAL_WITH_B')
    return dict(B_million_cny=bound, B_over_objective=ratio, objective_million_cny=objective,
        near_optimality_decision=near, base_comparison_decision=comparison,
        re_solve_count=re_solve_count, negative_excluded_columns=negative,
        excluded_columns=sum(str(r['screened_out']).lower()=='true' for r in selection),
        dual_grade='BARRIER_DUAL_ENGINEERING_GRADE',
        formula='sum(original_new_ub_gw * max(-(rc_cap+rc_new),0)) over screened_out sites',
        interpretation='Pair direction eliminates capacity-accounting equality; engineering pricing bound, not a replacement for full primal/dual feasibility or objective-gap disclosure',
        all_runs_must_be_preserved=True), flips


def write_csv(path, rows, fields):
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields);w.writeheader();w.writerows(rows)


def verify_semantic_files(root, names):
    """Bind semantic exports to their original manifest or verified download."""
    root=Path(root)
    if (root/'result_manifest.json').exists():
        manifest=root/'result_manifest.json'
        payload=json.loads(manifest.read_text(encoding='utf-8'))
        expected={v['path']:v['sha256'] for v in payload['files']}
    else:
        manifest=root/'download_identity.json'
        payload=json.loads(manifest.read_text(encoding='utf-8'))
        expected={k:v['sha256'] for k,v in payload['files'].items() if v['verified']}
    for name in names:
        if sha256(root/name)!=expected[name]:
            raise ValueError('Semantic export SHA mismatch: '+name)
    return dict(manifest=str(manifest),sha256=sha256(manifest))


def archive_paths(root):
    """Verify the source archive/checkpoint manifests before offline pricing."""
    root=Path(root)
    archive=root/'model_archive/archive_manifest.json'
    checkpoint=root/'barrier_checkpoint/barrier_checkpoint_manifest.json'
    a=json.loads(archive.read_text(encoding='utf-8'))
    c=json.loads(checkpoint.read_text(encoding='utf-8'))
    entries=[v for v in a['files'] if v['path'] in {'original.mps','original.mps.gz'}]
    if len(entries)!=1: raise ValueError('Expected exactly one archived original MPS')
    mps=archive.parent/entries[0]['path'];pi=checkpoint.parent/'dual_barpi.npy'
    if sha256(mps)!=entries[0]['sha256']: raise ValueError('Original MPS SHA mismatch')
    # Checkpoint structures changed over time; locate the exact named vector entry.
    def walk(x):
        if isinstance(x,dict):
            if x.get('path')=='dual_barpi.npy' and 'sha256' in x: yield x
            for value in x.values(): yield from walk(value)
        elif isinstance(x,list):
            for value in x: yield from walk(value)
    vectors=list(walk(c))
    if len(vectors)!=1 or sha256(pi)!=vectors[0]['sha256']:
        raise ValueError('Raw original-order BarPi SHA missing or mismatched')
    fingerprints=[]
    def fp(x):
        if isinstance(x,dict):
            if 'gurobi_fingerprint' in x: fingerprints.append(x['gurobi_fingerprint'])
            for v in x.values(): fp(v)
        elif isinstance(x,list):
            for v in x: fp(v)
    fp(c)
    if a['gurobi_fingerprint'] not in fingerprints:
        raise ValueError('Archive/checkpoint fingerprints differ')
    return mps,pi,dict(archive_manifest_sha256=sha256(archive),
        checkpoint_manifest_sha256=sha256(checkpoint),mps_sha256=entries[0]['sha256'],
        barpi_sha256=vectors[0]['sha256'],gurobi_fingerprint=a['gurobi_fingerprint'],
        source=c.get('source',{}))
