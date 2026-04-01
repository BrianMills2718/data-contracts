# data_contracts

<!-- GENERATED FILE: DO NOT EDIT DIRECTLY -->
<!-- generated_by: scripts/meta/render_agents_md.py -->
<!-- canonical_claude: CLAUDE.md -->
<!-- canonical_relationships: scripts/relationships.yaml -->
<!-- canonical_relationships_sha256: b0cf04cb9ddf -->
<!-- sync_check: python scripts/meta/check_agents_sync.py --check -->

This file is a generated Codex-oriented projection of repo governance.
Edit the canonical sources instead of editing this file directly.

Canonical governance sources:
- `CLAUDE.md` — human-readable project rules, workflow, and references
- `scripts/relationships.yaml` — machine-readable ADR, coupling, and required-reading graph

## Purpose

Typed data contracts for cross-project boundaries. This repo owns the shared
boundary model layer: strict Pydantic models at project seams, compatibility
checking, boundary registration, and lightweight runtime observability for
those crossings.

## Commands

```bash
pip install -e ~/projects/data_contracts
python -m pytest -q
python -m data_contracts list
python -m data_contracts check
python -m data_contracts matrix
python -m data_contracts pipeline step_a step_b
```

## Operating Rules

This projection keeps the highest-signal rules in always-on Codex context.
For full project structure, detailed terminology, and any rule omitted here,
read `CLAUDE.md` directly.

### Principles

1. Every function crossing a project boundary uses `@boundary` or an equivalent
   explicit registry entry.
2. Input/output payloads are `BoundaryModel` subclasses with
   `Field(description=...)` on every field.
3. Producer-side models stay strict with `extra="forbid"`.
4. Consumer-side parsing should use `.permissive()` rather than broadening the
   producer contract.
5. The package owns typed boundary/runtime primitives, not repo-specific
   workflows.
6. Repo-local ownership and migration posture live in
   `docs/ops/CAPABILITY_DECOMPOSITION.md`.

### Workflow

### Core API

```python
from data_contracts import BoundaryModel, boundary, registry, check_compatibility

class MyOutput(BoundaryModel):
    result: str = Field(description="The result")

@boundary(name="my_project.export", version="0.1.0", producer="my_project")
def my_export(data: MyInput) -> MyOutput:
    return MyOutput(result="ok")

violations = check_compatibility(producer_schema, consumer_schema)
```

### Key Exports

- `BoundaryModel` — base class with `extra="forbid"`, `.permissive()`, and `.schema_dict()`
- `@boundary` — validates outputs, registers boundaries, tracks call outcomes, and emits optional observability
- `ContractRegistry` / `registry` — auto-populated singleton of registered boundaries
- `check_compatibility()` — producer/consumer schema compatibility check
- `ContractInfo` / `ContractViolation` / `ContractViolationError` — contract metadata and failure primitives
- `BoundaryResult` / `ProvenanceRecord` — typed runtime and provenance helpers

### Registry

The local registry auto-populates at import time and persists to
`~/projects/data/contract_registry.json`.

## Machine-Readable Governance

`scripts/relationships.yaml` is the source of truth for machine-readable governance in this repo: ADR coupling, required-reading edges, and doc-code linkage. This generated file does not inline that graph; it records the canonical path and sync marker, then points operators and validators back to the source graph. Prefer deterministic validators over prompt-only memory when those scripts are available.

## References

- `README.md` — contributor entry point and consumer-facing summary
- `docs/plans/CLAUDE.md` — repo-local plan index
- `docs/ops/CAPABILITY_DECOMPOSITION.md` — local ownership source of record
- `src/data_contracts/models.py`
- `src/data_contracts/decorator.py`
- `src/data_contracts/checker.py`
- `src/data_contracts/registry.py`
