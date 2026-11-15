"""Author-authorized 24h-only RHS substitution; not a production runner option."""
from pathlib import Path
import hashlib,json,math


def apply_window_budget(art, budget_path, source_output, year, hours, output):
    budget_path=Path(budget_path)
    budget=json.loads(budget_path.read_text(encoding='utf-8'))
    source_sha=hashlib.sha256((Path(source_output)/'result_manifest.json').read_bytes()).hexdigest()
    if hours!=24 or budget['hour_indices']!=list(range(24)) or budget['year']!=year:
        raise ValueError('Window budget requires matching 24h year/window')
    if budget['status']!='PASS' or budget['source_result_manifest_sha256']!=source_sha:
        raise ValueError('Window budget source mismatch')
    value=budget['window_carbon_limit_mt']
    if not math.isfinite(value) or value!=budget['base_window_net_emissions_mt']*(1+1e-4):
        raise ValueError('Window budget formula mismatch')
    if art.index['annual_flow_scaling_factor']!=24/8760:
        raise ValueError('Not the authorized short horizon')
    if art.index['annual_carbon_limit_mtco2_per_year']!=budget['original_annual_carbon_limit_mt']:
        raise ValueError('Production annual budget mismatch')
    row=art.index['constraint_handles']['annual_net_carbon_limit']
    if row.Sense!='<':raise ValueError('Carbon constraint sense changed')
    original=float(row.RHS)
    row.RHS=value
    art.index['selected_horizon_carbon_limit_mtco2']=value
    art.model.update()
    report=dict(status='PASS',year=year,hours=hours,source_result_manifest_sha256=source_sha,
        budget_payload_sha256=hashlib.sha256(budget_path.read_bytes()).hexdigest(),
        original_window_carbon_limit_mt=original,effective_window_carbon_limit_mt=value,
        original_annual_carbon_limit_mt=budget['original_annual_carbon_limit_mt'],
        production_annual_carbon_limit_unchanged=True,scope='TEST_ONLY_TRUNCATED_HORIZON')
    (Path(output)/'window_carbon_override.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report
