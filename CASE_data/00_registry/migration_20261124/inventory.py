"""Metadata-only inventory; never follow junctions or open credential files."""
import csv
import json
import os
import stat
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=Path(__file__).resolve().parent


def scan(root):
    files=[];links=[]
    for folder,dirs,names in os.walk(root,followlinks=False):
        kept=[]
        for name in dirs:
            p=Path(folder)/name;s=p.stat(follow_symlinks=False)
            if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
                links.append(str(p.relative_to(ROOT)))
            else:kept.append(name)
        dirs[:]=kept
        for name in names:
            p=Path(folder)/name;s=p.stat(follow_symlinks=False)
            if getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:
                links.append(str(p.relative_to(ROOT)));continue
            files.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=s.st_size,
                              mtime_ns=s.st_mtime_ns,file_id=s.st_ino,device=s.st_dev))
    return files,links


def main():
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
    files=[];links=[]
    for name in ['supplementary_materials/reviews','case_results']:
        f,l=scan(ROOT/name);files+=f;links+=l
    groups=defaultdict(list)
    for f in files:
        parts=f['path'].split('/');key='/'.join(parts[:3] if parts[0]=='supplementary_materials' else parts[:2]);groups[key].append(f)
    rows=[]
    for key,arr in groups.items():
        ext=Counter()
        for f in arr:ext[Path(f['path']).suffix.lower()]+=f['bytes']
        rows.append(dict(directory=key,files=len(arr),bytes=sum(f['bytes'] for f in arr),
             tracked_files=sum(f['path'] in tracked for f in arr),latest_mtime_ns=max(f['mtime_ns'] for f in arr),
             largest_file=max(arr,key=lambda f:f['bytes'])['path'],largest_file_bytes=max(f['bytes'] for f in arr),
             extension_bytes=dict(ext.most_common(6))))
    rows.sort(key=lambda x:x['bytes'],reverse=True)
    data=dict(as_of_utc=datetime.now(timezone.utc).isoformat(),directories=rows,files=files,reparse_points_skipped=links)
    (WORK/'inventory_before.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (WORK/'directory_inventory.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(dict(files=len(files),bytes=sum(f['bytes'] for f in files),directories=len(rows),links=len(links))))
    for r in rows[:25]:print(f'{r["bytes"]/2**30:.3f} GiB | {r["files"]:5d} | {r["directory"]}')


if __name__=='__main__':main()
