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

### 2026-04-02 — claude-code — best-practice

Pipeline design rule: a declared pipeline must represent actual data flow, not
workflow sequence. Producer output schema fields must be present in consumer
input schema. Three pipelines were removed because they were workflow sequences,
not data pipelines:

- research_graph_to_canon: `research_v3.findings` outputs list[Finding] (in-memory),
  consumer needs `graph_path: str`. Different kinds — not a data pipeline.
  Correct design: create `research_v3.graph_export` boundary that writes to disk
  and returns `graph_path`, then connect that to `import_research_v3_graph`.

- canon_foundation_export: `promoted_assertion_to_foundation` converts one
  in-memory assertion; `export_foundation_assertions` takes `db_path` (config
  param). Different abstraction levels. Not a data pipeline.

- prompt_eval_score_and_save: `ascore_output` scores one call; `save_result`
  saves a whole experiment. Different abstraction levels. Not a data pipeline.

Gap 1 (memo_export → memo_path) was fixed by patching contract_registry.json
directly (research_v3 has no @boundary decorators; schema was registered
manually in a previous session). If register_schemas.py is extended to cover
research_v3, the patch will need to be re-applied or made canonical there.
