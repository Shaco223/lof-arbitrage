"""AC-I3.test.py — AC-I3 验收脚本骨架。

AC 编号: AC-I3
依赖模块: dev-004（云函数）
样本范围: 5 只样本
硬约束: 否

测试方法:
    对 api-lof-history?code=xxx&days=30 取样，按 §6.3 schema 校验

通过条件:
    items.length ≥ 20 个交易日；字段类型正确

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.I3


@pytest.mark.ac_i
@pytest.mark.pending
def test_ac_i3_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-I3"
    # TODO 模块就绪后填实——
    #   - 对 api-lof-history?code=xxx&days=30 取样，按 §6.3 schema 校验
    # 通过条件: items.length ≥ 20 个交易日；字段类型正确

