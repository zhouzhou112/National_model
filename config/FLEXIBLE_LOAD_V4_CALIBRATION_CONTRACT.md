# `service_constrained_v4` calibration and input contract

## Status and scientific boundary

`service_constrained_v4` is an independent demand-flexibility scenario
contract.  It does not modify `base`, `comfort_envelope_v3`, the accepted
744-hour Base result, the planning capacity-margin peak, or any solver basis.
The central V4 case is `flexible_load_comfort_v4_v1g`; V2G is only the separate
`flexible_load_comfort_v4_v2g_sensitivity` case.

The V4 JSON files are deliberately listed as `planned_not_runnable` until all
five tables below are calibrated, generated, and input-manifest checked.  A
missing field, a duplicate province-hour, an EV-energy closure error, or a
baseline charging profile above the declared available charging power is a hard
failure.  `ev_hour_weight` remains an uncontrolled-charging shape and must not
be inserted into any availability field.

## Model equations

For province `p`, hour `t`, and thermal service `c in {heating, cooling}`, V4
has one signed state rather than a positive/negative state pair:

```text
S[p,c,t] = rho[p,c] * S[p,c,t-1]
           + eta_charge[p,c] * P_up[p,c,t]
           - P_down[p,c,t] / eta_discharge[p,c]

-H_minus[p,c] * K[p,c] <= S[p,c,t] <= H_plus[p,c] * K[p,c]
D[p,c,t] >= -S[p,c,t]
0 <= P_up[p,c,t], P_down[p,c,t]
   <= envelope[p,c,t]
0 <= P_up[p,c,t], P_down[p,c,t]
   <= availability[p,c,t] * K[p,c]
```

`S[p,c,0]` is linked to `S[p,c,T-1]` by the same recurrence.  Thus the full
8,760-hour solve has an annual periodic boundary; a short gate is periodic only
over its declared test window and cannot be interpreted as annual operation.
`D` is a non-negative comfort-debt accounting variable.  It is bounded through
the signed state and carries an explicit state-hour cost, so comfort debt cannot
become an unpriced, unlimited negative inventory.

The EV formulation has one fleet SOC for V1G and V2G together:

```text
SOC[p,t] = (1-self_discharge) * SOC[p,t-1]
           + eta_charge * P_charge[p,t]
           - P_discharge[p,t] / eta_discharge
           - E_drive[p,t]

0 <= SOC[p,t] <= E_fleet[p,t]
SOC[p,t] >= E_departure_min[p,t]
P_charge[p,t] <= min(P_charge_available[p,t], connected[p,t] * K[p,ev_v1g])
P_discharge[p,t] <= min(P_discharge_available[p,t], connected[p,t] * K[p,ev_v2g])
```

V1G sets `P_discharge=0` and fixes `K[p,ev_v2g]=0`.  V2G does not create a
second deviation battery: it can discharge only from the same SOC after driving
withdrawals and departure minima are met.  No V4 flexible capacity receives
firm-capacity or operating-reserve credit in the current model boundary.

The annual objective adds, in million CNY/year:

```text
sum[p,c](enablement_CNY_per_kW_year[p,c] * K[p,c])
+ 1e-3 * sum[p,t,c](activation_CNY_per_MWh[p,c] * throughput[p,c,t])
+ 1e-6 * sum[p,t,c in thermal](comfort_debt_CNY_per_GWh_hour[p,c] * D[p,c,t])
```

The `1e-3` converts `CNY/MWh * GWh` to million CNY; a `CNY/kW-year` coefficient
times `GW` is already numerically million CNY/year.

## Required files and columns

All files are under `CISPO_DATA_ROOT/flexibility/`, have non-leap
`hour_index=0..8759`, and must cover each model year and all 31 canonical
provinces.

