# 2040 与 2050 实际加载参数核准

来自实际构建/求解对象和原始目标系数；核准来源为作者任务书与柔性参数定案方案。

## 2040：PASS

|参数|实际值|核准值|判定|
|---|---|---|---|
|v1g_fraction|0.3|0.3|PASS|
|v2g_fraction|0.15|0.15|PASS|
|v2g_cap_gw|60|60|PASS|
|legacy_bidirectional_activation|False|False|PASS|
|heating.retention_per_hour|{'min': 0.94, 'max': 0.94}|0.94|PASS|
|heating.positive_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.negative_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.comfort_band|1.0|1.0|PASS|
|heating.enablement_cost_yuan_per_kw_year|{'min': 35.0, 'max': 35.0}|35|PASS|
|heating.activation_cost_release_yuan_per_mwh|{'min': 40.0, 'max': 40.0}|40|PASS|
|heating.activation_cost_precondition_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|cooling.retention_per_hour|{'min': 0.92, 'max': 0.92}|0.92|PASS|
|cooling.positive_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.negative_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.comfort_band|1.0|1.0|PASS|
|cooling.enablement_cost_yuan_per_kw_year|{'min': 35.0, 'max': 35.0}|35|PASS|
|cooling.activation_cost_release_yuan_per_mwh|{'min': 40.0, 'max': 40.0}|40|PASS|
|cooling.activation_cost_precondition_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.enablement_cost_yuan_per_kw_year|{'min': 35.0, 'max': 35.0}|35|PASS|
|ev_v1g.activation_cost_yuan_per_mwh|{'min': 20.0, 'max': 20.0}|20|PASS|
|ev_v1g.infrastructure_cost_yuan_per_kw_year|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.degradation_cost_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v2g.enablement_cost_yuan_per_kw_year|{'min': 40.0, 'max': 40.0}|40|PASS|
|ev_v2g.activation_cost_yuan_per_mwh|{'min': 120.0, 'max': 120.0}|120|PASS|
|ev_v2g.infrastructure_cost_yuan_per_kw_year|{'min': 30.0, 'max': 30.0}|30|PASS|
|ev_v2g.degradation_cost_yuan_per_mwh|{'min': 110.0, 'max': 110.0}|110|PASS|
|charge_efficiency|0.94|0.94|PASS|
|discharge_efficiency|0.94|0.94|PASS|
|power_duration_hours|4.0|4.0|PASS|
|maximum_power_to_daily_average_ratio|2.0|2.0|PASS|
|actual_ev_charge_envelope_error|{'min': -2.6645352591003757e-15, 'max': 1.7763568394002505e-15}|0.0|PASS|
|actual_ev_inventory_error|{'min': -2.842170943040401e-14, 'max': 2.842170943040401e-14}|0.0|PASS|
|heating.participation_up_error|{'min': -1.1102230246251565e-16, 'max': 0.0}|0.0|PASS|
|heating.participation_down_error|{'min': -1.1102230246251565e-16, 'max': 3.3881317890172014e-21}|0.0|PASS|
|cooling.participation_up_error|{'min': -2.220446049250313e-16, 'max': 4.440892098500626e-16}|0.0|PASS|
|cooling.participation_down_error|{'min': -2.220446049250313e-16, 'max': 4.440892098500626e-16}|0.0|PASS|
|credit.heating|0.5|0.5|PASS|
|credit.cooling|0.55|0.55|PASS|
|credit.ev_v1g|0.45|0.45|PASS|
|credit.ev_v2g|0.45|0.45|PASS|
|credit.duration|4.0|4.0|PASS|
|credit.peak_reference|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|PASS|
|actual_objective.heating_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|actual_objective.cooling_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|actual_objective.heating_shift_down_gw_active[|{'min': 0.04, 'max': 0.04}|0.04|PASS|
|actual_objective.cooling_shift_down_gw_active[|{'min': 0.04, 'max': 0.04}|0.04|PASS|
|actual_objective.ev_mobility_v1g_relocated_gw[|{'min': 0.02, 'max': 0.02}|0.02|PASS|
|actual_objective.ev_mobility_discharge_gw[|{'min': 0.22999999999999998, 'max': 0.22999999999999998}|0.23|PASS|
|credit.variable_count|124|124|PASS|

## 2050：PASS

|参数|实际值|核准值|判定|
|---|---|---|---|
|v1g_fraction|0.4|0.4|PASS|
|v2g_fraction|0.2|0.2|PASS|
|v2g_cap_gw|120|120|PASS|
|legacy_bidirectional_activation|False|False|PASS|
|heating.retention_per_hour|{'min': 0.94, 'max': 0.94}|0.94|PASS|
|heating.positive_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.negative_state_duration_hours|{'min': 4.0, 'max': 4.0}|4|PASS|
|heating.comfort_band|1.0|1.0|PASS|
|heating.enablement_cost_yuan_per_kw_year|{'min': 30.0, 'max': 30.0}|30|PASS|
|heating.activation_cost_release_yuan_per_mwh|{'min': 30.0, 'max': 30.0}|30|PASS|
|heating.activation_cost_precondition_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|cooling.retention_per_hour|{'min': 0.92, 'max': 0.92}|0.92|PASS|
|cooling.positive_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.negative_state_duration_hours|{'min': 5.0, 'max': 5.0}|5|PASS|
|cooling.comfort_band|1.0|1.0|PASS|
|cooling.enablement_cost_yuan_per_kw_year|{'min': 30.0, 'max': 30.0}|30|PASS|
|cooling.activation_cost_release_yuan_per_mwh|{'min': 30.0, 'max': 30.0}|30|PASS|
|cooling.activation_cost_precondition_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.enablement_cost_yuan_per_kw_year|{'min': 30.0, 'max': 30.0}|30|PASS|
|ev_v1g.activation_cost_yuan_per_mwh|{'min': 20.0, 'max': 20.0}|20|PASS|
|ev_v1g.infrastructure_cost_yuan_per_kw_year|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v1g.degradation_cost_yuan_per_mwh|{'min': 0.0, 'max': 0.0}|0|PASS|
|ev_v2g.enablement_cost_yuan_per_kw_year|{'min': 30.0, 'max': 30.0}|30|PASS|
|ev_v2g.activation_cost_yuan_per_mwh|{'min': 100.0, 'max': 100.0}|100|PASS|
|ev_v2g.infrastructure_cost_yuan_per_kw_year|{'min': 20.0, 'max': 20.0}|20|PASS|
|ev_v2g.degradation_cost_yuan_per_mwh|{'min': 80.0, 'max': 80.0}|80|PASS|
|charge_efficiency|0.94|0.94|PASS|
|discharge_efficiency|0.94|0.94|PASS|
|power_duration_hours|4.0|4.0|PASS|
|maximum_power_to_daily_average_ratio|2.0|2.0|PASS|
|actual_ev_charge_envelope_error|{'min': -5.329070518200751e-15, 'max': 3.552713678800501e-15}|0.0|PASS|
|actual_ev_inventory_error|{'min': -4.263256414560601e-14, 'max': 2.842170943040401e-14}|0.0|PASS|
|heating.participation_up_error|{'min': -1.1102230246251565e-16, 'max': 6.776263578034403e-21}|0.0|PASS|
|heating.participation_down_error|{'min': -1.1102230246251565e-16, 'max': 0.0}|0.0|PASS|
|cooling.participation_up_error|{'min': -4.440892098500626e-16, 'max': 4.440892098500626e-16}|0.0|PASS|
|cooling.participation_down_error|{'min': -4.440892098500626e-16, 'max': 4.440892098500626e-16}|0.0|PASS|
|credit.heating|0.45|0.45|PASS|
|credit.cooling|0.5|0.5|PASS|
|credit.ev_v1g|0.4|0.4|PASS|
|credit.ev_v2g|0.4|0.4|PASS|
|credit.duration|4.0|4.0|PASS|
|credit.peak_reference|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|four_hour_window_containing_immutable_full_year_province_baseline_peak_v1|PASS|
|actual_objective.heating_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|actual_objective.cooling_shift_up_gw_active[|{'min': 0.0, 'max': 0.0}|0|PASS|
|actual_objective.heating_shift_down_gw_active[|{'min': 0.03, 'max': 0.03}|0.03|PASS|
|actual_objective.cooling_shift_down_gw_active[|{'min': 0.03, 'max': 0.03}|0.03|PASS|
|actual_objective.ev_mobility_v1g_relocated_gw[|{'min': 0.02, 'max': 0.02}|0.02|PASS|
|actual_objective.ev_mobility_discharge_gw[|{'min': 0.18, 'max': 0.18}|0.18|PASS|
|credit.variable_count|124|124|PASS|
