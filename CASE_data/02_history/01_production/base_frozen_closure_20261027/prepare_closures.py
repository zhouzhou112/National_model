"""Derive new closure payloads from preserved 1h conflicts and original MPS."""
from pathlib import Path
import hashlib
import json
import sys

import gurobipy as gp
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from cispo_model.frozen_closure import build_payload


def main():
    for year in [2040,2050,2060]:
        source=HERE.parent/'base_frozen_followups_20261027'/str(year)
        output=HERE/str(year)/'derived_static'
        output.mkdir(parents=True,exist_ok=False)
        run=source/'frozen_1h'
        mps=run/'model_archive/original.mps'
        conflicts=source/'frozen_1h_fixed_capacity_conflicts.json'
        report=json.loads((run/'frozen_capacity_report.json').read_text())
        model=gp.read(str(mps))
        payload=build_payload(model,pd.read_csv(run/'frozen_capacity_audit.csv'),
            json.loads(conflicts.read_text())['conflicts'],report['result_manifest_sha256'],year)
        payload['provenance']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [mps,conflicts,run/'frozen_capacity_audit.csv']}
        (output/'closure.json').write_text(json.dumps(payload,indent=2)+'\n')
        pd.DataFrame(payload['rows']).to_csv(output/'closure_audit.csv',index=False)
        print(year,len(payload['rows']),payload['annual_cost_delta_million_cny'],flush=True)
        model.dispose()


if __name__=='__main__':main()
