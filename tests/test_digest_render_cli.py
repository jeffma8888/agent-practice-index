import datetime as _dt
import pathlib

from agent_practice_index.audit import audit_checklist
from agent_practice_index.cli import main
from agent_practice_index.digest import build_digest
from agent_practice_index.prd import build_prd
from agent_practice_index.registry import load_all, practices_dir
from agent_practice_index.render import index_report, practice_brief
from agent_practice_index.scoring import rank

REPO = pathlib.Path(__file__).resolve().parents[1]
TODAY = _dt.date(2026, 8, 16)


def _load():
    return load_all(practices_dir(REPO))


def test_digest_respects_char_budget():
    ps = _load()
    out = build_digest(ps, TODAY, budget_chars=1500, bullet_chars=300)
    assert len(out) <= 1500 + 200  # header+notice slack
    assert "digest bounded" in out


def test_digest_reports_drops_visibly():
    ps = _load()
    tiny = build_digest(ps, TODAY, budget_chars=400, bullet_chars=200)
    assert "dropped" in tiny


def test_digest_per_bullet_truncation_marker():
    ps = _load()
    out = build_digest(ps, TODAY, budget_chars=100000, bullet_chars=60)
    assert "[...]" in out


def test_every_statement_survives_default_bullet_budget():
    # A statement is capped at 400 and the default bullet budget is 800, so no
    # record's statement should ever be the thing that gets truncated.
    ps = _load()
    for p in ps:
        assert len(p.statement) <= 400


def test_report_lists_all_and_shows_coverage():
    ps = _load()
    rep = index_report(ps, TODAY)
    for p in ps:
        assert p.id in rep
    assert "Coverage by area" in rep
    assert "Evidence base" in rep


def test_brief_contains_evidence_quote():
    ps = _load()
    p = rank(ps)[0]
    brief = practice_brief(p, TODAY)
    assert p.evidence[0].quote in brief
    assert "Verify adoption" in brief


def test_audit_checklist_is_a_checklist_not_a_verdict():
    ps = _load()
    out = audit_checklist(ps, TODAY, target=REPO)
    assert "checklist, not a verdict" in out
    assert "[ ]" in out  # unchecked boxes


def test_prd_first_story_demonstrates_gap():
    ps = _load()
    prd = build_prd(rank(ps)[0])
    assert prd["userStories"][0]["id"] == "US-001"
    assert "gap" in prd["userStories"][0]["title"].lower()
    assert prd["branchName"].startswith("practice/")


def test_cli_validate_ok(capsys):
    rc = main(["validate", str(REPO)])
    assert rc == 0
    assert "valid" in capsys.readouterr().out


def test_cli_unknown_area_errors(capsys):
    rc = main(["list", str(REPO), "--area", "nope"])
    assert rc == 2
    assert "Error:" in capsys.readouterr().err


def test_cli_stale_fail_flag(capsys):
    # Far-future date forces everything stale; --fail-if-stale should exit 1.
    rc = main(["stale", str(REPO), "--today", "2099-01-01", "--fail-if-stale"])
    assert rc == 1


def test_cli_digest_runs(capsys):
    rc = main(["digest", str(REPO), "--today", "2026-08-16"])
    assert rc == 0
    assert "Current agent-building practice" in capsys.readouterr().out


def test_cli_taxonomy_runs(capsys):
    rc = main(["taxonomy"])
    assert rc == 0
    assert "Evidence ladder" in capsys.readouterr().out
