"""Run only this experiment's subprocess with a bounded wall/RAM guard.

No existing processes are controlled. Memory pressure terminates ONLY the
new process group created here, never the cloud Base or other users' work.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import psutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--control",type=Path,required=True)
p.add_argument("--wall-seconds",type=int,default=7200)
p.add_argument("command",nargs=argparse.REMAINDER)
a=p.parse_args()
a.control.mkdir(parents=True,exist_ok=False)
command=a.command[1:] if a.command[0]=="--" else a.command
started=time.monotonic(); reason=None; peak=0; min_available=1e100
with (a.control/"stdout.log").open("w") as out, (a.control/"stderr.log").open("w") as err:
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    (a.control/"pid.json").write_text(json.dumps(dict(pid=child.pid,command=command)))
    with (a.control/"resources.jsonl").open("w",buffering=1) as f:
        while child.poll() is None:
            vm=psutil.virtual_memory();rss=0
            try:
                proc=psutil.Process(child.pid)
                rss=sum(x.memory_info().rss for x in [proc]+proc.children(recursive=True))
            except psutil.Error:pass
            peak=max(peak,rss);min_available=min(min_available,vm.available)
            elapsed=time.monotonic()-started
            f.write(json.dumps(dict(elapsed=elapsed,rss=rss,available=vm.available,load=os.getloadavg()))+"\n")
            if vm.available < 12*2**30 or elapsed>a.wall_seconds:
                reason="HOST_MEMORY_GUARD" if vm.available<12*2**30 else "PROBE_WALL_LIMIT"
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=30)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL)
                break
            time.sleep(5)
    rc=child.wait()
(a.control/"terminal.json").write_text(json.dumps(dict(exit_code=rc,reason=reason,wall_seconds=time.monotonic()-started,
    peak_sampled_rss_bytes=peak,min_host_available_bytes=min_available),indent=2))
raise SystemExit(rc if rc>=0 else 128-rc)
