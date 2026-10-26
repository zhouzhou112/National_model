"""Derive only launch tooling; keep the validated B2030 model source pinned."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
BASE = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud'
TEMPLATE = BASE + '/20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2/continuation.sbatch'
registered = json.loads((HERE.parent/'case3_2040_C2050_launch_20261019/deployment_C2050_t40_wls_v2/launch_config.json').read_text(encoding='utf-8'))
LICENSE = registered['license_path']
out = HERE/'deployment_v3'
out.mkdir(exist_ok=True)
template = subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','paracloud-bscc-a8','cat '+TEMPLATE])
(out/'case3_2040_v2_template.sbatch').write_bytes(template)
batch = template.decode('utf-8')
batch = batch.replace('# Author 2026-10-19: gated case3 continuation or framework C.', '# Author 2026-10-26: B2030 v3, derived from case3 2040 v2; scientific gates reused.')
batch = batch.replace('--job-name=cispo_cont_agg0','--job-name=cispo2030_B_frozen')
batch = batch.replace('export GRB_LICENSE_FILE="${CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}"', 'export GRB_LICENSE_FILE="'+LICENSE+'"')
batch = batch.replace("root = Path(sys.argv[1])", "root = Path(sys.argv[1])\nlaunch = json.loads((root/'launch_config.json').read_text())\nassert os.environ['GRB_LICENSE_FILE'] == launch['license_path']\ngates = json.loads((root/'FINAL_GATES_PASSED.json').read_text())\nassert gates['status'] == 'PASS' and gates['framework'] == 'B' and gates['planning_year'] == 2030")
batch = batch.replace('if psutil.virtual_memory().available < 700 * 2**30:', "available_memory_gib = psutil.virtual_memory().available / 2**30\n(root/'startup_resources.json').write_text(json.dumps(dict(job_id=os.environ['SLURM_JOB_ID'], allocation=tres, time_limit=field('TimeLimit'), available_memory_gib=available_memory_gib), indent=2))\nif available_memory_gib < 700:")
batch = batch.replace('available_memory_gib=psutil.virtual_memory().available/2**30', 'available_memory_gib=available_memory_gib')
start = batch.index('CISPO_SCENARIO=')
# B-only scenario, profile, V9 and fixed-capacity arguments retain the v2 production command.
previous = (HERE/'base_frozen_2030.sbatch').read_text(encoding='utf-8')
batch = batch[:start] + previous[previous.index('CISPO_SCENARIO='):]
# Author requested no repeated gates. Keep license/resource smoke, reuse the 481-test receipt.
a = batch.index('# Exercise the real runner')
b = batch.index('/usr/bin/time -v', a)
batch = batch[:a] + '# Scientific and regression gates reused unchanged from FINAL_GATES_PASSED.json.\n' + batch[b:]
(HERE/'base_frozen_2030_v3.sbatch').write_text(batch,encoding='utf-8',newline='\n')
(out/'template_changes.diff').write_text(''.join(difflib.unified_diff(template.decode().splitlines(True),batch.splitlines(True),fromfile=TEMPLATE,tofile='base_frozen_2030_v3.sbatch')),encoding='utf-8')
record = dict(template_path=TEMPLATE,template_sha256=hashlib.sha256(template).hexdigest(),
    registered_license_path=LICENSE,license_registry='deployment_C2050_t40_wls_v2/launch_config.json',
    template_discrepancy='case3 2040 v2 uses the historical fallback; the registered replacement WLS was used by successful C2050 v2',
    source_commit='9f0a042cbad241b13351b36dd68f3680666d42fb',scientific_gates_reused=True,
    credential_contents_read=False,batch_sha256=hashlib.sha256(batch.encode()).hexdigest())
(out/'derivation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

tool=(HERE/'deploy_pilot.py').read_text(encoding='utf-8')
tool=tool.replace("NAME='20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2'", "NAME='20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v3'")
tool=tool.replace("EVIDENCE=HERE/'deployment_v2'", "EVIDENCE=HERE/'deployment_v3'\nLICENSE="+repr(LICENSE))
tool=tool.replace('export GRB_LICENSE_FILE="${{CISPO_CLOUD_LICENSE:-$HOME/gurobipy-test-gcs/gurobi.lic}}"', 'export GRB_LICENSE_FILE="{LICENSE}"')
tool=tool.replace("commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()", "commit='9f0a042cbad241b13351b36dd68f3680666d42fb'")
tool=tool.replace("frozen_capacity_from=SOURCE_NAME,upstream=None", "license_path=LICENSE,license_comparison='STRING_ONLY',template_release='20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2',previous_failed_job='5276670',scientific_gates_reused=True,frozen_capacity_from=SOURCE_NAME,upstream=None")
old="""                data=subprocess.check_output(['git','show',commit+':'+rel],cwd=REPO)
                assert data==(HERE/name).read_bytes();add(name,data)"""
new="""                if name=='base_frozen_2030.sbatch':
                    data=(HERE/'base_frozen_2030_v3.sbatch').read_bytes()
                    recorded=subprocess.check_output(['git','show','HEAD:'+str((HERE/'base_frozen_2030_v3.sbatch').relative_to(REPO).as_posix())],cwd=REPO)
                    assert data==recorded,'Commit reviewed launch script before freezing'
                else:
                    data=subprocess.check_output(['git','show',commit+':'+rel],cwd=REPO)
                    assert data==(HERE/name).read_bytes()
                add(name,data)"""
assert old in tool
tool=tool.replace(old,new)
marker="(root/'cloud_source_repo_sha256.json').write_text"
check="""oldroot=root.parent/'20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2'
assert source_hashes==json.loads((oldroot/'cloud_source_repo_sha256.json').read_text())
assert {k:v['sha256'] for k,v in expected.items()}==json.loads((oldroot/'data_overlay_sha256.json').read_text())
same=[]
for folder in ['repo','additional_data','frozen_source']:
 for p in (root/folder).rglob('*'):
  if p.is_file():
   rel=p.relative_to(root);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((oldroot/rel).read_bytes()).digest(),str(rel)
   same.append(str(rel))
