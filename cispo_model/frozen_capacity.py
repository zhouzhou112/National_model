"""Opt-in Base-frozen investment bounds; operational decisions remain free.

GW, GWh and MtCO2/year are kept separate. Sources are joined by stable keys,
never table positions. Original sources and bounds are retained in the audit.
"""
from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd

PROFILE_ID = "barrier_stagea_base_frozen_agg0_v1_threads48"
RESOURCE_PROFILE_ID = "barrier_stagea_base_frozen_agg0_v1_threads44"
PROFILE_IDS = frozenset({PROFILE_ID, RESOURCE_PROFILE_ID})
RESTRICTED_RESOURCE_PROFILE_ID = 'barrier_stagea_resource_restricted_agg0_v1_threads44'
RESOURCE_FACTOR_PROFILE_ID = 'barrier_factor_resource_restricted_2050_threads44'
SELECTION_SCHEMA = 'capacity_bound_selection_v1'
TABLE_KEYS = {
    "vre_capacity.csv": ["grid_uid", "technology"],
    "thermal_nuclear_capacity.csv": ["province_code", "technology"],
    "storage_capacity.csv": ["province_code", "technology"],
    "transmission_capacity.csv": ["line_id"],
    "load_center_intra_transmission.csv": ["intra_edge_id"],
    "intra_grid_vre_site_design.csv": ["grid_uid", "technology"],
    "intra_grid_substation_design.csv": ["substation_id"],
    "hydro_capacity.csv": ["hydrochn_row_id"],
    "wave_capacity.csv": ["grid_uid"],
    "dac_capacity_capture.csv": ["province_code", "technology"],
    "hydro_spur_capacity.csv": ["hydrochn_row_id"],
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def manifest_size_bytes(value):
    """Read integer byte counts, including legacy CSV strings such as 8354.0."""
    try:
        size = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError('Invalid upstream byte count') from error
    if not size.is_finite() or size < 0 or size != size.to_integral_value():
        raise ValueError('Upstream byte count must be a nonnegative integer')
    return int(size)


def archived_candidate_flag(environment, scope, metadata):
    """Restore the actual recorded CLI flag, not a newer scope-label spelling."""
    command = environment.get('command', [])
    if not isinstance(command, list) or command.count('--state-in') != 1:
        raise ValueError('Missing/ambiguous archived state-in command')
    position = command.index('--state-in') + 1
    original = environment.get('planning_state_in')
    if position >= len(command) or command[position] != original or scope.get('state_in') != original:
        raise ValueError('Archived command/environment/scope upstream mismatch')
    flag = '--allow-candidate-state-in' in command
    if bool(metadata.get('candidate_unaccepted')) != flag:
        raise ValueError('Archived candidate CLI flag disagrees with state metadata')
    return flag


def checked_file(root, record):
    path = (Path(root) / record['path']).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('Frozen manifest path escapes source')
    if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
        raise ValueError(f'Frozen source SHA/bytes mismatch: {path}')
    return path


def read_source(source, supplement, year):
    """Verify semantic tables against the original manifest and supplement."""
    source, supplement = Path(source).resolve(), Path(supplement).resolve()
    manifest_path = source/'result_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('planning_year') != year:
        raise ValueError('Frozen source must have the same planning year')
    records = {r['path']: r for r in manifest['files']}
    identity = json.loads(checked_file(source, records['run_identity.json']).read_text(encoding='utf-8'))
    if identity['analysis_case']['scenario_id'] != 'base':
        raise ValueError('Frozen capacity source must be Base')
    evidence = dict(source_directory=str(source), source_release=source.parent.name,
                    result_manifest_sha256=digest(manifest_path), tables={})
    tables = {}
    for name, keys in TABLE_KEYS.items():
        if name == 'hydro_spur_capacity.csv':
            sp = supplement/'supplement_manifest.json'
            receipt = json.loads(sp.read_text(encoding='utf-8'))
            crosscheck = receipt.get('vre_crosscheck', {})
            if (receipt.get('status') != 'PASS' or crosscheck.get('passed') is not True
                    or crosscheck.get('tolerance_gw', np.inf) > 1e-9
                    or crosscheck.get('max_abs_difference_gw', np.inf) > 1e-9
                    or receipt.get('result_manifest_sha256') != evidence['result_manifest_sha256']
                    or receipt.get('vector_attribute') not in {'X', 'BarX'}):
                raise ValueError('Hydro spur supplement lacks verified Base/VRE identity')
            for checked_name in ('vre_capacity.csv','hydro_capacity.csv'):
                if receipt['source_table_sha256'][checked_name] != records[checked_name]['sha256']:
                    raise ValueError('Supplement semantic source mismatch')
            path = checked_file(supplement, receipt['table'])
            evidence['supplement'] = dict(path=str(sp), sha256=digest(sp), vector_attribute=receipt['vector_attribute'])
        else:
            path = checked_file(source, records[name])
        table = pd.read_csv(path, dtype={key: str for key in keys})
        if any(k not in table for k in keys) or table[keys].isna().any().any() or table.duplicated(keys).any():
            raise ValueError(f'Missing/duplicate frozen stable keys: {name}')
        tables[name] = table
        evidence['tables'][name] = dict(path=str(path), sha256=digest(path), bytes=path.stat().st_size, rows=len(table))
    return tables, evidence


def align(table, keys, target, column, *, subset=False):
    if column not in table:
        raise ValueError(f'Missing frozen source column: {column}')
    source = table.copy()
    for k in keys:
        source[k] = source[k].astype(str)
    wanted = pd.DataFrame(target, columns=keys).astype(str)
    if wanted.duplicated(keys).any() or source.duplicated(keys).any():
        raise ValueError('Frozen join must be one-to-one')
    if not subset and len(source) != len(wanted):
        raise ValueError('Frozen key set has extra or missing rows')
    merged = wanted.merge(source[keys+[column]], on=keys, how='left', validate='one_to_one', sort=False)
    values = pd.to_numeric(merged[column], errors='raise').to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Frozen join has missing/nonfinite source values')
    return values


def recover_upstream(source, year):
    """Cross-check archived environment, input SHA manifest and packaged state."""
    source = Path(source).resolve()
    manifest = json.loads((source/'result_manifest.json').read_text(encoding='utf-8'))
    records = {r['path']:r for r in manifest['files']}
    env_path = checked_file(source, records['run_environment.json'])
    inputs_path = checked_file(source, records['input_manifest.csv'])
    env = json.loads(env_path.read_text(encoding='utf-8'))
    inputs = pd.read_csv(inputs_path, keep_default_na=False)
    rows = inputs.loc[inputs.kind == 'planning_state']
    original = env.get('planning_state_in')
    evidence = dict(original_path=original, environment_sha256=digest(env_path),
                    input_manifest_sha256=digest(inputs_path), restored_path=None,
                    allow_candidate=False, files=[])
    if year == 2030:
        if original or len(rows):
            raise ValueError('Base 2030 must have no upstream state')
        return None, evidence
    if not original or rows.empty:
        raise ValueError('Base continuation lacks recorded upstream path/SHA')
    # Only the source release's packaged upstream is allowed, not another chain.
    parts = Path(original).parts
    starts = [i for i,x in enumerate(parts) if x.startswith('upstream_')]
    if len(starts) != 1:
        raise ValueError('Ambiguous Base upstream path')
    relative = Path(*parts[starts[0]:])
    root = (source.parent/relative).resolve()
    if not root.is_relative_to(source.parent) or not root.is_dir():
        raise ValueError('Original Base upstream is not packaged with source release')
    required = {'state_metadata.json','capacity_cohorts.csv.gz','state_transition_summary.csv','../result_manifest.json'}
    if set(rows.logical_path) != required:
        raise ValueError('Base upstream manifest file set mismatch')
    for row in rows.itertuples():
        expected_original = str(Path(original)/row.logical_path)
        if Path(row.resolved_path) != Path(expected_original):
            # Permit normalized ../ paths; do not resolve historical paths locally.
            import posixpath
            if posixpath.normpath(row.resolved_path) != posixpath.normpath(expected_original):
                raise ValueError('Base environment/input-manifest upstream mismatch')
        p=(root/row.logical_path).resolve()
        size_bytes = manifest_size_bytes(row.size_bytes)
        if not p.is_relative_to(source.parent) or p.stat().st_size != size_bytes or digest(p) != row.sha256:
            raise ValueError('Packaged Base upstream SHA mismatch')
        evidence['files'].append(dict(path=row.logical_path,sha256=row.sha256,bytes=size_bytes))
    metadata=json.loads((root/'state_metadata.json').read_text(encoding='utf-8'))
    from .planning_state import PlanningState
    # Candidate inference is verified by the original run's recorded state policy.
    scope_path=checked_file(source,records['run_scope.json'])
    scope=json.loads(scope_path.read_text(encoding='utf-8'))
    allow_candidate=archived_candidate_flag(env,scope,metadata)
    expected_boundary={2040:2030,2050:2040,2060:2050}[year]
    state=PlanningState.load(root,expected_boundary_year=expected_boundary,expected_scenario_id='base',
                             allow_unaccepted_candidate=allow_candidate)
    evidence.update(restored_path=str(root),allow_candidate=allow_candidate,
                    candidate_flag_source='VERIFIED_RUN_ENVIRONMENT_COMMAND_AND_STATE_METADATA',
                    scope_sha256=digest(scope_path),metadata_sha256=digest(root/'state_metadata.json'))
    return state,evidence


def investment_registry(artifacts, data):
    idx=artifacts.index
    provinces=list(map(str,idx['province_codes']))
    result=[]
    def add(variable,table,column,rows,unit='GW',subset=False):
        if variable not in artifacts.variables:
            return
        result.append((variable,table,column,rows,unit,subset))
    vre=data.vre_sites[['grid_uid','technology']].astype(str).values.tolist()
    thermal=[[p,t] for p in provinces for t in idx['thermal_index']]
    storage=[[p,t] for p in provinces for t in idx['storage_index']]
    hydro=data.hydro_stations[['hydrochn_row_id']].astype(str).values.tolist()
    add('vre_new','vre_capacity.csv','new_capacity_gw',vre)
    add('thermal_new','thermal_nuclear_capacity.csv','new_capacity_gw',thermal)
    pairs=idx.get('ccs_pairs',())
    add('thermal_retrofit_to_ccs','thermal_nuclear_capacity.csv','retrofit_out_gw',[[p,pair[0]] for p in provinces for pair in pairs],subset=True)
    add('storage_new','storage_capacity.csv','new_capacity_gw',storage)
    add('phs_energy_capacity','storage_capacity.csv','energy_capacity_gwh',[[p,'phs'] for p in provinces],unit='GWh',subset=True)
    add('line_new','transmission_capacity.csv','new_capacity_gw',data.lines[['line_id']].astype(str).values.tolist())
    add('intra_load_center_new','load_center_intra_transmission.csv','new_capacity_gw',data.intra_load_center_edges[['intra_edge_id']].astype(str).values.tolist())
    add('spur_augmentation','intra_grid_vre_site_design.csv','spur_augmentation_gw',vre)
    add('hydro_spur_augmentation','hydro_spur_capacity.csv','hydro_spur_augmentation_gw',hydro)
    add('trunk_augmentation','intra_grid_substation_design.csv','trunk_augmentation_gw',data.substations[['substation_id']].astype(str).values.tolist())
    add('hydro_new','hydro_capacity.csv','new_capacity_gw',hydro)
    if data.wave is not None:
        add('wave_new','wave_capacity.csv','new_capacity_gw',data.wave.sites[['grid_uid']].astype(str).values.tolist())
    add('dac_new','dac_capacity_capture.csv','new_capacity_mtpa',[[p,t] for p in provinces for t in idx['dac_index']],unit='MtCO2_per_year')
    return result


def apply_frozen_capacity(artifacts, data, tables, evidence, output):
    model=artifacts.model
    model.update()
    audit=[]
    plans=[]
    for variable,table,column,rows,unit,subset in investment_registry(artifacts,data):
        mv=artifacts.variables[variable]
        values=align(tables[table],TABLE_KEYS[table],rows,column,subset=subset).reshape(mv.shape)
        lower,upper=np.asarray(mv.LB),np.asarray(mv.UB)
        if (lower>upper).any():
            raise ValueError('Invalid original investment bounds')
        fixed=np.minimum(np.maximum(values,lower),upper)
        names=np.asarray(mv.VarName).reshape(-1)
        for name,keys,v,lo,up,x in zip(names,rows,values.flat,lower.flat,upper.flat,fixed.flat):
            audit.append(dict(variable=str(name),family=variable,stable_key=json.dumps(keys),source_table=table,
                              source_column=column,unit=unit,base_value=float(v),original_lb=float(lo),original_ub=float(up),
                              frozen_value=float(x),clip_amount=float(x-v)))
        plans.append((mv,fixed))
    frame=pd.DataFrame(audit)
    frame.to_csv(Path(output)/'frozen_capacity_audit.csv',index=False)
    statistics={}
    for unit,part in frame.groupby('unit'):
        absolute=part.clip_amount.abs()
        statistics[unit]=dict(columns=len(part),clipped_columns=int((absolute>0).sum()),
                              sum_absolute_clip=float(absolute.sum()),maximum_absolute_clip=float(absolute.max()))
    report={**evidence,'frozen_columns':len(frame),'clip_statistics':statistics,
            'audit_sha256':digest(Path(output)/'frozen_capacity_audit.csv')}
    # Only the author's MW thresholds have physical meaning here; never add GW,
    # GWh and Mt/year together. Other units remain separately disclosed.
    gw=statistics.get('GW',{})
    exceeded=gw.get('sum_absolute_clip',0)>1e-3 or gw.get('maximum_absolute_clip',0)>1e-5
    report['clip_reporting_threshold_exceeded']=exceeded
    (Path(output)/'frozen_capacity_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if exceeded:
        raise ValueError('Frozen GW clip exceeds author reporting threshold; stop before solve')
    for mv,fixed in plans:
        mv.LB=fixed
        mv.UB=fixed
    model.update()
    artifacts.index['frozen_capacity']=report
    return report


def apply_parameter_override(config, path):
    """Explicit B sensitivity payload; investment/loads/carbon changes forbidden.

Participation/comfort input tables must be prebuilt consistent V5 sources.
They still pass the existing loader's input/physics checks. No data is invented.
"""
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    allowed={'flexible_load','service_costs','contract_upper_fraction','weather'}
    if set(payload)-allowed:
        raise ValueError('B override cannot change load, investment cost, carbon or other model assumptions')
    flex=payload.get('flexible_load',{})
    if set(flex)-{'heating','cooling','ev_v1g','ev_v2g','firm_capacity_credit','v5_input_files'}:
        raise ValueError('Unsupported B flexibility override')
    # Prevent changing state/efficiency/model formulations through nested objects.
    allowed_fields={
        'heating':{'enabled'},'cooling':{'enabled'},
        'ev_v1g':{'enabled','shiftable_energy_fraction'},
        'ev_v2g':{'enabled','participation_fraction','national_contracted_power_cap_gw_by_planning_year'},
        'firm_capacity_credit':{'derating_fraction','derating_fraction_by_planning_year'},
        'v5_input_files':set(config.raw['flexible_load']['v5_input_files']),
    }
    from copy import deepcopy
    for section,values in flex.items():
        if not isinstance(values,dict) or set(values)-allowed_fields[section]:
            raise ValueError(f'Unsupported B override fields: {section}')
        config.raw['flexible_load'][section].update(deepcopy(values))
        if section in {'ev_v1g','ev_v2g'}:
            key='shiftable_energy_fraction' if section=='ev_v1g' else 'participation_fraction'
            if key in values:
                config.raw['flexible_load'][section].pop(key+'_by_planning_year',None)
    for service,fraction in payload.get('contract_upper_fraction',{}).items():
        if service not in {'heating','cooling','ev_v1g','ev_v2g'} or not isinstance(fraction,(int,float)) or not np.isfinite(fraction) or not 0<=fraction<=1:
            raise ValueError('Contract upper fraction must be finite in [0,1]')
    weather=payload.get('weather',{})
    if set(weather)-{'weather_year','weather_source_years','hydro_monthly_profile_file','wave_cf_filename','wave_time_reference_year','input_roots'}:
        raise ValueError('Unsupported B weather source override')
    import os
    for key,value in weather.get('input_roots',{}).items():
        if key not in {'CISPO_CF_ROOT','CISPO_HYDRO_ROOT','CISPO_WAVE_ROOT','CISPO_RAW_GRFR_ROOT'}:
            raise ValueError('Weather override only accepts existing time-series data roots')
        if not isinstance(value,str) or not value:
            raise ValueError('Weather data root must be an explicit path')
        directory=Path(value)
        if not directory.is_absolute():directory=Path(path).resolve().parent/directory
        if not directory.is_dir():raise FileNotFoundError(directory)
        os.environ[key]=str(directory.resolve())
    for key in ('weather_year','weather_source_years'):
        if key in weather:config.raw[key]=weather[key]
    if 'hydro_monthly_profile_file' in weather:
        config.raw['hydro']['provincial_aggregate_monthly_profile_file']=weather['hydro_monthly_profile_file']
    for key,dest in [('wave_cf_filename','cf_filename'),('wave_time_reference_year','time_reference_year')]:
        if key in weather:config.raw['wave_energy'][dest]=weather[key]
    from .config import resolve_flexibility_year
    resolve_flexibility_year(config.raw,config.planning_year)
    config.validate()
    config.raw['frozen_parameter_override']=dict(path=str(Path(path).resolve()),sha256=digest(path),resolved=payload)
    return payload


def override_service_costs(data, payload):
    for service,columns in payload.get('service_costs',{}).items():
        if service not in data.flexible_load_v4.service_costs:
            raise ValueError('Unknown B service cost family')
        existing=data.flexible_load_v4.service_costs[service]
        for key,value in columns.items():
            if key not in existing or not isinstance(value,(int,float)) or not np.isfinite(value) or value<0:
                raise ValueError('B service cost must be an existing field and finite nonnegative number')
            existing[key]=np.full_like(existing[key],float(value),dtype=float)


def apply_contract_upper_fractions(artifacts, payload):
    fractions=payload.get('contract_upper_fraction',{})
    if not fractions:
        return
    model=artifacts.model;model.update()
    mv=artifacts.variables['flexible_service_capacity']
    upper=np.asarray(mv.UB).copy()
    for i,service in enumerate(('heating','cooling','ev_v1g','ev_v2g')):
        upper[:,i]*=fractions.get(service,1.)
    mv.UB=upper
    # Disable the latent fractions too (zero-power regions need not force alpha=0).
    for service,key in [('ev_v1g','ev_enrolled_service_fraction'),('ev_v2g','ev_bidirectional_service_fraction')]:
        var=artifacts.variables.get(key)
        if fractions.get(service)==0 and hasattr(var,'UB'):
            var.UB=np.zeros(var.shape)
    model.update()


def validate_mode(config, args, *, test_only):
    """Fail closed on unrelated solve modes and mismatched production settings."""
    prohibited=('vre_screen_csv','state_in','allow_candidate_state_in','mga_spec','mga_baseline',
                'basis_in','primal_dual_checkpoint_in','recover_stage_a_from','late_entry_base_state',
                'archive_presolved_model','allow_diagnostic_state_in')
    if any(getattr(args,key,None) for key in prohibited):
        raise ValueError('Base-frozen is incompatible with explicit state, screening, MGA, starts or Stage B')
    scenario=config.raw['scenario']['id']
    if scenario!='case3_thermal_ev_v5' and not (test_only and scenario=='base' and not config.raw['features']['flexible_load']):
        raise ValueError('Base-frozen requires case3; Base is only the truncated identity control')
    if config.raw.get('candidate_screen',{}).get('enabled'):
        raise ValueError('Base-frozen cannot use candidate screening')
    if not test_only:
        profile_id = config.raw.get('solver_profile',{}).get('id')
        if profile_id not in PROFILE_IDS:
            raise ValueError('Base-frozen requires its reviewed production profile')
        expected=json.loads((Path(__file__).resolve().parents[1]/'config/solver_profiles'/f'{profile_id}.json').read_text())
        if any(config.raw['numerics'].get(k)!=v for k,v in expected['numerics'].items()):
            raise ValueError('Base-frozen production numeric settings differ from reviewed profile')
        if not getattr(args, 'preflight_only', False) and (not args.archive_original_model or not args.export_barrier_checkpoint):
            raise ValueError('Base-frozen production requires complete original-model/checkpoint preservation')


def expected_capacity_variables(artifacts, data):
    """Calculate only accounting-derived capacities from fixed decisions/floors."""
    v,idx=artifacts.variables,artifacts.index
    result={key:np.asarray(v[key].LB).copy() for key,*_ in investment_registry(artifacts,data)}
    for cap,new,floor in [
        ('vre_capacity','vre_new','vre_capacity_floor_gw'),
        ('hydro_capacity','hydro_new','hydro_capacity_floor_gw'),
        ('storage_capacity','storage_new','storage_capacity_floor_gw'),
        ('line_capacity','line_new','line_capacity_floor_gw'),
        ('intra_load_center_capacity','intra_load_center_new','intra_capacity_floor_gw'),
        ('wave_capacity','wave_new','wave_capacity_floor_gw'),
        ('dac_capacity','dac_new','dac_capacity_floor_mtpa'),
    ]:
        if cap in v:result[cap]=np.asarray(idx[floor])+result[new]
    thermal=np.asarray(idx['thermal_capacity_floor_gw'])+result['thermal_new']
    for j,(nonccs,ccs) in enumerate(idx['ccs_pairs']):
        thermal[:,idx['thermal_index'][nonccs]]-=result['thermal_retrofit_to_ccs'][:,j]
        thermal[:,idx['thermal_index'][ccs]]+=result['thermal_retrofit_to_ccs'][:,j]
    result['thermal_capacity']=thermal
    return result


def save_capacity_expectations(artifacts, data, output, tables):
    expected=expected_capacity_variables(artifacts,data)
    audit=pd.read_csv(Path(output)/'frozen_capacity_audit.csv')
    registry=investment_registry(artifacts,data)
    corrections={key: audit.loc[audit.family==key,'clip_amount'].to_numpy().reshape(artifacts.variables[key].shape)
                 for key,*_ in registry}
    closure = artifacts.index.get('frozen_capacity_closure')
    if closure:
        deltas = {r['variable']:r['delta_gw'] for r in closure['rows']}
        for key,*_ in registry:
            names=np.asarray(artifacts.variables[key].VarName)
            corrections[key] += np.array([deltas.get(str(n),0.) for n in names.flat]).reshape(names.shape)
    checks=[]
    for new,table,_,rows,unit,subset in registry:
        cap={'vre_new':'vre_capacity','thermal_new':'thermal_capacity','storage_new':'storage_capacity',
             'line_new':'line_capacity','intra_load_center_new':'intra_load_center_capacity',
             'hydro_new':'hydro_capacity','wave_new':'wave_capacity','dac_new':'dac_capacity'}.get(new)
        if cap is None:continue
        column='capacity_mtpa' if unit=='MtCO2_per_year' else 'capacity_gw'
        raw=align(tables[table],TABLE_KEYS[table],rows,column,subset=subset).reshape(expected[cap].shape)
        target=raw+corrections[new]
        if new=='thermal_new':
            idx=artifacts.index
            for j,(nonccs,ccs) in enumerate(idx['ccs_pairs']):
                target[:,idx['thermal_index'][nonccs]]-=corrections['thermal_retrofit_to_ccs'][:,j]
                target[:,idx['thermal_index'][ccs]]+=corrections['thermal_retrofit_to_ccs'][:,j]
        delta=np.abs(expected[cap]-target)
        checks.append(dict(capacity=cap,unit=unit,max_abs_difference=float(delta.max(initial=0.)),
                           passed=bool((delta<=1e-9).all())))
    alignment=dict(status='PASS' if all(r['passed'] for r in checks) else 'FAIL',checks=checks,
                   definition='Original Base total capacity plus only audited investment clips versus accounting-derived capacity')
    if closure:
        alignment['definition']='Original Base total capacity plus original clips and separately audited author static closure'
        alignment['closure_payload_sha256']=closure['payload_sha256']
    (Path(output)/'frozen_capacity_source_alignment.json').write_text(json.dumps(alignment,indent=2)+'\n',encoding='utf-8')
    if alignment['status']!='PASS':
        raise ValueError('Frozen source/current floor or capacity-accounting mismatch; stop before solve')
    path=Path(output)/'frozen_capacity_expected.json'
    path.write_text(json.dumps({k:x.tolist() for k,x in expected.items()},indent=2)+'\n',encoding='utf-8')
    return digest(path)


def export_frozen_capacity_check(artifacts, data, output):
    """Quality label only: a failed bound/equality check never stops preservation."""
    root=Path(output)
    expected=json.loads((root/'frozen_capacity_expected.json').read_text(encoding='utf-8'))
    checks=[]
    for key,values in expected.items():
        actual=np.asarray(artifacts.variables[key].X,dtype=float)
        wanted=np.asarray(values,dtype=float)
        if actual.shape!=wanted.shape:
            raise ValueError(f'Frozen output shape mismatch: {key}')
        delta=np.abs(actual-wanted)
        maximum=float(delta.max(initial=0.))
        checks.append(dict(variable_family=key,entries=int(actual.size),max_abs_difference=maximum,
                           passed=bool(np.isfinite(actual).all() and (delta<=1e-9).all())))
    # A directly exported missing family makes B's own output self-contained.
    pd.DataFrame({'hydrochn_row_id':data.hydro_stations.hydrochn_row_id,
                  'hydro_spur_augmentation_gw':np.asarray(artifacts.variables['hydro_spur_augmentation'].X)}).to_csv(
        root/'hydro_spur_capacity.csv',index=False)
    registry=investment_registry(artifacts,data)
    def table_check(table,column,rows,values,*,subset=False):
        actual_table=pd.read_csv(root/table,dtype={key:str for key in TABLE_KEYS[table]})
        actual=align(actual_table,TABLE_KEYS[table],rows,column,subset=subset)
        wanted=np.asarray(values).reshape(-1)
        delta=np.abs(actual-wanted)
        checks.append(dict(table=table,column=column,entries=len(actual),
                           max_abs_difference=float(delta.max(initial=0.)),passed=bool((delta<=1e-9).all())))
    for key,table,column,rows,unit,subset in registry:
        if key not in expected:
            if key != 'intra_load_center_new' or artifacts.index.get('capacity_bound_selection',{}).get('mode') != 'release_base_intra':
                raise ValueError('Unexpected missing frozen output expectation: '+key)
            continue
        table_check(table,column,rows,expected[key],subset=subset)
        cap={'vre_new':'vre_capacity','thermal_new':'thermal_capacity','storage_new':'storage_capacity',
             'line_new':'line_capacity','intra_load_center_new':'intra_load_center_capacity',
             'hydro_new':'hydro_capacity','wave_new':'wave_capacity','dac_new':'dac_capacity'}.get(key)
        if cap:
            table_check(table,'capacity_mtpa' if unit=='MtCO2_per_year' else 'capacity_gw',rows,expected[cap],subset=subset)
    idx=artifacts.index
    provinces=list(map(str,idx['province_codes']))
    storage_rows=[[p,t] for p in provinces for t in idx['storage_index']]
    durations=data.storage.set_index('technology').reindex(list(idx['storage_index'])).duration_h.to_numpy(dtype=float)
    energy=np.asarray(expected['storage_capacity'])*durations[None,:]
    if 'phs_energy_capacity' in expected:energy[:,idx['storage_index']['phs']]=expected['phs_energy_capacity']
    table_check('storage_capacity.csv','energy_capacity_gwh',storage_rows,energy)
    table_check('thermal_nuclear_capacity.csv','retrofit_in_gw',
                [[p,pair[1]] for p in provinces for pair in idx['ccs_pairs']],expected['thermal_retrofit_to_ccs'],subset=True)
    table_check('intra_grid_vre_site_design.csv','spur_capacity_gw',
                data.vre_sites[['grid_uid','technology']].astype(str).values.tolist(),
                np.asarray(idx['vre_spur_floor_gw'])+expected['spur_augmentation'])
    table_check('intra_grid_substation_design.csv','trunk_capacity_gw',
                data.substations[['substation_id']].astype(str).values.tolist(),
                np.asarray(idx['trunk_floor_gw'])+idx['initial_hydro_trunk_capacity_gw']+np.asarray(expected['trunk_augmentation']))
    report=dict(status='PASS' if all(r['passed'] for r in checks) else 'FAIL',
                tolerance=1e-9,checks=checks,interpretation='quality label; preserve every result')
    (root/'frozen_capacity_output_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def read_capacity_selection(path, config, *, base_frozen):
    """Opt-in input identity; absent means no file access or configuration change."""
    if path is None:
        return None
    path = Path(path).resolve()
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('schema_version') != SELECTION_SCHEMA:
        raise ValueError('Unsupported capacity selection schema')
    if payload.get('planning_year') != config.planning_year:
        raise ValueError('Capacity selection year mismatch')
    mode = payload.get('mode')
    if mode not in {'release_base_intra', 'vre_boundary_states'}:
        raise ValueError('Unsupported capacity selection mode')
    if (mode == 'release_base_intra') != bool(base_frozen):
        raise ValueError('D1 requires Base-frozen; VRE states require own upstream')
    if not isinstance(payload.get('columns'), list) or not payload['columns']:
        raise ValueError('Explicit nonempty column list required')
    evidence = dict(path=str(path), sha256=digest(path), schema_version=SELECTION_SCHEMA,
                    mode=mode, planning_year=config.planning_year,
                    column_records=len(payload['columns']),
                    source_references=payload.get('source_references', {}))
    config.raw['capacity_bound_selection'] = evidence
    return dict(payload=payload, evidence=evidence)


def validate_restricted_resource_mode(config, args, *, test_only):
    """Reviewed resource experiment only; no starts, screening or alternate LP."""
    raw=config.raw
    if (raw['scenario']['id']!='case3_thermal_ev_v5' or config.planning_year not in {2050,2060}
            or not getattr(args,'state_in',None)):
        raise ValueError('Restricted LATE resource mode requires 2050/2060 case3 upstream')
    if bool(getattr(args,'late_entry_base_state',False)) != (config.planning_year==2050):
        raise ValueError('Restricted LATE starts from Base2040 only in 2050')
    forbidden=('vre_screen_csv','frozen_capacity_from','mga_spec','mga_baseline','basis_in',
               'primal_dual_checkpoint_in','recover_stage_a_from','formulation_config','archive_presolved_model')
    if any(getattr(args,k,None) for k in forbidden) or raw.get('candidate_screen',{}).get('enabled'):
        raise ValueError('Restricted state list replaces screening and forbids alternate solve modes')
    if not test_only:
        if raw.get('solver_profile',{}).get('id')!=RESTRICTED_RESOURCE_PROFILE_ID:
            raise ValueError('Restricted resource production requires reviewed 44-thread profile')
        path=Path(__file__).resolve().parents[1]/'config/solver_profiles'/f'{RESTRICTED_RESOURCE_PROFILE_ID}.json'
        reference=json.loads(path.read_text())
        if any(raw['numerics'].get(k)!=v for k,v in reference['numerics'].items()):
            raise ValueError('Restricted resource production numeric settings drift')
        if not getattr(args,'preflight_only',False) and (not args.archive_original_model or not args.export_barrier_checkpoint):
            raise ValueError('Restricted production requires complete preservation')


def validate_resource_factor_mode(config, args):
    """Only the author-approved 2050 five-iteration restricted timing probe."""
    validate_restricted_resource_mode(config,args,test_only=True)
    if (config.planning_year!=2050 or args.horizon!='full_year'
            or getattr(args,'diagnostic_hours',None) is not None):
        raise ValueError('Resource factor probe must use the full 2050 model')
    if config.raw.get('solver_profile',{}).get('id')!=RESOURCE_FACTOR_PROFILE_ID:
        raise ValueError('Wrong resource factor probe profile')
    reference=json.loads((Path(__file__).resolve().parents[1]/'config/solver_profiles'/f'{RESTRICTED_RESOURCE_PROFILE_ID}.json').read_text())
    if any(config.raw['numerics'].get(k)!=v for k,v in reference['numerics'].items()):
        raise ValueError('Five-iteration probe must retain production numeric parameters')
    if config.raw['solver_profile'].get('direct_nonbasic_scientific_acceptance'):
        raise ValueError('Factor probe cannot claim scientific acceptance')
    if any(getattr(args,k,None) for k in ['export_diagnostic_state','allow_nonbasic_planning_state',
            'export_scientific_solver_artifacts','export_barrier_checkpoint','export_warm_start_basis']):
        raise ValueError('Factor probe cannot export a scientific solution or planning state')
    if not getattr(args,'preflight_only',False) and not args.archive_original_model:
        raise ValueError('Factor probe must preserve the original model')


def capture_selected_original_bounds(artifacts, data, selection):
    """Keep exact in-memory pre-freeze bounds for the authorized D1 columns."""
    if selection is None or selection['payload']['mode'] != 'release_base_intra':
        return
    records = selection['payload']['columns']
    if any(set(r) != {'family','stable_key'} or r['family'] != 'intra_load_center_new'
           or not isinstance(r['stable_key'],list) or len(r['stable_key']) != 1 for r in records):
        raise ValueError('D1 may release only explicitly listed intra-city investment columns')
    wanted = [tuple(map(str,r['stable_key'])) for r in records]
    if len(wanted) != len(set(wanted)):
        raise ValueError('Duplicate D1 stable keys')
    actual = list(map(tuple,data.intra_load_center_edges[['intra_edge_id']].astype(str).values.tolist()))
    if set(wanted) != set(actual) or len(actual) != len(wanted):
        raise ValueError('D1 must list exactly all intra-city link investment columns')
    artifacts.model.update()
    mv = artifacts.variables['intra_load_center_new']
    artifacts.index['_selected_original_intra_bounds'] = (
        np.asarray(mv.LB).copy(), np.asarray(mv.UB).copy(), actual)


def apply_capacity_selection(artifacts, data, selection, output):
    """Change only opted-in bounds. No rows, objective terms or parameters change."""
    if selection is None:
        return None
    root=Path(output);payload=selection['payload'];mode=payload['mode']
    if mode not in {'release_base_intra','vre_boundary_states'}:
        raise ValueError('Unsupported capacity selection mode')
    def bound_value(value):
        value=float(value)
        if math.isnan(value):raise ValueError('NaN original bound')
        return value if math.isfinite(value) else ('+inf' if value>0 else '-inf')
    audit=[];plans=[];model=artifacts.model;model.update()
    if mode == 'release_base_intra':
        original=artifacts.index.get('_selected_original_intra_bounds')
        if original is None:
            raise ValueError('Missing exact pre-freeze D1 bounds')
        mv=artifacts.variables['intra_load_center_new']
        lo,up,keys=original
        before_lo=np.asarray(mv.LB);before_up=np.asarray(mv.UB)
        names=np.asarray(mv.VarName)
        if not np.array_equal(before_lo,before_up):
            raise ValueError('D1 source was not fully Base-frozen')
        for i,key in enumerate(keys):
            audit.append(dict(variable=str(names[i]),family='intra_load_center_new',
                stable_key=list(key),state='free',before_lb=bound_value(before_lo[i]),
                before_ub=bound_value(before_up[i]),after_lb=bound_value(lo[i]),after_ub=bound_value(up[i])))
        # Existing exact Base source/closure checks run first. Remove only the
        # two explicitly released expectations; other investment checks remain.
        expected_path=root/'frozen_capacity_expected.json'
        expected=json.loads(expected_path.read_text(encoding='utf-8'))
        for key in ['intra_load_center_new','intra_load_center_capacity']:
            if key not in expected:raise ValueError('Missing D1 source expectation')
        plans.append((mv,lo,up))
        expected.pop('intra_load_center_new');expected.pop('intra_load_center_capacity')
    else:
        records=payload['columns']
        if any(set(r) != {'grid_uid','technology','state'} or r['state'] not in {'lower','upper','free'} for r in records):
            raise ValueError('VRE selection requires stable site keys and explicit states')
        lookup={(str(r['grid_uid']),str(r['technology'])):r['state'] for r in records}
        keys=list(map(tuple,data.vre_sites[['grid_uid','technology']].astype(str).values.tolist()))
        if len(lookup)!=len(records) or len(set(keys))!=len(keys) or set(lookup)!=set(keys):
            raise ValueError('VRE selection/current sites must match one-to-one')
        v=artifacts.variables
        required=['vre_capacity','vre_new','spur_augmentation']
        arrays={name:[np.asarray(v[name].LB).copy(),np.asarray(v[name].UB).copy()] for name in required}
        names={name:np.asarray(v[name].VarName) for name in required}
        floor=np.asarray(artifacts.index['vre_capacity_floor_gw'])
        spur_floor=np.asarray(artifacts.index['vre_spur_floor_gw'])
        max_cf=np.asarray(artifacts.index['vre_max_cf'])
        for i,key in enumerate(keys):
            state=lookup[key]
            if state=='free':continue
            cap_lo,cap_up=arrays['vre_capacity'][0][i],arrays['vre_capacity'][1][i]
            if not math.isclose(float(cap_lo),float(floor[i]),rel_tol=0,abs_tol=1e-12):
                raise ValueError('VRE inherited floor differs from original bounds')
            value=float(cap_lo if state=='lower' else cap_up)
            if not math.isfinite(value):raise ValueError('Cannot fix nonfinite VRE bound')
            new=value-float(floor[i])
            # The original spur row is s + inherited_spur >= max_cf * capacity.
            # Positive spur cost implies its minimal feasible value; DPV has UB=0.
            spur=0.0 if key[1]=='dpv' else max(float(arrays['spur_augmentation'][0][i]),float(max_cf[i])*value-float(spur_floor[i]))
            for name,x in [('vre_capacity',value),('vre_new',new),('spur_augmentation',spur)]:
                lo,up=arrays[name][0][i],arrays[name][1][i]
                if not math.isfinite(x) or x<lo or x>up:
                    raise ValueError('Selected value is outside original bounds: '+str((key,name,x,lo,up)))
                audit.append(dict(variable=str(names[name][i]),family=name,stable_key=list(key),
                    state=state,original_lb=bound_value(lo),original_ub=bound_value(up),fixed_value=float(x),
                    capacity_floor_gw=float(floor[i]),capacity_upper_gw=float(cap_up),
                    inherited_spur_gw=float(spur_floor[i]),max_cf=float(max_cf[i])))
                arrays[name][0][i]=arrays[name][1][i]=x
        for name,(lo,up) in arrays.items():plans.append((v[name],lo,up))
    # All identities/ranges checked before the first bound mutation.
    for mv,lo,up in plans:mv.LB=lo;mv.UB=up
    model.update()
    if mode=='release_base_intra':
        expected_path.write_text(json.dumps(expected,indent=2)+'\n',encoding='utf-8')
    changed=sum((r['before_lb']!=r['after_lb'] or r['before_ub']!=r['after_ub'])
                if mode=='release_base_intra' else
                (float(r['original_lb'])!=r['fixed_value'] or float(r['original_ub'])!=r['fixed_value'])
                for r in audit)
    report=dict(status='PASS',**selection['evidence'],selected_bound_columns=len(audit),changed_bound_columns=changed,
                constraints_and_objective_unchanged=True,rows=audit)
    if mode=='vre_boundary_states':
        report['site_states']={s:sum(v==s for v in lookup.values()) for s in ['lower','upper','free']}
        report['movable_free_sites']=int(sum(lookup[k]=='free' and arrays['vre_capacity'][1][i]>arrays['vre_capacity'][0][i] for i,k in enumerate(keys)))
    (root/'capacity_bound_selection_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    artifacts.index['capacity_bound_selection']=report
    return report
