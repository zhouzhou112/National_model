"""Finite four-connection read-only transfer of completed Base pricing archives.

Usage: --year 2040|2050 --output NEW_DIRECTORY. Remote work is bounded file I/O,
not LP parsing or optimization. Every chunk, partial file and error is retained.
No retries, scheduler, watcher, credentials or remote writes.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from fetch_pricing_archive import RELEASES, SMALL, HOST, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--year', type=int, choices=(2040, 2050), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    root = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/' + RELEASES[a.year] + '/output_8760'
    ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', HOST]
    code = 'root=' + repr(root) + '\nnames=' + repr(SMALL) + '\n' + '''import pathlib,json,hashlib,base64
root=pathlib.Path(root);out={}
for name in names:
 b=(root/name).read_bytes()
 out[name]={'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(out))
'''
    reply = subprocess.run(ssh + ['python3 -'], input=code.encode(), capture_output=True, check=True)
    evidence = {}
    for name, item in json.loads(reply.stdout).items():
        data = base64.b64decode(item['base64'])
        assert hashlib.sha256(data).hexdigest() == item['sha256']
        target = out / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        evidence[name] = dict(sha256=item['sha256'], bytes=len(data), verified=True)
    archive = json.loads((out / SMALL[0]).read_text())
    checkpoint = json.loads((out / SMALL[1]).read_text())
    mps = [v for v in archive['files'] if v['path'] == 'original.mps.gz']
    assert len(mps) == 1
    files = [('model_archive/original.mps.gz', mps[0]),
             ('barrier_checkpoint/dual_barpi.npy', checkpoint['vectors']['dual'])]
    assert shutil.disk_usage(out).free > 2 * sum(v['bytes'] for _, v in files) + 10 * 2**30
    transfers = []
    for name, meta in files:
        size = meta['bytes']
        chunks = out / (Path(name).name + '_chunks')
        chunks.mkdir()

        def transfer(i):
            start, end = size * i // 4, size * (i + 1) // 4
            target = chunks / ('part_' + str(i))
            remote = ('import sys\n'
                      'f=open(' + repr(root + '/' + name) + ',"rb")\n'
                      'f.seek(' + str(start) + ')\nn=' + str(end - start) + '\n'
                      'while n:\n b=f.read(min(n,1048576))\n'
                      ' if not b: raise EOFError("source truncated")\n'
                      ' sys.stdout.buffer.write(b)\n n-=len(b)\n')
            with target.open('xb') as stream, (chunks / ('part_' + str(i) + '.stderr')).open('xb') as err:
                subprocess.run(ssh + ['python3 -'], input=remote.encode('ascii'),
                               stdout=stream, stderr=err, check=True)
            assert target.stat().st_size == end - start
            return dict(index=i, offset=start, bytes=end-start, sha256=sha(target))

        print('Downloading four ranges:', name, size, flush=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            parts = list(pool.map(transfer, range(4)))
        target = out / name
        with target.open('xb') as stream:
            for part in parts:
                with (chunks / ('part_' + str(part['index']))).open('rb') as source:
                    shutil.copyfileobj(source, stream, length=4*1024*1024)
        assert target.stat().st_size == size and sha(target) == meta['sha256'], name
        evidence[name] = dict(sha256=meta['sha256'], bytes=size, verified=True)
        transfers.append(dict(path=name, parts=parts))
        print('SHA VERIFIED:', name, flush=True)
    result = dict(source_release=RELEASES[a.year], source=root, files=evidence,
                  started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                  transfer='four bounded read-only byte ranges; source manifest SHA verification',
                  chunks_preserved=transfers)
    (out / 'download_identity.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('VERIFIED', a.year, flush=True)


if __name__ == '__main__':
    main()
