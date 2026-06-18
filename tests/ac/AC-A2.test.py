"""AC-A2.test.py — AC-A2 验收脚本骨架。

AC 编号: AC-A2
依赖模块: dev-004（M3 冷却控制）
样本范围: 单基金
硬约束: 否

测试方法:
    30 分钟内多次注入超阈值；统计推送次数 + alert_log

通过条件:
    仅 1 次 sent；其余记录 status=cooldown_blocked

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.A2


@pytest.mark.ac_a
@pytest.mark.pending
def test_ac_a2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-A2"
    # TODO 模块就绪后填实——
    #   - 30 分钟内多次注入超阈值
    #   - 统计推送次数 + alert_log
    # 通过条件: 仅 1 次 sent；其余记录 status=cooldown_blocked

