"""Inventory Git drift using file metadata; never open credential candidates.

Run from repository root. Produces JSON counts and a local-only TSV inventory.
No file is staged, removed, committed, or pushed by this script.
"""
from pathlib import Path
import collections
import csv
import json
import subprocess

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def paths(*args):
    return [p.decode('utf-8') for p in subprocess.check_output(['git',*args,'-z'],cwd=ROOT).split(b'\0') if p]

def category(s):
    p=Path(s);parts=p.parts
    if s.startswith(('output/','supplementary_materials/output/')):return 'local_runtime_and_outputs'
    if s.startswith('.tmp') or '/.chart-data-' in s or '/.codex_tmp/' in s:return 'temporary'
    if 'ssh' in p.name.lower() or p.suffix in {'.lic','.key','.pem'} or p.name in {'.env','credentials.json'}:return 'connection_or_credential_candidate_not_read'
    if parts[0] in {'cispo_model','config','scripts','tests'}:return 'code_config_tests'
    if s.startswith('supplementary_materials/reviews/'):return 'review_evidence'
    if s.startswith('supplementary_materials/modules/'):return 'manuscript_modules'
    if s.startswith('supplementary_materials/'):return 'other_supplementary'
    return 'root_docs_or_other'

def main():
    rows=[]
    for kind,files in [('modified_tracked',paths('diff','--name-only')),('untracked',paths('ls-files','--others','--exclude-standard'))]:
        for s in files:
            p=ROOT/s
            rows.append(dict(path=s,kind=kind,category=category(s),bytes=p.stat().st_size if p.is_file() else 0))
    summary={}
    for row in rows:
        key=row['kind']+'/'+row['category'];v=summary.setdefault(key,dict(files=0,bytes=0));v['files']+=1;v['bytes']+=row['bytes']
    with (HERE/'inventory_local.tsv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','kind','category','bytes'],delimiter='\t');w.writeheader();w.writerows(rows)
    (HERE/'inventory_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
