"""Download completed audit outputs (excluding name scratch), verify every SHA.

Run after all three audit jobs complete: python collect.py. No job mutation,
new submission, model parsing, model copies or credentials are involved.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
receipt=json.loads((HERE/'submission_receipt.json').read_text())
code='from pathlib import Path\nimport json,sys,tarfile\nroot=Path('+repr(receipt['root'])+')\njobs='+repr(receipt['jobs'])+'\n'
code+='''
paths=[]
for year,job in jobs.items():
    folder=root/('result_'+year)
    assert (folder/('outputs_manifest_'+year+'.json')).exists(), 'Incomplete outputs '+year
    summary=json.loads((folder/('audit_summary_'+year+'.json')).read_text())
    assert summary['validations'].startswith('PASS')
    paths.extend(p for p in folder.iterdir() if p.is_file() and p.suffix!='.scratch')
    paths.extend(root/('tiny_bound_{}-{}.{}'.format(year,job,suffix)) for suffix in ['out','err'])
paths.extend(root/n for n in ['submission_receipt.json','uploaded_sha256.json'])
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
    for p in sorted(paths): archive.add(str(p),arcname=str(p.relative_to(root)),recursive=False)
'''
target=HERE/'cloud_results';target.mkdir(exist_ok=False)
archive=HERE/'cloud_results.tar.gz'
with archive.open('xb') as f:
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],input=code.encode(),stdout=f,stderr=subprocess.PIPE,timeout=600)
(HERE/'collection.stderr.log').write_bytes(p.stderr);p.check_returncode()
with tarfile.open(archive,'r:gz') as tf:
    for item in tf:
        dest=target/item.name
        if not dest.resolve().is_relative_to(target.resolve()) or not item.isfile():
            raise ValueError('Unexpected archive member: '+item.name)
        dest.parent.mkdir(parents=True,exist_ok=True)
        with tf.extractfile(item) as source,dest.open('xb') as sink:
            for block in iter(lambda:source.read(1<<20),b''):sink.write(block)
verified={}
for year in receipt['jobs']:
    folder=target/('result_'+year)
    manifest=json.loads((folder/('outputs_manifest_'+year+'.json')).read_text())
    for name,expected in manifest.items():
        p=folder/name;h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(8<<20),b''):h.update(block)
        assert h.hexdigest()==expected['sha256'] and p.stat().st_size==expected['bytes'],name
        verified[str(p.relative_to(HERE))]=expected
(HERE/'collection_verified.json').write_text(json.dumps(verified,indent=2),encoding='utf-8')
print('PASS: verified {} result files; package {} bytes'.format(len(verified),archive.stat().st_size))
