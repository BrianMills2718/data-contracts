# data_contracts

---

## ⚡ AUTONOMOUS OPERATION DIRECTIVE

> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> ⚠️  NEVER STOP — NO EXCEPTIONS, NO EXCUSES  ⚠️
> ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
>
> Brian has explicitly authorized continuous autonomous operation.
> A completed phase, a green test suite, or a finished commit is
> NOT a stop condition. Update the sprint tracker, commit, move
> immediately to the next phase.

**ONLY TWO LEGITIMATE STOP CONDITIONS:**
1. An action is BOTH irreversible AND affects shared state (force push, drop prod tables)
2. A genuine architectural decision not pre-made in the plan that cannot be safely defaulted

**Everything else — uncertainty, tool failure, partial results — is NOT a stop condition.**
Log it in the sprint tracker and proceed with the safer option.

**Always work in worktrees for Plan-level changes.** Commit at every verified milestone.
**Active sprint:** see `docs/ops/SPRINT_2026_04_04_EVENING.md` in project-meta.

---

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

## Principles

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

## Workflow

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

## References

- `README.md` — contributor entry point and consumer-facing summary
- `docs/plans/CLAUDE.md` — repo-local plan index
- `docs/ops/CAPABILITY_DECOMPOSITION.md` — local ownership source of record
- `src/data_contracts/models.py`
- `src/data_contracts/decorator.py`
- `src/data_contracts/checker.py`
- `src/data_contracts/registry.py`
