"""Read small immutable cloud artifacts; verify local copies and archive manifests.

Run with Python from the repository root. No remote writes or credential reads.
Large dispatch/checkpoint/model files are inventoried, never downloaded here.
"""
from pathlib import Path
import base64
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
RELEASES = {
    2030: '20260914_base_v9_t48_m750_tol1e4_v3',
    2040: '20260919_base2040_v9_t44_m750_tol1e4_v1',
    2050: '20260930_base2050_v9_t48_m750_tol1e4_v1',
}
REMOTE = r'''
from pathlib import Path
import base64, hashlib, json
base=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud')
result={}
for year,release in releases.items():
    root=base/release
    out=root/'output_8760'
    names=['solution_qc.json','solve_report.json','preservation_report.json',
           'result_manifest.json','run_identity.json','build_report.json',
           'run_summary.json','reservoir_station_index.csv','vre_capacity.csv',
           'hydro_capacity.csv','thermal_nuclear_capacity.csv','storage_capacity.csv',
           'wave_capacity.csv','annual_capacity_by_technology.csv',
           'planning_state_candidate/state_metadata.json',
           'planning_state_candidate/state_transition_summary.csv',
           'planning_state_candidate/capacity_cohorts.csv.gz']
    files={}
    for name in names:
        p=out/name
        if not p.exists(): continue
        assert p.stat().st_size<32*1024*1024, str(p)
        data=p.read_bytes()
        files[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                     'base64':base64.b64encode(data).decode('ascii')}
    inventory={}
    for p in out.rglob('*'):
        if p.is_file(): inventory[str(p.relative_to(out))]=p.stat().st_size
    result[year]={'release':str(root),'files':files,'inventory_bytes':inventory}
print(json.dumps(result))
'''

def main():
    proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20',
                         'paracloud-bscc-a8','python3 -'],
                        input='releases='+repr(RELEASES)+'\n'+REMOTE,
                        capture_output=True,text=True,encoding='utf-8',timeout=300)
    proc.check_returncode()
    result=json.loads(proc.stdout)
    for year,entry in result.items():
        target=HERE/'evidence'/year
        target.mkdir(parents=True,exist_ok=True)
        for name,info in entry['files'].items():
            data=base64.b64decode(info.pop('base64'))
            assert hashlib.sha256(data).hexdigest()==info['sha256']
            path=target/name
            path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists(): assert path.read_bytes()==data, str(path)
            else: path.write_bytes(data)
        manifest=json.loads((target/'result_manifest.json').read_text(encoding='utf-8'))
        entries={x['path']:x for x in manifest['files']}
        for name,info in entry['files'].items():
            if name in entries:
                assert info['sha256']==entries[name]['sha256'], (year,name)
                assert info['bytes']==entries[name]['bytes'], (year,name)
                info['archive_manifest_check']='PASS'
            else: info['archive_manifest_check']='NOT_LISTED_SOURCE_SHA_RECORDED'
    (HERE/'collection_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({year:{'files':len(e['files']),'bytes':sum(e['inventory_bytes'].values())}
                      for year,e in result.items()},indent=2))

if __name__=='__main__': main()
