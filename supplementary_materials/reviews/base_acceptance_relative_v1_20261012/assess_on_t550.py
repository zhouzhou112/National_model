"""One-shot offline assessment against verified T1 backup, without source writes.

Uploads only assessment source to a dedicated tools directory, evaluates each
archive with the public CLI, and retrieves small JSON evidence. Never transfers
the backup again and never reads credentials. Run from the repository root.
"""
from pathlib import Path
import base64
import json
import subprocess
from collect_evidence import RELEASES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-o','HostName=127.0.0.1',
     '-o','BindAddress=127.0.0.1','national-model-server']
REMOTE=r'''
from pathlib import Path
import base64,hashlib,json,subprocess,sys
root=Path('/home/zz2/National_model_server/acceptance_tools_20261012')
for name,content in files.items():
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(base64.b64decode(content))
sys.path.insert(0,str(root))
from cispo_model.relative_acceptance import archived_inputs
base=Path('/home/zz2/National_model_server/cloud_backup')
result={}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
for year,release in releases.items():
    source=base/release/'output_8760'
    target=base/release/'acceptance_relative_v1_20261012'
    target.mkdir(exist_ok=True)
    output=target/'solution_qc_relative_v1.json'
    if output.exists():
        raise RuntimeError('Assessment already exists; inspect before rerun: '+str(output))
    context=archived_inputs(source)
    inputs=target/'assessment_inputs.json'
    inputs.write_text(json.dumps(context,indent=2)+'\n')
    p=subprocess.run([sys.executable,str(root/'scripts/assess_relative_v1.py'),str(source),
                      '--inputs',str(inputs),'--output',str(output)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    names=['solution_qc.json','solve_report.json','preservation_report.json','result_manifest.json',
        'run_identity.json','build_report.json','planning_state_candidate/state_metadata.json',
        'planning_state_candidate/capacity_cohorts.csv.gz','hourly_province_balance.csv.gz',
        'reservoir_dispatch.npz','vre_capacity.csv','hydro_capacity.csv','thermal_nuclear_capacity.csv',
        'storage_capacity.csv','wave_capacity.csv','transmission_capacity.csv']
    hashes={n:sha(source/n) for n in names}
    manifest=json.loads((source/'result_manifest.json').read_text())
    indexed={r['path']:r['sha256'] for r in manifest['files']}
    for n,digest in hashes.items():
        if n in indexed:assert digest==indexed[n],n
    result[year]=dict(assessment=json.loads(output.read_text()),inputs=context,source_sha256=hashes,
        archive=str(source),sidecar=str(target),manifest_verified=[n for n in hashes if n in indexed])
print(json.dumps(result))
'''

def main():
    files={p:base64.b64encode((ROOT/p).read_bytes()).decode() for p in
           ['cispo_model/relative_acceptance.py','scripts/assess_relative_v1.py']}
    files['cispo_model/__init__.py']=base64.b64encode(b'').decode()
    code='files='+repr(files)+'\nreleases='+repr(RELEASES)+'\n'+REMOTE
    p=subprocess.run(SSH+['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python -'],
                     input=code,capture_output=True,text=True,encoding='utf-8',timeout=600)
    if p.returncode:raise RuntimeError(p.stderr)
    result=json.loads(p.stdout)
    for year,entry in result.items():
        target=HERE/'assessments'/year;target.mkdir(parents=True,exist_ok=True)
        for name,key in [('solution_qc_relative_v1.json','assessment'),('assessment_inputs.json','inputs')]:
            (target/name).write_text(json.dumps(entry[key],indent=2)+'\n',encoding='utf-8')
        (target/'evidence_manifest.json').write_text(json.dumps({k:v for k,v in entry.items() if k not in ['assessment','inputs']},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({y:e['assessment']['acceptance_profiles']['relative_v1']['status'] for y,e in result.items()}))

if __name__=='__main__':main()
