"""Bounded, independent OPS2050 hardware test. Never writes the source release.

Modes: smoke checks a >2000-variable license; prepare verifies/decompresses the
archived MPS; run measures the identical LP with 32 threads and five iterations.
All outputs are diagnostic, not a scientific solution or acceptance decision.
"""
import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
import sys
import threading
import time
from datetime import datetime, timezone

GIB = 2**30
EXPECTED_MPS_SHA = '33a4f822cbf894810082843e6ccabbb59db2183e3282f182b0df1cb807768a4b'
EXPECTED_PRM_SHA = '24d9ead7a115503af26481af3e1f8c5f8de5f5e0ff20459ffdf600943ae4a3c5'
EXPECTED_DIMS = (54288578, 43797081, 503239404)
EXPECTED_FINGERPRINT = -17374259 & 0xffffffff

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def save(path, value):
    p = Path(path)
    tmp = p.with_suffix(p.suffix+'.part')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    os.replace(tmp, p)

def safe_number(value):
    v = float(value)
    return v if math.isfinite(v) else None

def environment():
    import gurobipy as gp
    if gp.gurobi.version() != (13, 0, 2):
        raise RuntimeError('Exact Gurobi 13.0.2 required')
    env = gp.Env(empty=True)
    env.setParam('OutputFlag', 0)
    env.setParam('ThreadLimit', 32)
    env.setParam('MemLimit', 660*GIB/1e9)
    env.start()  # Solver consumes the configured license; no code reads its contents.
    return gp, env

def smoke(out):
    gp, env = environment()
    with env, gp.Model(env=env) as model:
        model.Params.Threads = 32
        x = model.addMVar(3001, lb=0, ub=1)
        model.addConstr(x.sum() >= 1)
        model.setObjective(x.sum())
        model.optimize()
        ok = model.Status == gp.GRB.OPTIMAL and abs(model.ObjVal-1) < 1e-8
        result = dict(utc=utc(), status='PASS' if ok else 'FAIL', variables=3001,
                      requested_threads=32, effective_threads=model.Params.Threads,
                      version=gp.gurobi.version(), objective=model.ObjVal,
                      scope='License/runtime check only; not the national model')
        save(out/'license_smoke.json', result)
        if not ok:
            raise RuntimeError('License/runtime smoke failed')

def prepare(root):
    source = root/'input/model_archive/original.mps.gz'
    target = root/'input/model_archive/original.mps'
    receipt = root/'input/model_archive/decompression_verified.json'
    if sha(source) != EXPECTED_MPS_SHA:
        raise RuntimeError('Compressed source MPS SHA mismatch')
    if target.exists():
        if not receipt.exists():
            raise RuntimeError('Unverified partial decompression retained; inspect before retry')
        data = json.loads(receipt.read_text(encoding='utf-8'))
        if target.stat().st_size != data['bytes'] or sha(target) != data['sha256']:
            raise RuntimeError('Existing decompressed MPS differs from receipt')
        return target
    started = time.monotonic()
    h = hashlib.sha256()
    with gzip.open(source, 'rb') as src, target.open('xb') as dst:
        for b in iter(lambda: src.read(8*1024*1024), b''):
            if shutil.disk_usage(root).free < 50*GIB:
                raise RuntimeError('Decompression stopped below 50 GiB disk reserve; partial file retained')
            dst.write(b)
            h.update(b)
    save(receipt, dict(utc=utc(), source_sha256=EXPECTED_MPS_SHA,
                      sha256=h.hexdigest(), bytes=target.stat().st_size,
                      elapsed_seconds=time.monotonic()-started, gzip_crc_verified=True))
    return target

def parameters(path):
    if sha(path) != EXPECTED_PRM_SHA:
        raise RuntimeError('Source parameter SHA mismatch')
    result = {}
    for line in path.read_text(encoding='ascii').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split()
        if key == 'LicenseID':
            continue  # Node license identity is independent of the old source license.
        number = float(value)
        result[key] = int(number) if number.is_integer() else number
    return result

