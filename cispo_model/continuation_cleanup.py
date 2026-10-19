"""Reusable R1 cleanup audit, preserving the author 6b/6c gates.

Derived from the audited 2026-10-12 implementation. No state mutation.
All new-build grouping remains by asset class, technology and stable asset ID.
"""
from pathlib import Path
import hashlib
import math
import pandas as pd

NETWORK={'vre_spur','hydro_spur','trunk','intra_load_center_transmission','interprovincial_transmission'}
GENERATION={'vre','hydro','thermal','wave','storage'}

def active_retrofit_assets(cohorts,planning_year):
    """Author 6c: existence of a surviving row, including an exact-zero row.

    No unapproved minimum-retrofit threshold or 'would become negative' filter.
    Retirement at the boundary means the cohort is no longer active.
    """
    active=cohorts.action.eq('retrofit_out') & cohorts.build_year.le(planning_year) & cohorts.retire_year.gt(planning_year)
    return set(cohorts.loc[active,['asset_class','technology','asset_id']].itertuples(index=False,name=None))

def assess(source, *, planning_year, source_year, protect_active_retrofit=True):
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
    protected=[]
    if protect_active_retrofit:
        protected_keys=active_retrofit_assets(cohorts,planning_year)
        for key,value in selected.items():
            if key in protected_keys:
                protected.append(dict(zip(keys,key),new_build_gw=float(value)))
        selected=selected[[key not in protected_keys for key in selected.index]]
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
    h=cohorts[(cohorts.asset_class=='hydro_spur') & (cohorts.build_year<=source_year) & (cohorts.retire_year>source_year)]
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
            positive_deleted_gw=positive,installed_source_year_gw=installed,ratio=fraction,
            ratio_gate_applicable=required,ratio_gate_pass=not required or fraction<=.001))
    generation=math.fsum(r['positive_deleted_gw'] for r in rows if r['asset_class'] in GENERATION)
    network=math.fsum(r['positive_deleted_gw'] for r in rows if r['asset_class'] in NETWORK)
    failures=[r for r in rows if not r['ratio_gate_pass']]
    report=dict(rule_version='AUTHOR_R1_20261014', source_year=source_year, planning_year=planning_year,
        retrofit_protected_groups=protected,retrofit_protected_new_build_gw=math.fsum(r['new_build_gw'] for r in protected),
        status='PASS' if generation<=1 and network<=1 and not failures else 'STOP_AUTHOR_REVIEW_REQUIRED',
        threshold_gw=.001,generation_and_storage_deleted_gw=generation,network_deleted_gw=network,
        separate_total_limit_gw=1,ratio_limit=.001,ratio_gate_minimum_installed_gw=1,
        deleted_assets=len(selected),positive_deleted_assets=int(selected.gt(0).sum()),
        deleted_cohort_rows=int(delete.sum()),nonpositive_deleted_assets=int(selected.le(0).sum()),
        retained_negative_rows=int(negative.sum()),retained_negative_zeroing_increase_gw=-math.fsum(cohorts.loc[negative,'capacity_delta']),
        removed_negative_cohort_rows=int((delete & cohorts.capacity_delta.lt(0)).sum()),
        signed_deleted_gw=math.fsum(cohorts.loc[delete,'capacity_delta']),
        by_technology=rows,failures=failures,source_sha256=inputs,
        denominator_hydro_spur='existing_capacity_gw + active hydro_spur cohorts in source year',
        disclosure=('Storage included in generation total conservatively; positive deleted storage GW by technology: '
            + ', '.join(f"{r['technology']}={r['positive_deleted_gw']:.17g}" for r in rows if r['asset_class']=='storage')
            + '. Positive deletion totals do not cancel negative groups; signed deltas disclosed separately.'),
        state_changed=False)
    return report,cohorts,delete,negative
