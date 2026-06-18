"""AC-A1.test.py — AC-A1 验收脚本骨架。

AC 编号: AC-A1
依赖模块: dev-004（M3 告警引擎）
样本范围: 单基金
硬约束: 否

测试方法:
    向告警引擎注入"溢价 6% 持续 1 分钟"事件流，监听通道 stub

通过条件:
    事件起算后 ≤ 2 分钟内收到 1 条告警，alert_log.status=sent

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.A1


@pytest.mark.ac_a
@pytest.mark.pending
def test_ac_a1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-A1"
    # TODO 模块就绪后填实——
    #   - 向告警引擎注入"溢价 6% 持续 1 分钟"事件流，监听通道 stub
    # 通过条件: 事件起算后 ≤ 2 分钟内收到 1 条告警，alert_log.status=sent

