# Plan 01: governed baseline and capability ownership rollout

**Status:** ✅ Complete
**Verified:** 2026-04-01T22:35:16Z
**Verification Evidence:**
```yaml
timestamp: 2026-04-01T22:35:16Z
tests:
  unit: 51 passed in 5.45s
  lint: ruff check src tests
  types: mypy src
  local_gate: make check
  governance:
    - make plan-sync
    - make agents-sync
    - make markdown-links
    - project-meta/scripts/meta/audit_governed_repo.py --repo-root . --json
notes:
  - installer established the mechanical governed baseline
  - installer-added sanctioned worktree entrypoints were removed to keep worktrees out of scope
  - a small real lint/type debt was fixed so the local check surface is truthful
```
**Priority:** High
**Blocked By:** None
**Blocks:** truthful governed baseline and shared capability ownership for `data_contracts`

---

## Gap

**Current:** `data_contracts` is already a real shared package, but it still
operates without the governed-repo baseline expected elsewhere in the active
stack:

1. no `docs/plans/` surface,
2. no `README.md`,
3. no generated `AGENTS.md`,
4. no `scripts/relationships.yaml`,
5. no local validators or read-gating hooks,
6. no `meta-process.yaml`,
7. no repo-local capability ownership source.

**Target:** give `data_contracts` a truthful governed baseline, one local
capability ownership source of record, and a clean shared-registry alignment
without silently enabling sanctioned worktrees.

**Why:** this package already sits on real cross-project boundaries. It should
be discoverable, auditable, and explicit about what it owns before more
consumers accumulate around it.

---

## Research

- `CLAUDE.md` — current repo-local contract and existing API guidance
- `pyproject.toml` — install and test surfaces
- `src/data_contracts/__init__.py` — package exports
- `src/data_contracts/models.py` — boundary models and provenance records
- `src/data_contracts/decorator.py` — `@boundary` runtime behavior
- `src/data_contracts/checker.py` — compatibility/breaking-change logic
- `src/data_contracts/registry.py` — persistent contract registry behavior
- `src/data_contracts/cli.py` — contributor/operator entry points
- `tests/test_checker.py` — compatibility and CLI matrix expectations
- `tests/test_decorator.py` — runtime decorator behavior and observability hook expectations
- `tests/test_registry.py` — registry persistence and composability behavior
- `/home/brian/projects/project-meta_worktrees/plan-52-data-contracts-wave/docs/plans/52_data-contracts-governed-baseline-and-capability-ownership-rollout.md` — shared rollout charter
- `/home/brian/projects/project-meta_worktrees/plan-52-data-contracts-wave/docs/ops/GOVERNED_REPO_CONTRACT.md` — governed-repo minimum contract
- `/home/brian/projects/project-meta_worktrees/plan-52-data-contracts-wave/scripts/meta/install_governed_repo.py` — shared installer behavior

---

## Files Affected

- `CLAUDE.md` (modify)
- `README.md` (create)
- `AGENTS.md` (create or refresh via renderer)
- `Makefile` (create if required for a truthful local command surface)
- `meta-process.yaml` (create)
- `docs/plans/01_governed-baseline-and-capability-ownership-rollout.md` (create)
- `docs/plans/CLAUDE.md` (create)
- `docs/plans/TEMPLATE.md` (create)
- `docs/ops/CAPABILITY_DECOMPOSITION.md` (create)
- `scripts/relationships.yaml` (create)
- bounded installer-driven validator and hook surfaces required for governed status

---

## Plan

### Steps

| Step | What | Status |
|------|------|--------|
| 1 | Freeze local plan/index/template before installer writes | Complete |
| 2 | Normalize `CLAUDE.md` to the shared renderer contract and add a truthful contributor entry surface | Complete |
| 3 | Run the shared governed-repo installer in this clean worktree | Complete |
| 4 | Re-audit and do one bounded manual followthrough for ownership, linkage, and README/Makefile gaps | Complete |
| 5 | Verify, document uncertainties, and close the wave without enabling sanctioned worktrees | Complete |

---

## Acceptance Criteria

- [ ] `data_contracts` audits `PASS` / `governed` after the bounded repair wave
- [ ] the repo has one explicit local ownership source at `docs/ops/CAPABILITY_DECOMPOSITION.md`
- [ ] `CLAUDE.md` and generated `AGENTS.md` stay in sync through the shared renderer
- [ ] the repo documents truthful local test/check commands
- [ ] sanctioned worktree entrypoints remain disabled unless a later explicit plan changes that policy

---

## Failure Modes

| Failure | How to detect | How to fix |
|---------|--------------|-----------|
| shared installer assumes a richer repo than `data_contracts` currently has | installer writes unexpected files or leaves the audit `partial` | keep the installer path primary, capture exact residuals, and do one bounded manual followthrough |
| AGENTS generation fails because `CLAUDE.md` is too free-form | renderer/audit complains about missing required sections | normalize `CLAUDE.md` to the shared section contract before rerunning |
| ownership row is written before local source is truthful | shared registry evidence outpaces repo-local docs | finish the local capability decomposition first, then register the shared row |
| the wave drifts into sanctioned worktree rollout | `meta-process.yaml` or Makefile gains claims/worktree enablement | revert that overreach and record it as out of scope |

---

## Notes

- real consumer evidence already exists in `llm_client`, `onto-canon6`, and prompt-eval schema-registration code
- `data_contracts` is small enough that adding a first README and a minimal Makefile is acceptable if that is the cleanest way to make the local contract truthful
- the shared installer correctly established a governed mechanical baseline, but its default worktree-coordination payload was explicitly removed because this wave keeps sanctioned worktrees out of scope
- making `make check` truthful required fixing a small existing lint/type debt in `src/` and `tests/` rather than documenting a knowingly broken local gate

## Ongoing Maintenance Rule

If execution shows that the current installer cannot truthfully govern a small
library repo like `data_contracts` without shared changes, update this plan
before continuing and keep any shared changes tightly coupled to that blocker.
