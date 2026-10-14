"""Finite, explicit read-only download of completed Base pricing inputs.

Usage: --year 2030|2040|2050 --output NEW_DIR. Copies no environment/license
files; never accesses running Base2060 or T550 backups. Retains partial files
on any failure. No scheduler, background watcher, retry or auto-commit.
"""
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

RELEASES={2030:'20260914_base_v9_t48_m750_tol1e4_v3',
          2040:'20260919_base2040_v9_t44_m750_tol1e4_v1',
          2050:'20260930_base2050_v9_t48_m750_tol1e4_v1'}
HOST='paracloud-bscc-a8'
SMALL=['model_archive/archive_manifest.json','barrier_checkpoint/barrier_checkpoint_manifest.json',
       'vre_capacity.csv','solve_report.json','model_config_snapshot.json']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--year',type=int,choices=list(RELEASES),required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists(),'Never overwrite a partial/archive directory'
    a.output.mkdir(parents=True)
    root='/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/'+RELEASES[a.year]+'/output_8760'
    code='root='+repr(root)+'\nnames='+repr(SMALL)+'\n'+'''import pathlib,json,hashlib,base64
root=pathlib.Path(root);out={}
for name in names:
 b=(root/name).read_bytes()
 out[name]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(out))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12',HOST,'python3 -'],input=code.encode(),capture_output=True,check=True)
    evidence={}
    for name,item in json.loads(result.stdout).items():
        b=base64.b64decode(item['base64']);assert hashlib.sha256(b).hexdigest()==item['sha256']
        dest=a.output/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(b)
        evidence[name]={'sha256':item['sha256'],'bytes':len(b),'verified':True}
    archive=json.loads((a.output/SMALL[0]).read_text())
    cp=json.loads((a.output/SMALL[1]).read_text())
    original=[v for v in archive['files'] if v['path'] in ['original.mps.gz','original.mps']]
    assert len(original)==1
    large=[('model_archive/'+original[0]['path'],original[0]),('barrier_checkpoint/dual_barpi.npy',cp['vectors']['dual'])]
    assert shutil.disk_usage(a.output).free>sum(v['bytes'] for _,v in large)+10*2**30
    for name,meta in large:
        dest=a.output/name
        print('Downloading',name,meta['bytes'],flush=True)
        subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',HOST+':'+root+'/'+name,str(dest)],check=True)
        assert dest.stat().st_size==meta['bytes'] and sha(dest)==meta['sha256'],name
        evidence[name]={'sha256':meta['sha256'],'bytes':meta['bytes'],'verified':True}
    (a.output/'download_identity.json').write_text(json.dumps(dict(source_release=RELEASES[a.year],source=root,files=evidence),indent=2)+'\n')
    print('VERIFIED',a.year,flush=True)


if __name__=='__main__':main()
