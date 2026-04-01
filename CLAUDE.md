# data_contracts

Typed data contracts for cross-project boundaries. Enforces Pydantic models at every function that crosses a project boundary.

## Core API

```python
from data_contracts import BoundaryModel, boundary, registry, check_compatibility

class MyOutput(BoundaryModel):
    result: str = Field(description="The result")

@boundary(name="my_project.export", version="0.1.0", producer="my_project")
def my_export(data: MyInput) -> MyOutput:
    return MyOutput(result="ok")

# Check schema compatibility
violations = check_compatibility(producer_schema, consumer_schema)
```

## Key Exports

- `BoundaryModel` -- base class with `extra="forbid"`, `.permissive()`, `.schema_dict()`
- `@boundary` -- decorator: validates I/O, registers in registry, tracks calls, logs to llm_client (optional)
- `ContractRegistry` / `registry` -- auto-populated singleton of all boundaries
- `check_compatibility(producer_schema, consumer_schema)` -- returns list of `ContractViolation`
- `ContractInfo` -- registry metadata model
- `ContractViolation` -- schema incompatibility model
- `ContractViolationError` -- runtime exception (fail loud)
- `BoundaryResult` -- call outcome for observability
- `ProvenanceRecord` -- data provenance tracking

## CLI

```bash
python -m data_contracts list    # list all registered boundaries
python -m data_contracts check   # check compatibility across producer-consumer pairs
```

## Rules

1. Every function crossing a project boundary uses `@boundary`
2. Input/output are `BoundaryModel` subclasses with `Field(description=...)` on every field
3. Producer models use `extra="forbid"` (strict) -- this is the default
4. Consumer models use `.permissive()` (extra="ignore")
5. No `dict`, `Any`, or `**kwargs` at boundaries

## Registry

Auto-populated at import time. Persists to `~/projects/data/contract_registry.json`.

## How to Build/Test

```bash
pip install -e ~/projects/data_contracts
pytest tests/ -v
```
