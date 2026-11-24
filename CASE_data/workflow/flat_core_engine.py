"""Finite, read-only postprocessing of verified originals into a versioned library.

Run on T550. Does not import the model or solver, move originals, or traverse credentials.
Each completed case has the same core file set and CSV columns. Failed/test cases
retain identity and inventories, with explicit scientific-data NOT_APPLICABLE.
"""
import csv
import hashlib
import json
import os
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path('/home/zz2/National_model_server')
DEST = BASE/'case_library_v2_20261123'
HERE = Path(__file__).resolve().parent
SERVICES = ['heating', 'cooling', 'ev_v1g', 'ev_v2g']
NATIVE = {
    'cost_components.csv': '02_costs.csv',
    'annual_capacity_by_province_technology.csv': '03_capacity.csv',
    'annual_generation_by_province_technology.csv': '04_generation.csv',
    'storage_capacity.csv': '05_storage_capacity.csv',
    'annual_storage_operation_by_technology.csv': '06_storage_annual.csv',
    'transmission_capacity.csv': '07_interprovince_network.csv',
    'load_center_intra_transmission.csv': '08_city_network.csv',
    'annual_adequacy_by_province.csv': '09_adequacy.csv',
    'annual_resource_accounting_by_province.csv': '10_resource_accounting.csv',
    'annual_constraint_shadow_prices.csv': '11_annual_constraint_duals.csv',
    'dac_capacity_capture.csv': '12_dac.csv',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def table(path, records, columns=None):
    frame = records if isinstance(records, pd.DataFrame) else pd.DataFrame(records, columns=columns)
    frame.to_csv(path, index=False, lineterminator='\n')


def file_category(name):
    name = name.lower()
    if any(x in name for x in ('mps', 'barx', 'barpi', 'checkpoint', 'archive')):
        return 'model_and_solution'
    if any(x in name for x in ('dispatch', 'hourly', 'flows.npz')):
        return 'hourly_arrays'
    if any(x in name for x in ('state', 'cohort')):
        return 'continuation_state'
    if any(x in name for x in ('accept', 'qc', 'certificate', 'pricing', 'audit')):
        return 'acceptance_and_audit'
    if name.endswith(('.log', '.err', '.out', '.jsonl')):
        return 'logs'
    return 'tables_and_identity'


def analyze(item, schemas):
    c = item['catalog']; release = c['release']; source = BASE/'cloud_backup'/release
    expected = INPUT['remote_inventory']['cases'][release]
    assert source.is_dir() and sha(source/'backup_manifest.json') == expected['backup_manifest_sha256']
    backup = json.loads((source/'backup_manifest.json').read_text())
    assert expected['backup_status'] == 'COMPLETE'
    entries = {f['path']: f for f in backup['files']}
    original_stats = {}
    for name, f in entries.items():
        p = source/name
        assert p.is_file() and p.stat().st_size == f['bytes'], p
        original_stats[name] = (p.stat().st_size, p.stat().st_mtime_ns)
    checked = {}

    def verified(name):
        key = 'output_8760/'+name
        p = source/key
        entry = entries[key]
        if key not in checked:
            actual = sha(p)
            assert actual == entry['sha256'], p
            checked[key] = dict(path=str(p), bytes=p.stat().st_size, sha256=actual)
        return p

    relative = Path('by_case')/c['case']/str(c['year'])/release
    dest = DEST/relative
    # A finished case can be resumed only by validating its existing manifest.
    manifest_path = dest/'core_manifest.json'
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        assert old['source_backup_manifest_sha256'] == expected['backup_manifest_sha256']
        for name, info in old['files'].items():
            assert sha(dest/name) == info['sha256']
        for f in (dest/'core').glob('*.csv'):
            header = next(csv.reader(f.open(encoding='utf-8')))
            if f.name in schemas:
                assert schemas[f.name] == header, f
            schemas[f.name] = header
        return old['summary']
    assert not dest.exists(), 'Partial case preserved; inspect before resuming: '+str(dest)
    core = dest/'core'; core.mkdir(parents=True)
    (dest/'full_backup').symlink_to(source, target_is_directory=True)
    analysis = []
    roots = [p for p in source.iterdir() if p.is_dir() and p.name not in ('output_8760', '.rsync-partial')]
    label = ('case3_'+str(c['year']) if c['case']=='Case3' else
             'nocredit_'+str(c['year']) if c['case']=='nocredit' else c['case'].lower()+str(c['year']))
    if c['kind'] in ('COMPLETED_PRODUCTION', 'COMPLETED_DIAGNOSTIC'):
        for stem in ('analysis_tools_20261020', 'analysis_tools_20261105_metrics', 'analysis_tools_20261105_t9', 'analysis_tools_20261106_deep_review'):
            for suffix in ('', '_spatial_v1'):
                p = BASE/stem/(label+suffix)
                if p.is_dir():
                    roots.append(p)
    links = dest/'analysis_links'; links.mkdir()
    for n, p in enumerate(sorted(set(roots))):
        link = links/f'{n+1:02d}_{p.name}'
        link.symlink_to(p, target_is_directory=True)
        files = []
        for folder, dirs, names in os.walk(p, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.rsync-partial')]
            for name in names:
                f = Path(folder)/name
                if f.is_file():
                    files.append(dict(path=str(f), bytes=f.stat().st_size))
        analysis.append(dict(path=str(p), library_link=str(link), files=files,
                             index_scope='paths_and_bytes_only_not_a_new_integrity_certificate'))
    inventory = [dict(category=file_category(name), path=str(source/name), relative_path=name,
                      bytes=f['bytes'], sha256=f['sha256'], hash_basis='verified_backup_manifest')
                 for name, f in entries.items()]
    table(core/'90_remote_files.csv', inventory)
    save(core/'91_remote_directories.json', dict(full_backup=str(source), organized_entry=str(dest),
         analysis_directories=analysis, local_policy='Only compact core; full originals remain on T550'))
    accepted = item['accepted_evidence']
    save(core/'20_acceptance.json', dict(schema_version=1, catalog_status=c['acceptance_status'],
         kind=c['kind'], evidence=accepted, interpretation='Existing reviewed decision; no new acceptance calculation',
         no_solution_reason=None if accepted else c['kind']))
    science = c['kind'] in ('COMPLETED_PRODUCTION', 'COMPLETED_DIAGNOSTIC')
    quality = dict(source_original_files=len(entries), no_solver_loaded=True)
    if science:
        mp = verified('result_manifest.json')
        assert sha(mp) == expected['source_result_manifest_sha256']
        annual = json.loads(verified('annual_summary.json').read_text())
        solve = json.loads(verified('solve_report.json').read_text())
        carbon = json.loads(verified('annual_carbon_ccs.json').read_text())
        config = json.loads(verified('model_config_snapshot.json').read_text())['resolved_configuration']
        assert int(annual['planning_year']) == c['year'] and annual['optimization_hours'] == 8760
        save(core/'01_annual_summary.json', dict(annual=annual, carbon=carbon,
             barrier_metrics=solve['solution_contract']['barrier_primal_dual_metrics'],
             solver_status=solve['status'], iterations=solve.get('iteration_counts'),
             runtime_seconds=solve.get('runtime_seconds'), quality=solve.get('solution_quality'),
             native_qc_status=solve.get('solution_qc_status'), current_acceptance=c['acceptance_status']))
        for src, target in NATIVE.items():
            frame = pd.read_csv(verified(src), keep_default_na=False)
            table(core/target, frame)
        annual_flex = pd.read_csv(verified('annual_flexible_load_by_province.csv')).set_index('province_code')
        flex_enabled = bool(annual['flexible_load_enabled'])
        service_rows = []
        if flex_enabled:
            f = np.load(verified('flexible_load_dispatch.npz'), allow_pickle=False)
            p = f['province_codes'].astype(int)
            assert np.array_equal(f['hour_index'], np.arange(8760)) and len(p)==31
            assert list(f['flexible_service_names']) == SERVICES
            frac = float(config['flexible_load']['ev_v1g']['shiftable_energy_fraction'])
            alpha=f['ev_enrolled_service_fraction'][:,None]; beta=f['ev_bidirectional_service_fraction'][:,None]
            delta=np.stack((f['actual_heating_gw']-f['baseline_heating_gw'],f['actual_cooling_gw']-f['baseline_cooling_gw'],
                f['ev_v1g_pool_charge']-(alpha-beta)*frac*f['baseline_ev_gw'],
                f['ev_v2g_pool_charge']-beta*frac*f['baseline_ev_gw']-f['ev_v2g_discharge_gw']), axis=1)
            closure=float(np.max(np.abs(delta.sum(axis=1)-(f['effective_total_load_gw']-f['baseline_total_load_gw']))))
            assert closure <= 1e-6, (release,closure)
            quality['service_decomposition_max_abs_gw']=closure
            contracts=f['flexible_service_capacity_gw']; credits=f['firm_flexible_capacity_credit_gw']
            np.testing.assert_allclose(contracts, annual_flex.loc[p, ['contracted_'+s+'_flexibility_gw' for s in SERVICES]],atol=1e-9,rtol=0)
            down=np.maximum(-delta,0).sum(axis=2); up=np.maximum(delta,0).sum(axis=2)
            for i,province in enumerate(p):
                for j,s in enumerate(SERVICES):
                    cap=float(contracts[i,j]); service_rows.append(dict(province_code=int(province),service=s,
                        applicability='ENABLED',contract_gw=cap,firm_credit_gw=float(credits[i,j]),
                        down_regulation_gwh=float(down[i,j]),up_regulation_gwh=float(up[i,j]),
                        net_load_change_gwh=float(up[i,j]-down[i,j]),
                        equivalent_down_hours=float(down[i,j]/cap) if cap>1e-10 else None))
            f.close()
        else:
            # No numerical values are invented for disabled services.
            for province in annual_flex.index:
                for s in SERVICES:
                    service_rows.append(dict(province_code=int(province),service=s,applicability='DISABLED_BY_SCENARIO',
                        contract_gw=None,firm_credit_gw=None,down_regulation_gwh=None,up_regulation_gwh=None,
                        net_load_change_gwh=None,equivalent_down_hours=None))
        table(core/'13_flex_services.csv',service_rows)
        with np.load(verified('vre_dispatch.npz'),allow_pickle=False) as v:
            rows=[]; vg=v['generation_gw'];va=v['available_gw']
            for i,p in enumerate(v['province_codes']):
                for j,t in enumerate(v['technologies'].astype(str)):
                    gen=float(vg[i,j].sum()); available=float(va[i,j].sum())
                    rows.append(dict(province_code=int(p),technology=t,generation_gwh=gen,available_gwh=available,curtailment_gwh=available-gen))
            frame=pd.DataFrame(rows); np.testing.assert_allclose(frame.curtailment_gwh.sum(),annual['vre_curtailment_gwh'],atol=1e-5,rtol=1e-10)
            table(core/'14_vre_curtailment.csv',frame)
        with np.load(verified('storage_dispatch.npz'),allow_pickle=False) as v:
            rows=[];se=v['energy_capacity_gwh'];sd=v['discharge_gw'];sc=v['charge_gw']
            for i,p in enumerate(v['province_codes']):
                for j,t in enumerate(v['technologies'].astype(str)):
                    energy=float(se[i,j]); dis=float(sd[i,j].sum())
                    rows.append(dict(province_code=int(p),technology=t,charge_gwh=float(sc[i,j].sum()),
                        discharge_gwh=dis,energy_capacity_gwh=energy,equivalent_full_discharge_cycles=dis/energy if energy>1e-10 else None))
            frame=pd.DataFrame(rows);np.testing.assert_allclose([frame.charge_gwh.sum(),frame.discharge_gwh.sum()],
                [annual['storage_charge_gwh'],annual['storage_discharge_gwh']],atol=1e-5,rtol=1e-10)
            table(core/'15_storage_operation.csv',frame)
        with np.load(verified('thermal_dispatch.npz'),allow_pickle=False) as v:
            rows=[];ts=v['startup_capacity_gw'];tt=v['shutdown_capacity_gw'];caps=pd.read_csv(verified('thermal_nuclear_capacity.csv')).set_index(['province_code','technology'])
            for i,p in enumerate(v['province_codes']):
                for j,t in enumerate(v['technologies'].astype(str)):
                    cap=float(caps.loc[(p,t),'capacity_gw']); start=float(ts[i,j].sum());stop=float(tt[i,j].sum())
                    rows.append(dict(province_code=int(p),technology=t,capacity_gw=cap,startup_capacity_sum_gw=start,
                        shutdown_capacity_sum_gw=stop,equivalent_full_capacity_starts=start/cap if cap>1e-10 else None,
                        equivalent_full_capacity_shutdowns=stop/cap if cap>1e-10 else None))
            table(core/'16_thermal_operation.csv',rows)
    save(core/'00_identity.json', dict(schema_version=1,case=c['case'],year=c['year'],release=release,kind=c['kind'],
        scientific_tables='COMPLETE' if science else 'NOT_APPLICABLE_NO_PRODUCTION_SOLUTION',
        backup_manifest_sha256=expected['backup_manifest_sha256'],source_result_manifest_sha256=expected.get('source_result_manifest_sha256'),
        full_backup=str(source),catalog_acceptance=c['acceptance_status'],original_catalog_entry=c))
    # Validate common columns and original statistics after all reads.
    for p in core.glob('*.csv'):
        header=next(csv.reader(p.open(encoding='utf-8')))
        if p.name in schemas:
            assert schemas[p.name] == header, (p.name,schemas[p.name],header)
        schemas[p.name]=header
    for name, before in original_stats.items():
        p=source/name;assert (p.stat().st_size,p.stat().st_mtime_ns)==before, 'Original changed: '+str(p)
    assert sha(source/'backup_manifest.json')==expected['backup_manifest_sha256']
    save(core/'92_provenance.json',dict(checked_source_files=checked,quality=quality,original_stats_unchanged=True,
        method='Native annual tables normalized; NPZ reduced on T550 using the existing service-pool formula',
        limitations=['Annual constraint duals are engineering shadow values, not settlement prices or complete hourly load prices',
        'Thermal equivalent starts are continuous-capacity equivalents, not discrete unit starts',
        'V2G down regulation is net against its own contracted pool; do not add discharge twice',
        'Blank disabled-service quantities mean not applicable, not missing-export zeros',
        'All 29 registered runs covered; this is not an inventory of every historical engineering test']))
    (dest/'README.md').write_text(f'# {c["case"]} {c["year"]}\n\n类型：{c["kind"]}；验收：{c["acceptance_status"]}。\n\n'
        'core/ 是统一轻量核心包。full_backup/ 是原件导航链接；analysis_links/ 指向既有分析，目标均未移动或改写。\n\n'
        '完整路径与大文件 SHA 见 core/90_remote_files.csv；分析文件位置见 core/91_remote_directories.json。\n',encoding='utf-8')
    files={str(p.relative_to(dest)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in core.iterdir() if p.is_file()}
    files['README.md']=dict(bytes=(dest/'README.md').stat().st_size,sha256=sha(dest/'README.md'))
    assert max(f['bytes'] for f in files.values())<=1024**2 and sum(f['bytes'] for f in files.values())<=3*1024**2
    summary=dict(case=c['case'],year=c['year'],release=release,kind=c['kind'],acceptance=c['acceptance_status'],
        relative_directory=str(relative),core_files=len(files)-1,core_bytes=sum(x['bytes'] for x in files.values()),
        source_backup=str(source),analysis_directories=len(analysis),original_files=len(entries),scientific_tables=science)
    save(manifest_path,dict(source_backup_manifest_sha256=expected['backup_manifest_sha256'],files=files,summary=summary))
    print(json.dumps(summary),flush=True)
    return summary


def main():
    global INPUT
    INPUT=json.loads((HERE/'library_inputs.json').read_text())
    DEST.mkdir(exist_ok=True)
    if (DEST/'LIBRARY_COMPLETE.json').exists():
        raise RuntimeError('Library already complete; verify it rather than rebuilding')
    schemas={}; summaries=[]
    for item in INPUT['cases']:
        summaries.append(analyze(item,schemas))
    science=[x for x in summaries if x['scientific_tables']]
    sets=[{p.name for p in (DEST/x['relative_directory']/'core').iterdir()} for x in science]
    assert all(s==sets[0] for s in sets), 'Core file sets differ'
    save(DEST/'schema.json',dict(version=1,csv_columns=schemas,scientific_core_files=sorted(sets[0]),
        categories={'00':'身份','01':'年度汇总与求解质量','02':'成本','03':'容量','04':'发电','05-06':'储能',
        '07-08':'网络','09-10':'充裕度与资源','11':'年度约束影子值','12':'DAC','13':'柔性签约与调用',
        '14':'弃风光','15-16':'储能和火电运行','20':'已有验收全文','90-92':'远端原件、分析目录与溯源'}))
    save(DEST/'catalog.json',dict(cases=summaries))
    (DEST/'README.md').write_text('# 求解案例资料库\n\n按 by_case/情景/年份/release 组织。core 为统一轻量结果；full_backup 与 analysis_links 是只用于导航的符号链接，原件未移动。\n\n25 个生产案例、1 个诊断案例、1 个排序测试、2 个失败尝试。后两类无生产结果表，不混入科学比较。\n\n所有 core 在 T550 从校验后的原件预处理；原始 MPS、BarX/BarPi、逐时数组只保留在备份树。\n',encoding='utf-8')
    package=HERE/'core_library.tar.gz'
    with tarfile.open(package,'w:gz') as tar:
        for name in ('README.md','schema.json','catalog.json'):
            tar.add(DEST/name,arcname=name)
        for row in summaries:
            p=DEST/row['relative_directory']
            for name in ('README.md','core_manifest.json','core'):
                tar.add(p/name,arcname=str(Path(row['relative_directory'])/name))
    receipt=dict(status='PASS',created_at_utc=datetime.now(timezone.utc).isoformat(),cases=len(summaries),
        scientific_cases=len(science),uniform_scientific_file_count=len(sets[0]),
        total_core_bytes=sum(x['core_bytes'] for x in summaries),archive_bytes=package.stat().st_size,
        archive_sha256=sha(package),library=str(DEST),source_originals_modified=False,solver_loaded=False)
    save(DEST/'LIBRARY_COMPLETE.json',receipt);save(HERE/'library_receipt.json',receipt)
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    main()
