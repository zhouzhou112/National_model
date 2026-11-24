"""Create a fresh isolated root from hashed code and previously transferred data."""
from pathlib import Path
import argparse
import hashlib
import json
import tarfile

p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('code',type=Path);p.add_argument('data_archive',type=Path);a=p.parse_args()
root=a.root.resolve();root.mkdir(parents=True,exist_ok=False)
if hashlib.sha256(a.data_archive.read_bytes()).hexdigest()!='c5b60a30756b46ae070fdf70f4f222c90e4aab352ccb678e040f70e1f4679a5d':
    raise ValueError('Old data archive SHA mismatch')
for archive,only_data in [(a.data_archive,True),(a.code,False)]:
    with tarfile.open(archive) as tar:
        members=[m for m in tar.getmembers() if not only_data or m.name.startswith('data/') or m.name=='experiment_manifest.json']
        for m in members:
            if not m.isfile() or not (root/m.name).resolve().is_relative_to(root) or (root/m.name).exists():
                raise ValueError('Unsafe/duplicate member '+m.name)
        tar.extractall(root,members=members)
for manifest,only_data in [('experiment_manifest.json',True),('server_code_manifest.json',False)]:
    for e in json.loads((root/manifest).read_text())['files']:
        if only_data and not e['path'].startswith('data/'):continue
        if hashlib.sha256((root/e['path']).read_bytes()).hexdigest()!=e['sha256']:raise ValueError(e['path'])
(root/'install_validation.json').write_text(json.dumps({'status':'PASS','old_data_archive_verified':True,'code_state_sha_verified':True}))
print('PASS',root)
