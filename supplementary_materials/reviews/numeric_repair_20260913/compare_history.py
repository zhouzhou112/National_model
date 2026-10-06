"""Compare preserved full-year run reports, without solving or editing inputs."""
from pathlib import Path
import csv
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
OLD=ROOT/'downloads/paracloud_4139552_2030_8760_stagea_barrier_v2_20260826'


def main():
    old=json.loads((OLD/'output/solve_report.json').read_text(encoding='utf-8'))
    evidence=OUT.parent/'base_numeric_failure_20260913/evidence'
    candidates=list(evidence.rglob('*solve_report*.json'))
    if len(candidates)!=1:
        raise ValueError(f'Expected one failed Base solve report, found {candidates}')
    new=json.loads(candidates[0].read_text(encoding='utf-8'))
    rows=[]
    for group in ('model_statistics','solver_parameters','iteration_counts'):
        for key in sorted(set(old.get(group,{})) | set(new.get(group,{}))):
            before=old.get(group,{}).get(key);after=new.get(group,{}).get(key)
            rows.append(dict(group=group,metric=key,old=before,new=after,equal=before==after))
    for key in ('status','runtime_seconds','solution_count','objective_value_million_cny',
                'solver_profile_id','formulation_profile_id'):
        rows.append(dict(group='run',metric=key,old=old.get(key),new=new.get(key),equal=old.get(key)==new.get(key)))
    with (OUT/'history/run_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['group','metric','old','new','equal']);writer.writeheader();writer.writerows(rows)
    print(json.dumps(rows,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
