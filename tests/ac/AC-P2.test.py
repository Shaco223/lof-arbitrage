"""AC-P2.test.py — AC-P2 验收脚本骨架。

AC 编号: AC-P2
依赖模块: dev-004（云函数 + 拉取器）
样本范围: 全部 30 只
硬约束: 否

测试方法:
    调 api-lof-list 取 30 行 coverage 字段；按 §M2 公式分流核对

通过条件:
    均值 ≥ 0.90；coverage<0.70 的个数 ≤ 3；指数型 ≈ 1.00

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.P2


@pytest.mark.ac_p
@pytest.mark.pending
def test_ac_p2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-P2"
    # TODO 模块就绪后填实——
    #   - 调 api-lof-list 取 30 行 coverage 字段
    #   - 按 §M2 公式分流核对
    # 通过条件: 均值 ≥ 0.90；coverage<0.70 的个数 ≤ 3；指数型 ≈ 1.00

