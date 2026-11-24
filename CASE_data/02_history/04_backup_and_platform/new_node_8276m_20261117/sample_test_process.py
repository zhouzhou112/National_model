"""One-test resource telemetry, ending with that process; never controls jobs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import psutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root',type=Path,required=True)
p.add_argument('--version',choices=['v1','v2'],required=True)
a=p.parse_args()
source=a.root/'runsource'/('t32_factor5_'+a.version)
receipt=json.loads((source/'controller_started.json').read_text(encoding='utf-8-sig'))
proc=psutil.Process(int(receipt['solver_pid']))
created=proc.create_time()
cmd=proc.cmdline()
if not any(str(source/'benchmark_mps.py').lower()==x.lower() for x in cmd):
    raise RuntimeError('PID command does not match the frozen test script')
out=a.root/'runs'/('t32_factor5_'+a.version)
max_rss=max_private=max_os_peak=0
min_free=psutil.virtual_memory().available
start=time.monotonic()
reason='PROCESS_EXITED'
with (out/'external_resources.jsonl').open('x',encoding='utf-8') as log:
    while time.monotonic()-start<30*3600:
        try:
            if proc.create_time()!=created or not proc.is_running():
                reason='PID_EXITED_OR_CHANGED';break
            mem=proc.memory_info();free=psutil.virtual_memory().available
            os_peak=getattr(mem,'peak_wset',mem.rss)
            private=getattr(mem,'private',mem.vms)
            max_rss=max(max_rss,mem.rss);max_private=max(max_private,private)
            max_os_peak=max(max_os_peak,os_peak);min_free=min(min_free,free)
            row=dict(utc=datetime.now(timezone.utc).isoformat(),pid=proc.pid,
                     rss_bytes=mem.rss,os_lifetime_peak_rss_bytes=os_peak,
                     private_bytes=private,available_bytes=free,
                     cpu_seconds=sum(proc.cpu_times()[:2]),threads=proc.num_threads())
            log.write(json.dumps(row)+'\n');log.flush()
        except psutil.NoSuchProcess:
            break
        time.sleep(1)
    else:reason='TELEMETRY_DEADLINE_ONLY_NO_SOLVER_CONTROL'
(out/'external_resources_summary.json').write_text(json.dumps(dict(
    finished_utc=datetime.now(timezone.utc).isoformat(),pid=proc.pid,
    create_time=created,reason=reason,peak_rss_bytes=max_rss,
    os_lifetime_peak_rss_bytes=max_os_peak,peak_private_bytes=max_private,
    minimum_available_bytes=min_free,elapsed_seconds=time.monotonic()-start,
    note='Started after MPS read began; OS lifetime peak covers earlier RSS, but pre-start time series is unavailable'),indent=2),encoding='utf-8')
