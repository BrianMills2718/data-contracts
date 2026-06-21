# Data Contracts Schema Diff Example

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Portfolio Claim

Data Contracts is supporting engineering evidence for governed AI systems. It shows how project boundaries can be explicit Pydantic schemas with compatibility checks instead of informal dictionaries.

## Concrete Schema-Diff Pattern

| Change | Compatibility judgment | Reason |
|--------|------------------------|--------|
| Add optional output field | Usually accepted | Existing consumers can ignore it |
| Add required output field | Requires review | Producers and consumers may disagree on availability |
| Remove output field | Usually blocked | Existing consumers may depend on it |
| Rename field | Usually blocked unless aliased | It is a remove plus add from the consumer perspective |
| Widen consumer model with `extra="ignore"` | Usually accepted | Consumer remains tolerant of producer additions |
| Tighten producer model with `extra="forbid"` | Usually accepted when tests pass | Unexpected fields fail loudly at the boundary |

## Reviewer Path

1. Read `README.md` for the boundary contract pattern.
2. Read `docs/SCHEMA_EVOLUTION.md` for versioning and compatibility rules.
3. Read `docs/ops/CAPABILITY_DECOMPOSITION.md` to see where ownership belongs.

## Caveat

This is infrastructure evidence. It should support applied systems such as AC15, Grounded Research, Open Web Retrieval, and OSINT Tools rather than lead the portfolio alone.
