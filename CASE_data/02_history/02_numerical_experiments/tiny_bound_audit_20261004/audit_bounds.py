#!/usr/bin/env python3
"""Read-only bound audit of a Gurobi free-format continuous-LP MPS archive.

Run on a compute node: python audit_bounds.py --inputs inputs.json --year 2050
Requires only Python's standard library and numpy; never imports a solver.
Checks compressed bytes/SHA256 BEFORE parsing. Scratch and results stay in --out.
Names are spooled to disk; numeric arrays and a checked 64-bit hash index avoid
storing a Python dictionary for 41 million column names. Unsupported sections,
integrality, ambiguous names/hash collisions and reversed bounds fail closed.
"""
import argparse
from array import array
from collections import Counter
import csv
import datetime
import gzip
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def name_hash(name):
    return int.from_bytes(hashlib.blake2b(name.encode('ascii'), digest_size=8).digest(), 'little')


def csv_write(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def parse_mps(path, out, year, expected=None, progress_every=20_000_000):
    with open(out / ('column_names_' + str(year) + '.scratch'), 'w+b', buffering=1 << 20) as spool:
        return _parse_mps(path, out, year, spool, expected, progress_every)


def _parse_mps(path, out, year, spool, expected=None, progress_every=20_000_000):
    started = time.monotonic()
    hashes, offsets, counts, families = array('Q'), array('Q'), array('I'), array('H')
    fam_index, stats = {}, []
    section = None
    objective = None
    nrows = 0
    cur_name, cur_nnz, cur_min, cur_max, cur_family = None, 0, math.inf, 0.0, None
    objective_nnz = 0
    section_names = []
    bound_types = Counter()
    bound_set = None
    bound_name = None
    bound_idx = None
    names_path = out / ('column_names_' + str(year) + '.scratch')
    spool_position = 0
    arrays_ready = False

    def flush_column():
        nonlocal spool_position
        if cur_name is None:
            return
        fid = fam_index.get(cur_family)
        if fid is None:
            fid = len(stats)
            if fid >= 65535:
                raise ValueError('Too many variable families')
            fam_index[cur_family] = fid
            stats.append(dict(family=cur_family, columns=0, matrix_nnz=0,
                              matrix_abs_min=math.inf, matrix_abs_max=0.0, max_column_nnz=0))
        encoded = cur_name.encode('ascii') + b'\n'
        hashes.append(name_hash(cur_name)); offsets.append(spool_position)
        counts.append(cur_nnz); families.append(fid)
        spool.write(encoded); spool_position += len(encoded)
        s = stats[fid]
        s['columns'] += 1; s['matrix_nnz'] += cur_nnz
        s['matrix_abs_min'] = min(s['matrix_abs_min'], cur_min)
        s['matrix_abs_max'] = max(s['matrix_abs_max'], cur_max)
        s['max_column_nnz'] = max(s['max_column_nnz'], cur_nnz)

    def initialize_arrays():
        nonlocal hvalues, order, sorted_hashes, lb, ub, nnz, fids, off, arrays_ready
        if arrays_ready:
            return
        spool.flush()
        hvalues = np.frombuffer(hashes, dtype=np.uint64)
        order = np.argsort(hvalues)
        sorted_hashes = hvalues[order]
        if np.any(sorted_hashes[1:] == sorted_hashes[:-1]):
            raise ValueError('Duplicate/non-contiguous column name or hash collision; no result accepted')
        nnz = np.frombuffer(counts, dtype=np.uint32)
        fids = np.frombuffer(families, dtype=np.uint16)
        off = np.frombuffer(offsets, dtype=np.uint64)
        lb = np.zeros(len(hvalues), dtype=np.float64)
        ub = np.full(len(hvalues), np.inf, dtype=np.float64)
        arrays_ready = True
        print('INDEX_READY columns={} elapsed={:.1f}s'.format(len(lb), time.monotonic()-started), flush=True)

    hvalues = order = sorted_hashes = lb = ub = nnz = fids = off = None
    opener = gzip.open if str(path).endswith('.gz') else open
    with io.TextIOWrapper(io.BufferedReader(opener(path, 'rb'), 1 << 20), encoding='ascii', errors='strict') as f:
        for line_number, line in enumerate(f, 1):
            if line_number % progress_every == 0:
                print('PROGRESS lines={} section={} columns={} elapsed={:.1f}s'.format(
                    line_number, section, len(counts), time.monotonic()-started), flush=True)
            if not line.strip() or line.startswith('*'):
                continue
            if line[0] not in ' \t':
                key = line.split()[0]
                if key not in ('NAME','OBJSENSE','ROWS','COLUMNS','RHS','RANGES','BOUNDS','ENDATA'):
                    raise ValueError('Unsupported MPS section: ' + key)
                if section == 'COLUMNS':
                    flush_column(); cur_name = None
                section = key; section_names.append(key)
                if key in ('BOUNDS','ENDATA'):
                    initialize_arrays()
                continue
            if section in ('NAME','OBJSENSE','RHS','RANGES'):
                continue
            tok = line.split()
            if section == 'ROWS':
                if tok[0] == 'N':
                    if objective is not None:
                        raise ValueError('Multiple free/objective rows unsupported')
                    objective = tok[1]
                elif tok[0] in ('E','G','L'):
                    nrows += 1
                else:
                    raise ValueError('Unsupported row type: ' + tok[0])
            elif section == 'COLUMNS':
                if len(tok) not in (3,5) or tok[1] == "'MARKER'":
                    raise ValueError('Non-continuous or malformed COLUMNS line')
                name = tok[0]
                if name != cur_name:
                    flush_column()
                    cur_name, cur_nnz, cur_min, cur_max = name, 0, math.inf, 0.0
                    cur_family = name.split('[', 1)[0]
                for k in range(1, len(tok), 2):
                    value = abs(float(tok[k+1]))
                    if not math.isfinite(value):
                        raise ValueError('Non-finite coefficient')
                    if tok[k] == objective:
                        objective_nnz += (value != 0)
                    elif value != 0:
                        cur_nnz += 1
                        if value < cur_min: cur_min = value
                        if value > cur_max: cur_max = value
            elif section == 'BOUNDS':
                kind, bset, name = tok[:3]
                if kind not in ('UP','LO','FX','MI','PL','FR'):
                    raise ValueError('Unsupported/non-continuous bound type: ' + kind)
                if len(tok) != (4 if kind in ('UP','LO','FX') else 3):
                    raise ValueError('Malformed BOUNDS record')
                if bound_set is None: bound_set = bset
                if bset != bound_set: raise ValueError('Multiple bound sets unsupported')
                if name != bound_name:
                    h = name_hash(name)
                    pos = int(np.searchsorted(sorted_hashes, np.uint64(h)))
                    if pos == len(order) or int(sorted_hashes[pos]) != h:
                        raise ValueError('Bound references absent column: ' + name)
                    bound_idx = int(order[pos]); spool.seek(int(off[bound_idx]))
                    if spool.readline().decode('ascii').rstrip('\n') != name:
                        raise ValueError('Hash lookup/name mismatch: ' + name)
                    bound_name = name
                j = bound_idx
                value = float(tok[3]) if len(tok) == 4 else None
                if value is not None and not math.isfinite(value):
                    raise ValueError('Use MI/PL/FR for infinite bounds')
                if kind == 'LO': lb[j] = value
                elif kind == 'UP': ub[j] = value
                elif kind == 'FX': lb[j] = ub[j] = value
                elif kind == 'MI': lb[j] = -np.inf
                elif kind == 'PL': ub[j] = np.inf
                elif kind == 'FR': lb[j], ub[j] = -np.inf, np.inf
                bound_types[kind] += 1
            elif section == 'ENDATA':
                raise ValueError('Unexpected data after ENDATA')
    if section != 'ENDATA' or section_names.count('COLUMNS') != 1:
        raise ValueError('Incomplete or repeated MPS sections')
    actual = dict(rows=nrows, columns=len(lb), nonzeros=sum(s['matrix_nnz'] for s in stats))
    if expected and actual != expected:
        raise ValueError('Dimensions differ from solver log: {} != {}'.format(actual, expected))
    metric_names = ['range_0_1e12','range_1e12_1e9','range_1e9_1e6','range_1e6_1e3',
                    'fixed','positive_lb_range_lt_1e6','positive_lb_tiny_nonfixed',
                    'zero_lb_positive_ub_lt_1e6','tiny_nonfixed','finite_positive','infinite_range',
                    'tiny_nnz_ge_1000','tiny_nnz_ge_8760']
    accumulated = {key: np.zeros(len(stats), dtype=np.int64) for key in metric_names}
    tiny_range_sums = np.zeros(len(stats)); tiny_matrix_nnz = np.zeros(len(stats), dtype=np.int64)
    histogram, nnz_distribution = Counter(), Counter()
    smallest = []
    tiny_csv_rows = 0
    fields = ['year','name','family','lb','ub','range','matrix_nnz','is_fixed']
    with open(out / ('tiny_bound_columns_{}.csv'.format(year)), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for start in range(0, len(lb), 1_000_000):
            stop = min(start+1_000_000, len(lb)); low, high = lb[start:stop], ub[start:stop]
            ranges = high-low; fid = fids[start:stop]; nz = nnz[start:stop]
            if np.any(np.isnan(ranges)) or np.any(ranges < 0):
                raise ValueError('Invalid or reversed variable bound')
            finite = np.isfinite(ranges); positive = finite & (ranges > 0)
            tiny = positive & (ranges < 1e-6)
            masks = [(ranges>0)&(ranges<=1e-12), (ranges>1e-12)&(ranges<=1e-9),
                     (ranges>1e-9)&(ranges<=1e-6), (ranges>1e-6)&(ranges<=1e-3),
                     ranges==0, (low>0)&(ranges<1e-6), (low>0)&tiny,
                     (low==0)&(high>0)&(high<1e-6), tiny, positive, ~finite,
                     tiny&(nz>=1000), tiny&(nz>=8760)]
            for key, mask in zip(metric_names, masks):
                accumulated[key] += np.bincount(fid[mask], minlength=len(stats)).astype(np.int64)
            tiny_range_sums += np.bincount(fid[tiny], weights=ranges[tiny], minlength=len(stats))
            tiny_matrix_nnz += np.bincount(fid[tiny], weights=nz[tiny], minlength=len(stats)).astype(np.int64)
            bins, numbers = np.unique(np.floor(np.log10(ranges[positive])).astype(np.int64), return_counts=True)
            histogram.update({int(k):int(v) for k,v in zip(bins,numbers)})
            bins, numbers = np.unique(nz[tiny], return_counts=True)
            nnz_distribution.update({int(k):int(v) for k,v in zip(bins,numbers)})
            for local in np.flatnonzero(tiny):
                index = start+int(local); item = (-float(ranges[local]), -index)
                if len(smallest)<50: heapq.heappush(smallest,item)
                elif item>smallest[0]: heapq.heapreplace(smallest,item)
            # Literal range<1e-6 request includes fixed variables; flag them explicitly.
            for local in np.flatnonzero(ranges<1e-6):
                j=start+int(local); spool.seek(int(off[j])); name=spool.readline().decode('ascii').rstrip('\n')
                writer.writerow(dict(year=year,name=name,family=stats[int(fid[local])]['family'],
                                     lb=repr(float(low[local])),ub=repr(float(high[local])),
                                     range=repr(float(ranges[local])),matrix_nnz=int(nz[local]),
                                     is_fixed=int(ranges[local]==0)))
                tiny_csv_rows += 1
    for i,s in enumerate(stats):
        s.update({key:int(values[i]) for key,values in accumulated.items()})
        s['tiny_nonfixed_range_sum_native_units'] = float(tiny_range_sums[i])
        s['tiny_nonfixed_matrix_nnz'] = int(tiny_matrix_nnz[i])
        if not math.isfinite(s['matrix_abs_min']): s['matrix_abs_min'] = None
    csv_write(out / ('bound_family_summary_{}.csv'.format(year)),stats,list(stats[0]))
    smallest_rows = []
    for neg_range,neg_index in sorted(smallest,reverse=True):
        j=-neg_index;spool.seek(int(off[j]));name=spool.readline().decode('ascii').rstrip('\n')
        smallest_rows.append(dict(year=year,name=name,family=stats[int(fids[j])]['family'],
                                  lb=repr(float(lb[j])),ub=repr(float(ub[j])),range=repr(-neg_range),
                                  matrix_nnz=int(nnz[j]),is_fixed=0))
    csv_write(out / ('smallest_50_nonfixed_{}.csv'.format(year)),smallest_rows,fields)
    csv_write(out / ('tiny_nnz_distribution_{}.csv'.format(year)),
              [dict(matrix_nnz=k,columns=v) for k,v in sorted(nnz_distribution.items())],['matrix_nnz','columns'])
    with open(out / ('range_histogram_{}.txt'.format(year)),'w',encoding='utf-8') as f:
        f.write('Finite range>0 only; log10(range) bins [k,k+1), i.e. 10^k <= range < 10^(k+1). Native variable units; fixed/infinite excluded.\n')
        for k in range(min(histogram),max(histogram)+1) if histogram else []:
            f.write('[{}, {})\t{}\n'.format(k,k+1,histogram[k]))
    totals = {key:int(values.sum()) for key,values in accumulated.items()}
    assert totals['finite_positive']+totals['fixed']+totals['infinite_range']==len(lb)
    assert sum(histogram.values())==totals['finite_positive']
    assert sum(nnz_distribution.values())==totals['tiny_nonfixed']
    assert tiny_csv_rows==totals['tiny_nonfixed']+totals['fixed']
    # Scratch is retained for traceability; never remove existing scientific files.
    return dict(actual_dimensions=actual, totals=totals, objective_nnz_excluded=objective_nnz,
                matrix_abs_min=min(s['matrix_abs_min'] for s in stats if s['matrix_abs_min'] is not None),
                matrix_abs_max=max(s['matrix_abs_max'] for s in stats), bound_types=dict(bound_types),
                sections=section_names, tiny_csv_rows_including_fixed=tiny_csv_rows,
                tiny_nnz_distribution={str(k):v for k,v in sorted(nnz_distribution.items())},
                histogram_log10={str(k):v for k,v in sorted(histogram.items())},
                parser_elapsed_seconds=time.monotonic()-started,
                scratch=dict(path=str(names_path),bytes=names_path.stat().st_size),
                validations='PASS: dimensions, unique name hashes, exact bound-name checks, bound order, histogram and partition sums')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--year',type=int,required=True,choices=[2030,2040,2050])
    ap.add_argument('--out',type=Path,default=None)
    args=ap.parse_args();cfg=json.loads(args.inputs.read_text());item=cfg['cases'][str(args.year)]
    path=Path(cfg['remote_base'])/item['release']/'output_8760/model_archive/original.mps.gz'
    manifest_path=path.parent/'archive_manifest.json'
    out=args.out or Path('result_{}'.format(args.year));out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();before=path.stat();manifest=json.loads(manifest_path.read_text())
    if manifest['status']!='COMPLETE' or manifest['errors']:raise ValueError('Archive is not complete')
    records=[r for r in manifest['files'] if r['path']=='original.mps.gz']
    if len(records)!=1:raise ValueError('Archive manifest MPS entry ambiguous')
    entry=records[0]
    if before.st_size!=entry['bytes']:raise ValueError('Compressed byte count mismatch')
    digest=sha256(path)
    if digest!=entry['sha256']:raise ValueError('Compressed SHA256 mismatch')
    (out/'archive_manifest_{}.json'.format(args.year)).write_bytes(manifest_path.read_bytes())
    with open(out/'inputs_sha256_{}.txt'.format(args.year),'w',encoding='utf-8') as f:
        for p,h in [(path,digest),(manifest_path,sha256(manifest_path)),(Path(__file__),sha256(__file__)),(args.inputs,sha256(args.inputs))]:
            f.write('{}  {}\n'.format(h,p.resolve()))
        f.write('# bytes={} manifest_bytes={} verified=PASS\n'.format(before.st_size,entry['bytes']))
    print('INPUT_VERIFIED year={} bytes={} SHA256={} elapsed={:.1f}s'.format(args.year,before.st_size,digest,time.monotonic()-start),flush=True)
    result=parse_mps(path,out,args.year,item['expected_dimensions'])
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Input changed during audit')
    result.update(year=args.year,input_mps=str(path),input_sha256=digest,archive_bytes=before.st_size,
                  input_metadata_unchanged=True,finished_at=datetime.datetime.now().astimezone().isoformat(),
                  elapsed_seconds=time.monotonic()-start,python=platform.python_version(),numpy=np.__version__,
                  note='Diagnostic only. LB>0 is a bound signature, not proof of inherited-cohort causation. No BarPi or solver call.')
    (out/'audit_summary_{}.json'.format(args.year)).write_text(json.dumps(result,indent=2),encoding='utf-8')
    outputs={p.name:dict(bytes=p.stat().st_size,sha256=sha256(p)) for p in out.iterdir() if p.is_file() and p.suffix!='.scratch'}
    (out/'outputs_manifest_{}.json'.format(args.year)).write_text(json.dumps(outputs,indent=2),encoding='utf-8')
    print('COMPLETE '+json.dumps(result),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('AUDIT_FAILED: '+repr(exc),file=sys.stderr,flush=True)
        raise
