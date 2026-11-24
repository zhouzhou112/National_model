"""Compare archived 1h models; only approved fixed bounds may change."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from cispo_model.factor_screen import mps_section_sha256


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def bounds(path):
    result={};inside=False
    with path.open() as stream:
        for line in stream:
            if line.strip()=='BOUNDS':inside=True;continue
            if inside:
                if line.startswith('ENDATA'):break
                parts=line.split()
                if parts:result.setdefault(parts[2],[]).append(parts[:1]+parts[3:])
    return result


def main():
    reports=[];summary=[]
    for year in [2040,2050,2060]:
        before=HERE.parent/'base_frozen_followups_20261027'/str(year)/'frozen_1h'
        work=HERE/str(year)
        if (work/'attempt_2/frozen_1h/model_archive/original.mps').exists():work=work/'attempt_2'
        after=work/'frozen_1h'
        payload=json.loads((HERE/str(year)/'derived_static/closure.json').read_text())
        a,b=[p/'model_archive/original.mps' for p in [before,after]]
        sa,sb=mps_section_sha256(a),mps_section_sha256(b)
        changed_sections=[k for k in sa if sa[k]!=sb[k]]
        ba,bb=bounds(a),bounds(b)
        changed={k for k in ba.keys()|bb.keys() if ba.get(k)!=bb.get(k)}
        approved={r['variable']:r for r in payload['rows']}
        exact=changed==set(approved) and all(bb[k][0][0]=='FX' and
            math.isclose(float(bb[k][0][1]),r['after_gw'],rel_tol=0,abs_tol=1e-12) for k,r in approved.items())
        audit_same=sha(before/'frozen_capacity_audit.csv')==sha(after/'frozen_capacity_audit.csv')
        sources_same=all(sha(ROOT/p)==h for p,h in payload['provenance'].items())
        report=dict(year=year,status='PASS' if exact and audit_same and sources_same and changed_sections==['BOUNDS_OTHER'] else 'FAIL',
            changed_sections=changed_sections,changed_columns=len(changed),approved_columns=len(approved),
            exact_authorized_bounds=exact,original_audit_identical=audit_same,original_sources_unchanged=sources_same,
            before_mps_sha256=sha(a),after_mps_sha256=sha(b),scope='Static closure integrity; not 24h feasibility')
        reports.append(report)
        families={}
        for item in payload['rows']:families[item['family']]=families.get(item['family'],0.)+item['delta_gw']
        summary.append(dict(year=year,rows=len(approved),spur_addition_mw=1000*families.get('spur_augmentation',0),
            trunk_addition_mw=1000*families.get('trunk_augmentation',0),bio_reduction_mw=-1000*families.get('thermal_new',0),
            annual_fixed_cost_delta_cny=1e6*payload['annual_cost_delta_million_cny']))
    (HERE/'derived_integrity.json').write_text(json.dumps(reports,indent=2)+'\n')
    with (HERE/'closure_summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    print(json.dumps(reports,indent=2))
    if not all(r['status']=='PASS' for r in reports):raise SystemExit(2)


if __name__=='__main__':main()
