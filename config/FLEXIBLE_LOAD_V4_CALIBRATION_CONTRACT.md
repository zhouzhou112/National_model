# `service_constrained_v4` data-supported contract

## Status and boundary

V4 is an independent flexibility scenario. It does not modify Base, V3, the
accepted 744 h Base result, capacity-margin peak load, or any solver basis.
`flexible_load_comfort_v4_v1g` is the central engineering case; V2G is only
`flexible_load_comfort_v4_v2g_sensitivity`.

The design deliberately converges on data that already exist:

- `hourly_load_2025_2060.csv.gz` supplies immutable province-hour
  `base_residual`, `heating`, `cooling`, and `ev`;
- `flexible_load_envelope_v3.csv.gz` supplies the audited BAIT `+/-1 C`
  heating/cooling power envelope;
- the Power_curve_V2 EV stock, daily energy and `ev_hour_weight` are already
  embodied in the immutable EV baseline.

The retained inputs do not observe vehicle connection sessions, trip chains or
departure SOC. V4 therefore does not fabricate them and does not call
`ev_hour_weight` a connection probability. The EV state is an aggregate
schedulable-service inventory, not a physical fleet SOC estimate.

## Thermal equations

For province `p`, component `c in {heating,cooling}`, and hour `t`:

```text
S[p,c,t] = rho[p,c] * S[p,c,t-1]
           + eta_charge[p,c] * P_up[p,c,t]
           - P_down[p,c,t] / eta_discharge[p,c]

0 <= S[p,c,t] <= duration[p,c] * K[p,c]
0 <= P_up[p,c,t], P_down[p,c,t] <= envelope[p,c,t]
0 <= P_up[p,c,t], P_down[p,c,t] <= K[p,c]
P_actual[p,c,t] = P_baseline[p,c,t] + P_up[p,c,t] - P_down[p,c,t]
```

The envelope is the accepted BAIT `+/-1 C` envelope multiplied by explicit
enrolment (`0.25` heating, `0.20` cooling central). `S` is non-negative:
curtailment must be backed by prior preheating/precooling inventory. There is no
negative comfort debt and no daily reset. The first hour is linked to the last
selected hour; only an 8,760 h solve has annual scientific meaning.

## EV equations

Let `f_smart=0.25` and `L_ev` be the immutable EV charging baseline:

```text
L_fixed[p,t] = (1-f_smart) * L_ev[p,t]
E_service[p,t] = eta_charge * f_smart * L_ev[p,t]

SOC_service[p,t] = SOC_service[p,t-1]
                   + eta_charge * P_smart[p,t]
                   - P_v2g[p,t] / eta_discharge
                   - E_service[p,t]

0 <= SOC_service[p,t] <= E_service_cap[p,t]
0 <= P_smart[p,t] <= P_smart_cap[p,t]
0 <= P_v2g[p,t] <= P_v2g_cap[p,t]
L_ev_actual[p,t] = L_fixed[p,t] + P_smart[p,t]
```

The central inventory cap is one day of flexible service. Charge power is the
larger of the flexible baseline and twice its daily-average proxy. The V2G
power cap uses a separate `0.10` participation assumption and exists only in
the sensitivity case. `minimum_departure_energy_gwh` is retained as a legacy
schema field but must equal zero. Likewise,
`connected_vehicle_fraction` must equal one and is only an aggregate service
normalisation; neither field is interpreted as observed mobility behaviour.

This construction guarantees that `P_smart=f_smart*L_ev`, `P_v2g=0`, and
`SOC_service=0` reproduce the immutable EV baseline exactly. Loader QC checks
this closure for every province and planning year.

## Objective

The objective stores all values in million CNY, but their accounting periods
are different in truncated engineering gates.  The enablement term is an
annualized planning cost; activation, relocation and degradation terms cover
only the selected optimization hours:

```text
sum[p,s](enablement_CNY_per_kW_year[p,s] * K[p,s])
+ 1e-3 * sum[p,t,c](thermal_activation_CNY_per_MWh[p,c]
                     * (P_up[p,c,t] + P_down[p,c,t]))
+ 1e-3 * sum[p,t](v1g_activation_CNY_per_MWh[p]
                   * abs(P_smart[p,t] - f_smart*L_ev[p,t]))
+ 1e-3 * sum[p,t](v2g_degradation_CNY_per_MWh[p] * P_v2g[p,t])
```

Central values and mandatory low/high ranges are in
`flexible_load_v4_central_parameters.csv`. They are engineering scenario
assumptions, not observations. Source mapping is in
`flexible_load_v4_source_registry.csv`; evidence-count QA is in
`flexible_load_v4_source_count_qa.csv`.

`cost_components.csv` therefore labels V4 enablement as
`ANNUALIZED_PLANNING_COST` and hourly terms as
`SELECTED_HORIZON_OPERATION_COST`.  Their sum may be optimized in a truncated
gate, but it must not be reported as an annual net-benefit estimate.

## Generated inputs

`scripts/build_flexible_load_v4_inputs.py` creates five files under
`CISPO_DATA_ROOT/flexibility/`:

| File | Purpose |
|---|---|
| `thermal_hourly_envelope_v4.csv.gz` | enrolled BAIT `+/-1 C` hourly bounds |
| `thermal_parameters_by_province_v4.csv` | retention, efficiency, duration |
| `ev_availability_hourly_v4.csv.gz` | smart-charge/V2G power and service-inventory caps |
| `ev_mobility_hourly_v4.csv.gz` | exact flexible-service withdrawal; zero legacy departure floor |
| `flex_enablement_cost_v4.csv` | enablement, activation and V2G degradation costs |

The three compressed tables use gzip with fixed `mtime=0`; two builds from
unchanged sources must be byte-identical before deployment.

The generator also writes `flexible_load_v4.manifest.json` with upstream and
generated-file SHA256. The sidecar is content-deterministic and uses portable
logical paths, so an unchanged input package retains the same identity across
repeated validation and deployment roots. The independent validator reloads
all five planning years through the runtime loader:

```powershell
conda run -n RL python scripts/build_flexible_load_v4_inputs.py

conda run -n RL python scripts/validate_flexible_load_v4_inputs.py `
  --source-manifest data/load/flexible_load_envelope_v3.manifest.json `
  --source-manifest config/flexible_load_v4_source_registry.csv `
  --source-manifest config/flexible_load_v4_central_parameters.csv `
  --source-manifest config/flexible_load_v4_source_count_qa.csv
```

## Acceptance gates

Required before interpreting any result:

1. input manifest and all five planning-year loader checks pass;
2. `2 provinces x 4 hours` algebra test proves scalar objective and no
   cross-province periodic broadcasting;
3. local 1 h and 24 h V1G gates are `OPTIMAL`, `solution_qc=PASS`, and have
   closed manifests;
4. 168 h is a later isolated engineering gate; no 744 h/8,760 h run follows
   without explicit authorization;
5. low/high enrolment, duration/retention and cost sensitivities are required
   before paper claims. V2G can never replace the V1G central case.

No V4 capacity receives firm-capacity, reserve or inertia credit.
