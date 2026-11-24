"""Evidence-based duplicate candidates; no deletion or hardlink operations."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).resolve().parent


def write(name,rows,fields):
    with (WORK/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    hashed=json.loads((WORK/'hashes_after.json').read_text());assert hashed['status']=='PASS'
    grouped=defaultdict(list)
    for r in hashed['files']:
        if r['bytes']>=1024**2:grouped[(r['bytes'],r['sha256'])].append(r)
    duplicates=[];redundant=0;group_count=0
    for (size,digest),arr in sorted(grouped.items(),key=lambda x:x[0][0],reverse=True):
        if len(arr)<2:continue
        group_count+=1;redundant+=size*(len(arr)-1)
        for r in arr:duplicates.append(dict(group=group_count,path=r['destination'],bytes=size,sha256=digest,
              copies_in_group=len(arr),disposition='REVIEW_REDUNDANCY_NOT_DELETE_AUTHORIZATION',
              reason='Exact byte duplicate; separate historical/provenance roles still need preservation review'))
    remote=defaultdict(list)
    for p in (ROOT/'CASE_data/01_cases').rglob('90_remote_files.csv'):
        with p.open(encoding='utf-8',newline='') as f:
            for r in csv.DictReader(f):remote[(int(r['bytes']),r['sha256'])].append(r['path'])
    candidates=[]
    for r in hashed['files']:
        paths=remote.get((r['bytes'],r['sha256']))
        if r['bytes']>=32*1024**2 and paths:
            candidates.append(dict(local_path=r['destination'],bytes=r['bytes'],sha256=r['sha256'],
                t550_path=sorted(set(paths))[0],status='MATCHES_COMPLETE_BACKUP_MANIFEST_PENDING_STAT',
                deletion_authorized=False))
    write('duplicate_groups.csv',duplicates,['group','path','bytes','sha256','copies_in_group','disposition','reason'])
    write('large_remote_copy_candidates.csv',candidates,['local_path','bytes','sha256','t550_path','status','deletion_authorized'])
    targets={r['t550_path']:dict(bytes=r['bytes'],sha256=r['sha256']) for r in candidates}
    (WORK/'remote_stat_targets.json').write_text(json.dumps(targets,indent=2)+'\n',encoding='utf-8')
    summary=dict(status='PASS',migration_files=hashed['file_count'],migration_bytes=hashed['bytes'],
        exact_duplicate_groups_over_1MiB=group_count,duplicate_members=len(duplicates),
        logical_duplicate_bytes_upper_bound=redundant,large_files_with_complete_T550_manifest_match=len(candidates),
        local_large_remote_matched_bytes=sum(r['bytes'] for r in candidates),
        deletion_count=0,confirmed_disposable_entire_review_directories=0,
        limitations=['Duplicate logical bytes are not measured reclaimable disk space',
        'Remote-matched bytes overlap duplicate groups; never add the two totals',
        'Failed or superseded experiments preserve method-selection and diagnostic evidence'])
    (WORK/'redundancy_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))


if __name__=='__main__':main()
