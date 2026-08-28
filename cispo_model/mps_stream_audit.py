"""Bounded-memory coefficient census for existing free-format continuous MPS.

Never imports Gurobi, builds, presolves or optimizes. Keeps family summaries and
the current column, not an LP matrix or per-row name table. Row-family extrema
are NOT per-row extrema. Log10 histogram bins are NOT exact quantiles.
Rejects unsupported MIP/QP/ranged constraints rather than silently misreading.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math
import re


@lru_cache(maxsize=32768)
def family(name):
    base = name.split("[", 1)[0]
    base = re.sub(r"_(?:p|h|row|b|k)\d+(?=_|$)", "_#", base)
    return re.sub(r"_\d+$", "_#", base)


class Stats:
    def __init__(self):
        self.count = 0
        self.low = self.high = None
        self.bins = Counter()

    def add(self, value, location):
        if not math.isfinite(value):
            raise ValueError("Nonfinite explicit MPS value")
        if value == 0:
            return
        absolute = abs(value)
        entry = {"value": value, "absolute": absolute, "location": location}
        self.count += 1
        if self.low is None or absolute < self.low["absolute"]:
            self.low = entry
        if self.high is None or absolute > self.high["absolute"]:
            self.high = entry
        self.bins[math.floor(math.log10(absolute))] += 1

    def result(self):
        return {"nonzero_entries": self.count, "minimum": self.low, "maximum": self.high,
                "ratio": self.high["absolute"] / self.low["absolute"] if self.count else None,
                "log10_histogram_floor_exponent": dict(sorted(self.bins.items()))}


def audit_lines(lines, progress=None):
    categories = {key: Stats() for key in ("matrix", "objective", "rhs", "objective_offset_mps_sign",
                                           "explicit_finite_bounds", "column_coefficient_ratio")}
    families = {key: {} for key in ("matrix_by_row_family", "matrix_by_column_family", "objective", "rhs", "bounds")}
    section = None
    objective_row = None
    row_count = column_count = line_count = 0
    ended = False
    current_column = None
    column_low, column_high = math.inf, 0.

    def add_family(group, name, value, location):
        key = family(name)
        if key not in families[group]:
            if len(families[group]) >= 10000:
                raise ValueError("Family count exceeds bounded-memory safety limit")
            families[group][key] = Stats()
        families[group][key].add(value, location)

    def flush_column():
        if column_high:
            categories["column_coefficient_ratio"].add(column_high / column_low, current_column)

    seen_sections = []
    vector_names = {}
    for line_count, line in enumerate(lines, 1):
        if isinstance(line, bytes):
            line = line.decode("ascii")
        if not line.strip() or line.startswith("*"):
            continue
        fields = line.split()
        if ended:
            raise ValueError("Unexpected data after ENDATA")
        if not line[0].isspace():
            next_section = fields[0]
            if next_section not in ("NAME", "ROWS", "COLUMNS", "RHS", "BOUNDS", "ENDATA"):
                raise ValueError(f"Unsupported MPS section: {next_section}")
            if next_section in seen_sections:
                raise ValueError(f"Repeated section: {next_section}")
            if section == "COLUMNS":
                flush_column()
            section = next_section
            seen_sections.append(section)
            if section == "ENDATA":
                ended = True
            continue
        if section == "ROWS":
            if len(fields) != 2 or fields[0] not in ("N", "L", "G", "E"):
                raise ValueError("Unsupported ROWS record")
            if fields[0] == "N":
                if objective_row is not None:
                    raise ValueError("Multiple free/objective rows unsupported")
                objective_row = fields[1]
            else:
                row_count += 1
        elif section in ("COLUMNS", "RHS"):
            if len(fields) not in (3, 5) or "'MARKER'" in fields:
                raise ValueError("Unsupported coefficient record or integer marker")
            if section == "RHS":
                previous = vector_names.setdefault("RHS", fields[0])
                if previous != fields[0]:
                    raise ValueError("Multiple RHS vectors unsupported")
            if section == "COLUMNS" and fields[0] != current_column:
                flush_column()
                current_column = fields[0]
                column_low, column_high = math.inf, 0.
                column_count += 1
            for index in range(1, len(fields), 2):
                name, value = fields[index], float(fields[index + 1])
                location = f"{fields[0]} -> {name}"
                if section == "RHS":
                    kind = "objective_offset_mps_sign" if name == objective_row else "rhs"
                    categories[kind].add(value, location)
                    if kind == "rhs":
                        add_family("rhs", name, value, location)
                elif name == objective_row:
                    categories["objective"].add(value, location)
                    add_family("objective", fields[0], value, location)
                else:
                    categories["matrix"].add(value, location)
                    add_family("matrix_by_row_family", name, value, location)
                    add_family("matrix_by_column_family", fields[0], value, location)
                    if value:
                        column_low, column_high = min(column_low, abs(value)), max(column_high, abs(value))
        elif section == "BOUNDS":
            previous = vector_names.setdefault("BOUNDS", fields[1])
            if previous != fields[1]:
                raise ValueError("Multiple bound vectors unsupported")
            if fields[0] in ("FR", "MI", "PL") and len(fields) == 3:
                continue
            if fields[0] not in ("LO", "UP", "FX") or len(fields) != 4:
                raise ValueError("Unsupported or integer variable bound")
            value = float(fields[3])
            categories["explicit_finite_bounds"].add(value, " ".join(fields[:3]))
            add_family("bounds", fields[2], value, " ".join(fields[:3]))
        else:
            raise ValueError(f"Unexpected entry in section {section}")
        if progress and line_count % 1_000_000 == 0:
            progress({"lines": line_count, "rows": row_count, "columns": column_count,
                      "matrix_nonzeros": categories["matrix"].count})
    if not ended or objective_row is None or not all(k in seen_sections for k in ("ROWS", "COLUMNS")):
        raise ValueError("Incomplete MPS: missing ENDATA/objective/required sections")
    return {"scope": "STREAMING_SAVED_MPS_NO_BUILD_NO_PRESOLVE_NO_OPTIMIZE",
            "constraints": row_count, "columns_contiguous_mps": column_count, "lines": line_count,
            "notes": ["Bounds are explicit records only; implicit defaults are not counted.",
                      "Per-row-family ranges are not individual-row ranges or a condition number.",
                      "Column statistics assume Gurobi's contiguous-column MPS ordering."],
            "ranges": {k: v.result() for k, v in categories.items()},
            "families": {k: {f: v.result() for f, v in sorted(group.items())} for k, group in families.items()}}
