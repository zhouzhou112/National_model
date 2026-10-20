"""One-shot checksummed pull of completed cloud outputs, executed on T550.

Usage: python3 backup_completed_cloud.py plan|run --config /path/to/config.json
Reuses the 2026-10-12 tiered rsync/SHA workflow. No polling, source writes,
credential reads, deletion, or scientific acceptance changes. plan refuses an
existing operation/destination; run resumes only that saved plan under locks.
Outputs: operation plan/status/logs and per-release verified backup_manifest.
"""
from pathlib import Path, PurePosixPath
from collections import defaultdict
from datetime import datetime, timezone
import argparse
try:
    import fcntl
except ImportError:  # Read-only unit tests can run on Windows.
    fcntl = None
import hashlib
import json
import os
import shlex
import shutil
import socket
import re
import subprocess

DEST = OP = SOURCE = SSH_CONFIG = SSH = RELEASES = None
MIN_FREE_FRACTION = 0.30
AUTHORIZATION = ''

def configure(config):
    """Load explicit paths/identities; never reuse the historical operation implicitly."""
    global DEST, OP, SOURCE, SSH_CONFIG, SSH, RELEASES, MIN_FREE_FRACTION, AUTHORIZATION
    releases = config['releases']
    assert releases and len(releases) == len(set(releases)), 'Unique releases required'
    operation = config['operation']
    for item in [operation] + releases:
        assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', item) and item not in ['.', '..'], item
    for key in ['destination', 'source', 'ssh_config']:
        assert PurePosixPath(config[key]).is_absolute(), key
    minimum = float(config.get('minimum_free_fraction', 0.30))
    assert 0.30 <= minimum < 1, 'Keep at least the established 30% reserve'
    DEST = Path(config['destination'])
    OP = DEST / '_operations' / operation
    SOURCE = config['source'].rstrip('/')
    SSH_CONFIG = config['ssh_config']
    SSH = ['ssh', '-F', SSH_CONFIG, 'paracloud-backup']
    RELEASES = releases
    MIN_FREE_FRACTION = minimum
    AUTHORIZATION = config['authorization']


INVENTORY = r'''
from pathlib import Path, PurePosixPath
import json, hashlib, socket, subprocess
active = subprocess.check_output(['squeue','-u',subprocess.check_output(['id','-un'],universal_newlines=True).strip(),'-h','-o','%Z'],universal_newlines=True).splitlines()
result={'hostname':socket.gethostname(),'releases':{}}
for release in releases:
    root=Path(source)/release
    assert str(root) not in active and str(root/'repo') not in active, 'Release still active: '+release
    assert (root/'batch_exit.json').is_file(), 'Missing terminal batch marker: '+release
    out=root/'output_8760'
    raw=(out/'result_manifest.json').read_bytes()
    manifest=json.loads(raw)
    entries={x['path']:x for x in manifest['files']}
    assert len(entries)==len(manifest['files'])
    assert (out/'solve_report.json').is_file(), 'Missing solve report'  # No QC/OPTIMAL gate for backups.
    assert json.loads((out/'preservation_report.json').read_text())['status']=='COMPLETE'
    for name in entries:
        rel=PurePosixPath(name)
        assert not rel.is_absolute() and '..' not in rel.parts, name
        assert (out/name).is_file(), name
    paths=list(out.rglob('*'))
    for pattern in ['release_files.sha256','source_identity.json','launch_config.json',
                    'cloud_source_repo_sha256.json','base_*.sbatch','slurm-*.out','slurm-*.err',
                    'stdout.log','stderr.log','held_submission.json','release_record.json',
                    'continuation.sbatch','case3*.sbatch','batch_exit.json','release_job.json',
                    'source_screen.csv','release_files.sha256','resource_usage.txt']:
        paths.extend(root.glob(pattern))
    records=[]
    for p in sorted(set(paths)):
        if p.is_dir(): continue
        assert not p.is_symlink(), 'Refuse unreviewed symlink '+str(p)
        assert p.is_file(), str(p)
        rel=str(p.relative_to(root))
        assert not any(x in p.name.lower() for x in ['private_key','gurobi.lic','credential'])
        st=p.stat()
        name=str(p.relative_to(out)) if out in p.parents else None
        if name in entries:
            record=entries[name]
            assert st.st_size==record['bytes'], rel
            digest=record['sha256']; origin='result_manifest.json'
        else:
            assert st.st_size<=32*1024*1024, 'Unmanifested large source requires separate audit: '+rel
            digest=hashlib.sha256(p.read_bytes()).hexdigest(); origin='source_sha256_read'
        tier='T3' if rel=='output_8760/model_archive/original.mps.gz' else (
             'T2' if rel.startswith('output_8760/barrier_checkpoint/') else 'T1')
        records.append({'path':rel,'bytes':st.st_size,'sha256':digest,'sha_source':origin,
                        'mtime_ns':st.st_mtime_ns,'tier':tier})
    result['releases'][release]={'result_manifest_sha256':hashlib.sha256(raw).hexdigest(),
                                'files':records}
print(json.dumps(result))
'''

def now():
    return datetime.now(timezone.utc).isoformat()

def write(path, data):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def inventory():
    code='source='+repr(SOURCE)+'\nreleases='+repr(RELEASES)+'\n'+INVENTORY
    p=subprocess.run(SSH+['python3 -'],input=code,text=True,capture_output=True,timeout=180)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)

