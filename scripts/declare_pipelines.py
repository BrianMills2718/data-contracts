#!/usr/bin/env python3
"""Declare the known ecosystem data pipelines in the contract registry.

Run this script whenever a new pipeline is established or an existing one
changes. Persists to ~/projects/data/contract_registry.json.

Usage:
    python scripts/declare_pipelines.py [--dry-run]

## Pipeline design notes

A "pipeline" here means a sequence of boundaries where step N's OUTPUT
feeds directly into step N+1's INPUT schema. If the data does not flow
directly (e.g., a db_path is shared config, or abstraction levels differ),
it is NOT a data pipeline and should not be declared here.

## Removed pipelines (wrong design, kept for reference)

research_graph_to_canon (removed 2026-04-02):
    research_v3.findings -> onto-canon6.import_research_v3_graph
    REASON: research_v3.findings outputs a list[Finding] (in-memory).
    import_research_v3_graph needs graph_path: str (a file path).
    These don't connect. The correct producer would be a future
    research_v3.graph_export boundary that writes findings to disk
    and returns graph_path. Declare this pipeline once that boundary exists.

canon_foundation_export (removed 2026-04-02):
    onto-canon6.promoted_assertion_to_foundation -> onto-canon6.export_foundation_assertions
    REASON: promoted_assertion_to_foundation operates on one in-memory assertion.
    export_foundation_assertions takes db_path + output_path as config params,
    not as data-pipeline outputs. These are different abstraction levels —
    one converts a record, the other bulk-exports from DB. Not a data pipeline.

prompt_eval_score_and_save (removed 2026-04-02):
    prompt_eval.ascore_output -> prompt_eval.save_result
    REASON: ascore_output scores a single LLM output (returns metrics for
    one call). save_result saves a whole experiment (experiment_name, execution_id,
    variants, trials, summary). Different abstraction levels. Not a data pipeline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from data_contracts.registry import ContractRegistry


PIPELINES: list[tuple[str, list[str]]] = [
    # Research memo → onto-canon6 ingestion
    # research_v3 writes memo.yaml to disk (memo_path in output schema).
    # onto-canon6 reads from that memo_path. Direct data pipeline.
    (
        "research_to_canon",
        [
            "research_v3.memo_export",
            "onto-canon6.import_research_v3_memo",
        ],
    ),
    # onto-canon6 full Digimon pipeline (DB → JSONL)
    # digimon_export_from_db reads from DB and produces entity/relationship records.
    # write_digimon_jsonl writes those records to JSONL files.
    (
        "canon_to_digimon_full",
        [
            "onto-canon6.digimon_export_from_db",
            "onto-canon6.write_digimon_jsonl",
        ],
    ),
]


def main() -> None:
    """Declare all known ecosystem pipelines."""
    parser = argparse.ArgumentParser(description="Declare ecosystem pipelines")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be declared")
    args = parser.parse_args()

    reg = ContractRegistry()

    # Remove pipelines that were previously declared but are now invalid.
    # This ensures a clean state after redesigns.
    stale = ["research_graph_to_canon", "canon_foundation_export", "prompt_eval_score_and_save"]
    for name in stale:
        if reg.remove_pipeline(name):
            print(f"  Removed stale pipeline: {name}")

    for name, steps in PIPELINES:
        if args.dry_run:
            print(f"  [dry-run] {name}: {' -> '.join(steps)}")
        else:
            decl = reg.declare_pipeline(name, steps)
            print(f"  Declared: {decl.name}: {' -> '.join(decl.steps)}")

    if not args.dry_run:
        print(f"\n{len(PIPELINES)} pipelines declared. Run 'python -m data_contracts check' to validate.")


if __name__ == "__main__":
    main()
