# Data Contracts Methodology

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Goal

`data_contracts` makes ecosystem data boundaries explicit. Its job is to turn
cross-project payload exchange into typed contracts that can be inspected,
validated, versioned, and checked for compatibility.

The target loop is:

```text
producer model -> boundary call -> consumer model -> compatibility check -> registry evidence
```

## Design Method

The repo uses a producer-strict, consumer-permissive contract model:

1. Producers expose Pydantic `BoundaryModel` outputs with `extra="forbid"`.
2. Consumers parse through permissive variants that ignore compatible additions.
3. `@boundary` records the name, version, producer, and consumers of each
   boundary.
4. Runtime calls validate inputs and outputs at the project seam.
5. Compatibility checks classify schema changes before consumers break.
6. The registry records the known contract surface, but decorated code remains
   canonical.

This deliberately separates contract mechanics from domain modeling. Projects
own their own schema semantics; `data_contracts` owns the validation and
compatibility substrate.

## Borrow-Vs-Build

Borrowed:

- Pydantic for model validation and JSON schema generation;
- Python packaging and CLI conventions for distribution;
- standard JSON schema concepts for compatibility analysis.

Built locally:

- `BoundaryModel` conventions for strict producers and permissive consumers;
- `@boundary` runtime validation and registration;
- compatibility and breaking-change checks;
- registry persistence and matrix rendering;
- lightweight pipeline composability checks;
- optional boundary-call observability integration.

## Modality Split

Deductive / plan-first surfaces:

- strict-vs-permissive boundary behavior;
- compatibility rule definitions;
- registry record shape;
- CLI command contracts;
- owned-vs-not-owned capability boundaries.

Exploratory / ladder surfaces:

- how much semantic compatibility can be detected mechanically;
- which registry persistence model is sufficient long term;
- whether richer provenance belongs in this package or in consuming projects;
- how much registry visualization is useful before it becomes project-meta
  governance.

Exploratory surfaces should be driven by real consumer traces rather than broad
infrastructure expansion.

## ADR Map

- [0001_boundary_contract_substrate_scope.md](adr/0001_boundary_contract_substrate_scope.md)
  records the scope decision: typed boundary substrate, not workflow engine or
  domain schema warehouse.

## Main Failure Modes

| Failure mode | Why it matters | Control |
|---|---|---|
| Treating schemas as semantics | A compatible shape can still mean the wrong thing. | Projects own domain review and tests. |
| Turning the registry into source of truth | Generated state can drift. | Decorated code remains canonical. |
| Absorbing project-specific schemas | Bloats shared infrastructure. | Capability decomposition excludes schema warehousing. |
| Overclaiming compatibility checks | Tooling catches structural breaks, not all meaning changes. | Validation docs distinguish mechanical and semantic review. |
| Rebuilding orchestration here | Duplicates project-meta/OpenClaw responsibilities. | ADR keeps this repo at the boundary-contract layer. |
