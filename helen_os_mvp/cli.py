#!/usr/bin/env python3
# HELEN OS MVP CLI

import argparse
import os
import sys

from router import run_pipeline, chat_loop


def main():
    parser = argparse.ArgumentParser(description="HELEN OS MVP")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="Run planner->worker->critic pipeline")
    p_run.add_argument("prompt", type=str)

    sub.add_parser("chat", help="Start interactive chat")

    args = parser.parse_args()
    if args.cmd == "run":
        out = run_pipeline(args.prompt)
        print(out)
        return 0
    if args.cmd == "chat":
        chat_loop()
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
