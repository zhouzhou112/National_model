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
SPUR_COLUMN = re.compile(r'^spur_augmentation_gw\[(\d+)\]$')


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


def parse_vre_mps(mps, barpi, *, include_spur=False):
    """Read the original Gurobi continuous, minimization MPS. Fail on drift."""
    pi = np.load(barpi, mmap_mode='r', allow_pickle=False)
    if pi.ndim != 1:
        raise ValueError('BarPi must be one-dimensional in original ROWS order')
    for start in range(0, len(pi), 1000000):
        if not np.isfinite(pi[start:start+1000000]).all():
            raise ValueError('Nonfinite BarPi')
    rows = {}; columns = {}; objective = None; section = None
    spur_rows = {}; rhs_set = None
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
                    if include_spur and name.startswith('spur_capacity_non_dpv['):
                        spur_rows[name] = dict(sense=sense, pi=float(pi[rows[name]]), rhs=0.)
            elif section == 'COLUMNS':
                if "'MARKER'" in tokens:
                    raise ValueError('Integer MPS is not a continuous pricing LP')
                name = tokens[0]
                if name != previous:
                    column_count += 1
                    previous = name
                match = SITE_COLUMN.fullmatch(name)
                if not match and not (include_spur and SPUR_COLUMN.fullmatch(name)):
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
                        if include_spur and row in spur_rows:
                            d.setdefault('spur_links', []).append(dict(row=row, coefficient=value))
            elif section == 'RHS' and include_spur:
                if rhs_set is not None and rhs_set != tokens[0]:
                    raise ValueError('Directional pricing requires one RHS vector')
                rhs_set=tokens[0]
                for k in range(1,len(tokens),2):
                    if tokens[k] in spur_rows:
                        spur_rows[tokens[k]]['rhs'] += finite(tokens[k+1].replace('D','E'))
            elif section == 'BOUNDS':
                kind, _, name = tokens[:3]
                if not SITE_COLUMN.fullmatch(name) and not (include_spur and SPUR_COLUMN.fullmatch(name)):
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
        if include_spur:
            for link in d.get('spur_links',[]):
                link.update(spur_rows[link['row']])
    return columns, dict(constraint_rows=len(rows), columns=column_count,
        constraint_name_order_sha256=row_hash.hexdigest(),
        method='c-A_transpose_BarPi; original MPS row order; raw solver-unit BarPi')


