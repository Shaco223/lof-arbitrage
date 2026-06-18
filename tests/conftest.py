"""tests/conftest.py — 通用 fixture / pending 标记自动 skip。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
FIXTURE_DIR = ROOT / "fixtures"

# 让 ac/e2e 子目录里的 from _lib import ... 可用
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def watchlist_csv(project_root: Path) -> Path:
    return project_root / "assets" / "lof-watchlist-v1.csv"


@pytest.fixture(scope="session")
def benchmark_csv(project_root: Path) -> Path:
    return project_root / "assets" / "benchmark-mapping-v1.csv"


def pytest_collection_modifyitems(config, items):
    skip_pending = pytest.mark.skip(reason="骨架阶段：等待对应模块交付后填实")
    for item in items:
        if "pending" in item.keywords:
            item.add_marker(skip_pending)