"""AC-A3.test.py — AC-A3 验收脚本骨架。

AC 编号: AC-A3
依赖模块: dev-004（M3 阈值判断含交易时段）
样本范围: 4 个时间点
硬约束: 否

测试方法:
    把系统时间 / 输入事件时间分别置于盘前、午休、盘后、周末

通过条件:
    全部场景下不触发推送，不写 alert_log.sent

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.A3


@pytest.mark.ac_a
@pytest.mark.pending
def test_ac_a3_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-A3"
    # TODO 模块就绪后填实——
    #   - 把系统时间 / 输入事件时间分别置于盘前、午休、盘后、周末
    # 通过条件: 全部场景下不触发推送，不写 alert_log.sent

