# 2030 参数核准

|参数|实际值|核准值|判定|
|---|---|---|---|
|resolved_config_difference_scope|True|True|PASS|
|base_case|base_2024_numeric_water_dac_by_year_20260913_v9|base_2024_numeric_water_dac_by_year_20260913_v9|PASS|
|v1g_fraction|0.2|0.2|PASS|
|v2g_fraction_total_fleet|0.1|0.1|PASS|
|v2g_cap_gw|10.0|10.0|PASS|
|legacy_bidirectional_activation|False|False|PASS|
|heating.retention_per_hour|{'min': 0.94, 'max': 0.94}|0.94|PASS|
|heating.positive_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.negative_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.comfort_band_delta_c|1.0|1.0|PASS|
|cooling.retention_per_hour|{'min': 0.92, 'max': 0.92}|0.92|PASS|
|cooling.positive_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.negative_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.comfort_band_delta_c|1.0|1.0|PASS|
|heating.enablement_cost_yuan_per_kw_year|{'min': 40.0, 'max': 40.0}|40|PASS|
|heating.activation_cost_yuan_per_mwh|{'min': 300.0, 'max': 300.0}|300|PASS|
|heating.infrastructure_cost_yuan_per_kw_year|{'min': 0.0, 'max': 0.0}|0|PASS|
|heating.degradation_cost_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|cooling.enablement_cost_yuan_per_kw_year|{'min': 40.0, 'max': 40.0}|40|PASS|
|cooling.activation_cost_yuan_per_mwh|{'min': 300.0, 'max': 300.0}|300|PASS|
|cooling.infrastructure_cost_yuan_per_kw_year|{'min': 0.0, 'max': 0.0}|0|PASS|
|cooling.degradation_cost_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.enablement_cost_yuan_per_kw_year|{'min': 40.0, 'max': 40.0}|40|PASS|
|ev_v1g.activation_cost_yuan_per_mwh|{'min': 30.0, 'max': 30.0}|30|PASS|
|ev_v1g.infrastructure_cost_yuan_per_kw_year|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.degradation_cost_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v2g.enablement_cost_yuan_per_kw_year|{'min': 50.0, 'max': 50.0}|50|PASS|
|ev_v2g.activation_cost_yuan_per_mwh|{'min': 150.0, 'max': 150.0}|150|PASS|
|ev_v2g.infrastructure_cost_yuan_per_kw_year|{'min': 40.0, 'max': 40.0}|40|PASS|
|ev_v2g.degradation_cost_yuan_per_mwh|{'min': 150.0, 'max': 150.0}|150|PASS|
|heating.activation_release|{'min': 40.0, 'max': 40.0}|40|PASS|
|heating.activation_precondition|{'min': 0.0, 'max': 0.0}|0|PASS|
|cooling.activation_release|{'min': 40.0, 'max': 40.0}|40|PASS|
|cooling.activation_precondition|{'min': 0.0, 'max': 0.0}|0|PASS|
|v1g.power_ratio|2.0|2.0|PASS|
|ev.charge_efficiency|0.94|0.94|PASS|
|ev.discharge_efficiency|0.94|0.94|PASS|
|v2g.duration_h|4.0|4.0|PASS|
|ev.actual_charge_envelope_error_gw|{'min': -8.881784197001252e-16, 'max': 8.881784197001252e-16}|0.0|PASS|
|ev.actual_24h_inventory_error_gwh|{'min': -7.105427357601002e-15, 'max': 1.4210854715202004e-14}|0.0|PASS|
|heating.participation_up_error_gw|{'min': -1.1102230246251565e-16, 'max': 0.0}|0.0|PASS|
|heating.participation_down_error_gw|{'min': -1.1102230246251565e-16, 'max': 1.3552527156068805e-20}|0.0|PASS|
|cooling.participation_up_error_gw|{'min': -2.220446049250313e-16, 'max': 2.220446049250313e-16}|0.0|PASS|
|cooling.participation_down_error_gw|{'min': -2.220446049250313e-16, 'max': 2.220446049250313e-16}|0.0|PASS|
|credit.duration_h|4.0|4.0|PASS|
|credit.heating|0.5|0.5|PASS|
|credit.cooling|0.6|0.6|PASS|
|credit.ev_v1g|0.5|0.5|PASS|
|credit.ev_v2g|0.5|0.5|PASS|
|credit.peak_reference|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|PASS|
|case3_thermal_ev_v5.build_resolved_config_identity|True|True|PASS|
|case3_thermal_ev_v5.legacy_branch|False|False|PASS|
|case3_thermal_ev_v5.objective_present.heating_shift_up_gw_active[|True|True|PASS|
|case3_thermal_ev_v5.objective.heating_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|case3_thermal_ev_v5.objective_present.heating_shift_down_gw_active[|True|True|PASS|
|case3_thermal_ev_v5.objective.heating_shift_down_gw_active[|{'min': 0.04, 'max': 0.04}|0.04|PASS|
|case3_thermal_ev_v5.objective_present.cooling_shift_up_gw_active[|False|False|PASS|
|case3_thermal_ev_v5.objective_present.cooling_shift_down_gw_active[|False|False|PASS|
|case3_thermal_ev_v5.objective_present.ev_mobility_v1g_relocated_gw[|True|True|PASS|
|case3_thermal_ev_v5.objective.ev_mobility_v1g_relocated_gw[|{'min': 0.03, 'max': 0.03}|0.03|PASS|
|case3_thermal_ev_v5.objective_present.ev_mobility_discharge_gw[|True|True|PASS|
|case3_thermal_ev_v5.objective.ev_mobility_discharge_gw[|{'min': 0.3, 'max': 0.3}|0.3|PASS|
|case3_thermal_ev_v5.credit_variables|124.0|124|PASS|
|case3_thermal_ev_v5_nocredit.build_resolved_config_identity|True|True|PASS|
|case3_thermal_ev_v5_nocredit.legacy_branch|False|False|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.heating_shift_up_gw_active[|True|True|PASS|
|case3_thermal_ev_v5_nocredit.objective.heating_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.heating_shift_down_gw_active[|True|True|PASS|
|case3_thermal_ev_v5_nocredit.objective.heating_shift_down_gw_active[|{'min': 0.04, 'max': 0.04}|0.04|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.cooling_shift_up_gw_active[|False|False|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.cooling_shift_down_gw_active[|False|False|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.ev_mobility_v1g_relocated_gw[|True|True|PASS|
|case3_thermal_ev_v5_nocredit.objective.ev_mobility_v1g_relocated_gw[|{'min': 0.03, 'max': 0.03}|0.03|PASS|
|case3_thermal_ev_v5_nocredit.objective_present.ev_mobility_discharge_gw[|True|True|PASS|
|case3_thermal_ev_v5_nocredit.objective.ev_mobility_discharge_gw[|{'min': 0.3, 'max': 0.3}|0.3|PASS|
|case3_thermal_ev_v5_nocredit.credit_variables|0.0|0|PASS|
