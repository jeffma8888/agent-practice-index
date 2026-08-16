import pytest
from pydantic import ValidationError

from agent_practice_index.models import Evidence, Practice

GOOD_EV = {
    "source_class": "vendor-primary", "title": "t",
    "locator": "https://example.com/x", "date": "2026-01-01", "quote": "hello",
}


def _practice(**over):
    base = dict(
        id="PRC-001", title="t", area="loop-architecture", kind="pattern",
        maturity="established", statement="do the thing",
        rationale="because", applies_when=["always"], how=["step"],
        check="look", failure_if_absent="bad", impact=3, effort=3,
        evidence=[GOOD_EV], as_of="2026-08-16",
    )
    base.update(over)
    return base


def test_valid_practice():
    Practice.model_validate(_practice())


def test_bad_id_rejected():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(id="P-1"))


def test_unknown_area_rejected():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(area="nonsense"))


def test_empty_quote_rejected():
    ev = dict(GOOD_EV, quote="   ")
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(evidence=[ev]))


def test_nonhttp_locator_rejected():
    ev = dict(GOOD_EV, locator="file:///etc/passwd")
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(evidence=[ev]))


def test_overlong_statement_rejected():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(statement="x" * 401))


def test_superseded_requires_target():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(status="superseded"))


def test_superseded_by_forces_status():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(superseded_by="PRC-002"))


def test_extra_field_forbidden():
    with pytest.raises(ValidationError):
        Practice.model_validate(_practice(surprise="x"))
