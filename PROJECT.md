# Data Contracts Project Dossier

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Role

`data_contracts` is supporting shared infrastructure. It is the Brian-built
typed boundary-contract substrate for project-to-project data exchange in the
ecosystem.

Its portfolio value is not that it is an end-user application. Its value is
that AI systems and research tools can expose explicit Pydantic contracts,
validate boundary calls, check schema compatibility, and detect breaking
changes instead of passing informal dictionaries across project seams.

## Current Status

Safe current claims:

- `BoundaryModel` provides strict producer-side contracts with permissive
  consumer parsing helpers;
- the `@boundary` decorator validates runtime inputs and outputs, registers
  contracts, and emits bounded observability when configured;
- `ContractRegistry` records known boundaries and consumer relationships;
- compatibility and breaking-change checks exist for producer/consumer schemas;
- the CLI can list contracts, check compatibility, render matrices, and
  validate simple pipelines;
- schema-evolution policy is documented in
  [docs/SCHEMA_EVOLUTION.md](docs/SCHEMA_EVOLUTION.md);
- capability ownership is documented in
  [docs/ops/CAPABILITY_DECOMPOSITION.md](docs/ops/CAPABILITY_DECOMPOSITION.md);
- evidence-backed consumers include `llm_client`, `onto-canon6`,
  `prompt_eval`, `research_v3`, `open_web_retrieval`, and
  `grounded-research`.

Do not claim:

- this repo designs every project's domain schema;
- it is a workflow engine, orchestration layer, or registry policy authority;
- compatibility checks prove semantic correctness;
- it replaces downstream tests or human schema review;
- the generated registry file is the source of truth. Decorated code is the
  source of truth.

## Reviewer Path

1. Read [README.md](README.md) for the boundary-contract pattern and public
   package surface.
2. Read [docs/SCHEMA_EVOLUTION.md](docs/SCHEMA_EVOLUTION.md) for compatibility
   rules.
3. Read [docs/SCHEMA_DIFF_EXAMPLE.md](docs/SCHEMA_DIFF_EXAMPLE.md) for a
   reviewer-friendly example of schema-diff judgments.
4. Read [docs/ops/CAPABILITY_DECOMPOSITION.md](docs/ops/CAPABILITY_DECOMPOSITION.md)
   for what this repo owns and what it should not absorb.
5. Read [docs/METHODOLOGY.md](docs/METHODOLOGY.md),
   [docs/VALIDATION.md](docs/VALIDATION.md), and
   [docs/CONCERNS.md](docs/CONCERNS.md) before using it as portfolio evidence.

## Why It Matters For An AI Engineer / Analyst Portfolio

AI systems fail at boundaries when implicit data contracts drift. This repo
shows the governance layer that makes cross-project boundaries explicit:
strict producer models, permissive consumer adapters, versioned schema
evolution, compatibility checks, and observable boundary calls.

The best public framing is: "I built a shared contract layer so AI and research
systems can make cross-project data exchanges inspectable, validated, and
compatible over time."

## Next Evidence To Create

The next portfolio-strengthening artifact is a populated compatibility trace:

1. Choose a real boundary used by a downstream project.
2. Show producer schema, consumer schema, and compatibility result.
3. Show what would count as a breaking change.
4. Show the runtime `@boundary` call behavior and registry entry.
5. Link the trace back to the downstream project that depends on the contract.
