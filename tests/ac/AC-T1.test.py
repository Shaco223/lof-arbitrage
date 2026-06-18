"""AC-T1：详情页头部固定展示三段式估算覆盖率。

测试方法：静态校验详情页源码与 mock detail 数据结构，确保三段字段
`top10_weight / benchmark_assigned_weight / cash_weight` 被渲染，且覆盖率颜色
阈值来自 §8（green/yellow/red）。真实 H5 Playwright 回归待稳定服务地址后补充。
通过条件：详情页包含覆盖率标签、三段式明细、tap 切换逻辑与颜色类。
依赖模块：dev-003（详情页）。
当前状态：已填实静态验收（硬约束第一阶段）。
"""
from __future__ import annotations

import re

import pytest

from _lib import AC

META = AC.T1


@pytest.mark.ac_t
@pytest.mark.ac_hard
def test_ac_t1_detail_page_renders_fixed_coverage_breakdown(project_root):
    """AC-T1 硬约束：详情页必须渲染覆盖率标签与三段式明细。"""
    assert META.code == "AC-T1"
    detail_vue = (project_root / "frontend" / "src" / "pages" / "detail" / "detail.vue").read_text(encoding="utf-8")
    mock_ts = (project_root / "frontend" / "src" / "mock" / "index.ts").read_text(encoding="utf-8")
    format_ts = (project_root / "frontend" / "src" / "utils" / "format.ts").read_text(encoding="utf-8")

    assert "coverage-tag" in detail_vue
    assert "估算覆盖率" in detail_vue
    assert "@tap=\"toggleBreakdown\"" in detail_vue
    assert "v-if=\"showBreakdown\"" in detail_vue
    for field in ("top10_weight", "benchmark_assigned_weight", "cash_weight"):
        assert f"detail.coverage_breakdown.{field}" in detail_vue
        assert field in mock_ts

    for css_class in ("coverage-green", "coverage-yellow", "coverage-red"):
        assert css_class in detail_vue

    assert re.search(r"if \(coverage >= 0\.9\) return 'green'", format_ts)
    assert re.search(r"if \(coverage >= 0\.7\) return 'yellow'", format_ts)
    assert "return 'red'" in format_ts
