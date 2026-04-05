# Schema Evolution Convention

**Owner:** data_contracts
**Established:** 2026-04-04
**Applies to:** All `@boundary`-registered schemas in the ecosystem

---

## The Problem

The capability registration policy (`project-meta/docs/ops/ADR-2026-04-04-capability-registration-policy.md`)
requires every meaningful capability to be registered as `@boundary`. This creates
a stability commitment: changing a registered schema can break consumers.

This document defines the convention for evolving schemas safely.

---

## Convention Rules

### Rule 1: New fields are always optional

When adding a new field to a registered schema, it must be optional (have a default
value). Never add a new required field to an existing schema version.

```python
# CORRECT: new field is optional
class MyOutput(BoundaryModel):
    existing_field: str
    new_field: str | None = None  # or = "default_value"

# WRONG: new required field breaks all existing consumers
class MyOutput(BoundaryModel):
    existing_field: str
    new_field: str  # required — this is a breaking change
```

The permissive consumer model (`model.permissive()`, `extra="ignore"`) handles
consumers that haven't been updated yet: they simply ignore unknown fields.

### Rule 2: Never remove or rename fields in place

Removing a field is a breaking change — consumers that read it will fail.
Renaming is equivalent to removing + adding.

If you must remove a field:
1. Mark it deprecated in the `Field(description=...)` for one version
2. Keep it with `None` default while consumers migrate
3. Remove it in a new explicit schema version (Rule 3)

```python
# Deprecation period: keep the field, mark it
old_field: str | None = Field(
    default=None,
    description="DEPRECATED — use new_field instead. Will be removed in v2."
)
new_field: str = Field(description="The replacement for old_field")
```

### Rule 3: Significant structural changes require a versioned schema

When additive changes aren't enough (different field structure, incompatible
type changes, semantic reinterpretation), create a new versioned schema:

```python
# Original
class SummaryOutputV1(BoundaryModel):
    text: str

# Breaking redesign: new version
class SummaryOutputV2(BoundaryModel):
    sections: list[str]
    title: str
```

Register both versions. Write an explicit migration adapter:

```python
def v1_to_v2(v1: SummaryOutputV1) -> SummaryOutputV2:
    return SummaryOutputV2(sections=[v1.text], title="")
```

Consumers migrate to V2 at their own pace. Remove V1 only when all consumers
have migrated (check `contract_registry.json` for consumers).

### Rule 4: Use the adapter pattern for implementation freedom

The schema is what's stable. The implementation behind it can change freely as
long as the adapter keeps the schema valid.

```python
# Internal type (can change freely)
@dataclass
class InternalResult:
    raw_text: str
    processing_time_ms: float
    metadata: dict

# Registered schema (stable)
class SummaryOutput(BoundaryModel):
    text: str = Field(description="Summarized text")

# Adapter: translates freely between internal and registered
@boundary(output_model=SummaryOutput)
def summarize(input: SummaryInput) -> SummaryOutput:
    internal = _internal_summarize(input.text)
    return SummaryOutput(text=internal.raw_text)  # adapter
```

---

## What the Tooling Enforces

The `data_contracts` pre-commit hook (`check_schemas.py`) automatically catches:
- Removed fields (breaking — consumer reads it and gets KeyError)
- New required fields (breaking — producer must always provide it)
- Type changes on existing fields (breaking — type mismatch at parse)

It does NOT catch:
- Semantic changes (field renamed to mean something different)
- New optional fields (these are safe — permissive consumer ignores them)
- Changes behind an adapter (the adapter is what the hook validates)

---

## Quick Reference

| Change type | Safe? | Action |
|-------------|-------|--------|
| Add optional field | ✅ Yes | Just do it |
| Add required field | ❌ No | Make it optional, or create V2 |
| Remove field | ❌ No | Deprecate first, then create V2 |
| Rename field | ❌ No | Add new (optional) + deprecate old |
| Change field type | ❌ No | Create V2 |
| Change implementation behind adapter | ✅ Yes | Just do it |
| Add entirely new schema | ✅ Yes | Register with `@boundary` |

---

## When in Doubt

Run `python -m data_contracts check` before committing. It runs the same
compatibility checks as the pre-commit hook and shows you exactly what would
break and why.
