#!/usr/bin/env python3
"""Sample Linux host/process-group and NVIDIA pressure without controlling jobs.

Writes resource_pressure.jsonl and resource_pressure_summary.json in a new
output directory. GPU utilization.memory is memory-controller activity, NOT
allocated VRAM percentage. Sampled peaks can miss sub-interval allocation spikes.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import time

import psutil


GPU_FIELDS = "index,uuid,name,memory.total,memory.used,memory.free,utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit,pstate"
GPU_KEYS = ("index", "uuid", "name", "memory_total_mib", "memory_used_mib",
            "memory_free_mib", "gpu_util_percent", "memory_controller_util_percent",
            "temperature_c", "power_w", "power_limit_w", "pstate")


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def gpu_rows(text):
    result = []
    for row in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not row:
            continue
        if len(row) != len(GPU_KEYS):
            raise ValueError(f"Unexpected GPU telemetry column count: {len(row)}")
        item = dict(zip(GPU_KEYS, (value.strip() for value in row)))
        item["index"] = int(item["index"])
        for key in GPU_KEYS[3:-1]:
            item[key] = numeric(item[key])
        total, used = item["memory_total_mib"], item["memory_used_mib"]
        item["vram_used_percent"] = 100 * used / total if total and used is not None else None
        result.append(item)
    return result


def nvidia_query(query):
    return subprocess.check_output(
        ["nvidia-smi", query, "--format=csv,noheader,nounits"], text=True,
        stderr=subprocess.PIPE, timeout=5,
    )


def pressure(kind):
    result = {}
    try:
        for line in Path(f"/proc/pressure/{kind}").read_text().splitlines():
            scope, *fields = line.split()
            result[scope] = {key: float(value) for key, value in
                             (field.split("=", 1) for field in fields)}
    except OSError:
        return None
    return result


def group_processes(pgid):
    result = []
    for proc in psutil.process_iter(["pid", "create_time", "memory_info", "cpu_times"]):
        try:
            if os.getpgid(proc.pid) == pgid:
                info = proc.info
                result.append({"pid": proc.pid, "create_time": info["create_time"],
                               "rss_bytes": info["memory_info"].rss,
                               "cpu_seconds": info["cpu_times"].user + info["cpu_times"].system})
        except (ProcessLookupError, PermissionError, psutil.Error):
            continue
    return result


def collect(pgid, selected_gpu):
    vm, swap = psutil.virtual_memory(), psutil.swap_memory()
    processes = group_processes(pgid)
    record = {
        "timestamp_utc": timestamp(), "monotonic_seconds": time.monotonic(),
        "host": {"memory_total_bytes": vm.total, "memory_available_bytes": vm.available,
                 "memory_used_percent": 100 * (vm.total - vm.available) / vm.total,
                 "swap_used_bytes": swap.used, "swap_in_bytes_total": swap.sin,
                 "swap_out_bytes_total": swap.sout, "cpu_util_percent": psutil.cpu_percent(),
                 "memory_psi": pressure("memory"), "io_psi": pressure("io")},
        "process_group": {"pgid": pgid, "rss_bytes": sum(p["rss_bytes"] for p in processes),
                          "members": processes},
        "gpus": [], "errors": [],
    }
    try:
        record["gpus"] = gpu_rows(nvidia_query("--query-gpu=" + GPU_FIELDS))
        pid_set = {p["pid"] for p in processes}
        clients = {}
        for row in csv.reader(io.StringIO(nvidia_query(
                "--query-compute-apps=gpu_uuid,pid,used_gpu_memory")), skipinitialspace=True):
            if len(row) == 3:
                uuid, pid, used = (value.strip() for value in row)
                # Store only this job's clients, never other users' command lines.
                if int(pid) in pid_set:
                    clients.setdefault(uuid, []).append({"pid": int(pid), "used_mib": numeric(used)})
        for gpu in record["gpus"]:
            gpu["selected"] = str(gpu["index"]) == selected_gpu or gpu["uuid"] == selected_gpu
            gpu["job_clients"] = clients.get(gpu["uuid"], [])
            values = [p["used_mib"] for p in gpu["job_clients"]]
            gpu["job_memory_used_mib"] = sum(values) if all(v is not None for v in values) else None
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        record["errors"].append(f"GPU telemetry: {error}")
    return record


def update_summary(summary, record):
    summary["sample_count"] = summary.get("sample_count", 0) + 1
    summary.setdefault("started_at", record["timestamp_utc"])
    summary["updated_at"] = record["timestamp_utc"]
    summary["telemetry_error_samples"] = summary.get("telemetry_error_samples", 0) + bool(record["errors"])
    host = record["host"]
    maxima = {"host_memory_used_percent": host["memory_used_percent"],
              "job_rss_bytes": record["process_group"]["rss_bytes"],
              "swap_used_bytes": host["swap_used_bytes"]}
    for key, value in maxima.items():
        summary[key + "_peak"] = max(summary.get(key + "_peak", 0), value)
    summary["host_memory_available_bytes_min"] = min(
        summary.get("host_memory_available_bytes_min", host["memory_available_bytes"]),
        host["memory_available_bytes"])
    for gpu in record["gpus"]:
        entry = summary.setdefault("gpus", {}).setdefault(gpu["uuid"], {"index": gpu["index"]})
        for key in ("memory_used_mib", "vram_used_percent", "gpu_util_percent",
                    "memory_controller_util_percent", "temperature_c", "power_w", "job_memory_used_mib"):
            value = gpu.get(key)
            if value is not None:
                entry[key + "_peak"] = max(entry.get(key + "_peak", 0), value)
        if gpu.get("gpu_util_percent") is not None:
            entry["gpu_util_sample_sum"] = entry.get("gpu_util_sample_sum", 0) + gpu["gpu_util_percent"]
            entry["gpu_util_sample_count"] = entry.get("gpu_util_sample_count", 0) + 1
            entry["gpu_util_sample_mean_percent"] = entry["gpu_util_sample_sum"] / entry["gpu_util_sample_count"]


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-group", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gpu-device", default="1")
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--once", action="store_true", help="One lightweight sample for validation")
    args = parser.parse_args()
    if args.interval <= 0 or args.process_group <= 1:
        parser.error("positive interval and process-group > 1 required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"sampling_interval_seconds": args.interval,
               "peak_semantics": "sampled, not an allocator high-water mark",
               "memory_controller_util_semantics": "activity, not VRAM capacity fraction"}
    path = args.output_dir / "resource_pressure.jsonl"
    psutil.cpu_percent()
    with path.open("x", encoding="utf-8", buffering=1) as stream:
        while True:
            started = time.monotonic()
            record = collect(args.process_group, args.gpu_device)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            update_summary(summary, record)
            atomic_json(args.output_dir / "resource_pressure_summary.json", summary)
            if args.once or (args.stop_file and args.stop_file.exists()) or not record["process_group"]["members"]:
                break
            time.sleep(max(0, args.interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
