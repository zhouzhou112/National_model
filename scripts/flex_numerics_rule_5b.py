"""Section 5b (2026-10-13, registered before F5 terminal) diagnostic evidence.

No settings are applied. Missing/limited/resource-stopped runs remain pending;
an observed SUBOPTIMAL endpoint is recorded separately from missing evidence.
"""
import math
import re


def solver_structure(log):
    result = {}
    presolved = re.findall(r"Presolved:\s*([\d,]+) rows,\s*([\d,]+) columns,\s*([\d,]+) nonzeros", log)
    if presolved:
        result.update(zip(("presolved_rows", "presolved_columns", "presolved_nonzeros"),
                          (int(v.replace(",", "")) for v in presolved[-1])))
    factors = re.findall(r"Factor NZ\s*:\s*([\d.eE+\-]+)", log)
    if factors:
        result["factor_nz"] = float(factors[-1])
    return result


def evaluate(rows):
    r = {x["run"]: x for x in rows}

    def number(name, field):
        try:
            value = float(r[name][field])
            return value if math.isfinite(value) else None
        except (KeyError, TypeError, ValueError):
            return None

    def quality(name):
        status, residual = number(name, "status"), number(name, "M_gw_gwh")
        if status not in (2, 13) or residual is None or r[name].get("state") != "COMPLETE":
            return None
        return status == 2 and residual <= 1e-3

    def conjunction(values):
        return False if False in values else None if None in values else True

    def ratio(name, field):
        a, b = number(name, field), number("F1", field)
        return a/b if a is not None and b is not None and b > 0 else None

    growth = ratio("F5", "M_gw_gwh")
    extrapolation = None
    if quality("F1") is not None and quality("F5") is not None and growth is not None:
        extrapolation = quality("F1") and quality("F5") and growth < 3
    candidates = []
    for setting, small, large, full in (("production", "P1", "P5", "F1"),
                                      ("AggFill_0", "P8", "P5b", "F8"),
                                      ("Aggregate_0", "P3", "P5a", "F7")):
        a = conjunction([quality(small), quality(large)])
        ratios = {field: ratio(full, field) for field in ("barrier_iterations", "runtime_s", "factor_nz")}
        b = conjunction([quality(full)] + [None if ratios[k] is None else ratios[k] <= 1.3
                                           for k in ("barrier_iterations", "runtime_s")])
        c = None if ratios["factor_nz"] is None else ratios["factor_nz"] <= 1.05
        candidates.append(dict(setting=setting, isolated_runs=[small, large], full_run=full,
                               criterion_a=a, criterion_b=b, criterion_c=c,
                               ratios_to_F1=ratios, eligible=conjunction([a, b, c])))
    # Do not promote a more aggressive setting while an earlier candidate is pending.
    selected = None
    for item in candidates:
        if item["eligible"] is None:
            break
        if item["eligible"]:
            selected = item["setting"]
            break
    required = ("P6", "P7", "P5a", "P5b", "P5c", "P8", "F1", "F2", "F5", "F7", "F8")
    pending = [n for n in required if quality(n) is None]
    state = "PENDING_5B_EXPERIMENTS"
    if not pending:
        if selected:
            state = "CANDIDATE_FOR_AUTHOR_CONFIRMATION"
        elif all(c["eligible"] is False for c in candidates):
            state = "PRODUCTION_2030_ONLY_LATER_YEARS_UNDECIDED" if extrapolation else "NO_START_RECOMMENDATION_AWAIT_AUTHOR"
    return dict(rule_version="2026-10-13_section_5b_pre_F5_terminal", state=state,
                f4_to_f1_excluded=True, f1_to_f5_ratio=growth,
                extrapolation_pass=extrapolation, candidates=candidates,
                provisional_candidate=selected, recommendation=selected if not pending else None,
                missing_limited_or_incomplete_runs=pending,
                caveat="Diagnostic recommendation only; author confirmation required; no production changes")
