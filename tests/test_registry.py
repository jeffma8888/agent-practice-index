"""The register itself must be trustworthy; these tests are the guarantee."""
import json
import pathlib

import pytest

from agent_practice_index.registry import (
    RegistryError, find, load_all, load_one, practices_dir,
)

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_all_records_load_and_validate(practices):
    assert len(practices) >= 11


def test_ids_are_sequential_no_gaps(practices):
    nums = sorted(int(p.id.split("-")[1]) for p in practices)
    assert nums == list(range(1, len(nums) + 1))


def test_filename_starts_with_id():
    for path in practices_dir(REPO).glob("PRC-*.json"):
        rec = load_one(path)
        assert path.name.startswith(rec.id)


def test_every_quote_is_present_and_nonempty(practices):
    for p in practices:
        assert p.evidence
        for ev in p.evidence:
            assert ev.quote.strip()
            assert ev.locator.startswith("http")


def test_duplicate_id_rejected(tmp_path):
    d = tmp_path / "practices"
    d.mkdir()
    base = json.loads(next(practices_dir(REPO).glob("PRC-001*.json")).read_text())
    (d / "PRC-001-a.json").write_text(json.dumps(base))
    dup = dict(base)
    (d / "PRC-001-b.json").write_text(json.dumps(dup))
    with pytest.raises(RegistryError):
        load_all(d)


def test_gap_in_ids_rejected(tmp_path):
    d = tmp_path / "practices"
    d.mkdir()
    src = sorted(practices_dir(REPO).glob("PRC-*.json"))[:2]
    first = json.loads(src[0].read_text())
    second = json.loads(src[1].read_text())
    second["id"] = "PRC-005"  # gap
    (d / "PRC-001-x.json").write_text(json.dumps(first))
    (d / "PRC-005-y.json").write_text(json.dumps(second))
    with pytest.raises(RegistryError):
        load_all(d)


def test_find_missing_raises(practices):
    with pytest.raises(RegistryError):
        find(practices, "PRC-999")
