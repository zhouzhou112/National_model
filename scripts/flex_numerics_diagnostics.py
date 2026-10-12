"""Original-unit overnight diagnostics; no acceptance gate or model mutation.

Call before_solve before optimize, after_solve in finally, then service_diagnostics.
Raw LP and available X/BarX/Pi/BarPi survive any subsequent semantic QC failure.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def before_solve(model, output):
    from cispo_model.solution_preservation import archive_model
    keys = ("Method", "Presolve", "Aggregate", "NumericFocus", "ScaleFlag", "BarConvTol",
            "Crossover", "Threads", "Seed", "FeasibilityTol", "OptimalityTol", "TimeLimit", "SoftMemLimit")
    save(output / "solver_parameters.json", {k: getattr(model.Params, k) for k in keys})
    archive_model(model, output, include_name_catalog=True)


def after_solve(model, output, registry=None):
    from cispo_model.solution_preservation import save_numeric_snapshot
    info = {}
    for key in ("Status", "SolCount", "Runtime", "BarIterCount", "ObjVal", "ConstrVio", "BoundVio", "DualVio", "ComplVio", "MaxMemUsed"):
        try:
            info[key] = getattr(model, key)
        except Exception as exc:
            info[key] = {"unavailable": str(exc)}
    save(output / "solver_result.json", info)
    save_numeric_snapshot(model, output, row_scaling_registry=registry)
    return info


def service_diagnostics(config, data, block, hours, start, output):
    from validate_flexible_portfolios import physical_qc
    qc, values = physical_qc(config, data, block, hours, start)
    service = data.flexible_load_v4
    cap = values["flexible_service_capacity"]
    profile = []
    worst = {}
    positive = lambda a: float(np.maximum(a, 0).max(initial=0))
    for col, component in enumerate(("heating", "cooling")):
        state, up, down = [np.asarray(values[f"{component}_{key}"]) for key in ("state", "shift_up", "shift_down")]
        p = service.thermal_parameters[component]
        residual = state - p["retention_per_hour"][:, None] * np.roll(state, 1, axis=1) - p["charge_efficiency"][:, None] * up + down / p["discharge_efficiency"][:, None]
        qc[f"{component}_cycle_gwh"] = float(np.abs(residual[:, 0]).max())
        qc[f"{component}_state_lower_gwh"] = positive(-state)
        for direction, value in (("up", up), ("down", down)):
            qc[f"{component}_{direction}_envelope_gw"] = positive(value - service.thermal_envelopes_gw[f"{component}_{direction}"][:, start:start+hours])
            qc[f"{component}_{direction}_lower_gw"] = positive(-value)
        pos = np.unravel_index(np.abs(residual).argmax(), residual.shape)
        worst[component] = dict(province_code=int(data.provinces.province_code.iloc[pos[0]]), hour_position=int(pos[1]), hour_index=int(start+pos[1]), signed_residual_gwh=float(residual[pos]))
        for province in range(len(data.provinces)):
            profile.append(pd.DataFrame(dict(component=component, province_code=int(data.provinces.province_code.iloc[province]), hour_position=np.arange(hours), hour_index=np.arange(start,start+hours), signed_residual_gwh=residual[province])))
    pd.concat(profile, ignore_index=True).to_csv(output / "thermal_residual_profile.csv.gz", index=False)
    np.savez_compressed(output / "service_values.npz", **{k: np.asarray(v) for k, v in values.items()})
    table = pd.DataFrame({"province_code": data.provinces.province_code.to_numpy()})
    for i, s in enumerate(("heating", "cooling", "ev_v1g", "ev_v2g")):
        table[s + "_contract_gw"] = cap[:, i]
    for key, name in (("ev_enrolled_service_fraction", "alpha"), ("ev_bidirectional_service_fraction", "beta")):
        table[name] = np.asarray(values[key]).ravel()
    table.to_csv(output / "service_decisions.csv", index=False)
    report = dict(physical_qc=qc, thermal_worst=worst,
                  maximum_service_residual_gw_gwh=max(v for k,v in qc.items() if k.endswith(("_gw", "_gwh"))),
                  dimensionless_metrics={k:v for k,v in qc.items() if not k.endswith(("_gw", "_gwh"))},
                  capacity_credit="NOT_PRESENT_IN_PRICE_TAKER; full-model credit rows audited separately")
    save(output / "service_diagnostics.json", report)
    return report
