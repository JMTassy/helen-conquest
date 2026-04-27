"""HELEN OS CLI entry point.

Usage:
  python -m helen_os.cli.helen init
  python -m helen_os.cli.helen start-session
  python -m helen_os.cli.helen propose-shell "ls"
  python -m helen_os.cli.helen replay
  python -m helen_os.cli.helen inspect
  python -m helen_os.cli.helen terminate --verdict NO_SHIP
"""
from __future__ import annotations

import argparse
import sys

from helen_os.cli import commands


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="helen")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("start-session")
    sp = sub.add_parser("propose-shell")
    sp.add_argument("command")
    sub.add_parser("replay")
    sub.add_parser("inspect")
    st = sub.add_parser("terminate")
    st.add_argument("--verdict", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return commands.dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
