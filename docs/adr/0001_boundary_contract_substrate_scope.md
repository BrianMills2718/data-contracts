# ADR 0001: Keep Data Contracts A Boundary Contract Substrate

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Status

Accepted.

## Context

The ecosystem needs explicit contracts at project seams. `data_contracts`
already provides strict producer models, permissive consumer parsing,
runtime boundary validation, compatibility checks, and a lightweight registry.

It is tempting for a shared contract package to grow into a domain schema
warehouse, workflow engine, registry policy authority, or orchestration layer.
That would make the package harder to reuse and would blur ownership with
consuming projects, `project-meta`, `llm_client`, and orchestration systems.

## Decision

`data_contracts` remains a typed boundary-contract substrate:

- own reusable `BoundaryModel` behavior;
- own the `@boundary` decorator for validation, registration, and bounded
  observability emission;
- own schema compatibility and breaking-change checks;
- own lightweight registry and CLI surfaces for contract inspection;
- leave project-specific schema semantics to consuming repos;
- leave ecosystem policy and enforcement to `project-meta`;
- leave LLM runtime, cost tracking, and durable observability storage to
  `llm_client`;
- leave workflow orchestration to the appropriate project or agent platform.

Portfolio pages should present this repo through downstream boundary traces,
not as a standalone product.

## Consequences

Benefits:

- keeps the package small and reusable;
- gives projects a common way to make boundary behavior explicit;
- avoids turning shared infrastructure into a schema warehouse;
- makes compatibility and breaking-change review easier to automate.

Costs:

- this repo alone does not prove downstream semantic correctness;
- complete value is easiest to see through applied consumer traces;
- future registry persistence needs may require a separate architecture
  decision.

## Controls

- [docs/SCHEMA_EVOLUTION.md](../SCHEMA_EVOLUTION.md) defines schema evolution
  rules.
- [docs/ops/CAPABILITY_DECOMPOSITION.md](../ops/CAPABILITY_DECOMPOSITION.md)
  defines ownership boundaries.
- [docs/VALIDATION.md](../VALIDATION.md) separates structural validation from
  semantic correctness.
- [docs/CONCERNS.md](../CONCERNS.md) tracks portfolio and architecture risks.
