"""Install supplied bytes in a fresh T550 runtime; never generate or repair data.

The transport supplies `expected`, the payload's per-file SHA/bytes manifest.
"""
from pathlib import Path
from itertools import zip_longest
import csv,datetime,gzip,hashlib,json,shutil,socket,tarfile

assert socket.gethostname().split('.')[0]=='t550'
root=Path('/home/zz2/National_model_server/ops_flex_resource_sensitivity_20261114')
archive=root/'baseline_install_payload.tar.gz';target=root/'baseline_runtime'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(8*1024**2),b''):h.update(x)
    return h.hexdigest()

assert sha(archive)=='1d004681780684247dda48f198cce339718abd2d43b62c3e7500d0d67e1e571e'
target.mkdir(exist_ok=False)
with tarfile.open(archive) as tf:
    for m in tf.getmembers():
        assert m.isfile() and (target/m.name).resolve().is_relative_to(target.resolve())
    tf.extractall(target)
for n,e in expected.items():
    assert (target/n).stat().st_size==e['bytes'] and sha(target/n)==e['sha256'],n
source=Path('/home/zz2/National_model_server/base_frozen_batch2_20261027/repo/data')
shutil.copytree(source,target/'repo/data',copy_function=shutil.copy2)
source_files={str(p.relative_to(source)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in source.rglob('*') if p.is_file()}
roots={};checks={}
for scenario in ['neutral','conservative','open']:
    data=target/'data_roots'/scenario
    shutil.copytree(source,data,copy_function=shutil.copy2)
    overrides=set()
    if scenario!='neutral':
        bundle=target/'inputs'/scenario;a=json.loads((bundle/'BUILD_AUDIT.json').read_text())
        for n,e in a['files'].items():
            assert sha(bundle/n)==e['sha256'] and (bundle/n).stat().st_size==e['bytes'],n
        for n in a['files']:
            if n.startswith(('load/','flexibility/')):
                p=data/n;p.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(bundle/n,p);overrides.add(n)
                assert sha(p)==a['files'][n]['sha256'] and p.stat().st_size==a['files'][n]['bytes'],n
    for n,e in source_files.items():
        if n not in overrides:
            assert sha(data/n)==e['sha256'] and (data/n).stat().st_size==e['bytes'],n
    with gzip.open(source/'load/hourly_load_2025_2060.csv.gz','rt') as f,gzip.open(data/'load/hourly_load_2025_2060.csv.gz','rt') as g:
        count=0
        for x,y in zip_longest(csv.DictReader(f),csv.DictReader(g)):
            assert x is not None and y is not None and x['demand_gw']==y['demand_gw']
            count+=1
    roots[scenario]=str(data)
    checks[scenario]=dict(all_installed_SHA_match=True,unchanged_other_files_SHA_match=True,demand_gw_text_identical=True,rows=count,overlaid_files=sorted(overrides))
report=dict(status='PASS',installed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=str(target),source_data_root=str(source),source_files=source_files,roots=roots,checks=checks,source_modified=False,payload_SHA=sha(archive))
(root/'installation_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
