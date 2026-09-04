"""Ingest cross-incident practices from a sibling register.

`agent-failure-modes` distils incidents into a `## Practices` section of its
RULES.md, one `- **[PRA-NNNN]** text` bullet followed by a `_derived from:_`
line naming incidents. Those are exactly the statements this index exists to
hold - but with the crucial difference that THERE the evidence is the incidents,
and HERE every claim must carry a resolvable citation and a mechanical check.

So this module does the honest half of the job: it parses the source, works out
which practices are not yet represented, and emits DRAFT records that a person
or agent completes. It does not write into practices/. A draft is marked as such
in three places (title, check, note) precisely so that it cannot be mistaken
for a finished record if someone commits it unread: the schema will reject a
draft whose `check` still contains the marker.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Practice

DRAFT_MARKER = "DRAFT-FROM-INCIDENT-RULES"

_HEADER_RE = re.compile(r"^## Practices\s*$", re.MULTILINE)
_NEXT_SECTION_RE = re.compile(r"^## ", re.MULTILINE)
_BULLET_RE = re.compile(
    r"^- \*\*\[(?P<id>PRA-\d{4})\]\*\*\s+(?P<text>.+?)\s*$", re.MULTILINE)
_DERIVED_RE = re.compile(r"^\s+- _derived from:_\s*(?P<incidents>.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class SourcePractice:
    source_id: str
    text: str
    incidents: tuple[str, ...]


def parse_rules(text: str) -> list[SourcePractice]:
    """Extract PRA bullets from a RULES.md. Empty list if no Practices section."""
    m = _HEADER_RE.search(text)
    if not m:
        return []
    body = text[m.end():]
    nxt = _NEXT_SECTION_RE.search(body)
    if nxt:
        body = body[:nxt.start()]

    out: list[SourcePractice] = []
    bullets = list(_BULLET_RE.finditer(body))
    for i, b in enumerate(bullets):
        end = bullets[i + 1].start() if i + 1 < len(bullets) else len(body)
        chunk = body[b.end():end]
        d = _DERIVED_RE.search(chunk)
        incidents = tuple(
            s.strip() for s in d.group("incidents").split(",") if s.strip()
        ) if d else ()
        out.append(SourcePractice(b.group("id"), b.group("text").strip(), incidents))
    return out


def already_covered(source: SourcePractice, practices: list[Practice]) -> bool:
    """A source practice is covered when an index record cites it by id in tags."""
    tag = source.source_id.lower()
    return any(tag in (t.lower() for t in p.tags) for p in practices)


def draft_record(source: SourcePractice, next_id: str, rules_locator: str,
                 as_of: str) -> dict:
    """A schema-shaped draft. Deliberately fails validation until completed."""
    statement = source.text if len(source.text) <= 400 else source.text[:397] + "..."
    return {
        "id": next_id,
        "title": f"{DRAFT_MARKER}: {source.source_id}",
        "area": "verification-gates",
        "kind": "guardrail",
        "maturity": "emerging",
        "statement": statement,
        "rationale": "TODO: state the mechanism in one or two sentences.",
        "applies_when": ["TODO"],
        "not_when": [],
        "how": ["TODO: concrete adoption step"],
        "check": f"{DRAFT_MARKER}: replace with a one-sentence mechanical check.",
        "failure_if_absent": "TODO",
        "impact": 3,
        "effort": 3,
        "evidence": [{
            "source_class": "incident-postmortem",
            "title": f"agent-failure-modes {source.source_id} "
                     f"(derived from {', '.join(source.incidents) or 'unspecified'})",
            "locator": rules_locator,
            "date": as_of,
            "quote": source.text,
            "note": f"{DRAFT_MARKER}: quote is the source bullet verbatim; keep it.",
        }],
        "as_of": as_of,
        "tags": [source.source_id.lower(), "from-incident-rules"],
    }


def is_draft(record: dict) -> bool:
    return DRAFT_MARKER in str(record.get("check", "")) or \
        DRAFT_MARKER in str(record.get("title", ""))
