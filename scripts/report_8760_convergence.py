"""Audit a saved Stage-A Barrier log and create a reproducible illustrated note.

No Gurobi import, model construction, presolve, optimize, or remote writes.
Run extract/plot with a Python environment containing numpy/matplotlib; run
PDF export separately with reportlab. Paths are supplied by the caller.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
ROW = re.compile(r"^\s*(\d+)(\*?)\s+" + r"\s+".join([f"({NUMBER})"] * 5) + r"\s+(\d+)s\s*$")
FIELDS = ("primal_objective", "dual_objective", "primal_infeasibility", "dual_infeasibility", "complementarity")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No data for {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_stdout(text):
    """Keep the original log line and its own residual channel."""
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = ROW.fullmatch(line)
        if match:
            row = dict(zip(FIELDS, map(float, match.groups()[2:7])))
            rows.append({"iteration": int(match[1]), "source_line": line_number,
                         "starred": bool(match[2]), **row,
                         "runtime_seconds": int(match[8])})
    return rows


def validate_series(stdout, callback):
    if not stdout or len(stdout) != len(callback):
        raise ValueError("Missing or mismatched Barrier records")
    expected = list(range(len(stdout)))
    if [r["iteration"] for r in stdout] != expected or [r["iteration"] for r in callback] != expected:
        raise ValueError("Iteration sequence has gaps, duplicates, or multiple solves")
    for a, b in zip(stdout, callback):
        for key in FIELDS:
            if not math.isfinite(a[key]) or not math.isfinite(b[key]):
                raise ValueError("Nonfinite convergence value")
        # Only objectives and time are checked across channels. Residuals differ.
        for key in FIELDS[:2]:
            if not math.isclose(a[key], b[key], rel_tol=1e-8, abs_tol=1e-8):
                raise ValueError(f"Objective mismatch at {a['iteration']} / {key}")
        if abs(a["runtime_seconds"] - b["runtime_seconds"]) > 1.1:
            raise ValueError("Log/callback time mismatch")
    if any(b["runtime_seconds"] <= a["runtime_seconds"] for a, b in zip(callback, callback[1:])):
        raise ValueError("Nonmonotone callback time")


def duration(seconds):
    value = round(seconds)
    days, value = divmod(value, 86400)
    hours, value = divmod(value, 3600)
    minutes, seconds = divmod(value, 60)
    return (f"{days}天" if days else "") + f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def extract(source, recovery, out):
    import numpy as np

    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    with (source / "downloaded_files_sha256.csv").open(encoding="utf-8-sig", newline="") as f:
        archived_hashes = {r["path"]: r["sha256"].lower() for r in csv.DictReader(f)}
    provenance = []

    def track(path, relative=None):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = archived_hashes.get(relative) if relative else None
        if relative and expected is None:
            raise ValueError(f"Missing archived hash: {relative}")
        if expected and expected != digest:
            raise ValueError(f"Source hash mismatch: {path}")
        provenance.append({"path": str(path.resolve()), "bytes": path.stat().st_size,
                           "sha256": digest, "archive_verification": "PASS" if expected else "RECORDED_ONLY"})
        return path

    def src(relative):
        return track(source / relative, relative)

    log_text = src("output/gurobi.log").read_text(encoding="utf-8-sig")
    stdout = parse_stdout(log_text)
    events = [json.loads(line) for line in src("output/solver_telemetry.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    callback = []
    for line_number, event in enumerate(events, 1):
        if event.get("phase") == "barrier" and event["event"] == "solver_progress":
            callback.append({"iteration": int(event["iteration"]), "source_line": line_number,
                             **{k: v for k, v in event.items() if k not in {"event", "phase", "iteration"}}})
    validate_series(stdout, callback)
    solve = read_json(src("output/solve_report.json"))
    build = read_json(src("output/build_report.json"))
    launch = read_json(src("run_control/launch_record.json"))
    config_snapshot = read_json(src("output/model_config_snapshot.json"))
    terminal = dict(line.split("=", 1) for line in src("run_control/terminal_status.txt").read_text().splitlines())
    track(source / "downloaded_files_sha256.csv")
    recover = {name: read_json(track(recovery / f"{name}.json")) for name in
               ("recovery_progress", "offline_recovery", "preservation_runtime_memory", "solution_qc")}
    if solve["iteration_counts"]["barrier"] != len(callback) - 1:
        raise ValueError("Final iteration count mismatch")

    def capture(pattern, converter=float):
        match = re.search(pattern, log_text)
        if not match:
            raise ValueError(f"Log field missing: {pattern}")
        return converter(match[1])

    presolve = capture(r"Presolve time: ([\d.]+)s")
    ordering = capture(r"Ordering time: ([\d.]+)s")
    presolved_match = re.search(r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", log_text)
    if not presolved_match:
        raise ValueError("Missing presolved model dimensions")
    before = solve["model_statistics"]
    after = dict(zip(("constraints", "variables", "nonzeros"), map(int, presolved_match.groups())))
    dimensions = [{"item": key, "original": before[key], "presolved": after[key],
                   "net_removed": before[key] - after[key], "net_reduction_percent": 100 * (1 - after[key] / before[key])}
                  for key in ("constraints", "variables", "nonzeros")]
    ranges = []
    for label, low, high, precision in (
        ("Matrix", before["coefficient_min_abs"], before["coefficient_max_abs"], "exact_json"),
        ("Objective", before["objective_coefficient_min_abs"], before["objective_coefficient_max_abs"], "exact_json"),
        ("RHS", before["rhs_min_abs"], before["rhs_max_abs"], "exact_json"),
        ("Bounds", 6e-11, 4e5, "rounded_log"),
    ):
        ranges.append({"category": label, "min_abs_nonzero": low, "max_abs": high,
                       "max_min_ratio": high / low, "log10_span": math.log10(high / low), "precision": precision})
    t0, t1 = callback[0]["runtime_seconds"], callback[-1]["runtime_seconds"]
    for i, row in enumerate(callback):
        row["absolute_objective_difference"] = abs(row["primal_objective"] - row["dual_objective"])
        row["relative_objective_difference"] = row["absolute_objective_difference"] / max(1, abs(row["primal_objective"]), abs(row["dual_objective"]))
        row["iteration_elapsed_seconds"] = row["runtime_seconds"] - callback[i - 1]["runtime_seconds"] if i else None
    intervals = np.diff([r["runtime_seconds"] for r in callback])
    solver_seconds = solve["runtime_seconds"]
    phases = [
        {"stage": "模型构建", "seconds": build["memory_after_build"]["elapsed_seconds"], "basis": "build_report.memory_after_build.elapsed_seconds", "inside_solver": False},
        {"stage": "预求解", "seconds": presolve, "basis": "gurobi.log Presolve time", "inside_solver": True},
        {"stage": "排序", "seconds": ordering, "basis": "gurobi.log Ordering time", "inside_solver": True},
        {"stage": "其他初始化（未分解）", "seconds": t0 - presolve - ordering, "basis": "iteration0 runtime - presolve - ordering", "inside_solver": True},
        {"stage": "Barrier 迭代0→607", "seconds": t1 - t0, "basis": "last callback runtime - first callback runtime", "inside_solver": True},
        {"stage": "求解收尾（未分解）", "seconds": solver_seconds - t1, "basis": "solver_end runtime - last callback runtime", "inside_solver": True},
    ]
    for row in phases:
        row["duration"] = duration(row["seconds"])
        row["solver_share_percent"] = 100 * row["seconds"] / solver_seconds if row["inside_solver"] else None
    if not math.isclose(sum(r["seconds"] for r in phases if r["inside_solver"]), solver_seconds, abs_tol=1e-6):
        raise ValueError("Phase time partition does not close")
    if any(r["seconds"] < 0 for r in phases):
        raise ValueError("Negative phase time")
    milestones = [{"iteration": i, "elapsed_days": callback[i]["runtime_seconds"] / 86400,
                   "primal_objective_million_cny": callback[i]["primal_objective"],
                   "dual_objective_million_cny": callback[i]["dual_objective"],
                   "relative_objective_difference": callback[i]["relative_objective_difference"],
                   **{"stdout_" + k: stdout[i][k] for k in FIELDS[2:]}}
                  for i in [0, 100, 200, 300, 400, 500, 593, len(callback) - 1]]
    key_lines = [{"line": i, "text": line.strip()} for i, line in enumerate(log_text.splitlines(), 1)
                 if any(word in line for word in ("Optimize a model", "fingerprint:", "range", "Presolve time:", "Presolved:",
                    "Ordering time:", "Dense cols", "Free vars", "AA' NZ", "Factor NZ", "Factor Ops", "Barrier solved", "Optimal objective", "User-callback calls"))]
    raw_quality = solve["solution_quality"]
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_dir": str(source.resolve()), "recovery_dir": str(recovery.resolve()),
        "source_commit": launch["cloud_code_commit"],
        "configuration_snapshot": config_snapshot,
        "report_code_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "job_id": launch["job_id"], "fingerprint": capture(r"Model fingerprint: (\S+)", str),
        "source_hash_verification": "PASS", "log_points": len(stdout), "last_iteration": len(stdout) - 1,
        "series_validation": "PASS; contiguous; time/objective rounding agreement; residuals kept separate",
        "job_started_at": launch["started_at"], "job_finished_at": terminal["finished_at"],
        "job_wall_seconds": (datetime.fromisoformat(terminal["finished_at"]) - datetime.fromisoformat(launch["started_at"])).total_seconds(),
        "solver_started_at": events[0]["timestamp"], "solver_finished_at": events[-1]["timestamp"],
        "solver_seconds": solver_seconds, "solver_days": solver_seconds / 86400,
        "barrier_iterations_seconds": t1 - t0, "barrier_solver_share_percent": 100 * (t1 - t0) / solver_seconds,
        "iteration_interval_minutes": {"min": float(intervals.min() / 60), "median": float(np.median(intervals) / 60),
                                       "mean": float(intervals.mean() / 60), "max": float(intervals.max() / 60)},
        "last_100_intervals_days": (t1 - callback[-101]["runtime_seconds"]) / 86400,
        "first_complementarity_below_1e8": next(r["iteration"] for r in stdout if r["complementarity"] < 1e-8),
        "dimensions": dimensions, "ranges": ranges, "phases": phases, "milestones": milestones,
        "resources": launch["resources"], "parameters": solve["solver_parameters"],
        "barrier_structure": {"dense_columns": capture(r"Dense cols\s*:\s*(\d+)", int), "free_variables": capture(r"Free vars\s*:\s*(\d+)", int),
                              "aa_transpose_nnz_approx": capture(r"AA' NZ\s*:\s*(\S+)"), "factor_nnz_approx": capture(r"Factor NZ\s*:\s*(\S+)"),
                              "factor_ops_approx": capture(r"Factor Ops\s*:\s*(\S+)"), "factor_memory_estimate_log_gb": 300.0},
        "peak_process_tree_rss_gib": solve["runtime_memory"]["peak_process_tree_rss_gib"],
        "peak_build_rss_gib": build["memory_after_build"]["peak_process_tree_rss_gib"],
        "peak_gurobi_memory_decimal_gb": max(r["max_memory_used_gb"] for r in callback),
        "user_callback_seconds": capture(r"time in user-callback ([\d.]+) sec"),
        "final_stdout": stdout[-1], "final_callback": callback[-1], "solution_quality": raw_quality,
        "solution_contract": solve["solution_contract"], "solver_status": solve["status"],
        "work_units": solve["work_units"], "stage_b_executed": False,
        "recovery": recover, "key_log_lines": key_lines,
    }
    write_csv(data / "barrier_stdout.csv", stdout)
    write_csv(data / "barrier_callback.csv", callback)
    write_csv(data / "matrix_ranges.csv", ranges)
    write_csv(data / "model_dimensions.csv", dimensions)
    write_csv(data / "phase_times.csv", phases)
    write_csv(data / "milestones.csv", milestones)
    write_csv(data / "source_sha256.csv", provenance)
    write_json(data / "summary.json", summary)
    write_json(data / "key_log_lines.json", key_lines)
    return summary, stdout, callback


def plot(out, s, stdout, callback):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullLocator
    import numpy as np

    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                         "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7,
                         "svg.fonttype": "none", "pdf.fonttype": 42, "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.1,
                         "savefig.facecolor": "white"})
    figures = out / "figures"
    figures.mkdir(exist_ok=True)
    colors = ["#247A9E", "#D27C2C", "#7A5195", "#777777"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), gridspec_kw={"width_ratios": [1.18, 1]})
    ax = axes[0]
    for i, row in enumerate(s["ranges"]):
        lo, hi = row["min_abs_nonzero"], row["max_abs"]
        ax.plot([lo, hi], [i, i], color=colors[i], lw=2.4, ls="--" if row["precision"] == "rounded_log" else "-", marker="|")
        ax.text(math.sqrt(lo * hi), i - 0.16, f"{lo:.2e} — {hi:.2e}", ha="center", va="bottom", fontsize=7)
    ax.set_yticks(range(4), ["Matrix", "Objective", "RHS", "Bounds*"])
    ax.set_xscale("log")
    ax.set_xlim(1e-11, 1e7)
    ax.set_ylim(3.6, -0.7)
    ax.set_xticks([1e-10, 1e-6, 1e-2, 1e2, 1e6])
    ax.set_xlabel("非零绝对值（各类别物理单位不同）")
    ax.set_title("a  原始模型数值范围", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#e5e9ed", lw=0.5)
    ax = axes[1]
    chosen = [s["phases"][i] for i in [0, 1, 2, 3, 4]]
    labels = ["模型构建", "预求解", "排序", "其他初始化", "迭代0→607"]
    for i, r in enumerate(chosen):
        ax.plot(r["seconds"] / 3600, i, "o", color=colors[0] if i < 4 else colors[1], ms=4)
        ax.text(r["seconds"] / 3600, i - 0.17, f"{r['seconds'] / 3600:.3g} h", ha="center", fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(0.04, 1300)
    ax.set_ylim(4.6, -0.6)
    ax.set_yticks(range(5), labels)
    ax.set_xlabel("阶段耗时 / h（对数轴）")
    ax.set_title("b  计算时间集中于内点迭代", loc="left", fontweight="bold")
    ax.grid(axis="x", color="#e5e9ed", lw=0.5)
    fig.subplots_adjust(left=0.105, right=0.975, top=0.88, bottom=0.22, wspace=0.52)
    fig.text(0.105, 0.045, "* Bounds 为日志舍入值。求解收尾约4.9 s未绘入；构建位于solver计时之外。", fontsize=7, color="#56616b")
    fig.savefig(figures / "01_scale_and_time.png", dpi=300)
    fig.savefig(figures / "01_scale_and_time.svg")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.45))
    days = np.array([r["runtime_seconds"] for r in stdout]) / 86400
    callback_days = np.array([r["runtime_seconds"] for r in callback]) / 86400
    iteration = np.array([r["iteration"] for r in stdout])
    for ax, tail, title in [(axes[0, 0], False, "a  全轨迹：stdout残差"), (axes[1, 0], True, "c  末段40步：并非单调下降")]:
        selection = slice(-41, None) if tail else slice(None)
        x = iteration[selection] if tail else days[selection]
        for key, label, color in zip(FIELDS[2:], ["Primal", "Dual", "Compl."], colors):
            values = np.array([r[key] for r in stdout])[selection]
            if np.any(values <= 0):
                raise ValueError("Log residual plot requires positive values; do not silently clip")
            ax.plot(x, values, color=color, label=label)
        ax.set_yscale("log")
        ax.set_xlabel("Barrier迭代编号" if tail else "累计solver时间 / 天（含预求解、排序）")
        ax.set_ylabel("stdout残差 / 互补性（不同指标）")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.legend(ncol=3, loc="center left" if tail else "upper right", frameon=False, columnspacing=0.6, handlelength=1.4)
        ax.grid(color="#e5e9ed", lw=0.5)
        ax.yaxis.set_minor_locator(NullLocator())
    ax = axes[0, 1]
    ax.plot(callback_days, [r["relative_objective_difference"] for r in callback], color=colors[0])
    ax.set_yscale("log")
    ax.set_xlabel("累计solver时间 / 天")
    ax.set_ylabel("相对目标差（callback计算）")
    ax.set_title("b  原对偶目标逐步接近", loc="left", fontweight="bold")
    ax.annotate(f"终值 {callback[-1]['relative_objective_difference']:.2e}", xy=(callback_days[-1], callback[-1]["relative_objective_difference"]),
                xytext=(0.40, 0.18), textcoords="axes fraction", fontsize=8, arrowprops={"arrowstyle": "-", "color": "#56616b"})
    ax.grid(color="#e5e9ed", lw=0.5)
    ax = axes[1, 1]
    ax.plot(iteration[1:], [r["iteration_elapsed_seconds"] / 60 for r in callback[1:]], color=colors[1], lw=0.8)
    median = s["iteration_interval_minutes"]["median"]
    ax.axhline(median, color="#697782", lw=0.8, ls="--", label=f"中位数 {median:.1f} min")
    ax.set_xlabel("Barrier迭代编号")
    ax.set_ylabel("相邻callback间隔 / min")
    ax.set_title("d  每步时间：日志差分实测", loc="left", fontweight="bold")
    ax.legend(loc="lower right", frameon=False)
    ax.set_ylim(bottom=0)
    ax.grid(color="#e5e9ed", lw=0.5)
    fig.subplots_adjust(left=0.105, right=0.975, top=0.92, bottom=0.14, hspace=0.49, wspace=0.39)
    fig.text(0.105, 0.035, "单次运行；全608个记录点，无平滑。相对目标差 = |P−D| / max(1, |P|, |D|)，不是求解器终止判据。", fontsize=7, color="#56616b")
    fig.savefig(figures / "02_barrier_convergence.png", dpi=300)
    fig.savefig(figures / "02_barrier_convergence.svg")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--recovery-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary, stdout, callback = extract(args.source_dir, args.recovery_dir, args.output_dir)
    plot(args.output_dir, summary, stdout, callback)
    print(json.dumps({k: summary[k] for k in ("log_points", "solver_days", "barrier_solver_share_percent", "iteration_interval_minutes", "last_100_intervals_days", "dimensions", "ranges", "phases", "milestones", "final_stdout", "final_callback")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
