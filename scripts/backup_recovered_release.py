"""Stream a completed release over existing SSH aliases; never copy credentials.

relay mode transfers a complete release into a new task-owned backup parent.
local mode downloads selected manifest-listed analysis inputs into a new folder.
Remote source files are read-only. Tar is streamed as bytes (not a shell text pipe).
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import tarfile
from pathlib import Path, PurePosixPath


def ssh(host: str, command: str, **kwargs):
    return subprocess.Popen(
        ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=30", host, command],
        **kwargs,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-host", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--destination-host")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    source = PurePosixPath(args.source_dir)
    if not source.is_absolute() or len(source.parts) < 5:
        parser.error("A specific absolute source directory is required")
    if args.destination_host:
        destination = PurePosixPath(args.destination)
        if not destination.is_absolute() or "backups" not in destination.parts:
            parser.error("Destination must be a specific absolute backups directory")
        src_cmd = f"tar -C {shlex.quote(str(source.parent))} -cf - {shlex.quote(source.name)}"
        dst_cmd = f"test -d {shlex.quote(str(destination))} && tar -C {shlex.quote(str(destination))} -xpf -"
        src = ssh(args.source_host, src_cmd, stdout=subprocess.PIPE)
        dst = ssh(args.destination_host, dst_cmd, stdin=src.stdout)
        src.stdout.close()
        dst_rc, src_rc = dst.wait(), src.wait()
        print(json.dumps({"source_returncode": src_rc, "destination_returncode": dst_rc}), flush=True)
        if src_rc or dst_rc:
            raise SystemExit(1)
    else:
        if args.manifest is None:
            parser.error("--manifest is required for selected local analysis download")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        names = [r["path"] for r in manifest["files"]
                 if "/" not in r["path"] and r["bytes"] < 10_000_000
                 and r["path"].endswith((".json", ".csv", ".csv.gz"))]
        names.append("result_manifest.json")
        dst = Path(args.destination).resolve()
        dst.mkdir(parents=True, exist_ok=True)
        src_cmd = f"tar -C {shlex.quote(str(source))} -cf - " + " ".join(map(shlex.quote, names))
        src = ssh(args.source_host, src_cmd, stdout=subprocess.PIPE)
        with tarfile.open(fileobj=src.stdout, mode="r|") as archive:
            for member in archive:
                if member.name not in names or not member.isfile():
                    raise ValueError(f"Unexpected archive member: {member.name}")
                archive.extract(member, path=dst, filter="data")
        rc = src.wait()
        print(json.dumps({"source_returncode": rc, "files": len(names)}), flush=True)
        if rc:
            raise SystemExit(rc)


if __name__ == "__main__":
    main()
