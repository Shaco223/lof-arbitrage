"""通用 pytest fixture 与 pending 标记自动跳过。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
FIXTURE_DIR = ROOT / "fixtures"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    markers = {
        "ac_p": "AC-P 性能/算法验收",
        "ac_c": "AC-C 采集验收",
        "ac_h": "AC-H 历史数据验收",
        "ac_a": "AC-A 告警验收",
        "ac_i": "AC-I 接口验收",
        "ac_s": "AC-S 架构与配额验收",
        "ac_t": "AC-T 透明度验收",
        "ac_q": "AC-Q QDII 参考指数估算验收",
        "ac_hard": "硬约束验收",
        "contract": "PRD §6 接口契约测试",
        "pending": "待对应模块交付后填实",
    }
    for name, description in markers.items():
        config.addinivalue_line("markers", f"{name}: {description}")


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def watchlist_csv(project_root: Path) -> Path:
    return project_root / "assets" / "lof-watchlist-v2.csv"


@pytest.fixture(scope="session")
def benchmark_csv(project_root: Path) -> Path:
    return project_root / "assets" / "benchmark-mapping-v2.csv"


def pytest_collection_modifyitems(config, items):
    skip_pending = pytest.mark.skip(reason="骨架阶段：等待对应模块交付后填实")
    for item in items:
        if "pending" in item.keywords:
            item.add_marker(skip_pending)
