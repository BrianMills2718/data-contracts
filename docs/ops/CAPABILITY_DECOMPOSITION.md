# Capability Decomposition

Last updated: 2026-04-01

## Purpose

This document is the repo-local source of record for what `data_contracts` owns
as shared infrastructure, what it intentionally exports to consumers, and what
it should not quietly absorb.

Use this together with:

- [`../plans/01_governed-baseline-and-capability-ownership-rollout.md`](../plans/01_governed-baseline-and-capability-ownership-rollout.md)
- [`../../README.md`](../../README.md)
- [`../../CLAUDE.md`](../../CLAUDE.md)

## Role

`data_contracts` is the shared typed boundary-contract substrate for the
ecosystem.

It owns:

- strict producer-side `BoundaryModel` contracts and permissive consumer-side
  parsing helpers
- the `@boundary` decorator for runtime validation, registration, and bounded
  observability emission
- compatibility and breaking-change checks for producer/consumer schemas
- a lightweight persistent `ContractRegistry` plus composability queries
- a small CLI for listing contracts, checking compatibility, rendering matrices,
  and validating pipelines

It does not own:

- project-specific schema design, workflows, ranking, or orchestration
- generic LLM runtime, cost tracking, or observability storage backends
- cross-repo governance policy or capability-registry enforcement
- sanctioned worktree coordination policy
- repo-specific import/export adapters or canonical semantic-build ownership

Those stay in consuming repos, `llm_client`, `project-meta`, or upstream domain
projects.

## Capability Ledger

| Capability | Current owner | Intended owner | Class | Posture | Notes |
|---|---|---|---|---|---|
| Strict boundary models, permissive consumer parsing, and field-description discipline | `data_contracts` | `data_contracts` | shared infrastructure | no move planned | This is the core reusable contract layer exported by the repo. |
| Runtime boundary validation, registration, and bounded observability emission | `data_contracts` | `data_contracts` | shared infrastructure | keep bounded | Emit compatible boundary-call records, but do not regrow a full runtime or observability store here. |
| Compatibility / breaking-change analysis and pipeline validation | `data_contracts` | `data_contracts` | shared infrastructure | no move planned | These checks are part of the package’s core value as a shared boundary library. |
| Generic LLM execution, durable observability storage, and cost tracking | `llm_client` | `llm_client` | consumed shared infrastructure | consume, do not re-own | `data_contracts` may integrate with `llm_client`, but the runtime layer belongs elsewhere. |
| Cross-repo governance policy, rollout enforcement, and capability registry ownership | `project-meta` | `project-meta` | consumed agent platform | consume, do not re-own | This repo participates in governed rollout but does not define the policy. |
| Repo-specific schemas and adapter semantics | consuming repos | consuming repos | intentionally out of scope | do not absorb | `data_contracts` provides primitives, not each project’s domain model decisions. |

## Known Consumers

Evidence-backed maintained consumers currently include:

- `llm_client`
  - public client call surfaces use `@boundary`
- `onto-canon6`
  - adapters and interchange surfaces use `BoundaryModel` and `@boundary`
- `prompt_eval`
  - schema-registration tooling uses the shared registry
- `research_v3`
  - `adapters.py` registers `research_v3.memo_export` and `research_v3.findings` via `@boundary`
  - imported by `ecosystem-ops/register_schemas.py` (committed 2026-04-05)
- `open_web_retrieval`
  - `AsyncSourceFetcher.fetch()` and retrieval surfaces use `@boundary`
  - imported by `ecosystem-ops/register_schemas.py`
- `grounded-research`
  - `grounded_research.verify.verify_disputes_tyler_v1` uses `@boundary(name="grounded-research.arbitration")`
  - imported by `ecosystem-ops/register_schemas.py`

Do not add a repo to the shared registry’s `known_consumers` list until there
is a maintained import, integration, or committed docs/code evidence.

## Boundary Rules

1. Keep `data_contracts` focused on reusable boundary contracts and compatibility semantics.
2. `llm_client` owns shared LLM runtime behavior and durable observability storage; do not regrow a competing runtime here.
3. `project-meta` owns cross-repo governance policy, rollout, and registry enforcement; this repo participates but does not define those rules.
4. If a proposed feature would turn `data_contracts` into a project-specific schema warehouse or workflow framework, stop and document the boundary decision before implementing it.

## Open Uncertainties

- Whether prompt_eval’s registry-based integration should remain within the same
  single shared capability row or justify a more granular “registry substrate”
  split later.
- Whether the long-term registry persistence path should remain the current
  shared JSON file or move behind a more governed storage contract.
- This ownership wave intentionally keeps sanctioned worktree coordination out
  of scope; the right later adoption gate for enabling it here remains unsettled.
