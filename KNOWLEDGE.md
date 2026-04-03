# Operational Knowledge — data_contracts

Shared findings from all agent sessions. Any agent brain can read and append.
Human-reviewed periodically.

## Findings

<!-- Append new findings below this line. Do not overwrite existing entries. -->
<!-- Format: ### YYYY-MM-DD — {agent} — {category}                          -->
<!-- Categories: bug-pattern, performance, schema-gotcha, integration-issue, -->
<!--             workaround, best-practice                                   -->
<!-- Agent names: claude-code, codex, openclaw                               -->

### 2026-04-02 — claude-code — schema-gotcha

First real pipeline validation run found 4 genuine schema gaps:
- `research_v3.memo_export` output missing `memo_path` field required by `onto-canon6.import_research_v3_memo`
- `research_v3.findings` output missing `graph_path` field required by `onto-canon6.import_research_v3_graph`
- `onto-canon6.promoted_assertion_to_foundation` output missing `db_path` required by `export_foundation_assertions`
- `prompt_eval.ascore_output` output missing `experiment_name` required by `save_result`

These are real cross-project boundary mismatches — the producer output schemas don't include path/context fields that the consumer boundaries require. Fix by adding these fields to the producer output models in each project.

Pipeline `canon_to_digimon_full` (digimon_export_from_db → write_digimon_jsonl) passes clean.
