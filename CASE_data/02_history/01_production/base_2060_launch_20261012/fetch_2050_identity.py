"""Read frozen 2050 source/state dependencies for local identity builds.

Only small source and state files are copied. Does not transfer result backups,
read credentials, write the cloud release, or operate completed jobs.
"""
from pathlib import Path
import base64,hashlib,io,json,subprocess,tarfile
HERE=Path(__file__).resolve().parent
REMOTE=r'''
from pathlib import Path
import base64,hashlib,io,json,tarfile
root=Path('/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260930_base2050_v9_t48_m750_tol1e4_v1')
buffer=io.BytesIO();hashes={}
with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
    for folder in ['repo','upstream_2040_bound_closed']:
        for path in sorted((root/folder).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':continue
            assert not path.is_symlink(),str(path)
            rel=path.relative_to(root).as_posix()
            hashes[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
            archive.add(path,arcname=rel,recursive=False)
print(json.dumps(dict(source=str(root),sha256=hashes,archive=base64.b64encode(buffer.getvalue()).decode())))
'''
def main():
    target=HERE/'frozen_2050_identity';assert not target.exists()
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','paracloud-bscc-a8','python3 -'],
        input=REMOTE,text=True,capture_output=True,encoding='utf-8',timeout=240)
    if p.returncode:raise RuntimeError(p.stderr)
    result=json.loads(p.stdout);data=base64.b64decode(result.pop('archive'));target.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        for member in archive.getmembers():
            dest=(target/member.name).resolve()
            assert dest.is_relative_to(target.resolve()) and member.isfile()
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(archive.extractfile(member).read())
    for name,digest in result['sha256'].items():assert hashlib.sha256((target/name).read_bytes()).hexdigest()==digest,name
    (HERE/'revision_6c/frozen_2050_source_sha256.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified frozen source/state files:',len(result['sha256']))
if __name__=='__main__':main()
