"""Author-approved resource overrides; central retention/efficiency/cost unchanged."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def audit_resource_parameters(config,data,artifacts,year,resource):
    # Reuse the established central checks, replacing only authorized resource
    # fractions and comfort band. This helper changes no model/data object.
    source=ROOT/'supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py'
    text=source.read_text()
    marker="    check('v1g_fraction',settings['ev_v1g']['shiftable_energy_fraction'],v)"
    replacement="    band=1.\n"
    if resource=='conservative':replacement+="    h=c=v=.2; b=.1; band=.5\n"
    elif resource=='open':replacement+="    h=c=v=1.; b=.5; cap=1000; band=2.\n"
    elif resource!='base':raise ValueError(resource)
    assert text.count(marker)==1
    text=text.replace(marker,replacement+marker).replace("manifest[component+'_comfort_band_c'],1.)","manifest[component+'_comfort_band_c'],band)")
    ns={'__file__':str(source),'__name__':'resource_central_parameter_reuse'}
    exec(compile(text,str(source),'exec'),ns)
    result=ns['parameters'](config,data,artifacts.model,year)
    expected_path=HERE/'contractable_total_national_source.csv'
    ref=pd.read_csv(expected_path)
    labels={'base':('Base','Pathway'),'conservative':('Conservative','Constant'),'open':('Open','Full')}
    label,part=labels[resource]
    row=ref[(ref.resource_scenario==label)&(ref.participation_setting==part)&(ref.planning_year==year)&(ref.weather_year==2024)]
    if len(row)!=1:raise ValueError('Ambiguous full-precision reference row')
    wanted=row.iloc[0][['heating_ceiling_gw','cooling_ceiling_gw','smart_ceiling_gw','discharge_ceiling_gw']].to_numpy(dtype=float)
    from cispo_model.flexible_load import _capacity_upper_from_profile
    service=data.flexible_load_v4
    annual=[]
    thermal_profiles=[]
    for component in ['heating','cooling']:
        power=np.maximum(service.thermal_envelopes_gw[component+'_up'],service.thermal_envelopes_gw[component+'_down'])
        thermal_profiles.append(power)
        annual.append(_capacity_upper_from_profile(power,service.thermal_availability[component],label=component+' annual resource gate'))
    annual.append(service.ev_availability['available_charge_power_gw'].max(axis=1))
    annual.append(_capacity_upper_from_profile(service.ev_availability['available_discharge_power_gw'],service.ev_availability['connected_vehicle_fraction'],label='V2G annual resource gate'))
    annual=np.column_stack(annual)
    actual=np.asarray(artifacts.variables['flexible_service_capacity'].UB)
    annual_sums=annual.sum(axis=0)
    difference=np.abs(annual_sums-wanted)
    result['checks'].append(dict(parameter='annual_8760_contract_upper_sums_gw',actual=annual_sums.tolist(),expected=wanted.tolist(),absolute_difference_gw=difference.tolist(),tolerance_gw=1e-6,passed=bool((difference<=1e-6).all())))
    start=artifacts.index['optimization_start_hour'];hours=artifacts.index['optimization_hours']
    predicted=np.column_stack([p[:,start:start+hours].max(axis=1) for p in thermal_profiles])
    short_error=np.abs(actual[:,:2]-predicted)
    exceed=actual[:,:2]-annual[:,:2]
    result['checks'].append(dict(parameter='selected_window_thermal_upper_by_province',maximum_absolute_difference_gw=float(short_error.max()),maximum_exceedance_over_annual_gw=float(exceed.max()),passed=bool((short_error<=1e-9).all() and (exceed<=1e-9).all())))
    ev_error=np.abs(actual[:,2:].sum(axis=0)-wanted[2:])
    result['checks'].append(dict(parameter='selected_window_EV_upper_equals_annual',actual=actual[:,2:].sum(axis=0).tolist(),expected=wanted[2:].tolist(),absolute_difference_gw=ev_error.tolist(),passed=bool((ev_error<=1e-6).all())))
    result['selected_window_contract_upper_sums_gw']=actual.sum(axis=0).tolist()
    result['annual_8760_contract_upper_sums_gw']=annual_sums.tolist()
    result['selected_window_thermal_upper_by_province']=[dict(province_code=int(p),actual_heating_gw=float(actual[i,0]),actual_cooling_gw=float(actual[i,1]),input_window_heating_gw=float(predicted[i,0]),input_window_cooling_gw=float(predicted[i,1]),annual_heating_gw=float(annual[i,0]),annual_cooling_gw=float(annual[i,1])) for i,p in enumerate(data.provinces.province_code)]
    result.update(resource=resource,contract_reference_sha256=hashlib.sha256(expected_path.read_bytes()).hexdigest(),effective_load_nonnegative_selected_window_rows=sum(c.ConstrName.startswith('effective_load_nonnegative') for c in artifacts.model.getConstrs()),full_year_negative_cells_from_supplied_input_acceptance=(139 if year==2050 else 2249 if year==2060 else 0) if resource=='open' else 0)
    result['status']='PASS' if all(c['passed'] for c in result['checks']) else 'FAIL'
    return result
