"""Exercise separate real-case deliveries, idempotence and tampered payload rejection."""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

DATA=Path(__file__).resolve().parent.parent


def digest(b):return hashlib.sha256(b).hexdigest()


def main():
    archive=DATA/'00_registry/paper_core_modules_v1_20261124.tar.gz'
    with tarfile.open(archive) as tar:all_data={m.name:tar.extractfile(m).read() for m in tar.getmembers()}
    cases=[c for c in json.loads(all_data['catalog.json'])['cases'] if c['scientific_tables']][:2]
    temp_root=DATA/'00_registry/import_tests';temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root,prefix='exact_') as tmp:
        tmp=Path(tmp).resolve();assert tmp.is_relative_to(temp_root.resolve());dest=tmp/'installed'
        def package(case,label,tamper=False):
            payload={k:v for k,v in all_data.items() if k.startswith(case['relative_directory']+'/') or k in ('schema.json','csv_schema.json')}
            payload['catalog.json']=json.dumps(dict(schema_version=json.loads(all_data['catalog.json'])['schema_version'],cases=[case])).encode()
            manifest=dict(files={k:dict(bytes=len(v),sha256=digest(v)) for k,v in payload.items()})
            if tamper:
                key=next(k for k in payload if k.endswith('02_costs.csv'));payload[key]+=b'BAD\n'
            payload['package_manifest.json']=json.dumps(manifest).encode();path=tmp/(label+'.tar.gz')
            with tarfile.open(path,'w:gz') as tar:
                for k,v in payload.items():info=tarfile.TarInfo(k);info.size=len(v);tar.addfile(info,io.BytesIO(v))
            receipt=tmp/(label+'.receipt.json');receipt.write_text(json.dumps(dict(status='PASS',archive_sha256=digest(path.read_bytes()),archive_bytes=path.stat().st_size,cases=1)))
            return path,receipt
        def run(pair):return subprocess.run([sys.executable,str(DATA/'workflow/import_core_package.py'),'--archive',str(pair[0]),'--receipt',str(pair[1]),'--root',str(dest)],capture_output=True)
        first=package(cases[0],'first');second=package(cases[1],'second')
        for pair in [first,second,second]:
            r=run(pair);assert r.returncode==0,r.stderr.decode(errors='replace')
        assert len(json.loads((dest/'catalog.json').read_text())['cases'])==2
        before={str(p.relative_to(dest)):digest(p.read_bytes()) for p in dest.rglob('*') if p.is_file()}
        r=run(package(cases[0],'bad',tamper=True));assert r.returncode!=0
        after={str(p.relative_to(dest)):digest(p.read_bytes()) for p in dest.rglob('*') if p.is_file()};assert before==after
    result=dict(status='PASS',checks=['two disjoint real-case batches preserve both cases','identical reimport accepted without payload overwrite','tampered core rejected before any destination change'])
    (DATA/'00_registry/import_tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main()
