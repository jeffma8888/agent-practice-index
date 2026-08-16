"""`practice audit` - the self-reflection path.

This is what turns a reading list into a feedback loop. An agent working on some
project asks the index: which practices apply to a repo like this, and for each
one, what exactly would I look at to tell whether we already do it?

Deliberate limitation, stated in the output itself: this emits a CHECKLIST, it
does not decide. Machine-deciding adoption from outside a repo would require
guessing at project structure, and a confident wrong answer is worse than an
honest prompt to look. The checks are written so the answer is cheap to obtain.
"""

from __future__ import annotations

import datetime as _dt
import pathlib

from .freshness import freshness, marker
from .models import Practice
from .scoring import adoption_value, confidence, rank

# Signals that a repo is running an autonomous loop rather than a single-shot
# agent. Loop practices are the expensive ones to skip, so they are surfaced
# first when these appear.
LOOP_SIGNALS = (
    "prd.json", "progress.txt", "LEARNINGS.md", "AGENTS.md", "CLAUDE.md",
    "ralph.sh", "foundry.config.json", "tasks.md",
)


def detect_signals(root: pathlib.Path) -> list[str]:
    """Which loop artifacts exist. A hint for ordering, never a verdict."""
    found = []
    for name in LOOP_SIGNALS:
        if (root / name).exists() or list(root.glob(f"**/{name}"))[:1]:
            found.append(name)
    return found


def audit_checklist(
    practices: list[Practice],
    today: _dt.date,
    target: pathlib.Path | None = None,
    area: str | None = None,
    floor: int = 2,
) -> str:
    selected = [p for p in practices if p.status == "active"]
    if area:
        selected = [p for p in selected if p.area == area]
    ordered = rank(selected, floor=floor)

    out = [
        "# Practice self-audit",
        "",
        f"Generated {today.isoformat()} against {len(ordered)} active records"
        + (f", area `{area}`" if area else "")
        + ".",
        "",
        "This is a checklist, not a verdict: each item names the check to run so "
        "the answer comes from the repo rather than from this document.",
        "",
    ]
    if target is not None:
        signals = detect_signals(target)
        out += [
            f"Target: `{target}`",
            "",
            "Loop artifacts detected: "
            + (", ".join(f"`{s}`" for s in signals) if signals else "none"),
            "",
            "Absent artifacts are not automatically a finding - a single-shot agent "
            "needs fewer of them than an unattended loop.",
            "",
        ]
    out += ["| Practice | Value | Statement | Check | Adopted? |",
            "| --- | --- | --- | --- | --- |"]
    for p in ordered:
        state = freshness(p, today)
        flag = "" if state == "fresh" else f" ({marker(state)})"
        statement = p.statement.replace("|", "\\|")
        check = p.check.replace("|", "\\|")
        out.append(
            f"| {p.id}{flag} | {adoption_value(p)} | {statement} | {check} | [ ] |")

    out += [
        "",
        "## How to use this",
        "",
        "1. Work top-down: the table is ordered by adoption value, so the first "
        "unchecked row is the highest-value thing this project is missing.",
        "2. Run the check column. It is written to be answerable with one command "
        "or one file read.",
        "3. For each genuine gap, `practice prd --practice <id>` emits build "
        "stories whose first story is a failing check, so adoption is verifiable "
        "rather than declared.",
        "4. Record the outcome where your agents will read it next iteration, not "
        "in a scratch file they will never open again.",
        "",
        f"Records below confidence {floor} are ranked last: treat them as "
        "candidates to investigate, not as instructions.",
        "",
    ]
    return "\n".join(out)
