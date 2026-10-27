"""Collect immutable Base semantic sources and original upstream capsules.

Cloud reads only. Every semantic file is checked against its result manifest;
upstream paths are recovered from archived environment and later cross-checked
by frozen_capacity.recover_upstream. No large model/vector download.
"""
from pathlib import Path
import base64
import json
import hashlib
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from cispo_model.frozen_capacity import TABLE_KEYS

RELEASES = {2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',
            2050:'20260930_base2050_v9_t48_m750_tol1e4_v1',
            2060:'20261012_base2060_v9a12_t48_m750_tol1e4_v1'}
REMOTE = r'''
from pathlib import Path
import json,hashlib,base64
base=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud')
result={}
for year,release in releases.items():
 root=base/release;out=root/'output_8760';manifest=json.loads((out/'result_manifest.json').read_text())
 entries={r['path']:r for r in manifest['files']}
 paths=[out/n for n in names]
 env=json.loads((out/'run_environment.json').read_text());parts=Path(env['planning_state_in']).parts
 starts=[i for i,v in enumerate(parts) if v.startswith('upstream_')];assert len(starts)==1
 upstream=root/Path(*parts[starts[0]:]).parent
 assert upstream.is_dir() and upstream.resolve().is_relative_to(root.resolve())
 paths += [p for p in upstream.rglob('*') if p.is_file()]
 files={}
 for p in sorted(set(paths)):
  assert p.is_file() and p.stat().st_size<=32*2**20,str(p)
  raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();rel=p.relative_to(root).as_posix()
  if out in p.parents and p.name!='result_manifest.json':
   rec=entries[p.relative_to(out).as_posix()];assert rec['bytes']==len(raw) and rec['sha256']==sha,rel
  files[rel]={'bytes':len(raw),'sha256':sha,'base64':base64.b64encode(raw).decode()}
 result[release]={'year':year,'files':files,'upstream_relative':str(upstream.relative_to(root))}
print(json.dumps(result))
'''


def main():
    names = [n for n in TABLE_KEYS if n!='hydro_spur_capacity.csv']
    names += ['result_manifest.json','run_environment.json','run_scope.json', 'input_manifest.csv',
              'run_identity.json','solution_qc.json','solve_report.json','annual_carbon_ccs.json']
    code='releases='+repr(RELEASES)+'\nnames='+repr(names)+'\n'+REMOTE
    # Cloud system Python is 3.6; avoid newer Path.is_relative_to there.
    code=code.replace('upstream.resolve().is_relative_to(root.resolve())','root.resolve() in upstream.resolve().parents')
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','python3 -'],
                     input=code,text=True,capture_output=True,timeout=900)
    (HERE/'collect_sources.stderr.log').write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr[-3000:])
    result=json.loads(p.stdout)
    for release,item in result.items():
        for name,entry in item['files'].items():
            raw=base64.b64decode(entry.pop('base64'))
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
            rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
            target=HERE/'source_base'/release/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==raw
            else:target.write_bytes(raw)
    (HERE/'source_collection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({release:len(item['files']) for release,item in result.items()})


if __name__=='__main__':main()
