"""Import an allowlisted, checksum-verified compact package into CASE_data."""
import argparse
import hashlib
import json
import tarfile
from datetime import datetime,timezone
from pathlib import Path,PurePosixPath


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--receipt',required=True)
    ap.add_argument('--root',default=str(Path(__file__).resolve().parent.parent));a=ap.parse_args()
    root=Path(a.root).resolve();package=Path(a.archive);receipt=json.loads(Path(a.receipt).read_text())
    assert receipt['status']=='PASS' and sha(package)==receipt['archive_sha256'] and package.stat().st_size==receipt['archive_bytes']
    with tarfile.open(package,'r:gz') as tar:
        members=tar.getmembers();manifest=json.load(tar.extractfile('package_manifest.json'));total=0
        allowed=set(manifest['files'])|{'package_manifest.json'};seen=set()
        for m in members:
            p=PurePosixPath(m.name);assert m.isfile() and not m.issym() and not m.islnk()
            assert not p.is_absolute() and '..' not in p.parts and m.name in allowed and m.name not in seen
            assert p.suffix in ('.json','.csv') and m.size<=1048576;seen.add(m.name);total+=m.size
        assert seen==allowed and total<=receipt['cases']*3145728+1048576
        # Read and validate the entire package before changing the destination.
        payload={m.name:tar.extractfile(m).read() for m in members}
        for name,info in manifest['files'].items():
            raw=payload[name];assert len(raw)==info['bytes'] and hashlib.sha256(raw).hexdigest()==info['sha256'],name
        metadata={'catalog.json','schema.json','csv_schema.json','package_manifest.json'}
        incoming=json.loads(payload['catalog.json']);incoming_schema=json.loads(payload['schema.json']);incoming_csv=json.loads(payload['csv_schema.json'])
        assert all(name in metadata or name.startswith('01_cases/') for name in payload)
        current=json.loads((root/'catalog.json').read_text()) if (root/'catalog.json').exists() else dict(schema_version=incoming['schema_version'],cases=[])
        assert current['schema_version']==incoming['schema_version']
        merged={c['release']:c for c in current['cases']}
        for case in incoming['cases']:
            rel=PurePosixPath(case['relative_directory'])
            assert rel.parts==('01_cases',case['paper_scenario'],str(case['year']),case['release'])
            if case['release'] in merged:assert merged[case['release']]==case,'Existing release metadata differs; use a new version'
            merged[case['release']]=case
        current['cases']=list(merged.values())
        if (root/'schema.json').exists():assert json.loads((root/'schema.json').read_text())==incoming_schema
        merged_csv=json.loads((root/'csv_schema.json').read_text()) if (root/'csv_schema.json').exists() else {}
        for name,columns in incoming_csv.items():
            if name in merged_csv:assert merged_csv[name]==columns,'CSV schema drift: '+name
            merged_csv[name]=columns
        for name,raw in payload.items():
            p=root/name;assert p.resolve().is_relative_to(root)
            if name not in metadata and p.exists():assert p.read_bytes()==raw,'Existing file differs; use a versioned destination: '+str(p)
        # Retain each incoming manifest/catalog as delivery evidence, then merge navigation metadata.
        delivery=root/'00_registry/deliveries'/receipt['archive_sha256'][:16];delivery.mkdir(parents=True,exist_ok=True)
        for name,raw in payload.items():
            p=delivery/name if name in metadata else root/name;p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():assert p.read_bytes()==raw
            else:p.write_bytes(raw)
        for name,value in [('catalog.json',current),('schema.json',incoming_schema),('csv_schema.json',merged_csv)]:
            p=root/name;temp=p.with_suffix('.json.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
    for name,info in manifest['files'].items():
        p=delivery/name if name in metadata else root/name
        assert sha(p)==info['sha256']
    schema=json.loads((root/'schema.json').read_text())
    for case in json.loads((root/'catalog.json').read_text())['cases']:
        for module in schema['modules']:(root/case['relative_directory']/module).mkdir(exist_ok=True)
    result=dict(status='PASS',files=len(manifest['files']),bytes=total,case_count=receipt['cases'],archive_sha256=receipt['archive_sha256'],
                imported_at_utc=datetime.now(timezone.utc).isoformat(),root=str(root),no_original_large_files=True)
    target=delivery/'import_receipt.json';target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
