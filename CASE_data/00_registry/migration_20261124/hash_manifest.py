"""Hash an exact migration plan before/after same-volume moves; no recursive deletion."""
import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];WORK=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--after',action='store_true');args=ap.parse_args()
    plan=json.loads((WORK/'move_plan.json').read_text());before={}
    if args.after:before={r['path']:r for r in json.loads((WORK/'hashes_before.json').read_text())['files']}
    def one(row):
        path=ROOT/(row['destination'] if args.after else row['path'])
        if os.name=='nt':path=Path('\\\\?\\'+str(path))
        s=path.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)==(row['bytes'],row['mtime_ns'],row['file_id'],row['device']),str(path)
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(8<<20),b''):h.update(b)
        t=path.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino)
        digest=h.hexdigest()
        if args.after:assert digest==before[row['path']]['sha256'],str(path)
        return dict(path=row['path'],destination=row['destination'],bytes=s.st_size,file_id=s.st_ino,sha256=digest)
    started=time.time();rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(one,plan['files'])):
            rows.append(result)
            if (i+1)%1000==0:print(json.dumps(dict(files=i+1,total=len(plan['files']),seconds=round(time.time()-started,1))),flush=True)
    receipt=dict(status='PASS',phase='after' if args.after else 'before',files=rows,file_count=len(rows),
        bytes=sum(r['bytes'] for r in rows),seconds=time.time()-started,all_file_id_size_mtime_stable=True)
    (WORK/('hashes_after.json' if args.after else 'hashes_before.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'}),flush=True)


if __name__=='__main__':main()
