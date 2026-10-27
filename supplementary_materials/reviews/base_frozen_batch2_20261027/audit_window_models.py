"""Verify the sole 24h model change versus static-closure gate is carbon RHS."""
from pathlib import Path
import argparse,hashlib,json,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]))
from cispo_model.factor_screen import mps_section_sha256


def rhs(path):
    result={};inside=False
    with path.open() as stream:
        for line in stream:
            if line.strip()=='RHS':inside=True;continue
            if inside:
                if not line.startswith(' '):break
                fields=line.split()
                for i in range(1,len(fields),2):result[fields[i]]=float(fields[i+1])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('year',type=int,choices=[2040,2050]);p.add_argument('--attempt',type=int,default=1);a=p.parse_args()
    before=HERE.parent/'base_frozen_closure_20261027'/str(a.year)
    after=HERE/str(a.year)
    if a.attempt!=1:after=after/('attempt_'+str(a.attempt))
    source=before/'base_control_24h/model_archive/original.mps'
    target=after/'base_control_24h/model_archive/original.mps'
    sa,sb=mps_section_sha256(source),mps_section_sha256(target)
    changed=[k for k in sa if sa[k]!=sb[k]]
    ra,rb=rhs(source),rhs(target)
    changed_rows=[k for k in ra.keys()|rb.keys() if ra.get(k)!=rb.get(k)]
    expected=json.loads((HERE/str(a.year)/'window_carbon_budget.json').read_text())['window_carbon_limit_mt']
    onehour=[p/'frozen_1h/model_archive/original.mps' for p in (before,after)]
    same_1h=hashlib.sha256(onehour[0].read_bytes()).digest()==hashlib.sha256(onehour[1].read_bytes()).digest()
    report=dict(status='PASS' if changed==['RHS'] and changed_rows==['annual_net_carbon_limit'] and abs(rb['annual_net_carbon_limit']-expected)<1e-12 and same_1h else 'FAIL',
        year=a.year,changed_sections=changed,changed_rhs_rows=changed_rows,
        original_carbon_rhs=ra['annual_net_carbon_limit'],effective_carbon_rhs=rb['annual_net_carbon_limit'],
        one_hour_model_identical=same_1h,annual_limit_unchanged=True,
        before_mps_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),after_mps_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (after/'window_model_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
    if report['status']!='PASS':raise SystemExit(2)


if __name__=='__main__':main()
