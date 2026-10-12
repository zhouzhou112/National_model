"""Read-only author section 6b cleanup gate; preserves the first stop evidence.

Usage: python audit_cleanup_6b.py [--source OUTPUT_DIR] [--output-dir DIR]
No state is changed. Quantities are GW; model new-build vintages are grouped
by asset class, technology and asset ID. Retrofit and non-GW rows are retained.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import pandas as pd

HERE=Path(__file__).resolve().parent
NETWORK={'vre_spur','hydro_spur','trunk','intra_load_center_transmission','interprovincial_transmission'}
GENERATION={'vre','hydro','thermal','wave','storage'}

def assess(source):
    source=Path(source)
    inputs={}
    def read(name):
        p=source/name
        inputs[name]=hashlib.sha256(p.read_bytes()).hexdigest()
        return pd.read_csv(p)
    cohorts=read('planning_state_candidate/capacity_cohorts.csv.gz')
    eligible=cohorts.unit.eq('GW') & cohorts.action.eq('new_build') & cohorts.build_year.gt(2025)
    c=cohorts.loc[eligible]
    keys=['asset_class','technology','asset_id']
    sums=c.groupby(keys,dropna=False).capacity_delta.agg(lambda x: math.fsum(x))
    assert set(c.asset_class)<=NETWORK|GENERATION
    selected=sums[sums<.001]
    deleted_keys=set(selected.index)
    delete=eligible & pd.Series([tuple(r) in deleted_keys for r in cohorts[keys].itertuples(index=False,name=None)],index=cohorts.index)
    negative=eligible & ~delete & cohorts.capacity_delta.lt(0)
    cap=read('annual_capacity_by_technology.csv').set_index('technology').capacity.to_dict()
    denominator={}
    for a,t in sums.index.droplevel('asset_id').unique():
        if a in GENERATION:
            denominator[(a,t)]=cap['ror']+cap['reservoir'] if a=='hydro' else cap[t]
    for a,file,field,techfield in [
        ('vre_spur','intra_grid_vre_site_design.csv','spur_capacity_gw','technology'),
        ('interprovincial_transmission','transmission_capacity.csv','capacity_gw','preset_technology'),
        ('intra_load_center_transmission','load_center_intra_transmission.csv','capacity_gw','technology')]:
        frame=read(file)
        for t,total in frame.groupby(techfield)[field].sum().items():
            denominator[(a,t)]=float(total)
    denominator[('trunk','AC_trunk')]=float(read('intra_grid_substation_design.csv').trunk_capacity_gw.sum())
    hydro=read('hydro_capacity.csv')
    # Matches master.py: existing hydro capacity + all active hydro_spur cohorts.
    h=cohorts[(cohorts.asset_class=='hydro_spur') & (cohorts.build_year<=2050) & (cohorts.retire_year>2050)]
    denominator[('hydro_spur','hydro')]=math.fsum(hydro.existing_capacity_gw)+math.fsum(h.capacity_delta)
    rows=[]
    for (a,t),values in selected.groupby(level=['asset_class','technology']):
        installed=denominator[(a,t)]
        assert installed>=0 and math.isfinite(installed)
        positive=math.fsum(max(float(x),0) for x in values)
        signed=math.fsum(values)
        required=installed>=1.0
        fraction=positive/installed if installed>0 else None
        rows.append(dict(asset_class=a,technology=t,selected_assets=len(values),
            positive_selected_assets=int(values.gt(0).sum()),signed_deleted_gw=signed,
            positive_deleted_gw=positive,installed_2050_gw=installed,ratio=fraction,
            ratio_gate_applicable=required,ratio_gate_pass=not required or fraction<=.001))
    generation=math.fsum(r['positive_deleted_gw'] for r in rows if r['asset_class'] in GENERATION)
    network=math.fsum(r['positive_deleted_gw'] for r in rows if r['asset_class'] in NETWORK)
    failures=[r for r in rows if not r['ratio_gate_pass']]
    report=dict(rule_version='AUTHOR_TASK_6B_20261012',
        status='PASS' if generation<=1 and network<=1 and not failures else 'STOP_AUTHOR_REVIEW_REQUIRED',
        threshold_gw=.001,generation_and_storage_deleted_gw=generation,network_deleted_gw=network,
        separate_total_limit_gw=1,ratio_limit=.001,ratio_gate_minimum_installed_gw=1,
        deleted_assets=len(selected),positive_deleted_assets=int(selected.gt(0).sum()),
        deleted_cohort_rows=int(delete.sum()),nonpositive_deleted_assets=int(selected.le(0).sum()),
        retained_negative_rows=int(negative.sum()),retained_negative_zeroing_increase_gw=-math.fsum(cohorts.loc[negative,'capacity_delta']),
        removed_negative_cohort_rows=int((delete & cohorts.capacity_delta.lt(0)).sum()),
        signed_deleted_gw=math.fsum(cohorts.loc[delete,'capacity_delta']),
        by_technology=rows,failures=failures,source_sha256=inputs,
        denominator_hydro_spur='existing_capacity_gw + active hydro_spur cohorts in 2050',
        disclosure='Storage included in generation total conservatively; current deleted storage is zero. Positive deletion totals do not cancel negative groups; signed deltas disclosed separately.',
        state_changed=False)
    return report,cohorts,delete,negative

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=HERE.parent/'base_acceptance_relative_v1_20261012/evidence/2050')
    p.add_argument('--output-dir',type=Path,default=HERE/'revision_6b')
    a=p.parse_args()
    report,_,_,_=assess(a.source)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'cleanup_gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    pd.DataFrame(report['by_technology']).to_csv(a.output_dir/'deletion_by_technology.csv',index=False)
    print(json.dumps({k:v for k,v in report.items() if k not in ['by_technology','source_sha256']},indent=2))

if __name__=='__main__':main()
