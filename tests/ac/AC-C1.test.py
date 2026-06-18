"""AC-C1.test.py — AC-C1 验收脚本骨架。

AC 编号: AC-C1
依赖模块: dev-004（调度 + 写入）
样本范围: 离线一日重放
硬约束: 否

测试方法:
    重放一个完整交易日的拉取日志，统计每分钟 lof_realtime 行数

通过条件:
    盘中 240 个分钟 × 30 行；整分钟缺失 ≤ 3 次

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.C1


@pytest.mark.ac_c
@pytest.mark.pending
def test_ac_c1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-C1"
    # TODO 模块就绪后填实——
    #   - 重放一个完整交易日的拉取日志，统计每分钟 lof_realtime 行数
    # 通过条件: 盘中 240 个分钟 × 30 行；整分钟缺失 ≤ 3 次