assert (root/'FINAL_GATES_PASSED.json').read_bytes()==(oldroot/'FINAL_GATES_PASSED.json').read_bytes()
(root/'v2_identity_reuse.json').write_text(json.dumps(dict(status='PASS',unchanged_file_count=len(same),source_commit='9f0a042cbad241b13351b36dd68f3680666d42fb',gates_identical=True),indent=2)+'\\n')
"""
assert marker in tool
tool=tool.replace(marker,check+marker)
marker="assert not (root/'submission_attempt.json').exists() and not (root/'preflight').exists()"
check="""launch=json.loads((root/'launch_config.json').read_text())
batch=(root/'base_frozen_2030.sbatch').read_text()
matches=re.findall(r'^export GRB_LICENSE_FILE="([^"\\n]+)"$',batch,re.M)
registered=json.loads((root.parent/'20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2'/'launch_config.json').read_text())['license_path']
assert matches==[registered] and launch['license_path']==registered,'WLS path string mismatch'
license_check=dict(status='PASS',mode='STRING_ONLY',sbatch_license_path=matches[0],registered_license_path=registered,credential_contents_read=False)
(root/'license_path_preflight.json').write_text(json.dumps(license_check,indent=2)+'\\n')
"""
assert marker in tool
tool=tool.replace(marker,marker+'\n'+check)
tool=tool.replace("dict(status='PASS',report=report)","dict(status='PASS',report=report,license_path_check=license_check)")
tool=tool.replace("assert not (root/'submission_attempt.json').exists(),'Do not repeat an uncertain submission'", "assert json.loads((root/'license_path_preflight.json').read_text())['status']=='PASS'\nassert not (root/'submission_attempt.json').exists(),'Do not repeat an uncertain submission'")
tool=tool.replace("['compute_node_smoke.json','batch_exit.json']", "['compute_node_smoke.json','startup_resources.json','batch_exit.json']")
compile(tool,'deploy_pilot_v3.py','exec')
(HERE/'deploy_pilot_v3.py').write_text(tool,encoding='utf-8',newline='\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
