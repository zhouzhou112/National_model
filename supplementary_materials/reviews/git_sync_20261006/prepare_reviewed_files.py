"""Produce an explicit Git staging list and scan selected text for secret literals.

Does not stage files. Credential candidates are excluded by name without reading.
Binary outputs, source snapshots and manuscript material are not selected.
"""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
def gitpaths(*args):
    return [p.decode() for p in subprocess.check_output(['git',*args,'-z'],cwd=ROOT).split(b'\0') if p]

def main():
    paths=set(gitpaths('diff','--name-only'))
    paths.discard('supplementary_materials/MODEL_V0719_REVIEW_REPORT.md')
    paths.update(s for s in gitpaths('ls-files','--others','--exclude-standard') if s.split('/')[0] in {'cispo_model','config','scripts','tests'})
    paths.update(['DOCUMENT_STATUS_20261002.md','SCENARIO_EXECUTION_PLAN_20261002.md','STAGE_A_PRESERVATION.md'])
    review_names=['barrier_jump_diagnosis_20261002','base_2040_continuation_20260919','base_2050_continuation_20260930','base_numeric_failure_20260913','base_regression_explanation_20260915','base_v9_terminal_20260919','cloud_failure_comparison_20260915','convergence_eta_20261004','crossover_contract_20260913','dac_year_schedule_20260913','deployed_repair_audit_20260915','dual_screening_20261002','factor_pair_8760_20261005','formal_launch_20260914','formal_launch_failure_20260914','numeric_applied_verification_20260915','numeric_doublecheck_20260913','numeric_prelaunch_20260913','numeric_repair_20260913','numeric_resolution_20260913','numerical_robustness_20261005','reservoir_storage_audit_20260913','solve_feasibility_vs_thermal_20260913','solver_alignment_thermal_20260913','thread_comparison_20260930','tiny_bound_audit_20261004','tolerance_1e4_readiness_20260913','validation_coordination_20261005','git_sync_20261006']
    # Reports and executable provenance only; bulk raw evidence stays local.
    allowed={'.md','.py','.sh','.sbatch','.json','.csv'}
    for name in review_names:
        d=ROOT/'supplementary_materials/reviews'/name
        for p in d.iterdir():
            if p.is_file() and p.suffix in allowed and p.stat().st_size<1024**2:
                if name=='git_sync_20261006' and p.name in {'selected_files.json','secret_scan.json','publication_validation.json'}:continue
                paths.add(p.relative_to(ROOT).as_posix())
    selected_json=['factor_pair_8760_20261005/final_assessment.json','numerical_robustness_20261005/server_evidence/20261006T2114Z/final_comparison.json','validation_coordination_20261005/unittest_verified_20261005T185140Z.json','validation_coordination_20261005/final_source_integrity_20261006.json','git_sync_20261006/inventory_summary.json','git_sync_20261006/cloud_versions.json','git_sync_20261006/fixed_versions.json']
    paths.update('supplementary_materials/reviews/'+p for p in selected_json)
    paths.add('supplementary_materials/reviews/validation_coordination_20261005/unittest_verified_20261005T185140Z.log')
    for s in ['GIT_SYNC_POLICY_ZH.md','AGENTS.md']:
        if (ROOT/s).is_file():paths.add(s)
    # Preserve malformed historical outputs locally; never repair raw evidence.
    paths.difference_update({
        'supplementary_materials/reviews/formal_launch_20260914/remote_preflight_result.json',
        'supplementary_materials/reviews/solve_feasibility_vs_thermal_20260913/thermal_readback.json',
    })
    dangerous=re.compile(r'(?:^|/)(?:\.env(?:\..*)?|id_rsa.*|id_ed25519.*|gurobi\.lic|credentials[^/]*)$|\.(?:pem|key|lic)$|ssh\.txt$',re.I)
    rules={
      'private_key':re.compile(r'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----'),
      'github_token':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b'),
      'aws_key':re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
      'literal_secret':re.compile(r'''(?i)(?:password|passwd|wlssecret|access_token|api_key)\s*[=:]\s*["']([^"'\n]{8,})["']'''),
    }
    findings=[];manifest=[]
    for s in sorted(paths):
        p=ROOT/s
        if dangerous.search(s):raise ValueError('Credential candidate excluded: '+s)
        b=p.read_bytes()
        if len(b)>5*1024**2 or b'\0' in b:raise ValueError('Unexpected large/binary candidate: '+s)
        text=b.decode('utf-8-sig')
        for rule,pattern in rules.items():
            for m in pattern.finditer(text):
                # Patterns in the scanner itself are not credentials.
                if p.name=='prepare_reviewed_files.py':continue
                findings.append(dict(path=s,line=text[:m.start()].count('\n')+1,rule=rule))
        manifest.append(dict(path=s,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    (HERE/'selected_files.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (HERE/'secret_scan.json').write_text(json.dumps({'findings':findings,'file_count':len(manifest),'bytes':sum(x['bytes'] for x in manifest)},indent=2)+'\n')
    (HERE/'staging_paths.txt').write_text('\n'.join(x['path'] for x in manifest)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest),'findings':findings},indent=2))

if __name__=='__main__':main()
