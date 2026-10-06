"""Create an explicitly unaccepted derivative: close one documented 4.353 kW overshoot."""
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

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source=Path(os.environ['UPSTREAM_STATE'])
    original=PlanningState.load(source,expected_boundary_year=2030,allow_unaccepted_candidate=True,expected_scenario_id='base')
    audit=json.loads((ROOT/'inherited_vre_audit.json').read_text())
    assert audit['rows']==1 and audit['upper_rows']==1 and audit['negative_rows']==0
    example=audit['examples'][0]
    assert example['asset_id']=='G000021474::dpv'
    assert 0 < audit['max_upper_gw'] < audit['capacity_floor_zero_gw']==1e-5
    exported=pd.read_csv(source.parent/'vre_capacity.csv')
    row=exported.loc[exported.grid_uid.eq('G000021474') & exported.technology.eq('dpv')].iloc[0]
    assert row.capacity_floor_gw==0 and row.exogenous_capacity_floor_gw==5.709e-6
    parent=ROOT/'upstream_2030_bound_closed'
    if parent.exists():
        # Preserve the one incomplete preparation attempt; never touch raw results.
        assert not (parent/'result_manifest.json').exists()
        assert json.loads((parent/'bound_closure_audit.json').read_text())['source_state']==str(source)
        history=ROOT/'preparation_history/upstream_2030_bound_closed_incomplete_no_manifest'
        assert parent.resolve().parent==ROOT.resolve() and not history.exists()
        parent.rename(history)
    target=parent/'planning_state_candidate'
    shutil.copytree(source,target)
    for name in ['solution_qc.json','solve_report.json','run_identity.json']:
        shutil.copy2(source.parent/name,parent/name)
    with gzip.open(source/'capacity_cohorts.csv.gz','rt',newline='') as f:
        reader=csv.DictReader(f)
        fieldnames=reader.fieldnames
        records=list(reader)
    touched=[]
    for record in records:
        if record['asset_class']=='vre' and record['asset_id']==example['asset_id']:
            assert record['action']=='new_build' and float(record['build_year'])==2030 and float(record['retire_year'])>2040
            before=float(record['capacity_delta'])
            assert abs(before-example['inherited_gw'])<1e-15
            after=math.nextafter(example['capacity_upper_gw']-example['capacity_floor_gw'],-math.inf)
            assert 0 < before-after < 1e-5
            record['capacity_delta']=repr(after)
            touched.append(dict(asset_id=record['asset_id'],before_gw=before,after_gw=after,
                                reduction_gw=before-after,reduction_kw=(before-after)*1e6,
                                observed_floor_2040_gw=example['capacity_floor_gw'],upper_gw=example['capacity_upper_gw']))
    assert len(touched)==1
    with gzip.open(target/'capacity_cohorts.csv.gz','wt',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,lineterminator='\n')
        writer.writeheader();writer.writerows(records)
    cohorts=pd.read_csv(target/'capacity_cohorts.csv.gz')
    active=cohorts.loc[cohorts.build_year.le(2040)&cohorts.retire_year.gt(2040)]
    summary=active.groupby(['asset_class','technology','unit','action'],dropna=False).agg(cohort_rows=('asset_id','size'),capacity_delta=('capacity_delta','sum')).reset_index()
    summary.insert(0,'active_planning_year',2040)
    summary.to_csv(target/'state_transition_summary.csv',index=False,encoding='utf-8-sig',lineterminator='\n')
    provenance=dict(status='EXPLICIT_ENGINEERING_BOUND_CLOSURE',scientifically_accepted=False,
                    source_state=str(source),source_state_metadata_sha256=digest(source/'state_metadata.json'),
                    source_capacity_cohorts_sha256=digest(source/'capacity_cohorts.csv.gz'),
                    threshold_gw=1e-5,affected_rows=touched,
                    reason='2030 10kW observed-floor cleanup was absent from exported new-build cohorts; raw observed floor is added again in 2040. Reduce only the single capacity overshoot to the unchanged technical upper bound.',
                    limitation='An explicit capacity-state approximation, not an unchanged exact 2030 solution. Raw upstream QC and candidate rejection retained; no general cross-year cleanup fix claimed.')
    (parent/'bound_closure_audit.json').write_text(json.dumps(provenance,indent=2)+'\n')
    metadata=json.loads((source/'state_metadata.json').read_text())
    metadata.update(capacity_cohorts_sha256=digest(target/'capacity_cohorts.csv.gz'),
                    state_transition_summary_sha256=digest(target/'state_transition_summary.csv'),
                    continuation_bound_closure=provenance,
                    source_capacity_state_policy='EXPLICIT_BOUND_CLOSED_UNACCEPTED_CANDIDATE')
    (target/'state_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    shutil.copy2(source.parent/'result_manifest.json',parent/'original_result_manifest.json')
    manifest=dict(manifest_purpose='DERIVED_UNACCEPTED_CAPACITY_STATE_INTEGRITY',scientifically_accepted=False,
                  source_result_directory=str(source.parent),source_result_manifest_sha256=digest(source.parent/'result_manifest.json'),
                  files=[dict(path=str(p.relative_to(parent)),bytes=p.stat().st_size,sha256=digest(p))
                         for p in sorted(parent.rglob('*')) if p.is_file()])
    (parent/'result_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    loaded=PlanningState.load(target,expected_boundary_year=2030,expected_scenario_id='base',allow_unaccepted_candidate=True)
    assert len(loaded.cohorts)==len(original.cohorts)==86900
    changed=loaded.cohorts.capacity_delta.to_numpy()!=original.cohorts.capacity_delta.to_numpy()
    assert int(changed.sum())==1
    assert digest(source/'capacity_cohorts.csv.gz')==provenance['source_capacity_cohorts_sha256']
    print(json.dumps(provenance,indent=2))

if __name__=='__main__': main()
