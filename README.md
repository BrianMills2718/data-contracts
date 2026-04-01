# data_contracts

Shared typed data contracts for cross-project boundaries.

`data_contracts` owns the shared model and validation layer for ecosystem
boundary crossings:

- strict producer-side boundary models,
- permissive consumer-side parsing helpers,
- the `@boundary` decorator for runtime validation and registration,
- schema compatibility and breaking-change checks,
- a lightweight contract registry and CLI.

## Suggested Reading Order

1. `CLAUDE.md`
2. `docs/plans/CLAUDE.md`
3. `docs/ops/CAPABILITY_DECOMPOSITION.md`
4. `README.md`

## Installation

```bash
pip install -e .

# Optional dev tooling
pip install -e ".[dev]"

# Optional shared observability integration
pip install -e ~/projects/llm_client
```

## Quick Start

```python
from pydantic import Field

from data_contracts import BoundaryModel, boundary, check_compatibility


class ExportInput(BoundaryModel):
    name: str = Field(description="Entity name")


class ExportOutput(BoundaryModel):
    normalized_name: str = Field(description="Canonicalized entity name")


@boundary(
    name="example.normalize_name",
    version="0.1.0",
    producer="example_project",
    consumers=["consumer_project"],
)
def normalize_name(data: ExportInput) -> ExportOutput:
    return ExportOutput(normalized_name=data.name.strip().title())


violations = check_compatibility(
    producer_schema=ExportOutput.model_json_schema(),
    consumer_schema=ExportOutput.permissive().model_json_schema(),
)
assert violations == []
```

## Package Surface

- `BoundaryModel`
  - strict producer-side base model with `.permissive()` for consumer parsing
- `@boundary`
  - validates boundary I/O, registers contracts, tracks call outcomes, and emits
    optional observability through `llm_client` when installed
- `ContractRegistry` / `registry`
  - persistent registry of known boundaries and compatibility relationships
- `check_compatibility()` / `check_breaking_changes()`
  - schema compatibility and version-drift checks
- CLI
  - `python -m data_contracts list`
  - `python -m data_contracts check`
  - `python -m data_contracts matrix`
  - `python -m data_contracts pipeline step_a step_b`

## Shared Capability Ownership

`data_contracts` is the shared typed boundary-contract substrate for the
ecosystem.

The repo-local ownership source of record is:

- `docs/ops/CAPABILITY_DECOMPOSITION.md`

That document states what `data_contracts` owns, what it should not absorb, and
which shared boundaries stay in `llm_client`, `project-meta`, or consuming
repos.

## Known Consumers

Evidence-backed current consumers include:

- `llm_client`
  - uses `@boundary` on public LLM call surfaces
- `onto-canon6`
  - uses `BoundaryModel` and `@boundary` on interchange/export/import adapters
- `prompt_eval`
  - uses the contract registry in schema-registration tooling

## Running Checks

```bash
make test-quick
make test
make check
make plan-sync
make agents-sync
```

`make check` is intended to be the truthful local gate for tests, lint, and
type checking.
