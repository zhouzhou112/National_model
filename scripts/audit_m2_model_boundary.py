"""Audit the historical M2 scientific-boundary register without building an LP.

The audit evaluates configuration and evidence-registration contracts only.  It
does not construct a Gurobi model, mutate inputs, or authorize a solve.  The
2026-07-28 v1 register is retained as evidence; the current release authority is
``config/release_contract_v0729.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config


ALLOWED_STATUS = {
    "CLOSED_M1",
    "CLOSED_M2",
    "LOCAL_GATE_PASS_PENDING_COMMIT",
    "IN_REVIEW",
    "OPEN_EVIDENCE",
    "FORMULATION_DESIGN",
    "DEFERRED_DATA",
    "SCOPE_LIMIT",
    "BASE_LOCKED",
    "BLOCKED_ANCHOR",
}
REQUIRED_FINDING_FIELDS = {
    "id",
    "priority",
    "area",
    "status",
    "scientific_case_impact",
    "lp_topology_impact",
    "basis_rule",
    "decision",
    "next_gate",
}


def _check(checks: list[dict[str, Any]], name: str, status: str, detail: str) -> None:
    checks.append({"check": name, "status": status, "detail": detail})


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(payload: dict[str, Any], dotted_path: str) -> Any:
    value: Any = payload
    for token in dotted_path.split("."):
        if not isinstance(value, dict) or token not in value:
            raise KeyError(dotted_path)
        value = value[token]
    return value


def _canonical(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return str(value)
    return str(value)


def _scenario_registry_mismatches(
    registry_path: Path, scenario_id: str, scenario_path: str, resolved_config: dict[str, Any]
) -> list[str]:
    registry = pd.read_csv(registry_path, keep_default_na=False)
    required = {
        "scenario_id",
        "parameter_path",
        "runtime_authority",
        "expected_value",
        "unit",
        "evidence_status",
        "sensitivity_range",
        "notes",
    }
    missing = required.difference(registry.columns)
    if missing:
        return ["missing_columns=" + ",".join(sorted(missing))]
    selected = registry.loc[registry.scenario_id.eq(scenario_id)].copy()
    if selected.empty:
        return ["no_rows_for_active_scenario"]
    if selected.parameter_path.duplicated().any():
        return ["duplicate_parameter_path"]
    mismatches: list[str] = []
    for row in selected.itertuples(index=False):
        if str(row.runtime_authority) != scenario_path:
            mismatches.append(f"authority:{row.parameter_path}")
            continue
        try:
            actual = _canonical(_resolve_path(resolved_config, str(row.parameter_path)))
        except KeyError:
            mismatches.append(f"missing_path:{row.parameter_path}")
            continue
        if actual != str(row.expected_value):
            mismatches.append(
                f"value:{row.parameter_path}: expected={row.expected_value}, actual={actual}"
            )
    return mismatches


def build_audit(decision_register: Path, output_dir: Path) -> dict[str, Any]:
    register = _load_json(decision_register)
    if register.get("contract_version") != "m2_model_boundary_audit_v1":
        raise ValueError("Unexpected M2 decision-register contract version")
    findings = register.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError("M2 decision register must contain nonempty findings")

    checks: list[dict[str, Any]] = []
    identifiers: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Every M2 finding must be an object")
        missing = REQUIRED_FINDING_FIELDS.difference(finding)
        if missing:
            raise ValueError(
                f"M2 finding {finding.get('id', '<missing>')} lacks: {sorted(missing)}"
            )
        if finding["status"] not in ALLOWED_STATUS:
            raise ValueError(f"Unsupported M2 status: {finding['status']}")
        if not isinstance(finding["scientific_case_impact"], bool) or not isinstance(
            finding["lp_topology_impact"], bool
        ):
            raise ValueError("M2 scientific_case_impact and lp_topology_impact must be boolean")
        identifiers.append(str(finding["id"]))
    _check(
        checks,
        "finding_ids_unique",
        "PASS" if len(identifiers) == len(set(identifiers)) else "HARD_FAIL",
        f"findings={len(identifiers)}, unique={len(set(identifiers))}",
    )

    source_review_reference = str(register.get("source_review", "")).strip()
    _check(
        checks,
        "independent_review_reference_declared",
        "PASS"
        if source_review_reference.startswith("supplementary_materials/")
        else "HARD_FAIL",
        (
            f"{source_review_reference}; external protected evidence reference, "
            "not a current release artifact"
        ),
    )

    base = load_model_config()
    scenario_path = "config/scenarios/flexible_load_comfort_v3_v2g_5pct.json"
    flexibility = load_model_config(scenario_path=scenario_path)
    _check(
        checks,
        "base_case_identity",
        "PASS"
        if base.raw["scientific_case"]["case_id"] == register["base_case_id"]
        else "HARD_FAIL",
        str(base.raw["scientific_case"]["case_id"]),
    )
    _check(
        checks,
        "base_wave_on_flexible_load_off",
        "PASS"
        if bool(base.raw["features"]["wave_energy"])
        and not bool(base.raw["features"]["flexible_load"])
        else "HARD_FAIL",
        f"wave={base.raw['features']['wave_energy']}, flexible={base.raw['features']['flexible_load']}",
    )
    _check(
        checks,
        "existing_vre_cohort_survival",
        "PASS"
        if base.raw["planning_sequence"]["existing_vre_retirement"]["mode"]
        == "cohort_survival_v1"
        else "HARD_FAIL",
        str(base.raw["planning_sequence"]["existing_vre_retirement"]["mode"]),
    )
    _check(
        checks,
        "duplicate_comid_rule_explicit",
        "PASS"
        if base.raw["hydro"].get("duplicate_comid_flow_allocation")
        == "static_capacity_potential_share_v1"
        else "HARD_FAIL",
        str(base.raw["hydro"].get("duplicate_comid_flow_allocation")),
    )

    beccs = _load_json(PROJECT_ROOT / "config/beccs_lifecycle_sensitivity_v1.json")
    screening = beccs.get("screening_cases", [])
    _check(
        checks,
        "beccs_lifecycle_remains_screening",
        "PASS"
        if screening
        and all(
            item.get("evidence_status") == "SCREENING_ASSUMPTION_REQUIRE_SOURCING"
            for item in screening
        )
        else "HARD_FAIL",
        f"screening_cases={len(screening)}",
    )

    scenario_registry = PROJECT_ROOT / "config/scenario_parameter_registry.csv"
    scenario_mismatches = _scenario_registry_mismatches(
        scenario_registry,
        "flexible_load_comfort_v3_v2g_5pct",
        scenario_path,
        flexibility.raw,
    )
    _check(
        checks,
        "flexibility_scenario_registry_alignment",
        "PASS" if not scenario_mismatches else "HARD_FAIL",
        "resolved scenario registry matches every declared parameter"
        if not scenario_mismatches
        else "; ".join(scenario_mismatches),
    )
    _check(
        checks,
        "flexibility_scenario_identity",
        "PASS"
        if flexibility.raw["scenario"]["id"] == "flexible_load_comfort_v3_v2g_5pct"
        and bool(flexibility.raw["features"]["flexible_load"])
        else "HARD_FAIL",
        f"scenario={flexibility.raw['scenario']['id']}, flexible={flexibility.raw['features']['flexible_load']}",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    finding_frame = pd.DataFrame(findings).sort_values(["priority", "id"])
    check_frame = pd.DataFrame(checks)
    finding_frame.to_csv(
        output_dir / "m2_decision_register.csv", index=False, encoding="utf-8-sig"
    )
    check_frame.to_csv(
        output_dir / "m2_contract_checks.csv", index=False, encoding="utf-8-sig"
    )
    status_counts = Counter(finding_frame.status.astype(str))
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "contract_version": register["contract_version"],
        "snapshot_status": register.get("snapshot_status"),
        "superseded_by": register.get("superseded_by"),
        "base_case_id": register["base_case_id"],
        "finding_count": int(len(finding_frame)),
        "finding_status_counts": dict(sorted(status_counts.items())),
        "contract_checks": {
            "pass": int(check_frame.status.eq("PASS").sum()),
            "open": int(check_frame.status.eq("OPEN").sum()),
            "hard_fail": int(check_frame.status.eq("HARD_FAIL").sum()),
        },
        "files": ["m2_decision_register.csv", "m2_contract_checks.csv"],
    }
    (output_dir / "m2_audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report_rows = "\n".join(
        f"| `{row.id}` | {row.priority} | {row.status} | {row.area} | {row.next_gate} |"
        for row in finding_frame.itertuples(index=False)
    )
    check_rows = "\n".join(
        f"| `{row.check}` | {row.status} | {row.detail} |"
        for row in check_frame.itertuples(index=False)
    )
    report = f"""# M2 模型边界审计（历史快照）

