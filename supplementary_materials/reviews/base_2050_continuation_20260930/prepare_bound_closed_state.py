"""Close only audited sub-10kW VRE overshoots in an unaccepted state copy.

Keeps source results, scientific rejection, technical bounds and all cohort keys.
Reduces the oldest active positive cohort first, preserving newer builds where possible.
Executed once inside the fresh release using its recorded environment.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import math
import os
import shutil
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'repo'))
from cispo_model.planning_state import PlanningState

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def main():
    source=Path(os.environ['UPSTREAM_STATE'])
    original=PlanningState.load(source,expected_boundary_year=2040,allow_unaccepted_candidate=True,expected_scenario_id='base')
    audit=json.loads((ROOT/'inherited_vre_audit.json').read_text())
    bad=list(csv.DictReader((ROOT/'inherited_vre_violations.csv').open(encoding='utf-8-sig')))
    assert audit['rows']==len(bad)==129 and audit['negative_rows']==0
    assert 0<audit['max_upper_gw']<audit['capacity_floor_zero_gw']==1e-5
    assert original.metadata['scientifically_accepted'] is False
    parent=ROOT/'upstream_2040_bound_closed'
    assert not parent.exists(), 'Never overwrite a derivative state'
    with gzip.open(source/'capacity_cohorts.csv.gz','rt',encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle); fields=reader.fieldnames; records=list(reader)
    assert len(records)==len(original.cohorts)==173800
    exports=pd.read_csv(source.parent/'vre_capacity.csv').set_index(['grid_uid','technology'])
    touched=[]
    sites=[]
    for row in bad:
        asset=row['asset_id']; upper=float(row['capacity_upper_gw']); floor=float(row['capacity_floor_gw'])
        current=float(row['inherited_gw'])
        needed=current-math.nextafter(upper-floor,-math.inf)
        assert 0<needed<1e-5 and abs(needed-float(row['upper_violation_gw']))<1e-12
        exported=exports.loc[(row['grid_uid'],row['technology'])]
        assert exported.inherited_capacity_adjustment_gw==0
        assert exported.capacity_gw<=exported.capacity_upper_gw+1e-9
        selected=[r for r in records if r['asset_class']=='vre' and r['asset_id']==asset
                  and float(r['build_year'])<=2050<float(r['retire_year'])]
        assert abs(math.fsum(float(r['capacity_delta']) for r in selected)-current)<1e-12
        old=math.fsum(float(r['capacity_delta']) for r in selected if float(r['build_year'])==2030)
        assert 0<old<1e-5
        left=needed
        for record in sorted(selected,key=lambda r:float(r['build_year'])):
            before=float(record['capacity_delta'])
            if before<=0 or left<=0: continue
            assert record['unit']=='GW' and record['action']=='new_build'
            reduction=min(before,left)
            after=max(0.0, math.nextafter(before-reduction,-math.inf))
            record['capacity_delta']=repr(after)
            actual=before-after
            touched.append(dict(asset_id=asset,build_year=int(record['build_year']),before_gw=before,
                                after_gw=after,reduction_gw=actual,reduction_kw=actual*1e6))
            left-=actual
        assert left<1e-12
        after_sum=math.fsum(float(r['capacity_delta']) for r in selected)
        assert floor+after_sum<=upper+1e-12
        sites.append(dict(asset_id=asset,reduction_kw=(current-after_sum)*1e6,
                          original_2030_micro_cohort_kw=old*1e6,upper_gw=upper,
                          exogenous_2050_floor_gw=floor,source_export_2040_gw=float(exported.capacity_gw)))
    # All checks above precede writes. Preserve the original audit and source.
    parent.mkdir()
    for rel in ['inherited_vre_audit.json','inherited_vre_violations.csv']:
        shutil.copy2(ROOT/rel,ROOT/('original_'+rel))
    target=parent/'planning_state_candidate'
    shutil.copytree(source,target)
    for name in ['solution_qc.json','solve_report.json','run_identity.json']:
        shutil.copy2(source.parent/name,parent/name)
    with gzip.open(target/'capacity_cohorts.csv.gz','wt',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(records)
    cohorts=pd.read_csv(target/'capacity_cohorts.csv.gz')
    active=cohorts.loc[cohorts.build_year.le(2040)&cohorts.retire_year.gt(2040)]
    summary=active.groupby(['asset_class','technology','unit','action'],dropna=False).agg(cohort_rows=('asset_id','size'),capacity_delta=('capacity_delta','sum')).reset_index()
    summary.insert(0,'active_planning_year',2040)
    summary.to_csv(target/'state_transition_summary.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    provenance=dict(status='EXPLICIT_ENGINEERING_BOUND_CLOSURE',scientifically_accepted=False,
                    source_state=str(source),source_state_metadata_sha256=digest(source/'state_metadata.json'),
                    source_capacity_cohorts_sha256=digest(source/'capacity_cohorts.csv.gz'),
                    threshold_gw=1e-5,affected_sites=len(sites),affected_cohort_rows=len(touched),
                    total_reduction_kw=sum(x['reduction_kw'] for x in touched),
                    maximum_site_reduction_kw=max(x['reduction_kw'] for x in sites),
                    reason='Sub-10kW 2030 cohorts were cleared from 2040 inherited floors but retained in exported cohorts; reaccumulation in 2050 exceeds unchanged site upper bounds. Close only the audited excess, oldest positive cohort first.',
                    limitation='Explicit approximate derivative, not the exact unmodified 2040 solution. Original upstream QC remains HARD_FAIL; no general cohort cleanup fix claimed.',
                    affected_rows=touched,sites=sites)
    (parent/'bound_closure_audit.json').write_text(json.dumps(provenance,indent=2)+'\n')
    metadata=dict(original.metadata)
    # Do not persist runtime-only acknowledgement fields as a scientific promotion.
    metadata.pop('candidate_use_acknowledged',None)
    metadata.update(capacity_cohorts_sha256=digest(target/'capacity_cohorts.csv.gz'),
                    state_transition_summary_sha256=digest(target/'state_transition_summary.csv'),
                    continuation_bound_closure=provenance,
                    source_capacity_state_policy='EXPLICIT_BOUND_CLOSED_UNACCEPTED_CANDIDATE')
    (target/'state_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    shutil.copy2(source.parent/'result_manifest.json',parent/'original_result_manifest.json')
    manifest=dict(manifest_purpose='DERIVED_UNACCEPTED_CAPACITY_STATE_INTEGRITY',scientifically_accepted=False,
                  source_result_directory=str(source.parent),source_result_manifest_sha256=digest(source.parent/'result_manifest.json'),
                  files=[dict(path=str(p.relative_to(parent)),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(parent.rglob('*')) if p.is_file()])
    (parent/'result_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    loaded=PlanningState.load(target,expected_boundary_year=2040,expected_scenario_id='base',allow_unaccepted_candidate=True)
    assert len(loaded.cohorts)==len(original.cohorts)
    other=[c for c in original.cohorts.columns if c!='capacity_delta']
    pd.testing.assert_frame_equal(loaded.cohorts[other],original.cohorts[other])
    changed=loaded.cohorts.capacity_delta.to_numpy()!=original.cohorts.capacity_delta.to_numpy()
    assert int(changed.sum())==len(touched)
    assert digest(source/'capacity_cohorts.csv.gz')==provenance['source_capacity_cohorts_sha256']
    assert loaded.metadata['scientifically_accepted'] is False and loaded.metadata['candidate_unaccepted']
    print(json.dumps({k:v for k,v in provenance.items() if k not in ('affected_rows','sites')},indent=2))

if __name__=='__main__': main()
