# Data Contracts Validation Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Validation Position

`data_contracts` has implementation evidence for structural boundary
governance. It still needs an applied downstream compatibility trace to become
strong portfolio evidence.

The key distinction:

- **shape-valid:** a payload satisfies a Pydantic boundary model;
- **compatibility-valid:** producer and consumer schemas can evolve without a
  detected structural break;
- **semantics-valid:** the consuming project interprets the field correctly for
  its domain.

This repo owns the first two categories. Consuming projects own the third.

## Current Evidence

| Evidence area | Current artifact | Claim licensed |
|---|---|---|
| Package surface | `README.md` | Boundary model, decorator, registry, checker, and CLI exist. |
| Schema evolution | `docs/SCHEMA_EVOLUTION.md` | Compatibility rules are explicit. |
| Schema diff example | `docs/SCHEMA_DIFF_EXAMPLE.md` | Reviewers can understand common change judgments. |
| Capability ownership | `docs/ops/CAPABILITY_DECOMPOSITION.md` | Shared boundary is documented and scoped. |
| Governed baseline | `docs/plans/01_governed-baseline-and-capability-ownership-rollout.md` | Local check surface was verified during rollout. |

## Evidence Not Yet Present

Do not claim the following without new evidence:

- semantic correctness of downstream project schemas;
- complete ecosystem-wide boundary coverage;
- registry persistence is final architecture;
- compatibility checks replace human review for meaning changes;
- this repo owns orchestration, workflow planning, or project-meta policy.

## Commands

Core checks:

```bash
make test-quick
make check
python scripts/check_markdown_links.py PROJECT.md docs/METHODOLOGY.md docs/ARTIFACTS.md docs/VALIDATION.md docs/CONCERNS.md docs/adr/0001_boundary_contract_substrate_scope.md docs/wiki_manifest.yaml
git diff --check
```

Governed-repo checks:

```bash
make plan-sync
make agents-sync
make markdown-links
```

## Portfolio Readiness Gate

The repo is portfolio-ready as supporting infrastructure when framed with its
current caveats. It becomes stronger externally when it has:

1. One populated compatibility trace from a real consumer.
2. A saved schema-diff artifact showing safe and breaking changes.
3. A registry matrix excerpt connected to a downstream project.
4. A consumer integration note showing why the boundary mattered.
