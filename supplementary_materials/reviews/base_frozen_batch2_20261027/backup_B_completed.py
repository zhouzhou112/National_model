"""T550 only, after terminal preservation: plan|run --config YEAR_backup_config.json.

Reuse full-result transfer and global lock; add explicit B closure/mapping metadata.
No listener, deletion, credentials, or source writes.
"""
from pathlib import Path
import argparse,importlib.util,json,socket
ROOT=Path(__file__).resolve().parents[3]
EXTRA=['frozen_closure.json','cf_fallback_cloud.json','cf_mapping_preflight.json',
       'engineering_gate_window_carbon_budget.json','engineering_gate_window_model_audit.json',
       'FINAL_GATES_PASSED.json','compute_node_smoke.json','startup_resources.json',
       'released_submission.json','data_copy_verification.json','license_path_preflight.json']
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['plan','run']);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
 spec=importlib.util.spec_from_file_location('full_backup',ROOT/'scripts/backup_completed_cloud.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 token="'source_screen.csv','release_files.sha256','resource_usage.txt'"
 assert m.INVENTORY.count(token)==1
 m.INVENTORY=m.INVENTORY.replace(token,token+','+','.join(repr(x) for x in EXTRA))
 m.configure(json.loads(a.config.read_text(encoding='utf-8')))
 assert socket.gethostname().split('.')[0]=='t550'
 {'plan':m.plan,'run':m.run}[a.phase]()
