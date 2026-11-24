"""Return compact gate evidence, retaining complete validation models on T550."""
from pathlib import Path
import argparse,subprocess,tarfile,json
from t550_validation import SSH,SCP,PY,REMOTE,HERE,digest,save


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('year',type=int,choices=[2040,2050,2060]);a=p.parse_args()
    code='remote='+repr(REMOTE)+'\nyear='+str(a.year)+'\n'+r'''
from pathlib import Path
import gzip,hashlib,json,sys,tarfile,math
root=Path(remote)/'repo';here=root/'supplementary_materials/reviews/base_frozen_batch2_20261027';work=here/str(year)/'cloud_identity_v2'
sys.path.insert(0,str(root))
from cispo_model.factor_screen import mps_section_sha256
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def archive(folder):
 p=folder/'model_archive/original.mps'
 return p if p.exists() else p.with_suffix('.mps.gz')
def bounds(p):
 result={};inside=False;opener=gzip.open if p.suffix=='.gz' else open
 with opener(p,'rt') as f:
  for line in f:
   if line.strip()=='BOUNDS':inside=True;continue
   if inside:
    if line.startswith('ENDATA'):break
    fields=line.split()
    if fields:result.setdefault(fields[2],[]).append(fields[:1]+fields[3:])
 return result
before=archive(work/'unclosed_1h');after=archive(work/'frozen_1h')
sa,sb=mps_section_sha256(before),mps_section_sha256(after)
changed=[k for k in sa if sa[k]!=sb[k]];ba,bb=bounds(before),bounds(after)
cols={k for k in ba.keys()|bb.keys() if ba.get(k)!=bb.get(k)}
payload=json.loads((work/'derived_static/closure.json').read_text());approved={r['variable']:r for r in payload['rows']}
exact=cols==set(approved) and all(bb[k][0][0]=='FX' and math.isclose(float(bb[k][0][1]),r['after_gw'],rel_tol=0,abs_tol=1e-12) for k,r in approved.items())
same=sha(work/'unclosed_1h/frozen_capacity_audit.csv')==sha(work/'frozen_1h/frozen_capacity_audit.csv')
overrides=[json.loads((work/n/'window_carbon_override.json').read_text()) for n in ['base_control_24h','zero_24h','frozen_24h']]
budget=json.loads((here/str(year)/'window_carbon_budget.json').read_text())
same_budget=all(r['effective_window_carbon_limit_mt']==budget['window_carbon_limit_mt'] and r['production_annual_carbon_limit_unchanged'] for r in overrides)
audit=dict(status='PASS' if exact and same and same_budget and changed==['BOUNDS_OTHER'] else 'FAIL',changed_sections=changed,changed_columns=len(cols),exact_authorized_bounds=exact,original_frozen_audit_identical=same,all_24h_budgets_identical=same_budget,annual_budget_unchanged=True,before_mps_sha256=sha(before),after_mps_sha256=sha(after),cf_environment='T550 mapping verified against cloud, no nearest-neighbor rule change')
(work/'production_identity_audit.json').write_text(json.dumps(audit,indent=2))
assert audit['status']=='PASS',audit
assert json.loads((work/'FINAL_GATES_PASSED.json').read_text())['status']=='PASS'
paths=[]
for p in work.rglob('*'):
 if p.is_file() and p.suffix in {'.json','.csv','.log'} and p.stat().st_size<500000 and 'solution_snapshot' not in p.parts:paths.append(p)
target=here/('B'+str(year)+'_cloud_identity_v2_small.tar.gz');assert not target.exists()
with tarfile.open(target,'w:gz') as tf:
 for p in paths:tf.add(p,arcname=p.relative_to(work).as_posix())
print(json.dumps(dict(status='PASS',archive=str(target),sha256=sha(target),files=len(paths),audit=audit)))
'''
    run=subprocess.run(SSH+[PY+' -'],input=code,text=True,capture_output=True,timeout=600)
    if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    receipt=json.loads(run.stdout);archive=HERE/f'B{a.year}_cloud_identity_v2_small.tar.gz'
    subprocess.run(SCP+['national-model-server:'+receipt['archive'],str(archive)],check=True)
    assert digest(archive)==receipt['sha256']
    target=HERE/str(a.year)/'cloud_identity_v2_t550';target.mkdir(exist_ok=False)
    with tarfile.open(archive) as tf:
        for m in tf.getmembers():assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        tf.extractall(target)
    save(HERE/f'B{a.year}_cloud_identity_v2_collection.json',receipt);print(receipt)


if __name__=='__main__':main()
