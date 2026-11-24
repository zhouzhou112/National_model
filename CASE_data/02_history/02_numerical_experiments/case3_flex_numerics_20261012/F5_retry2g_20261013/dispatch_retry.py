"""Run remotely through python -c with a JSON payload on stdin; no credentials."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

p = json.load(sys.stdin)
b = Path('/home/zz2/National_model_server')
data = b / 'probe_outputs/case3_flex_numerics_20261012_aef0cb7'
prior = b / 'probe_outputs/case3_flex_F5_direct_20261013_3e4a2fe'
old_source = prior / 'extension_source_f053057'
out = b / ('probe_outputs/case3_flex_F5_retry2g_20261013_' + p['commit'][:7])
source = out / ('source_' + p['commit'][:7])
assert not out.exists(), 'Do not duplicate an existing dispatch'
verified = {}
for root, name in ((data, 'bundle_manifest.json'), (old_source, 'extension_manifest.json')):
    manifest = json.loads((root / name).read_text())
    for item in manifest['files']:
        path = (root / item['path']).resolve()
        assert path.is_relative_to(root) and hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['path']
    verified[str(root)] = len(manifest['files'])
source.mkdir(parents=True)
for item in manifest['files']:
    assert item['path'].startswith('repo/')
    target = source / item['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(old_source / item['path'], target)
for name, item in p['files'].items():
    assert name in ('scripts/run_flex_full_diagnostic.py', 'scripts/run_flex_f5_retry_diagnostic.py')
    content = base64.b64decode(item['base64'])
    assert hashlib.sha256(content).hexdigest() == item['sha256']
    (source / 'repo' / name).write_bytes(content)
files = [dict(path=str(f.relative_to(source)), sha256=hashlib.sha256(f.read_bytes()).hexdigest(), bytes=f.stat().st_size)
         for f in sorted((source / 'repo').rglob('*')) if f.is_file()]
new_manifest = dict(diagnostic_commit=p['commit'], parent_source=str(old_source), verified_roots=verified,
                    overlay_files=list(p['files']), files=files)
manifest_path = source / 'extension_manifest.json'
manifest_path.write_text(json.dumps(new_manifest, indent=2) + '\n')
python = b / 'envs/cispo-2030-v1/bin/python'
script = source / 'repo/scripts/run_flex_f5_retry_diagnostic.py'
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
check = subprocess.run([str(python), str(script), '--help'], capture_output=True, text=True, env=env)
assert check.returncode == 0, check.stderr
cmd = [str(python), str(script), '--source', str(source), '--data-source', str(data), '--server-root', str(b),
       '--output', str(out), '--predecessor', str(prior), '--admission-deadline-utc', '2026-10-14T16:09:42Z']
with (out / 'retry_controller_console.log').open('x') as log:
    child = subprocess.Popen(cmd, cwd=source / 'repo', stdin=subprocess.DEVNULL, stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True, env=env)
receipt = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), pid=child.pid, command=cmd,
               source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
               diagnostic_commit=p['commit'], verified_roots=verified, overlay_files=list(p['files']),
               admission_gib=67, reserve_gib=2, previous_runs_unchanged=True)
(out / 'retry_dispatch_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(receipt=receipt, manifest=new_manifest)))
