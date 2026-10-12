"""Verify LF-equivalent historical sidecars and store exact source byte copies.

Windows read_text normalizes CRLF, so semantic/text equality alone does not
prove original byte SHA equality. Preserve existing canonical server sidecars;
write immutable source_bytes/ copies matching the locally referenced SHA.
"""
from pathlib import Path
import base64
import hashlib
import json
import subprocess
from assess_on_t550 import SSH

HERE=Path(__file__).resolve().parent


def main():
    records={}
    for year in [2030,2040,2050]:
        folder=HERE/'assessments'/str(year)
        evidence=json.loads((folder/'evidence_manifest.json').read_text(encoding='utf-8'))
        raw=(folder/'acceptance_relative_v1.json').read_bytes()
        records[evidence['sidecar']+'/acceptance_relative_v1.json']=dict(
            planning_year=year,base64=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
    code='records='+repr(records)+'\n'+'''
from pathlib import Path
import base64,hashlib,json
results=[]
for name,record in records.items():
    path=Path(name);assert path.parent.name=='acceptance_relative_v1_20261012'
    source=base64.b64decode(record['base64']);canonical=path.read_bytes()
    assert source.replace(b'\\r\\n',b'\\n')==canonical.replace(b'\\r\\n',b'\\n')
    exact=path.parent/'source_bytes'/path.name
    exact.parent.mkdir(exist_ok=True)
    if exact.exists():assert exact.read_bytes()==source
    else:exact.write_bytes(source)
    digest=hashlib.sha256(exact.read_bytes()).hexdigest();assert digest==record['sha256']
    results.append(dict(planning_year=record['planning_year'],canonical_path=str(path),
        canonical_sha256=hashlib.sha256(canonical).hexdigest(),canonical_lf_content_equal=True,
        source_bytes_path=str(exact),local_sha256=record['sha256'],server_source_bytes_sha256=digest))
print(json.dumps(results))
'''
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=60)
    p.check_returncode()
    result=dict(status='VERIFIED_BYTES_WITH_CANONICAL_LF',
        historical_canonical_files_unchanged=True,records=json.loads(p.stdout),
        correction='Earlier VERIFIED used read_text equality; canonical LF and local CRLF had different byte SHA. Exact immutable source_bytes copies now verified.')
    (HERE/'acceptance_byte_sync_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (HERE/'acceptance_sync_status.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