| File | Required columns | Calibration target and hard checks |
|---|---|---|
| `thermal_hourly_envelope_v4.csv.gz` | `province_code`, `year`, `hour_index`, `heating_increase_limit_gw`, `heating_reduction_limit_gw`, `cooling_increase_limit_gw`, `cooling_reduction_limit_gw`, `heating_availability_fraction`, `cooling_availability_fraction` | BAIT/balance-point envelope remains the power boundary.  Availability is the enrolled service fraction, in `[0,1]`; it must be positive whenever the corresponding envelope is positive.  A reduction limit cannot exceed immutable heating/cooling baseline load. |
| `thermal_parameters_by_province_v4.csv` | `province_code`, `year`, `component`, `retention_per_hour`, `charge_efficiency`, `discharge_efficiency`, `positive_state_duration_hours`, `negative_state_duration_hours` | Province-year building-climate archetype identification.  Fit/validate against building stock, heating/cooling technology shares, a temperature-response or RC simulation, and the retained hourly thermal series.  All efficiencies and retention are in `(0,1]`; both durations are positive. |
| `ev_availability_hourly_v4.csv.gz` | `province_code`, `year`, `hour_index`, `connected_vehicle_fraction`, `available_charge_power_gw`, `available_discharge_power_gw`, `fleet_energy_capacity_gwh` | Charging-session or home/work/public/fleet archetype calibration.  `connected_vehicle_fraction` is `[0,1]`; power and energy are non-negative.  Declared charge power must contain the immutable uncontrolled EV baseline at every hour, so the reference service is feasible. |
| `ev_mobility_hourly_v4.csv.gz` | `province_code`, `year`, `hour_index`, `driving_energy_withdrawal_gwh`, `minimum_departure_energy_gwh` | Trip-chain/departure calibration.  Driving withdrawals are non-negative and annually close to `eta_charge * baseline_EV_grid_energy` for every province.  Departure minima cannot exceed fleet energy capacity. |
| `flex_enablement_cost_v4.csv` | `province_code`, `year`, `service`, `enablement_cost_yuan_per_kw_year`, `activation_cost_yuan_per_mwh`, `comfort_debt_cost_yuan_per_gwh_hour` | Contract, aggregator, device-control, user-compensation and V2G degradation costs.  Required services are `heating`, `cooling`, `ev_v1g`, `ev_v2g`; all values are finite and non-negative.  V2G low/base/high degradation or compensation cases must be encoded here, never hidden in code. |

`flexible_load_v4.manifest.json` is the sixth required provenance artifact.  It
must record source manifests, preprocessing versions, all five output SHA256
hashes, province/year/hour coverage, parameter-registry revision and the
results of the table-level checks above.  The runtime input manifest includes
all six artifacts for V4 but never requires them for Base or V3.

After the five calibrated tables have been placed under the selected data root,
create the sidecar with at least one frozen upstream provenance manifest:

```powershell
python scripts/validate_flexible_load_v4_inputs.py `
  --scenario-config config/scenarios/flexible_load_comfort_v4_v1g.json `
  --source-manifest D:\path\to\building_and_ev_source_manifest.json
```

The command validates every planning year, applies the same loader checks as a
model build, and only then writes `flexible_load_v4.manifest.json`.  It does not
invent calibration values.

## Calibration evidence protocol

1. Freeze a source manifest for every raw building, charger/session, vehicle
   stock, battery, trip and compensation source.  Record source date, coverage,
   province mapping, units, preprocessing and SHA256.
2. Estimate thermal parameters by province-year archetype, then hold out at
   least one weather period or province group.  The result may be an archetype
   calibration, but must not be called an observed indoor-temperature series.
3. Construct EV connection and mobility profiles from observed sessions where
   available.  Provinces without observations may use a disclosed
   home/work/public/fleet transfer model, but must be labelled as transferred
   archetypes and receive low/base/high sensitivity cases.
4. Reconcile vehicle stock, usable battery energy, daily driving energy and
   charging efficiency.  The annual grid-energy closure is mandatory before a
   V4 case can build.
5. Separate one-time/device enablement, hourly activation, user compensation
   and battery degradation.  Do not charge baseline EV driving energy as a
   flexibility activation merely because it passes through `P_charge`.
6. Run input QC, a 1-hour algebra gate, a 24-hour formulation gate and a
   168-hour memory/solver gate before requesting an isolated 744-hour V4 gate.
   The fixed server must remain on its accepted Base checkout until that request
   is explicitly approved.

## Output and acceptance QC

`solution_qc.json` reports V4 thermal transition and periodic-boundary
residuals, signed-state bounds, comfort-debt definition, EV SOC recurrence,
departure/SOC/power violations, and the existing effective-load reconstruction.
`flexible_load_dispatch.npz` additionally exports signed thermal states,
comfort debt, mobility charge/discharge/SOC, charge deviation and contracted
service capacity.  A V4 run is invalid if any of these hard checks exceeds the
standard numerical tolerance.
