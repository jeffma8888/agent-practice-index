import datetime as _dt
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_root() -> pathlib.Path:
    return REPO_ROOT


@pytest.fixture
def practices():
    from agent_practice_index.registry import load_all, practices_dir
    return load_all(practices_dir(REPO_ROOT))


@pytest.fixture
def today() -> _dt.date:
    # Fixed date so freshness assertions are deterministic in CI.
    return _dt.date(2026, 8, 16)
