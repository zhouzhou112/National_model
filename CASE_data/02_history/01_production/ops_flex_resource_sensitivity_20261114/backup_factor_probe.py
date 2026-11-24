"""One-shot backup of all generated test artifacts, using the existing engine."""
import argparse,importlib.util,json,socket
from pathlib import Path
EXTRA=['FINAL_GATES_PASSED.json','compute_node_smoke.json','startup_resources.json',
       'data_copy_verification.json','license_path_preflight.json','runtime_slurm_job.txt',
       'runtime_hash_check.log','submission.json','release_receipt.json',
       'capacity_selection.json','source_code_sha256.json','resource_contract_reference.csv']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','run']);p.add_argument('--config',required=True);p.add_argument('--engine',required=True);a=p.parse_args()
 assert socket.gethostname().split('.')[0]=='t550'
 spec=importlib.util.spec_from_file_location('backup_engine',a.engine);engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
 token="'source_screen.csv','release_files.sha256','resource_usage.txt'";assert engine.INVENTORY.count(token)==1
 engine.INVENTORY=engine.INVENTORY.replace(token,token+','+','.join(repr(n) for n in EXTRA))
 marker="assert json.loads((out/'preservation_report.json').read_text())['status']=='COMPLETE'"
 assert engine.INVENTORY.count(marker)==1
 engine.INVENTORY=engine.INVENTORY.replace(marker,marker+"\n    report=json.loads((out/'solve_report.json').read_text())\n    assert report['requested_stop_observed'] is True and report['barrier_iterations']==5 and report['callback_stop_error'] is None\n    assert json.loads((out/'preservation_report.json').read_text())['scope']=='TEST_ONLY_FACTOR_PROBE_NO_FINAL_SOLUTION'")
 cfg=json.loads(Path(a.config).read_text());assert cfg['releases']==['20261115_lateopen_2050_restricted_factor5_t44_m750_v1'];engine.configure(cfg)
 {'plan':engine.plan,'run':engine.run}[a.phase]()
