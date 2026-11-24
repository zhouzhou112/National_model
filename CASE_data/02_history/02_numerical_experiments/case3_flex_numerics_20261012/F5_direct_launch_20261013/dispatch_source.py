
from pathlib import Path
import hashlib,json,os,subprocess,time,psutil,fcntl
from datetime import datetime,timezone
base=Path('/home/zz2/National_model_server')
source=base/'probe_outputs/case3_flex_numerics_20261012_aef0cb7'
out=base/'probe_outputs/case3_flex_F5_direct_20261013_3e4a2fe'
controller=base/'packages/run_flex_single_diagnostic_3e4a2fe.py'
assert hashlib.sha256(controller.read_bytes()).hexdigest()=='6639a8ba05ff8be81c7f82324b9bc212f002dff2096266e7e216a47c9cacce20'
assert not (source/'F5').exists(),'Old F5 already started'
assert not out.exists(),'New output already exists: inspect before retry'
p=psutil.Process(491304)
expected=[str(base/'envs/cispo-2030-v1/bin/python'),str(source/'repo/scripts/run_flex_server_series.py'),'--root',str(source),'--threads','16']
assert p.cmdline()==expected and p.uids().real==os.getuid(), 'Old coordinator identity mismatch'
assert not p.children(recursive=True),'Old queue has an active child'
assert json.loads((source/'queue_gate.json').read_text())['name']=='F5'
out.mkdir()
audit={'utc':datetime.now(timezone.utc).isoformat(),'authorization':'Author: directly start F5 after memory review','old_coordinator_pid':p.pid,'old_command':expected,'old_root':str(source),'new_root':str(out),'controller_sha256':'6639a8ba05ff8be81c7f82324b9bc212f002dff2096266e7e216a47c9cacce20','controller_git_commit':'3e4a2fe','available_bytes':psutil.virtual_memory().available}
p.suspend()
try:
 assert not p.children(recursive=True) and not (source/'F5').exists(),'F5 appeared during queue takeover'
 p.terminate()
finally:
 p.resume()
p.wait(timeout=15)
audit['old_queue_state']='TERMINATED_WHILE_WAITING_NO_SOLVER_CHILD'
(out/'takeover_receipt.json').write_text(json.dumps(audit,indent=2))
lock=base/'run_control/numerical_validation_solver.lock'
with lock.open('a') as f:
 for i in range(30):
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:time.sleep(.5)
 else:raise RuntimeError('Solver lock not released; no new solver launched')
 fcntl.flock(f,fcntl.LOCK_UN)
cmd=['flock','--nonblock',str(lock),str(base/'envs/cispo-2030-v1/bin/python'),str(controller),'--source-root',str(source),'--server-root',str(base),'--output',str(out)]
with (out/'controller_console.log').open('x') as log:
 child=subprocess.Popen(cmd,cwd=source/'repo',stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
audit.update(launcher_pid=child.pid,command=cmd)
(out/'launch_receipt.json').write_text(json.dumps(audit,indent=2))
print(json.dumps(audit),flush=True)
for i in range(20):
 if (out/'active.json').exists():
  print((out/'active.json').read_text(),flush=True);print((out/'F5_launch.json').read_text(),flush=True);break
 if child.poll() is not None:raise RuntimeError('Controller exited: '+(out/'controller_console.log').read_text())
 time.sleep(1)
