"""Small, explicit physical-data cleanup and cyclic-storage range reduction.

No generic matrix thresholding: resource cutoffs carry physical units. The
storage helper removes an arbitrary constant inventory offset in a cyclic
reservoir model; it never fixes the inventory at a particular hour.
"""
from __future__ import annotations

import numpy as np


def zero_capacity_headroom(floor, upper, threshold, asset_ids):
    """Opt-in GW bound approximation, with the removed feasible range recorded."""
    floor = np.asarray(floor, dtype=float)
    upper = np.asarray(upper, dtype=float)
    headroom = upper - floor
    rows = np.flatnonzero((np.abs(headroom) <= threshold) & (headroom != 0)) if threshold > 0 else np.array([], dtype=int)
    removed = headroom[rows].copy()
    if threshold > 0:
        headroom[rows] = 0.0
        upper = upper.copy()
        upper[rows] = floor[rows]
    return headroom, upper, {
        "cutoff_gw": float(threshold), "site_rows": rows.tolist(),
        "asset_ids": [str(asset_ids[i]) for i in rows],
        "removed_gw": removed.tolist(), "total_removed_gw": float(removed.sum()),
    }


def zero_retrofit_upper(upper, threshold, asset_ids):
    """Discard only positive retrofit UB below the explicit GW cutoff."""
    values = np.asarray(upper, dtype=float).copy()
    rows = np.flatnonzero((values > 0) & (values < threshold))
    removed = values[rows].copy()
    values[rows] = 0.0
    return values, {"cutoff_gw": float(threshold), "site_rows": rows.tolist(),
        "asset_ids": [str(asset_ids[i]) for i in rows],
        "removed_gw": removed.tolist(), "total_removed_gw": float(removed.sum())}


def clean_cascade_transfer_fractions(fractions, threshold: float):
    """Discard explicitly negligible routed-water fractions; never add water.

    This is a physical approximation, recorded by edge and hour. It must be
    applied after natural-flow reconciliation so discarded transfers cannot
    be silently reassigned to local inflow. Zero is the legacy default.
    """
    if not np.isfinite(threshold) or not 0 <= threshold <= 1e-3:
        raise ValueError('cascade_transfer_cleanup_fraction must be in [0, 1e-3]')
    cleaned=[];records=[]
    for edge,values in enumerate(fractions):
        values=np.asarray(values,dtype=float)
        if values.ndim!=1 or not np.isfinite(values).all() or (values<0).any() or (values>1).any():
            raise ValueError('Cascade transfer fractions must be finite and in [0, 1]')
        small=(values>0)&(values<threshold)
        result=values.copy();result[small]=0.;cleaned.append(result)
        if small.any():
            records.append(dict(edge_index=edge,hour_indices=np.flatnonzero(small).tolist(),
                                removed_fractions=values[small].tolist()))
    return cleaned,dict(threshold_fraction=threshold,removed_edge_hours=sum(len(r['hour_indices']) for r in records),
        edges=records,interpretation='Additional explicitly discarded routed water; no local-inflow compensation; not a matrix-wide coefficient cutoff')


