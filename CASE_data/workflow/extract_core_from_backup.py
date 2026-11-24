"""T550 stage 1: verified complete backup + accepted sidecar -> compact core staging.

Request format is documented in WORKFLOW_ZH.md. This never performs acceptance,
optimization or a new transfer of full results. It stops on identity or schema drift.
"""
import argparse
import json
from pathlib import Path

import flat_core_engine as engine


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    request=json.loads(Path(a.request).read_text());out=Path(a.out).resolve()
    assert not out.exists(),'New versioned staging required'
    records=[];inventory={}
    for row in request['cases']:
        release=row['release'];assert '/' not in release and '\\' not in release and release not in ('.','..')
        backup_root=engine.BASE/'cloud_backup'/release;manifest_path=backup_root/'backup_manifest.json'
        backup=json.loads(manifest_path.read_text());assert backup['status']=='COMPLETE'
        assert backup.get('source_unchanged_after_transfer') is True
        expected=row['source_result_manifest_sha256'];assert backup['source_result_manifest_sha256']==expected
        assert engine.sha(backup_root/'output_8760/result_manifest.json')==expected
        accepted=Path(row['acceptance_record']).resolve()
        assert accepted.is_relative_to(engine.BASE) and accepted.suffix=='.json'
        assert any(s in accepted.name.lower() for s in ('acceptance','relative_v1')),'Explicit acceptance record required'
        raw=accepted.read_bytes();assert len(raw)<=1048576 and engine.sha(accepted)==row['acceptance_sha256']
        doc=json.loads(raw)
        if 'release' in doc:assert doc['release']==release
        references=doc.get('source_sha256') or doc.get('source_evidence',{}).get('source_sha256',{})
        lookup={f['path']:f['sha256'] for f in backup['files']};n=0
        for key,value in references.items():
            if '/output_8760/' in key:key='output_8760/'+key.split('/output_8760/',1)[1]
            elif not key.startswith('/'):key='output_8760/'+key
            if key in lookup:assert lookup[key]==value;n+=1
        assert n or doc.get('release')==release,'No acceptance/source identity connection'
        catalog=dict(case=row['legacy_case'],year=int(row['year']),release=release,kind=row.get('kind','COMPLETED_PRODUCTION'),
                     acceptance_status=row['acceptance_status'])
        records.append(dict(catalog=catalog,accepted_evidence=dict(source_path=str(accepted),sha256=engine.sha(accepted),bytes=len(raw),document=doc)))
        inventory[release]=dict(backup_manifest_sha256=engine.sha(manifest_path),backup_status='COMPLETE',source_result_manifest_sha256=expected)
    out.mkdir(parents=True)
    engine.DEST=out;engine.INPUT=dict(remote_inventory=dict(cases=inventory))
    schemas={};cases=[engine.analyze(item,schemas) for item in records]
    engine.save(out/'catalog.json',dict(cases=cases))
    engine.save(out/'STAGING_COMPLETE.json',dict(status='PASS',source='T550 complete backups and declared acceptance SHA',
        cases=len(cases),schemas=schemas,request_sha256=engine.sha(Path(a.request)),solver_loaded=False))
    print(json.dumps(dict(status='PASS',cases=len(cases),directory=str(out))))


if __name__=='__main__':main()
