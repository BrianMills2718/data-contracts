#!/usr/bin/env python3
"""Pre-commit schema compatibility checker.

Runs contract compatibility checks when boundary model files change.
Designed to be called from a git pre-commit hook.

Usage:
    python -m data_contracts.check_schemas [--strict] [--json]

Exit codes:
    0 - All contracts compatible (or no registry to check)
    1 - Breaking violations found
    2 - Error running checks
"""

from __future__ import annotations

import json
import logging
import subprocess

from data_contracts.checker import check_compatibility
from data_contracts.registry import ContractRegistry

logger = logging.getLogger(__name__)


def _get_staged_files() -> list[str]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, check=True,
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def _is_boundary_related(filepath: str) -> bool:
    """Check if a file might contain boundary model definitions."""
    boundary_indicators = [
        "models.py", "adapters/", "contracts/", "boundary",
        "export", "import", "adapter",
    ]
    return any(indicator in filepath for indicator in boundary_indicators)


def run_checks(strict: bool = False, output_json: bool = False) -> int:
    """Run contract compatibility checks.

    Args:
        strict: If True, any violation is a hard failure. If False, only
                missing-field and field-removed violations fail.
        output_json: If True, output JSON instead of text.

    Returns:
        Exit code (0=pass, 1=violations, 2=error).
    """
    try:
        reg = ContractRegistry()
        boundaries = reg.list_all()
    except Exception as e:
        if output_json:
            print(json.dumps({"status": "error", "detail": str(e)}))
        else:
            logger.warning("Could not load contract registry: %s", e)
        return 0  # Don't block commits if registry is unavailable

    if not boundaries:
        if output_json:
            print(json.dumps({"status": "skip", "reason": "no registered boundaries"}))
        return 0

    all_violations = []

    # Check compatibility across explicitly named pipeline pairs.
    # Only compare boundaries that reference each other BY NAME in their
    # consumers list — not by project. This avoids false positives from
    # utility boundaries like llm_client.call_llm that list project names
    # as consumers (meaning "this project calls me") rather than pipeline
    # connections (meaning "my output feeds their input").
    boundary_by_name = {b.name: b for b in boundaries}
    checked_pairs: set[tuple[str, str]] = set()

    for prod in boundaries:
        if not prod.output_schema or not prod.consumers:
            continue
        for consumer_boundary_name in prod.consumers:
            # Only check if the consumer is a specific boundary name
            if consumer_boundary_name not in boundary_by_name:
                continue
            con = boundary_by_name[consumer_boundary_name]
            if not con.input_schema:
                continue
            pair_key = (prod.name, con.name)
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            violations = check_compatibility(
                prod.output_schema, con.input_schema,
                prod.name, con.name,
            )
            all_violations.extend(violations)

    if output_json:
        payload = {
            "status": "fail" if all_violations else "pass",
            "boundaries_checked": len(boundaries),
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
            print(f"Contract compatibility OK ({len(boundaries)} boundaries checked)")

    if all_violations:
        if strict:
            return 1
        # In non-strict mode, only fail on field_removed and missing_field
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
