"""Freshness is the reason this index exists, so it is computed, not asserted.

Every function here takes `today` explicitly. That is not ceremony: a function
that reads the clock internally cannot be tested deterministically, and a
freshness rule nobody can test is exactly the kind of rule that silently stops
working. Callers pass a date; the CLI defaults it to the system date once, at
the edge.
"""

from __future__ import annotations

import datetime as _dt

from .models import Practice

FRESH = "fresh"
DUE = "due"
STALE = "stale"

# A record is DUE at its review horizon and STALE once it is a further
# grace period past it. The gap exists so a routine refresh has a window
# to happen in before the record starts being reported as untrustworthy.
STALE_GRACE_DAYS = 90


def parse_date(value: str) -> _dt.date:
    return _dt.date.fromisoformat(value)


def age_days(practice: Practice, today: _dt.date) -> int:
    """Days since the record was last verified. Negative dates are a data bug,
    so surface them rather than clamping to zero."""
    return (today - parse_date(practice.as_of)).days


def due_date(practice: Practice) -> _dt.date:
    return parse_date(practice.as_of) + _dt.timedelta(days=practice.review_days)


def freshness(practice: Practice, today: _dt.date) -> str:
    """One of fresh / due / stale."""
    due = due_date(practice)
    if today <= due:
        return FRESH
    if today <= due + _dt.timedelta(days=STALE_GRACE_DAYS):
        return DUE
    return STALE


def needs_review(practices: list[Practice], today: _dt.date) -> list[Practice]:
    """Records at or past their review horizon, oldest verification first."""
    flagged = [p for p in practices if freshness(p, today) in (DUE, STALE)]
    return sorted(flagged, key=lambda p: (p.as_of, p.id))


def marker(state: str) -> str:
    """Short, greppable label for rendered output."""
    return {FRESH: "fresh", DUE: "REVIEW-DUE", STALE: "STALE"}[state]
