# Plan #N: [Name]

**Status:** Planned
**Priority:** High | Medium | Low
**Blocked By:** None
**Blocks:** None

---

## Gap

**Current:** What exists now

**Target:** What we want

**Why:** Why this matters

---

## Research

> **REQUIRED:** What was investigated before planning. Cite specific code, docs,
> prior art, or benchmarks. This prevents guessing.

- `path/to/file.py:45-89` — existing implementation
- `CLAUDE.md` — project conventions
- [External reference] — what the field already knows

---

## Files Affected

> Declare upfront what files will be touched.

- src/module.py (modify)
- src/new_file.py (create)
- tests/test_module.py (create)

---

## Plan

### Steps

| Step | What | Status |
|------|------|--------|
| 1 | First concrete action | Not started |
| 2 | Second concrete action | Not started |

---

## Acceptance Criteria

> **REQUIRED:** What passes and what fails. Every criterion must be verifiable.

- [ ] First criterion (how to verify: `command` or description)
- [ ] Second criterion
- [ ] All tests pass: `python -m pytest -q`

---

## Failure Modes

> What can go wrong and how to diagnose it.

| Failure | How to detect | How to fix |
|---------|--------------|-----------|
| Example failure | Symptom or test | Fix approach |

---

## Notes

[Design decisions, alternatives considered, ADRs created]

## Ongoing Maintenance Rule

If execution uncovers a real issue after the plan is created, update this plan
before continuing when the issue changes scope, blockers, files affected,
constraints, acceptance criteria, or required tests.
