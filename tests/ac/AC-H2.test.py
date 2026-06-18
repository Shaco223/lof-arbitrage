"""AC-H2.test.py — AC-H2 验收脚本骨架。

AC 编号: AC-H2
依赖模块: dev-004（每日校准 + 算法）
样本范围: 全部 30 只
硬约束: 否

测试方法:
    调 api-lof-history 取 premium_pctile_30d；离线脚本同口径独立计算后对比

通过条件:
    所有样本数值 ∈ [0,1]，与离线脚本绝对误差 ≤ 0.01

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.H2


@pytest.mark.ac_h
@pytest.mark.pending
def test_ac_h2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-H2"
    # TODO 模块就绪后填实——
    #   - 调 api-lof-history 取 premium_pctile_30d
    #   - 离线脚本同口径独立计算后对比
    # 通过条件: 所有样本数值 ∈ [0,1]，与离线脚本绝对误差 ≤ 0.01

