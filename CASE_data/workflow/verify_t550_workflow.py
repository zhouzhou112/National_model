"""One-shot workflow regression and exact remote duplicate-target stat checks."""
import hashlib
import json
from pathlib import Path

BASE=Path('/home/zz2/National_model_server');TOOLS=BASE/'paper_core_workflow_20261124'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    release='20261117_opsconservative_2060_v9a12_t44_m750_tol1e4_v1'
    rel=Path('by_case/OPS-Conservative/2060')/release/'core'
    old=BASE/'case_library_v2_20261123'/rel;new=BASE/'core_workflow_smoke_20261124'/rel
    skip={'00_identity.json','20_acceptance.json','90_remote_files.csv','91_remote_directories.json','92_provenance.json'}
    compared=[]
    for p in old.iterdir():
        if p.name not in skip:assert sha(p)==sha(new/p.name),p.name;compared.append(p.name)
    targets=json.loads((TOOLS/'remote_stat_targets.json').read_text());checks=[]
    for name,expected in targets.items():
        p=Path(name);relative=p.relative_to(BASE/'cloud_backup');root=BASE/'cloud_backup'/relative.parts[0]
        backup=json.loads((root/'backup_manifest.json').read_text());assert backup['status']=='COMPLETE'
        entry=next(x for x in backup['files'] if x['path']==str(p.relative_to(root)))
        assert entry['sha256']==expected['sha256'] and p.stat().st_size==expected['bytes']==entry['bytes']
        checks.append(dict(path=name,bytes=p.stat().st_size,sha256=entry['sha256'],backup_manifest_sha256=sha(root/'backup_manifest.json'),
            status='COMPLETE_MANIFEST_MATCH_AND_LIVE_STAT',hash_scope='SHA from previously verified COMPLETE manifest; no new remote full-file hash'))
    result=dict(status='PASS',workflow_case=release,scientific_files_identical=compared,scientific_file_count=len(compared),
                remote_targets=checks,remote_target_count=len(checks),solver_used=False)
    (TOOLS/'workflow_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',scientific_file_count=len(compared),remote_target_count=len(checks))))


if __name__=='__main__':main()
