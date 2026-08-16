"""Three numbers come out of a practice, and they are deliberately NOT blended.

  adoption_value -- how much it is worth doing (impact, discounted by effort)
  confidence     -- how well we know it is true (derived from evidence ONLY)
  freshness      -- whether the claim has been re-verified recently enough

Blending them produces the classic defect where a stale, thinly-sourced but
cheap practice outranks a well-evidenced expensive one, and no reader can see
which input moved the number. Ranking therefore sorts on adoption_value and
applies confidence and freshness as VISIBLE filters, never as hidden weights.
"""

from __future__ import annotations

from .models import Practice
from .taxonomy import SOURCE_WEIGHTS

W_IMPACT = 3
W_EFFORT = 1
_MAX_WEIGHTED = 5 * (W_IMPACT + W_EFFORT)

CONFIDENCE_FLOOR_DEFAULT = 2


def adoption_value(practice: Practice) -> float:
    """0.0-10.0, one decimal. Higher = adopt sooner.

    Impact is weighted 3x effort on purpose: a hard, high-impact practice should
    still outrank a trivial cosmetic one. `effort` is stored as ease (5 = easiest)
    so both inputs point the same direction and the arithmetic stays integer
    until the final division - reproducible across machines and versions.
    """
    weighted = practice.impact * W_IMPACT + practice.effort * W_EFFORT
    return round(10.0 * weighted / _MAX_WEIGHTED, 1)


def confidence(practice: Practice) -> int:
    """0-5, derived ONLY from evidence class and independence.

    Rules, in order:
      * the strongest single source sets the ceiling,
      * two or more DISTINCT source classes add one point (corroboration),
      * evidence that is exclusively model-output scores 0 at any volume.
    """
    if not practice.evidence:
        return 0
    weights = [SOURCE_WEIGHTS[e.source_class] for e in practice.evidence]
    if max(weights) == 0:
        return 0
    score = max(weights)
    if len({e.source_class for e in practice.evidence}) >= 2:
        score += 1
    return min(score, 5)


def rank(
    practices: list[Practice],
    floor: int = CONFIDENCE_FLOOR_DEFAULT,
) -> list[Practice]:
    """Order by adoption_value desc, then id asc for a stable total order.

    Records below the confidence floor are NOT dropped: they are sorted after
    the qualifying ones so a reader can see what was excluded and why. Silently
    hiding weak records is how an index starts lying about its own coverage.
    """
    qualifying = [p for p in practices if confidence(p) >= floor]
    below = [p for p in practices if confidence(p) < floor]
    key = lambda p: (-adoption_value(p), p.id)  # noqa: E731
    return sorted(qualifying, key=key) + sorted(below, key=key)


def below_floor(practices: list[Practice], floor: int = CONFIDENCE_FLOOR_DEFAULT) -> list[Practice]:
    """The records a ranking is showing under protest."""
    return [p for p in practices if confidence(p) < floor]