def plan():
    assert not OP.exists(), 'Review existing operation; never create duplicate transfer'
    assert all(not (DEST/r).exists() for r in RELEASES), 'Never overwrite an existing backup'
    inv=inventory()
    disk=shutil.disk_usage(DEST if DEST.exists() else DEST.parent)
    total=sum(f['bytes'] for r in inv['releases'].values() for f in r['files'])
    keep_t3=True
    assert (disk.free-total)/disk.total >= MIN_FREE_FRACTION, 'Insufficient space for complete backup; no silent T3 deferral'
    inv.update(created_at_utc=now(),destination=str(DEST),ssh_config=SSH_CONFIG,
               all_tiers_bytes=total,disk_total_bytes=disk.total,disk_free_bytes=disk.free,
               projected_free_fraction_all_tiers=(disk.free-total)/disk.total,
               t3_included=keep_t3,source=SOURCE,
               authorization=AUTHORIZATION)
    OP.mkdir(parents=True)
    write(OP/'backup_plan.json',inv)
    for release in RELEASES:
        (DEST/release).mkdir()
    print(json.dumps({k:v for k,v in inv.items() if k!='releases'},indent=2),flush=True)

def run():
    assert fcntl is not None, 'Transfer requires Linux flock'
    with (DEST/'_operations/transfer_global.lock').open('a') as global_lock, (OP/'transfer.lock').open('a') as lock:
        fcntl.flock(global_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        p=json.loads((OP/'backup_plan.json').read_text())
        assert p['destination']==str(DEST) and p['source']==SOURCE
        assert set(p['releases'])==set(RELEASES)
        status={'started_at_utc':now(),'status':'RUNNING','stages':[],'completed_bytes':0}
        write(OP/'transfer_status.json',status)
        try:
            for tier in ['T1','T2','T3']:
                for release in RELEASES:
                    files=[f for f in p['releases'][release]['files'] if f['tier']==tier]
                    if not files: continue
                    for f in files:
                        rel=PurePosixPath(f['path'])
                        assert not rel.is_absolute() and '..' not in rel.parts
                    remaining=sum(f['bytes'] for r in p['releases'].values() for f in r['files'])-status['completed_bytes']
                    disk=shutil.disk_usage(DEST)
                    assert (disk.free-remaining)/disk.total>=MIN_FREE_FRACTION, 'Disk reserve changed; stop safely'
                    listing=OP/(release+'_'+tier+'.files')
                    listing.write_text(''.join(f['path']+'\n' for f in files))
                    label=release+'_'+tier
                    stage={'release':release,'tier':tier,'bytes':sum(f['bytes'] for f in files),
                           'file_count':len(files),'started_at_utc':now(),'status':'TRANSFERRING'}
                    status['stages'].append(stage)
                    write(OP/'transfer_status.json',status)
                    print(json.dumps(stage),flush=True)
                    cmd=['rsync','-rt','--no-owner','--no-group','--protect-args',
                         '--partial-dir=.rsync-partial','--info=progress2','--stats',
                         '--files-from='+str(listing),'-e',shlex.join(SSH[:-1]),
                         'paracloud-backup:'+SOURCE+'/'+release+'/',str(DEST/release)+'/']
                    with (OP/(label+'.log')).open('a') as log:
                        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
                    assert result.returncode==0, 'rsync failed; see '+label+'.log'
                    stage['status']='VERIFYING_SHA256'
                    write(OP/'transfer_status.json',status)
                    for f in files:
                        target=DEST/release/f['path']
                        assert target.stat().st_size==f['bytes'], str(target)
                        assert digest(target)==f['sha256'], 'SHA mismatch '+str(target)
                    stage.update(status='VERIFIED',finished_at_utc=now())
                    status['completed_bytes']+=stage['bytes']
                    write(OP/'transfer_status.json',status)
                    print(json.dumps(stage),flush=True)
            final=inventory()
            for release in RELEASES:
                before=p['releases'][release]
                after=final['releases'][release]
                assert before['result_manifest_sha256']==after['result_manifest_sha256']
                afterfiles={f['path']:f for f in after['files']}
                for f in before['files']:
                    assert afterfiles[f['path']]==f, 'Source changed '+release+'/'+f['path']
                manifest={'status':'COMPLETE','verified_at_utc':now(),'source':SOURCE+'/'+release,
                          'destination':str(DEST/release),'source_unchanged_after_transfer':True,
                          'source_result_manifest_sha256':before['result_manifest_sha256'],
                          'files':before['files'],'deferred_files':before.get('deferred_files',[]),
                          'verification':'Every target bytes/SHA256 equals source archive manifest or source-side SHA256',
                          'scope':'Full output_8760 including T1/T2/T3 plus explicit root launch/log metadata; no input datasets or repo copy',
                          'scientific_acceptance':'BACKUP_ONLY; original QC and author status preserved without alteration'}
                write(DEST/release/'backup_manifest.json',manifest)
            status.update(status='COMPLETE',finished_at_utc=now(),source_unchanged=True,
                          disk_free_bytes=shutil.disk_usage(DEST).free)
            write(OP/'transfer_status.json',status)
            print(json.dumps(status,indent=2),flush=True)
        except Exception as error:
            status.update(status='ERROR',error=repr(error),failed_at_utc=now())
            write(OP/'transfer_status.json',status)
            raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['plan','run'])
    parser.add_argument('--config', required=True, type=Path, help='JSON operation, releases, source/destination and SSH config paths')
    args=parser.parse_args()
    configure(json.loads(args.config.read_text(encoding='utf-8')))
    assert socket.gethostname().split('.')[0]=='t550', 'Only run on verified t550'
    {'plan':plan,'run':run}[args.phase]()
