"""AC-H1.test.py — AC-H1 验收脚本骨架。

AC 编号: AC-H1
依赖模块: both（dev-004 history API；dev-003 折线展示由 AC-T1 单测）
样本范围: 抽 5 只
硬约束: 否

测试方法:
    调 api-lof-history?days=30；剔除节假日后检查日期序列连续性

通过条件:
    30 天范围内 trading_days 应 ≥ 20，且无非节假日断点

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.H1


@pytest.mark.ac_h
@pytest.mark.pending
def test_ac_h1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-H1"
    # TODO 模块就绪后填实——
    #   - 调 api-lof-history?days=30
    #   - 剔除节假日后检查日期序列连续性
    # 通过条件: 30 天范围内 trading_days 应 ≥ 20，且无非节假日断点

