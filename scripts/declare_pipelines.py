#!/usr/bin/env python3
"""Declare the known ecosystem data pipelines in the contract registry.

Run this script whenever a new pipeline is established or an existing one
changes. Persists to ~/projects/data/contract_registry.json.

Usage:
    python scripts/declare_pipelines.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from data_contracts.registry import ContractRegistry


PIPELINES: list[tuple[str, list[str]]] = [
    # Research memo → onto-canon6 ingestion
    # NOTE: schema gap — research_v3.memo_export output missing 'memo_path'
    # that onto-canon6.import_research_v3_memo requires. Real gap to fix.
    (
        "research_to_canon",
        [
            "research_v3.memo_export",
            "onto-canon6.import_research_v3_memo",
        ],
    ),
    # Research graph → onto-canon6 graph import
    # NOTE: schema gap — research_v3.findings output missing 'graph_path'
    # that onto-canon6.import_research_v3_graph requires. Real gap to fix.
    (
        "research_graph_to_canon",
        [
            "research_v3.findings",
            "onto-canon6.import_research_v3_graph",
        ],
    ),
    # onto-canon6 full Digimon pipeline (DB → JSONL)
    (
        "canon_to_digimon_full",
        [
            "onto-canon6.digimon_export_from_db",
            "onto-canon6.write_digimon_jsonl",
        ],
    ),
    # Foundation assertions (promoted → exported)
    # NOTE: schema gap — promoted_assertion_to_foundation output missing 'db_path'
    # that export_foundation_assertions requires. Real gap to fix.
    (
        "canon_foundation_export",
        [
            "onto-canon6.promoted_assertion_to_foundation",
            "onto-canon6.export_foundation_assertions",
        ],
    ),
    # prompt_eval internal pipeline
    # NOTE: schema gap — ascore_output output missing 'experiment_name'
    # that save_result requires. Real gap to fix.
    (
        "prompt_eval_score_and_save",
        [
            "prompt_eval.ascore_output",
            "prompt_eval.save_result",
        ],
    ),
]


def main() -> None:
    """Declare all known ecosystem pipelines."""
    parser = argparse.ArgumentParser(description="Declare ecosystem pipelines")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be declared")
    args = parser.parse_args()

    reg = ContractRegistry()

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
