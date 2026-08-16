"""The bounded, agent-pinnable digest. This is the primary consumption path.

Why bounding is the hard requirement and not a nicety: a digest is injected
into EVERY iteration of a loop, so its size is a per-iteration tax, and an
unbounded one eventually consumes the step budget it was meant to inform. The
observed failure is worse than slow - the elision is silent, so the consumer
believes it received guidance it never saw.

Two rules follow, and both are implemented here:
  * bound by CHARACTERS, not item count, because item size varies wildly;
  * make every elision VISIBLE in the output, so a reader can tell that the
    digest is incomplete without diffing it against the source.
"""

from __future__ import annotations

import datetime as _dt

from .freshness import freshness, marker
from .models import Practice
from .scoring import adoption_value, confidence, rank

DEFAULT_BUDGET_CHARS = 10_000
DEFAULT_BULLET_CHARS = 800
TRUNCATION_MARKER = " [...]"


def _bullet(practice: Practice, today: _dt.date) -> str:
    state = freshness(practice, today)
    flag = "" if state == "fresh" else f" [{marker(state)}]"
    return (
        f"- **[{practice.id} / {practice.area} / {practice.kind}"
        f" / value {adoption_value(practice)} / conf {confidence(practice)}"
        f" / {practice.maturity}{flag}]** {practice.statement} "
        f"_Check:_ {practice.check}"
    )


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    keep = max(0, limit - len(TRUNCATION_MARKER))
    return text[:keep].rstrip() + TRUNCATION_MARKER, True


def build_digest(
    practices: list[Practice],
    today: _dt.date,
    budget_chars: int = DEFAULT_BUDGET_CHARS,
    bullet_chars: int = DEFAULT_BULLET_CHARS,
    floor: int = 2,
) -> str:
    """Render the digest, applying per-bullet truncation THEN the total budget.

    Order matters: truncating each bullet first means one oversized record
    cannot evict several well-sized ones. Admission is top-down through the
    ranking, so the highest-value practices survive a tight budget, and the
    notice line reports exactly what was lost.
    """
    header = "## Current agent-building practice (generated - do not hand-edit)"
    ordered = rank(practices, floor=floor)

    bullets: list[str] = []
    truncated = 0
    for practice in ordered:
        text, was_cut = _truncate(_bullet(practice, today), bullet_chars)
        truncated += 1 if was_cut else 0
        bullets.append(text)

    admitted: list[str] = []
    used = len(header) + 1
    dropped = 0
    for text in bullets:
        cost = len(text) + 1
        if used + cost > budget_chars:
            dropped += 1
            continue
        admitted.append(text)
        used += cost

    notice = (
        f"> [digest bounded: {len(admitted)} of {len(bullets)} bullets shown, "
        f"{truncated} truncated, {dropped} dropped, as of {today.isoformat()}]"
    )
    return "\n".join([header, notice, *admitted]) + "\n"
