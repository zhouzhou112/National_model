"""Read-only D2 stop gate. Never edits or writes a planning state.

Usage: python audit_cohort_cleanup.py [--source OUTPUT_DIR] [--output-dir DIR]
Outputs: state_structure_audit.json, deletion_by_technology.csv,
cohort_bins.csv, and deletion_candidates.csv (all quantities in GW).
"""
from pathlib import Path
import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
BINS = [(1e-6, '(0,1e-6]'), (1e-5, '(1e-6,1e-5]'),
        (1e-4, '(1e-5,1e-4]'), (1e-3, '(1e-4,1e-3]'), (math.inf, '>1e-3')]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def assess(source):
    cohorts = source/'planning_state_candidate/capacity_cohorts.csv.gz'
    with gzip.open(cohorts, 'rt', encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    groups = defaultdict(list)
    bins = defaultdict(list)
    eligible = []
    for row in rows:
        if row['unit'] != 'GW' or int(row['build_year']) <= 2025 or row['action'] != 'new_build':
            continue
        eligible.append(row)
        key = (row['asset_class'], row['technology'], row['asset_id'])
        groups[key].append(row)
        value = float(row['capacity_delta'])
        if value > 0:
            label = next(label for bound, label in BINS if value <= bound)
            bins[(row['asset_class'], row['technology'], row['build_year'], label)].append(value)
    candidates = []
    sums = defaultdict(list)
    cohort_count = defaultdict(int)
    negative_groups = []
    for (asset_class, technology, asset_id), members in sorted(groups.items()):
        total = math.fsum(float(row['capacity_delta']) for row in members)
        if total < 0:
            negative_groups.append((asset_class, technology, asset_id, total))
        if 0 < total < 1e-3:
            candidates.append(dict(asset_class=asset_class, technology=technology,
                                   asset_id=asset_id, cohort_rows=len(members), deletion_gw=total))
            sums[(asset_class, technology)].append(total)
            cohort_count[(asset_class, technology)] += len(members)
    by_tech = [dict(asset_class=a, technology=t, assets=len(v),
                    cohort_rows=cohort_count[(a,t)], deletion_gw=math.fsum(v))
               for (a,t),v in sorted(sums.items())]
    total = math.fsum(r['deletion_gw'] for r in candidates)
    generation = math.fsum(r['deletion_gw'] for r in candidates
                          if r['asset_class'] in {'vre','hydro','thermal','storage','wave'})
    bin_rows = [dict(asset_class=a, technology=t, build_year=y, bin=b,
                     cohort_rows=len(v), total_gw=math.fsum(v))
                for (a,t,y,b),v in sorted(bins.items())]
    negatives = [float(r['capacity_delta']) for r in eligible if float(r['capacity_delta'])<0]
    report = dict(
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status='STOP_AUTHOR_REVIEW_REQUIRED' if total>1 else 'TOTAL_GATE_PASS_ONLY',
        source_output_directory=str(source.resolve()),
        source_sha256={str(p.relative_to(source)):sha(p) for p in [cohorts,
            source/'planning_state_candidate/state_metadata.json', source/'result_manifest.json']},
        rule='GW; action=new_build; build_year>2025; sum by asset_class,technology,asset_id over all model vintages; select 0<sum<0.001 GW',
        selected_assets=len(candidates), selected_cohort_rows=sum(r['cohort_rows'] for r in candidates),
        total_deletion_gw=total, total_stop_limit_gw=1.0, total_stop_triggered=total>1,
        generation_and_storage_deletion_gw=generation,
        connection_and_transmission_deletion_gw=total-generation,
        asset_sum_is_not_unique_generator_capacity=True,
        all_cohorts_active_at_2050=all(int(r['retire_year'])>2050 for r in eligible),
        negative_new_build_rows=len(negatives), negative_new_build_total_gw=math.fsum(negatives),
        negative_new_build_min_gw=min(negatives,default=0),
        negative_aggregate_groups=len(negative_groups),
        negative_tail_policy='Disclosed unchanged; not silently clamped or included as positive deletion candidates',
        by_technology=by_tech,
        actions_taken='READ_ONLY_AUDIT; no cohorts deleted, no derived state, no build, no submission',
        remaining_D1='headroom/retrofit/bound audits not run after D2 total stop',
    )
    # Secondary technology gate: recorded source capacity rather than cohort sum.
    capacity_path=source/'annual_capacity_by_technology.csv'
    if capacity_path.exists():
        with capacity_path.open(encoding='utf-8-sig',newline='') as stream:
            report['capacity_table_rows']=list(csv.DictReader(stream))
        report['source_sha256'][capacity_path.name]=sha(capacity_path)
        capacity={r['technology']:float(r['capacity']) for r in report['capacity_table_rows']
                  if r['unit']=='GW'}
        technology_checks=[]
        for row in by_tech:
            if row['asset_class'] not in {'vre','thermal','wave','storage','hydro'}:
                continue
            denominator=(capacity['ror']+capacity['reservoir'] if row['asset_class']=='hydro'
                         else capacity[row['technology']])
            fraction=row['deletion_gw']/denominator if denominator>0 else None
            technology_checks.append(dict(asset_class=row['asset_class'],technology=row['technology'],
                deletion_gw=row['deletion_gw'],installed_2050_gw=denominator,
                fraction=fraction,limit=0.001,stop_triggered=fraction is None or fraction>0.001))
        report['generation_storage_technology_gates']=technology_checks
        report['additional_stops']=[r for r in technology_checks if r['stop_triggered']]
        report['network_technology_fraction_gate']='NOT_COMPLETED_AFTER_TOTAL_AND_GENERATION_STOP'
        if report['additional_stops']:
            report['status']='STOP_AUTHOR_REVIEW_REQUIRED'
    return report, by_tech, bin_rows, candidates

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE.parent/'base_acceptance_relative_v1_20261012/evidence/2050')
    parser.add_argument('--output-dir',type=Path,default=HERE)
    args=parser.parse_args()
    report, by_tech, bins, candidates=assess(args.source)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'state_structure_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    write_csv(args.output_dir/'deletion_by_technology.csv',by_tech)
    write_csv(args.output_dir/'cohort_bins.csv',bins)
    write_csv(args.output_dir/'deletion_candidates.csv',candidates)
    print(json.dumps({k:report[k] for k in ['status','selected_assets','selected_cohort_rows','total_deletion_gw',
                      'generation_and_storage_deletion_gw','connection_and_transmission_deletion_gw',
                      'negative_new_build_rows','negative_new_build_total_gw']},indent=2))

if __name__=='__main__': main()
