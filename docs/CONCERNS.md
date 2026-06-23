# Data Contracts Concern Register

Wiki home: http://localhost:8088/index.php/Project_Wiki

## Open Concerns

| ID | Concern | Severity | Current mitigation | Next evidence/action |
|---|---|---:|---|---|
| DC-PORT-001 | Infrastructure can look abstract without an applied boundary trace. | High | Dossier frames it as supporting evidence. | Publish one real producer/consumer compatibility trace. |
| DC-PORT-002 | Structural compatibility can be mistaken for semantic correctness. | High | Validation register separates shape, compatibility, and semantics. | Tie portfolio claims to consumer tests or review notes. |
| DC-PORT-003 | Registry generated state can be mistaken for source of truth. | Medium | README and methodology say decorated code is canonical. | Include source decorator in any trace artifact. |
| DC-PORT-004 | The package could absorb project-specific schemas. | Medium | Capability decomposition excludes domain schema warehousing. | Keep project-specific adapters in consuming repos. |
| DC-PORT-005 | Registry persistence architecture may need to mature. | Medium | Capability decomposition lists it as an uncertainty. | Decide only after real registry use requires it. |

## Portfolio Judgment

`data_contracts` is useful supporting evidence for governed AI engineering. It
should not lead the portfolio, but it helps applied projects look more serious
because their cross-project payloads have typed contracts, compatibility
checks, and explicit failure behavior.
