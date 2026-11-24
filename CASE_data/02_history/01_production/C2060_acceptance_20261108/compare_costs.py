"""One-shot T550 cost accounting comparison; immutable originals, new sidecars."""
import base64
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys

RELEASES = {
    'Base': '20261012_base2060_v9a12_t48_m750_tol1e4_v1',
    'B': '20261027_basefrozen_2060_v9a12_agg0_t48_m750_tol1e4_v2',
    'C': '20261030_lateentry_2060_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def remote():
    base = Path('/home/zz2/National_model_server/cloud_backup')
    out = base / RELEASES['C'] / 'cost_comparison_20261108'
    if out.exists():
        raise FileExistsError('Review prior comparison before retry: ' + str(out))
    sources, costs, metrics, checks, configurations = {}, {}, {}, {}, {}
    for case, release in RELEASES.items():
        root = base / release / 'output_8760'
        backup_path = root.parent / 'backup_manifest.json'
        backup = json.loads(backup_path.read_text())
        manifest_bytes = (root / 'result_manifest.json').read_bytes()
        assert backup['status'] == 'COMPLETE'
        assert digest(manifest_bytes) == backup['source_result_manifest_sha256']
        entries = {e['path']: e for e in json.loads(manifest_bytes)['files']}
        verified, raw = {}, {}
        for name in ('cost_components.csv', 'solve_report.json', 'model_config_snapshot.json'):
            raw[name] = (root / name).read_bytes()
            e = entries[name]
            assert digest(raw[name]) == e['sha256'] and len(raw[name]) == e['bytes'], (case, name)
            verified[name] = dict(bytes=len(raw[name]), sha256=digest(raw[name]))
        rows = list(csv.DictReader(io.StringIO(raw['cost_components.csv'].decode('utf-8-sig'))))
        assert all(int(r['optimization_hours']) == 8760 and r['result_use'] == 'SCIENTIFIC_PRODUCTION' for r in rows)
        costs[case] = {r['cost_component']: r for r in rows}
        configurations[case] = json.loads(raw['model_config_snapshot.json'])['resolved_configuration']
        assert len(costs[case]) == len(rows)
        solve = json.loads(raw['solve_report.json'])
        assert solve['status'] == 'OPTIMAL'
        m = solve['solution_contract']['barrier_primal_dual_metrics']
        metrics[case] = dict(P=float(m['primal_objective']), D=float(m['dual_objective']))
        primary = math.fsum(float(r['value_million_cny_per_year']) for r in rows if r['included_in_primary_cost'].lower() == 'true')
        operation = math.fsum(float(r['value_million_cny_per_year']) for r in rows if r['cost_component'].startswith('operating_') and not r['cost_component'].startswith('operating_detail_'))
        annual_operation = float(costs[case]['annual_operation']['value_million_cny_per_year'])
        tol = max(1e-5, 1e-7 * metrics[case]['P'])
        assert abs(primary - metrics[case]['P']) <= tol, (case, primary, metrics[case])
        assert abs(operation - annual_operation) <= tol, (case, operation, annual_operation)
        checks[case] = dict(primary_sum=primary, objective=metrics[case]['P'], primary_difference=primary-metrics[case]['P'], operation_detail_sum=operation, annual_operation=annual_operation, operation_difference=operation-annual_operation, tolerance_million_cny=tol)
        sources[case] = dict(release=release, result_manifest_sha256=digest(manifest_bytes), backup_manifest_sha256=digest(backup_path.read_bytes()), files=verified)
    # Base lacks the eight flexible-load rows because its feature is disabled.
    # Permit only this evidenced difference; never fill arbitrary missing data.
    assert set(costs['B']) == set(costs['C']), 'B/C component sets differ'
    missing = set(costs['C']) - set(costs['Base'])
    assert not (set(costs['Base']) - set(costs['C']))
    allowed = {
        'operating_flexible_load_v5_enablement',
        'operating_flexible_load_v5_v2g_infrastructure',
        'operating_flexible_load_v5_thermal_activation',
        'operating_flexible_load_v5_ev_v1g_relocation',
        'operating_flexible_load_v5_ev_v2g_participation',
        'operating_flexible_load_v5_ev_v2g_degradation',
        'operating_detail_flexible_load_v5_thermal_release',
        'operating_detail_flexible_load_v5_thermal_precondition',
    }
    assert missing <= allowed and configurations['Base']['features']['flexible_load'] is False
    for name in missing:
        costs['Base'][name] = dict(costs['C'][name], value_million_cny_per_year='0')
    checks['missing_Base_components'] = dict(names=sorted(missing), treatment='zero; archived Base configuration flexible_load=false; all other components required')
    tables = {'primary_cost_comparison.csv': [], 'operating_cost_comparison.csv': []}
    for name in costs['C']:
        rows = [costs[c][name] for c in RELEASES]
        flags = [r['included_in_primary_cost'].lower() == 'true' for r in rows]
        assert len(set(flags)) == 1, name
        if flags[0]:
            table = 'primary_cost_comparison.csv'
        elif name.startswith('operating_') and not name.startswith('operating_detail_'):
            table = 'operating_cost_comparison.csv'
        else:
            continue
        values = {c: float(costs[c][name]['value_million_cny_per_year']) for c in RELEASES}
        tables[table].append(dict(cost_component=name, **{c+'_million_cny': v for c,v in values.items()}, Base_minus_C_yi_cny=(values['Base']-values['C'])/100, B_minus_C_yi_cny=(values['B']-values['C'])/100))
    acceptance_path = base / RELEASES['C'] / 'author_review_20261108/acceptance_author_20261108.json'
    acceptance = json.loads(acceptance_path.read_text())
    assert acceptance['status'] == 'PASS'
    bound = acceptance['certificate']['B_million_cny']
    summary = dict(status='PASS', computed_on='T550', units='million CNY/year; savings columns yi CNY/year', accounting='Primary table is additive; operating table decomposes annual_operation and must not be added again. Diagnostic detail rows excluded.', metrics=metrics, checks=checks, sources=sources, acceptance_sha256=digest(acceptance_path.read_bytes()), C_B_million_cny=bound, Base_minus_C_point_yi_cny=(metrics['Base']['P']-metrics['C']['P'])/100, B_minus_C_point_yi_cny=(metrics['B']['P']-metrics['C']['P'])/100, Base_minus_C_engineering_interval_yi_cny=[(metrics['Base']['D']-metrics['C']['P'])/100,(metrics['Base']['P']-metrics['C']['D']+bound)/100], interval_label='BARRIER_DUAL_ENGINEERING_GRADE; author comparison rule; not market settlement')
    out.mkdir()
    (out/'comparison_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    for name, rows in tables.items():
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    payload={}
    for p in out.iterdir():
        raw=p.read_bytes(); assert len(raw)<1024**2
        payload[p.name]=dict(bytes=len(raw),sha256=digest(raw),base64=base64.b64encode(raw).decode())
    print(json.dumps(dict(remote_directory=str(out),files=payload)))


def local():
    here=Path(__file__).resolve().parent
    assert not (here/'cost_comparison_receipt.json').exists()
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','HostName=127.0.0.1','-o','BindAddress=127.0.0.1','national-model-server']
    r=subprocess.run(ssh+['/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python - --remote'],input=Path(__file__).read_text(),text=True,encoding='utf-8',capture_output=True,timeout=180)
    (here/'cost_comparison_transport.stderr.log').write_text(r.stderr,encoding='utf-8')
    r.check_returncode(); result=json.loads(r.stdout)
    target=here/'cost_comparison';target.mkdir(exist_ok=True)
    for name,e in result['files'].items():
        raw=base64.b64decode(e.pop('base64'));assert len(raw)==e['bytes'] and digest(raw)==e['sha256']
        with (target/name).open('xb') as f:f.write(raw)
    (here/'cost_comparison_receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print((target/'comparison_summary.json').read_text())


if __name__=='__main__':
    remote() if '--remote' in sys.argv else local()
