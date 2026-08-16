"""Loading and validating the on-disk register.

Errors here are deliberately loud and specific: this repo's whole value is that
a consumer can trust the records, so a malformed record must fail the build
rather than be skipped. A registry that quietly ignores a bad file teaches its
users that validation passed when it did not.
"""

from __future__ import annotations

import json
import pathlib

from pydantic import ValidationError

from .models import Practice

PRACTICES_DIRNAME = "practices"


class RegistryError(Exception):
    """Raised when the register cannot be trusted as loaded."""


def practices_dir(root: pathlib.Path) -> pathlib.Path:
    return root / PRACTICES_DIRNAME


def _record_files(directory: pathlib.Path) -> list[pathlib.Path]:
    if not directory.is_dir():
        raise RegistryError(f"no practices directory at {directory}")
    return sorted(directory.glob("PRC-*.json"))


def load_one(path: pathlib.Path) -> Practice:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryError(f"{path.name}: invalid JSON ({exc})") from exc
    try:
        practice = Practice.model_validate(raw)
    except ValidationError as exc:
        raise RegistryError(f"{path.name}: {exc}") from exc
    if not path.name.startswith(practice.id):
        raise RegistryError(
            f"{path.name}: filename must start with the record id {practice.id!r} "
            "so a reader can find a record by id without opening every file")
    return practice


def load_all(directory: pathlib.Path) -> list[Practice]:
    """Load every record, then assert register-level invariants."""
    files = _record_files(directory)
    if not files:
        raise RegistryError(f"no PRC-*.json records found in {directory}")
    practices = [load_one(p) for p in files]

    seen: dict[str, str] = {}
    for practice, path in zip(practices, files):
        if practice.id in seen:
            raise RegistryError(
                f"duplicate id {practice.id} in {path.name} and {seen[practice.id]}")
        seen[practice.id] = path.name

    numbers = sorted(int(p.id.split("-")[1]) for p in practices)
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        missing = sorted(set(expected) - set(numbers))
        raise RegistryError(
            f"ids must be strictly sequential from PRC-001 with no gaps; "
            f"missing {missing or 'none'}, got {numbers}")

    known = {p.id for p in practices}
    for practice in practices:
        for ref in practice.supersedes:
            if ref not in known:
                raise RegistryError(
                    f"{practice.id}: supersedes unknown record {ref}")
        if practice.superseded_by and practice.superseded_by not in known:
            raise RegistryError(
                f"{practice.id}: superseded_by unknown record {practice.superseded_by}")
        if practice.superseded_by == practice.id:
            raise RegistryError(f"{practice.id}: cannot supersede itself")
    return practices


def find(practices: list[Practice], practice_id: str) -> Practice:
    for practice in practices:
        if practice.id == practice_id:
            return practice
    raise RegistryError(f"no record with id {practice_id!r}")
