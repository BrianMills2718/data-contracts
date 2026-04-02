"""CLI: python -m data_contracts list | check | matrix | pipeline"""

from __future__ import annotations

import argparse
import sys

from data_contracts.checker import check_compatibility
from data_contracts.registry import ContractRegistry


def cmd_list(_args: argparse.Namespace) -> None:
    """List all registered boundaries."""
    for b in sorted(ContractRegistry().list_all(), key=lambda x: x.name):
        cs = ", ".join(b.consumers) or "(none)"
        print(f"  {b.name}  v{b.version}  producer={b.producer or '?'}  "
              f"consumers={cs}  calls={b.call_count}  errors={b.error_count}")


def cmd_check(_args: argparse.Namespace) -> None:
    """Check compatibility across all explicitly declared pipelines."""
    reg = ContractRegistry()
    pipelines = reg.list_pipelines()
    if not pipelines:
        print("No declared pipelines. Use 'declare-pipeline' to register one.")
        return
    total_violations = 0
    for pipeline in pipelines:
        violations = reg.validate_pipeline(pipeline.steps)
        for v in violations:
            total_violations += 1
            print(f"  VIOLATION [{v.severity}] {v.producer} -> {v.consumer}: "
                  f"{v.kind} on '{v.field}' -- {v.detail}")
    if total_violations == 0:
        print(f"All clear. Checked {len(pipelines)} pipeline(s), 0 violations.")
    else:
        print(f"\n{total_violations} violation(s) across {len(pipelines)} pipeline(s).")
        sys.exit(1)


def cmd_matrix(_args: argparse.Namespace) -> None:
    """Render an NxN compatibility matrix of all boundaries with schemas."""
    reg = ContractRegistry()
    boundaries = sorted(reg.list_all(), key=lambda x: x.name)

    # Filter to boundaries that have at least one schema
    has_output = [b for b in boundaries if b.output_schema]
    has_input = [b for b in boundaries if b.input_schema]

    if not has_output or not has_input:
        print("No boundaries with both input and output schemas found.")
        return

    # Build compatibility matrix: rows=producers (output), cols=consumers (input)
    producer_names = [b.name for b in has_output]
    consumer_names = [b.name for b in has_input]

    # Truncate names for display
    max_name_len = 20
    def trunc(name: str) -> str:
        """Truncate boundary name for compact display."""
        return name if len(name) <= max_name_len else name[:max_name_len - 2] + ".."

    # Column header width
    col_w = max(len(trunc(n)) for n in consumer_names)
    col_w = max(col_w, 3)
    row_label_w = max(len(trunc(n)) for n in producer_names)
    row_label_w = max(row_label_w, 8)

    # Print header
    header = " " * (row_label_w + 2)
    for cn in consumer_names:
        header += trunc(cn).rjust(col_w + 1)
    print(header)
    print(" " * (row_label_w + 2) + "-" * (len(consumer_names) * (col_w + 1)))

    # Print rows
    for prod in has_output:
        row = trunc(prod.name).rjust(row_label_w) + " |"
        for con in has_input:
            if prod.name == con.name:
                cell = "."
            else:
                producer_schema = prod.output_schema
                consumer_schema = con.input_schema
                if producer_schema is None or consumer_schema is None:
                    cell = "?"
                    row += cell.rjust(col_w + 1)
                    continue
                violations = check_compatibility(
                    producer_schema,
                    consumer_schema,
                    producer_name=prod.name, consumer_name=con.name,
                )
                cell = "OK" if not violations else f"X{len(violations)}"
            row += cell.rjust(col_w + 1)
        print(row)

    # Legend
    print()
    print("Legend: OK=compatible  X<n>=violations  .=self")


def cmd_declare_pipeline(args: argparse.Namespace) -> None:
    """Declare and persist an explicit pipeline of boundary steps."""
    reg = ContractRegistry()
    decl = reg.declare_pipeline(args.name, args.steps)
    print(f"Declared pipeline '{decl.name}': {' -> '.join(decl.steps)}")


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Validate a pipeline of boundary steps for schema compatibility."""
    steps = args.steps
    if len(steps) < 2:
        print("Pipeline needs at least 2 steps.")
        sys.exit(1)

    reg = ContractRegistry()
    violations = reg.validate_pipeline(steps)

    if not violations:
        print(f"Pipeline valid: {' -> '.join(steps)}")
    else:
        print(f"Pipeline: {' -> '.join(steps)}")
        print()
        for v in violations:
            print(f"  VIOLATION [{v.severity}] {v.producer} -> {v.consumer}: "
                  f"{v.kind} on '{v.field}' -- {v.detail}")
        print(f"\n{len(violations)} violation(s).")
        sys.exit(1)


def main() -> None:
    """Entry point for python -m data_contracts."""
    p = argparse.ArgumentParser(prog="data_contracts", description="Typed data contracts")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("list", help="List all registered boundaries")
    sub.add_parser("check", help="Check compatibility across all declared pipelines")
    sub.add_parser("matrix", help="Render NxN compatibility matrix")
    pipe_p = sub.add_parser("pipeline", help="Validate an ad-hoc pipeline of boundary steps")
    pipe_p.add_argument("steps", nargs="+", help="Ordered boundary names forming the pipeline")
    decl_p = sub.add_parser("declare-pipeline", help="Declare and persist a named pipeline")
    decl_p.add_argument("name", help="Pipeline name")
    decl_p.add_argument("steps", nargs="+", help="Ordered boundary names forming the pipeline")
    args = p.parse_args()
    cmds = {
        "list": cmd_list, "check": cmd_check, "matrix": cmd_matrix,
        "pipeline": cmd_pipeline, "declare-pipeline": cmd_declare_pipeline,
    }
    if args.command in cmds:
        cmds[args.command](args)
    else:
        p.print_help()
        sys.exit(1)
