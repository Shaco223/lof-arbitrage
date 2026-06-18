"""AC-I1.test.py — AC-I1 验收脚本骨架。

AC 编号: AC-I1
依赖模块: dev-004（云函数）
样本范围: 30 行结构
硬约束: 否

测试方法:
    对 api-lof-list 连续打 100 次，统计 p95；逐字段比对 §6.1 schema

通过条件:
    p95 ≤ 800ms；每行 9 字段齐全 + 类型/枚举正确

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.I1


@pytest.mark.ac_i
@pytest.mark.pending
def test_ac_i1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-I1"
    # TODO 模块就绪后填实——
    #   - 对 api-lof-list 连续打 100 次，统计 p95
    #   - 逐字段比对 §6.1 schema
    # 通过条件: p95 ≤ 800ms；每行 9 字段齐全 + 类型/枚举正确

