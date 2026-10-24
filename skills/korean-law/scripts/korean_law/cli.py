"""Command-line interface for :mod:`korean_law`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from .client import LawAPIError, LawClient, TARGETS


def _parameters(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        key, separator, item = value.partition("=")
        if not separator or not key:
            raise LawAPIError("parameters must use KEY=VALUE")
        if key in result:
            raise LawAPIError(f"parameter {key!r} was provided more than once")
        result[key] = item
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="korean-law", description="Query Korea's official law open API.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="search official law data")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--target", choices=sorted(TARGETS), default="eflaw")
    search.add_argument("--page", type=int, default=1)
    search.add_argument("--display", type=int, default=20)
    search.add_argument("--parameter", "--param", action="append", default=[], metavar="KEY=VALUE")

    detail = subparsers.add_parser("detail", help="fetch one official document")
    detail.add_argument("--target", choices=sorted(TARGETS), required=True)
    identifiers = detail.add_mutually_exclusive_group(required=True)
    identifiers.add_argument("--id", dest="document_id")
    identifiers.add_argument("--mst")
    detail.add_argument("--effective-date")
    detail.add_argument("--article")

    subparsers.add_parser("doctor", help="check local configuration without network access")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = {
                "configured": bool(os.environ.get("LAW_API_OC", "").strip()),
                "environment_variable": "LAW_API_OC",
                "network_checked": False,
            }
        elif args.command == "search":
            result = LawClient().search(
                target=args.target,
                query=args.query,
                page=args.page,
                display=args.display,
                parameters=_parameters(args.parameter),
            )
        else:
            result = LawClient().detail(
                target=args.target,
                document_id=args.document_id,
                mst=args.mst,
                effective_date=args.effective_date,
                article=args.article,
            )
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    except LawAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
