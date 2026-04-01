"""CLI: python -m data_contracts list | python -m data_contracts check"""
from __future__ import annotations
import argparse, sys
from data_contracts.checker import check_compatibility
from data_contracts.registry import ContractRegistry


def cmd_list(_args: argparse.Namespace) -> None:
    """List all registered boundaries."""
    for b in sorted(ContractRegistry().list_all(), key=lambda x: x.name):
        cs = ", ".join(b.consumers) or "(none)"
        print(f"  {b.name}  v{b.version}  producer={b.producer or '?'}  "
              f"consumers={cs}  calls={b.call_count}  errors={b.error_count}")


def cmd_check(_args: argparse.Namespace) -> None:
    """Check compatibility across all declared producer-consumer pairs."""
    boundaries = ContractRegistry().list_all()
    total_violations = checked = 0
    for prod in boundaries:
        if not prod.output_schema or not prod.consumers:
            continue
        for cp in prod.consumers:
            for con in boundaries:
                if con.name == prod.name or con.producer != cp or not con.input_schema:
                    continue
                checked += 1
                for v in check_compatibility(prod.output_schema, con.input_schema, prod.name, con.name):
                    total_violations += 1
                    print(f"  VIOLATION [{v.severity}] {v.producer} -> {v.consumer}: "
                          f"{v.kind} on '{v.field}' -- {v.detail}")
    if total_violations == 0:
        print(f"All clear. Checked {checked} pair(s), 0 violations.")
    else:
        print(f"\n{total_violations} violation(s) across {checked} pair(s).")
        sys.exit(1)


def main() -> None:
    """Entry point for python -m data_contracts."""
    p = argparse.ArgumentParser(prog="data_contracts", description="Typed data contracts")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("list", help="List all registered boundaries")
    sub.add_parser("check", help="Check compatibility across producer-consumer pairs")
    args = p.parse_args()
    cmds = {"list": cmd_list, "check": cmd_check}
    if args.command in cmds:
        cmds[args.command](args)
    else:
        p.print_help()
        sys.exit(1)
