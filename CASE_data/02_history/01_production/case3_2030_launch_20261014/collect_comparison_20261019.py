"""Read-only collection of bounded Base/case3 2030 comparison evidence.

Run from repository root. Copies explicit result files, verifies remote SHA256,
and preserves all originals; does not read credentials or submit jobs.
"""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import argparse

OUT = Path(__file__).parent / 'comparison_20261019'
RELEASES = {'base': '20260914_base_v9_t48_m750_tol1e4_v3',
            'case3': '20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1'}
NAMES = ['annual_summary.json', 'annual_capacity_by_technology.csv',
         'annual_generation_by_technology.csv', 'annual_storage_operation_by_technology.csv',
         'annual_flexible_load_by_province.csv', 'annual_adequacy_by_province.csv',
         'annual_carbon_ccs.json', 'cost_components.csv', 'solve_report.json',
         'solution_qc.json', 'result_manifest.json', 'preservation_report.json',
         'model_config_snapshot.json', 'run_identity.json', 'gurobi.log',
         'candidate_selection.csv', 'vre_capacity.csv', 'thermal_nuclear_capacity.csv',
         'storage_capacity.csv', 'transmission_capacity.csv',
         'model_archive/archive_manifest.json',
         'barrier_checkpoint/barrier_checkpoint_manifest.json',
         'planning_state_candidate/state_metadata.json',
         'planning_state_candidate/capacity_cohorts.csv.gz',
         'planning_state_candidate/state_transition_summary.csv']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--r1-supplement',action='store_true')
    args=parser.parse_args()
    if not args.r1_supplement:
        OUT.mkdir(exist_ok=False)
    for label, release in RELEASES.items():
        if args.r1_supplement and label!='case3': continue
        names = (['intra_grid_vre_site_design.csv','load_center_intra_transmission.csv',
                  'intra_grid_substation_design.csv','hydro_capacity.csv','wave_capacity.csv']
                 if args.r1_supplement else NAMES)
        root = '/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/' + release + '/output_8760'
        code = 'root=' + repr(root) + '\nnames=' + repr(names) + '\n' + '''
import pathlib,json,hashlib,base64
root=pathlib.Path(root);out={}
for name in names:
 p=root/name
 if not p.is_file():
  out[name]={'exists':False};continue
 assert p.stat().st_size<20000000,name
 b=p.read_bytes()
 out[name]={'exists':True,'sha256':hashlib.sha256(b).hexdigest(),'base64':base64.b64encode(b).decode()}
print(json.dumps(out))
'''
        reply = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12',
            'paracloud-bscc-a8','python3 -'],input=code.encode(),capture_output=True,check=True)
        evidence = {}
        for name, item in json.loads(reply.stdout).items():
            if not item['exists']:
                evidence[name] = item; continue
            data=base64.b64decode(item['base64'])
            assert hashlib.sha256(data).hexdigest()==item['sha256']
            target=OUT/label/name;target.parent.mkdir(parents=True,exist_ok=True)
            assert not target.exists(),target
            target.write_bytes(data)
            evidence[name]={'sha256':item['sha256'],'bytes':len(data),'verified':True}
        suffix='_r1_collection.json' if args.r1_supplement else '_collection.json'
        (OUT/(label+suffix)).write_text(json.dumps(dict(source=root,files=evidence),indent=2)+'\n')
        print(label, 'verified files', sum(v.get('verified',False) for v in evidence.values()), flush=True)

if __name__=='__main__': main()
