"""Opt-in exact temporal splitting of annual linear accounts.

The block variables have zero objective coefficients. Eliminating them restores
the original row exactly. Signed accounts use free bounds; no hourly constraint
or annual budget is changed. Disabled calls evaluate the original sum directly.
"""
from __future__ import annotations

import gurobipy as gp


def annual_split_enabled(config):
    return bool(config.raw.get("formulation", {}).get("annual_dense_row_split", {}).get("enabled", False))


def annual_sum(model, config, hours, family, sum_block, *, unit="gwh", nonnegative=False):
    if not annual_split_enabled(config):
        return sum_block(slice(None))
    width = int(config.raw["formulation"]["annual_dense_row_split"].get("block_hours", 730))
    def scalar_expression(value):
        if hasattr(value, "item"):
            value = value.item()
        return gp.LinExpr(value)
    # Keep constants in the original annual row, summed in legacy order.
    # Summing block constants would otherwise introduce RHS rounding drift.
    annual_constant = scalar_expression(sum_block(slice(None))).getConstant()
    slices = [slice(start, min(start + width, hours)) for start in range(0, hours, width)]
    values = model.addMVar(len(slices), lb=0.0 if nonnegative else -gp.GRB.INFINITY,
                          name=f"annual_block_{family}_{unit}")
    for block, selected in enumerate(slices):
        expression = scalar_expression(sum_block(selected))
        expression.addConstant(-expression.getConstant())
        model.addConstr(values[block] == expression,
                        name=f"annual_block_{family}_definition_b{block}")
    audit = getattr(model, "_annual_dense_split_audit", None)
    if audit is None:
        audit = {"enabled": True, "block_hours": width, "hours": hours, "families": []}
        model._annual_dense_split_audit = audit
    audit["families"].append({"family": family, "unit": unit, "blocks": len(slices),
                              "lower_bound": "zero" if nonnegative else "free"})
    return values.sum() + annual_constant