生成时间：{summary['generated_at']}

> 本报告对应 2026-07-28 的 `m2_model_boundary_audit_v1`，已由
> `{summary['superseded_by']}` 取代为当前发布口径。下列状态只用于还原
> M2 Stage A 当时的决策，不得当作 2026-07-29 当前模型状态。

## 审计边界

本审计只决定哪些问题可以进入未来具名模型 case。它不修改 Base LP、运行时数据或求解器，也不把截断时域结果解释为年度科学结论。

## 决策登记

| ID | 优先级 | 快照状态 | 范围 | 当时的下一门禁 |
|---|---|---|---|---|
{report_rows}

## 自动契约检查

| 检查 | 状态 | 证据 |
|---|---|---|
{check_rows}

## 快照解释

- `M2-HYDRO-001`、`M2-FLEX-001` 与 `M2-EV-001` 的文字记录的是
  2026-07-28 当时状态；它们后续是否实现，应以当前 release contract、Git 和
  新输出证据判断。
- `M2-PARAM-001` 只覆盖历史 V3 overlay registry，不是当前全部可运行情景目录。
- BECCS lifecycle 与 adequacy 的未决科学边界仍需单独的数据或方法学证据。
- Base 是否保持 wave on、flexible load off，应由当前配置与 release audit 核验。
"""
    (output_dir / "M2_AUDIT_REPORT_ZH.md").write_text(report, encoding="utf-8-sig")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decision-register",
        default="config/m2_model_boundary_audit_v1.json",
    )
    parser.add_argument("--output-dir", default="outputs/m2_model_boundary_audit")
    args = parser.parse_args()
    decision_register = Path(args.decision_register)
    if not decision_register.is_absolute():
        decision_register = PROJECT_ROOT / decision_register
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    summary = build_audit(decision_register, output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["contract_checks"]["hard_fail"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
