"""practice -- command line entry point.

Conventions: errors go to stderr prefixed with "Error: " and exit 2; stdout
carries only the document so every command is pipeable. `--today` exists on
every date-sensitive command so behaviour is reproducible in tests and in CI,
where "now" must never change the output.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import sys

from . import __version__
from .audit import audit_checklist
from .digest import DEFAULT_BUDGET_CHARS, DEFAULT_BULLET_CHARS, build_digest
from .freshness import due_date, freshness, marker, needs_review
from .prd import render_prd
from .registry import RegistryError, find, load_all, practices_dir
from .render import index_report, list_lines, practice_brief, taxonomy_doc
from .scoring import adoption_value, confidence, rank
from .taxonomy import AREAS


def _resolve(path_arg: str) -> pathlib.Path:
    """Accept either a repo root (containing practices/) or the practices dir."""
    p = pathlib.Path(path_arg).expanduser()
    candidate = practices_dir(p)
    return candidate if candidate.is_dir() else p


def _fail(msg: str) -> int:
    sys.stderr.write(f"Error: {msg}\n")
    return 2


def _today(value: str | None) -> _dt.date:
    if value is None:
        return _dt.date.today()
    try:
        return _dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"--today must be YYYY-MM-DD: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="practice",
        description="Evidence-graded, freshness-tracked index of current "
                    "industry practice for building AI agent systems.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")

    def add_common(p: argparse.ArgumentParser, dated: bool = True,
                   floored: bool = True) -> None:
        p.add_argument("path", nargs="?", default=".")
        if dated:
            p.add_argument("--today", default=None,
                           help="ISO date to evaluate freshness against")
        if floored:
            p.add_argument("--floor", type=int, default=2,
                           help="confidence floor for ranking (default 2)")

    add_common(sub.add_parser("validate", help="Validate every record; exit 2 on any problem."),
               dated=False, floored=False)
    p_list = sub.add_parser("list", help="One line per practice, ranked.")
    add_common(p_list)
    p_list.add_argument("--area", default=None, help="restrict to one area")
    p_report = sub.add_parser("report", help="Full index report (markdown).")
    add_common(p_report)
    p_report.add_argument("--area", default=None, help="restrict to one area")

    p_show = sub.add_parser("show", help="Full brief for one practice (markdown).")
    p_show.add_argument("practice_id")
    add_common(p_show, floored=False)

    p_digest = sub.add_parser(
        "digest", help="Bounded, agent-pinnable digest (the primary consumption path).")
    add_common(p_digest)
    p_digest.add_argument("--max-chars", type=int, default=DEFAULT_BUDGET_CHARS)
    p_digest.add_argument("--max-per-bullet", type=int, default=DEFAULT_BULLET_CHARS)

    p_stale = sub.add_parser("stale", help="Records at or past their review horizon.")
    add_common(p_stale, floored=False)
    p_stale.add_argument("--fail-if-stale", action="store_true",
                         help="exit 1 if any record needs review (for CI)")

    p_audit = sub.add_parser(
        "audit", help="Self-audit checklist for a target project.")
    add_common(p_audit)
    p_audit.add_argument("--target", default=None,
                         help="repo to audit (only used to note detected artifacts)")
    p_audit.add_argument("--area", default=None, help="restrict to one area")

    p_prd = sub.add_parser("prd", help="Emit a build-loop prd.json to adopt a practice.")
    add_common(p_prd, floored=False)
    p_prd.add_argument("--practice", dest="practice_id", default=None,
                       help="practice id (default: top-ranked active record)")
    p_prd.add_argument("--project", default="target-project")

    sub.add_parser("taxonomy", help="Print the closed vocabularies and evidence ladder.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    if args.command == "taxonomy":
        sys.stdout.write(taxonomy_doc())
        return 0

    try:
        today = _today(getattr(args, "today", None))
    except ValueError as exc:
        return _fail(str(exc))

    area = getattr(args, "area", None)
    if area and area not in AREAS:
        return _fail(f"unknown area {area!r}; allowed: {sorted(AREAS)}")

    try:
        practices = load_all(_resolve(args.path))
    except RegistryError as exc:
        return _fail(str(exc))

    floor = getattr(args, "floor", 2)

    if args.command == "validate":
        sys.stdout.write(
            f"OK: {len(practices)} records valid; ids sequential; "
            f"{sum(len(p.evidence) for p in practices)} citations.\n")
        return 0

    # area is validated above; None means no restriction.
    scoped = [p for p in practices if p.area == area] if area else practices

    if args.command == "list":
        sys.stdout.write(list_lines(scoped, today, floor=floor))
        return 0

    if args.command == "report":
        sys.stdout.write(index_report(scoped, today, floor=floor))
        return 0

    if args.command == "show":
        try:
            practice = find(practices, args.practice_id)
        except RegistryError as exc:
            return _fail(str(exc))
        sys.stdout.write(practice_brief(practice, today))
        return 0

    if args.command == "digest":
        sys.stdout.write(build_digest(
            practices, today, budget_chars=args.max_chars,
            bullet_chars=args.max_per_bullet, floor=floor))
        return 0

    if args.command == "stale":
        flagged = needs_review(practices, today)
        if not flagged:
            sys.stdout.write(f"OK: all {len(practices)} records within their "
                             f"review horizon as of {today.isoformat()}.\n")
            return 0
        for p in flagged:
            sys.stdout.write(
                f"{p.id}  {marker(freshness(p, today)):<11} verified {p.as_of}  "
                f"due {due_date(p).isoformat()}  {p.title}\n")
        return 1 if args.fail_if_stale else 0

    if args.command == "audit":
        target = pathlib.Path(args.target).expanduser() if args.target else None
        if target is not None and not target.is_dir():
            return _fail(f"target {target} is not a directory")
        sys.stdout.write(audit_checklist(
            practices, today, target=target, area=area, floor=floor))
        return 0

    if args.command == "prd":
        active = [p for p in practices if p.status == "active"]
        if args.practice_id:
            try:
                practice = find(practices, args.practice_id)
            except RegistryError as exc:
                return _fail(str(exc))
        else:
            if not active:
                return _fail("no active records to build a prd from")
            practice = rank(active)[0]
        sys.stdout.write(render_prd(practice, args.project))
        return 0

    return _fail(f"unhandled command {args.command!r}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
