"""Cross-repo integration surfaces: from-rules ingest and gap:GAP tag links."""
import json
import pathlib

import pytest
from pydantic import ValidationError

from agent_practice_index.cli import main
from agent_practice_index.ingest import (
    DRAFT_MARKER, SourcePractice, already_covered, draft_record, is_draft, parse_rules,
)
from agent_practice_index.models import Practice
from agent_practice_index.registry import load_all, practices_dir

REPO = pathlib.Path(__file__).resolve().parents[1]

SAMPLE_RULES = """# Rules

## Rules from incidents

- **[INC-0001 / high]** something.

## Practices

Cross-incident best practice.

- **[PRA-0001]** First practice text here.
  - _derived from:_ INC-0001, INC-0002
- **[PRA-0002]** Second practice text.
  - _derived from:_ INC-0003

## Something after
- **[PRA-9999]** must NOT be parsed, wrong section.
"""


def test_parse_rules_extracts_only_practices_section():
    got = parse_rules(SAMPLE_RULES)
    assert [s.source_id for s in got] == ["PRA-0001", "PRA-0002"]
    assert got[0].incidents == ("INC-0001", "INC-0002")
    assert got[1].text == "Second practice text."


def test_parse_rules_no_section_returns_empty():
    assert parse_rules("# Rules\n\nnothing here\n") == []


def test_draft_fails_validation_until_completed():
    src = SourcePractice("PRA-0001", "Do the thing.", ("INC-0001",))
    d = draft_record(src, "PRC-099", "https://example.com/RULES.md", "2026-09-04")
    assert is_draft(d)
    with pytest.raises(ValidationError):
        Practice.model_validate(d)  # DRAFT marker in check is rejected by schema


def test_completed_draft_validates():
    src = SourcePractice("PRA-0001", "Do the thing.", ("INC-0001",))
    d = draft_record(src, "PRC-099", "https://example.com/RULES.md", "2026-09-04")
    d["title"] = "Do the thing"
    d["check"] = "Look at X and confirm Y."
    d["rationale"] = "because"
    d["applies_when"] = ["always"]
    d["how"] = ["step"]
    d["failure_if_absent"] = "bad"
    d["evidence"][0]["note"] = ""
    Practice.model_validate(d)


def test_already_covered_uses_source_tag():
    ps = load_all(practices_dir(REPO))
    covered = SourcePractice("PRA-0003", "x", ())
    uncovered = SourcePractice("PRA-0001", "x", ())
    assert already_covered(covered, ps)
    assert not already_covered(uncovered, ps)


def test_draft_quote_is_source_text_verbatim():
    src = SourcePractice("PRA-0007", "Exact words matter.", ())
    d = draft_record(src, "PRC-050", "https://e.com", "2026-09-04")
    assert d["evidence"][0]["quote"] == "Exact words matter."


def test_gap_link_tags_resolve_to_real_gap_ids():
    """Every gap:GAP-NNN tag must be well-formed; the id is the cross-repo key."""
    import re
    ps = load_all(practices_dir(REPO))
    tags = [t for p in ps for t in p.tags if t.startswith("gap:")]
    assert tags, "expected at least one gap link in the seed register"
    for t in tags:
        assert re.fullmatch(r"gap:GAP-\d{3}", t), t


def test_cli_tag_filter(capsys):
    rc = main(["list", str(REPO), "--tag", "gap:GAP-003", "--today", "2026-09-04"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PRC-007" in out and "PRC-008" in out
    assert "PRC-001" not in out


def test_cli_from_rules_on_sample(tmp_path, capsys):
    rules = tmp_path / "RULES.md"
    rules.write_text(SAMPLE_RULES, encoding="utf-8")
    rc = main(["from-rules", str(rules), str(REPO), "--today", "2026-09-04"])
    assert rc == 0
    drafts = json.loads(capsys.readouterr().out)
    assert len(drafts) == 2
    assert all(is_draft(d) for d in drafts)
    assert drafts[0]["id"] == "PRC-013"  # next after the 12 seed records


def test_cli_from_rules_missing_file(capsys):
    rc = main(["from-rules", "/nonexistent/RULES.md", str(REPO)])
    assert rc == 2
