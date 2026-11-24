"""Freeze explicit non-secret code/state files; reuse verified prior data archive."""
from pathlib import Path
import hashlib
import json
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    files={}
    for folder in ('cispo_model','config'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and p.suffix in {'.py','.json','.csv','.yml','.yaml'}:
                files['repo/'+p.relative_to(ROOT).as_posix()]=p
    files['repo/'+(HERE/'run_probe.py').relative_to(ROOT).as_posix()]=HERE/'run_probe.py'
    for p in (HERE/'upstream_2030_bound_closed').rglob('*'):
        if p.is_file():files[p.relative_to(HERE).as_posix()]=p
    manifest={'files':[{'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        for rel,p in sorted(files.items())]}
    mf=HERE/'server_code_manifest.json'
    mf.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with tarfile.open(HERE/'server_code_v1.tar.gz','x:gz') as tar:
        for rel,p in sorted(files.items()):tar.add(p,arcname=rel,recursive=False)
        tar.add(mf,arcname=mf.name)


if __name__=='__main__':main()
