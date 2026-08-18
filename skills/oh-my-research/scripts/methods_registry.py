#!/usr/bin/env python3
"""THINK methods registry loader."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def methods_csv() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "think" / "methods.csv"


def load_methods() -> list[dict[str, str]]:
    with methods_csv().open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def find_method(query: str) -> dict[str, str] | None:
    q = normalize(query)
    for row in load_methods():
        if q in normalize(row["method_name"]) or q == normalize(row["method_name"].replace(" ", "-")):
            return row
    return None


def offer(n: int = 5, priority: str = "core", exclude: list[str] | None = None) -> list[dict[str, str]]:
    exclude_n = {normalize(x) for x in (exclude or [])}
    rows = [r for r in load_methods() if r.get("research_priority") == priority]
    rows = [r for r in rows if normalize(r["method_name"]) not in exclude_n]
    random.shuffle(rows)
    return rows[:n]


def main() -> None:
    p = argparse.ArgumentParser(description="OMR THINK methods registry")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    o = sub.add_parser("offer")
    o.add_argument("-n", type=int, default=5)
    o.add_argument("--priority", default="core", choices=["core", "reshuffle"])
    o.add_argument("--exclude", nargs="*", default=[])
    f = sub.add_parser("find")
    f.add_argument("query")
    args = p.parse_args()
    if args.cmd == "list":
        for r in load_methods():
            print(f"{r['research_priority']:9} {r['method_name']}")
    elif args.cmd == "offer":
        for i, r in enumerate(offer(args.n, args.priority, args.exclude), 1):
            print(f"{i}. {r['method_name']} — {r['description'][:80]}…")
            print(f"   pattern: {r['output_pattern']}")
    elif args.cmd == "find":
        m = find_method(args.query)
        if not m:
            raise SystemExit(f"No method matching: {args.query}")
        print(f"{m['method_name']}\n{m['description']}\npattern: {m['output_pattern']}")


if __name__ == "__main__":
    main()
