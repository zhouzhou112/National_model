# CF Sparsification V1 worklog

## Scope

- Base commit: `6065bfba34b76098e86307081323e8545a4d25ac`.
- Branch: `codex/cf-sparsification-v1`.
- Scientific case: Base 2030, weather year 2024, wave enabled, flexible load disabled.
- Production already maps hourly VRE, wave and run-of-river capacity factors below
  `coefficient_zero_tolerance=1e-6` to exact zero.
- Candidate changes only that threshold to `1e-4`. It changes the physical
  feasible set and is therefore not an algebraically equivalent scaling.

No source CSV, Zarr, NetCDF, model equation, unit, temporal/spatial resolution,
solver tolerance or active server checkpoint was modified.

## Read-only physical error audit

The two audit scripts scan the source stores in bounded-memory chunks. For each
candidate threshold they report the increment relative to the production
`1e-6` threshold. `capacity_floor_gw` measures omitted availability at mandatory
capacity; `capacity_upper_gw` is a conservative feasible-set error bound.

At `744h/start2880`, threshold `1e-4` gives:

| Resource | Extra removed CF entries | Floor energy omitted (GWh) | Upper energy omitted (GWh) | Maximum system-hour upper loss (GW) |
|---|---:|---:|---:|---:|
| VRE | 6,152 | 0.012686 | 0.495424 | 0.009706 |
| Wave | 0 | 0 | 0 | 0 |
| Run-of-river | 14,826 | 0.015212 | 0.044205 | 0.000133 |

At the complete `8760h` horizon:

| Resource | Extra removed CF entries | Floor energy omitted (GWh) | Upper energy omitted (GWh) | Maximum system-hour upper loss (GW) |
|---|---:|---:|---:|---:|
| VRE | 64,001 | 0.148788 | 5.222078 | 0.011885 |
| Wave | 0 | 0 | 0 | 0 |
| Run-of-river | 261,060 | 0.266316 | 0.879441 | 0.001144 |

The summed full-year upper-energy bound is about `6.101519 GWh`; the summed
floor-energy change is about `0.415104 GWh`. The sum of resource-specific
maximum system-hour upper losses is a conservative `0.013030 GW`. These bounds
show that `1e-4` has a small physical effect, but do not prove a performance
benefit: removed entries are a very small fraction of the full LP nonzeros.

Evidence files:

- `output/cf_threshold_audit_744h_start2880.json`, SHA256
  `1e06dbeb67f3cad5b28f0d4eea9ab58f9ed5c6ea7eddb4f30decd43ff625c542`.
- `output/cf_threshold_audit_8760h.json`, SHA256
  `88083f775265e172a1ea5bba2372f78f29d79632a2ff15076591695daf5b7bf6`.
- `output/wave_ror_cf_threshold_audit_744h_start2880.json`, SHA256
  `96cb869c4eb8a7e944db7cf2b1b94258792931902722edd1c390c5545281a3db`.
- `output/wave_ror_cf_threshold_audit_8760h.json`, SHA256
  `586f3238c238f9d60e3e660cda0aa83d38d90bccbddf926932fbf2fc8241be87`.

## Server screens and queue

The external pair root is
`/home/zz2/National_model_server/campaign_tools/cf_744_pair_20260901_v1`.
At `2026-09-01T21:03:45+08:00`, two matched `744h/start2880` screens started:

- `2030_base_744h_cf1e6_factor5_concurrent_20260901_v1`;
- `2030_base_744h_cf1e4_factor5_concurrent_20260901_v1`.

Both use Method 2, Threads 16, Presolve 2, Crossover 0, BarIterLimit 5,
NumericFocus 1, ScaleFlag 2, no Gurobi time/memory limit, separate CPU sets and
2-second telemetry. A pair-level 95% host-memory guard can terminate only these
new screens. Because they overlap Stage B, their wall time is screening evidence;
promotion must use presolved dimensions, Factor NZ/Ops, residual trajectory and
RSS, followed by an isolated full Stage A+B comparison.

The five-step pair completed at about `2026-09-01T21:18+08:00`. Relative to
the production threshold, the `1e-4` candidate reduced Factor NZ by 2.24%,
Factor Ops by 6.14%, ordering time from 135.34 s to 117.64 s and concurrent
solver time from 562.91 s to 522.94 s. This is a promising but modest screen,
not an acceptance result.

At `2026-09-01T21:44:26+08:00`, the next matched pair started from the same
profiles without BarIterLimit:

- `2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1`;
- `2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1`.

Both use engineering Barrier checkpoint mode, identical 16-thread CPU binding,
no solver time/memory limit, corrected per-case 2-second telemetry and the same
pair-level 95% guard. They will compare full relaxed Stage A convergence and
checkpoint quality. Stage B and strict original-unit QC are still required
before either LP can be accepted.

The pair completed at `2026-09-01T22:42:36+08:00`; both runners returned zero,
the pair memory guard did not trigger, and both engineering checkpoints are
complete and eligible for an explicitly authorized deferred crossover. The
full Stage A evidence reverses the promising five-step screen:

| Metric | Baseline `1e-6` | Candidate `1e-4` | Candidate change |
|---|---:|---:|---:|
| Barrier iterations | 120 | 134 | +11.67% |
| Solver runtime (s) | 2995.079 | 3070.307 | +2.51% |
| Work units | 2842.982 | 3006.566 | +5.75% |
| End-to-end elapsed (s) | 3380.386 | 3478.729 | +2.91% |
| Process-tree RSS peak (GiB) | 20.049 | 20.402 | +1.76% |
| Raw nonzeros | 44,000,585 | 43,979,609 | -0.0477% |

The independently sampled job RSS was marginally lower for the candidate
(`21.193` versus `21.264` GB), but this is a different 2-second sampling metric
and does not override the runner's 0.5-second process-tree peak. Both runs have
an engineering-only `HARD_FAIL` solution contract and failed raw physical QC,
as expected for relaxed Barrier with Crossover disabled. The candidate objective
is `371.039 million CNY` higher (about `0.01598%`), which is not numerical drift:
the threshold changes the feasible set.

Decision: reject `coefficient_zero_tolerance=1e-4` as a performance candidate.
Do not run its Stage B, do not promote it to production or 8760h, and do not
combine it with another numerical candidate. Key terminal evidence is preserved
under `downloads/cf_744_stagea_pair_terminal_20260902_v1` in the main checkout.

The external Case 2 gate is
`/home/zz2/National_model_server/campaign_tools/case2_after_stage_b_20260901_v1`.
It starts the approved 2160h/Threads32 Case 2 exactly once only after Stage B
returns zero with QC PASS and complete reports, the production checkout is clean
at `6065bfb`, no competing solve exists, host memory use is below 90%, at least
96 GiB is available and memory PSI is normal.

## Reproduction commands

Set the same `CISPO_DATA_ROOT`, `CISPO_CF_ROOT`, `CISPO_WAVE_ROOT` and optional
hydrology mapping used by the model, then run:

```text
python scripts/audit_vre_cf_thresholds.py --planning-year 2030 --start-hour 0 --hours 8760 --output output/cf_threshold_audit_8760h.json
python scripts/audit_wave_ror_cf_thresholds.py --planning-year 2030 --start-hour 0 --hours 8760 --output output/wave_ror_cf_threshold_audit_8760h.json
```

## Promotion rule

Do not change the production default merely because the physical error bound is
small. Reject `1e-4` if it does not materially improve presolved structure,
factor operations, stable convergence or end-to-end Stage A+B time while
retaining strict original-unit QC. Do not combine this candidate with Annual
Energy Coordinate V1 until each single-factor candidate has been evaluated.
