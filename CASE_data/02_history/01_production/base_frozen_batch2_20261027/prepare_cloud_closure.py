"""Derive exact closure in production-matching CF environment, new outputs only."""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib
import pandas as pd
import gurobipy as gp
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from cispo_model.frozen_closure import build_payload
from run_year_gates import SOURCES


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('year',type=int,choices=SOURCES);p.add_argument('--resume-derive',action='store_true');a=p.parse_args()
    work=HERE/str(a.year)/'cloud_identity_v2'
    if not a.resume_derive:work.mkdir(exist_ok=False)
    source=HERE.parent/'base_frozen_followups_20261027/source_base'/SOURCES[a.year]
    unclosed=work/'unclosed_1h'
    def run(name,args):
        with (work/(name+'.log')).open('x') as f:subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    if not a.resume_derive:run('unclosed_build',[sys.executable,str(HERE/'run_gate.py'),'--year',str(a.year),'--hours','1','--mode','frozen',
        '--source-release',str(source),'--supplement',str(source/'frozen_capacity_B_20261027'),'--output',str(unclosed)])
    conflicts=work/'unclosed_conflicts.json'
    if not a.resume_derive:run('unclosed_audit',[sys.executable,str(HERE.parent/'base_frozen_followups_20261027/diagnose_fixed_capacity_conflicts.py'),str(unclosed),'--output',str(conflicts)])
    mps=unclosed/'model_archive/original.mps'
    if not mps.exists():mps=mps.with_suffix('.mps.gz')
    model=gp.read(str(mps));audit=unclosed/'frozen_capacity_audit.csv'
    manifest=json.loads((unclosed/'frozen_capacity_report.json').read_text())['result_manifest_sha256']
    payload=build_payload(model,pd.read_csv(audit),json.loads(conflicts.read_text())['conflicts'],manifest,a.year)
    payload['provenance']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [mps,audit,conflicts]}
    payload['environment_scope']='T550 CF fallback mapping independently verified equal to cloud production; original Base untouched'
    output=work/'derived_static';output.mkdir();(output/'closure.json').write_text(json.dumps(payload,indent=2)+'\n')
    pd.DataFrame(payload['rows']).to_csv(output/'closure_audit.csv',index=False)
    model.dispose();print(a.year,len(payload['rows']),payload['annual_cost_delta_million_cny'],flush=True)


if __name__=='__main__':main()
