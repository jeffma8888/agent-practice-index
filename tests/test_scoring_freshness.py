import datetime as _dt

from agent_practice_index.freshness import (
    DUE, FRESH, STALE, due_date, freshness, needs_review,
)
from agent_practice_index.models import Practice
from agent_practice_index.scoring import (
    adoption_value, below_floor, confidence, rank,
)

EV_STRONG = {"source_class": "first-party-field", "title": "t",
             "locator": "https://e.com", "date": "2026-01-01", "quote": "q"}
EV_WEAK = {"source_class": "secondary-summary", "title": "t",
           "locator": "https://e.com", "date": "2026-01-01", "quote": "q"}
EV_MODEL = {"source_class": "model-output", "title": "t",
            "locator": "https://e.com", "date": "2026-01-01", "quote": "q"}


def _p(pid="PRC-001", impact=3, effort=3, evidence=None, as_of="2026-08-16",
       review_days=180):
    return Practice.model_validate(dict(
        id=pid, title="t", area="loop-architecture", kind="pattern",
        maturity="established", statement="s", rationale="r",
        applies_when=["a"], how=["h"], check="c", failure_if_absent="f",
        impact=impact, effort=effort, evidence=evidence or [EV_STRONG],
        as_of=as_of, review_days=review_days))


def test_adoption_value_bounds():
    assert adoption_value(_p(impact=5, effort=5)) == 10.0
    assert adoption_value(_p(impact=1, effort=1)) == 2.0


def test_impact_weighted_over_effort():
    hi_impact = adoption_value(_p(impact=5, effort=1))
    hi_effort = adoption_value(_p(impact=1, effort=5))
    assert hi_impact > hi_effort


def test_confidence_model_output_is_zero():
    assert confidence(_p(evidence=[EV_MODEL])) == 0


def test_confidence_corroboration_adds_point():
    single = confidence(_p(evidence=[EV_WEAK]))
    two = confidence(_p(evidence=[EV_WEAK, dict(EV_STRONG)]))
    assert two > single


def test_rank_below_floor_sorted_last():
    strong = _p(pid="PRC-001", impact=1, effort=1, evidence=[EV_STRONG])
    weak = _p(pid="PRC-002", impact=5, effort=5, evidence=[EV_MODEL])
    ordered = rank([weak, strong], floor=2)
    # weak has higher value but is below floor -> must sort after strong
    assert ordered[-1].id == "PRC-002"
    assert below_floor([weak, strong], floor=2) == [weak]


def test_freshness_states():
    today = _dt.date(2026, 8, 16)
    fresh = _p(as_of="2026-08-01", review_days=180)
    assert freshness(fresh, today) == FRESH
    due = _p(as_of="2026-01-01", review_days=180)  # due 2026-06-30, within grace
    assert freshness(due, today) == DUE
    stale = _p(as_of="2025-01-01", review_days=180)
    assert freshness(stale, today) == STALE


def test_needs_review_orders_oldest_first():
    today = _dt.date(2026, 8, 16)
    a = _p(pid="PRC-001", as_of="2025-01-01", review_days=30)
    b = _p(pid="PRC-002", as_of="2025-06-01", review_days=30)
    flagged = needs_review([b, a], today)
    assert [p.id for p in flagged] == ["PRC-001", "PRC-002"]


def test_due_date_math():
    p = _p(as_of="2026-01-01", review_days=100)
    assert due_date(p) == _dt.date(2026, 4, 11)
