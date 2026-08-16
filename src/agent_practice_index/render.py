"""Markdown rendering. stdout carries only the document, so output is pipeable."""

from __future__ import annotations

import datetime as _dt

from .freshness import age_days, due_date, freshness, marker
from .models import Practice
from .scoring import adoption_value, below_floor, confidence, rank
from .taxonomy import AREAS, KINDS, MATURITIES, SOURCE_CLASSES, SOURCE_WEIGHTS


def list_lines(practices: list[Practice], today: _dt.date, floor: int = 2) -> str:
    rows = []
    for practice in rank(practices, floor=floor):
        state = freshness(practice, today)
        flag = "" if state == "fresh" else f" [{marker(state)}]"
        rows.append(
            f"{practice.id}  value {adoption_value(practice):>4}  "
            f"conf {confidence(practice)}  {practice.area:<20} "
            f"{practice.maturity:<14}{flag} {practice.title}")
    return "\n".join(rows) + "\n"


def practice_brief(practice: Practice, today: _dt.date) -> str:
    state = freshness(practice, today)
    out = [
        f"# {practice.id}: {practice.title}",
        "",
        f"- **Area:** {practice.area} ({AREAS[practice.area]})",
        f"- **Kind:** {practice.kind} ({KINDS[practice.kind]})",
        f"- **Maturity:** {practice.maturity} ({MATURITIES[practice.maturity]})",
        f"- **Status:** {practice.status}",
        f"- **Adoption value:** {adoption_value(practice)} / 10 "
        f"(impact {practice.impact}, ease {practice.effort})",
        f"- **Confidence:** {confidence(practice)} / 5 (derived from evidence only)",
        f"- **Verified:** {practice.as_of} ({age_days(practice, today)} days ago); "
        f"review by {due_date(practice).isoformat()} -> {marker(state)}",
        "",
        "## Statement",
        "",
        practice.statement,
        "",
        "## Why it works",
        "",
        practice.rationale,
        "",
        "## Applies when",
        "",
    ]
    out += [f"- {item}" for item in practice.applies_when]
    if practice.not_when:
        out += ["", "## Does NOT apply when", ""]
        out += [f"- {item}" for item in practice.not_when]
    out += ["", "## How to adopt", ""]
    out += [f"{i}. {step}" for i, step in enumerate(practice.how, start=1)]
    out += [
        "",
        "## Verify adoption",
        "",
        practice.check,
        "",
        "## What breaks without it",
        "",
        practice.failure_if_absent,
        "",
        "## Evidence",
        "",
    ]
    for ev in practice.evidence:
        out += [
            f"### {ev.title}",
            "",
            f"- **Class:** {ev.source_class} (weight {SOURCE_WEIGHTS[ev.source_class]})",
            f"- **Date:** {ev.date}",
            f"- **Locator:** {ev.locator}",
            "",
            f"> {ev.quote}",
            "",
        ]
        if ev.note:
            out += [ev.note, ""]
    if practice.supersedes:
        out += [f"Supersedes: {', '.join(practice.supersedes)}", ""]
    if practice.superseded_by:
        out += [f"Superseded by: {practice.superseded_by}", ""]
    if practice.tags:
        out += [f"Tags: {', '.join(practice.tags)}", ""]
    return "\n".join(out)


def index_report(practices: list[Practice], today: _dt.date, floor: int = 2) -> str:
    ordered = rank(practices, floor=floor)
    weak = below_floor(practices, floor=floor)
    stale = [p for p in practices if freshness(p, today) != "fresh"]

    out = [
        "# Agent practice index",
        "",
        f"Generated {today.isoformat()} from {len(practices)} records. "
        f"Ranked by adoption value; confidence floor {floor}.",
        "",
        "| Practice | Value | Conf | Area | Kind | Maturity | Verified |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for p in ordered:
        state = freshness(p, today)
        stamp = p.as_of if state == "fresh" else f"{p.as_of} ({marker(state)})"
        out.append(
            f"| {p.id} {p.title} | {adoption_value(p)} | {confidence(p)} | "
            f"{p.area} | {p.kind} | {p.maturity} | {stamp} |")

    out += ["", "## Statements", ""]
    for p in ordered:
        out.append(f"- **{p.id}** {p.statement}")

    out += ["", "## Coverage by area", ""]
    for area in sorted(AREAS):
        n = len([p for p in practices if p.area == area])
        gap = "" if n else "  <- no records yet"
        out.append(f"- {area}: {n}{gap}")

    if weak:
        out += [
            "",
            "## Below the confidence floor (shown deliberately)",
            "",
            "These records are retained and displayed so the ladder is visibly "
            "enforced rather than decorative. They are ranked last.",
            "",
        ]
        out += [f"- {p.id} (conf {confidence(p)}): {p.title}" for p in weak]

    if stale:
        out += [
            "",
            "## Needs re-verification",
            "",
            "Currency is the product. A record past its horizon is a claim about "
            "the industry that nobody has checked lately.",
            "",
        ]
        out += [
            f"- {p.id} ({marker(freshness(p, today))}, verified {p.as_of}): {p.title}"
            for p in stale
        ]

    out += [
        "",
        "## Evidence base",
        "",
        "| Source class | Weight | Citations |",
        "| --- | --- | --- |",
    ]
    for cls in SOURCE_CLASSES:
        n = sum(1 for p in practices for e in p.evidence if e.source_class == cls)
        out.append(f"| {cls} | {SOURCE_WEIGHTS[cls]} | {n} |")
    return "\n".join(out) + "\n"


def taxonomy_doc() -> str:
    out = [
        "# Taxonomy",
        "",
        "Closed vocabularies. A record that does not fit argues for a new term in "
        "a pull request; it does not invent a free-text label.",
        "",
        "## Areas",
        "",
    ]
    out += [f"- **{k}** - {v}" for k, v in AREAS.items()]
    out += ["", "## Kinds", ""]
    out += [f"- **{k}** - {v}" for k, v in KINDS.items()]
    out += ["", "## Maturity", ""]
    out += [f"- **{k}** - {v}" for k, v in MATURITIES.items()]
    out += [
        "",
        "## Evidence ladder",
        "",
        "Confidence is DERIVED from this table, so a record cannot inflate its own "
        "credibility with confident prose. Strongest first.",
        "",
        "| Source class | Weight |",
        "| --- | --- |",
    ]
    out += [f"| {c} | {SOURCE_WEIGHTS[c]} |" for c in SOURCE_CLASSES]
    out += [
        "",
        "`model-output` carries weight 0 on purpose: an assertion generated by a "
        "language model is a hypothesis to check, never evidence for itself.",
        "",
    ]
    return "\n".join(out)
