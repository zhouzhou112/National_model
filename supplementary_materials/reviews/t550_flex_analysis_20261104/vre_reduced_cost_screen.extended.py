#!/usr/bin/env python3
"""Offline reduced-cost screening of VRE site columns from an archived LP.

Reads a Gurobi-written MPS (plain or .gz) plus the saved Barrier dual vector
(BarPi, raw original constraint order) and computes, for EVERY column,
    rc_j = c_j - sum_i a_ij * pi_i
without any solver call.  For the VRE site families (vre_capacity_gw[z],
vre_new_gw[z]) it joins the result with the exported vre_capacity.csv and
writes a per-site table, a text histogram and screening counts for several
safety margins.  It also reports per-family column counts and nonzeros so the
dense-column structure of the LP can be quantified.

Standard library + numpy only (pandas/matplotlib optional).  Read-only.
Memory: ~8 GB for the row-name map of a 51M-row model.  Run it in a Slurm
allocation, not on a login node.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

FAMILY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*?)(?:\[([0-9,]+)\])?$")
VRE_FAMILIES = ("vre_capacity_gw", "vre_new_gw")
EXTRA_FAMILIES = ("spur_augmentation_gw", "wave_capacity_gw", "wave_new_gw",
                  "hydro_capacity_gw", "hydro_new_gw", "thermal_capacity_gw",
                  "thermal_new_gw", "storage_capacity_gw", "storage_new_gw",
                  "line_capacity_gw", "line_new_gw", "trunk_augmentation_gw")


def open_text(path: Path):
    if str(path).endswith(".gz"):
        return io.TextIOWrapper(io.BufferedReader(gzip.open(path, "rb"), 1 << 20), encoding="ascii", errors="replace")
    return open(path, "r", encoding="ascii", errors="replace", buffering=1 << 20)


def split_name(name: str):
    m = FAMILY_RE.match(name)
    if not m:
        return name, None
    return m.group(1), m.group(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mps", required=True)
    ap.add_argument("--barpi", required=True, help="dual_barpi.npy (raw original constraint order)")
    ap.add_argument("--vre-capacity-csv", default=None, help="output_8760/vre_capacity.csv for primal/bounds join")
    ap.add_argument("--out", required=True)
    ap.add_argument("--margins", default="0,0.05,0.1,0.2,0.5,1.0")
    ap.add_argument("--progress-every", type=int, default=20_000_000)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from dual_extensions import verify_inputs, RowsObserver, capacity_output
    case_out = out.parent
    identity = verify_inputs(Path(a.mps).parents[2], case_out)
    t0 = time.time()
    pi = np.load(a.barpi, mmap_mode="r")
    pi = np.asarray(pi, dtype=np.float64)
    n_rows_pi = pi.shape[0]
    print(f"[{time.time()-t0:7.1f}s] BarPi loaded: {n_rows_pi} entries, finite={np.isfinite(pi).all()}", flush=True)

    observer = RowsObserver(Path(a.mps).parents[2], case_out, pi, identity)
    row_index: dict[str, int] = {}
    obj_row = None
    section = None
    # per-column accumulators (column order = MPS order)
    col_names_of_interest: dict[int, str] = {}
    col_obj: list[float] = []
    col_atpi: list[float] = []
    col_nnz: list[int] = []
    fam_cols = defaultdict(int)
    fam_nnz = defaultdict(int)
    fam_maxnnz = defaultdict(int)
    cur_name = None
    cur_idx = -1
    cur_obj = 0.0
    cur_atpi = 0.0
    cur_nnz = 0
    cur_fam = None
    bounds: dict[str, dict] = {}
    rhs_obj_offset = 0.0
    lines = 0
    interest = set(VRE_FAMILIES) | set(EXTRA_FAMILIES)

    def flush_col():
        nonlocal cur_name, cur_idx, cur_obj, cur_atpi, cur_nnz, cur_fam
        if cur_name is None:
            return
        col_obj.append(cur_obj); col_atpi.append(cur_atpi); col_nnz.append(cur_nnz)
        fam_cols[cur_fam] += 1; fam_nnz[cur_fam] += cur_nnz
        if cur_nnz > fam_maxnnz[cur_fam]:
            fam_maxnnz[cur_fam] = cur_nnz
        if cur_fam in interest:
            col_names_of_interest[cur_idx] = cur_name

    with open_text(Path(a.mps)) as f:
        for line in f:
            lines += 1
            if lines % a.progress_every == 0:
                print(f"[{time.time()-t0:7.1f}s] {lines/1e6:.0f}M lines, section={section}, rows={len(row_index)}, cols={cur_idx+1}", flush=True)
            if line[0] not in " \t":
                tok = line.split()
                if not tok or tok[0].startswith("*"):
                    continue
                key = tok[0]
                if key in ("ROWS", "COLUMNS", "RHS", "RANGES", "BOUNDS", "ENDATA", "NAME", "OBJSENSE", "OBJSENSE_MAX", "OBJSENSE_MIN"):
                    if key == "COLUMNS":
                        observer.finish()
                        print(f"[{time.time()-t0:7.1f}s] ROWS done: {len(row_index)} constraint rows (BarPi {n_rows_pi})", flush=True)
                        if len(row_index) != n_rows_pi:
                            print("WARNING: row count differs from BarPi length; rc will be unreliable", flush=True)
                    if key in ("RHS", "RANGES", "BOUNDS", "ENDATA") and section == "COLUMNS":
                        flush_col(); cur_name = None
                        print(f"[{time.time()-t0:7.1f}s] COLUMNS done: {cur_idx+1} columns", flush=True)
                    section = key
                continue
            tok = line.split()
            if section == "ROWS":
                typ, name = tok[0], tok[1]
                if typ == "N":
                    if obj_row is None:
                        obj_row = name
                    continue
                observer.consume(typ, name)
                row_index[name] = len(row_index)
            elif section == "COLUMNS":
                name = tok[0]
                if name == "MARKER" or (len(tok) >= 3 and tok[1] == "'MARKER'"):
                    continue
                if name != cur_name:
                    flush_col()
                    cur_name = name; cur_idx += 1; cur_obj = 0.0; cur_atpi = 0.0; cur_nnz = 0
                    cur_fam = split_name(name)[0]
                # entries come in pairs
                for k in range(1, len(tok) - 1, 2):
                    rname = tok[k]; val = float(tok[k + 1])
                    if rname == obj_row:
                        cur_obj += val
                    else:
                        ri = row_index.get(rname)
                        if ri is None:
                            raise KeyError(f"unknown row {rname} in column {name}")
                        cur_atpi += val * pi[ri]
                        cur_nnz += 1
            elif section == "RHS":
                for k in range(1, len(tok) - 1, 2):
                    if tok[k] == obj_row:
                        rhs_obj_offset = float(tok[k + 1])
            elif section == "BOUNDS":
                btype = tok[0]
                cname = tok[2] if len(tok) >= 3 else None
                if cname is None:
                    continue
                fam = split_name(cname)[0]
                if fam in interest:
                    b = bounds.setdefault(cname, {})
                    if btype in ("UP", "LO", "FX", "MI", "PL", "FR", "BV"):
                        b[btype] = float(tok[3]) if len(tok) > 3 else None
    ncols = cur_idx + 1
    print(f"[{time.time()-t0:7.1f}s] parse finished: {lines} lines, {ncols} columns, {len(row_index)} rows", flush=True)

    obj = np.asarray(col_obj, dtype=np.float64)
    atpi = np.asarray(col_atpi, dtype=np.float64)
    nnz = np.asarray(col_nnz, dtype=np.int64)
    rc = obj - atpi
    capacity_output(out, col_names_of_interest, obj, rc, nnz, split_name, EXTRA_FAMILIES)
    np.save(out / "reduced_cost_all_columns.npy", rc)
    np.save(out / "column_nnz_all_columns.npy", nnz)

    # ---- family summary -------------------------------------------------
    total_nnz = int(nnz.sum())
    with open(out / "column_family_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "columns", "nonzeros", "nnz_share", "max_nnz_per_column", "mean_nnz_per_column"])
        for fam, c in sorted(fam_cols.items(), key=lambda kv: -fam_nnz[kv[0]]):
            w.writerow([fam, c, fam_nnz[fam], f"{fam_nnz[fam]/max(total_nnz,1):.6f}", fam_maxnnz[fam], f"{fam_nnz[fam]/c:.1f}"])
    dense_cols = int((nnz >= 1000).sum())
    print(f"columns with >=1000 nonzeros: {dense_cols}; total nnz {total_nnz}", flush=True)

    # ---- VRE site table ---------------------------------------------------
    site = {}
    for idx, name in col_names_of_interest.items():
        fam, sub = split_name(name)
        if fam in VRE_FAMILIES and sub is not None:
            z = int(sub)
            d = site.setdefault(z, {})
            d[fam] = dict(col=idx, obj=float(obj[idx]), atpi=float(atpi[idx]), rc=float(rc[idx]), nnz=int(nnz[idx]), bounds=bounds.get(name, {}))
    zs = sorted(site)
    print(f"VRE sites found in MPS: {len(zs)}", flush=True)
    prim = {}
    if a.vre_capacity_csv and Path(a.vre_capacity_csv).exists():
        with open(a.vre_capacity_csv, newline="", encoding="utf-8-sig") as fh:
            for i, row in enumerate(csv.DictReader(fh)):
                prim[i] = row
        print(f"vre_capacity.csv rows: {len(prim)}", flush=True)
    rows_out = []
    for z in zs:
        cap = site[z].get("vre_capacity_gw", {}); new = site[z].get("vre_new_gw", {})
        c_total = cap.get("obj", 0.0) + new.get("obj", 0.0)
        rc_build = cap.get("rc", 0.0) + new.get("rc", 0.0)
        p = prim.get(z, {})
        try:
            upper = float(p.get("capacity_upper_gw", "nan")); floor = float(p.get("capacity_floor_gw", "nan"))
            newcap = float(p.get("new_capacity_gw", "nan"))
        except ValueError:
            upper = floor = newcap = float("nan")
        headroom = upper - floor if not (math.isnan(upper) or math.isnan(floor)) else float("nan")
        ratio = rc_build / c_total if c_total > 0 else float("nan")
        rows_out.append(dict(site_index=z, grid_uid=p.get("grid_uid", ""), province_code=p.get("province_code", ""),
                             technology=p.get("technology", ""), cap_col=cap.get("col"), new_col=new.get("col"),
                             cap_nnz=cap.get("nnz"), obj_cap=cap.get("obj"), obj_new=new.get("obj"), obj_total=c_total,
                             rc_cap=cap.get("rc"), rc_new=new.get("rc"), rc_build=rc_build, rc_ratio=ratio,
                             capacity_floor_gw=floor, capacity_upper_gw=upper, headroom_gw=headroom,
                             new_capacity_gw=newcap))
    with open(out / "vre_site_reduced_costs.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()) if rows_out else ["site_index"])
        w.writeheader(); w.writerows(rows_out)

    # ---- screening statistics -------------------------------------------
    ratio = np.array([r["rc_ratio"] for r in rows_out], dtype=float)
    head = np.array([r["headroom_gw"] for r in rows_out], dtype=float)
    newc = np.array([r["new_capacity_gw"] for r in rows_out], dtype=float)
    capnnz = np.array([r["cap_nnz"] or 0 for r in rows_out], dtype=float)
    tech = np.array([r["technology"] for r in rows_out])
    has_head = np.nan_to_num(head, nan=1.0) > 1e-9
    built = np.nan_to_num(newc, nan=0.0) > 1e-6
    summary = {
        "sites": len(rows_out), "sites_with_headroom": int(has_head.sum()), "sites_built_in_base": int(built.sum()),
        "vre_capacity_nnz_total": int(capnnz.sum()), "lp_nnz_total": total_nnz,
        "vre_capacity_nnz_share": float(capnnz.sum() / max(total_nnz, 1)),
        "rc_ratio_of_built_sites": {"min": float(np.nanmin(ratio[built])) if built.any() else None,
                                    "median": float(np.nanmedian(ratio[built])) if built.any() else None,
                                    "max": float(np.nanmax(ratio[built])) if built.any() else None},
        "screening": [], "by_technology": {},
    }
    for m in [float(x) for x in a.margins.split(",")]:
        keep = has_head & (np.nan_to_num(ratio, nan=0.0) < m)
        summary["screening"].append({
            "margin": m, "sites_retained": int(keep.sum()), "retained_share": float(keep.mean()),
            "retained_nnz_share_of_vre_capacity": float(capnnz[keep].sum() / max(capnnz.sum(), 1)),
            "built_sites_dropped": int((built & ~keep).sum()),
        })
    for t in sorted(set(tech)):
        sel = tech == t
        summary["by_technology"][t] = {"sites": int(sel.sum()), "with_headroom": int((sel & has_head).sum()),
                                       "built": int((sel & built).sum()),
                                       "retained_margin_0.2": int((sel & has_head & (np.nan_to_num(ratio, nan=0.0) < 0.2)).sum())}
    # text histogram of rc_ratio for sites with headroom
    edges = [-1e9, -0.05, 0.0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 1e9]
    h, _ = np.histogram(ratio[has_head & np.isfinite(ratio)], bins=edges)
    summary["rc_ratio_histogram_sites_with_headroom"] = [{"bin": f"[{edges[i]:g},{edges[i+1]:g})", "count": int(h[i])} for i in range(len(h))]
    summary["elapsed_seconds"] = time.time() - t0
    summary["mps"] = str(a.mps); summary["barpi"] = str(a.barpi)
    (out / "screening_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    with open(out / "rc_ratio_histogram.txt", "w") as fh:
        fh.write("rc_build / annualized_cost, sites with headroom (rc<0 => would be built; large positive => never built)\n")
        for b in summary["rc_ratio_histogram_sites_with_headroom"]:
            fh.write(f"{b['bin']:>16s} {b['count']:8d} {'#' * int(60 * b['count'] / max(h.max(), 1))}\n")
    print(json.dumps(summary["screening"], indent=1))
    print(open(out / "rc_ratio_histogram.txt").read())
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        v = ratio[has_head & np.isfinite(ratio)]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(np.clip(v, -1, 10), bins=110, color="#4477AA")
        ax.set_xlabel("reduced cost of building 1 GW / annualized cost (clipped to [-1,10])"); ax.set_ylabel("sites")
        ax.set_title("VRE site reduced-cost ratio (sites with headroom)")
        fig.tight_layout(); fig.savefig(out / "rc_ratio_histogram.png", dpi=150)
    except Exception as e:  # noqa
        print(f"matplotlib unavailable or failed: {e}")
    print(f"[{time.time()-t0:7.1f}s] done -> {out}", flush=True)


if __name__ == "__main__":
    sys.modules["matplotlib"] = None  # No figures for this task.
    main()