def independent_spill_upper_scaled(
    hydro, release_upper: np.ndarray, flow_scale_m3s: float,
    *, positive_bound_floor_m3s: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Remove deferred spill freedom only at hydraulically isolated stations.

    For fixed feasible generation g, the cyclic inventory recursion that spills
    only on overflow is V[t]=min(S,V[t-1]+inflow[t]-g[t]). A periodic feasible
    trajectory exists whenever the original one does (start from its largest
    feasible initial inventory and take the monotone periodic limit). Its spill
    is max(0,V[t-1]+inflow[t]-g[t]-S) <= inflow[t]. Thus these bounds preserve
    the generation/capacity projection, though the original spill/storage path
    can change. No station touching a cascade edge is eligible: delayed spill
    can have downstream generation value. Assumes cyclic free initial storage,
    fixed head, no spill reward/requirement and no absolute inventory service.

    An optional positive-bound floor relaxes tiny positive spill upper bounds
    toward the original release bounds. It preserves the same dispatch
    projection and exact dry-hour zeros, without adding any inflow. The floor
    applies to upper bounds only, never to the spill variable's lower bound.
    """
    local = np.asarray(hydro.reservoir_local_inflow_m3s, dtype=float)
    upper = np.asarray(release_upper, dtype=float)
    if (upper.shape != local.shape or local.ndim != 2 or not np.isfinite(flow_scale_m3s)
            or flow_scale_m3s <= 0 or not np.isfinite(local).all() or (local < 0).any()
            or not np.isfinite(upper).all() or (upper < 0).any()
            or not np.isfinite(positive_bound_floor_m3s) or positive_bound_floor_m3s < 0):
        raise ValueError('Independent spill bounds require finite nonnegative water bounds')
    eligible = np.ones(len(local), dtype=bool)
    for column in (hydro.cascade_edge_source_local_rows, hydro.cascade_edge_target_local_rows):
        for rows in column:
            rows = np.asarray(rows, dtype=int)
            if (rows < 0).any() or (rows >= len(local)).any():
                raise ValueError('Invalid cascade station index in spill reduction')
            eligible[rows] = False
    result = upper.copy()
    inflow = local[eligible] / flow_scale_m3s
    inflow = np.where(inflow > 0, np.maximum(inflow, positive_bound_floor_m3s / flow_scale_m3s), 0.0)
    # Outward rounding of positive values never invents spill at a dry hour.
    inflow = np.where(inflow > 0, np.nextafter(inflow, np.inf), 0.0)
    result[eligible] = np.minimum(result[eligible], inflow)
    return result, eligible


def cyclic_inventory_upper_m3(hydro) -> np.ndarray:
    """Bound the necessary storage excursion by a safe total inflow budget.

For any feasible cyclic trajectory V, V-min(V) has the same releases and
lies in [0, min(source storage, total inflow)]. Incoming release budgets are
propagated topologically using max(transfer fraction); hence this also holds
for a cascade with time-dependent transfer losses and cyclic travel times.
This assumes storage enters only differences and zero-lower/upper bounds.
It preserves feasible dispatch/capacity projections, not absolute inventories.
"""
    local = np.asarray(hydro.reservoir_local_inflow_m3s, dtype=float)
    storage = np.asarray(hydro.reservoir_active_storage_m3, dtype=float)
    if (local.ndim != 2 or storage.shape != (local.shape[0],)
            or not np.isfinite(local).all() or not np.isfinite(storage).all()
            or (local < 0).any() or (storage < 0).any()):
        raise ValueError('Cyclic storage reduction requires nonnegative finite water data')
    budget = local.sum(axis=1) * 3600.0
    incoming = {int(i): [] for i in hydro.cascade_station_local_rows}
    fields = (hydro.cascade_edge_source_local_rows, hydro.cascade_edge_target_local_rows,
              hydro.cascade_edge_target_weights, hydro.cascade_edge_transfer_fraction)
    if len({len(x) for x in fields}) != 1:
        raise ValueError('Unequal cascade edge arrays')
    for sources, targets, weights, fractions in zip(*fields):
        fractions = np.asarray(fractions, dtype=float)
        if (len(targets) != len(weights) or not np.isfinite(fractions).all()
                or (fractions < 0).any() or (fractions > 1).any()
                or not np.isfinite(weights).all() or (np.asarray(weights) < 0).any()):
            raise ValueError('Invalid cascade transfer data')
        for target, weight in zip(targets, weights):
            incoming[int(target)].append((np.asarray(sources, dtype=int),
                                          float(weight) * float(fractions.max(initial=0))))
    unresolved = set(incoming)
    resolved = set(range(len(storage))) - unresolved
    while unresolved:
        ready = [i for i in sorted(unresolved)
                 if all(set(src).issubset(resolved) for src, _ in incoming[i])]
        if not ready:
            raise ValueError('Cyclic or unresolved cascade graph')
        for i in ready:
            budget[i] += sum(float(budget[src].sum()) * fraction for src, fraction in incoming[i])
            resolved.add(i)
            unresolved.remove(i)
    # Outward relative padding does not manufacture a positive zero-flow bound.
    budget = np.where(budget > 0, np.nextafter(budget * (1.0 + 1e-12), np.inf), 0.0)
    return np.minimum(storage, budget)
