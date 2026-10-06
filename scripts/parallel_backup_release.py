"""Verified, resumable SSH backup with bounded parallel byte-range transfers.

Requires an existing task-owned destination under /backups/. No credentials are
copied. Source is read-only. Destination can contain this task's partial copy.
Small files use one tar stream; large files use disjoint dd ranges. Reports live
outside the copied release. Integrity is checked after all ranges complete.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import time


def cmd(host, command):
    return ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30", "-o", "ConnectTimeout=20", host, command]


def relay(source_host, source_command, target_host, target_command):
    source = subprocess.Popen(cmd(source_host, source_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    target = subprocess.Popen(cmd(target_host, target_command), stdin=source.stdout, stderr=subprocess.PIPE)
    source.stdout.close()
    _, dst_err = target.communicate()
    src_err = source.stderr.read()
    src_rc = source.wait()
    if src_rc or target.returncode:
        raise RuntimeError(f"Transfer rc {src_rc}/{target.returncode}: {(src_err + dst_err).decode(errors='replace')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-host", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--destination-host", required=True)
    parser.add_argument("--destination-parent", required=True)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--reuse-dir", help="Existing read-only backup directory on the destination host")
    args = parser.parse_args()
    source = PurePosixPath(args.source_dir)
    parent = PurePosixPath(args.destination_parent)
    if not source.is_absolute() or not parent.is_absolute() or "backups" not in parent.parts or len(parent.parts) < 6:
        parser.error("Require specific absolute source and task-owned backups destination")
    if not 1 <= args.workers <= 8:
        parser.error("workers must be between 1 and 8")
    destination = parent / source.name
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    inventory_script = '''import json, hashlib, sys
from pathlib import Path
p=Path(sys.argv[1]).resolve()
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(4194304),b''): h.update(b)
 return h.hexdigest()
m=json.loads((p/'recovered_8760/result_manifest.json').read_text())
known={'recovered_8760/'+r['path']:r for r in m['files']}
rows=[]
for f in sorted(p.rglob('*')):
 if f.is_symlink(): raise ValueError('Source symlinks require explicit review')
 if not f.is_file(): continue
 n=f.relative_to(p).as_posix(); size=f.stat().st_size
 r=known.get(n)
 if r is not None and r['bytes']!=size: raise ValueError('Source manifest size mismatch: '+n)
 rows.append(dict(path=n,bytes=size,sha256=r['sha256'] if r else sha(f)))
print(json.dumps(rows))
'''
    inventory_path = args.evidence_dir / "release_inventory.json"
    if inventory_path.exists():
        records = json.loads(inventory_path.read_text())
    else:
        result = subprocess.run(cmd(args.source_host, "nice -n 10 python3 - " + shlex.quote(str(source))), input=inventory_script, text=True, capture_output=True, check=True)
        records = json.loads(result.stdout)
        inventory_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    total = sum(r["bytes"] for r in records)
    print(f"INVENTORY {len(records)} files {total} bytes", flush=True)
    for r in records:
        rel = PurePosixPath(r["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe inventory path")
    big = [r for r in records if r["bytes"] >= 16 * 1024**2]
    small = [r for r in records if r not in big]
    init_code = "import json,sys; from pathlib import Path; root=Path(sys.argv[1]); records=json.load(sys.stdin); [ (root/r['path']).parent.mkdir(parents=True,exist_ok=True) for r in records]"
    subprocess.run(cmd(args.destination_host, "python3 -c " + shlex.quote(init_code) + " " + shlex.quote(str(destination))), input=json.dumps(records), text=True, check=True)
    check_small = '''import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]);missing=[]
for r in json.load(sys.stdin):
 p=root/r['path']
 if not p.is_file() or p.stat().st_size!=r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:missing.append(r['path'])
print(json.dumps(missing))
'''
    small_result = subprocess.run(cmd(args.destination_host, "python3 -c " + shlex.quote(check_small) + " " + shlex.quote(str(destination))), input=json.dumps(small), text=True, capture_output=True, check=True)
    missing_small = json.loads(small_result.stdout)
    if missing_small:
        relay(args.source_host, "tar -C " + shlex.quote(str(source)) + " -cf - " + " ".join(map(shlex.quote, missing_small)),
              args.destination_host, "tar -C " + shlex.quote(str(destination)) + " -xpf -")
    print(f"SMALL_FILES_COMPLETE {len(small)} (transferred {len(missing_small)})", flush=True)
    progress_path = args.evidence_dir / "transfer_progress.json"
    done = set(json.loads(progress_path.read_text()).get("completed_ranges", [])) if progress_path.exists() else set()
    blocks = []
    chunk = 64 * 1024**2
    for r in big:
        for start in range(0, r["bytes"], chunk):
            count = min(chunk, r["bytes"] - start)
            key = f"{r['path']}:{start}:{count}"
            blocks.append((r, start, count, key))
    if args.reuse_dir:
        reuse_code = '''import json,sys,hashlib,shutil
from pathlib import Path
old=Path(sys.argv[1]); root=Path(sys.argv[2]); expected=json.load(sys.stdin); candidates={}
for name in ['primal_barx.npy','dual_barpi.npy']:
 p=old/'output/barrier_checkpoint'/name
 if not p.is_file():continue
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(4194304),b''):h.update(b)
 candidates[(p.stat().st_size,h.hexdigest())]=p
reused=[]
for r in expected:
 p=candidates.get((r['bytes'],r['sha256']))
 if p is None:continue
 target=root/r['path'];target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(p,target);reused.append(r['path'])
print(json.dumps(reused))
'''
        result = subprocess.run(cmd(args.destination_host, "nice -n 10 python3 -c " + shlex.quote(reuse_code) + " " + shlex.quote(args.reuse_dir) + " " + shlex.quote(str(destination))), input=json.dumps(big), text=True, capture_output=True, check=True)
        reused = set(json.loads(result.stdout))
        done.update(b[3] for b in blocks if b[0]["path"] in reused)
        print("HASH_VERIFIED_LOCAL_REUSE " + json.dumps(sorted(reused)), flush=True)
    def save_status(status):
        status["status"] = status.get("status", "IN_PROGRESS")
        status["source_dir"] = str(source)
        status["destination_dir"] = str(destination)
        progress_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
        write_code = "import sys; from pathlib import Path; Path(sys.argv[1]).write_text(sys.stdin.read(),encoding='utf-8')"
        subprocess.run(cmd(args.destination_host, "python3 -c " + shlex.quote(write_code) + " " + shlex.quote(str(parent / "backup_status.json"))), input=json.dumps(status, indent=2), text=True, check=True)
    save_status({"generated_at": datetime.now().astimezone().isoformat(), "completed_ranges": sorted(done),
                 "copied_bytes": sum(b[2] for b in blocks if b[3] in done) + sum(r["bytes"] for r in small), "total_bytes": total,
                 "range_count": len(blocks)})
    def copy_range(block):
        r, start, count, key = block
        src_cmd = f"dd if={shlex.quote(str(source / r['path']))} bs=1M skip={start} count={count} iflag=skip_bytes,count_bytes status=none"
        dst_cmd = f"dd of={shlex.quote(str(destination / r['path']))} bs=1M seek={start} oflag=seek_bytes conv=notrunc status=none"
        for attempt in range(3):
            try:
                relay(args.source_host, src_cmd, args.destination_host, dst_cmd)
                return key
            except RuntimeError:
                if attempt == 2: raise
                time.sleep(2)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(copy_range, b) for b in blocks if b[3] not in done]
        for future in as_completed(futures):
            done.add(future.result())
            copied = sum(b[2] for b in blocks if b[3] in done) + sum(r["bytes"] for r in small)
            progress = {"generated_at": datetime.now().astimezone().isoformat(), "copied_bytes": copied, "total_bytes": total,
                        "completed_ranges": sorted(done), "range_count": len(blocks), "elapsed_seconds": time.monotonic() - started}
            save_status(progress)
            print(f"TRANSFER {len(done)}/{len(blocks)} ranges, {copied/1024**3:.3f}/{total/1024**3:.3f} GiB", flush=True)
    verify_code = '''import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]); expected=json.load(sys.stdin); rows=[]
for r in expected:
 p=root/r['path']; h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(4194304),b''):h.update(b)
 rows.append(dict(path=r['path'],bytes=p.stat().st_size,sha256=h.hexdigest(),passed=p.stat().st_size==r['bytes'] and h.hexdigest()==r['sha256']))
print(json.dumps(dict(status='PASS' if all(r['passed'] for r in rows) else 'FAIL',files=rows)))
'''
    result = subprocess.run(cmd(args.destination_host, "nice -n 10 python3 -c " + shlex.quote(verify_code) + " " + shlex.quote(str(destination))), input=json.dumps(records), text=True, capture_output=True, check=True)
    report = json.loads(result.stdout)
    report.update(generated_at=datetime.now().astimezone().isoformat(), source_host=args.source_host,
                  source_dir=str(source), destination_host=args.destination_host, destination_dir=str(destination),
                  file_count=len(records), total_bytes=total, inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest())
    report_path = args.evidence_dir / "release_integrity_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save_status({"status": "COMPLETE" if report["status"] == "PASS" else "FAILED_INTEGRITY",
                 "generated_at": report["generated_at"], "completed_ranges": sorted(done), "copied_bytes": total,
                 "total_bytes": total, "range_count": len(blocks), "integrity_status": report["status"]})
    for path in [inventory_path, report_path]:
        subprocess.run(["scp", "-o", "BatchMode=yes", str(path), f"{args.destination_host}:{parent}/"], check=True)
    print("FINAL " + json.dumps({k: v for k, v in report.items() if k != "files"}), flush=True)
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
