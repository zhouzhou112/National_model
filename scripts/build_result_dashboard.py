#!/usr/bin/env python
"""Build the fixed CISPO result dashboard from an existing result directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.result_dashboard import build_result_dashboard  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "External analysis directory. Omit only before result-manifest "
            "finalization; use an external directory for accepted historical runs."
        ),
    )
    parser.add_argument(
        "--formats",
        default="svg",
        help="Comma-separated output formats: svg, png, pdf (default: svg).",
    )
    parser.add_argument(
        "--reference-load-gwh",
        type=float,
        help="Optional immutable full-year baseline-load denominator for old outputs.",
    )
    args = parser.parse_args()
    formats = [item.strip() for item in args.formats.split(",") if item.strip()]
    payload = build_result_dashboard(
        args.result_dir,
        output_dir=args.output_dir,
        formats=formats,
        reference_load_gwh=args.reference_load_gwh,
    )
    print(
        json.dumps(
            {
                "result_dir": str(args.result_dir.resolve()),
                "output_dir": str(
                    (args.output_dir or args.result_dir).resolve()
                ),
                "formats": formats,
                "result_use": payload["identity"]["result_use"],
                "solver_status": payload["acceptance"]["solver_status"],
                "solution_qc_status": payload["acceptance"][
                    "solution_qc_status"
                ],
                "hard_checks": (
                    f"{payload['acceptance']['hard_checks_passed']}/"
                    f"{payload['acceptance']['hard_checks_total']}"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