def directional_site_prices(columns, capacity_rows, selection, *, require_fixed=False):
    """Both directions, retaining the original minimal spur-capacity relation.

    Fixing a site also fixes its spur. It is therefore insufficient to price
    cap+new alone. Remove the spur row's multiplier and retain that inequality
    in the one-dimensional minimization: s(x)=max(0,max_cf*x-inherited_spur).
    Its objective coefficient is nonnegative and it must have no other rows.
    This is an analytical pricing calculation, not a change to the primal LP.
    Reference pricing at a proposed boundary is SCORE_ONLY; a certificate
    requires verified fixed bounds in the archived model itself.
    """
    states={(str(r['grid_uid']),str(r['technology'])):r['state'] for r in selection}
    keys=[(r['grid_uid'],r['technology']) for r in capacity_rows]
    if len(states)!=len(selection) or len(keys)!=len(set(keys)) or set(states)!=set(keys):
        raise ValueError('Directional selection/site identity mismatch')
    if len(columns)!=3*len(keys):
        raise ValueError('Directional pricing requires every cap/new/spur column')
    cap_owners={}
    for name,d in columns.items():
        if name.startswith('vre_capacity_gw['):
            for link in d.get('spur_links',[]):
                if link['coefficient']!=0:cap_owners.setdefault(link['row'],set()).add(name)
    result=[]
    for i,(row,key) in enumerate(zip(capacity_rows,keys)):
        state=states[key]
        if state not in {'lower','upper','free'}:raise ValueError('Unknown boundary state')
        cap=columns[f'vre_capacity_gw[{i}]'];new=columns[f'vre_new_gw[{i}]'];spur=columns[f'spur_augmentation_gw[{i}]']
        lo=finite(row['capacity_floor_gw']);up=finite(row['capacity_upper_gw'])
        if lo>up:raise ValueError('Invalid physical capacity span')
        cost=finite(cap['obj']+new['obj']);rc=finite(cap['rc']+new['rc']);scost=finite(spur['obj'])
        if cost<=0 or scost<0:raise ValueError('Directional pairing requires positive VRE/nonnegative spur cost')
        if key[1]=='dpv':
            if spur['ub']!=0 or spur['nnz']!=0:raise ValueError('DPV spur definition drift')
            m=stock=pi=0.
        else:
            cl=cap.get('spur_links',[]);sl=spur.get('spur_links',[])
            if len(sl)!=1 or spur['nnz']!=1 or sl[0]['sense']!='G' or sl[0]['coefficient']!=1:
                raise ValueError(f'Unreviewed spur row for site {i} {key}')
            owners=cap_owners.get(sl[0]['row'],set())
            if len(cl)==1 and cl[0]['row']==sl[0]['row'] and cl[0]['coefficient']<=0 and owners<={f'vre_capacity_gw[{i}]'}:
                m=-finite(cl[0]['coefficient'])
            elif not cl and not owners:
                # A zero design CF leaves s >= -inherited_spur in the original
                # MPS. No capacity column may own this row, including other sites.
                m=0.
            else:
                raise ValueError(f'Unreviewed coupled spur columns for site {i} {key}')
            stock=-finite(sl[0]['rhs']);pi=finite(sl[0]['pi'])
        # c-A'pi without relaxing this site's spur inequality.
        retained_rc=rc-m*pi
        item=dict(site_index=i,grid_uid=key[0],technology=key[1],province_code=row.get('province_code',''),
                  state=state,capacity_floor_gw=lo,capacity_upper_gw=up,obj_total=cost,
                  rc_pair=rc,spur_objective=scost,spur_row_pi=pi,max_cf=m,inherited_spur_gw=stock,
                  retained_row_pair_rc=retained_rc,fixed_archived_bounds_verified=False)
        if state=='free':
            item.update(improvement_bound_million_cny=0.,increase_rc_ratio=None,decrease_rc_ratio=None)
            result.append(item);continue
        x0=lo if state=='lower' else up
        s0=0. if key[1]=='dpv' else max(0.,m*x0-stock)
        if require_fixed:
            for d,x in [(cap,x0),(new,x0-lo),(spur,s0)]:
                if not (math.isclose(d['lb'],x,rel_tol=1e-12,abs_tol=1e-10) and math.isclose(d['ub'],x,rel_tol=1e-12,abs_tol=1e-10)):
                    raise ValueError('Archived selected cap/new/spur bounds differ from state')
            item['fixed_archived_bounds_verified']=True
        candidates=[lo,up,x0]
        if m>0 and lo<stock/m<up:candidates.append(stock/m)
        def delta(x):
            s=0. if key[1]=='dpv' else max(0.,m*x-stock)
            return retained_rc*(x-x0)+scost*(s-s0)
        best=min(candidates,key=delta);bound=max(0.,-delta(best))
        up_rc=retained_rc+(scost*m if m*x0>=stock else 0.)
        down_rc=-(retained_rc+(scost*m if m*x0>stock else 0.))
        item.update(anchor_capacity_gw=x0,anchor_spur_gw=s0,increase_rc=up_rc,decrease_rc=down_rc,
                    increase_rc_ratio=up_rc/cost,decrease_rc_ratio=down_rc/cost,
                    best_relaxed_capacity_gw=best,improvement_bound_million_cny=bound,
                    calculation_scope='FIXED_ARCHIVE_CERTIFICATE_TERM' if require_fixed else 'REFERENCE_BOUNDARY_SCORE_ONLY')
        result.append(item)
    return result


def directional_certificate(prices, objective):
    """No automatic release/re-solve; author inspects bound and adverse directions."""
    objective=finite(objective)
    if objective<=0:raise ValueError('Positive objective required')
    fixed=[r for r in prices if r['state']!='free']
    if any(r.get('fixed_archived_bounds_verified') is not True for r in fixed):
        raise ValueError('Reference scores cannot be promoted to a solution certificate')
    terms=[finite(r['improvement_bound_million_cny']) for r in fixed]
    if any(x<0 for x in terms):raise ValueError('Negative improvement term')
    bound=math.fsum(terms)
    negative=[r for r in fixed if r['improvement_bound_million_cny']>0]
    return dict(B_million_cny=bound,B_over_objective=bound/objective,objective_million_cny=objective,
                fixed_sites=len(fixed),negative_fixed_sites=len(negative),negative_columns=negative,
                dual_grade='BARRIER_DUAL_ENGINEERING_GRADE',automatic_resolve=False,
                formula='sum(max(0,-min_delta_L)) over fixed sites; candidates are original endpoints and spur-reuse kink',
                scope='VRE cap/new plus corresponding fixed spur; original spur inequalities retained analytically',
                near_optimality_decision='ACCEPT' if bound/objective<=1e-3 else 'ACCEPT_DISCLOSE' if bound/objective<=1e-2 else 'REPORT_AUTHOR_BEFORE_ANY_RESOLVE',
                all_runs_must_be_preserved=True)


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
