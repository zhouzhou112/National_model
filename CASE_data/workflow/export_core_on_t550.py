"""Build and package the modular paper core from SHA-verified T550 preprocessing.

No original outputs are edited. No solver is imported. New output directory required.
"""
import argparse
import csv
import hashlib
import json
import shutil
import tarfile
from datetime import datetime,timezone
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--library',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--schema',default=str(Path(__file__).with_name('core_schema_v1.json')))
    ap.add_argument('--names',default=str(Path(__file__).with_name('paper_scenarios.json')));a=ap.parse_args()
    lib=Path(a.library);out=Path(a.out);assert not out.exists(), 'Use a new version; never overwrite a prior delivery'
    schema=json.loads(Path(a.schema).read_text());names=json.loads(Path(a.names).read_text())['mapping']
    cases=json.loads((lib/'catalog.json').read_text())['cases'];out.mkdir(parents=True)
    catalog=[];all_files={};csv_schema={}
    for case in cases:
        src=lib/case['relative_directory'];old=json.loads((src/'core_manifest.json').read_text())
        for name,info in old['files'].items():assert sha(src/name)==info['sha256'],src/name
        identity=json.loads((src/'core/00_identity.json').read_text())
        backup=Path(identity['full_backup'])/'backup_manifest.json'
        assert sha(backup)==identity['backup_manifest_sha256'],backup
        b=json.loads(backup.read_text());assert b['status']=='COMPLETE'
        assert b.get('source_unchanged_after_transfer',True) is True
        paper=names[case['case']];relative=Path('01_cases')/paper/str(case['year'])/case['release'];dest=out/relative
        dest.mkdir(parents=True);file_manifest={};source_map={}
        for module in schema['modules']:(dest/module).mkdir()
        for original,module in schema['file_modules'].items():
            p=src/'core'/original
            if not p.exists():
                assert not case['scientific_tables'],p
                continue
            target=dest/module/original;shutil.copyfile(p,target)
            rel=str(target.relative_to(dest));file_manifest[rel]=dict(bytes=target.stat().st_size,sha256=sha(target))
            source_map[rel]=dict(path=str(p),sha256=sha(p))
            if target.suffix=='.csv':
                with target.open(encoding='utf-8') as f:header=next(csv.reader(f))
                if original in csv_schema:assert header==csv_schema[original]
                csv_schema[original]=header
        if case['scientific_tables']:
            annual=json.loads((src/'core/01_annual_summary.json').read_text());target=dest/'06_carbon/carbon_accounting.json'
            save(target,annual['carbon']);rel=str(target.relative_to(dest));file_manifest[rel]=dict(bytes=target.stat().st_size,sha256=sha(target))
            source_map[rel]=dict(path=str(src/'core/01_annual_summary.json'),sha256=sha(src/'core/01_annual_summary.json'),object='carbon')
            assert len(file_manifest)==schema['scientific_core_count']
        module_status={module:dict(title_zh=label,status='AVAILABLE' if any(n.startswith(module+'/') for n in file_manifest) else 'NOT_APPLICABLE_NO_COMPLETE_SOLUTION',
                            files=[n for n in file_manifest if n.startswith(module+'/')]) for module,label in schema['modules'].items()}
        info=dict(paper_scenario=paper,legacy_case=case['case'],year=case['year'],release=case['release'],kind=case['kind'],
             acceptance_status=case['acceptance'],scientific_tables=case['scientific_tables'],source_backup=identity['full_backup'],
             source_result_manifest_sha256=identity.get('source_result_manifest_sha256'),source_backup_manifest_sha256=identity['backup_manifest_sha256'],
             schema_version=schema['version'],modules=module_status,source_files=source_map,price_scope=schema['price_boundary'])
        save(dest/'case.json',info);save(dest/'core_manifest.json',dict(schema_version=schema['version'],files=file_manifest))
        assert max(f['bytes'] for f in file_manifest.values())<=schema['max_file_bytes']
        total=sum(f['bytes'] for f in file_manifest.values());assert total<=schema['max_case_bytes']
        for p in dest.rglob('*'):
            if p.is_file():all_files[str(p.relative_to(out))]=dict(bytes=p.stat().st_size,sha256=sha(p))
        catalog.append(dict(**{k:info[k] for k in ('paper_scenario','legacy_case','year','release','kind','acceptance_status','scientific_tables')},
                            relative_directory=str(relative),core_file_count=len(file_manifest),core_bytes=total))
    save(out/'catalog.json',dict(schema_version=schema['version'],cases=catalog));save(out/'schema.json',schema);save(out/'csv_schema.json',csv_schema)
    for name in ['catalog.json','schema.json','csv_schema.json']:all_files[name]=dict(bytes=(out/name).stat().st_size,sha256=sha(out/name))
    save(out/'package_manifest.json',dict(files=all_files,source_library=str(lib),computed_on='T550',created_at_utc=datetime.now(timezone.utc).isoformat()))
    package=out.with_suffix('.tar.gz')
    with tarfile.open(package,'w:gz') as tar:
        for name in sorted(all_files):tar.add(out/name,arcname=name)
        tar.add(out/'package_manifest.json',arcname='package_manifest.json')
    receipt=dict(status='PASS',schema_version=schema['version'],cases=len(catalog),complete_cases=sum(c['scientific_tables'] for c in catalog),
        files=len(all_files),core_bytes=sum(c['core_bytes'] for c in catalog),archive_bytes=package.stat().st_size,archive_sha256=sha(package),
        source_library=str(lib),destination=str(out),archive=str(package),source_originals_modified=False)
    save(out.with_suffix('.receipt.json'),receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
