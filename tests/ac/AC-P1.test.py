"""AC-P1.test.py — AC-P1 验收脚本骨架。

AC 编号: AC-P1
依赖模块: dev-004（拉取器 + IOPV 引擎）
样本范围: 161725 / 160706 / 501050 / 160119 / 160222
硬约束: 否

测试方法:
    离线 fixtures：盘后用官方公告净值反推真实溢价；逐分钟样本与拉取器输出对比

通过条件:
    |实时溢价 − 真实溢价| ≤ 0.5%（5 只指数 LOF 全部满足）

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.P1


@pytest.mark.ac_p
@pytest.mark.pending
def test_ac_p1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-P1"
    # TODO 模块就绪后填实——
    #   - 离线 fixtures：盘后用官方公告净值反推真实溢价
    #   - 逐分钟样本与拉取器输出对比
    # 通过条件: |实时溢价 − 真实溢价| ≤ 0.5%（5 只指数 LOF 全部满足）