def run(root, out):
    import numpy as np
    import psutil
    import msvcrt
    vm = psutil.virtual_memory()
    if vm.available < 650*GIB:
        raise RuntimeError('Test admission requires 650 GiB free; this is not the cloud production gate')
    if psutil.cpu_count() < 32:
        raise RuntimeError('Fewer than 32 visible processors')
    lock = (root/'test.lock').open('a+b')
    lock.seek(0); lock.write(b'1'); lock.flush(); lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    model = None
    env = None
    stop = threading.Event()
    samples = dict(peak_rss_bytes=0, peak_private_bytes=0, minimum_available_bytes=vm.available)
    start = time.monotonic()
    state = {'stage':'initializing', 'memory_stop_requested':False}
    process = psutil.Process()

    def monitor():
        with (out/'resources.jsonl').open('x', encoding='utf-8') as f:
            while not stop.is_set():
                memory = process.memory_info()
                available = psutil.virtual_memory().available
                private = getattr(memory, 'private', memory.vms)
                samples['peak_rss_bytes'] = max(samples['peak_rss_bytes'], memory.rss)
                samples['peak_private_bytes'] = max(samples['peak_private_bytes'], private)
                samples['minimum_available_bytes'] = min(samples['minimum_available_bytes'], available)
                item = dict(utc=utc(), elapsed_seconds=time.monotonic()-start, stage=state['stage'],
                            rss_bytes=memory.rss, private_bytes=private, available_bytes=available,
                            cpu_seconds=sum(process.cpu_times()[:2]), process_threads=process.num_threads())
                f.write(json.dumps(item)+'\n'); f.flush()
                if available < 30*GIB:
                    state['memory_stop_requested'] = True
                    if model is not None:
                        model.terminate()
                stop.wait(1)

    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    terminal = dict(started_utc=utc(), diagnostic_only=True, scientific_acceptance='NOT_APPLICABLE',
                    source_mps_sha256=EXPECTED_MPS_SHA, thread_limit=32, iteration_limit=5,
                    hard_memory_limit_gib=660, soft_memory_limit_gib=640,
                    minimum_available_gib=30, admission_available_gib=vm.available/GIB,
                    platform=sys.platform, python=sys.version)
    try:
        # Prior preparation must be complete; do not mix decompression into solver timing.
        prepared = root/'input/model_archive/decompression_verified.json'
        if not prepared.exists():
            raise RuntimeError('Run prepare first')
        metadata = json.loads(prepared.read_text(encoding='utf-8'))
        mps = root/'input/model_archive/original.mps'
        if mps.stat().st_size != metadata['bytes'] or sha(mps) != metadata['sha256']:
            raise RuntimeError('Prepared MPS integrity check failed')
        gp, env = environment()
        state['stage'] = 'read_mps'
        t = time.monotonic()
        model = gp.read(str(mps), env=env)
        terminal['read_mps_seconds'] = time.monotonic()-t
        dims = (int(model.NumConstrs),int(model.NumVars),int(model.DNumNZs))
        fingerprint = int(model.Fingerprint) & 0xffffffff
        terminal.update(dimensions=dims, fingerprint=fingerprint)
        if dims != EXPECTED_DIMS or fingerprint != EXPECTED_FINGERPRINT:
            raise RuntimeError('Read MPS dimension/fingerprint differs from archived LP; do not optimize')
        for key,value in parameters(root/'input/model_archive/parameters.prm').items():
            model.setParam(key, value)
        overrides = dict(Threads=32, BarIterLimit=5, TimeLimit=24*3600,
                         SoftMemLimit=640*GIB/1e9, MemLimit=660*GIB/1e9,
                         OutputFlag=1, LogToConsole=0, LogFile=str(out/'gurobi.log'))
        for key,value in overrides.items():
            model.setParam(key,value)
        model.write(str(out/'effective_parameters.prm'))
        terminal['overrides'] = overrides
        save(out/'identity_before_optimize.json',terminal)
        if state['memory_stop_requested']:
            raise RuntimeError('Free-memory guard triggered before optimization')
        state['stage'] = 'optimize'
        with (out/'barrier_iterations.jsonl').open('x',encoding='utf-8') as log:
            def callback(m, where):
                if where == gp.GRB.Callback.BARRIER:
                    iteration = int(m.cbGet(gp.GRB.Callback.BARRIER_ITRCNT))
                    rec = dict(utc=utc(),iteration=iteration,runtime_seconds=m.cbGet(gp.GRB.Callback.RUNTIME))
                    for key,attr in [('primal',gp.GRB.Callback.BARRIER_PRIMOBJ),('dual',gp.GRB.Callback.BARRIER_DUALOBJ),
                                     ('pinf',gp.GRB.Callback.BARRIER_PRIMINF),('dinf',gp.GRB.Callback.BARRIER_DUALINF),
                                     ('complementarity',gp.GRB.Callback.BARRIER_COMPL)]:
                        rec[key] = safe_number(m.cbGet(attr))
                    log.write(json.dumps(rec)+'\n');log.flush()
                    if iteration >= 5:
                        m.terminate()
                if state['memory_stop_requested']:
                    m.terminate()
            model.optimize(callback)
        terminal.update(status_code=int(model.Status),barrier_iterations=int(model.BarIterCount),
                        solver_seconds=model.Runtime,solution_count=int(model.SolCount),
                        memory_stop_requested=state['memory_stop_requested'])
        # Preserve any accessible vectors. Whole-attribute retrieval avoids creating
        # tens of millions of Python Var/Constr handles; free each list immediately.
        state['stage'] = 'preserve_available_vectors'
        terminal['vectors'] = {}
        for attr in ['BarX','BarPi','X','Pi']:
            try:
                values = model.getAttr(attr)
                array = np.asarray(values,dtype=np.float64)
                del values
                path = out/(attr+'.npy')
                np.save(path,array);del array
                terminal['vectors'][attr] = dict(status='SAVED',bytes=path.stat().st_size,sha256=sha(path))
            except (gp.GurobiError,AttributeError) as exc:
                terminal['vectors'][attr] = dict(status='UNAVAILABLE_AT_DIAGNOSTIC_STOP',error_type=type(exc).__name__)
        terminal['status'] = 'BOUNDED_TEST_FINISHED'
    except Exception as exc:
        terminal.update(status='TEST_STOPPED',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        state['stage']='finalize'
        try:
            if model is not None:
                model.dispose()
            if env is not None:
                env.dispose()
        finally:
            stop.set();thread.join(timeout=5)
            terminal.update(finished_utc=utc(),wall_seconds=time.monotonic()-start,resources=samples)
            save(out/'terminal.json',terminal)
            lock.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['smoke','prepare','run'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    a=parser.parse_args()
    root=a.root.resolve()
    if a.mode in {'smoke','run'}:
        authorization=root/'setup/execution_authorization.json'
        if not authorization.exists() or json.loads(authorization.read_text(encoding='utf-8-sig')).get('status')!='AUTHORIZED':
            raise RuntimeError('PREPARE_ONLY: author has deferred solver and license smoke execution; no Gurobi environment was created')
    if a.mode=='prepare':
        print(prepare(root));return
    if a.output is None:
        parser.error('--output is required for smoke and run')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    if a.mode=='smoke':
        try:
            smoke(out)
        except Exception as exc:
            save(out/'license_smoke.json',dict(utc=utc(),status='NOT_PASSED',
                 error_type=type(exc).__name__,error_code=getattr(exc,'errno',None),
                 note='No license contents or credential parameters were recorded'))
            raise
    else:run(root,out)

if __name__=='__main__':
    main()
