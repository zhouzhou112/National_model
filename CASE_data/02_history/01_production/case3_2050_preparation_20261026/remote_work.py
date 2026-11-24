"""Explicit one-shot T550 postprocessing, never scheduling or polling.

Run collect, price, assess, screen, or inspect from the repository root.
Large archives and pricing certificates stay on T550. Source results are read-only.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NOCREDIT = '20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1'
BASE2060 = '20261012_base2060_v9a12_t48_m750_tol1e4_v1'
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20',
       '-o', 'HostName=127.0.0.1', '-o', 'BindAddress=127.0.0.1', 'national-model-server']
PYTHON = '/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python'
COMMON = r'''
from pathlib import Path
import base64, hashlib, json, subprocess, sys, shutil, datetime
base=Path('/home/zz2/National_model_server/cloud_backup')
tools=Path('/home/zz2/National_model_server/postprocess_tools_20261026')
root=base/nocredit/'output_8760'
side=base/nocredit/'postprocess_20261026'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    if p.exists(): assert p.read_bytes()==raw, 'Conflicting output '+str(p)
    else: p.write_bytes(raw)
def payload(p):
    raw=p.read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
def verify(root,names):
    entries={x['path']:x for x in json.loads((root/'result_manifest.json').read_text())['files']}
    out={}
    for n in names:
        p=root/n; h=sha(p)
        if n in entries:
            assert h==entries[n]['sha256'] and p.stat().st_size==entries[n]['bytes'],n
        out[n]=dict(bytes=p.stat().st_size,sha256=h,manifest_match=n in entries)
    return out
for rel in [nocredit,base2060]:
    m=json.loads((base/rel/'backup_manifest.json').read_text())
    assert m['status']=='COMPLETE',rel
    assert sha(base/rel/'output_8760/result_manifest.json')==m['source_result_manifest_sha256'],rel
for name,encoded in tool_files.items():
    p=tools/name;raw=base64.b64decode(encoded);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==raw, 'Tool identity conflict'
    else:p.write_bytes(raw)
sys.path.insert(0,str(tools))
'''
ACTIONS = {
'compare': r'''
result={}
for label,release in [('Base','20260914_base_v9_t48_m750_tol1e4_v3'),
                      ('nocredit',nocredit),('case3','20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1')]:
    source=base/release/'output_8760'
    evidence=verify(source,['solve_report.json','result_manifest.json'])
    solve=json.loads((source/'solve_report.json').read_text())
    result[label]=dict(release=release,status=solve['status'],objective_value_million_cny=solve['objective_value_million_cny'],
        barrier_primal_dual_metrics=solve['solution_contract']['barrier_primal_dual_metrics'],source_verification=evidence)
print(json.dumps(result))
''',
'inspect': r'''
result=dict(host=subprocess.check_output(['hostname'],text=True).strip(),
    memory=Path('/proc/meminfo').read_text().splitlines()[:4],
    disk=dict(zip(['total','used','free'],shutil.disk_usage(base))),
    files=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size) for p in sorted(root.rglob('*')) if p.is_file()],
    backup=json.loads((base/nocredit/'backup_manifest.json').read_text()))
print(json.dumps(result))
''',
'collect': r'''
# Explicit size criterion includes every file <=32 MiB, including all annual/capacity tables.
names=[p.relative_to(root).as_posix() for p in sorted(root.rglob('*')) if p.is_file() and p.stat().st_size<=32*2**20]
manifest_before=sha(root/'result_manifest.json')
verified=verify(root,names)
files={n:payload(root/n) for n in names}
assert manifest_before==sha(root/'result_manifest.json')
assert all(files[n]['sha256']==v['sha256'] for n,v in verified.items())
print(json.dumps(dict(source=str(root),files=files,verification=verified,
    result_manifest_sha256=manifest_before,small_file_limit_bytes=32*2**20,
    omitted=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size) for p in sorted(root.rglob('*')) if p.is_file() and p.stat().st_size>32*2**20])))
''',
'price': r'''
side.mkdir(exist_ok=True)
target=side/'pricing'
assert not target.exists(), 'Inspect existing operation; never blindly repeat'
cmd=[sys.executable,str(tools/'scripts/price_screened_candidates.py'),'--run-dir',str(root),'--output',str(target)]
with (side/'pricing.stdout.log').open('w') as out,(side/'pricing.stderr.log').open('w') as err:
    p=subprocess.run(cmd,stdout=out,stderr=err)
assert p.returncode==0, (side/'pricing.stderr.log').read_text()[-3000:]
cert=target/'screen_pricing_certificate.json'; c=json.loads(cert.read_text())
summary={k:c[k] for k in ['B_million_cny','B_over_objective','near_optimality_decision','base_comparison_decision','scope']}
summary.update(certificate_path=str(cert),certificate_sha256=sha(cert),command=cmd,
    files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in target.iterdir() if p.is_file()},
    tool_sha256={n:sha(tools/n) for n in tool_files},source_identity=c['identity'],
    generated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save(side/'pricing_receipt.json',summary)
print(json.dumps(summary))
''',
'assess': r'''
from cispo_model.relative_acceptance import archived_inputs
side.mkdir(exist_ok=True)
names=['solution_qc.json','solve_report.json','hourly_province_balance.csv.gz','reservoir_dispatch.npz',
       'build_report.json','planning_state_candidate/state_metadata.json','vre_capacity.csv',
       'storage_capacity.csv','thermal_nuclear_capacity.csv','hydro_capacity.csv','wave_capacity.csv',
       'transmission_capacity.csv','result_manifest.json']
before=verify(root,names)
inputs=side/'assessment_inputs.json'; save(inputs,archived_inputs(root))
output=side/'solution_qc_relative_v1.json'
assert not output.exists(), 'Inspect existing assessment'
cmd=[sys.executable,str(tools/'scripts/assess_relative_v1.py'),str(root),'--inputs',str(inputs),'--output',str(output)]
p=subprocess.run(cmd,capture_output=True,text=True)
assert p.returncode in [0,2] and output.exists(),p.stderr
assert before==verify(root,names),'Source drift'
qc=json.loads(output.read_text())
result=dict(status=qc['acceptance_profiles']['relative_v1']['status'],source=str(root),command=cmd,
    source_verification=before,source_unchanged=True,tool_sha256={n:sha(tools/n) for n in tool_files})
save(side/'assessment_evidence.json',result)
result['files']={p.name:payload(p) for p in [inputs,output,side/'assessment_evidence.json']}
print(json.dumps(result))
''',
'screen': r'''
root=base/base2060/'output_8760';target=base/base2060/'screen_margin0p2_20261026'
assert not target.exists(), 'Inspect existing screen operation'
cmd=[sys.executable,str(tools/'scripts/build_vre_screen_list.py'),'--run-dir',str(root),
     '--source-release',base2060,'--margin','0.2','--output',str(target)]
p=subprocess.run(cmd,capture_output=True,text=True)
assert p.returncode==0,p.stderr
identity=json.loads((target/'screen_identity.json').read_text())
assert identity['scope']=='FULL_YEAR' and identity['identity']['source']['scenario_id']=='base'
print(json.dumps(dict(command=cmd,remote_directory=str(target),sites=identity['sites'],excluded_sites=identity['excluded_sites'],
    tool_sha256={n:sha(tools/n) for n in tool_files},
    files={p.name:payload(p) for p in target.iterdir() if p.is_file()})))
''',
}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=ACTIONS)
    args=parser.parse_args()
    names=['scripts/price_screened_candidates.py','scripts/build_vre_screen_list.py',
           'scripts/assess_relative_v1.py','cispo_model/vre_pricing.py','cispo_model/relative_acceptance.py']
    files={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}
    files['cispo_model/__init__.py']=''
    code='nocredit='+repr(NOCREDIT)+'\nbase2060='+repr(BASE2060)+'\ntool_files='+repr(files)+'\n'+COMMON+ACTIONS[args.action]
    compile(code,'<remote>','exec')
    p=subprocess.run(SSH+[PYTHON+' -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=14400)
    (HERE/(args.action+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    if p.returncode: raise RuntimeError(p.stderr[-4000:]+p.stdout[-1000:])
    result=json.loads(p.stdout)
    destination=HERE
    if args.action in ['collect','assess']:
        destination=HERE.parent/'case3_2030_launch_20261014/nocredit_results_20261026'
    if args.action=='screen': destination=HERE.parent/'base_2060_screen_20261026'
    destination.mkdir(parents=True,exist_ok=True)
    for name,info in result.get('files',{}).items() if args.action in ['collect','assess','screen'] else []:
        raw=base64.b64decode(info.pop('base64'))
        assert len(raw)==info['bytes'] and hashlib.sha256(raw).hexdigest()==info['sha256']
        relative=Path(name); assert not relative.is_absolute() and '..' not in relative.parts
        target=destination/('output_8760' if args.action=='collect' else 'assessment' if args.action=='assess' else '.')/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): assert target.read_bytes()==raw
        else: target.write_bytes(raw)
    target=destination/(args.action+'_receipt.json')
    assert not target.exists(),'Refuse overwrite of local receipt'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['files','backup','verification','source_verification','source_identity']},ensure_ascii=False))

if __name__=='__main__': main()
