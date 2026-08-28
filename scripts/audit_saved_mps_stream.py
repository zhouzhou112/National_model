"""Stream a saved MPS locally, without Gurobi or an in-memory LP.

Local: --input original.mps[.gz] --output-dir NEW_DIR
Remote read only: --ssh-host HOST --remote-path ABSOLUTE_MPS_GZ
  --expected-sha256 HASH --expected-bytes N --output-dir NEW_DIR
The remote command is only cat. Parsing/decompression/hashing are local.
No copying into, building on, or solving on a server. COMPLETE requires ENDATA,
gzip CRC (if compressed), source byte count/hash and optional LP size checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cispo_model.mps_stream_audit import audit_lines


class HashReader(io.RawIOBase):
    def __init__(self, source):
        self.source = source
        self.digest = hashlib.sha256()
        self.bytes_read = 0

    def readable(self):
        return True

    def readinto(self, target):
        data = self.source.read(len(target))
        if not data:
            return 0
        self.digest.update(data)
        self.bytes_read += len(data)
        target[:len(data)] = data
        return len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--ssh-host")
    parser.add_argument("--remote-path")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-bytes", type=int)
    parser.add_argument("--expected-rows", type=int)
    parser.add_argument("--expected-columns", type=int)
    parser.add_argument("--expected-nonzeros", type=int)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.input) == bool(args.ssh_host):
        parser.error("Choose exactly one local input or SSH source")
    if args.ssh_host and (not args.remote_path or not args.remote_path.startswith("/")
                         or not args.expected_sha256 or args.expected_bytes is None):
        parser.error("Remote read requires absolute path, expected SHA256 and bytes")
    if args.expected_sha256 and (len(args.expected_sha256) != 64 or
                                any(c not in "0123456789abcdefABCDEF" for c in args.expected_sha256)):
        parser.error("Invalid expected SHA256")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    status = {"status": "STARTING", "pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat(),
              "source": str(args.input.resolve()) if args.input else f"{args.ssh_host}:{args.remote_path}",
              "expected_sha256": args.expected_sha256, "expected_bytes": args.expected_bytes,
              "scope": "LOCAL_STREAM_AUDIT_NO_BUILD_NO_PRESOLVE_NO_OPTIMIZE"}
    def save_status():
        status.update(updated_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started)
        temporary = out / "status.tmp.json"
        temporary.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(out / "status.json")
    save_status()
    process = source = stderr_file = buffered = None
    try:
        if args.input:
            source = args.input.open("rb")
            input_before = args.input.stat()
            compressed = args.input.name.endswith(".gz")
        else:
            stderr_file = (out / "ssh.stderr.log").open("wb")
            process = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                                        "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
                                        args.ssh_host, "cat -- " + shlex.quote(args.remote_path)],
                                       stdout=subprocess.PIPE, stderr=stderr_file)
            source = process.stdout
            status["ssh_pid"] = process.pid
            compressed = args.remote_path.endswith(".gz")
        reader = HashReader(source)
        buffered = io.BufferedReader(reader, buffer_size=1024 * 1024)
        stream = gzip.GzipFile(fileobj=buffered) if compressed else buffered
        status["status"] = "RUNNING"
        save_status()
        def progress(entry):
            status.update(entry, source_bytes_read=reader.bytes_read)
            try:
                import psutil
                status["local_rss_bytes"] = psutil.Process().memory_info().rss
            except ImportError:
                pass
            save_status()
        result = audit_lines(stream, progress=progress)
        if process and process.wait(timeout=30) != 0:
            raise ValueError("SSH source read failed; see ssh.stderr.log")
        if args.input:
            after = args.input.stat()
            if (input_before.st_size, input_before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError("Input changed during audit")
        digest = reader.digest.hexdigest()
        if args.expected_sha256 and digest != args.expected_sha256.lower():
            raise ValueError("Input SHA256 mismatch; result must not be used")
        if args.expected_bytes is not None and reader.bytes_read != args.expected_bytes:
            raise ValueError("Input byte count mismatch")
        for expected, observed in ((args.expected_rows, result["constraints"]),
                                   (args.expected_columns, result["columns_contiguous_mps"]),
                                   (args.expected_nonzeros, result["ranges"]["matrix"]["nonzero_entries"])):
            if expected is not None and expected != observed:
                raise ValueError(f"LP size mismatch: expected {expected}, observed {observed}")
        result.update(input_sha256=digest, input_bytes=reader.bytes_read,
                      elapsed_seconds=time.monotonic()-started, scientifically_accepted=False)
        (out / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
        status.update(status="COMPLETE", input_sha256=digest, source_bytes_read=reader.bytes_read,
                      constraints=result["constraints"], columns=result["columns_contiguous_mps"],
                      matrix_nonzeros=result["ranges"]["matrix"]["nonzero_entries"])
        save_status()
        print(json.dumps(status, ensure_ascii=False))
    except BaseException as error:
        status.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        save_status()
        raise
    finally:
        if buffered:
            buffered.close()
        if source:
            source.close()
        if process and process.poll() is None:
            process.terminate()  # Our local cat/SSH client only, never a server solver.
            process.wait(timeout=15)
        if stderr_file:
            stderr_file.close()


if __name__ == "__main__":
    main()
