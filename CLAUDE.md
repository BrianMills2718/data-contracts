# data_contracts

Typed data contracts for cross-project boundaries. Enforces Pydantic models at every function that crosses a project boundary.

## Core API

```python
from data_contracts import BoundaryModel, boundary, registry

class MyOutput(BoundaryModel):
    result: str = Field(description="The result")

@boundary(name="my_project.export", version="0.1.0", producer="my_project")
def my_export(data: MyInput) -> MyOutput:
    return MyOutput(result="ok")
```

## Key Classes

- `BoundaryModel` — base class with `extra="forbid"`, `.permissive()` for consumer parsing, `.schema_dict()`
- `@boundary` — decorator that validates I/O, registers in registry, tracks calls
- `BoundaryRegistry` — auto-populated registry of all boundaries
- `ProvenanceRecord` — tracks where data came from (agent, project, timestamp, evidence)
- `ContractViolation` — raised on type mismatches (fail loud)

## Rules

1. Every function crossing a project boundary uses `@boundary`
2. Input/output are `BoundaryModel` subclasses with `Field(description=...)` on every field
3. Producer models use `extra="forbid"` (strict) — this is the default
4. Consumer models use `.permissive()` (extra="ignore")
5. No `dict`, `Any`, or `**kwargs` at boundaries

## Registry

Auto-populated at import time. Persists to `~/projects/data/contract_registry.json`.

```python
from data_contracts import registry
boundaries = registry.list_all()
registry.check_all()  # returns list of violations
```
