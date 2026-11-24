"""Explicit classification and relocation plan. No filesystem mutations of sources."""
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
WORK=Path(__file__).resolve().parent
GROUPS={
'01_production': '''base_2040_continuation_20260919 base_2050_continuation_20260930 base_2060_launch_20261012 base_2060_screen_20261026 base_acceptance_relative_v1_20261012 base_frozen_B_20261026 base_frozen_batch2_20261027 base_frozen_closure_20261027 base_frozen_followups_20261027 base_v9_terminal_20260919 C2050_completed_20261029 C2060_acceptance_20261108 C2060_completed_20261107 C2060_launch_20261030 case3_2030_launch_20261014 case3_2040_C2050_launch_20261019 case3_2050_acceptance_20261106 case3_2050_completed_20261106 case3_2050_launch_20261027 case3_2050_preparation_20261026 case3_2060_acceptance_20261114 case3_2060_completed_20261114 case3_2060_launch_20261106 completed_acceptance_20261020 completed_results_20261027 formal_launch_20260914 ops_flex_resource_sensitivity_20261114 thermal_launch_20260907'''.split(),
'02_numerical_experiments': '''barrier_jump_diagnosis_20261002 base_numeric_failure_20260913 base_regression_explanation_20260915 case3_flex_numerics_20261012 cloud_failure_comparison_20260915 convergence_eta_20261004 crossover_contract_20260913 deployed_repair_audit_20260915 factor_pair_8760_20261005 formal_launch_failure_20260914 numeric_applied_verification_20260915 numeric_doublecheck_20260913 numeric_prelaunch_20260913 numeric_repair_20260913 numeric_resolution_20260913 numerical_robustness_20261005 reservoir_storage_audit_20260913 solve_feasibility_vs_thermal_20260913 solver_alignment_thermal_20260913 thread_comparison_20260930 tiny_bound_audit_20261004 tolerance_1e4_readiness_20260913 validation_coordination_20261005'''.split(),
'03_result_analysis': '''dual_screening_20261002 export_annual_row_duals_20261105 flex_mechanism_exploration_20261106 t550_flex_analysis_20261104'''.split(),
'04_backup_and_platform': '''cloud_backup_20261012 cloud_backup_20261020 cloud_backup_20261024 cloud_backup_20261025 cloud_backup_20261027 cloud_joint_progress_20261016 new_node_8276m_20261117'''.split(),
}


def main():
    inv=json.loads((WORK/'inventory_before.json').read_text());dirs={x['directory']:x for x in inv['directories']}
    mapping={};rows=[]
    for group,names in GROUPS.items():
        for name in names:
            src='supplementary_materials/reviews/'+name
            assert src in dirs and src not in mapping,src
            mapping[src]='CASE_data/02_history/'+group+'/'+name
    # Historical deliveries are relocated intact, retaining their original manifests.
    for name in ['by_case','deliveries','core_library_20261123']:
        src='case_results/'+name
        if (ROOT/src).is_dir():mapping[src]='CASE_data/03_legacy_deliveries/'+name
    tracked=subprocess.check_output(['git','ls-files','-s','-z'],cwd=ROOT).decode().split('\0')
    tracked_moves=[]
    for line in tracked:
        if not line:continue
        attrs,path=line.split('\t',1);mode,blob,stage=attrs.split();assert stage=='0'
        for src,dest in mapping.items():
            if path.startswith(src+'/'):
                tracked_moves.append(dict(old=path,new=dest+path[len(src):],mode=mode,blob=blob));break
    for key,d in dirs.items():
        if not key.startswith('supplementary_materials/reviews/'):continue
        name=Path(key).name
        if key in mapping:
            group=mapping[key].split('/')[2]
            reason={'01_production':'生产准备、终态、验收与敏感性证据；迁移保留',
                    '02_numerical_experiments':'历史数值方案、失败与方法选择证据；不作为当前生产解，仍保留',
                    '03_result_analysis':'结果提取、定价与论文分析证据；保留并集中',
                    '04_backup_and_platform':'备份、传输与平台运行记录；保留'}[group]
            disposition='MOVE_KEEP'
        else:
            group='RETAIN_SUPPLEMENTARY_OR_METHODS';reason='论文/SI、参数或输入方法审查；本轮不搬动、不判废弃';disposition='KEEP_IN_PLACE'
        rows.append(dict(directory=key,destination=mapping.get(key,key),disposition=disposition,category=group,
                         files=d['files'],bytes=d['bytes'],reason=reason,delete_authorized=False))
    files=[dict(f,destination=next(dest+f['path'][len(src):] for src,dest in mapping.items() if f['path'].startswith(src+'/')))
           for f in inv['files'] if any(f['path'].startswith(src+'/') for src in mapping)]
    # Credential-looking paths are not read, hashed, or silently moved with evidence.
    suspicious=[f['path'] for f in files if re.search(r'(^|/)(gurobi\.lic|id_(rsa|ed25519)|.*\.pem|\.env)$',f['path'],re.I)]
    assert not suspicious,suspicious
    plan=dict(root=str(ROOT),moves=[dict(source=s,destination=d,compatibility_junction=True) for s,d in mapping.items()],
              files=files,tracked_moves=tracked_moves,original_inventory='inventory_before.json',deletion=False)
    (WORK/'move_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (WORK/'reviews_classification.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    patterns='\n'.join(Path(s).name for s in mapping if s.startswith('supplementary'))+'\n'
    (WORK/'reference_patterns.txt').write_text(patterns,encoding='utf-8')
    print(json.dumps(dict(move_directories=len(mapping),review_directories=sum(s.startswith('supplementary') for s in mapping),
        files=len(files),GiB=sum(f['bytes'] for f in files)/2**30,tracked_files=len(tracked_moves),retained_reviews=sum(r['disposition']=='KEEP_IN_PLACE' for r in rows))))


if __name__=='__main__':main()
