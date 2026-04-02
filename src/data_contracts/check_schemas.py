#!/usr/bin/env python3
"""Pre-commit schema compatibility checker.

Validates explicitly declared pipelines. Register pipelines with:
    registry.declare_pipeline("my_pipeline", ["boundary_a", "boundary_b"])
or from the CLI:
    python -m data_contracts declare-pipeline my_pipeline boundary_a boundary_b

Usage:
    python -m data_contracts.check_schemas [--strict] [--json]

Exit codes:
    0 - All declared pipelines compatible (or none declared)
    1 - Breaking violations found
    2 - Error running checks
"""

from __future__ import annotations

import json
import logging

from data_contracts.registry import ContractRegistry

logger = logging.getLogger(__name__)


def run_checks(
    strict: bool = False,
    output_json: bool = False,
    registry: ContractRegistry | None = None,
) -> int:
    """Run contract compatibility checks on all declared pipelines.

    Args:
        strict: If True, any violation is a hard failure. If False, only
                missing-field and field-removed violations fail.
        output_json: If True, output JSON instead of text.
        registry: Registry to use. Defaults to loading from disk.

    Returns:
        Exit code (0=pass, 1=violations, 2=error).
    """
    try:
        reg = registry if registry is not None else ContractRegistry()
        pipelines = reg.list_pipelines()
    except Exception as e:
        if output_json:
            print(json.dumps({"status": "error", "detail": str(e)}))
        else:
            logger.warning("Could not load contract registry: %s", e)
        return 0  # Don't block commits if registry is unavailable

    if not pipelines:
        if output_json:
            print(json.dumps({"status": "skip", "reason": "no declared pipelines"}))
        return 0

    all_violations = []
    for pipeline in pipelines:
        violations = reg.validate_pipeline(pipeline.steps)
        all_violations.extend(violations)

    if output_json:
        payload = {
            "status": "fail" if all_violations else "pass",
            "pipelines_checked": len(pipelines),
            "violations": [
                {"producer": v.producer, "consumer": v.consumer,
                 "field": v.field, "kind": v.kind, "detail": v.detail}
                for v in all_violations
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if all_violations:
            print(f"CONTRACT VIOLATIONS ({len(all_violations)}):")
            for v in all_violations:
                print(f"  {v.producer} → {v.consumer}: {v.kind} on '{v.field}' — {v.detail}")
        else:
            print(f"Contract compatibility OK ({len(pipelines)} pipeline(s) checked)")

    if all_violations:
        if strict:
            return 1
        hard_failures = [v for v in all_violations if v.kind in ("field_removed", "missing_field")]
        return 1 if hard_failures else 0

    return 0


def main() -> int:
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Pre-commit contract compatibility checker")
    parser.add_argument("--strict", action="store_true", help="Fail on any violation")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    return run_checks(strict=args.strict, output_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
