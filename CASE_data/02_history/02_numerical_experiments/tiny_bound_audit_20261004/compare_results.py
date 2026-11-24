"""Local reproducible comparison of three completed audit outputs; no solver/SSH.

Run after collect.py: python compare_results.py
Outputs full family/metric side-by-side CSVs, impact estimates, checks and tables.
Physical sums use unique *_capacity_gw assets; paired *_new_gw is not added again.
"""
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
YEARS=[2030,2040,2050]


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def weighted_quantile(counter,q):
    if not counter:return None
    pairs=sorted((int(k),int(v)) for k,v in counter.items())
    values=np.array([k for k,v in pairs]);cum=np.cumsum([v for k,v in pairs])
    rank=(int(cum[-1])-1)*q
    lo=int(values[np.searchsorted(cum,math.floor(rank),side='right')])
    hi=int(values[np.searchsorted(cum,math.ceil(rank),side='right')])
    return lo+(hi-lo)*(rank-math.floor(rank))


def main():
    tables={};summaries={};impacts={};smallest=[];hashes={}
    for year in YEARS:
        folder=HERE/'cloud_results'/('result_'+str(year))
        s=json.loads((folder/('audit_summary_{}.json'.format(year))).read_text())
        t=read_csv(folder/('bound_family_summary_{}.csv'.format(year)))
        tables[year]={r['family']:r for r in t};summaries[year]=s
        counts=Counter();native_sums=defaultdict(float);positive_lb=Counter();tiny_by_name={}
        fixed_count=0
        # Independent recomputation from the delivered all-tiny CSV.
        with (folder/('tiny_bound_columns_{}.csv'.format(year))).open(newline='',encoding='utf-8') as f:
            for row in csv.DictReader(f):
                width=float(row['range']);low=float(row['lb']);high=float(row['ub'])
                assert width==high-low and 0<=width<1e-6
                if int(row['is_fixed']):assert width==0;fixed_count+=1;continue
                assert width>0
                family=row['family'];counts[family]+=1;native_sums[family]+=width
                positive_lb[family]+=(low>0);tiny_by_name[row['name']]=row
        assert fixed_count==s['totals']['fixed']
        assert sum(counts.values())==s['totals']['tiny_nonfixed']
        for family,r in tables[year].items():
            assert counts[family]==int(r['tiny_nonfixed'])
            assert positive_lb[family]==int(r['positive_lb_tiny_nonfixed'])
            assert math.isclose(native_sums[family],float(r['tiny_nonfixed_range_sum_native_units']),rel_tol=1e-12,abs_tol=1e-25)
        # Summing capacities and their paired new-build variables would double count.
        capacity_families=[f for f in counts if f.endswith('_capacity_gw')]
        pairs=[]
        for name,row in tiny_by_name.items():
            if not row['family'].endswith('_capacity_gw'):continue
            peer=row['family'].replace('_capacity_gw','_new_gw')+name[len(row['family']):]
            p=tiny_by_name.get(peer)
            pairs.append(dict(capacity=name,new_variable=peer,new_is_tiny=p is not None,
                              capacity_range_gw=float(row['range']),new_range_gw=float(p['range']) if p else None,
                              ranges_close=math.isclose(float(row['range']),float(p['range']),rel_tol=1e-6,abs_tol=1e-15) if p else None))
        capacity_sum=sum(native_sums[f] for f in capacity_families)
        impact=dict(nonfixed_columns_by_family=dict(counts),positive_lb_nonfixed_by_family=dict(positive_lb),
                    range_sum_by_family_native_units=dict(native_sums),
                    capacity_only_families=capacity_families,capacity_assets=sum(counts[f] for f in capacity_families),
                    capacity_only_headroom_gw=capacity_sum,capacity_only_headroom_kw=capacity_sum*1e6,
                    theoretical_8760h_capacity_energy_upper_gwh=capacity_sum*8760,
                    power_units_columns=sum(c for f,c in counts.items() if f.endswith('_gw')),
                    non_power_units_columns=sum(c for f,c in counts.items() if not f.endswith('_gw')),
                    matched_capacity_new_pairs=pairs,
                    tiny_column_nnz_quantiles={str(q):weighted_quantile(s['tiny_nnz_distribution'],q) for q in [0,.5,.9,.95,1]},
                    caveat='Capacity headroom sum is a box-bound worst-case amount, not observed lost investment or objective/feasibility proof. Excludes paired new variables, storage energy and dispatch/water variables.')
        impacts[str(year)]=impact
        for row in read_csv(folder/('smallest_50_nonfixed_{}.csv'.format(year))):smallest.append(row)
        for p in folder.iterdir():
            if p.is_file():
                h=hashlib.sha256()
                with p.open('rb') as f:
                    for block in iter(lambda:f.read(8<<20),b''):h.update(block)
                hashes[str(p.relative_to(HERE))]=h.hexdigest()
    families=sorted(set().union(*(set(t) for t in tables.values())))
    metrics=[k for k in next(iter(tables[2030].values())) if k!='family']
    fields=['family']+['{}_{}'.format(k,y) for k in metrics for y in YEARS]
    rows=[dict(family=f,**{'{}_{}'.format(k,y):tables[y].get(f,{}).get(k,'') for k in metrics for y in YEARS}) for f in families]
    write_csv(HERE/'three_year_family_comparison.csv',rows,fields)
    total_rows=[]
    for key in summaries[2030]['totals']:
        total_rows.append(dict(metric=key,**{str(y):summaries[y]['totals'][key] for y in YEARS}))
    for key in ['rows','columns','nonzeros']:
        total_rows.append(dict(metric=key,**{str(y):summaries[y]['actual_dimensions'][key] for y in YEARS}))
    for key in ['matrix_abs_min','matrix_abs_max','parser_elapsed_seconds']:
        total_rows.append(dict(metric=key,**{str(y):summaries[y][key] for y in YEARS}))
    write_csv(HERE/'three_year_totals.csv',total_rows,['metric','2030','2040','2050'])
    if smallest:write_csv(HERE/'smallest_50_each_year.csv',smallest,list(smallest[0]))
    result=dict(validation='PASS: CSV widths, tiny/fixed counts, family counts and range sums independently recomputed',impacts=impacts)
    (HERE/'comparison_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (HERE/'comparison_input_sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({y:{k:v for k,v in d.items() if k!='matched_capacity_new_pairs'} for y,d in impacts.items()},indent=2))
    print('TOTALS '+json.dumps(total_rows))


if __name__=='__main__':main()
