"""Derive the 2050 launcher from the reviewed 2040 continuation, without model edits."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OLD=HERE.parent/'base_2040_continuation_20260919'

def replace_checked(text, old, new):
    if old not in text:
        raise ValueError('Missing reviewed template fragment: '+old)
    return text.replace(old,new)

def write_new(path, text):
    if path.exists() and path.read_text(encoding='utf-8')!=text:
        raise FileExistsError(path)
    path.write_text(text,encoding='utf-8',newline='\n')

def main():
    settings=json.loads((HERE/'launch_config.json').read_text())
    old_profile='barrier_checkpoint_full_year_cloud_2040_numeric_v1_threads44'
    new_profile=Path(settings['profile']).stem
    profile=json.loads((REPO/'config/solver_profiles'/f'{old_profile}.json').read_text())
    profile['profile_id']=new_profile
    profile['numerics']['threads']=48
    profile['description']=settings['authorization']+' Same v9 model, NF2, BarConvTol1e-4, Crossover0, unlimited solver runtime and no soft memory limit; no automatic 2060 or Stage B.'
    write_new(REPO/settings['profile'],json.dumps(profile,indent=2)+'\n')
    batch=(OLD/'base_2040.sbatch').read_text()
    for old,new in [('full 2040','full 2050'),('cispo2040_base_v9_t44','cispo2050_base_v9_t48'),
                    ('Verified 2030','Verified 2040'),('=44','=48'),('< 44','< 48'),
                    ('validate_2040.py','validate_2050.py'),(old_profile,new_profile),
                    ('--planning-year 2040','--planning-year 2050')]:
        batch=replace_checked(batch,old,new)
    write_new(HERE/'base_2050.sbatch',batch)
    validator=(OLD/'validate_2040.py').read_text()
    for old,new in [('actual 2030 candidate, year transition and tiny 2040','actual 2040 candidate, year transition and tiny 2050'),
                    (old_profile,new_profile),('.for_planning_year(2040)','.for_planning_year(2050)'),
                    ("old = load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path='config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json')",
                     "old = load_model_config('config/optimization_numeric_dac_by_year_v9.json', solver_path='config/solver_profiles/"+old_profile+".json').for_planning_year(2040)"),
                    ("    assert analysis_case_identity(old)['resolved_scientific_configuration_sha256'] == '937c3c6f4540dc2d217bd17eda44a4de0de76b41414e32d491d4283515b0d4f0'\n",''),
                    ('cfg.planning_year == 2040 and cfg.boundary_year == 2030','cfg.planning_year == 2050 and cfg.boundary_year == 2040'),
                    ("{'threads': [48, 44]}","{'threads': [44, 48]}"),
                    ('expected_boundary_year=2030','expected_boundary_year=2040'),
                    ('== 86900','== 173800'),
                    ('planning_year=2040, boundary_year=2030','planning_year=2050, boundary_year=2040'),
                    ("'--planning-year', '2040'","'--planning-year', '2050'"),
                    ("scope['planning_year'] == 2040 and scope['boundary_year'] == 2030","scope['planning_year'] == 2050 and scope['boundary_year'] == 2040"),
                    ('validation_2040.json','validation_2050.json')]:
        validator=replace_checked(validator,old,new)
    write_new(HERE/'validate_2050.py',validator)
    audit=(OLD/'audit_state_bounds.py').read_text().replace('actual 2040 inputs','actual 2050 inputs').replace('for_planning_year(2040)','for_planning_year(2050)').replace('expected_boundary_year=2030','expected_boundary_year=2040').replace('planning_year=2040','planning_year=2050')
    write_new(HERE/'audit_state_bounds.py',audit)
    records={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [REPO/settings['profile'],HERE/'base_2050.sbatch',HERE/'validate_2050.py',HERE/'audit_state_bounds.py']}
    write_new(HERE/'local_files.json',json.dumps(records,indent=2)+'\n')
    print(json.dumps(records,indent=2))

if __name__=='__main__': main()
