"""Schema compatibility checker for producer-consumer boundary pairs.

Detects: missing required fields, type mismatches, breaking changes between versions.
"""

from __future__ import annotations

from typing import Any

from data_contracts.models import ContractViolation


def _get_json_type(prop: dict[str, Any]) -> str | None:
    """Extract the JSON schema type string from a property definition."""
    if "type" in prop:
        return prop["type"]
    if "anyOf" in prop:
        types = [t.get("type") for t in prop["anyOf"] if "type" in t]
        return "|".join(sorted(types)) if types else None
    return None


def check_compatibility(
    producer_schema: dict[str, Any],
    consumer_schema: dict[str, Any],
    producer_name: str = "producer",
    consumer_name: str = "consumer",
) -> list[ContractViolation]:
    """Check if a producer's output schema satisfies a consumer's input schema.

    Returns a list of violations. Empty list means compatible.
    """
    violations: list[ContractViolation] = []
    producer_props = producer_schema.get("properties", {})
    consumer_props = consumer_schema.get("properties", {})
    consumer_required = set(consumer_schema.get("required", []))

    # Missing required fields
    for field_name in consumer_required - set(producer_props.keys()):
        violations.append(ContractViolation(
            producer=producer_name, consumer=consumer_name, field=field_name,
            kind="missing_field",
            detail=f"Consumer requires '{field_name}' but producer does not provide it",
        ))

    # Type mismatches on shared fields
    for field_name in set(producer_props) & set(consumer_props):
        pt, ct = _get_json_type(producer_props[field_name]), _get_json_type(consumer_props[field_name])
        if pt and ct and pt != ct:
            if not set(pt.split("|")).issubset(set(ct.split("|"))):
                violations.append(ContractViolation(
                    producer=producer_name, consumer=consumer_name, field=field_name,
                    kind="type_mismatch",
                    detail=f"Producer type '{pt}' vs consumer type '{ct}'",
                ))

    return violations


def check_breaking_changes(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
    boundary_name: str = "boundary",
) -> list[ContractViolation]:
    """Check if a new schema version has breaking changes vs the old one."""
    violations: list[ContractViolation] = []
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})

    # Removed fields
    for field_name in set(old_props) - set(new_props):
        violations.append(ContractViolation(
            producer=boundary_name, consumer="(any)", field=field_name,
            kind="field_removed",
            detail=f"Field '{field_name}' was removed in new version",
        ))

    # New required fields not in old schema
    old_req = set(old_schema.get("required", []))
    new_req = set(new_schema.get("required", []))
    for field_name in (new_req - old_req) - set(old_props):
        violations.append(ContractViolation(
            producer=boundary_name, consumer="(any)", field=field_name,
            kind="missing_field",
            detail=f"New required field '{field_name}' added without being in old schema",
        ))

    # Type changes on existing fields
    for field_name in set(old_props) & set(new_props):
        ot, nt = _get_json_type(old_props[field_name]), _get_json_type(new_props[field_name])
        if ot and nt and ot != nt:
            violations.append(ContractViolation(
                producer=boundary_name, consumer="(any)", field=field_name,
                kind="type_mismatch",
                detail=f"Type changed from '{ot}' to '{nt}'",
            ))

    return violations
