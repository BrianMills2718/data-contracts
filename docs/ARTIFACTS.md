# Data Contracts Artifact Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Primary Reviewer Artifacts

| Artifact | Role | Portfolio meaning |
|---|---|---|
| [PROJECT.md](../PROJECT.md) | Dossier entrypoint | Frames the repo as supporting contract infrastructure. |
| [README.md](../README.md) | Project overview | Package surface, quick start, and known consumers. |
| [docs/SCHEMA_EVOLUTION.md](SCHEMA_EVOLUTION.md) | Methodology | Schema versioning and compatibility convention. |
| [docs/SCHEMA_DIFF_EXAMPLE.md](SCHEMA_DIFF_EXAMPLE.md) | Portfolio guide | Reviewer-friendly compatibility examples. |
| [docs/ops/CAPABILITY_DECOMPOSITION.md](ops/CAPABILITY_DECOMPOSITION.md) | Ownership ledger | Defines what the package owns and excludes. |
| [docs/METHODOLOGY.md](METHODOLOGY.md) | Methodology spine | Explains the producer-strict, consumer-permissive method. |
| [docs/VALIDATION.md](VALIDATION.md) | Validation register | Separates structural checks from semantic correctness. |
| [docs/CONCERNS.md](CONCERNS.md) | Concern register | Tracks open portfolio and architecture risks. |
| [docs/adr/0001_boundary_contract_substrate_scope.md](adr/0001_boundary_contract_substrate_scope.md) | ADR | Locks scope to shared boundary contracts. |

## Code And Execution Surfaces

| Surface | Role |
|---|---|
| `src/data_contracts/models.py` | Boundary models, permissive variants, provenance helpers. |
| `src/data_contracts/decorator.py` | `@boundary` validation, registration, and observability hook. |
| `src/data_contracts/checker.py` | Compatibility and breaking-change analysis. |
| `src/data_contracts/registry.py` | Contract registry persistence and relationship queries. |
| `src/data_contracts/cli.py` | Agent/human command surface for listing and checking contracts. |
| `src/data_contracts/check_schemas.py` | Schema-checking entrypoint. |
| `tests/` | Unit coverage for checker, decorator, and registry behavior. |

## Evidence Artifacts

| Artifact | Evidence | Notes |
|---|---|---|
| [docs/SCHEMA_EVOLUTION.md](SCHEMA_EVOLUTION.md) | Schema evolution policy | Best source for compatibility rules. |
| [docs/SCHEMA_DIFF_EXAMPLE.md](SCHEMA_DIFF_EXAMPLE.md) | Example schema judgments | Useful for non-code reviewers. |
| [docs/ops/CAPABILITY_DECOMPOSITION.md](ops/CAPABILITY_DECOMPOSITION.md) | Known consumers and ownership | Lists evidence-backed consumers. |
| [docs/plans/01_governed-baseline-and-capability-ownership-rollout.md](plans/01_governed-baseline-and-capability-ownership-rollout.md) | Governed baseline history | Shows local check surface became truthful. |

## Missing Portfolio Artifacts

- One populated compatibility trace from a real downstream boundary.
- A before/after schema-diff artifact showing a breaking change and safe
  evolution path.
- A compact registry matrix excerpt tied to an applied project.
- A consumer note explaining how boundary contracts prevented drift or caught
  an integration error.
