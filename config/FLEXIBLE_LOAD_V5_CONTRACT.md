# Integrated flexible-load V5 contract

## 1. Scope and scenario identity

The formal comparison set contains exactly two primary analysis cases:

1. `base`: immutable load, no demand flexibility;
2. `flex_integrated_v5_central`: heating, cooling, V1G, V2G and derated
   firm-flexibility capacity value in one integrated counterfactual.

`base_2024_vre_wave_on_flex_off_v1` remains the common
`scientific_case`/baseline contract. The V5 overlay is a separate
`scenario`/analysis-case identity whose
`parent_baseline_case_id=base_2024_vre_wave_on_flex_off_v1`. Historical V3/V4
and separate hydro/PHS overlays remain explicit reproducibility artifacts but
are not selected by the default scenario suite.

V5 changes no Base load, supply, network, reserve, inertia, carbon or cost
boundary. All monetary values are in 2025 constant CNY.

## 2. Immutable load decomposition

For province \(p\) and hour \(t\), the accepted load reconstruction is

\[
L^{0}_{p,t}
=L^{res}_{p,t}+L^{heat}_{p,t}+L^{cool}_{p,t}+L^{EV}_{p,t}.
\]

V5 optimizes service delivery, not the upstream demand reconstruction. The
effective grid load is

\[
L^{eff}_{p,t}
=L^{res}_{p,t}
+\widetilde L^{heat}_{p,t}
+\widetilde L^{cool}_{p,t}
+\widetilde L^{EV}_{p,t}
-P^{V2G,out}_{p,t}.
\]

Strict hourly power balance uses \(L^{eff}_{p,t}\). The input baseline remains
exported and hashed independently.

## 3. Heating and cooling service

The accepted BAIT \(+/-1\,^\circ\mathrm{C}\) envelope supplies the province-hour
increase and reduction limits. V5 scales those limits by explicit enrolled
fractions (central: 25% heating and 20% cooling) and applies endogenous
contracted-power bounds.

Each service uses a non-negative equivalent inventory \(S_{p,t}\):

\[
S_{p,t}=\rho_p S_{p,t-1}
 \eta^{in}_p P^{up}_{p,t}
 -P^{down}_{p,t}/\eta^{out}_p.
\]

The state is periodic over the selected horizon. Only an 8760-hour accepted
run may be interpreted as an annual scientific result; truncated runs are
`TEST_ONLY_TRUNCATED_HORIZON`.

## 4. V1G smart charging

The central enrolled V1G share is 15% of the immutable EV charging baseline.
The remaining 85% is fixed. The flexible share is represented by one aggregate
fleet-service inventory whose exogenous hourly withdrawal closes exactly to
the enrolled reference energy after charging efficiency.

The retained data do not contain measured connection sessions, trip chains or
departure-SOC observations. Consequently,
`connected_vehicle_fraction=1` is a service-normalisation field, not an
empirical connection probability. Power and energy envelopes are therefore
registered engineering assumptions with low/central/high ranges.

V1G is not free. Endogenous smart-charging capacity pays an annual
control/aggregation cost. The activation term charges only downward
displacement of the uncontrolled charging reference:

\[
E^{reloc}_{p,t}\ge
\max\{L^{EV,flex}_{p,t}-P^{charge}_{p,t},0\}.
\]

This counts original charging energy moved away from its reference hour once.
Additional charging needed to replenish V2G discharge is not misclassified as
V1G relocation.

## 5. V2G contract and physical nesting

V2G is an endogenous incremental contract:

\[
0\le K^{V2G}_p\le K^{V1G}_p,\qquad
\sum_p K^{V2G}_p\le \overline K^{V2G}_y.
\]

The 2030 scenario upper bound of 10 GW is anchored to the national policy goal
of ten-gigawatt-scale bidirectional flexibility. It is a conservative
scenario cap, not a claim that policy defines a legal maximum. The 2040--2060
values are explicit extrapolations and require sensitivity interpretation.

V2G pays four distinct real-resource terms: annual availability, annualized
bidirectional infrastructure, owner participation per discharged MWh, and
battery degradation per discharged MWh. Retail tariff payments and policy
subsidies are treated as transfers and are not added to social system cost.
The electricity and loss energy used for charging remain in the physical
system objective.

## 6. Firm flexibility capacity value

V5 does not replace the Base capacity-margin peak with an unconstrained
endogenous effective peak. It retains the immutable full-year province
baseline peak and allows only a derated, physically bounded firm-flexibility
credit:

\[
C^{credit}_p+\sum_s F^{firm}_{p,s}
\ge (1+m)\max_t L^0_{p,t}.
\]

For each province, the accreditation window is the four consecutive hours
\(\{t^\star-1,t^\star,t^\star+1,t^\star+2\}\), where
\(t^\star=\arg\max_t L^0_{p,t}\). Each service credit is bounded by the minimum
available reduction/discharge power over that window, its contracted power,
and a transparent derating coefficient. V2G is additionally bounded by
available fleet energy divided by four hours.

Central deratings are 0.60 for heating/cooling and 0.50 for V1G/V2G. These are
engineering assumptions with registered ranges, not China-specific ELCC
estimates. V5 grants no reserve credit to flexible load. Publication claims
must therefore report both the central result and sensitivity to accreditation
assumptions.

## 7. Cost and evidence contracts

Parameter values and ranges are centralized in:

- `config/flexible_load_v5_central_parameters.csv`;
- `config/flexible_load_v5_parameter_registry.csv`;
- `config/flexible_load_v5_source_registry.csv`;
- `config/flexible_load_v5_source_count_qa.csv`.

`scripts/build_flexible_load_v5_inputs.py` deterministically generates the
hourly inputs and `flexible_load_v5.manifest.json`.

The generated CSV contract is byte-stable across the supported Windows and
Linux environments: UTF-8 encoding, LF line endings, `%.17g` floating-point
formatting, and gzip level 6 with an empty filename and `mtime=0`. This avoids
changing release hashes solely because the builder is executed with a
different pandas, NumPy, Python, or host operating-system version.
`scripts/validate_flexible_load_v5_inputs.py` resolves every cited source ID,
recomputes independent/China-specific/peer-reviewed evidence counts, validates
all four planning years, and fails closed on a manifest or parameter-order
mismatch.

## 8. Required validation sequence

The minimum gate sequence is:

1. unit tests and input/release-contract audits;
2. fresh 1-hour Base/V5 structural gates;
3. fresh 24-hour Base/V5 mechanism gates;
4. four-year 168-hour planning-sequence gates;
5. one authorized 2030/744-hour cold engineering gate.

No truncated gate is an annual scientific result or a valid 2040 planning
anchor. Full-year interpretation additionally requires `OPTIMAL`,
`solution_qc=PASS`, all current hard checks, current input manifest, valid
result manifest, and complete accounting-scope review.
