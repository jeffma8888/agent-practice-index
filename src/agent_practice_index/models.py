"""Schema for a practice record. Validation is this project's first quality gate.

Two design choices are deliberate and worth defending:

1. `statement` is imperative and standalone. An agent that reads ONLY the
   statement must still be able to act correctly, because in a bounded prompt
   digest the statement is often all that survives.
2. `check` is required. A practice nobody can verify adoption of is an opinion.
   The check is what lets `practice audit` tell an agent whether its own
   project already follows this, which is the difference between advice and a
   feedback loop.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .taxonomy import (
    AREAS,
    DEFAULT_REVIEW_DAYS,
    KINDS,
    MATURITIES,
    SOURCE_CLASSES,
    STATUSES,
)

PRACTICE_ID_RE = re.compile(r"^PRC-\d{3}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_STATEMENT = 400


class Evidence(BaseModel):
    """One citation. Every field here is checkable by a reader, on purpose."""

    model_config = ConfigDict(extra="forbid")

    source_class: str
    title: str
    locator: str = Field(description="URL, DOI, or stable public artifact path.")
    date: str = Field(description="ISO date the source was published or last updated.")
    quote: str = Field(description="VERBATIM excerpt from the source. Never a paraphrase.")
    note: str = ""

    @field_validator("source_class")
    @classmethod
    def _known_source(cls, v: str) -> str:
        if v not in SOURCE_CLASSES:
            raise ValueError(f"unknown source_class {v!r}; allowed: {SOURCE_CLASSES}")
        return v

    @field_validator("date")
    @classmethod
    def _iso_date(cls, v: str) -> str:
        if not ISO_DATE_RE.match(v):
            raise ValueError(f"date must be YYYY-MM-DD, got {v!r}")
        return v

    @field_validator("quote")
    @classmethod
    def _quote_present(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "quote must not be empty: a citation a reader cannot check against "
                "the source is indistinguishable from an invented one")
        return v

    @field_validator("locator")
    @classmethod
    def _locator_shape(cls, v: str) -> str:
        if not (v.startswith("https://") or v.startswith("http://")):
            raise ValueError(f"locator must be a resolvable http(s) URL, got {v!r}")
        return v


class Practice(BaseModel):
    """One current-industry practice for building agent systems."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    area: str
    kind: str
    status: str = "active"
    maturity: str

    statement: str = Field(
        description="The practice as a single imperative sentence, standalone.")
    rationale: str = Field(description="Why it works, in mechanism terms.")
    applies_when: list[str] = Field(
        min_length=1,
        description="Conditions under which this is the right default.")
    not_when: list[str] = Field(
        default_factory=list,
        description="Where it does NOT apply. Absent scope is how practices get cargo-culted.")
    how: list[str] = Field(min_length=1, description="Concrete adoption steps.")
    check: str = Field(
        description="How to verify adoption mechanically, in one sentence.")
    failure_if_absent: str = Field(
        description="What goes wrong when this practice is missing.")

    impact: int = Field(ge=1, le=5, description="How much outcomes change when adopted.")
    effort: int = Field(ge=1, le=5, description="Cost to adopt; 5 = cheapest/easiest.")

    evidence: list[Evidence] = Field(min_length=1)

    as_of: str = Field(description="ISO date this record was last verified current.")
    review_days: int = Field(
        default=DEFAULT_REVIEW_DAYS, ge=1,
        description="Re-verify after this many days; currency is the product here.")

    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str = ""
    tags: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_shape(cls, v: str) -> str:
        if not PRACTICE_ID_RE.match(v):
            raise ValueError(f"id must look like PRC-001, got {v!r}")
        return v

    @field_validator("area")
    @classmethod
    def _known_area(cls, v: str) -> str:
        if v not in AREAS:
            raise ValueError(f"unknown area {v!r}; allowed: {sorted(AREAS)}")
        return v

    @field_validator("kind")
    @classmethod
    def _known_kind(cls, v: str) -> str:
        if v not in KINDS:
            raise ValueError(f"unknown kind {v!r}; allowed: {sorted(KINDS)}")
        return v

    @field_validator("maturity")
    @classmethod
    def _known_maturity(cls, v: str) -> str:
        if v not in MATURITIES:
            raise ValueError(f"unknown maturity {v!r}; allowed: {sorted(MATURITIES)}")
        return v

    @field_validator("status")
    @classmethod
    def _known_status(cls, v: str) -> str:
        if v not in STATUSES:
            raise ValueError(f"unknown status {v!r}; allowed: {STATUSES}")
        return v

    @field_validator("as_of")
    @classmethod
    def _iso_as_of(cls, v: str) -> str:
        if not ISO_DATE_RE.match(v):
            raise ValueError(f"as_of must be YYYY-MM-DD, got {v!r}")
        return v

    @field_validator("statement")
    @classmethod
    def _statement_bounded(cls, v: str) -> str:
        text = v.strip()
        if not text:
            raise ValueError("statement must not be empty")
        if len(text) > _MAX_STATEMENT:
            raise ValueError(
                f"statement must be <= {_MAX_STATEMENT} chars (it has {len(text)}); "
                "a statement that does not survive a bounded digest is not usable "
                "by the consumer it was written for")
        return text

    @model_validator(mode="after")
    def _superseded_consistency(self) -> "Practice":
        if self.status == "superseded" and not self.superseded_by:
            raise ValueError(
                "a superseded practice must name superseded_by, otherwise a reader "
                "cannot find the replacement")
        if self.superseded_by and self.status != "superseded":
            raise ValueError(
                f"superseded_by is set but status is {self.status!r}; set status "
                "to 'superseded'")
        if self.superseded_by and not PRACTICE_ID_RE.match(self.superseded_by):
            raise ValueError(
                f"superseded_by must be a practice id like PRC-002, got "
                f"{self.superseded_by!r}")
        for ref in self.supersedes:
            if not PRACTICE_ID_RE.match(ref):
                raise ValueError(f"supersedes entries must be practice ids, got {ref!r}")
        return self
