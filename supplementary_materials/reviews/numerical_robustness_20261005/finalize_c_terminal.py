"""Audit saved C terminal evidence against the previously completed Boff reference.

Usage: python finalize_c_terminal.py SNAPSHOT_DIRECTORY
Pure small-file analysis; no model imports, builds, or solves.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        return [d for k in sorted(a.keys()|b.keys()) for d in diff(a.get(k,'<absent>'),b.get(k,'<absent>'),path+'.'+k)]
    return [] if a==b else [dict(key=path,off=a,on=b)]

def stats(p):
    result=read(p/'result.json')
    with (p/'barrier_trajectory.csv').open() as f:
        t=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    jumps=[];zeros=[]
    for prev,cur in zip(t,t[1:]):
        for key in ['primal_inf','dual_inf','complementarity']:
            if prev[key]>0 and cur[key]>=10*prev[key]:jumps.append(dict(iteration=cur['iteration'],metric=key,previous=prev[key],current=cur[key]))
            if prev[key]==0 and cur[key]>0:zeros.append(dict(iteration=cur['iteration'],metric=key))
    log=(p/'gurobi.log').read_text(encoding='utf-8',errors='replace')
    fac={}
    for label in ['Dense cols','Factor NZ','Factor Ops']:
        m=re.search(re.escape(label)+r'\s*:\s*([\d.eE+\-]+)',log)
        fac[label]=float(m[1]) if m else None
    m=re.search(r'Presolved: ([\d,]+) rows, ([\d,]+) columns, ([\d,]+) nonzeros',log)
    fac['presolved']=list(map(lambda s:int(s.replace(',','')),m.groups())) if m else None
    return dict(result=result,factor=fac,trajectory_records=len(t),continuous=[int(x['iteration']) for x in t]==list(range(result['barrier_iterations']+1)),runtime_monotone=all(b['runtime']>=a['runtime'] for a,b in zip(t,t[1:])),work_monotone=all(b['work']>=a['work'] for a,b in zip(t,t[1:])),jumps_ge10=jumps,zero_to_positive=zeros,mean_iteration_seconds_after_1=(t[-1]['runtime']-t[1]['runtime'])/(len(t)-2))

def main():
    out=Path(sys.argv[1]).resolve();base=out.parent/'20261006T1549Z'
    off=base/'B_off744';on=out/'C_on744_full'
    verification=read(out/'transfer_verification.json')
    for e in verification['files']:
        assert not e.get('missing'), e
        b=(out/e['path']).read_bytes()
        assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
    a=stats(off);b=stats(on)
    ga=read(base/'C_off744_factor_aggfill5.gate.json')['source_sha256']
    gb=read(out/'C_on744_full.gate.json')['source_sha256']
    identity=dict(config_differences=diff(read(off/'effective_config.json'),read(on/'effective_config.json')),parameters_differences=diff(a['result']['parameters'],b['result']['parameters']),input_manifest_bytes_equal=(off/'input_manifest.csv').read_bytes()==(on/'input_manifest.csv').read_bytes(),source_Cfollowup_first_gate_differences=diff(ga,gb),source_terminal_differences=diff(gb,verification['source_sha256']),Boff_source_limitation='Original Boff gate does not contain a source manifest. Historical bundle/change log shows only C constant fix before Boff started; later manifest and C gate/terminal are equal. This is provenance evidence, not a contemporaneous hash of Boff loaded modules.')
    rel=abs(a['result']['objective']-b['result']['objective'])/max(1,abs(a['result']['objective']))
    q={}
    for name,p in [('off',off),('on',on)]:
        qc=read(p/'physical_export/solution_qc.json')
        q[name]={'status':qc.get('status'),'hard_checks':qc.get('hard_checks')}
    answer=dict(reference='20261006T1549Z/B_off744',member='C_on744_full',identity=identity,off=a,on=b,objective_absolute_difference=b['result']['objective']-a['result']['objective'],objective_relative_difference=rel,objective_relative_tolerance=1e-7,objective_gate_pass=rel<=1e-7,qc=q,decision='REJECT_CURRENT_C',reason='Both default and AggFill5 fail structure-retention gate; full744 objective comparison also exceeds fixed tolerance. Cross0/QC failure is not proof of mathematical nonequivalence.',raw_file_count=len(verification['files']))
    (out/'final_comparison.json').write_text(json.dumps(answer,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:answer[k] for k in ['identity','objective_absolute_difference','objective_relative_difference','objective_gate_pass','decision','raw_file_count']},indent=2))
    print(json.dumps({'off':{k:v for k,v in a.items() if k!='result'},'on':{k:v for k,v in b.items() if k!='result'},'qc':q},indent=2))

if __name__=='__main__':main()
